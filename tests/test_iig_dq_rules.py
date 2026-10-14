"""D1 post44 item 5 (2026-10-14): DATA_QUALITY_RULES from the STTM, the corpus's
classes (patterns.json rule_classes) in the ACFC overlay.

Pair 4 (Northwind Benefits, header / detail / trailer tables, a typed Standard band)
under the ACFC overlay's DQ knobs, with an audit literal and a recycle lookup added
to its resolved spec: per FILE the Predefined header / trailer split (SOURCE_COLUMN
header columns '|' trailer columns, the CAQH golden's form), AddCustomColumnsRule
per audit literal, NullCheckRule over the PK / not-null columns, the Custom
ReferentialCheckRule on the recycle lookup's column; per STANDARD table the
STDDelta LRTrimRule, DataTypeCastRule and a DateConversionRule per Date column.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.contracts.resolved import ResolvedRecycle, ResolvedTable
from codegen.contracts.sttm import AuditColumn, RecycleSpec
from codegen.metadata_template import template_tab_rows
from test_iig_diff_identity import ADLS, KEYS, STG, _book, _index, iig_diff
from test_iig_v2_derivations import ACFC_OVERLAY, REPO

DQ = "DATA_QUALITY_RULES"
DQ_DIFF_HEAD = ["GROUP_ID", "OBJECT_ID", "RULE_TYPE", "RULE_CLASS", "SOURCE_COLUMN", "CREATED_BY"]
ADLS_DIFF_HEAD = ["GROUP_ID", "OBJECT_ID", "PIPELINE_ID", "TGT_TABLE_NAME", "LOB"]
STG_DIFF_HEAD = ["GROUP_ID", "OBJECT_ID", "PIPELINE_ID", "TGT_TABLE_NAME"]
FEED = "nw_member_risk"
DQ_KEYS = ("dq_rules", "dq_rule_classes", "dq_rule_types", "dq_params", "dq_citations",
           "dq_split_style", "dq_split_location")


@pytest.fixture(scope="module")
def dq(pair4_spec, tmp_path_factory):
    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from multi_table_golden import PAIR4_OVERLAY

    acfc = yaml.safe_load(ACFC_OVERLAY.read_text(encoding="utf-8"))
    knobs = {k: v for k, v in acfc["metadata"]["templates"]["iig_v2"].items() if k in DQ_KEYS}
    overlay = tmp_path_factory.mktemp("dq") / "dq.yaml"
    overlay.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": knobs}}}),
                       encoding="utf-8")
    config = load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY, overlay])
    tpl = config.metadata.templates["iig_v2"]
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    stage = pair4_spec.segments[1].stage_table
    spec = pair4_spec.model_copy(update={
        "audit_columns": [*pair4_spec.audit_columns,
                          AuditColumn(column="FILE_TYPE", datatype="String",
                                      value_spec="Default to 'NWB'")],
        "recycle": ResolvedRecycle(
            spec=RecycleSpec(applies_to="MEMBER_ID", enabled=True,
                             validation="Check with MEMBER_ID from STG.MBR.member",
                             on_match="load", on_no_match="recycle", recycle_window_days=15),
            frd_rule_text=None,
            recycle_table=ResolvedTable(catalog=stage.catalog, schema_name=stage.schema_name,
                                        table="nb_cob_report_recycle", role="recycle"),
            reference_table="STG.MBR.member", reference_id_column="MEMBER_ID",
            reference_filter=None)})
    rows = template_tab_rows(DQ, frd.feeds[0], config, spec, None, tpl)
    return rows, spec


def _v(row, header):
    cell = row.get(header)
    return None if cell is None else cell["value"]


def test_stage_rules_per_file_in_the_corpus_order(dq):
    rows, spec = dq
    stage = [r for r in rows if _v(r, "RULE_TYPE") != "STDDelta"]
    files = list(dict.fromkeys(_v(r, "OBJECT_ID") for r in stage))
    per_file = [sum(_v(r, "OBJECT_ID") == f for r in stage) for f in files]
    # D1 post45: + NullCheckRule / DeDuplicationRule, the baseline PER FEED — on the
    # first file's object only; the split / custom-columns / referential rows per file
    assert per_file == [5] + [3] * (len(files) - 1)
    assert [_v(r, "RULE_CLASS") for r in stage[5:8]] == [
        "LoadHeaderAndTrailerToSeparateTablesRule", "AddCustomColumnsRule",
        "ReferentialCheckRule"]
    assert [_v(r, "SEQUENCE_NO") for r in stage[5:8]] == [1, 2, 3]
    first = stage[:5]
    assert [(_v(r, "RULE_TYPE"), _v(r, "RULE_CLASS"), _v(r, "SEQUENCE_NO")) for r in first] == [
        ("Predefined", "LoadHeaderAndTrailerToSeparateTablesRule", 1),
        ("Predefined", "AddCustomColumnsRule", 2),
        ("Predefined", "NullCheckRule", 3),
        ("Predefined", "DeDuplicationRule", 4),
        ("Custom", "ReferentialCheckRule", 5)]
    split, custom, null, dedup, referential = first
    assert _v(dedup, "SOURCE_COLUMN") == _v(null, "SOURCE_COLUMN")     # the key columns
    header, trailer = spec.segments[0], spec.segments[2]
    assert _v(split, "SOURCE_COLUMN") == "|".join(
        ",".join(f.stage_column for f in seg.fields) for seg in (header, trailer))
    assert _v(split, "INPUT_PARAM") == "SRC_FILE_NAME"
    # the location shape carries the D1 storage account placeholder: open, never written
    assert _v(split, "TARGET_COLUMN") == ""
    # 2026-10-14: the storage account is the run's environment's (none here)
    assert split["TARGET_COLUMN"]["badge_entry"]["note"].startswith(
        "iig_env:DATA_QUALITY_RULES.TARGET_COLUMN — the tables' locations need the storage "
        "account: no environment is defined")
    assert (_v(custom, "SOURCE_COLUMN"), _v(custom, "INPUT_PARAM"),
            _v(custom, "TARGET_COLUMN")) == ("NWB", "literal", "FILE_TYPE")
    keyed = {"MEMBER_ID", *spec.not_null_columns}
    detail = [f.stage_column for f in spec.segments[1].fields]
    assert _v(null, "SOURCE_COLUMN").split(",") == [c for c in detail if c in keyed]
    assert _v(null, "SOURCE_COLUMN") == _v(null, "TARGET_COLUMN")
    assert (_v(referential, "SOURCE_COLUMN"), _v(referential, "INPUT_PARAM"),
            _v(referential, "TARGET_COLUMN")) == ("MEMBER_ID", "stg_files.REF_RULE_VIEW",
                                                  "REF_RULE_COL")


def test_stddelta_rules_per_standard_table(dq):
    rows, spec = dq
    std = [r for r in rows if _v(r, "RULE_TYPE") == "STDDelta"]
    by_class: dict[str, list] = {}
    for r in std:
        by_class.setdefault(_v(r, "RULE_CLASS"), []).append(r)
    assert len(by_class["LRTrimRule"]) == 3                       # one per standard table
    detail = spec.segments[1]
    trim = next(r for r in by_class["LRTrimRule"]
                if "MEMBER_ID" in _v(r, "SOURCE_COLUMN").split(","))
    assert _v(trim, "SOURCE_COLUMN").split(",") == [f.standard_column for f in detail.fields
                                                    if f.standard_column]
    assert _v(trim, "INPUT_PARAM") == "" and trim["INPUT_PARAM"]["badge_entry"]["badge"] == \
        "synthetic"                                               # decided blank (SFMC rows)
    casts = {_v(r, "INPUT_PARAM").rsplit(".", 1)[-1]: _v(r, "SOURCE_COLUMN")
             for r in by_class["DataTypeCastRule"]}
    trailer = spec.segments[2]
    assert set(casts["nb_cob_report_trl"].split(",")) == {
        f.standard_column for f in trailer.fields
        if f.standard_column and (f.standard_datatype or "").lower() != "string"}
    assert set(casts) == {"nb_cob_report_hdr", "nb_cob_report_dtl", "nb_cob_report_trl"}
    dates = [f.standard_column for s in spec.segments for f in s.fields
             if (f.standard_datatype or "").lower() == "date"]
    conversions = by_class["DateConversionRule"]
    assert sorted(_v(r, "SOURCE_COLUMN") for r in conversions) == sorted(dates)
    # no load rule states the formats: INPUT_PARAM open
    assert all(_v(r, "INPUT_PARAM") == "" and r["INPUT_PARAM"]["badge_entry"]["badge"] ==
               "needs_template" for r in conversions)
    for r in std:
        assert _v(r, "SEQUENCE_NO") >= 1


def test_a_flat_feed_writes_no_split_and_no_custom_columns(dq, pair4_spec):
    """No header / trailer table: neither the split rule nor AddCustomColumnsRule."""
    rows, spec = dq
    from codegen.metadata_template import _split_groups, _table_groups

    groups = _table_groups(spec)
    assert len(_split_groups(groups, groups[1])) == 2
    flat = [g for g in groups if g.is_detail]
    assert _split_groups(flat, flat[0]) == []


# -- iig_diff: a DQ row's table on its leg (iig_keys.yaml object_tables.by_rule_type) --


def diff_pair(tmp_path: Path) -> tuple[Path, Path]:
    """A golden (GROUP_IDs filled) and an agent workbook (GROUP_ID blank, ADLS and
    STGDELTA objects both 1) with one Predefined and one STDDelta rule."""
    golden = _book(tmp_path / "golden.xlsx", {
        ADLS: [ADLS_DIFF_HEAD, [180250, 1, 180450, f"stg_nw.{FEED}", "ZQ1"]],
        STG: [STG_DIFF_HEAD, [180251, 1, 180451, f"{FEED}_std"]],
        DQ: [DQ_DIFF_HEAD, [180250, 1, "Predefined", "NullCheckRule", "member_id", "prod.user"],
             [180251, 1, "STDDelta", "LRTrimRule", "member_id,lob", "prod.user"]]})
    agent = _book(tmp_path / "agent" / FEED / f"{FEED}_IIG.xlsx", {
        ADLS: [ADLS_DIFF_HEAD, [None, 1, None, f"stg_nw.{FEED}", "ZQ2"]],
        STG: [STG_DIFF_HEAD, [None, 1, None, f"{FEED}_std"]],
        DQ: [DQ_DIFF_HEAD, [None, 1, "Predefined", "NullCheckRule", "member_id", None],
             [None, 1, "STDDelta", "LRTrimRule", "member_id,lob", None]]})
    return golden, agent


def test_dq_rows_resolve_their_table_on_their_leg_and_pair(tmp_path: Path) -> None:
    """The agent leaves GROUP_ID blank and numbers its ADLS and STGDELTA objects 1
    both: a rule's table was ambiguous and the row never paired."""
    golden, agent = diff_pair(tmp_path)
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS,
                                group_index=[_index(tmp_path / "index.csv")])
    dq = payload["sheets"][DQ]
    assert dq["unpaired"] == {"golden": 0, "agent": 0}, (dq["pairing"], dq["unpaired"])
    assert dq["pairing"][iig_diff.BY_IDENTITY] == 2


def test_object_tables_route_by_rule_type() -> None:
    keys = iig_diff.load_keys(KEYS)
    assert keys.object_by_rule_type == {"STDDelta": "STGDELTA_STDDELTA_INGESTION_DET",
                                        "*": "ADLS_DELTA_INGESTION_DETAILS"}
