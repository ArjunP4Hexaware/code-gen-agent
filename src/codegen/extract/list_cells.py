"""post179: a TableName cell that LISTS tables - one STTM mapping for several
parallel feeds (a staging run: one table per line of business, "a_remit b_remit" in
every stage cell, one file per line in the sheet's File Names cell).

A cell lists tables when it holds two or more whitespace-separated words, each
a plain identifier (``gate.ddl_names.IDENTIFIER_RE``). It is SPLIT only on
evidence: the sheet's own File Names cell states exactly as many files. Then
feed ``i`` takes the ``i``-th name of every list cell and the ``i``-th file - the
order the document states, never a name match. A cell listing a different
number of names fills nothing for a split feed (blank + flagged). Pure: no I/O.
"""

from __future__ import annotations

import re

from codegen.gate.ddl_names import IDENTIFIER_RE

_SEPARATORS = re.compile(r"[\s,;]+")


def listed_tables(value: str | None) -> list[str] | None:
    """The names a list cell states, in order; None for an ordinary cell (one
    word, blank, or a word that is no plain identifier)."""
    if not value or not re.search(r"\s", value.strip()):
        return None
    names = [n for n in _SEPARATORS.split(value.strip()) if n]
    if len(names) < 2 or not all(IDENTIFIER_RE.match(n) for n in names):
        return None
    return names


def split_count(stage_table: str | None, own_files: list[str]) -> int | None:
    """How many feeds a sheet splits into: the stage list cell's length when the
    sheet's own file cell states exactly that many files; else None (no split)."""
    names = listed_tables(stage_table)
    if names is None or len(own_files) != len(names):
        return None
    return len(names)


def pick(value: str | None, index: int, count: int) -> tuple[str | None, bool]:
    """(the value feed ``index`` of ``count`` takes from one cell, whether the
    cell listed a different number of names). An ordinary cell is shared by
    every feed; a list cell of ``count`` names gives its ``index``-th; any other
    list leaves the cell blank for the split feed."""
    names = listed_tables(value)
    if names is None:
        return value, False
    if len(names) == count:
        return names[index], False
    return None, True
