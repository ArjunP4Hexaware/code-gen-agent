"""Audit column names as the STTM contract carries them (D1 App demo, 2026-10-13).

An STTM audit row may annotate its stage column — "LOB(Hardcod to MIDS)". The
contract carries the COLUMN (LOB); the note is a hardcode hint, kept as an
extraction flag citing the STTM cell (value MIDS). Every reader builds its
AuditColumn through ``clean_audit_column``, so no annotated name reaches the
contract — and through it the DDL, the IIG, the notebook pipeline or
metadata_inserts.sql.
"""

from __future__ import annotations

import re

_AUDIT_ANNOTATION_RE = re.compile(r"^(?P<base>[A-Za-z_]\w*)\s*\((?P<note>[^()]*)\)\s*$")
_HARDCODE_VALUE_RE = re.compile(r"\b(?:to|as|=|:)\s*(?P<value>\S.*?)\s*$", re.IGNORECASE)


def split_audit_annotation(column: str) -> tuple[str, str | None, str | None]:
    """``"LOB(Hardcod to MIDS)"`` -> ``("LOB", "Hardcod to MIDS", "MIDS")``: the
    column without its trailing parenthetical note, the note, and the value the
    note hardcodes (after "to" / "as" / "=" / ":"), else None. A name without a
    note comes back unchanged."""
    match = _AUDIT_ANNOTATION_RE.match(column.strip())
    if match is None:
        return column, None, None
    note = match.group("note").strip()
    value = _HARDCODE_VALUE_RE.search(note)
    return match.group("base"), note, value.group("value") if value else None


def clean_audit_column(column: str, key: str, cell: str, flags: list[str]) -> str:
    """The column the contract carries; an annotation appends the flag
    ``audit_column_annotated:<key> <cell>: ...`` (the hint, cited) to ``flags``."""
    base, note, value = split_audit_annotation(column)
    if note is not None:
        flags.append(f"audit_column_annotated:{key} {cell}: {column!r} -> column {base!r}, "
                      f"hardcode hint {note!r}" + (f" (value {value!r})" if value else ""))
    return base
