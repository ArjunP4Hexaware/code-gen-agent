"""Proposed vocabulary, approved once (post174; docs/PARSER_SELF_EXTENSION.md step 2).

Soham: "I cannot viably manage a solution every single time I need to extend the
parser." When a person answers a question with a value that a cell the FRD reader
REFUSED already states - on one of its "<label>: <value>" lines - the run proposes that
label for the field (the label as the document writes it, the cell's coordinates). A
person approves it once on the dev App; from the next run on, on BOTH Apps, the reader
reads that label itself (``extractor.frd.cell_line_labels``). Nothing is applied until
approved; a rejected proposal is never proposed again.

Where it lives: the shared state root (``CODEGEN_STATE_DIR``, ``config.state_root()``),
``vocabulary/proposals.json`` + ``vocabulary/approved.yaml`` - written through the storage
backend of that root (the Apps read a mirror of it, refreshed before every run).
Only the FRD and the STTM are ever read; a proposal carries no cell value, only the
label, the field and the coordinates.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path

import yaml

FOLDER = "vocabulary"
PROPOSALS = f"{FOLDER}/proposals.json"
APPROVED = f"{FOLDER}/approved.yaml"
# the fields a proposal may name: the post172 labelled-lines reader's
LINE_FIELDS = ("file_format", "frequency", "source_system", "delimiter")
_PAIR = re.compile(r"^\s*([^:]{1,60}?)\s*:\s*(.*)$")
_FEED = re.compile(r"^feeds\[\d+\]\.")


def _words(text) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).split())


def proposal_id(field: str, label: str) -> str:
    return hashlib.sha256(f"{field}\0{_words(label)}".encode()).hexdigest()[:12]


def propose(frd_contract: dict | None, gaps: Mapping | None, *, run: str = "",
            known: Mapping[str, list[str]] | None = None) -> list[dict]:
    """The proposals a run's answers make: for each answered ``feeds[i].<field>`` (a
    LINE_FIELDS field), the refused multi-line FRD cell of that field whose
    "<label>: <value>" line states the answer word for word -> {id, field, label,
    cell, run}. A label already ``known`` for the field proposes nothing."""
    structured = (frd_contract or {}).get("structured") or {}
    out: dict[str, dict] = {}
    for key, choice in (gaps or {}).items():
        answer = choice.get("value") if isinstance(choice, dict) else choice
        field = _FEED.sub("", str(key))
        if field not in LINE_FIELDS or not _words(answer):
            continue
        own = structured.get(key) or structured.get(_FEED.sub("feeds[0].", str(key)))
        # a field with no refused cell of its own (the delimiter has no FRD row) is
        # looked for in the feed's other refused multi-line cells
        prefix = str(key)[: len(str(key)) - len(field)]
        cells = [own] if isinstance(own, dict) else [
            v for k, v in structured.items()
            if isinstance(v, dict) and (k.startswith(prefix) or k.startswith("feeds[0]."))]
        for refused in cells:
            if refused.get("kind") != "multiline":
                continue
            out.update({p["id"]: p for p in _line_proposals(refused, field, answer, run, known)
                        if p["id"] not in out})
    return list(out.values())


def _line_proposals(refused: dict, field: str, answer, run: str,
                    known: Mapping[str, list[str]] | None) -> list[dict]:
    """The proposals one refused cell's "<label>: <value>" lines make for ``field``."""
    known_words = {_words(k) for k in (known or {}).get(field, [])}
    out = []
    for line in str(refused.get("text") or "").splitlines():
        match = _PAIR.match(line)
        if match is None or _words(answer) not in _words(match.group(2)):
            continue
        label = match.group(1).strip()
        if _words(label) in known_words:
            continue
        out.append({
            "id": proposal_id(field, label), "field": field, "label": label, "run": run,
            "cell": (f"FRD table {refused.get('table')} row {refused.get('row')} "
                     f"({refused.get('label')!r})")})
    return out


# -- the shared files --------------------------------------------------------------

def state_backend(config):
    """The storage backend of the shared state root (writable): the remote folder
    CODEGEN_STATE_DIR names on an App, the local folder elsewhere."""
    from codegen.config import STATE_DIR_ENV, state_root
    from codegen.storage import default_client_factory, open_backend

    value = (os.environ.get(STATE_DIR_ENV) or "").rstrip("/")
    if value.startswith("/Workspace/"):
        uri = f"workspace:{value}"
    elif value.startswith("/Volumes/") and not Path(value).is_dir():
        uri = f"volume:{value}"
    else:
        uri = f"local:{state_root().resolve().as_posix()}"
    return open_backend(uri, base_dir=Path.cwd(), client_factory=default_client_factory(config),
                        create_root=uri.startswith("local:"))


def _read(backend, rel: str) -> bytes | None:
    try:
        return backend.read_bytes(rel)
    except Exception:  # noqa: BLE001 - absent = empty
        return None


def load(backend) -> dict:
    """``{"proposals": [...], "approved": {field: [labels]}, "rejected": [ids]}``."""
    data = json.loads((_read(backend, PROPOSALS) or b"{}").decode("utf-8") or "{}")
    approved = yaml.safe_load((_read(backend, APPROVED) or b"").decode("utf-8")) or {}
    return {"proposals": list(data.get("proposals") or []),
            "rejected": list(data.get("rejected") or []),
            "approved": dict(approved.get("cell_line_labels") or {})}


def _save(backend, state: dict) -> None:
    backend.write_bytes(PROPOSALS, (json.dumps(
        {"proposals": state["proposals"], "rejected": sorted(set(state["rejected"]))},
        indent=2, sort_keys=True) + "\n").encode("utf-8"))
    backend.write_bytes(APPROVED, yaml.safe_dump(
        {"cell_line_labels": {f: sorted(set(v)) for f, v in sorted(state["approved"].items())
                              if v}}, sort_keys=True).encode("utf-8"))


def record(backend, proposals: list[dict]) -> list[dict]:
    """Add the new ones (never an approved, pending or rejected one again)."""
    state = load(backend)
    seen = {p["id"] for p in state["proposals"]} | set(state["rejected"]) | {
        proposal_id(f, label) for f, labels in state["approved"].items() for label in labels}
    new = [p for p in proposals if p["id"] not in seen]
    if new:
        state["proposals"] += new
        _save(backend, state)
    return new


def decide(backend, pid: str, approve: bool) -> dict:
    """Approve (the label joins approved.yaml) or reject one pending proposal."""
    state = load(backend)
    proposal = next((p for p in state["proposals"] if p["id"] == pid), None)
    if proposal is None:
        raise KeyError(pid)
    state["proposals"] = [p for p in state["proposals"] if p["id"] != pid]
    if approve:
        state["approved"].setdefault(proposal["field"], []).append(proposal["label"])
    else:
        state["rejected"].append(pid)
    _save(backend, state)
    return proposal


def approved_labels(state_dir: Path) -> dict[str, list[str]]:
    """The approved labels as ``load_config`` merges them (read from the local state
    root / its App mirror; absent file = none)."""
    path = Path(state_dir) / APPROVED
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    labels = data.get("cell_line_labels") or {}
    return {f: [str(x) for x in v] for f, v in labels.items() if f in LINE_FIELDS and v}
