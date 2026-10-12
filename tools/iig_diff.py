"""Cell-level diff of an agent IIG workbook against a golden one (openpyxl + PyYAML).

    python tools/iig_diff.py --golden <golden.xlsx> --agent <agent.xlsx> [<more.xlsx> ...]
        --out <dir>
    python tools/iig_diff.py --batch <pairs dir> --out <dir>
        [--keys tools/iig_keys.yaml] [--pair-mode key|position|fuzzy]

REFUSED without a build identity (2026-10-12): the agent workbook must sit at
most 5 folders below a ``CODEGEN_BUILD.json`` (written by ``codegen generate``
into its output root) or a ``run_meta.json`` carrying ``build`` (an App run);
otherwise the run prints ``unscored: agent workbook has no build identity`` and
exits 1 (batch: the pair is listed UNSCORED, exit 1). A stale workbook from an
older code path can never be scored again (round 3 pair_2's 7.9 was one).

Every report header states: AGENT BUILD (version, commit, branch, commit time
or the src tree id), the IGNORED set, and — for a non-key pairing — a banner.

Several ``--agent`` workbooks (a run writes one IIG per feed; a pair golden
covers every group of the pair) are compared as their UNION
(``read_agent_workbooks``); they must all carry the same build identity.

Row pairing — ``--pair-mode key`` (default) uses ONLY the natural key per
sheet below (``tools/iig_keys.yaml``); a key that is not unique on either side
is flagged and its duplicates pair in sheet order. Rows the key cannot pair (a
sheet with no key, a key column absent from either side, an OBJECT_ID that
does not resolve) are NOT paired: missing / extra, said in a warning. Position
(``--pair-mode position``) and normalized keys (``--pair-mode fuzzy``) are
explicit only and print a banner: not the validation score.

    Sheet                              Natural key
    DATA_FACTORY_PIPELINE_SCHEDULE     PIPELINE_NAME
    FILE_ADLS_INGESTION_DETAILS        SRC_ROOT_DIR, TGT_ADLS_PATH
    ADLS_DELTA_INGESTION_DETAILS       OBJECT_NAME, TGT_TABLE_NAME
    STGDELTA_STDDELTA_INGESTION_DET    OBJECT_NAME, TGT_TABLE_NAME
    ADLS_FIXED_WIDTH_HANDLER           SEGMENT, TGT_TABLE
    DATABRICKS_NOTEBOOK_DETAILS        DATABRICKS_NOTEBOOK_NAME
    DATA_QUALITY_RULES                 OBJECT_ID -> its table, RULE_CLASS, SOURCE_COLUMN
    EMAIL_TEMPLATE_CONFIG              TEMPLATE_NAME, STATUS
    ALL_FILES_STATIC_INFORMATION       FILE_NAME

Sheets match caselessly on their first 31 characters; an agent
FILE_ADLS_INGESTION_DETAILS is compared with a golden
ALL_FILES_STATIC_INFORMATION (``TEMPLATE_ALIASES``, ``template_mismatch`` in
score.json). An OBJECT_ID in a key is replaced by the table it resolves to in
its OWN workbook — the TGT_TABLE_NAME of the ADLS_DELTA / STGDELTA_STDDELTA /
RDBMS row with the same (GROUP_ID, OBJECT_ID), else the same OBJECT_ID when
every such row names one table; unresolved ids are listed as
``unresolved_object_ids`` in score.json. Every cell of a paired row is one of:

* ``exact``            — same value as written (None and "" are the same);
* ``normalized``       — equal once case, whitespace, trailing zeros, NULL vs
  empty and path separators are normalized;
* ``mismatch``         — both filled, different;
* ``missing-in-agent`` — golden filled, agent blank (or the column / row is
  absent from the agent workbook);
* ``extra-in-agent``   — golden blank, agent filled (or the column / row is
  absent from the golden);
* ``needs_assignment`` — a column of THE IGNORED SET (``needs_assignment`` in
  iig_keys.yaml, agreed 2026-10-12): INVENTORY_ID, OBJECT_ID, PIPELINE_ID,
  GROUP_ID, CONNECTION_ID / ``*_CONNECTION_ID``, CREATED_BY, UPDATED_BY,
  CREATED_DATE, UPDATED_DATE (+ iig_v1's CRETAED_*): reported separately,
  never scored. Every other ``*_ID`` column is scored.

A row present on one side only counts each of its cells as missing / extra.
score = 100 x (exact + normalized) / scored cells, one decimal (scored = every
status but needs_assignment). A sheet in only one workbook is all missing /
extra. Outputs per pair, under ``--out``:

* ``score.json``  — per sheet: key, key uniqueness, row counts, status counts,
  score, the needs_assignment columns; the totals;
* ``diff.xlsx``   — ``_DIFF_SUMMARY`` + one sheet per IIG sheet, one line per
  cell (key, rows, column, golden, agent, status); CREATED_BY / UPDATED_BY
  values withheld;
* ``routing.csv`` — sheet, column, status_summary, origin_tag (left blank).

Batch: ``--batch DIR`` takes every subdirectory holding one ``*golden*.xlsx``
and one ``*agent*.xlsx``, and every ``<pair>_golden.xlsx`` /
``<pair>_agent.xlsx`` couple in DIR itself; each pair writes to ``<out>/<pair>/``
and ``<out>/batch_summary.json`` lists every pair's totals.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import yaml
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font, PatternFill

DEFAULT_KEYS = Path(__file__).resolve().parent / "iig_keys.yaml"
BUILD_FILES = ("CODEGEN_BUILD.json", "run_meta.json")
UNSCORED = "unscored: agent workbook has no build identity"

# ----------- pair-mode constants
PAIR_MODES = ("key", "position", "fuzzy")
_FUZZY_PREFIXES = re.compile(
    r"^(PL_File_|PL_|NB_|WF_)", re.IGNORECASE,
)

# Template-version aliases: agent and golden may name the same logical sheet
# differently when they use different IIG template versions.
# Each entry maps an agent-side sheet ID to a golden-side sheet ID.
# Values are uppercased and clipped to 31 chars (same rule as sheet_id()).
TEMPLATE_ALIASES: dict[str, str] = {
    "FILE_ADLS_INGESTION_DETAILS"[:31].upper(): "ALL_FILES_STATIC_INFORMATION"[:31].upper(),
}

EXACT = "exact"
NORMALIZED = "normalized"
MISMATCH = "mismatch"
MISSING = "missing-in-agent"
EXTRA = "extra-in-agent"
ASSIGN = "needs_assignment"
STATUSES = (EXACT, NORMALIZED, MISMATCH, MISSING, EXTRA, ASSIGN)
SCORED = (EXACT, NORMALIZED, MISMATCH, MISSING, EXTRA)

NULL_TOKENS = {"NULL"}
WITHHELD = "<withheld>"
SUMMARY_SHEET = "_DIFF_SUMMARY"
_NUMBER = re.compile(r"[+-]?\d+\.\d+")
_FILLS = {
    EXACT: None,
    NORMALIZED: "DDEBF7",
    MISMATCH: "F8CBAD",
    MISSING: "FFE699",
    EXTRA: "D9D2E9",
    ASSIGN: "E7E6E6",
}


# --------------------------------------------------------------------- config


def sheet_id(name: str) -> str:
    """A sheet's identity: caseless, cut to Excel's 31 characters, so the
    framework table ``stgdelta_stddelta_ingestion_details`` is the IIG sheet
    ``STGDELTA_STDDELTA_INGESTION_DET``."""
    return name.strip().upper()[:31]


@dataclass(frozen=True)
class KeyConfig:
    sheets: dict[str, list[str]]
    needs_assignment: list[str]
    withhold_values: list[str]
    ignore_sheets: list[str]
    object_id_column: str = "OBJECT_ID"
    group_id_column: str = "GROUP_ID"
    object_sources: dict[str, list[str]] = field(default_factory=dict)

    def key_for(self, sheet: str) -> list[str] | None:
        return _by_sheet(self.sheets, sheet)

    def object_source(self, sheet: str) -> list[str] | None:
        return _by_sheet(self.object_sources, sheet)

    def is_object_id(self, column: str) -> bool:
        return column.upper() == self.object_id_column.upper()

    def is_assignment(self, column: str) -> bool:
        col = column.upper()
        return any(fnmatch.fnmatchcase(col, pat.upper()) for pat in self.needs_assignment)

    def is_withheld(self, column: str) -> bool:
        return column.upper() in {c.upper() for c in self.withhold_values}

    def is_ignored(self, sheet: str) -> bool:
        return sheet.startswith("_") or sheet_id(sheet) in {sheet_id(s) for s in self.ignore_sheets}


def _by_sheet(table: dict[str, list[str]], sheet: str) -> list[str] | None:
    for name, cols in table.items():
        if sheet_id(name) == sheet_id(sheet):
            return list(cols)
    return None


def _column_lists(path: Path, section: str, raw: object) -> dict[str, list[str]]:
    out = {}
    for name, cols in (raw or {}).items():
        cols = [cols] if isinstance(cols, str) else list(cols or [])
        if not cols:
            raise ValueError(f"{path}: {section}.{name} is empty")
        out[str(name)] = [str(c) for c in cols]
    return out


def load_keys(path: Path) -> KeyConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    known = {"sheets", "needs_assignment", "withhold_values", "ignore_sheets", "object_tables"}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{path}: unknown keys {sorted(unknown)}")
    objects = raw.get("object_tables") or {}
    unknown = set(objects) - {"id_column", "group_column", "sources"}
    if unknown:
        raise ValueError(f"{path}: unknown object_tables keys {sorted(unknown)}")
    return KeyConfig(
        sheets=_column_lists(path, "sheets", raw.get("sheets")),
        needs_assignment=[str(p) for p in raw.get("needs_assignment") or []],
        withhold_values=[str(c) for c in raw.get("withhold_values") or []],
        ignore_sheets=[str(s) for s in raw.get("ignore_sheets") or []],
        object_id_column=str(objects.get("id_column") or "OBJECT_ID"),
        group_id_column=str(objects.get("group_column") or "GROUP_ID"),
        object_sources=_column_lists(path, "object_tables.sources", objects.get("sources")),
    )


# ------------------------------------------------------------------- reading


@dataclass
class Sheet:
    name: str
    columns: list[str]  # header text as written, blank headers dropped
    rows: list[tuple[int, dict[str, object]]]  # (worksheet row, {COLUMN: value})

    def canon(self) -> dict[str, str]:
        return {c.upper(): c for c in self.columns}


def read_workbook(path: Path, keys: KeyConfig) -> dict[str, Sheet]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets: dict[str, Sheet] = {}
        for ws in wb.worksheets:
            if keys.is_ignored(ws.title):
                continue
            it = ws.iter_rows(values_only=True)
            header = next(it, None) or ()
            idx: list[tuple[int, str]] = []
            seen: Counter[str] = Counter()
            for i, cell in enumerate(header):
                name = str(cell).strip() if cell is not None else ""
                if not name:
                    continue
                seen[name.upper()] += 1
                if seen[name.upper()] > 1:
                    name = f"{name}#{seen[name.upper()]}"
                idx.append((i, name))
            rows = []
            for n, values in enumerate(it, start=2):
                row = {name: values[i] if i < len(values) else None for i, name in idx}
                if any(_raw(v) != "" for v in row.values()):
                    rows.append((n, row))
            sheets[ws.title] = Sheet(ws.title, [name for _, name in idx], rows)
        return sheets
    finally:
        wb.close()


ROW_STRIDE = 100_000      # merged agent workbooks: row = file number x stride + row


def read_agent_workbooks(paths: list[Path], keys: KeyConfig) -> dict[str, Sheet]:
    """One agent workbook, or the UNION of several (a run writes one IIG per
    feed; a pair golden covers every group of the pair). Sheets merge by
    identity, columns by name, rows are appended (agent row = file number x
    ROW_STRIDE + row). Each file's GROUP_ID is prefixed ``<file>/`` so the
    OBJECT_IDs every feed numbers from 1 never collide when they resolve to
    their tables (GROUP_ID is in the ignored set: never scored)."""
    if len(paths) == 1:
        return read_workbook(paths[0], keys)
    merged: dict[str, Sheet] = {}
    by_id: dict[str, str] = {}
    for index, path in enumerate(paths, start=1):
        for name, sheet in read_workbook(path, keys).items():
            target = by_id.setdefault(sheet_id(name), name)
            into = merged.setdefault(target, Sheet(target, [], []))
            known = {c.upper() for c in into.columns}
            into.columns += [c for c in sheet.columns if c.upper() not in known]
            for n, row in sheet.rows:
                row = {c: (f"{index}/{_raw(v)}" if c.upper() == keys.group_id_column.upper()
                           else v) for c, v in row.items()}
                into.rows.append((index * ROW_STRIDE + n, row))
    return merged


# --------------------------------------------------------------- cell rules


def _raw(value: object) -> str:
    return "" if value is None else str(value)


def _trim_zeros(text: str) -> str:
    return text.rstrip("0").rstrip(".") if "." in text else text


def normalize(value: object) -> str:
    """Case, whitespace, trailing zeros, NULL vs empty and path separators."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else _trim_zeros(repr(value))
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    text = " ".join(str(value).split())
    if text.upper() in NULL_TOKENS:
        return ""
    if _NUMBER.fullmatch(text):
        return _trim_zeros(text)
    text = text.replace("\\", "/")
    text = re.sub(r"(?<!:)/{2,}", "/", text)
    if len(text) > 1:
        text = text.rstrip("/")
    return text.casefold()


