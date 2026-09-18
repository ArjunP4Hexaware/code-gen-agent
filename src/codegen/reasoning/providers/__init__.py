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
        return MockProvider()

    # ONE decision for the transport (codegen.reasoning.transport): the mock
    # lock, the Databricks runtime (Foundation Model endpoint required —
    # overrides a yaml that still says anthropic), the configured provider,
    # and the safe degrade to mock when the chosen transport cannot resolve.
    from codegen.reasoning.transport import resolve_transport

    transport = resolve_transport(config)
    if transport.kind == "databricks_fmapi":
        if not transport.config_resolves:
            return MockProvider()
        from codegen.reasoning.providers.databricks_provider import (
            DatabricksFmapiProvider,
        )

        # An empty serving_endpoint raises the provider's named error here.
        return DatabricksFmapiProvider(config)
    if transport.kind == "anthropic":
        from codegen.reasoning.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(config)
    return MockProvider()
