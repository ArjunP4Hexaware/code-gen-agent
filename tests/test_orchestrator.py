"""post187 (Soham, 2026-11-09; Lokesh's rule): a pipeline name's prefix is the run's
orchestrator - PL_ for ADF (the default), WF_ for a Databricks Workflow - and nothing
else of the name changes. A run choice (App Advanced options, generate
--orchestrator); the provenance names it. Synthetic only."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import input_choices
from codegen.config import load_config
from codegen.orchestrator import label, pipeline_prefix, with_orchestrator

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def acfc():
    import os

    saved = os.environ.pop("CODEGEN_SKIP_ENV_OVERLAY", None)   # the ACFC patterns
    try:
        return load_config(REPO / "config" / "config.yaml")
    finally:
        if saved is not None:
            os.environ["CODEGEN_SKIP_ENV_OVERLAY"] = saved


def test_adf_is_the_default_and_workflow_the_alternative(acfc):
    assert acfc.engineering_standards.pipeline_orchestrator == "adf"
    assert pipeline_prefix(acfc) == "PL"
    workflow = with_orchestrator(acfc, "workflow")
    assert pipeline_prefix(workflow) == "WF"
    assert label(workflow) == "Databricks Workflow (WF_)"
    assert with_orchestrator(acfc, None) is acfc
    with pytest.raises(ValueError, match="unknown pipeline orchestrator"):
        with_orchestrator(acfc, "airflow")


def test_every_pattern_starts_with_the_prefix_part(acfc):
    templates = acfc.conventions.get("acfc_prx").pipeline_name_templates
    assert templates and all(t.startswith("{pipeline_prefix}_") for t in templates.values())


def test_workflow_names_are_the_adf_names_with_wf_in_place_of_pl(acfc, tmp_path):
    from test_derivations import FRD, _pair11_specs, _scoped

    config = _scoped(acfc, tmp_path)
    (tmp_path / "contracts").mkdir()
    specs, _flags = _pair11_specs(FRD, tmp_path / "contracts", config)
    spec, profile = specs[0], config.conventions.get("acfc_prx")
    tpl = config.metadata.templates["iig_v2"]
    items = [i for i in input_choices.defaulted_inputs(tpl)
             if i.flow and i.rule.faq == "pipeline_name"]
    assert len(items) == 4

    def names(cfg):
        tokens = input_choices.feed_tokens(spec, tpl, None, cfg)
        return {i.flow: input_choices.proposal(i, spec, profile, tpl, tokens, frozenset(),
                                               cfg).value for i in items}

    adf, workflow = names(config), names(with_orchestrator(config, "workflow"))
    assert all(v.startswith("PL_") for v in adf.values()), adf
    assert workflow == {flow: "WF_" + name[3:] for flow, name in adf.items()}


def test_generate_orchestrator_flag_names_and_sources_the_prefix(tmp_path):
    from test_naming_codes import _framework_run, _section

    naming = {"product": {"codes": ["DLK"], "entries": ["Data Lake"],
                          "quotes": ["paragraph 4: 'Synthetic files ingested into Lakehouse'"]}}
    done, report, log = _framework_run(tmp_path, naming, extra=["--orchestrator", "workflow"])
    assert done.returncode in (0, 3), done.stdout + done.stderr
    for text in (report, log):
        section = _section(text)
        line = next(x for x in section.splitlines() if "PIPELINE_NAME [file_to_stg]" in x)
        assert "= `WF_CHLD_DLK_NSP_RAW_TO_STG_" in line
        assert "{pipeline_prefix} = `WF` ← the run's pipeline orchestrator: Databricks " \
               "Workflow (WF_)" in section
    from openpyxl import load_workbook  # post194: the IIG, not the retired SQL

    names = [str(cell) for p in (tmp_path / "out").rglob("*_IIG.xlsx")
             for ws in load_workbook(p, read_only=True) for row in ws.iter_rows(values_only=True)
             for cell in row if cell]
    assert any(n.startswith("WF_CHLD_DLK_NSP_RAW_TO_STG_") for n in names)
    assert not any(n.startswith("PL_CHLD_") for n in names)


def test_an_unknown_orchestrator_stops_generate_before_anything_is_written(tmp_path):
    from test_naming_codes import _framework_run

    done, _report, _log = _framework_run(tmp_path, None, extra=["--orchestrator", "airflow"])
    assert done.returncode == 1
    assert "unknown pipeline orchestrator 'airflow'" in done.stdout + done.stderr
