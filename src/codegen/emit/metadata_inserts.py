"""``framework/metadata_inserts.sql`` — the metadata rows that DEFINE the feed's
tables and pipelines in the SQL Server metadata DB (multi-table step 6).

At this client "DDL" means these INSERT rows: the framework creates the Unity
Catalog Delta tables FROM them (docs/acfc/MULTI_TABLE_DESIGN.md rule 8); the
``CREATE TABLE`` text (``<FEED>_DDL.txt``) stays as a reference artefact. The
script is rendered from THE SAME CELL VALUES the IIG workbook carries — the
payload ``codegen.metadata_sheet.metadata_sheet_payload`` built once per feed
(``emit_framework``) — so the IIG, ``config_rows.xlsx`` and this file can never
disagree. Written on EVERY framework run (2026-10-08); it replaces the retired
per-environment ``config_inserts_<env>.sql``, whose DB-side knowledge it
carries (``config dml.*``, docs/acfc/METADATA_DB_SEMANTICS.md):

1. **One block per IIG sheet**, in ``dml.table_order`` order, then any other
   sheet in payload order. Table ``[<dml.schema>].[<framework.tables[sheet]
   or sheet>]``, identifiers bracketed. Each block opens with
   ``-- <SHEET>: <n> row(s)`` (a table the walkthrough did not describe says
   so, flag ``dml_not_described:<SHEET>``); a sheet with no rows gets its
   header line only.
2. **One** ``INSERT INTO … (<columns>) VALUES (…);`` **per payload row**, the
   columns in the sheet's header order, one statement per line.
3. **Cells** — the workbook keeps what humans hand over; the script writes
   what the framework reads:
   * a column in ``dml.db_null_columns`` is ``NULL`` whatever the workbook
     holds (§2 "not populating", §7 CLAIM_TYPE_ID);
   * a non-blank value is a quoted ``N'…'`` literal (``'`` doubled), mapped
     through ``dml.db_value_map`` first (ACTIVE_FLAG ``'Y'`` -> ``'S'``, §1 /
     §10 — unconfirmed); a line break never sits inside a literal: it is
     written ``N'a' + NCHAR(10) + N'b'`` (lossless, on the statement's line);
   * a blank cell DECIDED blank (``badge_entry.deliberate_blank``) is ``NULL``;
   * a blank cell in ``dml.db_blank_expressions`` is that expression
     (``CREATED_DATE`` / ``UPDATED_DATE`` -> ``GETDATE()``, §1);
   * a blank ``CREATED_BY`` / ``UPDATED_BY`` is ``@RFC_NUMBER`` (one variable,
     §1); a blank ``FILE_ADLS_INGESTION_DETAILS.SRC_CONNECTION_ID`` is
     ``@SRC_CONNECTION_ID`` (looked up / inserted, §3);
   * any other blank cell is OPEN: a NAMED PLACEHOLDER, unquoted —
     ``<<COLUMN#n>>``, ``n`` = the row's 1-based number in its sheet (the
     variables' own: ``<<RFC_NUMBER>>``, ``<<SRC_HOST_NAME>>``) — so the
     script does not parse, let alone run, until the engineer replaces every
     one. One placeholder per row is what fixes the retired script's single
     ``@OBJECT_ID`` / ``@PIPELINE_ID`` for every row.
4. **Atomic.** ``SET XACT_ABORT ON`` + ``BEGIN TRY`` / ``BEGIN TRANSACTION`` …
   ``COMMIT`` / ``BEGIN CATCH`` ``ROLLBACK`` + ``THROW``: a failed guard or
   insert aborts the whole script, never a half insert.
5. **Guards, before the first INSERT** (§1, §2, §3, §5): ``@RFC_NUMBER`` set;
   every schedule row's ``PIPELINE_ID`` unused; every ingestion row's
   ``GROUP_ID`` unused in its table ("never reused") and its key
   (``GROUP_ID``, ``OBJECT_ID``, ``PIPELINE_ID``) unused; the source
   connection looked up by host + root path — 0 rows = insert it and take
   ``SCOPE_IDENTITY()``, 1 = reuse it, more = abort (identifiers as spoken in
   the walkthrough: flag ``dml_unconfirmed:connection_table``).
6. **Catalogs** are written as the cells carry them: already MAPPED by
   ``conventions.catalog_map`` in the resolver.
7. **Table definitions, by mapped three-part name.** A ``-- TABLE
   DEFINITIONS`` index lists every table the feed defines with its stage and
   standard definitions (``emit.framework.table_definitions``, the CREATE
   text's derivation); ADLS rows are labelled ``-- table <stage> <- file
   <pattern>``, STGDELTA rows ``-- table <src> -> <tgt>``.

The file is byte-stable (no timestamps). Gate check ``metadata_inserts``: the
per-sheet statement counts equal the IIG's and, with every placeholder read
as ``NULL``, every statement parses as T-SQL (``emit.dml.validate_tsql``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.emit.dml import _ident, _table, validate_tsql
from codegen.gate.preflight import GateCheck

if TYPE_CHECKING:  # pragma: no cover — type hints only (framework imports this module)
    from codegen.emit.framework import TableDefinition

FILE_NAME = "metadata_inserts.sql"
PLACEHOLDER_RE = re.compile(r"<<[A-Za-z0-9_]+(?:#\d+)?>>")
_DESIGN = "docs/acfc/MULTI_TABLE_DESIGN.md"
_SEMANTICS = "docs/acfc/METADATA_DB_SEMANTICS.md"
_ADLS = "ADLS_DELTA_INGESTION_DETAILS"
_STGDELTA = "STGDELTA_STDDELTA_INGESTION_DET"
_FILE_ADLS = "FILE_ADLS_INGESTION_DETAILS"
_SCHEDULE = "DATA_FACTORY_PIPELINE_SCHEDULE"
_GROUP_TABLES = (_FILE_ADLS, _ADLS, _STGDELTA)
_AUDIT_BY = {"CREATED_BY", "UPDATED_BY", "CRETAED_BY"}          # the iig_v1 header typo is real
_CONNECTION = (_FILE_ADLS, "SRC_CONNECTION_ID")


@dataclass(frozen=True)
class DbRules:
    """The DB-side cell rules (``config dml.*``); ``none()`` = plain cells."""

    value_map: dict[str, dict[str, str]] = field(default_factory=dict)
    blank_expressions: dict[str, str] = field(default_factory=dict)
    null_columns: frozenset[str] = frozenset()
    variables: bool = False          # audit-by -> @RFC_NUMBER, the connection -> its variable

    @classmethod
    def none(cls) -> DbRules:
        return cls()

    @classmethod
    def from_config(cls, config: Config) -> DbRules:
        dml = config.dml
        return cls(value_map={k.upper(): v for k, v in dml.db_value_map.items()},
                   blank_expressions={k.upper(): v for k, v in dml.db_blank_expressions.items()},
                   null_columns=frozenset(c.upper() for c in dml.db_null_columns),
                   variables=True)


@dataclass(frozen=True)
class MetadataInserts:
    path: Path
    row_counts: dict[str, int]
    check: GateCheck
    flags: list[str] = field(default_factory=list)


def placeholder(column: str, row_number: int) -> str:
    """The named placeholder of an open cell: ``<<COLUMN#n>>``."""
    return f"<<{column}#{row_number}>>"


