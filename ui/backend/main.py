"""FastAPI backend for the CodeGen demo UI.

Thin layer over ``service.GenerationStore``: runs the real generation
pipeline in-process and serves its structured results. No generation logic
lives here.

Two run modes (see ui/README.md):
  dev (two-process):   .venv/bin/uvicorn ui.backend.main:app --reload --port 8571
                       + Vite dev server proxying /api (CORS only with CODEGEN_UI_DEV=1)
  single-port (Apps-shaped):  .venv/bin/python -m ui.backend.main
                       serves ui/frontend/dist at / when a build exists
"""

from __future__ import annotations

import os
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from codegen.config import load_dotenv
from ui.backend.service import Decision, FeedRun, GenerationStore

# Same .env resolution as the CLI. Inert while the UI hardwires dry_run=True
# (mock provider), but keeps env parity for the day a live knob lands.
load_dotenv()

CONFIG_PATH = "config/config.yaml"

# An Apps deployment may start without config/fixtures in place — come up
# with empty state and a clear message instead of crashing at import.
store: GenerationStore | None
startup_error: str | None = None
try:
    store = GenerationStore(CONFIG_PATH)
except Exception as exc:  # noqa: BLE001 — surfaced via /api/feeds, never hidden
    store = None
    startup_error = f"{type(exc).__name__}: {exc}"


def _require_store() -> GenerationStore:
    if store is None:
        raise HTTPException(503, f"pipeline unavailable — {startup_error}")
    return store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Generate on startup so the dashboard is populated on first load.
    # Dry-run + skip-tests: mock Layer-2 provider, no Spark needed — the
    # same fast path the CLI's --dry-run --skip-tests takes.
    if store is None:
        print(f"UI starting with EMPTY STATE — {startup_error}")
    else:
        try:
            store.generate(dry_run=True, skip_tests=True)
        except Exception as exc:  # noqa: BLE001 — startup must not crash the app
            print(f"Startup generation failed — UI starts empty; POST /api/generate retries: {exc}")
    yield


app = FastAPI(title="CodeGen / Data Engineer Agent — demo UI", lifespan=lifespan)

# CORS is only needed when the frontend is served from a different origin —
# i.e. the two-process dev workflow's Vite server. Single-port mode is
# same-origin, so the allowance stays off unless explicitly requested.
if os.environ.get("CODEGEN_UI_DEV"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _decision_for(feed_slug: str, index: int, decisions: dict) -> dict:
    entry = decisions.get(feed_slug, {}).get(str(index))
    return entry if entry else {"decision": "pending", "note": None}


def _summary(run: FeedRun, decisions: dict) -> dict:
    spec, gate = run.spec, run.gate
    counts = Counter(o.classification for o in run.outcomes)
    pending = sum(
        1
        for i in range(len(run.candidates))
        if _decision_for(spec.feed_slug, i, decisions)["decision"] == "pending"
    )
    return {
        "feed_slug": spec.feed_slug,
        "feed_id": spec.feed_id,
        "feed_name": spec.feed_name,
        "source_system": spec.source_system,
        "lobs": spec.lobs,
        "file_format": spec.file_format,
        "frequency": spec.frequency,
        "segmented": spec.is_segmented,
        "sttm_is_synthetic": spec.sttm_is_synthetic,
        "verdict": gate.verdict,
        "flags": gate.flags,
        "checks": [c.model_dump() for c in gate.checks],
        "rule_counts": dict(counts),
        "rule_total": len(run.outcomes),
        "candidate_count": len(run.candidates),
        "candidates_pending": pending,
        "files_written": len(run.written_files),
    }


@app.get("/api/feeds")
def list_feeds() -> dict:
    if store is None:
        return {
            "feeds": [],
            "failures": [{"label": "startup", "error": f"pipeline unavailable — {startup_error}"}],
        }
    decisions = store.load_decisions()
    return {
        "feeds": [_summary(run, decisions) for run in store.runs.values()],
        "failures": [f.model_dump() for f in store.failures],
    }


@app.get("/api/feeds/{slug}")
def feed_detail(slug: str) -> dict:
    run = _require_store().runs.get(slug)
    if run is None:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    decisions = _require_store().load_decisions()
    spec = run.spec
    return {
        **_summary(run, decisions),
        "delimiter": spec.delimiter,
        "file_name_patterns": spec.file_name_patterns,
        "landing_location": spec.landing_location,
        "natural_key_columns": spec.natural_key_columns,
        "not_null_columns": spec.not_null_columns,
        "phi_columns": spec.phi_columns,
        "load_windows_sla": spec.load_windows_sla,
        "contracts": {
            "frd_name": spec.frd_contract_name,
            "frd_sha256": spec.frd_contract_sha256,
            "sttm_name": spec.sttm_contract_name,
            "sttm_sha256": spec.sttm_contract_sha256,
            "sttm_is_synthetic": spec.sttm_is_synthetic,
        },
        "tables": {
            "stage": [s.stage_table.qualified_name for s in spec.segments],
            "standard": (spec.standard_table.qualified_name if spec.standard_table else None),
            "errors": spec.errors_table.qualified_name,
            "processed_files": spec.processed_files_table.qualified_name,
            "recycle": (spec.recycle.recycle_table.qualified_name if spec.recycle else None),
        },
        "outcomes": [o.model_dump() for o in run.outcomes],
        "candidates": [
            {
                **c.model_dump(),
                "index": i,
                "review": _decision_for(slug, i, decisions),
            }
            for i, c in enumerate(run.candidates)
        ],
        "written_files": run.written_files,
    }


class GenerateRequest(BaseModel):
    feed_slug: str | None = None
    dry_run: bool = True
    skip_tests: bool = True


@app.post("/api/generate")
def generate(req: GenerateRequest) -> dict:
    _require_store().generate(
        only_slug=req.feed_slug, dry_run=req.dry_run, skip_tests=req.skip_tests
    )
    if req.feed_slug is not None and req.feed_slug not in _require_store().runs:
        raise HTTPException(404, f"no resolved feed matches {req.feed_slug!r}")
    return list_feeds()


@app.get("/api/feeds/{slug}/file")
def generated_file(slug: str, path: str) -> dict:
    if slug not in _require_store().runs:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    try:
        content = _require_store().read_generated_file(slug, path)
    except PermissionError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"file not found: {path}") from exc
    return {"path": path, "content": content}


