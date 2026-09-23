"""M9.3 — the document chooser on the workspace backend (fake SDK client).

* the list endpoints return listing METADATA in bounded time and never open a
  workbook; content verdicts (kind by content, pairing facts) come from a
  background task with a per-file timeout, kept in the state role — a slow or
  failing file is listed as ``unreadable`` with the reason, never omitted,
  never retried in a loop;
* a selection either succeeds (download → pair → record) or FAILS carrying the
  reason, the STTM stays UNSELECTED and a run is refused — never a silent fall
  back to the config default. Since the addendum the STTM selection is a JOB
  (202 at once; the outcome is on the status — tests/test_m93_app_hang.py is
  about that contract); a VDD / local FRD failure is still a 424;
* choosing an STTM pairs its FRD / VDD from the SAME folder first
  (``frd_sttm_pairs/pair_N``), then the other input roots, and the result (or
  the question) is the job's ``pairing``.
"""

from __future__ import annotations

import json
import threading
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
from ui_select import select_sttm  # noqa: E402

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
    def __init__(self, monkeypatch, tmp_path, *, classify_timeout: float = 20.0,
                 select_timeout: float = 20.0):
        self.fake = FakeWorkspaceClient()
        self.fake.ws.dirs.update({f"{SHARED}/inputs", f"{SHARED}/state", PAIRS})
        self.slow: dict[str, float] = {}
        self.broken: dict[str, Exception] = {}
        # name -> Event: the download BLOCKS until the event is set (never, in
        # the test — the fixture sets it at teardown so no thread outlives it).
        self.blocked: dict[str, threading.Event] = {}
        download = self.fake.workspace.download

        def guarded(path, **kw):
            name = path.rsplit("/", 1)[-1]
            if name in self.blocked:
                self.fake.ws.calls.append(("download", path))
                self.blocked[name].wait()
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
                "classify_timeout_seconds": classify_timeout,
                "select_timeout_seconds": select_timeout,
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

    def release(self) -> None:
        for event in self.blocked.values():
            event.set()


@pytest.fixture
def ws(monkeypatch, tmp_path):
    workspace = _Workspace(monkeypatch, tmp_path)
    yield workspace
    workspace.release()
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
    # The verdicts live in the STATE role … (pushed by the background writer, M15.1)
    assert runner._index.wait_pushed(30)
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


def test_a_failed_state_write_warns_and_keeps_the_selection(ws):
    """Recording the choice is a convenience (it survives a container restart);
    a state folder the App cannot write is a deployment note, NOT a reason to
    throw the person's choice away. v0.5.4 failed the selection here — on a
    workspace whose state folder was read-only, choosing an STTM then did
    nothing at all."""
    ws.pairs("pair_1")
    runner = ws.runner()
    upload = ws.fake.workspace.upload

    def refuse(path, content, **kw):
        if path.endswith("/selection.json"):
            raise RuntimeError("PERMISSION_DENIED: state folder is read-only")
        return upload(path, content, **kw)

    ws.fake.workspace.upload = refuse
    local = runner.select_workbook("STTM_alpha.xlsx")
    assert local.name == "STTM_alpha.xlsx" and runner.selection()["sttm"] == "STTM_alpha.xlsx"
    assert runner.status()["selection_error"] is None
    job = runner.job_view()
    assert job["state"] == "done"
    assert [s["state"] for s in job["steps"] if s["step"] == "record"] == ["warning"]
    assert any("state folder is read-only" in w for w in job["warnings"]), job["warnings"]


