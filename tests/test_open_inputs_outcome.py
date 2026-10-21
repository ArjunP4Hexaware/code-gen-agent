"""post58: blocking per open line, and the generate outcome PASS_WITH_OPEN_INPUTS.

CODEGEN_STAGES.json ``questions`` records every open line as ``{line, key, scope,
blocking}``:

- QUESTION / UNRESOLVED are blocking: true. In the App they are the "Answers
  needed" list and the "required (blocking)" environment values.
- INPUT_NEEDED is blocking: false (the App's "not blocking" banner).

Outcomes:

- NEEDS_ANSWERS (exit 3): at least one blocking line is open, whether or not a
  workbook was written. Each feed entry's ``written`` says whether it was, so the
  App can still show the workbook.
- PASS_WITH_OPEN_INPUTS (exit 0): the workbook was written and every open line is
  non-blocking.

``run_stages.pair_outcome`` is the harness summary's reader. The required
environment value and lob_by_file cases are in test_environments.py,
test_environment_profiles.py (mock and live) and test_lob_lookup.py."""

from __future__ import annotations

import json

import pytest

from codegen import cli, run_stages
from codegen.resolve.resolver import normalize_feed_name
from test_iig_corpus_cells import FLOWS, _generate, _pair11

HELD_BACK = "Synthetic Held Back Feed"


def _manifest(tmp_path) -> dict:
    return run_stages.read_stage_manifest(tmp_path / "out")


def _hold_back(sttm) -> None:
    contract = json.loads(sttm.read_text(encoding="utf-8"))
    contract["needs_answers"] = [{"feed_name": HELD_BACK, "sheet": "S9",
                                  "key": "feeds[7].stage_target.schema",
                                  "reason": "no document states the stage schema"}]
    sttm.write_text(json.dumps(contract), encoding="utf-8")


def test_only_non_blocking_inputs_is_pass_with_open_inputs_and_exit_0(tmp_path, capsys):
    config, specs, pair = _pair11(tmp_path)
    code = _generate(config, pair, only_feed=specs[0].feed_id)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    manifest = _manifest(tmp_path)
    assert manifest["exit"] == 0
    assert manifest["stages"]["generate"] == {"status": "PASS_WITH_OPEN_INPUTS"}
    questions = manifest["questions"]
    assert {q["line"] for q in questions} == {"INPUT_NEEDED"}
    assert not any(q["blocking"] for q in questions)
    # the run-level block (post61: the email status set is a profile default, not open;
    # post81: application_name too): the environment + EMAIL_TO. No feed-level one —
    # the pipeline names (shipped convention) and ACTIVE_START_DATE are written
    assert sorted(q["key"] for q in questions) == ["run.email_to", "run.environment"]
    assert [q["scope"] for q in questions].count("feed") == 0
    assert all(set(q) == {"line", "key", "scope", "blocking"} for q in questions)
    (feed,) = manifest["feeds"]
    assert feed["written"] is True
    assert feed["status"] in ("PASS", "PASS_WITH_FLAGS")             # the gate verdict
    assert feed["open"] == {"blocking": 0, "non_blocking": 0}
    assert manifest["stages"]["iig_emit"] == {"status": "PASS"}
    outcome = [ln for ln in out.splitlines() if ln.startswith("OUTCOME")]
    assert outcome == ["OUTCOME         generate — PASS_WITH_OPEN_INPUTS: 1 feed(s) written; "
                       "2 input(s) still open, none blocking (answers_template.yaml); exit 0"]
    steps = {"layout": 0, "extract-sttm": 0, "generate": code}
    assert run_stages.pair_outcome(steps, tmp_path / "out") == "PASS_WITH_OPEN_INPUTS"


def test_every_input_answered_is_pass(tmp_path, capsys):
    config, specs, pair = _pair11(tmp_path)
    feed = specs[0].feed_id
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        "inputs:\n  run:\n    environment: {value: D1}\n"
        '    application_name: {value: "v-application_name"}\n'
        '    email_to: {value: "syn.dl@synthetic.example"}\n'
        '    email_statuses: {value: "all"}\n'
        f"  feeds:\n    {feed}:\n"
        '      active_start_date: {value: "2026-11-01 00:00:00"}\n'
        + "".join(f'      "pipeline_name.{flow}": {{value: "SYN_PL_{flow.upper()}"}}\n'
                  for flow in FLOWS), encoding="utf-8")
    assert _generate(config, pair, only_feed=feed, answers_path=answers) == cli.EXIT_OK
    manifest = _manifest(tmp_path)
    assert manifest["stages"]["generate"] == {"status": "PASS"}
    assert manifest["questions"] == []
    assert manifest["feeds"][0]["open"] == {"blocking": 0, "non_blocking": 0}
    assert not [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("OUTCOME")]


