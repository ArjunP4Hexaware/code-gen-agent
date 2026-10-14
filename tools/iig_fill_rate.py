"""Per-column fill rate of an IIG corpus against the agent's IIG workbooks.

    python tools/iig_fill_rate.py --corpus <xlsx | csv | dir> [...] --agent <xlsx | dir> [...]
        [--sheets DATABRICKS_NOTEBOOK_DETAILS,DATA_FACTORY_PIPELINE_SCHEDULE,EMAIL_TEMPLATE_CONFIG]
        [--threshold 90] [--json out.json] [--show-values] [--patterns DIR]

2026-10-13: for every column of the chosen sheets, how many corpus rows fill it
(a cell that is not blank and not ``NULL``) against how many agent rows do.
A column the corpus fills in at least ``--threshold`` % of rows and the agent
does not is a GAP; a column the iig_keys.yaml ``needs_assignment`` set names
(ids, audit stamps) is ``assigned`` — the framework / the engineer fills it,
the agent never invents it. The share of the corpus's most common value is
printed (the value itself only with ``--show-values``: corpus values are
production text — D1 only, never committed).

2026-10-14 (D1 post43 item 3): ``--patterns DIR`` writes ``patterns.md`` +
``patterns.json`` — per column of the chosen sheets the dominant value and its
share, and a SLOT pattern (each row's own feed / table / schema / domain /
subdomain / file / source values replaced by ``{feed}``, ``{table}``, …, taken
from its workbook's ingestion sheets) with its share; DAY_OF_SCHEDULE's fill
rate per PIPELINE_FREQUENCY; the grand master / master schedule rows per
GROUP_ID. SCRUBBED: every remaining token outside the fixture vocabulary is a
``G<n>`` placeholder (tools/iig_diff.py's export scrubber) and the written
files are re-scanned with scripts/scrub_check.py (a hit deletes them) — safe
to bring home. Sheets match by name with case and separators ignored (a name
cut to Excel's 31 characters matches its full name); a header row is the
first of the top rows with two or more cells; a ``.csv`` corpus file is one
table, named by its file stem (a suffix allowed: the EMAIL_TEMPLATE_CONFIG
export tools/build_goldens.py reads, email_template_config_by_pipeline.csv —
the 199 per-pair workbooks carry no email sheet). Every corpus workbook's
sheets are listed.

Run on D1 over the 199-IIG corpus (docs/acfc/iig_goldens/*.xlsx); at home
over the SFMC reference IIG, the pair-1 golden and any golden at hand.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

TOOLS = Path(__file__).resolve().parent
DEFAULT_SHEETS = ("DATABRICKS_NOTEBOOK_DETAILS", "DATA_FACTORY_PIPELINE_SCHEDULE",
                  "EMAIL_TEMPLATE_CONFIG")
SCHEDULE = "DATA_FACTORY_PIPELINE_SCHEDULE"
# 2026-10-14 (D1 post43 item 6): the corpus's DQ rule classes (--patterns)
RULES = "DATA_QUALITY_RULES"
RULE_COLUMNS = ("ruletype", "ruleclass")
# The ingestion sheets whose cells name a workbook's feed / tables / files —
# the slot values of --patterns (ALL_FILES_STATIC_INFORMATION is the whole
# inventory, never one feed's).
SLOT_SHEETS = ("ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DETAILS",
               "FILE_ADLS_INGESTION_DETAILS", "ADLS_FIXED_WIDTH_HANDLER")
SLOT_COLUMNS = {      # slot -> header ids (case / separators dropped)
    "table": ("tgttablename", "srctablename", "tgttable"),
    "schema": ("tgtschemaname", "srcschemaname"),
    "catalog": ("tgtcatalogname", "srccatalogname", "tgtdatabasename", "srcdatabasename"),
    "domain": ("domain",),
    "subdomain": ("subdomain",),
    "feed": ("objectname",),
    "file": ("srcfilename", "filename"),
    "source": ("source",),
}
NULLS = {"", "null", "none"}
HEADER_SCAN_ROWS = 10
MIN_SLOT_CHARS = 3
TOP_PATTERNS = 3
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SHEET_KEY = re.compile(r"[^A-Z0-9]+")
_EXCEL_SHEET_CHARS = 31
_GRAND_MASTER = re.compile(r"grand\s*[-_ ]?\s*master", re.IGNORECASE)
_MASTER = re.compile(r"(?<![a-z])master(?![a-z])", re.IGNORECASE)


def _diff_module():
    if "iig_diff" in sys.modules:
        return sys.modules["iig_diff"]
    spec = importlib.util.spec_from_file_location("iig_diff", TOOLS / "iig_diff.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["iig_diff"] = module
    spec.loader.exec_module(module)
    return module


def sheet_id(name: str) -> str:
    return name.strip().upper()[:_EXCEL_SHEET_CHARS]


def sheet_key(name: str) -> str:
    """A sheet name as compared: upper case, separators dropped."""
    return _SHEET_KEY.sub("", str(name).upper())


def match_sheet(name: str, wanted) -> str | None:
    """The wanted sheet ``name`` is (case / separators ignored; a name cut to
    Excel's 31 characters matches its full form), else None."""
    key, cut = sheet_key(name), sheet_key(sheet_id(name))
    for target in wanted:
        if key in (sheet_key(target), sheet_key(sheet_id(target))) or cut == sheet_key(target):
            return target
    return None


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
            out += sorted(path.rglob("*.csv")) if not iigs else []
        elif path.is_file():
            out.append(path)
    return out


@dataclass
class Book:
    """One corpus / agent workbook: every sheet's name, and the read ones."""

    name: str
    sheetnames: list[str]
    # canonical sheet -> ({header id: header}, [{header id: value}])
    sheets: dict[str, tuple[dict, list[dict]]] = field(default_factory=dict)


def _table(rows) -> tuple[list, list]:
    """(header row, data rows): the header is the first of the top rows with
    two or more cells (a title / blank row above it is skipped)."""
    rows = iter(rows)
    head: tuple = ()
    for _ in range(HEADER_SCAN_ROWS):
        row = next(rows, None)
        if row is None:
            return [], []
        if sum(1 for v in row if filled(v)) >= 2:
            head = row
            break
    return list(head), list(rows)


def _records(head: list, rows: list) -> tuple[dict, list[dict]]:
    ids = [header_id(h) for h in head]
    headers = {i: str(h).strip() for h, i in zip(head, ids, strict=False) if i}
    records = [{i: v for i, v in zip(ids, row, strict=False) if i} for row in rows
               if any(filled(v) for v in row)]
    return headers, records


def read_books(paths: list[Path], wanted) -> list[Book]:
    books: list[Book] = []
    for path in paths:
        if path.suffix.lower() == ".csv":
            # a table export: its stem names the table, possibly with a suffix
            # (build_goldens' email_template_config_by_pipeline.csv)
            target = match_sheet(path.stem, wanted) or next(
                (w for w in wanted if sheet_key(path.stem).startswith(sheet_key(w))), None)
            book = Book(path.name, [path.stem])
            if target:
                with path.open(encoding="utf-8-sig", newline="") as fh:
                    head, rows = _table(csv.reader(fh))
                book.sheets[target] = _records(head, rows)
            books.append(book)
            continue
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            book = Book(path.name, list(wb.sheetnames))
            for name in wb.sheetnames:
                target = match_sheet(name, wanted)
                if target is None:
                    continue
                headers, records = _records(*_table(wb[name].iter_rows(values_only=True)))
                have_h, have_r = book.sheets.setdefault(target, ({}, []))
                for k, v in headers.items():
                    have_h.setdefault(k, v)
                have_r.extend(records)
        finally:
            wb.close()
        books.append(book)
    return books


def merge_books(books: list[Book], sheets) -> dict[str, tuple[dict, list[dict]]]:
    out: dict[str, tuple[dict, list[dict]]] = {}
    for book in books:
        for sid, (headers, records) in book.sheets.items():
            if sid not in sheets:
                continue
            have_h, have_r = out.setdefault(sid, ({}, []))
            for k, v in headers.items():
                have_h.setdefault(k, v)
            have_r.extend(records)
    return out


def sheet_rows(paths: list[Path], wanted: set[str]) -> dict[str, tuple[dict, list[dict]]]:
    """sheet -> ({header id: header as first written}, [{header id: value}])
    over every workbook; a row whose cells are all blank is no row."""
    return merge_books(read_books(paths, wanted), set(wanted))


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


def print_inventory(books: list[Book], sheets: list[str], label: str = "corpus") -> None:
    """Every workbook's sheets, and which of the chosen sheets each gave rows."""
    print(f"{label} workbooks and their sheets:")
    for n, book in enumerate(books, 1):
        read = ", ".join(f"{s} {len(book.sheets[s][1])}" for s in sheets if s in book.sheets)
        print(f"  {n:>3} {book.name}: {len(book.sheetnames)} sheet(s) "
              f"[{', '.join(book.sheetnames)}] -> read: {read or 'none of the chosen sheets'}")
    for sid in sheets:
        n = sum(1 for b in books if sid in b.sheets)
        print(f"  {sid}: in {n} of {len(books)} {label} workbook(s)")


# ------------------------------------------------------------- --patterns


def _file_tokens(diff) -> tuple:
    try:
        return diff.load_keys(TOOLS / "iig_keys.yaml").file_name_tokens
    except Exception:  # noqa: BLE001 — patterns still work without the date rules
        return ()


def _slot_regex(value: str, tokens: tuple) -> re.Pattern[str] | None:
    """A slot value as a pattern over a cell: its alphanumeric words in order,
    any separators between them, case-insensitive, whole words; wildcards and
    date tokens (iig_keys.yaml file_name_tokens) dropped first."""
    text = str(value).strip().lower().replace("\\", "/").rsplit("/", 1)[-1]
    text = re.sub(r"\.[a-z0-9]{1,5}$", "", text)
    for pattern in tokens:
        text = pattern.sub(" ", text)
    words = [w for w in _NON_ALNUM.split(text) if w]
    if not words or len("".join(words)) < MIN_SLOT_CHARS:
        return None
    body = r"[\W_]*".join(re.escape(w) for w in words)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])", re.IGNORECASE)


