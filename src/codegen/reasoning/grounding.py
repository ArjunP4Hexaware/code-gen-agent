"""Grounding check: every citation must be verbatim contract text.

A citation passes only if it appears as a substring of the rule text or one
of the pack's contract excerpts, compared on *canonicalized* text: the pack
is shown to the model as indented JSON, so a faithful copy may carry JSON
escapes (``\\"``, ``\\n``), and models routinely normalize typography
(curly quotes, dashes) or whitespace. Canonicalization forgives exactly
those transcription artifacts — a paraphrase, hallucinated column, or
invented requirement still fails, and the candidate is surfaced as
ungrounded in the review artifact.
"""

from __future__ import annotations

from codegen.reasoning.schema import CandidateResponse, ContextPack

# JSON escape sequences a model may copy verbatim from the rendered pack.
# Backslash-backslash first so it cannot manufacture new escapes.
_JSON_ESCAPES = (("\\\\", "\\"), ('\\"', '"'), ("\\n", " "), ("\\t", " "), ("\\r", " "))
# Typographic characters models substitute for their ASCII equivalents.
_TYPOGRAPHY = (
    ("“", '"'),
    ("”", '"'),
    ("‘", "'"),
    ("’", "'"),
    ("–", "-"),
    ("—", "-"),
    ("…", "..."),
)


def _canonicalize(text: str) -> str:
    for sequence, replacement in (*_JSON_ESCAPES, *_TYPOGRAPHY):
        text = text.replace(sequence, replacement)
    return " ".join(text.split())


def grounding_failures(pack: ContextPack, response: CandidateResponse) -> list[str]:
    """Return one message per citation not found (canonicalized) in the pack."""
    citable = [_canonicalize(text) for text in (pack.rule_text, *pack.contract_excerpts)]
    failures: list[str] = []
    for citation in response.citations:
        canonical = _canonicalize(citation)
        if not canonical or not any(canonical in text for text in citable):
            failures.append(f"citation is not verbatim contract text: {citation!r}")
    return failures
