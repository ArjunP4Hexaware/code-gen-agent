"""A data type cell with a parenthesised attribute (D1 post73 pair_06).

``timestamp(YYYY-MM-DD HH:MM:SS)``, ``decimal(18,2)``, ``varchar(50)``: the
TYPE KEYWORD is what a vocabulary check reads (the audit datatypes, the DDL
type map); the parenthesised ATTRIBUTE is kept on the column, verbatim:

- ``size`` — digits, or digits ``,`` digits (a length / precision, scale): part
  of the type the DDL writes, so the contract keeps the whole cell text
  (``decimal(18,2)``) and a vocabulary check reads the keyword;
- ``format`` — anything else (a date / time pattern): split off, so the
  contract's datatype is the keyword (``timestamp``) and the pattern travels
  in the column's ``*_format`` field (the IIG's date rules read it).

A cell without parentheses is its own keyword (``kind`` ``none``)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

_PARENTHESISED = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_ ]*?)\s*\(\s*(.*?)\s*\)\s*$", re.DOTALL)
_SIZE = re.compile(r"^\d+(?:\s*,\s*\d+)?$")


@dataclass(frozen=True)
class TypeParts:
    raw: str                    # the cell as written (never re-spaced)
    keyword: str
    attribute: str | None
    kind: Literal["none", "size", "format"]

    @property
    def type_text(self) -> str:
        """The datatype the contract carries: the keyword when a format was
        split off, else the cell as written."""
        return self.keyword if self.kind == "format" else self.raw

    @property
    def format(self) -> str | None:
        return self.attribute if self.kind == "format" else None


def split_type(raw: str | None) -> TypeParts:
    """``raw`` as keyword + attribute (see the module docstring)."""
    written = "" if raw is None else str(raw)
    spaced = " ".join(written.split())
    match = _PARENTHESISED.match(spaced)
    if match is None:
        return TypeParts(written, spaced, None, "none")
    keyword, attribute = match.group(1).strip(), match.group(2)
    kind: Literal["size", "format"] = "size" if _SIZE.match(attribute) else "format"
    return TypeParts(written, keyword, attribute, kind)


__all__ = ["TypeParts", "split_type"]
