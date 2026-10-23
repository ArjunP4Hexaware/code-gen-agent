"""The STRUCTURE of DDL files, and the agent's DDL scored against a reference set.

    python tools/ddl_shape.py --reference <file | dir> [...] --agent <file | dir> [...]
        [--json out.json]
    python tools/ddl_shape.py --profile <file | dir> [...]

2026-10-23 (the DDL format question, docs/RESTART.md): ACFC's prod DDLs were
compared with the agent's by hand-written scans; this is that scan as a tool.
Every CREATE TABLE block is reduced to its shape — the create form, the share of
columns with a COMMENT, a table COMMENT, CLUSTER BY AUTO / LOCATION / PARTITIONED
BY, the TBLPROPERTIES names in order, the SET TAGS keys, PRIMARY KEY / NOT NULL,
the statement terminator, the quote escape, and (stage) whether every business
column is STRING. Each block's layer comes from its banner (``--stage table`` /
``--standard table``), else the file name (dlk / stg / stage vs std / standard).

The report compares, per layer and feature, the reference set's distribution
with the agent's: MATCH when the agent's value is the reference majority. It
prints counts and Delta property names only — never a table, column, comment
or tag value — so it is safe to share; ``--json`` writes the same.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_SUFFIXES = (".txt", ".sql")
_CREATE = re.compile(r"\bCREATE\s+(OR\s+REPLACE\s+)?(?:EXTERNAL\s+)?TABLE\s+"
                     r"(IF\s+NOT\s+EXISTS\s+)?", re.IGNORECASE)
_BANNERS = {"--stage table": "stage", "--standard table": "standard"}
_AUDIT_TYPES = {"timestamp", "timestamp_ntz", "date", "tinyint", "smallint", "int", "bigint",
                "boolean"}
FEATURES = ("create", "column_comment_share", "table_comment", "cluster_by_auto", "location",
            "partitioned_by", "tblproperties", "set_tags", "primary_key", "not_null",
            "terminated", "quote_escape", "stage_all_string")


def _mask(text: str) -> tuple[str, list[tuple[int, str]]]:
    """The text with every string literal's body and every ``--`` comment
    blanked (same length), so structure can be matched without the content
    confusing it; and each literal's (offset, escape used: backslash /
    doubled / none). Escapes recognised: a backslash, and a doubled quote."""
    out = list(text)
    literals: list[tuple[int, str]] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "-" and text.startswith("--", i):
            end = text.find("\n", i)
            end = n if end == -1 else end
            if text[i:end].strip().lower() not in _BANNERS:
                for k in range(i, end):
                    out[k] = " "
            i = end
        elif ch == "'":
            j, escape = i + 1, "none"
            while j < n:
                if text[j] == "\\":
                    escape = "backslash"
                    j += 2
                    continue
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        escape = "doubled" if escape == "none" else escape
                        j += 2
                        continue
                    break
                j += 1
            literals.append((i, escape))
            for k in range(i + 1, min(j, n)):
                out[k] = "x" if out[k] != "\n" else "\n"
            i = j + 1
        else:
            i += 1
    return "".join(out), literals


def _close_paren(masked: str, start: int) -> int:
    depth = 0
    for k in range(start, len(masked)):
        if masked[k] == "(":
            depth += 1
        elif masked[k] == ")":
            depth -= 1
            if depth == 0:
                return k
    return len(masked) - 1


def _split_columns(body: str) -> list[str]:
    parts, depth, current = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _layer_from_name(name: str) -> str:
    low = name.lower()
    if re.search(r"(^|[^a-z])(std|standard)([^a-z]|$)", low):
        return "standard"
    if re.search(r"(^|[^a-z])(dlk|stg|stage)([^a-z]|$)", low):
        return "stage"
    return "unknown"


def profile_text(text: str, name: str = "") -> list[dict]:
    """One shape per CREATE TABLE block of ``text``."""
    masked, literals = _mask(text)
    starts = [m for m in _CREATE.finditer(masked)]
    blocks = []
    for index, match in enumerate(starts):
        open_paren = masked.find("(", match.end())
        if open_paren == -1:
            continue
        close = _close_paren(masked, open_paren)
        tail_end = starts[index + 1].start() if index + 1 < len(starts) else len(masked)
        head = masked[:match.start()]
        banner = None
        for line in reversed(head.splitlines()):
            if line.strip().lower() in _BANNERS:
                banner = _BANNERS[line.strip().lower()]
                break
            if line.strip():
                break
        layer = banner or _layer_from_name(name)
        columns = [c for c in _split_columns(masked[open_paren + 1:close])
                   if not re.match(r"(CONSTRAINT|PRIMARY\s+KEY|FOREIGN\s+KEY)\b", c, re.I)]
        raw_tail = text[close + 1:tail_end]
        tail = masked[close + 1:tail_end]
        statement_end = tail.find(";")
        own_tail = tail if statement_end == -1 else tail[:statement_end]
        types = []
        for column in columns:
            parts = column.split()
            if len(parts) >= 2:
                types.append(re.split(r"[(<]", parts[1])[0].lower())
        business = [t for t in types if t not in _AUDIT_TYPES]
        tblprops_match = re.search(r"TBLPROPERTIES\s*\((.*?)\)", raw_tail[:len(own_tail) + 1],
                                   re.S | re.I)
        prop_names = tuple(re.findall(r"'([^']+)'\s*=", tblprops_match.group(1))
                           ) if tblprops_match else ()
        escapes = {e for at, e in literals if match.start() <= at < tail_end}
        quotes = ("backslash" if "backslash" in escapes else
                  "doubled" if "doubled" in escapes else "none")
        blocks.append({
            "file": name, "layer": layer,
            "create": ("CREATE OR REPLACE" if match.group(1) else
                       "CREATE IF NOT EXISTS" if match.group(2) else "CREATE"),
            "columns": len(columns),
            "column_comment_share": round(
                sum(bool(re.search(r"\bCOMMENT\s+'", c, re.I)) for c in columns)
                / len(columns), 2) if columns else 0.0,
            "table_comment": bool(re.search(r"(^|\s)COMMENT\s+'", own_tail, re.I)),
            "cluster_by_auto": bool(re.search(r"CLUSTER\s+BY\s+AUTO", own_tail, re.I)),
            "location": bool(re.search(r"\bLOCATION\s+'", own_tail, re.I)),
            "partitioned_by": bool(re.search(r"PARTITIONED\s+BY", own_tail, re.I)),
            "tblproperties": list(prop_names),
            "set_tags": sorted(set(re.findall(
                r"'([A-Za-z_]+)'\s*=", " ".join(re.findall(r"SET\s+TAGS\s*\(([^)]*)\)",
                                                          text[close:tail_end], re.I))))),
            "primary_key": bool(re.search(r"PRIMARY\s+KEY", masked[match.start():tail_end],
                                          re.I)),
            "not_null": bool(re.search(r"NOT\s+NULL", masked[open_paren:close], re.I)),
            "terminated": statement_end != -1,
            "quote_escape": quotes,
            "stage_all_string": (all(t == "string" for t in business) if layer == "stage"
                                 and business else None),
        })
    return blocks


def _files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            out.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in _SUFFIXES))
        elif path.is_file():
            out.append(path)
        else:
            raise SystemExit(f"ddl_shape: no such file or directory: {raw}")
    return out


def profile_paths(paths: list[str]) -> list[dict]:
    blocks = []
    for path in _files(paths):
        blocks.extend(profile_text(path.read_text(encoding="utf-8", errors="replace"),
                                   path.name))
    return blocks


def _value(block: dict, feature: str):
    value = block[feature]
    if feature == "column_comment_share":
        return "all" if value == 1 else "none" if value == 0 else "some"
    if isinstance(value, list):
        return tuple(value)
    return value


def compare(reference: list[dict], agent: list[dict]) -> dict:
    """Per layer and feature: the reference distribution, the agent's values
    and MATCH / DIFF against the reference majority."""
    report: dict = {}
    for layer in sorted({b["layer"] for b in reference + agent}):
        ref = [b for b in reference if b["layer"] == layer]
        got = [b for b in agent if b["layer"] == layer]
        rows = []
        for feature in FEATURES:
            ref_counts = Counter(_value(b, feature) for b in ref)
            got_counts = Counter(_value(b, feature) for b in got)
            if feature == "quote_escape":
                # a block with no escaped quote says nothing about the escape used
                ref_counts.pop("none", None)
                got_counts.pop("none", None)
            if feature == "stage_all_string" and layer != "stage":
                continue
            majority = ref_counts.most_common(1)[0][0] if ref_counts else None
            verdict = ("n/a" if not ref_counts or not got_counts else
                       "MATCH" if set(got_counts) == {majority} else "DIFF")
            rows.append({"feature": feature,
                         "reference": [[_show(v), n] for v, n in ref_counts.most_common()],
                         "agent": [[_show(v), n] for v, n in got_counts.most_common()],
                         "verdict": verdict})
        scored = [r for r in rows if r["verdict"] in ("MATCH", "DIFF")]
        report[layer] = {"reference_blocks": len(ref), "agent_blocks": len(got),
                         "matched": sum(r["verdict"] == "MATCH" for r in scored),
                         "scored": len(scored), "features": rows}
    return report


def _show(value) -> str:
    if isinstance(value, tuple):
        if not value:
            return "none"
        return f"{len(value)}: " + ", ".join(value)
    return str(value)


def render(report: dict) -> str:
    lines = []
    for layer, part in report.items():
        lines.append(f"## {layer}: {part['matched']}/{part['scored']} features match "
                     f"(reference {part['reference_blocks']} blocks, agent "
                     f"{part['agent_blocks']})")
        lines.append("")
        lines.append("| Feature | Reference | Agent | |")
        lines.append("|---|---|---|---|")
        for row in part["features"]:
            ref = "; ".join(f"{v} ×{n}" for v, n in row["reference"]) or "-"
            got = "; ".join(f"{v} ×{n}" for v, n in row["agent"]) or "-"
            lines.append(f"| {row['feature']} | {ref} | {got} | {row['verdict']} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--reference", nargs="+", default=[])
    parser.add_argument("--agent", nargs="+", default=[])
    parser.add_argument("--profile", nargs="+", default=[],
                        help="print each block's shape instead of comparing")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    if args.profile:
        shapes = profile_paths(args.profile)
        for shape in shapes:
            shape = {k: v for k, v in shape.items() if k != "file"}
            print(json.dumps(shape))
        return 0
    if not args.reference or not args.agent:
        parser.error("--reference and --agent are both required (or use --profile)")
    report = compare(profile_paths(args.reference), profile_paths(args.agent))
    print(render(report))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
