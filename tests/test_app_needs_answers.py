"""The App path for held-back feeds, and readable errors (Chunk C, 2026-10-09).

The demo App runs generation IN-PROCESS: there is no CLI exit code 3 there. A
run whose feeds are held back (NEEDS_ANSWERS — a band nothing names, a target
no document states, a file question left open) must end with the list of what
they need, answerable inline and re-runnable — and a run where EVERY feed is
held back must end in state ``needs_answers``, never "live run produced no
feeds". Any exception nobody caught becomes JSON the error card renders.

Shapes: ``tests/acfc_shapes/bands.py`` (synthetic, Chunk A). Layer 2 and the
layout recognizer are mock-locked; state and outputs live in tmp roles.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend.demo import (  # noqa: E402
    DemoRunner,
    LiveRunInProgress,
    layout_feed_key,
    merge_answers,
    needs_answer_item,
)
from ui.backend.service import GenerationStore  # noqa: E402

from acfc_shapes import bands  # noqa: E402
from acfc_shapes.common import xlsx_bytes  # noqa: E402
from test_harness_answer_lines import _NEEDED_KEY_RE  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SHEET = bands.SHEET
BAND_KEYS = [f"{SHEET}/band[{n}]/layer" for n in (1, 2, 3)]
BAND_ANSWERS = dict(zip(BAND_KEYS, ("source", "stage", "standard"), strict=True))


def _frd(tmp_path: Path) -> Path:
    """The look-alike sheet's FRD — catalogs stated (the suite runs without the
    ACFC overlay's default_catalog)."""
    contract = bands.frd_contract(stage_schema="nb_land")
    contract["feeds"][0]["stage_target"]["catalog"] = "nb_dlk"
    contract["feeds"][0]["standard_target"]["catalog"] = "nb_std"
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return path


@pytest.fixture()
def roles(monkeypatch, tmp_path):
    """Mock-locked providers; state and outputs in tmp local roles (the runtime
    layout cache too — never the checkout's ui/backend/state)."""
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    for role in ("state", "outputs"):
        (tmp_path / role).mkdir()
        monkeypatch.setenv(f"CODEGEN_STORAGE_{role.upper()}",
                           f"local:{(tmp_path / role).as_posix()}")
    return tmp_path


def _runner(tmp_path: Path) -> tuple[DemoRunner, GenerationStore]:
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, index_warmup=False)
    workbook = tmp_path / f"STTM_{bands.FEED}.xlsx"
    workbook.write_bytes(xlsx_bytes(bands.three_lookalike()))
    runner.selected_workbook = workbook
    runner.select_frd(_frd(tmp_path), "frd.contract.json")
    return runner, store


def _wait(runner: DemoRunner, *states: str, timeout: float = 300.0) -> str:
    deadline = time.monotonic() + timeout
    while runner.state not in states:
        assert time.monotonic() < deadline, f"stuck in {runner.state}: {runner.stages[-3:]}"
        time.sleep(0.05)
    return runner.state


def _hold_every_feed_back(runner: DemoRunner) -> dict:
    """Generate, then 'Proceed with unresolved' on the three band questions:
    the only sheet is held back."""
    runner.start_live()
    assert _wait(runner, "needs_layout", "failed", "done") == "needs_layout", runner.error
    assert [q["key"] for q in runner.status()["layout_questions"]] == BAND_KEYS
    runner.answer_layout({}, proceed=True)
    _wait(runner, "needs_answers", "failed", "done")
    return runner.status()