def book_slots(book: Book, tokens: tuple) -> list[tuple[str, re.Pattern[str]]]:
    """(slot, regex) for every slot value of the workbook's ingestion sheets,
    the longest value first (a table name before the domain inside it)."""
    found: dict[str, tuple[str, str]] = {}
    for sid, (_headers, records) in book.sheets.items():
        if sid not in SLOT_SHEETS:
            continue
        for row in records:
            for slot, ids in SLOT_COLUMNS.items():
                for cid in ids:
                    value = str(row.get(cid) or "").strip()
                    if not filled(value):
                        continue
                    if slot == "table" and "." in value:
                        schema, value = value.rsplit(".", 1)
                        found.setdefault(schema.split(".")[-1].lower(), ("schema", schema))
                    found.setdefault(value.lower(), (slot, value))
    # one slot per value: a value two slots share (an OBJECT_NAME that is the
    # table's name) takes the first slot of SLOT_COLUMNS
    rank = {slot: n for n, slot in enumerate(SLOT_COLUMNS)}
    chosen: dict[str, tuple[str, re.Pattern[str]]] = {}
    for slot, value in sorted(found.values(), key=lambda sv: rank[sv[0]]):
        regex = _slot_regex(value, tokens)
        if regex is not None:
            chosen.setdefault(regex.pattern, (slot, regex))
    return sorted(chosen.values(), key=lambda sr: -len(sr[1].pattern))


