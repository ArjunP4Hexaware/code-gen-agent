# ruff: noqa: E501  -- fixture data tables kept on one line per row
"""Band-detection shapes (Chunk A, 2026-10-09) — SYNTHETIC workbooks built in
code, one mapping sheet each, for ``tests/test_band_detection.py``.

Every shape is a variation the reader must survive on a document it has never
seen: bands found by their label group (Schema / TableName / ColumnName /
DataType …) wherever they sit, their LAYER only from evidence (a band title,
a layer word in the header text, a Catalog value, a Schema prefix), never from
column order. Vocabulary is the synthetic "Northwind Benefits" universe of
pair 4 (``nb_*``); nothing here is client-derived.
"""

from __future__ import annotations

from acfc_shapes.common import new_workbook, write_rows

SHEET = "BAND_MAPPING"

FIELDS = ["member_id", "plan_code", "risk_score", "effective_date"]
# Audit rows: "NA" on the source side, the audit column on the target side.
AUDIT = [("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")]
SOURCE_HEADERS = ["Field Name", "Description", "Data Type", "Mandatory Field"]
TARGET_HEADERS = ["Schema", "TableName", "ColumnName", "DataType"]


def _source_cells(name: str) -> list:
    return [name, f"{name.replace('_', ' ')} of the member", "String", "No"]


def _target_cells(schema: str, table: str, name: str, datatype: str = "String") -> list:
    return [schema, table, name, datatype]


def _merge(ws, row: int, first: int, last: int) -> None:
    if last > first:
        ws.merge_cells(start_row=row, start_column=first, end_row=row, end_column=last)


def sd_shaped(*, narrow_titles: bool = False):
    """The SD-feed shape: source A–H, stage I–L (Schema at I, TableName at J),
    a blank M, standard N–Q (Schema at N, TableName at O), Recycle Flag at R,
    NO Catalog. ``narrow_titles``: the "Stage Layer" / "Standard Layer" title
    merges cover only I–J / N–O (the schema + table columns) — the title row
    then disagrees with the header groups and the groups decide the spans."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    source = ["Client Data Table Column Name", "Description", "Comment", "Example Values",
              "Data Type", "NULL Check", "PHI/PII Field", "Mandatory"]
    header = [*source, *TARGET_HEADERS, None, *TARGET_HEADERS, "Recycle Flag"]
    titles = [None] * len(header)
    titles[0], titles[8], titles[13] = "Source File Layout", "Stage Layer", "Standard Layer"
    rows = [titles, header]
    for i, name in enumerate(FIELDS):
        rows.append([name, f"{name} text", "string", str(i + 1), "String",
                     "Not NULL" if i == 0 else "NULL", "No", "Yes" if i == 0 else "No",
                     *_target_cells("stg_nb", "nb_member_risk", name), None,
                     *_target_cells("nb", "nb_member_risk", name,
                                    "Decimal(10,2)" if name == "risk_score" else "String"),
                     "Recycle Flag (Enabled for 7 days)" if i == 0 else None])
    write_rows(ws, rows)
    _merge(ws, 1, 1, 8)
    if narrow_titles:
        _merge(ws, 1, 9, 10)
        _merge(ws, 1, 14, 15)
    else:
        _merge(ws, 1, 9, 12)
        _merge(ws, 1, 14, 17)
    return wb


def one_band(*, title: str | None = None, schema: str = "nb", header_words: bool = False,
             catalog: str | None = None):
    """A source band + ONE target-shaped band. ``title`` over the target band
    (None = no title row at all); ``schema`` the Schema values ("stg_nb" =
    schema-prefix evidence); ``header_words`` = "Stage …" header texts;
    ``catalog`` = a Catalog column with that value."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    target = (["Stage Schema", "Stage Table Name", "Stage Column Name", "Stage DataType"]
              if header_words else list(TARGET_HEADERS))
    if catalog is not None:
        target = ["Catalog", *target]
    header = [*SOURCE_HEADERS, *target]
    rows = []
    if title is not None:
        rows.append(["Source Data", None, None, None, title, *([None] * (len(target) - 1))])
    rows.append(header)
    for name in FIELDS:
        rows.append([*_source_cells(name), *([catalog] if catalog is not None else []),
                     *_target_cells(schema, "nb_member_risk", name)])
    write_rows(ws, rows)
    if title is not None:
        _merge(ws, 1, 1, 4)
        _merge(ws, 1, 5, 4 + len(target))
    return wb


def three_lookalike(*, titles: bool = False):
    """Three bands with the SAME label group (Schema | TableName | ColumnName |
    DataType) side by side and nothing else: a database-table source, the
    stage band, the standard band. Without titles nothing names a layer."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    rows = []
    if titles:
        rows.append(["Source", None, None, None, "Stage Layer", None, None, None,
                     "Standard Layer", None, None, None])
    rows.append(TARGET_HEADERS * 3)
    for name in FIELDS:
        rows.append([*_target_cells("nb_src", "member_risk_extract", name),
                     *_target_cells("nb_land", "nb_member_risk", name),
                     *_target_cells("nb", "nb_member_risk", name)])
    for column, datatype in AUDIT:
        rows.append(["NA", "NA", "NA", "NA",
                     *_target_cells("nb_land", "nb_member_risk", column, datatype),
                     *_target_cells("nb", "nb_member_risk", column, datatype)])
    write_rows(ws, rows)
    if titles:
        for first in (1, 5, 9):
            _merge(ws, 1, first, first + 3)
    return wb


def missing_table():
    """Titled stage + standard bands; the STAGE band has no TableName column."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    stage = ["Schema", "ColumnName", "DataType"]
    rows = [["Source Data", None, None, None, "Stage Layer", None, None,
             "Standard Layer", None, None, None],
            [*SOURCE_HEADERS, *stage, *TARGET_HEADERS]]
    for name in FIELDS:
        rows.append([*_source_cells(name), "stg_nb", name, "String",
                     *_target_cells("nb", "nb_member_risk", name)])
    write_rows(ws, rows)
    _merge(ws, 1, 1, 4)
    _merge(ws, 1, 5, 7)
    _merge(ws, 1, 8, 11)
    return wb


