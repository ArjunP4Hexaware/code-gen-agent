"""Cell-level diff of an agent IIG workbook against a golden one (openpyxl + PyYAML).

    python tools/iig_diff.py --golden <golden.xlsx> --agent <agent.xlsx> [<more.xlsx> ...]
        --out <dir>
    python tools/iig_diff.py --batch <pairs dir> --out <dir>
        [--keys tools/iig_keys.yaml] [--pair-mode identity|key|position|fuzzy]
        [--group-index <csv> ...]

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

Row pairing — ``--pair-mode identity`` (default, 2026-10-13) pairs a golden
row with the agent row that describes the SAME THING, never by a generated name
(the prod goldens name pipelines / notebooks in a legacy convention, the agent
in the EDO standard — zero rows paired on pair_2):

* each golden row's FEED and FLOW come from the group index
  (``docs/acfc/iig_goldens/01_pair_group_index.csv``: GROUP_ID / PIPELINE_ID ->
  flow_type file_to_stg / stg_to_std + matched_table), the feed matched to the
  agent workbook (one per feed) whose name or target table it is — a golden row
  of a feed the agent did not write is out of scope; each agent row's feed is its
  workbook, its flow the sheet's or its semantic cells (LAYER_NAME,
  PIPELINE_DESCRIPTION, PROCESS_NAME);
* per sheet the IDENTITY (``identity`` in iig_keys.yaml: e.g. schedule = feed x
  flow, ingestion = feed x flow x target table, DQ = feed x table x column x
  rule class, email = feed x flow x status), every value normalized (case,
  separators, a table's schema prefix); a component one side never states is
  dropped (warned), a row whose identity stays incomplete is left unpaired;
* a sheet with NO identity pairs by position only when both sides have the
  same number of rows — otherwise its rows stay unpaired, said in a warning;
* CONVENTION columns (``convention_columns``: PIPELINE_NAME, the notebook
  names, TEMPLATE_NAME, ...) are never used to pair and never scored: status
  ``convention``, counted with how many differ;
* every sheet reports rows paired by identity / by position / unpaired, so a
  score is never read without how its rows were matched.

``--pair-mode key`` keeps the natural key per sheet below (the 2026-10-12
rule: rows it cannot pair stay missing / extra). Position (``--pair-mode
position``) and normalized keys (``--pair-mode fuzzy``) are explicit only and
print a banner: not the validation score. Pairing is hash-indexed and
diff.xlsx is written in one pass: a 3,000-row sheet diffs in seconds.

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

Sheets match caselessly on their first 31 characters. Across templates
(iig_keys.yaml ``sheet_aliases``, 2026-10-13): an iig_v1 golden
ALL_FILES_STATIC_INFORMATION is compared with the iig_v2 agent
FILE_ADLS_INGESTION_DETAILS, reported as ``ALL_FILES_STATIC_INFORMATION →
FILE_ADLS_INGESTION_DETAILS``: a golden file row pairs with the agent row of
the feed that names that file (``file_name_tokens``: case, separators,
extension, CCYY_MM = YYYY_MM = ``*``), scoped like every sheet; only the
mapped columns (the headers both templates have) are compared, every other
column is ``not comparable`` (never missing / extra).

An OBJECT_ID in a key is replaced by the table it resolves to in its OWN
workbook — the TGT_TABLE_NAME of the ADLS_DELTA / STGDELTA_STDDELTA / RDBMS
row with the same (GROUP_ID, OBJECT_ID), else the same OBJECT_ID when
every such row names one table; unresolved ids are listed as
``unresolved_object_ids`` in score.json. Every cell of a paired row is one of:

* ``exact``            — same value as written (None and "" are the same);
* ``normalized``       — equal once case, whitespace, trailing zeros, NULL vs
  empty and path separators are normalized, or once each ENVIRONMENT value
  (``environment_tokens`` in iig_keys.yaml: the D1 storage prefix / catalogs
  the agent runs with, the prod ones a golden carries) is replaced by its token;
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

Like with like (2026-10-13, ``--scope feeds`` default, ``--scope all`` off): a
golden exported for a whole GROUP_ID carries every feed of the group, a run
writes its own. The feeds are what the file / object / table columns name
(``SCOPE_COLUMNS``; extension and date tokens dropped). A golden row the agent
did not pair that names ANOTHER feed of the golden and none of the agent's is
``out-of-scope`` (``out of scope: N rows`` per sheet), never missing; a row
that names no feed stays missing. A sheet only one side has is ``sheet not in
<side>`` with NO score; the golden / agent layouts (iig_v1 7 sheets, iig_v2 8)
are detected and a difference prints a ``NOTE`` that informs only (never a
template switch: iig_v1 and iig_v2 also differ in naming convention, which is
not scored). The overall ``score`` keeps its
meaning (out-of-scope counted as missing); ``comparable_score`` is over the
scoped cells of the sheets BOTH sides have. A repeated key is named in its
warning (console / score.json only — never in the scrubbed export).

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

Scrubbed evidence (2026-10-12) — the golden carries real client values, the
operator hands mismatch evidence home WITHOUT hand-scrubbing:

    python tools/iig_diff.py --golden G --agent A --out O --export-scrubbed DIR

writes ``DIR/mismatches.md`` (one line per mismatch / missing / extra cell),
``DIR/row_keys.md`` (per sheet: the key, every golden and agent row's key,
paired or not) and ``DIR/SELF_CHECK.md`` (counts only). Every value written is
scrubbed: (a) ``scripts/scrub_check.py``'s classes + the local denylist
(``docs/acfc/denylist_local.txt`` if present) -> ``<CLASS>``; (b) a token
(alphanumeric run) found in the golden but not in the committed fixtures'
token universe -> ``G<n>``, any other token outside the universe -> ``A<n>``
(one map for the whole export). Kept: tokens under 3 characters, numbers
under 5 digits, fixture tokens. The written files are re-scanned with
scrub_check; any hit = exit 2, the two evidence files deleted, the CLASS named
(never the term).

    python tools/iig_diff.py --golden G --golden-structure [--out O]

prints (and writes ``golden_structure.md`` / ``.json`` under ``--out``) the row
count per GROUP_ID (PIPELINE_ID on a sheet without GROUP_ID) per sheet, the
distinct OBJECT_NAME / TGT_TABLE_NAME / FILE_NAME counts, and which groups
share a table name — counts and ``group#k`` labels only, never an id or a name.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import functools
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import yaml
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font, PatternFill

DEFAULT_KEYS = Path(__file__).resolve().parent / "iig_keys.yaml"
# The gitignored values of iig_keys.yaml's ``local:<name>`` environment tokens
# (prod names never enter git); absent = those tokens are listed unresolved.
DEFAULT_ENV_LOCAL = Path(__file__).resolve().parent.parent / "codegen-state" / "env_tokens.yaml"
BUILD_FILES = ("CODEGEN_BUILD.json", "run_meta.json")
UNSCORED = "unscored: agent workbook has no build identity"

# ----------- pair-mode constants
PAIR_MODES = ("identity", "key", "position", "fuzzy")
# How a row pair was made (2026-10-13): by the row's IDENTITY (iig_keys.yaml
# ``identity`` — what the row describes, never a generated name), by position
# (a sheet with no identity whose row counts match), or by the natural key
# (``--pair-mode key``).
BY_IDENTITY, BY_POSITION, BY_KEY = "identity", "position", "key"
_FUZZY_PREFIXES = re.compile(
    r"^(PL_File_|PL_|NB_|WF_)", re.IGNORECASE,
)

EXACT = "exact"
NORMALIZED = "normalized"
MISMATCH = "mismatch"
MISSING = "missing-in-agent"
EXTRA = "extra-in-agent"
ASSIGN = "needs_assignment"
# A column whose values are generated under a naming convention
# (iig_keys.yaml ``convention_columns``: PIPELINE_NAME, notebook names, ...):
# never used to pair, never scored — counted on its own, with how many differ.
CONVENTION = "convention"
# 2026-10-13: a golden row of ANOTHER feed of the group (the golden is a
# whole-GROUP_ID export, the agent wrote the run's own feeds) — reported as
# "out of scope: N rows", never as missing.
OUT_OF_SCOPE = "out-of-scope"
STATUSES = (EXACT, NORMALIZED, MISMATCH, MISSING, EXTRA, ASSIGN, OUT_OF_SCOPE, CONVENTION)
SCORED = (EXACT, NORMALIZED, MISMATCH, MISSING, EXTRA)
# The overall score keeps its meaning (an out-of-scope cell counts as missing);
# ``comparable_score`` is the one over scoped cells of shared sheets only.
LEGACY_SCORED = (*SCORED, OUT_OF_SCOPE)
# The per-column breakdown (score.json ``column_counts``, the scrubbed sheets.md).
COLUMN_STATUSES = SCORED

# The IIG template layouts (metadata.templates in config/config.yaml; iig_v1 =
# the 7-tab SFMC reference, iig_v2 = the PRX 8-sheet layout).
TEMPLATE_SHEETS: dict[str, tuple[str, ...]] = {
    "iig_v1": ("DATA_FACTORY_PIPELINE_SCHEDULE", "ADLS_DELTA_INGESTION_DETAILS",
               "STGDELTA_STDDELTA_INGESTION_DET", "DATA_QUALITY_RULES",
               "DATABRICKS_NOTEBOOK_DETAILS", "EMAIL_TEMPLATE_CONFIG",
               "ALL_FILES_STATIC_INFORMATION"),
    "iig_v2": ("DATA_FACTORY_PIPELINE_SCHEDULE", "FILE_ADLS_INGESTION_DETAILS",
               "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET",
               "ADLS_FIXED_WIDTH_HANDLER", "DATABRICKS_NOTEBOOK_DETAILS",
               "DATA_QUALITY_RULES", "EMAIL_TEMPLATE_CONFIG"),
}
# Columns that name a FEED (its file, object or table): the agent union's
# values here are the scope a group-wide golden is restricted to.
SCOPE_COLUMNS = ("FILE_NAME", "SRC_FILE_NAME", "FILE_NAME_PATTERN", "SRC_FILE_NAME_PATTERN",
                 "OBJECT_NAME", "TGT_TABLE_NAME", "SRC_TABLE_NAME", "TGT_TABLE")
SCOPE_MODES = ("feeds", "all")

NULL_TOKENS = {"NULL"}
WITHHELD = "<withheld>"
# tools/build_goldens.py's provenance column (the GROUP_ID exports a de-
# duplicated golden row came from): never a cell, shown in row_keys.md only.
SOURCE_COLUMN = "_source_group_ids"
SUMMARY_SHEET = "_DIFF_SUMMARY"
_NUMBER = re.compile(r"[+-]?\d+\.\d+")
_FILLS = {
    EXACT: None,
    NORMALIZED: "DDEBF7",
    MISMATCH: "F8CBAD",
    MISSING: "FFE699",
    EXTRA: "D9D2E9",
    ASSIGN: "E7E6E6",
    OUT_OF_SCOPE: "F2F2F2",
    CONVENTION: "FCE4D6",
}


# --------------------------------------------------------------------- config


def sheet_id(name: str) -> str:
    """A sheet's identity: caseless, cut to Excel's 31 characters, so the
    framework table ``stgdelta_stddelta_ingestion_details`` is the IIG sheet
    ``STGDELTA_STDDELTA_INGESTION_DET``."""
    return name.strip().upper()[:31]


@dataclass(frozen=True)
class EnvToken:
    """One environment token: every value (any environment) it stands for."""
    token: str
    values: tuple[str, ...] = ()               # literals, casefolded
    patterns: tuple[re.Pattern, ...] = ()      # scrub_check classes
    unresolved: tuple[str, ...] = ()           # ``local:<name>`` with no local value

    def apply(self, text: str) -> str:
        for value in self.values:
            text = re.sub(rf"(?<![a-z0-9]){re.escape(value)}(?![a-z0-9])", self.token, text)
        for pattern in self.patterns:
            text = pattern.sub(self.token, text)
        return text


@dataclass(frozen=True)
class SheetAlias:
    """iig_keys.yaml ``sheet_aliases``: a golden sheet compared with the agent
    sheet of another template that holds the same facts."""
    golden_sheet: str
    agent_sheet: str
    golden_files: tuple[str, ...]
    agent_files: tuple[str, ...] = ()
    files_from_sheet: str | None = None
    files_from_columns: tuple[str, ...] = ()
    columns: tuple[tuple[str, str], ...] = ()     # (golden header, agent header)

    @property
    def label(self) -> str:
        return f"{self.golden_sheet} \u2192 {self.agent_sheet}"


@dataclass(frozen=True)
class KeyConfig:
    sheets: dict[str, list[str]]
    needs_assignment: list[str]
    withhold_values: list[str]
    ignore_sheets: list[str]
    object_id_column: str = "OBJECT_ID"
    group_id_column: str = "GROUP_ID"
    object_sources: dict[str, list[str]] = field(default_factory=dict)
    env_tokens: tuple[EnvToken, ...] = ()
    # 2026-10-13 identity pairing (iig_keys.yaml identity / flow /
    # convention_columns / group_index)
    identity: dict[str, list[str]] = field(default_factory=dict)
    flow_sheets: dict[str, str] = field(default_factory=dict)
    flow_rules: tuple[tuple[str, re.Pattern[str], str], ...] = ()
    convention_columns: tuple[str, ...] = ()
    group_index: tuple[str, ...] = ()
    sheet_aliases: tuple[SheetAlias, ...] = ()
    file_name_tokens: tuple[re.Pattern[str], ...] = ()
    # 2026-10-14: the columns naming a row's FILE, per sheet (identity @file)
    file_columns: dict[str, list[str]] = field(default_factory=dict)

    def identity_for(self, sheet: str) -> list[str] | None:
        return _by_sheet(self.identity, sheet)

    def is_convention(self, column: str) -> bool:
        return column.upper() in {c.upper() for c in self.convention_columns}

    def env_state(self) -> dict[str, str]:
        """token -> 'resolved' / 'unresolved: local:<name>, …' (names, never values)."""
        return {t.token: ("unresolved: " + ", ".join(f"local:{n}" for n in t.unresolved)
                          if t.unresolved else "resolved") for t in self.env_tokens}

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


def _env_tokens(path: Path, raw: object, local_path: Path | None) -> tuple[EnvToken, ...]:
    """``environment_tokens``: token -> its values, each a literal, a
    ``scrub_class:<name>`` (that scripts/scrub_check.py pattern) or a
    ``local:<name>`` (read from the gitignored ``local_path``)."""
    if not raw:
        return ()
    local: dict = {}
    if local_path is not None and Path(local_path).is_file():
        local = yaml.safe_load(Path(local_path).read_text(encoding="utf-8")) or {}
    classes = None
    out = []
    for token, specs in dict(raw).items():
        values, patterns, unresolved = [], [], []
        for spec in [specs] if isinstance(specs, str) else list(specs or []):
            spec = str(spec)
            if spec.startswith("scrub_class:"):
                if classes is None:
                    classes = dict(load_scrub_check().GENERIC_PATTERNS)
                name = spec.split(":", 1)[1]
                if name not in classes:
                    raise ValueError(f"{path}: environment_tokens.{token}: no scrub_check "
                                     f"class {name!r}")
                patterns.append(classes[name])
            elif spec.startswith("local:"):
                name = spec.split(":", 1)[1]
                given = local.get(name)
                given = [given] if isinstance(given, str) else list(given or [])
                values += [str(v).casefold() for v in given if str(v).strip()]
                if not any(str(v).strip() for v in given):
                    unresolved.append(name)
            else:
                values.append(spec.casefold())
        out.append(EnvToken(str(token), tuple(values), tuple(patterns),
                            tuple(unresolved)))
    return tuple(out)


def load_keys(path: Path, env_local: Path | None = DEFAULT_ENV_LOCAL) -> KeyConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    known = {"sheets", "needs_assignment", "withhold_values", "ignore_sheets", "object_tables",
             "environment_tokens", "identity", "flow", "convention_columns", "group_index",
             "sheet_aliases", "file_name_tokens", "file_columns"}
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
        env_tokens=_env_tokens(path, raw.get("environment_tokens"), env_local),
        identity=_column_lists(path, "identity", raw.get("identity")),
        **_flow(path, raw.get("flow")),
        convention_columns=tuple(str(c) for c in raw.get("convention_columns") or []),
        group_index=tuple(str(c) for c in raw.get("group_index") or []),
        sheet_aliases=_sheet_aliases(path, raw.get("sheet_aliases")),
        file_name_tokens=tuple(re.compile(str(t), re.IGNORECASE)
                               for t in raw.get("file_name_tokens") or []),
        file_columns=_column_lists(path, "file_columns", raw.get("file_columns")),
    )


_ALIAS_KEYS = {"agent_sheet", "golden_files", "agent_files", "agent_files_from", "columns"}


def _sheet_aliases(path: Path, raw: object) -> tuple[SheetAlias, ...]:
    out = []
    for golden, spec in dict(raw or {}).items():
        spec = dict(spec or {})
        unknown = set(spec) - _ALIAS_KEYS
        if unknown:
            raise ValueError(f"{path}: unknown sheet_aliases.{golden} keys {sorted(unknown)}")
        if not (spec.get("agent_sheet") and spec.get("golden_files") and spec.get("columns")):
            raise ValueError(f"{path}: sheet_aliases.{golden} needs agent_sheet, golden_files "
                             "and columns")
        source = dict(spec.get("agent_files_from") or {})
        out.append(SheetAlias(
            str(golden), str(spec["agent_sheet"]),
            tuple(str(c) for c in spec["golden_files"]),
            tuple(str(c) for c in spec.get("agent_files") or []),
            str(source["sheet"]) if source.get("sheet") else None,
            tuple(str(c) for c in source.get("columns") or []),
            tuple((str(g), str(a)) for g, a in dict(spec["columns"]).items())))
    return tuple(out)


def _flow(path: Path, raw: object) -> dict:
    raw = raw or {}
    unknown = set(raw) - {"sheets", "rules"}
    if unknown:
        raise ValueError(f"{path}: unknown flow keys {sorted(unknown)}")
    rules = []
    for index, rule in enumerate(raw.get("rules") or []):
        if not isinstance(rule, dict) or set(rule) != {"column", "match", "flow"}:
            raise ValueError(f"{path}: flow.rules[{index}] needs exactly column, match, flow")
        rules.append((str(rule["column"]).upper(), re.compile(str(rule["match"]), re.IGNORECASE),
                      str(rule["flow"])))
    return {"flow_sheets": {str(k): str(v) for k, v in (raw.get("sheets") or {}).items()},
            "flow_rules": tuple(rules)}


# --------------------------------------------------------------- group index

_ID_TEXT = re.compile(r"\.0+$")


def _id(value: object) -> str:
    """An id cell as text: ``180251``, ``180251.0`` and `` 180251 `` are one id."""
    return _ID_TEXT.sub("", _raw(value).strip())


class GroupIndex:
    """docs/acfc/iig_goldens/01_pair_group_index.csv (+ the round-2 addendum):
    a golden GROUP_ID / PIPELINE_ID -> (flow_type, matched_table). Rows the
    extraction did not match (NOT_FOUND) are skipped."""

    def __init__(self, paths: list[Path]) -> None:
        self.by_group: dict[str, tuple[str, str]] = {}
        self.by_pipeline: dict[str, tuple[str, str]] = {}
        self.files: list[str] = []
        for path in paths:
            if not path.is_file():
                continue
            self.files.append(str(path))
            with path.open(encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    flow = (row.get("flow_type") or "").strip()
                    table = (row.get("matched_table") or "").strip()
                    if not flow or not table or (row.get("confidence") or "") == "NOT_FOUND":
                        continue
                    if _id(row.get("group_id")):
                        self.by_group[_id(row.get("group_id"))] = (flow, table)
                    if _id(row.get("pipeline_id")):
                        self.by_pipeline[_id(row.get("pipeline_id"))] = (flow, table)

    def lookup(self, row: dict[str, object], canon: dict[str, str], keys: KeyConfig
               ) -> tuple[str, str] | None:
        """(flow, table) of a golden row: its GROUP_ID, else its PIPELINE_ID,
        else the one group build_goldens says it came from."""
        group = canon.get(keys.group_id_column.upper())
        if group and _id(row.get(group)) in self.by_group:
            return self.by_group[_id(row.get(group))]
        pipeline = canon.get("PIPELINE_ID")
        if pipeline and _id(row.get(pipeline)) in self.by_pipeline:
            return self.by_pipeline[_id(row.get(pipeline))]
        source = canon.get(SOURCE_COLUMN.upper())
        ids = [_id(s) for s in _raw(row.get(source)).split(",") if s.strip()] if source else []
        found = {self.by_group[i] for i in ids if i in self.by_group}
        return next(iter(found)) if len(found) == 1 else None


_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def identity_value(value: object, column: str = "") -> str | None:
    """One identity component, normalized: lowercased, separators dropped; a
    TABLE column also drops its schema prefix (``stg_cm.Sd_X`` -> ``sdx``)."""
    text = _raw(value).strip()
    if not text:
        return None
    if "TABLE" in column.upper() and "." in text:
        text = text.rsplit(".", 1)[1]
    return _NON_ALNUM.sub("", text.lower()) or None


_EXTENSION = re.compile(r"\.[a-z0-9]{1,5}$")
_NOT_FILE_CHAR = re.compile(r"[^0-9a-z#]+")


def file_identity(value: object, tokens: tuple[re.Pattern[str], ...]) -> str | None:
    """A file name / pattern as an identity: lowercased, directory and extension
    dropped, each ``file_name_tokens`` match (date tokens, digits of a date,
    wildcards) dropped WHEREVER it sits, separators dropped —
    ``SD_X_CCYY_MM.csv`` = ``SD_X_YYYY_MM.csv`` = ``SD_X_*.csv`` = ``SD_X*``.
    2026-10-13 (pair_12, 0 rows paired): the CAQH inventory names a file
    ``YYYYMMDD_<n>_<n>_<V>_*_P_I_1_T.txt`` (a date FIRST, a wildcard INSIDE),
    the agent's SRC_FILE_NAME ``<n>_<n>_<V>_P_I_1_T*`` — a marker kept inside
    the identity made them two files."""
    text = _raw(value).strip().lower().replace("\\", "/").rsplit("/", 1)[-1]
    text = _EXTENSION.sub("", text)
    for pattern in tokens:
        text = pattern.sub("#", text)
    text = _NOT_FILE_CHAR.sub("", text).replace("#", "")
    return text or None


def header_id(name: str) -> str:
    """A header as the templates are compared: case and separators dropped."""
    return _NON_ALNUM.sub("", name.lower())


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


def env_normalize(text: str, env: tuple[EnvToken, ...]) -> str:
    for token in env:
        text = token.apply(text)
    return text


def classify(golden: object, agent: object, env: tuple[EnvToken, ...] = ()) -> str:
    if _raw(golden) == _raw(agent):
        return EXACT
    g, a = normalize(golden), normalize(agent)
    if g == a:
        return NORMALIZED
    if env and g and a and env_normalize(g, env) == env_normalize(a, env):
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
    method: str = ""        # BY_IDENTITY / BY_POSITION / BY_KEY; "" = left unpaired


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


_WORD = re.compile(r"[a-z0-9]+")
_DATE_OR_WILD = re.compile(r"^(?:[yc]{2,4}|mm|dd|[yc]{4}mm(?:dd)?|mmdd[yc]{2,4}|\d{4,8})$")


def _stem_tokens(value: object) -> tuple[str, ...]:
    """A feed name's tokens: lowercased words, the extension and trailing
    date / wildcard tokens dropped (``NB_CM_NORTH_YYYYMMDD.txt`` -> nb cm north)."""
    text = re.sub(r"\.[a-z0-9]{1,5}$", "", _raw(value).strip().lower())
    tokens = _WORD.findall(text)
    while len(tokens) > 1 and _DATE_OR_WILD.match(tokens[-1]):
        tokens.pop()
    return tuple(tokens)


def _feed_stems(sheets: dict[str, Sheet]) -> set[tuple[str, ...]]:
    stems: set[tuple[str, ...]] = set()
    for sheet in sheets.values():
        canon = sheet.canon()
        cols = [canon[c] for c in SCOPE_COLUMNS if c in canon]
        for _, row in sheet.rows:
            for col in cols:
                stem = _stem_tokens(row.get(col))
                if stem and len("".join(stem)) >= 3:
                    stems.add(stem)
    return stems


class StemIndex:
    """Feed stems (token tuples) -> the feeds that write them, looked up by the
    n-grams of a cell's words (2026-10-13: ``_names_any`` compared every row
    with every stem — 3,000 golden files x 3,000 stems timed out on D1)."""

    def __init__(self, stems: dict[tuple[str, ...], set]) -> None:
        self.stems = stems
        self.lengths = sorted({len(s) for s in stems})

    def named(self, words: list[list[str]]) -> set:
        found: set = set()
        for cell in words:
            for n in self.lengths:
                for i in range(len(cell) - n + 1):
                    feeds = self.stems.get(tuple(cell[i:i + n]))
                    if feeds:
                        found |= feeds
        return found


def _row_words(row: dict[str, object], canon: dict[str, str],
               tables: ObjectTables | None) -> list[list[str]]:
    words = [_WORD.findall(_raw(v).lower()) for v in row.values()]
    if tables is not None:
        table = tables.table_for(row, canon)
        if table:
            words.append(_WORD.findall(table.lower()))
    return words


def feed_of_agent_row(number: int) -> int:
    """An agent row's feed: the workbook it came from (``ROW_STRIDE``)."""
    return number // ROW_STRIDE


