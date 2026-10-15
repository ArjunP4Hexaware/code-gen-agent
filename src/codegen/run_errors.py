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
the stage, a reason code from :data:`REASONS` and a :class:`Coord`. A raise
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


def located(exc: BaseException, coord: Coord | None, reason: str | None = None) -> BaseException:
    """Attach coordinates (and a :data:`REASONS` code) to an exception and
    return it: ``raise located(SomeError(full_message), Coord(...), "sttm.type")``.
    The message keeps its quoted text (the full tier); the coordinates tier reads
    only ``exc.coord`` / ``exc.reason``."""
    exc.coord = coord            # type: ignore[attr-defined]
    exc.reason = reason          # type: ignore[attr-defined]
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


# ------------------------------------------------------------------ vocabulary

# The CLI commands (the marker's ``stage``); anything else reads "codegen".
STAGES = frozenset({
    "codegen", "generate", "generate-all", "layout", "extract-sttm", "extract-frd",
    "extract-vdd", "pair", "sharepoint-fetch", "sharepoint-publish", "databricks-fetch",
    "databricks-publish", "databricks-seed-landing", "demo-source-files",
    "demo-metadata-sheet", "doctor", "verify",
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
    "contract.invalid": "contract fails validation",
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
    "gate.verdict_fail": "gate verdict FAIL",
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


def error_marker(stage: str, reason: str, coord: Coord | None = None, *,
                 exc: BaseException | None = None, checks: tuple[str, ...] | list[str] = (),
                 path: object = None) -> str:
    """One ``CODEGEN-ERROR {json}`` line. An exception's own coordinates and
    reason (:func:`located`) win over the catch site's; every field is checked
    against this module's vocabulary on the way in AND on the way out."""
    coord = error_coord(exc) or coord
    payload = {
        "stage": stage if stage in STAGES else "codegen",
        "reason": error_reason(exc) or (reason if reason in REASONS else "unclassified"),
        "coord": coord.as_dict() if isinstance(coord, Coord) else None,
        "exception": _exc_name(type(exc).__name__) if exc is not None else None,
        "checks": [c for c in checks if isinstance(c, str) and _CHECK_NAME.match(c)][:12],
        "counts": error_counts(exc),
        "where": path_hint(path),
    }
    return MARKER + json.dumps(payload, sort_keys=True)


def report_error(stage: str, reason: str, coord: Coord | None = None, *,
                 exc: BaseException | None = None, checks: tuple[str, ...] | list[str] = (),
                 path: object = None, stream=None) -> None:
    """Print the marker for one FAIL line (stderr by default)."""
    print(error_marker(stage, reason, coord, exc=exc, checks=checks, path=path),
          file=stream or sys.stderr, flush=True)


def coordinate_line(payload: object) -> str:
    """A marker payload as the coordinates tier prints it — rebuilt from the
    vocabulary; a field that does not validate is dropped, never echoed."""
    data = payload if isinstance(payload, dict) else {}
    stage = data.get("stage") if data.get("stage") in STAGES else "codegen"
    reason = data.get("reason") if data.get("reason") in REASONS else "unclassified"
    phrase = REASONS[reason]
    line = f"{'FAIL':<15} {stage} — {phrase}"
    coord = Coord.from_dict(data.get("coord"))
    if reason == "contract.mismatch":
        # "contract mismatch, feed 2 of 3: 4 columns only in FRD, ..." (addendum 4)
        summary = mismatch_summary(data.get("counts"))
        line += (f", {coord}" if coord is not None else "") + (f": {summary}" if summary else "")
    elif coord is not None:
        line += f" {coord}" if phrase.endswith(":") else f" at {coord}"
    where = data.get("where")
    if isinstance(where, str) and _WHERE.match(where):
        line += f" {where}"
    checks = [c for c in (data.get("checks") or []) if isinstance(c, str)
              and _CHECK_NAME.match(c)][:12] if isinstance(data.get("checks"), list) else []
    if checks:
        line += f" (failed checks: {', '.join(checks)})"
    name = _exc_name(data.get("exception"))
    if name:
        line += f" [{name}]"
    return line


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
_CODEGEN_LOG = re.compile(r"^(?:codegen \d|config overlays\b|" + re.escape(MARKER.strip()) + ")")


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
    lines = [ln for ln in _lines(stderr, stdout) if not ln.startswith(MARKER)]
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


__all__ = ["DOCS", "MARKER", "MISMATCH_LABELS", "REASONS", "STAGES", "Coord", "column_number",
           "coordinate_line", "error_coord", "error_counts", "error_marker", "error_reason",
           "first_error_line", "first_error_line_full", "is_warning_line", "located",
           "mismatch_summary", "path_hint", "report_error", "sheet_number",
           "silence_pydantic_deprecations", "without_warnings"]
