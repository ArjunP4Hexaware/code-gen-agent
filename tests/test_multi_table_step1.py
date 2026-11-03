"""Multi-table Phase C step 1 — the STTM parser reads BOTH bands into tables,
and the feed's files follow the file rule (docs/acfc/MULTI_TABLE_DESIGN.md
rules 1, 2, 6).

* tables = the distinct (catalog, schema, table) triples per band — pair 4's
  three segments are three tables, pair 1's three segments ONE table;
* each table's stage_def / standard_def take catalog and schema from their
  own band (pair 4: PR_DLK.stg_nb_cob / PR_STD.nb_cob);
* files: a LOB-token pattern with N listed LOBs -> N files, otherwise one file
  per pattern (pair 1: four patterns, no LOB -> four files).
"""

from __future__ import annotations

import json

import pytest

from acfc_shapes import FIXTURE_ROOT, pair4_nb
from codegen.config import load_config
from codegen.contracts.tables import TableModelError, detail_table, feed_tables, split_tables
from codegen.resolve.files import expand_files, header_block_files, split_lobs
from conftest import ACFC_SHAPES, LAYOUT_PROFILES, REPO

PAIR4_OVERLAY = FIXTURE_ROOT / "pair_4" / "config_overlay.yaml"
TOKENS = ["<LOB>", "{LOB}", "[LOB]"]


@pytest.fixture(scope="module")
def pair4_config():
    return load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY])


@pytest.fixture(scope="module")
def pair4_feed(pair4_config):
    from codegen.extract import extract_contract

    contract = extract_contract(FIXTURE_ROOT / pair4_nb.STTM_PATH,
                                FIXTURE_ROOT / pair4_nb.FRD_PATH, pair4_config,
                                generated_date="2026-10-07")
    (feed,) = contract.feeds
    return feed


@pytest.fixture(scope="module")
def pair1_pair(pair1_config, tmp_path_factory):
    """Pair 1's real-shape documents through the layout stage (synonyms only),
    then the STTM contract — the same chain as conftest.pair1_spec."""
    from codegen.extract import extract_contract
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.model import MockLayoutProvider
    from codegen.layout.resolve import resolve_pair as resolve_layout_pair

    tmp = tmp_path_factory.mktemp("pair1_step1")
    provider = MockLayoutProvider([LAYOUT_PROFILES / "mock", LAYOUT_PROFILES])
    pair = resolve_layout_pair(
        ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx", ACFC_SHAPES / "frd" / "f1_pair_1.docx",
        pair1_config, provider=provider, cache_dirs=[tmp / "cache"],
        generated_date="2026-01-01")
    frd_json = tmp / "frd.contract.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    contract = extract_contract(ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx", frd_json,
                                pair1_config, generated_date="2026-01-01",
                                layout=pair.sttm.profile)
    (feed,) = contract.feeds
    return pair.frd_contract.feeds[0], feed


# ------------------------------------------------------------------ pair 4


def test_pair4_discovery_falls_through_to_content_and_reads_both_bands(pair4_config):
    from codegen.layout.discover import discover

    found = discover(FIXTURE_ROOT / pair4_nb.STTM_PATH, pair4_config.extractor)
    assert found.profile.strategy == "content"
    assert any("segmented family band labels incomplete" in d for d in found.diagnostics)
    (sheet,) = [s for s in found.profile.sheets if s.kind == "mapping"]
    assert {b.layer for b in sheet.bands} >= {"source", "stage", "standard"}


def test_pair4_three_segments_are_three_tables_from_both_bands(pair4_feed):
    tables = feed_tables(pair4_feed)
    assert [t.segments for t in tables] == [["Header"], ["Detail"], ["Trailer"]]
    for table, facts in zip(tables, pair4_nb.TABLES, strict=True):
        assert table.stage_def.triple == (pair4_nb.STAGE_CATALOG, pair4_nb.STAGE_SCHEMA,
                                          facts.table)
        assert table.standard_def is not None
        assert table.standard_def.triple == (pair4_nb.STANDARD_CATALOG,
                                             pair4_nb.STANDARD_SCHEMA, facts.table)
        assert [c.name for c in table.stage_def.columns] == [f.column for f in facts.fields]
        assert {c.datatype for c in table.stage_def.columns} == {pair4_nb.STAGE_TYPE}
        carried = [f for f in facts.fields if f.std_column is not None]
        assert [(c.name, c.datatype) for c in table.standard_def.columns] == [
            (f.std_column, f.std_type) for f in carried]
        assert table.stage_def.primary_key == [f.column for f in facts.fields if f.primary_key]
        assert table.standard_def.primary_key == [f.std_column for f in carried
                                                  if f.primary_key]
        assert table.stage_def.mandatory == [f.column for f in facts.fields if f.mandatory]
        assert [a.column for a in table.stage_def.audit_columns] == [
            c for c, _t in pair4_nb.AUDIT]
    assert detail_table(tables) is tables[1]
    assert split_tables(tables) == [tables[0], tables[2]]


