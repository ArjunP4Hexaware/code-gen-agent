"""One Layer-2 question, asked until a schema-valid answer (2026-10-14).

D1 post43: pair_12 "5 calls, 5 failed, fallback used"; pair_2 one failure
per feed before the retry answered. The reason never reached the log. Both
live providers now ask through :func:`ask_candidate`:

- the post43 tolerant parser (:func:`codegen.layout.model.parse_json_response`:
  fences, a preamble, the outermost balanced object) before the schema check;
- a failed attempt is retried with ``RETRY_INSTRUCTION`` ("Respond with JSON
  only, no fences") — and, for a schema error, the error itself;
- a response that ends inside the JSON object (cut off at ``max_tokens``: the
  serving endpoint's extended thinking spends the same budget) is retried with
  ``reasoning.truncation_max_tokens``, said in the log;
- every failed attempt is recorded on the provider (``failures``): the reason
  (no response text) and the first ``RAW_LOG_CHARS`` characters of the raw
  response — D1-only diagnostics, written by
  :func:`codegen.reasoning.raw_log.log_layer2_failures`, never to a report,
  ``candidates.json`` or a tracked file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from pydantic import ValidationError

from codegen.layout.model import (
    RAW_LOG_CHARS,
    RETRY_INSTRUCTION,
    TRUNCATED,
    parse_json_response,
)
from codegen.reasoning.providers import ProviderError
from codegen.reasoning.schema import CandidateResponse


@dataclass(frozen=True)
class AttemptFailure:
    """One failed Layer-2 attempt. ``raw`` is D1-only (the model's text can
    quote the contract it was shown)."""

    request: int            # the provider's request number (1 = first rule asked)
    attempt: int
    attempts: int
    reason: str             # never the response text
    raw: str                # first RAW_LOG_CHARS characters
    max_tokens: int
    raised_to: int | None = None
    recovered: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def schema_reason(exc: ValidationError) -> str:
    """A pydantic error without the input values it echoes (model text)."""
    parts = [f"{'.'.join(map(str, e.get('loc', ()))) or '<root>'}: {e.get('msg', '')}"
             for e in exc.errors()]
    return f"schema validation failed ({len(parts)} error(s)): " + "; ".join(parts)


def ask_candidate(send, user_prompt: str, *, max_attempts: int, max_tokens: int,
                  truncation_max_tokens: int, failures: list[AttemptFailure],
                  request: int) -> CandidateResponse:
    """``send(prompt, max_tokens) -> text`` until a schema-valid response;
    every failed attempt is appended to ``failures``. A transport error is
    recorded and re-raised (the engine turns it into a failed candidate)."""
    attempts = max(1, max_attempts)
    prompt, tokens = user_prompt, max_tokens
    start = len(failures)
    last = ""
    for attempt in range(1, attempts + 1):
        try:
            text = send(prompt, tokens) or ""
        except Exception as exc:  # noqa: BLE001 — recorded, then the engine's
            failures.append(AttemptFailure(request, attempt, attempts,
                                           f"transport: {exc}", "", tokens))
            raise
        raised_to = None
        try:
            data = parse_json_response(text)
        except ValueError as exc:
            last = f"no JSON object: {exc}"
            retry = (f"Your previous response could not be read as JSON ({exc}). "
                     f"{RETRY_INSTRUCTION}")
            if TRUNCATED in str(exc) and truncation_max_tokens > tokens:
                raised_to = truncation_max_tokens
        else:
            try:
                response = CandidateResponse.model_validate(data)
            except ValidationError as exc:
                last = schema_reason(exc)
                retry = (f"Your previous response failed schema validation:\n{last}\n"
                         f"Respond again with ONLY the corrected JSON object. "
                         f"{RETRY_INSTRUCTION}")
            else:
                for index in range(start, len(failures)):
                    failures[index] = _recovered(failures[index])
                return response
        failures.append(AttemptFailure(request, attempt, attempts, last,
                                       text[:RAW_LOG_CHARS], tokens, raised_to))
        if raised_to is not None:
            tokens = raised_to
        prompt = f"{user_prompt}\n\n{retry}"
    raise ProviderError(f"no schema-valid response after {attempts} attempt(s); "
                        f"last error: {last}")


def _recovered(failure: AttemptFailure) -> AttemptFailure:
    return AttemptFailure(**{**failure.as_dict(), "recovered": True})


__all__ = ["AttemptFailure", "ask_candidate", "schema_reason"]