def _literal(text: str) -> str:
    """``N'…'``; a line break becomes ``+ NCHAR(10) +`` (13 for ``\\r``)."""
    parts = []
    for piece in re.split(r"(\r|\n)", text):
        if piece == "\n":
            parts.append("NCHAR(10)")
        elif piece == "\r":
            parts.append("NCHAR(13)")
        elif piece:
            parts.append("N'" + piece.replace("'", "''") + "'")
    return " + ".join(parts)


def _blank(value) -> bool:
    return value is None or value == ""


def cell_sql(column: str, value, entry: dict, row_number: int, rules: DbRules | None = None,
             sheet: str | None = None) -> str:
    """One IIG cell as a VALUES item (module docstring, rule 3)."""
    rules = rules or DbRules.none()
    upper = column.upper()
    if upper in rules.null_columns:
        return "NULL"
    if not _blank(value):
        text = str(value)
        mapped = rules.value_map.get(upper, {}).get(text.strip())
        return _literal(mapped if mapped is not None else text)
    if (entry or {}).get("deliberate_blank"):
        return "NULL"
    if upper in rules.blank_expressions:
        return rules.blank_expressions[upper]
    if rules.variables and upper in _AUDIT_BY:
        return "@RFC_NUMBER"
    if rules.variables and (sheet, upper) == _CONNECTION:
        return "@SRC_CONNECTION_ID"
    return placeholder(column, row_number)


