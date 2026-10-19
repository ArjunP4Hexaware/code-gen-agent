"""A codegen subprocess's error, read from its exit code and output (2026-10-15).

D1 post50: a harness took the first stderr line of a ``codegen`` run as "the
run's error", and a Pydantic deprecation warning printed before the real
Traceback became the reported error (and a clean run with only warnings on
stderr read as failed). D1 post51: the error lines the harness pushed quoted
document content (feed / file / sheet names: four static-denylist hits), and a
NEEDS_ANSWERS stage carried a warning as its "error". Two report tiers since
post52, shared by every reader in this repo (``scripts/run_round.py``,
``acfc_run.py``) and importable by an outside harness:

- :func:`first_error_line` — COORDINATES ONLY, what may reach a pushed report.
  Built solely from this module's own vocabulary (:data:`REASONS`,
  :data:`STAGES`), integers (:class:`Coord`) and a Python exception class name —
  never a byte of the run's output text. ``"FAIL            layout — FRD in no
  documented family (F1 / F2) at FRD 1 of 1"``.
- :func:`first_error_line_full` — the quoted line (sheet / file / feed names
  included); written only to ``codegen-outputs/`` inside ACFC, never pushed.

Both tiers: the exit code decides, per stage — 0 (PASS) and 3 (NEEDS_ANSWERS)
are not errors and return ``None`` whatever stderr holds; output is read only
when the stage FAILed. A Python warning is never the error: the WHOLE warning
block is skipped (:func:`without_warnings`).

The CLI makes the coordinates: every ``FAIL`` line it prints is paired with one
``CODEGEN-ERROR {json}`` marker line on stderr (:func:`report_error`) naming
the stage, a reason code from :data:`REASONS` and a :class:`Coord` (post55
adds counts, each validated on the way in and out: ``tables`` — an unreadable
FRD's table count + header-row fingerprints; ``flags`` / ``violations`` — a
gate FAIL's flags per type and failed-check findings per rule). A raise
site that interpolates document content attaches its coordinates with
:func:`located` (``raise located(WorkbookParseError(f"... {cell!r}"),
Coord.in_sheet("STTM", ws, row=r, col=c), "sttm.type")``); the message keeps
the quoted text for the full tier.

:func:`silence_pydantic_deprecations` stops the noise at its source (a filter
scoped to Pydantic's own deprecation category, nothing wider); the CLI calls
it at entry.
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from dataclasses import asdict, dataclass

# ----------------------------------------------------------------- coordinates

# What a coordinate may name — a document role or a run-level thing, never a name.
DOCS = ("STTM", "FRD", "VDD", "FAQ", "IIG", "DDL", "DML", "contract", "answers", "pairs",
        "config", "environment", "template", "layout", "file", "feed", "pair", "output",
        "storage", "model", "workbook", "document")
_AXES = ("sheet", "table", "band", "segment", "row", "col", "field")


@dataclass(frozen=True)
class Coord:
    """Where an error is, by position only: ``STTM sheet 2 row 4 col 7``,
    ``FRD table 3 row 2``, ``file 1 of 3``, ``feed 2 of 2``. Every field but
    ``doc`` is a non-negative integer (1-based positions); ``doc`` is one of
    :data:`DOCS`. There is deliberately no field that can hold text."""

    doc: str
    n: int | None = None
    of: int | None = None
    sheet: int | None = None
    table: int | None = None
    band: int | None = None
    segment: int | None = None
    row: int | None = None
    col: int | None = None
    field: int | None = None

    def __post_init__(self) -> None:
        if self.doc not in DOCS:
            raise ValueError(f"Coord doc must be one of {DOCS}")
        for name in ("n", "of", *_AXES):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)
                                      or value < 0):
                raise ValueError(f"Coord.{name} must be a non-negative int or None")

    def __str__(self) -> str:
        parts = [self.doc]
        if self.n is not None:
            parts.append(str(self.n) + (f" of {self.of}" if self.of is not None else ""))
        parts += [f"{axis} {getattr(self, axis)}" for axis in _AXES
                  if getattr(self, axis) is not None]
        return " ".join(parts)

    def as_dict(self) -> dict[str, object]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: object) -> Coord | None:
        """The marker's coordinate back, or None when anything is off (a
        tolerant reader: a malformed marker never becomes text)."""
        if not isinstance(data, dict):
            return None
        try:
            return cls(**{k: data[k] for k in ("doc", "n", "of", *_AXES) if k in data})
        except (TypeError, ValueError):
            return None

    @classmethod
    def in_sheet(cls, doc: str, ws: object, row: int | None = None,
                 col: int | str | None = None, **axes: int | None) -> Coord:
        """A worksheet position: the sheet's 1-based index in its workbook
        (openpyxl ``ws.parent.sheetnames``), never its name. ``col`` may be an
        index or a column letter."""
        names = getattr(getattr(ws, "parent", None), "sheetnames", None)
        title = getattr(ws, "title", None)
        sheet = names.index(title) + 1 if names and title in names else None
        return cls(doc, sheet=sheet, row=row, col=column_number(col), **axes)


def sheet_number(sheetnames: object, name: object) -> int | None:
    """1-based index of ``name`` in a workbook's sheet names (a list, or a
    workbook with ``.sheetnames``); None when absent."""
    names = getattr(sheetnames, "sheetnames", sheetnames)
    try:
        return list(names).index(name) + 1
    except (TypeError, ValueError):
        return None


def column_number(col: int | str | None) -> int | None:
    """A column as a 1-based index (``"G"`` -> 7); None for anything else."""
    if col is None or isinstance(col, bool):
        return None
    if isinstance(col, int):
        return col if col >= 0 else None
    letters = str(col).strip().upper()
    if not letters.isalpha() or len(letters) > 3:
        return None
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - 64)
    return number


def located(exc: BaseException, coord: Coord | None, reason: str | None = None, *,
            role: str | None = None, type_text: object = None) -> BaseException:
    """Attach coordinates (and a :data:`REASONS` code) to an exception and
    return it: ``raise located(SomeError(full_message), Coord(...), "sttm.type")``.
    The message keeps its quoted text (the full tier); the coordinates tier reads
    only ``exc.coord`` / ``exc.reason`` — and (post57) ``exc.role``, the header
    ROLE the error is about (:func:`role_word`: template vocabulary or nothing),
    and ``exc.type_keyword``, the TYPE KEYWORD of the cell (:func:`type_keyword`:
    framework type vocabulary, else ``other``). Neither can carry cell text."""
    exc.coord = coord            # type: ignore[attr-defined]
    exc.reason = reason          # type: ignore[attr-defined]
    if role is not None:
        exc.role = role_word(role)                  # type: ignore[attr-defined]
    if type_text is not None:
        exc.type_keyword = type_keyword(type_text)  # type: ignore[attr-defined]
    return exc


def _chain(exc: BaseException | None):
    seen = 0
    while exc is not None and seen < 12:
        yield exc
        exc = exc.__cause__ or exc.__context__
        seen += 1


def error_coord(exc: BaseException | None) -> Coord | None:
    """The first :class:`Coord` on ``exc`` or the exceptions it was raised from."""
    return next((c for e in _chain(exc) if isinstance(c := getattr(e, "coord", None), Coord)),
                None)


def error_reason(exc: BaseException | None) -> str | None:
    """The first registered reason code on ``exc`` or its chain."""
    return next((r for e in _chain(exc) if (r := getattr(e, "reason", None)) in REASONS), None)


def error_role(exc: BaseException | None) -> str | None:
    """The first allowlisted header role on ``exc`` or its chain."""
    return next((r for e in _chain(exc) if (r := getattr(e, "role", None)) in ROLE_WORDS), None)


def error_type(exc: BaseException | None) -> str | None:
    """The first allowlisted type keyword on ``exc`` or its chain."""
    return next((t for e in _chain(exc)
                 if (t := getattr(e, "type_keyword", None)) in (*TYPE_KEYWORDS, OTHER_TYPE)),
                None)


# ------------------------------------------------- roles and type keywords (post57)

# D1 post55 pairs 05 / 06: "STTM required element missing" / "STTM audit column
# invalid" said nothing of WHAT was missing or invalid. The coordinates tier now
# names the header ROLE — the STTM / FRD template's own vocabulary (the layout
# roles of codegen.layout.profile.Role plus the readers' structural words) — and
# the TYPE KEYWORD of a data type cell — the framework's type vocabulary (the DDL
# type map's keys, the audit datatypes, decimal); any other type reads "other".
# Both are allowlists: a value outside them is dropped (a role) or "other" (a
# type), never echoed. tests/test_error_roles.py keeps them in step with Role.
ROLE_WORDS = frozenset({
    # codegen.layout.profile.Role
    "business_rule", "cadence", "catalog", "column", "comments", "constraints", "critical",
    "data_definition", "data_type", "delimiter", "description", "dq_mandatory", "dq_rules",
    "end", "example", "example_value", "field_description", "field_length", "field_name",
    "field_sheet", "file_pattern", "format", "header_row", "inscope", "key", "length",
    "load_rule", "lob", "mandatory", "mandatory_column", "multi_record", "not_null",
    "null_check", "nullable", "ordinal", "phi", "pii", "position", "primary_key",
    "record_type_field", "recycle_flag", "required", "sample_value", "schema", "segment",
    "server", "source_database", "source_schema", "source_table", "source_type", "start",
    "table", "table_description", "target_type", "title", "transformation", "workspace",
    # the readers' structural words
    "audit_column", "mapping_sheet", "file_details_sheet", "version_sheet", "field_row",
    "metadata_block", "generator", "source_column", "source_datatype", "stage_band",
    "recycle_validation", "version",
})
# template labels -> their role word (the STTM header vocabulary as written)
_ROLE_ALIASES = {
    "columnname": "column", "tablename": "table", "datatype": "data_type",
    "stage_columnname": "column", "standard_columnname": "column",
    "stage_datatype": "target_type", "standard_datatype": "target_type",
    "stage_tablename": "table", "standard_tablename": "table",
    "stage_schema": "schema", "standard_schema": "schema", "files": "file_pattern",
    "file_type": "format", "fixed_width_length": "length", "fixed_width_start": "start",
    "fixed_width_end": "end", "source_datatype": "source_datatype",
}
TYPE_KEYWORDS = frozenset({
    "string", "varchar", "nvarchar", "char", "nchar", "text", "int", "integer", "bigint",
    "smallint", "tinyint", "long", "short", "byte", "decimal", "numeric", "number", "double",
    "float", "real", "money", "date", "datetime", "timestamp", "time", "boolean", "bool",
    "bit", "binary", "varbinary",
})
OTHER_TYPE = "other"
_WORD_TEXT = re.compile(r"[^a-z0-9]+")
_TYPE_HEAD = re.compile(r"^\s*([A-Za-z]+)")


def role_word(text: object) -> str | None:
    """A header role as the coordinates tier may name it — the template label
    normalized (``"stage DataType"`` -> ``target_type``) when it is one of
    :data:`ROLE_WORDS`, else None."""
    word = _WORD_TEXT.sub("_", str(text or "").lower()).strip("_")
    word = _ROLE_ALIASES.get(word, word)
    return word if word in ROLE_WORDS else None


def type_keyword(text: object) -> str | None:
    """A data type cell's leading keyword when it is framework vocabulary
    (``"Decimal(17,2)"`` -> ``decimal``), ``other`` for any other spelling,
    None for a blank cell."""
    raw = str(text if text is not None else "").strip()
    if not raw:
        return None
    match = _TYPE_HEAD.match(raw)
    word = match.group(1).lower() if match else ""
    return word if word in TYPE_KEYWORDS else OTHER_TYPE


# ------------------------------------------------------------------ vocabulary

# The CLI commands (the marker's ``stage``); anything else reads "codegen".
STAGES = frozenset({
    "codegen", "generate", "generate-all", "layout", "extract-sttm", "extract-frd",
    "extract-vdd", "pair", "sharepoint-fetch", "sharepoint-publish", "databricks-fetch",
    "databricks-publish", "databricks-seed-landing", "demo-source-files",
    "demo-metadata-sheet", "doctor", "verify", "layer2",
})

# reason code -> the coordinates tier's phrase. Phrases are fixed text: they may
# name a document ROLE, never a document's content. The harness keys on some of
# them (docs/acfc/HARNESS_EXIT_CODES.md): "contract not found:", "no resolved
# feed matches --feed", "produced no feeds", "under gaps:" — keep those words.
REASONS: dict[str, str] = {
    "unclassified": "error (unclassified)",
    "uncaught": "uncaught exception",
    "input.not_found": "input file not found",
    "workbook.not_found": "workbook not found",
    "contract.not_found": "contract not found:",
    "contract.mismatch": "contract mismatch",
    "contract.invalid": "contract validation",
    "feed.no_match": "no resolved feed matches --feed",
    "feed.none_produced": "produced no feeds",
    "answers.missing": "a value only the answers file can supply (under gaps:)",
    "answers.file": "answers file unreadable or invalid",
    "pairs.file": "pairs override file unreadable or invalid",
    "environment": "environment selection failed",
    "provider": "provider configuration invalid",
    "config": "configuration invalid",
    "usage": "command-line usage error",
    "storage": "storage unavailable",
    "gate.verdict_fail": "gate verdict FAIL (complete, review only: quarantined)",
    "template.gap": "template gap",
    "generate.emit": "generator could not render an artefact",
    "frd.unreadable": "FRD in no documented family (F1 / F2)",
    "frd.docx": "FRD document could not be read",
    "frd.value": "FRD field value invalid",
    "frd.missing": "FRD required element missing",
    "sttm.unreadable": "STTM workbook could not be read",
    "sttm.layout": "STTM layout not recognised",
    "sttm.header": "STTM header not recognised",
    "sttm.band": "STTM band invalid",
    "sttm.value": "STTM cell value invalid",
    "sttm.type": "STTM data type invalid",
    "sttm.audit": "STTM audit column invalid",
    "sttm.segment": "STTM segment layout invalid",
    "sttm.record_type": "STTM record-type spelling outside the vocabulary",
    "sttm.missing": "STTM required element missing",
    "sttm.duplicate": "STTM duplicate entry",
    "sttm.conflict": "STTM entries conflict",
    "vdd.unreadable": "VDD workbook could not be read",
    "vdd.layout": "VDD layout not recognised",
    "vdd.value": "VDD cell value invalid",
    "vdd.crosscheck": "STTM / VDD cross-check failed",
    "layout.unresolved": "layout roles unresolved",
    "layout.model": "layout model call failed",
    "layout.cache": "layout profile cache invalid",
    "layout.answer": "layout answer does not fit the document",
    "publish": "publish failed",
    "verify": "verification mismatch",
}

# Addendum 4 (post52): a contract mismatch is summarised by COUNTS on the first
# line — "contract mismatch, feed 2 of 3: 1 table only in FRD, 2 value conflicts"
# — never the names. Kind -> (singular, plural); the resolver tags each item
# (codegen.resolve.resolver.mismatch_item), the exception carries the counts.
MISMATCH_LABELS: dict[str, tuple[str, str]] = {
    "feed.frd_only": ("feed only in FRD", "feeds only in FRD"),
    "feed.sttm_only": ("feed only in STTM", "feeds only in STTM"),
    "table.frd_only": ("table only in FRD", "tables only in FRD"),
    "table.sttm_only": ("table only in STTM", "tables only in STTM"),
    "table.conflict": ("table conflict", "table conflicts"),
    "segment.frd_only": ("segment only in FRD", "segments only in FRD"),
    "segment.sttm_only": ("segment only in STTM", "segments only in STTM"),
    "segment.missing": ("required segment missing", "required segments missing"),
    "column.frd_only": ("column only in FRD", "columns only in FRD"),
    "column.sttm_only": ("column only in STTM", "columns only in STTM"),
    "column.type_conflict": ("type conflict", "type conflicts"),
    "value.conflict": ("value conflict", "value conflicts"),
    "value.unstated": ("value stated in no document", "values stated in no document"),
    "rule.unparseable": ("recycle rule not parseable", "recycle rules not parseable"),
    "other": ("other mismatch", "other mismatches"),
}


# post74 (D1 post73 pair_10): the STTM contract's validation rules by name,
# rule -> (disposition, what failed); codegen.contracts.validation classifies a
# failure into them. ``question``: no document states the value in a form the
# contract carries - the feed waits for the answer (NEEDS_ANSWERS); ``fail``:
# the extractor built an inconsistent feed. The first line names each failed
# rule and its count: "contract validation: segment_without_table (2) at STTM
# sheet 2". The order is the report order.
CONTRACT_RULES: dict[str, tuple[str, str]] = {
    "value_unstated": ("question", "a value the contract needs is stated by no document "
                                   "(file format, source system, a table / schema)"),
    "value_outside_vocabulary": ("question", "a value outside the contract's vocabulary "
                                             "(a segment, an audit data type)"),
    "value_out_of_range": ("question", "a number outside its range (recycle window days)"),
    "feed_without_audit_columns": ("question", "the feed lists no audit column"),
    "recycle_unknown_column": ("question", "the recycle rule names a column the feed does "
                                           "not carry (its row was skipped or is open)"),
    "segment_missing_on_fields": ("question", "some rows state a record segment, these do not"),
    "segment_without_table": ("question", "a row states a record segment without its stage "
                                          "table, or a table without a segment"),
    "feed_without_fields": ("fail", "no mapping row is left (every row skipped, unmapped or "
                                    "open)"),
    "field_count_mismatch": ("fail", "field_count differs from the fields listed"),
    "load_rule_unknown_column": ("fail", "a not-null / mandatory / PHI list names a column the "
                                         "feed does not carry"),
    "phi_mismatch": ("fail", "the fields flagged PHI differ from the PHI list"),
    "duplicate_feed_id": ("fail", "two feeds of one contract share a feed id"),
    "invalid_value": ("fail", "any other value the contract model refuses"),
}


def error_rules(exc: BaseException | None) -> dict[str, int]:
    """The first ``contract_rules`` mapping on ``exc`` or its chain, known rules only."""
    for e in _chain(exc):
        rules = getattr(e, "contract_rules", None)
        if isinstance(rules, dict):
            return {k: v for k, v in rules.items() if k in CONTRACT_RULES
                    and isinstance(v, int) and not isinstance(v, bool) and v > 0}
    return {}


def rules_summary(rules: object) -> str:
    """``{rule: n}`` as the coordinates tier prints it, in rule order."""
    if not isinstance(rules, dict):
        return ""
    return ", ".join(f"{rule} ({rules[rule]})" for rule in CONTRACT_RULES
                     if isinstance(rules.get(rule), int) and not isinstance(rules.get(rule), bool)
                     and rules[rule] > 0)


def mismatch_summary(counts: object) -> str:
    """``{kind: n}`` as the coordinates tier prints it, in :data:`MISMATCH_LABELS`
    order; unknown kinds / non-int counts are dropped."""
    if not isinstance(counts, dict):
        return ""
    parts = []
    for kind, (one, many) in MISMATCH_LABELS.items():
        n = counts.get(kind)
        if isinstance(n, int) and not isinstance(n, bool) and n > 0:
            parts.append(f"{n} {one if n == 1 else many}")
    return ", ".join(parts)


def error_counts(exc: BaseException | None) -> dict[str, int]:
    """The first ``counts`` mapping on ``exc`` or its chain (registered kinds only)."""
    for e in _chain(exc):
        counts = getattr(e, "counts", None)
        if isinstance(counts, dict):
            return {k: v for k, v in counts.items() if k in MISMATCH_LABELS
                    and isinstance(v, int) and not isinstance(v, bool) and v > 0}
    return {}


# D1 post51 pairs 08-10: an FRD in no documented family is described by its
# table COUNT and each table's header-row fingerprint (12 hex of term_sha256
# over row 0, codegen.extract.frd_docx.header_fingerprint) - never a title.
_FINGERPRINT = re.compile(r"^[0-9a-f]{12}$")
MAX_FINGERPRINTS = 16


def error_tables(exc: BaseException | None) -> dict[str, object] | None:
    """``{"count": n, "fingerprints": [...]}`` from the first exception on the
    chain that carries ``table_count`` (validated: an int, 12-hex strings)."""
    for e in _chain(exc):
        count = getattr(e, "table_count", None)
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            prints = getattr(e, "fingerprints", None) or []
            return {"count": count,
                    "fingerprints": [p for p in prints if isinstance(p, str)
                                     and _FINGERPRINT.match(p)][:MAX_FINGERPRINTS]}
    return None


def tables_summary(tables: object) -> str:
    """The marker's ``tables`` as the coordinates tier prints it; '' when invalid."""
    if not isinstance(tables, dict):
        return ""
    count = tables.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return ""
    prints = [p for p in (tables.get("fingerprints") or []) if isinstance(p, str)
              and _FINGERPRINT.match(p)][:MAX_FINGERPRINTS] \
        if isinstance(tables.get("fingerprints"), list) else []
    text = f"{count} table{'' if count == 1 else 's'}"
    if prints:
        text += f", header-row fingerprints {' '.join(prints)}"
        if count > len(prints):
            text += f" (+{count - len(prints)} more)"
    return text


