"""The ONE provider switch: ``mock`` | ``live`` (2026-10-13).

A model is called only when a person or a deployment SAYS so. Live is never
inferred from a configured endpoint, a Databricks login or the Databricks
runtime's env markers (``DATABRICKS_HOST`` / the App's port) — a D1 run that
silently answered from the mock read like a real run in its report.

Resolution, first that answers wins:

  1. ``--provider mock|live``          (CLI flag)
  2. ``CODEGEN_PROVIDER=mock|live``     (env — the ACFC App manifest, the
                                         harness jobs, ``acfc_run.py`` set live)
  3. ``reasoning.mode: mock|live``      (config; the shipped value is mock)
  4. mock                               (the default, everywhere)

It governs BOTH model users: the layout recognizer and Layer 2. ``--dry-run``
and the two lock env vars (``CODEGEN_FORCE_MOCK_PROVIDER`` /
``CODEGEN_FORCE_MOCK_LAYOUT``) still ask for the mock explicitly, and every
mock says why. Live with its endpoint / key unset fails at startup with one
line naming the setting — never a quiet degrade to the mock.

The test suite blocks every live call site (``guard_live_call``) unless
``CODEGEN_ALLOW_LIVE_TESTS=1`` opts in: ``tests/conftest.py`` sets
``CODEGEN_BLOCK_LIVE_MODEL`` at import.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Mode = Literal["mock", "live"]
PROVIDER_ENV = "CODEGEN_PROVIDER"
BLOCK_LIVE_ENV = "CODEGEN_BLOCK_LIVE_MODEL"
ALLOW_LIVE_TESTS_ENV = "CODEGEN_ALLOW_LIVE_TESTS"
_MODES = ("mock", "live")

# --dry-run asks for the mock; under provider=live that is said LOUDLY — the
# first line of the run and the report (2026-10-13): a D1 report must never
# look live when it is not.
DRY_RUN_OVER_LIVE = "provider=live overridden by --dry-run → mock"


def dry_run_reason(config=None, env=None) -> str:
    """Why a dry run answers from the mock: plain ``dry-run``, or — when the
    switch said live — the override, in words no report can misread."""
    return DRY_RUN_OVER_LIVE if provider_mode(config, env).live else "dry-run"


# A --provider flag the CLI parsed (set once per process by codegen.cli.main).
_flag: Mode | None = None


class ProviderConfigError(RuntimeError):
    """Live was asked for and cannot run: one line naming the unset setting."""


class LiveModelBlocked(BaseException):  # noqa: N818 — BaseException: no ``except
    """A live model call inside the test suite. A BaseException on purpose:
    Layer 2 turns provider errors into flagged candidates (``except
    Exception``), and an accidental live path must fail the test, not hide
    in a candidate card."""


@dataclass(frozen=True)
class ProviderMode:
    mode: Mode
    source: str     # "--provider" | "CODEGEN_PROVIDER" | "config reasoning.mode" | "default"

    @property
    def live(self) -> bool:
        return self.mode == "live"

    def text(self) -> str:
        """``provider=mock (default)`` — the words every mock reason and the
        version line carry, so a report can never be misread."""
        return f"provider={self.mode} ({self.source})"


def set_flag(value: str | None) -> None:
    global _flag
    if value is not None and value not in _MODES:
        raise ValueError(f"--provider {value!r}: expected mock | live")
    _flag = value  # type: ignore[assignment]


def provider_mode(config=None, env=None) -> ProviderMode:
    env = os.environ if env is None else env
    if _flag is not None:
        return ProviderMode(_flag, "--provider")
    raw = (env.get(PROVIDER_ENV) or "").strip().lower()
    if raw:
        if raw not in _MODES:
            raise ProviderConfigError(f"{PROVIDER_ENV}={raw!r}: expected mock | live")
        return ProviderMode(raw, PROVIDER_ENV)  # type: ignore[arg-type]
    configured = getattr(getattr(config, "reasoning", None), "mode", None)
    if configured == "live":
        return ProviderMode("live", "config reasoning.mode")
    return ProviderMode("mock", "default" if configured in (None, "mock") else "config")


def mode_from_raw(raw_config: dict, env=None) -> ProviderMode:
    """The same decision over the raw YAML (the CLI's first line runs before
    load_config validates anything)."""
    reasoning = raw_config.get("reasoning") if isinstance(raw_config, dict) else None
    mode = reasoning.get("mode") if isinstance(reasoning, dict) else None

    class _Raw:
        pass

    holder = _Raw()
    holder.reasoning = _Raw()  # type: ignore[attr-defined]
    holder.reasoning.mode = mode  # type: ignore[attr-defined]
    try:
        return provider_mode(holder, env)
    except ProviderConfigError:
        return ProviderMode("mock", f"{PROVIDER_ENV} invalid")


def check_live_config(config, env=None) -> None:
    """Live requested: the transport the config names must be fully set, or
    one line says which setting is unset. Mock: nothing to check."""
    env = os.environ if env is None else env
    mode = provider_mode(config, env)
    if not mode.live:
        return
    provider = config.reasoning.provider
    where = mode.text()
    if provider == "databricks_fmapi":
        from codegen.databricks import DatabricksConfigError, config_for

        try:
            endpoint = config_for(config.databricks, env=env, require=()).serving_endpoint
        except DatabricksConfigError as exc:
            raise ProviderConfigError(
                f"{where} but the Databricks workspace config does not resolve: "
                f"{' '.join(str(exc).split())}") from exc
        if not endpoint:
            raise ProviderConfigError(
                f"{where} but databricks.serving_endpoint is unset (config "
                "databricks.serving_endpoint or env DATABRICKS_SERVING_ENDPOINT)")
        return
    if provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ProviderConfigError(f"{where} with reasoning.provider anthropic but "
                                      "ANTHROPIC_API_KEY is unset")
        return
    raise ProviderConfigError(f"{where} but reasoning.provider is {provider!r} "
                              "(expected databricks_fmapi | anthropic)")


_UNSET = object()


def guard_live_call(what: str, env=None, sdk_module=_UNSET) -> None:
    """Called at every point that would open a live model connection.
    ``sdk_module``: the client package about to connect — a stand-in a test
    put in ``sys.modules`` (no ``__file__``) opens no connection and passes;
    the real installed package is blocked."""
    env = os.environ if env is None else env
    if sdk_module is not _UNSET and getattr(sdk_module, "__file__", None) is None:
        return
    if env.get(BLOCK_LIVE_ENV) and not env.get(ALLOW_LIVE_TESTS_ENV):
        raise LiveModelBlocked(
            f"{what}: a live model call while {BLOCK_LIVE_ENV} is set (the test suite) — "
            f"set {ALLOW_LIVE_TESTS_ENV}=1 to opt in to live tests")


__all__ = ["ALLOW_LIVE_TESTS_ENV", "BLOCK_LIVE_ENV", "LiveModelBlocked", "PROVIDER_ENV",
           "ProviderConfigError", "ProviderMode", "check_live_config", "guard_live_call",
           "mode_from_raw", "provider_mode", "set_flag"]
