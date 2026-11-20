"""post193: the incident tracker's CodeGen items 11, 12 and 13 (a staging Accumulators
run, reproduced on the tester's documents first - mock, /tmp).

- 11: the FRD's incomplete-record row says "No Rejection (Load As-IS)" - the stage load
  rejects every row with a listed field null, so ADLS MANDATORY_FIELD_LIST is left EMPTY
  (never "NA": the notebook reads it as a column name), the reason quoted from the FRD.
- 13: the FRD's duplicate row rejects only TRUE duplicates (every field equal) - the
  DeDuplicationRule lists every data column of the detail table, not the STTM key (a
  member key rejects that member's valid records).
- 12: the standard load splits STGDELTA SRC_DATA_TYPE on commas, so the ACFC overlay
  writes base types ('String:Decimal', the pair-1 golden's form): one piece per column.

The synthetic pair 4 under the ACFC overlay's knobs (as tests/test_dq_stated_only.py).
"""

from __future__ import annotations

import json

import pytest
import yaml

from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.metadata_template import frd_dq_check, template_tab_rows
from test_dq_stated_only import DEDUP, NULLS, STATED_KEYS, _with
from test_iig_dq_rules import DQ, _v
from test_iig_v2_derivations import ACFC_OVERLAY, REPO

ADLS = "ADLS_DELTA_INGESTION_DETAILS"
STG_STD = "STGDELTA_STDDELTA_INGESTION_DET"
KEYS = (*STATED_KEYS, "dq_no_rejection_words", "dq_true_duplicate_words", "data_type_style")


@pytest.fixture(scope="module")
def acfc(tmp_path_factory):
    """(config, template, FRD feed) - pair 4 with the ACFC overlay's DQ + type knobs."""
    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from multi_table_golden import PAIR4_OVERLAY

    shipped = yaml.safe_load(ACFC_OVERLAY.read_text(encoding="utf-8"))
    knobs = {k: v for k, v in shipped["metadata"]["templates"]["iig_v2"].items() if k in KEYS}
    assert set(KEYS) - set(knobs) <= {"dq_trim_rule_regex"}, set(KEYS) - set(knobs)
    overlay = tmp_path_factory.mktemp("post193") / "knobs.yaml"
    overlay.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": knobs}}}),
                       encoding="utf-8")
    config = load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY, overlay])
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    return config, config.metadata.templates["iig_v2"], frd.feeds[0]


def _rows(acfc, tab, spec):
    config, tpl, feed = acfc
    return template_tab_rows(tab, feed, config, spec, None, tpl)


# ------------------------------------------------------------- 11: no rejection

@pytest.mark.parametrize("value, says_no_rejection", [
    ("No Rejection (Load As-IS)", True),        # the staging FRD's wording
    ("no rejection, load the file as it is", True),
    ("NA", False), ("", False), ("None", False),    # states nothing: the STTM list stays
    ("Incomplete records will be rejected", False),
])
def test_the_incomplete_record_row_says_no_rejection_or_not(acfc, value, says_no_rejection):
    from codegen.metadata_template import frd_states_no_rejection

    _config, tpl, _feed = acfc
    found = frd_states_no_rejection([f"{NULLS}: {value}"], tpl)
    assert (found is not None) is says_no_rejection
    assert frd_states_no_rejection([f"{DEDUP}: {value}"], tpl) is None   # another row


def test_no_rejection_leaves_the_mandatory_list_empty_with_the_frds_reason(acfc, pair4_spec):
    assert pair4_spec.not_null_columns, "the fixture must mark required columns"
    spec = _with(pair4_spec, rules=[f"{NULLS}: No Rejection (Load As-IS)"])
    rows = _rows(acfc, ADLS, spec)
    assert rows
    for row in rows:
        cell = row["MANDATORY_FIELD_LIST"]
        assert cell["value"] in ("", None)           # empty - never "NA"
        entry = cell["badge_entry"]
        assert entry["badge"] == "from_frd"          # sourced, so not an iig_blank gap
        assert "No Rejection (Load As-IS)" in json.dumps(entry)   # the FRD quoted
        assert entry.get("deliberate_blank") is True    # decided blank, not unstated


def test_the_review_copy_does_not_ask_for_the_decided_blank(acfc, pair4_spec):
    """The 12-pair check (pair_01): the empty list was listed "no document states it"."""
    from codegen.iig_review import _reason

    config, _tpl, _feed = acfc
    spec = _with(pair4_spec, rules=[f"{NULLS}: No Rejection (Load As-IS)"])
    for row in _rows(acfc, ADLS, spec):
        entry = row["MANDATORY_FIELD_LIST"]["badge_entry"]
        assert _reason("MANDATORY_FIELD_LIST", "", entry, set(), config.iig_review) is None