def test_a_slow_state_write_never_holds_the_chosen_sttm_back(ws):
    """Reported from ACFC (direct upload): the FRD and VDD showed as paired,
    then the STTM's name took 2-3 more minutes to appear and Generate stayed
    disabled. The job's last step RECORDED the choice (selection.json, a
    Workspace API write) BEFORE applying it, with a 120 s budget. Now the
    choice is applied and the job done first; the write happens behind it."""
    import threading
    import time

    ws.pairs("pair_1")
    runner = ws.runner()
    upload = ws.fake.workspace.upload
    release = threading.Event()
    written: list[dict] = []

    def slow(path, content, **kw):
        if path.endswith("/selection.json"):
            release.wait(30)                     # the state role not answering
            data = content.read()
            written.append(json.loads(data))
            return upload(path, __import__("io").BytesIO(data), **kw)
        return upload(path, content, **kw)

    ws.fake.workspace.upload = slow
    started = time.monotonic()
    runner.start_selection("STTM_alpha.xlsx")
    job = runner.wait_selection(20)
    took = time.monotonic() - started
    assert job["state"] == "done" and took < 10, (took, job)
    assert runner.selection()["sttm"] == "STTM_alpha.xlsx"          # shown, Generate-able
    assert runner.status()["selection"]["frd"] == "FRD_bravo.docx"
    assert not written and not runner.wait_recorded(0.1)           # still being written
    # A second choice while the first write hangs: the NEWEST one is recorded.
    runner.clear_workbook()
    release.set()
    assert runner.wait_recorded(20)
    assert written[-1]["sttm"] is None, written
    assert json.loads(ws.fake.ws.files[f"{SHARED}/state/selection.json"])["sttm"] is None


def test_index_writes_never_run_inside_a_selection_step(ws, monkeypatch):
    """M15.1: with a cold index, classify / pair FRD / pair VDD each read a
    document on the request path — and each read used to end in a synchronous
    pull + push of document_index.json on the step's own thread (a Workspace
    API write that took minutes in ACFC, inside the step's budget). Now a
    state role whose write takes 5 s does not extend any step: the index is
    written locally and pushed by a background writer behind the selection.
    The background worker is OFF here so the request path must do all three
    reads itself (M15b.7 lets the worker win the race on a fast machine)."""
    ws.pairs("pair_1")
    runner = ws.runner()
    monkeypatch.setattr(runner._index, "_ensure_worker", lambda: None)
    # Explicitly COLD: no verdict anywhere (the test is about the reads the
    # request path must do itself, and a warm entry from a sibling test's
    # push made it flake).
    ws.fake.ws.files.pop(f"{SHARED}/state/document_index.json", None)
    runner._index._local_path().unlink(missing_ok=True)
    runner._index._entries = {}
    upload = ws.fake.workspace.upload
    pushes: list[float] = []

    def slow(path, content, **kw):
        if path.endswith("/document_index.json"):
            time.sleep(5)
            pushes.append(time.monotonic())
        return upload(path, content, **kw)

    ws.fake.workspace.upload = slow
    started = time.monotonic()
    assert runner.select_workbook("STTM_alpha.xlsx").name == "STTM_alpha.xlsx"
    took = time.monotonic() - started
    assert runner.job_view()["state"] == "done"
    assert runner.selection() == {"sttm": "STTM_alpha.xlsx", "frd": "FRD_bravo.docx",
                                  "vdd": "VDD_charlie.xlsx"}
    # Three documents are read cold on the request path; a 5 s write on that
    # path after each would have made this 15 s or more and put 5 s on the
    # classify / pair steps. No step took the write.
    assert took < 10, took
    job = runner.job_view()
    assert all(s["seconds"] < 5 for s in job["steps"] if s["step"] != "record"), job["steps"]
    # The index still reaches the state role — behind the selection, coalesced.
    assert runner._index.wait_pushed(40)
    assert pushes and f"{SHARED}/state/document_index.json" in ws.fake.ws.files
    entries = json.loads(ws.fake.ws.files[f"{SHARED}/state/document_index.json"])
    assert {e["name"] for e in entries.values()} >= {"STTM_alpha.xlsx", "FRD_bravo.docx",
                                                     "VDD_charlie.xlsx"}


