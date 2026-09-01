"""Run Layer 2 over the rules Layer 1 could not map.

For each ``unmapped`` outcome: build the context pack, ask the provider,
grounding-check the citations. Provider failures become candidates with
``response=None`` and a failure note — never a silent skip, and never an
exception that aborts generation of the deterministic modules.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.reasoning.context import build_context_pack
from codegen.reasoning.grounding import grounding_failures
from codegen.reasoning.providers import Provider
from codegen.reasoning.schema import CandidateResponse
from codegen.rules.compiler import RuleOutcome

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class RuleCandidate(BaseModel):
    """One reviewed-artifact entry: the provider's proposal plus its audit trail.

    ``kind`` distinguishes Layer-2 proposals ("layer2") from the segmented
    extraction's deterministic "confirm" items (soft confirmations of a
    document-derived fact). Both ride the SAME review artifact, decision
    store, and pending counts (wired in, not forked). A non-layer2 item MUST
    carry a non-empty ``citation`` quoting the exact FRD field or STTM cell
    it rests on — an item that cannot cite its evidence is a bug."""

    model_config = _MODEL_CONFIG

    feed_id: str
    rule_text: str
    provider: str
    # None when the provider errored out; see failure_notes.
    response: CandidateResponse | None
    # True only when every citation passed the verbatim grounding check.
    grounded: bool
    failure_notes: list[str]
    kind: str = "layer2"
    # Human-readable body for non-layer2 items.
    detail: str | None = None
    # The document evidence a non-layer2 item rests on (verbatim quote).
    citation: str | None = None


def segmented_review_items(spec: ResolvedFeedSpec) -> list[RuleCandidate]:
    """Deterministic review items for a segmented-extraction run: one soft
    CONFIRM item for the document-derived record identification. Empty for
    flat feeds. Every item cites the exact STTM cell it rests on."""
    seg = spec.segmented_extraction
    if seg is None:
        return []
    ident = seg.identification
    return [RuleCandidate(
        feed_id=spec.feed_id,
        rule_text=(
            "CONFIRM — positional header/detail identification per CAQH-style "
            f"spec: trailer marker {ident.trailer_marker!r}; header = "
            f"{ident.header_rule}; detail = {ident.detail_rule}. Confirm with "
            "the source team."
        ),
        provider="segmented-extraction",
        response=None,
        grounded=True,
        failure_notes=[],
        kind="confirm",
        detail=(
            "Record identification is DERIVED from the documents "
            f"({ident.method}), not assumed: the STTM states the trailer's "
            "static record-type value, and header/detail follow positionally. "
            "This is a soft confirmation, not an assumption gate — the run "
            "proceeds; a source-team confirmation closes it."
        ),
        citation=ident.citation,
    )]


def run_reasoning(
    spec: ResolvedFeedSpec,
    outcomes: list[RuleOutcome],
    provider: Provider,
) -> list[RuleCandidate]:
    """Produce one candidate per unmapped outcome, in contract order."""
    candidates: list[RuleCandidate] = []
    for outcome in outcomes:
        if outcome.classification != "unmapped":
            continue
        pack = build_context_pack(spec, outcome)
        try:
            response = provider.complete(pack)
        except Exception as exc:  # noqa: BLE001 — recorded, never silently dropped
            candidates.append(
                RuleCandidate(
                    feed_id=spec.feed_id,
                    rule_text=outcome.rule_text,
                    provider=provider.name,
                    response=None,
                    grounded=False,
                    failure_notes=[f"provider '{provider.name}' failed: {exc}"],
                )
            )
            continue
        failures = grounding_failures(pack, response)
        candidates.append(
            RuleCandidate(
                feed_id=spec.feed_id,
                rule_text=outcome.rule_text,
                provider=provider.name,
                response=response,
                grounded=not failures,
                failure_notes=failures,
            )
        )
    return candidates