def _sheet_order(payload: dict, config: Config) -> list[str]:
    tabs = payload.get("tabs", {})
    order = config.dml.table_order
    return [t for t in order if t in tabs] + [t for t in tabs if t not in order]


def _one_line(text) -> str:
    return " ".join(str(text).split())


def _index_lines(definitions: list[TableDefinition]) -> list[str]:
    lines = [
        "-- TABLE DEFINITIONS — every table this feed defines (one per distinct stage "
        "catalog.schema.table), by its MAPPED three-part name; reference only: the framework "
        "creates the Unity Catalog Delta tables from the rows below.",
    ]
    total = len(definitions)
    for number, definition in enumerate(definitions, start=1):
        segments = ", ".join(definition.segments) or "-"
        lines.append(f"-- table {number} of {total} (segments: {segments})")
        for block in (definition.stage, definition.standard):
            if block is None:
                lines.append("--   standard (none: no Standard band / standard table)")
                continue
            lines.append(f"--   {block.layer:<8} {block.label} — {len(block.business)} "
                         f"column(s) + {len(block.audit)} audit")
            lines.extend(f"--     {name} {dtype}" for name, dtype in block.columns)
    return lines


def _adls_label(values: dict, definitions: list[TableDefinition]) -> str:
    schema, table = values.get("TGT_DATABASE_NAME") or "", values.get("TGT_TABLE_NAME") or ""
    match = next((d.stage for d in definitions
                  if d.stage.table.table == table and d.stage.table.schema_name == schema), None)
    name = match.label if match is not None else ".".join(p for p in (schema, table) if p) or "?"
    return f"-- table {name} <- file {values.get('SRC_FILE_NAME') or '?'}"


def _stgdelta_label(values: dict) -> str:
    def three(prefix: str) -> str:
        return ".".join(values.get(f"{prefix}_{part}") or "?"
                        for part in ("CATALOG_NAME", "SCHEMA_NAME", "TABLE_NAME"))

    return f"-- table {three('SRC')} -> {three('TGT')}"


def _faq_value(faq, name: str) -> str | None:
    answer = getattr(faq, name, None) if faq is not None else None
    if answer is None or getattr(answer, "source", "unknown") == "unknown":
        return None
    text = str(answer.value).strip() if answer.value is not None else ""
    return text or None


# Columns whose workbook value and walkthrough value disagree (§10): the SQL
# follows the walkthrough, the header names the Friday checklist item.
_UNCONFIRMED = {
    "ACTIVE_FLAG": "the goldens print 'Y', §1 says the framework selects 'S' — "
                   "UNCONFIRMED, Friday checklist 9",
    "ACTIVE_RULE_FLG": "the same assumption as ACTIVE_FLAG — UNCONFIRMED, Friday checklist 9",
    "DAY_OF_SCHEDULE": "the pair-1 golden prints 0, §2 / §10 say NULL — UNCONFIRMED, "
                       "Friday checklist 10",
}


def _db_value_lines(config: Config) -> list[str]:
    """The three workbook -> database rules, as the script header states them."""
    dml = config.dml
    lines = [f"-- WORKBOOK -> DATABASE — three rules ({_SEMANTICS}; config dml.*). The IIG "
             "workbook keeps what humans hand over; this script writes what the framework "
             "reads. Every other cell is the workbook's value as is.",
             "--   RULE 1 — value map (dml.db_value_map): a workbook value the database "
             "spells differently"]
    for column, mapping in dml.db_value_map.items():
        pairs = ", ".join(f"{k!r} -> {v!r}" for k, v in mapping.items())
        note = _UNCONFIRMED.get(column.upper())
        lines.append(f"--     {column}: workbook {pairs}" + (f" ({note})" if note else ""))
    lines.append("--   RULE 2 — forced NULL (dml.db_null_columns): columns the framework fills "
                 "itself / does not use today, NULL whatever the workbook holds (§2 'not "
                 "populating … future purpose', §7): " + ", ".join(dml.db_null_columns))
    for column in dml.db_null_columns:
        note = _UNCONFIRMED.get(column.upper())
        if note:
            lines.append(f"--     {column}: {note}")
    audit = [f"{column} blank -> {expression}"
             for column, expression in dml.db_blank_expressions.items()]
    lines.append("--   RULE 3 — audit defaults and open cells: "
                 + "; ".join([*audit, "CREATED_BY / UPDATED_BY blank -> @RFC_NUMBER"])
                 + f" (§1); {_CONNECTION[0]}.{_CONNECTION[1]} blank -> @SRC_CONNECTION_ID "
                 "(§3); any other OPEN cell -> its <<COLUMN#n>> placeholder (fill before "
                 "running); a cell decided blank -> NULL")
    return lines


