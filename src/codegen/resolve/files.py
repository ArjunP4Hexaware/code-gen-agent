"""The files a feed receives (multi-table step 1, rule 2).

docs/acfc/MULTI_TABLE_DESIGN.md rule 2: files are the distinct SRC_FILE_NAME
patterns the feed receives. A pattern holding a LOB-varying token
(``extractor.lob_tokens``, e.g. ``<LOB>``) while N LOBs are listed expands to
N files, one per LOB (the LOB is the partition value); any other pattern is
one file with no LOB (pair 1: four patterns -> four files, LOB blank).
Patterns keep their own wording otherwise — date placeholders included; how a
pattern is written into an IIG cell is the emitter's business.
"""

from __future__ import annotations

import re

from codegen.contracts.sttm import SttmFeed
from codegen.contracts.tables import FeedFile

_PATTERN_SPLIT = re.compile(r"[\n;,]+")
_LOB_SPLIT = re.compile(r"[\n;,/]+")


def lob_token(pattern: str, tokens: list[str]) -> str | None:
    """The LOB-varying token in ``pattern`` as written there (case-insensitive
    match against ``tokens``), else None."""
    lowered = pattern.lower()
    for token in tokens:
        index = lowered.find(token.lower())
        if index >= 0:
            return pattern[index:index + len(token)]
    return None


def split_lobs(text: str | None, blank_values: list[str] | None = None) -> list[str]:
    """LOB codes from a header-block cell: ``,`` ``;`` ``/`` or newline
    separated, blanks and placeholder values (``TBD`` …) dropped, order kept,
    duplicates once."""
    blanks = {v.strip().lower() for v in blank_values or []}
    parts = [p.strip() for p in _LOB_SPLIT.split(text or "")]
    return list(dict.fromkeys(p for p in parts if p and p.lower() not in blanks))


def split_patterns(text: str | None) -> list[str]:
    """File patterns from a header-block cell (newline / ``;`` / ``,``)."""
    return list(dict.fromkeys(p.strip() for p in _PATTERN_SPLIT.split(text or "") if p.strip()))


def expand_files(patterns: list[str], lobs: list[str], tokens: list[str],
                 provenance: str = "") -> tuple[list[FeedFile], list[str]]:
    """Rule 2 over ``patterns``: a pattern with a LOB token and N listed LOBs
    -> N files; otherwise one file. Returns (files, flags); a pattern holding
    the token while no LOB is listed stays one file, token unexpanded,
    flagged ``lob_token_without_lobs:<pattern>``."""
    files: dict[str, FeedFile] = {}
    flags: list[str] = []
    for pattern in dict.fromkeys(p.strip() for p in patterns if p and p.strip()):
        token = lob_token(pattern, tokens)
        if token is not None and lobs:
            for lob in lobs:
                expanded = pattern.replace(token, lob)
                files.setdefault(expanded, FeedFile(
                    pattern=expanded, lob=lob, template=pattern,
                    provenance=(f"{provenance}: {pattern!r} with {token} = {lob!r} (one file "
                                f"per listed LOB)" if provenance else
                                f"{pattern!r} with {token} = {lob!r}")))
            continue
        if token is not None:
            flags.append(f"lob_token_without_lobs:{pattern} — the pattern varies by LOB "
                         f"({token}) but no LOB is listed; kept as one file, token unexpanded")
        files.setdefault(pattern, FeedFile(pattern=pattern, lob=None, template=pattern,
                                           provenance=provenance or repr(pattern)))
    return list(files.values()), flags


def header_block_files(feed: SttmFeed, tokens: list[str],
                       blank_values: list[str] | None = None) -> tuple[list[FeedFile], list[str]]:
    """Rule 2 over the STTM header block: its ``File(s)`` and ``LOB`` meta rows
    (``SttmFeed.meta_rows`` keys ``file_names`` / ``lob``). Empty when the
    block states no pattern (pair 1 reads ``TBD`` there — its patterns come
    from the FRD, through :func:`expand_files`)."""
    patterns = split_patterns(feed.meta_rows.get("file_names"))
    lobs = split_lobs(feed.meta_rows.get("lob"), blank_values)
    sheet = feed.mapping_sheet or "mapping sheet"
    return expand_files(patterns, lobs, tokens,
                        provenance=f"STTM {sheet} header block 'File(s)'")


