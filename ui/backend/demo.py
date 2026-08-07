"""Live demo runner: the FULL pipeline with real Layer-2 reasoning.

extract-sttm on the demo workbook → resolve against the demo FRD →
per-feed generate with ``dry_run=False`` → gate. Runs on a background
thread so the UI can poll stage-level progress; a single-run guard rejects
concurrent live runs; any failure lands in ``state="failed"`` with the
error message and never crashes the server.

Isolation: every live run writes under ``out/demo_<timestamp>/`` — never
the default out/ tree and never the tracked replay fixtures.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime

from codegen.extract import extract_to_file
from codegen.resolve.resolver import resolve_pair
from ui.backend.service import REPO_ROOT, FailedRun, FeedRun, GenerationStore


class LiveRunInProgress(RuntimeError):
    """A live run is already in flight (surface as HTTP 409)."""


class DemoRunner:
    """One live run at a time; stage list is append-only per run."""

    def __init__(self, store: GenerationStore, work=None) -> None:
        self._store = store
        self._work = work or self._execute  # injectable for tests
        self._lock = threading.Lock()
        self.state: str = "idle"  # idle | running | done | failed
        self.stages: list[dict] = []
        self.error: str | None = None

    def status(self) -> dict:
        return {"state": self.state, "stages": list(self.stages), "error": self.error}

    def start_live(self) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("a live demo run is already in progress")
            self.state = "running"
            self.stages = []
            self.error = None
        thread = threading.Thread(target=self._run, name="live-demo-run", daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            self._work()
            self.state = "done"
        except Exception as exc:  # noqa: BLE001 — must release the guard and surface, not crash
            self.error = f"{type(exc).__name__}: {exc}"
            self.state = "failed"

    def _stage(self, name: str, detail: str = "") -> None:
        self.stages.append({"stage": name, "detail": detail, "at": time.time()})

    def _execute(self) -> None:
        config = self._store.config
        label = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_root = REPO_ROOT / config.output.dir / label
        reports_root = run_root / "reports"
        run_root.mkdir(parents=True, exist_ok=True)

        frd_path = REPO_ROOT / config.contracts.dir / config.demo.frd
        workbook_path = REPO_ROOT / config.demo.workbook
        contract_path = run_root / "extracted_sttm.contract.json"

        self._stage("extracting workbook", f"{workbook_path.name} → STTM mapping contract")
        extract_to_file(workbook_path, frd_path, contract_path, config)

        self._stage("resolving contracts", f"{config.demo.frd} ⋈ extracted contract")
        specs = resolve_pair(frd_path, contract_path, config)

        runs: dict[str, FeedRun] = {}
        failures: list[FailedRun] = []
        for spec in specs:
            slug = spec.feed_slug
            try:
                runs[slug] = self._store._generate_feed(  # noqa: SLF001
                    spec,
                    dry_run=False,
                    skip_tests=True,
                    out_root=run_root,
                    reports_dir=reports_root,
                    on_stage=lambda detail, slug=slug: self._stage(f"{slug}: {detail}"),
                )
            except Exception as exc:  # noqa: BLE001 — one bad feed must not sink the run
                failures.append(FailedRun(label=slug, error=f"{type(exc).__name__}: {exc}"))
        if not runs:
            details = "; ".join(f"{f.label}: {f.error}" for f in failures) or "no feeds resolved"
            raise RuntimeError(f"live run produced no feeds — {details}")

        self._stage("publishing results", f"{len(runs)} feed(s), {len(failures)} failure(s)")
        self._store.adopt(
            runs,
            failures,
            mode="live",
            label=label,
            out_root=run_root,
            reports_root=reports_root,
        )