def _guards(schema: str, rendered: dict[str, list[tuple[int, dict[str, str]]]],
            rfc: bool) -> list[str]:
    """EXISTS guards before the first INSERT (module docstring, rule 5)."""
    lines = [f"-- GUARDS — checked before the first INSERT; any failure aborts the whole "
             f"script and rolls it back ({_SEMANTICS} §1, §2, §5)"]
    if rfc:
        lines.append("IF @RFC_NUMBER IS NULL RAISERROR(N'RFC_NUMBER is not assigned (audit "
                     "columns, §1)', 16, 1);")
    seen: set[str] = set()

    def add(line: str) -> None:
        if line not in seen:
            seen.add(line)
            lines.append(line)

    def assigned(sheet: str, number: int, items: dict[str, str], *columns: str) -> None:
        # the retired script's "IS NULL" checks, per placeholder: an id filled
        # in as NULL aborts instead of reaching the INSERT
        for column in columns:
            value = items.get(column, "")
            if value.startswith("<<"):
                add(f"IF {value} IS NULL RAISERROR(N'{sheet} row {number}: {column} is not "
                    "assigned', 16, 1);")

    for number, items in rendered.get(_SCHEDULE, []):
        assigned(_SCHEDULE, number, items, "PIPELINE_ID")
        if "PIPELINE_ID" in items:
            add(f"IF EXISTS (SELECT 1 FROM {_table(schema, _SCHEDULE)} WHERE [PIPELINE_ID] = "
                f"{items['PIPELINE_ID']}) RAISERROR(N'{_SCHEDULE} row {number}: PIPELINE_ID is "
                "already used (unique per process, §2)', 16, 1);")
    for sheet in _GROUP_TABLES:
        for number, items in rendered.get(sheet, []):
            table = _table(schema, sheet)
            assigned(sheet, number, items, "GROUP_ID", "OBJECT_ID", "PIPELINE_ID")
            if "GROUP_ID" in items:
                add(f"IF EXISTS (SELECT 1 FROM {table} WHERE [GROUP_ID] = {items['GROUP_ID']}) "
                    f"RAISERROR(N'{sheet} row {number}: GROUP_ID is already used (never "
                    "reused, §5)', 16, 1);")
            if all(k in items for k in ("GROUP_ID", "OBJECT_ID", "PIPELINE_ID")):
                add(f"IF EXISTS (SELECT 1 FROM {table} WHERE [GROUP_ID] = {items['GROUP_ID']} "
                    f"AND [OBJECT_ID] = {items['OBJECT_ID']} AND [PIPELINE_ID] = "
                    f"{items['PIPELINE_ID']}) RAISERROR(N'{sheet} row {number}: the key "
                    "(GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);")
    return lines