_PAIR_DIR = re.compile(r"^pair_\d{1,4}$")
_WHERE = re.compile(r"^<workdir>(?:/pair_\d{1,4})?/\u2026$")


def path_hint(path: object) -> str | None:
    """A path as the coordinates tier may show it (addendum 4): the work dir and
    every name in it elided, the harness's own ``pair_NN`` folder kept —
    ``<workdir>/pair_07/…``; ``<workdir>/…`` when there is none."""
    if path is None:
        return None
    parts = [p for p in re.split(r"[\\/]+", str(path)) if p]
    pair = next((p for p in reversed(parts) if _PAIR_DIR.match(p)), None)
    return f"<workdir>/{pair}/\u2026" if pair else "<workdir>/\u2026"


MARKER = "CODEGEN-ERROR "
_EXC_NAME = re.compile(r"^[A-Za-z_][\w.]{0,80}(?:Error|Exception|Exit|Interrupt|Blocked)$")
_CHECK_NAME = re.compile(r"^[a-z][a-z0-9_]{0,48}$")


def _exc_name(name: object) -> str | None:
    return name if isinstance(name, str) and _EXC_NAME.match(name) else None


_KIND = re.compile(r"^[a-z][a-z0-9_]{0,60}$")
MAX_KINDS = 12


def kind_counts(counts: object) -> dict[str, int]:
    """``{kind: n}`` kept only where the kind is a vocabulary token and n a
    positive int — the largest :data:`MAX_KINDS`, ties by name (D1 post51
    pair_01: gate flags by type, a failed check's violations by rule)."""
    if not isinstance(counts, dict):
        return {}
    valid = [(k, v) for k, v in counts.items() if isinstance(k, str) and _KIND.match(k)
             and isinstance(v, int) and not isinstance(v, bool) and v > 0]
    return dict(sorted(valid, key=lambda kv: (-kv[1], kv[0]))[:MAX_KINDS])


