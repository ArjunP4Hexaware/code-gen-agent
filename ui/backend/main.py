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
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
from codegen.storage import StorageError
from ui.backend import databricks_routes, sharepoint_routes
from ui.backend.demo import (
    DemoRunner,
    LiveRunInProgress,
    SelectionFailed,
    SelectionInProgress,
)
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
            "model_usage": [],
        }
    decisions = store.load_decisions()
    return {
        "feeds": [_summary(run, decisions) for run in store.runs.values()],
        "failures": [f.model_dump() for f in store.failures],
        "mode": store.mode,
        "label": store.label,
        # Per stage, what the served run did with a model (label included).
        "model_usage": store.model_usage,
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
    from codegen.reasoning.transport import resolve_transport

    transport = resolve_transport(store.config)
    return transport.available, transport.reason


@app.get("/api/demo/live-available")
def live_available() -> dict:
    """Which Layer-2 transport a live run would use, and whether it can.

    ``provider`` is the EFFECTIVE transport (``databricks_fmapi`` inside a
    Databricks runtime whatever the yaml says, ``anthropic`` locally with a
    key, ``mock (locked)`` under the lock); ``transport`` carries the
    detection detail the UI renders (runtime, marker, endpoint, model,
    label, override). ``reason`` is the remedy — never a secret, never env
    contents."""
    if store is None:
        return {"available": False, "provider": None,
                "reason": "backend has no config loaded", "transport": None}
    from codegen.reasoning.transport import resolve_transport

    transport = resolve_transport(store.config)
    return {"available": transport.available, "provider": transport.provider_name,
            "reason": transport.reason, "transport": transport.as_dict()}


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
    except ValueError as exc:  # nothing selected under Output
        raise HTTPException(400, str(exc)) from exc
    return _require_runner().status()


class VddSelectRequest(BaseModel):
    name: str


@app.post("/api/demo/vdd")
def select_vdd(req: VddSelectRequest) -> dict:
    """M3: choose a Vendor Data Dictionary workbook (.xlsx) from the input
    directories as the pair's third input; DELETE clears it."""
    runner = _require_runner()
    if "/" in req.name or "\\" in req.name or ".." in req.name:
        raise HTTPException(400, f"invalid workbook name {req.name!r}")
    # M9.3: through the input catalog — the local directories AND the remote /
    # extra input roots (a dictionary in a workspace pair folder used to be a
    # 404); a failed download is a 424 with the reason, never a silent no-op.
    try:
        runner.select_vdd_by_name(req.name)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except SelectionFailed as exc:
        raise HTTPException(424, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"{exc} (the input directories)") from exc
    return {"selected": req.name}


@app.delete("/api/demo/vdd")
def clear_vdd() -> dict:
    try:
        _require_runner().select_vdd(None)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"selected": None}


class LayoutAnswersRequest(BaseModel):
    answers: dict = {}
    proceed: bool = False
    cancel: bool = False
    refresh: bool = False  # M9.1: re-resolve past every cached profile instead


@app.post("/api/demo/layout-answers")
def layout_answers(req: LayoutAnswersRequest) -> dict:
    """The human's role placements for a run paused in ``needs_layout``
    (M2.5 §6): ``answers`` = ``{"sttm": {"<sheet>/<layer>/<role>": col},
    "frd": {"<field>": {table,row,col,…}}}``; ``proceed`` continues with the
    remaining roles read as empty (gate-flagged); ``cancel`` stops the run;
    ``refresh`` re-resolves the layout past every cached profile (M9.1)."""
    from codegen.layout.resolve import parse_answers

    runner = _require_runner()
    try:
        parse_answers(req.answers)
        runner.answer_layout(req.answers, proceed=req.proceed, cancel=req.cancel,
                             refresh=req.refresh)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return runner.status()


class LayoutRefreshRequest(BaseModel):
    enabled: bool = True


