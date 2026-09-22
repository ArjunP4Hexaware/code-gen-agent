"""The environment probe (M10): ask, classify, never stop a run.

READ-ONLY. For every object the artefacts touch — each stage / standard
table of the deployment DDL (Unity Catalog), each config row of the DML (the
SQL Server metadata DB) — one bounded question, one of four answers
(``codegen.env.model``). A question that cannot be asked, is refused, or does
not answer in time is ``unreadable`` WITH the reason; it is a flag, never a
stop, and the artefacts are then emitted exactly as with the probe disabled.

This module holds the CLASSIFIER and the two client protocols. It opens no
connection itself: the real transports are ``codegen.env.clients`` (an edge,
built only inside a Databricks runtime); tests pass fakes. Every query runs
in its own daemon thread, joined for ``timeout_seconds`` — a query that hangs
is given up, not waited for.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable
from typing import Protocol

from codegen.env.model import (
    EnvProbeResult,
    Evidence,
    ExpectedRow,
    ExpectedTable,
    FieldDiff,
    Observation,
    ProbedObject,
)


class ProbeUnreadable(RuntimeError):
    """The environment could not answer. ``query`` is what was (to be) asked."""

    def __init__(self, reason: str, query: str = "") -> None:
        super().__init__(reason)
        self.query = query


class Unavailable:
    """A client that cannot be built — every object it would serve reads
    ``unreadable`` with this reason, and nothing is attempted."""

    def __init__(self, reason: str) -> None:
        self.reason = reason


class UcClient(Protocol):
    # M13: optional attribute ``identity`` (who the client asks as) — recorded
    # on every Evidence it produces; absent = not recorded.
    def describe(self, qualified: str) -> tuple[list[tuple[str, str]] | None, str]:
        """(columns as (name, type) — None when the table does not exist, the
        query that was sent). Raises ``ProbeUnreadable`` otherwise."""


class MetadataDbClient(Protocol):
    def select_rows(self, table: str, columns: list[str],
                    key: dict[str, str]) -> tuple[list[dict], str]:
        """(rows matching the natural key as {column: value}, the query that
        was sent). Raises ``ProbeUnreadable`` when it cannot be asked."""


# ------------------------------------------------------------------ comparison

_TYPE_ALIASES = {"integer": "int", "long": "bigint", "short": "smallint", "byte": "tinyint",
                 "real": "float", "dec": "decimal", "numeric": "decimal", "bool": "boolean",
                 "timestamp_ltz": "timestamp"}


def normalize_type(dtype: str) -> str:
    """Spelling-insensitive type text: ``Decimal(17, 2)`` == ``decimal(17,2)``,
    ``INTEGER`` == ``int``. Nothing semantic — a width or a precision that
    differs is a difference."""
    text = re.sub(r"\s+", "", str(dtype or "")).lower()
    head, paren, tail = text.partition("(")
    return _TYPE_ALIASES.get(head, head) + paren + tail


def _same_value(expected: str | None, actual) -> bool:
    left = "" if expected is None else str(expected).strip()
    right = "" if actual is None else str(actual).strip()
    if left == right:
        return True
    try:  # 1 == 1.0 == "1": the driver returns typed values, the artefact text
        return float(left) == float(right)
    except ValueError:
        return False


def classify_table(expected: ExpectedTable,
                   actual: list[tuple[str, str]] | None) -> tuple[str, list[FieldDiff]]:
    if actual is None:
        return "absent", []
    have = {name.lower(): (name, dtype) for name, dtype in actual}
    want = {name.lower() for name, _ in expected.columns}
    diffs: list[FieldDiff] = []
    for name, dtype in expected.columns:
        found = have.get(name.lower())
        if found is None:
            diffs.append(FieldDiff(column=name, kind="added", expected=dtype))
        elif normalize_type(found[1]) != normalize_type(dtype):
            diffs.append(FieldDiff(column=name, kind="type", expected=dtype, actual=found[1]))
    for name, dtype in actual:
        if name.lower() not in want:
            diffs.append(FieldDiff(column=name, kind="removed", actual=dtype))
    return ("different" if diffs else "identical"), diffs


def classify_row(expected: ExpectedRow,
                 actual: dict | None) -> tuple[str, list[FieldDiff], list[FieldDiff]]:
    if actual is None:
        return "absent", [], []
    lowered = {str(k).lower(): v for k, v in actual.items()}
    status = {c.lower() for c in expected.status_columns}
    diffs: list[FieldDiff] = []
    status_diffs: list[FieldDiff] = []
    for column, value in expected.values.items():
        if column in expected.natural_key or column.lower() not in lowered:
            continue
        found = lowered[column.lower()]
        if _same_value(value, found):
            continue
        diff = FieldDiff(column=column, kind="value", expected=value,
                         actual=None if found is None else str(found))
        (status_diffs if column.lower() in status else diffs).append(diff)
    return ("different" if diffs else "identical"), diffs, status_diffs


# --------------------------------------------------------------------- bounded


def _bounded(call: Callable[[], object], timeout: float, what: str):
    box: dict = {}

    def run() -> None:
        try:
            box["value"] = call()
        except BaseException as exc:  # noqa: BLE001 — every failure is a reason, not a crash
            box["error"] = exc

    thread = threading.Thread(target=run, name="env-probe-query", daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise ProbeUnreadable(f"{what} did not answer within {timeout:g}s (given up)")
    if "error" in box:
        exc = box["error"]
        if isinstance(exc, ProbeUnreadable):
            raise exc
        raise ProbeUnreadable(f"{type(exc).__name__}: {(str(exc).splitlines() or [''])[0][:200]}")
    return box["value"]


# ----------------------------------------------------------------------- probe


def _text_rows(rows) -> list[dict[str, str | None]]:
    """A driver's typed values as text — what the classifier compares anyway."""
    return [{str(k): (None if v is None else str(v)) for k, v in dict(row).items()}
            for row in rows]


