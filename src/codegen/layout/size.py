"""How big a workbook REALLY is, before reading it (M11 items 5 and 11).

The primary fix for heavy workbooks is the used range
(``codegen.layout.extent``): a sheet formatted a million rows down holding
336 rows is read as 336 rows. This module is the BACKSTOP behind it — a
workbook whose used cells exceed ``inputs.max_workbook_cells`` is
``unreadable`` with the count and the cap, a verdict instead of a parse that
outlives its budget.

It must measure the used range too, never the declared one: the v0.6.2 pair-3
STTM declares ``1,048,538 x 34`` = 35.6M cells and holds about 11k (SHAPES_
ROUND2 §3) — refusing it on the declaration would turn a readable document
into a permanent "unreadable". So:

* read-only, each sheet's declared ``<dimension>`` first — when the whole
  workbook declares no more than the cap, that is the answer (cheap: no row
  is materialised);
* otherwise the sheets are STREAMED read-only and counted up to their used
  range (the last row with a value before ``stop_after`` consecutive empty
  rows, the same rule the loader applies) — a bloated sheet stops early.
"""

from __future__ import annotations

from pathlib import Path


class WorkbookTooLarge(RuntimeError):
    """The workbook's USED cells exceed the configured cap."""


def _declared_cells(ws) -> int:
    return (ws.max_row or 0) * (ws.max_column or 0)


def _used_cells(ws, stop_after: int) -> int:
    """Rows up to the used range x the widest valued column in it."""
    last_row = 0
    widest = 0
    empty_run = 0
    for index, row in enumerate(ws.iter_rows(values_only=True), start=1):
        valued = [i for i, v in enumerate(row, start=1) if v is not None and v != ""]
        if valued:
            last_row = index
            widest = max(widest, valued[-1])
            empty_run = 0
        else:
            empty_run += 1
            if stop_after > 0 and last_row and empty_run >= stop_after:
                break
    return last_row * widest


def workbook_cells(path: Path, stop_after: int = 500,
                   max_cells: int = 0) -> tuple[int, dict[str, int], bool]:
    """(total cells, per-sheet counts, streamed?). The declared dimensions
    when they fit under ``max_cells``; the streamed used range otherwise."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        declared = {ws.title: _declared_cells(ws) for ws in workbook.worksheets}
        if max_cells > 0 and sum(declared.values()) <= max_cells and all(declared.values()):
            return sum(declared.values()), declared, False
        used = {ws.title: _used_cells(ws, stop_after) for ws in workbook.worksheets}
    finally:
        workbook.close()
    return sum(used.values()), used, True


def check_workbook_size(path: Path, max_cells: int, stop_after: int = 500) -> None:
    """Raise ``WorkbookTooLarge`` when the workbook's USED cells exceed the
    cap. A cap of 0 (or less) is off. A workbook that cannot even be opened
    read-only is left alone — the reader that follows reports that in its
    own words."""
    if max_cells <= 0:
        return
    try:
        total, per_sheet, _streamed = workbook_cells(Path(path), stop_after, max_cells)
    except Exception:  # noqa: BLE001 — not this function's verdict to give
        return
    if total > max_cells:
        biggest = sorted(per_sheet.items(), key=lambda kv: -kv[1])[:3]
        detail = ", ".join(f"{name} {cells:,}" for name, cells in biggest if cells)
        raise WorkbookTooLarge(
            f"unreadable: {total:,} used cells, > cap {max_cells:,} "
            f"(inputs.max_workbook_cells; largest sheets: {detail}) — the document was not "
            "read. Raise the cap for this workspace, or split the workbook.")
