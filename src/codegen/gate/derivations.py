"""Derivation gate (M7 §2 f–i): every derived NAME, PATH and SQL LITERAL is
checked before it ships, and the sibling-type consistency of the standard
band is flagged.

* IIG cells: no cell may contain a line break; identifier columns
  (``derivations.name_columns``) must match the name charset and the length
  cap; path columns (``derivations.path_column_suffixes``) may hold no
  whitespace, no empty segment, no segment ending in punctuation, exactly
  one separator between segments, and stay under the path cap. A
  violation is a FAILED gate check naming the field, the value (truncated)
  and the provenance the cell was built from.
* SQL literals in the deployment DDL (``COMMENT '…'``, ``LOCATION '…'``,
  TBLPROPERTIES values): no newline / carriage return, balanced quotes
  after escaping, no leading / trailing whitespace; ``LOCATION`` literals
  are paths and follow the path rules too.
* Path assembly (:func:`join_path`) joins NORMALIZED segments; callers never
  string-concatenate a raw value.
* Name tokens (:func:`short_token`): a component of a WF_/NB_ name comes
  from a short token or stays blank — never a slug of prose.
* Sibling types: standard-band columns grouped by trailing suffix
  (``_pct``, ``_amt`` … from config, plus any suffix ≥ ``sibling_min_group``
  columns share); a group mixing base types is flagged
  ``sibling_type_mismatch:<suffix>`` citing the minority rows' STTM cells.
  The type is never altered.

Caps are config (``gate.derivations``): the framework's own limits are not
documented, so the shipped values are conservative defaults, stated as such.
"""

from __future__ import annotations

import re
from collections import Counter

from codegen.config import Config, DerivationsConfig
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.gate.preflight import GateCheck

_PATH_SEPARATORS = re.compile(r"[\\/]+")
_TRAILING_PUNCT = ".,;:"
# M10.2: a value with one of these schemes is a LOCATION URI, not a folder
# path — validated as a URI (scheme, authority, no whitespace, its path
# segments by the folder rules) and carried through unchanged.
LOCATION_SCHEMES = ("abfss", "abfs", "wasbs", "wasb", "dbfs", "s3", "s3a", "adl", "gs")
_SCHEME_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9+.-]*):/")


def location_scheme(value: str | None) -> str | None:
    """``abfss`` for ``abfss://c@a.dfs.core.windows.net/x``, ``dbfs`` for
    ``dbfs:/mnt/x``; None for a folder path (or an unknown scheme, which the
    folder rules then reject — ``https://`` is not a storage location)."""
    match = _SCHEME_RE.match(value or "")
    scheme = match.group(1).lower() if match else None
    return scheme if scheme in LOCATION_SCHEMES else None


def split_location(value: str) -> tuple[str, str, str]:
    """(scheme, authority, path) of a location URI. ``dbfs:/mnt/x`` has no
    authority: ('dbfs', '', '/mnt/x')."""
    text = value.strip()
    scheme, _, rest = text.partition(":")
    if rest.startswith("//"):
        authority, _, tail = rest[2:].partition("/")
        return scheme.lower(), authority, "/" + tail if tail or rest[2:].endswith("/") else ""
    return scheme.lower(), "", rest


def uri_violations(value: str, cap: int) -> list[str]:
    """The location-URI rule: scheme + authority (except dbfs:/), no line
    break / whitespace, length cap, and every path segment by the folder
    rules (no empty segment, none ending in punctuation)."""
    problems: list[str] = []
    if "\n" in value or "\r" in value:
        problems.append("line break")
    if re.search(r"\s", value):
        problems.append("whitespace")
    if len(value) > cap:
        problems.append(f"length {len(value)} > {cap}")
    scheme, authority, path = split_location(value)
    if scheme != "dbfs" and not authority:
        problems.append(f"no authority after {scheme}://")
    if authority and authority[-1] in _TRAILING_PUNCT:
        problems.append(f"authority {authority!r} ends in punctuation")
    inner = path.strip("/")
    for segment in inner.split("/") if inner else []:
        if segment == "":
            problems.append("empty segment")
        elif segment[-1] in _TRAILING_PUNCT:
            problems.append(f"segment {segment!r} ends in punctuation")
    return problems


def join_location(uri: str, *parts: str | None) -> str:
    """A location URI + relative segments: the URI's own text is kept, the
    parts are normalized like ``join_path`` and appended with one separator
    each. The scheme / authority are never re-spelt."""
    base = uri.strip().rstrip("/")
    tail = join_path(*parts)
    return f"{base}/{tail}" if tail else base + "/"
