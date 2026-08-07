"""Demo-mode backend: replay discovery/loading, live-run guardrails.

Needs the [ui] extra (fastapi); skipped cleanly when it isn't installed so
the core generator suite stays offline-and-extra-free.
"""

from __future__ import annotations

import threading
import time

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend.demo import DemoRunner, LiveRunInProgress  # noqa: E402
from ui.backend.replay import list_replay_sets, load_replay_set  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

REPLAY_SET = "live_e2e_20260807"


@pytest.fixture()
def client(monkeypatch):
    # No key in the test process: live must read as unavailable by default
    # and nothing can ever fire a billed call from the suite.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ui.backend import main

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
    assert client.get("/api/demo/live-available").json() == {"available": False}
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-echoed")
    payload = client.get("/api/demo/live-available").json()
    assert payload == {"available": True}
    assert "test-key-never-echoed" not in payload.get("available", True).__repr__()


def test_replay_discovery_finds_tracked_set():
    sets = {s.name: s for s in list_replay_sets()}
    assert REPLAY_SET in sets
    tracked = sets[REPLAY_SET]
    assert tracked.date == "2026-08-07"
    assert tracked.has_call_log
    assert len(tracked.feeds) == 3


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


def test_replay_load_unknown_set_raises():
    store = GenerationStore("config/config.yaml")
    with pytest.raises(FileNotFoundError):
        load_replay_set(store, "no_such_set")
    with pytest.raises(FileNotFoundError):
        load_replay_set(store, "../escape")