_MARK = "\x00"


def slot_pattern(value: object, slots: list[tuple[str, re.Pattern[str]]]) -> str:
    """The cell with every slot value replaced by a marker (scrubbed later)."""
    text = str(value).strip()
    for slot, regex in slots:
        text = regex.sub(f"{_MARK}{slot}{_MARK}", text)
    return text


def _scrub_pattern(text: str, scr) -> str:
    parts = text.split(_MARK)
    return "".join(f"{{{p}}}" if i % 2 else scr.scrub(p) for i, p in enumerate(parts))


def _share(n: int, total: int) -> float | None:
    return round(100.0 * n / total, 1) if total else None


def _is_master(row: dict) -> str | None:
    text = " ".join(str(row.get(c) or "") for c in ("pipelinedescription", "pipelinename"))
    if _GRAND_MASTER.search(text):
        return "grand_master"
    if _MASTER.search(text):
        return "master"
    return None


def _groups_under(pid: str, seen: set[str], group_of: dict, children: dict) -> set[str]:
    """The GROUP_IDs of ``pid`` and every pipeline below it."""
    if pid in seen:
        return set()
    seen.add(pid)
    out = set(group_of.get(pid, set()))
    for child in children.get(pid, []):
        out |= _groups_under(child, seen, group_of, children)
    return out


