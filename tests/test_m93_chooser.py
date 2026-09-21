"""M9.3 — the document chooser on the workspace backend (fake SDK client).

* the list endpoints return listing METADATA in bounded time and never open a
  workbook; content verdicts (kind by content, pairing facts) come from a
  background task with a per-file timeout, kept in the state role — a slow or
  failing file is listed as ``unreadable`` with the reason, never omitted,
  never retried in a loop;
* a selection either succeeds (download → pair → record) or is a 4xx carrying
  the reason, the STTM stays UNSELECTED and a run is refused — never a silent
  fall back to the config default;
* choosing an STTM pairs its FRD / VDD from the SAME folder first
  (``frd_sttm_pairs/pair_N``), then the other input roots, and the result (or
  the question) is in the same response.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import stores as ui_stores  # noqa: E402
from ui.backend.demo import DemoRunner, SelectionFailed  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.storage import open_storage  # noqa: E402
from storage_fakes import FakeWorkspaceClient  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
SHARED = "/Users/u/shared"
PAIRS = f"{SHARED}/frd_sttm_pairs"

# Opaque names: nothing in a file name pairs anything (no ticket, no stem).
TREE = {
    "pair_1": {"STTM_alpha.xlsx": SHAPES / "sttm" / "pair_1_family_a.xlsx",
               "FRD_bravo.docx": SHAPES / "frd" / "f1_pair_1.docx",
               "VDD_charlie.xlsx": SHAPES / "vdd" / "pair_1_v1_segments.xlsx"},
    "pair_2": {"STTM_delta.xlsx": SHAPES / "sttm" / "pair_2_family_b.xlsx",
               "FRD_echo.docx": SHAPES / "frd" / "f1_pair_2_variant.docx",
               "VDD_foxtrot.xlsx": SHAPES / "vdd" / "pair_2_v2_per_file.xlsx"},
    "pair_3": {"STTM_golf.xlsx": SHAPES / "sttm" / "pair_9_family_e.xlsx",
               "FRD_hotel.docx": SHAPES / "frd" / "f2_pair_8.docx",
               "VDD_india.xlsx": SHAPES / "vdd" / "pair_9_v3_per_table.xlsx"},
}
UNCLASSIFIED = SHAPES / "pair_1" / "golden" / "RFC_ACCUMULATORS_IIG.xlsx"


class _Workspace:
    def __init__(self, monkeypatch, tmp_path, *, classify_timeout: float = 20.0):
        self.fake = FakeWorkspaceClient()
        self.fake.ws.dirs.update({f"{SHARED}/inputs", f"{SHARED}/state", PAIRS})
        self.slow: dict[str, float] = {}
        self.broken: dict[str, Exception] = {}
        download = self.fake.workspace.download

        def guarded(path, **kw):
            name = path.rsplit("/", 1)[-1]
            if name in self.slow:
                self.fake.ws.calls.append(("download", path))
                time.sleep(self.slow[name])
            if name in self.broken:
                self.fake.ws.calls.append(("download", path))
                raise self.broken[name]
            return download(path, **kw)

        self.fake.workspace.download = guarded
        env = {"CODEGEN_STORAGE_INPUTS": f"workspace:/Workspace{SHARED}/inputs",
               "CODEGEN_STORAGE_STATE": f"workspace:/Workspace{SHARED}/state",
               "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
               "CODEGEN_EXTRA_INPUT_DIRS": f"workspace:/Workspace{PAIRS}"}
        monkeypatch.setattr(ui_stores, "open_storage", lambda config, base: open_storage(
            config, base, env=env, client=self.fake))
        ui_stores.reset_stores()
        self.store = GenerationStore(str(REPO / "config" / "config.yaml"))
        config = self.store.config
        monkeypatch.setattr(self.store, "config", config.model_copy(update={
            "inputs": config.inputs.model_copy(update={
                "classify_timeout_seconds": classify_timeout, "select_timeout_seconds": 20.0,
                "listing_ttl_seconds": 0.0})}))

    def put(self, folder: str, name: str, source: Path | bytes) -> None:
        self.fake.ws.dirs.add(f"{PAIRS}/{folder}")
        data = source if isinstance(source, bytes) else source.read_bytes()
        self.fake.ws.files[f"{PAIRS}/{folder}/{name}"] = data

    def pairs(self, *folders: str) -> None:
        for folder in folders or TREE:
            for name, source in TREE[folder].items():
                self.put(folder, name, source)

    def downloads(self, name: str | None = None) -> int:
        """Document downloads from the pairs root (state-file reads aside)."""
        return sum(1 for op, path in self.fake.ws.calls
                   if op == "download" and path.startswith(PAIRS)
                   and (name is None or path.endswith("/" + name)))

    def runner(self) -> DemoRunner:
        return DemoRunner(self.store, work=lambda: None)


@pytest.fixture
def ws(monkeypatch, tmp_path):
    workspace = _Workspace(monkeypatch, tmp_path)
    yield workspace
    ui_stores.reset_stores()


def _rows(runner) -> dict[str, dict]:
    return {c["name"]: c for c in runner.workbook_choices() if c["source"].startswith("frd_sttm")}


# ------------------------------------------------------------ 1. kind by content, off the request


def test_list_is_metadata_only_then_kinds_arrive_by_content_and_are_kept_in_state(ws):
    ws.pairs()
    ws.put("pair_1", "Inventory_juliet.xlsx", UNCLASSIFIED)
    runner = ws.runner()
    started = time.monotonic()
    rows = _rows(runner)
    assert time.monotonic() - started < 2.0
    assert len(rows) == 7 and {r["kind"] for r in rows.values()} == {"classifying"}
    assert all(isinstance(r["size"], int) and r["size"] > 0 for r in rows.values())
    assert rows["STTM_alpha.xlsx"]["source"] == "frd_sttm_pairs/pair_1"
    assert runner._index.wait_idle(60)
    rows = _rows(runner)
    assert {name: r["kind"] for name, r in rows.items()} == {
        "STTM_alpha.xlsx": "sttm", "STTM_delta.xlsx": "sttm", "STTM_golf.xlsx": "sttm",
        "VDD_charlie.xlsx": "vdd", "VDD_foxtrot.xlsx": "vdd", "VDD_india.xlsx": "vdd",
        "Inventory_juliet.xlsx": "unclassified"}               # listed, badged — never hidden
    assert "mapping sheet(s) ['FEED_1_MAPPING'] (content discovery)" in \
        rows["STTM_alpha.xlsx"]["kind_reason"]
    unclassified_reason = rows["Inventory_juliet.xlsx"]["kind_reason"]
    assert "no band row with stage + standard labels" in unclassified_reason
    # The verdicts live in the STATE role …
    index = {key: e for key, e in json.loads(
        ws.fake.ws.files[f"{SHARED}/state/document_index.json"]).items()
        if key.startswith("workspace:")}                        # (local fixtures are indexed too)
    assert sorted(e["name"] for e in index.values() if e["name"].endswith(".xlsx")) == sorted(rows)
    assert next(e for e in index.values() if e["name"] == "STTM_alpha.xlsx")["facts"]["tables"]
    # … so a restarted process (a new runner) reads NO workbook again.
    before = ws.downloads()
    again = ws.runner()
    assert {n: r["kind"] for n, r in _rows(again).items()} == {n: r["kind"]
                                                                 for n, r in rows.items()}
    again._index.wait_idle(10)
    assert ws.downloads() == before


def test_a_changed_file_is_read_again_once(ws):
    ws.pairs("pair_1")
    runner = ws.runner()
    _rows(runner)
    assert runner._index.wait_idle(60)
    assert _rows(runner)["VDD_charlie.xlsx"]["kind"] == "vdd"
    # The dictionary is replaced by a different workbook under the same name.
    ws.put("pair_1", "VDD_charlie.xlsx", UNCLASSIFIED)
    assert _rows(runner)["VDD_charlie.xlsx"]["kind"] == "classifying"   # new size: a new version
    assert runner._index.wait_idle(60)
    assert _rows(runner)["VDD_charlie.xlsx"]["kind"] == "unclassified"
    index = json.loads(ws.fake.ws.files[f"{SHARED}/state/document_index.json"])
    assert sum(1 for e in index.values() if e["name"] == "VDD_charlie.xlsx") == 1


def test_slow_and_failing_downloads_never_block_the_list_and_are_listed_unreadable(
        monkeypatch, tmp_path):
    ws = _Workspace(monkeypatch, tmp_path, classify_timeout=0.4)
    try:
        ws.pairs("pair_1")
        ws.put("pair_2", "STTM_slow.xlsx", TREE["pair_2"]["STTM_delta.xlsx"])
        ws.put("pair_3", "STTM_broken.xlsx", TREE["pair_3"]["STTM_golf.xlsx"])
        ws.slow["STTM_slow.xlsx"] = 2.0                        # longer than the 0.4 s timeout
        ws.broken["STTM_broken.xlsx"] = RuntimeError("403 Forbidden: no access to the object")
        runner = ws.runner()
        started = time.monotonic()
        rows = _rows(runner)
        assert time.monotonic() - started < 1.0                # the list does not wait for either
        assert {"STTM_slow.xlsx", "STTM_broken.xlsx", "STTM_alpha.xlsx"} <= set(rows)
        assert rows["STTM_slow.xlsx"]["kind"] == rows["STTM_broken.xlsx"]["kind"] == "classifying"
        assert runner._index.wait_idle(30)
        rows = _rows(runner)
        assert len(rows) == 4                                  # nothing omitted
        assert rows["STTM_alpha.xlsx"]["kind"] == "sttm"       # the healthy ones are classified
        assert rows["STTM_slow.xlsx"]["kind"] == "unreadable"
        assert "not read within 0.4s" in rows["STTM_slow.xlsx"]["kind_reason"]
        assert rows["STTM_broken.xlsx"]["kind"] == "unreadable"
        assert "403 Forbidden: no access to the object" in rows["STTM_broken.xlsx"]["kind_reason"]
        # Never retried in a loop: more listings, no more download attempts.
        attempts = (ws.downloads("STTM_slow.xlsx"), ws.downloads("STTM_broken.xlsx"))
        assert attempts == (1, 1)
        for _ in range(3):
            assert _rows(runner)["STTM_broken.xlsx"]["kind"] == "unreadable"
        runner._index.wait_idle(10)
        assert (ws.downloads("STTM_slow.xlsx"), ws.downloads("STTM_broken.xlsx")) == attempts
        # … until a person asks: exactly one more attempt.
        del ws.broken["STTM_broken.xlsx"]
        runner.reclassify_workbook("STTM_broken.xlsx")
        assert runner._index.wait_idle(30)
        assert _rows(runner)["STTM_broken.xlsx"]["kind"] == "sttm"
        assert ws.downloads("STTM_broken.xlsx") == 2
    finally:
        ui_stores.reset_stores()


# ------------------------------------------------------------ 2. a selection succeeds or says why


def test_failed_download_leaves_the_sttm_unselected_with_the_reason(ws):
    ws.pairs("pair_1", "pair_2")
    # Broken from the START: the background index may otherwise download the
    # workbook first, and a working copy of the listed size is (rightly) reused.
    ws.broken["STTM_alpha.xlsx"] = RuntimeError("503 workspace files API unavailable")
    runner = ws.runner()
    runner.select_workbook("STTM_delta.xlsx")                  # a good selection first
    assert runner.selected_workbook is not None and runner.selected_frd is not None
    runner._index.wait_idle(30)
    with pytest.raises(SelectionFailed) as failed:
        runner.select_workbook("STTM_alpha.xlsx")
    message = str(failed.value)
    assert "STTM 'STTM_alpha.xlsx' was NOT selected" in message
    assert "downloading workspace:" in message and "503 workspace files API unavailable" in message
    # Unselected — neither the previous pick nor its pair, and NOT the config default.
    assert runner.selected_workbook is None and runner.selected_frd is None
    assert runner.selected_vdd is None
    status = runner.status()
    assert status["selection_error"] == {"kind": "sttm", "name": "STTM_alpha.xlsx",
                                         "message": message}
    assert not any(c["selected"] for c in runner.workbook_choices())
    with pytest.raises(ValueError, match="was NOT selected"):
        runner.start_live()                                     # never runs the config default
    # Choosing again (the download works now) clears it.
    del ws.broken["STTM_alpha.xlsx"]
    runner.select_workbook("STTM_alpha.xlsx")
    assert runner.status()["selection_error"] is None and runner.selected_workbook is not None


def test_a_failed_state_write_fails_the_selection_too(ws):
    ws.pairs("pair_1")
    runner = ws.runner()
    upload = ws.fake.workspace.upload

    def refuse(path, content, **kw):
        if path.endswith("/selection.json"):
            raise RuntimeError("PERMISSION_DENIED: state folder is read-only")
        return upload(path, content, **kw)

    ws.fake.workspace.upload = refuse
    with pytest.raises(SelectionFailed, match="recording the selection in the state role failed"):
        runner.select_workbook("STTM_alpha.xlsx")
    assert runner.selected_workbook is None
    assert "state folder is read-only" in runner.status()["selection_error"]["message"]


def _api(monkeypatch, ws):
    from ui.backend import main

    if main.store is None:
        pytest.skip("the UI backend has no store in this environment")
    monkeypatch.setattr(main, "store", ws.store)
    monkeypatch.setattr(main, "runner", ws.runner())
    return TestClient(main.app), main


def test_api_select_failure_is_a_424_with_the_reason_and_the_status_shows_it(monkeypatch, ws):
    ws.pairs("pair_1")
    ws.broken["STTM_alpha.xlsx"] = RuntimeError("503 workspace files API unavailable")
    client, _main = _api(monkeypatch, ws)
    response = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"})
    assert response.status_code == 424
    assert "503 workspace files API unavailable" in response.json()["detail"]
    status = client.get("/api/demo/status").json()
    assert status["sttm_chosen"] is False
    assert status["selection_error"]["name"] == "STTM_alpha.xlsx"
    assert "was NOT selected" in status["selection_error"]["message"]
    rows = client.get("/api/demo/workbooks").json()["workbooks"]
    assert rows and not any(r["selected"] for r in rows)
    # A missing name stays a 404; a clear resets the error.
    assert client.post("/api/demo/workbook", json={"name": "nope.xlsx"}).status_code == 404
    client.delete("/api/demo/workbook")
    assert client.get("/api/demo/status").json()["selection_error"] is None


def test_api_vdd_from_a_workspace_folder_is_selectable_and_a_failure_is_a_424(monkeypatch, ws):
    """The route used to look in the LOCAL directories only: a dictionary that
    lives in a workspace pair folder answered 404."""
    ws.pairs("pair_1")
    client, _main = _api(monkeypatch, ws)
    assert client.post("/api/demo/vdd", json={"name": "VDD_charlie.xlsx"}).status_code == 200
    assert client.get("/api/demo/status").json()["vdd_name"] == "VDD_charlie.xlsx"
    ws.put("pair_1", "VDD_kilo.xlsx", TREE["pair_2"]["VDD_foxtrot.xlsx"])
    ws.broken["VDD_kilo.xlsx"] = RuntimeError("504 gateway timeout")
    response = client.post("/api/demo/vdd", json={"name": "VDD_kilo.xlsx"})
    assert response.status_code == 424 and "504 gateway timeout" in response.json()["detail"]
    assert client.get("/api/demo/status").json()["selection_error"]["kind"] == "vdd"


def test_selection_is_recorded_in_the_state_role_and_restored_after_a_restart(ws):
    ws.pairs("pair_1")
    runner = ws.runner()
    runner.select_workbook("STTM_alpha.xlsx")
    recorded = json.loads(ws.fake.ws.files[f"{SHARED}/state/selection.json"])
    assert recorded == {"sttm": "STTM_alpha.xlsx", "frd": "FRD_bravo.docx",
                        "vdd": "VDD_charlie.xlsx"}
    restarted = ws.runner()                                     # a new container
    assert restarted.selected_workbook.name == "STTM_alpha.xlsx"
    assert restarted.selected_frd_label == "FRD_bravo.docx"
    assert restarted.selected_vdd.name == "VDD_charlie.xlsx"
    # A recorded document that is gone is SAID, not replaced by the default.
    del ws.fake.ws.files[f"{PAIRS}/pair_1/STTM_alpha.xlsx"]
    broken = ws.runner()
    assert broken.selected_workbook is None
    assert "no longer in the input folders" in broken.status()["selection_error"]["message"]


# ------------------------------------------------------------ 3. pairing on select


def test_select_pairs_from_the_same_folder_first_and_answers_in_the_same_response(
        monkeypatch, ws):
    ws.pairs()                                                  # pair_1 .. pair_3
    client, _main = _api(monkeypatch, ws)
    for sttm, folder, frd, vdd in (
            ("STTM_alpha.xlsx", "pair_1", "FRD_bravo.docx", "VDD_charlie.xlsx"),
            ("STTM_delta.xlsx", "pair_2", "FRD_echo.docx", "VDD_foxtrot.xlsx"),
            ("STTM_golf.xlsx", "pair_3", "FRD_hotel.docx", "VDD_india.xlsx")):
        response = client.post("/api/demo/workbook", json={"name": sttm})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["selected"] == sttm and body["selection_error"] is None
        pairing = body["pairing"]
        for kind, expected in (("frd", frd), ("vdd", vdd)):
            assert pairing[kind]["chosen"] == expected, (sttm, kind, pairing[kind])
            assert pairing[kind]["scope"] == "same_folder"
            assert pairing[kind]["folder"] == f"frd_sttm_pairs/{folder}"
            # Only THIS folder's documents were ever candidates.
            assert {c["name"] for c in pairing[kind]["candidates"]} <= {expected}
            assert pairing[kind]["question"] is None
        status = client.get("/api/demo/status").json()
        assert (status["frd_name"], status["vdd_name"]) == (frd, vdd)
        assert status["pairing"]["frd"]["chosen"] == frd


def test_two_frds_in_the_folder_is_a_question_among_them_in_the_same_response(monkeypatch, ws):
    ws.pairs("pair_1", "pair_2")
    ws.put("pair_1", "FRD_lima.docx", TREE["pair_1"]["FRD_bravo.docx"])     # a second copy
    client, _main = _api(monkeypatch, ws)
    body = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"}).json()
    frd = body["pairing"]["frd"]
    assert frd["chosen"] is None and frd["scope"] == "same_folder"
    assert frd["question"]["key"] == "pair.frd" and frd["question"]["kind"] == "choice"
    assert {c["value"] for c in frd["question"]["candidates"]} == {"FRD_bravo.docx",
                                                                   "FRD_lima.docx"}
    assert "no candidate wins by the margin" in frd["reason"]
    assert client.get("/api/demo/status").json()["frd_chosen"] is False   # never guessed


def test_a_folder_without_candidates_falls_back_to_the_other_input_roots(monkeypatch, ws):
    ws.pairs("pair_2")
    ws.put("pair_1", "STTM_alpha.xlsx", TREE["pair_1"]["STTM_alpha.xlsx"])  # the STTM alone
    ws.put("shared_docs", "FRD_bravo.docx", TREE["pair_1"]["FRD_bravo.docx"])
    client, _main = _api(monkeypatch, ws)
    frd = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"}).json()[
        "pairing"]["frd"]
    assert frd["scope"] == "all" and frd["chosen"] == "FRD_bravo.docx" and frd["rule"] == "content"
    assert {"FRD_bravo.docx", "FRD_echo.docx"} <= {c["name"] for c in frd["candidates"]}


def test_a_sole_candidate_in_a_pair_folder_pairs_even_without_a_content_signal(ws):
    """The real pair-1 STTM states no file names (TBD): nothing in it points at
    its dictionary. In a pair FOLDER the folder is the person's pairing."""
    ws.put("pair_7", "STTM_mike.xlsx", TREE["pair_1"]["STTM_alpha.xlsx"])
    ws.put("pair_7", "VDD_november.xlsx", TREE["pair_3"]["VDD_india.xlsx"])  # unrelated content
    runner = ws.runner()
    runner.select_workbook("STTM_mike.xlsx")
    vdd = runner.last_pairing["vdd"]
    assert (vdd["chosen"], vdd["rule"], vdd["scope"]) == ("VDD_november.xlsx", "same_folder",
                                                          "same_folder")
    assert "the only VDD in the STTM's folder 'frd_sttm_pairs/pair_7'" in vdd["reason"]
    assert runner.vdd_auto_paired == {"vdd": "VDD_november.xlsx", "rule": "same_folder"}


