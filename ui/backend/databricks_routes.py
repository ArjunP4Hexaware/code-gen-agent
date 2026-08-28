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

router = APIRouter(prefix="/api/databricks")

_store = None
FETCH_DIR = Path(__file__).resolve().parents[2] / "inputs" / "databricks"


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


@router.get("/documents")
def documents() -> dict:
    cfg = _config()
    try:
        listing = list_documents(cfg)
    except DatabricksTransportError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        "catalog": cfg.catalog,
        "schema": cfg.schema,
        "documents": listing,
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