_LITERAL_RE = re.compile(r"(COMMENT|LOCATION)\s+'((?:[^']|'')*)'", re.IGNORECASE)
_TBLPROP_RE = re.compile(r"'((?:[^']|'')*)'\s*=\s*'((?:[^']|'')*)'")


def _truncate(value: str, limit: int = 80) -> str:
    text = value.replace("\n", "\\n").replace("\r", "\\r")
    return text if len(text) <= limit else text[:limit] + "…"


# ----------------------------------------------------------------- paths ---


def path_segments(value: str) -> list[str]:
    """Segments of a path in either separator style, whitespace-stripped;
    the empty segments a doubled separator leaves are KEPT so the check can
    name them (assembly drops them, checking reports them)."""
    text = value.strip()
    if text.startswith(("abfss://", "https://", "http://", "wasbs://", "dbfs:/")):
        scheme, _, rest = text.partition("://")
        return [f"{scheme}://" + rest.split("/", 1)[0]] + (
            rest.split("/", 1)[1].split("/") if "/" in rest else [])
    return re.split(r"[\\/]", text.strip("\\/")) if text.strip("\\/") else []


def path_violations(value: str, cap: int) -> list[str]:
    problems: list[str] = []
    if "\n" in value or "\r" in value:
        problems.append("line break")
    if re.search(r"\s", value):
        problems.append("whitespace")
    if len(value) > cap:
        problems.append(f"length {len(value)} > {cap}")
    if re.search(r"(?<!:)//|\\\\", value.replace("://", "", 1)):
        problems.append("doubled separator")
    for segment in path_segments(value):
        if segment == "":
            problems.append("empty segment")
        elif segment[-1] in _TRAILING_PUNCT:
            problems.append(f"segment {segment!r} ends in punctuation")
    return problems


def join_path(*parts: str | None, separator: str = "/") -> str:
    """Assemble a path from NORMALIZED segments: every part is split on both
    separator styles, blanks are dropped, each segment is stripped, and the
    result carries exactly one separator between segments (a scheme prefix
    such as ``abfss://host`` is kept as the first segment). Segments are not
    otherwise altered — a segment ending in punctuation is the gate's job."""
    segments: list[str] = []
    for part in parts:
        if not part:
            continue
        text = str(part).strip()
        if "://" in text:
            scheme, _, rest = text.partition("://")
            host, _, tail = rest.partition("/")
            segments.append(f"{scheme}://{host}")
            text = tail
        segments.extend(s.strip() for s in _PATH_SEPARATORS.split(text) if s.strip())
    return separator.join(segments)


# ----------------------------------------------------------------- names ---


def short_token(value: str | None, max_length: int) -> str | None:
    """The value as a name token when it IS one (single line, no longer than
    the cap after sanitizing); None for prose, which never becomes a name."""
    if not value or "\n" in value or "\r" in value:
        return None
    token = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    if not token or len(token) > max_length:
        return None
    return token


# ------------------------------------------------------------- IIG cells ---


def _is_path_column(header: str, cfg: DerivationsConfig) -> bool:
    upper = header.upper()
    return any(upper.endswith(s.upper()) for s in cfg.path_column_suffixes)


def check_iig_derivations(payload: dict, config: Config) -> GateCheck:
    """Every cell of the framework config rows: single line; identifier
    columns match the charset + cap; path columns follow the path rules."""
    cfg = config.gate.derivations
    pattern = re.compile(cfg.name_pattern)
    problems: list[str] = []
    uris = 0
    for tab_name, tab in payload.get("tabs", {}).items():
        for row_index, row in enumerate(tab.get("rows", []), start=2):
            for header, value in row.get("values", {}).items():
                if value in ("", None) or not isinstance(value, str):
                    continue
                badge = row.get("badges", {}).get(header, {})
                source = badge.get("badge", "?")
                if badge.get("tooltip"):
                    source += f" — {badge['tooltip']}"
                where = f"{tab_name}!{header} row {row_index} ({source})"
                if "\n" in value or "\r" in value:
                    problems.append(f"{where}: line break in {_truncate(value)!r}")
                    continue
                if header in cfg.name_columns:
                    cap = cfg.name_max_length.get(header, cfg.name_max_length.get("default", 128))
                    if not pattern.match(value):
                        problems.append(f"{where}: {_truncate(value)!r} is not an identifier "
                                        f"({cfg.name_pattern})")
                    if len(value) > cap:
                        problems.append(f"{where}: length {len(value)} > {cap}")
                elif _is_path_column(header, cfg):
                    # M10.2: which rule applied is part of the finding.
                    if location_scheme(value):
                        uris += 1
                        for problem in uri_violations(value, cfg.path_max_length):
                            problems.append(f"{where}: {problem} in {_truncate(value)!r} "
                                            "(location URI rule)")
                    else:
                        for problem in path_violations(value, cfg.path_max_length):
                            problems.append(f"{where}: {problem} in {_truncate(value)!r}")
    if problems:
        return GateCheck(name="derivations", passed=False, details="; ".join(problems))
    details = "every derived name and path is single-line and within its cap"
    if uris:
        details += f"; {uris} location URI cell(s) checked by the location URI rule"
    return GateCheck(name="derivations", passed=True, details=details)


