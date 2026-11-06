"""post179 (a staging run): an FRD "Target Table Name" cell that holds a nested
table ("Vendor | Target Table", one row per vendor) names the tables in its table
column. Before, every line of the cell was a table name - the header words and
the vendor too - and the layout stage split one FRD feed into four. A nested
table with no table column states no table (blank + flagged; the STTM fills it).
Synthetic FRDs only."""

from __future__ import annotations

from pathlib import Path

from acfc_shapes import frd as frd_fixtures
from acfc_shapes import pair1
from acfc_shapes.common import docx_bytes
from codegen.extract.frd_docx import extract_frd_contract

DATE = "2026-11-06"


def _frd(tmp_path: Path, tables_cell) -> Path:
    sections = [
        frd_fixtures._section("Descriptive Metadata", "", "d", "Ingest.", frd_fixtures.DESCRIPTIVE,
                              {"Data Source": "VENDOR_A", "Object Name": "Accumulators Daily",
                               "Frequency": "Daily", "LOBs": "ALL"}),
        frd_fixtures._section("Structural Metadata", "", "s", "Ingest.",
                              frd_fixtures.STRUCTURAL_P1,
                              {"Object/data Format": pair1.FILE_FORMAT,
                               "Target Table Name": tables_cell,
                               "Domain and Subdomain": "Pharmacy / Accumulators",
                               "Load Strategy STG": "Append",
                               "Load Strategy STD (View)": "Append"}),
    ]
    path = tmp_path / "frd_nested.docx"
    path.write_bytes(docx_bytes(sections))
    return path


def test_a_nested_target_table_cell_names_its_table_column(config, tmp_path):
    cell = [["Vendor", "Target Table"], ["VENDOR_A", "syn_claims_hist"]]
    contract, _ = extract_frd_contract(_frd(tmp_path, cell), config, generated_date=DATE)
    (feed,) = contract.feeds
    assert feed.stage_target.tables == ["syn_claims_hist"]
    (flag,) = [f for f in contract.extraction_flags if f.startswith("frd_nested_tables:")]
    assert "its 'Target Table' column names ['syn_claims_hist']" in flag
    assert "('Target Table Name')" in flag


def test_two_vendor_rows_name_two_tables_once_each(config):
    from codegen.extract.frd_docx import nested_table_names

    frd = config.extractor.frd
    rows = [["Vendor", "Table Name"], ["A", "t_one"], ["B", "t_two"], ["C", "t_one"], ["D", ""]]
    assert nested_table_names(rows, frd) == (["t_one", "t_two"], "Table Name")
    assert nested_table_names([], frd) == ([], None)


def test_a_nested_cell_without_a_table_column_states_no_table(config, tmp_path):
    cell = [["Vendor", "Notes"], ["VENDOR_A", "see the mapping document"]]
    contract, _ = extract_frd_contract(_frd(tmp_path, cell), config, generated_date=DATE)
    (feed,) = contract.feeds
    assert feed.stage_target.tables == []
    (flag,) = [f for f in contract.extraction_flags if f.startswith("frd_nested_tables:")]
    assert "no column header names a table" in flag and "the tables are unstated" in flag


def test_a_plain_cell_is_read_as_before(config, tmp_path):
    contract, _ = extract_frd_contract(_frd(tmp_path, "syn_claims_hist"), config,
                                       generated_date=DATE)
    (feed,) = contract.feeds
    assert feed.stage_target.tables == ["syn_claims_hist"]
    assert not [f for f in contract.extraction_flags if f.startswith("frd_nested_tables:")]
