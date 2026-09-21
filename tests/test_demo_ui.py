"""Demo-mode backend: replay discovery/loading, live-run guardrails.

Needs the [ui] extra (fastapi); skipped cleanly when it isn't installed so
the core generator suite stays offline-and-extra-free.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

REPO = Path(__file__).resolve().parents[1]

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend.demo import DemoRunner, LiveRunInProgress  # noqa: E402
from ui.backend.replay import (  # noqa: E402
    list_past_live_runs,
    list_replay_sets,
    load_past_live_run,
    load_replay_set,
)
from ui.backend.service import GenerationStore  # noqa: E402

REPLAY_SET = "live_e2e_20260807"
# The tracked replay set was removed from the repo 2026-08-22 (no client
# documents, raw or derived, in the repository); the two tests that read it
# skip until an anonymized set is restored under fixtures/replay/.
needs_replay_set = pytest.mark.skipif(
    not (REPO / "fixtures" / "replay" / REPLAY_SET / "call_log.json").is_file(),
    reason="tracked replay set removed from the repo 2026-08-22",
)


@pytest.fixture()
def decisions_path(monkeypatch, tmp_path):
    """Point decision persistence at a scratch file, away from real state."""
    from ui.backend import service

    path = tmp_path / "decisions.json"
    monkeypatch.setattr(service, "DECISIONS_PATH", path)
    return path


def _index_idle() -> None:
    """M9.3: the chooser reads listed documents in a background task; wait for
    it before deleting a file it may have open (a Windows sharing violation)."""
    from ui.backend import main

    if main.runner is not None:
        main.runner._index.wait_idle(30)


def _adopt_empty(store: GenerationStore, *, mode: str, label: str | None) -> None:
    store.adopt({}, [], mode=mode, label=label, out_root=store.out_root,
                reports_root=store.reports_root)


@pytest.fixture()
def client(monkeypatch):
    # No key in the test process: live must read as unavailable by default
    # and nothing can ever fire a billed call from the suite. The tracked
    # config selects databricks_fmapi, which resolves from YAML alone — so
    # the fixture pins the key-gated anthropic provider (and deletes the
    # key) rather than trusting config/config.yaml to stay un-runnable.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ui.backend import main

    if main.store is not None:
        reasoning = main.store.config.reasoning.model_copy(
            update={"provider": "anthropic"}
        )
        monkeypatch.setattr(
            main.store,
            "config",
            main.store.config.model_copy(update={"reasoning": reasoning}),
        )

    # Plain TestClient (no context manager): skips lifespan generation — these
    # tests exercise the demo endpoints, not the startup mock run.
    return TestClient(main.app)


def test_single_run_guard_rejects_concurrent_live(config):
    store = GenerationStore("config/config.yaml")
    release = threading.Event()
    runner = DemoRunner(store, work=release.wait)
    runner.start_live()
    try:
        with pytest.raises(LiveRunInProgress):
            runner.start_live()
    finally:
        release.set()
    for _ in range(50):
        if runner.state == "done":
            break
        time.sleep(0.02)
    assert runner.state == "done"
    # Guard released: a new run may start.
    runner._work = lambda: None
    runner.start_live()


def test_live_failure_surfaces_and_releases_guard():
    store = GenerationStore("config/config.yaml")

    def explode():
        raise RuntimeError("api down")

    runner = DemoRunner(store, work=explode)
    runner.start_live()
    for _ in range(50):
        if runner.state == "failed":
            break
        time.sleep(0.02)
    assert runner.state == "failed"
    assert "api down" in (runner.error or "")
    runner._work = lambda: None
    runner.start_live()  # guard released after failure


def test_needs_layout_pauses_the_run_until_answered(monkeypatch):
    """M2.5 §6: unresolved roles pause the run in ``needs_layout`` with the
    question list on the status; answers resume it; ``cancel`` fails it."""
    from codegen.layout import resolve as resolve_module
    from codegen.layout.profile import LayoutProfile
    from codegen.layout.resolve import DocumentResolution, LayoutQuestion, PairResolution

    calls: list[dict] = []

    def fake_resolve_pair(sttm, frd, config, **kwargs):
        calls.append(kwargs.get("answers") or {})
        profile = LayoutProfile(fingerprint="f", sheets=[], source="synonyms",
                                strategy="content")
        doc = DocumentResolution("sttm", profile)
        if not (kwargs.get("answers") or {}).get("sttm"):
            doc.questions = [LayoutQuestion("sttm", "S", "stage", "column", "why",
                                            ["A: x"], [{"col": 1, "header": "x"}])]
        return PairResolution(sttm=doc, frd=None, frd_contract=None)

    monkeypatch.setattr(resolve_module, "resolve_pair", fake_resolve_pair)
    store = GenerationStore("config/config.yaml")
    runner = DemoRunner(store)
    seen: dict = {}

    def work():
        result = runner._resolve_layout(REPO / "x.xlsx", REPO / "y.docx", store.config)
        seen["questions"] = result.questions

    runner._work = work
    runner.start_live()
    for _ in range(100):
        if runner.state == "needs_layout":
            break
        time.sleep(0.02)
    assert runner.state == "needs_layout"
    status = runner.status()
    assert status["layout_questions"][0]["key"] == "S/stage/column"
    assert status["layout_questions"][0]["candidates"] == [{"col": 1, "header": "x"}]
    runner.answer_layout({"sttm": {"S/stage/column": 1}})
    for _ in range(100):
        if runner.state == "done":
            break
        time.sleep(0.02)
    assert runner.state == "done" and seen["questions"] == []
    assert calls[-1] == {"sttm": {"S/stage/column": 1}, "frd": {}, "vdd": {}, "gaps": {}}
    # Not waiting -> answering is refused.
    with pytest.raises(LiveRunInProgress):
        runner.answer_layout({})
    # A cancel fails the run loudly.
    runner._work = work
    runner.start_live()
    for _ in range(100):
        if runner.state == "needs_layout":
            break
        time.sleep(0.02)
    runner.answer_layout({}, cancel=True)
    for _ in range(100):
        if runner.state == "failed":
            break
        time.sleep(0.02)
    assert runner.state == "failed" and "cancelled" in (runner.error or "")


def test_re_resolve_layout_is_a_one_shot_refresh_before_a_run_and_from_the_dialog(monkeypatch):
    """M9.1: "re-resolve layout" bypasses every cached profile — armed for the
    next run (one shot), or asked from the needs_layout dialog, where it also
    drops the answers given to the OLD profile's questions."""
    from codegen.layout import resolve as resolve_module
    from codegen.layout.profile import LayoutProfile
    from codegen.layout.resolve import DocumentResolution, LayoutQuestion, PairResolution

    calls: list[dict] = []

    def fake_resolve_pair(sttm, frd, config, **kwargs):
        calls.append({"refresh": kwargs.get("refresh"), "answers": kwargs.get("answers")})
        profile = LayoutProfile(fingerprint="f", sheets=[], source="synonyms",
                                strategy="content")
        doc = DocumentResolution("sttm", profile)
        if len(calls) < 3:          # two rounds of questions, then complete
            doc.questions = [LayoutQuestion("sttm", "S", "stage", "schema", "why",
                                            ["A: x"], [{"col": 1, "header": "x"}])]
        return PairResolution(sttm=doc, frd=None, frd_contract=None)

    monkeypatch.setattr(resolve_module, "resolve_pair", fake_resolve_pair)
    store = GenerationStore("config/config.yaml")
    runner = DemoRunner(store)
    runner._work = lambda: runner._resolve_layout(REPO / "x.xlsx", REPO / "y.docx", store.config)

    assert runner.status()["layout_refresh"] is False
    runner.set_layout_refresh(True)
    assert runner.status()["layout_refresh"] is True
    runner.start_live()
    for _ in range(100):
        if runner.state == "needs_layout":
            break
        time.sleep(0.02)
    assert runner.state == "needs_layout"
    assert calls[0]["refresh"] is True and runner.layout_refresh is False      # consumed
    assert any(s["stage"] == "re-resolve layout" for s in runner.status()["stages"])
    with pytest.raises(LiveRunInProgress):
        runner.set_layout_refresh(True)             # a run is in progress: use its dialog
    # An ordinary answer round: no refresh, the answer is carried.
    runner.answer_layout({"sttm": {"S/stage/schema": 1}})
    for _ in range(100):
        if len(calls) == 2 and runner.state == "needs_layout":
            break
        time.sleep(0.02)
    assert calls[1]["refresh"] is False and calls[1]["answers"]["sttm"] == {"S/stage/schema": 1}
    # "Re-resolve layout" from the dialog: refresh again, the old answers dropped.
    runner.answer_layout({}, refresh=True)
    for _ in range(100):
        if runner.state == "done":
            break
        time.sleep(0.02)
    assert runner.state == "done"
    assert calls[2]["refresh"] is True and calls[2]["answers"]["sttm"] == {}


