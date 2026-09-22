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


def test_tracked_config_ships_the_document_volumes_off(config):
    """The volumes named the Hexaware build workspace's own document volumes;
    inside ACFC the App listed / fetched from them. They ship blank: the
    volumes seam is off, the model endpoint still resolves."""
    with pytest.raises(db.DatabricksConfigError, match="not configured"):
        db.config_for(config.databricks, env={})
    cfg = db.config_for(config.databricks, env={}, require=())
    assert cfg.serving_endpoint == "databricks-claude-opus-5"
    # A machine that HAS such volumes opts in through its environment.
    opted = db.config_for(config.databricks, env=VOLUMES_ENV)
    assert (opted.catalog, opted.frd_volume) == ("soham_workspace", "frd_raw")


# The Hexaware desktop's volumes, set as env (the opt-in the tracked config
# no longer carries).
VOLUMES_ENV = {"DATABRICKS_CATALOG": "soham_workspace", "DATABRICKS_SCHEMA": "codegen_agent",
               "DATABRICKS_FRD_VOLUME": "frd_raw", "DATABRICKS_STTM_VOLUME": "sttm_raw"}


@pytest.fixture()
def volumes_env(monkeypatch):
    for name, value in VOLUMES_ENV.items():
        monkeypatch.setenv(name, value)


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


def test_client_construction_failure_is_a_transport_error(monkeypatch):
    # The SDK's WorkspaceClient constructor raises when auth cannot resolve
    # (expired CLI refresh token, unresolvable App credentials). That must
    # surface as the seam's own error — before this, it escaped list/fetch/
    # chat as a bare exception and the UI hid the resulting 500.
    import sys
    import types

    class _Boom:
        def __init__(self, *args, **kwargs):
            raise ValueError("default auth: cannot get access token")

    sdk = types.ModuleType("databricks.sdk")
    sdk.WorkspaceClient = _Boom
    root = types.ModuleType("databricks")
    root.sdk = sdk
    monkeypatch.setitem(sys.modules, "databricks", root)
    monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)

    cfg = db.config_for(_settings(), env={})
    with pytest.raises(db.DatabricksTransportError) as excinfo:
        db.list_documents(cfg)
    message = str(excinfo.value)
    assert "profile 'DEFAULT'" in message and "cannot get access token" in message

    # Same shape under the Apps runtime (env-injected credentials).
    monkeypatch.setenv("DATABRICKS_HOST", "https://example.invalid")
    with pytest.raises(db.DatabricksTransportError) as excinfo:
        db.chat(cfg, [{"role": "user", "content": "x"}], endpoint="ep")
    assert "injected app credentials" in str(excinfo.value)


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


# Recorded 2026-08-31 from the live serving endpoint (probe call, synthetic
# prompt/reply, signature truncated): extended-thinking Claude models return
# content as a LIST of typed blocks, not a string — the shape behind the
# demo_20260831_212539 run's "'list' object has no attribute 'strip'"
# provider failures.
_RECORDED_BLOCK_CONTENT = [
    {
        "type": "reasoning",
        "summary": [{"type": "summary_text", "text": "", "signature": "CAISoQIK"}],
    },
    {"type": "text", "text": "pong"},
]


def test_chat_joins_list_of_content_blocks():
    cfg = db.config_for(_settings(serving_endpoint="databricks-claude-opus-4-8"),
                        env={})

    def query(name, messages, max_tokens):
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content=_RECORDED_BLOCK_CONTENT))])

    client = SimpleNamespace(serving_endpoints=SimpleNamespace(query=query))
    text = db.chat(cfg, [{"role": "user", "content": "hi"}], client=client)
    assert text == "pong"  # reasoning block ignored, text block kept


def test_chat_content_text_handles_every_shape():
    assert db._chat_content_text(None) == ""
    assert db._chat_content_text("plain") == "plain"
    assert db._chat_content_text(_RECORDED_BLOCK_CONTENT) == "pong"
    # multiple text blocks join; stray plain strings in the list survive
    assert db._chat_content_text(
        [{"type": "text", "text": "a"}, "b", {"type": "tool_use"}]
    ) == "ab"
    with pytest.raises(db.DatabricksTransportError):
        db._chat_content_text(42)


def test_write_surface_is_exactly_the_sanctioned_set():
    # The governance "never writes back" control introspects for these; the
    # suite enforces the same invariant directly. The sanctioned write
    # surfaces are the landing seeder ({ensure_volume, upload_file},
    # 2026-08-27) and the human-gated publish ({publish_artifacts},
    # 2026-08-28), all guarded by WRITABLE_PREFIX;
    # execute/create_job/run_now/deletes remain forbidden absolutely.
    forbidden = ("execute", "create_job", "run_now", "delete", "remove")
    exported = [n for n in dir(db) if not n.startswith("_")]
    offenders = [n for n in exported
                 if any(w == n.lower() or n.lower().startswith(w) for w in forbidden)]
    assert offenders == []
    write_shaped = {n for n in exported
                    if any(w in n.lower() for w in ("upload", "write", "put", "publish"))
                    and n != "WRITABLE_PREFIX"}
    assert write_shaped == {"upload_file", "publish_artifacts"}
    assert db.WRITABLE_PREFIX == "soham_workspace.codegen_agent."


