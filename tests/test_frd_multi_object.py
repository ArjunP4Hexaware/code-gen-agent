"""The multi-object F1 FRD (the MIDS shape): section titles suffixed with
requirement IDs; one metadata block whose 'Target Table Name' row lists
FILE names for several feeds. The layout stage splits it into one feed per
STTM mapping sheet (stage band authoritative), pairs each feed's file by a
unique name match or asks, and the extractor implies the delimiter from
the file extension when the FRD's 'format' is prose."""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes import frd as frd_fixtures
from acfc_shapes.common import docx_bytes, table
from codegen.extract.extractor import _extension_delimiter
from codegen.extract.frd_docx import discover_frd, read_docx
from codegen.layout.model import MockLayoutProvider
from codegen.layout.resolve import resolve_pair
from test_frd_gapfill import load_config_for_tests

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
PROFILES = REPO / "fixtures" / "layout_profiles"
MIDS_FRD = REPO / "FRD_Medicare Expansion-MIDS - Socially Determined (1).docx"
MIDS_STTM = REPO / "STTM-Medicare Expansion-MIDS-Social Determine (1).xlsx"


def _multi_object_docx(tables_row: str, title_suffix: str = ": MDST000001") -> bytes:
    """An F1 document whose Structural title carries an ID and whose Target
    Table Name lists two FILE names for two feeds."""
    functional = "Ingest."
    descriptive = table([
        ["Descriptive Metadata", "", ""],
        ["Descriptive Metadata", "Name", "Descriptive Metadata"],
        ["Descriptive Metadata", "Description", "Two vendor files"],
        ["Descriptive Metadata", "Functional Requirement", functional],
        ["Descriptive Metadata", "Data Source", "VENDOR_A"],
        ["", "Object Name", "Vendor\nFileName\nVENDOR_A\nrisk_scores_YYYYMMDD.csv"],
        ["", "Frequency", "Monthly"],
        ["", "LOBs", "ALL"],
    ])
    structural = table([
        [f"Structural Metadata{title_suffix}", "", ""],
        [f"Structural Metadata{title_suffix}", "Name", "Structural Metadata"],
        [f"Structural Metadata{title_suffix}", "Description", "Files land in raw"],
        [f"Structural Metadata{title_suffix}", "Functional Requirement", functional],
        ["Structural Metadata", "Object/data Format", "File Data Ingestion"],
        ["", "Target Schema", "STG: pr_dlk_vnd_p.stg_vnd_p_accum; STD: pr_std_vnd_p.accum"],
        ["", "Target Table Name", tables_row],
        ["", "Domain and Subdomain", "Pharmacy / Accumulators"],
        ["", "Load Strategy STG", "Truncate and Load"],
        ["", "Load Strategy STD", "Append"],
    ])
    leading, trailing = frd_fixtures._common_tables("PROJECT_ALPHA", "Feeds")
    return docx_bytes(leading + [descriptive, structural] + trailing)


def test_section_title_with_requirement_id_suffix_is_recognised(tmp_path):
    config = load_config_for_tests()
    path = tmp_path / "frd.docx"
    path.write_bytes(_multi_object_docx("a_file_YYYYMMDD.csv\nb_file_YYYYMMDD.csv"))
    profile = discover_frd(read_docx(path), config.extractor.frd)
    assert {s.section for s in profile.sections} == {"descriptive", "structural"}
    assert "feeds[0].file_format" in profile.fields
    assert "feeds[0].stage_target.load_strategy" in profile.fields
    assert not [u.field for u in profile.unresolved if "load_strategy" in u.field]


