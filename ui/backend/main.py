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
from codegen.demo_sources import scan_reference_documents, source_files_payload
from codegen.governance_checks import RunFacts, governance_checks_payload
from codegen.input_requirements import input_requirements_payload
from codegen.metadata_sheet import (
    metadata_sheet_payload,
    workbook_bytes,
    workbook_filename,
)
from ui.backend import databricks_routes, sharepoint_routes
from ui.backend.demo import DemoRunner, LiveRunInProgress
from ui.backend.replay import (
    list_past_live_runs,
    list_replay_sets,
    load_past_live_run,
    load_replay_set,
)
from ui.backend.service import (
    REPO_ROOT,
    Decision,
    FeedRun,
    GenerationStore,
    NothingToGenerateError,
)

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


runner: DemoRunner | None = DemoRunner(store) if store is not None else None


def _require_store() -> GenerationStore:
    if store is None:
        raise HTTPException(503, f"pipeline unavailable — {startup_error}")
    return store


def _require_runner() -> DemoRunner:
    if runner is None:
        raise HTTPException(503, f"pipeline unavailable — {startup_error}")
    return runner


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

# SharePoint picker + confirm-gated publish. Registered before the "/" static
# mount below (which would otherwise swallow these paths) and bound to the
# same store, so publish addresses the CURRENT mode's artifact roots. With no
# store the routes answer 503 rather than 500 — the same posture as the rest
# of the app when startup generation failed.
sharepoint_routes.bind_store(store)
app.include_router(sharepoint_routes.router)
# Databricks volumes: same posture — 503 when unconfigured, panel hidden.
databricks_routes.bind_store(store)
app.include_router(databricks_routes.router)

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
        "framework": run.framework,
    }