def master_counts(books: list[Book]) -> dict:
    """Grand master / master schedule rows (PIPELINE_DESCRIPTION / NAME says so,
    or the row is another row's PARENT_PIPELINE_ID), and the GROUP_IDs under
    each: a child pipeline's GROUP_ID from the workbook's notebook / ingestion
    rows (PIPELINE_ID -> GROUP_ID); a grand master's through its masters."""
    per_book = []
    groups_per_master: Counter[int] = Counter()
    masters_per_group: Counter[int] = Counter()
    kinds: Counter[str] = Counter()
    for book in books:
        sched = book.sheets.get(SCHEDULE, ({}, []))[1]
        if not sched:
            continue
        group_of: dict[str, set[str]] = defaultdict(set)
        for _h, records in book.sheets.values():
            for row in records:
                pid, gid = str(row.get("pipelineid") or "").strip(), str(
                    row.get("groupid") or "").strip()
                if filled(pid) and filled(gid):
                    group_of[pid].add(gid)
        parents = {str(r.get("parentpipelineid") or "").strip() for r in sched}
        children: dict[str, list[str]] = defaultdict(list)
        for row in sched:
            parent = str(row.get("parentpipelineid") or "").strip()
            if filled(parent):
                children[parent].append(str(row.get("pipelineid") or "").strip())

        def groups_under(pid: str, seen: set[str], group_of=group_of,
                         children=children) -> set[str]:
            return _groups_under(pid, seen, group_of, children)

        masters = []
        for row in sched:
            pid = str(row.get("pipelineid") or "").strip()
            kind = _is_master(row) or ("parent" if pid and pid in parents else None)
            if kind is None:
                continue
            kinds[kind] += 1
            under = groups_under(pid, set())
            masters.append((kind, len(under)))
            groups_per_master[len(under)] += 1
        all_groups = {g for gs in group_of.values() for g in gs}
        per_group: Counter[str] = Counter()
        for row in sched:
            pid = str(row.get("pipelineid") or "").strip()
            if _is_master(row) or (pid and pid in parents):
                for gid in groups_under(pid, set()):
                    per_group[gid] += 1
        for gid in all_groups:
            masters_per_group[per_group.get(gid, 0)] += 1
        per_book.append({
            "schedule_rows": len(sched), "groups": len(all_groups),
            "grand_master": sum(1 for k, _ in masters if k == "grand_master"),
            "master": sum(1 for k, _ in masters if k == "master"),
            "parent_only": sum(1 for k, _ in masters if k == "parent")})
    return {"rows_by_kind": dict(kinds),
            "groups_under_a_master": {str(k): v for k, v in sorted(groups_per_master.items())},
            "master_rows_per_group": {str(k): v for k, v in sorted(masters_per_group.items())},
            "per_workbook": per_book}


def patterns_report(books: list[Book], sheets: list[str], assigned, withheld, scr,
                    tokens: tuple) -> dict:
    slots = {id(b): book_slots(b, tokens) for b in books}
    report: dict = {"sheets": {}}
    for sid in sheets:
        rows = [(b, r) for b in books for r in b.sheets.get(sid, ({}, []))[1]]
        headers: dict[str, str] = {}
        for b in books:
            for k, v in b.sheets.get(sid, ({}, []))[0].items():
                headers.setdefault(k, v)
        columns: dict = {}
        for cid, header in headers.items():
            values = [(b, r.get(cid)) for b, r in rows if filled(r.get(cid))]
            col: dict = {"rows": len(rows), "filled": len(values),
                         "filled_pct": _share(len(values), len(rows))}
            if assigned(header) or withheld(header):
                col["values"] = "withheld (assigned / withheld column)"
                columns[scr.scrub(header)] = col
                continue
            counts = Counter(str(v).strip() for _b, v in values)
            patterns = Counter(slot_pattern(v, slots[id(b)]) for b, v in values)
            if counts:
                value, n = counts.most_common(1)[0]
                col.update(dominant_value=scr.scrub(value),
                           dominant_value_share=_share(n, len(values)),
                           distinct_values=len(counts))
            if patterns:
                top = patterns.most_common(TOP_PATTERNS)
                col.update(dominant_pattern=_scrub_pattern(top[0][0], scr),
                           dominant_pattern_share=_share(top[0][1], len(values)),
                           distinct_patterns=len(patterns),
                           per_feed=_MARK in top[0][0],
                           top_patterns=[[_scrub_pattern(p, scr), _share(c, len(values))]
                                         for p, c in top])
            columns[scr.scrub(header)] = col
        report["sheets"][sid] = {"rows": len(rows), "columns": columns}
    sched = [r for b in books for r in b.sheets.get(SCHEDULE, ({}, []))[1]]
    by_freq: dict[str, list] = defaultdict(list)
    for row in sched:
        by_freq[scr.scrub(str(row.get("pipelinefrequency") or "").strip()) or "<blank>"].append(
            row.get("dayofschedule"))
    report["day_of_schedule_by_frequency"] = {
        freq: {"rows": len(days), "filled": sum(1 for d in days if filled(d)),
               "filled_pct": _share(sum(1 for d in days if filled(d)), len(days)),
               "dominant": (lambda c: [scr.scrub(c[0][0]), _share(c[0][1], len(days))]
                            if c else None)(Counter(str(d).strip() for d in days
                                                    if filled(d)).most_common(1))}
        for freq, days in sorted(by_freq.items(), key=lambda kv: -len(kv[1]))}
    report["masters"] = master_counts(books)
    report["rule_classes"] = rule_classes(books, scr)
    return report


