"""codegen.reasoning.transport — ONE decision for the Layer-2 model transport.

2026-10-13: a model is called only when the provider switch SAYS live
(``--provider`` > ``CODEGEN_PROVIDER`` > ``reasoning.mode``; default mock).
A Databricks runtime (``DATABRICKS_HOST`` / the App's port) is detected and
reported, never inferred into live; under live the CONFIGURED provider
decides; live that cannot run raises one named line, never a quiet mock; the
mock lock still beats everything. Both provider builders follow the decision.
"""

from __future__ import annotations

import pytest

from codegen.layout.model import build_layout_provider
from codegen.reasoning.mode import ProviderConfigError
from codegen.reasoning.providers import build_provider
from codegen.reasoning.transport import detect_runtime, resolve_transport

LIVE = {"CODEGEN_PROVIDER": "live"}


def _with_provider(config, provider: str, endpoint: str | None = None):
    reasoning = config.reasoning.model_copy(update={"provider": provider})
    databricks = config.databricks if endpoint is None else config.databricks.model_copy(
        update={"serving_endpoint": endpoint})
    return config.model_copy(update={"reasoning": reasoning, "databricks": databricks})


def test_runtime_detection_order():
    assert detect_runtime({}) == ("local", "no Databricks env marker")
    assert detect_runtime({"DATABRICKS_HOST": "x"}) == ("databricks", "DATABRICKS_HOST")
    assert detect_runtime({"DATABRICKS_RUNTIME_VERSION": "15.4"}) == (
        "databricks", "DATABRICKS_RUNTIME_VERSION")
    assert detect_runtime({"DATABRICKS_APP_PORT": "8080", "DATABRICKS_HOST": "x"}) == (
        "databricks_app", "DATABRICKS_APP_PORT")


@pytest.mark.parametrize("env", [{}, {"DATABRICKS_HOST": "https://x"},
                                 {"DATABRICKS_APP_PORT": "8080", "ANTHROPIC_API_KEY": "k"}])
def test_mock_is_the_default_whatever_the_runtime_says(config, env):
    """No switch = mock: an endpoint in the config, a Databricks login or the
    App's own env markers never make a run live."""
    t = resolve_transport(_with_provider(config, "databricks_fmapi"), env=env)
    assert (t.kind, t.available) == ("mock_locked", True)
    assert t.label == "Mock provider (reason: provider=mock (default))"
    assert t.detected_by == "provider=mock (default)"


def test_the_default_builders_answer_from_the_mock(config, monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://x")
    provider = build_provider(config, dry_run=False)
    assert provider.name == "mock" and provider.mock_reason == "provider=mock (default)"
    layout = build_layout_provider(config, dry_run=False)
    assert layout.name == "mock" and layout.mock_reason == "provider=mock (default)"


def test_live_anthropic_without_key_raises_instead_of_mocking(config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")
    cfg = _with_provider(config, "anthropic")
    t = resolve_transport(cfg, env=LIVE)
    assert (t.kind, t.available, t.runtime) == ("mock", False, "local")
    assert "ANTHROPIC_API_KEY is unset" in t.reason and "provider=live" in t.reason
    with pytest.raises(ProviderConfigError, match="ANTHROPIC_API_KEY is unset"):
        build_provider(cfg, dry_run=False)


def test_live_anthropic_with_key(config):
    t = resolve_transport(_with_provider(config, "anthropic"),
                          env={**LIVE, "ANTHROPIC_API_KEY": "k"})
    assert (t.kind, t.available, t.provider_name) == ("anthropic", True, "anthropic")
    assert t.label.startswith("Claude ") and "Anthropic API" in t.label
    assert config.reasoning.model in t.label
    assert t.reason == ""


def test_live_fmapi_configured(config):
    t = resolve_transport(_with_provider(config, "databricks_fmapi"), env=LIVE)
    assert (t.kind, t.available, t.overridden) == ("databricks_fmapi", True, False)
    assert t.endpoint == config.databricks.serving_endpoint
    assert t.detected_by == "provider=live (CODEGEN_PROVIDER)" and t.reason == ""


def test_live_takes_the_configured_provider_even_inside_databricks(config, monkeypatch):
    """The runtime no longer overrides the yaml: live + anthropic stays anthropic."""
    env = {**LIVE, "DATABRICKS_APP_PORT": "8080", "ANTHROPIC_API_KEY": "k"}
    t = resolve_transport(_with_provider(config, "anthropic"), env=env)
    assert (t.kind, t.runtime, t.overridden) == ("anthropic", "databricks_app", False)


def test_live_without_endpoint_is_a_named_startup_error(config, monkeypatch):
    from codegen.reasoning.mode import check_live_config

    cfg = _with_provider(config, "databricks_fmapi", endpoint="")
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")
    monkeypatch.delenv("DATABRICKS_SERVING_ENDPOINT", raising=False)
    t = resolve_transport(cfg, env=LIVE)
    assert (t.kind, t.available, t.endpoint) == ("databricks_fmapi", False, None)
    with pytest.raises(ProviderConfigError) as excinfo:
        check_live_config(cfg)
    message = str(excinfo.value)
    assert "\n" not in message and "databricks.serving_endpoint is unset" in message
    assert message.startswith("provider=live (CODEGEN_PROVIDER)")
    # Both builders raise the same line rather than degrading to the mock.
    with pytest.raises(ProviderConfigError, match="serving_endpoint is unset"):
        build_provider(cfg, dry_run=False)
    with pytest.raises(ProviderConfigError, match="serving_endpoint is unset"):
        build_layout_provider(cfg, dry_run=False)


def test_mock_lock_beats_everything(config):
    env = {**LIVE, "CODEGEN_FORCE_MOCK_PROVIDER": "1", "DATABRICKS_APP_PORT": "1",
           "ANTHROPIC_API_KEY": "k"}
    t = resolve_transport(_with_provider(config, "databricks_fmapi"), env=env)
    assert (t.kind, t.available, t.provider_name) == ("mock_locked", True, "mock (locked)")
    assert t.label == "Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)"
    assert t.runtime == "databricks_app" and t.detected_by == "CODEGEN_FORCE_MOCK_PROVIDER"


def test_as_dict_carries_no_secrets(config):
    d = resolve_transport(_with_provider(config, "anthropic"),
                          env={**LIVE, "ANTHROPIC_API_KEY": "sekrit"}).as_dict()
    assert set(d) >= {"kind", "runtime", "detected_by", "endpoint", "model", "label",
                      "provider_name"}
    assert "sekrit" not in repr(d)
