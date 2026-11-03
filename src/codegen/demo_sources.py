"""Demo-UI display helpers: source files a run reads + reference documents.

Everything here is DISPLAY ONLY for the demo dashboard and the
``codegen demo-source-files`` CLI command — pure reads, no network, no
writes, and nothing in ``resolve → rules → reasoning → emit → gate``
consumes it. Values not read from a real document are marked
``synthetic: True`` so the UI can badge them honestly.

Three responsibilities:

- ``scan_reference_documents``: which of the expected client reference
  documents (``demo.input_documents``) are present in the configured input
  directories. Matching is case-insensitive on the file name and strips a
  leading numeric upload prefix (``1787853350398_FRD_…`` matches
  ``FRD_…``). ``CODEGEN_INPUT_DOCS_DIR`` (``os.pathsep``-separated, i.e.
  ``:`` on POSIX and ``;`` on Windows) overrides the YAML dirs — the same
  env > YAML precedence as the SharePoint knobs.
- ``source_files_payload``: per feed of the demo FRD contract, the landing
  root / file patterns / format / frequency / targets a run would read,
  synthesizing (and flagging) the landing root from
  ``demo.source_files.landing_root_template`` when the contract has none,
  plus a server-rendered ``databricks fs ls`` stand-in listing
  (``demo.databricks_paths`` placeholders until a live listing exists).
- ``read_frd_convention``: the Structural Metadata values (ADLS location,
  target schemas, load strategies) read LIVE from the real FRD ``.docx``
  when one is present in the input dirs — stdlib zip+XML, read at request
  time, never cached to disk, never copied into the repo.
"""

from __future__ import annotations

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed, TargetSpec
from codegen.resolve.resolver import normalize_feed_name

_log = logging.getLogger("codegen.pairing")

# Leading numeric upload prefix some libraries prepend on upload, and the
# " (n)" copy suffix browsers append before the extension on re-download.
_UPLOAD_PREFIX = re.compile(r"^\d+_")
_COPY_SUFFIX = re.compile(r"\s*\(\d+\)(?=\.[^.]+$|$)")


def canonical_document_name(name: str) -> str:
    """THE document-name match key, shared by every list that compares names
    (documents card, STTM chooser dedupe, FRD pairing): case-insensitive,
    numeric upload prefix stripped, ``" (n)"`` copy suffix stripped."""
    return _COPY_SUFFIX.sub("", _UPLOAD_PREFIX.sub("", name)).lower()


# Backwards-compatible internal alias.
_canonical_name = canonical_document_name


def find_frd_docx(present: list[dict]) -> dict | None:
    """The FRD document among the documents-card matches: a ``.docx`` whose
    name carries the ``frd`` role token. "Any .docx" stopped being safe the
    moment the EDO standards documents joined the expected list — they are
    reference material, never the FRD under evaluation."""
    return next(
        (
            p
            for p in present
            if p["name"].lower().endswith(".docx") and "frd" in document_roles(p["name"])
        ),
        None,
    )

# A shared ticket/project number (6+ digits, e.g. 1005034) is the one
# CONSERVATIVE signal that an STTM and an FRD belong together; anything
# fuzzier risks false pairs, and no match means no pairing.
_TICKET_RE = re.compile(r"\d{6,}")


def _pair_key(name: str) -> frozenset[str]:
    return frozenset(_TICKET_RE.findall(canonical_document_name(name)))


def document_stem(name: str) -> str:
    """Canonical stem: canonical name minus the extension."""
    canonical = canonical_document_name(name)
    return re.sub(r"\.[^.]+$", "", canonical).strip()


