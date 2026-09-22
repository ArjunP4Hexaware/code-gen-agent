"""codegen.reasoning.transport — ONE decision for the Layer-2 model transport.

Inside a Databricks runtime the Foundation Model serving endpoint is the
transport whatever the yaml says (the override is reported); locally the
configured provider decides; the mock lock beats everything; an
unresolvable transport degrades to mock with the remedy in ``reason``.
Both provider builders follow the same decision.
"""

from __future__ import annotations

from codegen.layout.model import build_layout_provider
from codegen.reasoning.providers import build_provider
from codegen.reasoning.transport import detect_runtime, resolve_transport


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


def test_local_anthropic_without_key_is_mock_with_remedy(config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = _with_provider(config, "anthropic")
    t = resolve_transport(cfg, env={})
    assert (t.kind, t.available, t.runtime) == ("mock", False, "local")
    assert t.reason == "no ANTHROPIC_API_KEY in the backend env"
    assert build_provider(cfg, dry_run=False).name == "mock"


def test_local_anthropic_with_key(config):
    t = resolve_transport(_with_provider(config, "anthropic"), env={"ANTHROPIC_API_KEY": "k"})
    assert (t.kind, t.available, t.provider_name) == ("anthropic", True, "anthropic")
    assert t.label.startswith("Claude ") and "Anthropic API" in t.label
    assert config.reasoning.model in t.label
    assert t.reason == ""


def test_local_fmapi_configured(config):
    t = resolve_transport(_with_provider(config, "databricks_fmapi"), env={})
    assert (t.kind, t.available, t.overridden) == ("databricks_fmapi", True, False)
    assert t.endpoint == config.databricks.serving_endpoint
    assert t.detected_by == "config reasoning.provider" and t.reason == ""


def test_databricks_runtime_forces_fmapi_over_an_anthropic_yaml(config, monkeypatch):
    env = {"DATABRICKS_APP_PORT": "8080", "ANTHROPIC_API_KEY": "k"}
    cfg = _with_provider(config, "anthropic")
    t = resolve_transport(cfg, env=env)
    assert (t.kind, t.runtime, t.detected_by, t.available) == (
        "databricks_fmapi", "databricks_app", "DATABRICKS_APP_PORT", True)
    assert t.overridden and t.configured == "anthropic"
    assert "inside Databricks the Foundation Model endpoint is used instead" in t.reason
    # Both builders follow the decision (no network: the FMAPI providers only
    # resolve config at construction).
    monkeypatch.setenv("DATABRICKS_APP_PORT", "8080")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert build_provider(cfg, dry_run=False).name == "databricks_fmapi"
    assert build_layout_provider(cfg, dry_run=False).name == "databricks_fmapi"


def test_databricks_runtime_without_endpoint_is_unavailable_with_remedy(config, monkeypatch):
    cfg = _with_provider(config, "databricks_fmapi", endpoint="")
    t = resolve_transport(cfg, env={"DATABRICKS_HOST": "https://x"})
    assert (t.kind, t.available, t.endpoint) == ("databricks_fmapi", False, None)
    assert "databricks.serving_endpoint is not configured" in t.reason
    assert t.label.endswith("(serving endpoint unconfigured)") and t.config_resolves
    # The config resolves but names no endpoint: both builders raise the
    # provider's named error rather than silently degrading.
    import pytest

    from codegen.databricks import DatabricksConfigError

    monkeypatch.setenv("DATABRICKS_HOST", "https://x")
    with pytest.raises(DatabricksConfigError, match="serving_endpoint"):
        build_provider(cfg, dry_run=False)
    with pytest.raises(DatabricksConfigError, match="serving_endpoint"):
        build_layout_provider(cfg, dry_run=False)


def test_mock_lock_beats_everything(config):
    env = {"CODEGEN_FORCE_MOCK_PROVIDER": "1", "DATABRICKS_APP_PORT": "1",
           "ANTHROPIC_API_KEY": "k"}
    t = resolve_transport(_with_provider(config, "databricks_fmapi"), env=env)
    assert (t.kind, t.available, t.provider_name) == ("mock_locked", True, "mock (locked)")
    assert t.label == "Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)"
    assert t.runtime == "databricks_app" and t.detected_by == "CODEGEN_FORCE_MOCK_PROVIDER"


def test_as_dict_carries_no_secrets(config):
    d = resolve_transport(_with_provider(config, "anthropic"),
                          env={"ANTHROPIC_API_KEY": "sekrit"}).as_dict()
    assert set(d) >= {"kind", "runtime", "detected_by", "endpoint", "model", "label",
                      "provider_name"}
    assert "sekrit" not in repr(d)
