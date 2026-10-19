"""The leak gate (post75): the ONE implementation the container runner,
``tools/iig_diff.py --export-scrubbed`` and ``scripts/scrub_check.py`` call.
Ported from the D1 harness's pull_and_run notebook (its report + leak-gate
cell), which reproduced it per caller until now.

What it checks: every OUTPUT text (a run report, an export) against a denylist
built at gate time —

- **harvested** from the run's input documents (:func:`harvest`): file names
  and stems, sheet names, the header cells of each sheet's first two rows, and
  the column-A/B values of the rows below;
- the **static denylist**: a term file loaded BY PATH from the state root (the
  UC volume; :func:`static_denylist_path`) — client terms never live in the
  repo.

Harvested terms are filtered before the check (:func:`filter_terms`): five
characters or fewer, an English word (wordfreq when installed, else the
**repo-token dictionary** — the tokens of the tracked ``src/``, ``ui/`` and
``docs/`` files, ``fixtures/`` and the built frontend excluded, every file the
LEAK_LEDGER baseline lists excluded whole: a term the agent's own clean tree
spells cannot be a client term), an IIG template sheet / column name, or the
harness's own vocabulary. Static terms are never filtered.

Matching: harvested terms on word boundaries, static terms as substrings,
caseless. A hit whose every occurrence lies inside one of the report's own
label phrases is a **self-match** and does not count. Each hit is a record
(:class:`Hit`: the file, the term's class and sha256 — never the term). The
lane (:func:`lane`): ``approved`` only with zero real hits AND a clean scrub
check; anything else is ``held`` (stays local).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from codegen.term_hash import term_sha256

REPO = Path(__file__).resolve().parents[2]

STATIC_DENYLIST_ENV = "CODEGEN_LEAKGATE_DENYLIST"
STATIC_DENYLIST_REL = Path("leakgate") / "denylist_local.txt"

DICTIONARY_SCOPE = ("src", "ui", "docs")
DICTIONARY_EXCLUDE = ("ui/frontend/dist/", "fixtures/")
DICTIONARY_SUFFIXES = {".py", ".md", ".j2", ".ts", ".tsx", ".js", ".css", ".html", ".json",
                       ".yaml", ".yml", ".txt", ".toml", ".sql", ".cfg", ".ini", ".csv"}
LEDGER = REPO / "docs" / "acfc" / "LEAK_LEDGER.md"
LEDGER_BEGIN = "<!-- known-hit baseline: begin -->"
LEDGER_END = "<!-- known-hit baseline: end -->"

MIN_TERM = 4                 # a term shorter than this is never matched
MIN_HARVESTED = 6            # a harvested term must be longer than five characters

# cell texts that label structure in any workbook (never harvested)
STRUCTURAL_LABELS = frozenset({
    "pass", "fail", "status", "type", "name", "date", "description",
    "source", "target", "stage", "standard", "column", "schema",
    "table", "format", "value", "comment", "field", "user",
    "null", "data", "file", "report", "summary", "error",
    "counts", "runtime", "endpoint", "python", "version",
    "installed", "ready", "mapped", "generate", "extract",
    "layout", "verdict", "pair", "branch", "sha", "timestamp",
    "environment", "framework", "none", "true", "false",
})

# what the harness itself writes (status enums, stage names, field labels)
HARNESS_VOCAB = frozenset(w.casefold() for w in (
    "pass", "fail", "failed", "timeout", "needs_answers", "skipped",
    "clean", "blocked", "leak_gate_blocked",
    "sttm parse", "frd extract", "vdd cross-check", "generate",
    "ddl emit", "iig workbook emit", "dml emit", "notebook emit",
    "sttm_parse", "frd_extract", "vdd_crosscheck",
    "ddl_emit", "iig_emit", "dml_emit", "notebook_emit",
    "layout family", "frd type", "mapped columns",
    "unresolved column roles", "gate verdict",
    "unpopulated iig cells", "self-check", "leak gate",
    "terms checked", "real hits", "self-match hits",
    "exception", "message", "traceback", "needed answers",
    "run report", "environment", "summary", "stages", "counts",
    "overwrite", "append", "synonyms",
    "codegen-data-engineer-agent", "openpyxl", "pydantic",
    "jinja2", "pyyaml", "ruff", "databricks-sdk",
) if len(w) >= MIN_TERM)

# the report's own label regions: a hit wholly inside one is a self-match
REPORT_LABEL_PHRASES = (
    "sttm parse", "frd extract", "vdd cross-check", "generate",
    "ddl emit", "iig workbook emit", "dml emit", "notebook emit",
    "sttm_parse", "frd_extract", "vdd_crosscheck",
    "ddl_emit", "iig_emit", "dml_emit", "notebook_emit",
    "layout family", "frd type", "mapped columns",
    "unresolved column roles", "gate verdict",
    "unpopulated iig cells", "self-check (leak gate)",
    "terms checked", "hits found",
    "# run report", "## environment", "## summary",
    "### stages", "### counts", "### error", "### needed answers", "### model usage",
)

STATIC = "local_denylist"


# ------------------------------------------------------------------ harvest


def harvest(pair_dirs: Iterable[Path]) -> dict[str, str]:
    """term -> class from the run's input documents (module docstring);
    structural labels and terms under :data:`MIN_TERM` characters left out."""
    terms: dict[str, str] = {}
    for folder in pair_dirs:
        folder = Path(folder)
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.name.startswith("~$"):
                continue
            terms[path.name] = "file_name"
            terms[path.stem] = "file_stem"
            if path.suffix.lower() == ".xlsx":
                _harvest_workbook(path, terms)
    return {t: c for t, c in terms.items()
            if len(t) >= MIN_TERM and t.casefold() not in STRUCTURAL_LABELS}


def _harvest_workbook(path: Path, terms: dict[str, str]) -> None:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(path.open("rb"), read_only=True, data_only=True)
    except Exception:  # noqa: BLE001 - an unreadable workbook harvests its names only
        return
    try:
        for ws in wb.worksheets:
            terms[ws.title] = "sheet_name"
            for index, row in enumerate(ws.iter_rows(values_only=True), 1):
                cells = list(row) if index <= 2 else list(row)[:2]
                klass = "header_cell" if index <= 2 else "column_value"
                for value in cells:
                    if isinstance(value, str) and len(value.strip()) >= MIN_TERM:
                        terms.setdefault(value.strip(), klass)
    finally:
        wb.close()


# ---------------------------------------------------------- static denylist


def static_denylist_path() -> Path | None:
    """``CODEGEN_LEAKGATE_DENYLIST``, else ``<state root>/leakgate/denylist_local.txt``
    (the state root is the UC volume, or its local copy in the App) — None when
    neither exists."""
    named = os.environ.get(STATIC_DENYLIST_ENV, "").strip()
    if named:
        return Path(named)
    from codegen.config import state_root

    candidate = state_root() / STATIC_DENYLIST_REL
    return candidate if candidate.is_file() else None


def load_static_denylist(path: Path | None = None) -> dict[str, str]:
    """term -> ``local_denylist``: one term per line, ``#`` comments and blank
    lines skipped. {} when no file is named or found; a NAMED file that is
    missing is an error (the gate must not pass for want of its list)."""
    path = Path(path) if path is not None else static_denylist_path()
    if path is None:
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {line.strip(): STATIC for line in lines
            if line.strip() and not line.lstrip().startswith("#")
            and len(line.strip()) >= MIN_TERM}


# --------------------------------------------------------------- dictionary


def read_ledger(ledger: Path = LEDGER) -> set[tuple[str, str, str]]:
    """The (file, class, sha256) rows between the ledger's baseline markers."""
    if not Path(ledger).is_file():
        return set()
    text = Path(ledger).read_text(encoding="utf-8")
    if LEDGER_BEGIN not in text:
        return set()
    block = text.split(LEDGER_BEGIN, 1)[1].split(LEDGER_END, 1)[0]
    rows = set()
    for line in block.splitlines():
        parts = line.strip().strip("`").split("\t")
        if len(parts) in (3, 4) and re.fullmatch(r"[0-9a-f]{64}", parts[2]):
            rows.add((ledger_path_decode(parts[0]), parts[1], parts[2]))
    return rows


