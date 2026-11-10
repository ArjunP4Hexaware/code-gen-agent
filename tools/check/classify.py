"""The 12-pair check: which artefacts differ between the old and the new tree, and how -
KINDS, COUNTS and masked line SHAPES only (no cell text, no client names leave it).

argv: <work_old> <work_new>   (the harness --work dirs; tools/check/pair_check.sh)

Per differing file: "sha only" (only hex digests differ - a changed contract moves every
provenance banner's sha256) or REAL; for REAL text files the changed lines' shapes with
every word masked (words of the codegen vocabulary kept); for workbooks cell counts by
kind (value / comment) and sheet. Scratch paths, timestamps and the version are
normalized first."""
import collections
import difflib
import hashlib
import io
import re
import sys
from pathlib import Path

HEX = re.compile(r"\b[0-9a-f]{12,64}\b")
_NORM = [(re.compile(r"/tmp/[^\s'\"|)]*"), "PATH"),
         (re.compile(r"(work|state|out)_(old|new)"), r"\1_X"),
         (re.compile(r"run_\d{8}T\d{6}Z"), "run_TS"),
         (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?"), "TS"),
         (re.compile(r'"(seconds|elapsed|duration)[a-z_]*": [0-9.]+'), r'"\1": N'),
         (re.compile(r"in \d+(\.\d+)?s\b"), "in Ns"),
         (re.compile(r"\d+\.\d+\.\d+\.post\d+"), "VERSION")]
KEEP = re.compile(r"^(PIPELINE_NAME|NAMING|HELD|BACK|PROVENANCE|naming_\w+|iig_\w+|"
                  r"frd_\w+|TBLPROPERTIES|delta|CREATE|TABLE|COMMENT|INSERT|INTO)$")


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def kind(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    if name.endswith("_LOG.md"):
        return "combined LOG.md"
    if name.endswith(".json"):
        return "json:" + name if not re.search(r"\d", name) else "json"
    if name.endswith(".md"):
        return "report .md"
    return name.rsplit(".", 1)[-1]


def text(p: Path) -> str:
    data = p.read_bytes()
    try:
        s = data.decode("utf-8")
    except UnicodeDecodeError:
        return hashlib.sha256(data).hexdigest()
    for rx, rep in _NORM:
        s = rx.sub(rep, s)
    return s


def cells(p: Path) -> dict[tuple, tuple]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(p.read_bytes()))
    out = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None or c.comment is not None:
                    out[(ws.title, c.coordinate)] = (
                        text_value(c.value), text_value(c.comment.text if c.comment else None))
    return out


def text_value(v) -> str:
    s = "" if v is None else str(v)
    for rx, rep in _NORM:
        s = rx.sub(rep, s)
    return s


def shape(line: str) -> str:
    return re.sub(r"[A-Za-z0-9_.]+", lambda m: m.group(0) if KEEP.match(m.group(0)) else "w",
                  re.sub(r"`[^`]*`", "C", line))[:90]


old, new = files(Path(sys.argv[1])), files(Path(sys.argv[2]))
print("files old/new:", len(old), len(new))
print("only in OLD:", dict(collections.Counter(kind(r) for r in old.keys() - new.keys())))
print("only in NEW:", dict(collections.Counter(kind(r) for r in new.keys() - old.keys())))
kinds, by_pair = collections.Counter(), collections.Counter()
shapes, xlsx = collections.Counter(), collections.Counter()
for rel in sorted(old.keys() & new.keys()):
    a, b = old[rel], new[rel]
    if a.suffix == ".xlsx":
        ca, cb = cells(a), cells(b)
        if ca == cb:
            continue
        diff = [k for k in ca.keys() | cb.keys() if ca.get(k) != cb.get(k)]
        if all(HEX.sub("H", str(ca.get(k))) == HEX.sub("H", str(cb.get(k))) for k in diff):
            kinds["xlsx: sha only"] += 1
            continue
        kinds["xlsx: REAL"] += 1
        by_pair[rel.split("/")[0]] += 1
        for k in diff:
            va, vb = ca.get(k, ("", "")), cb.get(k, ("", ""))
            what = "value" if va[0] != vb[0] else "comment"
            xlsx[(rel.rsplit("/", 1)[-1].rsplit("_", 1)[-1], k[0][:22], what)] += 1
        continue
    ta, tb = text(a), text(b)
    if ta == tb:
        continue
    k = kind(rel)
    if "CODEGEN_BUILD" in rel:
        kinds["CODEGEN_BUILD.json (build stamp)"] += 1
        continue
    if HEX.sub("H", ta) == HEX.sub("H", tb):
        kinds[f"{k}: sha only"] += 1
        continue
    kinds[f"{k}: REAL"] += 1
    by_pair[rel.split("/")[0]] += 1
    for line in difflib.unified_diff(ta.splitlines(), tb.splitlines(), lineterm="", n=0):
        if not line.startswith(("---", "+++", "@@")):
            shapes[(k, line[0], shape(HEX.sub("H", line[1:])))] += 1
for name, n in sorted(kinds.items()):
    print(f"{n:5d}  {name}")
print("REAL changes by pair:", dict(by_pair))
if xlsx:
    print("workbook cells changed (file kind, sheet, value|comment):")
    for key, n in xlsx.most_common(15):
        print(f"  {n:5d}  {key}")
if shapes:
    print("changed-line shapes (words masked):")
    for (k, sign, s), n in shapes.most_common(25):
        print(f"  {n:5d}  {k:16s} {sign} {s}")
