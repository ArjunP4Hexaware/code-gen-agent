# ruff: noqa: E501  -- fixture data tables kept on one line per row
"""Family E, one mapping sheet PER SOURCE FILE (2026-10-13) — SYNTHETIC.

The D1 pairing check (pair_11) failed extract-sttm with "duplicate feed_id(s)
in STTM contract": a family-E workbook maps each source file on its own sheet,
every sheet carries the same project name and lands in the same stage table,
and the FRD's one metadata block lists the files. Here: four sibling files
plus one "additional" file, five mapping sheets, a File Details sheet listing
all five, and the FRD that names the project, the five files and the one
table. Vocabulary is the synthetic "Northwind Benefits" universe.
"""

from __future__ import annotations

from .cold_pairs import _f1, _merge, _sheet
from .common import docx_bytes, new_workbook

PROJECT = "Northwind Care Management Data"
TABLE = "nb_care_mgmt"
LOCATION = "/mftlanding/inbound/care_mgmt/northwind/"
# sheet -> its file (four siblings + one additional)
FILES = {
    "CM_NORTH": "NB_CM_NORTH_YYYYMMDD.txt",
    "CM_SOUTH": "NB_CM_SOUTH_YYYYMMDD.txt",
    "CM_EAST": "NB_CM_EAST_YYYYMMDD.txt",
    "CM_WEST": "NB_CM_WEST_YYYYMMDD.txt",
    "CM_ADDITIONAL": "NB_CM_ADDITIONAL_YYYYMMDD.txt",
}
FIELDS = [("member_id", "varchar", 15, "MEMBER_ID", "String", "Y"),
          ("program_code", "varchar", 6, "PROGRAM_CODE", "String", "Y"),
          ("enroll_date", "date", 10, "ENROLL_DATE", "Date", "N"),
          ("care_manager", "varchar", 40, "CARE_MANAGER", "String", "N")]


def build_sttm(sheets: dict[str, str] | None = None, *, own_file_rows: bool = True):
    """``sheets``: sheet -> file (default the five). ``own_file_rows``: each
    mapping sheet states its file in a ``File Name`` meta row (else only the
    File Details sheet names the files)."""
    sheets = FILES if sheets is None else sheets
    wb = new_workbook()
    _sheet(wb, "Version History", [["Version", "Date", "Author", "Change Description"],
                                   ["1.0", "2026-10-13", "Synthetic Analyst E", "Baseline"]])
    _sheet(wb, "File Details", [
        ["Vendor", "FileName", "File Description", "Location", "Frequency", "File Extension"],
        *[["Northwind Benefits", name, f"Care management extract {sheet}", LOCATION, "Monthly", ".txt"]
          for sheet, name in sheets.items()]])
    titles = ["Source File Layout", None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    for sheet, file_name in sheets.items():
        meta = [["Project Name", PROJECT]]
        if own_file_rows:
            meta.append(["File Name", file_name])
        meta.append([])
        body = [[name, f"{name.replace('_', ' ')} of the member", stype, mandatory,
                 "stg_nb_cm", TABLE, column, "String", "nb_cm", TABLE, column, ctype, None]
                for name, stype, _length, column, ctype, mandatory in FIELDS]
        for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")):
            body.append(["NA", None, None, None, "stg_nb_cm", TABLE, column, datatype,
                         "nb_cm", TABLE, column, datatype, None])
        ws = _sheet(wb, sheet, [*meta, titles, header, *body])
        title_row = len(meta) + 1
        for first, last in ((1, 4), (5, 8), (9, 12)):
            _merge(ws, title_row, first, last)
    return wb


def build_frd(files: list[str] | None = None,
              domain_cell: str = "Member / Care Management", *,
              name: str = PROJECT, table: str = TABLE) -> bytes:
    """F1: the project as the feed name, the files in Object Name, ONE table.
    ``domain_cell`` is the "Domain and Subdomain" row (pair_12 CAQH states
    both labels there on two lines)."""
    files = list(FILES.values()) if files is None else files
    return docx_bytes([
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", name),
            ("DM-2", "Description", "Monthly care management extracts from Northwind Benefits"),
            ("DM-3", "Functional Requirement", "Ingest the care management files into stage and standard."),
            ("DM-4", "Data Source", "Northwind Benefits"),
            ("DM-5", "Object Name", "\n".join(files)),
            ("DM-6", "Frequency", "Monthly"),
            ("DM-7", "LOBs", "ALL"),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "Care management structure"),
            ("SM-2", "Description", ""),
            ("SM-3", "Functional Requirement", ""),
            ("SM-4", "Object/data Format", "Pipe delimited text, first row is a header"),
            ("SM-5", "Target Schema", "stg_nb_cm (stage), nb_cm (standard)"),
            ("SM-6", "Target Table Name", table),
            ("SM-7", "Domain and Subdomain", domain_cell),
            ("SM-8", "Load Strategy STG", "Truncate and Load"),
            ("SM-9", "Load Strategy STD", "Upsert"),
            ("SM-10", "ADLS Location", ""),
            ("SM-11", "Inbound File Folder Path", LOCATION),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "member_id, program_code"),
            ("TM-2", "PII Fields", "member_id"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-1", "Uniqueness/Duplicate Record check/reject (HARD - In pipeline)", "Reject duplicate primary keys within a file"),
            ("DQ-3", "Record Recycle Process", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Northwind Benefits"),
            ("VM-2", "Vendor Abbreviation", "NB"),
        ]),
    ])