def ledger_path_decode(path: str) -> str:
    return path.replace("%28", "(").replace("%29", ")").replace("%25", "%")


@dataclass(frozen=True)
class Dictionary:
    words: frozenset[str]
    source: str                 # "wordfreq" | "repo-tokens" | "none"
    files: int = 0


def _tracked(root: Path, scope: tuple[str, ...]) -> list[str]:
    done = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", *scope],
                          capture_output=True, check=True, timeout=120)
    return [n for n in done.stdout.decode("utf-8", "replace").split("\0") if n]


def _glob_regex(pattern: str) -> str:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        c = pattern[i]
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[" and "]" in pattern[i + 1:]:
            j = pattern.index("]", i + 1)
            body = pattern[i + 1:j]
            out.append("[" + ("^" + body[1:] if body.startswith("!") else body) + "]")
            i = j
        elif c == "\\" and i + 1 < len(pattern):
            i += 1
            out.append(re.escape(pattern[i]))
        else:
            out.append(re.escape(c))
        i += 1
    return "".join(out)


def gitignore_rules(path: Path) -> list[tuple[re.Pattern[str], bool, bool]]:
    """(regex over the repo-relative posix path, negated, directories only) per
    line of a .gitignore — enough of git's rules for the repo's own file."""
    rules = []
    if not path.is_file():
        return rules
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        line = line[1:] if negated else line
        dir_only = line.endswith("/")
        line = line.rstrip("/")
        anchored = "/" in line
        body = _glob_regex(line.lstrip("/"))
        rules.append((re.compile(("^" if anchored else "^(?:.*/)?") + body + "$"),
                      negated, dir_only))
    return rules