def test_layout_refresh_endpoint(client):
    r = client.post("/api/demo/layout-refresh", json={"enabled": True})
    assert r.status_code == 200 and r.json()["layout_refresh"] is True
    assert client.get("/api/demo/status").json()["layout_refresh"] is True
    r = client.post("/api/demo/layout-refresh", json={"enabled": False})
    assert r.status_code == 200 and r.json()["layout_refresh"] is False
    # The dialog's re-resolve needs a waiting run, like every other answer.
    r = client.post("/api/demo/layout-answers", json={"answers": {}, "refresh": True})
    assert r.status_code == 409


def test_layout_answers_endpoint_guards(client):
    r = client.post("/api/demo/layout-answers", json={"answers": {"sttm": {"bad key": 1}}})
    assert r.status_code == 400
    r = client.post("/api/demo/layout-answers", json={"answers": {"sttm": {"S/stage/column": 1}}})
    assert r.status_code == 409          # no run is waiting


def test_run_live_requires_explicit_confirm(client):
    response = client.post("/api/demo/run-live", json={})
    assert response.status_code == 400
    assert "confirm" in response.json()["detail"]
    response = client.post("/api/demo/run-live", json={"confirm": False})
    assert response.status_code == 400


def test_run_live_without_key_is_rejected(client):
    response = client.post("/api/demo/run-live", json={"confirm": True})
    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_live_available_is_boolean_only(client, monkeypatch):
    payload = client.get("/api/demo/live-available").json()
    assert (payload["available"], payload["provider"], payload["reason"]) == (
        False, "mock", "no ANTHROPIC_API_KEY in the backend env")
    assert payload["transport"]["runtime"] == "local"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-echoed")
    payload = client.get("/api/demo/live-available").json()
    assert (payload["available"], payload["provider"], payload["reason"]) == (
        True, "anthropic", "")
    assert payload["transport"]["label"].startswith("Anthropic API (")
    assert "test-key-never-echoed" not in repr(payload)


