"""Score a generated IIG sheet row against a real one (stdlib + openpyxl).

    python scripts/iig_scorecard.py --generated out/<feed>/framework/<feed>_IIG.xlsx \
        --real "<real IIG rows>.xlsx" --sheet ADLS_DELTA_INGESTION_DETAILS \
        --real-table <TGT_TABLE_NAME> [--generated-table <TGT_TABLE_NAME>] \
        [--review <feed>_IIG_REVIEW.xlsx] [--alias generated=real ...]

Rows are matched by TGT_TABLE_NAME. One line per column of the REAL sheet:

* MATCH — same value (a blank generated cell matches a real NULL / blank);
* ALIAS — equal only once the fixture's anonymisation is undone (--alias
  pairs, applied to the generated value, case-insensitive); a case-only
  difference is a DIFF marked "(case only)";
* OPEN  — the generated cell is blank; owner from the review copy's
  REVIEW_SUMMARY (sheet + column);
* DIFF  — real vs generated, values cut to 60 characters; comma-list
  columns are compared by length + first 3 items.

CREATED_BY / UPDATED_BY values are never printed. The last line:
"filled N/<cols>, matched M, alias A, open K (BSA x, Engineer y,
Engineer-confirm z, CI/CD w), diff D".
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

WITHHELD = {"CREATED_BY", "UPDATED_BY", "CRETAED_BY"}
LIST_COLUMNS = {"SRC_COLUMNS", "SRC_DATA_TYPE", "TGT_COLUMN_NAMES", "TGT_DATA_TYPE",
                "MANDATORY_FIELD_LIST", "TGT_PRIMARY_KEY", "SRC_COL_LNGTH",
                "SRC_COL_STRT_END_INDX"}
NULLS = {"", "null", "none"}
# The CV golden fixture's anonymisation of the Socially Determined feeds.
DEFAULT_ALIASES = ["cv_=sd_", "sdh=sdoh", "civic_vantage=socially_determined",
                   "civic vantage=socially determined"]
OWNER_BUCKETS = {"BSA": "BSA", "Engineer": "Engineer", "Engineer (confirm)": "Engineer-confirm",
                 "Set at load (CI/CD)": "CI/CD"}
WIDTH = 60


def _text(value) -> str:
    return "" if value is None else str(value).strip()


def _is_null(value) -> bool:
    return _text(value).lower() in NULLS


def _cut(value: str) -> str:
    return value if len(value) <= WIDTH else value[:WIDTH - 3] + "..."


def _rows(path: Path, sheet: str | None) -> list[dict]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    ws = workbook[sheet] if sheet and sheet in workbook.sheetnames else workbook.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    headers = [_text(h) for h in rows[0]]
    return [{h: v for h, v in zip(headers, r, strict=False) if h} for r in rows[1:]]


def _owners(review: Path | None, sheet: str) -> dict[str, str]:
    if review is None or not review.is_file():
        return {}
    owners: dict[str, str] = {}
    for row in _rows(review, "REVIEW_SUMMARY"):
        if _text(row.get("Sheet")) == sheet:
            owners.setdefault(_text(row.get("Column")), _text(row.get("Owner")))
    return owners


def _dealias(value: str, aliases: list[tuple[str, str]]) -> str:
    out = value
    for generated, real in aliases:
        out = re.sub(re.escape(generated), real, out, flags=re.IGNORECASE)
    return out.lower()


def _items(value: str) -> list[str]:
    return [i.strip() for i in value.split(",") if i.strip()]


def _diff_text(column: str, real: str, generated: str) -> str:
    if column in LIST_COLUMNS:
        r, g = _items(real), _items(generated)
        text = (f"real {len(r)} items {[_cut(i) for i in r[:3]]} | "
                f"generated {len(g)} items {[_cut(i) for i in g[:3]]}")
        first = next((i for i, (a, b) in enumerate(zip(r, g, strict=False)) if a != b), None)
        if first is not None and first >= 3:
            text += (f"; first difference at item {first + 1}: {_cut(r[first])!r} vs "
                     f"{_cut(g[first])!r}")
        return text
    return f"real {_cut(real)!r} | generated {_cut(generated)!r}"


def _find(rows: list[dict], table: str, aliases) -> dict | None:
    for row in rows:
        if _text(row.get("TGT_TABLE_NAME")).lower() == table.lower():
            return row
    for row in rows:
        if _dealias(_text(row.get("TGT_TABLE_NAME")), aliases) == table.lower():
            return row
    return None


def score(generated: dict, real: dict, owners: dict[str, str],
          aliases: list[tuple[str, str]]) -> tuple[list[str], dict]:
    lines: list[str] = []
    counts = {"filled": 0, "match": 0, "alias": 0, "open": 0, "diff": 0}
    open_by: dict[str, int] = {}
    columns = list(real)
    for column in columns:
        real_value, gen_value = _text(real.get(column)), _text(generated.get(column))
        withheld = column in WITHHELD
        if gen_value:
            counts["filled"] += 1
        if not gen_value:
            if _is_null(real_value):
                status, detail = "MATCH", "(both blank / NULL)"
                counts["match"] += 1
            else:
                owner = owners.get(column) or ("not in the template" if column not in generated
                                               else "no review entry")
                bucket = OWNER_BUCKETS.get(owner, owner)
                open_by[bucket] = open_by.get(bucket, 0) + 1
                status, detail = "OPEN", f"owner: {owner}"
                counts["open"] += 1
        elif gen_value == real_value or (_is_null(gen_value) and _is_null(real_value)):
            status, detail = "MATCH", ""
            counts["match"] += 1
        elif (_dealias(gen_value, aliases) == real_value.lower()
              and _dealias(gen_value, aliases) != gen_value.lower()):
            # equal only once the fixture's anonymisation is undone
            status, detail = "ALIAS", ("" if withheld else f"generated {_cut(gen_value)!r}")
            counts["alias"] += 1
        else:
            status = "DIFF"
            detail = "(values withheld)" if withheld else _diff_text(column, real_value,
                                                                     gen_value)
            if not withheld and _dealias(gen_value, aliases) == real_value.lower():
                detail = "(case only) " + detail
            counts["diff"] += 1
        lines.append(f"{status:<5} {column:<26} {detail}".rstrip())
    known = ["BSA", "Engineer", "Engineer-confirm", "CI/CD"]
    parts = [f"{name} {open_by.get(name, 0)}" for name in known]
    parts += [f"{name} {n}" for name, n in open_by.items() if name not in known]
    summary = (f"filled {counts['filled']}/{len(columns)}, matched {counts['match']}, "
               f"alias {counts['alias']}, open {counts['open']} ({', '.join(parts)}), "
               f"diff {counts['diff']}")
    return lines + [summary], counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--real", required=True, type=Path)
    parser.add_argument("--sheet", default="ADLS_DELTA_INGESTION_DETAILS")
    parser.add_argument("--real-sheet", default=None,
                        help="sheet of the real workbook (default: --sheet, else the first)")
    parser.add_argument("--real-table", required=True)
    parser.add_argument("--generated-table", default=None)
    parser.add_argument("--review", type=Path, default=None,
                        help="review copy (default: <generated>_REVIEW.xlsx next to it)")
    parser.add_argument("--alias", action="append", default=None,
                        help="generated=real anonymisation pair (repeatable)")
    args = parser.parse_args(argv)

    aliases = [tuple(a.split("=", 1)) for a in (args.alias or DEFAULT_ALIASES)]
    review = args.review or args.generated.with_name(
        args.generated.name.replace("_IIG.xlsx", "_IIG_REVIEW.xlsx"))
    real = _find(_rows(args.real, args.real_sheet or args.sheet), args.real_table, [])
    if real is None:
        print(f"real row {args.real_table!r} not found", file=sys.stderr)
        return 2
    generated = _find(_rows(args.generated, args.sheet),
                      args.generated_table or args.real_table, aliases)
    if generated is None:
        print(f"generated row {args.generated_table or args.real_table!r} not found",
              file=sys.stderr)
        return 2
    lines, _counts = score(generated, real, _owners(review, args.sheet), aliases)
    print(f"{args.sheet}: real {args.real_table} vs generated "
          f"{_text(generated.get('TGT_TABLE_NAME'))}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