def classify(golden: object, agent: object) -> str:
    if _raw(golden) == _raw(agent):
        return EXACT
    g, a = normalize(golden), normalize(agent)
    if g == a:
        return NORMALIZED
    if not g:
        return EXTRA
    if not a:
        return MISSING
    return MISMATCH


def fuzzy_key(text: str) -> str:
    """Normalize a key value for fuzzy pairing: strip known prefixes
    (PL_File_, PL_, NB_, WF_), collapse underscores, casefold."""
    text = _FUZZY_PREFIXES.sub("", text.strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text.casefold()


# ------------------------------------------------------------------- pairing


@dataclass
class RowPair:
    golden: tuple[int, dict[str, object]] | None
    agent: tuple[int, dict[str, object]] | None
    key: str


class ObjectTables:
    """OBJECT_ID -> table name, from ONE workbook's own ingestion sheets.

    OBJECT_IDs number objects within a GROUP_ID (the ADLS group and the
    STGDELTA group of one feed both have an object 1), so a row resolves by
    (GROUP_ID, OBJECT_ID) first, then by OBJECT_ID alone when every source
    row carrying it names the same table. Ids are never compared across
    workbooks: a golden and an agent run number them differently."""

    def __init__(self, sheets: dict[str, Sheet], keys: KeyConfig) -> None:
        self.keys = keys
        self.by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.by_object: dict[str, set[str]] = defaultdict(set)
        for name, sheet in sheets.items():
            wanted = keys.object_source(name)
            if not wanted:
                continue
            canon = sheet.canon()
            id_col = canon.get(keys.object_id_column.upper())
            group_col = canon.get(keys.group_id_column.upper())
            name_cols = [canon[c.upper()] for c in wanted if c.upper() in canon]
            if not id_col or not name_cols:
                continue
            for _, row in sheet.rows:
                obj = normalize(row.get(id_col))
                table = next(
                    (_raw(row.get(c)).strip() for c in name_cols if normalize(row.get(c))), ""
                )
                if not obj or not table:
                    continue
                self.by_group[(normalize(row.get(group_col)) if group_col else "", obj)].add(table)
                self.by_object[obj].add(table)

    def table_for(self, row: dict[str, object], canon: dict[str, str]) -> str | None:
        id_col = canon.get(self.keys.object_id_column.upper())
        group_col = canon.get(self.keys.group_id_column.upper())
        obj = normalize(row.get(id_col)) if id_col else ""
        if not obj:
            return None
        group = normalize(row.get(group_col)) if group_col else ""
        tables = self.by_group.get((group, obj)) or self.by_object.get(obj) or set()
        if len({normalize(t) for t in tables}) != 1:
            return None
        return sorted(tables)[0]


@dataclass
class _Keyed:
    row: tuple[int, dict[str, object]]
    key: tuple[str, ...] | None  # None: an OBJECT_ID in the key did not resolve
    text: str
    object_id: str = ""


def _keyer(sheet: Sheet, cols: list[str], keys: KeyConfig, tables: ObjectTables | None):
    canon = sheet.canon()

    def keyed(row: tuple[int, dict[str, object]]) -> _Keyed:
        parts, texts = [], []
        for col in cols:
            if keys.is_object_id(col) and tables is not None:
                table = tables.table_for(row[1], canon)
                if table is None:
                    return _Keyed(row, None, "", _raw(row[1].get(col)).strip() or "<blank>")
                parts.append(normalize(table))
                texts.append(table)
            else:
                parts.append(normalize(row[1].get(col)))
                texts.append(_raw(row[1].get(col)).strip() or "<blank>")
        return _Keyed(row, tuple(parts), " | ".join(texts))

    return keyed


def _positional(g_rows: list, a_rows: list, label: str = "") -> list[RowPair]:
    pairs = []
    for i in range(max(len(g_rows), len(a_rows))):
        g = g_rows[i] if i < len(g_rows) else None
        a = a_rows[i] if i < len(a_rows) else None
        pairs.append(RowPair(g, a, f"#{i + 1}{label}"))
    return pairs


def _unpaired(g_rows: list, a_rows: list, label: str = "") -> list[RowPair]:
    """Key mode (2026-10-12): rows the natural key cannot pair are NOT paired —
    every golden row is missing-in-agent, every agent row extra-in-agent."""
    return ([RowPair(g, None, f"g#{i + 1}{label}") for i, g in enumerate(g_rows)]
            + [RowPair(None, a, f"a#{i + 1}{label}") for i, a in enumerate(a_rows)])


def pair_rows(
    golden: Sheet | None,
    agent: Sheet | None,
    key: list[str] | None,
    keys: KeyConfig | None = None,
    tables: tuple[ObjectTables | None, ObjectTables | None] = (None, None),
    pair_mode: str = "key",
) -> tuple[list[RowPair], dict]:
    """Pair rows by key; return pairs + key facts.

    ``pair_mode`` controls how rows are matched:

    * ``key`` (default) — ONLY the natural key from iig_keys.yaml. A sheet with
      no key, a key column absent from either side, and rows whose OBJECT_ID
      does not resolve are NOT paired (missing / extra), each said in a
      warning — never paired by position (2026-10-12: the round 3 pair_2 score
      was built on a silent position fallback).
    * ``position`` — explicit only: pair every sheet row-for-row by ordinal
      position (the report carries a banner).
    * ``fuzzy`` — explicit only: like ``key`` but key values are normalized
      (``PL_File_`` / ``PL_`` / ``NB_`` / ``WF_`` stripped, case / underscores
      collapsed) before matching (banner too).

    An OBJECT_ID key column is replaced by the table its row resolves to in
    its own workbook (``ObjectTables``)."""
    keys = keys or KeyConfig({}, [], [], [])
    g_rows = golden.rows if golden else []
    a_rows = agent.rows if agent else []
    facts: dict = {"key": key or "none", "pair_mode": pair_mode, "warnings": []}
    if pair_mode == "position":
        facts["key"] = "position"
        facts["pair_mode"] = "position"
        return _positional(g_rows, a_rows), facts
    if key:
        cols_g = _resolve(golden, key)
        cols_a = _resolve(agent, key)
        if (golden and None in cols_g) or (agent and None in cols_a):
            facts["warnings"].append(
                f"key column(s) {key} not in both sheets — rows NOT paired "
                "(--pair-mode position would pair them by order)"
            )
            key = None
    elif g_rows and a_rows:
        facts["warnings"].append("no natural key for this sheet in iig_keys.yaml — rows NOT "
                                 "paired (--pair-mode position would pair them by order)")
    if not key:
        return _unpaired(g_rows, a_rows), facts

    g_keyed = [_keyer(golden, cols_g, keys, tables[0])(r) for r in g_rows] if golden else []
    a_keyed = [_keyer(agent, cols_a, keys, tables[1])(r) for r in a_rows] if agent else []
    if any(keys.is_object_id(c) for c in key):
        facts["key"] = [
            f"{c} -> table" if keys.is_object_id(c) and tables[0] is not None else c for c in key
        ]
        unresolved = {
            "golden": [k.object_id for k in g_keyed if k.key is None],
            "agent": [k.object_id for k in a_keyed if k.key is None],
        }
        facts["unresolved_object_ids"] = unresolved
        if unresolved["golden"] or unresolved["agent"]:
            facts["warnings"].append(
                f"OBJECT_ID not resolved to a table (golden {len(unresolved['golden'])}, "
                f"agent {len(unresolved['agent'])} rows) — those rows NOT paired"
            )
    dup_g = _duplicates(g_keyed)
    dup_a = _duplicates(a_keyed)
    facts["key_unique"] = {"golden": not dup_g, "agent": not dup_a}
    facts["duplicate_keys"] = {"golden": dup_g, "agent": dup_a}
    if dup_g or dup_a:
        facts["warnings"].append(
            f"key {key} is not unique (golden {len(dup_g)}, agent {len(dup_a)} duplicated) "
            "— duplicates paired in sheet order"
        )
    # Build the key → agent-row index; optionally apply fuzzy normalization.
    use_fuzzy = pair_mode == "fuzzy"

    def _match_key(k: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if k is None or not use_fuzzy:
            return k
        return tuple(fuzzy_key(part) for part in k)

    by_key_a: dict[tuple[str, ...], list[_Keyed]] = defaultdict(list)
    for k in a_keyed:
        if k.key is not None:
            by_key_a[_match_key(k.key)].append(k)
    pairs = []
    for k in g_keyed:
        if k.key is None:
            continue
        bucket = by_key_a.get(_match_key(k.key))
        partner = bucket.pop(0).row if bucket else None
        pairs.append(RowPair(k.row, partner, k.text))
    leftover = sorted((k for b in by_key_a.values() for k in b), key=lambda k: k.row[0])
    pairs += [RowPair(None, k.row, k.text) for k in leftover]
    pairs += _unpaired(
        [k.row for k in g_keyed if k.key is None],
        [k.row for k in a_keyed if k.key is None],
        " (OBJECT_ID unresolved)",
    )
    return pairs, facts


def _resolve(sheet: Sheet | None, key: list[str]) -> list[str | None]:
    if sheet is None:
        return [None] * len(key)
    canon = sheet.canon()
    return [canon.get(k.upper()) for k in key]


def _duplicates(keyed: list[_Keyed]) -> list[str]:
    counts = Counter(k.key for k in keyed if k.key is not None)
    texts: dict[tuple[str, ...], str] = {}
    for k in keyed:
        if k.key is not None:
            texts.setdefault(k.key, k.text)
    return [texts[key] for key, n in counts.items() if n > 1]


# ------------------------------------------------------------------- diffing


@dataclass
class Cell:
    key: str
    golden_row: int | None
    agent_row: int | None
    column: str
    golden: object
    agent: object
    status: str


@dataclass
class SheetDiff:
    name: str
    presence: str  # compared | golden-only | agent-only
    facts: dict
    cells: list[Cell] = field(default_factory=list)
    rows: dict = field(default_factory=dict)
    columns: dict = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        c = Counter(cell.status for cell in self.cells)
        return {s: c.get(s, 0) for s in STATUSES}


def diff_sheet(
    name: str,
    golden: Sheet | None,
    agent: Sheet | None,
    keys: KeyConfig,
    tables: tuple[ObjectTables | None, ObjectTables | None] = (None, None),
    pair_mode: str = "key",
) -> SheetDiff:
    presence = "compared" if golden and agent else ("golden-only" if golden else "agent-only")
    pairs, facts = pair_rows(golden, agent, keys.key_for(name), keys, tables,
                             pair_mode=pair_mode)
    g_canon = golden.canon() if golden else {}
    a_canon = agent.canon() if agent else {}
    order = [c.upper() for c in golden.columns] if golden else []
    order += [c.upper() for c in (agent.columns if agent else []) if c.upper() not in g_canon]
    out = SheetDiff(name, presence, facts)
    out.columns = {
        "golden_only": [g_canon[c] for c in order if c in g_canon and c not in a_canon],
        "agent_only": [a_canon[c] for c in order if c in a_canon and c not in g_canon],
    }
    for pair in pairs:
        g_row = pair.golden[1] if pair.golden else None
        a_row = pair.agent[1] if pair.agent else None
        for col in order:
            label = g_canon.get(col) or a_canon[col]
            in_g = g_row is not None and col in g_canon
            in_a = a_row is not None and col in a_canon
            if not (in_g or in_a):
                continue  # neither workbook has this row in this column: no cell
            g_val = g_row.get(g_canon[col]) if in_g else None
            a_val = a_row.get(a_canon[col]) if in_a else None
            if keys.is_assignment(label):
                status = ASSIGN
            elif not in_g:
                status = EXTRA
            elif not in_a:
                status = MISSING
            else:
                status = classify(g_val, a_val)
            out.cells.append(
                Cell(
                    pair.key,
                    pair.golden[0] if pair.golden else None,
                    pair.agent[0] if pair.agent else None,
                    label,
                    g_val,
                    a_val,
                    status,
                )
            )
    out.rows = {
        "golden": len(golden.rows) if golden else 0,
        "agent": len(agent.rows) if agent else 0,
        "paired": sum(1 for p in pairs if p.golden and p.agent),
        MISSING: sum(1 for p in pairs if p.golden and not p.agent),
        EXTRA: sum(1 for p in pairs if p.agent and not p.golden),
    }
    return out


def diff_workbooks(
    golden: Path,
    agent: Path | list[Path],
    keys: KeyConfig,
    pair_mode: str = "key",
) -> list[SheetDiff]:
    g = read_workbook(golden, keys)
    a = read_agent_workbooks(agent if isinstance(agent, list) else [agent], keys)
    tables = (ObjectTables(g, keys), ObjectTables(a, keys))
    a_by_id = {sheet_id(n): n for n in a}
    g_ids = {sheet_id(n) for n in g}

    # Detect template-alias matches: an agent sheet whose ID maps to a golden ID.
    # Recognized as the same logical sheet but flagged as "template_mismatch".
    alias_map: dict[str, str] = {}  # golden_name -> agent_name
    template_mismatches: set[str] = set()  # golden sheet names with alias match
    for a_name in a:
        aid = sheet_id(a_name)
        if aid in TEMPLATE_ALIASES and TEMPLATE_ALIASES[aid] in {sheet_id(n) for n in g}:
            g_name = next(n for n in g if sheet_id(n) == TEMPLATE_ALIASES[aid])
            alias_map[g_name] = a_name
            template_mismatches.add(g_name)

    names = list(g) + [
        n for n in a
        if sheet_id(n) not in g_ids and n not in alias_map.values()
    ]
    result = []
    for name in names:
        g_sheet = g.get(name)
        a_name = alias_map.get(name) or a_by_id.get(sheet_id(name), "")
        a_sheet = a.get(a_name)
        sd = diff_sheet(name, g_sheet, a_sheet, keys, tables, pair_mode=pair_mode)
        if name in template_mismatches:
            sd.facts["template_mismatch"] = {
                "golden_sheet": name,
                "agent_sheet": alias_map[name],
                "note": "Different IIG template versions use different sheet names "
                        "for the same logical table.",
            }
        result.append(sd)
    return result


def _score(counts: dict[str, int]) -> float:
    scored = sum(counts[s] for s in SCORED)
    if not scored:
        return 100.0
    return round(100.0 * (counts[EXACT] + counts[NORMALIZED]) / scored, 1)


def score_payload(golden: Path, agent: Path | list[Path], keys_path: Path,
                  diffs: list[SheetDiff], header: dict | None = None) -> dict:
    totals: Counter[str] = Counter()
    sheets = {}
    warnings = []
    for d in diffs:
        counts = d.counts()
        totals.update(counts)
        assign: dict[str, dict[str, int]] = {}
        for cell in d.cells:
            if cell.status != ASSIGN:
                continue
            entry = assign.setdefault(
                cell.column, {"cells": 0, "golden_filled": 0, "agent_filled": 0, "equal": 0}
            )
            entry["cells"] += 1
            entry["golden_filled"] += bool(normalize(cell.golden))
            entry["agent_filled"] += bool(normalize(cell.agent))
            entry["equal"] += normalize(cell.golden) == normalize(cell.agent)
        sheet_warnings = list(d.facts.get("warnings", []))
        if d.presence != "compared":
            sheet_warnings.append(f"sheet is {d.presence}")
        warnings += [f"{d.name}: {w}" for w in sheet_warnings]
        entry: dict = {
            "presence": d.presence,
            "key": d.facts["key"],
            "pair_mode": d.facts.get("pair_mode", "key"),
            "key_unique": d.facts.get("key_unique"),
            "duplicate_keys": d.facts.get("duplicate_keys"),
            "unresolved_object_ids": d.facts.get("unresolved_object_ids"),
            "rows": d.rows,
            "columns": d.columns,
            "counts": counts,
            "score": _score(counts),
            "needs_assignment": assign,
            "warnings": sheet_warnings,
        }
        if d.facts.get("template_mismatch"):
            entry["template_mismatch"] = d.facts["template_mismatch"]
        sheets[d.name] = entry
    total_counts = {s: totals.get(s, 0) for s in STATUSES}
    return {
        **(header or {}),
        "golden": str(golden),
        "agent": [str(a) for a in agent] if isinstance(agent, list) else str(agent),
        "keys": str(keys_path),
        "totals": {
            **total_counts,
            "scored_cells": sum(total_counts[s] for s in SCORED),
            "score": _score(total_counts),
        },
        "sheets": sheets,
        "warnings": warnings,
    }


# ------------------------------------------------------------------- writing


def _cell_value(value: object) -> object:
    if isinstance(value, str):
        return ILLEGAL_CHARACTERS_RE.sub("", value)
    return value


def write_diff_xlsx(path: Path, payload: dict, diffs: list[SheetDiff], keys: KeyConfig) -> None:
    wb = openpyxl.Workbook()
    summary = wb.active
    summary.title = SUMMARY_SHEET
    head = ["SHEET", "PRESENCE", "KEY", "KEY_UNIQUE", "GOLDEN_ROWS", "AGENT_ROWS", "PAIRED"]
    head += [MISSING + " rows", EXTRA + " rows", *STATUSES, "SCORE"]
    summary.append(head)
    for d in diffs:
        info = payload["sheets"][d.name]
        unique = info["key_unique"]
        summary.append(
            [
                d.name,
                d.presence,
                ", ".join(info["key"]) if isinstance(info["key"], list) else info["key"],
                "" if unique is None else str(unique["golden"] and unique["agent"]),
                d.rows["golden"],
                d.rows["agent"],
                d.rows["paired"],
                d.rows[MISSING],
                d.rows[EXTRA],
                *[info["counts"][s] for s in STATUSES],
                info["score"],
            ]
        )
    t = payload["totals"]
    summary.append(["TOTAL", "", "", "", "", "", "", "", "", *[t[s] for s in STATUSES], t["score"]])
    _style(summary)

    fills = {s: PatternFill("solid", fgColor=c) for s, c in _FILLS.items() if c}
    for d in diffs:
        ws = wb.create_sheet(d.name[:31])
        ws.append(["KEY", "GOLDEN_ROW", "AGENT_ROW", "COLUMN", "GOLDEN", "AGENT", "STATUS"])
        for cell in d.cells:
            withheld = keys.is_withheld(cell.column)
            g = WITHHELD if withheld and _raw(cell.golden) else _cell_value(cell.golden)
            a = WITHHELD if withheld and _raw(cell.agent) else _cell_value(cell.agent)
            ws.append([cell.key, cell.golden_row, cell.agent_row, cell.column, g, a, cell.status])
            fill = fills.get(cell.status)
            if fill:
                ws.cell(ws.max_row, 7).fill = fill
        _style(ws)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _style(ws) -> None:
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    if ws.max_row > 1:
        ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        width = max((len(str(c.value)) for c in col if c.value is not None), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 8), 60)


def write_routing_csv(path: Path, diffs: list[SheetDiff]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sheet", "column", "status_summary", "origin_tag"])
        for d in diffs:
            per_col: dict[str, Counter[str]] = {}
            for cell in d.cells:
                per_col.setdefault(cell.column, Counter())[cell.status] += 1
            for column, counts in per_col.items():
                summary = "; ".join(f"{s}={counts[s]}" for s in STATUSES if counts[s])
                writer.writerow([d.name, column, summary, ""])


def find_build(agent: Path, depth: int = 5) -> dict | None:
    """The build that produced ``agent``: ``CODEGEN_BUILD.json`` (``codegen
    generate``) or ``run_meta.json``'s ``build`` (an App run) in the
    workbook's folder or up to ``depth`` folders above it. None = unknown."""
    folder = Path(agent).resolve().parent
    for candidate in [folder, *list(folder.parents)[:depth]]:
        for name in BUILD_FILES:
            path = candidate / name
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            build = data.get("build") if name == "run_meta.json" else data
            if isinstance(build, dict) and build.get("line") and (
                    build.get("sha") not in (None, "", "unknown") or build.get("src_tree")):
                return {**build, "file": str(path)}
    return None


def header_facts(keys: KeyConfig, pair_mode: str, build: dict | None) -> dict:
    """What every report states first: the agent's build, the ignored set and,
    for a non-key pairing, the banner."""
    facts: dict = {"agent_build": build["line"] if build else None,
                   "agent_build_file": build["file"] if build else None,
                   "ignored_set": list(keys.needs_assignment), "pair_mode": pair_mode}
    if pair_mode != "key":
        facts["banner"] = (f"PAIR MODE {pair_mode.upper()}: rows paired by "
                           f"{'ordinal position' if pair_mode == 'position' else 'normalized key'}"
                           ", NOT by the natural key — not the validation score")
    return facts


def agent_build(agents: list[Path]) -> tuple[dict | None, str | None]:
    """(build, None) when every agent workbook has the SAME build identity,
    else (None, why)."""
    builds = [find_build(a) for a in agents]
    if any(b is None for b in builds):
        return None, UNSCORED
    if len({b["line"] for b in builds}) > 1:
        return None, (f"{UNSCORED.split(':')[0]}: the agent workbooks come from different "
                      f"builds {sorted({b['line'] for b in builds})}")
    return builds[0], None


def run_pair(golden: Path, agent: Path | list[Path], out: Path, keys_path: Path,
             pair_mode: str = "key", build: dict | None = None) -> dict:
    keys = load_keys(keys_path)
    diffs = diff_workbooks(golden, agent, keys, pair_mode=pair_mode)
    payload = score_payload(golden, agent, keys_path, diffs,
                            header_facts(keys, pair_mode, build))
    out.mkdir(parents=True, exist_ok=True)
    (out / "score.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_diff_xlsx(out / "diff.xlsx", payload, diffs, keys)
    write_routing_csv(out / "routing.csv", diffs)
    return payload


# --------------------------------------------------------------------- batch


def find_pairs(directory: Path) -> tuple[dict[str, tuple[Path, Path]], list[str]]:
    """Pairs in ``directory``: subfolders with one golden + one agent xlsx, and
    ``<pair>_golden.xlsx`` / ``<pair>_agent.xlsx`` couples at the top level."""
    pairs: dict[str, tuple[Path, Path]] = {}
    problems: list[str] = []

    def xlsx(folder: Path) -> list[Path]:
        return sorted(p for p in folder.glob("*.xlsx") if not p.name.startswith("~$"))

    for sub in sorted(p for p in directory.iterdir() if p.is_dir()):
        files = xlsx(sub)
        if not files:
            continue
        golden = [p for p in files if "golden" in p.stem.lower()]
        agent = [p for p in files if "agent" in p.stem.lower() and p not in golden]
        if len(golden) == 1 and len(agent) == 1:
            pairs[sub.name] = (golden[0], agent[0])
        else:
            problems.append(
                f"{sub.name}: needs exactly one *golden*.xlsx and one *agent*.xlsx "
                f"(found {len(golden)} golden, {len(agent)} agent)"
            )
    flat: dict[str, dict[str, Path]] = defaultdict(dict)
    for p in xlsx(directory):
        m = re.fullmatch(r"(.+?)[_-](golden|agent)", p.stem, flags=re.IGNORECASE)
        if m:
            flat[m.group(1)][m.group(2).lower()] = p
        else:
            problems.append(f"{p.name}: not named <pair>_golden.xlsx / <pair>_agent.xlsx")
    for name, sides in sorted(flat.items()):
        if name in pairs:
            problems.append(f"{name}: both a folder and top-level files — folder used")
        elif set(sides) == {"golden", "agent"}:
            pairs[name] = (sides["golden"], sides["agent"])
        else:
            problems.append(f"{name}: has no {'agent' if 'golden' in sides else 'golden'} file")
    return pairs, problems


def run_batch(directory: Path, out: Path, keys_path: Path,
              pair_mode: str = "key") -> dict:
    pairs, problems = find_pairs(directory)
    summary: dict = {"pairs": {}, "skipped": problems, "unscored": {}}
    for name, (golden, agent) in pairs.items():
        build = find_build(agent)
        if build is None:
            summary["unscored"][name] = UNSCORED
            continue
        payload = run_pair(golden, agent, out / name, keys_path,
                           pair_mode=pair_mode, build=build)
        summary["pairs"][name] = {
            "golden": str(golden),
            "agent": str(agent),
            "agent_build": payload["agent_build"],
            "totals": payload["totals"],
            "warnings": payload["warnings"],
        }
    out.mkdir(parents=True, exist_ok=True)
    (out / "batch_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


# ----------------------------------------------------------------------- CLI


def _print_header(payload: dict) -> None:
    print(f"AGENT BUILD: {payload.get('agent_build')}")
    print(f"IGNORED (never scored): {', '.join(payload.get('ignored_set') or [])}")
    if payload.get("banner"):
        print(payload["banner"])


def _print_pair(payload: dict, out: Path) -> None:
    _print_header(payload)
    for name, s in payload["sheets"].items():
        c = s["counts"]
        line = ", ".join(f"{k} {c[k]}" for k in STATUSES)
        print(f"{name}: score {s['score']}; {line}")
    t = payload["totals"]
    print(f"TOTAL: score {t['score']}; " + ", ".join(f"{k} {t[k]}" for k in STATUSES))
    for w in payload["warnings"]:
        print(f"WARNING {w}")
    print(f"wrote {out / 'score.json'}, {out / 'diff.xlsx'}, {out / 'routing.csv'}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--golden", type=Path)
    ap.add_argument("--agent", type=Path, nargs="+",
                    help="the agent IIG workbook(s) - one per feed of the pair; several "
                         "are compared as their union")
    ap.add_argument("--batch", type=Path, help="directory of golden / agent pairs")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--keys", type=Path, default=DEFAULT_KEYS)
    ap.add_argument("--pair-mode", choices=PAIR_MODES, default="key",
                    help="Row pairing: key (default - the natural key ONLY; rows it "
                         "cannot pair stay missing / extra), position or fuzzy (explicit, "
                         "bannered - not the validation score)")
    args = ap.parse_args(argv)
    if args.batch:
        if args.golden or args.agent:
            ap.error("--batch takes no --golden / --agent")
        summary = run_batch(args.batch, args.out, args.keys,
                            pair_mode=args.pair_mode)
        for name, p in summary["pairs"].items():
            print(f"{name}: score {p['totals']['score']}; mismatch {p['totals'][MISMATCH]}")
        for problem in summary["skipped"]:
            print(f"SKIPPED {problem}")
        for name, why in summary["unscored"].items():
            print(f"UNSCORED {name}: {why}")
        print(f"wrote {args.out / 'batch_summary.json'}")
        return 1 if summary["unscored"] else 0
    if not (args.golden and args.agent):
        ap.error("--golden and --agent are required (or --batch)")
    agents = list(args.agent)
    build, why = agent_build(agents)
    if build is None:
        print(f"{why} ({BUILD_FILES[0]} / run_meta.json 'build' must sit next to each "
              "agent workbook or up to 5 folders above it, one build for all - "
              "regenerate with the current codegen)")
        return 1
    payload = run_pair(args.golden, agents if len(agents) > 1 else agents[0], args.out,
                       args.keys, pair_mode=args.pair_mode, build=build)
    _print_pair(payload, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
