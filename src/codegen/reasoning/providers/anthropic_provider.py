"""Real Layer 2 backend. Only constructed when ANTHROPIC_API_KEY is set and
dry-run is off (see ``build_provider``); ``anthropic`` is imported lazily so
the package is not a hard dependency of the deterministic path (install the
``live`` extra to get it).

The model is asked for a single JSON object matching CandidateResponse,
through the shared ask loop (:mod:`codegen.reasoning.providers.ask`): the
tolerant JSON parser, each invalid attempt retried with "JSON only, no fences"
(and the validation error), up to ``config.reasoning.max_attempts`` total
attempts, then ProviderError; every failed attempt is recorded.
"""

from __future__ import annotations

import json

from codegen.config import Config
from codegen.reasoning.providers.ask import AttemptFailure, ask_candidate
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.reasoning.usage import timed

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
    "the rule_text or the contract_excerpts entries ONLY — these are the only "
    "citable material. The column lists (available_source_columns, "
    "available_stage_columns, audit_columns) are context, not citable material: "
    "never use a bare column name as a citation.\n"
    "Ground every claim in the provided context pack only. Citations that are "
    "not exact substrings of the rule_text or contract_excerpts are rejected. "
    "Use only columns listed in the pack."
)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, config: Config) -> None:
        import anthropic

        from codegen.reasoning.mode import guard_live_call

        guard_live_call("Layer 2 (Anthropic API)", sdk_module=anthropic)
        self._client = anthropic.Anthropic()
        self._model = config.reasoning.model
        # What the run record reads (codegen.reasoning.usage).
        self.model = self._model
        self.endpoint: str | None = None
        self.calls = 0
        self.seconds = 0.0
        self._max_tokens = config.reasoning.max_tokens
        self._max_attempts = config.reasoning.max_attempts
        self._truncation_max_tokens = config.reasoning.truncation_max_tokens
        self.requests = 0
        self.failures: list[AttemptFailure] = []

    def complete(self, pack: ContextPack) -> CandidateResponse:
        user_prompt = "Context pack (the only citable text):\n" + json.dumps(
            pack.model_dump(), indent=2
        )
        self.requests += 1

        def send(prompt: str, max_tokens: int) -> str:
            # No sampling params: claude-opus-4-8 rejects temperature/top_p/top_k
            # with a 400 (removed on Opus 4.7+) — proven by the first live run.
            self.calls += 1
            message = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in message.content if block.type == "text")

        return ask_candidate(timed(self, send), user_prompt, max_attempts=self._max_attempts,
                             max_tokens=self._max_tokens,
                             truncation_max_tokens=self._truncation_max_tokens,
                             failures=self.failures, request=self.requests)