def test_a_blocking_question_with_the_workbook_written_is_needs_answers(tmp_path, capsys):
    """Without --feed, the feeds that have a contract are written and a held-back
    feed's QUESTION stays open: NEEDS_ANSWERS, exit 3, the written feeds marked
    written: true."""
    config, _specs, (frd, sttm) = _pair11(tmp_path)
    _hold_back(sttm)
    code = _generate(config, (frd, sttm), only_feed=None)
    out = capsys.readouterr().out
    assert code == cli.EXIT_NEEDS_ANSWERS, out
    manifest = _manifest(tmp_path)
    assert manifest["exit"] == 3
    assert manifest["stages"]["generate"] == {"status": "NEEDS_ANSWERS"}
    assert manifest["feeds"] and all(f["written"] for f in manifest["feeds"])
    assert manifest["stages"]["iig_emit"] == {"status": "PASS"}       # the workbook is there
    assert [q for q in manifest["questions"] if q["blocking"]] == [
        {"line": "QUESTION", "key": "feeds[7].stage_target.schema", "scope": "feed",
         "blocking": True}]
    outcome = [ln for ln in out.splitlines() if ln.startswith("OUTCOME")]
    assert len(outcome) == 1 and outcome[0].startswith(
        "OUTCOME         generate — NEEDS_ANSWERS: 1 blocking question(s) open")
    steps = {"layout": 0, "extract-sttm": 0, "generate": code}
    assert run_stages.pair_outcome(steps, tmp_path / "out") == "NEEDS_ANSWERS"


def test_a_feed_held_back_and_asked_for_is_needs_answers_with_nothing_written(tmp_path, capsys):
    config, _specs, (frd, sttm) = _pair11(tmp_path)
    _hold_back(sttm)
    code = _generate(config, (frd, sttm), only_feed=normalize_feed_name(HELD_BACK))
    assert code == cli.EXIT_NEEDS_ANSWERS, capsys.readouterr().out
    manifest = _manifest(tmp_path)
    assert manifest["stages"]["generate"] == {"status": "NEEDS_ANSWERS"}
    assert manifest["feeds"] == []


def _item(line, feed=None):
    return run_stages.open_item(line, "k", feed=feed)


@pytest.mark.parametrize(("items", "expected"), [
    ([], "PASS"),
    ([_item("INPUT_NEEDED", "a")], "PASS_WITH_OPEN_INPUTS"),
    ([_item("INPUT_NEEDED")], "PASS_WITH_OPEN_INPUTS"),                  # run-level
    ([_item("QUESTION", "a")], "NEEDS_ANSWERS"),
    ([_item("QUESTION")], "NEEDS_ANSWERS"),                              # the environment
    ([_item("UNRESOLVED", "b"), _item("INPUT_NEEDED", "a")], "NEEDS_ANSWERS"),
])
def test_generate_outcome(items, expected):
    assert run_stages.generate_outcome(crashed=False, hard_failed=False, gate_failed=False,
                                       open_items=items) == expected


def test_a_failure_outranks_open_lines():
    items = [_item("QUESTION", "b")]
    assert run_stages.generate_outcome(crashed=True, hard_failed=True, gate_failed=True,
                                       open_items=items) == "CRASHED"
    assert run_stages.generate_outcome(crashed=False, hard_failed=False, gate_failed=True,
                                       open_items=items) == "GATE_FAIL"
    assert run_stages.OUTCOMES.index("NEEDS_ANSWERS") \
        < run_stages.OUTCOMES.index("PASS_WITH_OPEN_INPUTS") < run_stages.OUTCOMES.index("PASS")


def test_pair_outcome_is_the_worst_step_and_reads_only_this_runs_manifest(tmp_path):
    out = tmp_path / "out"
    assert run_stages.pair_outcome({}, out) == "FAIL"
    assert run_stages.pair_outcome({"layout": 3}, out) == "NEEDS_ANSWERS"
    assert run_stages.pair_outcome({"layout": 0, "extract-sttm": 1}, out) == "FAIL"
    assert run_stages.pair_outcome({"layout": 0, "generate": 0}, out) == "PASS"  # no manifest
    run_stages.write_stage_manifest(
        out, command="generate", exit_code=0,
        statuses=run_stages.stage_statuses("PASS_WITH_OPEN_INPUTS", {}), feeds=[],
        questions=[_item("INPUT_NEEDED", "a")])
    assert run_stages.pair_outcome({"generate": 0}, out) == "PASS_WITH_OPEN_INPUTS"
    # another run's manifest (its exit differs from this step's) is not read
    assert run_stages.pair_outcome({"generate": 1}, out) == "FAIL"
    # a worse earlier step wins
    assert run_stages.pair_outcome({"extract-vdd": 1, "generate": 0}, out) == "FAIL"
    run_stages.write_stage_manifest(
        out, command="generate", exit_code=1,
        statuses=run_stages.stage_statuses("GATE_FAIL", {}), feeds=[])
    assert run_stages.pair_outcome({"layout": 0, "generate": 1}, out) == "GATE_FAIL"
    assert "pair_outcome" in run_stages.__all__
