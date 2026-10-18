"""post67: the live-run confirm dialog's numbers are MEASURED.

Tokens come from each provider response (FM API prompt_tokens /
completion_tokens, the Anthropic API input_tokens / output_tokens /
cache_read_input_tokens), summed per stage next to the live seconds; cost =
tokens x ``reasoning.prices`` (never calls x a constant); the App keeps the
last ``demo.run_history_size`` live runs per conventions profile and the
status carries their ranges — "no history yet" (runs 0) when empty.
Synthetic usage only; no model is called.
"""

from __future__ import annotations

import json
import threading
import time
from types import SimpleNamespace

import pytest
from ui.backend import run_history
from ui.backend.demo import DemoRunner
from ui.backend.run_history import LiveRunHistory, run_entry, summary, typical_range
from ui.backend.service import GenerationStore

from codegen.config import ModelPriceConfig, PriceTableConfig, load_config
from codegen.databricks import chat
from codegen.reasoning.usage import (
    StageUsage,
    add_tokens,
    completion_tokens,
    merge,
    message_tokens,
    usage_from_provider,
)

PRICES = PriceTableConfig(as_of="2026-10-06", source="test",
                          models={"claude-opus-5-5": ModelPriceConfig(
                              input=4.0, output=20.0, cache_read=0.2)})


def _live(stage: str = "layer2", *, calls: int = 3, seconds: float = 40.0,
          input_tokens: int = 20_000, output_tokens: int = 3_000,
          cache_read_tokens: int = 0, model: str = "claude-opus-5-5") -> dict:
    return StageUsage(stage=stage, provider="databricks_fmapi",
                      endpoint="databricks-claude-opus-5-5", model=model, calls=calls,
                      requests=calls, seconds=seconds, input_tokens=input_tokens,
                      output_tokens=output_tokens,
                      cache_read_tokens=cache_read_tokens).as_dict()


# --------------------------------------------------------------- tokens per call


def test_fmapi_chat_reports_the_response_tokens():
    def query(name, messages, max_tokens):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=1200, completion_tokens=300,
                                  prompt_tokens_details={"cached_tokens": 200}))

    client = SimpleNamespace(serving_endpoints=SimpleNamespace(query=query))
    cfg = load_config("config/config.yaml").databricks
    counts: dict = {}
    assert chat(cfg, [{"role": "user", "content": "x"}], endpoint="e", client=client,
                usage=counts) == "ok"
    # cached prompt tokens are cache reads, not input (the Anthropic API's counting)
    assert counts == {"input_tokens": 1000, "output_tokens": 300, "cache_read_tokens": 200}


