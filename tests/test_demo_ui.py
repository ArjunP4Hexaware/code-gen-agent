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
    assert client.get("/api/demo/live-available").json() == {
        "available": False, "provider": "anthropic",
        "reason": "no ANTHROPIC_API_KEY in the backend env",
    }
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-echoed")
    payload = client.get("/api/demo/live-available").json()
    assert payload == {"available": True, "provider": "anthropic", "reason": ""}
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
    assert payload == {"available": True, "provider": "databricks_fmapi", "reason": ""}


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
        (uploads / stored).unlink(missing_ok=True)
