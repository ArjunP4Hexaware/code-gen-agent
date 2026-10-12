"""Fingerprint a client document without revealing it (2026-10-12).

Two copies of the "same" STTM / FRD — one in the remote workspace, one at home —
can differ in ways a run cannot see (a re-saved sheet, a blanked column, a nested
table flattened). This prints only STRUCTURE and HASHES so the two outputs can be
compared anywhere: no cell value, no paragraph text, no sheet name, no file name
or path ever appears. Files are ``file#<n>`` (argument order); sheets are
``sheet[<index>]`` plus ``name#<first 12 hex of sha256(title)>``.

Usage:
    python scripts/doc_fingerprint.py <file> [<file> ...] [--json]
    python scripts/doc_fingerprint.py --compare A.json B.json

xlsx: per sheet — state, extent, non-blank rows / cells, formula cells, merged
ranges, the header row (the fullest of the first 20 rows, >= 3 cells: its index and a
hash), non-blank counts per header column below it, and a body hash over every
cell. docx: hash of word/document.xml, paragraph / table / row / cell counts
(nested tables included) and a hash of the paragraph texts.

Exit 0; 2 when a file is unreadable or unsupported (the reason names no path).
``--compare`` exits 1 when the two fingerprints differ, else 0.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

HEADER_MIN_CELLS = 3
HEADER_SCAN_ROWS = 20
_DOCX_TOKEN = re.compile(r"<(/?)w:(tbl|tr|tc|p|t)\b[^>]*?(/?)>|([^<]+)|<[^>]*>")


def _sha(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def fingerprint_xlsx(path: Path) -> list[dict[str, Any]]:
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    values_wb = load_workbook(path, read_only=False, data_only=True)
    formula_wb = load_workbook(path, read_only=False, data_only=False)
    sheets = []
    pairs = zip(values_wb.worksheets, formula_wb.worksheets, strict=True)
    for index, (ws, fws) in enumerate(pairs):
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        # The fullest of the first HEADER_SCAN_ROWS rows (ties: the first): a
        # band-label row above the real header (STTM mapping sheets) has fewer.
        filled = [(sum(not _blank(v) for v in r), -i)
                  for i, r in enumerate(rows[:HEADER_SCAN_ROWS])]
        most, neg_index = max(filled, default=(0, 0))
        header_row = 1 - neg_index if most >= HEADER_MIN_CELLS else None
        columns: dict[str, int] = {}
        header_hash = None
        if header_row is not None:
            header = rows[header_row - 1]
            texts = ["" if _blank(v) else str(v).strip() for v in header]
            while texts and not texts[-1]:
                texts.pop()
            header_hash = _sha("\t".join(texts))
            for col, value in enumerate(header):
                if not _blank(value):
                    columns[get_column_letter(col + 1)] = sum(
                        not _blank(r[col]) for r in rows[header_row:] if col < len(r))
        body = "\n".join("\t".join("" if v is None else str(v) for v in r) for r in rows)
        sheets.append({
            "index": index,
            "name_hash": _sha(ws.title)[:12],
            "state": ws.sheet_state,
            "max_row": ws.max_row,
            "max_column": ws.max_column,
            "nonblank_rows": sum(any(not _blank(v) for v in r) for r in rows),
            "nonblank_cells": sum(not _blank(v) for r in rows for v in r),
            "formula_cells": sum(c.data_type == "f" for r in fws.iter_rows() for c in r),
            "merged_ranges": len(ws.merged_cells.ranges),
            "header_row": header_row,
            "header_hash": header_hash,
            "columns_below_header": columns,
            "body_hash": _sha(body),
        })
    return sheets


def fingerprint_docx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        xml_bytes = zf.read("word/document.xml")
    counts = dict.fromkeys(("paragraphs", "nonempty_paragraphs", "top_level_tables",
                            "tables", "rows", "cells"), 0)
    texts: list[str] = []
    paras: list[list[str]] = []
    depth = 0
    in_text = False
    for m in _DOCX_TOKEN.finditer(xml_bytes.decode("utf-8")):
        closing, tag, selfclosing, chunk = m.groups()
        if chunk is not None:
            if in_text and paras:
                paras[-1].append(html.unescape(chunk))
            continue
        if tag is None:
            continue
        if tag == "t":
            in_text = not closing and not selfclosing
        elif tag == "p":
            if not closing:
                counts["paragraphs"] += 1
                paras.append([])
            if closing or selfclosing:
                text = "".join(paras.pop()) if paras else ""
                texts.append(text)
                counts["nonempty_paragraphs"] += bool(text.strip())
        elif tag == "tbl":
            if not closing:
                counts["tables"] += 1
                counts["top_level_tables"] += depth == 0
                depth += 0 if selfclosing else 1
            else:
                depth -= 1
        elif not closing:
            counts["rows" if tag == "tr" else "cells"] += 1
    return {"document_xml_sha256": _sha(xml_bytes), **counts, "text_hash": _sha("\n".join(texts))}


def fingerprint(path: Path, n: int) -> dict[str, Any]:
    entry: dict[str, Any] = {"file": f"file#{n}"}
    suffix = path.suffix.lower()
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {**entry, "error": f"unreadable ({type(exc).__name__})"}
    entry.update(sha256=_sha(data), size=len(data))
    try:
        if suffix in (".xlsx", ".xlsm"):
            entry.update(kind="xlsx", sheets=fingerprint_xlsx(path))
        elif suffix == ".docx":
            entry.update(kind="docx", docx=fingerprint_docx(path))
        else:
            entry["error"] = f"unsupported extension {suffix or '(none)'}"
    except Exception as exc:  # noqa: BLE001 — any parse failure is reported, never its text
        entry["error"] = f"unreadable ({type(exc).__name__})"
    return entry


def render(entry: dict[str, Any]) -> list[str]:
    head = f"{entry['file']}"
    if "sha256" in entry:
        head += f" sha256={entry['sha256']} size={entry['size']}"
    if "error" in entry:
        return [f"{head} ERROR {entry['error']}"]
    lines = [f"{head} kind={entry['kind']}"]
    for s in entry.get("sheets", []):
        lines.append(
            f"  sheet[{s['index']}] name#{s['name_hash']} {s['state']} max_row={s['max_row']} "
            f"max_column={s['max_column']} nonblank_rows={s['nonblank_rows']} "
            f"nonblank_cells={s['nonblank_cells']} formulas={s['formula_cells']} "
            f"merged={s['merged_ranges']} header_row={s['header_row']} "
            f"header#{(s['header_hash'] or '-')[:16]} body#{s['body_hash'][:16]}")
        if s["columns_below_header"]:
            lines.append("    columns: " + " ".join(
                f"{k}={v}" for k, v in s["columns_below_header"].items()))
    if "docx" in entry:
        lines.append("  " + " ".join(f"{k}={str(v)[:16] if k.endswith(('sha256', 'hash')) else v}"
                                     for k, v in entry["docx"].items()))
    return lines


def _diff_fields(a: dict[str, Any], b: dict[str, Any], skip: tuple[str, ...] = ()) -> list[str]:
    out = []
    for key in sorted(set(a) | set(b)):
        if key in skip or a.get(key) == b.get(key):
            continue
        va, vb = a.get(key), b.get(key)
        opaque = "hash" in key or "sha256" in key or isinstance(va, (dict, list))
        out.append(f"{key} differs" if opaque else f"{key} {va} vs {vb}")
    return out


def compare(a_entries: list[dict[str, Any]], b_entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if len(a_entries) != len(b_entries):
        lines.append(f"file count {len(a_entries)} vs {len(b_entries)}")
    for a, b in zip(a_entries, b_entries, strict=False):
        label = f"{a['file']} vs {b['file']}"
        top = _diff_fields(a, b, skip=("file", "sheets", "docx"))
        top += [f"docx.{d}" for d in _diff_fields(a.get("docx", {}), b.get("docx", {}))]
        if top:
            lines.append(f"{label}: " + "; ".join(top))
        sa, sb = a.get("sheets", []), b.get("sheets", [])
        for i in range(max(len(sa), len(sb))):
            if i >= len(sa) or i >= len(sb):
                only = sa[i] if i < len(sa) else sb[i]
                side = "A" if i < len(sa) else "B"
                lines.append(f"{label} sheet[{i}] name#{only['name_hash']}: only in {side}")
                continue
            diffs = _diff_fields(sa[i], sb[i], skip=("columns_below_header",))
            ca, cb = sa[i]["columns_below_header"], sb[i]["columns_below_header"]
            diffs += [f"column {c} {ca.get(c, '-')} vs {cb.get(c, '-')}"
                      for c in sorted(set(ca) | set(cb)) if ca.get(c) != cb.get(c)]
            if diffs:
                lines.append(f"{label} sheet[{i}] name#{sa[i]['name_hash']}: " + "; ".join(diffs))
    return lines


def _load(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help=".xlsx / .docx documents")
    parser.add_argument("--json", action="store_true", help="one JSON object per file")
    parser.add_argument("--compare", nargs=2, metavar=("A_JSON", "B_JSON"),
                        help="diff two saved --json outputs (counts and hash flags only)")
    args = parser.parse_args(argv)
    if args.compare:
        lines = compare(_load(args.compare[0]), _load(args.compare[1]))
        print("\n".join(lines) if lines else "identical")
        return 1 if lines else 0
    if not args.files:
        parser.error("give at least one file, or --compare A.json B.json")
    entries = [fingerprint(Path(f), n) for n, f in enumerate(args.files, start=1)]
    if args.json:
        print(json.dumps(entries[0] if len(entries) == 1 else entries, indent=2))
    else:
        print("\n".join(line for e in entries for line in render(e)))
    return 2 if any("error" in e for e in entries) else 0


if __name__ == "__main__":
    sys.exit(main())