def test_a_response_without_usage_reports_zero_tokens():
    assert completion_tokens(SimpleNamespace()) == {
        "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0}
    assert message_tokens(SimpleNamespace(usage=None)) == {
        "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0}


def test_anthropic_message_tokens_and_the_running_totals():
    owner = SimpleNamespace(name="anthropic", calls=2, seconds=12.0, model="claude-opus-5-5")
    for _ in range(2):
        add_tokens(owner, message_tokens(SimpleNamespace(usage=SimpleNamespace(
            input_tokens=500, output_tokens=80, cache_read_input_tokens=1000))))
    usage = usage_from_provider("layer2", owner, requests=2)
    assert (usage.input_tokens, usage.output_tokens, usage.cache_read_tokens) == (1000, 160, 2000)
    # the label (report, MODEL USAGE line) does not change
    assert "token" not in usage.label


def test_merge_sums_tokens_and_a_mock_reports_none():
    merged = merge("layer2", [StageUsage.from_dict(_live()), StageUsage.from_dict(_live())])
    assert (merged.input_tokens, merged.output_tokens) == (40_000, 6_000)
    mock = SimpleNamespace(name="mock", input_tokens=99)
    assert usage_from_provider("layer2", mock, requests=1).input_tokens == 0


# ------------------------------------------------------------------ the record


def test_cost_is_tokens_times_the_price_table():
    entry = run_entry(label="demo_1", wall_seconds=118.04, prices=PRICES,
                      model_usage=[_live("layout", calls=1, seconds=9.0, input_tokens=5_000,
                                         output_tokens=500, cache_read_tokens=10_000),
                                   _live()])
    assert entry["calls"] == 4 and entry["model_seconds"] == 49.0
    assert entry["wall_seconds"] == 118.0 and entry["tokens_measured"] is True
    expected = (25_000 * 4.0 + 3_500 * 20.0 + 10_000 * 0.2) / 1_000_000
    assert entry["cost_usd"] == pytest.approx(expected)


def test_no_tokens_or_no_price_means_no_dollars():
    unmeasured = run_entry(label="x", wall_seconds=90, prices=PRICES,
                           model_usage=[_live(input_tokens=0, output_tokens=0)])
    assert unmeasured["tokens_measured"] is False and unmeasured["cost_usd"] is None
    unpriced = run_entry(label="x", wall_seconds=90, prices=PRICES,
                         model_usage=[_live(model="claude-unlisted")])
    assert unpriced["tokens_measured"] is True and unpriced["cost_usd"] is None
    assert run_entry(label="x", wall_seconds=90, prices=None,
                     model_usage=[_live()])["cost_usd"] is None
    # never calls x a constant: the same calls with no tokens give no figure
    assert all(v is None for v in (unmeasured["cost_usd"], unpriced["cost_usd"]))


def test_a_mock_run_is_not_recorded_and_a_cached_live_run_costs_nothing():
    mock = StageUsage(stage="layer2", provider="mock", requests=2, mock_reason="dry-run")
    assert run_entry(label="x", wall_seconds=5, prices=PRICES,
                     model_usage=[mock.as_dict()]) is None
    cached = run_entry(label="x", wall_seconds=30, prices=PRICES,
                       model_usage=[_live(calls=0, seconds=0.0, input_tokens=0,
                                          output_tokens=0)])
    assert cached["cost_usd"] == 0.0 and cached["calls"] == 0


def test_typical_range_drops_the_extremes_from_five_runs_on():
    assert typical_range([]) is None
    assert typical_range([120.0]) == {"low": 120.0, "high": 120.0}
    assert typical_range([90.0, 300.0, 100.0, 110.0]) == {"low": 90.0, "high": 300.0}
    assert typical_range([90.0, 300.0, 100.0, 110.0, 30.0]) == {"low": 90.0, "high": 110.0}


def test_summary_takes_cost_only_from_measured_runs():
    entries = [run_entry(label=str(i), wall_seconds=100 + i, prices=PRICES,
                         model_usage=[_live(input_tokens=0, output_tokens=0) if i < 2
                                      else _live()])
               for i in range(4)]
    view = summary(entries, profile="acfc_prx", prices=PRICES)
    assert view["runs"] == 4 and view["cost_runs"] == 2
    assert view["wall_seconds"] == {"low": 100.0, "high": 103.0}
    assert view["prices_as_of"] == "2026-10-06"
    empty = summary([], profile="acfc_prx", prices=PRICES)
    assert empty["runs"] == 0 and empty["wall_seconds"] is None
    assert empty["cost_usd"] is None and empty["prices_as_of"] is None


@pytest.fixture
def history_file(monkeypatch, tmp_path):
    path = tmp_path / "state" / run_history.HISTORY_FILE
    monkeypatch.setattr(run_history, "HISTORY_PATH", path)
    return path


def test_the_record_keeps_the_last_n_runs_per_profile(history_file):
    config = load_config("config/config.yaml")
    config = config.model_copy(update={"demo": config.demo.model_copy(
        update={"run_history_size": 3})})
    history = LiveRunHistory(lambda: config)
    for i in range(5):
        history.record("acfc_prx", {"label": f"run{i}", "calls": i, "wall_seconds": 60.0 + i,
                                    "model_seconds": 10.0, "cost_usd": None})
    history.record("edo_sfmc", {"label": "other", "calls": 1, "wall_seconds": 30.0,
                                "model_seconds": 5.0, "cost_usd": None})
    assert [e["label"] for e in history.entries("acfc_prx")] == ["run2", "run3", "run4"]
    # persisted whole, and read back by a fresh instance (an App restart)
    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert sorted(saved["profiles"]) == ["acfc_prx", "edo_sfmc"]
    again = LiveRunHistory(lambda: config)
    assert again.view("acfc_prx")["runs"] == 3
    assert again.view("acfc_prx")["calls"] == {"low": 2, "high": 4}
    assert again.view("nothing_yet")["runs"] == 0


def test_an_unreadable_record_is_no_history(history_file):
    history_file.parent.mkdir(parents=True)
    history_file.write_text("{not json", encoding="utf-8")
    config = load_config("config/config.yaml")
    assert LiveRunHistory(lambda: config).view("acfc_prx")["runs"] == 0


# ------------------------------------------------------------- the App's runs


def _runner(work_fn):
    store = GenerationStore("config/config.yaml")
    box: dict = {}
    runner = DemoRunner(store, work=lambda: work_fn(box["runner"]), index_warmup=False)
    box["runner"] = runner
    return runner


def test_a_live_run_is_recorded_without_the_time_spent_waiting_for_the_person(history_file):
    def work(runner):
        runner._run_label = "demo_test"
        threading.Timer(0.4, runner._layout_event.set).start()
        runner._wait_for_person()                       # the dialog: not the run's time
        runner.model_usage = [_live()]

    runner = _runner(work)
    runner.state = "running"
    runner._run()
    assert runner.state == "done"
    entries = runner.live_history.entries(runner.live_history_profile())
    assert len(entries) == 1
    entry = entries[0]
    assert entry["label"] == "demo_test" and entry["calls"] == 3
    assert entry["wall_seconds"] < 0.3                  # the 0.4 s wait is left out
    assert entry["cost_usd"] == pytest.approx((20_000 * 4.0 + 3_000 * 20.0) / 1_000_000)
    view = runner.live_history.view(runner.live_history_profile())
    assert view["runs"] == 1 and view["cost_runs"] == 1


def test_mock_and_failed_runs_are_not_recorded(history_file):
    def mock_work(runner):
        runner.model_usage = [StageUsage(stage="layer2", provider="mock", requests=1,
                                         mock_reason="test").as_dict()]

    runner = _runner(mock_work)
    runner._run()
    assert runner.state == "done"

    def failing(runner):
        runner.model_usage = [_live()]
        time.sleep(0.01)
        raise RuntimeError("boom")

    failed = _runner(failing)
    failed._run()
    assert failed.state == "failed"
    assert runner.live_history.entries(runner.live_history_profile()) == []
    assert not history_file.exists()


def test_the_status_carries_the_history_not_constants(history_file, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from ui.backend import main

    def work(runner):
        runner.model_usage = [_live()]

    runner = _runner(work)
    monkeypatch.setattr(main, "store", runner._store)
    monkeypatch.setattr(main, "runner", runner)
    client = TestClient(main.app)
    status = client.get("/api/demo/status").json()
    assert "estimates" not in status
    assert status["live_history"]["runs"] == 0
    assert status["live_history"]["profile"] == runner.live_history_profile()
    runner._run()
    history = client.get("/api/demo/status").json()["live_history"]
    assert history["runs"] == 1 and history["calls"] == {"low": 3, "high": 3}
    assert history["prices_as_of"] == "2026-10-06"
