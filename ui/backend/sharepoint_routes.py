"""
SharePoint document picker and publish gate for the CodeGen demo UI.

Design: SharePoint is a *source of inputs*, not a second pipeline. A picked
document is downloaded into the same local input directory a manually placed
workbook lands in, so the existing `extract-sttm` → resolve → generate path
runs it with no change to the generator. There is deliberately no separate
"generate from SharePoint" execution path to keep in sync.

Credential posture matches the rest of the app: the client secret is read
from the environment (or the gitignored `.env`), its presence is reported to
the frontend as a boolean, and the value is never returned, logged, or
echoed in an error.

This module also carries the OUTBOUND half: the confirm-gated publish
endpoint — the only way the UI ever writes to SharePoint. Publishing is
something a reviewer does on purpose, per feed, after looking at the gate
verdict; it is never a side effect of generating. See sharepoint_publish.

Failure mapping — every SharePoint failure is someone else's to fix, so the
status code says whose:
  503  not configured yet (no tenant/app registration wired)
  502  Graph refused or is unreachable (permissions, tenant, network)
  400  the request asked for something invalid (bad name, wrong type,
       a path escaping the feed dir, a publish without confirm:true)
  404  no such feed, artifact, or library document
  413  the document is larger than the input cap / Graph's simple-upload cap
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from codegen.sharepoint import (
    SUPPORTED_SUFFIXES,
    GraphError,
    SharePointConfigError,
    build_client,
    config_for,
    published_name,
)
from ui.backend.service import REPO_ROOT

router = APIRouter()

# Where picked documents land. A sibling of out/ and reports/ rather than a
# temp dir: the operator needs to see what the run actually consumed, and
# `codegen sharepoint-fetch --dest` writes to the same place.
INPUTS_DIR = REPO_ROOT / "inputs" / "sharepoint"

# A library file name is attacker-adjacent input; it must never escape
# INPUTS_DIR. Same substitution rule the fetch path relies on.
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")

# Graph's simple-upload ceiling applies on the way out; on the way in the
# binding limit is what the workbook parser will sensibly open. 25 MiB is
# far above any real STTM workbook and still refuses a runaway download.
INPUT_MAX_BYTES = 25 * 1024 * 1024

# The `store` the routes read their config and artifact roots from. main.py
# injects the real GenerationStore at import; tests inject a stub.
_store = None


def bind_store(store) -> None:
    """One injection point, so this module never imports main (cycle) and
    tests can drive it without constructing the whole app state."""
    global _store
    _store = store


def _rel(path: Path) -> str:
    """Repo-relative when possible, absolute otherwise.

    INPUTS_DIR is overridable (and is pointed at a scratch dir under test), so
    a path outside the repo is a supported configuration, not a 500.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _require_store():
    if _store is None:
        raise HTTPException(503, "pipeline unavailable — no generation store bound")
    return _store


def _settings():
    return getattr(_require_store().config, "sharepoint", None)


def _client():
    """Config + authenticated client, or the caller's 503/502.

    Never leaks the secret: only SharePointConfigError's own text, which
    names remedies rather than values.
    """
    try:
        cfg = config_for(_settings())
    except SharePointConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        return cfg, build_client(cfg)
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SharePoint sign-in failed ({exc.code}). Check the app "
                   f"registration, its client secret, and admin consent."
                   + (f" Graph request-id {exc.request_id}." if exc.request_id else ""),
        ) from exc


@router.get("/api/sharepoint/config")
def sharepoint_config() -> dict:
    """Whether the picker can be offered, and what it points at.

    Never raises: an unconfigured tenant is a normal state that hides the
    panel, not an error the UI has to handle. `configured` is derived from
    presence only — no secret value crosses this boundary.
    """
    try:
        cfg = config_for(_settings())
    except (SharePointConfigError, HTTPException):
        return {"configured": False, "site": None, "library": None,
                "input_folder": None, "output_folder": None}
    return {
        "configured": True,
        "site": f"{cfg.host}{cfg.site_path}",
        "library": cfg.library,
        "input_folder": cfg.input_folder,
        "output_folder": cfg.output_folder,
    }


