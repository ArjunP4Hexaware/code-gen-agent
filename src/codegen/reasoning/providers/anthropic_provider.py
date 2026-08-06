"""Real Layer 2 backend. Only constructed when ANTHROPIC_API_KEY is set and
dry-run is off (see ``build_provider``); ``anthropic`` is imported lazily so
the package is not a hard dependency of the deterministic path.

The model is asked for a single JSON object matching CandidateResponse. Each
invalid attempt is retried with the validation error appended, up to
``config.reasoning.max_attempts`` total attempts, then ProviderError.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from codegen.config import Config
from codegen.reasoning.providers import ProviderError
from codegen.reasoning.schema import CandidateResponse, ContextPack

_SYSTEM_PROMPT = (
    "You are a data-engineering assistant proposing a REVIEW CANDIDATE for one "
    "free-text validation rule from an ingestion contract. Your output is never "
    "deployed directly; an engineer reviews it.\n"
    "Respond with a single JSON object and nothing else, with keys:\n"
    '  "classification": one of "mappable", "orchestration_config", '
    '"notification", "out_of_scope"\n'
    '  "code_candidate": a short PySpark sketch as a string, or null for '
    "non-code classifications\n"
    '  "rationale": why this classification and sketch\n'
    '  "citations": a non-empty list of EXACT verbatim substrings copied from '
    "the provided contract text that support your answer\n"
    "Ground every claim in the provided context pack only. Citations that are "
    "not exact substrings of the pack are rejected. Use only columns listed in "
    "the pack."
)


def _extract_json(text: str) -> str:
    """Tolerate a fenced code block around the JSON object."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline:].strip()
        if stripped.endswith("```"):
            stripped = stripped[: stripped.rfind("```")].strip()
    return stripped


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, config: Config) -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = config.reasoning.model
        self._max_tokens = config.reasoning.max_tokens
        self._max_attempts = config.reasoning.max_attempts

    def complete(self, pack: ContextPack) -> CandidateResponse:
        user_prompt = "Context pack (the only citable text):\n" + json.dumps(
            pack.model_dump(), indent=2
        )
        errors: list[str] = []
        for _ in range(self._max_attempts):
            message = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = "".join(block.text for block in message.content if block.type == "text")
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
