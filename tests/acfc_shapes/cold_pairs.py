# ruff: noqa: E501  -- fixture data tables: one STTM / FRD row per line
"""Cold pairs (Chunk B, 2026-10-09): six synthetic FRD + STTM pairs a
framework owner could hand the agent cold — built byte-stably from the spec
``tests/acfc_shapes/COLD_PAIRS.md`` (designed blind to the reader code and the
synonym tables). Every value is invented: Contoso Health (``ch_``), Fabrikam
Care (``fc_``), Northwind Benefits (``nb_``); catalogs, where stated at all,
the logical ``PR_DLK`` / ``PR_STD``.

Materialized under ``fixtures/acfc_shapes/cold/<id>/`` as
``STTM_<feed>.xlsx`` + ``FRD_<feed>.docx``; each pair directory also holds the
hand-written ``answers.yaml`` (what a human answers) and
``expected_questions.yaml`` (the QUESTION / UNRESOLVED keys each CLI stage
must print before the answers), both pinned by ``tests/test_cold_pairs.py``.

The FRD tables are written by a local OOXML writer, not ``common.table``:
the spec's cells carry a literal ``|`` (which ``common._runs`` models as a
run split) and the F2 Solution Requirement tables merge the value across
columns 2–4 (``w:gridSpan``), the way Word stores them.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .common import docx_bytes, merge_span, new_workbook, write_rows

# ------------------------------------------------------------------ docx


def _p(text: str, style: str | None = None) -> str:
    """A paragraph; an embedded newline is a ``<w:br/>`` (Shift+Enter)."""
    props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    runs = "<w:r><w:br/></w:r>".join(
        f'<w:r><w:t xml:space="preserve">{escape(part)}</w:t></w:r>' if part else ""
        for part in text.split("\n"))
    return f"<w:p>{props}{runs}</w:p>"


def _tbl(rows: list[list], width: int | None = None) -> str:
    """A Word table. A cell is a string, or ``(text, span)`` for a cell merged
    across ``span`` grid columns (``w:gridSpan``)."""
    def cells(row: list) -> list[tuple[str, int]]:
        return [c if isinstance(c, tuple) else (c, 1) for c in row]

    grid_width = width or max(sum(span for _t, span in cells(r)) for r in rows)
    grid = "".join('<w:gridCol w:w="2400"/>' for _ in range(grid_width))
    body = []
    for row in rows:
        tcs = []
        for text, span in cells(row):
            props = f'<w:tcPr><w:gridSpan w:val="{span}"/></w:tcPr>' if span > 1 else ""
            tcs.append(f"<w:tc>{props}{_p(text)}</w:tc>")
        body.append(f"<w:tr>{''.join(tcs)}</w:tr>")
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
            f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{''.join(body)}</w:tbl>")


def _f1(ref: str, title: str, rows: list[tuple[str, str, str]]) -> str:
    """An F1 section table, ``Ref | Label | Value``; row 0 = the section title."""
    return _tbl([[ref, title, ""], *[list(r) for r in rows]])


def _sr(number: int, rows: list[tuple[str, str]]) -> str:
    """An F2 Solution Requirement table: 4 grid columns, the value merged
    across columns 2–4; row 0 = ``Solution Requirement: <n>``."""
    return _tbl([[f"Solution Requirement: {number}", ("", 3)],
                 *[[label, (value, 3)] for label, value in rows]], width=4)


def _sr_rows(name: str, business: str, functional: str, section: tuple[str, str],
             acceptance: str, priority: str, source: str, traced: str) -> list[tuple[str, str]]:
    return [("Name", name), ("Business Requirement", business),
            ("Functional Requirement:", functional), section,
            ("Impact Details", ""), ("Solution Acceptance Criteria", acceptance),
            ("Priority", priority), ("Source/Reference", source),
            ("Traced/Related Requirements", traced), ("IS Owner", "Synthetic IS Owner")]


# ------------------------------------------------------------------ xlsx helpers


def _merge(ws, row: int, first: int, last: int) -> None:
    merge_span(ws, row, first, last)


def _sheet(wb, name: str, rows: list[list], start_row: int = 1):
    ws = wb.create_sheet(name)
    write_rows(ws, rows, start_row)
    return ws


# ================================================================== cold_1

COLD_1 = "ch_claims_daily"


def build_sttm_cold_1():
    """Family A inline meta; the Standard band (I–N) LEFT of the Stage band (O–T)."""
    wb = new_workbook()
    ws = _sheet(wb, "Version", [
        ["Contoso Health – Claims Daily STTM", None, None, None],
        [],
        ["Date", "Version", "Author(s)", "Description of Version/Changes"],
        ["2026-09-01", "1.0", "Synthetic Analyst A", "Initial draft"],
        ["2026-09-15", "1.1", "Synthetic Analyst B", "Added audit columns"],
    ])
    _merge(ws, 1, 1, 4)
    meta = [["File Names", "CH_CLAIMS_DAILY_YYYYMMDD.psv"],
            ["File Name Example", "CH_CLAIMS_DAILY_20260901.psv"],
            ["Frequency", "Daily"],
            ["File Format (text, csv)", "Delimited text"],
            ["File Delimiter", ","],
            ["Last Update Date", "2026-09-15"],
            ["Version", "1.1"],
            ["LOB", "ALL"],
            ["Target table Name Desc", "Daily professional and institutional claim headers"],
            ["Feed Type", "Inbound"],
            ["Load Strategy", "STG: Append; STD: Upsert"],
            []]
    titles = ["Source Data", None, None, None, None, None, "Data Rules and Primary Keys", None,
              "Standard Layer Table", None, None, None, None, None,
              "Staging Layer Table", None, None, None, None, None]
    band = ["Target Catalog", "Target Schema Name", "Target Table Name", "Target Column Name",
            "Target Data Type", "Load Rules"]
    header = ["S.No", "Field Name", "Required?", "Format", "Length", "Description",
              "Primary Key", "Not NULL", *band, *band]
    fields = [
        (1, "claim_id", "Y", "String", 20, "Unique claim identifier", "Y", "Y", "CLAIM_ID", "String", "Direct", "String", "Direct"),
        (2, "member_id", "Y", "String", 12, "Member identifier", "N", "Y", "MEMBER_ID", "String", "Direct", "String", "Direct"),
        (3, "service_from_date", "Y", "Date (YYYYMMDD)", 8, "First date of service", "N", "Y", "SERVICE_FROM_DATE", "Date", "Cast to DATE using yyyyMMdd", "String", "Direct"),
        (4, "billed_amount", "N", "Decimal", 12, "Total billed amount", "N", "N", "BILLED_AMOUNT", "Decimal(12,2)", "Cast to DECIMAL(12,2)", "String", "Direct"),
        (5, "claim_status", "Y", "String", 2, "Adjudication status code", "N", "Y", "CLAIM_STATUS", "String", "Direct", "String", "Direct"),
        (6, "provider_npi", "N", "String", 10, "Billing provider identifier", "N", "N", "PROVIDER_NPI", "String", "Direct", "String", "Direct"),
    ]
    std = ("PR_STD", "ch_claims", "ch_claim_header")
    stg = ("PR_DLK", "stg_ch_claims", "ch_claim_header")
    body = [[n, name, req, fmt, length, desc, pk, nn, *std, col, std_type, std_rule,
             *stg, col, stg_type, stg_rule]
            for n, name, req, fmt, length, desc, pk, nn, col, std_type, std_rule, stg_type, stg_rule
            in fields]
    for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                             ("REC_UPDATED_TIME", "Timestamp")):
        body.append([None, "NA", None, None, None, None, None, None,
                     *std, column, datatype, "Populated by framework",
                     *stg, column, datatype, "Populated by framework"])
    ws = _sheet(wb, "CH_CLAIMS_DAILY", [*meta, titles, header, *body])
    for first, last in ((1, 6), (7, 8), (9, 14), (15, 20)):
        _merge(ws, 13, first, last)
    return wb


def build_frd_cold_1() -> bytes:
    """F1: no heading styles, a sequence of Word tables (Ref | Label | Value)."""
    return docx_bytes([
        _tbl([["Version", "Date", "Author", "Change"],
              ["1.0", "2026-08-28", "Synthetic BSA", "Initial"]]),
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", "ch_claims_daily"),
            ("DM-2", "Description", "Daily claim headers from Contoso Health"),
            ("DM-3", "Functional Requirement", "The system shall ingest the Contoso Health daily claims file into the stage and standard layers."),
            ("DM-4", "Data Source", "Contoso Health"),
            ("DM-5", "Object Name", "CH_CLAIMS_DAILY_YYYYMMDD.psv"),
            ("DM-6", "Description", "One file per business day with all claim headers adjudicated that day"),
            ("DM-7", "Frequency", "Daily"),
            ("DM-8", "LOBs", "ALL"),
            ("DM-9", "Tags/Keywords", "claims, daily"),
            ("DM-10", "Inbound Ingestion", "Y"),
            ("DM-11", "Impact Details", ""),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "ch_claims_daily structure"),
            ("SM-2", "Description", "File and target structure"),
            ("SM-3", "Functional Requirement", "Land the file to stage, then publish to standard."),
            ("SM-4", "Object/data Format", "Pipe delimited (|) text file, extension .psv, first row is a column header"),
            ("SM-5", "Target Catalog and Schema", "Stage: PR_DLK.stg_ch_claims; Standard: PR_STD.ch_claims"),
            ("SM-6", "Target Table Name", "ch_claim_header"),
            ("SM-7", "Domain and Subdomain", "Claims / Professional and Institutional"),
            ("SM-8", "Load Strategy STG", "Append"),
            ("SM-9", "Load Strategy STD", "Upsert on claim_id"),
            ("SM-10", "Archive Schedule", "7 years"),
            ("SM-11", "Source Data Dictionary", "Not provided"),
            ("SM-12", "ADLS Location", "inbound/contoso_health/claims_daily/"),
            ("SM-13", "Inbound File Folder Path", "mftlanding/inbound/claims/contoso_health/"),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "claim_id"),
            ("TM-2", "PII Fields", "member_id"),
            ("TM-3", "Business Key", "claim_id"),
            ("TM-4", "Foreign Key(s)", "None"),
            ("TM-5", "Transformation Logic", "Dates cast from yyyyMMdd; amounts to DECIMAL(12,2)"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-1", "Uniqueness/Duplicate Record check/reject (HARD - In pipeline)", "Reject duplicate claim_id within a file"),
            ("DQ-2", "Incomplete Record Rejection Process (HARD - In pipeline)", "Reject records where claim_id or member_id is blank"),
            ("DQ-3", "Record Recycle Process (HARD - In pipeline)", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Contoso Health"),
            ("VM-2", "Vendor Abbreviation", "CH"),
        ]),
    ])


# ================================================================== cold_2

COLD_2 = "fc_elig_monthly"


def build_sttm_cold_2():
    """Fixed width, H / D / T banner rows, titles ``Target 1`` / ``Target 2``."""
    wb = new_workbook()
    _sheet(wb, "Revision Log", [["Rev", "Date", "Changed By", "Notes"],
                                ["A", "2026-08-11", "Synthetic Analyst D", "First cut"],
                                ["B", "2026-09-03", "Synthetic Analyst D", "Trailer count added"]])
    meta = [["Inbound File", "FC_ELIG_MTH_CCYYMM.dat"], ["Record Length", 120],
            ["File Layout", "Fixed width; Header, Detail and Trailer records"],
            ["LOB", "MCD, CHIP"], []]
    titles = ["Vendor Layout", None, None, None, None, None, None, None,
              "Target 1", None, None, None, None, None, "Target 2", None, None, None, None, None]
    target = ["Schema", "TableName", "ColumnName", "DataType", "Nullable", "Key"]
    header = ["Seq", "Record Type", "Field Name", "Start", "End", "Length", "Type", "Notes",
              *target, *target]
    land, std = "fc_elig_land", "fc_elig"
    hdr, dtl, trl = "fc_elig_hdr", "fc_elig_dtl", "fc_elig_trl"
    blank6 = [None] * 6

    def row(seq, rt, name, start, end, length, typ, notes, table, column, t1_null, t1_key,
            standard=None):
        t2 = blank6 if standard is None else [std, dtl, column, *standard]
        return [seq, rt, name, start, end, length, typ, notes,
                land, table, column, "String", t1_null, t1_key, *t2]

    body = [
        ["Header Record"],
        row(1, "H", "rec_type", 1, 1, 1, "X", "Always 'H'", hdr, "REC_TYPE", "N", "N"),
        row(2, "H", "file_create_date", 2, 9, 8, "9(8)", "CCYYMMDD", hdr, "FILE_CREATE_DATE", "N", "N"),
        row(3, "H", "sender_id", 10, 19, 10, "X(10)", "Sender code", hdr, "SENDER_ID", "N", "N"),
        ["Detail Record"],
        row(4, "D", "rec_type", 1, 1, 1, "X", "Always 'D'", dtl, "REC_TYPE", "N", "N", ("String", "N", "N")),
        row(5, "D", "member_id", 2, 13, 12, "X(12)", "Member identifier", dtl, "MEMBER_ID", "N", "Y", ("String", "N", "Y")),
        row(6, "D", "last_name", 14, 48, 35, "X(35)", None, dtl, "LAST_NAME", "Y", "N", ("String", "Y", "N")),
        row(7, "D", "first_name", 49, 73, 25, "X(25)", None, dtl, "FIRST_NAME", "Y", "N", ("String", "Y", "N")),
        row(8, "D", "birth_date", 74, 81, 8, "9(8)", "CCYYMMDD", dtl, "BIRTH_DATE", "N", "N", ("Date", "N", "N")),
        row(9, "D", "elig_start", 82, 89, 8, "9(8)", "CCYYMMDD", dtl, "ELIG_START", "N", "Y", ("Date", "N", "Y")),
        row(10, "D", "elig_end", 90, 97, 8, "9(8)", "CCYYMMDD; 99991231 = open", dtl, "ELIG_END", "Y", "N", ("Date", "Y", "N")),
        row(11, "D", "plan_code", 98, 103, 6, "X(6)", None, dtl, "PLAN_CODE", "N", "N", ("String", "N", "N")),
        ["Trailer Record"],
        row(12, "T", "rec_type", 1, 1, 1, "X", "Always 'T'", trl, "REC_TYPE", "N", "N"),
        row(13, "T", "record_count", 2, 10, 9, "9(9)", "Count of D records", trl, "RECORD_COUNT", "N", "N"),
        [14, "T", "filler", 11, 120, 110, "X(110)", "Filler – not loaded"],
    ]
    for rt, table in (("H", hdr), ("D", dtl), ("T", trl)):
        for column, datatype in (("SRC_FILE_NAME", "String"), ("LOAD_TS", "Timestamp"),
                                 ("BATCH_ID", "String")):
            t2 = [std, dtl, column, datatype, "N", "N"] if rt == "D" else blank6
            body.append([None, rt, "NA", None, None, None, None, None,
                         land, table, column, datatype, "N", "N", *t2])
    ws = _sheet(wb, "FC_ELIG_LAYOUT", [*meta, titles, header, *body])
    for first, last in ((1, 8), (9, 14), (15, 20)):
        _merge(ws, 6, first, last)
    for banner_row in (8, 12, 21):
        _merge(ws, banner_row, 1, 20)
    _sheet(wb, "Record Type Codes", [["Code", "Meaning"], ["H", "Header"], ["D", "Detail"],
                                     ["T", "Trailer"]])
    return wb


def build_frd_cold_2() -> bytes:
    """F2: Heading 1, a paragraph, a 2×2 domain table, three SR tables."""
    return docx_bytes([
        _p("Fabrikam Care Monthly Eligibility – Functional Requirements", "Heading1"),
        _p("This document describes the monthly eligibility feed from Fabrikam Care."),
        _tbl([["Domain", "Eligibility"], ["Sub Domain", "Enrollment Spans"]]),
        _sr(1, _sr_rows(
            "Receive monthly eligibility file",
            "Member services needs current eligibility spans.",
            "The system shall ingest the fixed-width file FC_ELIG_MTH_CCYYMM.dat, delivered monthly by the 5th business day, from mftlanding/inbound/eligibility/fabrikam_care/.",
            ("Structural Metadata", "Record length 120. Header (H), Detail (D) and Trailer (T) records are identified by the value in position 1."),
            "Trailer record_count equals the number of D records in the file.",
            "High", "Vendor layout v3", "SYN-REQ-2201")),
        _sr(2, _sr_rows(
            "Load to landing layer",
            "Keep every monthly file as received.",
            "Each record type shall be loaded to its own landing table in schema fc_elig_land, appending each month's file.",
            ("Technical Metadata", "Primary key of the detail record: member_id + elig_start."),
            "Three landing tables populated per file.",
            "High", "", "SYN-REQ-2202")),
        _sr(3, _sr_rows(
            "Publish to standard layer",
            "Analysts query one curated eligibility table.",
            "Detail records shall be published to fc_elig.fc_elig_dtl. Header and trailer records are not published.",
            ("Data Quality", "Reject detail records with a blank member_id."),
            "Standard table holds only D records.",
            "Medium", "", "SYN-REQ-2203")),
    ])


# ================================================================== cold_3

COLD_3 = "nb_provider_roster"
_NB_LOCATION = "/mftlanding/inbound/provider/northwind/"


def build_sttm_cold_3():
    """Family E: three mapping sheets + File Details, Version History, a code sheet."""
    wb = new_workbook()
    ws = _sheet(wb, "Version History", [
        ["Version History", None, None, None],
        ["Version", "Date", "Author", "Change Description"],
        ["0.1", "2026-08-20", "Synthetic Analyst C", "Draft"],
        ["1.0", "2026-09-02", "Synthetic Analyst C", "Baseline after review"]])
    _merge(ws, 1, 1, 4)
    _sheet(wb, "File Details", [
        ["Vendor", "FileName", "File Description", "Location", "Frequency", "File Extension"],
        ["Northwind Benefits", "NB_PROV_DEMOG_YYYYMMDD.csv", "Provider demographics", _NB_LOCATION, "Weekly", ".csv"],
        ["Northwind Benefits", "NB_PROV_LOC_YYYYMMDD.csv", "Provider service locations", _NB_LOCATION, "Weekly", ".csv"],
        ["Northwind Benefits", "NB_PROV_SPEC_YYYYMMDD.csv", "Provider specialties", _NB_LOCATION, "Weekly", ".csv"]])
    sheets = {
        "PROV_DEMOG": ("nb_provider_demographic", [
            (1, "provider_id", "varchar", 15, "NBP000000101", "PROVIDER_ID", "String", "Y"),
            (2, "provider_npi", "varchar", 10, "1000000001", "PROVIDER_NPI", "String", "N"),
            (3, "last_name", "varchar", 50, "Sample", "LAST_NAME", "String", "Y"),
            (4, "first_name", "varchar", 35, "Pat", "FIRST_NAME", "String", "N"),
            (5, "gender", "char", 1, "U", "GENDER", "String", "N"),
            (6, "effective_date", "date", 10, "2026-01-01", "EFFECTIVE_DATE", "Date", "Y")]),
        "PROV_LOC": ("nb_provider_location", [
            (1, "provider_id", "varchar", 15, "NBP000000101", "PROVIDER_ID", "String", "Y"),
            (2, "location_id", "varchar", 10, "L0001", "LOCATION_ID", "String", "Y"),
            (3, "address_line_1", "varchar", 60, "1 Example Way", "ADDRESS_LINE_1", "String", "Y"),
            (4, "city", "varchar", 40, "Sampleton", "CITY", "String", "Y"),
            (5, "state_code", "char", 2, "ZZ", "STATE_CODE", "String", "Y"),
            (6, "zip_code", "varchar", 10, "00000", "ZIP_CODE", "String", "N")]),
        "PROV_SPEC": ("nb_provider_specialty", [
            (1, "provider_id", "varchar", 15, "NBP000000101", "PROVIDER_ID", "String", "Y"),
            (2, "specialty_code", "varchar", 4, "SP01", "SPECIALTY_CODE", "String", "Y"),
            (3, "primary_flag", "char", 1, "Y", "PRIMARY_FLAG", "String", "N"),
            (4, "effective_date", "date", 10, "2026-01-01", "EFFECTIVE_DATE", "Date", "Y")]),
    }
    titles = ["Source Extract", None, None, None, None, "Raw Zone", None, None, None,
              "Curated Zone", None, None, None, "Rules"]
    header = ["Col #", "Source Field", "Source Type", "Max Len", "Sample",
              "Schema", "Table", "Column", "Type", "Schema", "Table", "Column", "Type",
              "Mandatory (Y/N)"]
    for sheet, (table, fields) in sheets.items():
        body = [[n, name, stype, length, sample, "stg_nb_prov", table, column, "String",
                 "nb_prov", table, column, ctype, mandatory]
                for n, name, stype, length, sample, column, ctype, mandatory in fields]
        for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                                 ("REC_UPDATED_TIME", "Timestamp"), ("FILE_TYPE", "String")):
            body.append([None, "NA", None, None, None, "stg_nb_prov", table, column, datatype,
                         "nb_prov", table, column, datatype, "N"])
        ws = _sheet(wb, sheet, [titles, header, *body])
        for first, last in ((1, 5), (6, 9), (10, 13)):
            _merge(ws, 1, first, last)
    _sheet(wb, "Specialty Codes", [["Code", "Description"], ["SP01", "Family Medicine"],
                                   ["SP02", "Pediatrics"], ["SP03", "Cardiology"],
                                   ["SP04", "Behavioral Health"]])
    return wb


def build_frd_cold_3() -> bytes:
    """F1, the ``Target Schema`` label variant (no catalog)."""
    return docx_bytes([
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", "nb_provider_roster"),
            ("DM-2", "Description", "Weekly provider roster from Northwind Benefits"),
            ("DM-3", "Functional Requirement", "Ingest the three roster files into stage and standard."),
            ("DM-4", "Data Source", "Northwind Benefits"),
            ("DM-5", "Object Name", "NB_PROV_DEMOG_YYYYMMDD.csv\nNB_PROV_LOC_YYYYMMDD.csv\nNB_PROV_SPEC_YYYYMMDD.csv"),
            ("DM-6", "Frequency", "Weekly"),
            ("DM-7", "LOBs", "ALL"),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "Provider roster structure"),
            ("SM-2", "Description", ""),
            ("SM-3", "Functional Requirement", ""),
            ("SM-4", "Object/data Format", "CSV, comma delimited, first row is a header"),
            ("SM-5", "Target Schema", "stg_nb_prov (stage), nb_prov (standard)"),
            ("SM-6", "Target Table Name", "nb_provider_demographic, nb_provider_location, nb_provider_specialty"),
            ("SM-7", "Domain and Subdomain", "Provider / Roster"),
            ("SM-8", "Load Strategy STG", "Truncate and Load"),
            ("SM-9", "Load Strategy STD", "Upsert"),
            ("SM-10", "ADLS Location", ""),
            ("SM-11", "Inbound File Folder Path", _NB_LOCATION),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "provider_id (demographic); provider_id + location_id (location); provider_id + specialty_code (specialty)"),
            ("TM-2", "PII Fields", "provider_npi, last_name, first_name"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-1", "Uniqueness/Duplicate Record check/reject (HARD - In pipeline)", "Reject duplicate primary keys within a file"),
            ("DQ-2", "Incomplete Record Rejection Process (HARD - In pipeline)", "Reject rows missing a mandatory field"),
            ("DQ-3", "Record Recycle Process", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Northwind Benefits"),
            ("VM-2", "Vendor Abbreviation", "NB"),
        ]),
    ])


# ================================================================== cold_4

COLD_4 = "ch_rx_claims"
_RX_LOCATION = "/mftlanding/inbound/pharmacy/contoso_health/"


def build_sttm_cold_4():
    """Family B: FILE_DETAILS + one MAPPING- sheet per table; a <LOB> pattern."""
    wb = new_workbook()
    _sheet(wb, "FILE_DETAILS", [
        ["Vendor", "FileName", "File Description", "Location", "Frequency"],
        ["Contoso Health", "CH_RX_CLM_<LOB>_YYYYMMDD.csv", "Paid pharmacy claims, one file per LOB (MCD, MCR, DSNP)", _RX_LOCATION, "Daily"],
        ["Contoso Health", "CH_RX_REV_YYYYMMDD.csv", "Pharmacy claim reversals, all LOBs in one file", _RX_LOCATION, "Weekly"]])
    _sheet(wb, "VERSION_HISTORY", [["Version", "Date", "Author", "Change Description"],
                                   ["1.0", "2026-09-10", "Synthetic Analyst E", "Initial"]])
    titles = ["Source File Layout", None, None, None, None, None, None,
              "Stage Layer", None, None, None, "Standard Layer", None, None, None]
    target = ["Target Schema", "Target Tbl", "Target Col", "Target Type"]
    header = ["Source Column", "Null Check", "Description", "Sample Value", "Source Type", "PHI",
              "Comment", *target, *target]
    sheets = {
        "MAPPING-RX_CLAIM": ("ch_rx_claim", [
            ("rx_claim_id", "NOT NULL", "Pharmacy claim identifier", "RX0000000001", "varchar(20)", "N", "RX_CLAIM_ID", "String"),
            ("member_id", "NOT NULL", "Member identifier", "M00000000001", "varchar(12)", "Y", "MEMBER_ID", "String"),
            ("fill_date", "NOT NULL", "Date dispensed", "2026-09-01", "date", "N", "FILL_DATE", "Date"),
            ("ndc_code", "NOT NULL", "Product code", "00000000000", "varchar(11)", "N", "NDC_CODE", "String"),
            ("quantity_dispensed", "NULL", "Units dispensed", "30", "decimal(10,3)", "N", "QUANTITY_DISPENSED", "Decimal(10,3)"),
            ("paid_amount", "NULL", "Plan paid amount", "12.50", "decimal(12,2)", "N", "PAID_AMOUNT", "Decimal(12,2)")],
            [("SRC_FILE_NAME", "String", None), ("REC_CREATION_TIME", "Timestamp", None),
             ("LOB", "String", "From the <LOB> token of the file name"), ("FILE_TYPE", "String", None)]),
        "MAPPING-RX_REVERSAL": ("ch_rx_reversal", [
            ("rx_claim_id", "NOT NULL", "Reversed claim identifier", "RX0000000001", "varchar(20)", "N", "RX_CLAIM_ID", "String"),
            ("reversal_date", "NOT NULL", "Date reversed", "2026-09-05", "date", "N", "REVERSAL_DATE", "Date"),
            ("reversal_reason_code", "NULL", "Reason code", "R1", "varchar(4)", "N", "REVERSAL_REASON_CODE", "String"),
            ("reversed_amount", "NULL", "Amount reversed", "12.50", "decimal(12,2)", "N", "REVERSED_AMOUNT", "Decimal(12,2)")],
            [("SRC_FILE_NAME", "String", None), ("REC_CREATION_TIME", "Timestamp", None),
             ("FILE_TYPE", "String", None)]),
    }
    for sheet, (table, fields, audits) in sheets.items():
        body = [[name, null, desc, sample, stype, phi, None,
                 "stg_ch_rx", table, column, "String", "ch_rx", table, column, std_type]
                for name, null, desc, sample, stype, phi, column, std_type in fields]
        for column, datatype, comment in audits:
            body.append(["NA", None, None, None, None, None, comment,
                         "stg_ch_rx", table, column, datatype, "ch_rx", table, column, datatype])
        ws = _sheet(wb, sheet, [titles, header, *body])
        for first, last in ((1, 7), (8, 11), (12, 15)):
            _merge(ws, 1, first, last)
    return wb


def build_frd_cold_4() -> bytes:
    """F1; the Object Name cell holds stanzas (a ``<label>:`` line, then the file)."""
    return docx_bytes([
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", "ch_rx_claims"),
            ("DM-2", "Description", "Pharmacy claims and reversals from the Contoso Health PBM"),
            ("DM-3", "Functional Requirement", "Ingest claim files per LOB and the weekly reversal file."),
            ("DM-4", "Data Source", "Contoso Health PBM"),
            ("DM-5", "Object Name", "Pharmacy claims:\nCH_RX_CLM_<LOB>_YYYYMMDD.csv\nReversals:\nCH_RX_REV_YYYYMMDD.csv"),
            ("DM-6", "Frequency", "Claims daily; reversals weekly"),
            ("DM-7", "LOBs", "MCD, MCR, DSNP"),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "Pharmacy structure"),
            ("SM-2", "Description", ""),
            ("SM-3", "Functional Requirement", ""),
            ("SM-4", "Object/data Format", "CSV"),
            ("SM-5", "Target Catalog and Schema", "PR_DLK.stg_ch_rx; PR_STD.ch_rx"),
            ("SM-6", "Target Table Name", "ch_rx_claim, ch_rx_reversal"),
            ("SM-7", "Domain and Subdomain", "Pharmacy / Claims"),
            ("SM-8", "Load Strategy STG", "Append"),
            ("SM-9", "Load Strategy STD", "Upsert"),
            ("SM-10", "ADLS Location", "inbound/contoso_health/pharmacy/"),
            ("SM-11", "Inbound File Folder Path", _RX_LOCATION),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "rx_claim_id"),
            ("TM-2", "PII Fields", "member_id"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-1", "Uniqueness/Duplicate Record check/reject (HARD - In pipeline)", "Reject duplicate rx_claim_id within a claim file"),
            ("DQ-2", "Incomplete Record Rejection Process (HARD - In pipeline)", "Reject records missing member_id"),
            ("DQ-3", "Record Recycle Process", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Contoso Health PBM"),
            ("VM-2", "Vendor Abbreviation", "CHRX"),
        ]),
    ])


# ================================================================== cold_5

COLD_5 = "fc_provdir"


def build_sttm_cold_5():
    """One sheet, no band title row, ONE target band (``… in DL``), no audit rows."""
    wb = new_workbook()
    header = ["No.", "Field Name", "Data Type", "Length", "Description", "PII",
              "Target Schema Name in DL", "Target Table Name in DL", "Target Column Name in DL",
              "Target Data Type in DL"]
    fields = [(1, "provider_id", "String", 15, "Directory provider identifier", "PROVIDER_ID", "String"),
              (2, "provider_name", "String", 80, "Display name", "PROVIDER_NAME", "String"),
              (3, "specialty_desc", "String", 60, "Specialty description", "SPECIALTY_DESC", "String"),
              (4, "phone_number", "String", 15, "Office phone", "PHONE_NUMBER", "String"),
              (5, "accepting_new_patients", "String", 1, "Y/N", "ACCEPTING_NEW_PATIENTS", "String"),
              (6, "last_verified_date", "Date", 10, "YYYY-MM-DD", "LAST_VERIFIED_DATE", "Date")]
    body = [[n, name, dtype, length, desc, "No", "fc_provdir", "fc_provider_directory", column, ttype]
            for n, name, dtype, length, desc, column, ttype in fields]
    _sheet(wb, "Provider Directory", [["File Name", "fc_provdir_YYYYMMDD.csv"],
                                      ["File Format", "CSV"], [], header, *body])
    return wb


def build_frd_cold_5() -> bytes:
    """Short free-form: a Title paragraph and three Normal paragraphs, NO table."""
    return docx_bytes([
        _p("Fabrikam Care – Provider Directory Feed", "Title"),
        _p("Fabrikam Care sends a provider directory extract so that member services can look up in-network providers."),
        _p("The file lands at /mftlanding/inbound/provider/fabrikam_care/fc_provdir_YYYYMMDD.csv."),
        _p("The data is to be loaded into the table fc_provider_directory."),
    ])


# ================================================================== cold_6

COLD_6 = "ch_member_enroll"


def build_sttm_cold_6():
    """Family C: vendor Layout + an STTM sheet with a document TITLE row (not a
    band row), ``Landing …`` / ``Curated … Nm`` headers, rules AFTER both bands."""
    wb = new_workbook()
    _sheet(wb, "Version Control", [["Version", "Date", "Description", "Updated By"],
                                   ["1.0", "2026-09-12", "Initial mapping", "Synthetic Analyst F"],
                                   ["1.1", "2026-09-26", "Added lob_code", "Synthetic Analyst F"]])
    _sheet(wb, "Layout", [
        ["FileName", "CH_MBR_ENROLL_YYYYMMDD.tsv"],
        [],
        ["Field #", "Field Name", "Req'd?", "Type", "Max Length", "Comments"],
        [1, "member_id", "Y", "AN", 12, None],
        [2, "subscriber_id", "Y", "AN", 12, None],
        [3, "relationship_code", "Y", "AN", 2, "18 = self"],
        [4, "coverage_start", "Y", "DT", 8, "CCYYMMDD"],
        [5, "coverage_end", "N", "DT", 8, "CCYYMMDD"],
        [6, "plan_id", "Y", "AN", 8, None],
        [7, "lob_code", "Y", "AN", 2, "see LOB Crosswalk"]])
    header = ["Field #", "Field Name", "Type", "Data Definition",
              "Landing Catalog", "Landing Schema", "Landing Table", "Landing Col", "Landing Data Type",
              "Curated Catalog", "Curated Schema Nm", "Curated Table Nm", "Curated Column Nm",
              "Curated Data Type", "PII", "Primary Key", "Load Rules"]
    stage = ("PR_DLK", "ch_mbr_land", "ch_member_enrollment")
    standard = ("PR_STD", "ch_mbr", "ch_member_enrollment")
    fields = [(1, "member_id", "AN", "Member identifier", "MEMBER_ID", "String", "Y", "Y", "Direct"),
              (2, "subscriber_id", "AN", "Subscriber identifier", "SUBSCRIBER_ID", "String", "Y", "N", "Direct"),
              (3, "relationship_code", "AN", "Relationship to subscriber", "RELATIONSHIP_CODE", "String", "N", "N", "Direct"),
              (4, "coverage_start", "DT", "Span start", "COVERAGE_START", "Date", "N", "Y", "Cast to DATE using yyyyMMdd"),
              (5, "coverage_end", "DT", "Span end", "COVERAGE_END", "Date", "N", "N", "Cast to DATE using yyyyMMdd"),
              (6, "plan_id", "AN", "Benefit plan", "PLAN_ID", "String", "N", "N", "Direct"),
              (7, "lob_code", "AN", "Line of business code", "LOB_CODE", "String", "N", "N", "Direct")]
    body = [[n, name, typ, definition, *stage, column, "String", *standard, column, std_type,
             pii, pk, rule]
            for n, name, typ, definition, column, std_type, pii, pk, rule in fields]
    for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp"),
                             ("REC_UPDATED_TIME", "Timestamp"), ("LOB", "String"),
                             ("FILE_TYPE", "String")):
        body.append([None, "NA", None, None, *stage, column, datatype, *standard, column, datatype,
                     "N", "N", "Populated by framework"])
    ws = _sheet(wb, "STTM", [
        ["Contoso Health Member Enrollment – Source to Target Mapping"],
        ["Delimiter", "Tab"],
        [],
        header, *body])
    _merge(ws, 1, 1, 17)
    _sheet(wb, "LOB Crosswalk", [["Code", "LOB"], ["01", "MCD"], ["02", "CHIP"], ["03", "MCR"]])
    return wb


def build_frd_cold_6() -> bytes:
    """F2 with Heading 1 sections."""
    return docx_bytes([
        _p("1 Overview", "Heading1"),
        _p("Contoso Health sends a daily member enrollment file. This document states the requirements for landing and curating it."),
        _tbl([["Domain", "Membership"], ["Sub Domain", "Enrollment"]]),
        _p("2 Solution Requirements", "Heading1"),
        _sr(1, _sr_rows(
            "Ingest member enrollment file",
            "Enrollment spans must be available the next morning.",
            "Ingest the tab-delimited daily file CH_MBR_ENROLL_YYYYMMDD.tsv from mftlanding/inbound/membership/contoso_health/ into the landing table ch_mbr_land.ch_member_enrollment.",
            ("Structural Metadata", "Load Strategy STG: Append"),
            "Every delivered file is landed once.",
            "High", "Vendor layout v2", "SYN-REQ-6101")),
        _sr(2, _sr_rows(
            "Curate member enrollment",
            "One current row per enrollment span.",
            "Publish enrollment spans to ch_mbr.ch_member_enrollment.",
            ("Technical Metadata", "Primary Key: member_id, coverage_start"),
            "No duplicate member_id + coverage_start in standard.",
            "High", "", "SYN-REQ-6102")),
        _sr(3, _sr_rows(
            "Enrollment data quality",
            "Bad spans must not reach analysts.",
            "Reject records whose coverage_end is earlier than coverage_start.",
            ("Data Quality", "Reject; no recycle."),
            "Rejected rows are logged with the reason.",
            "Medium", "", "SYN-REQ-6103")),
    ])


# ================================================================== registry

PAIRS: dict[str, str] = {"cold_1": COLD_1, "cold_2": COLD_2, "cold_3": COLD_3,
                         "cold_4": COLD_4, "cold_5": COLD_5, "cold_6": COLD_6}
SHAPE: dict[str, str] = {
    "cold_1": "family A inline meta; Standard band LEFT of Stage; F1 FRD; delimiter disagrees",
    "cold_2": "fixed width H/D/T banners; titles Target 1 / Target 2; LOAD_TS / BATCH_ID audits; F2 FRD",
    "cold_3": "family E: 3 mapping sheets + File Details; Raw Zone / Curated Zone; Schema/Table/Column/Type; F1 FRD, no catalog",
    "cold_4": "family B: FILE_DETAILS + 2 MAPPING- sheets; <LOB> x 3 + reversal file; Target Tbl / Col / Type",
    "cold_5": "one sheet, no title row, one 'in DL' band, no audits; three-paragraph FRD (no tables)",
    "cold_6": "family C: Layout + STTM with a document title row; Landing / Curated headers; tab delimited; F2 FRD",
}
_STTM = {"cold_1": build_sttm_cold_1, "cold_2": build_sttm_cold_2, "cold_3": build_sttm_cold_3,
         "cold_4": build_sttm_cold_4, "cold_5": build_sttm_cold_5, "cold_6": build_sttm_cold_6}
_FRD = {"cold_1": build_frd_cold_1, "cold_2": build_frd_cold_2, "cold_3": build_frd_cold_3,
        "cold_4": build_frd_cold_4, "cold_5": build_frd_cold_5, "cold_6": build_frd_cold_6}


def sttm_path(pair: str) -> str:
    return f"cold/{pair}/STTM_{PAIRS[pair]}.xlsx"


def frd_path(pair: str) -> str:
    return f"cold/{pair}/FRD_{PAIRS[pair]}.docx"


XLSX_BUILDERS = {sttm_path(p): _STTM[p] for p in PAIRS}
BYTES_BUILDERS = {frd_path(p): _FRD[p] for p in PAIRS}