def test_every_feed_held_back_ends_as_needs_answers_then_answers_complete_the_run(roles):
    runner, store = _runner(roles)
    status = _hold_every_feed_back(runner)

    # Not a generic failure: state needs_answers, no error, the list.
    assert status["state"] == "needs_answers", (status["error"], status["stages"][-3:])
    assert status["error"] is None and status["error_detail"] is None
    assert "produced no feeds" not in json.dumps(status)
    items = status["needs_answers"]
    assert [i["key"] for i in items] == BAND_KEYS
    for item in items:
        assert (item["label"], item["section"], item["answer_as"]) == (
            "UNRESOLVED", "answers", "band_layer")
        # A band nothing names holds its SHEET back (its feed is matched only
        # once the bands are known) — the sheet names the held-back feed.
        assert item["feed_name"] == SHEET and item["sheet"] == SHEET
        question = item["question"]
        assert question["kind"] == "role" and question["role"] == "layer"
        assert question["candidates"] == [{"value": v, "label": v}
                                          for v in ("source", "stage", "standard")]
        assert question["title"] and question["hint"] and question["reason"]
        # The CLI's line for the same key is what the harness reads.
        assert _NEEDED_KEY_RE.match(f"{item['label']:<15}{item['key']} — {item['reason']}")
    assert status["needs_answers_inputs"] == {"sttm": f"STTM_{bands.FEED}.xlsx",
                                              "frd": "frd.contract.json"}
    assert [a["label"] for a in status["set_aside"]] == [SHEET] * 3
    assert all("answers file: under `answers:`" in a["error"] for a in status["set_aside"])
    assert any(s["stage"] == "needs answers" for s in status["stages"])
    assert not store.runs or store.mode != "live"          # nothing was published

    # The list survives later status reads (a poll, a page reload).
    assert runner.status()["needs_answers"] == items

    # Answer inline and re-run: the band layers go to the STTM answers.
    runner.rerun_with_answers({"sttm": dict(BAND_ANSWERS)})
    assert _wait(runner, "done", "failed", "needs_answers", "needs_layout") == "done", (
        runner.error, runner.stages[-5:])
    status = runner.status()
    assert status["needs_answers"] == [] and status["set_aside"] == []
    assert any(s["stage"] == "answers carried" for s in status["stages"])
    assert list(store.runs) and store.mode == "live"
    assert runner.last_answers["sttm"] == BAND_ANSWERS


def test_rerun_validates_answers_and_refuses_changed_documents(roles):
    runner, _store = _runner(roles)
    _hold_every_feed_back(runner)
    with pytest.raises(ValueError, match="source | stage | standard"):
        runner.rerun_with_answers({"sttm": {BAND_KEYS[0]: "landing"}})
    with pytest.raises(ValueError, match="bad gap answer"):
        runner.rerun_with_answers({"gaps": {"feeds[0].stage_target.schema": "nb"}})
    assert runner.state == "needs_answers"                # nothing started
    other = roles / "other.xlsx"
    other.write_bytes(xlsx_bytes(bands.three_lookalike(titles=True)))
    runner.selected_workbook = other
    with pytest.raises(ValueError, match="documents changed"):
        runner.rerun_with_answers({"sttm": dict(BAND_ANSWERS)})


def test_a_run_paused_on_its_dialog_refuses_a_second_start(roles):
    runner, _store = _runner(roles)
    runner.start_live()
    assert _wait(runner, "needs_layout", "failed", "done") == "needs_layout"
    with pytest.raises(LiveRunInProgress):
        runner.start_live()
    with pytest.raises(LiveRunInProgress):
        runner.rerun_with_answers({})
    runner.answer_layout({}, cancel=True)
    assert _wait(runner, "failed") == "failed"
    # A cancelled run is a readable failure: type, message, innermost frame, health.
    detail = runner.status()["error_detail"]
    assert detail["type"] == "RuntimeError" and "cancelled" in detail["message"]
    assert detail["where"].startswith("ui/backend/demo.py:") and " in _resolve_layout" in \
        detail["where"]
    assert detail["health_line"].startswith("version ")


def _cancel_at_pairing(runner: DemoRunner) -> None:
    """The run-start pairing question, cancelled by the person: the run fails
    BEFORE its layout is resolved (where a re-run's answers are applied)."""
    def cancelled() -> None:
        raise RuntimeError("pairing cancelled by the user")

    runner._ask_pairing = cancelled


def test_a_rerun_that_fails_before_layout_never_seeds_the_next_run(roles):
    """A re-run's answers belong to THAT run: one cancelled before its layout
    is resolved leaves nothing armed, so the next ordinary Generate — here on
    another workbook whose sheet has the same name — asks its own questions
    instead of taking answers given for the first workbook."""
    runner, _store = _runner(roles)
    _hold_every_feed_back(runner)
    _cancel_at_pairing(runner)
    runner.rerun_with_answers({"sttm": dict(BAND_ANSWERS)})
    assert _wait(runner, "failed", "done", "needs_answers", "needs_layout") == "failed"
    assert "pairing cancelled" in runner.status()["error"]
    del runner._ask_pairing                                  # the real one again

    other = roles / "other.xlsx"
    other.write_bytes(xlsx_bytes(bands.three_lookalike()))
    runner.selected_workbook = other
    runner.start_live()
    assert _wait(runner, "needs_layout", "failed", "done", "needs_answers") == "needs_layout", (
        runner.error, runner.stages[-3:])
    assert not any(s["stage"] == "answers carried" for s in runner.stages)
    assert [q["key"] for q in runner.status()["layout_questions"]] == BAND_KEYS
    runner.answer_layout({}, cancel=True)
    assert _wait(runner, "failed") == "failed"


