"""D1 post50: two config fields named after BaseModel attributes made pydantic
print a UserWarning on every import (read by a harness as the run's error). They
took other Python names — ``extractor.discovery.validate`` -> ``thresholds``,
``dml.schema`` -> ``db_schema`` — and the YAML keys stay the OLD ones (aliases).
A YAML written with the old keys must load exactly as before, through the CLI's
load_config and the App's config path (the ACFC overlay applied first)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from codegen.config import load_config

REPO = Path(__file__).resolve().parents[1]
OLD_KEYS = """
extractor:
  discovery:
    validate:
      integer_like: 0.55
dml:
  schema: syn_meta
"""


def _overlay(tmp_path) -> Path:
    path = tmp_path / "old_keys.yaml"
    path.write_text(OLD_KEYS, encoding="utf-8")
    return path


def test_the_old_yaml_keys_load_through_load_config(tmp_path):
    config = load_config(REPO / "config" / "config.yaml", overlays=[_overlay(tmp_path)])
    assert config.dml.db_schema == "syn_meta"
    assert config.extractor.discovery.thresholds.integer_like == 0.55
    # the shipped values, untouched by an overlay that does not name them
    shipped = load_config(REPO / "config" / "config.yaml")
    assert shipped.dml.db_schema == "dbo"


def test_the_new_python_names_are_not_yaml_keys(tmp_path):
    path = tmp_path / "new_keys.yaml"
    path.write_text("dml:\n  db_schema: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(REPO / "config" / "config.yaml", overlays=[path])


def test_the_app_config_path_with_the_acfc_overlay_reads_the_old_keys(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from ui.backend import main
    from ui.backend.service import GenerationStore

    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(_overlay(tmp_path)))
    monkeypatch.chdir(REPO)
    store = GenerationStore(main.CONFIG_PATH)
    assert store.config.dml.db_schema == "syn_meta"
    assert store.config.extractor.discovery.thresholds.integer_like == 0.55
    assert store.config.environments          # the ACFC overlay was applied first


def test_importing_the_config_prints_no_warning():
    done = subprocess.run([sys.executable, "-W", "always", "-c", "import codegen.config"],
                          cwd=REPO, capture_output=True, text=True, check=False,
                          env={"PYTHONPATH": str(REPO / "src"), "SYSTEMROOT": "C:\\Windows"})
    assert done.returncode == 0, done.stderr
    assert "Warning" not in done.stderr, done.stderr
