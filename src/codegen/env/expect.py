"""What the artefacts EXPECT to find — built from the same rows the DML is.

Pure: no I/O, no transport. ``expected_rows`` classifies every IIG cell with
``codegen.emit.dml.cell_kind`` — the ONE precedence the INSERT renderer uses —
so the probe compares exactly what the script would write, and nothing it
cannot know at generation time (script variables left unassigned, audit
values, identity columns, multi-line cells).
"""

from __future__ import annotations

import json
from pathlib import Path

from codegen.config import Config
from codegen.env.model import ExpectedRow, ExpectedTable
from codegen.faq import LoadPatternFaq


def _faq_value(faq: LoadPatternFaq, name: str | None) -> str | None:
    if not name:
        return None
    answer = getattr(faq, name, None)
    if answer is None or getattr(answer, "source", "unknown") == "unknown":
        return None
    return str(answer.value)


def manages_row_status(faq: LoadPatternFaq) -> bool:
    value = _faq_value(faq, "manage_row_status")
    return value is not None and value.strip().lower() in ("yes", "y", "true")


def variable_values(faq: LoadPatternFaq, config: Config) -> dict[str, str | None]:
    """Script variable -> the literal it is DECLAREd with, None = unassigned."""
    import re

    values: dict[str, str | None] = {}
    for name, spec in config.dml.variables.items():
        value = _faq_value(faq, spec.faq_field)
        if value is not None and spec.sql_type.upper().startswith(("INT", "BIGINT", "SMALLINT")) \
                and not re.fullmatch(r"-?\d+", value.strip()):
            value = None
        values[name] = value.strip() if value is not None else None
    for role in config.dml.connection_roles:
        raw = (faq.connection_ids or {}).get(role)
        values[role] = str(raw).strip() if raw is not None and re.fullmatch(
            r"-?\d+", str(raw).strip()) else None
    return values


def expected_rows(payload: dict, faq: LoadPatternFaq, config: Config,
                  environment: str = "") -> list[ExpectedRow]:
    """``environment`` = which of dml.environments is being probed: its path
    prefix is what a path column holds THERE."""
    from codegen.emit.dml import cell_kind

    dml = config.dml
    variables = variable_values(faq, config)
    prefix = dml.env_path_prefix.get(environment, "")
    status = {c.upper() for c in dml.status_columns}
    manage_status = manages_row_status(faq)
    rows: list[ExpectedRow] = []
    for tab, content in payload.get("tabs", {}).items():
        table = config.framework.tables.get(tab, tab)
        key_columns = dml.natural_keys.get(tab)
        for index, row in enumerate(content.get("rows", [])):
            values: dict[str, str | None] = {}
            not_compared: list[str] = []
            status_columns: list[str] = []
            for header in content["headers"]:
                kind, literal = cell_kind(header, row["values"].get(header), config)
                if kind in ("variable", "connection"):
                    assigned = variables.get((literal or "").lstrip("@"))
                    if assigned is None:
                        not_compared.append(header)
                        continue
                    values[header] = assigned
                elif kind in ("audit_by", "audit_date", "identity", "multiline"):
                    not_compared.append(header)
                    continue
                elif kind == "path":
                    values[header] = f"{prefix}{literal}"
                else:  # active | claim_type | null | literal
                    values[header] = literal
                if header.upper() in status and not manage_status:
                    status_columns.append(header)
            natural_key: dict[str, str] = {}
            unkeyed: str | None = None
            if not key_columns:
                unkeyed = (f"no natural key is configured for {tab} (config dml.natural_keys) — "
                           "the row cannot be looked up")
            else:
                for column in key_columns:
                    value = values.get(column)
                    if value in (None, ""):
                        unkeyed = (f"natural key column {column} has no value at generation time "
                                   "(an unassigned script variable or a blank IIG cell) — the "
                                   "row cannot be looked up")
                        break
                    natural_key[column] = value
            rows.append(ExpectedRow(
                table=table, sheet=tab, row_index=index,
                natural_key={} if unkeyed else natural_key,
                values=values, not_compared=not_compared,
                status_columns=status_columns, unkeyed_reason=unkeyed))
    # A key shared by several rows of THIS feed identifies none of them: two
    # expected rows would be compared with the same environment row and one
    # of them would read `different` for no reason. (Pair 1: the FAQ supplies
    # ONE object_id for four file patterns, so DATA_QUALITY_RULES' rows share
    # keys — a real ambiguity of the IIG, reported, never papered over.)
    shared: dict[tuple, int] = {}
    for row in rows:
        if row.natural_key:
            marker = (row.table, tuple(sorted(row.natural_key.items())))
            shared[marker] = shared.get(marker, 0) + 1
    return [
        row if not row.natural_key
        or shared[(row.table, tuple(sorted(row.natural_key.items())))] == 1
        else row.model_copy(update={
            "natural_key": {},
            "unkeyed_reason": f"the natural key ({row.key_label}) is shared by "
                              f"{shared[(row.table, tuple(sorted(row.natural_key.items())))]} "
                              f"rows of this feed in {row.table} — it identifies none of them "
                              "(config dml.natural_keys)"})
        for row in rows]


# -- the hand-off file (the notebook fallback probes in-process, where spark
#    and dbutils exist; the CLI subprocesses have neither) --------------------- #


def expected_to_json(tables: list[ExpectedTable], rows: list[ExpectedRow]) -> str:
    return json.dumps({"tables": [t.model_dump() for t in tables],
                       "rows": [r.model_dump() for r in rows]},
                      indent=2, sort_keys=True) + "\n"


def expected_from_json(path: Path) -> tuple[list[ExpectedTable], list[ExpectedRow]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ([ExpectedTable.model_validate(t) for t in raw.get("tables", [])],
            [ExpectedRow.model_validate(r) for r in raw.get("rows", [])])