class FeedScope:
    """Like with like (2026-10-13): a golden exported for a whole GROUP_ID
    holds the rows of every feed of the group; the agent wrote the run's own.
    The feeds are what the files / objects / tables name (``SCOPE_COLUMNS``,
    as a whole run of words, extension and date tokens dropped). A golden row
    the agent did not pair is OUT of scope only on positive evidence: it names
    another feed of the golden and none of the agent's. A row that names no
    feed at all (an unresolved OBJECT_ID, a group-level row) stays missing.
    Off when the agent names no feed, or ``--scope all``. Hash-indexed: every
    lookup is by n-gram, never every stem against every row."""

    def __init__(self, agent: dict[str, Sheet], golden: dict[str, Sheet], keys: KeyConfig,
                 enabled: bool = True) -> None:
        by_feed: dict[tuple[str, ...], set] = defaultdict(set)
        for sheet in agent.values():
            canon = sheet.canon()
            cols = [canon[c] for c in SCOPE_COLUMNS if c in canon]
            for number, row in sheet.rows:
                for col in cols:
                    stem = _stem_tokens(row.get(col))
                    if stem and len("".join(stem)) >= 3:
                        by_feed[stem].add(feed_of_agent_row(number))
        self.enabled = enabled
        self.stems = set(by_feed)
        self.agent_index = StemIndex(dict(by_feed))
        self.other = _feed_stems(golden) - self.stems
        self.other_index = StemIndex({s: {None} for s in self.other})
        self.active = enabled and bool(self.stems) and bool(self.other)

    def out_of_scope(self, row: dict[str, object], canon: dict[str, str],
                     tables: ObjectTables | None) -> bool:
        words = _row_words(row, canon, tables)
        return not self.agent_index.named(words) and bool(self.other_index.named(words))

    def feed_of(self, row: dict[str, object], canon: dict[str, str],
                tables: ObjectTables | None) -> int | None:
        """The ONE agent feed a golden row names, else None."""
        feeds = self.agent_index.named(_row_words(row, canon, tables))
        return next(iter(feeds)) if len(feeds) == 1 else None


