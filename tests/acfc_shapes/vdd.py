# ruff: noqa: E501  -- fixture data tables: documented header/label texts kept on one line
"""Synthetic Vendor Data Dictionary (.xlsx) fixtures for the three field-
sheet header patterns of docs/acfc/SHAPES_FOR_PORT.md §3 — every VDD has
the universal 10-column ``FILES`` sheet plus one or more field sheets.

V1 (pair 1) — full position (11 cols), ONE field sheet, multi-segment via
    the ``Segment`` column (HDR/DTL/TRL); columns/lengths/starts from
    pair1.py so the VDD agrees with the STTM/FRD/golden.
V2 (pair 2) — length only (9 cols, with ``Example Value``), one field sheet
    per CSV file; Length blank throughout (§4).
V3 (pair 9) — DB table (8 cols), one field sheet per table; FILES sheet
    Delimiter / Multi Record Type / Record Type Field / Header Row blank.
"""

from __future__ import annotations

from . import pair1
from .common import new_workbook, write_rows

FILES_HEADER = ["File Name Pattern", "File Title", "Format", "Delimiter", "Delivery Cadence",
                "Content Description", "Field Sheet", "Multi Record Type", "Record Type Field",
                "Header Row"]
V1_HEADER = ["Position", "Field Name", "Data Type", "Start Position", "End Position", "Length",
             "Required", "PHI/PII", "Key", "Segment", "Description"]
V2_HEADER = ["Position", "Field Name", "Data Type", "Length", "Required", "PHI/PII", "Key",
             "Description", "Example Value"]
V3_HEADER = ["Position", "Field Name", "Data Type", "Length", "Required", "PHI/PII", "Key",
             "Description"]


def build_vdd_pair1(amounts: bool = False, amount_spans: bool = True):
    """``amounts`` (M9.2, a test VARIANT): rows for pair1.AMOUNT_FIELDS, 13
    bytes wide (UNVERIFIED) — without Start / End / Length when
    ``amount_spans`` is False (a dictionary that names the fields only)."""
    wb = new_workbook()
    ws = wb.create_sheet("FILES")
    write_rows(ws, [FILES_HEADER])
    write_rows(ws, [[pattern, f"{pair1.FEED_NAME} {'inbound' if 'FROM' in pattern else 'outbound'}",
                     "Fixed Width", None, "Daily" if pattern.startswith("I_") else "Monthly",
                     f"{pair1.FEED_NAME} balances", "FEED_1 Fields", "Y", "SEGMENT_IDENTIFIER", "N"]
                    for pattern in pair1.FILE_PATTERNS], start_row=2)
    ws = wb.create_sheet("FEED_1 Fields")
    write_rows(ws, [V1_HEADER])
    rows = []
    for position, c in enumerate(pair1.columns(), start=1):
        rows.append([position, c.name, pair1.SOURCE_TYPE, c.start, c.start + c.length - 1, c.length,
                     "Y" if c.required == "Y" else None, None, None,
                     pair1.VDD_SEGMENT[c.segment], c.description])
    for name, _column, start in (pair1.AMOUNT_FIELDS if amounts else []):
        width = pair1.AMOUNT_VDD_WIDTH
        rows.append([len(rows) + 1, " ".join(name.split()).upper(), pair1.SOURCE_TYPE,
                     start if amount_spans else None,
                     start + width - 1 if amount_spans else None,
                     width if amount_spans else None, None, None, None,
                     pair1.VDD_SEGMENT["DET"], "Accumulated amount"])
    write_rows(ws, rows, start_row=2)
    return wb


