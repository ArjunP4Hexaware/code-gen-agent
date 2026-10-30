"""Layer 2: grounding rejects fabrications; engine records failures loudly."""

from __future__ import annotations

import pytest

from codegen.reasoning.context import build_context_pack
from codegen.reasoning.engine import run_reasoning
from codegen.reasoning.grounding import grounding_failures
from codegen.reasoning.providers import build_provider
from codegen.reasoning.providers.mock import MockProvider
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.rules.compiler import compile_rules

MIN_WORDS = 3     # config.yaml reasoning.min_citation_words (pinned by a test below)


def _pack_with_excerpt(excerpt: str) -> ContextPack:
    """post159 (P1-6): a citation must quote the candidate's OWN rule, so the
    canonicalization cases put their text there."""
    return ContextPack(
        feed_id="feed",
        rule_text=excerpt,
        contract_excerpts=[excerpt],
        available_source_columns=[],
        available_stage_columns=[],
        audit_columns=[],
    )


def _grounding(pack, response):
    return grounding_failures(pack, response, min_citation_words=MIN_WORDS)


def _response_citing(citation: str) -> CandidateResponse:
    return CandidateResponse(
        classification="mappable",
        code_candidate=None,
        rationale="grounding-normalization test",
        citations=[citation],
    )


def _unmapped(spec):
    return [o for o in compile_rules(spec) if o.classification == "unmapped"]


def test_mock_candidates_are_grounded(specs_by_id, config):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    candidates = run_reasoning(spec, compile_rules(spec), MockProvider(),
                               reasoning=config.reasoning)
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
    failures = _grounding(pack, response)
    assert len(failures) == 2           # post159: and no citation from its own rule
    assert "not verbatim" in failures[0]
    assert "own rule" in failures[1]


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
    assert _grounding(pack, response) == []


def test_json_escaped_citation_passes():
    # The pack reaches the model as indented JSON, so a faithful copy may
    # carry \" and \n escapes; those must not read as fabrication.
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is\nnot H')
    response = _response_citing('where \\"RECORD_TYPE\\" is\\nnot H')
    assert _grounding(pack, response) == []


def test_curly_quote_citation_passes():
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is not H')
    response = _response_citing("where “RECORD_TYPE” is not H")
    assert _grounding(pack, response) == []


def test_fabricated_citation_still_fails_after_normalization():
    pack = _pack_with_excerpt('Reject rows where "RECORD_TYPE" is not H')
    response = _response_citing("all rows must carry a checksum column")
    failures = _grounding(pack, response)
    assert len(failures) == 2
    assert "not verbatim" in failures[0]


def test_provider_failure_is_recorded_not_raised(specs_by_id, config):
    class ExplodingProvider:
        name = "exploding"

        def complete(self, pack):
            raise RuntimeError("boom")

    spec = specs_by_id["caqh_tpl_inbound_files"]
    candidates = run_reasoning(spec, compile_rules(spec), ExplodingProvider(),
                               reasoning=config.reasoning)
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


def test_force_mock_env_locks_every_transport(config, monkeypatch):
    # The App deployment's hard lock (app.yaml sets it): no provider config
    # can route live while CODEGEN_FORCE_MOCK_PROVIDER is set — checked
    # before any transport resolution, dry-run or not.
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    assert build_provider(config, dry_run=False).name == "mock"
    reasoning = config.reasoning.model_copy(update={"provider": "anthropic"})
    anthropic_config = config.model_copy(update={"reasoning": reasoning})
    assert build_provider(anthropic_config, dry_run=False).name == "mock"


# ---------------------------------------------------------------- post159 (P1-6)
# L2-3 / L2-4: grounding is anchored in the candidate's OWN rule, on word
# boundaries, with reasoning.min_citation_words; a column name grounds nothing.

OWN = "Reject the file when the trailer record count does not match the detail rows"
SIBLING = "Send a notification to the support mailbox when a file is rejected"


def _probe_pack() -> ContextPack:
    return ContextPack(feed_id="feed", rule_text=OWN,
                       contract_excerpts=[OWN, SIBLING, "Daily"],
                       available_source_columns=["Member Id"],
                       available_stage_columns=["MEMBER_ID"], audit_columns=["LOB"])


def _citing(*citations: str) -> CandidateResponse:
    return CandidateResponse(classification="mappable", code_candidate=None,
                             rationale="probe", citations=list(citations))


def test_min_citation_words_is_a_config_knob(config):
    assert config.reasoning.min_citation_words == MIN_WORDS



@pytest.mark.parametrize("name, citations", [
    ("one_char", ["R"]),
    ("stopword", ["the"]),
    ("column_name_only", ["MEMBER_ID"]),
    ("column_name_case", ["member id"]),
    ("other_rule_in_same_feed", [SIBLING]),
    ("mid_word", ["eject the file when"]),
    ("two_words", ["the trailer"]),
])
def test_grounding_probe_cases_are_rejected(name, citations):
    failures = _grounding(_probe_pack(), _citing(*citations))
    assert failures, name
    assert any("own rule" in f for f in failures), name


def test_a_column_name_fails_even_beside_a_good_citation():
    failures = _grounding(_probe_pack(), _citing("the trailer record count", "LOB"))
    assert failures == ["citation 2 of 2 is only a column name, not contract text"]


def test_own_rule_citation_grounds_and_siblings_count_as_extras():
    assert _grounding(_probe_pack(), _citing("the trailer record count")) == []
    assert _grounding(_probe_pack(), _citing(OWN, SIBLING, "Daily")) == []
    assert _grounding(_probe_pack(), _citing("the trailer record count", "a file is")) == []


def test_a_rule_shorter_than_the_minimum_grounds_on_its_whole_text():
    pack = _pack_with_excerpt("Mandatory field")
    assert _grounding(pack, _citing("Mandatory field")) == []
    assert _grounding(pack, _citing("Mandatory"))


def test_failure_notes_never_quote_the_model_s_citation():
    failures = _grounding(_probe_pack(), _citing("invented requirement about checksums"))
    assert failures and not any("checksums" in f for f in failures)