def detect_template(names: list[str]) -> str | None:
    """iig_v1 (7 sheets) | iig_v2 (8 sheets) by sheet overlap; None if neither."""
    ids = {sheet_id(n) for n in names}
    if not ids:
        return None
    scored = sorted(((len(ids & {sheet_id(t) for t in tabs}) / len(ids | set(tabs)), name)
                     for name, tabs in TEMPLATE_SHEETS.items()), reverse=True)
    return scored[0][1] if scored[0][0] > 0 else None


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
        def named(values: list[str]) -> str:
            shown = ", ".join(repr(v) for v in values[:5])
            return shown + (f" (+{len(values) - 5} more)" if len(values) > 5 else "")

        facts["warnings"].append(
            f"key {key} is not unique (golden {len(dup_g)}, agent {len(dup_a)} duplicated"
            + (f"; golden: {named(dup_g)}" if dup_g else "")
            + (f"; agent: {named(dup_a)}" if dup_a else "")
            + ") — duplicates paired in sheet order"
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
    method: str = ""


@dataclass
class SheetDiff:
    name: str
    presence: str  # compared | golden-only | agent-only
    facts: dict
    cells: list[Cell] = field(default_factory=list)
    rows: dict = field(default_factory=dict)
    columns: dict = field(default_factory=dict)
    # kept for --export-scrubbed's row_keys.md; never written by the scorer
    pairs: list[RowPair] = field(default_factory=list, repr=False)
    sides: tuple = (None, None)       # (golden Sheet | None, agent Sheet | None)
    tables: tuple = (None, None)      # (golden ObjectTables, agent ObjectTables)
    out_of_scope_rows: int = 0        # golden rows of feeds the agent did not write
    # rows paired per method, rows left unpaired per side (in scope)
    pairing: dict = field(default_factory=dict)
    unpaired: dict = field(default_factory=dict)
    # every row's identity as text, per side: {"golden": {row: text}, "agent": ...}
    identity_text: dict = field(default_factory=dict)
    # the first golden / agent key values (unscrubbed; console + score.json only)
    key_samples: dict | None = None
    # the worksheet title in diff.xlsx when ``name`` is a display label
    # (a cross-template pair "<golden> → <agent>")
    title: str = ""
    # a cross-template sheet: the file names each side states (D1 only)
    file_samples: dict | None = None

    def counts(self) -> dict[str, int]:
        c = Counter(cell.status for cell in self.cells)
        return {s: c.get(s, 0) for s in STATUSES}

    def column_counts(self) -> dict[str, dict[str, int]]:
        """2026-10-13: per column (as the golden writes it), the cells of each
        scored status — which columns a sheet's score is made of."""
        out: dict[str, Counter[str]] = {}
        for cell in self.cells:
            if cell.status in COLUMN_STATUSES:
                out.setdefault(cell.column, Counter())[cell.status] += 1
        return {col: {s: c.get(s, 0) for s in COLUMN_STATUSES} for col, c in out.items()}


def _classify_pairs(pairs: list[RowPair], order: list[str], g_canon: dict, a_canon: dict,
                    keys: KeyConfig, tables: tuple, scope: FeedScope | None,
                    oos_rows: set[int] | None = None) -> tuple[list[Cell], set[int]]:
    """Every cell of every pair, with its status; + the golden rows out of
    scope (``oos_rows`` when the caller decided them, else the scope's test).
    A CONVENTION column's cell is ``convention`` — never scored."""
    cells: list[Cell] = []
    found: set[int] = set()
    for pair in pairs:
        g_row = pair.golden[1] if pair.golden else None
        a_row = pair.agent[1] if pair.agent else None
        if oos_rows is not None:
            out_of_scope = g_row is not None and a_row is None and pair.golden[0] in oos_rows
        else:
            out_of_scope = (g_row is not None and a_row is None and scope is not None
                            and scope.active and scope.out_of_scope(g_row, g_canon, tables[0]))
        if out_of_scope:
            found.add(pair.golden[0])
        for col in order:
            label = g_canon.get(col) or a_canon[col]
            in_g = g_row is not None and col in g_canon
            in_a = a_row is not None and col in a_canon
            if not (in_g or in_a):
                continue  # neither workbook has this row in this column: no cell
            g_val = g_row.get(g_canon[col]) if in_g else None
            a_val = a_row.get(a_canon[col]) if in_a else None
            if out_of_scope:
                status = OUT_OF_SCOPE
            elif keys.is_assignment(label):
                status = ASSIGN
            elif keys.is_convention(label):
                status = CONVENTION
            elif not in_g:
                status = EXTRA
            elif not in_a:
                status = MISSING
            else:
                status = classify(g_val, a_val, keys.env_tokens)
            cells.append(Cell(pair.key, pair.golden[0] if pair.golden else None,
                              pair.agent[0] if pair.agent else None, label, g_val, a_val,
                              status, pair.method))
    return cells, found


# ---------------------------------------------------------------- identity


@dataclass
class FeedContext:
    """Which FEED a row belongs to and which FLOW it is. Agent: its workbook
    (one IIG per feed); golden: the group index (GROUP_ID / PIPELINE_ID ->
    flow_type + matched_table) matched to the agent feed whose workbook name or
    table it is, else the one agent feed the row's cells name."""

    index: GroupIndex
    names: dict[str, int]           # normalized feed / table name -> agent feed
    scope: FeedScope
    keys: KeyConfig
    feeds: set[int] = field(default_factory=set)   # every agent feed (workbook)
    # tools/iig_identity_check.py: a golden paired with ITSELF — both sides take
    # their feed from the index's table (one workbook holds every feed)
    self_check: bool = False

    def golden(self, row: dict[str, object], canon: dict[str, str],
               tables: ObjectTables | None) -> tuple[int | None, str | None, bool]:
        """(feed, flow, foreign) — foreign: the index names a table no agent
        feed writes (another feed of the group: out of scope)."""
        hit = self.index.lookup(row, canon, self.keys)
        if hit is not None:
            flow, table = hit
            if self.self_check:
                return identity_value(table, "TABLE"), flow, False  # type: ignore[return-value]
            feed = self.names.get(identity_value(table, "TABLE") or "")
            return feed, flow, feed is None
        feed = self.scope.feed_of(row, canon, tables)
        if feed is None and len(self.feeds) == 1:
            feed = next(iter(self.feeds))       # one agent feed: an in-scope row is its
        return feed, None, False


def row_flow(sheet: str, row: dict[str, object], canon: dict[str, str],
             keys: KeyConfig) -> str | None:
    """A row's flow from the sheet (``flow.sheets``) or its semantic cells
    (``flow.rules``) — never from a generated name."""
    for name, flow in keys.flow_sheets.items():
        if sheet_id(name) == sheet_id(sheet):
            return flow
    for column, pattern, flow in keys.flow_rules:
        real = canon.get(column)
        if real and pattern.search(_raw(row.get(real)).strip()):
            return flow
    return None


def _parts(components: list[str], row: dict[str, object], canon: dict[str, str],
           tables: ObjectTables | None, feed: int | str | None, flow: str | None,
           files: tuple[list[str], tuple[re.Pattern[str], ...]] = ([], ())
           ) -> list[str | None]:
    out: list[str | None] = []
    for component in components:
        if component == FILE_COMPONENT:
            # the first file column the row fills, as a file identity
            names = (row.get(canon[c.upper()]) for c in files[0] if c.upper() in canon)
            out.append(next((i for i in (file_identity(v, files[1]) for v in names) if i),
                            None))
        elif component == "@feed":
            out.append(f"feed#{feed}" if feed is not None else None)
        elif component == "@flow":
            out.append(flow)
        elif component == "@table":
            table = tables.table_for(row, canon) if tables is not None else None
            out.append(identity_value(table, "TABLE"))
        else:
            real = canon.get(component.upper())
            out.append(identity_value(row.get(real), component) if real else None)
    return out


FILE_COMPONENT = "@file"


def _identity_pairs(name: str, golden: Sheet, agent: Sheet, components: list[str],
                    keys: KeyConfig, tables: tuple, ctx: FeedContext,
                    g_info: dict[int, tuple], oos: set[int], facts: dict,
                    texts: dict) -> list[RowPair] | None:
    """Pair on the sheet's identity, hash-indexed. None when no component
    survives (the caller then treats the sheet as having no identity)."""
    g_canon, a_canon = golden.canon(), agent.canon()
    files = (_by_sheet(keys.file_columns, name) or [], keys.file_name_tokens)
    g_parts = {n: _parts(components, row, g_canon, tables[0], g_info[n][0],
                         g_info[n][1] or row_flow(name, row, g_canon, keys), files)
               for n, row in golden.rows if n not in oos}
    def agent_side(n: int, row: dict) -> tuple:
        if ctx.self_check:
            feed, flow, _foreign = ctx.golden(row, a_canon, tables[1])
            return feed, flow or row_flow(name, row, a_canon, keys)
        return feed_of_agent_row(n), row_flow(name, row, a_canon, keys)

    a_parts = {n: _parts(components, row, a_canon, tables[1], *agent_side(n, row), files)
               for n, row in agent.rows}
    keep, dropped = [], []
    for i, component in enumerate(components):
        empty = [side for side, parts in (("golden", g_parts), ("agent", a_parts))
                 if parts and all(p[i] is None for p in parts.values())]
        (dropped if empty else keep).append(i)
        if empty:
            dropped[-1] = f"{component} (no {' / '.join(empty)} row states it)"
    facts["key"] = [components[i] for i in keep]
    facts["identity_dropped"] = dropped
    if dropped:
        facts["warnings"].append("identity component(s) dropped: " + "; ".join(dropped))
    if not keep:
        return None

    # A row that states NO flow (a master pipeline: no load leg) is its own kind
    # — it matches a row that states none; any other component left empty
    # makes the identity incomplete.
    flow_at = {i for i in keep if components[i] == "@flow"}
    # @file (2026-10-14, pair_12: 18 CAQH ADLS rows share feed x flow x table)
    # tells apart only the rows the other components leave EQUAL: a key that
    # is unique without it pairs without it, so a file-naming difference never
    # unpairs a row its table already identifies.
    file_at = {i for i in keep if components[i] == FILE_COMPONENT}
    base_keep = [i for i in keep if i not in file_at]

    def base(parts: list[str | None]) -> tuple[str | None, ...]:
        return tuple("-" if parts[i] is None and i in flow_at else parts[i] for i in base_keep)

    repeated: set[tuple] = set()
    if file_at:
        for parts in (g_parts, a_parts):
            counts = Counter(base(p) for p in parts.values())
            repeated |= {k for k, c in counts.items() if c > 1}
        facts["file_refined"] = len(repeated)

    def ident(parts: list[str | None]) -> tuple[str, ...] | None:
        chosen = base(parts)
        if chosen in repeated:
            chosen = (*chosen, *(parts[i] for i in sorted(file_at)))
        return None if any(v is None for v in chosen) else chosen  # type: ignore[return-value]

    for side, parts in (("golden", g_parts), ("agent", a_parts)):
        texts[side] = {n: " | ".join(p[i] or "<none>" for i in keep) for n, p in parts.items()}
    by_identity: dict[tuple[str, ...], list] = defaultdict(list)
    a_rows = dict(agent.rows)
    for n, parts in a_parts.items():
        key = ident(parts)
        if key is not None:
            by_identity[key].append((n, a_rows[n]))
    dup_a = [" | ".join(k) for k, rows in by_identity.items() if len(rows) > 1]
    seen: Counter[tuple[str, ...]] = Counter(
        k for k in (ident(p) for p in g_parts.values()) if k is not None)
    dup_g = [" | ".join(k) for k, n in seen.items() if n > 1]
    facts["key_unique"] = {"golden": not dup_g, "agent": not dup_a}
    facts["duplicate_keys"] = {"golden": dup_g, "agent": dup_a}
    if dup_g or dup_a:
        facts["warnings"].append(
            f"identity not unique (golden {len(dup_g)}, agent {len(dup_a)} repeated)"
            " — duplicates paired in sheet order")
    no_identity = {"golden": 0, "agent": 0}
    pairs: list[RowPair] = []
    for n, row in golden.rows:
        if n in oos:
            pairs.append(RowPair((n, row), None, "out of scope"))
            continue
        key = ident(g_parts[n])
        if key is None:
            no_identity["golden"] += 1
            pairs.append(RowPair((n, row), None, texts["golden"][n]))
            continue
        bucket = by_identity.get(key)
        partner = bucket.pop(0) if bucket else None
        pairs.append(RowPair((n, row), partner, texts["golden"][n],
                             BY_IDENTITY if partner else ""))
    for n, row in sorted((r for b in by_identity.values() for r in b), key=lambda r: r[0]):
        pairs.append(RowPair(None, (n, row), texts["agent"][n]))
    for n, row in agent.rows:
        if ident(a_parts[n]) is None:
            no_identity["agent"] += 1
            pairs.append(RowPair(None, (n, row), texts["agent"][n]))
    if no_identity["golden"] or no_identity["agent"]:
        facts["warnings"].append(
            f"identity incomplete (golden {no_identity['golden']}, agent "
            f"{no_identity['agent']} rows) — those rows NOT paired")
    return pairs


KEY_SAMPLE_ROWS = 5
FILE_SAMPLE_ROWS = 25


def key_samples(d: SheetDiff, keys: KeyConfig, n: int = KEY_SAMPLE_ROWS) -> dict:
    """The first ``n`` golden key values beside the first ``n`` agent ones —
    the key CONVENTION each side follows (OBJECT_ID shown as its table, as
    paired). UNSCRUBBED: console + score.json on D1 only, never the export.
    Under identity pairing: the first rows' IDENTITIES, as paired."""
    if d.identity_text:
        return {"key": d.facts.get("key"),
                "golden": list(d.identity_text.get("golden", {}).values())[:n],
                "agent": list(d.identity_text.get("agent", {}).values())[:n]}
    key = keys.key_for(d.name)
    out: dict = {"key": key or None, "golden": [], "agent": []}
    if not key:
        return out
    for side, sheet, tables in (("golden", d.sides[0], d.tables[0]),
                                ("agent", d.sides[1], d.tables[1])):
        if sheet is None:
            continue
        cols = _resolve(sheet, key)
        if None in cols:
            missing = [k for k, c in zip(key, cols, strict=True) if c is None]
            out[side] = [f"<key column(s) {missing} not in this sheet>"]
            continue
        keyer = _keyer(sheet, cols, keys, tables)
        for row in sheet.rows[:n]:
            k = keyer(row)
            out[side].append(k.text if k.key is not None
                             else f"<OBJECT_ID {k.object_id} unresolved>")
    return out


def _pair_by_identity(name: str, golden: Sheet | None, agent: Sheet | None,
                      keys: KeyConfig, tables: tuple, scope: FeedScope | None,
                      ctx: FeedContext | None, texts: dict
                      ) -> tuple[list[RowPair], dict, set[int]]:
    """Identity pairing (2026-10-13). Out of scope first: a golden row the
    group index places in a feed the agent did not write (or, without the
    index, one naming only another feed). Then the sheet's identity; a sheet
    with NO identity pairs by position only when both sides have the same
    number of rows — otherwise its rows stay unpaired, said in a warning."""
    facts: dict = {"key": "none", "pair_mode": "identity", "warnings": []}
    g_rows = golden.rows if golden else []
    a_rows = agent.rows if agent else []
    if golden is None or agent is None or ctx is None:
        return (_unpaired(g_rows, a_rows), facts, set())
    g_canon = golden.canon()
    g_info = {n: ctx.golden(row, g_canon, tables[0]) for n, row in g_rows}
    oos: set[int] = set()
    if ctx.scope.enabled:
        for n, row in g_rows:
            feed, _flow, foreign = g_info[n]
            if foreign or (feed is None and ctx.scope.active
                           and ctx.scope.out_of_scope(row, g_canon, tables[0])):
                oos.add(n)
    components = keys.identity_for(name)
    pairs = None
    if components:
        pairs = _identity_pairs(name, golden, agent, components, keys, tables, ctx, g_info,
                                oos, facts, texts)
    if pairs is not None:
        return pairs, facts, oos
    in_scope = [(n, row) for n, row in g_rows if n not in oos]
    out_rows = [RowPair((n, row), None, "out of scope") for n, row in g_rows if n in oos]
    if in_scope and len(in_scope) == len(a_rows):
        facts["key"] = "position"
        facts["warnings"].append(
            f"no identity for this sheet — {len(a_rows)} row(s) paired BY POSITION "
            "(row counts equal)")
        pairs = [RowPair(g, a, f"#{i + 1}", BY_POSITION)
                 for i, (g, a) in enumerate(zip(in_scope, a_rows, strict=True))]
        return pairs + out_rows, facts, oos
    if in_scope or a_rows:
        facts["warnings"].append(
            f"no identity for this sheet and row counts differ (golden {len(in_scope)}, "
            f"agent {len(a_rows)}) — rows NOT paired")
    return _unpaired(in_scope, a_rows) + out_rows, facts, oos


def diff_sheet(
    name: str,
    golden: Sheet | None,
    agent: Sheet | None,
    keys: KeyConfig,
    tables: tuple[ObjectTables | None, ObjectTables | None] = (None, None),
    pair_mode: str = "identity",
    scope: FeedScope | None = None,
    ctx: FeedContext | None = None,
) -> SheetDiff:
    presence = "compared" if golden and agent else ("golden-only" if golden else "agent-only")
    texts: dict = {}
    oos: set[int] | None = None
    if pair_mode == "identity":
        pairs, facts, oos = _pair_by_identity(name, golden, agent, keys, tables, scope, ctx,
                                              texts)
    else:
        pairs, facts = pair_rows(golden, agent, keys.key_for(name), keys, tables,
                                 pair_mode=pair_mode)
    g_canon = golden.canon() if golden else {}
    a_canon = agent.canon() if agent else {}
    order = [c.upper() for c in golden.columns] if golden else []
    order += [c.upper() for c in (agent.columns if agent else []) if c.upper() not in g_canon]
    order = [c for c in order if c != SOURCE_COLUMN.upper()]   # provenance, never scored
    out = SheetDiff(name, presence, facts, pairs=pairs, sides=(golden, agent), tables=tables)
    out.columns = {
        "golden_only": [g_canon[c] for c in order if c in g_canon and c not in a_canon],
        "agent_only": [a_canon[c] for c in order if c in a_canon and c not in g_canon],
    }
    out.cells, oos_rows = _classify_pairs(pairs, order, g_canon, a_canon, keys, tables,
                                          scope if agent is not None else None, oos)
    out.identity_text = texts
    return _tally(out, pairs, oos_rows, golden, agent, keys)


def _tally(out: SheetDiff, pairs: list[RowPair], oos_rows: set[int], golden: Sheet | None,
           agent: Sheet | None, keys: KeyConfig) -> SheetDiff:
    """Rows paired per method, unpaired per side, the row counts."""
    out.pairing = {m: sum(1 for p in pairs if p.golden and p.agent and p.method == m)
                   for m in (BY_IDENTITY, BY_POSITION, BY_KEY)}
    out.unpaired = {"golden": sum(1 for p in pairs if p.golden and not p.agent
                                  and p.golden[0] not in oos_rows),
                    "agent": sum(1 for p in pairs if p.agent and not p.golden)}
    out.rows = {
        "golden": len(golden.rows) if golden else 0,
        "agent": len(agent.rows) if agent else 0,
        "paired": sum(1 for p in pairs if p.golden and p.agent),
        MISSING: sum(1 for p in pairs if p.golden and not p.agent
                     and p.golden[0] not in oos_rows),
        EXTRA: sum(1 for p in pairs if p.agent and not p.golden),
    }
    out.out_of_scope_rows = len(oos_rows)
    out.key_samples = key_samples(out, keys)
    return out


def _first(row: dict[str, object], cols: list[str]) -> str:
    return next((_raw(row.get(c)).strip() for c in cols if _raw(row.get(c)).strip()), "")


def _sheet_named(sheets: dict[str, Sheet], name: str | None) -> Sheet | None:
    return next((s for n, s in sheets.items() if name and sheet_id(n) == sheet_id(name)), None)


def diff_alias_sheet(alias: SheetAlias, golden: Sheet, agent: Sheet,
                     agent_sheets: dict[str, Sheet], keys: KeyConfig, scope: FeedScope,
                     tables: tuple) -> SheetDiff:
    """A golden sheet against the agent sheet of ANOTHER template (iig_keys.yaml
    ``sheet_aliases``). A golden row pairs by its FILE: with the agent row that
    names it, else — the agent sheet naming no file (iig_v2 FILE_ADLS is one
    row per feed) — with the agent row of the feed whose ``agent_files_from``
    sheet names it; several golden files can pair with one feed row. Unpaired
    golden rows are out of scope like every sheet's (FeedScope). Only the mapped
    columns are compared; the rest are ``not comparable``, never missing."""
    facts: dict = {"key": ["@file"], "pair_mode": "identity", "warnings": []}
    tokens = keys.file_name_tokens
    a_canon, g_canon = agent.canon(), golden.canon()
    own = [a_canon[c.upper()] for c in alias.agent_files if c.upper() in a_canon]
    feed_files: dict[int, list[str]] = defaultdict(list)
    source = _sheet_named(agent_sheets, alias.files_from_sheet) if not own else None
    if source is not None:
        s_canon = source.canon()
        cols = [s_canon[c.upper()] for c in alias.files_from_columns if c.upper() in s_canon]
        for n, row in source.rows:
            name = _first(row, cols)
            if name:
                feed_files[feed_of_agent_row(n)].append(name)
    texts: dict = {"golden": {}, "agent": {}}
    by_file: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    no_file = {"golden": 0, "agent": 0}
    for n, row in agent.rows:
        names = [_first(row, own)] if own else feed_files.get(feed_of_agent_row(n), [])
        files = sorted({f for f in (file_identity(x, tokens) for x in names) if f})
        texts["agent"][n] = ", ".join(files) or "<no file>"
        no_file["agent"] += not files
        for f in files:
            by_file[f].append((n, row))
    repeated = [f for f, rows in by_file.items() if len(rows) > 1]
    if repeated:
        facts["warnings"].append(f"{len(repeated)} file(s) named by more than one agent row — "
                                 "paired with the first")
    g_cols = [g_canon[c.upper()] for c in alias.golden_files if c.upper() in g_canon]
    pairs: list[RowPair] = []
    oos: set[int] = set()
    matched_agent: set[int] = set()
    matched_files: set[str] = set()
    for n, row in golden.rows:
        f = file_identity(_first(row, g_cols), tokens)
        texts["golden"][n] = f or "<no file>"
        partner = by_file[f][0] if f and by_file.get(f) else None
        if partner is not None:
            matched_agent.add(partner[0])
            matched_files.add(f)  # type: ignore[arg-type]
            pairs.append(RowPair((n, row), partner, f or "", BY_IDENTITY))
        elif scope.active and scope.out_of_scope(row, g_canon, tables[0]):
            oos.add(n)
            pairs.append(RowPair((n, row), None, "out of scope"))
        else:
            no_file["golden"] += f is None
            pairs.append(RowPair((n, row), None, texts["golden"][n]))
    pairs += [RowPair(None, (n, row), texts["agent"][n])
              for n, row in agent.rows if n not in matched_agent]
    if no_file["golden"] or no_file["agent"]:
        facts["warnings"].append(f"no file name (golden {no_file['golden']}, agent "
                                 f"{no_file['agent']} rows) — those rows NOT paired")
    unmatched = sorted(set(by_file) - matched_files)
    if unmatched:
        facts["warnings"].append(f"{len(unmatched)} agent file(s) with no golden row")
    mapping: list[tuple[str, str]] = []
    absent = []
    g_heads = {header_id(c): c for c in golden.columns}
    a_heads = {header_id(c): c for c in agent.columns}
    for g_col, a_col in alias.columns:
        g_real, a_real = g_heads.get(header_id(g_col)), a_heads.get(header_id(a_col))
        if g_real and a_real:
            mapping.append((g_real, a_real))
        else:
            absent.append(f"{g_col} -> {a_col}")
    if absent:
        facts["warnings"].append("mapped column(s) not in both workbooks: " + ", ".join(absent))
    mapped_g = {header_id(g) for g, _a in mapping}
    mapped_a = {header_id(a) for _g, a in mapping}
    out = SheetDiff(alias.label, "compared", facts, pairs=pairs, sides=(golden, agent),
                    tables=tables, title=golden.name)
    out.columns = {
        "golden_only": [], "agent_only": [],
        "mapped": {g: a for g, a in mapping},
        "not_comparable": {
            "golden": [c for c in golden.columns if header_id(c) not in mapped_g
                       and c.upper() != SOURCE_COLUMN.upper()],
            "agent": [c for c in agent.columns if header_id(c) not in mapped_a]},
    }
    order = [g.upper() for g, _a in mapping]
    out.cells, oos_rows = _classify_pairs(pairs, order, {g.upper(): g for g, _a in mapping},
                                          {g.upper(): a for g, a in mapping}, keys, tables,
                                          None, oos)
    out.identity_text = texts
    # D1 only (unscrubbed): the file names each side states and their identity,
    # so a sheet that pairs nothing shows WHY (pair_12: 0 rows paired).
    out.file_samples = {
        "golden": [{"row": n, "name": _first(row, g_cols),
                    "identity": file_identity(_first(row, g_cols), tokens)}
                   for n, row in golden.rows[:FILE_SAMPLE_ROWS]],
        "agent": [{"row": n, "feed": feed_of_agent_row(n), "name": name,
                   "identity": file_identity(name, tokens)}
                  for n, row in agent.rows
                  for name in ([_first(row, own)] if own
                               else feed_files.get(feed_of_agent_row(n), []) or [""])],
        "golden_rows": len(golden.rows), "agent_rows": len(agent.rows),
        "agent_files_from": None if own else alias.files_from_sheet,
    }
    return _tally(out, pairs, oos_rows, golden, agent, keys)


_FEED_TABLE_COLUMNS = ("TGT_TABLE_NAME", "TGT_TABLE")


def agent_feed_names(paths: list[Path], agent: dict[str, Sheet]) -> dict[str, int]:
    """normalized name -> agent feed: each workbook's name (``<feed>_IIG.xlsx``)
    and every target table its rows write. A name two feeds share is dropped."""
    seen: dict[str, set[int]] = defaultdict(set)
    for index, path in enumerate(paths, start=1 if len(paths) > 1 else 0):
        stem = re.sub(r"_iig(_review)?$", "", path.stem.lower())
        if identity_value(stem):
            seen[identity_value(stem) or ""].add(index)
    for sheet in agent.values():
        canon = sheet.canon()
        cols = [canon[c] for c in _FEED_TABLE_COLUMNS if c in canon]
        for number, row in sheet.rows:
            for col in cols:
                value = identity_value(row.get(col), "TABLE")
                if value:
                    seen[value].add(feed_of_agent_row(number))
    return {name: next(iter(feeds)) for name, feeds in seen.items() if len(feeds) == 1}


def diff_workbooks(
    golden: Path,
    agent: Path | list[Path],
    keys: KeyConfig,
    pair_mode: str = "identity",
    scope_mode: str = "feeds",
    group_index: list[Path] | None = None,
    self_check: bool = False,
) -> list[SheetDiff]:
    g = read_workbook(golden, keys)
    paths = agent if isinstance(agent, list) else [agent]
    a = read_agent_workbooks(paths, keys)
    tables = (ObjectTables(g, keys), ObjectTables(a, keys))
    scope = FeedScope(a, g, keys, enabled=scope_mode == "feeds")
    index_paths = (group_index if group_index is not None
                   else [REPO_ROOT / rel for rel in keys.group_index])
    feeds = {feed_of_agent_row(n) for sheet in a.values() for n, _row in sheet.rows}
    ctx = FeedContext(GroupIndex(index_paths), agent_feed_names(paths, a), scope, keys,
                      feeds or {1 if len(paths) > 1 else 0}, self_check=self_check)
    a_by_id = {sheet_id(n): n for n in a}
    g_ids = {sheet_id(n) for n in g}

    # Cross-template sheets (iig_keys.yaml sheet_aliases): only when the golden
    # lacks the agent's sheet AND the agent lacks the golden's.
    aliased: dict[str, tuple[str, SheetAlias]] = {}   # golden sheet -> (agent sheet, alias)
    for alias in keys.sheet_aliases:
        g_name = next((n for n in g if sheet_id(n) == sheet_id(alias.golden_sheet)), None)
        a_name = a_by_id.get(sheet_id(alias.agent_sheet))
        if (g_name and a_name and sheet_id(alias.agent_sheet) not in g_ids
                and sheet_id(alias.golden_sheet) not in a_by_id):
            aliased[g_name] = (a_name, alias)
    taken = {a_name for a_name, _alias in aliased.values()}
    names = list(g) + [n for n in a if sheet_id(n) not in g_ids and n not in taken]
    result = []
    for name in names:
        if name in aliased:
            a_name, alias = aliased[name]
            sd = diff_alias_sheet(alias, g[name], a[a_name], a, keys, scope, tables)
            sd.facts["template_mismatch"] = {
                "golden_sheet": name, "agent_sheet": a_name,
                "note": "Different IIG template versions: rows paired by file name, only "
                        "the columns both templates have compared (iig_keys.yaml "
                        "sheet_aliases); the rest not comparable."}
        else:
            sd = diff_sheet(name, g.get(name), a.get(a_by_id.get(sheet_id(name), "")), keys,
                            tables, pair_mode=pair_mode, scope=scope, ctx=ctx)
        sd.facts["scope"] = {"active": scope.active, "feeds": len(scope.stems)}
        result.append(sd)
    return result


def _score(counts: dict[str, int]) -> float:
    """The overall / per-sheet score as it always was: an out-of-scope cell
    counts as missing (the number a past report quoted stays comparable)."""
    scored = sum(counts.get(s, 0) for s in LEGACY_SCORED)
    if not scored:
        return 100.0
    return round(100.0 * (counts[EXACT] + counts[NORMALIZED]) / scored, 1)


def _convention(cells: list[Cell]) -> dict[str, int]:
    """Convention cells of PAIRED rows: how many, how many differ."""
    paired = [c for c in cells if c.status == CONVENTION
              and c.golden_row is not None and c.agent_row is not None]
    differing = sum(1 for c in paired if classify(c.golden, c.agent) not in (EXACT, NORMALIZED))
    return {"cells": len(paired), "differing": differing}


def _comparable(counts: dict[str, int]) -> float | None:
    """Over SCOPED cells only (out-of-scope rows left out)."""
    scored = sum(counts.get(s, 0) for s in SCORED)
    if not scored:
        return None
    return round(100.0 * (counts[EXACT] + counts[NORMALIZED]) / scored, 1)


def template_note(golden: str, agent: str) -> str:
    """The one-line note when the layouts differ. Informs only: switching the agent's
    template also switches its naming convention (iig_v1 = WF_ / NB_, iig_v2 =
    PL_File_), which is what turned the round-7 pair_2 diff into 0.0."""
    return (f"golden is {len(TEMPLATE_SHEETS[golden])}-sheet ({golden} layout); agent is "
            f"{len(TEMPLATE_SHEETS[agent])}-sheet ({agent}); the extra/missing sheet is "
            "reported separately and does not affect the comparable score. Naming "
            "convention differs between templates and is not scored.")


def template_facts(diffs: list[SheetDiff]) -> dict:
    """Which IIG layout each side is, and — when they differ — the one-line note."""
    golden = detect_template([d.sides[0].name for d in diffs if d.sides[0] is not None])
    agent = detect_template([d.sides[1].name for d in diffs if d.sides[1] is not None])
    facts: dict = {"golden": golden, "agent": agent}
    if golden and agent and golden != agent:
        facts["note"] = template_note(golden, agent)
    return facts


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
        one_side = {"golden-only": "sheet not in agent",
                    "agent-only": "sheet not in golden"}.get(d.presence)
        if one_side:
            sheet_warnings.append(f"{one_side} — no score")
        if d.out_of_scope_rows:
            sheet_warnings.append(f"out of scope: {d.out_of_scope_rows} golden row(s) of "
                                  "feeds this run did not write (not missing)")
        warnings += [f"{d.name}: {w}" for w in sheet_warnings]
        entry: dict = {
            "presence": d.presence,
            "note": one_side,
            "key": d.facts["key"],
            "pair_mode": d.facts.get("pair_mode", "key"),
            "key_unique": d.facts.get("key_unique"),
            "duplicate_keys": d.facts.get("duplicate_keys"),
            "unresolved_object_ids": d.facts.get("unresolved_object_ids"),
            "rows": d.rows,
            "columns": d.columns,
            "counts": counts,
            # 2026-10-13: which columns the score is made of
            "column_counts": d.column_counts(),
            # A sheet one side does not have has NO score (was 0.0): a template
            # difference, not a result.
            "score": None if one_side else _score(counts),
            "comparable_score": None if one_side else _comparable(counts),
            "out_of_scope_rows": d.out_of_scope_rows,
            "needs_assignment": assign,
            # 2026-10-13: HOW rows were matched — never read a score without it
            "pairing": d.pairing,
            "unpaired": d.unpaired,
            "identity_dropped": d.facts.get("identity_dropped"),
            "convention_cells": _convention(d.cells),
            # D1 only (unscrubbed): the key convention each side follows.
            "key_samples": d.key_samples,
            "warnings": sheet_warnings,
        }
        if d.facts.get("template_mismatch"):
            entry["template_mismatch"] = d.facts["template_mismatch"]
        if d.columns.get("not_comparable") is not None:
            entry["mapped_columns"] = d.columns["mapped"]
            entry["not_comparable"] = d.columns["not_comparable"]
        if d.file_samples is not None:
            entry["file_samples"] = d.file_samples       # D1 only (unscrubbed)
        sheets[d.name] = entry
    total_counts = {s: totals.get(s, 0) for s in STATUSES}
    shared: Counter[str] = Counter()
    for d in diffs:
        if d.presence == "compared":
            shared.update(d.counts())
    pairing: Counter[str] = Counter()
    unpaired: Counter[str] = Counter()
    convention: Counter[str] = Counter()
    for d in diffs:
        pairing.update(d.pairing)
        unpaired.update(d.unpaired)
        convention.update(_convention(d.cells))
    templates = template_facts(diffs)
    scope = next((d.facts.get("scope") for d in diffs if d.facts.get("scope")), None)
    return {
        **(header or {}),
        "golden": str(golden),
        "agent": [str(a) for a in agent] if isinstance(agent, list) else str(agent),
        "keys": str(keys_path),
        "templates": templates,
        "scope": scope,
        "totals": {
            **total_counts,
            "scored_cells": sum(total_counts[s] for s in LEGACY_SCORED),
            "score": _score(total_counts),
            # 2026-10-13: like with like — scoped cells of the sheets BOTH sides have.
            "comparable_score": _comparable({s: shared.get(s, 0) for s in STATUSES}),
            "comparable_cells": sum(shared.get(s, 0) for s in SCORED),
            "out_of_scope_rows": sum(d.out_of_scope_rows for d in diffs),
            "pairing": {m: pairing.get(m, 0) for m in (BY_IDENTITY, BY_POSITION, BY_KEY)},
            "unpaired": {s: unpaired.get(s, 0) for s in ("golden", "agent")},
            "convention_cells": {k: convention.get(k, 0) for k in ("cells", "differing")},
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
        ws = wb.create_sheet((d.title or d.name)[:31])
        ws.append(["KEY", "GOLDEN_ROW", "AGENT_ROW", "COLUMN", "GOLDEN", "AGENT", "STATUS",
                   "PAIRED_BY"])
        for row_number, cell in enumerate(d.cells, start=2):
            withheld = keys.is_withheld(cell.column)
            g = WITHHELD if withheld and _raw(cell.golden) else _cell_value(cell.golden)
            a = WITHHELD if withheld and _raw(cell.agent) else _cell_value(cell.agent)
            ws.append([cell.key, cell.golden_row, cell.agent_row, cell.column, g, a, cell.status,
                       cell.method])
            fill = fills.get(cell.status)
            if fill:
                # the row just appended (ws.max_row rescans the sheet on every call)
                ws.cell(row_number, 7).fill = fill
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
                   "ignored_set": list(keys.needs_assignment), "pair_mode": pair_mode,
                   "environment_tokens": keys.env_state()}
    if pair_mode in ("position", "fuzzy"):
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
             pair_mode: str = "identity", build: dict | None = None,
             scope_mode: str = "feeds", group_index: list[Path] | None = None) -> dict:
    return _run_pair(golden, agent, out, keys_path, pair_mode, build, scope_mode,
                     group_index)[0]


def _run_pair(golden: Path, agent: Path | list[Path], out: Path, keys_path: Path,
              pair_mode: str = "identity", build: dict | None = None,
              scope_mode: str = "feeds", group_index: list[Path] | None = None
              ) -> tuple[dict, list[SheetDiff], KeyConfig]:
    keys = load_keys(keys_path)
    diffs = diff_workbooks(golden, agent, keys, pair_mode=pair_mode, scope_mode=scope_mode,
                           group_index=group_index)
    payload = score_payload(golden, agent, keys_path, diffs,
                            header_facts(keys, pair_mode, build))
    out.mkdir(parents=True, exist_ok=True)
    (out / "score.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_diff_xlsx(out / "diff.xlsx", payload, diffs, keys)
    write_routing_csv(out / "routing.csv", diffs)
    return payload, diffs, keys


# ----------------------------------------------------------- scrubbed export

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_STATUSES = (MISMATCH, MISSING, EXTRA)
EXPORT_FILES = ("mismatches.md", "row_keys.md", "sheets.md")
SELF_CHECK_FILE = "SELF_CHECK.md"
LOCAL_DENYLIST_REL = Path("docs") / "acfc" / "denylist_local.txt"
_TOKEN_SPLIT = re.compile(r"([\W_]+)")        # a token = a run of letters / digits
_MARKED = re.compile("\x00([A-Z0-9_]+)\x00")   # a scrub_check class placeholder in flight
_TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".txt", ".md", ".csv"}
_PLACEHOLDER_NAMES = {"email_address": "EMAIL"}
EXPORT_INTRO = (
    "Every value below is scrubbed: a scrub_check class (and a local-denylist term) is "
    "`<CLASS>`; a token found in the golden but not in the repo's committed fixtures is "
    "`G<n>`, any other token outside the fixtures is `A<n>` - one map for every file of "
    "this export, so the same token is the same placeholder everywhere. Tokens under 3 "
    "characters and numbers under 5 digits are kept. CREATED_BY / UPDATED_BY values are "
    "withheld."
)


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_SPLIT.split(text)[::2] if t]