@app.post("/api/demo/layout-refresh")
def layout_refresh(req: LayoutRefreshRequest) -> dict:
    """M9.1 "re-resolve layout": arm (or disarm) a one-shot bypass of every
    cached layout profile for the NEXT run; its runtime cache entries are
    overwritten by what the run resolves. 409 while a run is in progress
    (its layout dialog has its own re-resolve action)."""
    runner = _require_runner()
    try:
        runner.set_layout_refresh(req.enabled)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return runner.status()


class LayoutAdviceRequest(BaseModel):
    confirm: bool = False  # a model call (billed on a live transport)


@app.post("/api/demo/layout-advice")
def layout_advice(req: LayoutAdviceRequest) -> dict:
    """Ask the Layer-2 transport for advice on the pending layout questions:
    one call over the question texts, header strips and candidate labels
    (never a data row). Confirm-gated like run-live; the mock lock or an
    unavailable transport answers offline and the response names it."""
    from codegen.layout.model import LayoutProviderError

    if not req.confirm:
        raise HTTPException(400, "layout advice requires explicit confirm: true (a model call)")
    runner = _require_runner()
    try:
        runner.advise_layout(dry_run=False)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except LayoutProviderError as exc:
        raise HTTPException(502, f"layout advice failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — transport errors surface, never a bare 500
        raise HTTPException(502, f"layout advice failed: {type(exc).__name__}: {exc}") from exc
    return demo_status()


@app.get("/api/demo/status")
def demo_status() -> dict:
    demo = _require_store().config.demo
    runner_status = _require_runner().status()
    # ONE snapshot of the selection record for every field below (M9.3
    # addendum: the list's ``selected`` and the chooser disagreed on site).
    chosen = runner_status["selection"]
    return {
        **runner_status,
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
        "sttm_workbook": chosen["sttm"] or Path(demo.workbook).name,
        "sttm_chosen": chosen["sttm"] is not None,
        # M3: the optional Vendor Data Dictionary (third input), file name only.
        "vdd_name": chosen["vdd"],
        # The outputs a run would produce (notebook and / or framework) —
        # None while nothing is selected — and the selection itself.
        "output_mode": (
            _require_runner().output_mode if _require_runner().output_parts is not None
            else _require_runner().effective_output_parts()
        ),
        "output_parts": _require_runner().effective_output_parts(),
        # M4/M5 generation options a run would use (override or config default).
        "conventions_profile": (_require_runner().conventions_profile
                                or _require_store().config.conventions.profile),
        "iig_template": (_require_runner().iig_template
                         or _require_store().config.metadata.template),
        "playbook_template": (_require_runner().playbook_template
                              or _require_store().config.playbook.template),
        # The FRD side of the pair. frd_warning: the STTM is an explicit
        # non-golden pick while the FRD is still the pinned demo golden —
        # a feed-match failure is likely; the human decides, no auto-fix.
        "frd_name": chosen["frd"] or _require_store().config.demo.frd,
        "frd_chosen": chosen["frd"] is not None,
        # Set when choosing the STTM selected its associated FRD automatically
        # ({frd, rule: pairing_map | ticket | name_stem}); None for a manual pick.
        "frd_auto_paired": _require_runner().frd_auto_paired,
        "vdd_auto_paired": _require_runner().vdd_auto_paired,
        "frd_warning": (
            chosen["sttm"] is not None
            and chosen["sttm"] != Path(_require_store().config.demo.workbook).name
            and chosen["frd"] is None
        ),
        "error_hint": _require_runner().error_hint,
    }


@app.get("/api/demo/frd-choices")
def frd_choices() -> dict:
    """FRD options for the chooser: local FRDs — contract JSONs AND FRD .docx
    documents (standalone doctrine, 2026-09-18: a .docx is extracted by
    ``codegen.extract.frd_docx`` when the run starts) — and, ONLY with
    ``upstream.enabled``, the upstream contracts (FRD→STTM agent's table).

    M9.3 addendum: this request NEVER calls the warehouse. Upstream rows are the
    runner's snapshot, refreshed in a background task with a hard timeout
    (``upstream_state``: disabled | loading | ready | failed — the chooser
    polls while it is ``loading``). ``no_contract`` is kept for API
    compatibility and is always empty."""
    from codegen.demo_sources import pair_sttm_with_frd, suggest_pairs

    store = _require_store()
    runner = _require_runner()
    sttm_name = runner.effective_workbook().name

    upstream_rows: list[dict] = []
    snapshot = runner.upstream_snapshot()
    contracts, upstream_error = snapshot["rows"], snapshot["error"]
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

    local = sorted(runner.local_frd_candidates())
    orphans: list[str] = []

    return {
        "sttm": sttm_name,
        "current": {
            "label": runner.selected_frd_label or store.config.demo.frd,
            "chosen": runner.selected_frd is not None,
        },
        "upstream": upstream_rows,
        "upstream_error": upstream_error,
        "upstream_enabled": snapshot["enabled"],
        "upstream_state": snapshot["state"],
        "local": local,
        "no_contract": orphans,
    }


class FrdSelectRequest(BaseModel):
    kind: str  # "upstream" | "local"
    id: str    # doc_id (upstream) or file name (local)


@app.post("/api/demo/frd")
def select_frd(req: FrdSelectRequest, response: Response) -> dict:
    runner = _require_runner()
    try:
        if req.kind == "upstream":
            # A warehouse read: never awaited here. 202 + the job; the outcome
            # ({selected, audited_at, feeds} or the error) is the status'
            # ``selection_job``. Refused (403) while upstream.enabled is false.
            try:
                job = runner.start_upstream_frd(req.id)
            except PermissionError as exc:
                raise HTTPException(403, str(exc)) from exc
            response.status_code = 202
            return {"job": job, "kind": "upstream"}
        if req.kind == "local":
            # A local FRD is a .contract.json or an FRD .docx (extracted by
            # the runner when the run starts — standalone doctrine).
            if "/" in req.id or "\\" in req.id or ".." in req.id:
                raise HTTPException(400, f"invalid contract name {req.id!r}")
            # The contracts dir, the inboxes of the inputs role and the extra
            # input roots (M8.1) — a remote document is downloaded on selection.
            candidate = runner.fetch_frd_candidate(req.id)
            if candidate is not None:
                runner.select_frd(candidate, req.id)
                return {"selected": req.id, "kind": "local", "feeds": None}
            raise HTTPException(404, f"no local contract named {req.id!r}")
        raise HTTPException(400, f"unknown kind {req.kind!r}")
    except (LiveRunInProgress, SelectionInProgress) as exc:
        raise HTTPException(409, str(exc)) from exc
    except (StorageError, OSError) as exc:
        # M9.3: the FRD stays as it was; the reason is the response AND the status.
        failed = runner._fail_selection("frd", req.id, exc, "downloading it")  # noqa: SLF001
        raise HTTPException(424, str(failed)) from exc


_UPLOAD_MAX_BYTES = 25 * 1024 * 1024  # same cap as the SharePoint import


@app.post("/api/demo/upload", status_code=201)
async def upload_demo_document(
    kind: Annotated[str, Form()], file: Annotated[UploadFile, File()]
) -> dict:
    """From-device upload for the choose step: an STTM workbook (.xlsx), an
    FRD contract JSON, or an FRD .docx. Lands in the gitignored
    ``inputs/uploads/`` inbox (scanned exactly like the SharePoint/Databricks
    ones) and is selected for the next run in the same motion. A JSON upload
    must PARSE as an FRD contract; a .docx must be an F1/F2 FRD the
    extractor recognises (``codegen.extract.frd_docx``) — either refusal is
    loud, never a guess."""
    import tempfile

    from codegen.contracts import FrdContract
    from codegen.extract.frd_docx import FrdDocxError, discover_frd, read_docx

    runner = _require_runner()
    if runner.state == "running":
        raise HTTPException(409, "cannot change inputs while a live run is in progress")

    name = Path(file.filename or "").name
    if not name or name.startswith("~$") or ".." in name:
        raise HTTPException(400, f"invalid file name {file.filename!r}")
    payload = await file.read()
    if len(payload) > _UPLOAD_MAX_BYTES:
        cap_mib = _UPLOAD_MAX_BYTES // (1024 * 1024)
        raise HTTPException(413, f"{name!r} exceeds the {cap_mib} MiB upload cap")
    if not payload:
        raise HTTPException(400, f"{name!r} is empty")

    lower = name.lower()
    if kind == "sttm":
        if not lower.endswith(".xlsx"):
            raise HTTPException(400, f"an STTM upload must be a .xlsx workbook, got {name!r}")
    elif kind == "frd":
        if lower.endswith(".docx"):
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as handle:
                handle.write(payload)
                probe = Path(handle.name)
            try:
                discover_frd(read_docx(probe), _require_store().config.extractor.frd)
            except FrdDocxError as exc:
                raise HTTPException(400, f"not an F1/F2 FRD document: {exc}") from exc
            finally:
                probe.unlink(missing_ok=True)
        elif not lower.endswith(".json"):
            raise HTTPException(
                400,
                "an FRD upload must be a .contract.json (FRD→STTM agent) or an FRD "
                f".docx, got {name!r}",
            )
        else:
            try:
                FrdContract.model_validate_json(payload)
            except Exception as exc:  # noqa: BLE001 — surface the first validation line
                raise HTTPException(
                    400,
                    "not a valid FRD contract: " + str(exc).splitlines()[0][:200]
                    + " — upload the FRD .docx instead, or run the FRD→STTM agent",
                ) from exc
            if not lower.endswith(".contract.json"):
                name = name[: -len(".json")] + ".contract.json"
    else:
        raise HTTPException(400, f"unknown upload kind {kind!r}")

    from ui.backend import stores as ui_stores

    config = _require_store().config
    dest_dir = ui_stores.inbox_dir(config, "uploads", REPO_ROOT / "inputs" / "uploads")
    dest_dir.mkdir(parents=True, exist_ok=True)      # repo dir or local working copy
    # Write-then-rename, same discipline as the SharePoint import.
    tmp = dest_dir / (name + ".part")
    tmp.write_bytes(payload)
    dest = dest_dir / name
    tmp.replace(dest)
    ui_stores.push_input(config, "uploads", name)    # no-op for the local role
    runner.refresh_inputs()

    try:
        if kind == "sttm":
            # A job, like any STTM choice: selected once the status' job is done.
            job = runner.start_selection(name)
            return {"stored": name, "kind": kind, "selected": False, "job": job}
        runner.select_frd(dest, name)
    except (LiveRunInProgress, SelectionInProgress) as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"stored": name, "kind": kind, "selected": True}