def pair_sttm_with_frd(sttm_names: list[str], frd_names: list[str],
                       explicit_map: dict[str, str] | None = None) -> dict[str, str]:
    """{sttm name -> companion frd name}. Precedence: the EXPLICIT pairing
    map (canonical stems, from config — ships the MIDS pair) first, then a
    shared ticket number where exactly one FRD matches exactly one STTM.
    Ambiguity pairs nothing — conservative by design. The ≥3-token stem
    heuristic lives in ``suggest_pairs`` and is a UI SUGGESTION only,
    never an automatic pairing."""
    explicit_map = {document_stem(k): document_stem(v)
                    for k, v in (explicit_map or {}).items()}
    frd_by_stem = {document_stem(f): f for f in frd_names}
    explicit_pairs: dict[str, str] = {}
    for sttm in sttm_names:
        mapped = explicit_map.get(document_stem(sttm))
        if mapped and mapped in frd_by_stem:
            explicit_pairs[sttm] = frd_by_stem[mapped]
    remaining_sttm = [s for s in sttm_names if s not in explicit_pairs]
    remaining_frd = [f for f in frd_names
                     if f not in set(explicit_pairs.values())]
    return {**explicit_pairs,
            **_pair_by_ticket(remaining_sttm, remaining_frd)}


# -- the name key (2026-10-13) ------------------------------------------------ #
# A document's NAME as a set of content tokens: lowercased, split on any run of
# whitespace _ - . , the role tokens dropped WHEREVER they sit (a client names
# its FRD "<title>_FRD.docx" as readily as "FRD_<title>.docx"). The old rule
# compared the first three tokens only — every file of a vendor's family shares
# them ("Pyx_ Care Management …"), so a sibling feed made the match ambiguous
# and a different one could pair the wrong documents.

ROLE_TOKENS = frozenset({"frd", "sttm", "vdd", "iig"})
NAME_FUZZY_THRESHOLD = 0.8      # config: inputs.pairing.name_fuzzy_threshold
_NAME_SPLIT = re.compile(r"[\s_\-.]+")
_STEM_MIN = 4                   # the stem rule codegen.pairing._name_match uses


def _raw_tokens(name: str) -> list[str]:
    # ".contract.json" is a double extension, not content.
    stem = re.sub(r"\.contract$", "", document_stem(name))
    return [t for t in _NAME_SPLIT.split(stem) if t]


def document_roles(name: str) -> frozenset[str]:
    """The role tokens (frd / sttm / vdd / iig) a document name carries,
    anywhere in it."""
    return frozenset(t for t in _raw_tokens(name) if t in ROLE_TOKENS)


@dataclass(frozen=True)
class RoleVerdict:
    """A document's role by NAME — ``frd`` | ``sttm`` | ``vdd`` | ``iig`` |
    ``unclassified`` — and the rule that assigned it (shown in the App's
    pairing diagnostic and printed by ``codegen pair``)."""

    role: str
    rule: str


_noted_two_roles: set[str] = set()


def classify_document_name(name: str) -> RoleVerdict:
    """The role a document's name states: a role token ANYWHERE in it
    ("Pyx_ … DSNP_FRD.docx" is an FRD as surely as "FRD_….docx"). An ``iig``
    token always makes it an IIG — a validation golden, never an input. Two
    of frd / sttm / vdd: the first one (the prefix) decides, with a NOTE. A
    ``.contract.json`` is an FRD contract whatever its name. No token:
    ``unclassified`` (content may still decide where the caller reads it)."""
    tokens = _raw_tokens(name)
    if name.lower().endswith(".contract.json"):
        return RoleVerdict("frd", "FRD contract JSON (.contract.json)")
    if "iig" in tokens:
        return RoleVerdict("iig", "token 'iig' in the name: a validation golden, never an input")
    roles = list(dict.fromkeys(t for t in tokens if t in ROLE_TOKENS))
    if not roles:
        return RoleVerdict("unclassified", "no frd / sttm / vdd / iig token in the name")
    if len(roles) == 1:
        return RoleVerdict(roles[0], f"token {roles[0]!r} in the name")
    rule = (f"tokens {', '.join(repr(r) for r in roles)} in the name — the first "
            f"(prefix) decides: {roles[0]!r}")
    if name not in _noted_two_roles:
        _noted_two_roles.add(name)
        _log.info("NOTE %s carries two role tokens; %s", name, rule)
    return RoleVerdict(roles[0], rule)


def name_tokens(name: str) -> tuple[str, ...]:
    """The content tokens of a document name, in order (role tokens dropped)."""
    return tuple(t for t in _raw_tokens(name) if t not in ROLE_TOKENS)