def _git_ls_fixtures(root: Path) -> list[Path]:
    """``git ls-files fixtures/`` — raises where there is no git (D1's workspace)."""
    if not (root / ".git").exists():
        raise FileNotFoundError(f"no .git under {root}")
    done = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", "fixtures/"],
                          capture_output=True, check=True, timeout=120)
    return [root / p for p in done.stdout.decode("utf-8", "replace").split("\0") if p]


def _glob_regex(pattern: str) -> str:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        c = pattern[i]
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[" and "]" in pattern[i + 1:]:
            j = pattern.index("]", i + 1)
            body = pattern[i + 1:j]
            out.append("[" + ("^" + body[1:] if body.startswith("!") else body) + "]")
            i = j
        elif c == "\\" and i + 1 < len(pattern):
            i += 1
            out.append(re.escape(pattern[i]))
        else:
            out.append(re.escape(c))
        i += 1
    return "".join(out)


def gitignore_rules(path: Path) -> list[tuple[re.Pattern[str], bool, bool]]:
    """(regex over the repo-relative posix path, negated, directories only) per
    line of a .gitignore — enough of git's rules for the repo's own file."""
    rules = []
    if not path.is_file():
        return rules
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        line = line[1:] if negated else line
        dir_only = line.endswith("/")
        line = line.rstrip("/")
        anchored = "/" in line
        body = _glob_regex(line.lstrip("/"))
        rules.append((re.compile(("^" if anchored else "^(?:.*/)?") + body + "$"),
                      negated, dir_only))
    return rules