def gitignored(rel: str, is_dir: bool, rules) -> bool:
    ignored = False
    for regex, negated, dir_only in rules:
        if (is_dir or not dir_only) and regex.match(rel):
            ignored = not negated            # the last matching line wins
    return ignored


def walk_scope(root: Path, scope: tuple[str, ...]) -> list[str]:
    """No git: the scope's files the repo's .gitignore does not ignore
    (repo-relative names)."""
    rules = gitignore_rules(root / ".gitignore")
    names: list[str] = []
    for top in scope:
        base = root / top
        if base.is_file() and not gitignored(top, False, rules):
            names.append(top)
            continue
        if not base.is_dir() or gitignored(top, True, rules):
            continue
        for folder, dirs, files in os.walk(base):
            rel = Path(folder).relative_to(root).as_posix()
            dirs[:] = sorted(x for x in dirs if not gitignored(f"{rel}/{x}", True, rules))
            names += [f"{rel}/{n}" for n in sorted(files)
                      if not gitignored(f"{rel}/{n}", False, rules)]
    return names


def repo_token_dictionary(root: Path = REPO, scope: tuple[str, ...] = DICTIONARY_SCOPE,
                          ledger: Path | None = None,
                          token_pattern: str = rf"[A-Za-z]{{{MIN_TERM},}}") -> Dictionary:
    """The tokens (letters only, >= :data:`MIN_TERM`, caseless) of the TRACKED
    text files under ``scope``; :data:`DICTIONARY_EXCLUDE` and every file the
    ledger baseline lists are left out, and a token whose hash is a ledger
    hash is dropped. No git (D1's workspace) = the same scope walked on disk,
    the repo's .gitignore honoured. ``token_pattern``: what a token is
    (iig_diff's export keeps letter-and-digit runs of the same files)."""
    root = Path(root)
    rows = read_ledger(ledger if ledger is not None else root / "docs" / "acfc" /
                       "LEAK_LEDGER.md")
    ledgered = {f for f, _k, _h in rows}
    hashes = {h for _f, _k, h in rows}
    try:
        if not (root / ".git").exists():
            raise FileNotFoundError(f"no .git under {root}")
        names = _tracked(root, scope)
        source = "repo-tokens"
    except (OSError, subprocess.SubprocessError):
        names = walk_scope(root, scope)          # D1's workspace checkout has no .git
        source = "repo-tokens (disk walk, .gitignore honoured)"
    tokens: set[str] = set()
    used = 0
    for name in names:
        if name.startswith(DICTIONARY_EXCLUDE) or name in ledgered:
            continue
        path = root / name
        if path.suffix.lower() not in DICTIONARY_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        used += 1
        tokens.update(t.casefold() for t in re.findall(token_pattern, text))
    tokens = {t for t in tokens if term_sha256(t) not in hashes}
    return Dictionary(frozenset(tokens), source, used)


