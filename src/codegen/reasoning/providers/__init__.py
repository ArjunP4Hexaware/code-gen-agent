"""Provider factory. Mock is the default; the real API needs an explicit key.

``build_provider`` returns the deterministic mock unless BOTH hold: dry-run
is off and ``ANTHROPIC_API_KEY`` is set in the environment. With no key the
process makes zero network calls.
"""

from __future__ import annotations

import os
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

    # databricks_fmapi: the same Claude model over Databricks FMAPI — a
    # transport, not a vendor change. Selected only when explicitly
    # configured AND the workspace config resolves; otherwise the safe
    # degradation is the same as a missing Anthropic key: mock.
    if config.reasoning.provider == "databricks_fmapi":
        from codegen.databricks import DatabricksConfigError, config_for

        try:
            config_for(config.databricks)
        except DatabricksConfigError:
            return MockProvider()
        from codegen.reasoning.providers.databricks_provider import (
            DatabricksFmapiProvider,
        )

        return DatabricksFmapiProvider(config)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return MockProvider()
    from codegen.reasoning.providers.anthropic_provider import AnthropicProvider

    return AnthropicProvider(config)