def pairing_key(name: str) -> str:
    """THE pairing key: the content tokens joined. Two documents of one pair
    usually share it exactly ("STTM_Pyx_Care_Management_Data_MI_DSNP.xlsx" and
    "Pyx_ Care Management Data MI DSNP_FRD.docx")."""
    return " ".join(name_tokens(name))


def _same_word(a: str, b: str) -> bool:
    """Equal, or — both alphabetic and at least ``_STEM_MIN`` long — one is a
    prefix of the other ("social" / "socially", "determine" / "determined")."""
    if a == b:
        return True
    return (a.isalpha() and b.isalpha() and min(len(a), len(b)) >= _STEM_MIN
            and (a.startswith(b) or b.startswith(a)))


def name_overlap(a: str, b: str) -> tuple[float, list[tuple[str, str]]]:
    """Token-set overlap (Jaccard) of two names' content tokens, and the word
    pairs matched by STEM only. A token pairs with at most one token of the
    other name, exact matches first, then whole-word prefix ("social" /
    "socially" — never a merely common prefix: "medicare" / "medicaid").
    0.0 when either name has no content token."""
    left, right = sorted(set(name_tokens(a))), sorted(set(name_tokens(b)))
    if not left or not right:
        return 0.0, []
    total = len(left) + len(right)
    unmatched = list(right)
    shared = 0
    stems: list[tuple[str, str]] = []
    for exact in (True, False):
        for token in list(left):
            hit = next((t for t in unmatched
                        if (t == token if exact else _same_word(t, token))), None)
            if hit is not None:
                unmatched.remove(hit)
                left.remove(token)
                shared += 1
                if not exact:
                    stems.append((token, hit))
    return shared / (total - shared), stems


def name_similarity(a: str, b: str) -> float:
    return name_overlap(a, b)[0]


@dataclass(frozen=True)
class NameMatch:
    """What the NAMES say about one STTM's companion: ``chosen`` with ``rule``
    ``name_key`` (exact key) or ``name_fuzzy`` (overlap at or above the
    threshold, unique), else None; ``reason`` names the files and why."""

    chosen: str | None
    rule: str | None
    similarity: float
    reason: str


def match_by_name(sttm_name: str, candidate_names: list[str],
                  threshold: float = NAME_FUZZY_THRESHOLD) -> NameMatch:
    """Exact key first (exactly one candidate shares it); else the unique
    candidate whose overlap reaches ``threshold``. Two or more at the same
    level, or none at the threshold: nothing is chosen — the caller asks."""
    candidates = [c for c in candidate_names if c != sttm_name]
    key = pairing_key(sttm_name)
    if not key:
        return NameMatch(None, None, 0.0, f"{sttm_name!r} has no content token to pair on")
    exact = [c for c in candidates if pairing_key(c) == key]
    if len(exact) == 1:
        return NameMatch(exact[0], "name_key", 1.0,
                         f"paired by key: {sttm_name!r} and {exact[0]!r} share the key {key!r}")
    if exact:
        return NameMatch(None, None, 1.0, f"{len(exact)} candidates share the key {key!r}: "
                         + ", ".join(repr(c) for c in exact))
    scores = sorted(((name_similarity(sttm_name, c), c) for c in candidates),
                    key=lambda sc: (-sc[0], sc[1]))
    above = [(s, c) for s, c in scores if s >= threshold]
    if len(above) == 1:
        score, chosen = above[0]
        stems = name_overlap(sttm_name, chosen)[1]
        stem_text = ("; stem-matched: " + ", ".join(f"{a!r} ~ {b!r}" for a, b in stems)
                     if stems else "")
        return NameMatch(chosen, "name_fuzzy", score, (
            f"paired by fuzzy: {sttm_name!r} and {chosen!r} — token overlap {score:.2f} "
            f"≥ {threshold:g} (tokens {' '.join(name_tokens(sttm_name))!r} vs "
            f"{' '.join(name_tokens(chosen))!r}{stem_text}); no exact key match"))
    if above:
        return NameMatch(None, None, above[0][0], (
            f"{len(above)} candidates overlap the name at ≥ {threshold:g}: "
            + ", ".join(f"{c!r} ({s:.2f})" for s, c in above)))
    best = scores[0] if scores else (0.0, None)
    return NameMatch(None, None, best[0], (
        f"no name matches {sttm_name!r}: best overlap {best[0]:.2f}"
        + (f" ({best[1]!r})" if best[1] else "") + f" is below the threshold {threshold:g}"))


