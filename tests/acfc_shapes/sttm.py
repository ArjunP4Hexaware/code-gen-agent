# ruff: noqa: E501  -- fixture data tables: documented header/label texts kept on one line
"""Synthetic STTM workbooks reproducing the five layout families of
docs/acfc/SHAPES_FOR_PORT.md §1 — sheet names (anonymized as documented),
meta rows with the documented labels at the documented rows, the band row at
the documented row with the documented band texts and merges, the header
row with the documented header texts in order, and 10–30 plausible
synthetic rows. Vocabulary is synthetic throughout (FEED_n, VENDOR_x,
SRC_SYS_x); pair 1 renders from ``pair1.py`` so it matches the golden.
"""

from __future__ import annotations

from . import pair1
from .common import band_row, merge_bands, merge_span, new_workbook, write_rows

_STAGE_STD_4 = ["Schema", "TableName", "ColumnName", "DataType"]
_STAGE_STD_6 = ["Workspace", "Catalog", "Schema", "TableName", "ColumnName", "DataType"]


def _version_sheet(wb, title, header, header_row, rows, merge_a2d2=False):
    ws = wb.create_sheet(title)
    if header_row > 1:
        ws.cell(row=1, column=1, value="Version History")
        if merge_a2d2:
            ws.cell(row=2, column=1, value="Document control")
            merge_span(ws, 2, 1, 4)
    write_rows(ws, [header], start_row=header_row)
    write_rows(ws, rows, start_row=header_row + 1)
    return ws


# --------------------------------------------------------------- Family A ---


def build_pair1():
    """Pair 1 (Family A): Version | LOB_CROSSWALK | FEED_1_MAPPING — the REAL
    sheet geometry (M9.0), transcribed from the two ACFC captures on the
    ``acfc-hotfix-1`` branch: ``docs/acfc/HANDOVER_GENIE.md`` §2 (meta rows,
    data-row constants) and ``docs/acfc/PAIR1_HEADERS.md`` §1 (rows 14-15,
    cell by cell, and the four merges).

    Meta r1-r10 with the recorded labels; file names / example / frequency
    read ``TBD``, the format reads ``.dat``, the rest are empty. Band r14,
    four merges: ``Source Data`` A14:I14, ``Data Rules and Primary Keys``
    K14:P14, ``Staging Layer Table`` R14:W14, ``Standard Layer Table``
    Y14:AD14. Header r15: nine source headers in A-I, six rules headers in
    K-P, the six ``… in DL`` layer headers at R-W and again at Y-AD — 27
    header texts over 30 columns; J, Q and X are EMPTY spacer columns in both
    rows. Schema and table constants repeat on every data row; each record
    block is introduced by a segment banner row (``Header`` / ``Details`` /
    ``Trailer``) while the Segment column keeps the golden's own vocabulary;
    one detail row's target column reads ``Do Not Map`` with no data type."""
    wb = new_workbook()
    _version_sheet(
        wb, "Version",
        ["Date", "Version", "Author(s)", "Description of Version/Changes"], 3,
        [["2026-01-05", "0.1", "SYN Author A", "Initial draft"],
         ["2026-01-19", "1.0", "SYN Author A", "Approved layout"],
         ["2026-02-02", "1.1", "SYN Author B", "Added standard layer"]],
        merge_a2d2=True,
    )
    ws = wb.create_sheet("LOB_CROSSWALK")
    write_rows(ws, [["Source LOB Code", "Source LOB Name", "Target LOB", "Region", "Notes"]])
    write_rows(ws, [[f"L{i:02d}", f"Synthetic LOB {i}", "ALL", f"REGION_{'AB'[i % 2]}", None]
                    for i in range(1, 18)], start_row=2)
    merge_span(ws, 19, 1, 2)
    merge_span(ws, 19, 3, 5)

    ws = wb.create_sheet("FEED_1_MAPPING")
    meta = [
        ["File Names", "TBD"],
        ["File Name Example", "TBD"],
        ["Frequency", "TBD"],
        ["File Format (text, csv)", ".dat"],
        ["File Delimiter", None],
        ["Last Update Date", None],
        ["Version", None],
        ["LOB", pair1.LOB],
        ["Target table Name Desc", f"Accumulator balances exchanged with {pair1.VENDOR_NAME}"],
        ["Feed Type", None],
    ]
    write_rows(ws, meta, start_row=1)
    # (label, first column, last column) — 1-based, inclusive.
    bands = [("Source Data", 1, 9), ("Data Rules and Primary Keys", 11, 16),
             ("Staging Layer Table", 18, 23), ("Standard Layer Table", 25, 30)]
    for label, first, last in bands:
        ws.cell(row=14, column=first, value=label)
        merge_span(ws, 14, first, last)
    layer_headers = ["Workspace", "Target Catalog", "Target Schema Name in DL",
                     "Target Table Name in DL", "Target_Column_Name_in_DL",
                     "Target Data Type in DL"]
    source_headers = ["S.No", "Segment", "Field Name", "Required?", "Format", "Start", "Length",
                      "End", "Description"]
    rules_headers = ["Data Definition", "PII", "Primary Key", "Critical Data", "Not NULL",
                     "Load Rules"]
    header = (source_headers + [None] + rules_headers + [None] + layer_headers + [None]
              + layer_headers)
    assert len([h for h in header if h]) == 27 and len(header) == 30
    assert [i + 1 for i, h in enumerate(header) if h is None] == [10, 17, 24]      # J, Q, X
    write_rows(ws, [header], start_row=15)

    def targets(stage_column, stage_type, standard_column, standard_type):
        return [None,
                "DLK", pair1.STAGE_CATALOG, pair1.STAGE_SCHEMA, pair1.TABLE,
                stage_column, stage_type, None,
                "DLK", pair1.STANDARD_CATALOG, pair1.STANDARD_SCHEMA, pair1.TABLE,
                standard_column, standard_type]

    rows: list[list] = []
    sno = 0
    segment = None
    for c in pair1.columns():
        if c.segment != segment:
            if segment == pair1.UNMAPPED_AFTER_SEGMENT:
                sno += 1
                rows.append(_pair1_unmapped_row(sno, targets))
            segment = c.segment
            rows.append([pair1.SEGMENT_BANNERS[segment]])
        sno += 1
        rows.append([
            sno, c.segment, c.name, c.required, pair1.SOURCE_TYPE, c.start, c.length,
            c.start + c.length - 1, c.description, None,
            c.description, "N", None, "N", "Y" if c.required == "Y" else "N", c.load_rule,
            *targets(c.name, c.dtype, c.name, c.dtype),
        ])
    for name, dtype in pair1.AUDIT_COLUMNS:
        rows.append([
            None, None, "NA", None, None, None, None, None, "Audit column", None,
            None, None, None, None, None, None,
            *targets(name, dtype, name, dtype),
        ])
    write_rows(ws, rows, start_row=16)
    return wb


