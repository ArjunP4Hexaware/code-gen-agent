"""A worksheet's REAL used range (M11 item 11).

A sheet may carry a styled but EMPTY cell a million rows down (Excel keeps
formatting a user dragged to the bottom). openpyxl then reports
``max_row = 1,048,538`` — and every ``iter_rows`` over the sheet, in normal
mode, CREATES a cell object for every row up to it: 34 columns x a million
rows. That, not the data, is what ran the v0.6.2 parser past its budget on a
sheet holding 336 real rows (SHAPES_ROUND2 §3).

So documents are loaded through :func:`load_document`, which drops each
worksheet's dead tail right after the load — EMPTY cells only (styled, no
value) more than ``stop_after`` rows (config ``extractor.used_range_empty_rows``)
below the data (the exact cut: :func:`trim_worksheet`). openpyxl derives
``max_row`` from the cells it holds, so every scan downstream is bounded
without a change at the call site.

A cell WITH a value is never dropped: rows with values far below a long run
of empty rows are kept and read (the sheet is then slower to scan, never
incomplete), and ``TrimReport`` counts them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrimReport:
    """Per sheet: (declared max_row, used max_row, valued rows found below a
    long run of empty rows — kept and read)."""

    sheets: dict[str, tuple[int, int, int]] = field(default_factory=dict)

    @property
    def trimmed(self) -> dict[str, tuple[int, int, int]]:
        return {name: v for name, v in self.sheets.items() if v[0] != v[1]}

    def notes(self) -> list[str]:
        out = []
        for name, (declared, used, beyond) in self.trimmed.items():
            note = (f"sheet {name!r}: used range {used} row(s) (the sheet reached row "
                    f"{declared:,}, formatting only)")
            if beyond:
                note += (f"; {beyond} row(s) with values lie below a run of empty rows — "
                         "kept and read")
            out.append(note)
        return out


def used_max_row(valued_rows: list[int], stop_after: int) -> tuple[int, int]:
    """(last row before the first gap of >= ``stop_after`` empty rows, the
    number of valued rows beyond it). ``valued_rows`` sorted ascending."""
    if not valued_rows:
        return 0, 0
    last = valued_rows[0]
    for index, row in enumerate(valued_rows[1:], start=1):
        if stop_after > 0 and row - last - 1 >= stop_after:
            return last, len(valued_rows) - index
        last = row
    return last, 0


def trim_worksheet(ws, stop_after: int) -> tuple[int, int, int]:
    """Drop the empty cells of the dead tail. (declared, used, beyond).

    The cut is the EARLIER of two bounds — the last held cell (valued or only
    styled) before the first gap of ``stop_after`` rows holding no cell at
    all, and ``stop_after`` rows past the last VALUED row — but never above
    the last valued row: no cell with a value is ever dropped. The first
    bound keeps a normal sheet's trailing formatted rows, so a clean sheet
    and a copy of it with one styled cell a million rows down trim to the
    SAME max_row (fingerprint input); the second bounds a sheet whose
    formatting was dragged down row after row without a gap."""
    cells = getattr(ws, "_cells", None)
    if cells is None:                                    # a read-only sheet: nothing held
        return ws.max_row or 0, ws.max_row or 0, 0
    declared = ws.max_row or 0
    if stop_after <= 0 or not cells:
        return declared, declared, 0
    valued = sorted({row for (row, _col), cell in cells.items()
                     if cell.value is not None and cell.value != ""})
    used, beyond = used_max_row(valued, stop_after)
    held, _ = used_max_row(sorted({row for (row, _col) in cells}), stop_after)
    last_valued = valued[-1] if valued else 0
    # Never above the last valued row: values below a long gap are KEPT.
    cut = max(min(held, used + stop_after), last_valued)
    # Only a sheet whose cells run past the cut loses anything: a sheet with a
    # few formatted empty rows keeps its exact max_row, so no cached layout
    # profile is invalidated. A sheet holding NO value is cut at its held
    # cells or ``stop_after``, whichever is first.
    if cut < declared:
        for key in [k for k in cells if k[0] > cut]:
            del cells[key]
        dims = getattr(ws, "row_dimensions", None)
        if dims is not None:
            for row in [r for r in list(dims) if isinstance(r, int) and r > cut]:
                del dims[row]
        merged = getattr(ws, "merged_cells", None)
        if merged is not None:                           # a merge wholly in the dead tail
            for rng in [r for r in merged.ranges if r.min_row > cut]:
                merged.remove(rng)
    return declared, (ws.max_row or 0), beyond


def trim_workbook(workbook, stop_after: int) -> TrimReport:
    report = TrimReport()
    for ws in workbook.worksheets:
        report.sheets[ws.title] = trim_worksheet(ws, stop_after)
    return report


def load_document(path: Path, stop_after: int):
    """``load_workbook(path, data_only=True)`` trimmed to the used range —
    the ONE way a document workbook is opened for discovery and extraction."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, data_only=True)
    workbook.trim_report = trim_workbook(workbook, stop_after)   # type: ignore[attr-defined]
    return workbook