def suggest_pairs(sttm_names: list[str], frd_names: list[str],
                  threshold: float = NAME_FUZZY_THRESHOLD) -> dict[str, str]:
    """UI-suggestion-only heuristic: the name match (exact key, else a unique
    overlap at the threshold), uniqueness-constrained both ways; ambiguity =
    no suggestion. NEVER used to auto-pair — the person confirms with a click."""
    suggestions: dict[str, str] = {}
    claimed: dict[str, str] = {}
    for sttm in sttm_names:
        frd = match_by_name(sttm, frd_names, threshold).chosen
        if frd is None:
            continue
        if frd in claimed:
            suggestions.pop(claimed[frd], None)
            continue
        claimed[frd] = sttm
        suggestions[sttm] = frd
    return suggestions


def auto_pair_document(sttm_name: str, candidate_names: list[str],
                       explicit_map: dict[str, str] | None = None,
                       threshold: float = NAME_FUZZY_THRESHOLD) -> tuple[str, str] | None:
    """The companion document (FRD or VDD) to select automatically when
    ``sttm_name`` is chosen, with the rule that decided it: ``pairing_map``
    (config, canonical stems) -> ``ticket`` (a shared 6+-digit number) ->
    ``name_key`` (the same pairing key) -> ``name_fuzzy`` (the unique token
    overlap at or above ``threshold``). Ambiguity or no match -> None: the
    person picks. (2026-09-18: pairing became automatic at selection time;
    the chooser still lets the person override it.)"""
    candidates = [c for c in candidate_names if c != sttm_name]
    explicit = {document_stem(k): document_stem(v) for k, v in (explicit_map or {}).items()}
    by_stem_name = {document_stem(c): c for c in candidates}
    mapped = explicit.get(document_stem(sttm_name))
    if mapped and mapped in by_stem_name:
        return by_stem_name[mapped], "pairing_map"
    by_ticket = _pair_by_ticket([sttm_name], candidates)
    if sttm_name in by_ticket:
        return by_ticket[sttm_name], "ticket"
    match = match_by_name(sttm_name, candidates, threshold)
    if match.chosen is not None:
        return match.chosen, match.rule
    return None


auto_pair_frd = auto_pair_document
auto_pair_vdd = auto_pair_document


def _pair_by_ticket(sttm_names: list[str], frd_names: list[str]) -> dict[str, str]:
    """Ticket-number pairing (the pre-map behaviour), same conservatism."""
    frd_by_ticket: dict[str, list[str]] = {}
    for frd in frd_names:
        for ticket in _pair_key(frd):
            frd_by_ticket.setdefault(ticket, []).append(frd)
    pairs: dict[str, str] = {}
    claimed: dict[str, str] = {}
    for sttm in sttm_names:
        candidates = {
            frd
            for ticket in _pair_key(sttm)
            for frd in frd_by_ticket.get(ticket, [])
        }
        if len(candidates) != 1:
            continue
        frd = next(iter(candidates))
        if frd in claimed:  # two STTMs claiming one FRD → drop both
            pairs.pop(claimed[frd], None)
            continue
        claimed[frd] = sttm
        pairs[sttm] = frd
    return pairs


# -- reference documents ----------------------------------------------------- #


def input_document_dirs(config: Config, base_dir: Path, env=None) -> list[Path]:
    """Directories scanned for reference documents, env > YAML.

    ``CODEGEN_INPUT_DOCS_DIR`` is split on ``os.pathsep`` (``:`` on POSIX,
    ``;`` on Windows — a bare ``:`` split would break ``C:\\`` drive paths).
    Relative entries resolve against ``base_dir`` (the repo root).
    """
    env = os.environ if env is None else env
    raw = env.get("CODEGEN_INPUT_DOCS_DIR", "")
    entries = (
        [e for e in raw.split(os.pathsep) if e.strip()]
        if raw
        else list(config.demo.input_documents.dirs)
    )
    resolved = []
    for entry in entries:
        path = Path(entry)
        resolved.append(path if path.is_absolute() else base_dir / path)
    return resolved


