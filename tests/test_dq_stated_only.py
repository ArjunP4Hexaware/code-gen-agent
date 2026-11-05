"""post171 (Soham, 2026-11-05, "DQ option 1"): a DATA_QUALITY_RULES row only where a
document STATES the rule. "If we're arguing about things in the prod IIG that's
automatically wrong": a real pair_11 IIG carried 15 DQ rows, 11 of them (DeDuplication,
DataTypeCast, DateConversion) stated by neither document - its FRD says "NA" to the
duplicate and incomplete-record checks.

- DeDuplicationRule: only when the FRD's "Uniqueness - Duplicate Record Check" row states
  a check; columns = the STTM Primary Key (Soham, pair_03), blank + flagged without one.
- NullCheckRule: the fields the STTM names for a DQ check (its "include in DQ check" Y
  cells, its DQ rules sheet's null-check rows naming a field of the feed) - the STTM wins
  over an FRD "NA"; else an FRD-stated incomplete-record rejection (key / required cols).
- No DataTypeCastRule; DateConversionRule only where a load rule states the formats.
- What is only derivable is a review-copy suggestion (``iig_dq_not_generated:``).
The synthetic pair 4 under the ACFC overlay's DQ knobs.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import yaml

from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.metadata_template import (
    dq_not_generated_flags,
    frd_dq_check,
    sttm_dq_null_columns,
    template_tab_rows,
)
from test_iig_dq_rules import DQ, DQ_KEYS, _v
from test_iig_v2_derivations import ACFC_OVERLAY, REPO

STATED_KEYS = (*DQ_KEYS, "dq_stated_only", "dq_frd_check_labels", "dq_no_check_words",
               "dq_sheet_null_values", "dq_sheet_field_headers", "dq_sheet_rule_headers",
               "dq_trim_rule_regex")
DEDUP = "Uniqueness - Duplicate Record Check (Reject HARD - In pipeline)"
NULLS = "Incomplete Record Rejection Process (HARD - In pipeline)"


@pytest.fixture(scope="module")
def stated(tmp_path_factory):
    """(config, template, FRD feed) - pair 4 with the ACFC overlay's DQ knobs."""
    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from multi_table_golden import PAIR4_OVERLAY

    acfc = yaml.safe_load(ACFC_OVERLAY.read_text(encoding="utf-8"))
    knobs = {k: v for k, v in acfc["metadata"]["templates"]["iig_v2"].items()
             if k in STATED_KEYS}
    assert knobs["dq_stated_only"] is True
    overlay = tmp_path_factory.mktemp("dq") / "dq.yaml"
    overlay.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": knobs}}}),
                       encoding="utf-8")
    config = load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY, overlay])
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    return config, config.metadata.templates["iig_v2"], frd.feeds[0]


def _rows(stated, spec):
    config, tpl, feed = stated
    return template_tab_rows(DQ, feed, config, spec, None, tpl)


def _classes(rows) -> list[str]:
    return [_v(r, "RULE_CLASS") for r in rows]


def _with(spec, rules=None, change=None, sheet=None):
    update = {}
    if rules is not None:
        update["validation_rules"] = rules
    if sheet is not None:
        update["dq_sheet_rows"] = sheet
    if change is not None:
        update["segments"] = [s.model_copy(update={"fields": [change(f) for f in s.fields]})
                              for s in spec.segments]
    return spec.model_copy(update=update)


# ---------------------------------------------------------------- the FRD's rows

@pytest.mark.parametrize("value, stated_text", [
    ("NA", None), ("N/A", None), ("None", None), ("TBD", None), ("", None),
    ("No rejection, load the file as it is", None),
    ("True duplicate records will be rejected", "True duplicate records will be rejected"),
])
def test_the_frds_duplicate_row_states_a_check_or_none(stated, value, stated_text):
    _config, tpl, _feed = stated
    assert frd_dq_check([f"{DEDUP}: {value}"], tpl, "dedup") == stated_text
    assert frd_dq_check([f"{NULLS}: {value}"], tpl, "dedup") is None      # another row


# ---------------------------------------------------------------- the rows written

def test_nothing_stated_no_key_rule_and_no_cast_rule(stated, pair4_spec):
    """The pair_11 shape: the FRD answers NA, the STTM names no DQ field - the key,
    required and typed columns alone write NO NullCheck / DeDup / cast row."""
    spec = _with(pair4_spec, rules=[f"{DEDUP}: NA", f"{NULLS}: NA"])
    classes = _classes(_rows(stated, spec))
    for rule in ("NullCheckRule", "DeDuplicationRule", "DataTypeCastRule"):
        assert rule not in classes, classes


def test_a_stated_duplicate_check_keys_on_the_sttm_primary_key(stated, pair4_spec):
    spec = _with(pair4_spec, rules=[f"{DEDUP}: Duplicate records will be rejected"])
    (dedup,) = [r for r in _rows(stated, spec) if _v(r, "RULE_CLASS") == "DeDuplicationRule"]
    key = [f.stage_column for f in pair4_spec.segments[1].fields if f.primary_key]
    assert key and _v(dedup, "SOURCE_COLUMN").split(",") == key
    # 2026-10-14 (framework owner, the pair_9 goldens): INPUT_PARAM = the target table's
    # FQN <catalog>.<schema>.<table> (moved here from test_iig_corpus_cells, post171)
    stage = pair4_spec.segments[1].stage_table
    assert _v(dedup, "INPUT_PARAM").endswith(f".{stage.schema_name}.{stage.table}")
    assert _v(dedup, "RULE_TYPE") == "Predefined"