def test_live_available_fmapi_needs_no_key(client, monkeypatch):
    # FMAPI availability is pure config resolution — no key, no network.
    from ui.backend import main

    reasoning = main.store.config.reasoning.model_copy(
        update={"provider": "databricks_fmapi"}
    )
    monkeypatch.setattr(
        main.store,
        "config",
        main.store.config.model_copy(update={"reasoning": reasoning}),
    )
    payload = client.get("/api/demo/live-available").json()
    assert (payload["available"], payload["provider"], payload["reason"]) == (
        True, "databricks_fmapi", "")
    assert payload["transport"]["endpoint"] == main.store.config.databricks.serving_endpoint
    assert payload["transport"]["runtime"] == "local"


def test_databricks_runtime_forces_the_foundation_model_endpoint(client, monkeypatch):
    """Inside a Databricks runtime (Apps injects DATABRICKS_APP_PORT) the
    transport is the Foundation Model endpoint even when the yaml says
    anthropic — and the override is reported, never silent."""
    monkeypatch.setenv("DATABRICKS_APP_PORT", "8080")
    payload = client.get("/api/demo/live-available").json()
    transport = payload["transport"]
    assert payload["provider"] == "databricks_fmapi" and payload["available"] is True
    assert transport["runtime"] == "databricks_app"
    assert transport["detected_by"] == "DATABRICKS_APP_PORT"
    assert transport["configured"] == "anthropic" and transport["overridden"] is True
    assert "inside Databricks the Foundation Model endpoint is used" in transport["reason"]
    assert transport["label"].startswith("Databricks Foundation Model endpoint ")


@needs_replay_set
def test_replay_discovery_finds_tracked_set():
    sets = {s.name: s for s in list_replay_sets()}
    assert REPLAY_SET in sets
    tracked = sets[REPLAY_SET]
    assert tracked.date == "2026-08-07"
    assert tracked.has_call_log
    assert len(tracked.feeds) == 3


