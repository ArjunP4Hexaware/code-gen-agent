"""DatabricksFmapiProvider: selection rules, stubbed transport, retries.

The FMAPI endpoint is never called: ``codegen.databricks.chat`` is
monkeypatched (the provider's single transport touchpoint), the same
posture as test_anthropic_provider's fake ``anthropic`` module. One test
proves keyless import with zero environment.
"""

from __future__ import annotations

import pytest

from codegen.reasoning.providers import ProviderError, build_provider
from codegen.reasoning.schema import ContextPack

VALID_JSON = (
    '{"classification": "mappable", "code_candidate": "# sketch", '
    '"rationale": "because", "citations": ["the rule text"]}'
)


def _pack() -> ContextPack:
    return ContextPack(
        feed_id="feed",
        rule_text="the rule text",
        contract_excerpts=["the rule text"],
        available_source_columns=["a"],
        available_stage_columns=["A"],
        audit_columns=["LOB"],
    )


def _fmapi_config(config, **databricks_overrides):
    databricks = config.databricks.model_copy(update=databricks_overrides)
    reasoning = config.reasoning.model_copy(update={"provider": "databricks_fmapi"})
    return config.model_copy(update={"databricks": databricks,
                                     "reasoning": reasoning})


def test_module_imports_keyless(monkeypatch):
    for var in ("DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_CONFIG_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    import codegen.reasoning.providers.databricks_provider as module

    assert module.DatabricksFmapiProvider.name == "databricks_fmapi"


def test_dry_run_always_wins(config):
    provider = build_provider(_fmapi_config(config), dry_run=True)
    assert provider.name == "mock"


def test_selected_when_configured_and_not_dry_run(config):
    provider = build_provider(_fmapi_config(config), dry_run=False)
    assert provider.name == "databricks_fmapi"


def test_unresolvable_workspace_config_degrades_to_mock(config):
    broken = _fmapi_config(config, catalog="", schema_name="")
    assert build_provider(broken, dry_run=False).name == "mock"


def test_default_provider_stays_anthropic_shaped(config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert build_provider(config, dry_run=False).name == "mock"


def test_missing_serving_endpoint_is_a_named_error(config):
    from codegen.databricks import DatabricksConfigError

    with pytest.raises(DatabricksConfigError, match="serving_endpoint"):
        build_provider(_fmapi_config(config, serving_endpoint=""), dry_run=False)


def _stub_chat(monkeypatch, responses: list[str]) -> dict:

    calls = {"count": 0, "kwargs": []}

    def fake_chat(cfg, messages, endpoint=None, max_tokens=1024):
        calls["count"] += 1
        calls["kwargs"].append({"messages": messages, "endpoint": endpoint,
                                "max_tokens": max_tokens})
        return responses.pop(0)

    import codegen.databricks as databricks_module

    monkeypatch.setattr(databricks_module, "chat", fake_chat)
    return calls


def test_valid_response_first_try(config, monkeypatch):
    calls = _stub_chat(monkeypatch, [VALID_JSON])
    provider = build_provider(_fmapi_config(config), dry_run=False)
    response = provider.complete(_pack())
    assert response.classification == "mappable"
    assert calls["count"] == 1
    assert calls["kwargs"][0]["endpoint"] == "databricks-claude-opus-4-8"
    # System prompt travels as a chat message; no sampling params exist.
    assert calls["kwargs"][0]["messages"][0]["role"] == "system"


def test_invalid_then_valid_retries_with_error(config, monkeypatch):
    calls = _stub_chat(monkeypatch, ["not json at all", VALID_JSON])
    provider = build_provider(_fmapi_config(config), dry_run=False)
    assert provider.complete(_pack()).classification == "mappable"
    assert calls["count"] == 2
    retry_user = calls["kwargs"][1]["messages"][1]["content"]
    assert "failed schema validation" in retry_user


def test_exhausted_attempts_raise_provider_error(config, monkeypatch):
    _stub_chat(monkeypatch, ["nope", "still nope"])
    provider = build_provider(_fmapi_config(config), dry_run=False)
    with pytest.raises(ProviderError, match="no schema-valid response"):
        provider.complete(_pack())
