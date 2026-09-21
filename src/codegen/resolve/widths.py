"""Fixed-width byte widths (M9.2) — the chain behind one field's width.

A source-band ``Length`` cell is a byte width only when it is an INTEGER. The
real pair-1 sheet writes ``10,2`` for its amount fields: a precision, scale
pair — a statement about the VALUE, not about how many bytes the field
occupies. The chain for a positional field's width:

1. the STTM length, when it is an integer;
2. the STTM span ``end - start + 1``, when both cells are integers
   (flag ``width_from_sttm_span``);
3. the Vendor Data Dictionary's span for the same field — matched by
   normalized field name and, when both documents are segmented, by segment —
   ``end - start + 1`` (its Length column when it states no end)
   (flag ``width_from_vdd``);
4. the person's answer to ``feeds[i].fields[<name>].width``
   (flag ``width_from_user``).

The non-integer length is KEPT as the source type's precision
(``Decimal(10,2)``, flag ``length_is_precision``). A width is NEVER derived
from a precision: 10 digits with 2 decimals may occupy 10, 11, 12 or 13 bytes
depending on the sign and the decimal point — only a document can say.

Steps 1-2 run in the extractor (the STTM alone), 3-4 in the contract resolver
(it has the VDD); the layout stage asks question 4 when 1-3 leave a field open.
"""

from __future__ import annotations

import re

_INTEGER_RE = re.compile(r"^\s*0*(\d+)(?:\.0+)?\s*$")
_PRECISION_RE = re.compile(
    r"^\s*(?:[A-Za-z][A-Za-z ]*\(\s*)?(\d+)\s*[,.]\s*(\d+)\s*\)?\s*$")
WIDTH_KEY_RE = re.compile(r"^feeds\[(\d+)\]\.fields\[(.+)\]\.width$")


def as_integer(value: str | int | None) -> int | None:
    """The integer a cell states ("13", "013", "13.0"), else None."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = _INTEGER_RE.match(str(value))
    return int(match.group(1)) if match else None


def as_precision(value: str | None) -> str | None:
    """``Decimal(p,s)`` for a length cell that states a precision and scale —
    "10,2", "10.2", "Decimal(10,2)", "NUMBER (10, 2)" — else None."""
    if as_integer(value) is not None:
        return None                      # "13.0": an integer a spreadsheet wrote as a float
    match = _PRECISION_RE.match(value or "")
    return f"Decimal({int(match.group(1))},{int(match.group(2))})" if match else None


def sttm_width(length: str | None, start: str | None, end: str | None
               ) -> tuple[int | None, str | None]:
    """(width, link) from the STTM alone: link ``"length"`` or ``"sttm_span"``;
    (None, None) when neither states one."""
    width = as_integer(length)
    if width is not None and width > 0:
        return width, "length"
    first, last = as_integer(start), as_integer(end)
    if first is not None and last is not None and last >= first:
        return last - first + 1, "sttm_span"
    return None, None


def normalize_field_name(value: str | None) -> str:
    """The matching form of a field name across documents: case, spaces, line
    breaks and punctuation dropped ("Amount\\n(01)" == "AMOUNT (01)")."""
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def width_key(feed_index: int, field_name: str) -> str:
    """The gap-question key of a field's width; the name is written on one
    line (the cell's line break becomes a space)."""
    return f"feeds[{feed_index}].fields[{' '.join(field_name.split())}].width"


def parse_width_answers(gaps: dict | None) -> dict[int, dict[str, int]]:
    """``{feed index: {normalized field name: width}}`` from ``gaps`` answers
    keyed ``feeds[i].fields[<name>].width``; a non-integer answer is refused."""
    out: dict[int, dict[str, int]] = {}
    for key, choice in (gaps or {}).items():
        match = WIDTH_KEY_RE.match(str(key))
        if match is None:
            continue
        value = choice.get("value") if isinstance(choice, dict) else choice
        width = as_integer(value)
        if width is None or width <= 0:
            raise ValueError(f"bad width answer {key!r}: {value!r} is not a positive integer "
                             "(a byte width — never a precision)")
        out.setdefault(int(match.group(1)), {})[normalize_field_name(match.group(2))] = width
    return out


__all__ = [
    "WIDTH_KEY_RE",
    "as_integer",
    "as_precision",
    "normalize_field_name",
    "parse_width_answers",
    "sttm_width",
    "width_key",
]