def test_a_stated_duplicate_check_without_a_key_is_written_blank_and_flagged(stated,
                                                                            pair4_spec):
    spec = _with(pair4_spec, rules=[f"{DEDUP}: Duplicate records will be rejected"],
                 change=lambda f: f.model_copy(update={"primary_key": False,
                                                       "standard_primary_key": None}))
    (dedup,) = [r for r in _rows(stated, spec) if _v(r, "RULE_CLASS") == "DeDuplicationRule"]
    assert _v(dedup, "SOURCE_COLUMN") in ("", None)
    assert dedup["SOURCE_COLUMN"]["badge_entry"]["badge"] == "needs_template"     # flagged


def test_the_sttm_wins_for_the_null_check(stated, pair4_spec):
    """The FRD says NA; the STTM names two fields for the DQ check (one by its own
    cell, one on the DQ rules sheet) - those two are the NullCheckRule's columns."""
    detail = pair4_spec.segments[1].fields
    first, second = detail[0], detail[1]
    spec = _with(pair4_spec, rules=[f"{NULLS}: NA"],
                 change=lambda f: f.model_copy(update={"dq_check": f is first}),
                 sheet=[{"FieldName": second.source_column, "DQ Rules": "Don't allow nulls",
                         "DataType": "varchar"},
                        {"FieldName": "NOT_A_FIELD_OF_THIS_FEED", "DQ Rules":
                         "Don't allow nulls", "DataType": "varchar"},
                        {"FieldName": detail[2].source_column, "DQ Rules": "Allow null values",
                         "DataType": "varchar"}])
    (null,) = [r for r in _rows(stated, spec) if _v(r, "RULE_CLASS") == "NullCheckRule"]
    assert _v(null, "SOURCE_COLUMN").split(",") == [first.stage_column, second.stage_column]
    _config, tpl, _feed = stated
    assert sttm_dq_null_columns(spec, detail, tpl)[1] == 1        # the unmatched sheet row


# ---------------------------------------------------------------- the review copy

def test_what_is_only_derivable_is_a_review_suggestion(stated, pair4_spec):
    _config, tpl, _feed = stated
    spec = _with(pair4_spec, rules=[f"{DEDUP}: NA"],
                 sheet=[{"FieldName": "NOT_A_FIELD_OF_THIS_FEED",
                         "DQ Rules": "Don't allow nulls"}])
    flags = dq_not_generated_flags(spec, tpl)
    assert any(f.startswith("iig_dq_not_generated:DeDuplicationRule") for f in flags)
    assert any(f.startswith("iig_dq_not_generated:NullCheckRule") and "1 null-check field"
               in f for f in flags)
    assert any(f.startswith("iig_dq_not_generated:DataTypeCastRule") for f in flags)
    assert dq_not_generated_flags(spec, SimpleNamespace(dq_stated_only=False)) == []


def test_the_review_copy_lists_the_suggestions(stated):
    config, _tpl, _feed = stated
    assert "iig_dq_not_generated:" in config.iig_review.review_flag_prefixes


# ---------------------------------------------------------------- the STTM reader

def test_the_include_in_dq_check_cell_is_read_never_inferred():
    """pair 7's shape: "Mandatory Fields (Include in DQ Check)" Y on the mandatory
    fields, empty on the others - read as yes / unknown (None), never as no."""
    from acfc_shapes import FIXTURE_ROOT
    from codegen.extract import generic
    from codegen.layout.discover import discover

    config = load_config(REPO / "config" / "config.yaml")
    workbook = FIXTURE_ROOT / "sttm" / "pair_7_family_e.xlsx"
    ir = generic.read_workbook(discover(workbook, config.extractor), workbook.name, config)
    rows = ir.sheets[0].fields
    read = [generic._dq_check(r, config.extractor.discovery) for r in rows]
    stated = [r.values.get("rules.dq_mandatory") for r in rows]
    assert read == [True if s == "Y" else None for s in stated]
    assert read.count(True) >= 2 and None in read


def test_the_feeds_review_copy_carries_the_suggestions(stated, pair4_spec, tmp_path):
    """End to end on pair 4 (framework mode): the suggestion reaches the review copy's
    summary sheet - the one place the BSA reads it."""
    import openpyxl

    from codegen import cli

    config, _tpl, _feed = stated
    spec = _with(pair4_spec, rules=[f"{DEDUP}: NA"])
    scoped = config.model_copy(update={"output": config.output.model_copy(
        update={"dir": str(tmp_path)})})
    result = cli.generate_feed_result(spec, scoped, dry_run=True, skip_tests=True,
                                      output_mode="framework", conventions_profile="acfc_prx",
                                      iig_template="iig_v2", console=False)
    assert any(f.startswith("iig_dq_not_generated:") for f in
               result.framework_artefacts.review_flags)
    (review,) = tmp_path.rglob("*_IIG_REVIEW.xlsx")
    summary = openpyxl.load_workbook(review, read_only=True).worksheets[0]
    texts = [str(c) for row in summary.iter_rows(values_only=True) for c in row if c]
    assert any(t.startswith("iig_dq_not_generated:DeDuplicationRule") for t in texts)
