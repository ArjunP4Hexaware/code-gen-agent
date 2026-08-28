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

# Leading numeric upload prefix some libraries prepend on upload.
_UPLOAD_PREFIX = re.compile(r"^\d+_")


def _canonical_name(name: str) -> str:
    """Case-insensitive match key with any numeric upload prefix stripped."""
    return _UPLOAD_PREFIX.sub("", name).lower()


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
    """The synthetic ``databricks fs ls`` block, one command + files per feed.

    Rendered server-side so no path logic lives in TypeScript. Date
    placeholders in the file patterns stay as-is.
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


def source_files_payload(config: Config, base_dir: Path, env=None) -> dict:
    """Everything ``GET /api/demo/source-files`` returns; also printed by
    ``codegen demo-source-files``. Loads the demo FRD contract the same way
    the resolver does; pure read, no network."""
    frd_path = base_dir / config.contracts.dir / config.demo.frd
    if not frd_path.is_file():
        raise FileNotFoundError(f"demo FRD contract not found: {frd_path}")
    contract = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))
    feed_rows = [feed_source_files(feed, config) for feed in contract.feeds]

    convention = None
    documents = scan_reference_documents(config, base_dir, env)
    frd_docx = next(
        (p for p in documents["present"] if p["name"].lower().endswith(".docx")), None
    )
    if frd_docx is not None:
        convention = read_frd_convention(Path(frd_docx["path"]))

    return {
        "frd_contract": Path(config.demo.frd).name,
        "feeds": feed_rows,
        "shell_listing": shell_listing(feed_rows, config),
        "convention_check": convention,
    }