def _pair1_unmapped_row(sno: int, targets) -> list:
    """The one source field the STTM marks ``Do Not Map`` (no data type) —
    closes the detail block, after the last mapped detail field."""
    name, start, length = pair1.UNMAPPED_FIELD
    marker = pair1.UNMAPPED_MARKER
    return [sno, pair1.UNMAPPED_AFTER_SEGMENT, name, "N", pair1.SOURCE_TYPE, start, length,
            start + length - 1, "Reserved for future use", None, "Reserved for future use", "N",
            None, "N", "N", None, *targets(marker, None, marker, None)]


def build_pair8():
    """Pair 8 (Family A): single FEED_8_LAYOUT sheet. Meta r1-r6 (all
    populated), band r7 'Header Record' | 'Staging Layer' | 'Standard Layer',
    field headers r8 (21 cols). Multi-segment: HR/DR/TR/FT record blocks,
    each introduced by a merged segment-label row and with the `count`
    column merged down the block (the documented 145-merge shape)."""
    wb = new_workbook()
    ws = wb.create_sheet("FEED_8_LAYOUT")
    meta = [
        ["File Names", "FEED_8_*.txt"],
        ["Last Update Date", "2026-02-10"],
        ["Version", "2.0"],
        ["LOB", "ALL"],
        ["Target table Name Desc", "FEED_8 flat file layout from VENDOR_H"],
        ["Feed Type", "Inbound"],
    ]
    write_rows(ws, meta, start_row=1)
    groups = [("Header Record", 9), ("Staging Layer", 6), ("Standard Layer", 6)]
    write_rows(ws, [band_row(groups)], start_row=7)
    merge_bands(ws, 7, groups)
    header = (["count", "Sr. No", "Input File", "Output Flat File layout", "Data Definition",
               "PII", "Primary Key", "Critical Data", "NOT NULL"] + _STAGE_STD_6 + _STAGE_STD_6)
    assert len(header) == 21
    write_rows(ws, [header], start_row=8)
    blocks = {
        "HR": ["REC_TYPE", "FILE_DATE", "SENDER_ID", "RECEIVER_ID"],
        "DR": ["REC_TYPE", "MEMBER_KEY", "SERVICE_DATE", "PROVIDER_KEY", "AMOUNT_BILLED",
               "AMOUNT_PAID", "DIAGNOSIS_CD", "PROCEDURE_CD"],
        "TR": ["REC_TYPE", "DETAIL_COUNT", "TOTAL_PAID"],
        "FT": ["REC_TYPE", "FILE_COUNT"],
    }
    tables = {"HR": "feed_8_hdr", "DR": "feed_8_dtl", "TR": "feed_8_trl", "FT": "feed_8_ftr"}
    row = 9
    for index, (segment, fields) in enumerate(blocks.items()):
        if index:
            # Segment-label row introducing the next record block (merged
            # across the source group, like the r7 'Header Record' band).
            label = {"DR": "Detail Record", "TR": "Trailer Record", "FT": "File Trailer"}[segment]
            ws.cell(row=row, column=1, value=label)
            merge_span(ws, row, 1, 9)
            row += 1
        first = row
        for sr, field in enumerate(fields, start=1):
            write_rows(ws, [[
                len(fields) if sr == 1 else None, sr, field, f"{field} X(10)", f"{field} value",
                "N", "Y" if field.endswith("_KEY") else None, "N", "Y" if sr == 1 else "N",
                "DLK", "syn_dlk", "stg_feed8", tables[segment], field, "String",
                "DLK", "syn_std", "feed8", tables[segment], field, "String",
            ]], start_row=row)
            row += 1
        ws.merge_cells(start_row=first, start_column=1, end_row=row - 1, end_column=1)
    return wb


# --------------------------------------------------------------- Family B ---