def test_pair4_files_expand_per_header_block_lob(pair4_feed, pair4_config):
    files, flags = header_block_files(
        pair4_feed, pair4_config.extractor.lob_tokens,
        pair4_config.extractor.discovery.meta_blank_values)
    assert flags == []
    assert [f.lob for f in files] == pair4_nb.LOBS
    assert [f.pattern for f in files] == [
        pair4_nb.FILE_TEMPLATE.replace("<LOB>", lob) for lob in pair4_nb.LOBS]
    assert {f.template for f in files} == {pair4_nb.FILE_TEMPLATE}
    assert all(f.partition_value == f.lob for f in files)
    assert all("header block" in f.provenance for f in files)


def test_band_facts_add_nothing_to_the_contract_json_when_constant(pair4_feed):
    fields = json.loads(pair4_feed.model_dump_json(by_alias=True, exclude_defaults=True))
    keys = {k for f in fields["fields"] for k in f}
    assert "primary_key" in keys                  # stated Y on three detail rows
    assert not keys & {"stage_catalog", "stage_schema", "standard_catalog", "standard_schema",
                       "standard_mandatory", "standard_primary_key"}


# ------------------------------------------------------------------ pair 1


def test_pair1_three_segments_are_one_table(pair1_pair):
    _frd_feed, feed = pair1_pair
    (table,) = feed_tables(feed)
    assert table.segments == ["Header", "Detail", "Trailer"]
    assert table.stage_def.triple == (feed.stage.catalog, feed.stage.schema_name,
                                      feed.stage.table)
    assert table.stage_def.catalog is not None
    assert len(table.stage_def.columns) == 21          # the golden's 21 columns
    assert [a.column for a in table.stage_def.audit_columns] == [
        a.column for a in feed.audit_columns]
    assert table.standard_def is not None
    assert table.standard_def.triple == (feed.standard.catalog, feed.standard.schema_name,
                                         feed.standard.table)
    assert detail_table([table]) is table
    assert split_tables([table]) == []


def test_pair1_four_patterns_without_lob_are_four_files(pair1_pair, pair1_config):
    frd_feed, feed = pair1_pair
    blank = pair1_config.extractor.discovery.meta_blank_values
    assert header_block_files(feed, TOKENS, blank) == ([], [])   # File Names reads TBD
    files, flags = expand_files(frd_feed.file_name_patterns, split_lobs(feed.meta_rows.get("lob")),
                                TOKENS, provenance="FRD Object Name")
    assert flags == []
    assert len(files) == 4
    assert [f.pattern for f in files] == frd_feed.file_name_patterns
    assert all(f.lob is None and f.partition_value is None for f in files)


# ------------------------------------------------------------------ synthetic


def test_a_single_pattern_without_a_lob_token_is_one_file_even_with_lobs_listed():
    files, flags = expand_files(["ABC_RPT_CCYYMMDD.txt"], ["110", "120"], TOKENS)
    assert flags == []
    assert [(f.pattern, f.lob) for f in files] == [("ABC_RPT_CCYYMMDD.txt", None)]


def test_two_lobs_expand_a_token_pattern_to_two_files_case_insensitively():
    files, flags = expand_files(["XYZ_{lob}_*.csv"], split_lobs("A1; B2"), TOKENS)
    assert flags == []
    assert [(f.pattern, f.lob, f.template) for f in files] == [
        ("XYZ_A1_*.csv", "A1", "XYZ_{lob}_*.csv"), ("XYZ_B2_*.csv", "B2", "XYZ_{lob}_*.csv")]


def test_a_token_pattern_without_lobs_is_one_file_and_a_flag():
    files, flags = expand_files(["XYZ_<LOB>.txt"], [], TOKENS)
    assert [(f.pattern, f.lob) for f in files] == [("XYZ_<LOB>.txt", None)]
    assert flags and flags[0].startswith("lob_token_without_lobs:XYZ_<LOB>.txt")


def test_split_lobs_drops_placeholders_and_duplicates():
    assert split_lobs("110, 120\n120 / TBD", ["tbd"]) == ["110", "120"]


def test_the_table_name_decides_not_the_segment(pair4_feed):
    hdr, _dtl, _trl = (t.table for t in pair4_nb.TABLES)
    fields = [f.model_copy(update={"stage_table": hdr, "standard_table": hdr})
              if f.record_segment == "Trailer" else f for f in pair4_feed.fields]
    tables = feed_tables(pair4_feed.model_copy(update={"fields": fields}))
    assert [t.segments for t in tables] == [["Header", "Trailer"], ["Detail"]]
    assert split_tables(tables) == [tables[0]]


def test_a_differing_schema_alone_makes_another_table(pair4_feed):
    fields = [f.model_copy(update={"stage_schema": "stg_other"})
              if f.record_segment == "Trailer" else f for f in pair4_feed.fields]
    tables = feed_tables(pair4_feed.model_copy(update={"fields": fields}))
    assert [t.stage_def.schema_name for t in tables] == [
        pair4_nb.STAGE_SCHEMA, pair4_nb.STAGE_SCHEMA, "stg_other"]


def test_one_stage_table_naming_two_standard_tables_is_an_error(pair4_feed):
    fields = list(pair4_feed.fields)
    index = next(i for i, f in enumerate(fields) if f.stage_column == "MEMBER_ID")
    fields[index] = fields[index].model_copy(update={"standard_table": "elsewhere"})
    with pytest.raises(TableModelError, match="maps to 2 standard tables"):
        feed_tables(pair4_feed.model_copy(update={"fields": fields}))
