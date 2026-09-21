"""M2 — FRD .docx extractor (families F1/F2) reading through an FRD layout
profile (M2.5 §7 pulled forward).

Pins, per fixtures/acfc_shapes FRD document, which contract fields come out
filled and which stay empty under the SHAPES_FOR_PORT §2 label variants
alone, that every sourced field carries provenance (table/row/col + the
label seen), that F2 fields are attributed to the right section, and —
for M4 — exactly which pair-1 facts the FRD supplies versus the STTM.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen.cli import main
from codegen.contracts.frd import FrdContract, TargetSpec
from codegen.extract.frd_docx import (
    FrdDocxError,
    contract_to_json,
    discover_frd,
    extract_frd_contract,
    read_docx,
)
from codegen.layout.frd_profile import frd_fingerprint

REPO = Path(__file__).resolve().parents[1]
FRD = REPO / "fixtures" / "acfc_shapes" / "frd"
CONFIG = REPO / "config" / "config.yaml"
DATE = "2026-01-01"


@pytest.fixture(scope="module")
def pair1(config):
    return extract_frd_contract(FRD / "f1_pair_1.docx", config, generated_date=DATE)


@pytest.fixture(scope="module")
def pair2(config):
    return extract_frd_contract(FRD / "f1_pair_2_variant.docx", config, generated_date=DATE)


@pytest.fixture(scope="module")
def pair8(config):
    return extract_frd_contract(FRD / "f2_pair_8.docx", config, generated_date=DATE)


# ------------------------------------------------------------ F1 pair 1


def test_f1_pair1_fields_filled_and_empty(pair1):
    contract, profile = pair1
    assert profile.family == "F1" and profile.source == "synonyms"
    assert [s.section for s in profile.sections] == [
        "descriptive", "structural", "administrative", "technical", "data_quality", "vendor"]
    assert profile.unresolved == []
    (feed,) = contract.feeds
    filled = {
        "feed_name": "f1_pair_1.docx feed 1 (unnamed)",    # M9.3: flagged placeholder
        "source_system": "VENDOR_A",
        "file_format": "Fixed Width Text",
        "frequency": "Daily",
        "lobs": ["ALL"],
        "domain": "Pharmacy",
        "sub_domain": "Accumulators",
        "landing_location": "/Pharmacy/Accumulators/",
        "archive_retention": "Archive after load; retain 7 years",
        "phi_pii_notes": "CARDHOLDER_ID",
        "sttm_reference": "Accumulators VDD (VENDOR_A layout v2)",
        "requirement_ids": ["SYN-BR-001"],
        "recycle_rule": "Not applicable — no recycle process for this feed.",
    }
    for name, value in filled.items():
        assert getattr(feed, name) == value, name
    # M9.3: the target cell is an inline layer block — one table per layer,
    # never a raw line; the document states no schema and no catalog.
    assert feed.stage_target == TargetSpec(catalog=None, schema=None,
                                           tables=["vnd_p_accum_client"], load_strategy="Append")
    assert feed.standard_target == TargetSpec(catalog=None, schema=None,
                                              tables=["vnd_p_accum_client"], load_strategy="Append")
    # M9.3: the Object Name cell lists "<label>: <file>" lines — the patterns.
    assert feed.file_name_patterns == [
        "I_ACCUM_*_TO_CLIENT_*.csv", "I_ACCUM_*_FROM_CLIENT_*.csv",
        "F_ACCUM_*_TO_CLIENT_*.csv", "F_ACCUM_*_FROM_CLIENT_*.csv"]
    assert feed.delimiter is None
    assert feed.record_segments == [] and feed.load_windows_sla == []
    assert feed.history_backfill is None
    # Rules: the Functional Requirement, the acceptance criteria, the
    # technical rule rows, and every populated Data Quality row (labelled).
    assert feed.validation_rules[0].startswith("Ingest the Accumulators fixed-width files")
    assert feed.validation_rules[1].startswith("1. Header, Detail and Trailer records land")
    assert "Load the file as received; no business filtering." in feed.validation_rules
    assert "Dates yyyyMMdd to yyyy-MM-dd; amounts to decimal" in feed.validation_rules
    assert "None" not in feed.validation_rules                 # Filter Criteria: None = blank
    assert any(r.startswith("Uniqueness/Duplicate Record check/reject (HARD - In pipeline): ")
               for r in feed.validation_rules)
    assert contract.status == "PASS_WITH_FLAGS"                # one blank DQ row
    assert contract.provenance is not None
    assert [a for a in contract.provenance.ambiguities if "Referential check" in a]
    assert [a.acd_type for a in contract.assumptions_constraints_dependencies] == [
        "Assumption", "Constraint", "Dependency"]
    assert contract.project.project_name == "Functional Requirements Document — PROJECT_ALPHA"


def test_f1_pair1_every_sourced_field_has_provenance_with_label_seen(pair1):
    contract, profile = pair1
    (feed,) = contract.feeds
    evidence = contract.field_provenance
    expected_labels = {
        "feeds[0].feed_name": ("descriptive", "Object Name"),
        "feeds[0].source_system": ("descriptive", "Data Source"),
        "feeds[0].frequency": ("descriptive", "Frequency"),
        "feeds[0].lobs": ("descriptive", "LOBs"),
        "feeds[0].file_format": ("structural", "Object/data Format"),
        "feeds[0].stage_target.schema": ("structural", "Target Catalog and Schema"),
        "feeds[0].stage_target.tables": ("structural", "Target Table Name"),
        "feeds[0].domain": ("structural", "Domain and Subdomain"),
        "feeds[0].stage_target.load_strategy": ("structural", "Load Strategy STG"),
        "feeds[0].standard_target.load_strategy": ("structural", "Load Strategy STD (View)"),
        "feeds[0].landing_location": ("structural", "ADLS Location"),
        "feeds[0].landing_location (confirming)": ("structural", "Inbound File Folder Path"),
        "feeds[0].archive_retention": ("structural", "Archive Schedule"),
        "feeds[0].sttm_reference": ("structural", "Source Data Dictionary"),
        "feeds[0].phi_pii_notes": ("technical", "PII Fields"),
        "feeds[0].requirement_ids": ("descriptive", "Traced/Related Requirements"),
        "feeds[0].recycle_rule": ("data_quality", "Record Recycle Process (HARD - In pipeline)"),
    }
    for path, (section, label) in expected_labels.items():
        assert path in evidence, path
        assert (evidence[path].section, evidence[path].label) == (section, label), path
        assert evidence[path].source == "synonyms"
    # Every non-empty scalar feed field is sourced.
    for name in ("feed_name", "source_system", "file_format", "frequency", "domain",
                 "landing_location", "archive_retention", "phi_pii_notes", "sttm_reference",
                 "recycle_rule"):
        assert f"feeds[0].{name}" in evidence, name
    assert len([k for k in evidence if k.startswith("feeds[0].validation_rules[")]) == 10
    # Table coordinates are real: the label cell text at (table,row,col) is the label.
    tables = read_docx(FRD / "f1_pair_1.docx").tables
    for path, item in evidence.items():
        assert tables[item.table][item.row][item.col] == item.label, path
    # ADLS Location is primary; the inbound folder is a confirming source, not a conflict.
    assert feed.landing_location == "/Pharmacy/Accumulators/"
    assert contract.layout is not None
    assert contract.layout.family == "F1" and contract.layout.fingerprint == profile.fingerprint


def test_pair1_real_shape_cells_are_parsed_flagged_and_cited(pair1):
    """M9.3 — the three real-shape cells of the pair-1 FRD: the inline layer
    block, the file-list Object Name cell and the feed no cell names."""
    contract, _profile = pair1
    flags = {f.split(":")[0]: f for f in contract.extraction_flags}
    assert list(flags) == ["frd_layer_block", "file_pattern_from_object_name",
                           "frd_feed_name_unstated"]
    assert "table 5 row 6 ('Target Table Name')" in flags["frd_layer_block"]
    assert "stage table='vnd_p_accum_client'; standard table='vnd_p_accum_client'" \
        in flags["frd_layer_block"]
    assert "never as a table name" in flags["frd_layer_block"]
    assert "table 4 row 5 ('Object Name')" in flags["file_pattern_from_object_name"]
    assert "labelled_files value, not a name" in flags["frd_feed_name_unstated"]
    # The refused Object Name cell is recorded, its lines kept per label.
    refused = contract.structured["feeds[0].feed_name"]
    assert refused.kind == "labelled_files" and refused.label == "Object Name"
    assert [(r.values["label"], r.key) for r in refused.rows][0] == (
        "LOB_A outbound", "I_ACCUM_*_TO_CLIENT_*.csv")
    # Provenance: both tables cite the one cell they were read from.
    evidence = contract.field_provenance
    assert evidence["feeds[0].stage_target.tables"].label == "Target Table Name"
    assert evidence["feeds[0].standard_target.tables"].label == "Target Table Name"
    # No raw line of the block ever reaches a list.
    (feed,) = contract.feeds
    for tables in (feed.stage_target.tables, feed.standard_target.tables):
        assert not any(":" in t or "Layer" in t for t in tables)


def test_layer_block_parser_variants(config):
    from codegen.extract.frd_docx import parse_layer_blocks

    frd = config.extractor.frd
    assert parse_layer_blocks("plain_table", frd) is None
    assert parse_layer_blocks("STG: a.b; STD: c.d", frd) is None
    assert parse_layer_blocks("Staging Layer:\nTable: t1\nStandard Layer:\nTable: t2", frd) == {
        "stage": {"table": "t1"}, "standard": {"table": "t2"}}
    full = parse_layer_blocks(
        "stage layer\nCatalog : cat1\nSchema: s1\nTable Name: t1\nowner: someone\n"
        "STD Layer:\nSchema Name: s2\nTarget Table: t2", frd)
    assert full == {"stage": {"catalog": "cat1", "schema": "s1", "table": "t1"},
                    "standard": {"schema": "s2", "table": "t2"}}
    # A heading with nothing beneath it parses to an empty layer, never a table.
    assert parse_layer_blocks("Staging Layer:", frd) == {"stage": {}}


def test_unnamed_feed_is_a_flag_never_a_silent_default(config, tmp_path):
    """A document whose Object Name row is absent (and whose Name row is
    blank) still extracts — under a placeholder name AND a flag."""
    from acfc_shapes import frd as frd_fixtures
    from acfc_shapes.common import docx_bytes
    from codegen.extract.frd_docx import is_unnamed_feed

    sections = [
        frd_fixtures._section("Descriptive Metadata", "", "d", "Ingest.",
                              [lab for lab in frd_fixtures.DESCRIPTIVE if lab != "Object Name"],
                              {"Data Source": "VENDOR_Z", "Frequency": "Daily", "LOBs": "ALL"}),
        frd_fixtures._section("Structural Metadata", "", "s", "Ingest.",
                              frd_fixtures.STRUCTURAL_P1,
                              {"Object/data Format": "csv", "Target Table Name": "t1",
                               "Target Catalog and Schema": "stg_z",
                               "Domain and Subdomain": "D / S", "Load Strategy STG": "Append",
                               "Load Strategy STD (View)": "Append"}),
    ]
    path = tmp_path / "unnamed.docx"
    path.write_bytes(docx_bytes(sections))
    contract, _ = extract_frd_contract(path, config, generated_date=DATE)
    (feed,) = contract.feeds
    assert is_unnamed_feed(feed.feed_name) and feed.feed_name.startswith("unnamed.docx feed 1")
    (flag,) = [f for f in contract.extraction_flags if f.startswith("frd_feed_name_unstated")]
    assert "no Object Name value" in flag and "no usable Name row" in flag


def test_pair1_split_of_facts_between_frd_and_sttm_for_m4(pair1):
    """What M4 can take from the FRD (this extractor) and what it must take
    from the pair-1 STTM instead — pinned so M4 has no surprises."""
    contract, _profile = pair1
    (feed,) = contract.feeds
    from_frd = {
        "feed_name": feed.feed_name, "source_system": feed.source_system,
        "file_format": feed.file_format, "frequency": feed.frequency, "lobs": feed.lobs,
        "domain": feed.domain, "sub_domain": feed.sub_domain,
        "landing_location": feed.landing_location,
        "stage catalog.schema.table": f"{feed.stage_target.catalog}.{feed.stage_target.schema_name}"
                                      f".{feed.stage_target.tables[0]}",
        "standard catalog.schema.table": f"{feed.standard_target.catalog}."
                                         f"{feed.standard_target.schema_name}."
                                         f"{feed.standard_target.tables[0]}",
        "load strategy STG/STD": (feed.stage_target.load_strategy,
                                  feed.standard_target.load_strategy),
    }
    assert from_frd == {
        # M9: the real-shape FRD names no feed, no schema and no catalog —
        # the STTM bands supply them (flagged by the resolver).
        "feed_name": "f1_pair_1.docx feed 1 (unnamed)", "source_system": "VENDOR_A",
        "file_format": "Fixed Width Text", "frequency": "Daily", "lobs": ["ALL"],
        "domain": "Pharmacy", "sub_domain": "Accumulators",
        "landing_location": "/Pharmacy/Accumulators/",
        "stage catalog.schema.table": "None.None.vnd_p_accum_client",
        "standard catalog.schema.table": "None.None.vnd_p_accum_client",
        "load strategy STG/STD": ("Append", "Append"),
    }
    # From the STTM (fixtures/acfc_shapes/sttm/pair_1_family_a.xlsx), not the FRD
    # (the file patterns ARE the FRD's since M9 — its Object Name cell lists them):
    from_sttm_only = {"delimiter": feed.delimiter, "record_segments": feed.record_segments}
    assert from_sttm_only == {"delimiter": None, "record_segments": []}
    assert len(feed.file_name_patterns) == 4


# ------------------------------------------------------------ F1 pair 2 variant


def test_f1_pair2_variant_labels_blanks_and_two_feeds(pair2):
    contract, profile = pair2
    assert profile.family == "F1"
    assert [s.section for s in profile.sections] == [
        "descriptive", "structural", "administrative", "technical", "data_quality", "vendor"] * 2
    assert [s.feed_index for s in profile.sections] == [0] * 6 + [1] * 6
    assert [f.feed_name for f in contract.feeds] == ["FEED_2 Claims", "FEED_2 Members"]
    for index, (feed, sub) in enumerate(zip(contract.feeds, ("Claims", "Members"), strict=True)):
        # Object Name blank → the section's Name row is the cited fallback.
        assert contract.field_provenance[f"feeds[{index}].feed_name"].label == "Name"
        assert feed.source_system == "VENDOR_B" and feed.file_format == "csv"
        assert feed.frequency == "Daily" and feed.lobs == ["ALL"]
        assert (feed.domain, feed.sub_domain) == ("Claims", sub)
        assert feed.stage_target == TargetSpec(catalog=None, schema="stg_vendor_b",
                                               tables=[f"feed_2_{sub.lower()}"],
                                               load_strategy="Truncate and Load")
        assert feed.standard_target.load_strategy == "Upsert"
        assert feed.standard_target.schema_name == "vendor_b"
        # Blank by the document (SHAPES_FOR_PORT §4, pair 2): ADLS Location,
        # Archive Schedule, Functional Requirement, Traced/Related Requirements.
        # ADLS Location blank → the inbound-folder variant label (a
        # confirming source on the same slot) supplies the landing location.
        assert feed.landing_location == "inbound/vendor_b"
        assert (contract.field_provenance[f"feeds[{index}].landing_location"].label
                == "Inbound/outbound File Folder Path")
        assert feed.archive_retention is None
        assert feed.requirement_ids == [] and feed.recycle_rule is None
        assert feed.validation_rules == [
            "Load as is",
            "Uniqueness/Duplicate Record check/reject (HARD - In pipeline): Duplicates on "
            "MEMBER_ID rejected.",
        ]
        labels = {contract.field_provenance[k].label for k in contract.field_provenance
                  if k.startswith(f"feeds[{index}].")}
        assert {"Target Schema", "Load Strategy STD", "Load Strategy STG"} <= labels
    assert contract.status == "PASS_WITH_FLAGS"
    blank = [a for a in contract.provenance.ambiguities if "value blank" in a]
    assert any("'Object Name' present, value blank" in a for a in blank)
    assert any("'Functional Requirement' present, value blank" in a for a in blank)
    # Labels with no contract slot (owners, stewards, SLA …) are logged, never mapped.
    assert any("'Business Owner'" in n for n in profile.notes)
    assert any("'Service Level Agreement'" in n for n in profile.notes)


# ------------------------------------------------------------ F2 pair 8


def test_f2_pair8_fields_attributed_to_sections(pair8):
    contract, profile = pair8
    assert profile.family == "F2" and profile.unresolved == []
    assert [s.section for s in profile.sections] == [
        "descriptive", "structural", "administrative", "technical", "data_quality", "vendor",
        "recycle", "email"]
    (feed,) = contract.feeds
    assert feed.feed_name == "FEED_8" and feed.source_system == "VENDOR_H"
    assert feed.frequency == "Weekly" and feed.lobs == ["ALL"]
    assert feed.file_format == "Fixed Width Text"
    assert (feed.domain, feed.sub_domain) == ("Claims", "Encounters")
    assert feed.stage_target == TargetSpec(catalog=None, schema="stg_feed8",
                                           tables=["feed_8_hdr", "feed_8_dtl", "feed_8_trl",
                                                   "feed_8_ftr"],
                                           load_strategy="Truncate and Load")
    assert feed.standard_target.schema_name == "feed8"
    assert feed.standard_target.load_strategy == "Append"
    assert feed.phi_pii_notes == "MEMBER_KEY" and feed.requirement_ids == ["SYN-BR-001"]
    assert feed.recycle_rule == "Recycle DR records whose MEMBER_KEY is not found; retain 10 days."
    # One rule per Solution Requirement (its Functional Requirement row), in
    # document order; acceptance-criteria boilerplate is not a rule.
    assert feed.validation_rules == [
        "Register the feed in the data catalog.",
        "Create feed_8_hdr/dtl/trl/ftr tables in both layers.",
        "Record owners and stewards.",
        "Apply the STTM load rules.",
        "Reject records whose length does not match the segment layout.",
        "Record vendor facts.",
        "Recycle DR records whose MEMBER_KEY is not found; retain 10 days.",
        "Send success and failure emails.",
    ]
    evidence = contract.field_provenance
    # Row-4 inline pairs cite the SR table, row 4, the section label and the inline label.
    frequency = evidence["feeds[0].frequency"]
    assert (frequency.section, frequency.row, frequency.label, frequency.inline_label) == (
        "descriptive", 4, "Descriptive Metadata", "Frequency")
    assert evidence["feeds[0].stage_target.schema"].section == "structural"
    assert evidence["feeds[0].stage_target.schema"].inline_label == "Target Schema"
    assert evidence["feeds[0].recycle_rule"].section == "recycle"
    assert evidence["feeds[0].recycle_rule"].label == "Functional Requirement:"
    rule_sections = [evidence[f"feeds[0].validation_rules[{n}]"].section for n in range(8)]
    assert rule_sections == ["descriptive", "structural", "administrative", "technical",
                             "data_quality", "vendor", "recycle", "email"]
    assert contract.status == "PASS"


# ------------------------------------------------------------ mechanics


def test_output_is_byte_stable_and_cli_writes_contract_and_profile(config, tmp_path):
    first, _ = extract_frd_contract(FRD / "f1_pair_1.docx", config, generated_date=DATE)
    second, _ = extract_frd_contract(FRD / "f1_pair_1.docx", config, generated_date=DATE)
    assert contract_to_json(first) == contract_to_json(second)
    out = tmp_path / "pair1.contract.json"
    profile_path = tmp_path / "pair1.profile.json"
    assert main(["extract-frd", "--config", str(CONFIG), "--docx", str(FRD / "f1_pair_1.docx"),
                 "--out", str(out), "--profile", str(profile_path),
                 "--generated-date", DATE]) == 0
    assert out.read_text(encoding="utf-8") == contract_to_json(first)
    reloaded = FrdContract.model_validate(json.loads(out.read_text(encoding="utf-8")))
    assert reloaded.feeds[0].feed_name == "f1_pair_1.docx feed 1 (unnamed)"
    assert reloaded.extraction_flags == first.extraction_flags != []
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    assert profile["family"] == "F1" and profile["source"] == "synonyms"
    assert "feeds[0].frequency" in profile["fields"]
    # A profile carries positions and labels only — never a document value.
    assert "VENDOR_A" not in profile_path.read_text(encoding="utf-8")


def test_fingerprint_is_over_labels_not_values(config):
    content = read_docx(FRD / "f1_pair_1.docx")
    baseline = frd_fingerprint(content.tables)
    tables = [[list(row) for row in table] for table in content.tables]
    tables[5][4][2] = "VENDOR_CHANGED"            # a value cell
    assert frd_fingerprint(tables) == baseline
    tables[5][4][1] = "Data Source (renamed)"     # a label cell
    assert frd_fingerprint(tables) != baseline


def test_unrecognised_document_is_loud(config, tmp_path):
    from acfc_shapes.common import docx_bytes, table

    path = tmp_path / "notes.docx"
    path.write_bytes(docx_bytes([table([["Term", "Definition"], ["STG", "Stage"]])]))
    with pytest.raises(FrdDocxError, match="no metadata section table"):
        discover_frd(read_docx(path), config.extractor.frd)
    assert main(["extract-frd", "--config", str(CONFIG), "--docx", str(path),
                 "--out", str(tmp_path / "x.json")]) == 1


def test_upstream_contract_shape_still_loads_and_docx_nulls_are_allowed():
    demo = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
    if demo.is_file():
        contract = FrdContract.model_validate(json.loads(demo.read_text(encoding="utf-8")))
        assert contract.field_provenance == {} and contract.layout is None
    spec = TargetSpec(catalog=None, schema=None, tables=[], load_strategy=None)
    assert spec.load_strategy is None