def build_pair2():
    """Pair 2 (Family B): FILE_DETAILS | VERSION_HISTORY | MAPPING- |
    MAPPING-1 | MAPPING-2; band r1 (3 labels, no merges), headers r2 (16)."""
    wb = new_workbook()
    ws = wb.create_sheet("FILE_DETAILS")
    write_rows(ws, [["Vendor", "FileName", "File Description", "Location", "Frequency"]])
    files = [("VENDOR_B", "feed_2_claims_YYYYMMDD.csv", "Claims extract", "inbound/vendor_b", "Daily"),
             ("VENDOR_B", "feed_2_members_YYYYMMDD.csv", "Member extract", "inbound/vendor_b", "Weekly"),
             ("VENDOR_B", "feed_2_providers_YYYYMMDD.csv", "Provider extract", "inbound/vendor_b", "Monthly")]
    write_rows(ws, [list(f) for f in files], start_row=2)
    ws = wb.create_sheet("VERSION_HISTORY")
    write_rows(ws, [["Version", "Date", "Author", "Change Description"],
                    ["1.0", "2026-01-12", "SYN Author C", "Initial"]])
    header = (["Database column Name", "NULL CHECK", "Description", "Sample Value", "DataType",
               "PHI Field", "Mandatory Field", "Comment"] + _STAGE_STD_4 + _STAGE_STD_4)
    assert len(header) == 16
    specs = {
        "MAPPING-": ("feed_2_claims", ["CLAIM_ID", "MEMBER_ID", "CLAIM_DATE", "CLAIM_AMOUNT",
                                        "CLAIM_STATUS", "PROVIDER_ID", "DIAG_CODE", "PROC_CODE",
                                        "PAID_AMOUNT", "ADJ_CODE"]),
        "MAPPING-1": ("feed_2_members", ["MEMBER_ID", "FIRST_NAME", "LAST_NAME", "DOB", "GENDER",
                                          "ADDRESS_1", "CITY", "STATE", "ZIP", "PLAN_CODE",
                                          "EFFECTIVE_DATE", "TERM_DATE"]),
        "MAPPING-2": ("feed_2_providers", ["PROVIDER_ID", "NPI", "PROVIDER_NAME", "SPECIALTY",
                                            "TAX_ID", "ADDRESS_1", "CITY", "STATE", "ZIP", "STATUS"]),
    }
    for sheet_name, (table, fields) in specs.items():
        ws = wb.create_sheet(sheet_name)
        write_rows(ws, [["Source File Layout", None, None, None, None, None, None, None,
                         "Stage Layer", None, None, None, "Standard Layer"]])
        write_rows(ws, [header], start_row=2)
        rows = []
        for i, f in enumerate(fields):
            phi = "Yes" if f in {"FIRST_NAME", "LAST_NAME", "DOB", "MEMBER_ID"} else "No"
            rows.append([f, "Not NULL" if i == 0 else "NULL", f"{f.title()} value", f"S{i:03d}",
                         "Date" if f.endswith("DATE") or f == "DOB" else "String", phi,
                         "Yes" if i == 0 else "No", "Load as is",
                         "stg_vendor_b", table, f, "String",
                         "vendor_b", table, f, "Date" if f.endswith("DATE") or f == "DOB" else "String"])
        for name, dtype in (("SRC_FILE_NAME", "string"), ("REC_CREATION_TIME", "timestamp"),
                            ("REC_UPDATED_TIME", "timestamp")):
            rows.append(["NA", "NULL", "NA", "NA", "NA", "No", "No", None,
                         "stg_vendor_b", table, name, dtype, "vendor_b", table, name, dtype])
        write_rows(ws, rows, start_row=3)
    return wb


def build_pair11():
    """Pair 11 (Family B, the one-block / many-files FRD's STTM): FILE_DETAILS
    with three files and their frequencies (the FRD's Frequency cell points
    here), three MAPPING- sheets whose stage tables the FRD never names (it
    lists the FILE names), two schemas across the three sheets, and a
    standard band that mixes a type inside one suffix group (the sibling-type
    check's target: one _pct column typed String among Decimal siblings)."""
    from . import frd as frd_fixtures

    wb = new_workbook()
    ws = wb.create_sheet("FILE_DETAILS")
    write_rows(ws, [["Vendor", "FileName", "File Description", "Location", "Frequency"]])
    files = [("VENDOR_C", frd_fixtures.PAIR11_FILES[0], None, None, "Yearly Twice"),
             ("VENDOR_C", frd_fixtures.PAIR11_FILES[1], None, None, "Yearly Twice"),
             ("VENDOR_C", frd_fixtures.PAIR11_FILES[2], None, None, "Monthly")]
    write_rows(ws, [list(f) for f in files], start_row=2)
    ws = wb.create_sheet("VERSION_HISTORY")
    write_rows(ws, [["Version", "Date", "Author", "Change Description"],
                    ["1.0", "2026-03-01", "SYN Author D", "Initial"]])
    header = (["Database column Name", "NULL CHECK", "Description", "Sample Value", "DataType",
               "PHI Field", "Mandatory Field", "Comment"] + _STAGE_STD_4 + _STAGE_STD_4)
    specs = {
        "MAPPING-VC_ENROLLMENT": ("stg_dom_a", "dom_a", "vc_enrollment",
                                  [("MEMBER_ID", "String"), ("ZIP_CODE", "String"),
                                   ("POVERTY_PCT", "Decimal(18,2)"), ("UNEMPLOYMENT_PCT", "Decimal(18,2)"),
                                   ("UNINSURED_PCT", "String"), ("TOTAL_POP", "Decimal(18,0)"),
                                   ("ELDERLY_POP", "Decimal(18,0)"), ("REPORT_DT", "Date")]),
        "MAPPING-VC_DISENROLLMENT": ("stg_dom_a", "dom_a", "vc_disenrollment",
                                     [("MEMBER_ID", "String"), ("ZIP_CODE", "String"),
                                      ("RISK_SCORE", "Decimal(18,4)"), ("RISK_CD", "String"),
                                      ("REPORT_DT", "Date")]),
        "MAPPING-VC_INDIVIDUAL_RISK": ("stg_dom_b", "dom_b", "vc_individual_risk",
                                       [("MEMBER_ID", "String"), ("RISK_SCORE", "Decimal(18,4)"),
                                        ("RISK_CD", "String"), ("REPORT_DT", "Date")]),
    }
    for sheet_name, (stage_schema, std_schema, table, fields) in specs.items():
        ws = wb.create_sheet(sheet_name)
        write_rows(ws, [["Source File Layout", None, None, None, None, None, None, None,
                         "Stage Layer", None, None, None, "Standard Layer"]])
        write_rows(ws, [header], start_row=2)
        rows = []
        for i, (f, dtype) in enumerate(fields):
            rows.append([f, "Not NULL" if i == 0 else "NULL", f"{f.title()} value", f"S{i:03d}",
                         "String", "Yes" if f == "MEMBER_ID" else "No",
                         "Yes" if i == 0 else "No", "Load as is",
                         stage_schema, table, f, "String",
                         std_schema, table, f, dtype])
        for name, dtype in (("SRC_FILE_NAME", "string"), ("REC_CREATION_TIME", "timestamp"),
                            ("REC_UPDATED_TIME", "timestamp")):
            rows.append(["NA", "NULL", "NA", "NA", "NA", "No", "No", None,
                         stage_schema, table, name, dtype, std_schema, table, name, dtype])
        write_rows(ws, rows, start_row=3)
    return wb


