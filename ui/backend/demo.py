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
from pathlib import Path

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
        # Label of the most recent COMPLETED run, so the UI can restore its
        # results (via the past-live-run loader) from any later state.
        self.last_run_label: str | None = None
        # The operator's chosen STTM workbook. None = the config default.
        # In-memory only: a restart returns to config.demo.workbook.
        self.selected_workbook: Path | None = None
        # Output mode override (notebook | framework | both). None = the
        # config default; in-memory only, same as the workbook choice.
        self.output_mode: str | None = None
        # The chosen FRD contract path. None = the demo golden (config.demo
        # .frd) — the pinned default that keeps the golden path byte-
        # identical. Set via /api/demo/frd (local file or a materialized
        # upstream contract); in-memory only.
        self.selected_frd: Path | None = None
        self.selected_frd_label: str | None = None
        # Structured hint for the failed-run card: when a feed-match
        # failure has a known companion FRD, the UI renders a one-click
        # "choose the pair" button from this. Never an auto-retry.
        self.error_hint: dict | None = None

    def effective_frd(self) -> Path:
        return self.selected_frd or (
            REPO_ROOT / self._store.config.contracts.dir / self._store.config.demo.frd
        )

    def select_frd(self, path: Path, label: str) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the FRD while a live run is in progress"
                )
        self.selected_frd = path
        self.selected_frd_label = label

    def clear_frd(self) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the FRD while a live run is in progress"
                )
        self.selected_frd = None
        self.selected_frd_label = None

    def select_output_mode(self, mode: str | None) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output mode while a live run is in progress"
                )
        if mode is not None and mode not in ("notebook", "framework", "both"):
            raise ValueError(f"unknown output mode {mode!r}")
        self.output_mode = mode

    # -- STTM workbook choice ------------------------------------------------

    def _workbook_dirs(self) -> tuple[tuple[str, Path], ...]:
        """Directories a live run's STTM may come from, with display labels.

        The config workbook's own directory, plus the SharePoint landing dir
        (where ``sharepoint-fetch --dest`` and the UI picker deliver files).
        """
        configured = REPO_ROOT / self._store.config.demo.workbook
        return (
            (configured.parent.relative_to(REPO_ROOT).as_posix(), configured.parent),
            ("inputs/sharepoint", REPO_ROOT / "inputs" / "sharepoint"),
            # Where `codegen databricks-fetch` and the UI's volume fetch land
            # documents — same treatment as the SharePoint inbox.
            ("inputs/databricks", REPO_ROOT / "inputs" / "databricks"),
            # Where the UI's from-device upload (POST /api/demo/upload) lands
            # documents — same treatment as the other two inboxes.
            ("inputs/uploads", REPO_ROOT / "inputs" / "uploads"),
        )

    def effective_workbook(self) -> Path:
        return self.selected_workbook or (REPO_ROOT / self._store.config.demo.workbook)

    def workbook_choices(self) -> list[dict]:
        """Every .xlsx a live run could consume, flagged with the selection.

        Only an EXPLICIT pick counts as selected — before one, the UI shows
        "none chosen" and no row is badged, even though a run would fall
        back to the config default.
        """
        effective = self.selected_workbook
        seen: set[str] = set()
        choices: list[dict] = []
        for source, directory in self._workbook_dirs():
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.xlsx")):
                if path.name.startswith("~$") or path.name in seen:  # Excel lock files / dupes
                    continue
                seen.add(path.name)
                choices.append(
                    {"name": path.name, "source": source, "selected": path == effective}
                )
        return choices

    def select_workbook(self, name: str) -> Path:
        """Pick a workbook BY NAME from the scanned dirs — never a raw path."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
        for _source, directory in self._workbook_dirs():
            if not directory.is_dir():
                continue
            for path in directory.glob("*.xlsx"):
                if path.name == name and not path.name.startswith("~$"):
                    self.selected_workbook = path
                    return path
        raise FileNotFoundError(
            f"no STTM workbook named {name!r} in "
            + " or ".join(src for src, _ in self._workbook_dirs())
        )

    def clear_workbook(self) -> None:
        """Back to 'none chosen' — the presenter's reset for the choose step."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
        self.selected_workbook = None

    def status(self) -> dict:
        return {
            "state": self.state,
            "stages": list(self.stages),
            "error": self.error,
            "last_run_label": self.last_run_label,
        }

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

    def _attach_pairing_hint(self, exc: Exception, workbook_path: Path,
                             frd_label: str) -> None:
        """On a feed-match failure, name the FRD the run used and — when
        the pairing helpers know a companion — offer it. Information only;
        choosing remains the human's act, and there is no auto-retry."""
        if "matches 0 FRD feeds" not in str(exc):
            return
        try:
            from codegen.demo_sources import pair_sttm_with_frd, suggest_pairs
            from codegen.upstream_contracts import list_contracts

            doc_ids = [row["doc_id"] for row in list_contracts(self._store.config)]
            explicit = pair_sttm_with_frd(
                [workbook_path.name], doc_ids,
                explicit_map=self._store.config.demo.pairing_map,
            )
            suggested = suggest_pairs([workbook_path.name], doc_ids)
            candidate = explicit.get(workbook_path.name) or suggested.get(
                workbook_path.name
            )
        except Exception:  # noqa: BLE001, S110 — offline: the hint is optional
            candidate = None
        if candidate:
            self.error_hint = {
                "sttm": workbook_path.name,
                "frd_used": frd_label,
                "candidate_doc_id": candidate,
                "message": (
                    f"This run used FRD '{frd_label}'. A companion FRD "
                    f"'{candidate}' is available from the FRD→STTM agent; "
                    "choose it in the STTM picker."
                ),
            }

    def _stage(self, name: str, detail: str = "") -> None:
        self.stages.append({"stage": name, "detail": detail, "at": time.time()})

    def _execute(self) -> None:
        config = self._store.config
        label = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_root = REPO_ROOT / config.output.dir / label
        reports_root = run_root / "reports"
        run_root.mkdir(parents=True, exist_ok=True)

        frd_path = self.effective_frd()
        frd_label = self.selected_frd_label or frd_path.name
        workbook_path = self.effective_workbook()
        contract_path = run_root / "extracted_sttm.contract.json"

        self.error_hint = None
        # Self-contained run directory: copy the FRD the run actually used
        # (content-identical => provenance hashes unchanged) and record run
        # metadata, so a past run reloads with ITS pair — never the pinned
        # demo golden (the View-results bug of 2026-08-27).
        import json as json_module
        import shutil

        run_frd = run_root / "frd.contract.json"
        if frd_path.suffix.lower() == ".docx":
            # M2: a .docx FRD is extracted into the run's own contract file
            # (deterministic, stdlib) — the rest of the path is unchanged.
            from codegen.extract.frd_docx import contract_to_json, extract_frd_contract

            self._stage("extracting FRD", f"{frd_path.name} → FRD feed contract (docx)")
            frd_contract, _profile = extract_frd_contract(frd_path, config)
            run_frd.write_text(contract_to_json(frd_contract), encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(frd_path, run_frd)
        (run_root / "run_meta.json").write_text(
            json_module.dumps({
                "frd_label": frd_label,
                "sttm_workbook": workbook_path.name,
                "output_mode": self.output_mode or config.output.mode,
            }, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        frd_path = run_frd

        self._stage("extracting workbook",
                    f"{workbook_path.name} → STTM mapping contract (FRD: {frd_label})")
        try:
            extract_to_file(workbook_path, frd_path, contract_path, config)
        except Exception as exc:
            self._attach_pairing_hint(exc, workbook_path, frd_label)
            raise

        self._stage("resolving contracts", f"{frd_label} ⋈ extracted contract")
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
                    output_mode=self.output_mode,
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
        self.last_run_label = label
