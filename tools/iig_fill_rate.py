"""Per-column fill rate of an IIG corpus against the agent's IIG workbooks.

    python tools/iig_fill_rate.py --corpus <xlsx | dir> [...] --agent <xlsx | dir> [...]
        [--sheets DATABRICKS_NOTEBOOK_DETAILS,DATA_FACTORY_PIPELINE_SCHEDULE,EMAIL_TEMPLATE_CONFIG]
        [--threshold 90] [--json out.json] [--show-values]

2026-10-13: for every column of the chosen sheets, how many corpus rows fill it
(a cell that is not blank and not ``NULL``) against how many agent rows do.
A column the corpus fills in at least ``--threshold`` % of rows and the agent
does not is a GAP; a column the iig_keys.yaml ``needs_assignment`` set names
(ids, audit stamps) is ``assigned`` — the framework / the engineer fills it,
the agent never invents it. The share of the corpus's most common value is
printed (the value itself only with ``--show-values``: corpus values are
production text — D1 only, never committed).

Run on D1 over the 199-IIG corpus (docs/acfc/iig_goldens/*.xlsx); at home
over the SFMC reference IIG, the pair-1 golden and any golden at hand.
Sheets match by name (case, the framework table name cut to Excel's 31
characters); columns by header (case, separators).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

TOOLS = Path(__file__).resolve().parent
DEFAULT_SHEETS = ("DATABRICKS_NOTEBOOK_DETAILS", "DATA_FACTORY_PIPELINE_SCHEDULE",
                  "EMAIL_TEMPLATE_CONFIG")
NULLS = {"", "null", "none"}
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _diff_module():
    spec = importlib.util.spec_from_file_location("iig_diff", TOOLS / "iig_diff.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("iig_diff", module)
    spec.loader.exec_module(module)
    return module


def sheet_id(name: str) -> str:
    return name.strip().upper()[:31]


def header_id(name: object) -> str:
    return _NON_ALNUM.sub("", str(name or "").lower())


def filled(value: object) -> bool:
    return str(value if value is not None else "").strip().lower() not in NULLS


def workbooks(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_dir():
            # a run folder: its IIGs only (never config_rows / config_inserts)
            books = sorted(p for p in path.rglob("*.xlsx") if not p.name.startswith("~$")
                           and not p.name.endswith("_REVIEW.xlsx"))
            iigs = [p for p in books if p.name.upper().endswith("_IIG.XLSX")]
            out += iigs or books
        elif path.is_file():
            out.append(path)
    return out


def sheet_rows(paths: list[Path], wanted: set[str]) -> dict[str, tuple[dict, list[dict]]]:
    """sheet -> ({header id: header as first written}, [{header id: value}])
    over every workbook; a row whose cells are all blank is no row."""
    out: dict[str, tuple[dict, list[dict]]] = {}
    for path in paths:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            for name in book.sheetnames:
                sid = sheet_id(name)
                if sid not in wanted:
                    continue
                rows = book[name].iter_rows(values_only=True)
                head = next(rows, None) or ()
                ids = [header_id(h) for h in head]
                headers, records = out.setdefault(sid, ({}, []))
                for h, i in zip(head, ids, strict=False):
                    if i:
                        headers.setdefault(i, str(h).strip())
                for row in rows:
                    if any(filled(v) for v in row):
                        records.append({i: v for i, v in zip(ids, row, strict=False) if i})
        finally:
            book.close()
    return out


def always_blank(root: Path = TOOLS.parent, template: str = "iig_v2") -> set[str]:
    """The template's framework-assigned columns (config.yaml, the ACFC overlay
    on top: a list replaces) — assigned like the needs_assignment set."""
    import yaml

    found: list[str] = []
    for path in (root / "config" / "config.yaml", root / "config" / "overlays" / "acfc_env.yaml"):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            continue
        listed = (((raw.get("metadata") or {}).get("templates") or {}).get(template)
                  or {}).get("always_blank")
        if listed is not None:
            found = list(listed)
    return {header_id(h) for h in found}


def fill_rates(corpus: dict, agent: dict, sheets: list[str], threshold: float,
               assigned) -> dict:
    """Per sheet, per column: corpus / agent rows and filled counts, the
    dominant corpus value's share, and the status (gap / ok / assigned /
    sparse)."""
    report: dict = {}
    for sid in sheets:
        c_heads, c_rows = corpus.get(sid, ({}, []))
        a_heads, a_rows = agent.get(sid, ({}, []))
        columns = {**{k: v for k, v in a_heads.items()}, **c_heads}
        sheet: dict = {"corpus_rows": len(c_rows), "agent_rows": len(a_rows), "columns": {}}
        for cid, header in columns.items():
            c_filled = [r.get(cid) for r in c_rows if filled(r.get(cid))]
            a_filled = sum(1 for r in a_rows if filled(r.get(cid)))
            c_pct = round(100.0 * len(c_filled) / len(c_rows), 1) if c_rows else None
            a_pct = round(100.0 * a_filled / len(a_rows), 1) if a_rows else None
            common = Counter(str(v).strip() for v in c_filled).most_common(1)
            status = ("assigned" if assigned(header) else
                      "no corpus rows" if c_pct is None else
                      "sparse" if c_pct < threshold else
                      "gap" if (a_pct or 0.0) < threshold else "ok")
            sheet["columns"][header] = {
                "corpus_filled": len(c_filled), "corpus_pct": c_pct,
                "agent_filled": a_filled, "agent_pct": a_pct,
                "dominant_share": (round(100.0 * common[0][1] / len(c_filled), 1)
                                   if common else None),
                "dominant_value": common[0][0] if common else None,
                "in_corpus": cid in c_heads, "in_agent": cid in a_heads, "status": status,
            }
        report[sid] = sheet
    return report


def print_report(report: dict, show_values: bool) -> None:
    for sid, sheet in report.items():
        print(f"{sid}: corpus {sheet['corpus_rows']} row(s), agent {sheet['agent_rows']} "
              "row(s)")
        print(f"  {'column':<34} {'corpus %':>9} {'agent %':>8} {'dominant %':>10}  status")
        for header, col in sheet["columns"].items():
            def pct(v):
                return "-" if v is None else f"{v:.1f}"
            line = (f"  {header:<34} {pct(col['corpus_pct']):>9} {pct(col['agent_pct']):>8} "
                    f"{pct(col['dominant_share']):>10}  {col['status']}")
            if show_values and col["dominant_value"] is not None:
                line += f"  (D1 only: {col['dominant_value'][:60]!r})"
            print(line)
        gaps = [h for h, c in sheet["columns"].items() if c["status"] == "gap"]
        print(f"  GAPS ({len(gaps)}): {', '.join(gaps) or 'none'}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", nargs="+", type=Path, required=True)
    ap.add_argument("--agent", nargs="+", type=Path, required=True)
    ap.add_argument("--sheets", default=",".join(DEFAULT_SHEETS))
    ap.add_argument("--threshold", type=float, default=90.0)
    ap.add_argument("--keys", type=Path, default=TOOLS / "iig_keys.yaml")
    ap.add_argument("--json", type=Path, help="write the report here (values withheld "
                                              "unless --show-values)")
    ap.add_argument("--show-values", action="store_true",
                    help="print / write the dominant corpus value (D1 only: production text)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    keys = _diff_module().load_keys(args.keys)
    blank = always_blank()

    def assigned(header: str) -> bool:
        return keys.is_assignment(header) or header_id(header) in blank
    sheets = [sheet_id(s) for s in args.sheets.split(",") if s.strip()]
    corpus_books, agent_books = workbooks(args.corpus), workbooks(args.agent)
    if not corpus_books or not agent_books:
        print(f"FAIL no workbook: corpus {len(corpus_books)}, agent {len(agent_books)}")
        return 1
    print(f"corpus: {len(corpus_books)} workbook(s); agent: {len(agent_books)} workbook(s); "
          f"threshold {args.threshold:.0f}%")
    report = fill_rates(sheet_rows(corpus_books, set(sheets)),
                        sheet_rows(agent_books, set(sheets)), sheets, args.threshold,
                        assigned)
    print_report(report, args.show_values)
    if args.json:
        if not args.show_values:
            for sheet in report.values():
                for col in sheet["columns"].values():
                    col["dominant_value"] = None
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
