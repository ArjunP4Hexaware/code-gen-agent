"""post145: the confirm dialog says what a pair the agent has not mapped before
costs. Runs on pairs it already mapped make no layout call (cached, or read by
the synonyms), so their measured ranges read 0 calls; a new pair's first run
makes the layout calls. That cost is in DBUs: measured from the recorded runs
whose layout stage sent FM API calls (tokens x ``reasoning.dbu_rates``), else
the configured, cited ``demo.new_pair_layout_estimate``. Synthetic usage only;
no model is called.
"""

from __future__ import annotations

from ui.backend.run_history import new_pair_cost, run_entry, summary

from codegen.config import DbuRateConfig, NewPairLayoutEstimate, load_config
from codegen.reasoning.usage import StageUsage

RATE = DbuRateConfig(input=57.143, output=285.714, source="FM API rate, synthetic test")
RATES = {"claude-opus-5-5": RATE}
ESTIMATE = NewPairLayoutEstimate(dbu_low=1.5, dbu_high=4.5, source="offline estimate, test")


def _usage(stage: str, *, calls: int, input_tokens: int, output_tokens: int,
           provider: str = "databricks_fmapi", model: str = "claude-opus-5-5") -> dict:
    return StageUsage(stage=stage, provider=provider, endpoint="databricks-claude-opus-5-5",
                      model=model, calls=calls, requests=calls, seconds=10.0,
                      input_tokens=input_tokens, output_tokens=output_tokens).as_dict()


def _entry(*usages: dict, outcome: str = "PASS") -> dict:
    return run_entry(label="demo_x", model_usage=list(usages), wall_seconds=60.0,
                     outcome=outcome)


def test_a_recorded_stage_keeps_its_name():
    entry = _entry(_usage("layout", calls=2, input_tokens=10, output_tokens=5))
    assert entry["stages"][0]["stage"] == "layout"


def test_measured_layout_runs_give_the_dbu_range():
    runs = [_entry(_usage("layout", calls=2, input_tokens=5_757, output_tokens=9_860)),
            _entry(_usage("layout", calls=3, input_tokens=11_514, output_tokens=19_720),
                   outcome="NEEDS_ANSWERS")]               # a stopped run measured it too
    cost = new_pair_cost(runs, dbu_rates=RATES, estimate=ESTIMATE)
    assert cost == {"measured_runs": 2, "calls": {"low": 2, "high": 3},
                    "dbu": {"low": 3.15, "high": 6.29}, "source": "FM API rate, synthetic test"}


def test_only_the_layout_stage_counts():
    runs = [_entry(_usage("layer2", calls=4, input_tokens=5_757, output_tokens=9_860))]
    assert new_pair_cost(runs, dbu_rates=RATES, estimate=ESTIMATE)["measured_runs"] == 0


def test_no_measurement_says_the_estimate_as_one():
    runs = [_entry(_usage("layout", calls=0, input_tokens=0, output_tokens=0))]
    assert new_pair_cost(runs, dbu_rates=RATES, estimate=ESTIMATE) == {
        "measured_runs": 0, "calls": None, "dbu": {"low": 1.5, "high": 4.5},
        "source": "offline estimate, test"}


def test_a_model_without_a_rate_or_a_non_fmapi_call_is_never_priced():
    unrated = _entry(_usage("layout", calls=2, input_tokens=10, output_tokens=5, model="other"))
    direct = _entry(_usage("layout", calls=2, input_tokens=10, output_tokens=5,
                           provider="anthropic"))
    assert new_pair_cost([unrated, direct], dbu_rates=RATES, estimate=None) is None


def test_the_summary_carries_it_even_before_enough_completed_runs():
    view = summary([], profile="acfc_prx", dbu_rates=RATES, new_pair_estimate=ESTIMATE)
    assert view["runs"] == 0
    assert view["new_pair"]["dbu"] == {"low": 1.5, "high": 4.5}


def test_the_shipped_rate_reproduces_the_measured_layer2_run():
    # CHANGELOG post123: pair_11's Layer-2 run, 5,757 in / 9,860 out = 3.15 DBU
    config = load_config("config/config.yaml")
    rate = config.reasoning.dbu_rates["claude-opus-5-5"]
    assert round(rate.dbu(input_tokens=5_757, output_tokens=9_860), 2) == 3.15
    # post148: Venu's conservative approximation, its source named
    estimate = config.demo.new_pair_layout_estimate
    assert (estimate.dbu_low, estimate.dbu_high) == (6, 8)
    assert "Venu" in estimate.source