def test_the_sttm_is_selected_and_a_run_may_start_before_its_pairing_lands(ws, monkeypatch):
    """M15.2: the job is DONE — the STTM applied, Generate enabled — as soon as
    the workbook is classified; both pairing steps land behind it
    (``pairing_pending`` names what is still on its way) and a run started
    meanwhile waits for them, never taking the config default instead."""
    ws.pairs("pair_1")
    runner = ws.runner()
    gate = threading.Event()
    real = runner._plan_pair

    def gated(kind, sttm_name, deadline=None):
        gate.wait(15)
        return real(kind, sttm_name, deadline)

    monkeypatch.setattr(runner, "_plan_pair", gated)
    runner.start_selection("STTM_alpha.xlsx")
    assert runner._job_done.wait(20)
    job = runner.job_view()
    assert job["state"] == "done" and job["pairing_pending"] == ["frd", "vdd"], job
    assert runner.selection() == {"sttm": "STTM_alpha.xlsx", "frd": None, "vdd": None}
    assert not runner.wait_paired(0.1)
    runner.start_live()                                     # enabled: no refusal
    for _ in range(100):
        if runner.stages and runner.stages[-1]["stage"] == "pairing":
            break
        time.sleep(0.05)
    assert runner.state == "running" and runner.stages[-1]["stage"] == "pairing", runner.stages
    gate.set()
    assert runner.wait_paired(30)
    assert runner.selection() == {"sttm": "STTM_alpha.xlsx", "frd": "FRD_bravo.docx",
                                  "vdd": "VDD_charlie.xlsx"}
    for _ in range(200):
        if runner.state == "done":
            break
        time.sleep(0.05)
    assert runner.state == "done"                           # the run went on after the pairing
    assert runner.wait_recorded(20)
    job = runner.job_view()
    steps = [s["step"] for s in job["steps"]]
    # The two pairings run in parallel (M15b.6): their order in the trace is free.
    assert job["pairing_pending"] == [] and steps[-1] == "record"
    assert set(steps[-3:-1]) == {"pair FRD", "pair VDD"}
    # M15.6: every step says how long it took.
    assert all(isinstance(s["seconds"], (int, float)) for s in job["steps"]), job["steps"]


def test_the_frd_and_vdd_pairings_run_in_parallel(ws, monkeypatch):
    """M15b.6: a slow VDD read (5 s) does not delay the FRD chip — the two
    pairings run in their own threads and each is applied as it lands, so the
    total pairing time is max(frd, vdd), not the sum."""
    ws.pairs("pair_1")
    runner = ws.runner()
    real = runner._plan_pair

    def slow_vdd(kind, sttm_name, deadline=None):
        if kind == "vdd":
            time.sleep(5)
        return real(kind, sttm_name, deadline)

    monkeypatch.setattr(runner, "_plan_pair", slow_vdd)
    runner.start_selection("STTM_alpha.xlsx")
    assert runner._job_done.wait(20)
    done_at = time.monotonic()
    while runner.selection()["frd"] is None and time.monotonic() - done_at < 10:
        time.sleep(0.05)
    frd_after = time.monotonic() - done_at
    assert runner.selection()["frd"] == "FRD_bravo.docx" and frd_after < 3, frd_after
    assert runner.selection()["vdd"] is None                 # still on its way
    assert runner.job_view()["pairing_pending"] == ["vdd"]
    assert runner.wait_paired(20)
    total = time.monotonic() - done_at
    assert runner.selection()["vdd"] == "VDD_charlie.xlsx"
    assert 5 <= total < 8, total                             # max(frd, vdd), not the sum
    steps = {s["step"]: s for s in runner.job_view()["steps"]}
    assert steps["pair FRD"]["state"] == "done" and steps["pair VDD"]["state"] == "done"
    assert steps["pair VDD"]["seconds"] >= 5 > steps["pair FRD"]["seconds"]