def gitignored(rel: str, is_dir: bool, rules) -> bool:
    ignored = False
    for regex, negated, dir_only in rules:
        if (is_dir or not dir_only) and regex.match(rel):
            ignored = not negated            # the last matching line wins
    return ignored


def _walk_fixtures(root: Path) -> list[Path]:
    """No git: every file under ``fixtures/`` the repo's .gitignore does not
    ignore (an ignored folder is never entered, as in git) — so a gitignored
    client-derived file on disk never joins the universe."""
    rules = gitignore_rules(root / ".gitignore")
    base = root / "fixtures"
    if not base.is_dir() or gitignored("fixtures", True, rules):
        return []
    files = []
    for folder, dirs, names in os.walk(base):
        rel = Path(folder).relative_to(root).as_posix()
        dirs[:] = sorted(d for d in dirs if not gitignored(f"{rel}/{d}", True, rules))
        files += [Path(folder) / n for n in sorted(names)
                  if not gitignored(f"{rel}/{n}", False, rules)]
    return files


def _file_text(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix == ".xlsx":
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            try:
                return "\n".join(str(v) for ws in wb.worksheets
                                 for row in ws.iter_rows(values_only=True)
                                 for v in row if v is not None)
            finally:
                wb.close()
        if suffix == ".docx":
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            xml = re.sub(r"</w:p>|</w:tc>|<w:tab/>|<w:br/>", " ", xml)
            return html.unescape(re.sub(r"<[^>]+>", "", xml))
        if suffix in _TEXT_SUFFIXES:
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # an unreadable fixture adds no token: the safe direction
        return ""
    return ""


@functools.cache
def fixture_universe(root: Path = REPO_ROOT) -> tuple[frozenset[str], str, int]:
    """(caseless tokens of every committed fixture, where the list came from,
    file count). ``git ls-files fixtures/``; without git, a .gitignore-aware
    walk of ``fixtures/`` on disk."""
    root = Path(root)
    try:
        files = _git_ls_fixtures(root)
        source = "git ls-files fixtures/"
    except (OSError, subprocess.SubprocessError):
        files = _walk_fixtures(root)
        source = ("disk walk of fixtures/ (no git), .gitignore honoured"
                  if (root / ".gitignore").is_file()
                  else "disk walk of fixtures/ (no git, NO .gitignore: every file counted)")
    tokens: set[str] = set()
    for path in files:
        if path.is_file():
            tokens.update(t.casefold() for t in _tokens(_file_text(path)))
    return frozenset(tokens), source, len(files)


def load_scrub_check(root: Path = REPO_ROOT):
    path = Path(root) / "scripts" / "scrub_check.py"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - the scrubbed export needs scrub_check.py")
    spec = importlib.util.spec_from_file_location("iig_diff_scrub_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_local_denylist(path: Path | None) -> list[str]:
    """Terms of the gitignored local denylist: ``|``-separated per line, ``#``
    lines and blanks skipped. Absent (D1) = no terms."""
    if path is None or not Path(path).is_file():
        return []
    terms: list[str] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip().startswith("#"):
            terms += [t.strip() for t in line.split("|") if t.strip()]
    return list(dict.fromkeys(terms))


def _term_regex(terms: list[str]) -> re.Pattern[str] | None:
    """Whole terms, caseless; ``_`` is a boundary (a term inside a snake_case
    name matches)."""
    if not terms:
        return None
    alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<![^\W_])(?:{alternatives})(?![^\W_])", re.IGNORECASE)


def _marker(klass: str) -> str:
    return "\x00" + _PLACEHOLDER_NAMES.get(klass, klass.upper()) + "\x00"


class Scrubber:
    """Scrubs one value at a time; the G / A maps span the whole export."""

    def __init__(self, scrub_check, universe: frozenset[str], golden_tokens: frozenset[str],
                 local_terms: list[str], harvested: dict[str, str]) -> None:
        self.sc = scrub_check
        self.universe = universe
        self.golden = golden_tokens
        self.local = _term_regex(local_terms)
        self.harvested = sorted(((t, k) for t, k in harvested.items() if len(t) >= 5),
                                key=lambda tk: -len(tk[0]))
        self.maps: dict[str, dict[str, str]] = {"G": {}, "A": {}}
        self.uses: Counter[str] = Counter()
        self.before: Counter[str] = Counter()     # scrub_check hits per class, pre-replacement

    def _count(self, text: str) -> None:
        if self.local is not None:
            self.before["local_denylist"] += len(self.local.findall(text))
        for token, klass in self.harvested:
            self.before[klass] += text.count(token)
        for klass, _ in self.sc.structural_hits(text):
            self.before[klass] += 1
        for klass, pattern in self.sc.GENERIC_PATTERNS:
            self.before[klass] += sum(1 for _ in pattern.finditer(text))

    def _mark(self, text: str) -> str:
        if self.local is not None:
            text = self.local.sub(_marker("local_denylist"), text)
        for token, klass in self.harvested:
            text = text.replace(token, _marker(klass))
        for klass, regex in (("email_address", self.sc.EMAIL),
                             ("workspace_user_path", self.sc.WORKSPACE_USER_PATH)):
            text = regex.sub(lambda m, k=klass: _marker(k) if self.sc.structural_hits(m.group(0))
                             else m.group(0), text)
        for klass, pattern in self.sc.GENERIC_PATTERNS:
            text = pattern.sub(_marker(klass), text)
        return text

    def _token(self, token: str) -> str:
        if not token or len(token) < (5 if token.isdigit() else 3):
            return token
        low = token.casefold()
        if low in self.universe:
            return token
        prefix = "G" if low in self.golden else "A"
        table = self.maps[prefix]
        if low not in table:
            table[low] = f"{prefix}{len(table) + 1}"
        self.uses[prefix] += 1
        return table[low]

    def scrub(self, value: object) -> str:
        text = _raw(value)
        if not text:
            return ""
        self._count(text)
        out = []
        for i, part in enumerate(_MARKED.split(self._mark(text))):
            if i % 2:
                out.append(f"<{part}>")
                continue
            pieces = _TOKEN_SPLIT.split(part)
            out += [self._token(p) if j % 2 == 0 else p for j, p in enumerate(pieces)]
        return "".join(out)


def _md(text: str) -> str:
    text = text.replace("|", "\\|").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "<br>")