def test_a_rerun_whose_documents_change_at_run_start_drops_its_answers(roles):
    """The answers are bound to the documents the re-run was asked for: when
    the run-start pairing hands the run another FRD, they name the old pair's
    sheets — dropped (said as a stage), the questions asked afresh."""
    runner, _store = _runner(roles)
    _hold_every_feed_back(runner)
    other_frd = roles / "frd_other.contract.json"
    other_frd.write_bytes(runner.effective_frd().read_bytes())

    def pairing_picks_another_frd() -> None:
        runner.selected_frd = other_frd
        runner.selected_frd_label = other_frd.name

    runner._ask_pairing = pairing_picks_another_frd
    runner.rerun_with_answers({"sttm": dict(BAND_ANSWERS)})
    assert _wait(runner, "needs_layout", "failed", "done", "needs_answers") == "needs_layout", (
        runner.error, runner.stages[-3:])
    stages = [s["stage"] for s in runner.stages]
    assert "answers not carried" in stages and "answers carried" not in stages
    assert [q["key"] for q in runner.status()["layout_questions"]] == BAND_KEYS
    runner.answer_layout({}, cancel=True)
    assert _wait(runner, "failed") == "failed"


def test_some_feeds_held_back_end_done_and_a_failure_keeps_the_open_questions(roles):
    """Some feeds held back: the run is DONE and the list says what the others
    need. A run that fails after "Proceed with unresolved" keeps the questions
    it left open answerable, beside the readable error."""
    runner, _store = _runner(roles)
    held = needs_answer_item({"key": "feeds[1].stage_target.schema", "kind": "text",
                              "document": "frd", "reason": "blank"}, feed_name="nb_second")
    runner._work = lambda: runner._run_items.append(held)
    runner.start_live()
    assert _wait(runner, "done", "failed") == "done"
    assert runner.status()["needs_answers"] == [held] and runner.status()["error"] is None

    left_open = needs_answer_item({"key": f"{SHEET}/stage/table", "kind": "role",
                                   "document": "sttm", "reason": "no TableName header"})

    def work():
        runner._open_owed = [left_open]
        raise ValueError("the stage band has no values for ['table']")

    runner._work = work
    runner.start_live()
    assert _wait(runner, "failed", "done") == "failed"
    status = runner.status()
    assert status["needs_answers"] == [left_open]
    detail = status["error_detail"]
    assert (detail["type"], detail["message"]) == (
        "ValueError", "the stage band has no values for ['table']")
    assert detail["where"].startswith("tests/test_app_needs_answers.py:")
    assert detail["where"].endswith(" in work")


def test_a_done_run_keeps_the_owed_questions_proceed_left_open(roles):
    """Some feeds generated, one failed for want of an answer the person
    skipped with "Proceed with unresolved": the run is DONE and the owed
    question is still listed (beside the held-back feeds' keys), so the failed
    feed can be answered inline and re-run — as the CLI prints its QUESTION /
    UNRESOLVED line whatever the exit code."""
    runner, _store = _runner(roles)
    held = needs_answer_item({"key": "feeds[1].stage_target.schema", "kind": "text",
                              "document": "frd", "reason": "blank"}, feed_name="nb_second")
    left_open = needs_answer_item({"key": f"{SHEET}/stage/table", "kind": "role",
                                   "document": "sttm", "reason": "no TableName header"})

    def work():
        runner._open_owed = [left_open, held]           # one key owed AND held back
        runner._run_items.append(held)

    runner._work = work
    runner.start_live()
    assert _wait(runner, "done", "failed") == "done"
    status = runner.status()
    assert status["error"] is None
    # The held-back item first (it names its feed), each key once.
    assert status["needs_answers"] == [held, left_open]