# ---------------------------------------------------------------------------
# The Pyx shape (2026-10-13, D1 pair_11 identity diff — SYNTHETIC): one mapping
# sheet per REPORT, each landing in its own stage table; sheet titles
# abbreviate the report ("Engmnt", a title cut at 31 characters); a
# "Table_Details" sheet lists the tables under Stage / Standard headers; the
# STTM states "csv" while the FRD's format cell says "Text files"; the FRD
# names no feed and lists the five report files.
REPORT_SCHEMAS = ("stg_nb_cm", "nb_cm")
# sheet -> (stage table, file as the FRD lists it, as File Details lists it)
REPORTS = {
    "Weekly DNC Report": ("nb_cm_dnc_report", "Northwind_CM_DNC_Report_MMDDYYYY.csv",
                          "Northwind_CM_DNC_Report_*.csv"),
    "Monthly Outreach Report": ("nb_cm_outreach_report",
                                "Northwind_CM_Outreach_Report_MMYYYY.csv",
                                "Northwind_CM_Outreach_Report_*.csv"),
    "Monthly Engmnt Billing": ("nb_cm_engagement_billing",
                               "Northwind_CM_Engagement_Billing_Report_MMYYYY.csv",
                               "Northwind_CM_Engagement_Billing_Report_*.csv"),
    "Monthly Screening Repor": ("nb_cm_screening_report",
                                "Northwind_CM_Screening_Report_MMYYYY.csv",
                                "Northwind_CM_Screening_Report_*.csv"),
    "Weekly Activity Report": ("nb_cm_weekly_activity",
                               "Northwind_CM_Weekly_Activity_Report_MMDDYYYY.csv",
                               "Northwind_CM_Weekly_Activity_Report_*.csv"),
}
TABLE_DETAILS = "Table_Details"


def build_sttm_reports(*, table_details: bool = True, own_file_rows: bool = False,
                       blank_stage_tables: tuple[str, ...] = (),
                       reports: dict[str, tuple[str, str, str]] | None = None):
    """The Pyx-shaped workbook. ``blank_stage_tables``: sheets whose stage
    TableName cells are left blank (the owner's question)."""
    reports = REPORTS if reports is None else reports
    stage_schema, std_schema = REPORT_SCHEMAS
    wb = new_workbook()
    _sheet(wb, "Version History", [["Version", "Date", "Author", "Change Description"],
                                   ["1.0", "2026-10-13", "Synthetic Analyst E", "Baseline"]])
    _sheet(wb, "File Details", [
        ["Vendor", "FileName", "File Description", "Location", "Frequency", "File Extension"],
        *[["Northwind Benefits", details, f"{sheet} extract", LOCATION,
           "Weekly" if sheet.startswith("Weekly") else "Monthly", "csv"]
          for sheet, (_table, _frd, details) in reports.items()]])
    if table_details:
        # Stage / Standard words in a short header row over table rows: the
        # band-row reading takes it for a mapping sheet with every role open.
        _sheet(wb, TABLE_DETAILS, [
            ["Report", "Stage Table", "Standard Table", "Load Type"],
            *[[sheet, f"{stage_schema}.{table}", f"{std_schema}.{table}", "Append"]
              for sheet, (table, _frd, _details) in reports.items()]])
    titles = ["Source File Layout", None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    for sheet, (table, _frd_name, details) in reports.items():
        meta = [["Project Name", "Northwind Care Management Reports"], ["File Format", "csv"]]
        if own_file_rows:
            meta.append(["File Name", details])
        meta.append([])
        stage_table = None if sheet in blank_stage_tables else table
        body = [[name, f"{name.replace('_', ' ')} of the member", stype, mandatory,
                 stage_schema, stage_table, column, "String", std_schema, table, column, ctype,
                 None]
                for name, stype, _length, column, ctype, mandatory in FIELDS]
        for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")):
            body.append(["NA", None, None, None, stage_schema, stage_table, column, datatype,
                         std_schema, table, column, datatype, None])
        ws = _sheet(wb, sheet, [*meta, titles, header, *body])
        title_row = len(meta) + 1
        for first, last in ((1, 4), (5, 8), (9, 12)):
            _merge(ws, title_row, first, last)
    return wb


def build_frd_reports(files: list[str] | None = None, *, file_format: str = "Text files"
                      ) -> bytes:
    """F1: no feed name (the Object Name cell lists the five report files),
    the format cell "Text files", one stage / standard schema."""
    files = [frd for _t, frd, _d in REPORTS.values()] if files is None else files
    return docx_bytes([
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", ""),
            ("DM-2", "Description", "Weekly and monthly care management reports from Northwind"),
            ("DM-3", "Functional Requirement", "Ingest the report files into stage and standard."),
            ("DM-4", "Data Source", "Northwind Benefits"),
            ("DM-5", "Object Name", "\n".join(files)),
            ("DM-6", "Frequency", "Weekly Wednesday"),
            ("DM-7", "LOBs", "ALL"),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "Care management report structure"),
            ("SM-2", "Description", ""),
            ("SM-3", "Functional Requirement", ""),
            ("SM-4", "Object/data Format", file_format),
            ("SM-5", "Target Schema", "stg_nb_cm (stage), nb_cm (standard)"),
            ("SM-6", "Target Table Name", "\n".join(files)),
            ("SM-7", "Domain and Subdomain", "Member / Care Management"),
            ("SM-8", "Load Strategy STG", "Truncate and Load"),
            ("SM-9", "Load Strategy STD", "Upsert"),
            ("SM-10", "ADLS Location", ""),
            ("SM-11", "Inbound File Folder Path", LOCATION),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "member_id, program_code"),
            ("TM-2", "PII Fields", "member_id"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-3", "Record Recycle Process", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Northwind Benefits"),
            ("VM-2", "Vendor Abbreviation", "NB"),
        ]),
    ])