# --------------------------------------------------------------- Family C ---


def build_pair3():
    """Pair 3 (Family C): Version Control | Layout | STTM | FileNames.
    Layout: meta r1 FileName, headers r4 (13). STTM: meta r1-r2, band r4
    (4 merged groups), headers r5 (31)."""
    wb = new_workbook()
    write_rows(wb.create_sheet("Version Control"),
               [["Version", "Date", "Description", "Updated By"],
                ["1.0", "2026-01-08", "Initial", "SYN Author D"],
                ["1.1", "2026-01-22", "Added LOB columns", "SYN Author D"]])
    lob_cols = ["LOB_A", "LOB_B", "LOB_C", "LOB_D", "LOB_E"]
    fields = [("REC_ID", "X", 10), ("SUBSCRIBER_ID", "X", 12), ("MEMBER_SFX", "X", 2),
              ("LAST_NAME", "X", 35), ("FIRST_NAME", "X", 25), ("DOB", "9", 8),
              ("GENDER", "X", 1), ("ELIG_START", "9", 8), ("ELIG_END", "9", 8),
              ("PLAN_CD", "X", 6), ("GROUP_CD", "X", 8), ("PCP_ID", "X", 10),
              ("FILLER", "X", 20)]
    ws = wb.create_sheet("Layout")
    write_rows(ws, [["FileName", "feed_3_elig_YYYYMMDD.txt"]])
    header = ["Field #", "Field Name", "Req'd?", "Type", "Length", "Start", "End", "Comments"] + lob_cols
    assert len(header) == 13
    write_rows(ws, [header], start_row=4)
    start = 1
    rows = []
    for i, (name, typ, length) in enumerate(fields, start=1):
        rows.append([i, name, "Y" if i <= 3 else "N", typ, length, start, start + length - 1,
                     f"{name} as sent by SRC_SYS_A", "Y", "Y", "N", "Y", "N"])
        start += length
    write_rows(ws, rows, start_row=5)

    ws = wb.create_sheet("STTM")
    write_rows(ws, [["File Name", "See FileNames sheet"], ["Version", "1.1"]])
    groups = [("Source - [SRC_SYS_A] File", 12), ("Destination", 7),
              ("Target Table - Staging Layer", 6), ("Target Table - Standard Layer", 6)]
    write_rows(ws, [band_row(groups)], start_row=4)
    merge_bands(ws, 4, groups)
    header = (["Field #", "Field Name", "Type", "Length", "Start Position", "End Position",
               "Comments"] + lob_cols + ["Data Definition", "PII", "Primary Key", "Critical Data",
               "Required/Situational/Optional", "DQ Rules", "Load Rules"]
              + _STAGE_STD_6 + _STAGE_STD_6)
    assert len(header) == 31
    write_rows(ws, [header], start_row=5)
    start = 1
    rows = []
    for i, (name, typ, length) in enumerate(fields, start=1):
        rows.append([i, name, typ, length, start, start + length - 1, f"{name} as sent by SRC_SYS_A",
                     "Y", "Y", "N", "Y", "N",
                     f"{name} definition", "Y" if name in {"LAST_NAME", "FIRST_NAME", "DOB"} else "N",
                     "Y" if i == 2 else None, "N", "Required" if i <= 3 else "Optional",
                     "Not null" if i <= 3 else None, "Load as is",
                     "DLK", "syn_dlk", "stg_elig", "feed_3_elig", name, "String",
                     "DLK", "syn_std", "elig", "feed_3_elig", name, "Date" if typ == "9" and "D" in name else "String"])
        start += length
    write_rows(ws, rows, start_row=6)
    write_rows(wb.create_sheet("FileNames"),
               [["LOB", "Carrier", "Inbound File Name"],
                ["LOB_A", "CARRIER_1", "feed_3_elig_YYYYMMDD.txt"],
                ["LOB_B", "CARRIER_2", "feed_3_elig_b_YYYYMMDD.txt"]])
    return wb


# --------------------------------------------------------------- Family D ---


def build_pair4():
    """Pair 4 (Family D): STTM | LOB_CROSSWALK | OVERPUNCH_RULES. STTM meta
    r1 (File Name only), band r4 (4 merged groups), headers r5 (25)."""
    wb = new_workbook()
    ws = wb.create_sheet("STTM")
    write_rows(ws, [["File Name", "feed_4_remit_YYYYMMDD.dat"]])
    groups = [("Source Data", 7), ("Data Rules", 6),
              ("Target Table - Staging Layer", 6), ("Target Table - Standard Layer", 6)]
    write_rows(ws, [band_row(groups)], start_row=4)
    merge_bands(ws, 4, groups)
    lake = ["Workspace", "Target Catalog", "Target Schema Name in Lakehouse",
            "Target Table Name in Lakehouse", "Target Column Name in Lakehouse",
            "Target Data Type in Lakehouse"]
    header = (["Sl. No.", "Field Name", "Type", "Start", "End", "Len", "Description",
               "Data Definition", "PII", "Primary Key", "Critical Data", "Not NULL", "LOAD Rule"]
              + lake + lake)
    assert len(header) == 25
    write_rows(ws, [header], start_row=5)
    fields = [("REMIT_ID", "AN", 12), ("PAYER_ID", "AN", 10), ("PAYEE_NPI", "N", 10),
              ("CHECK_NUMBER", "AN", 15), ("CHECK_DATE", "N", 8), ("CHECK_AMOUNT", "S9(9)V99", 11),
              ("CLAIM_ID", "AN", 20), ("SERVICE_FROM", "N", 8), ("SERVICE_TO", "N", 8),
              ("BILLED_AMT", "S9(9)V99", 11), ("PAID_AMT", "S9(9)V99", 11), ("ADJ_REASON", "AN", 5)]
    start = 1
    rows = []
    for i, (name, typ, length) in enumerate(fields, start=1):
        rows.append([i, name, typ, start, start + length - 1, length, f"{name} description",
                     f"{name} definition", "N", "Y" if i == 1 else None, "N", "Y" if i <= 2 else "N",
                     "Overpunch decode" if typ.startswith("S9") else "Load as is",
                     "DLK", "syn_dlk", "stg_remit", "feed_4_remit", name, "String",
                     "DLK", "syn_std", "remit", "feed_4_remit", name,
                     "Decimal(11,2)" if typ.startswith("S9") else "String"])
        start += length
    for aud, dtype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                       ("REC_UPDATED_TIME", "Timestamp")):
        rows.append([None, "NA", None, None, None, None, "Audit column",
                     None, None, None, None, None, None,
                     "DLK", "syn_dlk", "stg_remit", "feed_4_remit", aud, dtype,
                     "DLK", "syn_std", "remit", "feed_4_remit", aud, dtype])
    write_rows(ws, rows, start_row=6)
    write_rows(wb.create_sheet("LOB_CROSSWALK"),
               [["Plan Code", "LOB", "Region"]] + [[f"P{i}", "ALL", f"REGION_{i}"] for i in range(1, 8)])
    ws = wb.create_sheet("OVERPUNCH_RULES")
    write_rows(ws, [["Overpunch decoding", None, None], ["Signed numeric last character", None, None],
                    ["Character", "Digit", "Sign"]])
    merge_span(ws, 1, 1, 3)
    merge_span(ws, 2, 1, 3)
    write_rows(ws, [[c, str(d), "+"] for d, c in enumerate("{ABCDEFGHI")]
               + [[c, str(d), "-"] for d, c in enumerate("}JKLMNOPQR")], start_row=4)
    return wb


