"""Scrub raw client reference exports into tracked, anonymized fixtures.

Reads  inputs/reference_raw/   (gitignored, raw client exports — NEVER tracked)
Writes fixtures/reference/     (tracked, anonymized copies)

Preserved exactly: tab names, header rows, column order, generic value shapes
(DAILY, Overwrite/Append, rule types, Y/N flags, 9999-12-31 dates).

Replaced with consistent labeled synthetics (one global map, so cross-tab
references stay coherent): emails, person names, workspace URLs, cluster/pool
IDs, secret names, storage accounts, container/resource names, abfss and VM
strings, SQL-server/keyvault/webhook hosts, internal share paths, the RFC
number and its author tags, and all numeric pipeline/group/object/inventory/
connection IDs.

No raw client value appears in this file — everything sensitive is harvested
from the raw inputs at runtime, by pattern or by sheet/column position.

Usage:  python scripts/scrub_reference.py
Emits:  fixtures/reference/<name>            (scrubbed copies)
        fixtures/reference/SCRUB_REPORT.md   (class + count per file; no raw values)
        inputs/reference_raw/scrub_map.json  (raw->synthetic map, gitignored, debug only)
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "inputs" / "reference_raw"
OUT = REPO / "fixtures" / "reference"

# raw name -> scrubbed name. The playbook's raw name carries the client RFC
# number, so it is located by glob and never spelled here (the scrub scanner
# denylists it).
FILES = {
    "SFMC_IIG.xlsx": "SFMC_IIG.xlsx",
    "SFMC_stage_table_creation.txt": "SFMC_stage_table_creation.txt",
    "SFMC_standard_table_creation.txt": "SFMC_standard_table_creation.txt",
}
PLAYBOOK_GLOB = "RFC*_SFMC_Deployment_Playbook.xlsx"
PLAYBOOK_OUT = "SFMC_Deployment_Playbook.xlsx"


def raw_playbook_path():
    matches = sorted(RAW.glob(PLAYBOOK_GLOB))
    if not matches:
        raise FileNotFoundError(f"no {PLAYBOOK_GLOB} under {RAW}")
    return matches[0]


class TokenMap:
    """Consistent raw-value -> labeled-synthetic mapping."""

    def __init__(self) -> None:
        self.map: dict[str, str] = {}
        self.counters: Counter[str] = Counter()
        self.hits: dict[str, Counter[str]] = defaultdict(Counter)
        self.current_file = ""

    def token(self, raw: str, klass: str, template: str) -> str:
        if raw not in self.map:
            self.counters[klass] += 1
            self.map[raw] = template.format(n=self.counters[klass])
        self.hits[self.current_file][klass] += 1
        return self.map[raw]


TM = TokenMap()

# Ordered regex rules: (class, pattern, synthetic template).  URL-ish rules run
# before bare-resource rules so hosts inside URLs are consumed whole.
REGEX_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("abfss_location", re.compile(r"abfss://[^@\s'\"]+@[\w-]+\.dfs\.core\.windows\.net"),
     "abfss://syn-container-{n:03d}@synstorage{n:03d}.dfs.synthetic.example"),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"),
     "syn.person.{n:03d}@synthetic.example"),
    ("workspace_url", re.compile(r"https?://adb-\d+\.\d+\.azuredatabricks\.net/?"),
     "https://syn-dbx-workspace-{n:03d}.synthetic.example/"),
    ("keyvault_url", re.compile(r"https?://[\w-]+\.vault\.azure\.net/?"),
     "https://syn-keyvault-{n:03d}.synthetic.example/"),
    ("webhook_url", re.compile(r"https?://[\w-]+\.azurewebsites\.net\S*"),
     "https://syn-webhook-{n:03d}.synthetic.example/"),
    ("sqlserver_host", re.compile(r"\b[\w-]+\.database\.windows\.net?\b"),
     "syn-sqlserver-{n:03d}.synthetic.example"),
    ("cluster_or_pool_id", re.compile(r"\b\d{4}-\d{6}-[a-z0-9]{4,8}(?:-pool-[a-z0-9]+)?\b"),
     "SYN-CLUSTER-{n:03d}"),
    ("secret_name", re.compile(r"\b[A-Z0-9][A-Z0-9-]*-(?:ACCESS-)?TOKEN\b"),
     "SYN-SECRET-{n:03d}"),
    ("storage_account", re.compile(r"\bzuseprdlkst\d+\b"),
     "synstorageacct{n:03d}"),
    ("resource_name", re.compile(r"\b[zZ]-[Uu][Ss][Ee]-[A-Za-z0-9-]+\b"),
     "SYN-RESOURCE-{n:03d}"),
    ("vm_name", re.compile(r"\bzy[a-z0-9]{8,}\b"),
     "SYN-VM-{n:03d}"),
    ("rfc_number", re.compile(r"(?<![A-Za-z0-9])RFC[ _-]?\d{5,6}(?!\d)"),
     "SYN-RFC-{n:03d}"),
    ("author_tag", re.compile(r"\b[a-z]{1,3}\d{5}\b"),
     "syn-user-{n:03d}"),
    ("share_path", re.compile(r"[A-Z]:\\[^\s'\"]+"),
     r"O:\\SYN-INTERNAL-SHARE\\{n:03d}"),
    ("client_name", re.compile(r"(?i)amerihealth\s?caritas"),
     "SyntheticPayer"),
]

# Column-scoped ID classes (cell-exact replacement; header name -> class/template).
ID_COLUMNS: dict[str, tuple[str, str]] = {
    "PIPELINE_ID": ("pipeline_id", "SYN-PIPE-{n:03d}"),
    "PARENT_PIPELINE_ID": ("pipeline_id", "SYN-PIPE-{n:03d}"),
    "GROUP_ID": ("group_id", "SYN-GRP-{n:03d}"),
    "OBJECT_ID": ("object_id", "SYN-OBJ-{n:03d}"),
    "INVENTORY_ID": ("pipeline_id", "SYN-PIPE-{n:03d}"),  # shares the 190xxx space
    "SRC_ADLS_CONNECTION_ID": ("connection_id", "SYN-CONN-{n:03d}"),
    "METADATA_CONNECTION_ID": ("connection_id", "SYN-CONN-{n:03d}"),
    "TGT_CONNECTION_ID": ("connection_id", "SYN-CONN-{n:03d}"),
    "CLUSTER_DETAILS_ID": ("connection_id", "SYN-CONN-{n:03d}"),
    "SRC_CONTAINER_NAME": ("container_name", "syn-container-src-{n:03d}"),
    "TGT_CONTAINER_NAME": ("container_name", "syn-container-tgt-{n:03d}"),
}

# Playbook columns whose values are people/teams -> harvested for a global
# name pass (catches the same names inside free-text cells elsewhere).
NAME_COLUMNS = {
    "Task Owner",
    "Rollback Execution Task Owner",
    "Rollback Validation Done By",
    "Task / App Owner or App Support Resource",
    "Rollback Validation Team",
    "Rollback Execution Team",
    "Deployment Team",
    "INTERNAL_CONTACT_NM",
    "SUPPLIER_CONTACT_PH",
    "GENERATOR_CONTACT_PH",
}


def scrub_text(text: str) -> str:
    for klass, pattern, template in REGEX_RULES:
        def _sub(m: re.Match[str], klass: str = klass, template: str = template) -> str:
            raw = m.group(0)
            if "synthetic.example" in raw or "SYN-" in raw or raw.startswith(("syn.", "syn-")):
                return raw  # already a synthetic token from an earlier rule
            return TM.token(raw, klass, template)
        text = pattern.sub(_sub, text)
    return text


def _row_values(ws, row: int) -> list:
    try:
        return next(ws.iter_rows(min_row=row, max_row=row, values_only=True), []) or []
    except (IndexError, StopIteration):
        return []


def harvest_ids(wb: openpyxl.Workbook) -> dict[str, str]:
    """First pass: map every value in an ID-designated column to its token."""
    id_map: dict[str, str] = {}
    for ws in wb.worksheets:
        headers = _row_values(ws, 1)
        for col_idx, header in enumerate(headers, start=1):
            if not isinstance(header, str) or header.strip() not in ID_COLUMNS:
                continue
            klass, template = ID_COLUMNS[header.strip()]
            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                v = row[0].value
                if v is None or str(v).strip() == "":
                    continue
                raw = str(v).strip()
                id_map[raw] = TM.token(raw, klass, template)
    return id_map


def harvest_names(wb: openpyxl.Workbook) -> list[str]:
    names: set[str] = set()
    for ws in wb.worksheets:
        header_row = 2 if ws.title in (
            "PrePost-Prod & Prod Execution", "Rollback Execution", "Rollback Validation") else 1
        headers = _row_values(ws, header_row)
        for col_idx, header in enumerate(headers, start=1):
            if not isinstance(header, str) or header.strip() not in NAME_COLUMNS:
                continue
            for row in ws.iter_rows(min_row=3, min_col=col_idx, max_col=col_idx):
                v = row[0].value
                if isinstance(v, str) and v.strip() and "@" not in v and len(v.strip()) > 2:
                    names.add(v.strip())
    return sorted(names, key=len, reverse=True)  # longest first so substrings don't clobber


def replace_ids_and_names(text: str, id_map: dict[str, str], names: list[str]) -> str:
    # Only long, distinctive IDs (>= 4 chars) are replaced as substrings in free
    # text; short ones (OBJECT_ID '1') are handled cell-exact in scrub_cell.
    for raw, tok in sorted(id_map.items(), key=lambda kv: -len(kv[0])):
        if len(raw) >= 4:
            if raw.isdigit():  # survive _RFC_<number>-style separators
                text = re.sub(rf"(?<!\d){re.escape(raw)}(?!\d)", tok, text)
            else:
                text = re.sub(rf"\b{re.escape(raw)}\b", tok, text)
    for name in names:
        if name in text:
            TM.hits[TM.current_file]["person_or_team_name"] += 1
            text = text.replace(name, TM.token(name, "person_or_team_name", "SYN-PERSON-{n:03d}"))
    return text


def scrub_workbook(raw_path: Path, out_path: Path,
                   id_map: dict[str, str], names: list[str]) -> None:
    wb = openpyxl.load_workbook(raw_path)
    for ws in wb.worksheets:
        headers = {}
        for col_idx, v in enumerate(_row_values(ws, 1), start=1):
            if isinstance(v, str):
                headers[col_idx] = v.strip()
        # playbook tabs put headers on row 2
        if ws.title in ("PrePost-Prod & Prod Execution",
                        "Rollback Execution", "Rollback Validation"):
            for col_idx, v in enumerate(_row_values(ws, 2), start=1):
                if isinstance(v, str):
                    headers[col_idx] = v.strip()
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                v = cell.value
                if v is None:
                    continue
                header = headers.get(cell.column, "")
                # Contact List: every data cell is contact material -> wholesale
                if ws.title == "Contact List":
                    if isinstance(v, str) and v.strip():
                        cell.value = TM.token(v.strip(), "contact_list_cell", "SYN-CONTACT-{n:03d}")
                    continue
                # Overview row owners (column A below the two header rows)
                if ws.title == "Overview" and cell.column == 1 and cell.row >= 3:
                    if isinstance(v, str) and v.strip():
                        cell.value = TM.token(
                            v.strip(), "person_or_team_name", "SYN-PERSON-{n:03d}")
                    continue
                raw = str(v).strip()
                if header in ID_COLUMNS and raw in id_map:
                    TM.hits[TM.current_file][ID_COLUMNS[header][0]] += 1
                    cell.value = id_map[raw]
                    continue
                if isinstance(v, str):
                    new = scrub_text(v)
                    new = replace_ids_and_names(new, id_map, names)
                    if new != v:
                        cell.value = new
                elif (isinstance(v, (int, float)) and str(int(v)) in id_map
                      and len(str(int(v))) >= 4):
                    TM.hits[TM.current_file]["numeric_id"] += 1
                    cell.value = id_map[str(int(v))]
    # deterministic docProps so re-runs don't churn the tracked bytes
    epoch = datetime.datetime(2000, 1, 1)
    wb.properties.created = epoch
    wb.properties.modified = epoch
    wb.properties.creator = "scrub_reference"
    wb.properties.lastModifiedBy = "scrub_reference"
    wb.save(out_path)


def main() -> int:
    if not RAW.is_dir():
        sys.exit(f"raw input dir missing: {RAW}")
    try:
        FILES[raw_playbook_path().name] = PLAYBOOK_OUT
    except FileNotFoundError as exc:
        sys.exit(str(exc))
    missing = [n for n in FILES if not (RAW / n).exists()]
    if missing:
        sys.exit(f"missing raw reference files: {missing}")
    OUT.mkdir(parents=True, exist_ok=True)

    # Harvest IDs + names from both workbooks first, so free-text references
    # in either file (and in the .txt goldens) map to the same tokens.
    iig = openpyxl.load_workbook(RAW / "SFMC_IIG.xlsx", read_only=True, data_only=True)
    playbook = openpyxl.load_workbook(
        raw_playbook_path(), read_only=True, data_only=True)
    id_map = harvest_ids(iig)
    id_map.update(harvest_ids(playbook))
    # RFC numbers: seed both the RFC-prefixed and bare-digit forms onto ONE
    # token, so an "RFC#s" column holding just the bare number maps coherently.
    rfc_pat = re.compile(r"(?<![A-Za-z0-9])RFC[ _-]?(\d{5,6})(?!\d)")
    for wbook in (
        openpyxl.load_workbook(RAW / "SFMC_IIG.xlsx", read_only=True, data_only=True),
        openpyxl.load_workbook(raw_playbook_path(),
                               read_only=True, data_only=True),
    ):
        for ws in wbook.worksheets:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        for m in rfc_pat.finditer(v):
                            tok = TM.token(m.group(0), "rfc_number", "SYN-RFC-{n:03d}")
                            TM.map.setdefault(m.group(1), tok)
                            id_map[m.group(1)] = tok
        wbook.close()
    names = harvest_names(playbook) + harvest_names(iig)
    names = sorted(set(names), key=len, reverse=True)
    iig.close()
    playbook.close()

    for raw_name, out_name in FILES.items():
        TM.current_file = out_name
        src, dst = RAW / raw_name, OUT / out_name
        if raw_name.endswith(".txt"):
            text = src.read_text(encoding="utf-8")
            text = scrub_text(text)
            text = replace_ids_and_names(text, id_map, names)
            dst.write_text(text, encoding="utf-8", newline="\n")
        else:
            scrub_workbook(src, dst, id_map, names)
        print(f"scrubbed {raw_name} -> fixtures/reference/{out_name}")

    # debug map (gitignored — contains raw values)
    (RAW / "scrub_map.json").write_text(
        json.dumps(TM.map, indent=2, sort_keys=True), encoding="utf-8")

    # tracked report: class + count per file, NO raw values
    lines = ["# Reference-fixture scrub report", "",
             "Generated by `scripts/scrub_reference.py`. Counts are replacement",
             "events per class per output file; raw values live only in the",
             "gitignored `inputs/reference_raw/scrub_map.json`.", ""]
    for fname in FILES.values():
        lines.append(f"## {fname}")
        counts = TM.hits.get(fname, {})
        if not counts:
            lines.append("- (no replacements)")
        for klass in sorted(counts):
            lines.append(f"- {klass}: {counts[klass]}")
        lines.append("")
    (OUT / "SCRUB_REPORT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    total = sum(sum(c.values()) for c in TM.hits.values())
    print(f"report -> fixtures/reference/SCRUB_REPORT.md ({total} replacements)")

    # verification: no harvested raw token survives in any output
    from scrub_check import harvest_raw_denylist, scan_paths  # noqa: E402
    deny = harvest_raw_denylist()
    hits = scan_paths([OUT], deny)
    if hits:
        for path, token_class, ctx in hits:
            print(f"RAW VALUE SURVIVED [{token_class}] in {path}: {ctx}", file=sys.stderr)
        return 1
    print("verification scan: clean")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
