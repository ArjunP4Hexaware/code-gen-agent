"""Model advice on paused layout questions (the dialog's two buttons)."""

from __future__ import annotations

import pytest

from codegen.layout.model import (
    MockLayoutProvider,
    build_advice_request,
    validate_advice,
)

QUESTIONS = [
    {"document": "frd", "key": "feeds[0].frequency", "title": "Load frequency",
     "hint": "How often the file arrives.", "reason": "no label maps", "header": [],
     "candidates": [{"table": 0, "row": 3, "col": 0, "label": "Impact Details"},
                    {"table": 0, "row": 4, "col": 0, "label": "Frequency"}]},
    {"document": "frd", "key": "feeds[0].file_format", "title": "File format",
     "hint": "How the file is laid out.", "reason": "no label maps", "header": [],
     "candidates": [{"table": 0, "row": 3, "col": 0, "label": "Impact Details"},
                    {"table": 0, "row": 5, "col": 0, "label": "IS Owner"}]},
    {"document": "sttm", "key": "S/source/field_name", "title": "Field name",
     "hint": "The column naming each field.", "reason": "no header matches",
     "header": ["A: Attribute", "B: Source Field Name"],
     "candidates": [{"col": 1, "header": "Attribute"}, {"col": 2, "header": "Source Field Name"}]},
]


def test_advice_request_carries_only_question_texts_and_labels():
    request = build_advice_request([{**QUESTIONS[0], "secret": "data row"}])
    assert request["kind"] == "layout_advice"
    assert set(request["questions"][0]) == {"key", "document", "title", "hint", "reason",
                                            "header", "candidates"}
    assert "secret" not in str(request)


def test_mock_advice_picks_matching_labels_and_says_when_none_does():
    provider = MockLayoutProvider([])
    advice = validate_advice(provider.advise_layout(build_advice_request(QUESTIONS)), QUESTIONS)
    assert advice["feeds[0].frequency"]["index"] == 1
    assert "Frequency" in advice["feeds[0].frequency"]["rationale"]
    assert advice["feeds[0].file_format"]["index"] is None
    assert "none of the remaining labels" in advice["feeds[0].file_format"]["rationale"]
    assert advice["S/source/field_name"]["index"] == 1
    assert provider.requests[-1]["kind"] == "layout_advice"


def test_validate_advice_drops_unknown_keys_and_out_of_range_picks():
    response = {"advice": [
        {"key": "feeds[0].frequency", "candidate_index": 7, "rationale": "bad index"},
        {"key": "not_a_question", "candidate_index": 0, "rationale": "x"},
        {"key": "S/source/field_name", "candidate_index": None, "rationale": "r" * 1000},
        "garbage",
    ]}
    advice = validate_advice(response, QUESTIONS)
    assert set(advice) == {"feeds[0].frequency", "S/source/field_name"}
    assert advice["feeds[0].frequency"]["index"] is None
    assert len(advice["S/source/field_name"]["rationale"]) == 400
    assert validate_advice({}, QUESTIONS) == {}
    assert validate_advice({"advice": None}, QUESTIONS) == {}


def test_runner_advises_only_while_waiting(monkeypatch):
    pytest.importorskip("httpx")
    from ui.backend.demo import DemoRunner, LiveRunInProgress
    from ui.backend.service import GenerationStore

    runner = DemoRunner(GenerationStore("config/config.yaml"))
    with pytest.raises(LiveRunInProgress):
        runner.advise_layout(dry_run=True)
    runner.state = "needs_layout"
    runner.layout_questions = list(QUESTIONS)
    advice = runner.advise_layout(dry_run=True)
    assert advice["provider"] == "mock"
    assert advice["advice"]["feeds[0].frequency"]["index"] == 1
    assert runner.status()["layout_advice"] == advice


@pytest.fixture()
def client(monkeypatch):
    httpx = pytest.importorskip("httpx")
    del httpx
    from fastapi.testclient import TestClient

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ui.backend import main

    return TestClient(main.app)


def test_layout_advice_endpoint_guards(client):
    r = client.post("/api/demo/layout-advice", json={})
    assert r.status_code == 400 and "confirm" in r.json()["detail"]
    r = client.post("/api/demo/layout-advice", json={"confirm": True})
    assert r.status_code == 409  # no run is waiting