@app.delete("/api/demo/frd")
def clear_frd() -> dict:
    try:
        _require_runner().clear_frd()
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"selected": None}


@app.get("/api/demo/runs")
def past_runs() -> dict:
    """The run folders "Clear past runs" would delete (names only)."""
    from ui.backend import stores

    try:
        return {"runs": stores.run_labels(_require_store().config)}
    except Exception as exc:  # noqa: BLE001 — a remote listing error is a 502, not a 500
        raise HTTPException(502, f"could not list the outputs role: {exc}") from exc


class ClearRunsRequest(BaseModel):
    confirm: bool = False   # deletion is permanent


@app.post("/api/demo/runs/clear")
def clear_past_runs(req: ClearRunsRequest) -> dict:
    """Delete every past run folder (demo_<timestamp>) in the outputs role —
    the remote copy too. Needs confirm: true; refused while a run is in
    progress. Nothing else in the outputs role is touched."""
    if not req.confirm:
        raise HTTPException(400, "clearing runs deletes them permanently — send confirm: true")
    try:
        result = _require_runner().clear_runs()
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"clearing runs failed: {exc}") from exc
    return result


@app.get("/api/demo/output-options")
def output_options() -> list[str]:
    """The outputs a run can produce — exactly these (codegen.output_modes)."""
    from codegen.output_modes import OUTPUT_OPTIONS

    return list(OUTPUT_OPTIONS)


