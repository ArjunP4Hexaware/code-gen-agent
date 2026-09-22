"""In-memory stand-ins for the M10 probe's two targets.

Both real targets (ACFC's Unity Catalog, ACFC's SQL Server metadata DB) exist
only inside the operator's workspace, so the suite drives THESE. Each fake
records every question it was asked (``asked``) — a test can assert what the
probe sent, not only what it concluded.
"""

from __future__ import annotations

import time

from codegen.env.clients import render_select
from codegen.env.probe import ProbeUnreadable


class FakeUc:
    """``tables``: qualified name (lower-case) -> [(column, type)] | an
    Exception to raise | ``"hang"``. A name that is not there = absent."""

    def __init__(self, tables: dict | None = None) -> None:
        self.tables = {k.lower(): v for k, v in (tables or {}).items()}
        self.asked: list[str] = []

    def describe(self, qualified: str):
        query = f"DESCRIBE TABLE {qualified}"
        self.asked.append(query)
        found = self.tables.get(qualified.lower())
        if found == "hang":
            time.sleep(30)
        if isinstance(found, Exception):
            raise ProbeUnreadable(str(found), query)
        return (None if found is None else list(found)), query


class FakeDb:
    """``rows``: table -> list of row dicts. A keyed SELECT returns the rows
    whose key columns match (as text). ``refuse``: table -> reason."""

    def __init__(self, rows: dict | None = None, refuse: dict | None = None,
                 schema: str = "dbo") -> None:
        self.rows = rows or {}
        self.refuse = refuse or {}
        self.schema = schema
        self.asked: list[str] = []

    def select_rows(self, table: str, columns: list[str], key: dict[str, str]):
        query = render_select(self.schema, table, columns, key)
        self.asked.append(query)
        if table in self.refuse:
            raise ProbeUnreadable(self.refuse[table], query)
        found = [dict(row) for row in self.rows.get(table, [])
                 if all(str(row.get(k)) == str(v) for k, v in key.items())]
        return found, query


def identical_row(expected) -> dict:
    """The environment's row that matches an ExpectedRow exactly."""
    return {**{c: v for c, v in expected.values.items()}, **expected.natural_key}