@needs_replay_set
def test_replay_load_rebuilds_live_state_offline(monkeypatch, tmp_path):
    # No key, no network: replay must still produce full pipeline state with
    # the recorded anthropic candidates injected.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    store = GenerationStore("config/config.yaml")
    load_replay_set(store, REPLAY_SET)
    assert store.mode == "replay"
    assert store.label == REPLAY_SET
    assert len(store.runs) == 3
    for run in store.runs.values():
        assert run.gate.verdict == "PASS_WITH_FLAGS"
        assert run.candidates, "replayed feed must carry recorded candidates"
        for candidate in run.candidates:
            assert candidate.provider == "anthropic"
            assert candidate.grounded
    # Isolation: replay artifacts live under their own root, not default out/.
    assert store.out_root.name == f"replay_{REPLAY_SET}"


def test_decisions_are_scoped_to_the_run(decisions_path):
    store = GenerationStore("config/config.yaml")
    store.save_decision("feed_a", 0, "approved", None)  # run_key "mock"
    assert store.load_decisions()["feed_a"]["0"]["decision"] == "approved"

    # Same rule under a different run starts pending, and its decision
    # never bleeds back into mock.
    _adopt_empty(store, mode="live", label="demo_20990101_000000")
    assert store.load_decisions() == {}
    store.save_decision("feed_a", 0, "rejected", None)
    assert store.load_decisions()["feed_a"]["0"]["decision"] == "rejected"

    _adopt_empty(store, mode="mock", label=None)
    assert store.load_decisions()["feed_a"]["0"]["decision"] == "approved"


def test_pre_v2_decisions_shape_is_discarded(decisions_path):
    import json as json_mod

    decisions_path.write_text(
        json_mod.dumps({"cv_x": {"0": {"decision": "approved", "note": None}}})
    )
    store = GenerationStore("config/config.yaml")
    assert store.load_decisions() == {}


def test_reset_decisions_clears_only_current_run(decisions_path):
    store = GenerationStore("config/config.yaml")
    store.save_decision("feed_a", 0, "approved", None)  # mock
    _adopt_empty(store, mode="replay", label="some_set")
    store.save_decision("feed_a", 0, "approved", None)  # some_set
    store.reset_decisions()
    assert store.load_decisions() == {}
    _adopt_empty(store, mode="mock", label=None)
    assert store.load_decisions()["feed_a"]["0"]["decision"] == "approved"


def test_reset_decisions_endpoint(client, decisions_path):
    response = client.post("/api/decisions/reset")
    assert response.status_code == 200
    assert "mode" in response.json()


def test_past_live_run_discovery_completed_vs_failed(tmp_path):
    store = GenerationStore("config/config.yaml")
    good = tmp_path / "demo_20260101_010101" / "feed_x" / "candidates"
    good.mkdir(parents=True)
    (good / "candidates.json").write_text("[]")
    (tmp_path / "demo_20260101_020202").mkdir()  # died before any feed
    (tmp_path / "not_a_demo_dir").mkdir()

    runs = {r.name: r for r in list_past_live_runs(store, root=tmp_path)}
    assert set(runs) == {"demo_20260101_010101", "demo_20260101_020202"}
    assert runs["demo_20260101_010101"].complete
    assert runs["demo_20260101_010101"].timestamp == "2026-01-01 01:01:01"
    assert runs["demo_20260101_010101"].feeds == ["feed_x"]
    assert not runs["demo_20260101_020202"].complete


def test_incomplete_live_run_refuses_to_load(tmp_path):
    store = GenerationStore("config/config.yaml")
    (tmp_path / "demo_20260101_020202").mkdir()
    with pytest.raises(RuntimeError, match="failed before producing results"):
        load_past_live_run(store, "demo_20260101_020202", root=tmp_path)
    with pytest.raises(FileNotFoundError):
        load_past_live_run(store, "demo_nonexistent", root=tmp_path)


def test_live_runs_endpoint_shape(client):
    payload = client.get("/api/demo/live-runs").json()
    assert "runs" in payload
    for run in payload["runs"]:
        assert {"name", "timestamp", "feeds", "complete"} <= set(run)