def _row_ref(n: int | None) -> str:
    if n is None:
        return "-"
    return str(n) if n < ROW_STRIDE else f"{n // ROW_STRIDE}:{n % ROW_STRIDE}"


def _key_text(sheet: Sheet | None, row: dict | None, key: list[str] | None, keys: KeyConfig,
              tables: ObjectTables | None, scr: Scrubber) -> str:
    """A row's natural key, each part scrubbed; an OBJECT_ID shows the table it
    resolves to in its own workbook."""
    if sheet is None or row is None or not key:
        return "(no key)"
    canon = sheet.canon()
    parts = []
    for col in key:
        real = canon.get(col.upper())
        if real is None:
            return "(key column absent)"
        value = row.get(real)
        if keys.is_withheld(col):
            parts.append(WITHHELD)
        elif keys.is_object_id(col) and tables is not None:
            table = tables.table_for(row, canon)
            parts.append(scr.scrub(table) if table
                         else f"OBJECT_ID {scr.scrub(value) or '<blank>'} unresolved")
        else:
            parts.append(scr.scrub(value) if _raw(value).strip() else "<blank>")
    return " | ".join(parts)


def _row_text(d: SheetDiff, side: str, number: int | None, sheet: Sheet | None,
              row: dict | None, key: list[str] | None, keys: KeyConfig,
              table: ObjectTables | None, scr: Scrubber) -> str:
    """The row's identity (each part scrubbed) under identity pairing, else
    its natural key."""
    text = d.identity_text.get(side, {}).get(number) if d.identity_text else None
    if text is not None:
        return " | ".join(scr.scrub(part) for part in text.split(" | "))
    return _key_text(sheet, row, key, keys, table, scr)


def _value(cell_value: object, column: str, keys: KeyConfig, scr: Scrubber) -> str:
    if keys.is_withheld(column):
        return WITHHELD if _raw(cell_value) else ""
    return scr.scrub(cell_value)


def _write_mismatches(path: Path, diffs: list[SheetDiff], keys: KeyConfig,
                      scr: Scrubber) -> Counter[str]:
    lines, counts = [], Counter()
    for d in diffs:
        g_sheet, a_sheet = d.sides
        g_rows = dict(g_sheet.rows) if g_sheet else {}
        a_rows = dict(a_sheet.rows) if a_sheet else {}
        key = keys.key_for(d.name)
        for cell in d.cells:
            if cell.status not in EXPORT_STATUSES or keys.is_assignment(cell.column):
                continue
            counts[cell.status] += 1
            if cell.golden_row is not None:
                row_key = _row_text(d, "golden", cell.golden_row, g_sheet,
                                    g_rows.get(cell.golden_row), key, keys, d.tables[0], scr)
            else:
                row_key = _row_text(d, "agent", cell.agent_row, a_sheet,
                                    a_rows.get(cell.agent_row), key, keys, d.tables[1], scr)
            row_key += f" (golden row {_row_ref(cell.golden_row)}, agent row "
            row_key += f"{_row_ref(cell.agent_row)})"
            lines.append("| " + " | ".join(_md(t) for t in (
                scr.scrub(d.name), scr.scrub(cell.column), cell.status,
                _value(cell.golden, cell.column, keys, scr),
                _value(cell.agent, cell.column, keys, scr), row_key)) + " |")
    total = sum(counts.values())
    by_status = ", ".join(f"{s} {counts[s]}" for s in EXPORT_STATUSES)
    head = ["# IIG mismatches - scrubbed export", "", EXPORT_INTRO, "",
            f"Cells: {total} ({by_status}). Exact / normalized / needs_assignment cells are "
            "not listed.", "",
            "| sheet | column | status | golden | agent | row key |",
            "| --- | --- | --- | --- | --- | --- |"]
    path.write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    return counts


def template_vocabulary(root: Path = REPO_ROOT) -> frozenset[str]:
    """The IIG template's own sheet names and column headers (config/config.yaml
    ``demo.metadata_sheet`` = iig_v1, ``metadata.templates`` = iig_v2): template
    fields, not client data — written as they are in the scrubbed export."""
    path = Path(root) / "config" / "config.yaml"
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return frozenset()
    layouts = [((config.get("demo") or {}).get("metadata_sheet") or {}).get("tabs") or {}]
    layouts += [(t or {}).get("tabs") or {}
                for t in ((config.get("metadata") or {}).get("templates") or {}).values()]
    words: set[str] = set()
    for tabs in layouts:
        for sheet, tab in tabs.items():
            words.add(str(sheet).upper())
            words.update(str(h).upper() for h in (tab or {}).get("headers") or [])
    return frozenset(words)


def _template_text(value: str, vocabulary: frozenset[str], scr: Scrubber) -> str:
    """A template sheet / column name as written, anything else scrubbed."""
    parts = [p.strip() for p in value.split("→")]
    if all(p.upper() in vocabulary for p in parts):
        return value
    return scr.scrub(value)


