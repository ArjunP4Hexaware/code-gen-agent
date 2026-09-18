"""In-process generation service for the demo UI.

Runs the exact same pipeline as ``codegen.cli._generate_feed`` (resolve ->
compile rules -> Layer 2 -> render -> gate -> report) but keeps the structured
objects (spec, outcomes, candidates, gate) so the API can serve them as JSON
instead of parsing console output or markdown. The UI never re-implements
generation logic — it only invokes this sequence and reads its artifacts.

Candidate approve/reject decisions are a UI-side overlay persisted to
``ui/backend/state/decisions.json`` (gitignored). Per the two-layer trust
rule, an approved candidate is still never merged into generated modules —
that remains v2; the decision file records the engineer's review only.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from codegen.config import Config, load_config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.emit.context import TemplateGapError, build_context
from codegen.emit.emitter import emit_feed
from codegen.faq import faq_for_spec
from codegen.gate import compute_verdict, run_generated_tests, run_preflight
from codegen.gate.verdict import GateResult
from codegen.reasoning import build_provider, run_reasoning
from codegen.reasoning.engine import RuleCandidate, segmented_review_items
from codegen.report import write_generation_report
from codegen.resolve.resolver import ContractMismatchError, resolve_pair
from codegen.rules.compiler import RuleOutcome, compile_rules

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(__file__).resolve().parent / "state"
DECISIONS_PATH = STATE_DIR / "decisions.json"
# v2: decisions are scoped per run (mock / demo_<ts> / replay set) so an
# approval made while rehearsing one state never bleeds into another.
DECISIONS_VERSION = 2

Decision = Literal["pending", "approved", "rejected"]
# Which pipeline produced the state the UI is showing.
RunMode = Literal["mock", "live", "replay"]


class FeedRun(BaseModel):
    """Everything one generation run produced for one feed."""

    model_config = _MODEL_CONFIG

    spec: ResolvedFeedSpec
    outcomes: list[RuleOutcome]
    candidates: list[RuleCandidate]
    gate: GateResult
    written_files: list[str]  # repo-relative, posix
    error: str | None = None
    # Option B artefact summary (framework/both modes): file names, row
    # counts per tab, badge coverage, framework-assigned blank columns.
    framework: dict | None = None


class FailedRun(BaseModel):
    """A pair or feed that failed before the gate could run."""

    model_config = _MODEL_CONFIG

    label: str
    error: str


class NothingToGenerateError(RuntimeError):
    """Raised when a generate is requested but config lists no contract pairs."""


class GenerationStore:
    """In-memory results of the latest run, plus persisted review decisions."""

    def __init__(self, config_path: str) -> None:
        self._lock = threading.Lock()
        self.config: Config = load_config(config_path)
        self.runs: dict[str, FeedRun] = {}
        self.failures: list[FailedRun] = []
        self.has_run = False
        # Demo modes (live/replay) swap the whole result set and read files
        # from their own isolated roots; mock is the default.
        self.mode: RunMode = "mock"
        self.label: str | None = None
        self.out_root: Path = REPO_ROOT / self.config.output.dir
        self.reports_root: Path = REPO_ROOT / self.config.output.reports_dir

    def adopt(
        self,
        runs: dict[str, FeedRun],
        failures: list[FailedRun],
        *,
        mode: RunMode,
        label: str | None,
        out_root: Path,
        reports_root: Path,
    ) -> None:
        """Atomically swap the served state for a demo (live/replay) run."""
        with self._lock:
            self.runs = runs
            self.failures = failures
            self.mode = mode
            self.label = label
            self.out_root = out_root
            self.reports_root = reports_root
            self.has_run = True

    # -- generation ---------------------------------------------------------

    def generate(
        self,
        *,
        only_slug: str | None = None,
        dry_run: bool = True,
        skip_tests: bool = True,
        output_mode: str | None = None,
    ) -> None:
        with self._lock:
            # Refuse loudly BEFORE touching state (mirrors the CLI): with no
            # pairs, resetting mode/out_root here would strand a loaded
            # live/replay run's feeds pointing at roots that hold no files.
            if not self.config.contracts.pairs:
                raise NothingToGenerateError(
                    "No contract pairs are configured (contracts.pairs) — use the Generate "
                    "page to run from an STTM workbook and its FRD."
                )
            # A plain generate returns the UI to mock state and default roots.
            self.mode = "mock"
            self.label = None
            self.out_root = REPO_ROOT / self.config.output.dir
            self.reports_root = REPO_ROOT / self.config.output.reports_dir
            contracts_dir = REPO_ROOT / self.config.contracts.dir
            failures: list[FailedRun] = []
            for pair in self.config.contracts.pairs:
                frd_path = contracts_dir / pair.frd
                sttm_path = contracts_dir / pair.sttm
                try:
                    specs = resolve_pair(frd_path, sttm_path, self.config)
                except (ContractMismatchError, ValueError) as exc:
                    failures.append(
                        FailedRun(label=f"{frd_path.name} + {sttm_path.name}", error=str(exc))
                    )
                    continue
                for spec in specs:
                    if only_slug is not None and spec.feed_slug != only_slug:
                        continue
                    try:
                        self.runs[spec.feed_slug] = self._generate_feed(
                            spec, dry_run=dry_run, skip_tests=skip_tests,
                            output_mode=output_mode,
                        )
                    except TemplateGapError as exc:
                        failures.append(FailedRun(label=spec.feed_id, error=f"template gap: {exc}"))
            if only_slug is None:
                self.failures = failures
            else:
                self.failures.extend(failures)
            self.has_run = True

    def _generate_feed(
        self,
        spec: ResolvedFeedSpec,
        *,
        dry_run: bool,
        skip_tests: bool,
        out_root: Path | None = None,
        reports_dir: Path | None = None,
        candidates_override: list[RuleCandidate] | None = None,
        on_stage: Callable[[str], None] | None = None,
        output_mode: str | None = None,
        extra_flags: list[str] | None = None,
        conventions_profile: str | None = None,
        iig_template: str | None = None,
        playbook_template: str | None = None,
    ) -> FeedRun:
        # Mirrors codegen.cli._generate_feed step for step — keep in sync.
        from codegen.gate.drag_fill import drag_fill_flags
        from codegen.gate.vdd_check import vdd_cross_check

        vdd_flags, vdd_check = vdd_cross_check(spec, self.config)
        extra_flags = [*(extra_flags or []), *spec.provenance_flags, *drag_fill_flags(spec),
                       *vdd_flags]
        # out_root/reports_dir isolate demo runs; candidates_override replays
        # a recorded Layer-2 result instead of calling any provider.
        stage = on_stage or (lambda _detail: None)
        out_root = out_root if out_root is not None else REPO_ROOT / self.config.output.dir
        reports_dir = (
            reports_dir if reports_dir is not None else REPO_ROOT / self.config.output.reports_dir
        )
        feed_dir = out_root / spec.feed_slug

        stage("compiling rules")
        outcomes = compile_rules(spec)
        if candidates_override is not None:
            candidates = candidates_override
        else:
            stage("Layer-2 reasoning" + ("" if dry_run else " (live)"))
            provider = build_provider(self.config, dry_run)
            candidates = run_reasoning(spec, outcomes, provider)
            # Segmented-extraction review items join the same review flow;
            # replayed candidate sets already carry them (they are written
            # into candidates.json), so only the fresh path adds them.
            candidates = [*segmented_review_items(spec), *candidates]
        stage("emitting code")
        # Three-input model: mirrors cli._generate_feed — FAQ file answers
        # plus contract prefills; missing file => defaults, flagged by gate.
        faq = faq_for_spec(spec, self.config, base_dir=REPO_ROOT)

        duplicate_outcome = next(
            (o for o in outcomes if o.feature == "allow_duplicate_file_name"), None
        )
        context = build_context(
            spec,
            self.config,
            allow_duplicate_file_name=True,
            duplicate_rule_text=(
                duplicate_outcome.rule_text if duplicate_outcome is not None else None
            ),
            notification_rule_texts=[
                o.rule_text for o in outcomes if o.classification == "notification"
            ],
            faq=faq,
        )
        # Option A/B branch — MIRRORS cli._generate_feed (its helpers are
        # reused directly so the two cannot drift).
        from codegen.cli import _emit_framework_only, _read_ddl_sources, _run_emit_framework

        effective_mode = output_mode or self.config.output.mode
        framework_artefacts = None
        rfc_artefacts = None
        checks = None
        tests_skipped = skip_tests or not self.config.gate.run_generated_tests
        if effective_mode in ("framework", "rfc"):
            stage("framework artefacts")
            written, checks, tests_skipped, ddl_sources = _emit_framework_only(
                context, spec, self.config, feed_dir, skip_tests
            )
            framework_artefacts = _run_emit_framework(
                spec, faq, ddl_sources, self.config, out_root, outcomes,
                base_dir=REPO_ROOT, conventions_profile=conventions_profile,
                iig_template=iig_template,
            )
            written = [*written, *framework_artefacts.files]
            if effective_mode == "rfc":
                stage("RFC package")
                from codegen.emit.rfc import emit_rfc_package

                rfc_artefacts = emit_rfc_package(
                    spec, faq, self.config, out_root, framework_artefacts,
                    flags_so_far=[*extra_flags, *framework_artefacts.flags],
                    conventions_profile=conventions_profile, iig_template=iig_template,
                    playbook_template=playbook_template, base_dir=REPO_ROOT,
                )
                written = [*written, *rfc_artefacts.files]
        else:
            written = emit_feed(context, out_root)
            if effective_mode in ("both", "all"):
                stage("framework artefacts")
                ddl_sources = _read_ddl_sources(feed_dir)
                framework_artefacts = _run_emit_framework(
                    spec, faq, ddl_sources, self.config, out_root, outcomes,
                    base_dir=REPO_ROOT, conventions_profile=conventions_profile,
                    iig_template=iig_template,
                )
                written = [*written, *framework_artefacts.files]
                if effective_mode == "all":
                    stage("RFC package")
                    from codegen.emit.rfc import emit_rfc_package

                    rfc_artefacts = emit_rfc_package(
                        spec, faq, self.config, out_root, framework_artefacts,
                        flags_so_far=[*extra_flags, *framework_artefacts.flags],
                        conventions_profile=conventions_profile, iig_template=iig_template,
                        playbook_template=playbook_template, base_dir=REPO_ROOT,
                    )
                    written = [*written, *rfc_artefacts.files]
        if framework_artefacts is not None:
            extra_flags = [*extra_flags, *framework_artefacts.flags]
        if rfc_artefacts is not None:
            extra_flags = [*extra_flags, *rfc_artefacts.flags]
        self._write_candidates_artifact(candidates, feed_dir)

        stage("gate")
        if checks is None:
            checks = run_preflight(feed_dir, self.config)
        if vdd_check is not None:
            checks = [*checks, vdd_check]
            if not tests_skipped:
                checks = [
                    *checks,
                    run_generated_tests(feed_dir, self.config.gate.pytest_tail_lines),
                ]

        gate = compute_verdict(
            spec.feed_id,
            outcomes,
            candidates,
            checks,
            tests_skipped,
            faq=faq,
            standards=self.config.engineering_standards,
            extra_flags=extra_flags,
        )
        write_generation_report(
            spec,
            written,
            outcomes,
            candidates,
            gate,
            reports_dir,
            out_root,
            inputs_summary=context["provenance"]["inputs"],
        )
        framework_summary = None
        if framework_artefacts is not None:
            from codegen.emit.framework import report_section

            with open(reports_dir / f"{spec.feed_slug}.md", "a",
                      encoding="utf-8", newline="\n") as handle:
                handle.write(report_section(framework_artefacts))
                if rfc_artefacts is not None:
                    from codegen.emit.rfc import report_section as rfc_report_section

                    handle.write(rfc_report_section(rfc_artefacts))
            framework_summary = {
                "files": [p.name for p in framework_artefacts.files],
                "row_counts": framework_artefacts.row_counts,
                "coverage": framework_artefacts.coverage,
                "flagged_blank_columns": framework_artefacts.flagged_blank_columns,
            }
        return FeedRun(
            spec=spec,
            outcomes=outcomes,
            candidates=candidates,
            gate=gate,
            written_files=[p.relative_to(REPO_ROOT).as_posix() for p in written],
            framework=framework_summary,
        )

    @staticmethod
    def _write_candidates_artifact(candidates: list[RuleCandidate], feed_dir: Path) -> None:
        if not candidates:
            return
        artifact_dir = feed_dir / "candidates"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload = []
        for candidate in candidates:
            entry = candidate.model_dump()
            if entry.get("kind") == "layer2":
                # Default-kind entries serialize exactly as before the
                # segmented dialect — flat candidates.json stays byte-stable.
                entry.pop("kind", None)
                entry.pop("detail", None)
                entry.pop("citation", None)
            payload.append(entry)
        (artifact_dir / "candidates.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
        )

    # -- review decisions ---------------------------------------------------

    @property
    def run_key(self) -> str:
        """Identity of the currently loaded run: decisions are scoped to it."""
        return self.label or "mock"

    @staticmethod
    def _load_all_decisions() -> dict[str, dict[str, dict[str, dict]]]:
        if not DECISIONS_PATH.is_file():
            return {}
        payload = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("version") != DECISIONS_VERSION:
            # Pre-v2 shape was keyed by rule alone and bled across runs and
            # modes — disposable dev state, deliberately discarded.
            return {}
        return payload.get("runs", {})

    @staticmethod
    def _write_all_decisions(runs: dict) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"version": DECISIONS_VERSION, "runs": runs}
        DECISIONS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def load_decisions(self) -> dict[str, dict[str, dict]]:
        """Decisions for the CURRENT run only — each run starts pending."""
        return self._load_all_decisions().get(self.run_key, {})

    def save_decision(
        self, feed_slug: str, candidate_index: int, decision: Decision, note: str | None
    ) -> dict:
        with self._lock:
            all_runs = self._load_all_decisions()
            feed_decisions = all_runs.setdefault(self.run_key, {}).setdefault(feed_slug, {})
            entry = {"decision": decision, "note": note}
            feed_decisions[str(candidate_index)] = entry
            self._write_all_decisions(all_runs)
            return entry

    def reset_decisions(self) -> None:
        """Clear the CURRENT run's slate (other runs' decisions are kept)."""
        with self._lock:
            all_runs = self._load_all_decisions()
            if all_runs.pop(self.run_key, None) is not None:
                self._write_all_decisions(all_runs)

    # -- file access --------------------------------------------------------

    def read_generated_file(self, feed_slug: str, rel_path: str) -> str:
        """Read one generated file; refuses paths outside the feed's out dir.

        Reads from the CURRENT mode's output root, so live/replay runs serve
        their own isolated artifacts.
        """
        feed_dir = (self.out_root / feed_slug).resolve()
        target = (feed_dir / rel_path).resolve()
        if not target.is_relative_to(feed_dir):
            raise PermissionError(f"path escapes feed directory: {rel_path}")
        if not target.is_file():
            raise FileNotFoundError(rel_path)
        return target.read_text(encoding="utf-8")

    def read_generated_bytes(self, feed_slug: str, rel_path: str) -> bytes:
        """Binary twin of read_generated_file (xlsx downloads); same containment."""
        feed_dir = (self.out_root / feed_slug).resolve()
        target = (feed_dir / rel_path).resolve()
        if not target.is_relative_to(feed_dir):
            raise PermissionError(f"path escapes feed directory: {rel_path}")
        if not target.is_file():
            raise FileNotFoundError(rel_path)
        return target.read_bytes()

    def read_report(self, feed_slug: str) -> str | None:
        path = self.reports_root / f"{feed_slug}.md"
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
