"""codegen.databricks: config resolution, listing/fetch via a stubbed SDK.

The volumes transport seam. Nothing here opens a socket: the SDK client is
stubbed the way test_anthropic_provider stubs `anthropic`, and one test
proves the module imports and resolves config with zero environment.
"""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

import codegen.databricks as db


def _settings(**overrides):
    values = {
        "profile": "DEFAULT",
        "schema_name": "codegen_agent",
        "catalog": "soham_workspace",
        "frd_volume": "frd_raw",
        "sttm_volume": "sttm_raw",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_module_imports_and_fails_loud_with_zero_env():
    with pytest.raises(db.DatabricksConfigError) as excinfo:
        db.config_for(None, env={})
    message = str(excinfo.value)
    assert "databricks:" in message and "DATABRICKS_PROFILE" in message


def test_config_from_settings_and_env_precedence():
    cfg = db.config_for(_settings(), env={})
    assert cfg.catalog == "soham_workspace"
    assert cfg.schema == "codegen_agent"
    cfg = db.config_for(_settings(), env={"DATABRICKS_CATALOG": "other_cat"})
    assert cfg.catalog == "other_cat"  # env > YAML


def test_partial_config_names_the_missing_knobs():
    with pytest.raises(db.DatabricksConfigError, match="sttm_volume"):
        db.config_for(_settings(sttm_volume=""), env={})


def test_tracked_config_section_resolves(config):
    cfg = db.config_for(config.databricks, env={})
    assert cfg.frd_volume == "frd_raw" and cfg.sttm_volume == "sttm_raw"


class _StubFiles:
    def __init__(self, listings=None, payload=b"", raises=None):
        self.listings = listings or {}
        self.payload = payload
        self.raises = raises

    def list_directory_contents(self, path):
        if self.raises:
            raise self.raises
        return self.listings.get(path, [])

    def download(self, path):
        if self.raises:
            raise self.raises
        return SimpleNamespace(contents=io.BytesIO(self.payload))


def _entry(name, size=10, directory=False):
    return SimpleNamespace(name=name, file_size=size, is_directory=directory)


def test_list_documents_filters_and_sorts():
    cfg = db.config_for(_settings(), env={})
    client = SimpleNamespace(files=_StubFiles(listings={
        db.volume_path(cfg, "frd_raw"): [
            _entry("Zebra FRD.docx"), _entry("alpha frd.docx"),
            _entry("notes.txt"), _entry("subdir", directory=True),
        ],
        db.volume_path(cfg, "sttm_raw"): [_entry("map.xlsx")],
    }))
    listing = db.list_documents(cfg, client=client)
    assert [f["name"] for f in listing["frd"]] == ["alpha frd.docx", "Zebra FRD.docx"]
    assert [f["name"] for f in listing["sttm"]] == ["map.xlsx"]


def test_list_documents_surfaces_failures():
    cfg = db.config_for(_settings(), env={})
    client = SimpleNamespace(files=_StubFiles(raises=RuntimeError("no grant")))
    with pytest.raises(db.DatabricksTransportError, match="no grant"):
        db.list_documents(cfg, client=client)


def test_fetch_document_writes_atomically(tmp_path):
    cfg = db.config_for(_settings(), env={})
    client = SimpleNamespace(files=_StubFiles(payload=b"workbook-bytes"))
    local = db.fetch_document(cfg, "sttm_raw", "map.xlsx", tmp_path, client=client)
    assert local == tmp_path / "map.xlsx"
    assert local.read_bytes() == b"workbook-bytes"
    assert not list(tmp_path.glob("*.part"))


def test_fetch_document_rejects_bad_names(tmp_path):
    cfg = db.config_for(_settings(), env={})
    for bad in ("../escape.xlsx", "a/b.xlsx", ".hidden.xlsx", "script.py"):
        with pytest.raises(db.DatabricksTransportError):
            db.fetch_document(cfg, "sttm_raw", bad, tmp_path, client=object())


def test_fetch_document_cleans_up_part_file_on_failure(tmp_path):
    cfg = db.config_for(_settings(), env={})
    client = SimpleNamespace(files=_StubFiles(raises=RuntimeError("cut off")))
    with pytest.raises(db.DatabricksTransportError, match="cut off"):
        db.fetch_document(cfg, "frd_raw", "frd.docx", tmp_path, client=client)
    assert list(tmp_path.iterdir()) == []


# -- B1 surface: catalog reads, EXPLAIN, job read, chat (all stubbed) ---------- #


def test_profile_resolution_and_optional_b1_knobs():
    # Profile always resolves: env DATABRICKS_PROFILE > DATABRICKS_CONFIG_PROFILE
    # > YAML > DEFAULT; the B1 knobs stay optional at config time.
    cfg = db.config_for(_settings(profile=""), env={})
    assert cfg.profile == "DEFAULT"
    cfg = db.config_for(_settings(profile=""), env={"DATABRICKS_CONFIG_PROFILE": "WORK"})
    assert cfg.profile == "WORK"
    assert cfg.warehouse_id == "" and cfg.serving_endpoint == ""


def test_explain_and_chat_raise_named_errors_when_unconfigured():
    cfg = db.config_for(_settings(), env={})
    with pytest.raises(db.DatabricksConfigError, match="warehouse_id"):
        db.explain(cfg, "SELECT 1", client=object())
    with pytest.raises(db.DatabricksConfigError, match="serving_endpoint"):
        db.chat(cfg, [{"role": "user", "content": "x"}], client=object())


class _StubTables:
    def __init__(self, table=None, raises=None):
        self.table, self.raises = table, raises

    def get(self, full_name):
        if self.raises:
            raise self.raises
        return self.table


def _table(full_name="c.s.t", columns=(), properties=None):
    return SimpleNamespace(
        full_name=full_name,
        table_type=SimpleNamespace(value="MANAGED"),
        columns=[SimpleNamespace(name=n, type_text=t) for n, t in columns],
        properties=properties or {},
    )


def test_table_exists_and_describe_and_properties():
    cfg = db.config_for(_settings(), env={})
    table = _table(columns=(("id", "string"), ("amount", "double")),
                   properties={"delta.enableChangeDataFeed": "true"})
    client = SimpleNamespace(tables=_StubTables(table=table))
    assert db.table_exists(cfg, "c.s.t", client=client) is True
    described = db.describe_table(cfg, "c.s.t", client=client)
    assert described["columns"] == [{"name": "id", "type": "string"},
                                    {"name": "amount", "type": "double"}]
    assert db.table_properties(cfg, "c.s.t", client=client) == {
        "delta.enableChangeDataFeed": "true"
    }
    missing = SimpleNamespace(tables=_StubTables(
        raises=RuntimeError("TABLE_DOES_NOT_EXIST: does not exist")))
    assert db.table_exists(cfg, "c.s.nope", client=missing) is False
    denied = SimpleNamespace(tables=_StubTables(raises=RuntimeError("PERMISSION_DENIED")))
    with pytest.raises(db.DatabricksTransportError, match="PERMISSION_DENIED"):
        db.table_exists(cfg, "c.s.t", client=denied)


def test_explain_prefixes_and_returns_plan():
    cfg = db.config_for(_settings(warehouse_id="wh123"), env={})
    captured = {}

    def execute_statement(statement, warehouse_id, wait_timeout):
        captured.update(statement=statement, warehouse_id=warehouse_id)
        return SimpleNamespace(
            status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED"), error=None),
            result=SimpleNamespace(data_array=[["== Physical Plan =="], ["Scan t"]]),
        )

    client = SimpleNamespace(
        statement_execution=SimpleNamespace(execute_statement=execute_statement)
    )
    plan = db.explain(cfg, "SELECT * FROM t;", client=client)
    # Never executed as written: the statement is EXPLAIN-prefixed.
    assert captured["statement"] == "EXPLAIN SELECT * FROM t"
    assert captured["warehouse_id"] == "wh123"
    assert "Physical Plan" in plan


def test_explain_surfaces_failure_state():
    cfg = db.config_for(_settings(warehouse_id="wh123"), env={})
    client = SimpleNamespace(statement_execution=SimpleNamespace(
        execute_statement=lambda **_: SimpleNamespace(
            status=SimpleNamespace(state=SimpleNamespace(value="FAILED"),
                                   error=SimpleNamespace(message="syntax error")),
            result=None,
        )
    ))
    with pytest.raises(db.DatabricksTransportError, match="syntax error"):
        db.explain(cfg, "EXPLAIN SELECT nope", client=client)


def test_get_job_reads_settings_only():
    cfg = db.config_for(_settings(), env={})
    job = SimpleNamespace(
        job_id=42,
        settings=SimpleNamespace(
            name="wrapper",
            tasks=[SimpleNamespace(task_key="run_wrapper")],
            parameters=[SimpleNamespace(name="object_id")],
        ),
    )
    client = SimpleNamespace(jobs=SimpleNamespace(get=lambda job_id: job))
    assert db.get_job(cfg, 42, client=client) == {
        "job_id": 42, "name": "wrapper",
        "tasks": ["run_wrapper"], "parameters": ["object_id"],
    }


def test_chat_uses_endpoint_and_returns_content():
    cfg = db.config_for(_settings(serving_endpoint="databricks-claude-opus-4-8"),
                        env={})
    captured = {}

    def query(name, messages, max_tokens):
        captured.update(name=name, count=len(messages), max_tokens=max_tokens)
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="hello"))])

    client = SimpleNamespace(serving_endpoints=SimpleNamespace(query=query))
    text = db.chat(cfg, [{"role": "user", "content": "hi"}], max_tokens=50,
                   client=client)
    assert text == "hello"
    assert captured == {"name": "databricks-claude-opus-4-8", "count": 1,
                        "max_tokens": 50}


