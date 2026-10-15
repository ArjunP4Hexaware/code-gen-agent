"""D1 post51 pair_03: 109 s against ~10 s for the other pairs. Profiled at home
on a 330-column synthetic STTM (layout, extract-sttm, generate under mock): no
stage scales with the column count and no model call is made per column or
per row (layout: one request per document with open roles; Layer 2: one per
unmapped rule; pair_03 failed at the resolver, before Layer 2). The time is
the live model's, so the run record now says how long the live calls took
(``StageUsage.seconds``, on the MODEL USAGE line) — nothing is capped blind."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from codegen.reasoning import usage as usage_mod
from codegen.reasoning.usage import NO_CALL_NEEDED, StageUsage, merge, timed, usage_from_provider
from post51_pairs import family_e_workbook

REPO = Path(__file__).resolve().parents[1]


class _Live:
    name = "databricks_fmapi"
    endpoint = "databricks-claude-opus-5-5"
    model = "claude-opus-5-5"

    def __init__(self) -> None:
        self.calls = 0
        self.seconds = 0.0


def test_timed_adds_each_round_trip_to_the_provider(monkeypatch):
    ticks = iter([10.0, 12.5, 20.0, 21.0])
    monkeypatch.setattr(usage_mod.time, "perf_counter", lambda: next(ticks))
    provider = _Live()
    send = timed(provider, lambda prompt: prompt.upper())
    assert send("a") == "A" and send("b") == "B"
    assert provider.seconds == 3.5


def test_a_failed_round_trip_still_counts_its_time(monkeypatch):
    ticks = iter([0.0, 4.0])
    monkeypatch.setattr(usage_mod.time, "perf_counter", lambda: next(ticks))
    provider = _Live()

    def boom(_prompt):
        raise TimeoutError("endpoint")

    with pytest.raises(TimeoutError):
        timed(provider, boom)("x")
    assert provider.seconds == 4.0


def test_the_label_names_the_seconds_for_a_live_stage():
    provider = _Live()
    provider.calls, provider.seconds = 2, 97.26
    used = usage_from_provider("layout", provider, requests=1)
    assert used.seconds == 97.3
    assert used.label == ("Claude Opus 5.5 (databricks-claude-opus-5-5) · 2 call(s) in 97.3s")
    merged = merge("layer2", [used, StageUsage(stage="layer2", provider="databricks_fmapi",
                                               calls=1, requests=1, seconds=1.2)])
    assert merged.seconds == 98.5
    # a mock never reports seconds; no seconds keeps the old label
    assert StageUsage(stage="layout", provider="databricks_fmapi", model="claude-opus-5-5",
                      calls=1, requests=1).label.endswith("· 1 call(s)")


def test_a_330_column_sttm_needs_no_model_call(tmp_path):
    fields = [f"Field {i:03d}" for i in range(330)]
    workbook = family_e_workbook(tmp_path / "wide.xlsx", [None], fields=fields)
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    start = time.perf_counter()
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "layout", "--workbook", str(workbook),
         "--provider", "mock", "--no-cache", "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    elapsed = time.perf_counter() - start
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"{'MODEL USAGE':<15} layout: {NO_CALL_NEEDED}" in done.stdout
    assert elapsed < 60          # ~1.5 s at home; a per-column cost would show here
