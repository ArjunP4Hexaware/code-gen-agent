"""Classify leak-gate hits at home without a term ever entering git (2026-10-15).

The ACFC harness's leak gate emits one JSON record per hit (JSONL):

    {"output_file": "...", "pattern_class": "...", "term_sha256": "<64 hex>",
     "occurrences": 3}

This tool hashes every line of a LOCAL candidates file (gitignored; one string
per line, ``#`` comments and blank lines skipped) the same way the gate does —
:func:`codegen.term_hash.term_sha256`: strip, casefold, Unicode NFC, then
sha256 of the UTF-8 bytes — and prints, per hit record, which candidate it is.

Usage:

    CODEGEN_HIT_CANDIDATES=<path> python tools/hit_lookup.py hits.jsonl
    python tools/hit_lookup.py hits.jsonl --candidates <path> [--json]

The candidates path comes from ``--candidates``, else ``CODEGEN_HIT_CANDIDATES``.
The output names the candidate a hash matched — it is for the operator's
terminal only: never commit it, never paste it into a pushed report (the
summary line at the end carries counts only). Exit 0 always when the inputs
read; 2 on a missing / unreadable input or a malformed record.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from codegen.term_hash import STABLE, term_sha256  # noqa: E402

CANDIDATES_ENV = "CODEGEN_HIT_CANDIDATES"
FIELDS = ("output_file", "pattern_class", "term_sha256", "occurrences")


class InputError(ValueError):
    """A hits / candidates input that cannot be read."""


def load_candidates(path: Path) -> dict[str, str]:
    """sha256 -> the first candidate line that hashes to it."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InputError(f"candidates file {path}: {exc}") from exc
    table: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        table.setdefault(term_sha256(line), line.strip())
    return table


def load_hits(path: Path) -> list[dict]:
    """The JSONL hit records, each checked for the four fields."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"hits file {path}: {exc}") from exc
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"hits file {path} line {number}: not JSON ({exc.msg})") from exc
        missing = [f for f in FIELDS if f not in record]
        if missing:
            raise InputError(f"hits file {path} line {number}: missing {', '.join(missing)}")
        record["term_sha256"] = str(record["term_sha256"]).strip().lower()
        hits.append(record)
    return hits


def lookup(hits: list[dict], candidates: dict[str, str]) -> list[dict]:
    """Each hit with ``candidate`` = the matching candidate, or None."""
    return [{**hit, "candidate": candidates.get(hit["term_sha256"])} for hit in hits]


def render(results: list[dict]) -> list[str]:
    lines = []
    for r in results:
        name = r["candidate"] if r["candidate"] is not None else "(no candidate matched)"
        lines.append(f"{r['term_sha256'][:12]}  {r['pattern_class']:<28} "
                     f"x{r['occurrences']:<4} {r['output_file']}  ->  {name}")
    return lines


def summary(results: list[dict]) -> str:
    """Counts only (safe to paste): matched / unmatched hits and hashes."""
    matched = [r for r in results if r["candidate"] is not None]
    by_hash = Counter(r["term_sha256"] for r in results)
    hit_hashes = {r["term_sha256"] for r in matched}
    return (f"{len(results)} hit record(s), {len(by_hash)} distinct hash(es): "
            f"{len(matched)} record(s) / {len(hit_hashes)} hash(es) matched a candidate, "
            f"{len(results) - len(matched)} record(s) unmatched")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("hits", type=Path, help="the gate's per-hit JSONL records")
    ap.add_argument("--candidates", type=Path, default=None,
                    help=f"one candidate string per line (default: ${CANDIDATES_ENV})")
    ap.add_argument("--json", action="store_true", help="JSON lines instead of a table")
    args = ap.parse_args(argv)
    path = args.candidates or (Path(os.environ[CANDIDATES_ENV])
                               if os.environ.get(CANDIDATES_ENV) else None)
    if path is None:
        print(f"no candidates file: pass --candidates or set {CANDIDATES_ENV}", file=sys.stderr)
        return 2
    try:
        results = lookup(load_hits(args.hits), load_candidates(path))
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"hash: {STABLE}")
    if args.json:
        for r in results:
            print(json.dumps(r, ensure_ascii=False))
    else:
        print("\n".join(render(results)))
    print(summary(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