def test_no_write_shaped_api_exists():
    # The governance "never writes back" control introspects for these; the
    # suite enforces the same invariant directly.
    forbidden = ("execute", "create_job", "run_now", "upload", "write", "put")
    exported = [n for n in dir(db) if not n.startswith("_")]
    offenders = [n for n in exported
                 if any(w == n.lower() or n.lower().startswith(w) for w in forbidden)]
    assert offenders == []


# -- routes (offline: transport monkeypatched at the routes seam) -------------- #

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import databricks_routes  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(ui_main.app)


def test_documents_route_unconfigured_is_503(client, monkeypatch):
    store = ui_main._require_store()
    from codegen.config import DatabricksSettings

    monkeypatch.setattr(
        store, "config",
        store.config.model_copy(update={"databricks": DatabricksSettings()}),
    )
    response = client.get("/api/databricks/documents")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_documents_and_fetch_routes_with_stubbed_transport(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        databricks_routes, "list_documents",
        lambda cfg: {"frd": [], "sttm": [{"name": "map.xlsx", "size": 5,
                                          "volume": "sttm_raw"}]},
    )
    payload = client.get("/api/databricks/documents").json()
    assert payload["catalog"] == "soham_workspace"
    assert payload["documents"]["sttm"][0]["name"] == "map.xlsx"

    fetched = {}

    def fake_fetch(cfg, volume, name, dest):
        fetched["args"] = (volume, name, dest)
        return tmp_path / name

    monkeypatch.setattr(databricks_routes, "FETCH_DIR", tmp_path)
    monkeypatch.setattr(databricks_routes, "fetch_document", fake_fetch)
    response = client.post(
        "/api/databricks/fetch", json={"volume": "sttm_raw", "name": "map.xlsx"}
    )
    assert response.json() == {"fetched": "map.xlsx", "dest": "inputs/databricks"}
    assert fetched["args"] == ("sttm_raw", "map.xlsx", tmp_path)

    response = client.post(
        "/api/databricks/fetch", json={"volume": "nope", "name": "map.xlsx"}
    )
    assert response.status_code == 400