def test_app_start_indexes_the_recorded_selections_folder_first(ws, monkeypatch):
    """M15b.7: the folder selection.json names is queued for the background
    index and read first — before any person acts."""
    from ui.backend.docindex import DocumentIndex

    monkeypatch.setattr(DocumentIndex, "_ensure_worker", lambda self: None)   # queue only
    ws.pairs()                                                                # pair_1 .. pair_3
    ws.fake.ws.files[f"{SHARED}/state/selection.json"] = json.dumps(
        {"sttm": "STTM_delta.xlsx", "frd": "FRD_echo.docx", "vdd": "VDD_foxtrot.xlsx"}).encode()
    runner = ws.runner()                                                      # restore job
    job = runner.wait_selection(30)
    assert job["kind"] == "restore" and job["state"] == "done", job
    assert runner.selection()["sttm"] == "STTM_delta.xlsx"
    queued = []
    while True:
        try:
            queued.append(runner._index._queue.get_nowait())
        except Exception:  # noqa: BLE001 — drained
            break
    assert queued, "nothing was queued for the index at start"
    assert {d.source for d in queued[:3]} == {"frd_sttm_pairs/pair_2"}, [d.source for d in queued]


def test_an_automatic_pair_from_a_prior_sttm_never_survives_a_new_selection(ws, monkeypatch):
    """M15.3 (the stale-VDD finding of the review workflow): a pair VDD step
    that returned nothing — it raised, or timed out — left the PREVIOUS STTM's
    dictionary selected and badged auto-paired for the new one."""
    ws.pairs("pair_1")
    ws.put("pair_7", "STTM_golf.xlsx", TREE["pair_3"]["STTM_golf.xlsx"])     # alone in its folder
    runner = ws.runner()
    runner.select_workbook("STTM_alpha.xlsx")
    assert runner.selection()["vdd"] == "VDD_charlie.xlsx" and runner.vdd_auto_paired
    real = runner._plan_pair

    def broken(kind, sttm_name, deadline=None):
        if kind == "vdd":
            raise RuntimeError("the dictionary scan exploded")
        return real(kind, sttm_name, deadline)

    monkeypatch.setattr(runner, "_plan_pair", broken)
    runner.select_workbook("STTM_golf.xlsx")
    job = runner.job_view()
    assert job["state"] == "done"
    assert [s["state"] for s in job["steps"] if s["step"] == "pair VDD"] == ["warning"]
    assert runner.selection()["vdd"] is None and runner.vdd_auto_paired is None
    assert runner.status()["selection"]["vdd"] is None


def test_a_pairing_that_raises_never_discards_the_chosen_sttm(ws, monkeypatch):
    ws.pairs("pair_1")
    runner = ws.runner()
    monkeypatch.setattr(runner, "_plan_pair",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("pairing exploded")))
    assert runner.select_workbook("STTM_alpha.xlsx").name == "STTM_alpha.xlsx"
    assert runner.selection() == {"sttm": "STTM_alpha.xlsx", "frd": None, "vdd": None}
    job = runner.job_view()
    assert job["state"] == "done"
    assert [s["state"] for s in job["steps"] if s["step"].startswith("pair")] == ["warning",
                                                                                  "warning"]


def _api(monkeypatch, ws):
    from ui.backend import main

    if main.store is None:
        pytest.skip("the UI backend has no store in this environment")
    monkeypatch.setattr(main, "store", ws.store)
    monkeypatch.setattr(main, "runner", ws.runner())
    return TestClient(main.app), main


