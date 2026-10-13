"""Provider factory. Mock is the default; the real API needs an explicit key.

``build_provider`` returns the deterministic mock unless BOTH hold: dry-run
is off and ``ANTHROPIC_API_KEY`` is set in the environment. With no key the
process makes zero network calls.
"""

from __future__ import annotations

from typing import Protocol

from codegen.config import Config
from codegen.reasoning.schema import CandidateResponse, ContextPack


class ProviderError(RuntimeError):
    """A provider exhausted its attempts without a valid response."""


class Provider(Protocol):
    """What the reasoning engine needs from any provider."""

    name: str

    def complete(self, pack: ContextPack) -> CandidateResponse: ...


def build_provider(config: Config, dry_run: bool) -> Provider:
    from codegen.reasoning.providers.mock import MockProvider

    if dry_run:
        from codegen.reasoning.mode import dry_run_reason

        return MockProvider(reason=dry_run_reason(config))

    # ONE decision for the transport (codegen.reasoning.transport): the mock
    # lock, the provider switch (codegen.reasoning.mode — mock by default),
    # the configured provider. LIVE that cannot run RAISES (one line naming
    # the unset setting) — never a quiet degrade to the mock (2026-10-13).
    from codegen.reasoning.mode import ProviderConfigError, check_live_config
    from codegen.reasoning.transport import resolve_transport

    transport = resolve_transport(config)
    if transport.kind == "mock":
        raise ProviderConfigError(transport.reason)
    if transport.kind == "databricks_fmapi":
        if not transport.config_resolves or transport.endpoint is None:
            check_live_config(config)                       # raises the named line
            raise ProviderConfigError(transport.reason)
        from codegen.reasoning.providers.databricks_provider import (
            DatabricksFmapiProvider,
        )

        # An empty serving_endpoint raises the provider's named error here.
        return DatabricksFmapiProvider(config)
    if transport.kind == "anthropic":
        from codegen.reasoning.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(config)
    return MockProvider(reason=mock_reason(transport))


def mock_reason(transport) -> str:
    """Why the resolved transport means a mock: the lock env var by name, or
    the unreachable transport's own reason."""
    if transport.kind == "mock_locked":
        return transport.detected_by    # CODEGEN_FORCE_MOCK_PROVIDER | provider=mock (<source>)
    return f"endpoint unreachable — {transport.reason or transport.label}"
