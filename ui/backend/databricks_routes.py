"""Databricks volumes routes: list the client's raw documents, fetch one.

Mirrors the SharePoint routes' posture: a fetched document lands in
``inputs/databricks/`` — a scanned input directory — so it starts through
the EXISTING generate path (the STTM chooser, the documents card). There is
deliberately no second "generate from Databricks" execution path. Status
codes say whose problem it is: 503 not configured (the panel renders
nothing), 502 the workspace refused, 400 bad request. Read-only: list and
download; nothing here writes to the workspace.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from codegen.databricks import (
    DatabricksConfigError,
    DatabricksTransportError,
    config_for,
    fetch_document,
    list_documents,
)
from codegen.demo_sources import canonical_document_name, pair_sttm_with_frd

router = APIRouter(prefix="/api/databricks")

_store = None
REPO_ROOT = Path(__file__).resolve().parents[2]
FETCH_DIR = REPO_ROOT / "inputs" / "databricks"


def bind_store(store) -> None:
    global _store  # noqa: PLW0603 — same binding pattern as sharepoint_routes
    _store = store


def _config():
    if _store is None:
        raise HTTPException(503, "pipeline unavailable")
    try:
        return config_for(_store.config.databricks)
    except DatabricksConfigError as exc:
        raise HTTPException(503, str(exc)) from exc


def _local_index() -> dict[str, tuple[str, int]]:
    """canonical name -> (local file name, size) across every input dir the
    STTM chooser's local scan covers, so the volumes list can be deduped
    SERVER-SIDE against what is already on disk."""
    directories = [
        FETCH_DIR,
        REPO_ROOT / "inputs" / "sharepoint",
        (REPO_ROOT / _store.config.demo.workbook).parent if _store else None,
    ]
    index: dict[str, tuple[str, int]] = {}
    for directory in directories:
        if directory is None or not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and not path.name.startswith("~$"):
                index.setdefault(
                    canonical_document_name(path.name),
                    (path.name, path.stat().st_size),
                )
    return index


def _annotate(entry: dict, local: dict[str, tuple[str, int]]) -> dict:
    """fetched (local copy matches) | differs (size mismatch — Re-fetch) |
    fetchable (no local copy)."""
    match = local.get(canonical_document_name(entry["name"]))
    if match is None:
        return {**entry, "state": "fetchable"}
    local_name, local_size = match
    state = "fetched" if local_size == entry["size"] else "differs"
    return {**entry, "state": state, "local_name": local_name}


@router.get("/documents")
def documents() -> dict:
    cfg = _config()
    try:
        listing = list_documents(cfg)
    except DatabricksTransportError as exc:
        raise HTTPException(502, str(exc)) from exc
    local = _local_index()
    sttm = [_annotate(e, local) for e in listing.get("sttm", [])]
    frd = [_annotate(e, local) for e in listing.get("frd", [])]
    # Conservative STTM↔FRD pairing by shared ticket number (no match →
    # no pairing) so the chooser can say "includes companion FRD".
    pairs = pair_sttm_with_frd([e["name"] for e in sttm], [e["name"] for e in frd])
    for entry in sttm:
        companion = pairs.get(entry["name"])
        if companion:
            entry["companion_frd"] = companion
    paired_frds = set(pairs.values())
    for entry in frd:
        entry["paired"] = entry["name"] in paired_frds
    return {
        "catalog": cfg.catalog,
        "schema": cfg.schema,
        "documents": {"sttm": sttm, "frd": frd},
    }


class FetchRequest(BaseModel):
    volume: str
    name: str


@router.post("/fetch")
def fetch(req: FetchRequest) -> dict:
    cfg = _config()
    if req.volume not in (cfg.frd_volume, cfg.sttm_volume):
        raise HTTPException(400, f"unknown volume {req.volume!r}")
    try:
        local = fetch_document(cfg, req.volume, req.name, FETCH_DIR)
    except DatabricksTransportError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"fetched": local.name, "dest": "inputs/databricks"}
