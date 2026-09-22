"""DML deliverable for the SQL Server metadata DB (M7 §3).

From the SAME config rows that fill the IIG workbook, one T-SQL script per
environment — ``config_inserts_<env>.sql`` — plus a Databricks notebook
source that runs it over JDBC. Every rule here cites
``docs/acfc/METADATA_DB_SEMANTICS.md`` (the framework walkthrough):

* a **variables block** at the top — ``@RFC_NUMBER``, ``@PIPELINE_ID``,
  ``@PARENT_PIPELINE_ID``, ``@GROUP_ID``, ``@OBJECT_ID`` and one
  ``@<ROLE>`` per connection column — each with a comment saying who
  assigns it and the uniqueness rule; a FAQ answer fills the value, else
  ``NULL -- ASSIGN`` and a ``dml_unassigned:@<name>`` flag. Never a made-up
  id (§1, §2, §5);
* a **preflight** block — ``@PIPELINE_ID`` and ``@GROUP_ID`` unused, each
  connection lookup returns 0 or 1 rows — ``RAISERROR`` on violation, and
  the connection insert-or-reuse pattern capturing ``SCOPE_IDENTITY()`` (§3);
* one **INSERT per config row**, tables in the walkthrough's dependency
  order (§9), column lists explicit, ``CREATED_BY`` / ``UPDATED_BY`` =
  ``@RFC_NUMBER``, dates ``GETDATE()``, ``ACTIVE_FLAG`` = ``dml.active_flag``
  (§1 — 'S'), NULL / NA conventions per table (§2, §7), string literals
  escaped, NO line break inside a literal — a multi-line source value is a
  ``dml_multiline`` flag and a NULL, never a literal;
* per-environment variants differ only in the variables block (``@ENV``,
  ``@PATH_PREFIX``); path columns are rendered ``CONCAT(@PATH_PREFIX, …)``
  so the body is identical across environments;
* validation: every statement parses under sqlglot's ``tsql`` dialect when
  sqlglot is installed, else a structural check; the per-table row counts
  equal the IIG's.

Tables the walkthrough did not describe (§8) are still written from the
IIG cells under the §1 conventions, marked as such in the script.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.env.model import EnvProbeResult, ProbedObject
from codegen.faq import LoadPatternFaq
from codegen.gate.preflight import GateCheck

_SEMANTICS = "docs/acfc/METADATA_DB_SEMANTICS.md"
_AUDIT_BY = {"CREATED_BY", "UPDATED_BY", "CRETAED_BY"}          # the iig_v1 header typo is real
_AUDIT_DATE = {"CREATED_DATE", "UPDATED_DATE", "CREATED_AT", "UPDATED_AT"}
_ACTIVE = {"ACTIVE_FLAG", "ACTIVE_RULE_FLG"}
_ALWAYS_NULL = {"DAY_OF_SCHEDULE", "UDF2", "UDF3", "UDF4", "UDF5", "ESTIMATED_START_TIME",
                "COMPLETION_SLA", "RUNTIME_SLA", "CRITICAL_PROCESSING_PERIOD"}
_IDENTITY_COLUMNS = {"INVENTORY_ID", "TEMPLATE_ID", "CLUSTER_DETAILS_ID"}
_VARIABLE_COLUMNS = {"PIPELINE_ID": "@PIPELINE_ID", "PARENT_PIPELINE_ID": "@PARENT_PIPELINE_ID",
                     "GROUP_ID": "@GROUP_ID", "OBJECT_ID": "@OBJECT_ID"}


@dataclass(frozen=True)
class DmlArtefacts:
    files: list[Path]
    row_counts: dict[str, int]
    flags: list[str] = field(default_factory=list)
    checks: list[GateCheck] = field(default_factory=list)
    variables: dict[str, str | None] = field(default_factory=dict)   # name -> value or None


# ------------------------------------------------------------------- SQL bits


def _ident(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def _table(schema: str, name: str) -> str:
    return f"{_ident(schema)}.{_ident(name)}"


def _literal(value) -> str:
    text = str(value).replace("'", "''")
    return f"N'{text}'"


def _int_literal(value) -> str | None:
    text = str(value).strip()
    return text if re.fullmatch(r"-?\d+", text) else None


def _is_path_column(header: str, config: Config) -> bool:
    upper = header.upper()
    return any(upper.endswith(s.upper()) for s in config.gate.derivations.path_column_suffixes)


def _faq_value(faq: LoadPatternFaq, name: str) -> str | None:
    answer = getattr(faq, name, None)
    if answer is None or getattr(answer, "source", "unknown") == "unknown":
        return None
    return str(answer.value)


# ------------------------------------------------------------- variables block


def _variables(faq: LoadPatternFaq, config: Config, spec: ResolvedFeedSpec, env: str,
               flags: list[str]) -> tuple[list[str], dict[str, str | None]]:
    dml = config.dml
    lines: list[str] = [
        f"-- ENVIRONMENT = {env}",
        f"DECLARE @ENV NVARCHAR(16) = {_literal(env)};",
        f"DECLARE @PATH_PREFIX NVARCHAR(400) = {_literal(dml.env_path_prefix.get(env, ''))};"
        "  -- environment path prefix (config dml.env_path_prefix); path columns are "
        "CONCAT(@PATH_PREFIX, <path>)",
    ]
    values: dict[str, str | None] = {}
    for name, spec_ in dml.variables.items():
        value = _faq_value(faq, spec_.faq_field) if spec_.faq_field else None
        values[name] = value
        if value is None:
            rendered = "NULL"
            flags.append(f"dml_unassigned:@{name} — {spec_.assigned_by}; {spec_.rule} "
                         f"({_SEMANTICS}); answer FAQ {spec_.faq_field!r} or set it in the "
                         "notebook")
        elif spec_.sql_type.upper().startswith(("INT", "BIGINT", "SMALLINT")):
            rendered = _int_literal(value) or "NULL"
            if rendered == "NULL":
                flags.append(f"dml_unassigned:@{name} — FAQ value {value!r} is not an integer")
                values[name] = None
        else:
            rendered = _literal(value)
        marker = "" if values[name] is not None else "  -- ASSIGN"
        lines.append(f"DECLARE @{name} {spec_.sql_type} = {rendered};{marker}  "
                     f"-- assigned by: {spec_.assigned_by}; rule: {spec_.rule}")
    # one variable per connection role + the lookup keys of the source connection
    for role in dml.connection_roles:
        value = (faq.connection_ids or {}).get(role)
        values[role] = value
        rendered = _int_literal(value) if value is not None else None
        if rendered is None:
            values[role] = None
            flags.append(f"dml_unassigned:@{role} — identity value of the connection table; "
                         f"reused by host / root path or inserted (preflight); {_SEMANTICS} §3")
        lines.append(f"DECLARE @{role} INT = {rendered or 'NULL'};"
                     f"{'' if rendered else '  -- ASSIGN or leave NULL to look up / insert'}  "
                     "-- assigned by: identity (connection table); rule: reuse the existing "
                     "connection for the same host + root path, insert otherwise")
    host = _faq_value(faq, "source_host")
    root = spec.landing_location if spec.landing_location and "\n" not in spec.landing_location \
        else None
    values["SRC_HOST_NAME"] = host
    values["SRC_ROOT_PATH"] = root
    if host is None:
        flags.append("dml_unassigned:@SRC_HOST_NAME — platform / Azure team; the file "
                     f"connection's host ({_SEMANTICS} §3)")
    lines.append(f"DECLARE @SRC_HOST_NAME NVARCHAR(200) = {_literal(host) if host else 'NULL'};"
                 f"{'' if host else '  -- ASSIGN'}  -- assigned by: platform team; rule: the "
                 "connection is keyed by host + root path")
    if root:
        lines.append(f"DECLARE @SRC_ROOT_PATH NVARCHAR(400) = {_literal(root)};  -- source: FRD "
                     "ADLS Location / landing path")
    else:
        lines.append("DECLARE @SRC_ROOT_PATH NVARCHAR(400) = NULL;  -- ASSIGN  -- no FRD landing "
                     "path stated")
    return lines, values


# ------------------------------------------------------------------ preflight


def _preflight(config: Config, tables_present: set[str],
               env_present: frozenset[str] = frozenset(),
               env_assertions: tuple[str, ...] = (), rdbms: bool = False) -> list[str]:
    """``env_present`` (M10): tabs where the environment probe FOUND a row of
    this feed. There the "id must be unused" assertion would refuse the very
    state the probe reported — the id is in use BY that row — so it gives way
    to the expected-state assertions (``env_assertions``). Both empty = the
    block is byte for byte what it was before M10."""
    dml = config.dml
    schema = dml.schema
    conn = dml.connection_table
    lines = ["-- PREFLIGHT: engineer-assigned ids must be unused; a connection lookup "
             f"must return 0 or 1 rows ({_SEMANTICS} §1, §3, §5)",
             "IF @RFC_NUMBER IS NULL RAISERROR('RFC_NUMBER is not assigned (audit columns, "
             f"{_SEMANTICS} §1)', 16, 1);"]
    if "DATA_FACTORY_PIPELINE_SCHEDULE" in tables_present:
        lines.append("IF @PIPELINE_ID IS NULL RAISERROR('PIPELINE_ID is not assigned', 16, 1);")
        if "DATA_FACTORY_PIPELINE_SCHEDULE" in env_present:
            lines.append("-- ENVIRONMENT: the pipeline row exists (probe) — its PIPELINE_ID is "
                         "in use by that row; the unused-id assertion is replaced by the "
                         "expected-state assertions below")
        else:
            lines.append(
                f"IF EXISTS (SELECT 1 FROM {_table(schema, 'DATA_FACTORY_PIPELINE_SCHEDULE')} "
                "WHERE [PIPELINE_ID] = @PIPELINE_ID) RAISERROR('PIPELINE_ID %d is already used "
                "(unique per process)', 16, 1, @PIPELINE_ID);")
    group_tables = [t for t in ("FILE_ADLS_INGESTION_DETAILS", "ADLS_DELTA_INGESTION_DETAILS",
                                "STGDELTA_STDDELTA_INGESTION_DET") if t in tables_present
                    and not (rdbms and t in dml.file_source_tables)]
    if group_tables:
        lines.append("IF @GROUP_ID IS NULL RAISERROR('GROUP_ID is not assigned', 16, 1);")
        for t in group_tables:
            if t in env_present:
                lines.append(f"-- ENVIRONMENT: rows of this feed exist in {t} (probe) — the "
                             "GROUP_ID is in use by them; see the expected-state assertions")
                continue
            lines.append(f"IF EXISTS (SELECT 1 FROM {_table(schema, t)} WHERE [GROUP_ID] = "
                         f"@GROUP_ID) RAISERROR('GROUP_ID %d is already used in {t} (never "
                         "reused)', 16, 1, @GROUP_ID);")
    if env_assertions:
        lines.append("-- EXPECTED STATE (environment probe): this script was written against "
                     "what the probe found; it refuses to run if the metadata DB has changed")
        lines.extend(env_assertions)
    if rdbms:
        # M11 item 13: the FILE connection (host + root path) does not apply —
        # the source connection is an RDBMS connection (§4, not described).
        lines.append("-- REVIEW connection: the source is an RDBMS table; the FILE connection "
                     f"lookup does not apply and the RDBMS connection table ({_SEMANTICS} §4) "
                     "is not described — @SRC_CONNECTION_ID must be ASSIGNED by hand")
        if env_assertions:
            lines.append("-- EXPECTED STATE (environment probe): this script was written "
                         "against what the probe found; it refuses to run if the metadata DB "
                         "has changed")
            lines.extend(env_assertions)
        return lines
    lines += [
        "-- connection lookup (table / column identifiers as spoken in the walkthrough — "
        "confirm: dml_unconfirmed:connection_table)",
        "DECLARE @CONNECTION_MATCHES INT = 0;",
        f"SELECT @CONNECTION_MATCHES = COUNT(*) FROM {_table(schema, conn.name)} WHERE "
        f"{_ident(conn.host_column)} = @SRC_HOST_NAME AND {_ident(conn.root_column)} = "
        "@SRC_ROOT_PATH;",
        "IF @CONNECTION_MATCHES > 1 RAISERROR('more than one connection matches host + root "
        "path (expected 0 or 1)', 16, 1);",
        "IF @SRC_CONNECTION_ID IS NULL AND @SRC_HOST_NAME IS NOT NULL",
        "BEGIN",
        f"    SELECT @SRC_CONNECTION_ID = {_ident(conn.id_column)} FROM "
        f"{_table(schema, conn.name)} WHERE {_ident(conn.host_column)} = @SRC_HOST_NAME AND "
        f"{_ident(conn.root_column)} = @SRC_ROOT_PATH;",
        "    IF @SRC_CONNECTION_ID IS NULL",
        "    BEGIN",
        f"        INSERT INTO {_table(schema, conn.name)} ({_ident(conn.description_column)}, "
        f"{_ident(conn.host_column)}, {_ident(conn.root_column)}, "
        f"{_ident(conn.source_type_column)}, [CREATED_BY], [CREATED_DATE], [UPDATED_BY], "
        "[UPDATED_DATE]) VALUES (CONCAT(N'File connection for ', @SRC_ROOT_PATH), "
        "@SRC_HOST_NAME, @SRC_ROOT_PATH, N'File', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, "
        "GETDATE());",
        "        SET @SRC_CONNECTION_ID = SCOPE_IDENTITY();",
        "    END",
        "END",
    ]
    return lines


# ------------------------------------------------------------------- inserts


def cell_kind(header: str, value, config: Config) -> tuple[str, str | None]:
    """(kind, literal) for one IIG cell — THE precedence of the §1/§2/§7
    conventions. The INSERT renderer and the environment probe's expectations
    (codegen.env.expect) both read it, so the probe compares exactly what the
    script would write. Kinds: variable | connection | audit_by | audit_date |
    active | claim_type | identity | null | multiline | path | literal."""
    upper = header.upper()
    if upper in _VARIABLE_COLUMNS:
        return "variable", _VARIABLE_COLUMNS[upper]
    if upper in config.dml.connection_roles:
        return "connection", f"@{upper}"
    if upper in _AUDIT_BY:
        return "audit_by", None
    if upper in _AUDIT_DATE:
        return "audit_date", None
    if upper in _ACTIVE:
        return "active", config.dml.active_flag
    if upper == "CLAIM_TYPE_ID":
        return "claim_type", config.dml.claim_type_id_default
    if upper in _IDENTITY_COLUMNS:
        return "identity", None
    if upper in _ALWAYS_NULL or value in ("", None):
        return "null", None
    text = str(value)
    if "\n" in text or "\r" in text:
        return "multiline", None
    if _is_path_column(header, config):
        return "path", text
    return "literal", text


def _cell_sql(header: str, value, badge: str, tab: str, config: Config, flags: list[str],
              multiline: list[str]) -> str:
    """The SQL expression for one IIG cell, per the §1/§2/§7 conventions."""
    kind, literal = cell_kind(header, value, config)
    if kind in ("variable", "connection"):
        return str(literal)
    if kind == "audit_by":
        return "@RFC_NUMBER"
    if kind == "audit_date":
        return "GETDATE()"
    if kind == "multiline":
        flags.append(f"dml_multiline:{tab}.{header} — the IIG cell spans lines ({badge}); "
                     "written as NULL, never a literal")
        multiline.append(f"{tab}.{header}")
        return "NULL  /* dml_multiline */"
    if kind == "path":
        return f"CONCAT(@PATH_PREFIX, {_literal(literal)})"
    if literal is None:  # identity | null | an unset claim type
        return "NULL"
    return _literal(literal)


def _raiserror(message: str) -> str:
    """A RAISERROR literal: no format specifiers, quotes doubled, one line."""
    text = " ".join(message.split()).replace("%", "%%").replace("'", "''")
    return f"RAISERROR('{text[:400]}', 16, 1);"


def _equals(column: str, expression: str) -> str:
    return f"{_ident(column)} IS NULL" if expression.startswith("NULL") \
        else f"{_ident(column)} = {expression}"


def _differs(column: str, expression: str) -> str:
    return f"{_ident(column)} IS NOT NULL" if expression.startswith("NULL") \
        else f"({_ident(column)} <> {expression} OR {_ident(column)} IS NULL)"


@dataclass(frozen=True)
class _EnvAdjusted:
    """The probed environment's body + what the preflight needs to know."""

    lines: list[str]
    assertions: tuple[str, ...]
    present_tabs: frozenset[str]
    flags: list[str]


