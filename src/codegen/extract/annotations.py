"""FILE_DETAILS annotation rows: rows that do not fit the sheet's row schema.

A FILE_DETAILS sheet lists one file per row (vendor, file name, frequency …).
Real sheets also carry guidance written INTO the table — ``DataType = …``
lines, a note under the last file, an italic or coloured example row. Such a
row is not a file: it is skipped by every reader of the sheet (the classic
MAPPING- parser, the content-driven reader, the layout stage's file facts)
and listed in the extraction report (the contract notes + one
``file_details_annotation_skipped`` flag per row, citing its cell), never
read as a file pattern.

The rule is structural and deliberately narrow — a row is an annotation when

* any cell reads as an assignment (``<label> = <value>``), or
* the file-name cell is empty while other cells carry text, or
* the file-name cell holds several lines, or prose (whitespace and no file
  extension), or
* every non-empty cell is styled as guidance (italic, or an explicit
  non-black font colour) — a styled real file row is therefore skipped too,
  but never silently: the report line names it.

A row that passes is read exactly as before, so a sheet without annotations
reads byte-identically.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_ASSIGNMENT_RE = re.compile(r"^\s*[A-Za-z][\w /().-]{0,40}?\s*=\s*\S")
_EXTENSION_RE = re.compile(r"\.[A-Za-z0-9*]{1,6}\s*$")
_FILE_NAME_HEADERS = ("filename", "file name", "inbound file name")


def file_name_index(headers: Sequence[str | None]) -> int | None:
    """The file-name column of a FILE_DETAILS header row (normalized
    headers): an exact known header first, else the first header naming a
    file and a name that is not a description."""
    normalized = [(h or "").strip().lower() for h in headers]
    exact = next((i for i, h in enumerate(normalized) if h in _FILE_NAME_HEADERS), None)
    if exact is not None:
        return exact
    return next((i for i, h in enumerate(normalized)
                 if "file" in h and "name" in h and "description" not in h), None)


def _guidance_style(cell) -> str | None:
    font = getattr(cell, "font", None)
    if font is None:
        return None
    if font.i:
        return "italic"
    color = font.color
    if color is not None and color.type == "rgb" and isinstance(color.rgb, str) \
            and color.rgb[-6:].upper() != "000000":
        return "coloured"
    return None


def annotation_reason(cells: Sequence[str | None], name_index: int | None,
                      styled: Sequence | None = None) -> str | None:
    """Why this FILE_DETAILS row is an annotation, or None when it fits the
    row schema. ``cells`` are the row's text values; ``styled`` (optional) the
    openpyxl cells of the same row, for the guidance-style signal."""
    filled = [c for c in cells if c]
    if not filled:
        return None                                   # a blank row: nothing to skip
    assignment = next((c for c in filled if _ASSIGNMENT_RE.match(c)), None)
    if assignment is not None:
        return "an assignment line ('<label> = <value>'), not a file row"
    name = cells[name_index] if name_index is not None and name_index < len(cells) else None
    if not name:
        return "no file name in the file-name column, only other text (a note row)"
    if "\n" in name or "\r" in name:
        return "the file-name cell holds several lines of text"
    if re.search(r"\s", name.strip()) and not _EXTENSION_RE.search(name):
        return "the file-name cell is prose (words, no file extension), not a file name"
    if styled:
        styles = [_guidance_style(c) for c in styled
                  if c is not None and getattr(c, "value", None) not in (None, "")]
        if styles and all(styles):
            kinds = "/".join(sorted(set(styles)))
            return f"every filled cell is styled as guidance ({kinds} font)"
    return None


def describe(sheet: str, row: int, reason: str, cells: Sequence[str | None],
             limit: int = 60) -> str:
    """One extraction-report line: the row's cell, the reason, its text
    (truncated, single line)."""
    joined = " | ".join(c for c in cells if c).replace("\n", " ").replace("\r", " ")
    shown = joined if len(joined) <= limit else joined[:limit] + "…"
    return f"{sheet}!row {row} — {reason}; reads {shown!r}"


def flag(entry: str) -> str:
    return f"file_details_annotation_skipped:{entry} (not read as a file)"


__all__ = ["annotation_reason", "describe", "file_name_index", "flag"]
