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
from codegen.gate import compute_verdict, run_generated_tests, run_preflight
from codegen.gate.verdict import GateResult
from codegen.reasoning import build_provider, run_reasoning
from codegen.reasoning.engine import RuleCandidate
from codegen.report import write_generation_report
from codegen.resolve.resolver import ContractMismatchError, resolve_pair
from codegen.rules.compiler import RuleOutcome, compile_rules

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(__file__).resolve().parent / "state"
DECISIONS_PATH = STATE_DIR / "decisions.json"

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


class FailedRun(BaseModel):
    """A pair or feed that failed before the gate could run."""

    model_config = _MODEL_CONFIG

    label: str
    error: str


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
    ) -> None:
        with self._lock:
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
                            spec, dry_run=dry_run, skip_tests=skip_tests
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
    ) -> FeedRun:
        # Mirrors codegen.cli._generate_feed step for step — keep in sync.
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
        stage("emitting code")

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
        )
        written = emit_feed(context, out_root)
        self._write_candidates_artifact(candidates, feed_dir)

        stage("gate")
        checks = run_preflight(feed_dir, self.config)
        tests_skipped = skip_tests or not self.config.gate.run_generated_tests
        if not tests_skipped:
            checks = [
                *checks,
                run_generated_tests(feed_dir, self.config.gate.pytest_tail_lines),
            ]

        gate = compute_verdict(spec.feed_id, outcomes, candidates, checks, tests_skipped)
        write_generation_report(spec, written, outcomes, candidates, gate, reports_dir, out_root)
        return FeedRun(
            spec=spec,
            outcomes=outcomes,
            candidates=candidates,
            gate=gate,
            written_files=[p.relative_to(REPO_ROOT).as_posix() for p in written],
        )

    @staticmethod
    def _write_candidates_artifact(candidates: list[RuleCandidate], feed_dir: Path) -> None:
        if not candidates:
            return
        artifact_dir = feed_dir / "candidates"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload = [c.model_dump() for c in candidates]
        (artifact_dir / "candidates.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
        )

    # -- review decisions ---------------------------------------------------

    def load_decisions(self) -> dict[str, dict[str, dict]]:
        if not DECISIONS_PATH.is_file():
            return {}
        return json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))

    def save_decision(
        self, feed_slug: str, candidate_index: int, decision: Decision, note: str | None
    ) -> dict:
        with self._lock:
            decisions = self.load_decisions()
            feed_decisions = decisions.setdefault(feed_slug, {})
            entry = {"decision": decision, "note": note}
            feed_decisions[str(candidate_index)] = entry
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            DECISIONS_PATH.write_text(json.dumps(decisions, indent=2) + "\n", encoding="utf-8")
            return entry

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

    def read_report(self, feed_slug: str) -> str | None:
        path = self.reports_root / f"{feed_slug}.md"
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
