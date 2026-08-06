"""AnthropicProvider against a stubbed SDK: parsing, retry, loud exhaustion.

The real API is never called in tests; a fake ``anthropic`` module is
injected so the lazy import inside the provider picks it up.
"""

from __future__ import annotations

import sys
import types

import pytest

from codegen.reasoning.providers import ProviderError
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


class _FakeMessages:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        text = self._responses.pop(0)
        block = types.SimpleNamespace(type="text", text=text)
        return types.SimpleNamespace(content=[block])


def _install_fake_anthropic(monkeypatch, responses: list[str]) -> _FakeMessages:
    messages = _FakeMessages(responses)
    client = types.SimpleNamespace(messages=messages)
    fake = types.ModuleType("anthropic")
    fake.Anthropic = lambda: client
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    return messages


def _provider(config):
    from codegen.reasoning.providers.anthropic_provider import AnthropicProvider

    return AnthropicProvider(config)


def test_valid_json_first_try(config, monkeypatch):
    messages = _install_fake_anthropic(monkeypatch, [VALID_JSON])
    response = _provider(config).complete(_pack())
    assert messages.calls == 1
    assert response.classification == "mappable"
    assert response.citations == ["the rule text"]


def test_fenced_json_is_unwrapped(config, monkeypatch):
    fenced = f"```json\n{VALID_JSON}\n```"
    _install_fake_anthropic(monkeypatch, [fenced])
    response = _provider(config).complete(_pack())
    assert response.rationale == "because"


def test_invalid_then_valid_retries_once(config, monkeypatch):
    messages = _install_fake_anthropic(monkeypatch, ["not json at all", VALID_JSON])
    response = _provider(config).complete(_pack())
    assert messages.calls == 2
    assert response.classification == "mappable"


def test_exhausted_attempts_raise_provider_error(config, monkeypatch):
    bad = ['{"classification": "nonsense"}'] * config.reasoning.max_attempts
    messages = _install_fake_anthropic(monkeypatch, bad)
    with pytest.raises(ProviderError, match="no schema-valid response"):
        _provider(config).complete(_pack())
    assert messages.calls == config.reasoning.max_attempts