def _env_inserts(payload: dict, config: Config, result: EnvProbeResult) -> _EnvAdjusted:
    """The INSERT block adjusted to what the probe found, row by row.

    absent / unreadable / not probed -> the INSERT, exactly as without a probe.
    identical -> a comment, no statement. different -> a REVIEW block naming
    the natural key and both values of every differing column, with an UPDATE
    CANDIDATE that is commented out unless ``dml.emit_updates`` — the DML stays
    INSERT-only until the framework team confirms an update path exists
    (METADATA_DB_SEMANTICS §11 q19). Status columns are never part of any of
    it. Every probed row also gets an expected-state assertion.
    """
    dml = config.dml
    tables = payload.get("tabs", {})
    order = ([t for t in dml.table_order if t in tables]
             + [t for t in tables if t not in dml.table_order])
    lines: list[str] = []
    assertions: list[str] = []
    present: set[str] = set()
    flags: list[str] = []
    scratch: list[str] = []   # _cell_sql's flag sinks — already raised by _inserts
    for tab in order:
        rows = tables[tab].get("rows", [])
        if not rows:
            continue
        table = config.framework.tables.get(tab, tab)
        qualified = _table(dml.schema, table)
        described = tab in dml.described_tables
        headers = list(tables[tab]["headers"])
        states = [result.row(tab, i) for i in range(len(rows))]
        tally = {s: sum(1 for o in states if o is not None and o.state == s)
                 for s in ("absent", "identical", "different", "unreadable")}
        lines.append("")
        lines.append(f"-- {tab}: {len(rows)} row(s)"
                     + ("" if described else f" — table not yet described in the framework "
                                             f"walkthrough ({_SEMANTICS} §8); §1 conventions only"))
        lines.append(f"--   environment (probed {result.probed_at}): "
                     + ", ".join(f"{n} {s}" for s, n in tally.items() if n)
                     + ("" if described or not (tally["identical"] or tally["different"])
                        else " — natural key UNCONFIRMED for this table (config "
                             "dml.natural_keys; METADATA_DB_SEMANTICS §8, §11)"))
        statements = 0
        for index, row in enumerate(rows):
            expressions = {h: _cell_sql(h, row["values"].get(h),
                                        row["badges"].get(h, {}).get("badge", "?"),
                                        tab, config, scratch, scratch) for h in headers}
            insert = (f"INSERT INTO {qualified} ({', '.join(_ident(h) for h in headers)}) "
                      f"VALUES ({', '.join(expressions[h] for h in headers)});")
            probed: ProbedObject | None = states[index]
            if probed is None or probed.state == "unreadable":
                lines.append(insert)
                statements += 1
                continue
            where = " AND ".join(_equals(k, expressions[k]) for k in probed.natural_key)
            label = f"{table}[{', '.join(f'{k}={v}' for k, v in probed.natural_key.items())}]"
            if probed.state == "absent":
                lines.append(insert)
                statements += 1
                assertions.append(
                    f"IF EXISTS (SELECT 1 FROM {qualified} WHERE {where}) " + _raiserror(
                        f"environment changed since the probe: {label} was absent, now exists"))
                continue
            present.add(tab)
            if probed.state == "identical":
                lines.append(f"-- ENVIRONMENT identical: {label} exists and matches this row — "
                             "no statement (INSERT skipped)")
                same = " AND ".join([where, *(_equals(c, expressions[c])
                                              for c in probed.compared if c in expressions)])
                assertions.append(
                    f"IF NOT EXISTS (SELECT 1 FROM {qualified} WHERE {same}) " + _raiserror(
                        f"environment changed since the probe: {label} was identical to this "
                        "script, no longer"))
                continue
            # different
            differing = [d for d in probed.diffs if d.column in expressions]
            names = ", ".join(d.column for d in differing)
            lines.append(f"-- REVIEW {label}: exists and DIFFERS from this row — INSERT skipped")
            for d in differing:
                lines.append(f"--   {_ident(d.column)}: this script {expressions[d.column]} | "
                             "environment "
                             + ("NULL" if d.actual is None else _literal(d.actual)))
            sets = [f"{_ident(d.column)} = {expressions[d.column]}" for d in differing]
            if any(h.upper() == "UPDATED_BY" for h in headers):
                sets.append("[UPDATED_BY] = @RFC_NUMBER")
            if any(h.upper() == "UPDATED_DATE" for h in headers):
                sets.append("[UPDATED_DATE] = GETDATE()")
            update = f"UPDATE {qualified} SET {', '.join(sets)} WHERE {where};"
            if dml.emit_updates:
                lines.append("--   dml.emit_updates is ON: the framework team confirmed an "
                             "update path for config rows")
                lines.append(update)
                statements += 1
                held = " AND ".join([where, *(
                    f"{_ident(d.column)} IS NULL" if d.actual is None
                    else f"{_ident(d.column)} = {_literal(d.actual)}" for d in differing)])
                assertions.append(
                    f"IF NOT EXISTS (SELECT 1 FROM {qualified} WHERE {held}) " + _raiserror(
                        f"environment changed since the probe: {label} no longer holds the "
                        f"probed values of {names}"))
            else:
                lines.append("--   UPDATE candidate — NOT executed (dml.emit_updates is off: no "
                             "update path for config rows is confirmed by the framework team, "
                             f"{_SEMANTICS} §11 q19):")
                lines.append(f"--   {update}")
                still = " OR ".join(_differs(d.column, expressions[d.column]) for d in differing)
                assertions.append(
                    f"IF EXISTS (SELECT 1 FROM {qualified} WHERE {where} AND ({still})) "
                    + _raiserror(f"{label} still differs from this script in {names} — resolve "
                                 "the REVIEW block before running"))
            flags.append(f"dml_review:{label} — differs in {names}; "
                         + ("UPDATE emitted (dml.emit_updates)" if dml.emit_updates
                            else "INSERT skipped, UPDATE candidate commented out"))
        lines.append(f"SELECT {_literal(tab)} AS table_name, @@ROWCOUNT AS rows_inserted;"
                     if statements else
                     f"SELECT {_literal(tab)} AS table_name, 0 AS rows_inserted;  -- nothing to "
                     "do in this environment")
    return _EnvAdjusted(lines=lines, assertions=tuple(assertions),
                        present_tabs=frozenset(present), flags=flags)


