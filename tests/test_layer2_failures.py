"""Layer-2 failures (2026-10-14, D1 post43: pair_12 "5 calls, 5 failed,
fallback used"; pair_2 one failure per feed before the retry answered).

Both live providers ask through ``codegen.reasoning.providers.ask``: the post43
tolerant JSON parser, one "JSON only, no fences" retry, ``max_tokens`` raised
for the retry when a response ends inside its JSON object. Every failed
attempt is logged — reason + the first 500 characters of the raw response,
D1-only (stderr ``RAW (D1 only)`` + ``<state>/rejections/layer2_<feed>.raw.json``)
— and a run where every Layer-2 call failed says so in the report header.
The serving endpoint is never called: ``codegen.databricks.chat`` is stubbed.
"""

from __future__ import annotations

import io
import json

import pytest

from codegen.reasoning.engine import run_reasoning
from codegen.reasoning.providers import build_provider
from codegen.reasoning.raw_log import failure_lines, log_layer2_failures
from codegen.reasoning.schema import ContextPack
from codegen.reasoning.usage import StageUsage, layer2_usage
from codegen.report.generation_report import all_failed_line

VALID = ('{"classification": "mappable", "code_candidate": "# sketch", '
         '"rationale": "because", "citations": ["the rule text"]}')


@pytest.fixture(autouse=True)
def _live(monkeypatch):
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")


def _pack() -> ContextPack:
    return ContextPack(feed_id="feed", rule_text="the rule text",
                       contract_excerpts=["the rule text"], available_source_columns=["a"],
                       available_stage_columns=["A"], audit_columns=["LOB"])


def _provider(config, monkeypatch, responses):
    calls: list[dict] = []

    def fake_chat(cfg, messages, endpoint=None, max_tokens=1024):
        calls.append({"prompt": messages[1]["content"], "max_tokens": max_tokens})
        answer = responses.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    import codegen.databricks as databricks_module

    monkeypatch.setattr(databricks_module, "chat", fake_chat)
    reasoning = config.reasoning.model_copy(update={"provider": "databricks_fmapi"})
    provider = build_provider(config.model_copy(update={"reasoning": reasoning}),
                              dry_run=False)
    assert provider.name == "databricks_fmapi"
    return provider, calls


def test_fenced_and_preambled_responses_parse_first_time(config, monkeypatch):
    provider, calls = _provider(config, monkeypatch, [
        f"```json\n{VALID}\n```", f"Here is the candidate {{as asked}}:\n{VALID}\nDone."])
    assert provider.complete(_pack()).classification == "mappable"
    assert provider.complete(_pack()).rationale == "because"
    assert len(calls) == 2 and provider.failures == []


def test_a_truncated_response_raises_max_tokens_for_the_retry(config, monkeypatch):
    provider, calls = _provider(config, monkeypatch, [VALID[:40], VALID])
    assert provider.complete(_pack()).classification == "mappable"
    assert [c["max_tokens"] for c in calls] == [config.reasoning.max_tokens,
                                                config.reasoning.truncation_max_tokens]
    assert "Respond with JSON only, no fences" in calls[1]["prompt"]
    [failure] = provider.failures
    assert failure.recovered and failure.raised_to == config.reasoning.truncation_max_tokens
    assert "ends inside the JSON object" in failure.reason
    lines = failure_lines("feed_a", provider.failures)
    assert lines[0].startswith("LAYER2 FAILED  feed_a request 1 attempt 1/2 (answered on retry)")
    assert lines[1].startswith("RAW (D1 only)  layer2 feed_a request 1 attempt 1, first 500")
    assert lines[2].startswith("NOTE           layer2 feed_a request 1: max_tokens "
                               f"{config.reasoning.max_tokens} -> "
                               f"{config.reasoning.truncation_max_tokens}")