@app.get("/api/feeds")
def list_feeds() -> dict:
    if store is None:
        return {
            "feeds": [],
            "failures": [{"label": "startup", "error": f"pipeline unavailable — {startup_error}"}],
            "mode": "mock",
            "label": None,
        }
    decisions = store.load_decisions()
    return {
        "feeds": [_summary(run, decisions) for run in store.runs.values()],
        "failures": [f.model_dump() for f in store.failures],
        "mode": store.mode,
        "label": store.label,
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
    # Always mock here regardless of the request body: with a real key in the
    # backend env, honoring dry_run=False would allow billed calls without the
    # cost confirmation. The ONLY live path is /api/demo/run-live.
    try:
        _require_store().generate(
            only_slug=req.feed_slug, dry_run=True, skip_tests=req.skip_tests
        )
    except NothingToGenerateError as exc:
        raise HTTPException(409, str(exc)) from exc
    if req.feed_slug is not None and req.feed_slug not in _require_store().runs:
        raise HTTPException(404, f"no resolved feed matches {req.feed_slug!r}")
    return list_feeds()


# -- demo modes: replay + live ----------------------------------------------- #


@app.get("/api/replay/sets")
def replay_sets() -> dict:
    return {"sets": [s.model_dump() for s in list_replay_sets()]}


class ReplayLoadRequest(BaseModel):
    set: str


@app.post("/api/replay/load")
def replay_load(req: ReplayLoadRequest) -> dict:
    try:
        load_replay_set(_require_store(), req.set)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc
    return list_feeds()


@app.post("/api/decisions/reset")
def reset_decisions() -> dict:
    """Presenter's clean-slate button: clears the CURRENT run's decisions."""
    _require_store().reset_decisions()
    return list_feeds()


@app.get("/api/demo/live-runs")
def live_runs() -> dict:
    return {"runs": [r.model_dump() for r in list_past_live_runs(_require_store())]}


class LiveRunLoadRequest(BaseModel):
    run: str


@app.post("/api/demo/load-live-run")
def load_live_run(req: LiveRunLoadRequest) -> dict:
    try:
        load_past_live_run(_require_store(), req.run)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    return list_feeds()


def _live_ready() -> tuple[bool, str]:
    """Whether a live (non-mock) Layer-2 run can happen, and why not.

    Mirrors ``build_provider``'s selection exactly: databricks_fmapi needs a
    resolvable workspace config; anthropic needs ANTHROPIC_API_KEY. Boolean +
    provider name ONLY — never the key, never env contents.
    """
    if store is None:
        return False, "backend has no config loaded"
    if os.environ.get("CODEGEN_FORCE_MOCK_PROVIDER"):
        # Hard mock lock (the App deployment): the run button stays usable —
        # build_provider returns the mock, so a "live" run makes ZERO model
        # calls. The provider surface reports the lock explicitly.
        return True, ""
    provider = store.config.reasoning.provider
    if provider == "databricks_fmapi":
        from codegen.databricks import DatabricksConfigError, config_for

        try:
            cfg = config_for(store.config.databricks)
        except DatabricksConfigError:
            return False, "Databricks workspace config does not resolve"
        if not cfg.serving_endpoint:
            return False, "databricks.serving_endpoint is not configured"
        return True, ""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, "no ANTHROPIC_API_KEY in the backend env"
    return True, ""


@app.get("/api/demo/live-available")
def live_available() -> dict:
    available, _reason = _live_ready()
    if os.environ.get("CODEGEN_FORCE_MOCK_PROVIDER"):
        provider = "mock (locked)"
    else:
        provider = store.config.reasoning.provider if store is not None else None
    return {"available": available, "provider": provider}


class LiveRunRequest(BaseModel):
    confirm: bool = False


@app.post("/api/demo/run-live")
def run_live(req: LiveRunRequest) -> dict:
    if not req.confirm:
        raise HTTPException(400, "live run requires explicit confirm: true (billed API calls)")
    available, reason = _live_ready()
    if not available:
        raise HTTPException(400, f"live run unavailable: {reason}")
    _require_store()
    try:
        _require_runner().start_live()
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return _require_runner().status()


@app.get("/api/demo/status")
def demo_status() -> dict:
    demo = _require_store().config.demo
    return {
        **_require_runner().status(),
        "mode": _require_store().mode,
        "label": _require_store().label,
        "estimates": {
            "calls": demo.estimated_calls,
            "cost_usd": demo.estimated_cost_usd,
            "seconds": demo.estimated_seconds,
        },
        # Which STTM workbook a live run would consume — file name only, so
        # the "choose an STTM" step is legible in the UI before firing.
        # sttm_chosen distinguishes an operator's explicit pick from the
        # config-default fallback, so the UI can demand the choice up front.
        "sttm_workbook": _require_runner().effective_workbook().name,
        "sttm_chosen": _require_runner().selected_workbook is not None,
        # Output mode a run would use (Option A notebook / Option B
        # framework / both) — the runner's override or the config default.
        "output_mode": (
            _require_runner().output_mode or _require_store().config.output.mode
        ),
        # The FRD side of the pair. frd_warning: the STTM is an explicit
        # non-golden pick while the FRD is still the pinned demo golden —
        # a feed-match failure is likely; the human decides, no auto-fix.
        "frd_name": (_require_runner().selected_frd_label
                     or _require_store().config.demo.frd),
        "frd_chosen": _require_runner().selected_frd is not None,
        "frd_warning": (
            _require_runner().selected_workbook is not None
            and _require_runner().selected_workbook.name
            != Path(_require_store().config.demo.workbook).name
            and _require_runner().selected_frd is None
        ),
        "error_hint": _require_runner().error_hint,
    }


@app.get("/api/demo/frd-choices")
def frd_choices() -> dict:
    """FRD options for the chooser: upstream contracts (FRD→STTM agent's
    table, with audit stamps and pairing vs the current STTM), local
    contract JSONs, and documents with NO contract (not selectable — "run
    the FRD→STTM agent first"). Upstream unreachable → that section absent
    with a reason, everything else still renders."""
    from codegen.demo_sources import (
        canonical_document_name,
        document_stem,
        pair_sttm_with_frd,
        suggest_pairs,
    )
    from codegen.upstream_contracts import list_contracts

    store = _require_store()
    runner = _require_runner()
    sttm_name = runner.effective_workbook().name

    upstream_rows: list[dict] = []
    upstream_error: str | None = None
    try:
        contracts = list_contracts(store.config)
    except Exception as exc:  # noqa: BLE001 — chooser stays usable offline
        contracts, upstream_error = [], str(exc).splitlines()[0][:160]
    doc_ids = [row["doc_id"] for row in contracts]
    paired = pair_sttm_with_frd([sttm_name], doc_ids,
                                explicit_map=store.config.demo.pairing_map)
    suggested = suggest_pairs([sttm_name], doc_ids)
    for row in contracts:
        upstream_rows.append({
            **row,
            "paired": paired.get(sttm_name) == row["doc_id"],
            "suggested": (suggested.get(sttm_name) == row["doc_id"]
                          and paired.get(sttm_name) != row["doc_id"]),
        })

    contracts_dir = REPO_ROOT / store.config.contracts.dir
    local = sorted(
        {p.name for d in (contracts_dir, REPO_ROOT / "inputs" / "databricks",
                          REPO_ROOT / "inputs" / "sharepoint")
         if d.is_dir()
         for p in d.glob("*.contract.json")}
    )

    upstream_stems = {document_stem(d) for d in doc_ids}
    orphans = sorted({
        p.name
        for d in (REPO_ROOT / "inputs" / "databricks",
                  REPO_ROOT / "inputs" / "sharepoint")
        if d.is_dir()
        for p in d.glob("*.docx")
        if canonical_document_name(p.name).startswith("frd")
        and document_stem(p.name) not in upstream_stems
    })

    return {
        "sttm": sttm_name,
        "current": {
            "label": runner.selected_frd_label or store.config.demo.frd,
            "chosen": runner.selected_frd is not None,
        },
        "upstream": upstream_rows,
        "upstream_error": upstream_error,
        "local": local,
        "no_contract": orphans,
    }


class FrdSelectRequest(BaseModel):
    kind: str  # "upstream" | "local"
    id: str    # doc_id (upstream) or file name (local)


@app.post("/api/demo/frd")
def select_frd(req: FrdSelectRequest) -> dict:
    from codegen.upstream_contracts import UpstreamContractError, materialize

    store = _require_store()
    runner = _require_runner()
    try:
        if req.kind == "upstream":
            path, contract, meta = materialize(store.config, req.id, REPO_ROOT)
            runner.select_frd(path, req.id)
            feeds = [{
                "feed_name": f.feed_name,
                "stage": f"{f.stage_target.schema_name}."
                         f"{','.join(f.stage_target.tables)}",
                "standard": (f"{f.standard_target.schema_name}."
                             f"{','.join(f.standard_target.tables)}"
                             if f.standard_target.tables else None),
            } for f in contract.feeds]
            return {"selected": req.id, "kind": "upstream",
                    "audited_at": meta["audited_at"], "feeds": feeds}
        if req.kind == "local":
            if "/" in req.id or "\\" in req.id or ".." in req.id:
                raise HTTPException(400, f"invalid contract name {req.id!r}")
            for directory in (REPO_ROOT / store.config.contracts.dir,
                              REPO_ROOT / "inputs" / "databricks",
                              REPO_ROOT / "inputs" / "sharepoint"):
                candidate = directory / req.id
                if candidate.is_file():
                    runner.select_frd(candidate, req.id)
                    return {"selected": req.id, "kind": "local", "feeds": None}
            raise HTTPException(404, f"no local contract named {req.id!r}")
        raise HTTPException(400, f"unknown kind {req.kind!r}")
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except UpstreamContractError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.delete("/api/demo/frd")
def clear_frd() -> dict:
    try:
        _require_runner().clear_frd()
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"selected": None}


