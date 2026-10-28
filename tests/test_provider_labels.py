"""post136: the App says which provider a run uses, never the served mode in its place.

- ``/api/feeds`` ``provider``: the provider the NEXT run uses (the sidebar badge).
  The served result set's ``mode`` read "mock" after every deploy (no run
  served) while the App runs live.
- ``run_provider``: the provider the SERVED run used (the banner). A
  Generate-page run under the mock lock is mode "live" and was labelled
  "LIVE RUN" though no model was called.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("kind, provider", [("databricks_fmapi", "live"), ("anthropic", "live"),
                                            ("mock", "mock"), ("mock_locked", "mock")])
def test_the_provider_follows_the_transport_a_run_would_use(kind, provider, monkeypatch):
    from ui.backend.service import provider_of

    from codegen.reasoning import transport

    monkeypatch.setattr(transport, "resolve_transport", lambda _config: SimpleNamespace(kind=kind))
    assert provider_of(None) == provider


def _feeds(store, monkeypatch) -> dict:
    pytest.importorskip("httpx")
    pytest.importorskip("fastapi")   # the ui extra (absent in the D1 venv)
    from fastapi.testclient import TestClient
    from ui.backend import main

    monkeypatch.setattr(main, "store", store)
    return TestClient(main.app).get("/api/feeds").json()


def test_with_no_run_served_the_badge_still_names_the_live_provider(monkeypatch):
    pytest.importorskip("fastapi")
    from ui.backend import main
    from ui.backend.service import GenerationStore

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    monkeypatch.setattr(main, "provider_of", lambda _config: "live")
    body = _feeds(store, monkeypatch)
    assert body["mode"] == "mock"             # nothing served: the behaviour value
    assert body["provider"] == "live"         # what the badge says
    assert body["run_provider"] is None


def test_a_served_run_carries_the_provider_that_answered_it(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from ui.backend.service import GenerationStore

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    store.adopt({}, [], mode="live", label="demo_x", out_root=tmp_path, reports_root=tmp_path,
                run_provider="mock")
    body = _feeds(store, monkeypatch)
    assert (body["mode"], body["run_provider"]) == ("live", "mock")
    # forgetting the run forgets its provider too
    assert store.forget_runs(["demo_x"])
    assert store.run_provider is None


def test_a_provider_that_cannot_resolve_never_breaks_the_feeds_route(monkeypatch):
    """The badge is a label: /api/feeds (every page reads it) still answers."""
    pytest.importorskip("fastapi")
    from ui.backend import main
    from ui.backend.service import GenerationStore

    def boom(_config):
        raise AttributeError("no reasoning section")

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    monkeypatch.setattr(main, "provider_of", boom)
    body = _feeds(store, monkeypatch)
    assert body["provider"] is None and body["feeds"] == []