# ------------------------------------------------ the FRD's Region / LOB table
# 2026-10-14 (D1 pair_12, CAQH ADLS_DELTA): the FRD's LOB cell held a Region /
# LOB table and the agent wrote the whole table, comma-joined, into every row's
# LOB cell. The golden has ONE LOB code per file row, keyed by the file's plan
# identifier (several files share one LOB). The table is read as rows; each
# file is keyed to the row whose key cell (region, REG#, plan id ...) is one of
# the file name's tokens; a file no row (or several LOBs) keys stays OPEN and
# is asked for — the table is never written into a cell.

_KEY_SPLIT = re.compile(r"[^0-9A-Za-z#]+")
# A key shorter than this never matches a file token ("1" would match the
# "_1_" of every CAQH file name).
_MIN_KEY_LENGTH = 3


def _norm_header(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).casefold()


def _key(text: str) -> str:
    return re.sub(r"[\s#]+", "", str(text or "")).casefold()


def lob_column(table: list[dict[str, str]], lob_headers: list[str]) -> str | None:
    """The table's LOB column (its header as written), else None."""
    wanted = {_norm_header(h) for h in lob_headers}
    if not table:
        return None
    return next((h for h in table[0] if _norm_header(h) in wanted), None)


def lob_table_from_rows(rows: list[list[str]], lob_headers: list[str]) -> list[dict[str, str]]:
    """``rows[0]`` is the header row: exactly one LOB column (``lob_headers``)
    and at least one other column -> one {header: cell} mapping per data row
    (blank rows dropped). Anything else -> [] (not a LOB table)."""
    if len(rows) < 2:
        return []
    header = [str(c or "").strip() for c in rows[0]]
    wanted = {_norm_header(h) for h in lob_headers}
    if len(header) < 2 or sum(_norm_header(h) in wanted for h in header) != 1 \
            or any(not h for h in header):
        return []
    table: list[dict[str, str]] = []
    for row in rows[1:]:
        cells = [str(c or "").strip() for c in row][:len(header)]
        cells += [""] * (len(header) - len(cells))
        if any(cells):
            table.append(dict(zip(header, cells, strict=True)))
    return table


def lob_table_from_lines(lines: list[str], lob_headers: list[str],
                         key_headers: list[str]) -> list[dict[str, str]]:
    """A table flattened one cell per line: the leading lines that are all
    known headers (``lob_headers`` + ``key_headers``, at least two) are the
    header row, the rest are its rows in order. [] when the lines do not
    divide into whole rows."""
    words = {_norm_header(h) for h in [*lob_headers, *key_headers]}
    lines = [str(line).strip() for line in lines if str(line).strip()]
    width = 0
    while width < len(lines) and _norm_header(lines[width]) in words:
        width += 1
    if width < 2 or len(lines) == width or (len(lines) - width) % width:
        return []
    rows = [lines[i:i + width] for i in range(0, len(lines), width)]
    return lob_table_from_rows(rows, lob_headers)


def parse_lob_answer(text: str | None) -> dict[str, str]:
    """``gaps: feeds[<i>].lob_by_file`` answer text: ``<file token or
    pattern>=<LOB>`` pairs (``:`` also accepted) separated by ``;`` or new
    lines -> {normalised token: LOB}."""
    answers: dict[str, str] = {}
    for part in re.split(r"[;\n]+", text or ""):
        key, sep, lob = part.partition("=") if "=" in part else part.partition(":")
        if sep and key.strip() and lob.strip():
            answers[_key(key)] = lob.strip()
    return answers


