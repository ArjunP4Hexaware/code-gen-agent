"""End-to-end dry run of generate-all into a temp output root (no Spark).

Runs against the anonymized CV/golden pair (restored working-tree-only from
git history; skips if absent). The pair is injected into a temp config —
``config.contracts.pairs`` stays empty in the tracked config on purpose.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from tests.conftest import require_fixture_files

from codegen.cli import main

REPO = Path(__file__).resolve().parents[1]

CV_FRD = "FRD_demo_cv_golden.contract.json"
CV_STTM = "sttm_mapping_contracts_cv_golden.json"
CV_FEEDS = ["cv_community_demographic_risk", "cv_community_risk", "cv_individual_risk"]
# From fixtures/faq/<slug>.faq.yaml: yearly → Y_, monthly → M_ (standards
# job_prefix_by_frequency).
EXPECTED_JOB_NAMES = {
    "cv_community_demographic_risk": "Y_ingest_cv_community_demographic_risk",
    "cv_community_risk": "Y_ingest_cv_community_risk",
    "cv_individual_risk": "M_ingest_cv_individual_risk",
}


def test_generate_all_dry_run(tmp_path, monkeypatch, capsys):
    raw = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    contracts_dir = REPO / raw["contracts"]["dir"]
    require_fixture_files(contracts_dir / CV_FRD, contracts_dir / CV_STTM)
    raw["contracts"]["pairs"] = [{"frd": CV_FRD, "sttm": CV_STTM}]
    raw["output"]["dir"] = str(tmp_path / "out")
    raw["output"]["reports_dir"] = str(tmp_path / "reports")
    raw["gate"]["run_generated_tests"] = False
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    monkeypatch.chdir(REPO)  # contracts dir + faq dir in config are repo-relative
    exit_code = main(["generate-all", "--config", str(config_path), "--dry-run"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert output.count("PASS_WITH_FLAGS") == len(CV_FEEDS)
    assert "FAIL" not in output

    reports = sorted(p.stem for p in (tmp_path / "reports").glob("*.md"))
    assert reports == CV_FEEDS

    for feed in CV_FEEDS:
        feed_dir = tmp_path / "out" / feed
        # Three-input banner is in every generated module; candidates stay out.
        for module in (feed_dir / "pipeline").glob("*.py"):
            text = module.read_text(encoding="utf-8")
            assert "LAYER-2 CANDIDATE" not in text
            if module.name != "__init__.py":
                assert "Inputs (three-input model):" in text
        # Job name comes from the standards pattern + FAQ frequency prefix.
        workflow = json.loads((feed_dir / "job" / "workflow.json").read_text(encoding="utf-8"))
        assert workflow["name"] == EXPECTED_JOB_NAMES[feed]
        # create_tables=false: notebook lists prerequisites, executes no DDL.
        notebook = json.loads(
            (feed_dir / f"{feed}.ipynb").read_text(encoding="utf-8")
        )
        cell_ids = [c["id"] for c in notebook["cells"]]
        assert "prerequisites" in cell_ids and "ddl" not in cell_ids

        report_text = (tmp_path / "reports" / f"{feed}.md").read_text(encoding="utf-8")
        assert "PASS_WITH_FLAGS" in report_text
        assert "## Inputs (three-input model)" in report_text
        assert "standards_stub:" in report_text
        assert "load_mode_not_enforced: declared truncate_and_load" in report_text
        assert "faq_unanswered:" in report_text
