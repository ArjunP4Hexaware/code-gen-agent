"""Landing-volume write surface + seeder + live/synthetic/auto shell modes.

Everything against a stubbed SDK — no socket is ever opened. The write
guard is the headline: any target outside WRITABLE_PREFIX is refused
before a client exists.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

import codegen.databricks as db
from codegen.cli import _resolve_pattern_tokens, _synthetic_file_bytes
from codegen.demo_sources import resolve_shell_listing


def _settings(**overrides):
    values = {
        "profile": "DEFAULT",
        "schema_name": "codegen_agent",
        "catalog": "soham_workspace",
        "frd_volume": "frd_raw",
        "sttm_volume": "sttm_raw",
        "landing_volume": "mftlanding",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _cfg(**overrides):
    return db.config_for(_settings(**overrides), env={})


# -- the write guard ----------------------------------------------------------- #


def test_writes_refuse_anything_outside_the_writable_prefix():
    foreign = _cfg(catalog="ai_ready_data", schema_name="claims_stage1")
    for call in (
        lambda: db.ensure_volume(foreign, client=object()),
        lambda: db.upload_file(foreign, "a/b.csv", b"x", client=object()),
        lambda: db.list_landing(foreign, client=object()),
    ):
        with pytest.raises(db.DatabricksConfigError, match="only writable location"):
            call()
    # force does not bypass the guard.
    with pytest.raises(db.DatabricksConfigError, match="only writable location"):
        db.upload_file(foreign, "a/b.csv", b"x", force=True, client=object())


def test_missing_landing_volume_is_a_named_error():
    with pytest.raises(db.DatabricksConfigError, match="landing_volume"):
        db.ensure_volume(_cfg(landing_volume=""), client=object())


class _StubVolumes:
    def __init__(self, exists=True, read_error=None):
        self.exists = exists
        self.read_error = read_error
        self.created = []

    def read(self, full_name):
        if self.read_error:
            raise self.read_error
        if not self.exists:
            raise RuntimeError("VOLUME_DOES_NOT_EXIST: does not exist")
        return SimpleNamespace(full_name=full_name)

    def create(self, catalog_name, schema_name, name, volume_type):
        self.created.append(f"{catalog_name}.{schema_name}.{name}")
        self.exists = True


class _StubLandingFiles:
    def __init__(self):
        self.store: dict[str, bytes] = {}

    def get_metadata(self, path):
        if path not in self.store:
            raise RuntimeError("NOT_FOUND")
        return SimpleNamespace(content_length=len(self.store[path]))

    def upload(self, path, contents, overwrite=False):
        self.store[path] = contents.read()

    def list_directory_contents(self, directory):
        directory = directory.rstrip("/")
        children: dict[str, dict] = {}
        for path, data in self.store.items():
            if not path.startswith(directory + "/"):
                continue
            remainder = path[len(directory) + 1:]
            head = remainder.split("/")[0]
            child = f"{directory}/{head}"
            is_dir = "/" in remainder
            entry = children.setdefault(child, {
                "path": child, "name": head, "dir": is_dir,
                "size": 0 if is_dir else len(data),
            })
            entry["dir"] = entry["dir"] or is_dir
        return [
            SimpleNamespace(path=e["path"], name=e["name"], is_directory=e["dir"],
                            file_size=e["size"], last_modified=1787200000000)
            for e in children.values()
        ]


def _stub_client(exists=True):
    return SimpleNamespace(volumes=_StubVolumes(exists=exists),
                           files=_StubLandingFiles())


def test_ensure_volume_created_vs_existed():
    cfg = _cfg()
    client = _stub_client(exists=False)
    assert db.ensure_volume(cfg, client=client) == {
        "full_name": "soham_workspace.codegen_agent.mftlanding", "created": True,
    }
    assert client.volumes.created == ["soham_workspace.codegen_agent.mftlanding"]
    assert db.ensure_volume(cfg, client=client)["created"] is False


def test_upload_verify_and_force_semantics():
    cfg = _cfg()
    client = _stub_client()
    path = db.upload_file(cfg, "mftlanding/inbound/a/f.csv", b"12345", client=client)
    assert path == "/Volumes/soham_workspace/codegen_agent/mftlanding/mftlanding/inbound/a/f.csv"
    # No overwrite without force:
    with pytest.raises(db.DatabricksTransportError, match="--force"):
        db.upload_file(cfg, "mftlanding/inbound/a/f.csv", b"999", client=client)
    db.upload_file(cfg, "mftlanding/inbound/a/f.csv", b"999", force=True, client=client)
    listed = db.list_landing(cfg, client=client)
    assert listed == [{
        "path": "mftlanding/inbound/a/f.csv", "name": "f.csv", "size": 3,
        "modified": listed[0]["modified"],
    }]
    with pytest.raises(db.DatabricksTransportError, match="invalid landing path"):
        db.upload_file(cfg, "../escape.csv", b"x", client=client)


# -- seeder building blocks ---------------------------------------------------- #


def test_token_resolution_table_and_unknown_flag():
    date = datetime(2026, 8, 27)
    assert _resolve_pattern_tokens("x_CCYY_MM.csv", date) == ("x_2026_08.csv", [])
    assert _resolve_pattern_tokens("y_YYYYMMDD_HHMM.psv", date) == ("y_20260827_0600.psv", [])
    # Word boundaries: OH stays literal; mixed-case words untouched.
    resolved, flagged = _resolve_pattern_tokens("a_mrdn_OH_CCYYMMDD.psv", date)
    assert resolved == "a_mrdn_OH_20260827.psv" and flagged == []
    # Unknown date-ish token is left literal AND flagged.
    resolved, flagged = _resolve_pattern_tokens("z_YYWW.csv", date)
    assert resolved == "z_YYWW.csv" and flagged == ["YYWW"]


def test_synthetic_file_bytes_deterministic_and_fake():
    columns = [SimpleNamespace(source_column="member_id"),
               SimpleNamespace(source_column="zip_code")]
    spec = SimpleNamespace(feed_slug="f", delimiter="|",
                           segments=[SimpleNamespace(fields=columns)])
    first = _synthetic_file_bytes(spec, "a.csv")
    assert first == _synthetic_file_bytes(spec, "a.csv")  # deterministic
    assert first != _synthetic_file_bytes(spec, "b.csv")  # per-file seed
    text = first.decode()
    assert text.splitlines()[0] == "member_id|zip_code"
    assert len(text.splitlines()) == 4  # header + 3 rows
    assert "MEM" in text and "ZIP" in text  # obviously-fake values


# -- shell modes --------------------------------------------------------------- #


def _rows():
    return [{"landing_root": {"value": "mftlanding/inbound/a/b/c", "synthetic": False},
             "file_name_patterns": ["p_YYYY.csv"]}]


def test_shell_mode_synthetic_is_default_renderer(config):
    result = resolve_shell_listing(_rows(), config, mode="synthetic")
    assert result["mode"] == "synthetic" and result["reason"] is None
    assert result["lines"][0].startswith("$ databricks fs ls dbfs:/Volumes/")


def test_shell_mode_live_renders_real_entries(config, monkeypatch):
    import codegen.demo_sources as ds

    monkeypatch.setattr(
        ds, "live_shell_listing",
        lambda rows, cfg: (["$ databricks fs ls dbfs:/Volumes/x/", "real.csv  5 B  t"],
                           "soham_workspace.codegen_agent.mftlanding"),
    )
    result = resolve_shell_listing(_rows(), config, mode="live")
    assert result["mode"] == "live"
    assert result["source"] == "soham_workspace.codegen_agent.mftlanding"
    assert result["listed_at"]
    assert "real.csv  5 B  t" in result["lines"]


def test_shell_mode_live_falls_back_with_one_line_reason(config, monkeypatch):
    import codegen.demo_sources as ds

    def explode(rows, cfg):
        raise db.DatabricksTransportError("listing failed: PERMISSION_DENIED\nlong trace")

    monkeypatch.setattr(ds, "live_shell_listing", explode)
    result = resolve_shell_listing(_rows(), config, mode="live")
    assert result["mode"] == "synthetic"
    assert result["reason"] == "listing failed: PERMISSION_DENIED"
    assert "\n" not in result["reason"]


def test_shell_mode_auto_respects_probe(config, monkeypatch):
    import codegen.demo_sources as ds

    monkeypatch.setattr(ds, "_landing_available",
                        lambda cfg: (False, "volume x does not exist"))
    result = resolve_shell_listing(_rows(), config, mode="auto")
    assert result["mode"] == "synthetic"
    assert result["reason"] == "volume x does not exist"

    monkeypatch.setattr(ds, "_landing_available", lambda cfg: (True, ""))
    monkeypatch.setattr(ds, "live_shell_listing",
                        lambda rows, cfg: (["$ x"], "src"))
    assert resolve_shell_listing(_rows(), config, mode="auto")["mode"] == "live"


# -- endpoint ------------------------------------------------------------------ #

pytest.importorskip("fastapi")
from pathlib import Path  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
needs_demo_frd = pytest.mark.skipif(
    not (REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json").is_file(),
    reason="demo FRD fixture not restored",
)


@needs_demo_frd
def test_endpoint_reports_mode_and_reason(monkeypatch, tmp_path):
    import codegen.demo_sources as ds

    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(tmp_path))
    monkeypatch.setattr(ds, "_landing_available", lambda cfg: (False, "no creds"))
    client = TestClient(ui_main.app)
    payload = client.get("/api/demo/source-files").json()
    assert payload["shell_mode"] == "synthetic"
    assert payload["shell_reason"] == "no creds"

    monkeypatch.setattr(ds, "_landing_available", lambda cfg: (True, ""))
    monkeypatch.setattr(ds, "live_shell_listing",
                        lambda rows, cfg: (["$ live"], "soham_workspace.codegen_agent.mftlanding"))
    payload = client.get("/api/demo/source-files").json()
    assert payload["shell_mode"] == "live"
    assert payload["shell_listing"] == ["$ live"]
    assert payload["shell_listed_at"]
