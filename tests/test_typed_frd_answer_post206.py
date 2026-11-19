"""post206 (the tester's dead end, 2026-11-19): an FRD field the reader could not
place was asked as a choice over FRD table cells only. When no cell states it, the
person had "None of these" alone, and "proceed" held the feed and asked the SAME
question again. A field whose typed value the layout stage applies
(``layout.resolve.answerable_frd_field``) is now marked ``typed`` (the page offers a
text box, plus the deliberate blank where ``answers.blankable_fields`` allows it)."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from acfc_shapes import cold_pairs
from codegen.config import load_config

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"


@pytest.fixture
def config():
    return load_config(REPO / "config" / "config.yaml")


def _role(key: str, document: str = "frd") -> dict:
    return {"document": document, "key": key, "kind": "role", "candidates": [],
            "reason": "no label in the document maps to this field"}


def test_an_answerable_frd_field_is_marked_typed_with_its_blank_choice(config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import typed_frd_question

    fmt = typed_frd_question(_role("feeds[0].file_format"), config)
    assert fmt["typed"] is True
    assert fmt["leave_blank"] == config.answers.leave_blank      # a blankable field
    assert fmt["example"]                                        # the field's example
    lobs = typed_frd_question(_role("feeds[2].lobs"), config)
    assert lobs["typed"] is True and lobs["leave_blank"] is None  # typed, never blank
    assert typed_frd_question(_role("feeds[0].domain"), config)["typed"] is True


def test_other_questions_are_left_as_they_are(config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import typed_frd_question

    # an answer cannot rename a feed - no text box for the feed's name
    name = _role("feeds[0].feed_name")
    assert typed_frd_question(name, config) == name
    column = _role("MAPPING/stage/table", document="sttm")
    assert typed_frd_question(column, config) == column
    text = _role("feeds[0].file_format") | {"kind": "text"}
    assert typed_frd_question(text, config) == text              # already typed


@pytest.fixture
def app_roles(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    for role in ("state", "outputs"):
        (tmp_path / role).mkdir()
        monkeypatch.setenv(f"CODEGEN_STORAGE_{role.upper()}",
                           f"local:{(tmp_path / role).as_posix()}")
    return tmp_path


def _wait(runner, *states: str, timeout: float = 300.0) -> str:
    deadline = time.monotonic() + timeout
    while runner.state not in states:
        assert time.monotonic() < deadline, f"stuck in {runner.state}: {runner.stages[-3:]}"
        time.sleep(0.05)
    return runner.state


def test_the_app_takes_a_typed_value_for_an_frd_field_no_cell_states(app_roles):
    """cold_5: a prose FRD - no field placeable. The layout dialog marks its FRD
    field questions typed; a typed LOBs answer + proceed is applied (the run never
    asks LOBs again), where before only "None of these" was possible."""
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, index_warmup=False)
    runner.selected_workbook = SHAPES / cold_pairs.sttm_path("cold_5")
    frd = SHAPES / cold_pairs.frd_path("cold_5")
    runner.select_frd(frd, frd.name)
    runner.start_live()
    assert _wait(runner, "needs_layout", "needs_answers", "failed", "done") == "needs_layout"
    questions = {q["key"]: q for q in runner.status()["layout_questions"]}
    lobs = questions["feeds[0].lobs"]
    assert lobs["kind"] == "role" and lobs["document"] == "frd"
    assert lobs["typed"] is True and lobs["leave_blank"] is None
    assert not questions.get("feeds[0].feed_name", {}).get("typed")
    runner.answer_layout({"gaps": {"feeds[0].lobs": {"value": "ALL", "source": "user"}}},
                         proceed=True)
    deadline = time.monotonic() + 60
    while runner.state == "needs_layout":
        assert time.monotonic() < deadline
        time.sleep(0.05)
    state = _wait(runner, "needs_answers", "failed", "done")
    status = runner.status()
    keys = {item["key"] for item in status["needs_answers"]}
    assert "feeds[0].lobs" not in keys, (state, sorted(keys))
    # what is still owed after "proceed" carries the typed marker too
    for item in status["needs_answers"]:
        question = item["question"]
        if question.get("kind", "role") == "role" and question.get("document") == "frd" \
                and item["key"] != "feeds[0].feed_name":
            assert question.get("typed") is True, item["key"]