def _kinds_text(counts: object) -> str:
    return ", ".join(f"{k} {n}" for k, n in kind_counts(counts).items())


def error_marker(stage: str, reason: str, coord: Coord | None = None, *,
                 exc: BaseException | None = None, checks: tuple[str, ...] | list[str] = (),
                 path: object = None, flags: dict | None = None,
                 violations: dict | None = None) -> str:
    """One ``CODEGEN-ERROR {json}`` line. An exception's own coordinates and
    reason (:func:`located`) win over the catch site's; every field is checked
    against this module's vocabulary on the way in AND on the way out."""
    coord = error_coord(exc) or coord
    payload: dict[str, object] = {
        "stage": stage if stage in STAGES else "codegen",
        "reason": error_reason(exc) or (reason if reason in REASONS else "unclassified"),
        "coord": coord.as_dict() if isinstance(coord, Coord) else None,
        "exception": _exc_name(type(exc).__name__) if exc is not None else None,
        "checks": [c for c in checks if isinstance(c, str) and _CHECK_NAME.match(c)][:12],
        "counts": error_counts(exc),
        "where": path_hint(path),
    }
    rules = error_rules(exc)
    if rules:
        payload["rules"] = rules
    role, kind = error_role(exc), error_type(exc)
    if role is not None:
        payload["role"] = role
    if kind is not None:
        payload["type"] = kind
    tables = error_tables(exc)
    if tables is not None:
        payload["tables"] = tables
    # a gate FAIL (pair_01): flags by type, the failed checks' violations by rule
    if kind_counts(flags):
        payload["flags"] = kind_counts(flags)
    if kind_counts(violations):
        payload["violations"] = kind_counts(violations)
    return MARKER + json.dumps(payload, sort_keys=True)