# ---------------------------------------------------------- SQL literals ---


def literal_violations(literal: str, *, is_path: bool, cfg: DerivationsConfig) -> list[str]:
    problems: list[str] = []
    if "\n" in literal or "\r" in literal:
        problems.append("line break")
    if literal != literal.strip():
        problems.append("leading/trailing whitespace")
    if literal.replace("''", "").count("'"):
        problems.append("unbalanced quote")
    if is_path:
        problems.extend(uri_violations(literal, cfg.path_max_length)
                        if location_scheme(literal)
                        else path_violations(literal, cfg.path_max_length))
    return problems


def check_sql_literals(ddl_texts: list[tuple[str, str]], config: Config) -> GateCheck:
    """COMMENT / LOCATION / TBLPROPERTIES literals of every emitted DDL text."""
    cfg = config.gate.derivations
    problems: list[str] = []
    for name, text in ddl_texts:
        for match in _LITERAL_RE.finditer(text):
            kind, literal = match.group(1).upper(), match.group(2)
            for problem in literal_violations(literal, is_path=kind == "LOCATION", cfg=cfg):
                problems.append(f"{name}: {kind} literal {_truncate(literal)!r}: {problem}")
        for match in _TBLPROP_RE.finditer(text):
            for literal in match.groups():
                for problem in literal_violations(literal, is_path=False, cfg=cfg):
                    problems.append(f"{name}: TBLPROPERTIES literal {_truncate(literal)!r}: "
                                    f"{problem}")
    return GateCheck(name="sql_literals", passed=not problems,
                     details="; ".join(problems) if problems
                     else "every COMMENT / LOCATION / TBLPROPERTIES literal is single-line")


# --------------------------------------------------------- sibling types ---


def _base_type(dtype: str | None) -> str:
    return re.sub(r"\(.*\)", "", dtype or "").strip().lower()


def sibling_type_flags(spec: ResolvedFeedSpec, config: Config) -> list[str]:
    """One ``sibling_type_mismatch:<suffix>`` flag per suffix group whose
    standard-band base types differ, citing the minority rows' STTM cells.
    Groups: suffixes from config, plus any suffix ``sibling_min_group`` or
    more columns share. The types are transcribed as stated, never altered."""
    cfg = config.gate.derivations
    configured = {s.lower() for s in cfg.sibling_suffixes}
    flags: list[str] = []
    for segment in spec.segments:
        groups: dict[str, list] = {}
        for f in segment.fields:
            name = f.standard_column or f.stage_column
            if not f.standard_datatype or "_" not in name:
                continue
            suffix = "_" + name.rsplit("_", 1)[1].lower()
            groups.setdefault(suffix, []).append(f)
        for suffix, fields in sorted(groups.items()):
            if suffix not in configured and len(fields) < cfg.sibling_min_group:
                continue
            counts = Counter(_base_type(f.standard_datatype) for f in fields)
            if len(counts) < 2:
                continue
            majority = counts.most_common(1)[0][0]
            minority = [f for f in fields if _base_type(f.standard_datatype) != majority]
            cited = ", ".join(
                f"{f.standard_column or f.stage_column} {f.standard_datatype}"
                + (f" ({f.provenance.sheet} row {f.provenance.row})" if f.provenance else "")
                for f in minority)
            flags.append(
                f"sibling_type_mismatch:{suffix} — {segment.stage_table.table}: "
                f"{len(fields)} columns end in {suffix}, {counts[majority]} typed "
                f"{majority}, minority: {cited}; transcribed as stated, confirm with the STTM "
                "author")
    return flags


__all__ = [
    "check_iig_derivations",
    "check_sql_literals",
    "join_path",
    "literal_violations",
    "path_segments",
    "path_violations",
    "short_token",
    "sibling_type_flags",
]
