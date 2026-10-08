"""``framework/metadata_inserts.sql`` — the metadata rows that DEFINE the feed's
tables and pipelines in the SQL Server metadata DB (multi-table step 6).

At this client "DDL" means these INSERT rows: the framework creates the Unity
Catalog Delta tables FROM them (docs/acfc/MULTI_TABLE_DESIGN.md rule 8); the
``CREATE TABLE`` text (``<FEED>_DDL.txt``) stays as a reference artefact. The
script is rendered from THE SAME CELL VALUES the IIG workbook carries — the
payload ``codegen.metadata_sheet.metadata_sheet_payload`` built once per feed
(``emit_framework``) — so the IIG, ``config_rows.xlsx`` and this file can never
disagree; nothing here derives a value. ``config_inserts_<env>.sql``
(``emit/dml.py``, the variables / preflight / per-environment runner script) is
a separate artefact and is left exactly as it is.

Rendering rules:

1. **One block per IIG sheet**, in ``dml.table_order`` order, then any other
   sheet in payload order. Table ``[<dml.schema>].[<framework.tables[sheet]
   or sheet>]``, identifiers bracketed (``emit/dml.py``'s T-SQL spelling).
   Each block opens with ``-- <SHEET>: <n> row(s)``; a sheet with no rows
   gets that header line only.
2. **One** ``INSERT INTO … (<columns>) VALUES (…);`` **per payload row**, the
   columns in the sheet's header order, one statement per line.
3. **Cells.**
   * A non-blank value is a quoted ``N'…'`` literal (``'`` doubled), the value
     as text (an integer cell such as ``SEQUENCE_NO`` too). A line break never
     sits inside a literal: a multi-line value is written losslessly as
     ``N'line 1' + NCHAR(10) + N'line 2'`` (``NCHAR(13)`` for a carriage
     return), still on the statement's one line — unlike the runner script,
     which writes NULL there, this file must carry every IIG cell.
   * A blank cell that is OPEN is a NAMED PLACEHOLDER, unquoted —
     ``<<COLUMN#n>>``, ``n`` = the row's 1-based number within its sheet — so
     the script does not parse, let alone run, until the engineer replaces
     every one. Open means what the BSA's review copy means
     (``codegen.iig_review``): every blank cell not decided blank — the
     ``needs_template`` cells, the template's ``always_blank`` columns (ids,
     connections, audit dates) and any other blank no input states.
   * A blank cell DECIDED blank (``badge_entry.deliberate_blank`` — e.g. the
     pair-1 family's LOB) is ``NULL``.
4. **Catalogs** are written as the cells carry them: already MAPPED by
   ``conventions.catalog_map`` in the resolver. Nothing is re-mapped or
   re-derived here.
5. **Table definitions, by mapped three-part name.** Before the sheet blocks
   a ``-- TABLE DEFINITIONS`` index lists every table the feed defines (rule 1:
   one per distinct stage triple) with its stage definition and its standard
   definition as ``catalog.schema.table`` and their column lists — comments,
   reference only — from ``emit.framework.table_definitions``, the same
   derivation as the CREATE reference text. Inside
   ``ADLS_DELTA_INGESTION_DETAILS`` each INSERT is preceded by
   ``-- table <stage table> <- file <SRC_FILE_NAME>`` (the stage table the
   row's ``TGT_DATABASE_NAME`` / ``TGT_TABLE_NAME`` cells name, by its
   three-part name) and inside ``STGDELTA_STDDELTA_INGESTION_DET`` by
   ``-- table <src catalog.schema.table> -> <tgt catalog.schema.table>``
   (the row's own cells).

The file is byte-stable (no timestamps). Gate check ``metadata_inserts``:
the per-sheet statement counts equal the IIG's and, with every placeholder
read as ``NULL``, every statement parses as T-SQL
(``emit.dml.validate_tsql``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.emit.dml import _ident, _table, validate_tsql
from codegen.gate.preflight import GateCheck

if TYPE_CHECKING:  # pragma: no cover — type hints only (framework imports this module)
    from codegen.emit.framework import TableDefinition

FILE_NAME = "metadata_inserts.sql"
PLACEHOLDER_RE = re.compile(r"<<[A-Za-z0-9_]+#\d+>>")
_DESIGN = "docs/acfc/MULTI_TABLE_DESIGN.md"
_ADLS = "ADLS_DELTA_INGESTION_DETAILS"
_STGDELTA = "STGDELTA_STDDELTA_INGESTION_DET"


@dataclass(frozen=True)
class MetadataInserts:
    path: Path
    row_counts: dict[str, int]
    check: GateCheck


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


def cell_sql(column: str, value, entry: dict, row_number: int) -> str:
    """One IIG cell as a VALUES item (rule 3)."""
    if not _blank(value):
        return _literal(str(value))
    if (entry or {}).get("deliberate_blank"):
        return "NULL"
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


def render_metadata_inserts(spec: ResolvedFeedSpec, payload: dict,
                            definitions: list[TableDefinition], config: Config,
                            banner: list[tuple[str, str]],
                            ddl_name: str | None = None) -> tuple[str, dict[str, int]]:
    """The script text and the INSERT count per sheet."""
    schema = config.dml.schema
    reference = f"`{ddl_name}`" if ddl_name else "the CREATE reference text"
    lines = [
        f"-- {FILE_NAME} — feed {spec.feed_slug}",
        f"-- TARGET SYSTEM = SQL Server metadata DB ({schema} config tables): the rows that "
        f"DEFINE this feed's tables and pipelines — the client's \"DDL\" ({_DESIGN} rule 8). "
        f"The framework creates the Unity Catalog Delta tables from them; {reference} is the "
        "CREATE reference.",
        "-- SOURCE = the same cells as the IIG workbook (config_rows.xlsx / the clean IIG "
        "copy); nothing here is derived again.",
        "-- <<COLUMN#n>> = an OPEN cell (row n of that sheet): replace every one before "
        "running — the script does not parse until then. NULL = a cell decided blank.",
        *[f"-- {key}: {_one_line(value)}" for key, value in banner if key != "Layout"],
        "",
        *_index_lines(definitions),
    ]
    tabs = payload.get("tabs", {})
    counts: dict[str, int] = {}
    for sheet in _sheet_order(payload, config):
        tab = tabs[sheet]
        rows = tab.get("rows", [])
        headers = list(tab["headers"])
        table = _table(schema, config.framework.tables.get(sheet, sheet))
        columns = ", ".join(_ident(h) for h in headers)
        lines += ["", f"-- {sheet}: {len(rows)} row(s)"]
        for number, row in enumerate(rows, start=1):
            values = row["values"]
            if sheet == _ADLS:
                lines.append(_adls_label(values, definitions))
            elif sheet == _STGDELTA:
                lines.append(_stgdelta_label(values))
            items = [cell_sql(h, values.get(h), row["badges"].get(h) or {}, number)
                     for h in headers]
            lines.append(f"INSERT INTO {table} ({columns}) VALUES ({', '.join(items)});")
        counts[sheet] = len(rows)
    lines.append("")
    return "\n".join(lines), counts


def placeholders_as_null(text: str) -> str:
    """The script with every open-cell placeholder read as NULL (validation)."""
    return PLACEHOLDER_RE.sub("NULL", text)


def emit_metadata_inserts(spec: ResolvedFeedSpec, payload: dict,
                          definitions: list[TableDefinition], config: Config,
                          framework_dir: Path, banner: list[tuple[str, str]],
                          ddl_name: str | None = None) -> MetadataInserts:
    text, counts = render_metadata_inserts(spec, payload, definitions, config, banner,
                                           ddl_name=ddl_name)
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
    return MetadataInserts(path=path, row_counts=counts, check=check)


__all__ = ["FILE_NAME", "PLACEHOLDER_RE", "MetadataInserts", "cell_sql", "emit_metadata_inserts",
           "placeholder", "placeholders_as_null", "render_metadata_inserts"]