def test_replay_load_unknown_set_raises():
    store = GenerationStore("config/config.yaml")
    with pytest.raises(FileNotFoundError):
        load_replay_set(store, "no_such_set")
    with pytest.raises(FileNotFoundError):
        load_replay_set(store, "../escape")


# -- from-device uploads (POST /api/demo/upload) ------------------------------


def test_upload_rejects_bad_inputs(client):
    # A JSON that does not parse as an FRD contract is refused loudly — a
    # document with no contract stays "run the FRD→STTM agent first".
    r = client.post(
        "/api/demo/upload",
        data={"kind": "frd"},
        files={"file": ("bogus.json", b"{}", "application/json")},
    )
    assert r.status_code == 400
    assert "not a valid FRD contract" in r.json()["detail"]

    r = client.post(
        "/api/demo/upload",
        data={"kind": "nope"},
        files={"file": ("x.xlsx", b"x", "application/octet-stream")},
    )
    assert r.status_code == 400

    # An STTM upload must be a workbook.
    r = client.post(
        "/api/demo/upload",
        data={"kind": "sttm"},
        files={"file": ("mapping.csv", b"a,b", "text/csv")},
    )
    assert r.status_code == 400


def test_upload_sttm_workbook_lands_and_selects(client):
    import io

    from openpyxl import Workbook

    buf = io.BytesIO()
    Workbook().save(buf)
    name = "uploaded_test_sttm.xlsx"
    uploads = REPO / "inputs" / "uploads"
    try:
        r = client.post(
            "/api/demo/upload",
            data={"kind": "sttm"},
            files={"file": (name, buf.getvalue(), "application/octet-stream")},
        )
        assert r.status_code == 201
        assert r.json() == {"stored": name, "kind": "sttm", "selected": True}
        rows = client.get("/api/demo/workbooks").json()["workbooks"]
        mine = [w for w in rows if w["name"] == name]
        assert mine and mine[0]["selected"] and mine[0]["source"] == "inputs/uploads"
    finally:
        client.delete("/api/demo/workbook")
        _index_idle()
        (uploads / name).unlink(missing_ok=True)