def scan_reference_documents(config: Config, base_dir: Path, env=None) -> dict:
    """Expected vs present vs missing, matched by canonicalized file name.

    ``present`` entries carry the resolved local path for the backend's own
    use (the convention-check reader); the UI shows names only.
    """
    found: dict[str, Path] = {}
    for directory in input_document_dirs(config, base_dir, env):
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file():
                found.setdefault(_canonical_name(path.name), path)

    present: list[dict] = []
    missing: list[str] = []
    for name in config.demo.input_documents.expected:
        match = found.get(_canonical_name(name))
        if match is not None:
            present.append({"name": name, "path": str(match)})
        else:
            missing.append(name)
    return {
        "expected": list(config.demo.input_documents.expected),
        "present": present,
        "missing": missing,
    }


# -- source files per feed ---------------------------------------------------- #


def _target_display(target: TargetSpec | None) -> str | None:
    if target is None or not target.tables:
        return None
    schema = target.schema_name
    return ", ".join(f"{schema}.{t}" if schema else t for t in target.tables)


def feed_source_files(feed: FrdFeed, config: Config) -> dict:
    """One feed's row for the "source files this run will read" panel.

    The landing root comes from the contract when stated; a null
    ``landing_location`` is synthesized from the template and flagged, with
    null domain/sub_domain falling back to ``unknown_domain`` /
    ``unknown_subdomain`` (still flagged). Slugging reuses the resolver's
    ``normalize_feed_name`` rule. The load strategy is always the config
    stand-in and always flagged.
    """
    sf = config.demo.source_files
    if feed.landing_location:
        landing = {"value": feed.landing_location.replace("\\", "/"), "synthetic": False}
    else:
        landing = {
            "value": sf.landing_root_template.format(
                domain=normalize_feed_name(feed.domain) if feed.domain else "unknown_domain",
                sub_domain=(
                    normalize_feed_name(feed.sub_domain)
                    if feed.sub_domain
                    else "unknown_subdomain"
                ),
                source_system=normalize_feed_name(feed.source_system),
            ),
            "synthetic": True,
        }
    return {
        "feed_name": feed.feed_name,
        "landing_root": landing,
        "file_name_patterns": list(feed.file_name_patterns),
        "file_format": feed.file_format,
        "delimiter": feed.delimiter,
        "frequency": feed.frequency,
        "stage_target": _target_display(feed.stage_target),
        "standard_target": _target_display(feed.standard_target),
        "load_strategy": {
            "stage": sf.load_strategy.stage,
            "standard": sf.load_strategy.standard,
            "synthetic": True,
        },
    }


def shell_listing(feed_rows: list[dict], config: Config) -> list[str]:
    """The SYNTHETIC ``databricks fs ls`` block — the offline fallback.

    Rendered server-side so no path logic lives in TypeScript. Date
    placeholders in the file patterns stay as-is. The live twin is
    ``live_shell_listing`` below; ``resolve_shell_listing`` picks per
    ``demo.shell_listing`` (live | synthetic | auto) and labels honestly.
    """
    db = config.demo.databricks_paths
    lines: list[str] = []
    for row in feed_rows:
        root = row["landing_root"]["value"].strip("/")
        lines.append(
            f"$ databricks fs ls dbfs:/Volumes/{db.catalog}/{db.schema_name}/{db.volume}/{root}/"
        )
        if row["file_name_patterns"]:
            lines.extend(row["file_name_patterns"])
        else:
            lines.append("(no file name patterns in the FRD)")
    return lines


# -- live shell listing (the seam's landing volume) --------------------------- #