def _rdbms_review(tab: str, rows: int) -> list[str]:
    return [
        f"-- REVIEW {tab}: the source is an RDBMS table (source_kind=rdbms), not a file —",
        f"--   this table describes a FILE source; its {rows} row(s) are not written. The",
        "--   framework's RDBMS connection table (§4) and RDBMS -> ADLS ingestion table (§6)",
        "--   are not described by the walkthrough, so no statement is generated for them",
        f"--   ({_SEMANTICS} §4, §6). Write these rows by hand once they are described.",
    ]


def _inserts(payload: dict, config: Config, flags: list[str],
             rdbms: bool = False) -> tuple[list[str], dict[str, int]]:
    dml = config.dml
    tables = payload.get("tabs", {})
    order = ([t for t in dml.table_order if t in tables]
             + [t for t in tables if t not in dml.table_order])
    lines: list[str] = []
    counts: dict[str, int] = {}
    multiline: list[str] = []
    for tab in order:
        rows = tables[tab].get("rows", [])
        if not rows:
            continue
        table = config.framework.tables.get(tab, tab)
        described = tab in dml.described_tables
        lines.append("")
        lines.append(f"-- {tab}: {len(rows)} row(s)"
                     + ("" if described else f" — table not yet described in the framework "
                                             f"walkthrough ({_SEMANTICS} §8); §1 conventions only"))
        if not described:
            flags.append(f"dml_not_described:{tab} — written from the IIG cells under the §1 "
                         f"conventions only ({_SEMANTICS} §8)")
        headers = list(tables[tab]["headers"])
        counts[tab] = len(rows)
        if rdbms and tab in dml.file_source_tables:
            # M11 item 13: the rows are ACCOUNTED FOR (the count stays the
            # IIG's) but not written — a REVIEW block says why.
            lines.extend(_rdbms_review(tab, len(rows)))
            flags.append(f"dml_rdbms_review:{tab} — {len(rows)} row(s) describe a file source; "
                         "the feed's source is an RDBMS table, so a REVIEW block is written "
                         f"instead ({_SEMANTICS} §4, §6 not described)")
            lines.append(f"SELECT {_literal(tab)} AS table_name, 0 AS rows_inserted;  -- REVIEW")
            continue
        for row in rows:
            values = [_cell_sql(h, row["values"].get(h), row["badges"].get(h, {}).get("badge", "?"),
                                tab, config, flags, multiline) for h in headers]
            lines.append(f"INSERT INTO {_table(dml.schema, table)} "
                         f"({', '.join(_ident(h) for h in headers)}) VALUES ({', '.join(values)});")
        lines.append(f"SELECT {_literal(tab)} AS table_name, @@ROWCOUNT AS rows_inserted;")
    return lines, counts