# The LOB lookup's sources, in order (the NOTE names the one that keyed a file).
LOB_SOURCES = {
    "answers": "the answers file (gaps: lob_by_file)",
    "frd_plan": "the FRD LOB table's plan-id column",
    "frd_region": "the FRD LOB table's region column (a region token in the file name)",
    "lob_reference": "the client lob_reference table (conventions.lob_reference)",
}


def _columns(table: list[dict[str, str]], headers: list[str]) -> list[str]:
    wanted = {_norm_header(h) for h in headers}
    return [h for h in (table[0] if table else {}) if _norm_header(h) in wanted]


def _lob_by_column(table: list[dict[str, str]], lob_header: str, columns: list[str],
                   tokens: set[str]) -> tuple[str, str] | None:
    """(LOB, '<column> <cell>') when the rows whose ``columns`` cell is a
    token of the file name name exactly ONE LOB; else None."""
    hits: dict[str, str] = {}
    for row in table:
        for column in columns:
            cell = row.get(column, "")
            key = _key(cell)
            if row.get(lob_header) and len(key) >= _MIN_KEY_LENGTH and key in tokens:
                hits.setdefault(row[lob_header], f"{column} {cell!r}")
    return next(iter(hits.items())) if len(hits) == 1 else None


def key_files_by_lob_table(files: list[FeedFile], table: list[dict[str, str]],
                           lob_header: str | None, *, plan_headers: list[str],
                           region_headers: list[str], reference: dict[str, str] | None = None,
                           answers: dict[str, str] | None = None
                           ) -> tuple[list[FeedFile], list[str]]:
    """Each file without a LOB takes ONE LOB, the first source that keys it:
    an answer naming one of its tokens (or its whole pattern); the FRD LOB
    table's plan-id column (a plan id that is a token of the file name); its
    region column (a region token in the file name, matched to REG#); the
    client ``lob_reference`` (plan id -> LOB). Returns (files, unmatched
    patterns) — a file no source keys (or a source naming several LOBs) keeps
    lob None: the caller asks ONE question for all of them, and the table is
    never a cell value. ``FeedFile.lob_source`` records the source."""
    from codegen.config import is_placeholder

    answers = answers or {}
    reference = {k: v for k, v in (reference or {}).items()
                 if not is_placeholder(k) and not is_placeholder(v)}
    plan = _columns(table, plan_headers)
    region = _columns(table, region_headers)
    keyed: list[FeedFile] = []
    unmatched: list[str] = []
    for file in files:
        if file.lob:
            keyed.append(file)
            continue
        tokens = {_key(t) for t in _KEY_SPLIT.split(file.pattern) if t}
        found: tuple[str, str, str] | None = None
        answered = next((lob for key, lob in answers.items()
                         if key == _key(file.pattern) or key in tokens), None)
        if answered:
            found = (answered, "answers", "")
        for source, columns in (("frd_plan", plan), ("frd_region", region)):
            if found is None and lob_header is not None and columns:
                hit = _lob_by_column(table, lob_header, columns, tokens)
                if hit is not None:
                    found = (hit[0], source, hit[1])
        if found is None:
            refs = {lob for plan_id, lob in reference.items()
                    if len(_key(plan_id)) >= _MIN_KEY_LENGTH and _key(plan_id) in tokens}
            if len(refs) == 1:
                found = (refs.pop(), "lob_reference", "")
        if found is None:
            unmatched.append(file.pattern)
            keyed.append(file)
            continue
        lob, source, where = found
        keyed.append(file.model_copy(update={
            "lob": lob, "lob_source": source,
            "provenance": f"{file.provenance}; LOB {lob!r} from {LOB_SOURCES[source]}"
                          + (f" row {where}" if where else "")}))
    return keyed, unmatched


__all__ = ["LOB_SOURCES", "FeedFile", "expand_files", "header_block_files",
           "key_files_by_lob_table", "lob_column", "lob_table_from_lines",
           "lob_table_from_rows", "lob_token", "parse_lob_answer", "split_lobs", "split_patterns"]
