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


# --- human-gated artifact publish (the outbound half, added 2026-08-28) --- #
#
# The UC twin of the SharePoint publish gate: the reviewer picks the target
# catalog.schema.volume in the UI, confirms, and ONE feed's artifacts land
# under <volume>/<feed_slug>/. Same doctrine as sharepoint_publish: confirm
# required, one feed per call, never a side effect of generating. Code-level
# policy (codegen.databricks.WRITABLE_PREFIX) refuses any target outside the
# sanctioned prefix, whatever the picker says.


@router.get("/publish-target")
def publish_target() -> dict:
    """Defaults + availability for the publish panel.

    Always answers (the panel renders the picker even when publishing cannot
    work yet) — `available` + `reason` say whether a publish would succeed.
    """
    from codegen.databricks import WRITABLE_PREFIX

    if _store is None:
        return {"available": False, "reason": "pipeline unavailable",
                "writable_prefix": WRITABLE_PREFIX}
    try:
        cfg = config_for(_store.config.databricks)
    except DatabricksConfigError as exc:
        return {"available": False, "reason": str(exc),
                "writable_prefix": WRITABLE_PREFIX}
    return {
        "available": True,
        "reason": "",
        "catalog": cfg.catalog,
        "schema": cfg.schema,
        "volume": cfg.output_volume or "",
        "writable_prefix": WRITABLE_PREFIX,
    }


class PublishRequest(BaseModel):
    confirm: bool = False
    feed_slug: str
    catalog: str = ""
    schema_name: str = ""
    volume: str = ""
    force: bool = False


def _volume_publishable(store, feed_slug: str) -> list[Path]:
    """Everything a volume publish uploads: the report (required), the
    assembled notebook when notebook mode produced one, and the framework
    artefacts when framework mode did. Addressed through the CURRENT mode's
    roots, same as the SharePoint gate."""
    feed_dir = (store.out_root / feed_slug).resolve()
    candidates = [
        (store.reports_root / f"{feed_slug}.md").resolve(),
        feed_dir / f"{feed_slug}.ipynb",
    ]
    framework_dir = feed_dir / "framework"
    if framework_dir.is_dir():
        candidates.extend(sorted(p for p in framework_dir.iterdir() if p.is_file()))
    return [p for p in candidates if p.is_file()]


@router.post("/publish")
def publish(req: PublishRequest) -> dict:
    from codegen.databricks import ensure_volume, publish_artifacts

    if req.confirm is not True:
        raise HTTPException(
            400,
            'publishing writes to a Unity Catalog volume and requires an '
            'explicit {"confirm": true}',
        )
    if _store is None:
        raise HTTPException(503, "pipeline unavailable")
    if req.feed_slug not in _store.runs:
        raise HTTPException(404, f"no generated feed named {req.feed_slug!r}")
    cfg = _config()
    artifacts = _volume_publishable(_store, req.feed_slug)
    if not artifacts:
        raise HTTPException(
            404,
            f"nothing to publish for {req.feed_slug!r} — generate the feed first",
        )
    try:
        target = ensure_volume(
            cfg,
            volume=req.volume or cfg.output_volume,
            knob="output_volume",
            catalog=req.catalog,
            schema=req.schema_name,
        )
        published = publish_artifacts(
            cfg, req.feed_slug, artifacts,
            catalog=req.catalog, schema=req.schema_name, volume=req.volume,
            force=req.force,
        )
    except DatabricksConfigError as exc:
        # Includes the WRITABLE_PREFIX refusal: the picker asked for a
        # target policy forbids — that is the caller's request to fix (400),
        # not a missing configuration (503).
        raise HTTPException(400, str(exc)) from exc
    except DatabricksTransportError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        "published": True,
        "volume": target["full_name"],
        "volume_created": target["created"],
        "artifacts": published,
    }