def report_error(stage: str, reason: str, coord: Coord | None = None, *,
                 exc: BaseException | None = None, checks: tuple[str, ...] | list[str] = (),
                 path: object = None, stream=None, flags: dict | None = None,
                 violations: dict | None = None) -> None:
    """Print the marker for one FAIL line (stderr by default)."""
    print(error_marker(stage, reason, coord, exc=exc, checks=checks, path=path, flags=flags,
                       violations=violations),
          file=stream or sys.stderr, flush=True)


def coordinate_line(payload: object) -> str:
    """A marker payload as the coordinates tier prints it — rebuilt from the
    vocabulary; a field that does not validate is dropped, never echoed."""
    data = payload if isinstance(payload, dict) else {}
    stage = data.get("stage") if data.get("stage") in STAGES else "codegen"
    reason = data.get("reason") if data.get("reason") in REASONS else "unclassified"
    phrase = REASONS[reason]
    line = f"{'FAIL':<15} {stage} — {phrase}"
    # post57: what kind of thing — "(role target_type; type tinyint)"
    what = []
    if data.get("role") in ROLE_WORDS:
        what.append(f"role {data['role']}")
    if data.get("type") in (*TYPE_KEYWORDS, OTHER_TYPE):
        what.append(f"type {data['type']}")
    if what and not phrase.endswith(":"):
        line += f" ({'; '.join(what)})"
    coord = Coord.from_dict(data.get("coord"))
    if reason == "contract.mismatch":
        # "contract mismatch, feed 2 of 3: 4 columns only in FRD, ..." (addendum 4)
        summary = mismatch_summary(data.get("counts"))
        line += (f", {coord}" if coord is not None else "") + (f": {summary}" if summary else "")
    elif reason == "contract.invalid":
        # post74: "contract validation: segment_without_table (2) at STTM sheet 2"
        summary = rules_summary(data.get("rules"))
        line += (f": {summary}" if summary else "") + (f" at {coord}" if coord is not None
                                                        else "")
    elif coord is not None:
        line += f" {coord}" if phrase.endswith(":") else f" at {coord}"
    tables = tables_summary(data.get("tables"))
    if tables:
        # "... at FRD: 12 tables, header-row fingerprints 1a2b3c4d5e6f ..."
        line += f": {tables}"
    where = data.get("where")
    if isinstance(where, str) and _WHERE.match(where):
        line += f" {where}"
    checks = [c for c in (data.get("checks") or []) if isinstance(c, str)
              and _CHECK_NAME.match(c)][:12] if isinstance(data.get("checks"), list) else []
    detail = []
    if checks:
        violations = _kinds_text(data.get("violations"))
        detail.append(f"failed checks: {', '.join(checks)}"
                      + (f" [{violations}]" if violations else ""))
    flags = _kinds_text(data.get("flags"))
    if flags:
        detail.append(f"flags by type: {flags}")
    if detail:
        line += f" ({'; '.join(detail)})"
    name = _exc_name(data.get("exception"))
    if name:
        line += f" [{name}]"
    return line


