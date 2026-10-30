"""post159 (P2-2, L2-5): a Layer-2 answer is bounded by reasoning.response_limits.

``rationale``, ``code_candidate``, each citation and the citations list have a
config-driven maximum length; an over-limit answer is a schema failure - the
ask loop retries it with the error, then records a failed candidate - never a
crash and never an accepted 5 MB answer. Stub transports only (the suite
blocks live model calls); synthetic text."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codegen.reasoning.engine import reason_over_packs
from codegen.reasoning.schema import CandidateResponse, ContextPack, limits_context
from test_layer2_failures import _provider

RULE = "Reject the file when the trailer record count does not match the detail rows"
FIVE_MB = 5 * 1024 * 1024


@pytest.fixture(autouse=True)
def _live(monkeypatch):
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")


def _pack() -> ContextPack:
    return ContextPack(feed_id="feed_a", rule_text=RULE, contract_excerpts=[RULE],
                       available_source_columns=["a"], available_stage_columns=["A"],
                       audit_columns=["LOB"])


def _answer(**update) -> dict:
    return {"classification": "mappable", "code_candidate": "# sketch",
            "rationale": "because", "citations": [RULE], **update}


def _batch(**update) -> str:
    return json.dumps({"candidates": [{**_answer(**update), "rule": 1}]})


def test_the_limits_are_config_knobs(config):
    limits = config.reasoning.response_limits
    assert limits.rationale_max_chars < FIVE_MB
    assert limits.code_candidate_max_chars < FIVE_MB
    assert limits.citation_max_chars < FIVE_MB
    assert limits.citations_max_items > 0


@pytest.mark.parametrize("field, value", [
    ("rationale", "x" * FIVE_MB),
    ("code_candidate", "# " + "x" * FIVE_MB),
    ("citations", [RULE, "y" * FIVE_MB]),
], ids=["rationale", "code_candidate", "citation"])
def test_a_5_mb_stub_answer_is_a_failed_candidate(config, monkeypatch, field, value):
    answer = _batch(**{field: value})
    provider, sent = _provider(config, monkeypatch, [answer, answer])
    (candidate,) = reason_over_packs([_pack()], provider, reasoning=config.reasoning)
    assert candidate.response is None and not candidate.grounded
    assert len(sent) == config.reasoning.max_attempts       # retried, then recorded
    assert "schema validation failed" in sent[1]["prompt"]
    assert all("schema validation failed" in f.reason and "response_limits" in f.reason
               for f in provider.failures)
    (note,) = candidate.failure_notes
    assert "response_limits" in note and len(note) < 2000   # the text is never echoed


def test_too_many_citations_is_a_schema_failure(config, monkeypatch):
    many = [RULE] * (config.reasoning.response_limits.citations_max_items + 1)
    provider, _sent = _provider(config, monkeypatch, [_batch(citations=many)] * 2)
    (candidate,) = reason_over_packs([_pack()], provider, reasoning=config.reasoning)
    assert candidate.response is None
    assert "citations_max_items" in candidate.failure_notes[0]


def test_an_over_limit_answer_the_retry_fixes_is_kept(config, monkeypatch):
    provider, sent = _provider(config, monkeypatch,
                               [_batch(rationale="x" * FIVE_MB), _batch()])
    (candidate,) = reason_over_packs([_pack()], provider, reasoning=config.reasoning)
    assert len(sent) == 2 and candidate.response is not None and candidate.grounded
    assert [f.recovered for f in provider.failures] == [True]


def test_the_rule_by_rule_path_is_bounded_too(config, monkeypatch):
    provider, _sent = _provider(config, monkeypatch,
                                [json.dumps(_answer(rationale="x" * FIVE_MB))] * 2)
    per_rule = type("PerRule", (), {"name": provider.name, "complete": provider.complete})()
    (candidate,) = reason_over_packs([_pack()], per_rule, reasoning=config.reasoning)
    assert candidate.response is None
    assert "rationale_max_chars" in candidate.failure_notes[0]


def test_an_answer_built_in_code_is_bounded_by_the_engine(config):
    class Stub:
        name = "stub"

        def complete(self, pack):
            return CandidateResponse(classification="mappable", code_candidate="x" * FIVE_MB,
                                     rationale="r", citations=[pack.rule_text])

    (candidate,) = reason_over_packs([_pack()], Stub(), reasoning=config.reasoning)
    assert candidate.response is None and not candidate.grounded
    assert "code_candidate_max_chars" in candidate.failure_notes[0]


def test_the_limit_is_the_knob_not_a_literal(config):
    limits = config.reasoning.response_limits.model_copy(update={"rationale_max_chars": 3})
    data = _answer(rationale="four")
    with pytest.raises(ValidationError, match="rationale_max_chars"):
        CandidateResponse.model_validate(data, context=limits_context(limits))
    assert CandidateResponse.model_validate(
        data, context=limits_context(config.reasoning.response_limits)).rationale == "four"
