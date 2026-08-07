"""Replay mode: load a tracked live-run artifact set as UI state.

Sets live under ``fixtures/replay/<name>/`` in the layout their README
documents: one directory per feed slug holding ``candidates.json`` (+
``report.md``), plus an optional ``call_log.json``. Loading re-runs the
DETERMINISTIC pipeline (resolve → compile rules → emit → gate) on the
config-declared demo contract pair and injects the recorded Layer-2
candidates in place of any provider call — so the whole results UI renders
from a real recorded run with zero network and zero model access.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ConfigDict

from codegen.reasoning.engine import RuleCandidate
from codegen.resolve.resolver import ContractMismatchError, resolve_pair
from ui.backend.service import REPO_ROOT, FailedRun, FeedRun, GenerationStore

REPLAY_ROOT = REPO_ROOT / "fixtures" / "replay"


class ReplaySet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    date: str | None  # ISO date parsed from a <name>_YYYYMMDD suffix
    feeds: list[str]
    has_call_log: bool


def _set_date(name: str) -> str | None:
    match = re.search(r"(\d{4})(\d{2})(\d{2})$", name)
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else None


def list_replay_sets() -> list[ReplaySet]:
    if not REPLAY_ROOT.is_dir():
        return []
    sets = []
    for entry in sorted(REPLAY_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        feeds = sorted(
            child.name for child in entry.iterdir() if (child / "candidates.json").is_file()
        )
        if not feeds:
            continue
        sets.append(
            ReplaySet(
                name=entry.name,
                date=_set_date(entry.name),
                feeds=feeds,
                has_call_log=(entry / "call_log.json").is_file(),
            )
        )
    return sets


def _reject_traversal(name: str) -> None:
    if any(sep in name for sep in ("/", "\\", "..")):
        raise FileNotFoundError(name)


def _resolve_demo_specs(store: GenerationStore, sttm_path=None) -> dict:
    """Resolve the demo FRD against the given (or golden) STTM contract."""
    config = store.config
    contracts_dir = REPO_ROOT / config.contracts.dir
    sttm = sttm_path if sttm_path is not None else contracts_dir / config.demo.sttm
    try:
        specs = resolve_pair(contracts_dir / config.demo.frd, sttm, config)
    except (ContractMismatchError, ValueError) as exc:
        raise RuntimeError(f"demo contract pair failed to resolve: {exc}") from exc
    return {spec.feed_slug: spec for spec in specs}


def _rebuild_state(
    store: GenerationStore,
    specs_by_slug: dict,
    candidate_files: dict[str, object],
    *,
    mode: str,
    label: str,
    out_root,
    reports_root,
) -> None:
    """Deterministic pipeline re-run with recorded candidates injected."""
    runs: dict[str, FeedRun] = {}
    failures: list[FailedRun] = []
    for slug, candidates_path in candidate_files.items():
        spec = specs_by_slug.get(slug)
        if spec is None:
            failures.append(
                FailedRun(label=slug, error="recorded feed not in the run's contract pair")
            )
            continue
        payload = json.loads(candidates_path.read_text(encoding="utf-8"))
        candidates = [RuleCandidate.model_validate(entry) for entry in payload]
        runs[slug] = store._generate_feed(  # noqa: SLF001 — same-package collaborator
            spec,
            dry_run=True,
            skip_tests=True,
            out_root=out_root,
            reports_dir=reports_root,
            candidates_override=candidates,
        )
    store.adopt(
        runs,
        failures,
        mode=mode,  # type: ignore[arg-type]
        label=label,
        out_root=out_root,
        reports_root=reports_root,
    )


def load_replay_set(store: GenerationStore, name: str) -> None:
    """Rebuild full UI state from a tracked set. Raises on unknown names."""
    _reject_traversal(name)
    set_dir = REPLAY_ROOT / name
    replay_set = next((s for s in list_replay_sets() if s.name == name), None)
    if replay_set is None:
        raise FileNotFoundError(f"no replay set named {name!r} under fixtures/replay/")

    out_root = REPO_ROOT / store.config.output.dir / f"replay_{name}"
    _rebuild_state(
        store,
        _resolve_demo_specs(store),
        {slug: set_dir / slug / "candidates.json" for slug in replay_set.feeds},
        mode="replay",
        label=name,
        out_root=out_root,
        reports_root=out_root / "reports",
    )


# -- past live runs (out/demo_<timestamp>/) --------------------------------- #

EXTRACTED_CONTRACT_NAME = "extracted_sttm.contract.json"


class PastLiveRun(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    timestamp: str | None  # human-readable, parsed from demo_YYYYMMDD_HHMMSS
    feeds: list[str]
    # False = failed/interrupted before any feed produced candidates; such a
    # run is listed (labeled failed) but refuses to load.
    complete: bool


def _run_timestamp(name: str) -> str | None:
    match = re.fullmatch(r"demo_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", name)
    if not match:
        return None
    y, mo, d, h, mi, s = match.groups()
    return f"{y}-{mo}-{d} {h}:{mi}:{s}"


def list_past_live_runs(store: GenerationStore, root=None) -> list[PastLiveRun]:
    out_dir = root if root is not None else REPO_ROOT / store.config.output.dir
    if not out_dir.is_dir():
        return []
    runs = []
    for entry in sorted(out_dir.glob("demo_*"), reverse=True):
        if not entry.is_dir():
            continue
        feeds = sorted(
            child.name
            for child in entry.iterdir()
            if (child / "candidates" / "candidates.json").is_file()
        )
        runs.append(
            PastLiveRun(
                name=entry.name,
                timestamp=_run_timestamp(entry.name),
                feeds=feeds,
                complete=bool(feeds),
            )
        )
    return runs


def load_past_live_run(store: GenerationStore, name: str, root=None) -> None:
    """Restore a completed live run's results as LIVE state.

    Same mechanism as replay — deterministic re-run + that run's recorded
    candidates — but resolved against the run's own EXTRACTED contract (the
    live pipeline generated from it, so provenance hashes must match) and
    served from the run's own directory.
    """
    _reject_traversal(name)
    out_dir = root if root is not None else REPO_ROOT / store.config.output.dir
    run = next((r for r in list_past_live_runs(store, root=root) if r.name == name), None)
    if run is None:
        raise FileNotFoundError(f"no past live run named {name!r} under {out_dir.name}/")
    if not run.complete:
        raise RuntimeError(f"live run {name!r} failed before producing results — cannot load")

    run_dir = out_dir / name
    extracted = run_dir / EXTRACTED_CONTRACT_NAME
    _rebuild_state(
        store,
        _resolve_demo_specs(store, sttm_path=extracted if extracted.is_file() else None),
        {slug: run_dir / slug / "candidates" / "candidates.json" for slug in run.feeds},
        mode="live",
        label=name,
        out_root=run_dir,
        reports_root=run_dir / "reports",
    )