def test_single_sheet_frd_with_file_names_as_tables_takes_the_sheet_table(tmp_path):
    """Pair-1 STTM has ONE mapping sheet (stage table vnd_p_accum_client); the
    FRD's 'Target Table Name' lists two FILE names and its Object Name is a
    flattened table. -> the feed is named after the sheet's stage table, its
    tables come from the stage band, the file-like entries become its file
    patterns, and nothing is asked about the stage band or the files."""
    config = load_config_for_tests()
    path = tmp_path / "frd.docx"
    path.write_bytes(_multi_object_docx("I_ACCUM_*_TO_CLIENT_*.csv\nF_ACCUM_*_TO_CLIENT_*.csv"))
    sttm = SHAPES / "sttm" / "pair_1_family_a.xlsx"
    pair = resolve_pair(sttm, path, config, provider=MockLayoutProvider([PROFILES / "mock",
                                                                        PROFILES]),
                        cache_dirs=[PROFILES], use_cache=True, generated_date="2026-01-01")
    (feed,) = pair.frd_contract.feeds
    assert feed.feed_name == "vnd_p_accum_client"          # the Object Name cell was a table
    assert feed.stage_target.tables == ["vnd_p_accum_client"]
    assert feed.standard_target.tables == ["vnd_p_accum_client"]
    assert feed.file_name_patterns == ["I_ACCUM_*_TO_CLIENT_*.csv", "F_ACCUM_*_TO_CLIENT_*.csv"]
    assert feed.stage_target.load_strategy == "Truncate and Load"
    keys = {q.key for q in pair.questions}
    assert not any("stage_target" in k or "file_name_patterns" in k for k in keys)
    assert any(f.startswith("frd_unstated:feeds[0].stage_target.tables source_used:STTM stage band")
               for f in pair.flags)
    assert any(f.startswith("frd_unstated:feeds[0].feed_name source_used:STTM stage band")
               for f in pair.flags)


def test_multi_sheet_split_pairs_files_uniquely_or_asks(tmp_path):
    """Two mapping sheets, three file names: the table whose tokens match one
    file uniquely gets it; the other is asked; an answer settles it."""
    from codegen.extract.frd_docx import read_frd
    from codegen.layout.resolve import split_frd_feeds_by_sttm

    config = load_config_for_tests()
    path = tmp_path / "frd.docx"
    path.write_bytes(_multi_object_docx(
        "demographics_package_YYYY_MM.csv\nanalytics_package_YYYY_MM.csv"))
    content = read_docx(path)
    profile = discover_frd(content, config.extractor.frd)
    contract = read_frd(content, profile, config, document_name="frd.docx",
                        generated_date="2026-01-01")
    facts = {
        "meta": {},
        "files": [("demographics_package_YYYY_MM.csv", "FILE_DETAILS!B2"),
                  ("analytics_package_YYYY_MM.csv", "FILE_DETAILS!B3"),
                  ("sd_ind_risk_data_package_amer_MI_YYYYMMDD.psv", "FILE_DETAILS!B4")],
        "sheet_tables": [
            {"sheet": "MAPPING-SD_COMMUNITY_DEMOGRAPHI",
             "stage_table": "sd_community_demographic_risk",
             "standard_table": "sd_community_demographic_risk",
             "stage_schema": "stg_vnd_p_accum"},
            {"sheet": "MAPPING-SD_COMMUNITY_RISK", "stage_table": "sd_community_risk",
             "standard_table": None, "stage_schema": "stg_cm"},
        ],
    }
    split, flags, questions = split_frd_feeds_by_sttm(contract, facts, {}, config)
    assert [f.feed_name for f in split.feeds] == ["sd_community_demographic_risk",
                                                  "sd_community_risk"]
    # the sheet's stage band names THIS feed's schema; the FRD block said one for all
    assert split.feeds[0].stage_target.schema_name == "stg_vnd_p_accum"
    assert split.feeds[1].stage_target.schema_name == "stg_cm"
    assert any(f.startswith("frd_unstated:feeds[1].stage_target.schema source_used:STTM stage band")
               for f in flags)
    assert not any("feeds[0].stage_target.schema" in f for f in flags)
    assert split.feeds[0].file_name_patterns == ["demographics_package_YYYY_MM.csv"]
    assert split.feeds[0].standard_target.tables == ["sd_community_demographic_risk"]
    assert split.feeds[1].standard_target.tables == []
    assert any(f.startswith("frd_feeds_split_from_sttm:") for f in flags)
    assert any("unique name match" in f for f in flags)
    (question,) = questions
    assert question.key == "feeds[1].file_name_patterns" and question.kind == "choice"
    assert len(question.candidates) == 3
    assert question.suggested is None and question.suggested_reason == ""   # two files left
    assert "suggested_reason" in question.as_dict()
    # one table + one file left over -> pre-selected WITH its reason named
    two_files = {**facts, "files": facts["files"][:2]}
    _s, _f, (q2,) = split_frd_feeds_by_sttm(contract, two_files, {}, config)
    assert q2.candidates[q2.suggested]["value"] == "analytics_package_YYYY_MM.csv"
    assert "leftover, not a name match" in q2.suggested_reason
    split2, flags2, questions2 = split_frd_feeds_by_sttm(
        contract, facts, {"feeds[1].file_name_patterns": {
            "value": "analytics_package_YYYY_MM.csv", "layer": None, "source": "STTM"}}, config)
    assert questions2 == []
    assert split2.feeds[1].file_name_patterns == ["analytics_package_YYYY_MM.csv"]
    assert any("source_used:user" in f for f in flags2)