def english_words(root: Path = REPO) -> Dictionary:
    """wordfreq's top 50k English words (>= 4 characters) when installed;
    else the repo-token dictionary (never an install)."""
    try:
        from wordfreq import top_n_list
    except ImportError:
        return repo_token_dictionary(root)
    return Dictionary(frozenset(w.casefold() for w in top_n_list("en", 50000)
                                if len(w) >= MIN_TERM), "wordfreq")


def template_vocabulary(config=None) -> frozenset[str]:
    """The IIG templates' sheet and column names (caseless), from the config."""
    if config is None:
        from codegen.config import load_config

        config = load_config(REPO / "config" / "config.yaml")
    words: set[str] = set()
    for tpl in config.metadata.templates.values():
        for tab, spec in (tpl.tabs or {}).items():
            words.add(str(tab).casefold())
            words.update(str(h).casefold() for h in getattr(spec, "headers", None) or [])
    return frozenset(words)


def _all_words_in(term: str, words: frozenset[str]) -> bool:
    parts = [w for w in re.split(r"[\s_\-/.,;:()]+", term.strip()) if w.isalpha()]
    return bool(parts) and all(w.casefold() in words for w in parts)


@dataclass(frozen=True)
class Denylist:
    terms: dict[str, str]
    dropped: int
    dictionary: str
    dictionary_tokens: int = 0
    raw: int = 0

    @property
    def static_sha256(self) -> str | None:
        return _terms_sha({t: c for t, c in self.terms.items() if c == STATIC}) or None

    @property
    def harvested_sha256(self) -> str:
        return _terms_sha({t: c for t, c in self.terms.items() if c != STATIC})


def filter_terms(raw: dict[str, str], words: frozenset[str],
                 vocabulary: frozenset[str] = frozenset()) -> tuple[dict[str, str], int]:
    """(the terms checked, how many harvested ones were dropped) — module docstring."""
    kept: dict[str, str] = {}
    dropped = 0
    noise = words | vocabulary | HARNESS_VOCAB
    for term, klass in raw.items():
        if klass == STATIC:
            kept[term] = klass
            continue
        folded = term.strip().casefold()
        if len(term.strip()) < MIN_HARVESTED or folded in noise or _all_words_in(term, words):
            dropped += 1
        else:
            kept[term] = klass
    return kept, dropped


def build_denylist(pair_dirs: Iterable[Path], static: Path | None = None, *,
                   root: Path = REPO, dictionary: Dictionary | None = None,
                   vocabulary: frozenset[str] | None = None) -> Denylist:
    """Harvest + static list, filtered (the gate's denylist for one run)."""
    raw = {**harvest(pair_dirs), **load_static_denylist(static)}
    words = dictionary if dictionary is not None else english_words(root)
    vocab = vocabulary if vocabulary is not None else template_vocabulary()
    terms, dropped = filter_terms(raw, words.words, vocab)
    return Denylist(terms, dropped, words.source, len(words.words), len(raw))


def _terms_sha(terms: dict[str, str]) -> str:
    if not terms:
        return ""
    ordered = sorted(terms.items(), key=lambda item: item[0].casefold())
    content = "\n".join(f"{t}\t{c}" for t, c in ordered)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------- scan


@dataclass(frozen=True)
class Hit:
    output_file: str
    pattern_class: str
    term_sha256: str
    occurrences: int
    self_match: bool
    report_field: str | None
    line_excerpt_len: int


@dataclass
class GateResult:
    terms_checked: int
    dictionary: str
    harvested_dropped: int
    static_sha256: str | None
    harvested_sha256: str
    hits: list[Hit] = field(default_factory=list)

    @property
    def real_hits(self) -> int:
        return sum(1 for h in self.hits if not h.self_match)

    @property
    def self_match_hits(self) -> int:
        return sum(1 for h in self.hits if h.self_match)

    @property
    def clean(self) -> bool:
        return self.real_hits == 0

    def summary(self) -> dict:
        return {"verdict": "CLEAN" if self.clean else "BLOCKED", "dictionary": self.dictionary,
                "terms_checked": self.terms_checked, "real_hits": self.real_hits,
                "self_match_hits": self.self_match_hits,
                "harvested_terms_dropped": self.harvested_dropped,
                "static_denylist_sha256": self.static_sha256,
                "harvested_terms_sha256": self.harvested_sha256}


