"""The HEDIS Stage -> Consumption STTM reader, family H4 (post161, 2026-11-02).

docs/acfc/HEDIS_CONSUMPTION_STTM_SHAPE.md §2 H4: a ``CONTENTS`` sheet (file pattern,
consumption table, load criteria) and one mapping sheet per consumption table with the
header ``STAGE TABLE NAME`` | ``STAGE COLUMN NAME`` | ``STAGE LOGIC`` | (spacer) |
``CONSUMPTION TABLE NAME`` | ``CONSUMPTION COLUMN NAME`` | ``DATA TYPE (MAX Length)``.
Drift handled: the header in any of the first rows, the block starting in any column
(a label such as ``PROCESS 1`` in A1, a spacer column), free text to the right of the
header, audit rows at the bottom.

Output: a :class:`~codegen.contracts.gold.GoldContract` (``dialect="hedis_h4"``), one
feed per mapping sheet, by the gold contract's three-way rule:

- **filled** - the sheet states it: target table, columns, source table / column, a
  direct-map expression, a Spark type, the CONTENTS load criteria;
- **proposed** - derived, with its basis (printed INPUT_NEEDED): a SQL Server type's
  Spark equivalent (the target platform is an open question, shape doc §6 Q2);
- **question** - unstated or free text (printed QUESTION, the cell quoted): target
  catalog / schema, primary key, source catalog.schema, a prose / lookup logic cell, an
  unknown type, a sheet naming several consumption tables.

Never a guess. A logic cell is copied as an expression only when it says direct map
(the stage column itself) or hardcodes ONE quoted literal; audit rows ("ETL generated")
are marked ``edit_class="audit"``. Reads the workbook from bytes (openpyxl 3.1.2 keeps a
path-opened workbook's file handle).
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from openpyxl import load_workbook

from codegen.config import HedisConsumptionConfig
from codegen.contracts.gold import (
    GoldAnswer,
    GoldColumn,
    GoldContract,
    GoldFeed,
    GoldProposal,
    GoldQuestion,
    GoldSource,
    GoldSourceSet,
    GoldTarget,
    GoldWhere,
)

_TYPE_RE = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9]*)\s*(?:\(\s*([0-9]+|max)\s*(?:,\s*([0-9]+))?\s*\))?\s*$",
    re.IGNORECASE)
_LITERAL_RE = re.compile(r"'([^']*)'")


class HedisReadError(ValueError):
    """The workbook is not family H4 (no mapping sheet found)."""


def _norm(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _text(value) -> str | None:
    text = re.sub(r"[ \t]+\n", "\n", str(value)).strip() if value is not None else ""
    return text or None


def _header(ws, roles: dict[str, list[str]], search_rows: int
            ) -> tuple[int | None, dict[str, int]]:
    """(header row, role -> column) of the first row naming the most roles."""
    labels = {_norm(label): role for role, names in roles.items() for label in names}
    best: tuple[int | None, dict[str, int]] = (None, {})
    for r, row in enumerate(ws.iter_rows(min_row=1, max_row=search_rows, values_only=True), 1):
        found: dict[str, int] = {}
        for c, value in enumerate(row, 1):
            role = labels.get(_norm(value))
            if role and role not in found:
                found[role] = c
        if len(found) > len(best[1]):
            best = (r, found)
    return best


def _rows(ws, header_row: int, cols: dict[str, int], blank_end: int):
    """(row number, role -> cell value) under the header until ``blank_end`` blank rows."""
    blanks = 0
    for r, row in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True),
                            header_row + 1):
        cells = {role: (row[c - 1] if c - 1 < len(row) else None) for role, c in cols.items()}
        if all(_text(v) is None for v in cells.values()):
            blanks += 1
            if blanks >= blank_end:
                return
            continue
        blanks = 0
        yield r, cells


def _contents(wb, cfg: HedisConsumptionConfig) -> dict[str, dict[str, str | None]]:
    """CONTENTS: normalized consumption table -> {file_pattern, load_criteria}."""
    names = {_norm(n) for n in cfg.contents_sheet_names}
    out: dict[str, dict[str, str | None]] = {}
    for ws in wb.worksheets:
        if _norm(ws.title) not in names:
            continue
        row_no, cols = _header(ws, cfg.contents_headers, cfg.header_search_rows)
        if row_no is None or "target_table" not in cols:
            continue
        for _r, cells in _rows(ws, row_no, cols, cfg.blank_rows_end):
            table = _text(cells.get("target_table"))
            if table:
                out[_norm(table)] = {"file_pattern": _text(cells.get("file_pattern")),
                                     "load_criteria": _text(cells.get("load_criteria"))}
    return out


def _type(cell: str | None, cfg: HedisConsumptionConfig
          ) -> tuple[str | None, str | None, str]:
    """(spark type, length, status) of a data-type cell: 'filled' (Spark as written),
    'proposed' (a SQL Server name mapped), 'question' (anything else)."""
    if not cell:
        return None, None, "question"
    match = _TYPE_RE.match(cell)
    if not match:
        return None, None, "question"
    name, first, second = match.group(1).lower(), match.group(2), match.group(3)
    length = None if first is None else first
    if name in {t.lower() for t in cfg.spark_types}:
        spark = name if first is None or name not in {"decimal"} else (
            f"decimal({first},{second})" if second else f"decimal({first})")
        return spark, (length if name not in {"decimal"} else None), "filled"
    mapped = cfg.sql_type_map.get(name)
    if mapped is None:
        return None, None, "question"
    if mapped == "decimal" and first is not None and first.isdigit():
        mapped = f"decimal({first},{second})" if second else f"decimal({first})"
        length = None
    return mapped, length, "proposed"


def _logic(logic: str | None, source_column: str | None, cfg: HedisConsumptionConfig
           ) -> tuple[str | None, str | None]:
    """(expression or None, edit class) - only what the cell says, never a guess."""
    low = _norm(logic)
    if logic is None:
        return None, "blank"
    if any(w in low for w in cfg.logic_audit):
        return None, "audit"
    if any(w in low for w in cfg.logic_direct) and source_column:
        return source_column, "direct"
    if any(w in low for w in cfg.logic_hardcoded):
        literals = _LITERAL_RE.findall(logic)
        if len(literals) == 1:
            return "'" + literals[0].replace("\\", "\\\\").replace("'", "\\'") + "'", "hardcoded"
        return None, "hardcoded"
    return None, "prose"


def _read_sheet(ws, sheet_index: int, feed_index: int, workbook: str,
                contents: dict, cfg: HedisConsumptionConfig,
                answers: dict[str, str]) -> GoldFeed | None:
    row_no, cols = _header(ws, cfg.mapping_headers, cfg.header_search_rows)
    if row_no is None or len(cols) < cfg.min_mapping_roles or "target_column" not in cols:
        return None
    key = f"feeds[{feed_index}]"
    where = GoldWhere(file=workbook, block_index=sheet_index, source_row=row_no)
    questions: list[GoldQuestion] = []
    proposals: list[GoldProposal] = []
    answered: list[GoldAnswer] = []
    flags: list[str] = []
    filled: dict[str, int] = {}

    def fill(role: str) -> None:
        filled[role] = filled.get(role, 0) + 1

    def ask(qkey: str, role: str, reason: str, quoted: str | None = None,
            at: GoldWhere | None = None, candidates: list[str] | None = None) -> str | None:
        """An answer closes the question (counted filled); else the QUESTION."""
        if qkey in answers:
            answered.append(GoldAnswer(key=qkey, role=role, value=answers[qkey]))
            fill(role)
            return answers[qkey]
        questions.append(GoldQuestion(key=qkey, role=role, reason=reason, quoted=quoted,
                                      where=at or where, candidates=candidates or []))
        return None

    rows = list(_rows(ws, row_no, cols, cfg.blank_rows_end))
    targets = list(dict.fromkeys(t for _r, c in rows if (t := _text(c.get("target_table")))))
    if len(targets) == 1:
        target_table = targets[0]
        fill("target_table")
    else:
        target_table = ask(f"{key}.target_table", "target_table",
                           f"the sheet names {len(targets)} consumption tables; one feed "
                           "loads one table", candidates=targets) or (targets[0] if targets
                                                                       else ws.title)
        if not targets:
            flags.append(f"hedis_target_table_from_sheet_name: sheets[{sheet_index}]")
    catalog = cfg.target_catalog or ask(f"{key}.target_catalog", "target_catalog",
                                        "no document states the consumption catalog")
    if cfg.target_catalog:
        fill("target_catalog")
    schema = cfg.target_schema or ask(f"{key}.target_schema", "target_schema",
                                      "no document states the consumption schema")
    if cfg.target_schema:
        fill("target_schema")

    listed = contents.get(_norm(target_table))
    load_mode = None
    if listed is None:
        flags.append(f"hedis_not_in_contents: sheets[{sheet_index}] - its table is not "
                     "listed on the CONTENTS sheet")
    criteria = (listed or {}).get("load_criteria")
    if criteria and _norm(criteria) in cfg.load_criteria_map:
        load_mode = cfg.load_criteria_map[_norm(criteria)]
        fill("load_mode")
    else:
        load_mode = ask(f"{key}.load_mode", "load_mode",
                        "the CONTENTS sheet states no load criteria this reader maps",
                        quoted=criteria)
    primary_key = ask(f"{key}.primary_key", "primary_key",
                      "the mapping sheet marks no key column")

    columns: list[GoldColumn] = []
    sources: dict[str, GoldSource] = {}
    for r, cells in rows:
        attribute = _text(cells.get("target_column"))
        if attribute is None:
            continue
        j = len(columns)
        at = GoldWhere(file=workbook, block_index=sheet_index, source_row=r)
        source_table = _text(cells.get("source_table"))
        source_column = _text(cells.get("source_column"))
        if source_table:
            parts = source_table.split(".")
            sources.setdefault(source_table, GoldSource(
                database=None, table=parts[-1],
                catalog_schema=".".join(parts[:-1]) if len(parts) == 3 else None))
            fill("source_table")
        type_cell = _text(cells.get("data_type"))
        spark, length, status = _type(type_cell, cfg)
        if status == "filled":
            fill("target_type")
        elif status == "proposed":
            proposals.append(GoldProposal(
                key=f"{key}.columns[{j}].target_type", role="target_type", value=spark,
                basis=f"the sheet types it {type_cell!r} (SQL Server vocabulary); the "
                      "consumption platform is unconfirmed", where=at))
        else:
            spark = ask(f"{key}.columns[{j}].target_type", "target_type",
                        "the data type cell is empty or not a type this reader knows",
                        quoted=type_cell, at=at)
        logic = _text(cells.get("logic"))
        expression, edit = _logic(logic, source_column, cfg)
        if expression is not None:
            fill("expression")
        elif edit != "audit":
            expression = ask(f"{key}.columns[{j}].expression", "expression",
                             "the stage logic is free text, a lookup or blank - "
                             "only a direct map or one hardcoded literal is copied",
                             quoted=logic, at=at)
        columns.append(GoldColumn(
            target_attribute=attribute, block_index=sheet_index, source_row=r,
            source_table=source_table, source_field=source_column, description=None,
            source_format=None, target_format=type_cell, length=length,
            length_status="filled" if length else None, target_type=spark,
            target_type_status=(status if status in ("filled", "proposed") else
                                ("filled" if spark else None)),
            expression=expression,
            expression_status="filled" if expression is not None else None,
            edit_class=edit))
    audit = sum(1 for c in columns if c.edit_class == "audit")
    if audit:
        flags.append(f"hedis_audit_rows: {audit} audit column(s) (ETL generated) - "
                     "populated by the load, not mapped")
    unqualified = [t for t, s in sources.items() if s.catalog_schema is None]
    if unqualified:
        value = ask(f"{key}.source_catalog_schema", "source_catalog_schema",
                    f"{len(unqualified)} source table(s) without a catalog.schema")
        if value:
            sources = {t: (s if s.catalog_schema else s.model_copy(
                update={"catalog_schema": value})) for t, s in sources.items()}
    return GoldFeed(
        index=feed_index, manifest_index=sheet_index, blocks=[sheet_index],
        json_file=f"{workbook}#sheets[{sheet_index}]",
        target=GoldTarget(catalog=catalog, schema=schema, table=target_table),
        refresh_schedule=None, load_mode=load_mode,
        primary_key=[k.strip() for k in primary_key.split(",")] if primary_key else [],
        scd2_mode=None, sk_strategy=None, columns=columns,
        source_sets=[GoldSourceSet(block_index=sheet_index, sources=list(sources.values()),
                                   columns=list(range(len(columns))))],
        regions=[], filled=filled, proposals=proposals, questions=questions,
        flags=flags, answered=answered)


def read_workbook(path: Path, cfg: HedisConsumptionConfig, *,
                  answers: dict[str, str] | None = None,
                  contract_name: str | None = None) -> GoldContract:
    """A family-H4 workbook -> a gold contract (one feed per mapping sheet)."""
    wb = load_workbook(io.BytesIO(Path(path).read_bytes()), data_only=True)
    contents = _contents(wb, cfg)
    skip = {_norm(n) for n in cfg.contents_sheet_names}
    feeds: list[GoldFeed] = []
    for sheet_index, ws in enumerate(wb.worksheets):
        if _norm(ws.title) in skip:
            continue
        feed = _read_sheet(ws, sheet_index, len(feeds), Path(path).name, contents, cfg,
                           answers or {})
        if feed is not None:
            feeds.append(feed)
    if not feeds:
        raise HedisReadError("no mapping sheet: no sheet's first rows name the H4 header "
                             f"roles (at least {cfg.min_mapping_roles})")
    return GoldContract(contract_name=contract_name or Path(path).stem, dialect="hedis_h4",
                        extractor_version=None, feeds=feeds)
