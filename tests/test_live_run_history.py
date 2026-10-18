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

LIST = ModelPriceConfig(input=4.0, output=20.0, cache_read=0.2,
                        source="anthropic list price, 2026-10-06")
PRICES = PriceTableConfig(anthropic={"claude-opus-5-5": LIST})
# the workspace's FM API rate, once filled (synthetic numbers)
WORKSPACE = PriceTableConfig(
    anthropic={"claude-opus-5-5": LIST},
    databricks_fmapi={"claude-opus-5-5": ModelPriceConfig(
        input=2.0, output=10.0, cache_read=0.1, source="workspace DBU rate, 2026-10-20")})


def _live(stage: str = "layer2", *, calls: int = 3, seconds: float = 40.0,
          input_tokens: int = 20_000, output_tokens: int = 3_000,
          cache_read_tokens: int = 0, model: str = "claude-opus-5-5",
          provider: str = "databricks_fmapi") -> dict:
    return StageUsage(stage=stage, provider=provider,
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


def _entry(*, outcome: str | None = "PASS", **kwargs) -> dict | None:
    return run_entry(outcome=outcome, **kwargs)


def test_cost_is_tokens_times_the_price_table():
    entry = _entry(label="demo_1", wall_seconds=118.04, prices=PRICES,
                      model_usage=[_live("layout", calls=1, seconds=9.0, input_tokens=5_000,
                                         output_tokens=500, cache_read_tokens=10_000),
                                   _live()])
    assert entry["calls"] == 4 and entry["model_seconds"] == 49.0
    assert entry["wall_seconds"] == 118.0 and entry["tokens_measured"] is True
    expected = (25_000 * 4.0 + 3_500 * 20.0 + 10_000 * 0.2) / 1_000_000
    assert entry["cost_usd"] == pytest.approx(expected) and entry["cost_basis"] == "list"


def test_the_shipped_table_has_list_prices_and_an_empty_workspace_entry():
    prices = load_config("config/config.yaml").reasoning.prices
    row = prices.anthropic["claude-opus-5-5"]
    assert (row.input, row.output, row.cache_read) == (4.0, 20.0, 0.2)
    assert row.source == "anthropic list price, 2026-10-06"
    assert prices.databricks_fmapi == {}
    assert prices.rate("databricks_fmapi", "claude-opus-5-5")[1] == "list"


def test_fm_api_runs_use_the_workspace_rate_once_it_exists():
    assert WORKSPACE.rate("databricks_fmapi", "claude-opus-5-5")[1] == "workspace"
    # an Anthropic API call is billed at the list price whatever the workspace rate
    assert WORKSPACE.rate("anthropic", "claude-opus-5-5")[1] == "list"
    entry = _entry(label="x", wall_seconds=100, prices=WORKSPACE, model_usage=[_live()])
    assert entry["cost_basis"] == "workspace"
    assert entry["cost_usd"] == pytest.approx((20_000 * 2.0 + 3_000 * 10.0) / 1_000_000)


def test_the_dialog_says_which_price_it_used():
    entries = [_entry(label=str(i), wall_seconds=100, prices=PRICES, model_usage=[_live()])
               for i in range(3)]
    at_list = summary(entries, profile="acfc_prx", prices=PRICES)
    assert at_list["cost_basis"] == "list" and at_list["billed_in_dbus"] is True
    assert at_list["price_source"] == "anthropic list price, 2026-10-06"
    # the same recorded runs, priced after the workspace's rate was filled in
    at_rate = summary(entries, profile="acfc_prx", prices=WORKSPACE)
    assert at_rate["cost_basis"] == "workspace" and at_rate["billed_in_dbus"] is False
    assert at_rate["price_source"] == "workspace DBU rate, 2026-10-20"
    assert at_rate["cost_usd"]["high"] < at_list["cost_usd"]["high"]
    # Anthropic API runs at the list price: no DBU note
    direct = [_entry(label=f"d{i}", wall_seconds=100, prices=PRICES,
                     model_usage=[_live(provider="anthropic")]) for i in range(3)]
    assert summary(direct, profile="acfc_prx", prices=PRICES)["billed_in_dbus"] is False


def test_no_tokens_or_no_price_means_no_dollars():
    unmeasured = _entry(label="x", wall_seconds=90, prices=PRICES,
                           model_usage=[_live(input_tokens=0, output_tokens=0)])
    assert unmeasured["tokens_measured"] is False and unmeasured["cost_usd"] is None
    unpriced = _entry(label="x", wall_seconds=90, prices=PRICES,
                         model_usage=[_live(model="claude-unlisted")])
    assert unpriced["tokens_measured"] is True and unpriced["cost_usd"] is None
    assert _entry(label="x", wall_seconds=90, prices=None,
                     model_usage=[_live()])["cost_usd"] is None
    # never calls x a constant: the same calls with no tokens give no figure
    assert all(v is None for v in (unmeasured["cost_usd"], unpriced["cost_usd"]))


def test_a_mock_run_is_not_recorded_and_a_cached_live_run_costs_nothing():
    mock = StageUsage(stage="layer2", provider="mock", requests=2, mock_reason="dry-run")
    assert _entry(label="x", wall_seconds=5, prices=PRICES,
                     model_usage=[mock.as_dict()]) is None
    cached = _entry(label="x", wall_seconds=30, prices=PRICES,
                       model_usage=[_live(calls=0, seconds=0.0, input_tokens=0,
                                          output_tokens=0)])
    assert cached["cost_usd"] == 0.0 and cached["calls"] == 0


def test_typical_range_drops_the_extremes_from_five_runs_on():
    assert typical_range([]) is None
    assert typical_range([120.0]) == {"low": 120.0, "high": 120.0}
    assert typical_range([90.0, 300.0, 100.0, 110.0]) == {"low": 90.0, "high": 300.0}
    assert typical_range([90.0, 300.0, 100.0, 110.0, 30.0]) == {"low": 90.0, "high": 110.0}


def test_summary_takes_cost_only_from_measured_runs():
    entries = [_entry(label=str(i), wall_seconds=100 + i, prices=PRICES,
                         model_usage=[_live(input_tokens=0, output_tokens=0) if i < 2
                                      else _live()])
               for i in range(4)]
    view = summary(entries, profile="acfc_prx", prices=PRICES)
    assert view["runs"] == 4 and view["cost_runs"] == 2
    assert view["wall_seconds"] == {"low": 100.0, "high": 103.0}
    assert view["price_source"] == "anthropic list price, 2026-10-06"
    empty = summary([], profile="acfc_prx", prices=PRICES)
    assert empty["runs"] == 0 and empty["wall_seconds"] is None
    assert empty["cost_usd"] is None and empty["price_source"] is None
    assert empty["cost_basis"] is None and empty["billed_in_dbus"] is False


@pytest.fixture
def history_file(monkeypatch, tmp_path):
    path = tmp_path / "state" / run_history.HISTORY_FILE
    monkeypatch.setattr(run_history, "HISTORY_PATH", path)
    return path


def _kept(label: str, outcome: str, i: int, wall: float) -> dict:
    return {"label": label, "outcome": outcome, "at": f"2026-10-18T10:{i:02d}:00+00:00",
            "calls": i, "wall_seconds": wall, "model_seconds": 10.0, "cost_usd": None}


def test_the_record_keeps_the_last_n_runs_per_profile_and_outcome(history_file):
    config = load_config("config/config.yaml")
    config = config.model_copy(update={"demo": config.demo.model_copy(
        update={"run_history_size": 3})})
    history = LiveRunHistory(lambda: config)
    for i in range(5):
        history.record("acfc_prx", _kept(f"run{i}", "PASS", i, 60.0 + i))
    for i in range(5, 9):
        history.record("acfc_prx", _kept(f"ask{i}", "NEEDS_ANSWERS", i, 20.0 + i))
    history.record("edo_sfmc", _kept("other", "PASS", 9, 30.0))
    labels = [e["label"] for e in history.entries("acfc_prx")]
    # the last 3 per outcome, oldest first
    assert labels == ["run2", "run3", "run4", "ask6", "ask7", "ask8"]
    # persisted whole, keyed (profile, outcome), and read back after an App restart
    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert sorted(saved["profiles"]) == ["acfc_prx", "edo_sfmc"]
    assert sorted(saved["profiles"]["acfc_prx"]) == ["NEEDS_ANSWERS", "PASS"]
    again = LiveRunHistory(lambda: config)
    view = again.view("acfc_prx")
    assert view["runs"] == 3 and view["calls"] == {"low": 2, "high": 4}
    assert view["stopped"] == {"runs": 3, "wall_seconds": {"low": 26.0, "high": 28.0}}
    assert again.view("nothing_yet")["runs"] == 0
    assert again.view("nothing_yet")["stopped"] is None


def test_the_range_comes_from_completed_runs_only():
    completed = [_entry(label=f"p{i}", outcome=outcome, wall_seconds=100 + i, prices=PRICES,
                        model_usage=[_live()])
                 for i, outcome in enumerate(["PASS", "PASS_WITH_OPEN_INPUTS", "PASS"])]
    stopped = [_entry(label=f"s{i}", outcome=outcome, wall_seconds=25 + i, prices=PRICES,
                      model_usage=[_live(calls=1)])
               for i, outcome in enumerate(["NEEDS_ANSWERS", "GATE_FAIL"])]
    view = summary([*completed, *stopped], profile="acfc_prx", prices=PRICES)
    assert view["runs"] == 3 and view["calls"] == {"low": 3, "high": 3}
    assert view["wall_seconds"] == {"low": 100.0, "high": 102.0}
    assert view["stopped"] == {"runs": 2, "wall_seconds": {"low": 25.0, "high": 26.0}}
    assert view["cost_runs"] == 3


def test_under_three_completed_runs_there_is_no_range():
    two = [_entry(label=f"p{i}", wall_seconds=100, prices=PRICES, model_usage=[_live()])
           for i in range(2)]
    stopped = [_entry(label="s", outcome="NEEDS_ANSWERS", wall_seconds=30, prices=PRICES,
                      model_usage=[_live()])]
    view = summary([*two, *stopped], profile="acfc_prx", prices=PRICES)
    assert view["runs"] == 2 and view["min_runs"] == 3
    assert view["wall_seconds"] is None and view["calls"] is None
    assert view["cost_usd"] is None and view["cost_basis"] is None
    # the runs that stopped are still shown
    assert view["stopped"]["runs"] == 1


def test_crashed_and_failed_runs_are_not_kept():
    for outcome in ("CRASHED", "FAIL", None):
        assert _entry(label="x", outcome=outcome, wall_seconds=10, prices=PRICES,
                      model_usage=[_live()]) is None
    for outcome in ("PASS", "PASS_WITH_OPEN_INPUTS", "NEEDS_ANSWERS", "GATE_FAIL"):
        kept = _entry(label="x", outcome=outcome, wall_seconds=10, prices=PRICES,
                      model_usage=[_live()])
        assert kept["outcome"] == outcome


def test_an_older_record_not_keyed_by_outcome_is_no_history(history_file):
    history_file.parent.mkdir(parents=True)
    history_file.write_text(json.dumps({"profiles": {"acfc_prx": [_kept("old", "PASS", 1, 60)]}}),
                            encoding="utf-8")
    config = load_config("config/config.yaml")
    history = LiveRunHistory(lambda: config)
    assert history.entries("acfc_prx") == []
    history.record("acfc_prx", _kept("new", "PASS", 2, 70))
    assert [e["label"] for e in history.entries("acfc_prx")] == ["new"]


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
        runner.outcome = "PASS"
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
    assert entry["outcome"] == "PASS"
    assert entry["wall_seconds"] < 0.3                  # the 0.4 s wait is left out
    assert entry["cost_usd"] == pytest.approx((20_000 * 4.0 + 3_000 * 20.0) / 1_000_000)
    view = runner.live_history.view(runner.live_history_profile())
    assert view["runs"] == 1 and view["wall_seconds"] is None     # under three: no range


def test_needs_answers_and_gate_fail_runs_are_kept_as_stopped(history_file):
    from ui.backend.demo import RunNeedsAnswers

    def held_back(runner):
        runner.model_usage = [_live(calls=1)]
        runner.outcome = "NEEDS_ANSWERS"
        raise RunNeedsAnswers("every feed is held back")

    def gate_failed(runner):
        runner.model_usage = [_live()]
        runner.outcome = "GATE_FAIL"
        raise RuntimeError("live run produced no feeds (GATE_FAIL)")

    asked = _runner(held_back)
    asked._run()
    assert asked.state == "needs_answers"
    quarantined = _runner(gate_failed)
    quarantined._run()
    assert quarantined.state == "failed"
    profile = asked.live_history_profile()
    outcomes = [e["outcome"] for e in LiveRunHistory(lambda: asked._store.config).entries(profile)]
    assert sorted(outcomes) == ["GATE_FAIL", "NEEDS_ANSWERS"]


def test_mock_and_failed_runs_are_not_recorded(history_file):
    def mock_work(runner):
        runner.outcome = "PASS"
        runner.model_usage = [StageUsage(stage="layer2", provider="mock", requests=1,
                                         mock_reason="test").as_dict()]

    runner = _runner(mock_work)
    runner._run()
    assert runner.state == "done"

    def failing(runner):
        runner.model_usage = [_live()]
        runner.outcome = "PASS"            # written, then a later step crashed
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
        runner.outcome = "PASS_WITH_OPEN_INPUTS"

    runner = _runner(work)
    monkeypatch.setattr(main, "store", runner._store)
    monkeypatch.setattr(main, "runner", runner)
    client = TestClient(main.app)
    status = client.get("/api/demo/status").json()
    assert "estimates" not in status
    assert status["live_history"]["runs"] == 0
    assert status["live_history"]["profile"] == runner.live_history_profile()
    for _ in range(3):
        runner._run()
    history = client.get("/api/demo/status").json()["live_history"]
    assert history["runs"] == 3 and history["calls"] == {"low": 3, "high": 3}
    assert history["stopped"] is None
    assert history["cost_basis"] == "list" and history["billed_in_dbus"] is True
    assert history["price_source"] == "anthropic list price, 2026-10-06"