def build_vdd_pair2():
    wb = new_workbook()
    files = {
        "feed_2_claims_YYYYMMDD.csv": ("Claims", ["CLAIM_ID", "MEMBER_ID", "CLAIM_DATE", "CLAIM_AMOUNT",
                                                  "CLAIM_STATUS", "PROVIDER_ID", "DIAG_CODE", "PROC_CODE",
                                                  "PAID_AMOUNT", "ADJ_CODE"]),
        "feed_2_members_YYYYMMDD.csv": ("Members", ["MEMBER_ID", "FIRST_NAME", "LAST_NAME", "DOB", "GENDER",
                                                    "ADDRESS_1", "CITY", "STATE", "ZIP", "PLAN_CODE",
                                                    "EFFECTIVE_DATE", "TERM_DATE"]),
        "feed_2_providers_YYYYMMDD.csv": ("Providers", ["PROVIDER_ID", "NPI", "PROVIDER_NAME", "SPECIALTY",
                                                        "TAX_ID", "ADDRESS_1", "CITY", "STATE", "ZIP", "STATUS"]),
    }
    ws = wb.create_sheet("FILES")
    write_rows(ws, [FILES_HEADER])
    write_rows(ws, [[pattern, f"FEED_2 {title}", "csv", ",", "Daily", f"{title} extract",
                     f"{title} Fields", "N", None, "Y"] for pattern, (title, _) in files.items()],
               start_row=2)
    for title, fields in files.values():
        ws = wb.create_sheet(f"{title} Fields")
        write_rows(ws, [V2_HEADER])
        write_rows(ws, [[i, f, "Date" if f.endswith("DATE") or f == "DOB" else "String", None,
                         "Y" if i == 1 else "N", "Y" if f in {"FIRST_NAME", "LAST_NAME", "DOB", "MEMBER_ID"} else "N",
                         "Y" if i == 1 else None, f"{f.title()} value",
                         "20260115" if f.endswith("DATE") or f == "DOB" else f"S{i:03d}"]
                        for i, f in enumerate(fields, start=1)], start_row=2)
    return wb


def build_vdd_pair9():
    wb = new_workbook()
    tables = {
        "ENCOUNTER": [("ENCOUNTER_ID", "bigint", None, "Y"), ("MEMBER_KEY", "varchar", 50, "N"),
                      ("PROVIDER_KEY", "varchar", 50, "N"), ("ENCOUNTER_DATE", "date", None, "N"),
                      ("ENCOUNTER_TYPE", "varchar", 50, "N"), ("STATUS", "varchar", 50, "N"),
                      ("TOTAL_CHARGE", "decimal", None, "N"), ("LOB_CD", "varchar", 50, "N"),
                      ("CREATED_TS", "timestamp", None, "N"), ("UPDATED_TS", "timestamp", None, "N"),
                      ("SOURCE_BATCH", "varchar", 50, "N"), ("IS_DELETED", "bit", None, "N")],
        "ENCOUNTER_LINE": [("ENCOUNTER_LINE_ID", "bigint", None, "Y"), ("ENCOUNTER_ID", "bigint", None, "N"),
                           ("LINE_NO", "int", None, "N"), ("PROCEDURE_CD", "varchar", 50, "N"),
                           ("MODIFIER", "varchar", 50, "N"), ("UNITS", "int", None, "N"),
                           ("CHARGE_AMT", "decimal", None, "N"), ("DIAGNOSIS_CD", "varchar", 50, "N"),
                           ("CREATED_TS", "timestamp", None, "N"), ("UPDATED_TS", "timestamp", None, "N")],
        "ENCOUNTER_STATUS": [("STATUS", "varchar", 50, "Y"), ("STATUS_DESC", "varchar", 50, "N"),
                             ("ACTIVE", "bit", None, "N")],
    }
    ws = wb.create_sheet("FILES")
    write_rows(ws, [FILES_HEADER])
    write_rows(ws, [[f"dbo.{table}", table, "Database table", None, "Daily", f"{table} rows",
                     table, None, None, None] for table in tables], start_row=2)
    for table, columns in tables.items():
        ws = wb.create_sheet(table)
        write_rows(ws, [V3_HEADER])
        write_rows(ws, [[i, name, typ, length, "Y" if key == "Y" else "N", "N", key or "N",
                         f"{name} description"] for i, (name, typ, length, key) in enumerate(columns, start=1)],
                   start_row=2)
    return wb


BUILDERS = {
    "vdd/pair_1_v1_segments.xlsx": build_vdd_pair1,
    "vdd/pair_2_v2_per_file.xlsx": build_vdd_pair2,
    "vdd/pair_9_v3_per_table.xlsx": build_vdd_pair9,
}