# -- routes (offline: transport monkeypatched at the routes seam) -------------- #

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import databricks_routes  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(ui_main.app)


def test_documents_route_unconfigured_is_503(client, monkeypatch):
    for name in VOLUMES_ENV:
        monkeypatch.delenv(name, raising=False)
    # As shipped: the chooser's Databricks section is absent (503), and no
    # workspace client is ever built for it.
    monkeypatch.setattr(db, "_client", lambda _cfg: pytest.fail("a client was built"))
    assert client.get("/api/databricks/documents").status_code == 503
    store = ui_main._require_store()
    from codegen.config import DatabricksSettings

    monkeypatch.setattr(
        store, "config",
        store.config.model_copy(update={"databricks": DatabricksSettings()}),
    )
    response = client.get("/api/databricks/documents")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_documents_route_workspace_refusal_is_502_with_message(client, volumes_env, monkeypatch):
    # A refused/unauthenticated workspace is NOT "unconfigured": the UI shows
    # the message (and a Retry) instead of hiding the section.
    def refuse(_cfg):
        raise db.DatabricksTransportError(
            "workspace auth via profile 'DEFAULT' failed: refresh token is invalid"
        )

    monkeypatch.setattr(databricks_routes, "list_documents", refuse)
    response = client.get("/api/databricks/documents")
    assert response.status_code == 502
    assert "refresh token is invalid" in response.json()["detail"]


def test_documents_and_fetch_routes_with_stubbed_transport(client, volumes_env, monkeypatch,
                                                           tmp_path):
    monkeypatch.setattr(
        databricks_routes, "list_documents",
        lambda cfg: {"frd": [], "sttm": [{"name": "map.xlsx", "size": 5,
                                          "volume": "sttm_raw"}]},
    )
    monkeypatch.setattr(databricks_routes, "FETCH_DIR", tmp_path / "none")
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


def test_documents_route_dedupe_states_and_pairing(client, volumes_env, monkeypatch, tmp_path):
    """fetched (same size) / differs (size mismatch) / fetchable, matched via
    the shared canonical name (upload prefix + copy suffix + case); the
    1005034 pair is annotated, the unpaired STTM is not."""
    monkeypatch.setattr(databricks_routes, "FETCH_DIR", tmp_path)
    (tmp_path / "STTM_A_1005034 (1).xlsx").write_bytes(b"12345")       # 5 bytes
    (tmp_path / "999_sttm_b.XLSX").write_bytes(b"different-content")   # != 5

    monkeypatch.setattr(
        databricks_routes, "list_documents",
        lambda cfg: {
            "sttm": [
                {"name": "STTM_A_1005034 (1).xlsx", "size": 5, "volume": "sttm_raw"},
                {"name": "STTM_B.xlsx", "size": 5, "volume": "sttm_raw"},
                {"name": "STTM_C_new.xlsx", "size": 7, "volume": "sttm_raw"},
            ],
            "frd": [
                {"name": "FRD_A_1005034.docx", "size": 9, "volume": "frd_raw"},
                {"name": "FRD_unrelated.docx", "size": 9, "volume": "frd_raw"},
            ],
        },
    )
    payload = client.get("/api/databricks/documents").json()
    sttm = {e["name"]: e for e in payload["documents"]["sttm"]}
    frd = {e["name"]: e for e in payload["documents"]["frd"]}

    assert sttm["STTM_A_1005034 (1).xlsx"]["state"] == "fetched"
    assert sttm["STTM_A_1005034 (1).xlsx"]["local_name"] == "STTM_A_1005034 (1).xlsx"
    assert sttm["STTM_B.xlsx"]["state"] == "differs"       # matched 999_sttm_b.XLSX
    assert sttm["STTM_B.xlsx"]["local_name"] == "999_sttm_b.XLSX"
    assert sttm["STTM_C_new.xlsx"]["state"] == "fetchable"

    assert sttm["STTM_A_1005034 (1).xlsx"]["companion_frd"] == "FRD_A_1005034.docx"
    assert "companion_frd" not in sttm["STTM_B.xlsx"]
    assert frd["FRD_A_1005034.docx"]["paired"] is True
    assert frd["FRD_unrelated.docx"]["paired"] is False
    assert frd["FRD_A_1005034.docx"]["state"] == "fetchable"


# -- publish (the human-gated outbound half, added 2026-08-28) ---------------- #


class _StubPublishClient:
    """volumes.read/create + files.upload, recording every call."""

    def __init__(self, volume_exists=True, existing=()):
        self.uploads = []
        self.created = []
        self._exists = volume_exists

        outer = self

        class _Volumes:
            def read(self, full_name):
                if not outer._exists:
                    raise RuntimeError(f"{full_name} does not exist")
                return SimpleNamespace(full_name=full_name)

            def create(self, **kwargs):
                outer.created.append(kwargs)
                outer._exists = True

        class _Files:
            def upload(self, path, data, overwrite=False):
                outer.uploads.append((path, data.read(), overwrite))

        self.volumes = _Volumes()
        self.files = _Files()