def test_api_select_failure_is_a_failed_job_with_the_reason_on_the_status(monkeypatch, ws):
    ws.pairs("pair_1")
    ws.broken["STTM_alpha.xlsx"] = RuntimeError("503 workspace files API unavailable")
    client, _main = _api(monkeypatch, ws)
    status = select_sttm(client, "STTM_alpha.xlsx")
    job = status["selection_job"]
    assert job["state"] == "failed" and job["error"]["code"] == "failed"
    assert "503 workspace files API unavailable" in job["error"]["message"]
    assert [(s["step"], s["state"]) for s in job["steps"]] == [("locate", "done"),
                                                              ("download", "failed")]
    assert status["sttm_chosen"] is False and status["selection"]["sttm"] is None
    assert status["selection_error"]["name"] == "STTM_alpha.xlsx"
    assert "was NOT selected" in status["selection_error"]["message"]
    rows = client.get("/api/demo/workbooks").json()["workbooks"]
    assert rows and not any(r["selected"] for r in rows)
    # A missing name is a failed job saying so; a clear resets the error.
    missing = select_sttm(client, "nope.xlsx")["selection_job"]
    assert missing["state"] == "failed" and missing["error"]["code"] == "not_found"
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
    # Restored by a background job: App start never waits for a download.
    job = restarted.wait_selection(60)
    assert job["kind"] == "restore" and job["state"] == "done", job
    assert restarted.selection() == recorded
    assert restarted.selected_workbook.name == "STTM_alpha.xlsx"
    assert restarted.selected_frd_label == "FRD_bravo.docx"
    assert restarted.selected_vdd.name == "VDD_charlie.xlsx"
    # A recorded document that is gone is SAID, not replaced by the default.
    del ws.fake.ws.files[f"{PAIRS}/pair_1/STTM_alpha.xlsx"]
    broken = ws.runner()
    assert broken.wait_selection(60)["state"] == "failed"
    assert broken.selected_workbook is None
    assert "no longer in the input folders" in broken.status()["selection_error"]["message"]


# ------------------------------------------------------------ 3. pairing on select


def test_select_pairs_from_the_same_folder_first_and_the_job_carries_the_outcome(
        monkeypatch, ws):
    ws.pairs()                                                  # pair_1 .. pair_3
    client, _main = _api(monkeypatch, ws)
    for sttm, folder, frd, vdd in (
            ("STTM_alpha.xlsx", "pair_1", "FRD_bravo.docx", "VDD_charlie.xlsx"),
            ("STTM_delta.xlsx", "pair_2", "FRD_echo.docx", "VDD_foxtrot.xlsx"),
            ("STTM_golf.xlsx", "pair_3", "FRD_hotel.docx", "VDD_india.xlsx")):
        status = select_sttm(client, sttm)
        job = status["selection_job"]
        assert job["state"] == "done" and job["error"] is None, job
        assert status["selection"] == {"sttm": sttm, "frd": frd, "vdd": vdd}
        assert status["selection_error"] is None
        # ONE record: the list's flag is the status' selection.
        rows = client.get("/api/demo/workbooks").json()["workbooks"]
        assert [r["name"] for r in rows if r["selected"]] == [sttm]
        assert {r["name"]: r["selected_as"] for r in rows if r["selected_as"]} == {
            sttm: "sttm", vdd: "vdd"}
        pairing = job["pairing"]
        for kind, expected in (("frd", frd), ("vdd", vdd)):
            assert pairing[kind]["chosen"] == expected, (sttm, kind, pairing[kind])
            assert pairing[kind]["scope"] == "same_folder"
            assert pairing[kind]["folder"] == f"frd_sttm_pairs/{folder}"
            # Only THIS folder's documents were ever candidates.
            assert {c["name"] for c in pairing[kind]["candidates"]} <= {expected}
            assert pairing[kind]["question"] is None
        assert (status["frd_name"], status["vdd_name"]) == (frd, vdd)
        assert status["pairing"]["frd"]["chosen"] == frd


