"""Raw-client-value denylist scanner (pre-push / test-time scrub check).

Two layers:

1. GENERIC_PATTERNS — always on: shapes that identify real client infra and
   must never appear in tracked fixtures or emitted artefacts. Synthetic
   replacements are chosen so they never match these (``*.synthetic.example``
   hosts, ``SYN-*`` tokens).

2. Harvested raw denylist — when ``inputs/reference_raw/`` is present locally,
   every concrete sensitive token is harvested from the raw client exports at
   scan time (emails, URLs/hosts, cluster ids, resource/storage names, RFC
   numbers, author tags, VM names, 4+ digit IDs from ID columns, contact
   names). Raw values are never written into this tracked file.

Usage:
    python scripts/scrub_check.py [path ...]     # default: fixtures/reference out
Exit 1 on any hit. Also importable: harvest_raw_denylist(), scan_paths().
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "inputs" / "reference_raw"

GENERIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("databricks_workspace_host", re.compile(r"adb-\d{6,}\.\d+\.azuredatabricks\.net")),
    ("real_adls_host", re.compile(r"[\w-]+\.dfs\.core\.windows\.net")),
    ("real_sqlserver_host", re.compile(r"[\w-]+\.database\.windows\.net")),
    ("real_keyvault_host", re.compile(r"[\w-]+\.vault\.azure\.net")),
    ("real_webhook_host", re.compile(r"[\w-]+\.azurewebsites\.net")),
    ("cluster_id_shape", re.compile(r"\b\d{4}-\d{6}-[a-z0-9]{4,8}\b")),
    ("client_rfc_number", re.compile(r"\bRFC[ _-]?\d{5,6}\b")),
    ("client_email_domain", re.compile(r"(?i)@amerihealthcaritas")),
    ("client_storage_prefix", re.compile(r"(?i)zuseprdlkst\d+|z-use-pr-dlk")),
    ("client_vm_prefix", re.compile(r"\bzy[a-z0-9]{8,}\b")),
]

_HARVEST = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"      # emails
    r"|abfss://[^\s'\"]+"                                        # abfss URIs
    r"|https?://[^\s'\"]+"                                       # URLs
    r"|\b\d{4}-\d{6}-[a-z0-9]{4,8}(?:-pool-[a-z0-9]+)?\b"       # cluster/pool ids
    r"|\b[A-Z0-9][A-Z0-9-]{4,}-TOKEN\b"                          # secret names
    r"|\bzuseprdlkst\d+\b"                                       # storage accounts
    r"|\b[zZ]-[Uu][Ss][Ee]-[A-Za-z0-9-]+\b"                      # resource names
    r"|\bzy[a-z0-9]{8,}\b"                                       # VM names
    r"|\bRFC[ _-]?\d{5,6}\b"                                     # RFC numbers
    r"|\b[a-z]{1,3}\d{5}\b"                                      # author tags
    r"|\b19\d{4}\b"                                              # 190xxx pipeline/group ids
)

SCAN_SUFFIXES = {".txt", ".sql", ".md", ".py", ".json", ".yaml", ".yml", ".ipynb", ".csv", ".html"}


def _iter_strings(path: Path):
    """Yield the textual content of a file (xlsx: every cell, sheet by sheet)."""
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        yield v
        wb.close()
    elif path.suffix.lower() in SCAN_SUFFIXES or path.suffix == "":
        try:
            yield path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return


def harvest_raw_denylist() -> dict[str, str]:
    """token -> class, harvested from the raw client exports (if present)."""
    deny: dict[str, str] = {}
    if not RAW.is_dir():
        return deny
    for f in RAW.iterdir():
        if f.name == "scrub_map.json" or f.suffix.lower() not in (".xlsx", ".txt"):
            continue
        for text in _iter_strings(f):
            for m in _HARVEST.finditer(text):
                tok = m.group(0)
                if "synthetic.example" in tok or tok.startswith(("SYN-", "syn.", "syn-")):
                    continue
                deny[tok] = "harvested_raw_value"
                rfc = re.fullmatch(r"RFC[ _-]?(\d{5,6})", tok)
                if rfc:
                    deny[rfc.group(1)] = "harvested_raw_value"
    return deny


def scan_paths(paths: list[Path], deny: dict[str, str] | None = None):
    """Return [(path, class, context)] for every denylist hit under paths."""
    deny = deny if deny is not None else harvest_raw_denylist()
    hits: list[tuple[Path, str, str]] = []
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            if RAW in f.parents or f == RAW:
                continue  # never scan the raw dir itself
            for text in _iter_strings(f):
                for klass, pat in GENERIC_PATTERNS:
                    m = pat.search(text)
                    if m:
                        hits.append((f, klass, m.group(0)[:60]))
                for tok, klass in deny.items():
                    if len(tok) >= 5 and tok in text:
                        hits.append((f, klass, tok[:40] + "..."))
    return hits


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv] or [REPO / "fixtures" / "reference", REPO / "out"]
    targets = [t for t in targets if t.exists()]
    hits = scan_paths(targets)
    for path, klass, ctx in hits:
        print(f"DENYLIST HIT [{klass}] {path}: {ctx}")
    if hits:
        print(f"\n{len(hits)} hit(s) — raw client values present.", file=sys.stderr)
        return 1
    print(f"clean: {', '.join(str(t) for t in targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