# ---------------------------------------------------------- model usage (post74)

# D1 post73 pair_11 (556 s): the report had no MODEL USAGE line, so where the
# time went could not be read. Every "MODEL USAGE" console line is paired with
# one ``CODEGEN-USAGE {json}`` marker on stderr — the stage (layout | layer2),
# the provider word and numbers only (calls, requests, seconds, failed,
# recovered); never a model reply, never a document's text. The harness reads
# them with :func:`model_usage` / :func:`usage_summary` (STABLE).
USAGE_MARKER = "CODEGEN-USAGE "
USAGE_STAGES = ("layout", "layer2")
USAGE_PROVIDERS = ("databricks_fmapi", "anthropic", "mock", "replay", "none",
                   # post76: Layer 2 not asked in this run (codegen.layer2_stage)
                   "deferred", "skipped")
_USAGE_INTS = ("calls", "requests", "failed", "recovered")


def _usage_entry(data: object) -> dict | None:
    """A usage payload kept only when every field validates."""
    if not isinstance(data, dict) or data.get("stage") not in USAGE_STAGES:
        return None
    entry: dict[str, object] = {"stage": data["stage"],
                                "provider": data.get("provider")
                                if data.get("provider") in USAGE_PROVIDERS else "none"}
    for name in _USAGE_INTS:
        value = data.get(name, 0)
        entry[name] = value if isinstance(value, int) and not isinstance(value, bool) \
            and value >= 0 else 0
    seconds = data.get("seconds", 0)
    entry["seconds"] = round(float(seconds), 1) if isinstance(seconds, (int, float)) \
        and not isinstance(seconds, bool) and seconds >= 0 else 0.0
    return entry


