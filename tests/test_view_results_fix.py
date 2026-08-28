"""Past-live-run loading: the View-results bug class (2026-08-27).

Three regressions locked in: (1) a run whose feeds produced ZERO Layer-2
candidates is complete — completeness keys on emitted artefacts, not on
candidates.json; (2) a run reloads with ITS OWN recorded FRD, never the
pinned demo golden; (3) framework/both runs reload in their own output
mode. Synthetic run directories are built from the golden fixture pair.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from ui.backend.replay import list_past_live_runs, load_past_live_run
from ui.backend.service import GenerationStore

REPO = Path(__file__).resolve().parents[1]
_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"

needs_demo_pair = pytest.mark.skipif(
    not (_FRD.is_file() and _STTM.is_file()),
    reason="demo fixture pair not restored (removed 2026-08-22)",
)


def _store() -> GenerationStore:
    return GenerationStore("config/config.yaml")


@pytest.fixture()
def runs_root():
    """Run dirs must live under the repo (written_files are repo-relative),
    exactly as real runs under out/ do. Cleaned up afterwards."""
    root = REPO / "out" / "_pytest_view_results"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _make_run(tmp_path: Path, name: str, *, feeds: list[str],
              marker: str = "README.md", with_frd: bool = True,
              output_mode: str | None = None) -> Path:
    run_dir = tmp_path / name
    for feed in feeds:
        feed_dir = run_dir / feed
        if marker == "README.md":
            feed_dir.mkdir(parents=True)
            (feed_dir / "README.md").write_text("generated", encoding="utf-8")
        else:
            (feed_dir / marker).mkdir(parents=True)
    if with_frd:
        shutil.copyfile(_FRD, run_dir / "frd.contract.json")
    shutil.copyfile(_STTM, run_dir / "extracted_sttm.contract.json")
    if output_mode:
        (run_dir / "run_meta.json").write_text(
            json.dumps({"output_mode": output_mode}), encoding="utf-8"
        )
    return run_dir


CV_FEEDS = ["cv_community_demographic_risk", "cv_community_risk",
            "cv_individual_risk"]


def test_complete_without_candidates(tmp_path):
    """Zero Layer-2 candidates is a legitimate, COMPLETE run (the MIDS bug)."""
    (tmp_path / "demo_20260827_232306" / "feed_a").mkdir(parents=True)
    (tmp_path / "demo_20260827_232306" / "feed_a" / "README.md").write_text("x")
    (run,) = list_past_live_runs(_store(), root=tmp_path)
    assert run.complete and run.feeds == ["feed_a"]


def test_framework_only_feed_dirs_count(tmp_path):
    (tmp_path / "demo_20260827_000001" / "feed_b" / "framework").mkdir(parents=True)
    (run,) = list_past_live_runs(_store(), root=tmp_path)
    assert run.complete and run.feeds == ["feed_b"]


def test_empty_run_still_incomplete(tmp_path):
    (tmp_path / "demo_20260827_000002").mkdir()
    (run,) = list_past_live_runs(_store(), root=tmp_path)
    assert not run.complete
    with pytest.raises(RuntimeError, match="failed before producing results"):
        load_past_live_run(_store(), "demo_20260827_000002", root=tmp_path)


@needs_demo_pair
def test_load_uses_the_runs_own_frd_and_empty_candidates(runs_root):
    """The run's frd.contract.json wins over config.demo.frd, and feeds
    without candidates.json load with an empty candidate list."""
    _make_run(runs_root, "demo_20260827_111111", feeds=CV_FEEDS)
    store = _store()
    load_past_live_run(store, "demo_20260827_111111", root=runs_root)
    assert sorted(store.runs) == CV_FEEDS
    assert all(run.candidates == [] for run in store.runs.values())
    assert store.label == "demo_20260827_111111"
    assert store.mode == "live"


@needs_demo_pair
def test_load_falls_back_to_demo_golden_for_old_runs(runs_root):
    """Pre-fix run dirs (no frd copy) keep loading via the demo golden."""
    _make_run(runs_root, "demo_20260827_222222", feeds=CV_FEEDS, with_frd=False)
    store = _store()
    load_past_live_run(store, "demo_20260827_222222", root=runs_root)
    assert sorted(store.runs) == CV_FEEDS


@needs_demo_pair
def test_load_replays_in_the_recorded_output_mode(runs_root):
    _make_run(runs_root, "demo_20260827_333333", feeds=CV_FEEDS,
              output_mode="both")
    store = _store()
    load_past_live_run(store, "demo_20260827_333333", root=runs_root)
    for run in store.runs.values():
        assert run.framework is not None  # framework artefacts regenerated
        assert any(f.endswith(".ipynb") for f in run.written_files)
