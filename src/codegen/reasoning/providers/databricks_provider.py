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
from codegen.reasoning.providers.anthropic_provider import _SYSTEM_PROMPT
from codegen.reasoning.providers.ask import AttemptFailure, ask_candidate
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.reasoning.usage import timed


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
        # What the run record reads (codegen.reasoning.usage).
        self.endpoint = self._endpoint
        self.model = config.reasoning.model
        self.calls = 0
        self.seconds = 0.0
        self.requests = 0
        self.failures: list[AttemptFailure] = []

    def complete(self, pack: ContextPack) -> CandidateResponse:
        import json as json_module

        from codegen.databricks import chat

        user_prompt = "Context pack (the only citable text):\n" + json_module.dumps(
            pack.model_dump(), indent=2
        )
        self.requests += 1

        def send(prompt: str, max_tokens: int) -> str:
            self.calls += 1
            return chat(
                self._cfg,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                endpoint=self._endpoint,
                max_tokens=max_tokens,
            )

        return ask_candidate(timed(self, send), user_prompt, max_attempts=self._max_attempts,
                             max_tokens=self._max_tokens,
                             truncation_max_tokens=self._truncation_max_tokens,
                             failures=self.failures, request=self.requests)
