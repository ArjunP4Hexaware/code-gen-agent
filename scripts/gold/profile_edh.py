"""Shape profiler for the EDH E2E gold-mapping JSON dialect — COUNTS ONLY.

    python scripts/gold/profile_edh.py DIR        # DIR holds _manifest.json + the table files

Prints one JSON object: key presence, grammar pattern counts (docs/acfc/EDH_E2E_JSON_SCHEMA.md
§3), defect counts and example COORDINATES (``file[<n>].mappings[<k>]``, 1-based sorted file
order, manifest excluded). It never prints a value read from the files: no table, column,
region label, criteria text or expression — tests/test_gold_profiler.py asserts it. Stdlib only,
so it runs on D1 against the real set and at home against tests/fixtures/edh_gold_synthetic/.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

FLAGS = re.I | re.S
W = r"[A-Za-z_][A-Za-z0-9_#]*"
LIT = r"(?:'[^']*'|‘[^’]*’|’[^’]*’|\"[^\"]*\"|“[^”]*”|\d+(?:\.\d+)?)"
CONNECTIVES = {"and", "or", "&", "where", "column", "columns", "table", "tables", "the", ",", "."}
PK_SPELLINGS = {"Primary key", "Primary Key", "PRIMARY KEY", "PK"}
SENTINELS = {"NOT AVAILABLE", "NOT SUPPLIED", "COLUMN NOT FOUND", "NULL"}
STANDARD_REGION_KEY = re.compile(r"^[A-Z]+[0-9]+ - LOB ?\(")

# §3.1 join hints
J_USING = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+(?:WHERE\s+(?P<pre>.+?)\s+)?AND\s+INNER\s+JOIN\s+with\s+"
    rf"{W}(?:\s*&\s*(?P<tbl2>{W}))?(?:\s+tables?)?(?:\s+WHERE\s+(?P<mid>.+?))?\s+using\s+"
    rf"{W}(?:\s+column)?(?:\s*&\s*(?P<col2>{W})(?:\s+columns?)?\s*$)?(?P<rest>.*)$",
    FLAGS,
)
J_COLUMN_NO_USING = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+AND\s+INNER\s+JOIN\s+with\s+{W}\s+WHERE\s+(?P<mid>.+?)\s+{W}\s+column(?P<rest>.*)$",
    FLAGS,
)
J_EQUALITIES = re.compile(rf"(INNER|OUTER).*?{W}\.{W}\s*\*?=\s*{W}\.{W}", FLAGS)
J_TABLE_ONLY = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+AND\s+INNER\s+JOIN\s+with\s+{W}(?:\s+table)?\s*$", FLAGS
)

# §3.2 filters (run after the join clause and the "<verb> FROM <src> [WHERE]" preamble are removed)
PREAMBLE = re.compile(rf"^\s*{W}\s+FROM\s+{W}\s*(?:WHERE\b)?", FLAGS)
F_PATTERNS = [
    (
        "F3 date window, relative",
        re.compile(
            rf"{W}\s*\(\s*{W}\s*\)\s*>=\s*sysdate\s*-\s*\d+\s+AND\s+{W}\s*\(\s*{W}\s*\)\s*<=\s*sysdate",
            FLAGS,
        ),
    ),
    (
        "F4 date window, as-of range",
        re.compile(
            rf"\(\s*{W}\s*/\s*{W}\s*>=\s*{W}\s+AND\s+{W}\s*/\s*{W}\s*<=\s*{W}\s*\)"
            rf"(?:\s+AND\s+\(\s*{W}\s*/\s*{W}\s*>=\s*{W}\s+AND\s+{W}\s*/\s*{W}\s*<=\s*{W}\s*\))?",
            FLAGS,
        ),
    ),
    ("F5 date window, between", re.compile(rf"{W}\s*<\s*{W}\s*\(\s*\)\s*<\s*{W}", FLAGS)),
    ("F2 IN list", re.compile(rf"{W}\s+IN\s*\(\s*{LIT}(?:\s*,\s*{LIT})*\s*\)", FLAGS)),
    ("F1 equality", re.compile(rf"{W}(?:\s+{W})*\s*(?:=|<>|!=)\s*(?:{LIT}|{W})", FLAGS)),
]

# §3.3 mapping_edits (non-Direct rows), first match wins
NULL_TEST = (
    rf"(?:ISNULL\s*\(\s*{W}\s*\)|{W}\s+ISNULL|{W}\s+IS\s+(?:NOT\s+)?NULL|"
    rf"{W}\s+(?:IS\s+)?(?:NOT\s+)?(?:an?\s+)?(?:{W}\s+)?empty\s+string(?:\s+OR\s+NULL)?)"
)
M_PATTERNS = [
    ("literal NULL", re.compile(r"^\s*set(?:\s+(?:to|as))?\s+NULL\s*$", FLAGS)),
    ("system value", re.compile(r"^\s*current\s+timestamp\s*$", FLAGS)),
    ("CAST", re.compile(r"\b(?:CONVERT|CAST)\s*\(", FLAGS)),
    (
        "substring slice",
        re.compile(
            rf"^\s*(?:TRIM\s*\(\s*{W}\s*\)|\(\s*{W}\s*\)|{W})\s*\[\s*\d+\s*,\s*\d+\s*\]\s*$", FLAGS
        ),
    ),
    (
        "COALESCE-equivalent",
        re.compile(
            rf"^\s*if\s+{NULL_TEST}\s+THEN\s+(?:(?!\bif\b).)+?\s+ELSE\s+(?:(?!\bif\b).)+$", FLAGS
        ),
    ),
    ("CASE", re.compile(r"^\s*if\b.+\bTHEN\b.+\bELSE\b.+$", FLAGS)),
]


def join_class(text: str) -> tuple[str | None, str]:
    """The §3.1 pattern of one cell and the text left for the filter grammar."""
    if not re.search(r"\bjoin\b", text, FLAGS):
        return None, text
    m = J_USING.match(text)
    if m:
        rest = " ".join(x for x in (m.group("pre"), m.group("mid"), m.group("rest")) if x)
        return (
            "J1 using-column, filter before join" if m.group("pre") else "J1 using-column"
        ), rest
    m = J_COLUMN_NO_USING.match(text)
    if m:
        return "J2 column named without using", f"{m.group('mid') or ''} {m.group('rest') or ''}"
    if J_EQUALITIES.search(text):
        return "J3 alias-qualified equalities", ""
    if J_TABLE_ONLY.match(text):
        return "J4 table only", ""
    return "J free text", text


def filter_classes(text: str) -> tuple[list[str], list[str]]:
    """The §3.2 patterns found, and the words no pattern or connective accounts for."""
    found, residue = [], PREAMBLE.sub(" ", text)
    for name, rx in F_PATTERNS:
        if rx.search(residue):
            found.append(name)
            residue = rx.sub(" ", residue)
    leftover = [t for t in re.findall(r"[A-Za-z_]+|&|,", residue) if t.lower() not in CONNECTIVES]
    return found, leftover


def edit_class(text: str, source_field: str | None) -> str | None:
    """The §3.3 class of one non-Direct mapping_edits cell; None = free text."""
    s = text.strip()
    if re.fullmatch(W, s):
        if "_" not in s:
            return None
        same = s.lower() == (source_field or "").strip().lower()
        return "column reference (= source_field)" if same else "column reference (another column)"
    for name, rx in M_PATTERNS:
        if rx.search(s):
            return name
    return None


def _is_identifier(value: str | None) -> bool:
    return bool(re.fullmatch(W, value or ""))


def profile(directory: str | Path) -> dict:
    d = Path(directory)
    files = sorted(p for p in d.glob("*.json") if not p.name.startswith("_"))
    c = {
        name: collections.Counter()
        for name in (
            "top",
            "row_keys_files",
            "row_non_null",
            "joins",
            "join_features",
            "filters",
            "filter_per_cell",
            "edits",
            "regions",
            "defects",
            "blocks",
            "document_notes",
        )
    }
    examples: dict[str, str] = {}
    region_keys: set[str] = set()
    rows = direct = concat_inside = 0
    for i, path in enumerate(files, start=1):
        doc = json.loads(path.read_text(encoding="utf-8"))
        mappings = doc.get("mappings") or []
        for k, v in doc.items():
            c["top"][k] += v not in (None, "", [], {})
        for k in {k for x in mappings for k in x}:
            c["row_keys_files"][k] += 1
        regions = doc.get("regional_table_structures") or {}
        region_keys |= set(regions)
        _profile_regions(regions, mappings, c["regions"])
        targets = {x.get("target_table") for x in mappings}
        attrs = [x.get("target_attribute") for x in mappings]
        c["defects"]["top target_table not an identifier"] += not _is_identifier(
            (doc.get("target_table") or "").strip()
        )
        keyed = [(x.get("block_index"), x.get("target_attribute")) for x in mappings]
        c["defects"]["duplicated (block_index, target_attribute)"] += len(keyed) != len(set(keyed))
        blocks = {x.get("block_index") for x in mappings}
        c["blocks"]["files with >1 block"] += len(blocks) > 1
        c["blocks"]["blocks"] += len(blocks)
        c["blocks"]["rows without block_index"] += sum(
            not isinstance(x.get("block_index"), int) for x in mappings
        )
        c["blocks"]["rows without source_row"] += sum(
            not isinstance(x.get("source_row"), int) for x in mappings
        )
        notes = doc.get("document_notes")
        c["document_notes"]["files with document_notes null"] += notes is None
        for note in notes or []:
            c["document_notes"]["kind " + str(note.get("kind"))] += 1
        c["defects"][">1 mappings[].target_table"] += len(targets) > 1
        c["defects"]["target_attribute not an identifier"] += any(
            not _is_identifier(a) for a in attrs
        )
        for r, x in enumerate(mappings):
            rows += 1
            where = f"file[{i}].mappings[{r}]"
            for k, v in x.items():
                c["row_non_null"][k] += v not in (None, "")
            fmt = (x.get("source_format") or "").strip()
            c["defects"]["drag-filled VARCHAR<n>, n > 2 (rows)"] += bool(
                re.fullmatch(r"VARCHAR(?:[3-9]|\d\d+)", fmt, FLAGS)
            )
            idx = (x.get("indexes") or "").strip()
            c["defects"]["indexes not a PK spelling (rows)"] += (
                bool(idx) and idx not in PK_SPELLINGS
            )
            _profile_criteria(x.get("selection_criteria"), where, c, examples)
            edit = x.get("mapping_edits")
            if edit:
                if re.match(r"\s*direct\b", edit, FLAGS):
                    direct += 1
                    continue
                concat_inside += bool(re.search(r"\S\s*:\s*\S", edit))
                name = edit_class(edit, x.get("source_field")) or "free text"
                c["edits"][name] += 1
                examples.setdefault("edit: " + name, where)
    out = {name: dict(counter) for name, counter in c.items()}
    out.update(
        files=len(files),
        rows=rows,
        direct_edits=direct,
        concat_inside=concat_inside,
        distinct_region_keys=len(region_keys),
        examples=examples,
    )
    return out


def _profile_regions(regions: dict, mappings: list, counter: collections.Counter) -> None:
    if not regions:
        return
    counter["files with regions"] += 1
    counter["non-standard region keys"] += sum(not STANDARD_REGION_KEY.match(k) for k in regions)
    counter["files with 7 regions"] += len(regions) == 7
    shapes = {
        tuple((it.get("column_name"), it.get("data_type")) for it in v) for v in regions.values()
    }
    counter["files whose regions differ"] += len(shapes) > 1
    targets = {x.get("target_attribute") for x in mappings}
    first = {it.get("column_name") for it in next(iter(regions.values()))}
    counter["files whose region columns match targets"] += (
        bool(first) and len(first & targets) / len(first) > 0.8
    )
    for items in regions.values():
        for it in items:
            dt = it.get("data_type")
            counter["items"] += 1
            counter["column_name not an identifier"] += not _is_identifier(it.get("column_name"))
            counter["data_type sentinel or null"] += dt is None or dt.strip().upper() in SENTINELS
            counter["data_type trailing comma"] += bool(dt) and dt.rstrip().endswith(",")
            counter["data_type inner padding"] += bool(dt) and bool(re.search(r"\S\s{2,}\S", dt))


def _profile_criteria(text: str | None, where: str, c: dict, examples: dict) -> None:
    if not text:
        return
    jc, rest = join_class(text)
    if jc:
        c["joins"][jc] += 1
        examples.setdefault("join: " + jc, where)
        m = J_USING.match(text)
        if m:
            c["join_features"]["two joined tables"] += bool(m.group("tbl2"))
            c["join_features"]["second join column"] += bool(m.group("col2"))
    found, leftover = filter_classes(rest if jc else text)
    if jc and jc != "J free text" and not found and not leftover:
        c["filter_per_cell"]["join only"] += 1
        return
    for name in found:
        c["filters"][name] += 1
        examples.setdefault("filter: " + name, where)
    if leftover or not found:
        c["filter_per_cell"]["free text"] += 1
    elif any(n.startswith(("F3", "F4", "F5")) for n in found):
        c["filter_per_cell"]["date window"] += 1
    else:
        c["filter_per_cell"]["equality"] += 1


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    print(json.dumps(profile(argv[0]), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