def test_upload_frd_docx_lands_and_selects(client):
    """Standalone doctrine (2026-09-18): an FRD .docx is a first-class
    upload — validated as an F1/F2 document, stored, listed among the local
    FRDs and selected; a non-FRD .docx is refused loudly."""
    docx = REPO / "fixtures" / "acfc_shapes" / "frd" / "f1_pair_1.docx"
    name = "uploaded_test_FRD_pair1.docx"
    uploads = REPO / "inputs" / "uploads"
    try:
        r = client.post(
            "/api/demo/upload",
            data={"kind": "frd"},
            files={"file": (name, docx.read_bytes(),
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document")},
        )
        assert r.status_code == 201, r.text
        assert r.json() == {"stored": name, "kind": "frd", "selected": True}
        choices = client.get("/api/demo/frd-choices").json()
        assert name in choices["local"]
        assert choices["current"] == {"label": name, "chosen": True}
        assert choices["no_contract"] == []
        # Selecting a local docx by name works the same way as a contract.
        assert client.post("/api/demo/frd", json={"kind": "local", "id": name}).status_code == 200
        bogus = client.post(
            "/api/demo/upload",
            data={"kind": "frd"},
            files={"file": ("notes.docx", b"not a docx", "application/octet-stream")},
        )
        assert bogus.status_code == 400
        assert "not an F1/F2 FRD document" in bogus.json()["detail"]
    finally:
        client.delete("/api/demo/frd")
        _index_idle()
        (uploads / name).unlink(missing_ok=True)


def test_upload_frd_contract_lands_and_selects(client):
    src = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
    if not src.is_file():
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")
    # A plain .json name is normalized to .contract.json so the local scan
    # (glob *.contract.json) can see it.
    name = "uploaded_test_frd.json"
    stored = "uploaded_test_frd.contract.json"
    uploads = REPO / "inputs" / "uploads"
    try:
        r = client.post(
            "/api/demo/upload",
            data={"kind": "frd"},
            files={"file": (name, src.read_bytes(), "application/json")},
        )
        assert r.status_code == 201
        assert r.json() == {"stored": stored, "kind": "frd", "selected": True}
        choices = client.get("/api/demo/frd-choices").json()
        assert stored in choices["local"]
        assert choices["current"] == {"label": stored, "chosen": True}
    finally:
        client.delete("/api/demo/frd")
        _index_idle()
        (uploads / stored).unlink(missing_ok=True)


def test_generation_options_endpoint_offers_config_and_validates(client):
    """M6: the conventions profile / IIG template / playbook template
    selectors read their options from config; null = the config default;
    an unknown value is a 400 and changes nothing."""
    r = client.get("/api/demo/generation-options")
    assert r.status_code == 200
    body = r.json()
    assert body["conventions_profile"]["options"] == ["acfc_prx", "edo_sfmc"]
    assert body["conventions_profile"]["default"] == "edo_sfmc"
    assert body["iig_template"]["options"] == ["iig_v1", "iig_v2"]
    assert body["playbook_template"]["options"] == ["main_single", "sfmc_7sheet"]
    assert all(body[k]["selected"] is None for k in body)
    status = client.get("/api/demo/status").json()
    assert (status["conventions_profile"], status["iig_template"],
            status["playbook_template"]) == ("edo_sfmc", "iig_v1", "sfmc_7sheet")

    r = client.post("/api/demo/generation-options", json={
        "conventions_profile": "acfc_prx", "iig_template": "iig_v2",
        "playbook_template": "main_single"})
    assert r.status_code == 200
    assert r.json()["conventions_profile"]["selected"] == "acfc_prx"
    status = client.get("/api/demo/status").json()
    assert (status["conventions_profile"], status["iig_template"],
            status["playbook_template"]) == ("acfc_prx", "iig_v2", "main_single")

    r = client.post("/api/demo/generation-options", json={"iig_template": "iig_v9"})
    assert r.status_code == 400
    assert client.get("/api/demo/generation-options").json()["iig_template"]["selected"] == "iig_v2"
    # Back to defaults.
    r = client.post("/api/demo/generation-options", json={})
    assert r.status_code == 200
    assert all(v["selected"] is None for v in r.json().values())


def test_vdd_endpoints_select_and_clear(client):
    """M3/M6: the VDD chooser — any listed .xlsx becomes the third input;
    DELETE clears it; a path escape is refused."""
    r = client.post("/api/demo/vdd", json={"name": "../x.xlsx"})
    assert r.status_code == 400
    r = client.post("/api/demo/vdd", json={"name": "no_such_workbook.xlsx"})
    assert r.status_code == 404
    workbooks = client.get("/api/demo/workbooks").json()["workbooks"]
    if not workbooks:
        pytest.skip("no workbooks in the input directories")
    name = workbooks[0]["name"]
    r = client.post("/api/demo/vdd", json={"name": name})
    assert r.status_code == 200 and r.json() == {"selected": name}
    assert client.get("/api/demo/status").json()["vdd_name"] == name
    r = client.delete("/api/demo/vdd")
    assert r.status_code == 200
    assert client.get("/api/demo/status").json()["vdd_name"] is None


def test_layout_answers_accept_frd_cell_claims(client):
    """M6: an FRD question is answered with a candidate cell claim (the
    shape the merge step re-validates); a non-mapping claim is a 400."""
    r = client.post("/api/demo/layout-answers", json={
        "answers": {"frd": {"feeds[0].frequency": "Daily"}}})
    assert r.status_code == 400
    # A well-formed claim passes the shape check; with no run waiting the
    # runner refuses (409), which is the expected guard here.
    r = client.post("/api/demo/layout-answers", json={
        "answers": {"frd": {"feeds[0].frequency": {
            "table": 0, "row": 3, "col": 1, "label": "Daily", "source": "user"}}}})
    assert r.status_code == 409


def test_choosing_an_sttm_auto_pairs_its_frd(client):
    """Choosing the CV golden STTM selects its FRD contract automatically
    (unique name-stem match); clearing the STTM drops the automatic pair; a
    manual FRD pick is never marked automatic."""
    if not (REPO / "fixtures" / "workbooks" / "demo_sttm_cv_golden.xlsx").is_file():
        pytest.skip("CV golden workbook not restored")
    try:
        r = client.post("/api/demo/workbook", json={"name": "demo_sttm_cv_golden.xlsx"})
        assert r.status_code == 200
        status = client.get("/api/demo/status").json()
        assert status["frd_chosen"] is True
        assert status["frd_name"] == "FRD_demo_cv_golden.contract.json"
        assert status["frd_auto_paired"] == {"frd": "FRD_demo_cv_golden.contract.json",
                                             "rule": "name_stem"}
        assert status["frd_warning"] is False
        choices = client.get("/api/demo/frd-choices").json()
        assert choices["current"] == {"label": "FRD_demo_cv_golden.contract.json",
                                      "chosen": True}
        # A manual pick of the same file is a manual pick.
        r = client.post("/api/demo/frd", json={"kind": "local",
                                               "id": "FRD_demo_cv_golden.contract.json"})
        assert r.status_code == 200
        assert client.get("/api/demo/status").json()["frd_auto_paired"] is None
        # Re-choosing the STTM pairs again; clearing the STTM clears the pair.
        client.post("/api/demo/workbook", json={"name": "demo_sttm_cv_golden.xlsx"})
        assert client.get("/api/demo/status").json()["frd_auto_paired"] is not None
        client.delete("/api/demo/workbook")
        status = client.get("/api/demo/status").json()
        assert status["frd_chosen"] is False and status["frd_auto_paired"] is None
    finally:
        client.delete("/api/demo/workbook")
        client.delete("/api/demo/frd")


def test_choosing_an_sttm_auto_pairs_its_vdd(client):
    """A workbook whose name matches the STTM's (role tokens dropped) is
    selected as the VDD with the STTM; clearing the STTM clears it; a manual
    VDD choice is never marked automatic."""
    import io

    from openpyxl import Workbook

    if not (REPO / "fixtures" / "workbooks" / "demo_sttm_cv_golden.xlsx").is_file():
        pytest.skip("CV golden workbook not restored")
    uploads = REPO / "inputs" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    vdd = uploads / "VDD_demo_cv_golden.xlsx"
    buf = io.BytesIO()
    Workbook().save(buf)
    vdd.write_bytes(buf.getvalue())
    try:
        client.post("/api/demo/workbook", json={"name": "demo_sttm_cv_golden.xlsx"})
        status = client.get("/api/demo/status").json()
        assert status["vdd_name"] == "VDD_demo_cv_golden.xlsx"
        assert status["vdd_auto_paired"] == {"vdd": "VDD_demo_cv_golden.xlsx",
                                             "rule": "name_stem"}
        client.post("/api/demo/vdd", json={"name": "VDD_demo_cv_golden.xlsx"})
        assert client.get("/api/demo/status").json()["vdd_auto_paired"] is None
        client.post("/api/demo/workbook", json={"name": "demo_sttm_cv_golden.xlsx"})
        client.delete("/api/demo/workbook")
        status = client.get("/api/demo/status").json()
        assert status["vdd_name"] is None and status["vdd_auto_paired"] is None
    finally:
        client.delete("/api/demo/workbook")
        client.delete("/api/demo/frd")
        client.delete("/api/demo/vdd")
        _index_idle()
        vdd.unlink(missing_ok=True)


def test_output_parts_are_independent_and_empty_refuses_a_run(client, monkeypatch):
    """The Output toggles are a real multi-select: any subset, none allowed
    (run-live then 400), All its own state; the generator mode is derived."""
    try:
        r = client.post("/api/demo/output-parts", json={"parts": ["notebook", "rfc"]})
        assert r.status_code == 200
        assert r.json()["output_parts"] == ["notebook", "rfc"] and r.json()["output_mode"] == "all"
        r = client.post("/api/demo/output-parts", json={"parts": ["all"]})
        assert r.json()["output_parts"] == ["all"] and r.json()["output_mode"] == "all"
        r = client.post("/api/demo/output-parts", json={"parts": ["framework"]})
        assert r.json()["output_mode"] == "framework"
        r = client.post("/api/demo/output-parts", json={"parts": []})
        assert r.status_code == 200
        assert r.json()["output_parts"] == [] and r.json()["output_mode"] is None
        monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
        r = client.post("/api/demo/run-live", json={"confirm": True})
        assert r.status_code == 400 and "no output selected" in r.json()["detail"]
        r = client.post("/api/demo/output-parts", json={"parts": ["zip"]})
        assert r.status_code == 400
        r = client.post("/api/demo/output-parts", json={"parts": None})
        assert r.json()["output_parts"] == ["notebook"]  # config default
    finally:
        client.post("/api/demo/output-parts", json={"parts": None})

