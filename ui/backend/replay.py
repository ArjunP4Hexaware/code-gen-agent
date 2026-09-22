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
from pathlib import Path

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


def _resolve_demo_specs(store: GenerationStore, sttm_path=None,
                        frd_path=None) -> dict:
    """Resolve the run's FRD (or the demo golden) against the given (or
    golden) STTM contract."""
    config = store.config
    contracts_dir = REPO_ROOT / config.contracts.dir
    sttm = sttm_path if sttm_path is not None else contracts_dir / config.demo.sttm
    frd = frd_path if frd_path is not None else contracts_dir / config.demo.frd
    try:
        specs = resolve_pair(frd, sttm, config)
    except (ContractMismatchError, ValueError) as exc:
        raise RuntimeError(f"contract pair failed to resolve: {exc}") from exc
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
    output_mode: str | list[str] | None = None,
) -> None:
    """Deterministic pipeline re-run with recorded candidates injected.

    A feed with NO candidates file is a legitimate state (every rule
    compiled deterministically — e.g. the MIDS feeds) and replays with an
    empty override, never an error.
    """
    runs: dict[str, FeedRun] = {}
    failures: list[FailedRun] = []
    for slug, candidates_path in candidate_files.items():
        spec = specs_by_slug.get(slug)
        if spec is None:
            failures.append(
                FailedRun(label=slug, error="recorded feed not in the run's contract pair")
            )
            continue
        if candidates_path is not None and candidates_path.is_file():
            payload = json.loads(candidates_path.read_text(encoding="utf-8"))
            candidates = [RuleCandidate.model_validate(entry) for entry in payload]
        else:
            candidates = []
        runs[slug] = store._generate_feed(  # noqa: SLF001 — same-package collaborator
            spec,
            dry_run=True,
            skip_tests=True,
            out_root=out_root,
            reports_dir=reports_root,
            candidates_override=candidates,
            output_mode=output_mode,
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

    out_root = _outputs_dir(store) / f"replay_{name}"
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


def _outputs_dir(store: GenerationStore, root=None) -> Path:
    """The outputs role's local directory (``./out`` by default)."""
    if root is not None:
        return root
    from ui.backend import stores

    return stores.outputs_root(store.config)


def list_past_live_runs(store: GenerationStore, root=None) -> list[PastLiveRun]:
    out_dir = _outputs_dir(store, root)
    if root is None:
        # A remote outputs role outlives the container: bring down the runs
        # this process has no working copy of, so they list and load.
        from ui.backend import stores

        for label in stores.remote_run_labels(store.config):
            if not (out_dir / label).is_dir():
                stores.pull_run(store.config, label)
    if not out_dir.is_dir():
        return []
    runs = []
    for entry in sorted(out_dir.glob("demo_*"), reverse=True):
        if not entry.is_dir():
            continue
        # A generated feed dir is marked by its emitted artefacts — NOT by
        # candidates.json: a feed whose rules all compiled deterministically
        # has no candidates at all (the MIDS feeds), and framework-mode runs
        # emit no README. Any of these markers means the feed generated.
        feeds = sorted(
            child.name
            for child in entry.iterdir()
            if child.is_dir()
            and (
                (child / "README.md").is_file()
                or (child / "ddl").is_dir()
                or (child / "framework").is_dir()
                or (child / "candidates" / "candidates.json").is_file()
            )
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
    out_dir = _outputs_dir(store, root)
    run = next((r for r in list_past_live_runs(store, root=root) if r.name == name), None)
    if run is None:
        raise FileNotFoundError(f"no past live run named {name!r} under {out_dir.name}/")
    if not run.complete:
        raise RuntimeError(f"live run {name!r} failed before producing results — cannot load")

    run_dir = out_dir / name
    extracted = run_dir / EXTRACTED_CONTRACT_NAME
    # The run's OWN pair: runs record the FRD they used (frd.contract.json)
    # and their metadata; older runs fall back to the demo golden FRD and an
    # output mode inferred from what the feed dirs actually hold.
    run_frd = run_dir / "frd.contract.json"
    meta_path = run_dir / "run_meta.json"
    output_mode = None
    from codegen.output_modes import output_parts

    if meta_path.is_file():
        try:
            output_mode = json.loads(meta_path.read_text(encoding="utf-8")).get(
                "output_mode"
            )
        except ValueError:
            output_mode = None
    if output_mode is not None:
        # A run recorded under a retired mode (both / rfc / all) replays as
        # Notebook + Framework artefacts, with a one-time notice.
        output_mode = output_parts(output_mode, source=f"run_meta.json of {name}")
    if output_mode is None and run.feeds:
        first = run_dir / run.feeds[0]
        has_framework = (first / "framework").is_dir()
        has_pipeline = (first / "pipeline").is_dir()
        has_rfc = any(p.is_dir() and p.name.startswith("RFC") for p in first.iterdir())
        inferred = (["rfc"] if has_rfc
                    else ["notebook"] * has_pipeline + ["framework"] * has_framework)
        output_mode = output_parts(inferred or ["notebook"], source=f"past run {name}")
    _rebuild_state(
        store,
        _resolve_demo_specs(
            store,
            sttm_path=extracted if extracted.is_file() else None,
            frd_path=run_frd if run_frd.is_file() else None,
        ),
        {slug: run_dir / slug / "candidates" / "candidates.json" for slug in run.feeds},
        mode="live",
        label=name,
        out_root=run_dir,
        reports_root=run_dir / "reports",
        output_mode=output_mode,
    )
