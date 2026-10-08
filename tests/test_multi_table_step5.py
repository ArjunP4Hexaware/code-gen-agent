"""Multi-table Phase C step 5 — DATA_FACTORY_PIPELINE_SCHEDULE's four rows.

Without a client inventory (template_rows overlay) the schedule is the four
structural pipelines: grand master -> master -> file-to-stage,
stage-to-standard. Names from the naming convention ({feed} = FAQ
feed_abbreviation, else the feed slug in capitals), frequency from the feed,
parent by position (the top pipeline's parent 0; the rest the engineer's, the
tooltip naming the parent row), ids / dates / audit left to the engineer. A
configured inventory (pair 1's overlay) still wins.
"""

from __future__ import annotations

import pytest

from multi_table_golden import compare_to_golden

ROLES = ["grand_master", "master", "file_to_stage", "stage_to_standard"]


def test_pair4_schedule_is_the_four_convention_rows_and_matches_the_golden(pair4_payload,
                                                                          pair4_golden):
    assert compare_to_golden(pair4_payload, pair4_golden, "DATA_FACTORY_PIPELINE_SCHEDULE") == []


def test_parents_by_position(pair4_payload):
    rows = pair4_payload["tabs"]["DATA_FACTORY_PIPELINE_SCHEDULE"]["rows"]
    assert [r["values"]["PARENT_PIPELINE_ID"] for r in rows] == ["0", "", "", ""]
    tooltips = [r["badges"]["PARENT_PIPELINE_ID"]["tooltip"] for r in rows]
    assert "METADATA_DB_SEMANTICS.md §2" in tooltips[0]
    assert "row 1 (grand_master)" in tooltips[1]
    assert "row 2 (master)" in tooltips[2] and "row 2 (master)" in tooltips[3]
    for column in ("PIPELINE_ID", "ACTIVE_START_DATE", "CREATED_BY", "CREATED_DATE"):
        assert {r["values"][column] for r in rows} == {""}, column


def test_names_take_the_faq_feed_abbreviation_when_answered(pair4_config, pair4_spec):
    from types import SimpleNamespace

    from codegen.metadata_template import _pipeline_schedule

    tpl = pair4_config.metadata.templates["iig_v2"]
    from codegen.metadata_sheet import _feed_from_spec

    feed = _feed_from_spec(pair4_spec)
    faq = SimpleNamespace(feed_abbreviation=SimpleNamespace(value="NBCOB", source="engineer"))
    rows = _pipeline_schedule("DATA_FACTORY_PIPELINE_SCHEDULE", feed, pair4_config, pair4_spec,
                              faq, tpl)
    assert [r["PIPELINE_NAME"]["value"] for r in rows] == [
        "PL_GMSTR_NBCOB", "PL_MSTR_NBCOB", "PL_File_NBCOB_ADLS_To_Delta_Incr",
        "PL_File_NBCOB_Delta_To_STD_Incr"]


def test_a_configured_inventory_still_wins(pair1_payload):
    rows = pair1_payload["tabs"]["DATA_FACTORY_PIPELINE_SCHEDULE"]["rows"]
    assert [r["values"]["PIPELINE_NAME"] for r in rows] == [
        "PARENT_PIPELINE", "FILE_ONPREM_ADLS", "FILE_RAW_TO_STAGE", "STAGE_TO_STD"]
    assert {r["values"]["PARENT_PIPELINE_ID"] for r in rows} == {""}


def test_a_parent_must_be_an_earlier_role():
    from pydantic import ValidationError

    from codegen.config import MetadataTemplateConfig, PipelineRoleConfig

    with pytest.raises(ValidationError, match="not an earlier role"):
        MetadataTemplateConfig(tabs={}, pipeline_roles=[
            PipelineRoleConfig(role="child", name="x", description="x", parent="master")])