def test_two_frds_in_the_folder_is_a_question_among_them_on_the_job(monkeypatch, ws):
    ws.pairs("pair_1", "pair_2")
    ws.put("pair_1", "FRD_lima.docx", TREE["pair_1"]["FRD_bravo.docx"])     # a second copy
    client, _main = _api(monkeypatch, ws)
    frd = select_sttm(client, "STTM_alpha.xlsx")["selection_job"]["pairing"]["frd"]
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
    # M15c: the other roots pair from INDEXED facts (never a scan on the
    # request path) — let the background index finish first.
    runner = _main._require_runner()
    runner.local_frd_candidates()
    assert runner._index.wait_idle(60)
    frd = select_sttm(client, "STTM_alpha.xlsx")["selection_job"]["pairing"]["frd"]
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


# ------------------------------------------------------------ M15: dead zone, late reads, order


def test_a_weak_vdd_score_is_a_question_not_a_dead_zone(config):
    """M15.4: a VDD whose best score sat above 0 but below min_score was
    neither paired nor asked about (and blocked the same-folder rescue)."""
    from codegen.pairing import facts_from_dict, pair_by_content

    sttm = facts_from_dict({"meta": {"file_format": ["CSV", "Sheet!B3"]}})
    weak = facts_from_dict({"meta": {"file_format": ["csv", "FILES!C2"]}})
    nothing = facts_from_dict({})
    paths = {"VDD_a.xlsx": Path("VDD_a.xlsx"), "VDD_b.xlsx": Path("VDD_b.xlsx")}
    decision = pair_by_content("vdd", Path("STTM_x.xlsx"), paths, config, REPO, known_facts={
        "STTM_x.xlsx": sttm, "VDD_a.xlsx": weak, "VDD_b.xlsx": nothing})
    best = decision.candidates[0]
    assert decision.chosen is None and best.name == "VDD_a.xlsx"
    assert 0 < best.score < config.inputs.pairing.min_score
    assert decision.ambiguous                                   # asked, with the scores
    question = decision.question()
    assert question["candidates"][0]["value"] == "VDD_a.xlsx"
    assert f"score {best.score:g}" in question["candidates"][0]["source"]
    # Kept as found (test_vdd_pairing_kind): a dictionary that shares NOTHING is
    # still OFFERED rather than silently dropped.
    none = pair_by_content("vdd", Path("STTM_x.xlsx"), {"VDD_b.xlsx": paths["VDD_b.xlsx"]},
                           config, REPO, known_facts={"STTM_x.xlsx": sttm, "VDD_b.xlsx": nothing})
    assert none.chosen is None and none.ambiguous


def test_the_sole_vdd_in_the_folder_pairs_even_on_a_weak_score(ws, monkeypatch):
    """M15.4: the same-folder rescue applies whenever the folder holds exactly
    one non-STTM workbook, whatever its content score."""
    from dataclasses import replace

    import codegen.pairing as pairing

    ws.put("pair_7", "STTM_mike.xlsx", TREE["pair_1"]["STTM_alpha.xlsx"])
    ws.put("pair_7", "VDD_november.xlsx", TREE["pair_1"]["VDD_charlie.xlsx"])
    real = pairing.pair_by_content

    def weak(kind, sttm_path, candidates, config, base_dir, **kw):
        decision = real(kind, sttm_path, candidates, config, base_dir, **kw)
        if kind != "vdd":
            return decision
        signal = (pairing.PairSignal("meta_file_format", 1.0, "same format"),)
        scored = tuple(pairing.PairCandidate(name, 1.0, signal) for name in candidates
                       if name != sttm_path.name)
        return replace(decision, chosen=None, rule=None, candidates=scored,
                       reason="no candidate wins by the margin: best 1, next 0", min_score=3.0)

    monkeypatch.setattr(pairing, "pair_by_content", weak)
    runner = ws.runner()
    runner.select_workbook("STTM_mike.xlsx")
    vdd = runner.last_pairing["vdd"]
    assert (vdd["chosen"], vdd["rule"], vdd["scope"]) == ("VDD_november.xlsx", "same_folder",
                                                          "same_folder")
    assert vdd["candidates"][0]["score"] == 1.0
    assert runner.selection()["vdd"] == "VDD_november.xlsx"


