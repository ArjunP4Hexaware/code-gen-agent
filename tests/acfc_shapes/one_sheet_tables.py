# ruff: noqa: E501  -- fixture data tables kept on one line per row
"""ONE mapping sheet, SEVERAL tables (post156, the pair_09 shape) — SYNTHETIC.

The source is a set of DATABASE TABLES: one FRD metadata block names every
target table (and the source tables in Object Name), and the STTM maps all of
them on ONE sheet — its stage TableName column holds a different table per
block of rows. Read as one table, the FRD's other tables met no STTM table
(ContractMismatchError: "N tables only in FRD"). Vocabulary is the synthetic
"Northwind Benefits" universe.
"""

from __future__ import annotations

from .cold_pairs import _f1, _merge, _sheet
from .common import docx_bytes, new_workbook

PROJECT = "Northwind Provider Directory"
CATALOG = "NB_PROVIDER_DB"
SOURCE_SCHEMA = "dbo"
STAGE_SCHEMA, STANDARD_SCHEMA = "stg_nb_prov", "nb_prov"
# source table -> (stage table, standard table, [(column, source type, stage type, standard type)])
TABLES = {
    "PROVIDER": ("nb_provider", "nb_provider", [
        ("PROVIDER_ID", "varchar", "String", "String"),
        ("PROVIDER_NAME", "varchar", "String", "String"),
        ("EFFECTIVE_DATE", "date", "String", "Date")]),
    "PROVIDER_ADDRESS": ("nb_provider_address", "nb_provider_address", [
        ("PROVIDER_ID", "varchar", "String", "String"),
        ("ADDRESS_LINE", "varchar", "String", "String"),
        ("ZIP_CODE", "varchar", "String", "String")]),
    "PROVIDER_SPECIALTY": ("nb_provider_specialty", "nb_provider_specialty", [
        ("PROVIDER_ID", "varchar", "String", "String"),
        ("SPECIALTY_CODE", "varchar", "String", "String")]),
}


def build_sttm(*, blank_repeats: bool = False):
    """``blank_repeats``: each table's name only on its block's FIRST row (the
    rest blank, as a merged cell reads) - the rows below belong to it."""
    wb = new_workbook()
    _sheet(wb, "Version History", [["Version", "Date", "Author", "Change Description"],
                                   ["1.0", "2026-10-29", "Synthetic Analyst T", "Baseline"]])
    titles = ["Source Table Layout", None, None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None]
    header = ["Table Catalog", "Table Schema", "Table Name", "Column Name", "Data Type",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType"]
    body = []
    for source, (stage, standard, columns) in TABLES.items():
        for n, (column, stype, stage_type, std_type) in enumerate(columns):
            stated = n == 0 or not blank_repeats
            body.append([CATALOG, SOURCE_SCHEMA, source, column, stype,
                         STAGE_SCHEMA, stage if stated else None, column, stage_type,
                         STANDARD_SCHEMA, standard if stated else None, column, std_type])
        for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")):
            body.append([None, None, None, "NA", None, STAGE_SCHEMA, stage if not blank_repeats else None,
                         column, datatype, STANDARD_SCHEMA, standard if not blank_repeats else None,
                         column, datatype])
    ws = _sheet(wb, "Mapping", [["Project Name", PROJECT], [], titles, header, *body])
    for first, last in ((1, 5), (6, 9), (10, 13)):
        _merge(ws, 3, first, last)
    return wb


def build_frd() -> bytes:
    """One block: the source tables in Object Name, every target table in Target
    Table Name, the format a database table."""
    stages = [stage for stage, _std, _cols in TABLES.values()]
    return docx_bytes([
        _f1("DM", "Descriptive Metadata", [
            ("DM-1", "Name", PROJECT),
            ("DM-2", "Description", "Monthly provider directory tables from Northwind Benefits"),
            ("DM-3", "Functional Requirement", "Ingest the provider tables into stage and standard."),
            ("DM-4", "Data Source", "Northwind Benefits"),
            ("DM-5", "Object Name", "\n".join(TABLES)),
            ("DM-6", "Frequency", "Monthly"),
            ("DM-7", "LOBs", "ALL"),
        ]),
        _f1("SM", "Structural Metadata", [
            ("SM-1", "Name", "Provider directory structure"),
            ("SM-2", "Description", ""),
            ("SM-3", "Functional Requirement", ""),
            ("SM-4", "Object/data Format", "Database Table"),
            ("SM-5", "Target Schema", f"{STAGE_SCHEMA} (stage), {STANDARD_SCHEMA} (standard)"),
            ("SM-6", "Target Table Name", "\n".join(stages)),
            ("SM-7", "Domain and Subdomain", "Provider / Directory"),
            ("SM-8", "Load Strategy STG", "Truncate and Load"),
            ("SM-9", "Load Strategy STD", "Upsert"),
            ("SM-10", "ADLS Location", ""),
            ("SM-11", "Inbound File Folder Path", ""),
        ]),
        _f1("TM", "Technical Metadata", [
            ("TM-1", "Primary Key", "PROVIDER_ID"),
            ("TM-2", "PII Fields", "none"),
        ]),
        _f1("DQ", "Data Quality", [
            ("DQ-3", "Record Recycle Process", "Not applicable"),
        ]),
        _f1("VM", "Vendor Metadata", [
            ("VM-1", "Vendor Name", "Northwind Benefits"),
            ("VM-2", "Vendor Abbreviation", "NB"),
        ]),
    ])