def build_pair6():
    """Pair 6 (Family D): Version Control (header r2) | Server details (6
    environment-group merges) | FEED_6_MAPPING: band r2 'Source table' |
    'Stage Layer' | 'STD layer' (merged), headers r3 (22). DB-table source."""
    wb = new_workbook()
    _version_sheet(wb, "Version Control",
                   ["Version", "Date", "Author(s)", "Description of Version/Changes"], 2,
                   [["1.0", "2026-01-15", "SYN Author E", "Initial"],
                    ["1.1", "2026-02-01", "SYN Author E", "Added STD layer"]])
    ws = wb.create_sheet("Server details")
    write_rows(ws, [["Server", "Database", "Environment"]])
    row = 2
    for env in ("DEV", "QA", "UAT", "PRE-PROD", "PROD", "DR"):
        write_rows(ws, [[f"syn-{env.lower()}-db-01.synthetic.example", "SRC_SYS_C", env],
                        [f"syn-{env.lower()}-db-02.synthetic.example", "SRC_SYS_C_ARCHIVE", None],
                        [f"syn-{env.lower()}-db-03.synthetic.example", "SRC_SYS_C_REPORT", None]],
                   start_row=row)
        ws.merge_cells(start_row=row, start_column=3, end_row=row + 2, end_column=3)
        row += 3
    ws = wb.create_sheet("FEED_6_MAPPING")
    ws.cell(row=1, column=1, value="FEED_6 — SRC_SYS_C table to lakehouse mapping")
    groups = [("Source table", 10), ("Stage Layer", 6), ("STD layer", 6)]
    write_rows(ws, [band_row(groups)], start_row=2)
    merge_bands(ws, 2, groups)
    header = (["Inscope for Implementation", "SERVER NAME", "TABLE_CATALOG", "TABLE_SCHEMA",
               "TABLE_NAME", "COLUMN_NAME", "Primary Key", "DATA_TYPE", "NULL/NOT NULL",
               "Load Rules"] + _STAGE_STD_6 + _STAGE_STD_6)
    assert len(header) == 22
    write_rows(ws, [header], start_row=3)
    columns = [("AUTH_ID", "int", "Y"), ("MEMBER_KEY", "varchar", "N"), ("AUTH_STATUS", "char", "N"),
               ("REQUEST_DATE", "datetime", "N"), ("DECISION_DATE", "datetime", "N"),
               ("SERVICE_CODE", "varchar", "N"), ("UNITS_REQUESTED", "int", "N"),
               ("UNITS_APPROVED", "int", "N"), ("PROVIDER_KEY", "varchar", "N"),
               ("REVIEWER_ID", "varchar", "N"), ("CREATED_TS", "datetime", "N"),
               ("UPDATED_TS", "datetime", "N")]
    rows = []
    for name, typ, pk in columns:
        rows.append(["Y", "syn-prod-db-01.synthetic.example", "SRC_SYS_C", "dbo", "AUTHORIZATION",
                     name, pk, typ, "NOT NULL" if pk == "Y" else "NULL", "Load as is",
                     "DLK", "syn_dlk", "stg_um", "src_sys_c_authorization", name, "String",
                     "DLK", "syn_std", "um", "src_sys_c_authorization", name,
                     {"int": "Int", "datetime": "Timestamp"}.get(typ, "String")])
    for aud, dtype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                       ("REC_UPDATED_TIME", "Timestamp")):
        rows.append([None, None, None, None, None, "NA", None, None, None, None,
                     "DLK", "syn_dlk", "stg_um", "src_sys_c_authorization", aud, dtype,
                     "DLK", "syn_std", "um", "src_sys_c_authorization", aud, dtype])
    write_rows(ws, rows, start_row=4)
    return wb


# --------------------------------------------------------------- Family E ---


