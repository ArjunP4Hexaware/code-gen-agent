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

3. A local term file (2026-10-15) — ``CODEGEN_SCRUB_DENYLIST`` names a
   gitignored file, one term per line (``#`` comments / blank lines skipped):
   :func:`load_local_denylist`, merged by :func:`active_denylist`.

Usage:
    python scripts/scrub_check.py [path ...]     # default: fixtures/reference out
    python scripts/scrub_check.py --rebaseline [root ...]   # default: config docs/acfc
        # rewrites the docs/acfc/LEAK_LEDGER.md baseline rows: one
        # "<file> <class> <sha256(term)>" per tracked hit (never the term)
Exit 1 on any hit. Also importable: harvest_raw_denylist(), scan_paths(),
scan_hits(), active_denylist(), ledger_baseline().
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "inputs" / "reference_raw"
LOCAL_DENYLIST_ENV = "CODEGEN_SCRUB_DENYLIST"
LEDGER = REPO / "docs" / "acfc" / "LEAK_LEDGER.md"
LEDGER_BEGIN = "<!-- known-hit baseline: begin -->"
LEDGER_END = "<!-- known-hit baseline: end -->"
LEDGER_ROOTS = ("config", "docs/acfc")

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
    # 2026-10-13 (round5 RUN.md named the pair's documents): a downloaded copy's
    # "(1).xlsx" suffix — the shape of a real document name, never a repo output's.
    ("copy_suffixed_document_name",
     re.compile(r"(?i)\(\d+\)\.(?:xlsx|xlsm|xls|docx|doc|csv|pdf)\b")),
]

# 2026-10-13: the SD document titles, as sha256 of each lowercased word pair /
# triple (raw title words never live in this tracked file — see the docstring).
# A text's words (lowercased [a-z0-9] runs) are hashed two and three at a time.
TITLE_PHRASE_SHA256 = frozenset({
    "aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f",
    "754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c",
    "c1b9daadae5dab4264e1f76f6ece18916beecc7905428b132bcd860a28e87e2d",
    "6da0a3d08dfb415091939601b1b877bce5be655c443468527dcf589fe1af3059",
})
_WORD = re.compile(r"[a-z0-9]+")


def title_phrases(text: str) -> list[str]:
    """The word pairs / triples of ``text`` that are a deny-listed document title
    phrase (for hashing only — never printed)."""
    import hashlib
    words = _WORD.findall(text.lower())
    return [phrase for n in (2, 3) for i in range(len(words) - n + 1)
            if hashlib.sha256((phrase := " ".join(words[i:i + n])).encode("utf-8")).hexdigest()
            in TITLE_PHRASE_SHA256]


def title_hits(text: str) -> int:
    """How many word pairs / triples of ``text`` are a deny-listed document title
    phrase (the phrase itself is never returned)."""
    return len(title_phrases(text))

# 2026-10-12 (round3 pair_2 score.json committed a workspace path carrying a
# user's address): ANY e-mail address and ANY /Workspace/Users/<user> path,
# except the synthetic / placeholder forms the repo writes on purpose.
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
WORKSPACE_USER_PATH = re.compile(r"/Workspace/Users/([^/\s'\"<>]+)")
_ALLOWED_EMAIL_DOMAINS = ("synthetic.example", "example.com", "example.org", "example", "invalid",
                          "anthropic.com")
_ALLOWED_WORKSPACE_USERS = {"u", "user", "me", "someone", "you"}


def structural_hits(text: str) -> list[tuple[str, str]]:
    """[(class, match)] for the address-shaped leaks: an e-mail address whose
    domain is not a synthetic / example one, and a ``/Workspace/Users/<user>``
    path whose user segment is not a placeholder (``<…>`` never matches)."""
    hits = []
    for m in EMAIL.finditer(text):
        domain = m.group(0).rsplit("@", 1)[1].lower()
        if not any(domain == d or domain.endswith("." + d) for d in _ALLOWED_EMAIL_DOMAINS):
            hits.append(("email_address", m.group(0)))
    for m in WORKSPACE_USER_PATH.finditer(text):
        user = m.group(1)
        if not user.strip("`.…*"):        # an elided user ("/Workspace/Users/…") names no one
            continue
        if user.lower() not in _ALLOWED_WORKSPACE_USERS and "synthetic" not in user.lower():
            hits.append(("workspace_user_path", m.group(0)))
    return hits

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


def load_local_denylist(path: str | Path | None = None) -> dict[str, str]:
    """token -> "local_denylist" from the file ``CODEGEN_SCRUB_DENYLIST`` names
    (or ``path``): one term per line, ``#`` comments and blank lines skipped.
    {} when no file is named; a named file that is missing is an error."""
    path = path or os.environ.get(LOCAL_DENYLIST_ENV, "").strip()
    if not path:
        return {}
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {line.strip(): "local_denylist" for line in lines
            if line.strip() and not line.lstrip().startswith("#")}


def active_denylist() -> dict[str, str]:
    """The harvested raw denylist plus the local term file."""
    return {**harvest_raw_denylist(), **load_local_denylist()}


def scan_hits(paths: list[Path], deny: dict[str, str] | None = None):
    """[(path, class, term)] — the same hits as :func:`scan_paths`, each with
    the FULL matched term (for hashing; never print it)."""
    deny = deny if deny is not None else harvest_raw_denylist()
    hits: list[tuple[Path, str, str]] = []
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            if RAW in f.parents or f == RAW or f.resolve() == Path(__file__).resolve():
                continue
            for text in _iter_strings(f):
                for klass, pat in GENERIC_PATTERNS:
                    m = pat.search(text)
                    if m:
                        hits.append((f, klass, m.group(0)))
                for klass, match in structural_hits(text)[:1]:
                    hits.append((f, klass, match))
                phrases = title_phrases(text)
                if phrases:
                    hits.append((f, "document_title_phrase", phrases[0]))
                for tok, klass in deny.items():
                    if len(tok) >= 5 and tok in text:
                        hits.append((f, klass, tok))
    return hits


