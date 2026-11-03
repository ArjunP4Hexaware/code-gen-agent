# ruff: noqa: E501  -- fixture data tables: one field per line
"""Pair 4 (multi-table, 2026-10-07): the synthetic Northwind Benefits COB feed.

The framework owners' multi-table model (docs/acfc/MULTI_TABLE_DESIGN.md §1):
one STTM defines THREE tables (Header / Detail / Trailer, a TableName per
segment), the header block lists SIX LOBs that each arrive as their own file,
and every row carries a Stage band AND a Standard band, each with its own
LOGICAL catalog (PR_DLK / PR_STD), schema, table, column, type, mandatory and
key. A separate STG→STD sheet (``ForReference``) repeats the standard side —
a secondary source the fixture keeps in agreement with the Standard band. Everything here is invented — vendor, feed, columns, codes.

NOT the documented pair 4 of docs/acfc/SHAPES_FOR_PORT.md (that one is
``sttm/pair_4_family_d.xlsx``, built by ``sttm.build_pair4``); the directory
name ``pair_4/`` follows the brief.

The facts below are the single source both builders (STTM workbook, FRD
contract) read; the goldens under ``fixtures/acfc_shapes/pair_4/golden/`` are
written by hand and checked against these facts by
``tests/test_pair4_multi_table_fixture.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .common import merge_span, new_workbook, write_rows

FEED = "nb_cob_report"
VENDOR = "Northwind Benefits"
FILE_TEMPLATE = "NWB_COB_RPT_<LOB>_CCYYMMDD.txt"
LOBS = ["110", "120", "210", "220", "310", "320"]
FILE_LOCATION = "mftlanding/inbound/membership/cob/northwind_benefits/"
FREQUENCY = "Monthly"
DOMAIN = "Membership"
SUB_DOMAIN = "Coordination of Benefits"
FILE_TYPE = "Pipe delimited text (.txt)"
DELIMITER = "|"
STAGE_SCHEMA = "stg_nb_cob"
STANDARD_SCHEMA = "nb_cob"    # the stage schema without its stg_ prefix
# LOGICAL catalogs as the STTM states them; the deployment environment maps
# them (catalog_map in the overlay).
STAGE_CATALOG = "PR_DLK"
STANDARD_CATALOG = "PR_STD"
LOAD_STRATEGY = "Append"

MAIN_SHEET = "NB_COB_REPORT"
REFERENCE_SHEET = "ForReference"

# Header block (rows 1–8, label in A, value in B), in the brief's order.
HEADER_BLOCK: list[tuple[str, str]] = [
    ("File(s)", FILE_TEMPLATE),
    ("File Generator", VENDOR),
    ("File Location", FILE_LOCATION),
    ("LOB", ", ".join(LOBS)),
    ("File frequency", FREQUENCY),
    ("Domain", DOMAIN),
    ("Sub-Domain", SUB_DOMAIN),
    ("File type", FILE_TYPE),
]
# Row 10: the band row (Source | Stage | Standard, merged); row 11: headers.
# Each target band carries its own Catalog / Schema / TableName / ColumnName /
# DataType / Mandatory / Primary Key.
BAND_ROW = 10
TABLE_HEADER_ROW = 11
SOURCE_HEADERS = ["#", "Field Name", "Data Type", "Length", "Segment"]
BAND_HEADERS = ["Catalog", "Schema", "TableName", "ColumnName", "DataType", "Mandatory",
                "Primary Key"]
MAIN_BANDS = [("Source", len(SOURCE_HEADERS)), ("Stage Layer", len(BAND_HEADERS)),
              ("Standard Layer", len(BAND_HEADERS))]
MAIN_HEADERS = SOURCE_HEADERS + BAND_HEADERS + BAND_HEADERS

REFERENCE_BAND = [("Client - Source", 1), ("STG - Dest 1", 3), ("STD - Dest2", 4)]
REFERENCE_HEADERS = ["Field Name", "Table Name", "Column Name", "Data Type",
                     "Schema", "Table Name", "Column Name", "Data Type"]


@dataclass(frozen=True)
class Field:
    name: str                    # STTM Field Name (source)
    length: int
    column: str                  # stage ColumnName
    mandatory: bool
    primary_key: bool
    std_column: str | None       # ForReference STD column; None = not carried to standard
    std_type: str | None


@dataclass(frozen=True)
class Table:
    segment: str                 # STTM Segment cell
    table: str                   # stage TableName (= the standard table name)
    fields: list[Field]


SOURCE_TYPE = "String"           # every source field of a text file
STAGE_TYPE = "String"            # the stage lands every business column as String
AUDIT: list[tuple[str, str]] = [("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                                ("REC_UPDATED_TIME", "Timestamp")]

TABLES: list[Table] = [
    Table("Header", f"{FEED}_hdr", [
        Field("Record Type", 1, "RECORD_TYPE", True, False, None, None),
        Field("File Name", 60, "FILE_NAME", True, False, "FILE_NAME", "String"),
        Field("File Creation Date", 8, "FILE_CREATION_DATE", True, False, "FILE_CREATION_DATE", "Date"),
        Field("File Creation Time", 6, "FILE_CREATION_TIME", False, False, "FILE_CREATION_TIME", "String"),
        Field("Vendor Name", 40, "VENDOR_NAME", True, False, "VENDOR_NAME", "String"),
        Field("LOB", 3, "LOB", True, False, "LOB", "String"),
        Field("Report Period Start", 8, "REPORT_PERIOD_START", True, False, "REPORT_PERIOD_START_DATE", "Date"),
        Field("Report Period End", 8, "REPORT_PERIOD_END", True, False, "REPORT_PERIOD_END_DATE", "Date"),
    ]),
    Table("Detail", f"{FEED}_dtl", [
        Field("Record Type", 1, "RECORD_TYPE", True, False, None, None),
        Field("LOB", 3, "LOB", True, False, "LOB", "String"),
        Field("Member ID", 12, "MEMBER_ID", True, True, "MEMBER_ID", "String"),
        Field("Subscriber ID", 12, "SUBSCRIBER_ID", True, False, "SUBSCRIBER_ID", "String"),
        Field("Member Last Name", 35, "MEMBER_LAST_NAME", False, False, "MEMBER_LAST_NAME", "String"),
        Field("Member First Name", 25, "MEMBER_FIRST_NAME", False, False, "MEMBER_FIRST_NAME", "String"),
        Field("Member Date of Birth", 8, "MEMBER_DOB", True, False, "MEMBER_BIRTH_DATE", "Date"),
        Field("Member Gender", 1, "MEMBER_GENDER", False, False, "MEMBER_GENDER", "String"),
        Field("Other Carrier ID", 10, "OTHER_CARRIER_ID", True, True, "OTHER_CARRIER_ID", "String"),
        Field("Other Carrier Name", 60, "OTHER_CARRIER_NAME", False, False, "OTHER_CARRIER_NAME", "String"),
        Field("Other Policy Number", 20, "OTHER_POLICY_NUMBER", True, False, "OTHER_POLICY_NUMBER", "String"),
        Field("Other Group Number", 20, "OTHER_GROUP_NUMBER", False, False, "OTHER_GROUP_NUMBER", "String"),
        Field("Coverage Type", 2, "COVERAGE_TYPE", True, False, "COVERAGE_TYPE", "String"),
        Field("COB Order", 1, "COB_ORDER", True, False, "COB_ORDER", "Int"),
        Field("COB Effective Date", 8, "COB_EFF_DATE", True, True, "COB_EFF_DATE", "Date"),
        Field("COB Termination Date", 8, "COB_TERM_DATE", False, False, "COB_TERM_DATE", "Date"),
        Field("Medicare Indicator", 1, "MEDICARE_IND", False, False, "MEDICARE_IND", "String"),
        Field("Source of Information", 2, "SOURCE_OF_INFO", False, False, "SOURCE_OF_INFO", "String"),
        Field("Verification Date", 8, "VERIFICATION_DATE", False, False, "VERIFICATION_DATE", "Date"),
        Field("Record Status", 1, "RECORD_STATUS", True, False, "RECORD_STATUS", "String"),
    ]),
    Table("Trailer", f"{FEED}_trl", [
        Field("Record Type", 1, "RECORD_TYPE", True, False, None, None),
        Field("File Name", 60, "FILE_NAME", True, False, "FILE_NAME", "String"),
        Field("Detail Record Count", 9, "DETAIL_RECORD_COUNT", True, False, "DETAIL_RECORD_COUNT", "Int"),
        Field("Total Record Count", 9, "TOTAL_RECORD_COUNT", True, False, "TOTAL_RECORD_COUNT", "Int"),
        Field("File Creation Date", 8, "FILE_CREATION_DATE", True, False, "FILE_CREATION_DATE", "Date"),
        Field("End of File Marker", 3, "END_OF_FILE_MARKER", False, False, "END_OF_FILE_MARKER", "String"),
    ]),
]


def table_by_segment(segment: str) -> Table:
    return next(t for t in TABLES if t.segment == segment)


# ------------------------------------------------------------------ STTM


def _yn(flag: bool) -> str:
    return "Y" if flag else "N"


def _main_rows() -> list[list]:
    rows: list[list] = []
    number = 0
    for table in TABLES:
        for f in table.fields:
            number += 1
            stage = [STAGE_CATALOG, STAGE_SCHEMA, table.table, f.column, STAGE_TYPE,
                     _yn(f.mandatory), _yn(f.primary_key)]
            standard = ([STANDARD_CATALOG, STANDARD_SCHEMA, table.table, f.std_column,
                         f.std_type, _yn(f.mandatory), _yn(f.primary_key)]
                        if f.std_column is not None else [None] * len(BAND_HEADERS))
            rows.append([number, f.name, SOURCE_TYPE, f.length, table.segment]
                        + stage + standard)
        for column, dtype in AUDIT:
            rows.append([None, "NA", "NA", None, table.segment,
                         STAGE_CATALOG, STAGE_SCHEMA, table.table, column, dtype, "N", "N",
                         STANDARD_CATALOG, STANDARD_SCHEMA, table.table, column, dtype, "N",
                         "N"])
    return rows


def _reference_rows() -> list[list]:
    rows: list[list] = []
    for table in TABLES:
        for f in table.fields:
            std = ([STANDARD_SCHEMA, table.table, f.std_column, f.std_type]
                   if f.std_column is not None else [None, None, None, None])
            rows.append([f.name, table.table, f.column, STAGE_TYPE, *std])
        for column, dtype in AUDIT:
            rows.append(["NA", table.table, column, dtype,
                         STANDARD_SCHEMA, table.table, column, dtype])
    return rows


def build_sttm():
    wb = new_workbook()
    main = wb.create_sheet(MAIN_SHEET)
    write_rows(main, [[label, value] for label, value in HEADER_BLOCK])
    band: list = []
    for label, width in MAIN_BANDS:
        band.extend([label] + [None] * (width - 1))
    write_rows(main, [band, MAIN_HEADERS] + _main_rows(), start_row=BAND_ROW)
    col = 1
    for _label, width in MAIN_BANDS:
        merge_span(main, BAND_ROW, col, col + width - 1)
        col += width

    ref = wb.create_sheet(REFERENCE_SHEET)
    band: list = []
    for label, width in REFERENCE_BAND:
        band.extend([label] + [None] * (width - 1))
    write_rows(ref, [band, REFERENCE_HEADERS] + _reference_rows())
    col = 1
    for _label, width in REFERENCE_BAND:
        merge_span(ref, 1, col, col + width - 1)
        col += width
    return wb


# ------------------------------------------------------------------ FRD contract


def frd_contract() -> dict:
    tables = [t.table for t in TABLES]
    return {
        "contract_name": f"{FEED} feed-level mapping contract (synthetic)",
        "generated_from_frd": f"FRD_{FEED}.docx",
        "generated_date": "2026-10-07T00:00:00+00:00",
        "generator": "hand-built synthetic fixture (tests/acfc_shapes/pair4_nb.py)",
        "status": "PASS",
        "project": {
            "project_id": "SYN-PRJ-04",
            "project_name": f"{VENDOR} COB Report Ingestion",
            "business_context_summary": (
                "Ingest the monthly coordination-of-benefits report the vendor sends per "
                "line of business into the stage and standard layers."),
        },
        "in_scope": ["One pipe-delimited file per LOB with Header, Detail and Trailer records."],
        "out_of_scope": ["Any transformation beyond what the STTM maps."],
        "assumptions_constraints_dependencies": [],
        "feeds": [{
            "feed_name": FEED,
            "source_system": VENDOR,
            "file_name_patterns": [FILE_TEMPLATE],
            "file_format": "txt",
            "delimiter": DELIMITER,
            "record_segments": [t.segment for t in TABLES],
            "frequency": FREQUENCY,
            "load_windows_sla": [],
            "lobs": list(LOBS),
            "domain": DOMAIN,
            "sub_domain": SUB_DOMAIN,
            "landing_location": FILE_LOCATION,
            "stage_target": {"catalog": None, "schema": STAGE_SCHEMA, "tables": tables,
                             "load_strategy": LOAD_STRATEGY},
            "standard_target": {"catalog": None, "schema": STANDARD_SCHEMA, "tables": tables,
                                "load_strategy": LOAD_STRATEGY},
            "validation_rules": [],
            "recycle_rule": None,
            "history_backfill": None,
            "archive_retention": None,
            "phi_pii_notes": "PHI fields included in the mapping document",
            "sttm_reference": f"STTM_{FEED}.xlsx",
            "requirement_ids": ["SYN-REQ-0401"],
        }],
        "system_interfaces": [],
        "open_items": [],
    }


def build_frd_contract() -> bytes:
    return (json.dumps(frd_contract(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")


STTM_PATH = "pair_4/sttm_nb_cob_report.xlsx"
FRD_PATH = "pair_4/frd_nb_cob_report.contract.json"

XLSX_BUILDERS = {STTM_PATH: build_sttm}
BYTES_BUILDERS = {FRD_PATH: build_frd_contract}