class OutputModeRequest(BaseModel):
    mode: str | None = None  # notebook | framework | both; null = config default


@app.post("/api/demo/output-mode")
def select_output_mode(req: OutputModeRequest) -> dict:
    try:
        _require_runner().select_output_mode(req.mode)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return demo_status()


@app.get("/api/feeds/{slug}/download")
def download_generated_file(slug: str, path: str) -> Response:
    """Binary download (framework workbooks / inserts) with containment."""
    if slug not in _require_store().runs:
        raise HTTPException(404, f"no generated feed named {slug!r}")
    try:
        payload = _require_store().read_generated_bytes(slug, path)
    except PermissionError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"file not found: {path}") from exc
    name = Path(path).name
    media = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if name.endswith(".xlsx")
        else "text/plain; charset=utf-8"
    )
    return Response(
        content=payload,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@app.get("/api/demo/workbooks")
def demo_workbooks() -> dict:
    """STTM workbooks a live run could consume (fixtures + sharepoint inbox)."""
    return {"workbooks": _require_runner().workbook_choices()}


class WorkbookSelectRequest(BaseModel):
    name: str


@app.post("/api/demo/workbook")
def select_workbook(req: WorkbookSelectRequest) -> dict:
    try:
        _require_runner().select_workbook(req.name)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"workbooks": _require_runner().workbook_choices()}


@app.delete("/api/demo/workbook")
def clear_workbook() -> dict:
    """Return the choose-an-STTM step to 'none chosen'."""
    try:
        _require_runner().clear_workbook()
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"workbooks": _require_runner().workbook_choices()}