def test_needs_answer_item_routes_each_key_kind():
    band = needs_answer_item({"key": "S/band[2]/layer", "kind": "role", "document": "sttm"})
    role = needs_answer_item({"key": "S/stage/table", "kind": "role", "document": "sttm"})
    cell = needs_answer_item({"key": "feeds[0].lobs", "kind": "role", "document": "frd"})
    gap = needs_answer_item({"key": "feeds[0].file_name_patterns", "kind": "choice",
                             "document": "frd"})
    text = needs_answer_item({"key": "feeds[1].stage_target.schema", "kind": "text",
                              "document": "frd"})
    assert [(i["answer_as"], i["section"], i["label"]) for i in (band, role, cell, gap, text)] \
        == [("band_layer", "answers", "UNRESOLVED"), ("column", "answers", "UNRESOLVED"),
            ("frd_cell", "answers", "UNRESOLVED"), ("gap", "gaps", "QUESTION"),
            ("gap", "gaps", "QUESTION")]


def test_a_held_back_key_is_renumbered_to_the_layout_contract():
    """The extractor reads the run's FRD, which leaves out the feeds set aside
    without a file: its feeds[1] is the layout contract's feeds[2]."""
    class F:
        def __init__(self, name):
            self.feed_name = name

    layout = [F("a"), F("b"), F("c")]
    run = [layout[0], layout[2]]
    assert layout_feed_key("feeds[1].stage_target.schema", run, layout) \
        == "feeds[2].stage_target.schema"
    assert layout_feed_key("S/band[1]/layer", run, layout) == "S/band[1]/layer"
    assert layout_feed_key("feeds[0].stage_target.tables", layout, layout) \
        == "feeds[0].stage_target.tables"
    assert merge_answers({"sttm": {"a": 1}}, {"sttm": {"b": "stage"}, "gaps": {}}) == {
        "sttm": {"a": 1, "b": "stage"}, "frd": {}, "vdd": {}, "gaps": {}}


# ------------------------------------------------------------------ the API


@pytest.fixture()
def client(monkeypatch):
    """The App with its unhandled-exception handler; server exceptions come
    back as responses (what a browser sees), not re-raised into the test."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ui.backend import main

    if main.store is not None:
        reasoning = main.store.config.reasoning.model_copy(update={"provider": "anthropic"})
        monkeypatch.setattr(main.store, "config",
                            main.store.config.model_copy(update={"reasoning": reasoning}))
    return TestClient(main.app, raise_server_exceptions=False)


def test_an_uncaught_exception_in_a_route_is_json_with_where_and_health(client, monkeypatch):
    from ui.backend import main

    def boom():
        raise KeyError("selection.json has no 'sttm'")

    monkeypatch.setattr(main.runner, "status", boom)
    response = client.get("/api/demo/status")
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["detail"].startswith("KeyError: ")
    error = body["error"]
    assert error["type"] == "KeyError" and "selection.json" in error["message"]
    # The traceback's innermost frame: file:line in function.
    assert error["where"].startswith("tests/test_app_needs_answers.py:")
    assert error["where"].endswith(" in boom")
    assert error["request"] == "GET /api/demo/status"
    facts = client.get("/api/health/facts").json()
    assert error["health"] == {k: facts[k] for k in ("version", "codegen_source",
                                                     "config_overlays", "startup_error")}
    assert error["health_line"] == facts["health_line"]
    assert "startup error: none" in error["health_line"]


def test_an_error_card_never_carries_a_secret_env_value(client, monkeypatch):
    from ui.backend import main

    monkeypatch.setenv("SYNTHETIC_API_TOKEN", "tok-synthetic-123456")

    def boom():
        raise RuntimeError("upstream said no for tok-synthetic-123456")

    monkeypatch.setattr(main.runner, "status", boom)
    body = client.get("/api/demo/status").json()
    assert "tok-synthetic-123456" not in json.dumps(body)
    assert "<SYNTHETIC_API_TOKEN masked>" in body["error"]["message"]


def test_rerun_endpoint_guards(client):
    response = client.post("/api/demo/rerun-with-answers", json={"answers": {}})
    assert response.status_code == 400 and "confirm" in response.json()["detail"]
    # No key in the test process: live is unavailable, so nothing can start.
    response = client.post("/api/demo/rerun-with-answers",
                           json={"answers": {"sttm": {BAND_KEYS[0]: "stage"}},
                                 "confirm": True})
    assert response.status_code == 400 and "unavailable" in response.json()["detail"]
