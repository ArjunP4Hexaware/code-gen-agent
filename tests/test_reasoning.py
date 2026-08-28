"""Layer 2: grounding rejects fabrications; engine records failures loudly."""

from __future__ import annotations

from codegen.reasoning.context import build_context_pack
from codegen.reasoning.engine import run_reasoning
from codegen.reasoning.grounding import grounding_failures
from codegen.reasoning.providers import build_provider
from codegen.reasoning.providers.mock import MockProvider
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.rules.compiler import compile_rules


def _pack_with_excerpt(excerpt: str) -> ContextPack:
    return ContextPack(
        feed_id="feed",
        rule_text="the rule",
        contract_excerpts=[excerpt],
        available_source_columns=[],
        available_stage_columns=[],
        audit_columns=[],
    )


def _response_citing(citation: str) -> CandidateResponse:
    return CandidateResponse(
        classification="mappable",
        code_candidate=None,
        rationale="grounding-normalization test",
        citations=[citation],
    )


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


def test_json_escaped_citation_passes():
    # The pack reaches the model as indented JSON, so a faithful copy may
    # carry \" and \n escapes; those must not read as fabrication.
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is\nnot H')
    response = _response_citing('where \\"RECORD_TYPE\\" is\\nnot H')
    assert grounding_failures(pack, response) == []


def test_curly_quote_citation_passes():
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is not H')
    response = _response_citing("where “RECORD_TYPE” is not H")
    assert grounding_failures(pack, response) == []


def test_fabricated_citation_still_fails_after_normalization():
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is not H')
    response = _response_citing("all rows must carry a checksum column")
    failures = grounding_failures(pack, response)
    assert len(failures) == 1
    assert "not verbatim" in failures[0]


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
    # The anthropic transport is key-gated; the tracked config now selects
    # databricks_fmapi, so pin the provider to test the keyless default.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reasoning = config.reasoning.model_copy(update={"provider": "anthropic"})
    anthropic_config = config.model_copy(update={"reasoning": reasoning})
    assert build_provider(anthropic_config, dry_run=False).name == "mock"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    assert build_provider(anthropic_config, dry_run=True).name == "mock"
    # Dry-run forces mock across every transport, the tracked one included.
    assert build_provider(config, dry_run=True).name == "mock"
