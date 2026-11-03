"""Grounding check: every citation must be verbatim contract text.

A citation passes only if it appears in the rule text or one of the pack's
contract excerpts, compared on *canonicalized* text: the pack is shown to the
model as indented JSON, so a faithful copy may carry JSON escapes (``\\"``,
``\\n``), and models routinely normalize typography (curly quotes, dashes) or
whitespace. Canonicalization forgives exactly those transcription artifacts —
a paraphrase, hallucinated column, or invented requirement still fails, and
the candidate is surfaced as ungrounded in the review artifact.

post159 (P1-6, L2-3 / L2-4): a substring is not enough. A citation matches on
word boundaries, quotes at least ``reasoning.min_citation_words`` words (or
the WHOLE rule / excerpt it comes from, when that is shorter), and is never
just an available column name; at least one citation must come from the
candidate's OWN rule — a sibling rule, the SLA or the frequency (every pack of
a feed carries them) count only as extras. The failure notes name the
citation by its position, never by its text (the model's words stay in
``candidates.json``).
"""

from __future__ import annotations

import re

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
_WORD = re.compile(r"\w+")


def _canonicalize(text: str) -> str:
    for sequence, replacement in (*_JSON_ESCAPES, *_TYPOGRAPHY):
        text = text.replace(sequence, replacement)
    return " ".join(text.split())


def _found(citation: str, text: str) -> bool:
    """``citation`` in ``text`` on word boundaries (an edge that is a word
    character may not continue a word of ``text``)."""
    left = r"(?<!\w)" if re.match(r"\w", citation) else ""
    right = r"(?!\w)" if re.search(r"\w$", citation) else ""
    return re.search(left + re.escape(citation) + right, text) is not None


def _quotes(citation: str, source: str, min_words: int) -> bool:
    """A citation of ``source``: found on word boundaries and long enough —
    ``min_words`` words, or all of ``source``."""
    if not _found(citation, source):
        return False
    return len(_WORD.findall(citation)) >= min_words or citation == source


def grounding_failures(pack: ContextPack, response: CandidateResponse, *,
                       min_citation_words: int) -> list[str]:
    """One message per citation that fails, plus one when no citation quotes
    the candidate's own rule."""
    own = _canonicalize(pack.rule_text)
    extras = [_canonicalize(text) for text in pack.contract_excerpts]
    columns = {_canonicalize(c).casefold()
               for c in (*pack.available_source_columns, *pack.available_stage_columns,
                         *pack.audit_columns)}
    total = len(response.citations)
    failures: list[str] = []
    from_own_rule = False
    for number, citation in enumerate(response.citations, 1):
        canonical = _canonicalize(citation)
        where = f"citation {number} of {total}"
        if not canonical:
            failures.append(f"{where} is empty")
        elif canonical.casefold() in columns:
            failures.append(f"{where} is only a column name, not contract text")
        elif _quotes(canonical, own, min_citation_words):
            from_own_rule = True
        elif any(_quotes(canonical, text, min_citation_words) for text in extras):
            pass                        # a sibling / SLA / frequency fact: an extra
        elif any(_found(canonical, text) for text in (own, *extras)):
            failures.append(f"{where} is too short to ground on (fewer than "
                            f"{min_citation_words} words, not a whole rule or excerpt)")
        else:
            failures.append(f"{where} is not verbatim contract text")
    if not from_own_rule:
        failures.append("no citation quotes the candidate's own rule text "
                        f"(at least {min_citation_words} words, or the whole rule)")
    return failures