def rule_classes(books: list[Book], scr) -> list[dict]:
    """DATA_QUALITY_RULES rows per (RULE_TYPE, RULE_CLASS) over the corpus,
    and how many workbooks have each (scrubbed), the most rows first."""
    rows: Counter[tuple] = Counter()
    books_with: dict[tuple, set[int]] = defaultdict(set)
    for n, book in enumerate(books):
        for row in book.sheets.get(RULES, ({}, []))[1]:
            key = tuple(str(row.get(c) or "").strip() for c in RULE_COLUMNS)
            rows[key] += 1
            books_with[key].add(n)
    return [{"rule_type": scr.scrub(t), "rule_class": scr.scrub(c), "rows": count,
             "workbooks": len(books_with[(t, c)])}
            for (t, c), count in rows.most_common()]


def patterns_markdown(report: dict, books: list[Book], sheets: list[str], scr) -> str:
    def pct(v):
        return "-" if v is None else f"{v:.1f}"

    def md(text: object) -> str:
        return str(text).replace("|", "\\|").replace("\n", " ")

    lines = ["# IIG corpus patterns - scrubbed (placeholders only)", "",
             "Slot placeholders: {feed} {table} {schema} {catalog} {domain} {subdomain} "
             "{file} {source} - the row's own workbook's values (ADLS / STGDELTA / FILE_ADLS"
             " / fixed-width sheets). G<n>: a token outside the fixture vocabulary.", "",
             f"- corpus workbooks: {len(books)}"]
    for sid in sheets:
        n = sum(1 for b in books if sid in b.sheets)
        lines.append(f"- {sid}: in {n} workbook(s), "
                     f"{report['sheets'].get(sid, {}).get('rows', 0)} row(s)")
    shapes = Counter(tuple(sorted(scr.scrub(s) for s in b.sheetnames)) for b in books)
    lines += ["", "## Sheet sets (workbooks with each set)", ""]
    lines += [f"- {c} x [{md(', '.join(s))}]" for s, c in shapes.most_common()]
    for sid, sheet in report["sheets"].items():
        lines += ["", f"## {sid} ({sheet['rows']} corpus rows)", "",
                  "| column | filled % | dominant value | share % | dominant pattern | share % "
                  "| patterns | per-feed |", "|---|---|---|---|---|---|---|---|"]
        for header, col in sheet["columns"].items():
            if "values" in col:
                lines.append(f"| {md(header)} | {pct(col['filled_pct'])} | {col['values']} "
                             "| | | | | |")
                continue
            lines.append(
                f"| {md(header)} | {pct(col['filled_pct'])} | "
                f"{md(col.get('dominant_value', ''))} | {pct(col.get('dominant_value_share'))} | "
                f"{md(col.get('dominant_pattern', ''))} | "
                f"{pct(col.get('dominant_pattern_share'))} | {col.get('distinct_patterns', 0)} | "
                f"{'yes' if col.get('per_feed') else ''} |")
    lines += ["", f"## DAY_OF_SCHEDULE by PIPELINE_FREQUENCY ({SCHEDULE})", "",
              "| frequency | rows | DAY filled | filled % | dominant DAY | share % |",
              "|---|---|---|---|---|---|"]
    for freq, d in report["day_of_schedule_by_frequency"].items():
        dom = d["dominant"] or ["", None]
        lines.append(f"| {md(freq)} | {d['rows']} | {d['filled']} | {pct(d['filled_pct'])} | "
                     f"{md(dom[0])} | {pct(dom[1])} |")
    lines += ["", f"## {RULES} rule classes (RULE_TYPE x RULE_CLASS)", "",
              f"- workbooks with the sheet: {sum(1 for b in books if RULES in b.sheets)} of "
              f"{len(books)}", "", "| RULE_TYPE | RULE_CLASS | rows | workbooks |",
              "|---|---|---|---|"]
    lines += [f"| {md(r['rule_type']) or '<blank>'} | {md(r['rule_class']) or '<blank>'} | "
              f"{r['rows']} | {r['workbooks']} |" for r in report["rule_classes"]]
    m = report["masters"]
    lines += ["", "## Grand master / master schedule rows", "",
              f"- rows by kind (description / name, else a PARENT_PIPELINE_ID): "
              f"{m['rows_by_kind'] or 'none'}",
              f"- GROUP_IDs under one master row -> master rows: {m['groups_under_a_master']}",
              f"- master rows over one GROUP_ID -> GROUP_IDs: {m['master_rows_per_group']}",
              "", "| workbook | schedule rows | GROUP_IDs | grand master | master | parent only |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {n} | {w['schedule_rows']} | {w['groups']} | {w['grand_master']} | "
              f"{w['master']} | {w['parent_only']} |" for n, w in enumerate(m["per_workbook"], 1)]
    return "\n".join(lines) + "\n"