def _publish_cfg():
    return db.config_for(
        _settings(landing_volume="mftlanding", output_volume="generated"),
        env={},
    )


def test_publish_artifacts_targets_per_feed_directory(tmp_path):
    cfg = _publish_cfg()
    report = tmp_path / "cv_feed.md"
    report.write_bytes(b"# report")
    notebook = tmp_path / "cv_feed.ipynb"
    notebook.write_bytes(b"{}")
    client = _StubPublishClient()
    published = db.publish_artifacts(cfg, "cv_feed", [report, notebook],
                                     client=client)
    assert [p[0] for p in client.uploads] == [
        "/Volumes/soham_workspace/codegen_agent/generated/cv_feed/cv_feed.md",
        "/Volumes/soham_workspace/codegen_agent/generated/cv_feed/cv_feed.ipynb",
    ]
    assert published[0]["size_bytes"] == 8
    assert all(p[2] is False for p in client.uploads)  # no silent overwrite


def test_publish_refuses_targets_outside_writable_prefix(tmp_path):
    cfg = _publish_cfg()
    artifact = tmp_path / "a.md"
    artifact.write_bytes(b"x")
    with pytest.raises(db.DatabricksConfigError, match="only writable location"):
        db.publish_artifacts(cfg, "feed", [artifact], catalog="client_prod",
                             client=_StubPublishClient())
    with pytest.raises(db.DatabricksConfigError, match="only writable location"):
        db.publish_artifacts(cfg, "feed", [artifact], schema="other_schema",
                             client=_StubPublishClient())


def test_publish_refuses_bad_slug_and_missing_volume(tmp_path):
    cfg = _publish_cfg()
    artifact = tmp_path / "a.md"
    artifact.write_bytes(b"x")
    with pytest.raises(db.DatabricksTransportError, match="invalid feed slug"):
        db.publish_artifacts(cfg, "../escape", [artifact],
                             client=_StubPublishClient())
    bare = db.config_for(_settings(), env={})
    with pytest.raises(db.DatabricksConfigError, match="output_volume"):
        db.publish_artifacts(bare, "feed", [artifact],
                             client=_StubPublishClient())


def test_ensure_volume_generalizes_to_output_volume():
    cfg = _publish_cfg()
    client = _StubPublishClient(volume_exists=False)
    result = db.ensure_volume(cfg, client=client, volume="generated",
                              knob="output_volume")
    assert result == {"full_name": "soham_workspace.codegen_agent.generated",
                      "created": True}
    assert client.created[0]["name"] == "generated"


def test_publish_target_route_reports_defaults(client, volumes_env, monkeypatch):
    payload = client.get("/api/databricks/publish-target").json()
    assert payload["available"] is True
    assert payload["writable_prefix"] == "soham_workspace.codegen_agent."
    assert payload["volume"] == "generated"


def test_publish_route_requires_confirm(client):
    response = client.post("/api/databricks/publish",
                           json={"feed_slug": "x", "confirm": False})
    assert response.status_code == 400
    assert "confirm" in response.json()["detail"]


def test_publish_route_with_stubbed_transport(client, volumes_env, monkeypatch, tmp_path):
    store = ui_main._require_store()
    (tmp_path / "reports").mkdir()
    (tmp_path / "cv_feed").mkdir()
    (tmp_path / "reports" / "cv_feed.md").write_bytes(b"# r")
    (tmp_path / "cv_feed" / "cv_feed.ipynb").write_bytes(b"{}")
    monkeypatch.setattr(store, "out_root", tmp_path)
    monkeypatch.setattr(store, "reports_root", tmp_path / "reports")
    monkeypatch.setattr(store, "runs", {"cv_feed": object()})

    import codegen.databricks as db_module

    calls = {}
    monkeypatch.setattr(
        db_module, "ensure_volume",
        lambda cfg, **kw: {"full_name": "soham_workspace.codegen_agent.generated",
                           "created": False},
    )

    def fake_publish(cfg, slug, files, **kw):
        calls["slug"] = slug
        calls["names"] = [p.name for p in files]
        return [{"name": p.name, "path": f"/Volumes/x/{p.name}",
                 "size_bytes": 1} for p in files]

    monkeypatch.setattr(db_module, "publish_artifacts", fake_publish)
    response = client.post(
        "/api/databricks/publish",
        json={"feed_slug": "cv_feed", "confirm": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["published"] is True
    assert calls["slug"] == "cv_feed"
    assert calls["names"] == ["cv_feed.md", "cv_feed.ipynb"]


def test_publish_route_unknown_feed_is_404(client, monkeypatch):
    store = ui_main._require_store()
    monkeypatch.setattr(store, "runs", {})
    response = client.post("/api/databricks/publish",
                           json={"feed_slug": "ghost", "confirm": True})
    assert response.status_code == 404