def tracked_files(*roots: str, repo: Path = REPO) -> list[Path]:
    """``git ls-files`` under ``roots`` (paths that exist in the working tree)."""
    done = subprocess.run(["git", "-C", str(repo), "ls-files", "-z", "--", *roots],
                          capture_output=True, check=True)
    names = [n for n in done.stdout.decode("utf-8", "replace").split("\0") if n]
    return [repo / n for n in names if (repo / n).is_file()]


def ledger_baseline(files: list[Path], deny: dict[str, str] | None = None,
                    repo: Path = REPO, ledger: Path = LEDGER) -> set[tuple[str, str, str]]:
    """{(repo-relative file, class, term_sha256)} of every hit in ``files``
    (the ledger itself is skipped: it holds only hashes)."""
    return set(ledger_hit_counts(files, deny, repo, ledger))


def ledger_hit_counts(files: list[Path], deny: dict[str, str] | None = None,
                      repo: Path = REPO, ledger: Path = LEDGER) -> dict[tuple[str, str, str], int]:
    """(repo-relative file, class, term_sha256) -> hits (one per scanned text:
    an xlsx cell, a whole text file) — the ledger rows' occurrences column."""
    sys.path.insert(0, str(repo / "src"))
    from collections import Counter

    from codegen.term_hash import term_sha256

    files = [f for f in files if Path(f).resolve() != Path(ledger).resolve()]
    return dict(Counter(
        (Path(p).resolve().relative_to(repo.resolve()).as_posix(), klass, term_sha256(term))
        for p, klass, term in scan_hits(files, deny)))


def read_ledger_baseline(ledger: Path = LEDGER) -> set[tuple[str, str, str]]:
    """The (file, class, sha256) lines between the ledger's baseline markers."""
    text = ledger.read_text(encoding="utf-8")
    if LEDGER_BEGIN not in text:
        return set()
    block = text.split(LEDGER_BEGIN, 1)[1].split(LEDGER_END, 1)[0]
    out = set()
    for line in block.splitlines():
        parts = line.strip().strip("`").split("\t")
        if len(parts) in (3, 4) and re.fullmatch(r"[0-9a-f]{64}", parts[2]):
            out.add((ledger_path_decode(parts[0]), parts[1], parts[2]))
    return out


def ledger_path_encode(path: str) -> str:
    """A path as the ledger writes it: '(' / ')' percent-encoded — a real
    document's copy suffix ('name (7).xlsx') is itself a scrub pattern
    (copy_suffixed_document_name), and the ledger must not add a hit."""
    return path.replace("%", "%25").replace("(", "%28").replace(")", "%29")


def ledger_path_decode(path: str) -> str:
    return path.replace("%28", "(").replace("%29", ")").replace("%25", "%")


def write_ledger_baseline(rows, ledger: Path = LEDGER) -> None:
    """Replace the rows between the ledger's baseline markers (the prose above
    and below is kept; the markers are appended when absent). Deliberate only:
    ``scrub_check.py --rebaseline`` — the test never writes. ``rows`` is a set
    of (file, class, sha256), or a {row: occurrences} mapping (a 4th column)."""
    text = ledger.read_text(encoding="utf-8")
    counts = rows if isinstance(rows, dict) else {}
    body = "\n".join(f"{ledger_path_encode(f)}\t{k}\t{d}"
                      + (f"\t{counts[(f, k, d)]}" if counts else "") for f, k, d in sorted(rows))
    block = f"{LEDGER_BEGIN}\n```\n{body}\n```\n{LEDGER_END}"
    if LEDGER_BEGIN in text:
        head, rest = text.split(LEDGER_BEGIN, 1)
        text = head + block + rest.split(LEDGER_END, 1)[1]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    ledger.write_bytes(text.encode("utf-8"))


def scan_paths(paths: list[Path], deny: dict[str, str] | None = None):
    """Return [(path, class, context)] for every denylist hit under paths."""
    deny = deny if deny is not None else harvest_raw_denylist()
    hits: list[tuple[Path, str, str]] = []
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            if RAW in f.parents or f == RAW:
                continue  # never scan the raw dir itself
            if f.resolve() == Path(__file__).resolve():
                continue  # the scanner's own pattern table is not a leak
            for text in _iter_strings(f):
                for klass, pat in GENERIC_PATTERNS:
                    m = pat.search(text)
                    if m:
                        hits.append((f, klass, m.group(0)[:60]))
                for klass, match in structural_hits(text)[:1]:   # one per file, like above
                    hits.append((f, klass, match[:60]))
                if title_hits(text):
                    hits.append((f, "document_title_phrase", "<a deny-listed title phrase>"))
                for tok, klass in deny.items():
                    if len(tok) >= 5 and tok in text:
                        hits.append((f, klass, tok[:40] + "..."))
    return hits


def main(argv: list[str]) -> int:
    if argv[:1] == ["--rebaseline"]:
        rows = ledger_hit_counts(tracked_files(*(argv[1:] or LEDGER_ROOTS)), active_denylist())
        write_ledger_baseline(rows)
        print(f"{LEDGER.relative_to(REPO).as_posix()}: {len(rows)} baseline row(s), "
              f"{sum(rows.values())} hit(s) written (file, class, sha256, occurrences — never "
              "the term)")
        return 0
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
