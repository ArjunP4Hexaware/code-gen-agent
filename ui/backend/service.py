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
from codegen.emit.context import TemplateGapError
from codegen.gate.verdict import GateResult

# post60: the feed pipeline is codegen.cli.generate_feed_result (the CLI's);
# build_provider stays importable here for callers that patch it.
from codegen.reasoning import build_provider  # noqa: F401
from codegen.reasoning.engine import RuleCandidate
from codegen.resolve.resolver import ContractMismatchError, resolve_pair
from codegen.rules.compiler import RuleOutcome

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
    """Everything one generation run produced for one feed.

    D1 post51: under pydantic < 2.10 the ``model_usage`` field (an API key the
    frontend reads, so not renamed) printed a protected-namespace UserWarning on
    import; ``protected_namespaces=()`` silences it for this model only."""

    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())

    spec: ResolvedFeedSpec
    outcomes: list[RuleOutcome]
    candidates: list[RuleCandidate]
    gate: GateResult
    written_files: list[str]  # repo-relative, posix
    error: str | None = None
    # Option B artefact summary (framework mode): file names, row
    # counts per tab, badge coverage, framework-assigned blank columns.
    framework: dict | None = None
    # What this feed's run did with a model, per stage
    # (codegen.reasoning.usage.StageUsage.as_dict — carries the label).
    model_usage: list[dict] | None = None


class FailedRun(BaseModel):
    """A pair or feed that failed before the gate could run."""

    model_config = _MODEL_CONFIG

    label: str
    error: str


class NothingToGenerateError(RuntimeError):
    """Raised when a generate is requested but config lists no contract pairs."""


def display_path(path: Path) -> str:
    """A generated file as the UI shows it: repo-relative when the run lives
    under the checkout, the absolute path otherwise.

    With a REMOTE outputs role (M8.1) a run's working copy is a temp directory
    — ``/tmp/codegen_storage/outputs_<id>/…`` — which is NOT under REPO_ROOT,
    and ``relative_to`` then raises ``'…' is not in the subpath of '…'``. That
    killed every feed of a live run inside the ACFC App ("live run produced no
    feeds"). The UI only needs the ``/<feed_slug>/`` segment, which both forms
    carry.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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
        # The served run's layout-stage record (None: the run started from
        # contracts, no layout stage ran). Layer 2 is merged from the feeds.
        self.layout_usage = None
        # The IIG template version the served run used (None = the config
        # default) — the metadata-sheet preview renders in it (IIG-first M2).
        self.iig_template: str | None = None

    @property
    def model_usage(self) -> list[dict]:
        """What the served run did with a model, per stage — every provider
        label the UI shows for the run renders from this."""
        from codegen.reasoning.usage import run_usage

        if not self.runs:
            return []
        return run_usage([r.model_usage or [] for r in self.runs.values()], self.layout_usage)

    def adopt(
        self,
        runs: dict[str, FeedRun],
        failures: list[FailedRun],
        *,
        mode: RunMode,
        label: str | None,
        out_root: Path,
        reports_root: Path,
        layout_usage=None,
        iig_template: str | None = None,
    ) -> None:
        """Atomically swap the served state for a demo (live/replay) run."""
        with self._lock:
            self.layout_usage = layout_usage
            self.iig_template = iig_template
            self.runs = runs
            self.failures = failures
            self.mode = mode
            self.label = label
            self.out_root = out_root
            self.reports_root = reports_root
            self.has_run = True

    def forget_runs(self, labels: list[str]) -> bool:
        """The served run's folder was deleted: serve nothing rather than a
        run whose files are gone. True when the loaded run was among them."""
        with self._lock:
            if self.label is None or self.label not in labels:
                return False
            self.runs = {}
            self.failures = []
            self.mode = "mock"
            self.label = None
            self.layout_usage = None
            self.iig_template = None
            self.out_root = REPO_ROOT / self.config.output.dir
            self.reports_root = REPO_ROOT / self.config.output.reports_dir
            self.has_run = False
            return True

    # -- generation ---------------------------------------------------------

    def generate(
        self,
        *,
        only_slug: str | None = None,
        dry_run: bool = True,
        skip_tests: bool = True,
        output_mode: str | list[str] | None = None,
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
            self.layout_usage = None
            self.iig_template = None
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
        output_mode: str | list[str] | None = None,
        extra_flags: list[str] | None = None,
        conventions_profile: str | None = None,
        iig_template: str | None = None,
        playbook_template: str | None = None,
        layout_usage=None,
        environment=None,
        faq_answers: dict | None = None,
    ) -> FeedRun:
        # post60: THE feed pipeline is codegen.cli.generate_feed_result — the
        # CLI's own (no mirror to keep in sync); this wraps it in a FeedRun.
        # 2026-10-14: ``environment`` = the run's (codegen.environments; None =
        # the default) — the framework emit reads it from the config it is given.
        # out_root/reports_dir isolate demo runs; candidates_override replays
        # a recorded Layer-2 result instead of calling any provider.
        from codegen.cli import generate_feed_result
        from codegen.environments import with_environment

        result = generate_feed_result(
            spec, with_environment(self.config, environment), dry_run=dry_run,
            skip_tests=skip_tests, output_mode=output_mode, extra_flags=extra_flags,
            conventions_profile=conventions_profile, iig_template=iig_template,
            playbook_template=playbook_template, layout_usage=layout_usage,
            faq_answers=faq_answers,
            out_root=out_root if out_root is not None else REPO_ROOT / self.config.output.dir,
            reports_dir=(reports_dir if reports_dir is not None
                         else REPO_ROOT / self.config.output.reports_dir),
            base_dir=REPO_ROOT, on_stage=on_stage, candidates_override=candidates_override,
            console=False)
        framework_summary = None
        artefacts = result.framework_artefacts
        if artefacts is not None:
            framework_summary = {
                "files": [p.name for p in artefacts.files],
                "groups": artefacts.groups,
                "row_counts": artefacts.row_counts,
                "coverage": artefacts.coverage,
                "flagged_blank_columns": artefacts.flagged_blank_columns,
            }
        return FeedRun(
            spec=spec,
            outcomes=result.outcomes,
            candidates=result.candidates,
            gate=result.gate,
            written_files=[display_path(p) for p in result.written],
            framework=framework_summary,
            model_usage=[u.as_dict() for u in result.model_usage],
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

    def _decisions_path(self) -> Path:
        from ui.backend import stores

        return stores.state_file(self.config, "decisions.json", DECISIONS_PATH)

    def _load_all_decisions(self) -> dict[str, dict[str, dict[str, dict]]]:
        path = self._decisions_path()
        if not path.is_file():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("version") != DECISIONS_VERSION:
            # Pre-v2 shape was keyed by rule alone and bled across runs and
            # modes — disposable dev state, deliberately discarded.
            return {}
        return payload.get("runs", {})

    def _write_all_decisions(self, runs: dict) -> None:
        from ui.backend import stores

        path = self._decisions_path()
        path.parent.mkdir(parents=True, exist_ok=True)   # repo dir or local scratch
        payload = {"version": DECISIONS_VERSION, "runs": runs}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        stores.push_state(self.config, "decisions.json")

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