@router.get("/api/sharepoint/documents")
def sharepoint_documents() -> dict:
    """List pickable workbooks/contracts in the configured input folder."""
    cfg, client = _client()
    try:
        items = client.list_documents(suffixes=SUPPORTED_SUFFIXES)
    except SharePointConfigError as exc:      # library name wrong -> config problem
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not list {cfg.library!r} ({exc.code}). The app "
                   f"registration may lack read access to this site.",
        ) from exc
    return {
        "site": f"{cfg.host}{cfg.site_path}",
        "library": cfg.library,
        "folder": cfg.input_folder,
        "documents": [
            {"item_id": i.item_id, "name": i.name, "size_bytes": i.size,
             "modified": i.modified, "web_url": i.web_url}
            for i in items
        ],
    }


class ImportRequest(BaseModel):
    item_id: str
    name: str


def _import_item(client, item_id: str, name: str) -> dict:
    """Download one library document into INPUTS_DIR and return the shape the
    UI hands to a generate call. Shared by the import route and locate."""
    name = Path(name).name
    if not name:
        raise HTTPException(status_code=400, detail="document has no filename")
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"only {sorted(SUPPORTED_SUFFIXES)} can be consumed — "
                   f"an STTM workbook (.xlsx) or a contract (.json)",
        )

    try:
        payload = client.download_item(item_id)
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not download {name!r} from SharePoint ({exc.code}).",
        ) from exc

    if len(payload) > INPUT_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"{name} is {len(payload)} bytes; the cap is {INPUT_MAX_BYTES}",
        )

    safe = _SAFE_NAME.sub("_", name)
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = INPUTS_DIR / safe
    # Write-then-rename: a failed transfer must never leave a truncated .xlsx
    # that the workbook parser would report as a layout problem.
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.replace(dest)

    return {
        "path": _rel(dest),
        "name": safe,
        "stem": dest.stem,
        "kind": "workbook" if suffix == ".xlsx" else "contract",
        "source": "sharepoint",
        "size_bytes": len(payload),
    }


@router.post("/api/sharepoint/import", status_code=201)
def sharepoint_import(body: ImportRequest) -> dict:
    """Download one library document into the local input dir."""
    _cfg, client = _client()
    return _import_item(client, body.item_id, body.name)


class LocateRequest(BaseModel):
    name: str


def _item_payload(item) -> dict:
    return {"item_id": item.item_id, "name": item.name, "size_bytes": item.size,
            "modified": item.modified, "web_url": item.web_url}


@router.post("/api/sharepoint/locate")
def sharepoint_locate(body: LocateRequest) -> dict:
    """Name a document; the app finds it in the library itself.

    Matching is EXACT (case-insensitive, extension optional) or it is a human
    decision: anything else returns `candidates` for the user to pick from
    explicitly. There is deliberately no best-match auto-pick — generating a
    pipeline from a similarly-named wrong workbook is exactly the class of
    failure the resolver's strict pairing rules exist to prevent.

    `already_published` is INFORMATIONAL. Unlike the FRD→STTM app, which
    short-circuits to an existing `<doc_id>.sttm.xlsx`, one workbook here
    yields N feeds whose slugs are only known after resolution — so there is
    no pre-run name to key a short-circuit on. What the output folder already
    holds for this stem is surfaced for the operator to judge; the app never
    decides on their behalf. See CLAUDE.md for why this half was not ported.
    """
    target = Path(body.name.strip()).name
    if not target:
        raise HTTPException(status_code=400, detail="give the document's name")

    cfg, client = _client()
    try:
        items = client.list_documents(suffixes=SUPPORTED_SUFFIXES)
    except SharePointConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not list {cfg.library!r} ({exc.code}).",
        ) from exc

    folded = target.casefold()
    exact = [i for i in items
             if i.name.casefold() == folded or Path(i.name).stem.casefold() == folded]
    if len(exact) != 1:
        partial = exact or [i for i in items if folded in i.name.casefold()]
        if not partial:
            raise HTTPException(
                status_code=404,
                detail=f"No document named {target!r} in "
                       f"{cfg.library}/{cfg.input_folder or '<root>'} "
                       f"({len(items)} document(s) there).",
            )
        return {"status": "candidates",
                "candidates": [_item_payload(i) for i in partial]}
    found = exact[0]

    stem = Path(found.name).stem.casefold()
    try:
        rendered = client.list_documents(suffixes=None, folder=cfg.output_folder)
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Found {found.name!r}, but could not check the output folder "
                   f"({exc.code}).",
        ) from exc

    return {
        "status": "ready",
        "document": _import_item(client, found.item_id, found.name),
        "already_published": [
            _item_payload(i) for i in rendered if stem in i.name.casefold()
        ],
    }


