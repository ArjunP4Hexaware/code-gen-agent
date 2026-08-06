"""Grounding check: every citation must be verbatim contract text.

A citation passes only if it appears as an exact substring of the rule text
or one of the pack's contract excerpts. Anything else — paraphrase,
hallucinated column, invented requirement — is a grounding failure, and the
candidate is surfaced as ungrounded in the review artifact.
"""

from __future__ import annotations

from codegen.reasoning.schema import CandidateResponse, ContextPack


def grounding_failures(pack: ContextPack, response: CandidateResponse) -> list[str]:
    """Return one message per citation not found verbatim in the pack."""
    citable = [pack.rule_text, *pack.contract_excerpts]
    failures: list[str] = []
    for citation in response.citations:
        if not any(citation in text for text in citable):
            failures.append(f"citation is not verbatim contract text: {citation!r}")
    return failures