# auto-mode existence probe cache: one workspace round-trip per minute, max.
_LANDING_PROBE_CACHE: dict = {"key": None, "at": 0.0, "ok": False, "reason": ""}
_LANDING_PROBE_TTL_SECONDS = 60.0


def _landing_available(config: Config) -> tuple[bool, str]:
    """(available, reason) — creds resolve AND the landing volume exists."""
    import time

    from codegen.databricks import (
        DatabricksConfigError,
        config_for,
        landing_volume_exists,
    )

    try:
        cfg = config_for(config.databricks)
        key = f"{cfg.catalog}.{cfg.schema}.{cfg.landing_volume}"
    except DatabricksConfigError as exc:
        return False, str(exc).split(".")[0]
    now = time.time()
    if (_LANDING_PROBE_CACHE["key"] == key
            and now - _LANDING_PROBE_CACHE["at"] < _LANDING_PROBE_TTL_SECONDS):
        return _LANDING_PROBE_CACHE["ok"], _LANDING_PROBE_CACHE["reason"]
    try:
        ok = landing_volume_exists(cfg)
        reason = "" if ok else f"volume {key} does not exist"
    except Exception as exc:  # noqa: BLE001 — incl. raw SDK auth errors: the
        # probe must degrade to synthetic, never surface a 500.
        ok, reason = False, str(exc).splitlines()[0][:120]
    _LANDING_PROBE_CACHE.update(key=key, at=now, ok=ok, reason=reason)
    return ok, reason


def live_shell_listing(feed_rows: list[dict], config: Config) -> tuple[list[str], str]:
    """The REAL listing, grouped under each feed's landing root.

    Returns (lines, volume full name); raises on any seam problem — the
    caller decides how to fall back, never this function.
    """
    from codegen.databricks import config_for, list_landing

    cfg = config_for(config.databricks)
    entries = list_landing(cfg)
    db = config.demo.databricks_paths
    root = f"dbfs:/Volumes/{db.catalog}/{db.schema_name}/{db.volume}"

    lines: list[str] = []
    claimed: set[str] = set()
    for row in feed_rows:
        prefix = row["landing_root"]["value"].strip("/")
        lines.append(f"$ databricks fs ls {root}/{prefix}/")
        matching = [e for e in entries if e["path"].startswith(prefix + "/")]
        for entry in matching:
            claimed.add(entry["path"])
            lines.append(f"{entry['name']}  {entry['size']:,} B  {entry['modified']}")
        if not matching:
            lines.append("(empty)")
    leftovers = [e for e in entries if e["path"] not in claimed]
    if leftovers:
        lines.append(f"$ databricks fs ls {root}/")
        for entry in leftovers:
            lines.append(f"{entry['path']}  {entry['size']:,} B  {entry['modified']}")
    return lines, f"{db.catalog}.{db.schema_name}.{db.volume}"


def resolve_shell_listing(feed_rows: list[dict], config: Config,
                          mode: str | None = None) -> dict:
    """{lines, mode, reason, source, listed_at} per demo.shell_listing.

    live: real listing or a LOUD-but-graceful synthetic fallback with the
    one-line reason. auto: live only when creds resolve and the volume
    exists (cached probe). synthetic: the offline renderer, as before.
    """
    from datetime import datetime

    requested = mode or config.demo.shell_listing
    result = {
        "lines": shell_listing(feed_rows, config),
        "mode": "synthetic",
        "reason": None,
        "source": None,
        "listed_at": None,
    }
    if requested == "synthetic":
        return result
    if requested == "auto":
        available, reason = _landing_available(config)
        if not available:
            result["reason"] = reason or "landing volume unavailable"
            return result
    try:
        lines, source = live_shell_listing(feed_rows, config)
    except Exception as exc:  # noqa: BLE001 — one-line reason, never a stack trace
        result["reason"] = str(exc).splitlines()[0][:160]
        return result
    return {
        "lines": lines,
        "mode": "live",
        "reason": None,
        "source": source,
        "listed_at": datetime.now().strftime("%H:%M:%S"),
    }


