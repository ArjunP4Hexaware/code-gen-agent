"""M1 — content-driven STTM parsing through layout profiles.

Every fixtures/acfc_shapes STTM workbook is discovered (codegen.layout)
and read (codegen.extract.generic); the EXPECTED table below pins, per
fixture: the strategy that produced the profile, the mapping sheets found,
rows per band/segment, the roles resolved per layer, and the roles left
unresolved under the synonym tables ALONE — families A/C/E legitimately
leave the documented header oddities unresolved (M2.5's job; the tables
are deliberately not widened to force them). The test prints the table.

Contract emission is exercised where the layout resolves (families B, D,
E-pair-5) and refused loudly where it does not (pairs 1, 7, 8). The two
legacy strategies (MAPPING- prefix, segmented family) now also produce
profiles and carry provenance; their output is byte-checked elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from codegen.extract import ExtractionError, extract_contract
from codegen.extract.generic import read_workbook
from codegen.extract.workbook import ContentLayoutDetected, parse_workbook
from codegen.layout.discover import discover
from codegen.layout.fingerprint import fingerprint, header_bound
from segmented_fixture import build_workbook, frd_contract_dict

REPO = Path(__file__).resolve().parents[1]
STTM = REPO / "fixtures" / "acfc_shapes" / "sttm"
GENERATED_DATE = "2026-01-01"

TARGET_FULL = ["catalog", "column", "schema", "table", "target_type", "workspace"]
TARGET_SEG = ["catalog", "column", "constraints", "field_description", "mandatory_column",
              "primary_key", "schema", "table", "table_description", "target_type",
              "transformation"]

# fixture -> strategy, {mapping sheet -> (rows per segment, audit rows,
#                       {layer -> resolved roles}, [unresolved "layer/role"])}
EXPECTED: dict[str, tuple[str, dict]] = {
    "pair_1_family_a.xlsx": ("content", {
        # M9: the real-shape sheet resolves FULLY by synonyms ("… in DL",
        # "Format"); Detail counts the "Do Not Map" row — the reader keeps it,
        # the contract builder leaves it out with a field_unmapped flag.
        "FEED_1_MAPPING": (
            {"Header": 8, "Detail": 13, "Trailer": 3}, 3,
            {"source": ["description", "end", "field_name", "length", "ordinal", "required",
                        "segment", "source_type", "start"],
             "rules": ["critical", "data_definition", "load_rule", "not_null", "pii",
                       "primary_key"],
             "stage": TARGET_FULL,
             "standard": TARGET_FULL},
            [],
        )}),
    "pair_8_family_a.xlsx": ("content", {
        "FEED_8_LAYOUT": (
            {}, 0,
            {"source": ["key", "ordinal", "pii"], "stage": TARGET_FULL, "standard": TARGET_FULL},
            ["source/field_name"],
        )}),
    "pair_2_family_b.xlsx": ("mapping_prefix", {
        name: (
            {"-": 10 if name == "MAPPING-" else 12 if name == "MAPPING-1" else 10}, 3,
            {"source": ["comments", "description", "field_name", "mandatory", "null_check",
                        "pii", "sample_value", "source_type"],
             "stage": ["column", "schema", "table", "target_type"],
             "standard": ["column", "schema", "table", "target_type"]},
            [],
        ) for name in ("MAPPING-", "MAPPING-1", "MAPPING-2")}),
    "pair_3_family_c.xlsx": ("content", {
        "STTM": (
            {"-": 13}, 0,
            {"source": ["comments", "end", "field_name", "length", "source_type", "start"],
             "rules": ["critical", "data_definition", "dq_rules", "load_rule", "pii",
                       "primary_key", "required"],
             "stage": TARGET_FULL, "standard": TARGET_FULL},
            [],
        )}),
    "pair_4_family_d.xlsx": ("content", {
        "STTM": (
            {"-": 12}, 3,
            {"source": ["description", "end", "field_name", "length", "ordinal",
                        "source_type", "start"],
             "rules": ["critical", "data_definition", "load_rule", "not_null", "pii",
                       "primary_key"],
             "stage": TARGET_FULL, "standard": TARGET_FULL},
            [],
        )}),
    "pair_6_family_d.xlsx": ("content", {
        "FEED_6_MAPPING": (
            {"-": 12}, 3,
            {"source": ["field_name", "inscope", "key", "load_rule", "nullable", "server",
                        "source_database", "source_schema", "source_table", "source_type"],
             "stage": TARGET_FULL, "standard": TARGET_FULL},
            [],
        )}),
    "pair_5_family_e.xlsx": ("content", {
        "FEED_5_MAPPING": (
            {"Header": 3, "Detail": 8, "Trailer": 2}, 6,
            {"source": ["comments", "end", "field_length", "field_name", "length", "ordinal",
                        "pii", "segment", "source_type", "start"],
             "stage": TARGET_SEG, "standard": TARGET_SEG},
            [],
        )}),
    "pair_7_family_e.xlsx": ("content", {
        "MAPPING_FEED_7": (
            {"-": 12}, 0,
            {"source": ["comments", "description", "field_name", "ordinal", "pii", "source_type"],
             "stage": ["schema", "table"],
             "standard": ["schema", "table", "target_type"],
             "rules": ["comments", "dq_mandatory", "recycle_flag"]},
            ["stage/column", "stage/target_type", "standard/column"],
        )}),
    "pair_9_family_e.xlsx": ("content", {
        "MAPPING_FEED_9": (
            {"-": 12}, 0,
            {"source": ["description", "field_name", "key", "length", "pii", "required",
                        "source_database", "source_schema", "source_table", "source_type"],
             "stage": TARGET_FULL, "standard": TARGET_FULL},
            [],
        ),
        "MAPPING_FEED_9_TBL2": (
            {"-": 10}, 0,
            {"source": ["description", "field_name", "key", "length", "pii", "required",
                        "source_database", "source_schema", "source_table", "source_type"],
             "stage": TARGET_FULL, "standard": TARGET_FULL},
            [],
        )}),
    "pair_10_family_e.xlsx": ("content", {
        "Outbound_REGION_A": (
            {}, 0,
            {"source": ["description", "nullable"], "stage": TARGET_FULL,
             "standard": TARGET_FULL, "rules": ["comments"]},
            ["source/field_name"],
        ),
        "Inbound_REGION_A": (
            {}, 0,
            {"source": ["description", "required", "source_type"], "stage": TARGET_FULL,
             "standard": TARGET_FULL, "rules": ["comments"]},
            ["source/field_name"],
        ),
        "Inbound_REGION_B_Adult": (
            {}, 0,
            {"source": ["description", "required"], "stage": TARGET_FULL,
             "standard": TARGET_FULL, "rules": ["comments"]},
            ["source/field_name"],
        ),
        "Inbound_REGION_B_Child": (
            {}, 0,
            {"source": ["description", "required"], "stage": TARGET_FULL,
             "standard": TARGET_FULL, "rules": ["comments"]},
            ["source/field_name"],
        )}),
}

# Auxiliary sheets recognised by header signature, per fixture.
EXPECTED_AUX: dict[str, list[tuple[str, str]]] = {
    "pair_1_family_a.xlsx": [("version", "Version"), ("lob_crosswalk", "LOB_CROSSWALK")],
    "pair_2_family_b.xlsx": [("file_details", "FILE_DETAILS"), ("version", "VERSION_HISTORY")],
    "pair_3_family_c.xlsx": [("version", "Version Control"), ("layout", "Layout"),
                             ("file_details", "FileNames")],
    "pair_4_family_d.xlsx": [("lob_crosswalk", "LOB_CROSSWALK")],
    "pair_5_family_e.xlsx": [("version", "Version History"), ("file_details", "File Details"),
                             ("table_details", "Table_Details"), ("dq_rules", "Sheet1")],
    "pair_6_family_d.xlsx": [("version", "Version Control")],
    "pair_7_family_e.xlsx": [("version", "Version History"), ("file_details", "File Details")],
    "pair_8_family_a.xlsx": [],
    "pair_9_family_e.xlsx": [("table_details", "Summary"), ("version", "Log")],
    "pair_10_family_e.xlsx": [("version", "Version")],
}


def _observe(path: Path, config) -> tuple[str, dict, list[tuple[str, str]]]:
    found = discover(path, config.extractor)
    profile = found.profile
    observed: dict = {}
    if profile.strategy == "content":
        ir = read_workbook(found, path.name, config)
        for data in ir.sheets:
            sp = data.profile
            observed[sp.name] = (
                data.rows_per_segment(), len(data.audit),
                {b.layer: sorted(b.roles) for b in sp.bands if b.roles},
                [f"{u.layer}/{u.role}" for u in profile.unresolved_for(sp.name)],
            )
    else:
        from codegen.extract.workbook import workbook_ir

        ir = workbook_ir(found, path.name, config.extractor)
        for sheet in ir.sheets:
            sp = profile.sheet(sheet.sheet_name)
            assert sp is not None
            observed[sheet.sheet_name] = (
                {"-": len(sheet.rows)}, len(sheet.audit),
                {b.layer: sorted(b.roles) for b in sp.bands if b.roles},
                [f"{u.layer}/{u.role}" for u in profile.unresolved_for(sheet.sheet_name)],
            )
    aux = [(s.kind, s.name) for s in profile.sheets if s.kind not in ("mapping", "ignore")]
    return profile.strategy, observed, aux


@pytest.mark.parametrize("name", sorted(EXPECTED, key=lambda n: int(n.split("_")[1])))
def test_every_sttm_fixture_discovers_and_reads_as_pinned(name, config):
    strategy, observed, aux = _observe(STTM / name, config)
    expected_strategy, expected_sheets = EXPECTED[name]
    assert strategy == expected_strategy
    assert list(observed) == list(expected_sheets), "mapping sheets found"
    for sheet, (rows, audit, roles, missing) in expected_sheets.items():
        got_rows, got_audit, got_roles, got_missing = observed[sheet]
        assert got_rows == rows, (name, sheet, "rows per band")
        assert got_audit == audit, (name, sheet, "audit rows")
        assert got_roles == roles, (name, sheet, "roles resolved")
        assert got_missing == missing, (name, sheet, "roles missing")
    assert aux == EXPECTED_AUX[name]


def test_report_table(config, capsys):
    """Prints the M1 report table: fixture | strategy | mapping sheets | rows
    per band | roles resolved | roles missing (visible with ``pytest -s``)."""
    lines = ["| fixture | strategy | mapping sheet | rows per band | roles resolved | "
             "roles missing |", "| --- | --- | --- | --- | --- | --- |"]
    for name in sorted(EXPECTED, key=lambda n: int(n.split("_")[1])):
        strategy, observed, _aux = _observe(STTM / name, config)
        for sheet, (rows, audit, roles, missing) in observed.items():
            rows_text = ", ".join(f"{k}={v}" for k, v in rows.items()) or "0"
            if audit:
                rows_text += f" (+{audit} audit)"
            resolved = "; ".join(f"{layer}: {len(names)}" for layer, names in roles.items())
            lines.append(f"| {name} | {strategy} | {sheet} | {rows_text} | {resolved} | "
                         f"{', '.join(missing) or '—'} |")
    table = "\n".join(lines)
    with capsys.disabled():
        print("\n\nM1 layout discovery report\n" + table + "\n")
    assert table.count("\n") == 1 + sum(len(s) for _, s in EXPECTED.values())


# ------------------------------------------------------- contract emission


def _frd(feed_name: str, patterns: list[str], stage_tables: list[str], standard_tables: list[str],
         *, fmt="csv", delimiter=",", segments=(), stage_schema="stg", std_schema="std") -> dict:
    data = frd_contract_dict()
    feed = data["feeds"][0]
    feed.update({
        "feed_name": feed_name, "file_name_patterns": patterns, "file_format": fmt,
        "delimiter": delimiter, "record_segments": list(segments),
        "stage_target": {"catalog": None, "schema": stage_schema, "tables": stage_tables,
                         "load_strategy": "Truncate and Load"},
        "standard_target": {"catalog": None, "schema": std_schema, "tables": standard_tables,
                            "load_strategy": "Append"},
        "validation_rules": ["Load the file as received."], "recycle_rule": None,
    })
    return data


def _write_frd(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_family_d_pair4_emits_a_contract_with_provenance(config, tmp_path):
    frd = _write_frd(tmp_path, _frd("FEED_4 remit", ["feed_4_remit_YYYYMMDD.dat"],
                                    ["feed_4_remit"], ["feed_4_remit"], fmt="dat", delimiter="|",
                                    stage_schema="stg_remit", std_schema="remit"))
    contract = extract_contract(STTM / "pair_4_family_d.xlsx", frd, config,
                                generated_date=GENERATED_DATE)
    assert contract.layout is not None and contract.layout.strategy == "content"
    assert contract.layout.source == "synonyms" and contract.layout.unresolved == []
    (feed,) = contract.feeds
    assert feed.feed_id == "feed_4_remit"
    assert feed.field_count == 12 and feed.mapping_sheet == "STTM"
    assert feed.stage.schema_name == "stg_remit" and feed.stage.table == "feed_4_remit"
    assert feed.standard is not None and feed.standard.schema_name == "remit"
    assert [a.column for a in feed.audit_columns] == ["SRC_FILE_NAME", "REC_CREATION_TIME",
                                                      "REC_UPDATED_TIME"]
    assert feed.source_file.name_pattern == "feed_4_remit_YYYYMMDD.dat"   # from the meta row
    assert feed.meta_rows == {"file_names": "feed_4_remit_YYYYMMDD.dat"}
    first = feed.fields[0]
    assert first.source_column == "REMIT_ID" and first.source_datatype == "AN"
    assert first.stage_datatype == "String" and first.standard_datatype == "String"
    assert not first.nullable and first.mandatory is False
    assert first.value_spec == "Load as is"
    amount = next(f for f in feed.fields if f.source_column == "CHECK_AMOUNT")
    assert amount.standard_datatype == "Decimal(11,2)" and amount.value_spec == "Overpunch decode"
    for index, field in enumerate(feed.fields):
        assert field.provenance is not None
        assert (field.provenance.sheet, field.provenance.row, field.provenance.col,
                field.provenance.source) == ("STTM", 6 + index, 2, "synonyms")
    assert [(a.kind, a.sheet, len(a.rows)) for a in contract.auxiliary_sheets] == [
        ("lob_crosswalk", "LOB_CROSSWALK", 7)]
    assert contract.sttm_version.startswith("unversioned")


def test_family_d_pair6_database_source_emits_a_contract(config, tmp_path):
    frd = _write_frd(tmp_path, _frd("SRC_SYS_C authorization", ["dbo.AUTHORIZATION"],
                                    ["src_sys_c_authorization"], ["src_sys_c_authorization"],
                                    fmt="table", delimiter=None, stage_schema="stg_um",
                                    std_schema="um"))
    contract = extract_contract(STTM / "pair_6_family_d.xlsx", frd, config,
                                generated_date=GENERATED_DATE)
    (feed,) = contract.feeds
    assert feed.field_count == 12 and contract.sttm_version == "1.1"
    auth_id = feed.fields[0]
    assert auth_id.source_column == "AUTH_ID" and auth_id.source_datatype == "int"
    assert not auth_id.nullable                       # NULL/NOT NULL column read
    assert feed.fields[1].nullable
    assert auth_id.standard_datatype == "Int"
    assert auth_id.provenance is not None and auth_id.provenance.col == 6
    # The workbook names no file pattern; the FRD's is taken and noted.
    assert feed.source_file.name_pattern == "dbo.AUTHORIZATION"
    assert any("file pattern taken from the FRD" in n for n in contract.notes)


def test_family_e_pair5_segment_column_emits_segmented_fields(config, tmp_path):
    frd = _write_frd(tmp_path, _frd("FEED_5 claims", ["FEED_5_*.txt"],
                                    ["feed_5_hdr", "feed_5_dtl", "feed_5_trl"],
                                    ["feed_5_hdr", "feed_5_dtl", "feed_5_trl"],
                                    fmt="txt", delimiter="|", segments=("Header", "Detail",
                                                                        "Trailer"),
                                    stage_schema="stg_clm", std_schema="clm"))
    contract = extract_contract(STTM / "pair_5_family_e.xlsx", frd, config,
                                generated_date=GENERATED_DATE)
    (feed,) = contract.feeds
    assert feed.field_count == 13
    by_segment = {}
    for field in feed.fields:
        by_segment.setdefault(field.record_segment, set()).add(field.stage_table)
    assert by_segment == {"Header": {"feed_5_hdr"}, "Detail": {"feed_5_dtl"},
                          "Trailer": {"feed_5_trl"}}
    assert feed.source_system == "VENDOR_E"                # File Details vendor
    assert feed.source_file.frequency == "Weekly"
    assert feed.meta_rows["domain"] == "Claims" and feed.meta_rows["sub_domain"] == "Medical"
    assert feed.load_rules.phi_columns == ["Member Id"]
    assert [a.kind for a in contract.auxiliary_sheets] == ["file_details", "table_details",
                                                           "dq_rules"]


def test_family_b_pair2_goes_through_the_legacy_strategy_with_provenance(config, tmp_path):
    data = _frd("FEED_2 claims", ["feed_2_claims_YYYYMMDD.csv"], ["feed_2_claims"],
                ["feed_2_claims"], stage_schema="stg_vendor_b", std_schema="vendor_b")
    members = json.loads(json.dumps(data["feeds"][0]))
    members.update({"feed_name": "FEED_2 members",
                    "file_name_patterns": ["feed_2_members_YYYYMMDD.csv"],
                    "stage_target": {**members["stage_target"], "tables": ["feed_2_members"]},
                    "standard_target": {**members["standard_target"],
                                        "tables": ["feed_2_members"]}})
    providers = json.loads(json.dumps(members))
    providers.update({"feed_name": "FEED_2 providers",
                      "file_name_patterns": ["feed_2_providers_YYYYMMDD.csv"],
                      "stage_target": {**providers["stage_target"], "tables": ["feed_2_providers"]},
                      "standard_target": {**providers["standard_target"],
                                          "tables": ["feed_2_providers"]}})
    data["feeds"] += [members, providers]
    contract = extract_contract(STTM / "pair_2_family_b.xlsx", _write_frd(tmp_path, data), config,
                                generated_date=GENERATED_DATE)
    assert contract.layout is not None and contract.layout.strategy == "mapping_prefix"
    assert [f.field_count for f in contract.feeds] == [10, 12, 10]
    for feed in contract.feeds:
        assert all(f.provenance is not None and f.provenance.source == "synonyms"
                   for f in feed.fields)
        assert feed.fields[0].provenance.row == 3 and feed.fields[0].provenance.col == 1


@pytest.mark.parametrize("name,fragment", [
    ("pair_8_family_a.xlsx", "no field rows could be read"),
    ("pair_7_family_e.xlsx", "stage band has no values for ['column', 'target_type']"),
])
def test_unresolved_layouts_refuse_contract_emission_loudly(name, fragment, config, tmp_path):
    frd = _write_frd(tmp_path, _frd("Any feed", ["*.txt"], ["t"], ["t"]))
    with pytest.raises(ExtractionError, match=fragment.replace("[", r"\[").replace("]", r"\]")):
        extract_contract(STTM / name, frd, config, generated_date=GENERATED_DATE)


def test_legacy_flat_api_names_the_content_path(config):
    with pytest.raises(ContentLayoutDetected, match="content-driven discovery"):
        parse_workbook(STTM / "pair_4_family_d.xlsx", config.extractor)


# ------------------------------------------------ segmented golden + fingerprint


def test_segmented_golden_profile_and_provenance(config, tmp_path):
    workbook_path = tmp_path / "seg.xlsx"
    build_workbook().save(workbook_path)
    frd = _write_frd(tmp_path, frd_contract_dict())
    scoped = config.model_copy(update={"load_pattern_faq": config.load_pattern_faq.model_copy(
        update={"per_feed_dir": str(tmp_path / "faq")})})
    found = discover(workbook_path, config.extractor)
    assert found.profile.strategy == "segmented_family"
    (sheet,) = found.profile.mapping_sheets
    assert sheet.segment_strategy == "column" and sheet.segment_column == 8
    assert [b.layer for b in sheet.bands] == ["source", "stage", "standard"]
    contract = extract_contract(workbook_path, frd, scoped, generated_date=GENERATED_DATE)
    assert contract.layout is not None and contract.layout.strategy == "segmented_family"
    (feed,) = contract.feeds
    assert all(f.provenance is not None and f.provenance.col == 2 for f in feed.fields)


def test_fingerprint_ignores_data_rows_but_not_headers(tmp_path):
    source = STTM / "pair_4_family_d.xlsx"
    baseline = fingerprint(load_workbook(source))
    wb = load_workbook(source)
    wb["STTM"].cell(row=8, column=2, value="DATA_ROW_CHANGED")      # a data row (header is r5)
    wb["STTM"].cell(row=12, column=18, value="other_table")
    assert fingerprint(wb) == baseline
    assert [header_bound(load_workbook(source)[n])[0] for n in ("STTM", "LOB_CROSSWALK")] == [5, 1]
    wb = load_workbook(source)
    wb["STTM"].cell(row=5, column=2, value="Field Name (renamed)")   # a header text
    assert fingerprint(wb) != baseline
