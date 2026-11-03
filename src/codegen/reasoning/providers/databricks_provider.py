"""Layer-2 provider over Databricks Foundation Model APIs — a TRANSPORT.

Anthropic remains the sole model vendor: ``databricks.serving_endpoint``
serves the same Claude model named by ``reasoning.model``
(``databricks-claude-opus-4-8`` ↔ ``claude-opus-4-8``); only the wire
changes. Selected by ``build_provider`` only when ``reasoning.provider:
databricks_fmapi`` AND the workspace config resolves AND dry-run is off —
Anthropic stays the default, mock always wins on dry-run.

Same discipline as the Anthropic provider: identical system prompt, the
shared ask loop (:mod:`codegen.reasoning.providers.ask` — the tolerant JSON
parser, one "JSON only, no fences" retry, ``max_tokens`` raised on a
truncated response, every failed attempt recorded) and NO sampling
parameters (the no-temperature rule holds across transports).
The SDK is only touched inside ``codegen.databricks.chat``; this module
imports keyless.
"""

from __future__ import annotations

from codegen.config import Config
from codegen.reasoning.providers.anthropic_provider import (
    _BATCH_SYSTEM_PROMPT,
    _SYSTEM_PROMPT,
    batch_prompt,
)
from codegen.reasoning.providers.ask import AttemptFailure, ask_batch, ask_candidate
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.reasoning.usage import add_tokens, timed


class DatabricksFmapiProvider:
    name = "databricks_fmapi"

    def __init__(self, config: Config) -> None:
        from codegen.databricks import config_for

        # The endpoint needs no document volume (those ship blank).
        self._cfg = config_for(config.databricks, require=())
        self._endpoint = self._cfg.serving_endpoint
        if not self._endpoint:
            from codegen.databricks import DatabricksConfigError

            raise DatabricksConfigError(
                "reasoning.provider is databricks_fmapi but "
                "databricks.serving_endpoint is not configured"
            )
        self._max_tokens = config.reasoning.max_tokens
        self._max_attempts = config.reasoning.max_attempts
        self._truncation_max_tokens = config.reasoning.truncation_max_tokens
        self._limits = config.reasoning.response_limits
        # What the run record reads (codegen.reasoning.usage).
        self.endpoint = self._endpoint
        self.model = config.reasoning.model
        self.calls = 0
        self.seconds = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.requests = 0
        self.failures: list[AttemptFailure] = []

    def _sender(self, system: str):
        from codegen.databricks import chat

        def send(prompt: str, max_tokens: int) -> str:
            self.calls += 1
            counts: dict = {}
            try:
                return chat(
                    self._cfg,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    endpoint=self._endpoint,
                    max_tokens=max_tokens,
                    usage=counts,
                )
            finally:
                add_tokens(self, counts)

        return timed(self, send)

    def complete(self, pack: ContextPack) -> CandidateResponse:
        import json as json_module

        user_prompt = "Context pack (the only citable text):\n" + json_module.dumps(
            pack.model_dump(), indent=2
        )
        self.requests += 1
        return ask_candidate(self._sender(_SYSTEM_PROMPT), user_prompt,
                             max_attempts=self._max_attempts, max_tokens=self._max_tokens,
                             truncation_max_tokens=self._truncation_max_tokens,
                             failures=self.failures, request=self.requests,
                         limits=self._limits)

    def complete_batch(self, packs: list[ContextPack]) -> dict[int, CandidateResponse]:
        """post76: every unmapped rule of a feed in ONE request (rule n = packs[n-1])."""
        self.requests += 1
        return ask_batch(self._sender(_BATCH_SYSTEM_PROMPT), batch_prompt(packs), len(packs),
                         max_attempts=self._max_attempts, max_tokens=self._max_tokens,
                         truncation_max_tokens=self._truncation_max_tokens,
                         failures=self.failures, request=self.requests,
                         limits=self._limits)