# -- live convention check from the real FRD docx ----------------------------- #

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Structural Metadata labels (FRD template field names, not client data),
# squashed to alphanumerics for matching against merged/split table cells.
_CONVENTION_FIELDS = {
    "adlslocation": "adls_location",
    "targetschema": "target_schema",
    "loadstrategystg": "load_strategy_stg",
    "loadstrategystd": "load_strategy_std",
    "objectdataformat": "object_format",
}


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def read_docx_label_values(docx_path: Path) -> dict[str, str] | None:
    """Every table cell's (squashed label → next-cell text), first wins.

    The generic reader behind document-level checks: FRD metadata tables are
    label/value rows, so downstream callers can ask "does the document carry
    a non-empty value under this label?" without knowing the table layout.
    Returns None when the file cannot be parsed (same posture as
    ``read_frd_convention``)."""
    try:
        with zipfile.ZipFile(docx_path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError):
        return None

    def cell_text(tc) -> str:
        paragraphs = (
            "".join(t.text or "" for t in p.iter(f"{_W}t")) for p in tc.iter(f"{_W}p")
        )
        return re.sub(r"\s+", " ", " ".join(paragraphs)).strip()

    values: dict[str, str] = {}
    for row in root.iter(f"{_W}tr"):
        cells = [cell_text(tc) for tc in row.iter(f"{_W}tc")]
        for i, cell in enumerate(cells[:-1]):
            key = _squash(cell)
            if key and key not in values:
                values[key] = cells[i + 1]
    return values


def read_frd_convention(docx_path: Path) -> dict | None:
    """Read Structural Metadata values live from the FRD .docx (stdlib only).

    Returns None when the file cannot be parsed — this backs a display-only
    bonus block, and a corrupt document must not take the panel down. Word
    splits text into arbitrary runs, so cell text is the run texts joined
    with no separator, whitespace-collapsed. The document repeats its
    template tables in a "Do Not Use" section; first occurrence wins.
    """
    try:
        with zipfile.ZipFile(docx_path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError):
        return None

    def cell_text(tc) -> str:
        # Runs join with no separator (Word splits words across runs);
        # paragraphs within a cell join with a space.
        paragraphs = (
            "".join(t.text or "" for t in p.iter(f"{_W}t")) for p in tc.iter(f"{_W}p")
        )
        return re.sub(r"\s+", " ", " ".join(paragraphs)).strip()

    values: dict[str, str] = {}
    for row in root.iter(f"{_W}tr"):
        cells = [cell_text(tc) for tc in row.iter(f"{_W}tc")]
        for i, cell in enumerate(cells[:-1]):
            field = _CONVENTION_FIELDS.get(_squash(cell))
            if field is not None and cells[i + 1]:
                values.setdefault(field, cells[i + 1])
    if not values:
        return None
    return {"source": docx_path.name, **values}


# -- the one payload both the endpoint and the CLI serve ---------------------- #


def source_files_payload(config: Config, base_dir: Path, env=None,
                         shell_mode: str | None = None) -> dict:
    """The source-files payload (the App route was removed 2026-10-16); printed by
    ``codegen demo-source-files``. Contract/docx reads are local;
    ``shell_mode`` (None = config's demo.shell_listing) may add ONE
    workspace listing call for the live shell block — the CLI pins
    "synthetic" to stay offline."""
    frd_path = base_dir / config.contracts.dir / config.demo.frd
    if not frd_path.is_file():
        raise FileNotFoundError(f"demo FRD contract not found: {frd_path}")
    contract = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))
    feed_rows = [feed_source_files(feed, config) for feed in contract.feeds]

    convention = None
    documents = scan_reference_documents(config, base_dir, env)
    frd_docx = find_frd_docx(documents["present"])
    if frd_docx is not None:
        convention = read_frd_convention(Path(frd_docx["path"]))

    shell = resolve_shell_listing(feed_rows, config, mode=shell_mode)
    return {
        "frd_contract": Path(config.demo.frd).name,
        "feeds": feed_rows,
        "shell_listing": shell["lines"],
        "shell_mode": shell["mode"],
        "shell_reason": shell["reason"],
        "shell_source": shell["source"],
        "shell_listed_at": shell["listed_at"],
        "convention_check": convention,
    }