def usage_entry(usage: object) -> dict | None:
    """One stage's usage (a ``StageUsage`` or a dict) as validated numbers."""
    data = usage if isinstance(usage, dict) else {
        name: getattr(usage, name, None) for name in ("stage", "provider", "seconds",
                                                      *_USAGE_INTS)}
    return _usage_entry(data)


def usage_marker(usage: object) -> str | None:
    """The marker line of one stage's usage (a ``StageUsage`` or a dict)."""
    entry = usage_entry(usage)
    return None if entry is None else USAGE_MARKER + json.dumps(entry, sort_keys=True)


def report_usage(usage: object, stream=None) -> None:
    line = usage_marker(usage)
    if line is not None:
        print(line, file=stream or sys.stderr, flush=True)


def model_usage(stderr: str | bytes | None = "", stdout: str | bytes | None = "") -> list[dict]:
    """STABLE (post74): every validated ``CODEGEN-USAGE`` marker of one stage's
    output, in order — whatever its exit code."""
    out = []
    for line in (*_text(stderr).splitlines(), *_text(stdout).splitlines()):
        if line.startswith(USAGE_MARKER):
            try:
                entry = _usage_entry(json.loads(line[len(USAGE_MARKER):]))
            except ValueError:
                entry = None
            if entry is not None:
                out.append(entry)
    return out


