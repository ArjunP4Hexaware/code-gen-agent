"""Layer 2: grounding rejects fabrications; engine records failures loudly."""

from __future__ import annotations

from codegen.reasoning.context import build_context_pack
from codegen.reasoning.engine import run_reasoning
from codegen.reasoning.grounding import grounding_failures
from codegen.reasoning.providers import build_provider
from codegen.reasoning.providers.mock import MockProvider
from codegen.reasoning.schema import CandidateResponse
from codegen.rules.compiler import compile_rules


def _unmapped(spec):
    return [o for o in compile_rules(spec) if o.classification == "unmapped"]


def test_mock_candidates_are_grounded(specs_by_id):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    candidates = run_reasoning(spec, compile_rules(spec), MockProvider())
    assert len(candidates) == 2
    for candidate in candidates:
        assert candidate.provider == "mock"
        assert candidate.grounded
        assert candidate.response is not None
        assert not candidate.failure_notes


def test_fabricated_citation_is_rejected(specs_by_id):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    outcome = _unmapped(spec)[0]
    pack = build_context_pack(spec, outcome)
    response = CandidateResponse(
        classification="mappable",
        code_candidate="# sketch",
        rationale="made up",
        citations=["this text appears nowhere in the contract"],
    )
    failures = grounding_failures(pack, response)
    assert len(failures) == 1
    assert "not verbatim" in failures[0]


def test_verbatim_citation_passes(specs_by_id):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    outcome = _unmapped(spec)[0]
    pack = build_context_pack(spec, outcome)
    response = CandidateResponse(
        classification="mappable",
        code_candidate=None,
        rationale="cites the rule itself",
        citations=[outcome.rule_text],
    )
    assert grounding_failures(pack, response) == []


def test_provider_failure_is_recorded_not_raised(specs_by_id):
    class ExplodingProvider:
        name = "exploding"

        def complete(self, pack):
            raise RuntimeError("boom")

    spec = specs_by_id["caqh_tpl_inbound_files"]
    candidates = run_reasoning(spec, compile_rules(spec), ExplodingProvider())
    assert len(candidates) == 2
    for candidate in candidates:
        assert candidate.response is None
        assert not candidate.grounded
        assert "boom" in candidate.failure_notes[0]


def test_build_provider_defaults_to_mock(config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert build_provider(config, dry_run=False).name == "mock"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    assert build_provider(config, dry_run=True).name == "mock"