def build_pair5():
    """Pair 5 (Family E): Version History (band r3, headers r4) | File
    Details (7) | Table_Details | FEED_5_MAPPING (meta r1-r9, band r10
    3 merged groups, headers r11 = 33) | Sheet2 | Sheet3 | Sheet1 (DQ)."""
    wb = new_workbook()
    ws = wb.create_sheet("Version History")
    ws.cell(row=3, column=1, value="Document Version History")
    merge_span(ws, 3, 1, 4)
    write_rows(ws, [["Version", "Date", "Author", "Description"],
                    ["1.0", "2026-01-20", "SYN Author F", "Initial"]], start_row=4)
    write_rows(wb.create_sheet("File Details"),
               [["Vendor", "FileName", "Actual File Name", "File Description", "Location",
                 "Frequency", "File Extension"],
                ["VENDOR_E", "FEED_5_*.txt", "FEED_5_20260115.txt", "Claims file", "inbound/vendor_e",
                 "Weekly", ".txt"]])
    write_rows(wb.create_sheet("Table_Details"),
               [["S.No", "SchemaName", "Table_Name", "Table_Description"],
                [1, "stg_clm", "feed_5_dtl", "Claims detail"]])
    ws = wb.create_sheet("FEED_5_MAPPING")
    meta = [["File(s)", "FEED_5_*.txt"], ["File Generator", None],
            ["File Location", "inbound/vendor_e"], ["LOB", "ALL"], ["File frequency", "Weekly"],
            ["Domain", "Claims"], ["Sub-Domain", "Medical"],
            ["NOTE", "Files are pipe delimited; header and trailer rows carry record counts."],
            ["File type", "txt (pipe delimited |)"]]
    write_rows(ws, meta, start_row=1)
    groups = [("Source Layout", 11), ("Stage Layer", 11), ("Standard Layer", 11)]
    write_rows(ws, [band_row(groups)], start_row=10)
    merge_bands(ws, 10, groups)
    layer = ["Catalog", "Schema", "TableName", "ColumnName", "DataType", "Mandatory",
             "Primary Key", "Constraints", "Field Description", "Table Description",
             "Transformations/Data Quality"]
    header = (["Field Id", "Column No.", "Field Name", "Data Type", "Length", "Field Length",
               "Start position", "End Position", "Segment", "PII/PHI", "Comments"] + layer + layer)
    assert len(header) == 33
    write_rows(ws, [header], start_row=11)
    segments = {
        "Header": ("feed_5_hdr", [("Record Type", "Static text identifying the header record. Contains the value HDR"),
                                  ("File Date", "File creation date"), ("Sender", "Sender identifier")]),
        "Detail": ("feed_5_dtl", [("Claim Number", "Claim identifier"), ("Member Id", "Member identifier"),
                                  ("Service Date", "Date of service"), ("Billed Amount", "Amount billed"),
                                  ("Paid Amount", "Amount paid"), ("Provider Id", "Rendering provider"),
                                  ("Diagnosis Code", "Primary diagnosis"), ("Procedure Code", "Procedure")]),
        "Trailer": ("feed_5_trl", [("Record Type", "Static text identifying the trailer record. Contains the value TRL"),
                                   ("Record Count", "Number of detail records")]),
    }
    rows = []
    fid = 0
    for segment, (table, fields) in segments.items():
        for colno, (name, comment) in enumerate(fields, start=1):
            fid += 1
            stage_col = name.upper().replace(" ", "_")
            rows.append([fid, colno, name, "varchar", 20, None, None, None, segment,
                         "Yes" if name == "Member Id" else "No", comment,
                         "syn_dlk", "stg_clm", table, stage_col, "String",
                         "Yes" if colno == 1 else None, None, None, comment, f"{segment} table", None,
                         "syn_std", "clm", table, stage_col, "String",
                         None, None, None, comment, f"{segment} table", "Load as is"])
        for aud, dtype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "timestamp")):
            rows.append([None] * 11 + ["syn_dlk", "stg_clm", table, aud, dtype] + [None] * 6
                        + ["syn_std", "clm", table, aud, dtype] + [None] * 6)
    write_rows(ws, rows, start_row=12)
    write_rows(wb.create_sheet("Sheet2"),
               [["Field", "Expansion", "Note"], ["Diagnosis Code", "Split into DX1..DX5", "future"],
                ["Procedure Code", "Split into PX1..PX3", "future"]])
    write_rows(wb.create_sheet("Sheet3"), [[n] for n in ("Claim Number", "Member Id", "Service Date")])
    write_rows(wb.create_sheet("Sheet1"),
               [["FieldName", "DQ Rules", "DataType"], ["Claim Number", "Not null", "varchar"],
                ["Service Date", "Valid date yyyyMMdd", "varchar"], ["Paid Amount", ">= 0", "decimal"]])
    return wb


