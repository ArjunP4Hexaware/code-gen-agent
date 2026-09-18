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


# Output selection as independent PARTS (what the UI toggles) mapped onto
# the generator's single mode. "all" is its own part — selecting it is not
# the same UI state as ticking the three others, even though it generates
# the same set. An rfc part always carries the framework artefacts it is
# built from (the generator writes them either way).
OUTPUT_PARTS = ("notebook", "framework", "rfc", "all")
_MODE_TO_PARTS = {
    "notebook": ["notebook"],
    "framework": ["framework"],
    "both": ["notebook", "framework"],
    "rfc": ["rfc"],
    "all": ["all"],
}


def parts_for_mode(mode: str) -> list[str]:
    return list(_MODE_TO_PARTS[mode])


def mode_for_parts(parts: list[str]) -> str | None:
    """None when nothing is selected (a run is refused)."""
    chosen = set(parts)
    if not chosen:
        return None
    if "all" in chosen or ("notebook" in chosen and "rfc" in chosen):
        return "all"
    if "rfc" in chosen:
        return "rfc"
    if "notebook" in chosen and "framework" in chosen:
        return "both"
    return "framework" if "framework" in chosen else "notebook"


class DemoRunner:
    """One live run at a time; stage list is append-only per run."""

    def __init__(self, store: GenerationStore, work=None) -> None:
        self._store = store
        self._work = work or self._execute  # injectable for tests
        self._lock = threading.Lock()
        self.state: str = "idle"  # idle | running | needs_layout | done | failed
        # M2.5 layout resolution: while a run waits for the human to place
        # unresolved roles, ``layout_questions`` holds the question list
        # (grouped by document in the UI) and ``_layout_answers`` the reply.
        self.layout_questions: list[dict] = []
        self.layout_report: dict | None = None
        self._layout_event = threading.Event()
        self._layout_answers: dict | None = None
        self.stages: list[dict] = []
        self.error: str | None = None
        # Label of the most recent COMPLETED run, so the UI can restore its
        # results (via the past-live-run loader) from any later state.
        self.last_run_label: str | None = None
        # The operator's chosen STTM workbook. None = the config default.
        # In-memory only: a restart returns to config.demo.workbook.
        self.selected_workbook: Path | None = None
        # Output selection (parts, see OUTPUT_PARTS). None = the config
        # default; [] = nothing selected (Generate refused); in-memory only.
        self.output_parts: list[str] | None = None
        # The chosen FRD contract path. None = the demo golden (config.demo
        # .frd) — the pinned default that keeps the golden path byte-
        # identical. Set via /api/demo/frd (local file or a materialized
        # upstream contract); in-memory only.
        self.selected_frd: Path | None = None
        self.selected_frd_label: str | None = None
        # {"frd": name, "rule": pairing_map|ticket|name_stem} when the FRD was
        # selected automatically for the chosen STTM; None for a manual pick.
        self.frd_auto_paired: dict | None = None
        # M3: optional Vendor Data Dictionary (third input); None = no VDD.
        self.selected_vdd: Path | None = None
        # {"vdd": name, "rule": …} when choosing the STTM selected it; None manual.
        self.vdd_auto_paired: dict | None = None
        # M4/M5 generation options (None = the config default each): the
        # conventions profile, the IIG template version and the playbook
        # template. In-memory only, like the output mode.
        self.conventions_profile: str | None = None
        self.iig_template: str | None = None
        self.playbook_template: str | None = None
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
        self.frd_auto_paired = None

    def select_vdd(self, path: Path | None) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the VDD while a live run is in progress")
        self.selected_vdd = path
        self.vdd_auto_paired = None

    def clear_frd(self) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the FRD while a live run is in progress"
                )
        self.selected_frd = None
        self.selected_frd_label = None
        self.frd_auto_paired = None

    def local_frd_candidates(self) -> dict[str, Path]:
        """FRDs a run can use without a network call: contract JSONs and
        FRD-named .docx in the contracts dir and the three inboxes (any .docx
        in the uploads inbox — only a kind=frd upload puts one there)."""
        from codegen.demo_sources import canonical_document_name

        contracts_dir = REPO_ROOT / self._store.config.contracts.dir
        uploads = REPO_ROOT / "inputs" / "uploads"
        dirs = (contracts_dir, REPO_ROOT / "inputs" / "databricks",
                REPO_ROOT / "inputs" / "sharepoint", uploads)
        found: dict[str, Path] = {}
        for directory in dirs:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.contract.json")):
                found.setdefault(path.name, path)
            for path in sorted(directory.glob("*.docx")):
                if path.name.startswith("~$"):
                    continue
                if directory == uploads or canonical_document_name(path.name).startswith("frd"):
                    found.setdefault(path.name, path)
        return found

    def auto_pair_frd(self, sttm_name: str) -> dict | None:
        """Select the FRD associated with the chosen STTM when one is present
        (config pairing map -> shared ticket -> unique name stem). A manual
        FRD choice is replaced only when a pair is found; a stale automatic
        pair from a previous STTM is cleared."""
        from codegen.demo_sources import auto_pair_frd

        candidates = self.local_frd_candidates()
        match = auto_pair_frd(sttm_name, list(candidates),
                              explicit_map=self._store.config.demo.pairing_map)
        if match is None:
            if self.frd_auto_paired is not None:
                self.selected_frd = None
                self.selected_frd_label = None
                self.frd_auto_paired = None
            return None
        frd_name, rule = match
        self.selected_frd = candidates[frd_name]
        self.selected_frd_label = frd_name
        self.frd_auto_paired = {"frd": frd_name, "rule": rule}
        return self.frd_auto_paired

    def auto_pair_vdd(self, sttm_name: str) -> dict | None:
        """Select the Vendor Data Dictionary associated with the chosen STTM
        when one is present among the listed workbooks (config vdd_pairing_map
        -> shared ticket -> unique name stem); same override rules as the FRD."""
        from codegen.demo_sources import auto_pair_vdd

        candidates = {c["name"]: c for c in self.workbook_choices() if c["name"] != sttm_name}
        match = auto_pair_vdd(sttm_name, list(candidates),
                              explicit_map=self._store.config.demo.vdd_pairing_map)
        if match is None:
            if self.vdd_auto_paired is not None:
                self.selected_vdd = None
                self.vdd_auto_paired = None
            return None
        vdd_name, rule = match
        for _source, directory in self._workbook_dirs():
            candidate = directory / vdd_name
            if candidate.is_file():
                self.selected_vdd = candidate
                self.vdd_auto_paired = {"vdd": vdd_name, "rule": rule}
                return self.vdd_auto_paired
        return None

    @property
    def output_mode(self) -> str | None:
        """The generator mode the selected parts map onto; None = config
        default when nothing was selected, also None when the selection is
        empty (callers refuse a run in that case)."""
        if self.output_parts is None:
            return None
        return mode_for_parts(self.output_parts)

    def effective_output_parts(self) -> list[str]:
        if self.output_parts is not None:
            return list(self.output_parts)
        return parts_for_mode(self._store.config.output.mode)

    def select_output_mode(self, mode: str | None) -> None:
        """Compatibility entry: a single mode selects its parts."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output mode while a live run is in progress"
                )
        if mode is not None and mode not in _MODE_TO_PARTS:
            raise ValueError(f"unknown output mode {mode!r}")
        self.output_parts = None if mode is None else parts_for_mode(mode)

    def select_output_parts(self, parts: list[str] | None) -> None:
        """The UI's toggles: any subset of OUTPUT_PARTS, empty allowed
        (Generate is refused until one is chosen); None = config default."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output while a live run is in progress"
                )
        if parts is None:
            self.output_parts = None
            return
        unknown = [p for p in parts if p not in OUTPUT_PARTS]
        if unknown:
            raise ValueError(f"unknown output part(s) {unknown!r}; expected {OUTPUT_PARTS}")
        self.output_parts = list(dict.fromkeys(parts))

    def select_generation_options(self, *, conventions_profile: str | None = None,
                                  iig_template: str | None = None,
                                  playbook_template: str | None = None) -> None:
        """Validate against the config and record the choice (None = default)."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change generation options while a live run is in progress")
        config = self._store.config
        config.conventions.get(conventions_profile)      # raises ValueError when unknown
        config.metadata.resolve(iig_template)
        config.playbook.resolve(playbook_template)
        self.conventions_profile = conventions_profile
        self.iig_template = iig_template
        self.playbook_template = playbook_template

    def generation_options(self) -> dict:
        """What the selectors offer + what is selected (None = config default)."""
        config = self._store.config
        return {
            "conventions_profile": {
                "options": sorted(config.conventions.profiles),
                "default": config.conventions.profile,
                "selected": self.conventions_profile,
            },
            "iig_template": {
                "options": ["iig_v1", *sorted(config.metadata.templates)],
                "default": config.metadata.template,
                "selected": self.iig_template,
            },
            "playbook_template": {
                "options": sorted(config.playbook.templates),
                "default": config.playbook.template,
                "selected": self.playbook_template,
            },
        }

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
                    self.auto_pair_frd(name)
                    self.auto_pair_vdd(name)
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
        if self.frd_auto_paired is not None:
            self.selected_frd = None
            self.selected_frd_label = None
            self.frd_auto_paired = None
        if self.vdd_auto_paired is not None:
            self.selected_vdd = None
            self.vdd_auto_paired = None

    def status(self) -> dict:
        return {
            "state": self.state,
            "stages": list(self.stages),
            "error": self.error,
            "last_run_label": self.last_run_label,
            "layout_questions": list(self.layout_questions),
            "layout_report": self.layout_report,
            "frd_auto_paired": self.frd_auto_paired,
            "vdd_auto_paired": self.vdd_auto_paired,
            "output_parts": self.effective_output_parts(),
        }

    def answer_layout(self, answers: dict | None, *, proceed: bool = False,
                      cancel: bool = False) -> None:
        """Deliver the human's role placements to the waiting run (or tell
        it to proceed with empties / to stop)."""
        if self.state != "needs_layout":
            raise LiveRunInProgress("no live run is waiting for layout answers")
        self._layout_answers = {"answers": answers or {}, "proceed": proceed, "cancel": cancel}
        self._layout_event.set()

    def _resolve_layout(self, workbook_path: Path, frd_path: Path, config,
                        vdd_path: Path | None = None):
        """cache -> synonyms -> model -> validate -> user, pausing the run in
        ``needs_layout`` until every question is answered or the human
        chooses to proceed with the unresolved roles read as empty."""
        from codegen.layout.model import build_layout_provider
        from codegen.layout.resolve import parse_answers, resolve_pair

        provider = build_layout_provider(config, dry_run=False, base_dir=REPO_ROOT)
        runtime_cache = REPO_ROOT / config.layout.runtime_cache_dir
        answers: dict = {"sttm": {}, "frd": {}, "vdd": {}}
        while True:
            result = resolve_pair(workbook_path, frd_path, config, provider=provider,
                                  answers=answers, runtime_cache_dir=runtime_cache,
                                  base_dir=REPO_ROOT, vdd_path=vdd_path)
            self.layout_report = result.report()
            if not result.questions:
                return result
            self.layout_questions = [q.as_dict() for q in result.questions]
            self._layout_answers = None
            self._layout_event.clear()
            self.state = "needs_layout"
            self._stage("needs layout", f"{len(result.questions)} unresolved role(s) — "
                                        "waiting for the human")
            self._layout_event.wait()
            self.state = "running"
            reply = self._layout_answers or {}
            self.layout_questions = []
            if reply.get("cancel"):
                raise RuntimeError("layout resolution cancelled by the user")
            merged = parse_answers(reply.get("answers") or {})
            answers = {"sttm": {**answers["sttm"], **merged["sttm"]},
                       "frd": {**answers["frd"], **merged["frd"]},
                       "vdd": {**answers.get("vdd", {}), **merged.get("vdd", {})}}
            if reply.get("proceed"):
                result = resolve_pair(workbook_path, frd_path, config, provider=provider,
                                      answers=answers, runtime_cache_dir=runtime_cache,
                                      base_dir=REPO_ROOT, vdd_path=vdd_path)
                self.layout_report = result.report()
                return result

    def start_live(self) -> None:
        if self.output_parts == []:
            raise ValueError("no output selected — choose at least one of notebook, "
                             "framework artefacts, RFC package, or All")

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
        frd_is_docx = frd_path.suffix.lower() == ".docx"
        if frd_is_docx:
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
                "conventions_profile": self.conventions_profile or config.conventions.profile,
                "iig_template": self.iig_template or config.metadata.template,
                "playbook_template": self.playbook_template or config.playbook.template,
            }, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        frd_path = run_frd

        self._stage("resolving layout", f"{workbook_path.name} (+ {frd_label})")
        resolution = self._resolve_layout(
            workbook_path, self.effective_frd() if frd_is_docx else frd_path, config,
            vdd_path=self.selected_vdd)
        layout_flags = list(resolution.flags)
        vdd_contract_path: Path | None = None
        if self.selected_vdd is not None and resolution.vdd is not None:
            from codegen.extract.vdd import contract_to_json as vdd_to_json
            from codegen.extract.vdd import extract_vdd_contract

            self._stage("extracting VDD", f"{self.selected_vdd.name} → VDD contract")
            vdd_contract, _ = extract_vdd_contract(self.selected_vdd, config,
                                                   layout=resolution.vdd.profile)
            vdd_contract_path = run_root / "vdd.contract.json"
            vdd_contract_path.write_text(vdd_to_json(vdd_contract), encoding="utf-8",
                                         newline="\n")

        self._stage("extracting workbook",
                    f"{workbook_path.name} → STTM mapping contract (FRD: {frd_label})")
        try:
            extract_to_file(workbook_path, frd_path, contract_path, config,
                            layout=resolution.sttm.profile)
        except Exception as exc:
            self._attach_pairing_hint(exc, workbook_path, frd_label)
            raise

        self._stage("resolving contracts", f"{frd_label} ⋈ extracted contract")
        specs = resolve_pair(frd_path, contract_path, config, vdd_path=vdd_contract_path)

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
                    extra_flags=layout_flags,
                    conventions_profile=self.conventions_profile,
                    iig_template=self.iig_template,
                    playbook_template=self.playbook_template,
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