def test_every_failure_is_logged_with_its_reason_and_raw_text(config, monkeypatch,
                                                              tmp_path):
    long_prose = "I cannot answer that in JSON. " * 40
    responses = [long_prose, '{"classification": "nonsense"}',      # rule 1: both fail
                 "nope", VALID,                                    # rule 2: retry answers
                 RuntimeError("endpoint 503")]                     # rule 3: transport
    provider, _calls = _provider(config, monkeypatch, responses)
    from codegen.rules.compiler import RuleOutcome

    outcomes = [RuleOutcome(feed_id="feed_a", rule_text=f"rule {n}",
                            classification="unmapped", feature=None, grounding="",
                            notes=None)
                for n in (1, 2, 3)]
    spec = type("Spec", (), {"feed_id": "feed_a"})()
    import codegen.reasoning.engine as engine

    monkeypatch.setattr(engine, "build_context_pack", lambda _spec, _outcome: _pack())
    candidates = run_reasoning(spec, outcomes, provider)
    assert [c.response is None for c in candidates] == [True, False, True]
    assert [(f.request, f.attempt, f.recovered) for f in provider.failures] == [
        (1, 1, False), (1, 2, False), (2, 1, True), (3, 1, False)]
    reasons = [f.reason for f in provider.failures]
    assert reasons[0].startswith("no JSON object: no '{' in the response")
    assert reasons[1].startswith("schema validation failed") and "nonsense" not in reasons[1]
    assert reasons[3] == "transport: endpoint 503"
    assert len(provider.failures[0].raw) == 500

    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{tmp_path.as_posix()}")
    err = io.StringIO()
    path = log_layer2_failures(provider, "feed_a", config, tmp_path, stream=err)
    printed = err.getvalue().splitlines()
    assert sum(line.startswith("LAYER2 FAILED") for line in printed) == 4
    assert sum(line.startswith("RAW (D1 only)") for line in printed) == 3   # not transport
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "rejections" / "layer2_feed_a.raw.json"
    assert stored["chars"] == 500 and len(stored["failures"]) == 4

    usage = layer2_usage(provider, candidates)
    assert (usage.requests, usage.failed, usage.recovered) == (3, 2, 1)
    assert usage.label.endswith("5 call(s), 2 failed, 1 answered on retry")
    assert not usage.all_failed
    # nothing failed on a mock: no output, no file
    assert log_layer2_failures(build_provider(config, dry_run=True), "feed_a", config,
                               tmp_path, stream=err) is None


def test_every_call_failed_is_said_in_the_report_header(config, tmp_path):
    from codegen.report.generation_report import write_generation_report

    usage = StageUsage(stage="layer2", provider="databricks_fmapi",
                       endpoint="databricks-claude-opus-5-5", model="claude-opus-5-5",
                       calls=10, requests=5, failed=5)
    assert usage.all_failed
    assert "every model call failed (5 of 5 request(s), 10 call(s))" in all_failed_line(usage)
    spec = type("Spec", (), {"feed_id": "feed_a", "feed_slug": "feed_a",
                             "frd_contract_name": "f", "frd_contract_sha256": "0",
                             "sttm_contract_name": "s", "sttm_contract_sha256": "0",
                             "sttm_is_synthetic": False, "segmented_extraction": None})()
    gate = type("Gate", (), {"checks": [], "flags": [], "verdict": "PASS_WITH_FLAGS"})()
    report = write_generation_report(spec, [], [], [], gate, tmp_path, tmp_path,
                                     model_usage=[usage])
    head = report.read_text(encoding="utf-8").splitlines()[:3]
    assert head[2].startswith("> **WARNING** Layer 2 (rule reasoning): every model call "
                              "failed")
    # a partial failure, a mock and a no-call stage say nothing up there
    for quiet in (StageUsage(stage="layer2", provider="databricks_fmapi", calls=3,
                             requests=3, failed=2),
                  StageUsage(stage="layer2", provider="mock", requests=3),
                  StageUsage(stage="layer2", provider="databricks_fmapi")):
        assert not quiet.all_failed