def build_pair7():
    """Pair 7 (Family E): Version History (band r5, headers r6) | File
    Details | MAPPING_FEED_7 (field headers r1 = 19 cols, NO band row —
    the Stage/Standard prefixes live in the header texts) | Sheet2 |
    Queries | Analysis_Notes | Analysis Sheet - Detail | Analysis Sheet -
    Compound | Sample Records | Sheet1."""
    wb = new_workbook()
    ws = wb.create_sheet("Version History")
    ws.cell(row=5, column=1, value="Version History")
    merge_span(ws, 5, 1, 4)
    write_rows(ws, [["Version", "Date", "Author", "Description"],
                    ["1.0", "2026-01-25", "SYN Author G", "Initial"]], start_row=6)
    write_rows(wb.create_sheet("File Details"),
               [["Vendor", "FileName", "File Description", "Location", "Frequency (Historical Drops)"],
                ["VENDOR_G", "FEED_7_RX_*.dat", "Pharmacy claims", "inbound/vendor_g", "Daily"],
                ["VENDOR_G", "FEED_7_RX_HIST_*.dat", "Pharmacy claims history", "inbound/vendor_g", "One time"]])
    ws = wb.create_sheet("MAPPING_FEED_7")
    header = ["Field ID", "Field Name", "Mandatory or Situational", "Column Description", "Comments",
              "Format", "Size", "PHI/PII Field", "Stage Schema", "Stage Table Name",
              "Stage Table - Column Name", "Stage Table - DataType", "Standard Schema",
              "Standard Table Name", "Standard Table - Column Name", "Standard Data Type",
              "Mandatory Fields (Include in DQ Check)", "Recycle Flag", "Comments"]
    assert len(header) == 19
    write_rows(ws, [header])
    fields = [("101-A1", "BIN Number", "M", "9(6)", 6), ("102-A2", "Version Release", "M", "X(2)", 2),
              ("103-A3", "Transaction Code", "M", "X(2)", 2), ("104-A4", "Processor Control", "S", "X(10)", 10),
              ("109-A9", "Transaction Count", "M", "9(1)", 1), ("201-B1", "Service Provider ID", "M", "X(15)", 15),
              ("302-C2", "Cardholder ID", "M", "X(20)", 20), ("401-D1", "Date of Service", "M", "9(8)", 8),
              ("402-D2", "Prescription Number", "M", "9(12)", 12), ("407-D7", "Product ID", "M", "X(19)", 19),
              ("442-E7", "Quantity Dispensed", "M", "9(7)V999", 10), ("405-D5", "Days Supply", "M", "9(3)", 3)]
    rows = []
    for fid, name, ms, fmt, size in fields:
        stage_col = name.upper().replace(" ", "_")
        rows.append([fid, name, ms, f"{name} per the vendor spec", None, fmt, size,
                     "Yes" if name == "Cardholder ID" else "No",
                     "stg_rx", "feed_7_rx_claims", stage_col, "String",
                     "rx", "feed_7_rx_claims", stage_col, "Decimal(10,3)" if "V" in fmt else "String",
                     "Y" if ms == "M" else None, None, None])
    write_rows(ws, rows, start_row=2)
    write_rows(wb.create_sheet("Sheet2"), [[f"SYN-ID-{i:04d}"] for i in range(1, 16)])
    write_rows(wb.create_sheet("Queries"), [["Is the history drop a full replace?"], ["Which BIN values are in scope?"]])
    write_rows(wb.create_sheet("Analysis_Notes"),
               [["Records analysed", 1200], ["Compound records", 40], ["Distinct BINs", 3]])
    write_rows(wb.create_sheet("Analysis Sheet - Detail"),
               [["FIELD_NAME", "TEXTVALUE", "FIELD_NO"]] + [[n, "sample", f] for f, n, *_ in fields])
    write_rows(wb.create_sheet("Analysis Sheet - Compound"),
               [["Field", "Field Name", "Mandatory or Situational", "Source", "Format", "Size", "Start",
                 "End", "Record Analysis", "Record Analysis"],
                ["CD", "Compound Ingredient", "S", "Vendor", "X(19)", 19, 1, 19, "seen", "3 per claim"]])
    write_rows(wb.create_sheet("Sample Records"), [["SYNBIN|D0|B1|SYNPCN|1|..."], ["SYNBIN|D0|B1|SYNPCN|1|..."]])
    write_rows(wb.create_sheet("Sheet1"),
               [["Source Field"] + [f"LEGACY_COL_{i}" for i in range(1, 17)],
                ["BIN Number"] + ["BIN"] + [None] * 15])
    return wb


def build_pair9():
    """Pair 9 (Family E): Summary | MAPPING_FEED_9 | MAPPING_FEED_9_TBL2 |
    Sheet2 | Log (header r2) | Sheet1. Band r1 'Source Tables' | 'Target -
    DL Staging Layer' | 'Target - DL Standard Layer' (merged), headers r2
    (24). DB source. NOTE: the documented pair 9 has ONE 1,400-row mapping
    sheet spanning 36 tables; the fixture splits two tables onto two
    mapping sheets to exercise the family's one-sheet-per-table shape."""
    wb = new_workbook()
    write_rows(wb.create_sheet("Summary"),
               [["S.No", "Source", "Source Type", "Name", "Table Description", "Total Count",
                 "Load strategy(Stage)", "Load strategy(std)"],
                [1, "SRC_SYS_D", "Table", "ENCOUNTER", "Encounter header", 12, "Truncate and Load", "Upsert"],
                [2, "SRC_SYS_D", "Table", "ENCOUNTER_LINE", "Encounter lines", 10, "Truncate and Load", "Upsert"]])
    header = (["DataBase", "Schema", "TableName", "ColumnName", "Key (Y/N)", "Required", "Length",
               "Data Type", "Column Description", "Column Long Description", "PII",
               "Critical Data elements"] + ["Workspace", "Catalog", "Schema", "TableName",
                                             "ColumnName", "Data Type"] * 2)
    assert len(header) == 24
    tables = {
        "MAPPING_FEED_9": ("ENCOUNTER", [("ENCOUNTER_ID", "bigint", "Y"), ("MEMBER_KEY", "varchar", "N"),
                                          ("PROVIDER_KEY", "varchar", "N"), ("ENCOUNTER_DATE", "date", "N"),
                                          ("ENCOUNTER_TYPE", "varchar", "N"), ("STATUS", "varchar", "N"),
                                          ("TOTAL_CHARGE", "decimal", "N"), ("LOB_CD", "varchar", "N"),
                                          ("CREATED_TS", "timestamp", "N"), ("UPDATED_TS", "timestamp", "N"),
                                          ("SOURCE_BATCH", "varchar", "N"), ("IS_DELETED", "bit", "N")]),
        "MAPPING_FEED_9_TBL2": ("ENCOUNTER_LINE", [("ENCOUNTER_LINE_ID", "bigint", "Y"), ("ENCOUNTER_ID", "bigint", "N"),
                                                    ("LINE_NO", "int", "N"), ("PROCEDURE_CD", "varchar", "N"),
                                                    ("MODIFIER", "varchar", "N"), ("UNITS", "int", "N"),
                                                    ("CHARGE_AMT", "decimal", "N"), ("DIAGNOSIS_CD", "varchar", "N"),
                                                    ("CREATED_TS", "timestamp", "N"), ("UPDATED_TS", "timestamp", "N")]),
    }
    for sheet_name, (table, columns) in tables.items():
        ws = wb.create_sheet(sheet_name)
        groups = [("Source Tables", 12), ("Target - DL Staging Layer", 6), ("Target - DL Standard Layer", 6)]
        write_rows(ws, [band_row(groups)])
        merge_bands(ws, 1, groups)
        write_rows(ws, [header], start_row=2)
        rows = []
        for name, typ, key in columns:
            rows.append(["SRC_SYS_D", "dbo", table, name, key, "Y" if key == "Y" else "N",
                         50 if typ == "varchar" else None, typ, f"{name} description",
                         f"{name} long description", "N", "N",
                         "DLK", "syn_dlk", "stg_enc", f"src_sys_d_{table.lower()}", name, "String",
                         "DLK", "syn_std", "enc", f"src_sys_d_{table.lower()}", name,
                         {"bigint": "BigInt", "int": "Int", "date": "Date", "timestamp": "Timestamp",
                          "decimal": "Decimal(18,2)", "bit": "Boolean"}.get(typ, "String")])
        write_rows(ws, rows, start_row=3)
    write_rows(wb.create_sheet("Sheet2"), [["ENCOUNTER_ID", 1001], ["MEMBER_KEY", "M-0001"], ["STATUS", "A"]])
    ws = wb.create_sheet("Log")
    ws.cell(row=1, column=1, value="Change log")
    write_rows(ws, [["Version", "Date", "Description"], ["1.0", "2026-01-30", "Initial"]], start_row=2)
    write_rows(wb.create_sheet("Sheet1"), [["ENCOUNTER_ID"], ["MEMBER_KEY"], ["PROVIDER_KEY"]])
    return wb


