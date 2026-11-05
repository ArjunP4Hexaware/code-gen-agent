"""post174: the App side of proposed vocabulary (docs/PARSER_SELF_EXTENSION.md step 2).

A run with answers records the labels they prove (shared state root); GET
/api/vocabulary lists them; Approve / Reject only on the dev App (Soham: the primary App,
CODEGEN_STORAGE_PRIMARY_APP) - the staging App reads them, a decision there is 403."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

CELL = {"kind": "multiline", "table": 6, "row": 4, "col": 2, "label": "Object/data Format",
        "text": "Kind Of File: .txt\nSeparator: Pipe Delimited"}


@pytest.fixture()
def state(monkeypatch, tmp_path):
    root = tmp_path / "codegen-state"
    root.mkdir()
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(root))
    return root


def _record_from_a_run(state, tmp_path):
    """The runner's hook, as a run with the person's file-format answer calls it."""
    from ui.backend.demo import DemoRunner

    from codegen.config import load_config

    frd = tmp_path / "frd.contract.json"
    frd.write_text(json.dumps({"structured": {"feeds[0].file_format": CELL}}),
                   encoding="utf-8")
    runner = DemoRunner.__new__(DemoRunner)            # the hook only, no store / thread
    runner.last_answers = {"gaps": {"feeds[0].file_format": {"value": "txt"}}}
    runner.stages = []
    config = load_config("config/config.yaml")
    DemoRunner._propose_vocabulary(runner, frd, "demo_20261105_120000", config)
    return runner


def test_a_run_with_answers_records_the_proposal(state, tmp_path):
    runner = _record_from_a_run(state, tmp_path)
    data = json.loads((state / "vocabulary" / "proposals.json").read_text(encoding="utf-8"))
    (proposal,) = data["proposals"]
    assert (proposal["field"], proposal["label"]) == ("file_format", "Kind Of File")
    assert any(s["stage"] == "vocabulary" for s in runner.stages)


def _client(monkeypatch, app_name: str | None):
    from ui.backend import main

    monkeypatch.setenv("CODEGEN_STORAGE_PRIMARY_APP", "codegen-agent")
    if app_name is None:
        monkeypatch.delenv("DATABRICKS_APP_NAME", raising=False)
    else:
        monkeypatch.setenv("DATABRICKS_APP_NAME", app_name)
    return TestClient(main.app)


def test_staging_lists_but_cannot_decide(state, tmp_path, monkeypatch):
    _record_from_a_run(state, tmp_path)
    client = _client(monkeypatch, "codegen-agent-staging")
    body = client.get("/api/vocabulary").json()
    assert body["can_decide"] is False and len(body["proposals"]) == 1
    pid = body["proposals"][0]["id"]
    assert client.post(f"/api/vocabulary/{pid}/approve").status_code == 403
    assert len(client.get("/api/vocabulary").json()["proposals"]) == 1    # unchanged


def test_the_dev_app_approves_and_the_next_config_reads_the_label(state, tmp_path,
                                                                  monkeypatch):
    from codegen.config import load_config

    _record_from_a_run(state, tmp_path)
    client = _client(monkeypatch, "codegen-agent")
    pid = client.get("/api/vocabulary").json()["proposals"][0]["id"]
    body = client.post(f"/api/vocabulary/{pid}/approve").json()
    assert body["proposals"] == [] and body["approved"] == {"file_format": ["Kind Of File"]}
    labels = load_config("config/config.yaml").extractor.frd.cell_line_labels
    assert "Kind Of File" in labels["file_format"]
    assert client.post(f"/api/vocabulary/{pid}/approve").status_code == 404   # done
    assert client.post(f"/api/vocabulary/{pid}/maybe").status_code == 404


def test_a_local_server_may_decide(state, monkeypatch):
    assert _client(monkeypatch, None).get("/api/vocabulary").json()["can_decide"] is True


def test_no_answers_no_proposal(state, tmp_path):
    from ui.backend.demo import DemoRunner

    from codegen.config import load_config

    runner = SimpleNamespace(last_answers={}, stages=[])
    DemoRunner._propose_vocabulary(runner, tmp_path / "absent.json", "r",
                                   load_config("config/config.yaml"))
    assert not (state / "vocabulary").exists()