# ------------------------------------------------------------ the classifier itself (pure, offline)


@pytest.mark.parametrize("path,kind", [
    *[(p, "sttm") for p in sorted((SHAPES / "sttm").glob("*.xlsx"))],
    *[(p, "vdd") for p in sorted((SHAPES / "vdd").glob("*.xlsx"))],
    (UNCLASSIFIED, "unclassified"),
], ids=lambda v: v.name if isinstance(v, Path) else v)
def test_workbooks_are_classified_by_content_never_by_name(path, kind, config, tmp_path):
    from codegen.layout.classify import classify_workbook

    # Under a name that says nothing (or the WRONG thing) about what it is.
    disguised = tmp_path / ("VDD_not_really.xlsx" if kind == "sttm" else "STTM_not_really.xlsx")
    disguised.write_bytes(path.read_bytes())
    verdict = classify_workbook(disguised, config.extractor)
    assert verdict.kind == kind, verdict.reason
    assert verdict.reason


def test_a_file_that_is_not_a_workbook_is_unclassified_with_the_error(config, tmp_path):
    from codegen.layout.classify import classify_workbook

    broken = tmp_path / "STTM_truncated.xlsx"
    broken.write_bytes(b"PK\x03\x04 not a real workbook")
    verdict = classify_workbook(broken, config.extractor)
    assert verdict.kind == "unclassified" and verdict.reason.startswith("could not be read")