# ---------------------------------------------------------------- validation


def _strip_comment(line: str) -> str:
    """The line without its trailing ``--`` comment (a ``--`` inside a quoted
    literal is kept)."""
    in_quote = False
    for i, ch in enumerate(line):
        if ch == "'":
            in_quote = not in_quote
        elif not in_quote and line.startswith("--", i):
            return line[:i].rstrip()
    return line


def _statements(text: str) -> list[str]:
    """Top-level statements of the script: comments dropped, BEGIN / END
    lines are structure (balanced separately), everything else accumulates
    until a line ending in ';'."""
    statements: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = _strip_comment(raw.strip())
        if not line:
            continue
        if line in ("BEGIN", "END"):
            continue
        current.append(line)
        if line.endswith(";"):
            statements.append(" ".join(current))
            current = []
    if current:
        statements.append(" ".join(current))
    return statements


def validate_tsql(text: str) -> list[str]:
    """Parse problems, statement by statement, under sqlglot's tsql dialect —
    a statement sqlglot can only keep as a raw ``Command`` counts as a
    problem, so the check is real, not a fallback. Without sqlglot: a
    structural check (balanced quotes / parentheses / BEGIN-END)."""
    problems: list[str] = []
    stripped = [_strip_comment(ln.strip()) for ln in text.splitlines()]
    if stripped.count("BEGIN") != stripped.count("END"):
        problems.append(f"BEGIN/END unbalanced ({stripped.count('BEGIN')} vs "
                        f"{stripped.count('END')})")
    body = "\n".join(ln for ln in stripped if ln)
    if body.replace("''", "").count("'") % 2:
        problems.append("unbalanced single quotes")
    if body.count("(") != body.count(")"):
        problems.append("unbalanced parentheses")
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError:  # pragma: no cover — the structural fallback above is the check
        return problems
    for statement in _statements(text):
        try:
            parsed = sqlglot.parse(statement, read="tsql")
        except Exception as exc:  # noqa: BLE001 — the parser's message IS the finding
            problems.append(f"sqlglot tsql: {statement[:80]!r}: {str(exc)[:160]}")
            continue
        for node in parsed:
            if node is None or isinstance(node, exp.Command):
                problems.append(f"sqlglot tsql: {statement[:80]!r}: not recognised as a "
                                "statement (parsed as a raw command)")
    return problems


