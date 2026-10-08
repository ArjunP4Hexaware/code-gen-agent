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


__all__ = ["FeedFile", "expand_files", "header_block_files", "lob_token", "split_lobs",
           "split_patterns"]