@app.get("/api/demo/input-documents")
def input_documents() -> dict:
    """The documents card's data: reference documents + the FRD stand-in.

    ``reference_documents`` is a live scan of the configured input dirs
    (``demo.input_documents``, env-overridable) against the expected client
    reference documents — present entries carry the resolved path for the
    backend's own use; the UI shows names only. Listing only — wiring a
    found document into the generator is the next step. The ``frd`` kind is
    unchanged: a scan of the SharePoint inbox for a real FRD contract.
    """
    inbox = REPO_ROOT / "inputs" / "sharepoint"

    def scan(patterns: list[str]) -> list[str]:
        if not inbox.is_dir():
            return []
        return sorted({p.name for pat in patterns for p in inbox.glob(pat) if p.is_file()})

    return {
        "documents": [
            {
                "kind": "reference_documents",
                **scan_reference_documents(_require_store().config, REPO_ROOT),
            },
            {
                "kind": "frd",
                "matches": scan(["*.contract.json"]),
                "stand_in": Path(_require_store().config.demo.frd).name,
            },
        ]
    }


@app.get("/api/demo/source-files")
def demo_source_files() -> dict:
    """The "source files this run will read" panel + synthetic shell listing.

    Display data only, rendered server-side (no path logic in TypeScript);
    reads the demo FRD contract at request time and, when the real FRD .docx
    is present in the input dirs, its Structural Metadata convention values —
    nothing is cached to disk.
    """
    try:
        return source_files_payload(_require_store().config, REPO_ROOT)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


def _metadata_sheet_inputs(store: GenerationStore):
    """The current run's specs + unmapped rule texts, if any run is loaded."""
    if not store.runs:
        return None, None
    specs = [run.spec for run in store.runs.values()]
    unmapped = {
        run.spec.feed_slug: {
            o.rule_text for o in run.outcomes if o.classification == "unmapped"
        }
        for run in store.runs.values()
    }
    return specs, unmapped


@app.get("/api/demo/governance-checks")
def governance_checks() -> dict:
    """The two architecture decks' stated controls, read live and evaluated
    against the loaded run (codegen.governance_checks)."""
    store = _require_store()
    decisions = store.load_decisions()
    runs = list(store.runs.values())
    candidates = [c for run in runs for c in run.candidates]
    pending = sum(
        1
        for run in runs
        for i in range(len(run.candidates))
        if _decision_for(run.spec.feed_slug, i, decisions)["decision"] == "pending"
    )
    facts = RunFacts(
        loaded=bool(runs),
        mode=store.mode if runs else None,
        feeds=len(runs),
        fingerprinted_feeds=sum(
            1 for run in runs
            if run.spec.frd_contract_sha256 and run.spec.sttm_contract_sha256
        ),
        candidates=len(candidates),
        grounded_candidates=sum(1 for c in candidates if c.grounded),
        pending_reviews=pending,
        reports_on_disk=sum(
            1 for run in runs if store.read_report(run.spec.feed_slug) is not None
        ),
        candidate_providers=tuple(c.provider for c in candidates),
    )
    return governance_checks_payload(store.config, REPO_ROOT, facts)


@app.get("/api/demo/input-requirements")
def input_requirements() -> dict:
    """The FRD contract evaluated against the client requirements deck,
    read LIVE from the input dirs (codegen.input_requirements). The one
    reference document consumed in processing; absent deck → absent check."""
    return input_requirements_payload(_require_store().config, REPO_ROOT)


@app.get("/api/demo/metadata-sheet")
def metadata_sheet() -> dict:
    """Display-only preview of the ACFC metadata sheet (see codegen.metadata_sheet)."""
    store = _require_store()
    specs, unmapped = _metadata_sheet_inputs(store)
    try:
        return metadata_sheet_payload(
            store.config, REPO_ROOT, specs=specs,
            unmapped_by_slug=unmapped, run_label=store.label,
        )
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/demo/metadata-sheet.xlsx")
def metadata_sheet_xlsx() -> Response:
    """The same preview as a downloadable workbook — built in memory, never
    written to disk on the serving path."""
    store = _require_store()
    specs, unmapped = _metadata_sheet_inputs(store)
    try:
        payload = metadata_sheet_payload(
            store.config, REPO_ROOT, specs=specs,
            unmapped_by_slug=unmapped, run_label=store.label,
        )
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(
        content=workbook_bytes(payload),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{workbook_filename(payload)}"'
        },
    )


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