def test_a_candidate_not_read_in_time_survives_as_name_only(monkeypatch, tmp_path):
    """M15.5: a download that outlived the step's remaining budget raised
    StepTimeout, which the loop caught as an OSError and DROPPED the candidate
    ("unreachable") — the folder's own dictionary vanished from the pairing.
    It stays now, scored on its name, and the outcome says it was not read."""
    workspace = _Workspace(monkeypatch, tmp_path, select_timeout=6.0)
    try:
        workspace.pairs("pair_1")
        workspace.blocked["VDD_charlie.xlsx"] = threading.Event()   # never arrives
        runner = workspace.runner()
        assert runner.select_workbook("STTM_alpha.xlsx").name == "STTM_alpha.xlsx"
        job = runner.job_view()
        assert job["state"] == "done"
        assert [s["state"] for s in job["steps"] if s["step"] == "pair VDD"] == ["done"]
        vdd = runner.last_pairing["vdd"]
        assert [c["name"] for c in vdd["candidates"]] == ["VDD_charlie.xlsx"]
        assert vdd["unread"] == ["VDD_charlie.xlsx"]
        # Chosen by the folder rule, then its file did not arrive: said, not selected.
        assert vdd["chosen"] is None and "could not be downloaded" in vdd["reason"]
        assert runner.selection()["vdd"] is None
    finally:
        workspace.release()
        ui_stores.reset_stores()


def test_folders_list_in_natural_order_and_the_chosen_folder_is_indexed_first(ws, monkeypatch):
    """M15.8: pair_1, pair_2, … pair_10 (a string sort put pair_10 second), and
    the background index reads the folder of the STTM being selected next."""
    for folder in ("pair_10", "pair_2", "pair_1"):
        ws.put(folder, f"STTM_{folder}.xlsx", TREE["pair_1"]["STTM_alpha.xlsx"])
        ws.put(folder, f"VDD_{folder}.xlsx", TREE["pair_1"]["VDD_charlie.xlsx"])
    runner = ws.runner()
    monkeypatch.setattr(runner._index, "_ensure_worker", lambda: None)   # queue only
    rows = [c for c in runner.workbook_choices() if c["source"].startswith("frd_sttm")]
    assert [c["source"].rsplit("/", 1)[-1] for c in rows] == [
        "pair_1", "pair_1", "pair_2", "pair_2", "pair_10", "pair_10"]
    runner._index.prioritize("frd_sttm_pairs/pair_10")
    queued = []
    while True:
        try:
            queued.append(runner._index._queue.get_nowait())
        except Exception:  # noqa: BLE001 — drained
            break
    order = [d.source.rsplit("/", 1)[-1] for d in queued if d.source.startswith("frd_sttm")]
    assert order[:2] == ["pair_10", "pair_10"] and order[2:] == ["pair_1", "pair_1",
                                                                 "pair_2", "pair_2"]


