"""Synthetic reproductions of the D1 post51 12-pair report's extraction
failures (acfc-results run_20261015T074546Z_97fe673). The real documents stay
ACFC-side; each builder here reproduces the shape that produced one pair's
error line, in the FEED_n / VENDOR_x vocabulary of tests/acfc_shapes."""

from __future__ import annotations

import json
from pathlib import Path

from acfc_shapes.common import band_row, merge_bands, new_workbook, write_rows
from segmented_fixture import frd_contract_dict

LAYER = ["Catalog", "Schema", "TableName", "ColumnName", "DataType", "Mandatory",
         "Primary Key", "Constraints", "Field Description", "Table Description",
         "Transformations/Data Quality"]
SOURCE = ["Field Id", "Column No.", "Field Name", "Data Type", "Length", "Field Length",
          "Start position", "End Position", "Segment", "PII/PHI", "Comments"]
FIELDS = ["Claim Number", "Member Id", "Service Date", "Billed Amount", "Paid Amount",
          "Provider Id"]
AUDIT = [("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "timestamp")]


def family_e_workbook(path: Path, segments: list[str | None], *,
                      audit: list[tuple[str, str]] = AUDIT, table: str = "feed_5_dtl",
                      fields: list[str] = FIELDS) -> Path:
    """A Family E mapping sheet (meta r1-r9, band r10, headers r11) with ONE
    stage / standard table; ``segments[i]`` is field i's Segment cell (cycled),
    audit rows leave theirs empty."""
    wb = new_workbook()
    write_rows(wb.create_sheet("File Details"),
               [["Vendor", "FileName", "Actual File Name", "File Description", "Location",
                 "Frequency", "File Extension"],
                ["VENDOR_E", "FEED_5_*.txt", "FEED_5_20260115.txt", "Claims file",
                 "inbound/vendor_e", "Weekly", ".txt"]])
    ws = wb.create_sheet("FEED_5_MAPPING")
    write_rows(ws, [["File(s)", "FEED_5_*.txt"], ["File Generator", None],
                    ["File Location", "inbound/vendor_e"], ["LOB", "ALL"],
                    ["File frequency", "Weekly"], ["Domain", "Claims"],
                    ["Sub-Domain", "Medical"], ["NOTE", "Pipe delimited."],
                    ["File type", "txt (pipe delimited |)"]], start_row=1)
    groups = [("Source Layout", 11), ("Stage Layer", 11), ("Standard Layer", 11)]
    write_rows(ws, [band_row(groups)], start_row=10)
    merge_bands(ws, 10, groups)
    write_rows(ws, [SOURCE + LAYER + LAYER], start_row=11)
    rows = []
    for index, name in enumerate(fields):
        column = name.upper().replace(" ", "_")
        rows.append([index + 1, index + 1, name, "varchar", 20, None, None, None,
                     segments[index % len(segments)], "No", name,
                     "syn_dlk", "stg_clm", table, column, "String", None, None, None, name,
                     "claims", None,
                     "syn_std", "clm", table, column, "String", None, None, None, name,
                     "claims", "Load as is"])
    for column, dtype in audit:
        rows.append([None] * 11 + ["syn_dlk", "stg_clm", table, column, dtype] + [None] * 6
                    + ["syn_std", "clm", table, column, dtype] + [None] * 6)
    write_rows(ws, rows, start_row=12)
    wb.save(path)
    return path


def family_e_frd(path: Path, *, tables: tuple[str, ...] = ("feed_5_dtl",),
                 segments: tuple[str, ...] = ()) -> Path:
    data = frd_contract_dict()
    data["feeds"][0].update({
        "feed_name": "FEED_5 claims", "file_name_patterns": ["FEED_5_*.txt"],
        "file_format": "txt", "delimiter": "|", "record_segments": list(segments),
        "stage_target": {"catalog": None, "schema": "stg_clm", "tables": list(tables),
                         "load_strategy": "Truncate and Load"},
        "standard_target": {"catalog": None, "schema": "clm", "tables": list(tables),
                            "load_strategy": "Append"},
        "validation_rules": ["Load the file as received."], "recycle_rule": None,
    })
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def untitled_f2_frd(path: Path, caption: str = "blank", spacer: bool = False) -> Path:
    """The F2 (Solution Requirement) FRD of tests/acfc_shapes with UNTITLED
    requirement tables (D1 post51 pairs 08-10): ``caption`` "blank" = row 0
    empty, "none" = no caption row; ``spacer`` = an empty first column."""
    from acfc_shapes.frd import build_f2_pair8

    path.write_bytes(build_f2_pair8(caption=caption, spacer=spacer))
    return path