def usage_summary(entries: list[dict]) -> str:
    """STABLE (post74): the per-stage line a report carries — ``layout: 2
    call(s) in 41.3s (databricks_fmapi); layer2: 20 call(s) in 480.2s over 5
    feed(s), 1 failed`` — or ``no model call`` when nothing was asked."""
    totals: dict[str, dict] = {}
    for entry in (e for e in (_usage_entry(x) for x in entries or []) if e is not None):
        total = totals.setdefault(entry["stage"], {"calls": 0, "seconds": 0.0, "failed": 0,
                                                    "feeds": 0, "providers": []})
        total["calls"] += entry["calls"]
        total["seconds"] += entry["seconds"]
        total["failed"] += entry["failed"]
        total["feeds"] += 1
        if entry["provider"] not in total["providers"]:
            total["providers"].append(entry["provider"])
    parts = []
    for stage in USAGE_STAGES:
        if stage not in totals:
            continue
        t = totals[stage]
        text = (f"{stage}: {t['calls']} call(s) in {t['seconds']:.1f}s "
                f"({', '.join(t['providers'])})")
        if stage == "layer2":
            text += f" over {t['feeds']} feed(s)"
        if t["failed"]:
            text += f", {t['failed']} failed"
        parts.append(text)
    return "; ".join(parts) or "no model call"


# -------------------------------------------------------------------- warnings

# path:lineno: SomethingWarning: message   (warnings.formatwarning)
_WARN_LOCATED = re.compile(r"^.+:\d+: (?:[A-Za-z_][\w.]*)?Warning: ")
# any located category line (PydanticDeprecatedSince20 does not end in Warning)
_LOCATED = re.compile(r"^.+:\d+: [A-Za-z_][\w.]*: ")
# SomethingWarning: message                  (a bare category line)
_WARN_BARE = re.compile(r"^\s*(?:[A-Za-z_][\w.]*)?Warning: ")
_WARN_CALL = re.compile(r"^\s*warnings\.warn(?:_explicit)?\(")
_PYDANTIC = re.compile(r"PydanticDeprecat(?:edSince\d+|ionWarning)")
_ERROR_OPEN = re.compile(r"^(?:Traceback \(most recent call last\)|FAIL\b|ERROR\b|"
                         r"(?:[A-Za-z_][\w.]*)?(?:Error|Exception)\b:?)")
# Lines that end a warning block: the CLI's padded labels ("NOTE           x"),
# log records, codegen's own banner lines, the error marker.
_CLI_LABEL = re.compile(r"^[A-Z][A-Z_]*(?: [A-Z_]+)*\s{2,}\S")
_LOG_RECORD = re.compile(r"^(?:\d{4}-\d\d-\d\d[ T]\d|(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)"
                         r"(?::|\s))")
_CODEGEN_LOG = re.compile(r"^(?:codegen \d|config overlays\b|" + re.escape(MARKER.strip()) + "|"
                          + re.escape(USAGE_MARKER.strip()) + ")")


def is_warning_line(line: str) -> bool:
    """A line that OPENS a warning block (never an error)."""
    return bool(_WARN_LOCATED.match(line) or _WARN_BARE.match(line)
                or _WARN_CALL.match(line) or _PYDANTIC.search(line))


def _ends_block(line: str) -> bool:
    stripped = line.strip()
    return bool(_ERROR_OPEN.match(stripped) or is_warning_line(line) or _CLI_LABEL.match(line)
                or _LOG_RECORD.match(line) or _CODEGEN_LOG.match(line)) \
        and not line[:1].isspace()


