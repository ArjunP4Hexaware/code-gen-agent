"""Document text in a written workbook is DATA, never a formula (P0-5, 2026-10-30).

openpyxl binds any ``str`` of two or more characters that starts with ``=`` as a
FORMULA cell (``data_type == 'f'``): an FRD field or STTM cell such as
``=WEBSERVICE("http://...")`` copied into the IIG / review copy / config rows /
test-record workbook would run when a BSA opens the file. Every workbook the
agent writes goes through :func:`neutralize_formulas` just before it is saved
(``metadata_sheet.stable_workbook_bytes`` is the funnel; the two direct
``save`` calls call it too), and the gate check ``xlsx_no_formulas``
(``codegen.gate.xlsx_formulas``) reopens every emitted workbook and FAILS on a
formula cell.

Which characters, and why:

- ``=`` is the only character openpyxl turns into a formula, so it is the one
  that must have its ``data_type`` forced back to ``'s'`` (a string cell —
  Excel never evaluates a stored string cell on open).
- ``+ - @`` are formula starters in Excel's own INPUT parser (``+1+1``,
  ``@SUM(..)``, ``-1+1``): stored as strings they are inert on open, but a BSA
  who edits the cell and presses Enter has Excel re-parse the text. The cell
  style's ``quotePrefix`` (Excel's "text, typed with a leading apostrophe"
  flag) stops that re-parse, so every string starting with ``= + - @`` gets
  it.
- Tab / CR are CSV-injection prefixes (a CSV reader trims them, then sees
  ``=``); in an xlsx string cell they are text and Excel's input parser does
  not evaluate a cell that starts with whitespace, so they need nothing here
  (a line break already FAILS ``iig_single_line``).

The value is never altered — no apostrophe is prepended, the cell text stays a
byte-identical transcription of the document. Numbers, dates and ``None`` are
untouched; only the cells whose text starts with a trigger character change
(their ``data_type`` and one ``quotePrefix`` cell style), so a workbook with no
such cell serializes to exactly the bytes it did before.
"""

from __future__ import annotations

# Excel input-parser formula starters (see the module docstring).
FORMULA_TRIGGERS = ("=", "+", "-", "@")


def neutralize_formulas(workbook) -> int:
    """Force every string cell of ``workbook`` that starts with a formula
    trigger to a quote-prefixed STRING cell, value unchanged. Returns how many
    cells it touched. Only cells that exist are visited (``_cells``): iterating
    a sheet's range would create empty cells and change the bytes."""
    touched = 0
    for sheet in workbook.worksheets:
        for cell in sheet._cells.values():
            value = cell.value
            if isinstance(value, str) and value.startswith(FORMULA_TRIGGERS):
                cell.data_type = "s"
                cell.quotePrefix = True
                touched += 1
    return touched