def _write_sheets(path: Path, diffs: list[SheetDiff], scr: Scrubber,
                  vocabulary: frozenset[str]) -> int:
    """sheets.md (2026-10-13): the per-sheet table WITH missing / extra, then
    each sheet's per-column breakdown — the score made interpretable. Sheet
    and column names are template fields (written as they are); anything that
    is not one is scrubbed like every value."""
    lines = ["# IIG diff per sheet - scrubbed export", "", EXPORT_INTRO, "",
             "Template sheet and column names are written as they are; every other name "
             "is scrubbed.", "",
             "| sheet | paired (identity / position / key) | unpaired (golden / agent) | score "
             "| comparable | exact | normalized | mismatch | missing | extra | out of scope "
             "| convention |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    columns_listed = 0
    detail: list[str] = []
    for d in diffs:
        c = d.counts()
        one_side = d.presence != "compared"
        score = "-" if one_side else _score(c)
        comparable = "-" if one_side else _comparable(c)
        pairing, unpaired = d.pairing or {}, d.unpaired or {}
        lines.append("| " + " | ".join(str(x) for x in (
            _md(_template_text(d.name, vocabulary, scr)),
            f"{pairing.get(BY_IDENTITY, 0)} / {pairing.get(BY_POSITION, 0)} / "
            f"{pairing.get(BY_KEY, 0)}",
            f"{unpaired.get('golden', 0)} / {unpaired.get('agent', 0)}",
            score, "-" if comparable is None else comparable,
            c[EXACT], c[NORMALIZED], c[MISMATCH], c[MISSING], c[EXTRA], c[OUT_OF_SCOPE],
            c[CONVENTION])) + " |")
        per_column = d.column_counts()
        detail += [f"## {_md(_template_text(d.name, vocabulary, scr))}", ""]
        if not per_column:
            detail += [("No cells compared (" + ("sheet on one side only" if one_side else
                                                  "no row paired or unpaired in scope") + ")."),
                       ""]
            continue
        detail += ["| column | exact | normalized | mismatch | missing | extra |",
                   "| --- | --- | --- | --- | --- | --- |"]
        for column, counts in per_column.items():
            columns_listed += 1
            detail.append("| " + " | ".join(str(x) for x in (
                _md(_template_text(column, vocabulary, scr)), counts[EXACT], counts[NORMALIZED],
                counts[MISMATCH], counts[MISSING], counts[EXTRA])) + " |")
        detail.append("")
    lines += ["", "Missing = a golden cell the agent row does not fill (or a golden row "
                  "no agent row pairs with); extra = an agent cell / row the golden does "
                  "not have.", "", *detail]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return columns_listed


def _write_row_keys(path: Path, diffs: list[SheetDiff], keys: KeyConfig,
                    scr: Scrubber) -> dict[str, int]:
    lines = ["# Row keys - scrubbed export", "", EXPORT_INTRO, ""]
    listed = {"golden": 0, "agent": 0}
    for d in diffs:
        g_sheet, a_sheet = d.sides
        key = keys.key_for(d.name)
        used = d.facts.get("key")
        # an identity component (@feed / @flow / @table / @file) is the tool's vocabulary
        used = (", ".join(c if c.startswith("@") else scr.scrub(c) for c in used)
                if isinstance(used, list) else str(used))
        g2a = {p.golden[0]: p.agent[0] for p in d.pairs if p.golden and p.agent}
        a2g = {a: g for g, a in g2a.items()}
        lines += [f"## {_md(scr.scrub(d.name))}", "",
                  f"- presence: {d.presence}; pair mode: {d.facts.get('pair_mode', 'key')}; "
                  f"paired by {', '.join(f'{m} {n}' for m, n in d.pairing.items() if n) or 'none'}",
                  f"- key columns used for pairing: {_md(used)}",
                  f"- rows: golden {d.rows['golden']}, agent {d.rows['agent']}, "
                  f"paired {d.rows['paired']}", ""]
        for side, sheet, table, other, partner in (
                ("golden", g_sheet, d.tables[0], "agent", g2a),
                ("agent", a_sheet, d.tables[1], "golden", a2g)):
            if sheet is None:
                lines += [f"No {side} rows (sheet absent).", ""]
                continue
            # A de-duplicated golden (build_goldens) says which exports held each row.
            source = sheet.canon().get(SOURCE_COLUMN.upper())
            extra_head, extra_rule = (" source exports |", " --- |") if source else ("", "")
            lines += [f"### {side.capitalize()} rows", "",
                      f"| {side} row | key | status | {other} row |{extra_head}",
                      f"| --- | --- | --- | --- |{extra_rule}"]
            for n, row in sheet.rows:
                listed[side] += 1
                mate = partner.get(n)
                text = _row_text(d, side, n, sheet, row, key, keys, table, scr)
                line = (f"| {_row_ref(n)} | {_md(text)} | "
                        f"{'paired' if mate is not None else 'unpaired'} | {_row_ref(mate)} |")
                if source:
                    ids = [s for s in _raw(row.get(source)).split(",") if s.strip()]
                    line += f" {len(ids)}: {_md(scr.scrub(','.join(ids)))} |"
                lines.append(line)
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return listed


def _rescan(sc, files: list[Path], deny: dict[str, str], local) -> Counter[str]:
    hits = Counter(klass for _, klass, _ in sc.scan_paths(files, deny=deny))
    if local is not None:
        for f in files:
            n = len(local.findall(f.read_text(encoding="utf-8")))
            if n:
                hits["local_denylist"] += n
    return hits


def _class_counts(counts: Counter[str] | dict[str, int]) -> str:
    items = sorted((k, v) for k, v in counts.items() if v)
    return ", ".join(f"{k} {v}" for k, v in items) or "none"


def export_scrubbed(diffs: list[SheetDiff], keys: KeyConfig, out: Path, root: Path = REPO_ROOT,
                    local_denylist: Path | None = None,
                    harvest: dict[str, str] | None = None) -> dict:
    """Write mismatches.md + row_keys.md + SELF_CHECK.md under ``out``. The
    result's ``rescan`` is empty when the written files are clean; otherwise
    the two evidence files are deleted (SELF_CHECK.md names the classes)."""
    root = Path(root)
    sc = load_scrub_check(root)
    deny_path = root / LOCAL_DENYLIST_REL if local_denylist is None else Path(local_denylist)
    terms = load_local_denylist(deny_path)
    harvested = sc.harvest_raw_denylist() if harvest is None else dict(harvest)
    universe, source, n_files = fixture_universe(root)
    golden_tokens: set[str] = set()
    for d in diffs:
        g = d.sides[0]
        if g is None:
            continue
        texts = [g.name, *g.columns, *(_raw(v) for _, row in g.rows for v in row.values())]
        golden_tokens.update(t.casefold() for text in texts for t in _tokens(text))
    scr = Scrubber(sc, universe, frozenset(golden_tokens), terms, harvested)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    counts = _write_mismatches(out / EXPORT_FILES[0], diffs, keys, scr)
    listed = _write_row_keys(out / EXPORT_FILES[1], diffs, keys, scr)
    columns_listed = _write_sheets(out / EXPORT_FILES[2], diffs, scr, template_vocabulary(root))
    cells = sum(counts.values())
    by_status = ", ".join(f"{s} {counts[s]}" for s in EXPORT_STATUSES)
    placeholders = (f"G {len(scr.maps['G'])} ({scr.uses['G']} uses), "
                    f"A {len(scr.maps['A'])} ({scr.uses['A']} uses)")
    before = _class_counts(scr.before)
    lines = ["# SELF_CHECK - scrubbed export (counts only)", "",
             f"- fixtures token universe: {source}, {n_files} files, {len(universe)} tokens",
             f"- local denylist: {f'{len(terms)} terms' if terms else 'absent'}",
             f"- raw harvest (inputs/reference_raw): "
             f"{f'{len(harvested)} tokens' if harvested else 'absent or empty'}",
             f"- cells exported: {cells} ({by_status})",
             f"- rows listed in row_keys.md: golden {listed['golden']}, agent {listed['agent']}",
             f"- per-column rows in sheets.md: {columns_listed}",
             f"- placeholders: {placeholders}",
             f"- scrub_check hits before replacement, per class: {before}"]
    check_path = out / SELF_CHECK_FILE
    check_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    hits = _rescan(sc, [out / f for f in (*EXPORT_FILES, SELF_CHECK_FILE)], harvested, scr.local)
    if hits:
        for name in EXPORT_FILES:
            (out / name).unlink(missing_ok=True)
        rescan = (f"FAILED - {_class_counts(hits)} (classes only; "
                  f"{', '.join(EXPORT_FILES)} deleted)")
    else:
        rescan = "0 hits"
    with check_path.open("a", encoding="utf-8") as fh:
        fh.write(f"- re-scan of {', '.join((*EXPORT_FILES, SELF_CHECK_FILE))} with "
                 f"scrub_check: {rescan}\n")
    return {
        "cells": cells, "counts": dict(counts), "rows_listed": listed,
        "placeholders": {p: len(m) for p, m in scr.maps.items()}, "uses": dict(scr.uses),
        "before": dict(scr.before), "rescan": dict(hits), "universe_source": source,
        "line": (f"SELF_CHECK: {cells} cells exported ({by_status}); placeholders {placeholders}"
                 f"; scrub_check hits before replacement: {before}; re-scan: {rescan}"),
    }


# ----------------------------------------------------------- golden structure

GROUP_COLUMNS = ("GROUP_ID", "PIPELINE_ID")
NAME_COLUMNS = ("OBJECT_NAME", "TGT_TABLE_NAME", "FILE_NAME")
SHARE_COLUMNS = ("TGT_TABLE_NAME", "OBJECT_NAME")
_LABEL = {"GROUP_ID": "group", "PIPELINE_ID": "pipeline"}
STRUCTURE_NOTE = (
    "real GROUP_IDs withheld (PIPELINE_IDs too): group#k / pipeline#k number the distinct "
    "ids in sorted order; table / object / file names are compared by normalized value and "
    "never printed"
)


def _id_order(value: str) -> tuple:
    return (0, int(value), "") if value.isdigit() else (1, 0, value)


def _label_order(label: str) -> tuple:
    prefix, _, n = label.partition("#")
    return (prefix != "group", prefix, int(n) if n.isdigit() else 1 << 30)


def _values(rows: list[dict], canon: dict[str, str], col: str) -> set[str]:
    real = canon.get(col)
    return {v for r in rows if real and (v := normalize(r.get(real)))}


def golden_structure(golden: Path, keys: KeyConfig) -> dict:
    """Row counts per GROUP_ID (PIPELINE_ID where a sheet has no GROUP_ID) per
    sheet, distinct name counts, and which groups share a table / object name.
    Labels and counts only."""
    sheets = read_workbook(golden, keys)
    seen: dict[str, set[str]] = {c: set() for c in GROUP_COLUMNS}
    for sheet in sheets.values():
        canon = sheet.canon()
        for col in GROUP_COLUMNS:
            seen[col] |= _values([r for _, r in sheet.rows], canon, col)
    labels = {(col, v): f"{_LABEL[col]}#{i}" for col in GROUP_COLUMNS
              for i, v in enumerate(sorted(seen[col], key=_id_order), start=1)}
    info: dict[str, dict] = {}
    ungrouped: dict[str, dict] = {}
    groups: dict[str, dict] = {}
    members: dict[tuple[str, str], tuple[list[dict], dict[str, str]]] = {}
    names: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    linked: dict[str, set[str]] = defaultdict(set)
    for name, sheet in sheets.items():
        canon = sheet.canon()
        rows = [r for _, r in sheet.rows]
        by = next((c for c in GROUP_COLUMNS if c in canon), None)
        if by is None:
            ungrouped[name] = {"rows": len(rows), "distinct": {
                c: len(_values(rows, canon, c)) for c in NAME_COLUMNS if c in canon}}
            info[name] = {"rows": len(rows), "grouped_by": None, "groups": 0}
            continue
        buckets: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            value = normalize(row.get(canon[by]))
            label = labels[(by, value)] if value else f"{_LABEL[by]}#blank"
            buckets[label].append(row)
            pid = normalize(row.get(canon["PIPELINE_ID"])) if "PIPELINE_ID" in canon else ""
            if by == "GROUP_ID" and value and pid:
                linked[label].add(labels[("PIPELINE_ID", pid)])
                linked[labels[("PIPELINE_ID", pid)]].add(label)
        info[name] = {"rows": len(rows), "grouped_by": by, "groups": len(buckets)}
        for label, bucket in buckets.items():
            group = groups.setdefault(label, {"column": by, "sheets": {}})
            group["sheets"][name] = {"rows": len(bucket), "distinct": {
                c: len(_values(bucket, canon, c)) for c in NAME_COLUMNS if c in canon}}
            members[(label, name)] = (bucket, canon)
            for col in (*SHARE_COLUMNS, "SRC_TABLE_NAME"):
                names[label][col] |= _values(bucket, canon, col)
    for (label, name), (bucket, canon) in members.items():
        entry = groups[label]["sheets"][name]
        entry["shared_rows"], entry["pairs_with"] = {}, {}
        for col in SHARE_COLUMNS:
            if col not in canon:
                continue
            partners: set[str] = set()
            shared = 0
            for row in bucket:
                value = normalize(row.get(canon[col]))
                hit = {o for o in names if o != label and value and value in names[o][col]}
                shared += bool(hit)
                partners |= hit
            entry["shared_rows"][col] = shared
            entry["pairs_with"][col] = sorted(partners, key=_label_order)
    ordered = {}
    for label in sorted(groups, key=_label_order):
        group = groups[label]
        group["pairs_with"] = {col: sorted({o for s in group["sheets"].values()
                                            for o in s.get("pairs_with", {}).get(col, [])},
                                           key=_label_order) for col in SHARE_COLUMNS}
        group["reads_tables_of"] = sorted(
            (o for o in names if o != label
             and names[label]["SRC_TABLE_NAME"] & names[o]["TGT_TABLE_NAME"]), key=_label_order)
        group["linked"] = sorted(linked[label], key=_label_order)
        ordered[label] = group
    return {"note": STRUCTURE_NOTE, "group_ids": len(seen["GROUP_ID"]),
            "pipeline_ids": len(seen["PIPELINE_ID"]), "sheets": info, "groups": ordered,
            "ungrouped": ungrouped}


def structure_lines(data: dict) -> list[str]:
    def opt(value) -> str:
        return "-" if value is None else str(value)

    lines = ["# Golden structure (counts only)", "", f"Note: {data['note']}.", "",
             f"Distinct GROUP_IDs: {data['group_ids']}; distinct PIPELINE_IDs: "
             f"{data['pipeline_ids']}", "", "## Sheets", "",
             "| sheet | rows | grouped by | groups |", "| --- | ---: | --- | ---: |"]
    for name, s in data["sheets"].items():
        by = {"GROUP_ID": "GROUP_ID", "PIPELINE_ID": "PIPELINE_ID (sheet has no GROUP_ID)",
              None: "not grouped (no GROUP_ID / PIPELINE_ID column)"}[s["grouped_by"]]
        lines.append(f"| {name} | {s['rows']} | {by} | {s['groups']} |")
    head = ["sheet", "rows", *(f"distinct {c}" for c in NAME_COLUMNS)]
    for col in SHARE_COLUMNS:
        head += [f"rows sharing {col} with another group",
                 f"pairs with group#k on {col} hash"]
    for label, g in data["groups"].items():
        other = "PIPELINE_ID" if g["column"] == "GROUP_ID" else "GROUP_ID"
        pairs = "; ".join(f"on {c}: {', '.join(g['pairs_with'][c]) or '-'}"
                          for c in SHARE_COLUMNS)
        lines += ["", f"## {label} (grouped by {g['column']})", "",
                  f"- sheets with rows: {', '.join(g['sheets'])}",
                  f"- {other}s on the same rows: {', '.join(g['linked']) or '-'}",
                  f"- pairs with: {pairs}",
                  "- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): "
                  f"{', '.join(g['reads_tables_of']) or '-'}", "",
                  "| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
        for name, s in g["sheets"].items():
            cells = [name, str(s["rows"]), *(opt(s["distinct"].get(c)) for c in NAME_COLUMNS)]
            for col in SHARE_COLUMNS:
                cells += [opt(s["shared_rows"].get(col)),
                          ", ".join(s["pairs_with"].get(col, [])) or "-"]
            lines.append("| " + " | ".join(cells) + " |")
    if data["ungrouped"]:
        lines += ["", "## Not grouped", "",
                  "| sheet | rows | " + " | ".join(f"distinct {c}" for c in NAME_COLUMNS) + " |",
                  "|" + " --- |" * (2 + len(NAME_COLUMNS))]
        for name, s in data["ungrouped"].items():
            lines.append(f"| {name} | {s['rows']} | "
                         + " | ".join(opt(s["distinct"].get(c)) for c in NAME_COLUMNS) + " |")
    return lines


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
              pair_mode: str = "identity", scope_mode: str = "feeds") -> dict:
    pairs, problems = find_pairs(directory)
    summary: dict = {"pairs": {}, "skipped": problems, "unscored": {}}
    for name, (golden, agent) in pairs.items():
        build = find_build(agent)
        if build is None:
            summary["unscored"][name] = UNSCORED
            continue
        payload = run_pair(golden, agent, out / name, keys_path,
                           pair_mode=pair_mode, build=build, scope_mode=scope_mode)
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
    env = payload.get("environment_tokens") or {}
    if env:
        print("ENVIRONMENT TOKENS: " + "; ".join(f"{t} {s}" for t, s in env.items()))
    if payload.get("banner"):
        print(payload["banner"])


def _print_pair(payload: dict, out: Path) -> None:
    _print_header(payload)
    for name, s in payload["sheets"].items():
        c = s["counts"]
        line = ", ".join(f"{k} {c[k]}" for k in STATUSES)
        score = s["note"] if s.get("note") else s["score"]
        pairing, unpaired = s.get("pairing") or {}, s.get("unpaired") or {}
        conv = s.get("convention_cells") or {}
        how = (f"paired by identity {pairing.get(BY_IDENTITY, 0)}, position "
               f"{pairing.get(BY_POSITION, 0)}"
               + (f", key {pairing[BY_KEY]}" if pairing.get(BY_KEY) else "")
               + f"; unpaired golden {unpaired.get('golden', 0)}, agent "
                 f"{unpaired.get('agent', 0)}; convention {conv.get('cells', 0)} "
                 f"({conv.get('differing', 0)} differ)")
        nc = s.get("not_comparable")
        if nc is not None:
            how += (f"; not comparable: golden {len(nc['golden'])}, agent "
                    f"{len(nc['agent'])} column(s)")
        print(f"{name}: score {score}; comparable {s.get('comparable_score')}; {how}; {line}")
    t = payload["totals"]
    print(f"TOTAL: score {t['score']}; " + ", ".join(f"{k} {t[k]}" for k in STATUSES))
    print(f"COMPARABLE: score {t.get('comparable_score')} over {t.get('comparable_cells')} "
          f"scoped cell(s) of the sheets both sides have; out of scope: "
          f"{t.get('out_of_scope_rows', 0)} golden row(s)")
    print(f"PAIRING: identity {t['pairing'].get(BY_IDENTITY, 0)}, position "
          f"{t['pairing'].get(BY_POSITION, 0)}, key {t['pairing'].get(BY_KEY, 0)} row(s); "
          f"unpaired golden {t['unpaired']['golden']}, agent {t['unpaired']['agent']}; "
          f"convention cells {t['convention_cells']['cells']} "
          f"({t['convention_cells']['differing']} "
          "differ — never scored)")
    note = (payload.get("templates") or {}).get("note")
    if note:
        print(f"NOTE {note}")
    for w in payload["warnings"]:
        print(f"WARNING {w}")
    _print_key_samples(payload)
    _print_file_samples(payload)
    print(f"wrote {out / 'score.json'}, {out / 'diff.xlsx'}, {out / 'routing.csv'}")


def _print_file_samples(payload: dict) -> None:
    """FILE NAMES (D1 only, unscrubbed): a cross-template sheet's golden file
    names beside the agent's (FILE_NAME vs the agent's SRC_FILE_NAME), each
    with the identity it pairs on."""
    for name, s in payload["sheets"].items():
        samples = s.get("file_samples")
        if not samples:
            continue
        print(f"FILE NAMES (D1 only - unscrubbed) {name}: golden {samples['golden_rows']} "
              f"row(s), agent {samples['agent_rows']} row(s); agent files from "
              f"{samples.get('agent_files_from') or 'the sheet itself'}")
        golden = [f"{g['name'] or '<blank>'} => {g['identity']}" for g in samples["golden"]]
        agent = [f"{a['name'] or '<no file>'} => {a['identity']} (feed {a['feed']})"
                 for a in samples["agent"]]
        width = max([len("golden FILE_NAME => identity"), *(len(g) for g in golden)])
        print(f"    {'golden FILE_NAME => identity':<{width}} | agent SRC_FILE_NAME => identity")
        for i in range(max(len(golden), len(agent))):
            g = golden[i] if i < len(golden) else ""
            a = agent[i] if i < len(agent) else ""
            print(f"    {g:<{width}} | {a}")


def _print_key_samples(payload: dict) -> None:
    """KEY CONVENTIONS (D1 only, unscrubbed): per sheet, the first golden key
    values beside the first agent ones."""
    print(f"KEY CONVENTIONS (D1 only - unscrubbed; first {KEY_SAMPLE_ROWS} rows per side)")
    for name, s in payload["sheets"].items():
        samples = s.get("key_samples") or {}
        if not samples.get("key"):
            print(f"  {name}: no natural key")
            continue
        print(f"  {name}: key {samples['key']}")
        golden, agent = samples.get("golden") or [], samples.get("agent") or []
        width = max([len("golden"), *(len(v) for v in golden)])
        print(f"    {'golden':<{width}} | agent")
        for i in range(max(len(golden), len(agent))):
            g = golden[i] if i < len(golden) else ""
            a = agent[i] if i < len(agent) else ""
            print(f"    {g:<{width}} | {a}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # a cp1252 console: "→" never raises
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--golden", type=Path)
    ap.add_argument("--agent", type=Path, nargs="+",
                    help="the agent IIG workbook(s) - one per feed of the pair; several "
                         "are compared as their union")
    ap.add_argument("--batch", type=Path, help="directory of golden / agent pairs")
    ap.add_argument("--out", type=Path,
                    help="required, except for --golden-structure alone")
    ap.add_argument("--keys", type=Path, default=DEFAULT_KEYS)
    ap.add_argument("--pair-mode", choices=PAIR_MODES, default="identity",
                    help="Row pairing: identity (default - what a row describes: feed x "
                         "flow x the sheet's identity columns, iig_keys.yaml identity; a "
                         "sheet with no identity by position only when the row counts are "
                         "equal), key (the natural key only), position or fuzzy (explicit, "
                         "bannered - not the validation score)")
    ap.add_argument("--group-index", type=Path, action="append", metavar="CSV",
                    help="golden GROUP_ID / PIPELINE_ID -> flow_type + matched_table "
                         "(default: iig_keys.yaml group_index, "
                         "docs/acfc/iig_goldens/01_pair_group_index.csv + addendum)")
    ap.add_argument("--scope", choices=SCOPE_MODES, default="feeds",
                    help="feeds (default): golden rows of feeds the agent did not write "
                         "are 'out of scope', not missing; all: score every golden row")
    ap.add_argument("--export-scrubbed", type=Path, metavar="DIR",
                    help="with --golden / --agent: also write mismatches.md, row_keys.md and "
                         "SELF_CHECK.md to DIR, every value scrubbed (safe to hand home)")
    ap.add_argument("--golden-structure", action="store_true",
                    help="print row counts per GROUP_ID per sheet of --golden (counts and "
                         "group#k labels only); written to --out when given")
    args = ap.parse_args(argv)
    if args.out is None and not args.golden_structure:
        ap.error("the following arguments are required: --out")
    if args.batch:
        if args.golden or args.agent:
            ap.error("--batch takes no --golden / --agent")
        if args.export_scrubbed or args.golden_structure:
            ap.error("--export-scrubbed / --golden-structure take --golden, not --batch")
        summary = run_batch(args.batch, args.out, args.keys,
                            pair_mode=args.pair_mode, scope_mode=args.scope)
        for name, p in summary["pairs"].items():
            print(f"{name}: score {p['totals']['score']}; mismatch {p['totals'][MISMATCH]}")
        for problem in summary["skipped"]:
            print(f"SKIPPED {problem}")
        for name, why in summary["unscored"].items():
            print(f"UNSCORED {name}: {why}")
        print(f"wrote {args.out / 'batch_summary.json'}")
        return 1 if summary["unscored"] else 0
    if args.golden_structure:
        if not args.golden:
            ap.error("--golden-structure needs --golden")
        _golden_structure_cli(args.golden, args.keys, args.out)
        if not args.agent:
            return 0
        if args.out is None:
            ap.error("the following arguments are required: --out")
    if not (args.golden and args.agent):
        ap.error("--golden and --agent are required (or --batch)")
    agents = list(args.agent)
    build, why = agent_build(agents)
    if build is None:
        print(f"{why} ({BUILD_FILES[0]} / run_meta.json 'build' must sit next to each "
              "agent workbook or up to 5 folders above it, one build for all - "
              "regenerate with the current codegen)")
        return 1
    if args.export_scrubbed is None:
        payload = run_pair(args.golden, agents if len(agents) > 1 else agents[0], args.out,
                           args.keys, pair_mode=args.pair_mode, build=build,
                           scope_mode=args.scope, group_index=args.group_index)
        _print_pair(payload, args.out)
        return 0
    try:
        load_scrub_check()
    except FileNotFoundError as exc:
        print(f"export refused: {exc}")
        return 2
    payload, diffs, keys = _run_pair(args.golden, agents if len(agents) > 1 else agents[0],
                                     args.out, args.keys, pair_mode=args.pair_mode, build=build,
                                     scope_mode=args.scope, group_index=args.group_index)
    _print_pair(payload, args.out)
    check = export_scrubbed(diffs, keys, args.export_scrubbed)
    print(check["line"])
    written = EXPORT_FILES + (SELF_CHECK_FILE,) if not check["rescan"] else (SELF_CHECK_FILE,)
    print(f"wrote {', '.join(str(args.export_scrubbed / f) for f in written)}")
    return 2 if check["rescan"] else 0


def _golden_structure_cli(golden: Path, keys_path: Path, out: Path | None) -> dict:
    data = golden_structure(golden, load_keys(keys_path))
    lines = structure_lines(data)
    print("\n".join(lines))
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "golden_structure.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (out / "golden_structure.json").write_text(json.dumps(data, indent=2) + "\n",
                                                   encoding="utf-8")
        print(f"wrote {out / 'golden_structure.md'}, {out / 'golden_structure.json'}")
    return data


if __name__ == "__main__":
    sys.exit(main())