class OutputModeRequest(BaseModel):
    # notebook | framework; a retired value (both / rfc / all) maps to both
    # outputs with a one-time notice. null = config default
    mode: str | None = None


@app.post("/api/demo/output-mode")
def select_output_mode(req: OutputModeRequest) -> dict:
    try:
        _require_runner().select_output_mode(req.mode)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return demo_status()


class OutputPartsRequest(BaseModel):
    # any subset of notebook | framework; [] = nothing selected (a run is
    # refused); null = the config default
    parts: list[str] | None = None


@app.post("/api/demo/output-parts")
def select_output_parts(req: OutputPartsRequest) -> dict:
    try:
        _require_runner().select_output_parts(req.parts)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return demo_status()


class GenerationOptionsRequest(BaseModel):
    # null = the config default for that knob
    conventions_profile: str | None = None
    iig_template: str | None = None
    playbook_template: str | None = None


@app.get("/api/demo/generation-options")
def generation_options() -> dict:
    """M6: the conventions profile / IIG template / playbook template
    selectors — options from config, selection (None = default)."""
    return _require_runner().generation_options()


@app.post("/api/demo/generation-options")
def select_generation_options(req: GenerationOptionsRequest) -> dict:
    try:
        _require_runner().select_generation_options(
            conventions_profile=req.conventions_profile, iig_template=req.iig_template,
            playbook_template=req.playbook_template)
    except LiveRunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _require_runner().generation_options()


