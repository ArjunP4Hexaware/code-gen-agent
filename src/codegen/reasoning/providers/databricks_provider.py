"""Layer-2 provider over Databricks Foundation Model APIs — a TRANSPORT.

Anthropic remains the sole model vendor: ``databricks.serving_endpoint``
serves the same Claude model named by ``reasoning.model``
(``databricks-claude-opus-4-8`` ↔ ``claude-opus-4-8``); only the wire
changes. Selected by ``build_provider`` only when ``reasoning.provider:
databricks_fmapi`` AND the workspace config resolves AND dry-run is off —
Anthropic stays the default, mock always wins on dry-run.

Same discipline as the Anthropic provider: identical system prompt and
JSON-extraction, schema-validation retries with the error appended, and NO
sampling parameters (the no-temperature rule holds across transports).
The SDK is only touched inside ``codegen.databricks.chat``; this module
imports keyless.
"""

from __future__ import annotations

from pydantic import ValidationError

from codegen.config import Config
from codegen.reasoning.providers import ProviderError
from codegen.reasoning.providers.anthropic_provider import (
    _SYSTEM_PROMPT,
    _extract_json,
)
from codegen.reasoning.schema import CandidateResponse, ContextPack


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
        # What the run record reads (codegen.reasoning.usage).
        self.endpoint = self._endpoint
        self.model = config.reasoning.model
        self.calls = 0

    def complete(self, pack: ContextPack) -> CandidateResponse:
        import json as json_module

        from codegen.databricks import chat

        user_prompt = "Context pack (the only citable text):\n" + json_module.dumps(
            pack.model_dump(), indent=2
        )
        errors: list[str] = []
        for _ in range(self._max_attempts):
            self.calls += 1
            text = chat(
                self._cfg,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                endpoint=self._endpoint,
                max_tokens=self._max_tokens,
            )
            try:
                return CandidateResponse.model_validate_json(_extract_json(text))
            except ValidationError as exc:
                errors.append(str(exc))
                user_prompt += (
                    "\n\nYour previous response failed schema validation:\n"
                    f"{exc}\nRespond again with ONLY the corrected JSON object."
                )
        raise ProviderError(
            f"no schema-valid response after {self._max_attempts} attempt(s); "
            f"last error: {errors[-1]}"
        )