def test_a_run_never_waits_for_the_vdd_and_waits_for_a_pending_frd_only_when_none_is_selected(
        ws, monkeypatch):
    """M15c (ACFC): Generate enabled, then the run sat on "waiting for the FRD
    / VDD pairing" for minutes — the VDD scan, with the FRD long paired. A run
    waits for a pending FRD only while NONE is selected, never for the VDD."""
    ws.pairs("pair_1")
    runner = ws.runner()
    gate = threading.Event()
    real = runner._plan_pair

    def slow_vdd(kind, sttm_name, deadline=None):
        if kind == "vdd":
            gate.wait(15)
        return real(kind, sttm_name, deadline)

    monkeypatch.setattr(runner, "_plan_pair", slow_vdd)
    runner.start_selection("STTM_alpha.xlsx")
    assert runner._job_done.wait(20)
    for _ in range(200):                                  # the FRD lands on its own
        if runner.selection()["frd"]:
            break
        time.sleep(0.05)
    assert runner.selection() == {"sttm": "STTM_alpha.xlsx", "frd": "FRD_bravo.docx", "vdd": None}
    started = time.monotonic()
    runner.start_live()
    for _ in range(200):
        if runner.state == "done":
            break
        time.sleep(0.05)
    assert runner.state == "done" and time.monotonic() - started < 3      # no wait for the VDD
    assert not any(s["stage"] == "pairing" for s in runner.stages), runner.stages
    gate.set()
    assert runner.wait_paired(20)

    # A pending FRD with none selected IS waited for: a run cannot go without one.
    runner2 = ws.runner()
    gate2 = threading.Event()
    real2 = runner2._plan_pair

    def slow_frd(kind, sttm_name, deadline=None):
        if kind == "frd":
            gate2.wait(15)
        return real2(kind, sttm_name, deadline)

    monkeypatch.setattr(runner2, "_plan_pair", slow_frd)
    runner2.start_selection("STTM_alpha.xlsx")
    assert runner2._job_done.wait(20)
    runner2.start_live()
    time.sleep(0.5)
    assert runner2.state == "running" and runner2.stages[-1]["stage"] == "pairing", runner2.stages
    gate2.set()
    for _ in range(200):
        if runner2.state == "done":
            break
        time.sleep(0.05)
    assert runner2.state == "done" and runner2.selection()["frd"] == "FRD_bravo.docx"


def test_the_other_roots_are_never_scanned_on_the_request_path(ws, monkeypatch):
    """M15c: an STTM whose folder holds no VDD falls to the "all" scope — scored
    from indexed facts or names only, never a read of every workbook of every
    folder on the request path (that scan took minutes in ACFC)."""
    ws.pairs()                                                          # pair_1 .. pair_3
    ws.put("inbox_7", "STTM_mike.xlsx", TREE["pair_1"]["STTM_alpha.xlsx"])   # alone
    runner = ws.runner()
    monkeypatch.setattr(runner._index, "_ensure_worker", lambda: None)  # cold, no worker
    started = time.monotonic()
    runner.select_workbook("STTM_mike.xlsx")
    took = time.monotonic() - started
    # The STTM itself (classify) and, at most, the LOCAL fixture workbooks —
    # never a remote pair folder's document.
    remote = {name for folder in TREE.values() for name in folder}
    assert "STTM_mike.xlsx" in runner._index.request_parses
    assert not remote & set(runner._index.request_parses), runner._index.request_parses
    vdd = runner.last_pairing["vdd"]
    assert vdd["scope"] == "all" and vdd["chosen"] is None
    assert vdd["unread"] and set(vdd["unread"]) <= {
        "VDD_charlie.xlsx", "VDD_foxtrot.xlsx", "VDD_india.xlsx",
        "STTM_alpha.xlsx", "STTM_delta.xlsx", "STTM_golf.xlsx"}
    assert took < 10, took


def test_an_explicit_pairing_map_entry_decides_without_reading_anything(ws, monkeypatch):
    """M15c: ``_plan_pair`` read every candidate BEFORE letting
    ``pair_by_content`` return the pairing_map's answer."""
    ws.pairs("pair_1", "pair_2")
    runner = ws.runner()
    monkeypatch.setattr(runner._index, "_ensure_worker", lambda: None)
    config = runner._store.config
    monkeypatch.setattr(runner._store, "config", config.model_copy(update={
        "demo": config.demo.model_copy(update={"pairing_map": {"STTM_alpha": "FRD_echo"}})}))
    runner.select_workbook("STTM_alpha.xlsx")
    frd = runner.last_pairing["frd"]
    assert (frd["chosen"], frd["rule"], frd["scope"]) == ("FRD_echo.docx", "pairing_map",
                                                          "pairing_map")
    assert not {"FRD_echo.docx", "FRD_bravo.docx"} & set(runner._index.request_parses)
    assert runner.selection()["frd"] == "FRD_echo.docx"


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