def write_patterns(out: Path, books: list[Book], sheets: list[str], keys, assigned,
                   root: Path = TOOLS.parent) -> dict:
    """patterns.md + patterns.json under ``out``, scrubbed; re-scanned, and
    deleted on a scrub_check hit (the result's ``rescan`` names the classes)."""
    diff = _diff_module()
    sc = diff.load_scrub_check(root)
    terms = diff.load_local_denylist(root / diff.LOCAL_DENYLIST_REL)
    harvested = sc.harvest_raw_denylist()
    universe, _source, _n = diff.fixture_universe(root)
    corpus_tokens: set[str] = set()
    for b in books:
        for _h, records in b.sheets.values():
            for row in records:
                for v in row.values():
                    corpus_tokens.update(t.casefold() for t in diff._tokens(str(v or "")))
    scr = diff.Scrubber(sc, universe, frozenset(corpus_tokens), terms, harvested)

    def withheld(header: str) -> bool:
        return header_id(header) in {header_id(c) for c in keys.withhold_values}

    report = patterns_report(books, sheets, assigned, withheld, scr, _file_tokens(diff))
    out.mkdir(parents=True, exist_ok=True)
    files = [out / "patterns.md", out / "patterns.json"]
    files[0].write_text(patterns_markdown(report, books, sheets, scr), encoding="utf-8")
    files[1].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    hits = diff._rescan(sc, files, harvested, scr.local)
    if hits:
        for f in files:
            f.unlink(missing_ok=True)
    report["rescan"] = dict(hits)
    report["placeholders"] = len(scr.maps["G"]) + len(scr.maps["A"])
    return report


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
    ap.add_argument("--patterns", type=Path, metavar="DIR",
                    help="write the scrubbed patterns.md / patterns.json here")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    keys = _diff_module().load_keys(args.keys)
    blank = always_blank()

    def assigned(header: str) -> bool:
        return keys.is_assignment(header) or header_id(header) in blank
    sheets = [s.strip().upper() for s in args.sheets.split(",") if s.strip()]
    corpus_books, agent_books = workbooks(args.corpus), workbooks(args.agent)
    if not corpus_books or not agent_books:
        print(f"FAIL no workbook: corpus {len(corpus_books)}, agent {len(agent_books)}")
        return 1
    print(f"corpus: {len(corpus_books)} workbook(s); agent: {len(agent_books)} workbook(s); "
          f"threshold {args.threshold:.0f}%")
    read = [*sheets, *(s for s in (*SLOT_SHEETS, RULES) if s not in sheets)]
    corpus = read_books(corpus_books, read if args.patterns else sheets)
    agent = read_books(agent_books, sheets)
    print_inventory(corpus, sheets)
    report = fill_rates(merge_books(corpus, set(sheets)), merge_books(agent, set(sheets)),
                        sheets, args.threshold, assigned)
    print_report(report, args.show_values)
    if args.json:
        if not args.show_values:
            for sheet in report.values():
                for col in sheet["columns"].values():
                    col["dominant_value"] = None
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        print(f"wrote {args.json}")
    if args.patterns:
        patterns = write_patterns(args.patterns, corpus, sheets, keys, assigned)
        if patterns["rescan"]:
            print(f"FAIL patterns not written: the re-scan found "
                  f"{', '.join(f'{k} {v}' for k, v in sorted(patterns['rescan'].items()))}")
            return 1
        print(f"wrote {args.patterns / 'patterns.md'} + patterns.json (scrubbed: "
              f"{patterns['placeholders']} placeholder(s); re-scan 0 hits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