def reversed_offset():
    """Any order, any offset: meta rows 1–5, the title row at 6, headers at 7,
    the first band at column D, and the STANDARD band left of the stage band."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    meta = [["File Name", "nb_member_risk_YYYYMMDD.csv"], ["Frequency", "Daily"],
            ["File Format", "Delimited"], ["File Delimiter", ","], ["Load Strategy", "Append"]]
    pad = [None, None, None]
    titles = [*pad, "Source Data", None, None, None, "Standard Layer Table", None, None, None,
              "Staging Layer Table", None, None, None]
    header = [*pad, *SOURCE_HEADERS, *TARGET_HEADERS, *TARGET_HEADERS]
    rows = [*meta, titles, header]
    for name in FIELDS:
        rows.append([*pad, *_source_cells(name),
                     *_target_cells("nb", "nb_member_risk", name),
                     *_target_cells("stg_nb", "nb_member_risk", name)])
    write_rows(ws, rows)
    _merge(ws, 6, 4, 7)
    _merge(ws, 6, 8, 11)
    _merge(ws, 6, 12, 15)
    return wb


def two_claim_stage():
    """No titles, two target bands whose Schema values BOTH carry stg_."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    rows = [[*SOURCE_HEADERS, *TARGET_HEADERS, *TARGET_HEADERS]]
    for name in FIELDS:
        rows.append([*_source_cells(name), *_target_cells("stg_nb", "nb_member_risk", name),
                     *_target_cells("stg_nb2", "nb_member_risk", name)])
    write_rows(ws, rows)
    return wb


def catalog_values():
    """No titles, two target bands told apart only by their Catalog values
    (the logical catalogs PR_DLK / PR_STD)."""
    wb = new_workbook()
    ws = wb.create_sheet(SHEET)
    target = ["Catalog", *TARGET_HEADERS]
    rows = [[*SOURCE_HEADERS, *target, *target]]
    for name in FIELDS:
        rows.append([*_source_cells(name),
                     "PR_DLK", *_target_cells("nb_land", "nb_member_risk", name),
                     "PR_STD", *_target_cells("nb", "nb_member_risk", name)])
    write_rows(ws, rows)
    return wb


FEED = "nb_member_risk"


def frd_contract(stage_schema: str = "stg_nb", standard_schema: str = "nb") -> dict:
    """The FRD contract every band shape pairs with (one delimited feed, one
    table per layer) — the same synthetic universe, hand-built. The schemas
    must agree with the STTM's bands (the resolver cross-checks them)."""
    return {
        "contract_name": f"{FEED} feed-level mapping contract (synthetic)",
        "generated_from_frd": f"FRD_{FEED}.docx",
        "generated_date": "2026-10-09T00:00:00+00:00",
        "generator": "hand-built synthetic fixture (tests/acfc_shapes/bands.py)",
        "status": "PASS",
        "project": {"project_id": "SYN-PRJ-12", "project_name": "Northwind Benefits Member Risk",
                    "business_context_summary": "Ingest the daily member risk extract."},
        "in_scope": ["One comma-delimited file per day."],
        "out_of_scope": ["Any transformation beyond what the STTM maps."],
        "assumptions_constraints_dependencies": [],
        "feeds": [{
            "feed_name": FEED,
            "source_system": "Northwind Benefits",
            "file_name_patterns": [f"{FEED}_YYYYMMDD.csv"],
            "file_format": "csv",
            "delimiter": ",",
            "record_segments": [],
            "frequency": "Daily",
            "load_windows_sla": [],
            "lobs": ["ALL"],
            "domain": "Member",
            "sub_domain": "Risk",
            "landing_location": "inbound/northwind/member_risk",
            "stage_target": {"catalog": None, "schema": stage_schema, "tables": [FEED],
                             "load_strategy": "Append"},
            "standard_target": {"catalog": None, "schema": standard_schema, "tables": [FEED],
                                "load_strategy": "Append"},
            "validation_rules": [],
            "recycle_rule": None,
            "history_backfill": None,
            "archive_retention": None,
            "phi_pii_notes": "No PHI in this extract",
            "sttm_reference": f"STTM_{FEED}.xlsx",
            "requirement_ids": ["SYN-REQ-1201"],
        }],
        "system_interfaces": [],
        "open_items": [],
    }


def mapping_prefix_reversed():
    """A MAPPING- sheet (the family-B reader's sheet name) whose band labels
    the legacy reader refuses: standard before stage. Read by content."""
    wb = new_workbook()
    ws = wb.create_sheet("MAPPING-NB")
    rows = [["Source File Layout", None, None, None, "Standard Layer", None, None, None,
             "Stage Layer", None, None, None],
            [*SOURCE_HEADERS, *TARGET_HEADERS, *TARGET_HEADERS]]
    for name in FIELDS:
        rows.append([*_source_cells(name), *_target_cells("nb", "nb_member_risk", name),
                     *_target_cells("stg_nb", "nb_member_risk", name)])
    write_rows(ws, rows)
    return wb
