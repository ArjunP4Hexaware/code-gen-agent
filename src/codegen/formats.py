"""What KIND of file a feed arrives as (M11). One definition, imported by
resolve / extract / emit / metadata so they can never disagree — the same
reason ``_FORMAT_DELIMITERS`` is shared.

Three kinds, mutually exclusive:

``delimited``    a separator between fields (the default; `delimiter` is it).
``fixed_width``  byte positions, no separator — `delimiter` is ``""``.
``spreadsheet``  an .xlsx / .xls workbook: no separator and no byte
                 positions, a SHEET instead. `delimiter` is ``""`` too, which
                 is why the fixed-width test may never be "the delimiter is
                 empty" alone (before M11 it was, in two places, and an xlsx
                 feed would have rendered as fixed width).
"""

from __future__ import annotations

import re

_EXTENSION_RE = re.compile(r"\.([A-Za-z0-9]{2,5})(?:$|[^A-Za-z0-9])")


def _tokens(config) -> tuple[list[str], list[str]]:
    vdd = config.extractor.vdd
    return ([t.lower() for t in getattr(config.extractor, "spreadsheet_tokens", ())],
            [t.lower() for t in vdd.fixed_width_tokens])


def _extensions(text: str | None) -> set[str]:
    return {m.group(1).lower() for m in _EXTENSION_RE.finditer(text or "")}


def is_spreadsheet(file_format: str | None, config, file_patterns=()) -> bool:
    """True when the SOURCE files are spreadsheets. The format cell may say
    so ("xlsx", ".xlsx", "Excel"), or every file pattern may carry a
    spreadsheet extension while the format is prose ("File Data Ingestion")."""
    spreadsheet_tokens, _fixed = _tokens(config)
    if not spreadsheet_tokens:
        return False
    fmt = (file_format or "").lower()
    if any(token in fmt for token in spreadsheet_tokens):
        return True
    patterns = [p for p in (file_patterns or ()) if p]
    return bool(patterns) and all(
        _extensions(p) & set(spreadsheet_tokens) for p in patterns)


def is_fixed_width(file_format: str | None, config, delimiter: str | None = None,
                   file_patterns=()) -> bool:
    """True for a positional file. A spreadsheet never is, however empty its
    delimiter."""
    if is_spreadsheet(file_format, config, file_patterns):
        return False
    _spreadsheet, fixed_tokens = _tokens(config)
    fmt = (file_format or "").lower()
    if any(token in fmt for token in fixed_tokens):
        return True
    return delimiter == ""


_TYPE_FORMAT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z_ ]*?)\s*\((.+)\)\s*$")


def split_type_format(raw: str | None) -> tuple[str, str | None]:
    """M11 item 13 (SHAPES_ROUND2 §4.2): a type cell that carries a FORMAT —
    ``timestamp(YYYY-MM-DD HH:MM:SS)`` — is (``timestamp``, the format). A
    parenthesised PRECISION (``decimal(10,2)``, ``varchar(50)``) is part of
    the type and stays."""
    text = (raw or "").strip()
    match = _TYPE_FORMAT_RE.match(text)
    if match is None:
        return text, None
    inner = match.group(2).strip()
    if re.fullmatch(r"[\d\s,]+", inner):
        return text, None
    return match.group(1).strip(), inner


def file_kind(file_format: str | None, config, delimiter: str | None = None,
              file_patterns=()) -> str:
    if is_spreadsheet(file_format, config, file_patterns):
        return "spreadsheet"
    if is_fixed_width(file_format, config, delimiter, file_patterns):
        return "fixed_width"
    return "delimited"
