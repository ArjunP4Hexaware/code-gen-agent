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


def split_count(stage_table: str | None, own_files: list[str],
                standard_tables: list[str | None] | None = None) -> int | None:
    """How many feeds a sheet splits into, else None (no split). post182 (an
    adversarial review): the evidence must be stated twice and agree -
    * the sheet's own File Names cell states exactly as many files;
    * a STANDARD TableName cell lists as many names too (one stage cell with two
      words and a file + its control file was a typo split into two feeds);
    * the order agrees: a table's distinctive word (one no other listed table
      has) that names a DIFFERENT position's file, and not its own, refuses the
      split (the files listed in the other order would pair crosswise)."""
    names = listed_tables(stage_table)
    if names is None or len(own_files) != len(names):
        return None
    count = len(names)
    if not any(len(listed_tables(s) or []) == count for s in standard_tables or []):
        return None
    words = [set(n.lower().split("_")) for n in names]
    for i, own in enumerate(words):
        distinctive = own - set().union(*(w for j, w in enumerate(words) if j != i))
        hits = {j for j, f in enumerate(own_files)
                for w in distinctive if len(w) > 1 and w in f.lower()}
        if hits and i not in hits:
            return None
    return count


def nth_name(value: str | None, index: int) -> str | None:
    """The ``index``-th name of a list cell (the split's flag / label text)."""
    names = listed_tables(value) or []
    return names[index] if index < len(names) else None


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