@router.get("/api/sharepoint/artifact/{item_id}")
def sharepoint_artifact(item_id: str):
    """Serve an already-published artifact for viewing/download.

    The item id must belong to the output folder's current listing — this
    endpoint re-verifies that before downloading, so it can never be used to
    proxy arbitrary library items the app's identity happens to read.
    """
    from fastapi.responses import Response

    cfg, client = _client()
    try:
        rendered = client.list_documents(suffixes=None, folder=cfg.output_folder)
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not list the output folder ({exc.code}).",
        ) from exc
    match = [i for i in rendered if i.item_id == item_id]
    if not match:
        raise HTTPException(
            status_code=404,
            detail="no such artifact in the SharePoint output folder",
        )
    try:
        payload = client.download_item(item_id)
    except GraphError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not download {match[0].name!r} ({exc.code}).",
        ) from exc
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={"Content-Disposition":
                 f'attachment; filename="{_SAFE_NAME.sub("_", match[0].name)}"'},
    )


class PublishRequest(BaseModel):
    feed_slug: str
    path: str | None = None
    confirm: bool = False


def _publishable(store, feed_slug: str, rel_path: str | None) -> list[Path]:
    """Resolve what a publish call will upload, with containment enforced.

    Addressed through the CURRENT mode's roots, so a live/replay run publishes
    its own isolated artifacts — the same rule `read_generated_file` follows.
    A `..` in `path` is a 400, never a library write outside the feed dir.
    """
    feed_dir = (store.out_root / feed_slug).resolve()
    if rel_path:
        target = (feed_dir / rel_path).resolve()
        if not target.is_relative_to(feed_dir):
            raise HTTPException(
                status_code=400,
                detail=f"path escapes the feed directory: {rel_path}",
            )
        return [target]
    return [
        (store.reports_root / f"{feed_slug}.md").resolve(),
        feed_dir / f"{feed_slug}.ipynb",
    ]


@router.post("/api/sharepoint/publish")
def sharepoint_publish(body: PublishRequest) -> dict:
    """Publish ONE feed's artifacts to the library's output folder.

    This endpoint is the manual publish gate. Publishing is something a
    reviewer does on purpose, per feed, after looking at the gate verdict —
    never a side effect of generating. Three consequences in the shape here:

    - `confirm: true` is required, exactly like the billed-run gate on
      /api/demo/run-live. A missing/false confirm is a 400, so no client can
      publish by accident with a bare POST.
    - One feed per call. There is deliberately no publish-all: the review
      happened per feed, so the publish is per feed.
    - Artifacts are addressed under `out/<feed_slug>/` with containment
      enforced, and named through `published_name` so two feeds cannot
      overwrite each other's `bronze.py` in one flat library folder.

    Failure mapping matches the rest of this module: 503 unconfigured,
    502 Graph refused, 400 bad request, 404 no such artifact.
    """
    if body.confirm is not True:
        raise HTTPException(
            status_code=400,
            detail="publishing writes to the client's SharePoint library and "
                   "requires an explicit {\"confirm\": true}",
        )
    store = _require_store()
    if body.feed_slug not in store.runs:
        raise HTTPException(
            status_code=404, detail=f"no generated feed named {body.feed_slug!r}"
        )

    artifacts = _publishable(store, body.feed_slug, body.path)
    missing = [p for p in artifacts if not p.is_file()]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"nothing to publish for {body.feed_slug!r}: "
                   + ", ".join(p.name for p in missing)
                   + " — generate the feed first",
        )

    cfg, client = _client()
    published = []
    for path in artifacts:
        name = published_name(body.feed_slug, path.name)
        try:
            result = client.upload_file(path, name=name)
        except GraphError as exc:
            raise HTTPException(
                status_code=413 if exc.status == 413 else 502,
                detail=f"Could not publish {name!r} to SharePoint ({exc.code})."
                       + (f" Graph request-id {exc.request_id}." if exc.request_id else ""),
            ) from exc
        published.append({
            "name": name,
            "size_bytes": path.stat().st_size,
            "web_url": result.get("webUrl"),
        })

    return {
        "published": True,
        "feed_slug": body.feed_slug,
        "artifacts": published,
        "target": f"{cfg.host}{cfg.site_path}/{cfg.library}"
                  + (f"/{cfg.output_folder}" if cfg.output_folder else ""),
    }
