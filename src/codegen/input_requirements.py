"""Input-requirements check: the FRD contract vs the client requirements deck.

``FRD-and-Dictionary-Input-Requirements.pptx`` (slide 2) defines the eleven
Structural Metadata template rows an FRD must fill, each with the guidance
for filling it. This module READS THAT DECK LIVE at request time — verbatim
row names and how-to-fill text, nothing cached or committed — and evaluates
the demo FRD contract against each row: which requirements the contract
carries values for, which are empty, and which the contract shape cannot
capture at all.

This is the first reference document actually USED IN PROCESSING (the
documents card's other entries remain display-only): the check's rows come
from the document, not from code. The evaluation itself never touches
``resolve → rules → reasoning → emit → gate`` — it is a request-time input
check at the edge, and the run's verdict is unaffected.

Posture matches the convention-check reader: stdlib zip+XML, first parse
wins, and an absent or unparseable deck makes the check absent — never a
stack trace (the ACFC port reads from the client's own inputs dir).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# Paragraph markers around slide 2's requirements table: rows start after
# the last column-header cell and stop at the closing observation.
_TABLE_STARTS_AFTER = "how to fill it"
_TABLE_ENDS_BEFORE = "zero of three frds"

# Template row name (squashed) → how the FRD *contract* captures it.
# A row absent here is one the contract shape cannot capture — reported as
# ``not_captured`` rather than silently skipped.
_ROW_TO_FIELDS: dict[str, callable] = {
    "objectdataformat": lambda f: [f.file_format, f.delimiter],
    "targetschema": lambda f: [f.stage_target.schema_name,
                               f.standard_target.schema_name],
    "targettablename": lambda f: [", ".join(f.stage_target.tables) or None,
                                  ", ".join(f.standard_target.tables) or None],
    "domainandsubdomain": lambda f: [f.domain, f.sub_domain],
    "loadstrategystg": lambda f: [f.stage_target.load_strategy],
    "loadstrategystd": lambda f: [f.standard_target.load_strategy],
    "archiveschedule": lambda f: [f.archive_retention],
    "adlslocation": lambda f: [f.landing_location],
    # The deck's headline row: no FRD on hand names a vendor data
    # dictionary — they name the STTM instead, and the contract carries
    # that as sttm_reference. Treat a VDD as absent unless a future
    # contract field exists for it.
    "sourcedatadictionary": lambda f: [None],
}


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def read_requirements(pptx_path: Path) -> list[dict] | None:
    """Slide 2's requirement rows, verbatim: [{row, decides, how_to_fill}].

    Returns None when the file is absent or does not parse — display-and-
    check callers degrade to "check absent", never to an error page.
    """
    try:
        with zipfile.ZipFile(pptx_path) as archive:
            slide_names = sorted(
                (n for n in archive.namelist()
                 if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                key=lambda n: int(re.search(r"\d+", n).group()),
            )
            texts: list[str] = []
            for name in slide_names:
                root = ET.fromstring(archive.read(name))
                for paragraph in root.iter(f"{_A}p"):
                    text = "".join(
                        t.text or "" for t in paragraph.iter(f"{_A}t")
                    ).strip()
                    if text:
                        texts.append(text)
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError):
        return None

    try:
        start = next(i for i, t in enumerate(texts)
                     if _squash(t) == _squash(_TABLE_STARTS_AFTER))
        end = next(i for i, t in enumerate(texts)
                   if _squash(t).startswith(_squash(_TABLE_ENDS_BEFORE)))
    except StopIteration:
        return None

    body = texts[start + 1:end]
    if len(body) < 4 or len(body) % 4:
        return None
    rows = []
    for i in range(0, len(body), 4):
        name, decides, _filled, how = body[i:i + 4]
        rows.append({"row": name, "decides": decides, "how_to_fill": how})
    return rows or None


def _feed_status(feed: FrdFeed, row_key: str) -> str:
    extractor = _ROW_TO_FIELDS.get(row_key)
    if extractor is None:
        return "not_captured"
    values = extractor(feed)
    filled = [v for v in values if v]
    if len(filled) == len(values):
        return "filled"
    if filled:
        return "partial"
    return "missing"


def requirements_check(pptx_path: Path, contract: FrdContract) -> dict | None:
    """Evaluate every contract feed against every deck row.

    Returns {source, rows: [{row, how_to_fill, status, feeds: {name:
    status}}], summary: {filled, partial, missing, not_captured}} — or None
    when the deck is absent/unparseable. Statuses: the worst per-feed
    status wins the row ("missing" > "partial" > "filled");
    ``not_captured`` means the contract shape has no field for the row, so
    the agent flags it rather than guessing.
    """
    requirements = read_requirements(pptx_path)
    if requirements is None:
        return None

    order = {"missing": 0, "partial": 1, "filled": 2}
    rows = []
    summary = {"filled": 0, "partial": 0, "missing": 0, "not_captured": 0}
    for requirement in requirements:
        key = _squash(requirement["row"])
        if key not in _ROW_TO_FIELDS:
            status = "not_captured"
            feeds = {feed.feed_name: "not_captured" for feed in contract.feeds}
        else:
            feeds = {
                feed.feed_name: _feed_status(feed, key) for feed in contract.feeds
            }
            status = min(feeds.values(), key=lambda s: order[s])
        summary[status] += 1
        rows.append({
            "row": requirement["row"],
            "how_to_fill": requirement["how_to_fill"],
            "status": status,
            "feeds": feeds,
        })
    return {"source": pptx_path.name, "rows": rows, "summary": summary}


def document_requirements_check(pptx_path: Path, docx_path: Path) -> dict | None:
    """The REAL FRD document evaluated against the deck's requirement rows.

    Both documents are read live: the deck supplies the row names, the FRD
    docx supplies its label→value table cells (via
    ``read_docx_label_values``). A row is ``filled`` when the document
    carries a non-empty value under that label, ``missing`` when the label
    is absent or empty. Compound labels ("Domain and Sub-domain") fall back
    to their parts. Returns None when either document fails to parse."""
    from codegen.demo_sources import read_docx_label_values

    requirements = read_requirements(pptx_path)
    labels = read_docx_label_values(docx_path)
    if requirements is None or labels is None:
        return None

    def status(row_name: str) -> str:
        key = _squash(row_name)
        if key in labels:
            return "filled" if labels[key] else "missing"
        parts = [p for p in re.split(r"\band\b|/", row_name.lower()) if p.strip()]
        if len(parts) > 1:
            found = [labels.get(_squash(p), "") for p in parts if _squash(p) in labels]
            if found and len(found) == len(parts):
                return "filled" if all(found) else "partial"
            if any(found):
                return "partial"
        return "missing"

    rows = []
    summary = {"filled": 0, "partial": 0, "missing": 0}
    for requirement in requirements:
        row_status = status(requirement["row"])
        summary[row_status] += 1
        rows.append({"row": requirement["row"], "status": row_status})
    return {"source": docx_path.name, "rows": rows, "summary": summary}


def input_requirements_payload(config: Config, base_dir: Path, env=None) -> dict:
    """The endpoint payload: the deck found via the documents-card scan
    (same dirs, same matching) evaluated against the demo FRD contract —
    and, when the real FRD .docx is present, against that document too."""
    import json

    from codegen.demo_sources import scan_reference_documents

    documents = scan_reference_documents(config, base_dir, env)
    deck = next(
        (p for p in documents["present"]
         if _squash("FRD-and-Dictionary-Input-Requirements") in _squash(p["name"])),
        None,
    )
    if deck is None:
        return {"check": None, "document_check": None,
                "reason": "requirements document not present"}

    frd_path = base_dir / config.contracts.dir / config.demo.frd
    if not frd_path.is_file():
        return {"check": None, "document_check": None,
                "reason": "demo FRD contract not found"}
    contract = FrdContract.model_validate(
        json.loads(frd_path.read_text(encoding="utf-8"))
    )
    check = requirements_check(Path(deck["path"]), contract)
    if check is None:
        return {"check": None, "document_check": None,
                "reason": "requirements document did not parse"}

    # The real FRD document, when present, gets the same evaluation — the
    # deck's own "filled counts the real FRDs on hand" exercise, live.
    document_check = None
    frd_docx = next(
        (p for p in documents["present"] if p["name"].lower().endswith(".docx")), None
    )
    if frd_docx is not None:
        document_check = document_requirements_check(
            Path(deck["path"]), Path(frd_docx["path"])
        )
    return {"check": check, "document_check": document_check, "reason": None}