@pytest.mark.parametrize("rules", [[], [f"{NULLS}: NA"],
                                   [f"{NULLS}: Incomplete records will be rejected"]])
def test_otherwise_the_mandatory_list_is_the_sttms_required_columns(acfc, pair4_spec, rules):
    """Without post214's MandatoryColumnCheckRule (an overlay that does not configure it)."""
    config, tpl, feed = acfc
    tpl = tpl.model_copy(update={"dq_rules": [k for k in tpl.dq_rules
                                              if k != "std_mandatory_check"]})
    spec = _with(pair4_spec, rules=rules)
    for row in template_tab_rows(ADLS, feed, config, spec, None, tpl):
        assert _v(row, "MANDATORY_FIELD_LIST") == ",".join(pair4_spec.not_null_columns)


@pytest.mark.parametrize("rules", [[], [f"{NULLS}: NA"],
                                   [f"{NULLS}: Incomplete records will be rejected"]])
def test_post214_the_dq_rule_checks_them_and_the_list_is_a_decided_blank(acfc, pair4_spec,
                                                                         rules):
    spec = _with(pair4_spec, rules=rules)
    for row in _rows(acfc, ADLS, spec):
        cell = row["MANDATORY_FIELD_LIST"]
        assert cell["value"] in ("", None)
        assert cell["badge_entry"].get("deliberate_blank") is True
        assert "MandatoryColumnCheckRule" in cell["badge_entry"]["tooltip"]
    assert any(_v(r, "RULE_CLASS") == "MandatoryColumnCheckRule"
               for r in _rows(acfc, DQ, spec))


# ------------------------------------------------------------- 13: true duplicates

TRUE_DUP = ("True Duplicate records within the same file will be rejected and loaded to "
            "Reject table.")


def test_true_duplicates_are_read_on_word_boundaries(acfc):
    from codegen.metadata_template import frd_states_true_duplicates

    _config, tpl, _feed = acfc
    assert frd_states_true_duplicates(TRUE_DUP, tpl)
    assert not frd_states_true_duplicates("Duplicate records will be rejected", tpl)
    assert not frd_states_true_duplicates("untrue duplicates", tpl)
    assert not frd_states_true_duplicates(None, tpl)


def test_a_true_duplicate_check_lists_every_data_column(acfc, pair4_spec):
    _config, tpl, _feed = acfc
    spec = _with(pair4_spec, rules=[f"{DEDUP}: {TRUE_DUP}\nTable Name:\nx.y.z_reject"])
    assert frd_dq_check(spec.validation_rules, tpl, "dedup")
    (dedup,) = [r for r in _rows(acfc, DQ, spec) if _v(r, "RULE_CLASS") == "DeDuplicationRule"]
    detail = pair4_spec.segments[1]
    columns = [f.stage_column for f in detail.fields if f.stage_column]
    key = [f.stage_column for f in detail.fields if f.primary_key]
    assert key and len(columns) > len(key)               # the fixture can tell them apart
    assert _v(dedup, "SOURCE_COLUMN").split(",") == columns
    assert _v(dedup, "TARGET_COLUMN").split(",") == columns
    assert "True Duplicate" in json.dumps(dedup["SOURCE_COLUMN"]["badge_entry"])


def test_a_plain_duplicate_check_still_keys_on_the_sttm_primary_key(acfc, pair4_spec):
    spec = _with(pair4_spec, rules=[f"{DEDUP}: Duplicate records will be rejected"])
    (dedup,) = [r for r in _rows(acfc, DQ, spec) if _v(r, "RULE_CLASS") == "DeDuplicationRule"]
    key = [f.stage_column for f in pair4_spec.segments[1].fields if f.primary_key]
    assert _v(dedup, "SOURCE_COLUMN").split(",") == key


# ------------------------------------------------------------- 12: base types

def test_the_acfc_overlay_writes_base_source_types(acfc):
    _config, tpl, _feed = acfc
    assert tpl.data_type_style == "base"


def test_src_data_type_has_one_comma_piece_per_column(acfc, pair4_spec):
    """A decimal STTM type must not add a comma piece: the standard load splits the list."""
    decimal = pair4_spec.model_copy(update={"segments": [
        s.model_copy(update={"fields": [
            f.model_copy(update={"stage_datatype": "Decimal(12,2)",
                                 "standard_datatype": "Decimal(12,2)"})
            for f in s.fields]})
        for s in pair4_spec.segments]})
    for row in _rows(acfc, STG_STD, decimal):
        src = _v(row, "SRC_DATA_TYPE").split(",")
        assert len(src) == len(_v(row, "TGT_COLUMN_NAMES").split(","))
        assert "Decimal:Decimal" in src and not any("(" in t for t in src)
