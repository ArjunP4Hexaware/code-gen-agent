"""Synthetic reproductions of the D1 post73 12-pair report's extract-sttm
failures (acfc-results run_20261019T193332Z_fe61bc4, timestamp 181043Z). The
real documents stay ACFC-side; each builder reproduces the shape behind one
pair's coordinate-only error line, in the FEED_n / VENDOR_x vocabulary of
tests/acfc_shapes:

- pair_05 ``STTM required element missing (role column) at STTM sheet 4 row 59
  col 15``: a row whose stage ColumnName is blank while another target cell
  reads a skip marker ("Do Not Map" / "N/A");
- pair_06 ``STTM audit column invalid (role audit_column; type timestamp) at
  STTM sheet 3 row 30``: an audit row typed ``timestamp(YYYY-MM-DD HH:MM:SS)``;
- pair_08 ``STTM required element missing (role target_type) at STTM sheet 1
  row 96 col 17``: ONE row with a stage column and no data type;
- pair_10 ``Contract fails validation at STTM sheet 2``: a feed the contract
  model refuses (no file format stated anywhere).

The mapping sheet is :func:`post51_pairs.family_e_workbook`'s Family E layout
(File Details sheet 1, the mapping sheet 2: source band columns 1-11, stage
band 12-22 with ColumnName in column 15 and DataType in 16, standard band
23-33)."""

from __future__ import annotations

import json
from pathlib import Path

from acfc_shapes.common import band_row, merge_bands, new_workbook, write_rows
from post51_pairs import AUDIT, FIELDS, LAYER, SOURCE, family_e_frd

# 0-based positions in a data row (see the module docstring)
CELL = {"field_name": 2, "segment": 8, "stage_column": 14, "stage_type": 15,
        "standard_column": 25, "standard_type": 26}
STAGE_COLUMN_COL = 15
STAGE_TYPE_COL = 16
FIRST_DATA_ROW = 12


def mapping_workbook(path: Path, overrides: dict[int, dict[str, object]] | None = None, *,
                     audit: list[tuple[str, str]] = AUDIT, fields: list[str] = FIELDS,
                     table: str = "feed_5_dtl") -> Path:
    """A Family E workbook whose field ``i`` (0-based) takes the cells named in
    ``overrides[i]`` (keys of :data:`CELL`; ``None`` empties the cell)."""
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
        row = [index + 1, index + 1, name, "varchar", 20, None, None, None, None, "No", name,
               "syn_dlk", "stg_clm", table, column, "String", None, None, None, name,
               "claims", None,
               "syn_std", "clm", table, column, "String", None, None, None, name,
               "claims", "Load as is"]
        for key, value in (overrides or {}).get(index, {}).items():
            row[CELL[key]] = value
        rows.append(row)
    for column, dtype in audit:
        rows.append([None] * 11 + ["syn_dlk", "stg_clm", table, column, dtype] + [None] * 6
                    + ["syn_std", "clm", table, column, dtype] + [None] * 6)
    write_rows(ws, rows, start_row=FIRST_DATA_ROW)
    wb.save(path)
    return path


def frd(path: Path, **updates: object) -> Path:
    """The Family E FRD contract, with ``updates`` on its one feed."""
    family_e_frd(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["feeds"][0].update(updates)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def without_markers(config):
    """``config`` with no skip marker at all (neither list): the pre-post74
    behaviour for a row whose stage column is blank."""
    profile = config.conventions.get(None).model_copy(update={"skip_row_markers": []})
    conventions = config.conventions.model_copy(update={
        "profiles": {**config.conventions.profiles, config.conventions.profile: profile}})
    extractor = config.extractor.model_copy(update={"unmapped_markers": []})
    return config.model_copy(update={"conventions": conventions, "extractor": extractor})


def coordinates(exc: BaseException, stage: str = "extract-sttm") -> str:
    """The coordinates-tier line the CLI's marker makes of ``exc``."""
    from codegen.run_errors import MARKER, Coord, coordinate_line, error_marker

    marker = error_marker(stage, "sttm.unreadable", Coord("STTM"), exc=exc)
    return coordinate_line(json.loads(marker[len(MARKER):]))