def probe_feed(feed_slug: str, tables: list[ExpectedTable], rows: list[ExpectedRow],
               uc: UcClient | Unavailable, db: MetadataDbClient | Unavailable,
               probed_at: str, timeout_seconds: float = 20.0) -> EnvProbeResult:
    objects: list[ProbedObject] = []
    uc_identity = getattr(uc, "identity", None)
    db_identity = getattr(db, "identity", None)

    for table in tables:
        base = {"kind": "uc_table", "name": table.qualified, "layer": table.layer}
        if isinstance(uc, Unavailable):
            objects.append(ProbedObject(**base, state="unreadable", error=uc.reason))
            continue
        try:
            columns, query = _bounded(lambda t=table: uc.describe(t.qualified),
                                      timeout_seconds, f"DESCRIBE {table.qualified}")
        except ProbeUnreadable as exc:
            objects.append(ProbedObject(
                **base, state="unreadable", error=str(exc),
                evidence=(Evidence(source="unity_catalog", query=exc.query, at=probed_at,
                                   identity=uc_identity)
                          if exc.query else None)))
            continue
        state, diffs = classify_table(table, columns)
        objects.append(ProbedObject(
            **base, state=state, diffs=diffs,
            observation=Observation(columns=None if columns is None
                                    else [(str(n), str(t)) for n, t in columns]),
            evidence=Evidence(source="unity_catalog", query=query, at=probed_at,
                              identity=uc_identity)))

    for row in rows:
        base = {"kind": "config_row", "name": row.name, "table": row.table,
                "sheet": row.sheet, "row_index": row.row_index,
                "natural_key": dict(row.natural_key)}
        if row.unkeyed_reason:
            objects.append(ProbedObject(**base, state="unreadable", error=row.unkeyed_reason))
            continue
        if isinstance(db, Unavailable):
            objects.append(ProbedObject(**base, state="unreadable", error=db.reason))
            continue
        columns = [c for c in row.values if c not in row.natural_key]
        try:
            found, query = _bounded(
                lambda r=row, c=columns: db.select_rows(r.table, [*r.natural_key, *c],
                                                        dict(r.natural_key)),
                timeout_seconds, f"SELECT from {row.table}")
        except ProbeUnreadable as exc:
            objects.append(ProbedObject(
                **base, state="unreadable", error=str(exc),
                evidence=(Evidence(source="metadata_db", query=exc.query, at=probed_at,
                                   identity=db_identity)
                          if exc.query else None)))
            continue
        evidence = Evidence(source="metadata_db", query=query, at=probed_at,
                            identity=db_identity)
        observation = Observation(rows=_text_rows(found))
        if len(found) > 1:
            objects.append(ProbedObject(
                **base, state="unreadable", evidence=evidence, observation=observation,
                error=f"the natural key ({row.key_label}) matched {len(found)} rows in "
                      f"{row.table} — it does not identify one row; nothing is concluded"))
            continue
        state, diffs, status_diffs = classify_row(row, found[0] if found else None)
        compared = [c for c in columns if c not in row.status_columns] if found else []
        objects.append(ProbedObject(**base, state=state, diffs=diffs, compared=compared,
                                    status_diffs=status_diffs, evidence=evidence,
                                    observation=observation))

    return EnvProbeResult(feed_slug=feed_slug, probed_at=probed_at, objects=objects)