def _connection_lines(config: Config) -> list[str]:
    """The source connection's reuse-or-insert lookup (§3) — the retired
    script's block, verbatim in shape."""
    schema, conn = config.dml.schema, config.dml.connection_table
    return [
        "-- CONNECTION LOOKUP (§3; table / column identifiers as spoken in the walkthrough — "
        "confirm: dml_unconfirmed:connection_table): 0 rows = insert and take its identity, "
        "1 = reuse, more = abort",
        "DECLARE @CONNECTION_MATCHES INT = 0;",
        f"SELECT @CONNECTION_MATCHES = COUNT(*) FROM {_table(schema, conn.name)} WHERE "
        f"{_ident(conn.host_column)} = @SRC_HOST_NAME AND {_ident(conn.root_column)} = "
        "@SRC_ROOT_PATH;",
        "IF @CONNECTION_MATCHES > 1 RAISERROR(N'more than one connection matches host + root "
        "path (expected 0 or 1)', 16, 1);",
        # the retired script skipped the lookup on a NULL host and left the id
        # NULL; here a NULL host with no id aborts (a connection row keyed by
        # a NULL host is never inserted)
        "IF @SRC_CONNECTION_ID IS NULL AND @SRC_HOST_NAME IS NULL RAISERROR(N'SRC_HOST_NAME "
        "is not assigned and no SRC_CONNECTION_ID is given (§3)', 16, 1);",
        "IF @SRC_CONNECTION_ID IS NULL",
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


def render_metadata_inserts(spec: ResolvedFeedSpec, payload: dict,
                            definitions: list[TableDefinition], config: Config,
                            banner: list[tuple[str, str]], ddl_name: str | None = None,
                            faq=None, flags: list[str] | None = None,
                            ) -> tuple[str, dict[str, int]]:
    """The script text and the INSERT count per sheet (``flags`` collects the
    dml_* flags)."""
    flags = flags if flags is not None else []
    schema = config.dml.schema
    rules = DbRules.from_config(config)
    tabs = payload.get("tabs", {})
    order = _sheet_order(payload, config)

    rendered: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for sheet in order:
        tab = tabs[sheet]
        rendered[sheet] = [
            (number, {h: cell_sql(h, row["values"].get(h), row["badges"].get(h) or {}, number,
                                  rules, sheet) for h in tab["headers"]})
            for number, row in enumerate(tab.get("rows", []), start=1)]
    used = {v for rows in rendered.values() for _n, items in rows for v in items.values()}
    connection_used = "@SRC_CONNECTION_ID" in used
    # The connection insert stamps its own audit columns with @RFC_NUMBER too.
    rfc_used = "@RFC_NUMBER" in used or connection_used

    reference = f"`{ddl_name}`" if ddl_name else "the CREATE reference text"
    lines = [
        f"-- {FILE_NAME} — feed {spec.feed_slug}",
        f"-- TARGET SYSTEM = SQL Server metadata DB ({schema} config tables): the rows that "
        f"DEFINE this feed's tables and pipelines — the client's \"DDL\" ({_DESIGN} rule 8). "
        f"The framework creates the Unity Catalog Delta tables from them; {reference} is the "
        "CREATE reference. It replaces the retired config_inserts_<env>.sql.",
        "-- SOURCE = the same cells as the IIG workbook (config_rows.xlsx / the clean IIG "
        "copy), with the DB values below; nothing else is derived.",
        "-- <<COLUMN#n>> = an OPEN cell (row n of that sheet): replace every one before "
        "running — the script does not parse until then. NULL = a cell decided blank.",
        "-- RUN = one transaction: any guard or insert that fails rolls back everything.",
        *[f"-- {key}: {_one_line(value)}" for key, value in banner if key != "Layout"],
        *_db_value_lines(config),
        "",
        *_index_lines(definitions),
        "",
        "SET NOCOUNT ON;",
        "SET XACT_ABORT ON;",
        "BEGIN TRY",
        "BEGIN TRANSACTION;",
    ]
    if rfc_used or connection_used:
        lines += ["", "-- VARIABLES"]
    rfc = _faq_value(faq, "rfc_number")
    if rfc_used:
        value = _literal(f"RFC{rfc}") if rfc else "<<RFC_NUMBER>>"
        lines.append(f"DECLARE @RFC_NUMBER NVARCHAR(50) = {value};  -- the RFC / ATMT ticket: "
                     "CREATED_BY / UPDATED_BY of every row (§1)")
        if not rfc:
            flags.append("dml_unassigned:@RFC_NUMBER — the engineer (the RFC / ATMT ticket); "
                         f"answer FAQ 'rfc_number' or fill <<RFC_NUMBER>> ({_SEMANTICS} §1)")
    if connection_used:
        host = _faq_value(faq, "source_host")
        stated = str((getattr(faq, "connection_ids", None) or {}).get(_CONNECTION[1], "")).strip()
        known = stated if re.fullmatch(r"-?\d+", stated) else None
        root = spec.landing_location if spec.landing_location and \
            "\n" not in spec.landing_location else None
        lines += [
            f"DECLARE @SRC_HOST_NAME NVARCHAR(200) = "
            f"{_literal(host) if host else '<<SRC_HOST_NAME>>'};  -- platform team: the file "
            "connection's host (§3)",
            f"DECLARE @SRC_ROOT_PATH NVARCHAR(400) = "
            f"{_literal(root) if root else '<<SRC_ROOT_PATH>>'};  -- the FRD landing path",
            f"DECLARE @SRC_CONNECTION_ID INT = {known if known else 'NULL'};  -- set to reuse a "
            "known connection id (FAQ connection_ids); NULL = looked up by host + root path, "
            "inserted when absent",
        ]
        if not host:
            flags.append("dml_unassigned:@SRC_HOST_NAME — platform / Azure team; the file "
                         f"connection's host ({_SEMANTICS} §3); answer FAQ 'source_host' or "
                         "fill <<SRC_HOST_NAME>>")
    lines += ["", *_guards(schema, rendered, rfc_used)]
    if connection_used:
        flags.append(f"dml_unconfirmed:connection_table — table / column identifiers "
                     f"{config.dml.connection_table.name}({config.dml.connection_table.id_column}, "
                     f"{config.dml.connection_table.host_column}, "
                     f"{config.dml.connection_table.root_column}) are as spoken in the "
                     f"walkthrough, not printed; confirm before running ({_SEMANTICS} §3)")
        lines += _connection_lines(config)

    counts: dict[str, int] = {}
    for sheet in order:
        tab = tabs[sheet]
        rows = tab.get("rows", [])
        headers = list(tab["headers"])
        table = _table(schema, config.framework.tables.get(sheet, sheet))
        columns = ", ".join(_ident(h) for h in headers)
        described = sheet in config.dml.described_tables
        lines += ["", f"-- {sheet}: {len(rows)} row(s)"
                  + ("" if described else f" — table not yet described in the framework "
                                          f"walkthrough ({_SEMANTICS} §8); §1 conventions only")]
        if rows and not described:
            flags.append(f"dml_not_described:{sheet} — written from the IIG cells under the §1 "
                         f"conventions only ({_SEMANTICS} §8)")
        for (_number, items), row in zip(rendered[sheet], rows, strict=True):
            values = row["values"]
            if sheet == _ADLS:
                lines.append(_adls_label(values, definitions))
            elif sheet == _STGDELTA:
                lines.append(_stgdelta_label(values))
            lines.append(f"INSERT INTO {table} ({columns}) VALUES "
                         f"({', '.join(items[h] for h in headers)});")
        counts[sheet] = len(rows)
    lines += [
        "",
        "COMMIT TRANSACTION;",
        "END TRY",
        "BEGIN CATCH",
        "IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;",
        "THROW;",
        "END CATCH;",
        "",
    ]
    return "\n".join(lines), counts


def placeholders_as_null(text: str) -> str:
    """The script with every open-cell placeholder read as NULL (validation)."""
    return PLACEHOLDER_RE.sub("NULL", text)


def emit_metadata_inserts(spec: ResolvedFeedSpec, payload: dict,
                          definitions: list[TableDefinition], config: Config,
                          framework_dir: Path, banner: list[tuple[str, str]],
                          ddl_name: str | None = None, faq=None) -> MetadataInserts:
    flags: list[str] = []
    text, counts = render_metadata_inserts(spec, payload, definitions, config, banner,
                                           ddl_name=ddl_name, faq=faq, flags=flags)
    path = framework_dir / FILE_NAME
    path.write_text(text, encoding="utf-8", newline="\n")
    iig_counts = {name: len(tab.get("rows", [])) for name, tab in payload.get("tabs", {}).items()}
    problems = validate_tsql(placeholders_as_null(text))
    if counts != iig_counts:
        problems.append(f"INSERTs per sheet {counts} != IIG rows {iig_counts}")
    check = GateCheck(
        name="metadata_inserts", passed=not problems,
        details="; ".join(problems) if problems else
        f"{FILE_NAME}: one INSERT per IIG row ({sum(counts.values())}); every statement "
        "parses (tsql) with the open-cell placeholders read as NULL")
    return MetadataInserts(path=path, row_counts=counts, check=check, flags=flags)


__all__ = ["FILE_NAME", "PLACEHOLDER_RE", "DbRules", "MetadataInserts", "cell_sql",
           "emit_metadata_inserts", "placeholder", "placeholders_as_null",
           "render_metadata_inserts"]
