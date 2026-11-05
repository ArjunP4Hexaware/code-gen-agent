"""post177 (Soham, 2026-11-05): the grand master / master's PIPELINE_FREQUENCY comes
from the documents - the ONE frequency every feed of the run states - never from a
constant copied out of a production IIG (post102 pinned the pair_11 golden's Daily,
which pair_12's golden contradicts). Feeds that differ, or a feed that states none,
leave it blank + flagged."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from codegen import input_choices
from codegen.contracts.frd import FrdContract
from codegen.metadata_template import (
    RUN_FREQUENCY,
    RUN_FREQUENCY_FLAG,
    RUN_UNRESOLVED,
    _pipeline_roles,
    run_frequency,
    with_run_frequency,
    with_run_frequency_config,
    with_run_frequency_from_frd,
)

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "fixtures" / "acfc_shapes" / "pair_4" / "frd_nb_cob_report.contract.json"
SCHED = "DATA_FACTORY_PIPELINE_SCHEDULE"


def _config():
    from test_iig_corpus_cells import _acfc  # the ACFC overlay (the suite skips it)

    return _acfc()


def _tpl():
    return _config().metadata.templates["iig_v2"]


def _feed(frequency: str | None, name: str = "Feed A"):
    contract = FrdContract.model_validate(json.loads(CONTRACT.read_text(encoding="utf-8")))
    return contract.feeds[0].model_copy(update={"frequency": frequency, "feed_name": name})


def _masters(tpl, feed):
    rows = _pipeline_roles(SCHED, feed, None, tpl)
    return [r for r, role in zip(rows, tpl.pipeline_roles, strict=True)
            if role.role in ("grand_master", "master")]


def test_the_acfc_masters_carry_no_frequency_constant():
    """The hard rule, pinned: no pipeline role states a frequency of its own -
    `run` (from the documents) or nothing (the feed's)."""
    tpl = _tpl()
    assert tpl.pipeline_roles
    for role in tpl.pipeline_roles:
        assert role.frequency in (None, RUN_FREQUENCY), role
    masters = [r.role for r in tpl.pipeline_roles if r.frequency == RUN_FREQUENCY]
    assert masters == ["grand_master", "master"]


def test_feeds_that_agree_give_the_masters_their_frequency():
    tpl = _tpl()
    feeds = [_feed("Weekly", "Feed A"), _feed("Weekly", "Feed B")]
    token, source = run_frequency(feeds, None, tpl)
    assert token == "Weekly" and "2 feed(s)" in source
    resolved = with_run_frequency(tpl, feeds)
    for row in _masters(resolved, feeds[0]):
        cell = row["PIPELINE_FREQUENCY"]
        assert cell["value"] == "Weekly"
        assert cell["badge_entry"]["badge"] == "from_frd"
        assert not (cell["badge_entry"].get("note") or "").startswith(RUN_FREQUENCY_FLAG)


def test_feeds_that_differ_leave_the_masters_blank_and_flagged():
    tpl = _tpl()
    feeds = [_feed("Weekly", "Feed A"), _feed("Monthly", "Feed B")]
    assert run_frequency(feeds, None, tpl) is None
    unresolved = with_run_frequency(tpl, feeds)
    masters = [r for r in unresolved.pipeline_roles if r.role in ("grand_master", "master")]
    assert {(r.frequency, r.frequency_source) for r in masters} == {
        (RUN_FREQUENCY, RUN_UNRESOLVED)}
    # decided once for the run: a later one-feed view (the per-feed IIG) never
    # re-decides it from that feed alone
    assert with_run_frequency(unresolved, [feeds[0]]) is unresolved
    for row in _masters(unresolved, feeds[0]):
        cell = row["PIPELINE_FREQUENCY"]
        assert cell["value"] in (None, "")
        assert cell["badge_entry"]["note"].startswith(f"{RUN_FREQUENCY_FLAG}:")
        # the derived description needs {freq}: it stays open, nothing guessed
        description = row.get("PIPELINE_DESCRIPTION")
        assert description is None or "Daily" not in str(description["value"] or "")


def test_a_feed_that_states_no_frequency_resolves_nothing():
    tpl = _tpl()
    assert run_frequency([_feed("Weekly", "Feed A"), _feed(None, "Feed B")], None, tpl) is None
    assert run_frequency([], None, tpl) is None


def test_the_masters_names_carry_the_run_frequency_or_none():
    config = _config()
    tpl = config.metadata.templates["iig_v2"]
    profile = config.conventions.profiles["acfc_prx"]
    spec = SimpleNamespace(stage_load_strategy="", standard_load_strategy="")
    feed = {"frequency": "Monthly", "frequency_code": "MTH"}
    # unresolved (`run`, the feeds do not agree): no frequency in the masters' names
    for flow in ("grand_master", "master"):
        tokens = input_choices.flow_tokens(feed, spec, profile, flow, config, tpl)
        assert (tokens["frequency"], tokens["frequency_code"]) == ("", "")
    resolved = with_run_frequency(tpl, [_feed("Weekly", "Feed A"), _feed("Weekly", "Feed B")])
    for flow in ("grand_master", "master"):
        tokens = input_choices.flow_tokens(feed, spec, profile, flow, config, resolved)
        assert (tokens["frequency"], tokens["frequency_code"]) == ("Weekly", "WKL")
    # a child keeps its feed's own frequency either way
    assert input_choices.flow_tokens(feed, spec, profile, "file_to_stg", config, resolved)[
        "frequency_code"] == "MTH"


def test_from_frd_reads_the_contract_feeds(tmp_path):
    tpl = _tpl()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["feeds"] = [{**contract["feeds"][0], "frequency": "Weekly"}]
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    resolved = with_run_frequency_from_frd(tpl, path)
    assert {r.frequency for r in resolved.pipeline_roles if r.role in ("grand_master",
                                                                      "master")} == {"Weekly"}
    assert with_run_frequency_from_frd(tpl, None) is tpl
    assert with_run_frequency_from_frd(tpl, tmp_path / "missing.json") is tpl


def _contract_file(tmp_path, frequencies):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = contract["feeds"][0]
    contract["feeds"] = [{**base, "feed_name": f"Feed {i}", "frequency": f}
                         for i, f in enumerate(frequencies)]
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def test_the_run_config_carries_the_decision_to_every_template(tmp_path):
    config = _config()
    agree = with_run_frequency_config(config, _contract_file(tmp_path, ["Weekly", "Weekly"]))
    roles = agree.metadata.templates["iig_v2"].pipeline_roles
    assert [r.frequency for r in roles if r.role in ("grand_master", "master")] == [
        "Weekly", "Weekly"]
    differ = with_run_frequency_config(config, _contract_file(tmp_path, ["Weekly", "Monthly"]))
    roles = differ.metadata.templates["iig_v2"].pipeline_roles
    assert {r.frequency_source for r in roles if r.role in ("grand_master", "master")} == {
        RUN_UNRESOLVED}
    assert with_run_frequency_config(config, None) is config
