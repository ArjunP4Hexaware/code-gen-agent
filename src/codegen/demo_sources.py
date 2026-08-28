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
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed, TargetSpec
from codegen.resolve.resolver import normalize_feed_name

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
    canonical name starts with ``frd``. "Any .docx" stopped being safe the
    moment the EDO standards documents joined the expected list — they are
    reference material, never the FRD under evaluation."""
    return next(
        (
            p
            for p in present
            if p["name"].lower().endswith(".docx")
            and canonical_document_name(p["name"]).startswith("frd")
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


def _token_prefix(name: str, count: int = 3) -> tuple[str, ...]:
    tokens = [t for t in re.split(r"[\s_\-]+", document_stem(name)) if t]
    # Drop the frd/sttm role prefix so the content tokens align.
    if tokens and tokens[0] in ("frd", "sttm"):
        tokens = tokens[1:]
    return tuple(tokens[:count])


def suggest_pairs(sttm_names: list[str], frd_names: list[str]) -> dict[str, str]:
    """UI-suggestion-only heuristic: the first >=3 tokens match after
    squashing. Uniqueness-constrained both ways; ambiguity = no suggestion.
    NEVER used to auto-pair — the person confirms with a click."""
    frd_by_prefix: dict[tuple, list[str]] = {}
    for frd in frd_names:
        prefix = _token_prefix(frd)
        if len(prefix) >= 3:
            frd_by_prefix.setdefault(prefix, []).append(frd)
    suggestions: dict[str, str] = {}
    claimed: dict[str, str] = {}
    for sttm in sttm_names:
        prefix = _token_prefix(sttm)
        candidates = frd_by_prefix.get(prefix, []) if len(prefix) >= 3 else []
        if len(candidates) != 1:
            continue
        frd = candidates[0]
        if frd in claimed:
            suggestions.pop(claimed[frd], None)
            continue
        claimed[frd] = sttm
        suggestions[sttm] = frd
    return suggestions


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
    """Everything ``GET /api/demo/source-files`` returns; also printed by
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
