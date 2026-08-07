"""Real Layer 2 backend. Only constructed when ANTHROPIC_API_KEY is set and
dry-run is off (see ``build_provider``); ``anthropic`` is imported lazily so
the package is not a hard dependency of the deterministic path (install the
``live`` extra to get it).

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
    "Respond with exactly one JSON object and nothing else — no preamble, no "
    "markdown fences, no commentary after it. The object must contain exactly "
    "these four keys, always all present, and no others:\n"
    '  "classification": one of "mappable", "orchestration_config", '
    '"notification", "out_of_scope"\n'
    '  "code_candidate": a short PySpark sketch as a string, or the JSON '
    "literal null for non-code classifications (never omit the key)\n"
    '  "rationale": why this classification and sketch\n'
    '  "citations": a non-empty list of EXACT verbatim substrings copied from '
    "the provided contract text that support your answer\n"
    "Ground every claim in the provided context pack only. Citations that are "
    "not exact substrings of the pack are rejected. Use only columns listed in "
    "the pack."
)


def _first_balanced_object(text: str) -> str | None:
    """Return the first ``{...}`` block with balanced, string-aware braces."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _extract_json(text: str) -> str:
    """Isolate the JSON object from a response that may carry prose or fences.

    Never raises: with no object present the stripped text is returned as-is
    and the schema validation downstream turns it into a normal retry.
    """
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    candidate = _first_balanced_object(stripped)
    return candidate if candidate is not None else stripped


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, config: Config) -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = config.reasoning.model
        self._max_tokens = config.reasoning.max_tokens
        self._max_attempts = config.reasoning.max_attempts
        self._temperature = config.reasoning.temperature

    def complete(self, pack: ContextPack) -> CandidateResponse:
        user_prompt = "Context pack (the only citable text):\n" + json.dumps(
            pack.model_dump(), indent=2
        )
        errors: list[str] = []
        for _ in range(self._max_attempts):
            message = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
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
