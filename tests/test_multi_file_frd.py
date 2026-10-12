"""Multi-file FRD → multiple feeds: when a single F1 cycle lists >1 file
family in its Object Name cell and >1 target table, the parser splits into
one feed per target table and proposes the file→table pairing as a QUESTION.

Fixture text is from the real pair_2 (SD / MIDS) FRD's nested table:
  Vendor | INB/OUB | FileName               | FileName         | Vendor
  SD     | INB     | demographics_package…csv | Enrollment File  | MI
  SD     | INB     | analytics_package…csv   | Disenrollment…   | MI
  SD     | INB     | sd_ind_risk….psv        | HSW Report       | MI

Target Table Name cell (same document) lists the same three names
(newline-separated).  Both cells are one-per-line file names, not real table
names — the layout stage later replaces them with the STTM's own tables.
"""

from __future__ import annotations

import re

import pytest

from codegen.contracts.frd import FrdFeed, StructuredRow, StructuredValue, TargetSpec
from codegen.extract.frd_docx import (
    _canonical_pattern,
    _extract_patterns_from_structured,
    _name_similarity,
    _split_multi_file_feeds,
    is_unnamed_feed,
)

# --------------- fixture data (verbatim from pair_2 SD/MIDS FRD) ---------------

_NESTED_TABLE_ROWS = [
    StructuredRow(key="demographics_package_YYYY_MM.csv",
                  values={"Vendor": "SD", "INB/OUB": "INB",
                          "FileName": "demographics_package_YYYY_MM.csv",
                          "FileName_2": "Enrollment File", "Vendor_2": "MI"}),
    StructuredRow(key="analytics_package_YYYY_MM.csv",
                  values={"Vendor": "SD", "INB/OUB": "INB",
                          "FileName": "analytics_package_YYYY_MM.csv",
                          "FileName_2": "Disenrollment File", "Vendor_2": "MI"}),
    StructuredRow(key="sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
                  values={"Vendor": "SD", "INB/OUB": "INB",
                          "FileName": "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
                          "FileName_2": "HSW Report", "Vendor_2": "MI"}),
]

_STRUCTURED_NESTED = StructuredValue(
    kind="nested_table", table=17, row=5, col=2, label="Object Name",
    text=("Vendor\nINB/OUB\nFileName\nFileName\nVendor\nSD \nINB\n"
          "demographics_package_YYYY_MM.csv\nEnrollment File\nMI\n\n"
          "SD\nINB\nanalytics_package_YYYY_MM.csv\nDisenrollment File\nMI\n"
          "SD\nINB\nsd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv\n"
          "HSW Report\nMI"),
    headers=["Vendor", "INB/OUB", "FileName", "FileName_2", "Vendor_2"],
    rows=_NESTED_TABLE_ROWS,
)

_TABLES = [
    "demographics_package_YYYY_MM.csv",
    "analytics_package_YYYY_MM.csv",
    "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
]


def _make_feed(tables: list[str], patterns: list[str]) -> FrdFeed:
    """Minimal FrdFeed for the split tests."""
    return FrdFeed(
        feed_name="test_feed",
        source_system="TEST",
        file_name_patterns=patterns,
        file_format="csv",
        delimiter=None,
        record_segments=[],
        frequency=None,
        load_windows_sla=[],
        lobs=[],
        domain=None,
        sub_domain=None,
        landing_location=None,
        stage_target=TargetSpec(
            catalog=None, schema="stg", tables=tables, load_strategy="Truncate and Load"),
        standard_target=TargetSpec(
            catalog=None, schema="std", tables=[], load_strategy="Append"),
        validation_rules=[],
        recycle_rule=None,
        history_backfill=None,
        archive_retention=None,
        phi_pii_notes=None,
        sttm_reference=None,
        requirement_ids=[],
    )


# ---- _extract_patterns_from_structured -----------------------------------


def test_nested_table_extracts_three_file_patterns():
    patterns = _extract_patterns_from_structured(_STRUCTURED_NESTED)
    assert patterns == [
        "demographics_package_YYYY_MM.csv",
        "analytics_package_YYYY_MM.csv",
        "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
    ]


def test_multiline_text_is_not_extracted():
    """Multiline text may contain an incidental file name among non-file
    content — extracting it would steal a pattern from the real source."""
    sv = StructuredValue(
        kind="multiline", table=0, row=0, col=0, label="Object Name",
        text="demographics_package_CCYY_MM.csv; analytics_package_CCYY_MM.csv\n"
             "sd_ind_risk_data_package_amer_MI_CCYYMMDD_HHMM.psv")
    assert _extract_patterns_from_structured(sv) == []


def test_empty_structured_returns_no_patterns():
    sv = StructuredValue(
        kind="multiline", table=0, row=0, col=0, label="Object Name",
        text="Refer to the mapping document")
    assert _extract_patterns_from_structured(sv) == []


# ---- _canonical_pattern / _name_similarity --------------------------------


def test_ccyy_and_yyyy_are_equivalent():
    assert _canonical_pattern("demographics_CCYY_MM.csv") == \
           _canonical_pattern("demographics_YYYY_MM.csv")


def test_identical_names_have_similarity_one():
    assert _name_similarity(
        "demographics_package_YYYY_MM.csv",
        "demographics_package_YYYY_MM.csv") == 1.0


def test_disjoint_names_have_similarity_zero():
    assert _name_similarity("alpha_beta.csv", "gamma_delta.psv") == 0.0


def test_partial_overlap_returns_fraction():
    sim = _name_similarity(
        "demographics_package_YYYY_MM.csv",
        "demographics_extract_YYYY_MM.csv")
    assert 0.0 < sim < 1.0


# ---- _split_multi_file_feeds ---------------------------------------------


def test_single_feed_three_tables_three_files_splits_into_three():
    feed = _make_feed(_TABLES, [
        "demographics_package_YYYY_MM.csv",
        "analytics_package_YYYY_MM.csv",
        "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
    ])
    flags: list[str] = []
    ambiguities: list[str] = []
    result = _split_multi_file_feeds([feed], flags, ambiguities, "test.docx")

    assert len(result) == 3
    for f in result:
        assert len(f.stage_target.tables) == 1
        assert len(f.file_name_patterns) >= 1
        assert is_unnamed_feed(f.feed_name)
    # Each QUESTION flag names a proposed pairing.
    assert sum("QUESTION" in f for f in flags) == 3
    assert any("multi_file_frd" in a for a in ambiguities)


def test_single_table_single_file_is_not_split():
    feed = _make_feed(["one_table"], ["one_file_YYYY.csv"])
    result = _split_multi_file_feeds([feed], [], [], "test.docx")
    assert result == [feed]


def test_two_feeds_are_not_split():
    f1 = _make_feed(["t1"], ["f1_YYYY.csv"])
    f2 = _make_feed(["t2"], ["f2_YYYY.csv"])
    result = _split_multi_file_feeds([f1, f2], [], [], "test.docx")
    assert result == [f1, f2]


def test_name_similarity_guides_assignment():
    """The file whose name shares the most tokens with a table is paired to it."""
    feed = _make_feed(
        ["alpha_beta", "gamma_delta"],
        ["gamma_delta_YYYY.csv", "alpha_beta_YYYY.csv"],
    )
    result = _split_multi_file_feeds([feed], [], [], "test.docx")
    assert result[0].stage_target.tables == ["alpha_beta"]
    assert result[0].file_name_patterns == ["alpha_beta_YYYY.csv"]
    assert result[1].stage_target.tables == ["gamma_delta"]
    assert result[1].file_name_patterns == ["gamma_delta_YYYY.csv"]
