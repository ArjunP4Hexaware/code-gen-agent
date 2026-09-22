"""Layer-2 transport detection: WHICH model transport a run will use, and why.

Program policy: Anthropic is the sole model vendor; inside a Databricks
workspace the intended transport is the **Databricks Foundation Model
serving endpoint** (``databricks.serving_endpoint``, a Claude Opus 5
endpoint) — a transport, not a vendor change. This module is the ONE place
that decides:

* ``mock_locked``   — ``CODEGEN_FORCE_MOCK_PROVIDER`` is set: the mock answers.
* ``databricks_fmapi`` — configured, OR the process runs inside Databricks
  (an Apps runtime injects ``DATABRICKS_APP_PORT`` / ``DATABRICKS_HOST``; a
  cluster sets ``DATABRICKS_RUNTIME_VERSION``). Inside Databricks the
  endpoint is REQUIRED: a config that still says ``anthropic`` is
  overridden and the override is reported, never silent.
* ``anthropic``     — local, configured ``anthropic``, key present.
* ``mock``          — the safe degrade when the chosen transport cannot
  resolve; ``reason`` names the remedy.

Both provider builders (Layer 2 reasoning, layout recognizer) and the UI's
``/api/demo/live-available`` read this, so the code path and what the
screen says can never disagree. ``label`` is what a run WOULD use, in the
same words as the per-run record (``codegen.reasoning.usage``), minus the
call count — what a run actually did is that record, not this.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Literal

from codegen.config import Config
from codegen.reasoning.usage import model_display_name

Runtime = Literal["databricks_app", "databricks", "local"]
Kind = Literal["mock_locked", "databricks_fmapi", "anthropic", "mock"]

# Env markers, in detection order. Values are never read or reported.
_APP_MARKERS = ("DATABRICKS_APP_PORT", "DATABRICKS_APP_NAME")
_WORKSPACE_MARKERS = ("DATABRICKS_HOST", "DATABRICKS_RUNTIME_VERSION")


@dataclass(frozen=True)
class Layer2Transport:
    kind: Kind
    configured: str
    runtime: Runtime
    detected_by: str
    endpoint: str | None
    model: str
    available: bool
    reason: str
    label: str
    # True when the runtime forced FMAPI over a config that said otherwise.
    overridden: bool = False
    # False when the Databricks workspace config itself does not resolve (the
    # builders then degrade to mock); True with an empty endpoint means the
    # FMAPI provider raises its named "serving_endpoint" error instead.
    config_resolves: bool = True

    @property
    def provider_name(self) -> str:
        """The name the UI and the run-live guard show."""
        return "mock (locked)" if self.kind == "mock_locked" else self.kind

    def as_dict(self) -> dict:
        data = asdict(self)
        data["provider_name"] = self.provider_name
        return data


def detect_runtime(env=None) -> tuple[Runtime, str]:
    """(runtime, the env marker that decided it). Local when none is set."""
    env = os.environ if env is None else env
    for marker in _APP_MARKERS:
        if env.get(marker):
            return "databricks_app", marker
    for marker in _WORKSPACE_MARKERS:
        if env.get(marker):
            return "databricks", marker
    return "local", "no Databricks env marker"


def _fmapi(config: Config, configured: str, runtime: Runtime, detected_by: str,
           overridden: bool) -> Layer2Transport:
    from codegen.databricks import DatabricksConfigError, config_for

    model = config.reasoning.model
    endpoint: str | None = None
    problems: list[str] = []
    config_resolves = True
    try:
        # The endpoint needs no document volume (those ship blank).
        endpoint = config_for(config.databricks, require=()).serving_endpoint or None
        if endpoint is None:
            problems.append(
                "inside Databricks the Layer-2 transport is the Foundation Model serving "
                "endpoint, but databricks.serving_endpoint is not configured"
                if runtime != "local" else "databricks.serving_endpoint is not configured")
    except DatabricksConfigError as exc:
        config_resolves = False
        problems.append(f"Databricks workspace config does not resolve: {exc}")
    if overridden:
        problems.append(f"config reasoning.provider is {configured!r}; inside Databricks the "
                        "Foundation Model endpoint is used instead")
    label = (f"{model_display_name(model)} ({endpoint})" if endpoint
             else f"{model_display_name(model)} (serving endpoint unconfigured)")
    return Layer2Transport(kind="databricks_fmapi", configured=configured, runtime=runtime,
                           detected_by=detected_by, endpoint=endpoint, model=model,
                           available=endpoint is not None, reason="; ".join(problems),
                           label=label, overridden=overridden, config_resolves=config_resolves)


def resolve_transport(config: Config, env=None) -> Layer2Transport:
    env = os.environ if env is None else env
    configured = config.reasoning.provider
    runtime, marker = detect_runtime(env)
    model = config.reasoning.model
    if env.get("CODEGEN_FORCE_MOCK_PROVIDER"):
        return Layer2Transport(kind="mock_locked", configured=configured, runtime=runtime,
                               detected_by="CODEGEN_FORCE_MOCK_PROVIDER", endpoint=None,
                               model=model, available=True, reason="",
                               label="Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)")
    if runtime != "local":
        # Inside Databricks the endpoint is the transport, whatever the yaml says.
        return _fmapi(config, configured, runtime, marker,
                      overridden=configured != "databricks_fmapi")
    if configured == "databricks_fmapi":
        return _fmapi(config, configured, runtime, "config reasoning.provider", overridden=False)
    if not env.get("ANTHROPIC_API_KEY"):
        return Layer2Transport(kind="mock", configured=configured, runtime=runtime,
                               detected_by="config reasoning.provider", endpoint=None,
                               model=model, available=False,
                               reason="no ANTHROPIC_API_KEY in the backend env",
                               label="Mock provider (reason: endpoint unreachable — no "
                                     "ANTHROPIC_API_KEY in the backend env)")
    return Layer2Transport(kind="anthropic", configured=configured, runtime=runtime,
                           detected_by="config reasoning.provider", endpoint=None, model=model,
                           available=True, reason="",
                           label=f"{model_display_name(model)} (Anthropic API, {model})")


__all__ = ["Layer2Transport", "detect_runtime", "resolve_transport"]