# -------------------------------------------------------------------- notebook


def _notebook_source(env: str, sql_name: str, variables: dict[str, str | None],
                     config: Config) -> str:
    from codegen.emit.emitter import _environment

    template = _environment().get_template("framework/insert_scripts_notebook.py.j2")
    return template.render(env=env, sql_name=sql_name, variables=sorted(variables),
                           int_variables=sorted(n for n in variables if n not in
                                                ("RFC_NUMBER", "SRC_HOST_NAME", "SRC_ROOT_PATH")),
                           secret_scope=config.dml.secret_scope,
                           jdbc_url_secret=config.dml.jdbc_url_secret,
                           user_secret=config.dml.user_secret,
                           password_secret=config.dml.password_secret,
                           semantics=_SEMANTICS)


# ------------------------------------------------------------------------ emit


def emit_dml(spec: ResolvedFeedSpec, faq: LoadPatternFaq, payload: dict, config: Config,
             framework_dir: Path, banner: list[tuple[str, str]],
             env_probe: EnvProbeResult | None = None,
             probed_environment: str = "") -> DmlArtefacts:
    """``env_probe`` (M10) adjusts ONLY the script of ``probed_environment`` —
    a probe sees one metadata DB, and what it found says nothing about the
    others. When it found no row of this feed (all absent / unreadable) that
    script too is byte for byte what it is without a probe."""
    dml = config.dml
    files: list[Path] = []
    flags: list[str] = []
    checks: list[GateCheck] = []
    row_counts: dict[str, int] = {}
    variables: dict[str, str | None] = {}
    flags.append(f"dml_unconfirmed:connection_table — table / column identifiers "
                 f"{dml.connection_table.name}({dml.connection_table.id_column}, "
                 f"{dml.connection_table.host_column}, {dml.connection_table.root_column}) are "
                 f"as spoken in the walkthrough, not printed; confirm before running "
                 f"({_SEMANTICS} §3)")
    rdbms = getattr(spec, "source_kind", None) == "rdbms"
    inserts, row_counts = _inserts(payload, config, flags, rdbms=rdbms)
    adjusted: _EnvAdjusted | None = None
    if env_probe is not None and probed_environment in dml.environments and any(
            o.kind == "config_row" and o.state in ("identical", "different")
            for o in env_probe.objects):
        adjusted = _env_inserts(payload, config, env_probe)
        flags.extend(adjusted.flags)
    for env in dml.environments:
        env_flags: list[str] = []
        var_lines, variables = _variables(faq, config, spec, env, env_flags)
        if env == dml.environments[0]:
            flags.extend(env_flags)
        header = [
            f"-- TARGET SYSTEM = SQL Server metadata DB ({dml.schema} config tables)",
            "-- RUN FROM = Databricks notebook (Insert_scripts_config_table_<env>.py) over JDBC, "
            "in one transaction",
            f"-- GENERATED by codegen-data-engineer-agent for feed {spec.feed_slug}; rules: "
            f"{_SEMANTICS}",
            *[f"-- {key}: {value}" for key, value in banner if key != "Layout"],
            f"-- ACTIVE_FLAG is written as {_literal(dml.active_flag)} (walkthrough §1); the "
            "review workbooks show the golden's value — see METADATA_DB_SEMANTICS §10",
            *([f"-- ENVIRONMENT STATE = adjusted to the read-only probe of {env} at "
               f"{env_probe.probed_at}; the other environments' scripts are NOT adjusted"]
              if adjusted is not None and env_probe is not None and env == probed_environment
              else []),
            "SET NOCOUNT ON;",
            "",
            "-- VARIABLES (this block is the only part that differs per environment)",
            *var_lines,
            "",
            *(_preflight(config, set(row_counts), adjusted.present_tabs, adjusted.assertions,
                         rdbms=rdbms)
              if adjusted is not None and env == probed_environment
              else _preflight(config, set(row_counts), rdbms=rdbms)),
            *(adjusted.lines if adjusted is not None and env == probed_environment
              else inserts),
            "",
        ]
        text = "\n".join(header)
        path = framework_dir / dml.file_name_pattern.format(env=env)
        path.write_text(text, encoding="utf-8", newline="\n")
        files.append(path)
        problems = validate_tsql(text)
        checks.append(GateCheck(name=f"dml_parse_{env}", passed=not problems,
                                details="; ".join(problems) if problems
                                else f"{path.name}: every statement parses (tsql)"))
        notebook = framework_dir / dml.notebook_file_name_pattern.format(env=env)
        notebook.write_text(_notebook_source(env, path.name, variables, config),
                            encoding="utf-8", newline="\n")
        files.append(notebook)
    iig_counts = {name: len(tab.get("rows", [])) for name, tab in payload.get("tabs", {}).items()
                  if tab.get("rows")}
    checks.append(GateCheck(name="dml_row_counts", passed=row_counts == iig_counts,
                            details=(f"DML rows per table equal the IIG's: {row_counts}"
                                     if row_counts == iig_counts
                                     else f"DML {row_counts} != IIG {iig_counts}")))
    return DmlArtefacts(files=files, row_counts=row_counts, flags=flags, checks=checks,
                        variables=variables)


__all__ = ["DmlArtefacts", "emit_dml", "validate_tsql"]
