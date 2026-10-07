"""GET /api/health's storage-root probe (2026-10-07): when the documents
panel lists nothing, the screen says which env var or which grant is
missing. Fake workspace: unset / refused (not found, permission denied) /
empty / readable."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from storage_fakes import FakeWorkspaceClient, PermissionDenied

REPO = Path(__file__).resolve().parents[1]
PRINCIPAL = "codegen-app-sp (app-id-123)"


def _probe(env: dict, client):
    from ui.backend.health import probe_roots

    return {(r["env"], r["value"]): r
            for r in probe_roots(REPO, env=env, client_factory=lambda: client,
                                 principal=PRINCIPAL, timeout=5.0)["roots"]}


@pytest.fixture
def fake():
    client = FakeWorkspaceClient()
    client.ws.dirs.update({"/Users/u/shared/pairs", "/Users/u/shared/pairs/pair_1",
                           "/Users/u/shared/state"})
    client.ws.files["/Users/u/shared/pairs/pair_1/STTM_x.xlsx"] = b"x"
    return client


def test_unset_roots_say_so(fake):
    rows = _probe({}, fake)
    assert {env for env, _ in rows} == {"CODEGEN_EXTRA_INPUT_DIRS", "CODEGEN_STORAGE_INPUTS",
                                        "CODEGEN_STORAGE_STATE", "CODEGEN_STORAGE_OUTPUTS"}
    assert all(r["state"] == "unset" and r["value"] is None for r in rows.values())


def test_readable_empty_and_refused(fake):
    env = {"CODEGEN_EXTRA_INPUT_DIRS": "workspace:/Workspace/Users/u/shared/pairs;"
                                       "/Workspace/Users/u/not_shared/pairs",
           "CODEGEN_STORAGE_STATE": "workspace:/Workspace/Users/u/shared/state",
           "CODEGEN_STORAGE_OUTPUTS": "workspace:/Workspace/Users/u/gone/outputs"}
    rows = _probe(env, fake)
    ok = rows[("CODEGEN_EXTRA_INPUT_DIRS", "workspace:/Workspace/Users/u/shared/pairs")]
    assert ok["state"] == "readable" and "1 entry" in ok["detail"]
    refused = rows[("CODEGEN_EXTRA_INPUT_DIRS", "workspace:/Workspace/Users/u/not_shared/pairs")]
    assert refused["state"] == "not_shared"                 # a bare /Workspace path is read too
    assert PRINCIPAL in refused["detail"] and "Can Read" in refused["detail"]
    empty = rows[("CODEGEN_STORAGE_STATE", "workspace:/Workspace/Users/u/shared/state")]
    assert empty["state"] == "empty"
    gone = rows[("CODEGEN_STORAGE_OUTPUTS", "workspace:/Workspace/Users/u/gone/outputs")]
    assert gone["state"] == "not_shared" and "Can Manage" in gone["detail"]
    assert rows[("CODEGEN_STORAGE_INPUTS", None)]["state"] == "unset"
    assert {c[0] for c in fake.ws.calls} <= {"list", "get_status"}   # read-only


def test_permission_denied_is_not_shared_and_a_bad_uri_is_invalid(fake):
    def denied(path):
        raise PermissionDenied(f"User does not have READ on {path}")

    fake.workspace = SimpleNamespace(**{**vars(fake.workspace), "list": denied})
    rows = _probe({"CODEGEN_STORAGE_INPUTS": "workspace:/Workspace/Users/u/shared/pairs",
                   "CODEGEN_STORAGE_STATE": "ftp:/nowhere"}, fake)
    assert rows[("CODEGEN_STORAGE_INPUTS", "workspace:/Workspace/Users/u/shared/pairs")][
        "state"] == "not_shared"
    assert rows[("CODEGEN_STORAGE_STATE", "ftp:/nowhere")]["state"] == "invalid"


def test_principal_name_comes_from_the_workspace_identity(monkeypatch):
    from ui.backend.health import app_principal

    me = SimpleNamespace(display_name="codegen-app-sp", user_name="app-id-123")
    client = SimpleNamespace(current_user=SimpleNamespace(me=lambda: me))
    monkeypatch.setenv("DATABRICKS_HOST", "https://example.invalid")
    assert app_principal(lambda: client) == "codegen-app-sp (app-id-123)"
    monkeypatch.delenv("DATABRICKS_HOST")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "app-id-123")
    assert app_principal(None) == "the App's service principal (app-id-123)"
    monkeypatch.delenv("DATABRICKS_CLIENT_ID")
    assert "not running as a Databricks App" in app_principal(None)


def test_health_route_carries_the_roots(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from ui.backend import main

    for name in ("CODEGEN_EXTRA_INPUT_DIRS", "CODEGEN_STORAGE_INPUTS", "CODEGEN_STORAGE_STATE",
                 "CODEGEN_STORAGE_OUTPUTS"):
        monkeypatch.delenv(name, raising=False)
    body = TestClient(main.app).get("/api/health").json()
    assert {"status", "startup_error", "principal", "roots"} <= set(body)
    assert [r["env"] for r in body["roots"]] == ["CODEGEN_EXTRA_INPUT_DIRS",
                                                 "CODEGEN_STORAGE_INPUTS",
                                                 "CODEGEN_STORAGE_STATE",
                                                 "CODEGEN_STORAGE_OUTPUTS"]
