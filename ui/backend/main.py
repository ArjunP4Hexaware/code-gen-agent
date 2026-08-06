"""FastAPI backend for the CodeGen demo UI.

Thin layer over ``service.GenerationStore``: runs the real generation
pipeline in-process and serves its structured results. No generation logic
lives here.

Run from the repo root:
    .venv/bin/uvicorn ui.backend.main:app --reload --port 8571
"""

from __future__ import annotations

from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ui.backend.service import Decision, FeedRun, GenerationStore

CONFIG_PATH = "config/config.yaml"

store = GenerationStore(CONFIG_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Generate on startup so the dashboard is populated on first load.
    # Dry-run + skip-tests: mock Layer-2 provider, no Spark needed — the
    # same fast path the CLI's --dry-run --skip-tests takes.
    store.generate(dry_run=True, skip_tests=True)
    yield


app = FastAPI(title="CodeGen / Data Engineer Agent — demo UI", lifespan=lifespan)

# Vite dev server origin.
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
    decisions = store.load_decisions()
    return {
        "feeds": [_summary(run, decisions) for run in store.runs.values()],
        "failures": [f.model_dump() for f in store.failures],
    }


@app.get("/api/feeds/{slug}")
def feed_detail(slug: str) -> dict:
    run = store.runs.get(slug)
    if run is None:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    decisions = store.load_decisions()
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
    store.generate(only_slug=req.feed_slug, dry_run=req.dry_run, skip_tests=req.skip_tests)
    if req.feed_slug is not None and req.feed_slug not in store.runs:
        raise HTTPException(404, f"no resolved feed matches {req.feed_slug!r}")
    return list_feeds()


@app.get("/api/feeds/{slug}/file")
def generated_file(slug: str, path: str) -> dict:
    if slug not in store.runs:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    try:
        content = store.read_generated_file(slug, path)
    except PermissionError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"file not found: {path}") from exc
    return {"path": path, "content": content}


@app.get("/api/feeds/{slug}/report")
def report(slug: str) -> dict:
    content = store.read_report(slug)
    if content is None:
        raise HTTPException(404, f"no report for {slug!r}")
    return {"markdown": content}


class DecisionRequest(BaseModel):
    decision: Decision
    note: str | None = None


@app.post("/api/feeds/{slug}/candidates/{index}/decision")
def decide(slug: str, index: int, req: DecisionRequest) -> dict:
    run = store.runs.get(slug)
    if run is None:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    if not 0 <= index < len(run.candidates):
        raise HTTPException(404, f"candidate index {index} out of range")
    entry = store.save_decision(slug, index, req.decision, req.note)
    return {"feed_slug": slug, "index": index, "review": entry}
