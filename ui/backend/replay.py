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


def load_replay_set(store: GenerationStore, name: str) -> None:
    """Rebuild full UI state from a tracked set. Raises on unknown names."""
    if any(sep in name for sep in ("/", "\\", "..")):
        raise FileNotFoundError(name)
    set_dir = REPLAY_ROOT / name
    replay_set = next((s for s in list_replay_sets() if s.name == name), None)
    if replay_set is None:
        raise FileNotFoundError(f"no replay set named {name!r} under fixtures/replay/")

    config = store.config
    contracts_dir = REPO_ROOT / config.contracts.dir
    try:
        specs = resolve_pair(
            contracts_dir / config.demo.frd, contracts_dir / config.demo.sttm, config
        )
    except (ContractMismatchError, ValueError) as exc:
        raise RuntimeError(f"demo contract pair failed to resolve: {exc}") from exc
    specs_by_slug = {spec.feed_slug: spec for spec in specs}

    out_root = REPO_ROOT / config.output.dir / f"replay_{name}"
    reports_root = out_root / "reports"
    runs: dict[str, FeedRun] = {}
    failures: list[FailedRun] = []
    for slug in replay_set.feeds:
        spec = specs_by_slug.get(slug)
        if spec is None:
            failures.append(
                FailedRun(label=slug, error="replay feed not in the demo contract pair")
            )
            continue
        payload = json.loads((set_dir / slug / "candidates.json").read_text(encoding="utf-8"))
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
        mode="replay",
        label=name,
        out_root=out_root,
        reports_root=reports_root,
    )