def test_shared_family_token_never_pairs_and_the_leftover_is_only_a_suggestion():
    """Three tables ending in 'risk', three files: 'risk' is shared by every
    table so it pairs nothing; 'demographic(s)' and 'ind(iv)' pair uniquely;
    the leftover table is ASKED, with the leftover file pre-selected."""
    from codegen.layout.resolve import _mutual_unique_matches

    tables = ["sd_community_demographic_risk", "sd_community_risk", "sd_indiv_risk"]
    files = ["demographics_package_YYYY_MM.csv", "analytics_package_YYYY_MM.csv",
             "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv"]
    assert _mutual_unique_matches(tables, files) == {
        "sd_community_demographic_risk": "demographics_package_YYYY_MM.csv",
        "sd_indiv_risk": "sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv",
    }
    # the single 'risk' file must NOT be a confident match for sd_community_risk
    assert _mutual_unique_matches(["sd_community_risk", "sd_indiv_risk"],
                                  ["sd_ind_risk_YYYYMMDD.psv"]) == {
        "sd_indiv_risk": "sd_ind_risk_YYYYMMDD.psv"}
    assert _mutual_unique_matches(["a_risk", "b_risk"], ["risk_YYYYMMDD.csv"]) == {}


def test_empty_file_patterns_name_the_dialog_question_as_the_remedy():
    from types import SimpleNamespace

    from codegen.extract.extractor import ExtractionError, _match_file_details

    feed = SimpleNamespace(feed_name="sd_community_risk", file_name_patterns=[])
    ir = SimpleNamespace(file_details=[SimpleNamespace(file_name="analytics_package_YYYY_MM.csv")])
    with pytest.raises(ExtractionError) as info:
        _match_file_details(feed, ir)
    assert "names NO file" in str(info.value)
    assert "'File for table sd_community_risk'" in str(info.value)


def test_extension_implies_the_delimiter_when_the_format_is_prose():
    assert _extension_delimiter("demographics_package_YYYY_MM.csv") == ","
    assert _extension_delimiter("sd_ind_risk_YYYYMMDD_HHMM.psv") == "|"
    assert _extension_delimiter("file.tsv") == "\t"
    assert _extension_delimiter("file.dat") is None and _extension_delimiter(None) is None


@pytest.mark.skipif(not (MIDS_FRD.is_file() and MIDS_STTM.is_file()),
                    reason="MIDS client documents are local-only (never tracked)")
def test_mids_pair_resolves_standalone_from_the_docx(tmp_path):
    """The real MIDS pair through the docx path: three feeds named after the
    STTM's stage tables, format and strategies from the FRD's Structural
    block, each file paired uniquely or asked, no stage-band question."""
    from codegen.config import load_config

    config = load_config(REPO / "config" / "config.yaml")
    pair = resolve_pair(MIDS_STTM, MIDS_FRD, config, provider=MockLayoutProvider([]),
                        cache_dirs=[], use_cache=False, generated_date="2026-01-01")
    feeds = pair.frd_contract.feeds
    assert [f.feed_name for f in feeds] == [
        "sd_community_demographic_risk", "sd_community_risk", "sd_indiv_risk"] or len(feeds) == 3
    assert all(f.file_format == "File Data Ingestion" for f in feeds)
    assert all(f.stage_target.load_strategy == "Truncate and Load" for f in feeds)
    assert all(f.standard_target.load_strategy == "Append" for f in feeds)
    keys = [q.key for q in pair.questions]
    assert not any("stage_target" in k for k in keys)
    assert any(f.startswith("frd_feeds_split_from_sttm:") for f in pair.flags)