def build_pair10():
    """Pair 10 (Family E): Version (header r2) | Outbound_REGION_A (17) |
    Inbound_REGION_A (20) | Inbound_REGION_B_Adult (18) |
    Inbound_REGION_B_Child (18) | Mapping (vendor spec). Each mapping
    sheet: meta r2 (Target Table Description), band r4 (3 merged groups),
    headers r5. The document does not record pair 10's band TEXTS; the
    fixture uses 'Source Data' | 'Stage Layer' | 'Standard Layer'."""
    wb = new_workbook()
    _version_sheet(wb, "Version", ["Date", "Version", "Author(s)", "Description of Version/Changes"], 2,
                   [["2026-02-03", "1.0", "SYN Author H", "Initial"]])
    stage6 = ["Workspace", "Catalog", "Stage Schema", "Stage Table Name", "Stage Column Name", "Stage DataType"]
    std6 = ["Workspace", "Catalog", "Standard Schema", "Standard Table Name", "Standard Column Name", "Standard Data Type"]

    def sheet(title, description, source_headers, stage_headers, std_headers, rows_src, table):
        ws = wb.create_sheet(title)
        ws.cell(row=2, column=1, value="Target Table Description")
        ws.cell(row=2, column=2, value=description)
        groups = [("Source Data", len(source_headers)), ("Stage Layer", 6), ("Standard Layer", 6)]
        write_rows(ws, [band_row(groups)], start_row=4)
        merge_bands(ws, 4, groups)
        header = source_headers + stage_headers + std_headers + ["Comments"]
        write_rows(ws, [header], start_row=5)
        rows = []
        for src in rows_src:
            name = src[0] if title.startswith("Outbound") else src[1]
            stage_col = str(name).upper().replace(" ", "_").replace("#", "NO")
            rows.append(list(src) + ["DLK", "syn_dlk", "stg_survey", table, stage_col, "String",
                                     "DLK", "syn_std", "survey", table, stage_col, "String", None])
        write_rows(ws, rows, start_row=6)
        return len(header)

    n = sheet("Outbound_REGION_A", "Members selected for the outbound survey file",
              ["Source Column Name", "Nullable ?", "Description", "PII (Y/N)"],
              ["Workspace", "Catalog", "Stage Schema", "Stage Table Name", "Stage_Column_Name", "Datatype"],
              ["Workspace", "Catalog", "Standard Schema", "Standard Table Name", "Standard Column_Name", "Datatype"],
              [(c, "N" if i < 3 else "Y", f"{c} description", "Y" if c in {"MEMBER_NAME", "PHONE"} else "N")
               for i, c in enumerate(["MEMBER_ID", "SURVEY_WAVE", "LOB", "MEMBER_NAME", "PHONE",
                                      "LANGUAGE", "REGION", "PLAN_CODE", "SAMPLE_FLAG", "MAIL_DATE"])],
              "feed_10_outbound_a")
    assert n == 17
    n = sheet("Inbound_REGION_A", "Survey responses, region A",
              ["Survey Item #", "Data Field", "PII Y/N", "Type", "Mandatory?", "Value/Question", "Description"],
              stage6, std6,
              [(i, f"Q{i} Response", "N", "Numeric", "Y" if i <= 2 else "N", f"Question {i} text",
                f"Response to question {i}") for i in range(1, 13)],
              "feed_10_inbound_a")
    assert n == 20
    for suffix in ("Adult", "Child"):
        n = sheet(f"Inbound_REGION_B_{suffix}", f"Survey responses, region B ({suffix.lower()})",
                  ["Survey Item #", "Data Field", "Description", "PII Field", "Mandatory?"],
                  stage6, std6,
                  [(i, f"Q{i} Response", f"Response to question {i}", "N", "Y" if i <= 2 else "N")
                   for i in range(1, 11)],
                  f"feed_10_inbound_b_{suffix.lower()}")
        assert n == 18
    write_rows(wb.create_sheet("Mapping"),
               [["Field", "Value/Question", "Result Values for File Spec", "Type", "Required?"]]
               + [[f"Q{i} Response", f"Question {i} text", "1-5", "Numeric", "Y" if i <= 2 else "N"]
                  for i in range(1, 13)])
    return wb


BUILDERS = {
    "sttm/pair_1_family_a.xlsx": build_pair1,
    "sttm/pair_8_family_a.xlsx": build_pair8,
    "sttm/pair_2_family_b.xlsx": build_pair2,
    "sttm/pair_11_family_b.xlsx": build_pair11,
    "sttm/pair_3_family_c.xlsx": build_pair3,
    "sttm/pair_4_family_d.xlsx": build_pair4,
    "sttm/pair_6_family_d.xlsx": build_pair6,
    "sttm/pair_5_family_e.xlsx": build_pair5,
    "sttm/pair_7_family_e.xlsx": build_pair7,
    "sttm/pair_9_family_e.xlsx": build_pair9,
    "sttm/pair_10_family_e.xlsx": build_pair10,
}
