"""End-to-end dry run of generate-all into a temp output root (no Spark)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codegen.cli import main

REPO = Path(__file__).resolve().parents[1]


def test_generate_all_dry_run(tmp_path, monkeypatch, capsys):
    raw = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    if not raw["contracts"]["pairs"]:
        pytest.skip("contract fixtures removed from the repo 2026-08-22; pairs not configured")
    raw["output"]["dir"] = str(tmp_path / "out")
    raw["output"]["reports_dir"] = str(tmp_path / "reports")
    raw["gate"]["run_generated_tests"] = False
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    monkeypatch.chdir(REPO)  # contracts dir in config is repo-relative
    exit_code = main(["generate-all", "--config", str(config_path), "--dry-run"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert output.count("PASS_WITH_FLAGS") == 4
    assert "FAIL" not in output

    reports = sorted(p.name for p in (tmp_path / "reports").glob("*.md"))
    assert len(reports) == 4
    caqh_dir = tmp_path / "out" / "caqh_tpl_inbound_files"
    candidates = caqh_dir / "candidates" / "candidates.json"
    assert candidates.is_file()
    report_text = (tmp_path / "reports" / "caqh_tpl_inbound_files.md").read_text(encoding="utf-8")
    assert "Layer-2 candidates" in report_text
    assert "PASS_WITH_FLAGS" in report_text
    # Candidates stay out of generated modules.
    for module in (caqh_dir / "pipeline").glob("*.py"):
        assert "LAYER-2 CANDIDATE" not in module.read_text(encoding="utf-8")