def without_warnings(text: str) -> list[str]:
    """``text``'s lines minus every Python warning BLOCK.

    A block is the warning's head (``path:line: Category: message``, a bare
    ``Category: message`` or a ``warnings.warn(`` line) plus its continuation:
    the message's further lines — blank ones included (pydantic's
    protected-namespace message has one; D1 post51 reported its second half,
    "You may be able to resolve this warning ...", as pair_07's error) — through
    the indented source line ``warnings`` prints under it. The block ends early,
    exclusive, at the next traceback / error line, warning head, CLI label line,
    log record or codegen banner line."""
    kept: list[str] = []
    lines = (text or "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not is_warning_line(line):
            kept.append(line)
            i += 1
            continue
        i += 1                                           # the head
        while i < len(lines):
            nxt = lines[i]
            if nxt[:1].isspace() and nxt.strip():        # the source line(s): end of block
                while i < len(lines) and lines[i][:1].isspace() and lines[i].strip():
                    i += 1
                break
            if nxt.strip() and _ends_block(nxt):
                break
            i += 1                                       # message continuation / blank
    return kept


# ----------------------------------------------------------------- the readers

def _failed(returncode: int | None) -> bool:
    """Per stage: exit 0 = PASS, exit 3 = NEEDS_ANSWERS — neither is an error."""
    return bool(returncode) and returncode != 3


def _lines(stderr, stdout) -> list[str]:
    return [ln for ln in (*without_warnings(_text(stderr)), *without_warnings(_text(stdout)))
            if ln.strip()]


def first_error_line(returncode: int, stderr: str | bytes | None = "",
                     stdout: str | bytes | None = "") -> str | None:
    """The COORDINATES-ONLY error line of one finished ``codegen`` stage — the
    tier a pushed report may carry.

    STABLE API (2026-10-15; post52 version note: the text is coordinates only,
    and exit 3 returns None) — imported by the ACFC harness; signature unchanged:

    - ``returncode`` 0 (PASS) or 3 (NEEDS_ANSWERS) -> ``None``, whatever the
      streams hold; stderr is consulted only when the stage FAILed;
    - the first ``CODEGEN-ERROR`` marker (stderr before stdout) ->
      ``"FAIL            <stage> — <reason phrase> at <coordinates> [<Exception>]"``,
      e.g. ``FAIL            extract-sttm — STTM audit column invalid at STTM
      sheet 2 row 28 col 7 [ExtractionError]``;
    - no marker: an uncaught traceback -> ``"... codegen — uncaught exception
      [<ExceptionClass>]"``; any other output -> ``"... codegen — error
      (unclassified)"`` (the quoted line is :func:`first_error_line_full`'s).

    The result is assembled only from :data:`REASONS`, :data:`STAGES`,
    integers and a validated exception class name — no output text passes."""
    if not _failed(returncode):
        return None
    lines = _lines(stderr, stdout)
    for ln in lines:
        if ln.startswith(MARKER):
            try:
                return coordinate_line(json.loads(ln[len(MARKER):]))
            except ValueError:
                return coordinate_line({})
    name = _traceback_exception(lines)
    if name is not None:
        return coordinate_line({"reason": "uncaught", "exception": name})
    return coordinate_line({})


def first_error_line_full(returncode: int, stderr: str | bytes | None = "",
                          stdout: str | bytes | None = "") -> str | None:
    """The QUOTED error line (sheet / file / feed names included) — for
    ``codegen-outputs/`` inside ACFC only, never a pushed report.

    Same exit-code rule as :func:`first_error_line` (0 / 3 -> ``None``); else
    the first line, stderr before stdout, that opens an error
    (``Traceback (most recent call last):``, a ``FAIL`` / ``ERROR`` line,
    ``<Name>Error:`` / ``<Name>Exception:``), warning blocks and marker lines
    skipped; no such line -> the first non-empty one; none -> ``""``."""
    if not _failed(returncode):
        return None
    lines = [ln for ln in _lines(stderr, stdout)
             if not ln.startswith((MARKER, USAGE_MARKER))]
    return next((ln for ln in lines if _ERROR_OPEN.match(ln.strip())),
                lines[0] if lines else "")


def _traceback_exception(lines: list[str]) -> str | None:
    """The exception class of the first traceback's final line, if it parses."""
    start = next((i for i, ln in enumerate(lines)
                  if ln.startswith("Traceback (most recent call last)")), None)
    if start is None:
        return None
    for ln in lines[start + 1:]:
        if ln[:1].isspace():
            continue
        head = ln.split(":", 1)[0].strip()
        return _exc_name(head) or ""
    return ""


def _text(stream: str | bytes | None) -> str:
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode("utf-8", errors="replace")
    return stream


def silence_pydantic_deprecations() -> None:
    """Ignore Pydantic's deprecation category (and only it) in this process.
    No-op when pydantic does not define it."""
    try:
        from pydantic.warnings import PydanticDeprecationWarning
    except ImportError:         # pragma: no cover - pydantic < 2.0 / absent
        return
    warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)


__all__ = ["CONTRACT_RULES", "DOCS", "MARKER", "MISMATCH_LABELS", "OTHER_TYPE", "REASONS",
           "USAGE_MARKER", "model_usage", "report_usage", "usage_entry", "usage_marker",
           "usage_summary",
           "ROLE_WORDS", "STAGES", "TYPE_KEYWORDS", "Coord", "column_number", "error_role",
           "error_type", "role_word", "type_keyword",
           "coordinate_line", "error_coord", "error_counts", "error_marker", "error_reason",
           "error_rules", "error_tables", "kind_counts", "rules_summary", "tables_summary",
           "first_error_line", "first_error_line_full", "is_warning_line", "located",
           "mismatch_summary", "path_hint", "report_error", "sheet_number",
           "silence_pydantic_deprecations", "without_warnings"]