@app.get("/api/feeds/{slug}/report")
def report(slug: str) -> dict:
    content = _require_store().read_report(slug)
    if content is None:
        raise HTTPException(404, f"no report for {slug!r}")
    return {"markdown": content}


class DecisionRequest(BaseModel):
    decision: Decision
    note: str | None = None


@app.post("/api/feeds/{slug}/candidates/{index}/decision")
def decide(slug: str, index: int, req: DecisionRequest) -> dict:
    run = _require_store().runs.get(slug)
    if run is None:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    if not 0 <= index < len(run.candidates):
        raise HTTPException(404, f"candidate index {index} out of range")
    entry = _require_store().save_decision(slug, index, req.decision, req.note)
    return {"feed_slug": slug, "index": index, "review": entry}


# --------------------------------------------------------------------------- #
# Single-port mode: serve the built frontend when ui/frontend/dist exists.
# Registered after every /api route so the "/" mount only catches the rest.
# Absent in dev, where Vite serves the frontend on its own port instead.
# Pattern mirrors frd-to-sttm's review_app_react backend, plus an SPA
# fallback because this frontend uses BrowserRouter deep links.
# --------------------------------------------------------------------------- #
class _SpaStaticFiles(StaticFiles):
    """StaticFiles with client-side-routing fallback and a no-store HTML shell.

    Unknown non-/api paths (e.g. a /feeds/<slug> deep link or a page reload)
    return index.html so the React router resolves them. The HTML shell is
    never cached: it names the hashed bundle it loads, and a cached shell
    requesting a stale hash after a rebuild renders a blank page. Hashed
    /assets/ files are content-addressed and stay cacheable.
    """

    async def get_response(self, path: str, scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            response = await super().get_response("index.html", scope)
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store, must-revalidate"
        return response


_FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", _SpaStaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    # DATABRICKS_APP_PORT is what Databricks Apps injects at runtime;
    # CODEGEN_UI_PORT is the local override; default stays this repo's 8571.
    # 0.0.0.0 is required in the deployed Apps context; CODEGEN_UI_HOST=127.0.0.1
    # exists for locked-down local machines where binding all interfaces
    # triggers a firewall prompt.
    uvicorn.run(
        app,
        host=os.environ.get("CODEGEN_UI_HOST", "0.0.0.0"),
        port=int(os.environ.get("DATABRICKS_APP_PORT", os.environ.get("CODEGEN_UI_PORT", "8571"))),
    )