def _pattern(term: str, klass: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    return re.compile(escaped if klass == STATIC else rf"\b{escaped}\b", re.IGNORECASE)


def _is_self_match(term: str, text_lower: str) -> bool:
    positions = [m.start() for m in re.finditer(re.escape(term.lower()), text_lower)]
    regions = [(m.start(), m.end()) for phrase in REPORT_LABEL_PHRASES
               for m in re.finditer(re.escape(phrase), text_lower)]
    return all(any(a <= pos and pos + len(term) <= b for a, b in regions) for pos in positions)


def _pair_index(text: str, start: int, is_json: bool) -> int | None:
    pattern = r'"pair"\s*:\s*"pair_(\d+)"' if is_json else r"^## pair_(\d+)"
    found = list(re.finditer(pattern, text[:start], re.MULTILINE))
    return int(found[-1].group(1)) - 1 if found else None


def scan(files: dict[str, str], denylist: Denylist) -> GateResult:
    """Gate ``files`` ({name: text}) — every term of ``denylist``."""
    result = GateResult(len(denylist.terms), denylist.dictionary, denylist.dropped,
                        denylist.static_sha256, denylist.harvested_sha256)
    for name, text in files.items():
        lower = text.lower()
        is_json = name.endswith(".json")
        for term, klass in denylist.terms.items():
            if len(term) < MIN_TERM:
                continue
            matches = list(_pattern(term, klass).finditer(text))
            if not matches:
                continue
            pairs: set[int] = set()
            longest = 0
            for m in matches:
                index = _pair_index(text, m.start(), is_json)
                if index is not None:
                    pairs.add(index)
                start = text.rfind("\n", 0, m.start()) + 1
                end = text.find("\n", m.end())
                longest = max(longest, (len(text) if end == -1 else end) - start)
            result.hits.append(Hit(
                output_file=name, pattern_class=klass, term_sha256=term_sha256(term),
                occurrences=len(matches), self_match=_is_self_match(term, lower),
                report_field=",".join(f"pairs[{i}]" for i in sorted(pairs)) or None,
                line_excerpt_len=longest))
    return result


def scan_paths(paths: Iterable[Path], denylist: Denylist, root: Path | None = None) -> GateResult:
    """:func:`scan` over text files (every file below a folder)."""
    files: dict[str, str] = {}
    for base in paths:
        base = Path(base)
        found = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in found:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            files[(path.relative_to(root) if root else path).as_posix()] = text
    return scan(files, denylist)


def redact(text: str, denylist: Denylist) -> str:
    """Every term -> ``[H:<first 10 of its sha256>]`` (longest first)."""
    for term in sorted(denylist.terms, key=len, reverse=True):
        if len(term) >= MIN_TERM:
            tag = f"[H:{term_sha256(term)[:10]}]"
            text = _pattern(term, denylist.terms[term]).sub(tag, text)
    return text


def classify(hit: Hit, denylist: Denylist, vocabulary: frozenset[str]) -> str:
    """framework_term (an IIG template / harness word) | document_identifier."""
    for term in denylist.terms:
        if term_sha256(term) == hit.term_sha256:
            folded = term.strip().casefold()
            framework = folded in vocabulary | HARNESS_VOCAB
            return "framework_term" if framework else "document_identifier"
    return "document_identifier"


def write_hits(result: GateResult, path: Path) -> None:
    """One JSON line per hit — hashes and counts, never a term."""
    with open(path, "w", encoding="utf-8") as fh:
        for hit in result.hits:
            fh.write(json.dumps(asdict(hit), separators=(",", ":")) + "\n")


def lane(result: GateResult, scrub_clean: bool = True) -> str:
    """``approved`` only with zero real hits and a clean scrub check; else ``held``."""
    return "approved" if result.clean and scrub_clean else "held"