@app.get("/api/feeds/{slug}/download")
def download_generated_file(slug: str, path: str) -> Response:
    """Binary download (framework workbooks / inserts, the assembled
    notebook) with containment."""
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
        else "application/x-ipynb+json" if name.endswith(".ipynb")
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


@app.post("/api/demo/workbook", status_code=202)
def select_workbook(req: WorkbookSelectRequest) -> dict:
    """Choose the STTM — **202 + a job, at once** (M9.3 addendum,
    APP_CHOOSER_BUG: this request used to download, parse and pair before it
    answered, and hung the App). Locate → download → classify → pair FRD → pair
    VDD → record run in a background job, each step with a timeout; nothing is
    selected until all have succeeded. ``GET /api/demo/status`` carries the job
    (``selection_job``: state running | done | failed, the steps, ``error``
    {code: not_found | timeout | failed, message}, ``pairing.frd`` /
    ``pairing.vdd`` = {chosen, rule, reason, scope, candidates, question}) and
    the one record of what is selected (``selection``). A failed job leaves the
    STTM UNSELECTED (``selection_error``) — never the config default. 409 while
    a run or another selection is in progress."""
    runner = _require_runner()
    try:
        job = runner.start_selection(req.name)
    except (LiveRunInProgress, SelectionInProgress) as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"job": job}


@app.post("/api/demo/workbook/reclassify")
def reclassify_workbook(req: WorkbookSelectRequest) -> dict:
    """M9.3: read an ``unreadable`` workbook again (a person asked — the
    background index never retries on its own)."""
    try:
        _require_runner().reclassify_workbook(req.name)
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
    from ui.backend import stores as ui_stores

    inbox = ui_stores.inbox_dir(_require_store().config, "sharepoint",
                                REPO_ROOT / "inputs" / "sharepoint")

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
    return {"configured": _reference_documents_present(store.config),
            **governance_checks_payload(store.config, REPO_ROOT, facts)}


def _reference_documents_present(config) -> bool:
    """The request-time checks are grounded in demo.input_documents; when
    none of those files resolve (an ACFC deployment), the panels hide and
    the endpoints say so with ``configured: false``."""
    from codegen.demo_sources import scan_reference_documents

    try:
        return bool(scan_reference_documents(config, REPO_ROOT)["present"])
    except Exception:  # noqa: BLE001 — a scan failure reads as unconfigured
        return False


@app.get("/api/demo/input-requirements")
def input_requirements() -> dict:
    """The FRD contract evaluated against the client requirements deck,
    read LIVE from the input dirs (codegen.input_requirements). The one
    reference document consumed in processing; absent deck → absent check."""
    config = _require_store().config
    return {"configured": _reference_documents_present(config),
            **input_requirements_payload(config, REPO_ROOT)}


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
