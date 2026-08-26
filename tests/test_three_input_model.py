"""Three-input model: FAQ loader/prefills, job naming, flags, notebook DDL gate.

These tests run without contract fixtures: the FAQ/prefill/naming logic only
needs two spec attributes, so a stub stands in for ResolvedFeedSpec.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from codegen.config import EngineeringStandardsConfig
from codegen.emit.context import resolve_job_name
from codegen.emit.notebook import build_notebook
from codegen.faq import (
    QUESTION_FIELDS,
    FaqAnswer,
    LoadPatternFaq,
    answers,
    apply_contract_prefills,
    load_faq,
    summarize,
)
from codegen.gate.verdict import compute_verdict


def _spec(load_strategy="Truncate and Load", frequency="Monthly Run; whenever"):
    return SimpleNamespace(stage_load_strategy=load_strategy, frequency=frequency)


# -- loader ------------------------------------------------------------------


def test_missing_faq_file_yields_all_unknown_defaults(config):
    faq = load_faq("no_such_feed_slug", config)
    assert all(a.source == "unknown" for a in answers(faq).values())
    assert faq.target_tables_exist.value == "yes"  # default yes, still unanswered
    assert faq.dataset_ids.source is None and faq.dataset_ids.target is None


def test_cv_fixture_faq_file_loads_with_contract_sources(config):
    faq = load_faq("cv_individual_risk", config)
    assert faq.load_mode.value == "truncate_and_load"
    assert faq.load_mode.source == "contract"
    assert faq.load_frequency.value == "monthly"
    assert "Monthly Run" in faq.load_frequency.evidence


# -- contract prefills -------------------------------------------------------


def test_prefill_load_mode_and_frequency_from_contract():
    faq = apply_contract_prefills(LoadPatternFaq(), _spec())
    assert faq.load_mode.value == "truncate_and_load"
    assert faq.load_mode.source == "contract"
    assert 'Truncate and Load' in faq.load_mode.evidence
    assert faq.load_frequency.value == "monthly"
    assert faq.load_frequency.source == "contract"
    assert faq.load_frequency.evidence == "Monthly Run; whenever"


def test_prefill_append_and_yearly():
    faq = apply_contract_prefills(LoadPatternFaq(), _spec("Append", "Yearly Twice"))
    assert faq.load_mode.value == "append"
    assert faq.load_frequency.value == "yearly"


def test_file_answer_wins_over_prefill():
    answered = LoadPatternFaq(
        load_mode=FaqAnswer(value="merge_on_keys", source="engineer"),
        load_frequency=FaqAnswer(value="daily", source="engineer"),
    )
    faq = apply_contract_prefills(answered, _spec())
    assert faq.load_mode.value == "merge_on_keys"
    assert faq.load_mode.source == "engineer"
    assert faq.load_frequency.value == "daily"


def test_ambiguous_frequency_stays_unknown():
    faq = apply_contract_prefills(
        LoadPatternFaq(), _spec(frequency="File arrives twice a year, roughly")
    )
    assert faq.load_frequency.source == "unknown"


# -- job naming (engineering standards) --------------------------------------


def test_job_prefix_from_frequency():
    standards = EngineeringStandardsConfig()
    faq = LoadPatternFaq(load_frequency=FaqAnswer(value="monthly", source="contract"))
    assert resolve_job_name(standards, faq, "cv_individual_risk") == "M_ingest_cv_individual_risk"


def test_job_name_falls_back_to_legacy_when_frequency_unknown():
    assert (
        resolve_job_name(EngineeringStandardsConfig(), LoadPatternFaq(), "some_feed")
        == "ingest_some_feed"
    )


def test_edo_workflow_name_from_config(config):
    """The tracked config carries the EDO WF_ pattern + abbreviation tables."""
    faq = LoadPatternFaq(load_frequency=FaqAnswer(value="daily", source="contract"))
    name = resolve_job_name(
        config.engineering_standards,
        faq,
        "sfmc_email_campaign_tracking",
        source="Salesforce Marketing Cloud",
        domain="member",
        sub_domain="outreach",
        lobs=["All"],
    )
    assert name == "WF_DLK_NSP_SFMC_EMAIL_CAMPAIGN_TRACKING_MBR_OUTREACH_ALL_DLY"


def test_edo_workflow_name_collapses_unknown_components(config):
    """A feed with no domain/LOB still gets a legal, collapsed name."""
    name = resolve_job_name(
        config.engineering_standards,
        LoadPatternFaq(),
        "some_feed",
        source=None,
        domain=None,
        sub_domain=None,
        lobs=[],
    )
    assert name == "WF_DLK_NSP_SOME_FEED_ADH"
    assert "__" not in name


def test_edo_notebook_name_from_config(config):
    from codegen.emit.context import resolve_notebook_name

    name = resolve_notebook_name(
        config.engineering_standards,
        LoadPatternFaq(),
        "sfmc_email_campaign_tracking",
        domain="member",
        sub_domain="outreach",
    )
    assert name == "NB_DLK_NSP_MBR_OUTREACH_INGEST"


def test_notebook_name_none_when_pattern_unset():
    from codegen.emit.context import resolve_notebook_name

    assert (
        resolve_notebook_name(EngineeringStandardsConfig(), LoadPatternFaq(), "x") is None
    )


# -- gate flags (verdict logic untouched) ------------------------------------


def test_faq_and_standards_flags_never_fail(config):
    faq = apply_contract_prefills(LoadPatternFaq(), _spec())
    gate = compute_verdict(
        "feed", [], [], [], False, faq=faq, standards=config.engineering_standards
    )
    assert gate.verdict == "PASS_WITH_FLAGS"
    unanswered = [f for f in gate.flags if f.startswith("faq_unanswered:")]
    assert len(unanswered) == len(QUESTION_FIELDS) - 2  # load_mode + load_frequency answered
    assert any(
        f.startswith("load_mode_not_enforced: declared truncate_and_load") for f in gate.flags
    )
    # The EDO standards documents landed 2026-08-26 (config.yaml), so the
    # tracked config no longer raises the stub flag; the model DEFAULT still
    # does, keeping the honest degrade for configs without the section.
    assert not any(f.startswith("standards_stub:") for f in gate.flags)
    default_gate = compute_verdict(
        "feed", [], [], [], False, standards=EngineeringStandardsConfig()
    )
    assert any(f.startswith("standards_stub:") for f in default_gate.flags)


def test_no_faq_no_standards_keeps_old_behavior():
    gate = compute_verdict("feed", [], [], [], False)
    assert gate.verdict == "PASS"
    assert gate.flags == []


# -- notebook: create_tables=false swaps DDL cells for prerequisites ---------

_MODULE = '"""Mod."""\n\n\nX = 1\n'
_ENTRYPOINT = "# Databricks notebook source\ny = 1\n"
_DDL = (
    "-- GENERATED by codegen-data-engineer-agent\n"
    "-- FRD sha256 aaaa | STTM sha256 bbbb\n"
    "CREATE TABLE IF NOT EXISTS stg.t_detail (a STRING) USING DELTA\n"
)


def _nb_context(create_tables: bool) -> dict:
    return {
        "feed": {"slug": "demo", "id": "demo", "name": "demo", "source_system": "sys"},
        "provenance": {
            "frd_name": "frd.json",
            "frd_sha": "a" * 64,
            "sttm_sha": "b" * 64,
            "synthetic": False,
            "inputs": {
                "standards_status": "STUB — awaiting client engineering standards document",
                "writer_behavior": "MERGE-by-file",
                "answered": 0,
                "from_contract": 0,
                "unknown": 8,
                "load_mode": "unknown",
                "load_mode_source": "unknown",
                "dataset_source": None,
                "dataset_target": None,
            },
        },
        "standards": {"status": "STUB", "create_tables": create_tables},
        "default_catalog": None,
        "stage_schema": "stg",
        "segments": [{"stage_table": "t_detail"}],
        "errors_table": "t_detail_errors",
        "processed_files_table": "t_detail_processed_files",
        "recycle": None,
        "standard": None,
    }


def _cell_ids(create_tables: bool) -> tuple[list[str], dict]:
    text = build_notebook(
        _nb_context(create_tables),
        module_sources=[("feed_spec", _MODULE)],
        ddl_sources=[("stg.t_detail.sql", _DDL)],
        entrypoint_source=_ENTRYPOINT,
    )
    notebook = json.loads(text)
    return [c["id"] for c in notebook["cells"]], notebook


def test_notebook_lists_prerequisites_instead_of_ddl_when_create_tables_false():
    ids, notebook = _cell_ids(create_tables=False)
    assert "prerequisites" in ids and "ddl" not in ids
    prereq = next(c for c in notebook["cells"] if c["id"] == "prerequisites")
    text = "".join(prereq["source"])
    assert "`stg.t_detail`" in text
    assert "`stg.t_detail_errors`" in text
    assert "`stg.t_detail_processed_files`" in text
    assert "REFERENCE only" in text


def test_notebook_keeps_ddl_cells_when_create_tables_true():
    ids, _notebook = _cell_ids(create_tables=True)
    assert "ddl" in ids and "prerequisites" not in ids


def test_summarize_counts():
    faq = apply_contract_prefills(LoadPatternFaq(), _spec())
    view = summarize(faq)
    assert view["answered"] == 2
    assert view["from_contract"] == 2
    assert view["unknown"] == len(QUESTION_FIELDS) - 2
    assert view["load_mode"] == "truncate_and_load"
