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
    extraction's deterministic review items — an "extraction_assumption"
    needs explicit engineer approval; an "escalated_conflict" is held for a
    source-team ruling and acknowledged. Both ride the SAME review artifact,
    decision store, and pending counts as Layer-2 candidates (wired in, not
    forked); neither comes from a model call."""

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
    # Human-readable body for non-layer2 items (what is assumed/held and why).
    detail: str | None = None


def segmented_review_items(spec: ResolvedFeedSpec) -> list[RuleCandidate]:
    """Deterministic review items for a segmented-extraction run — the two
    governance boundaries (plus the discovered natural-key gap) surfaced as
    approve/reject cards in the existing review flow. Empty for flat feeds
    and when the discriminator status is ``confirmed`` (the provenance line
    still records it)."""
    seg = spec.segmented_extraction
    if seg is None:
        return []
    items: list[RuleCandidate] = []
    d = seg.discriminators
    if d.status != "confirmed":
        items.append(RuleCandidate(
            feed_id=spec.feed_id,
            rule_text=(
                f"ASSUMPTION — record-type discriminators: Header={d.header!r}, "
                f"Detail={d.detail!r}, Trailer={d.trailer!r} (status: {d.status})"
            ),
            provider="segmented-extraction",
            response=None,
            grounded=True,
            failure_notes=[],
            kind="extraction_assumption",
            detail=(
                "The workbook confirms segment membership per field but states "
                "the literal H/D/T record-type values nowhere. These values are "
                "DECLARED in the feed's FAQ, not inferred, and every artefact "
                "row derived from them is flagged ASSUMED. Approve to proceed "
                "under the assumption; flip the FAQ status to 'confirmed' once "
                "the source team supplies the source dictionary."
            ),
        ))
    if seg.natural_key_declared:
        items.append(RuleCandidate(
            feed_id=spec.feed_id,
            rule_text=(
                "ASSUMPTION — natural key declared, not derived: "
                + ", ".join(seg.natural_key_declared)
            ),
            provider="segmented-extraction",
            response=None,
            grounded=True,
            failure_notes=[],
            kind="extraction_assumption",
            detail=(
                "The workbook's Mandatory/Primary Key columns carry no signal, "
                "so the MERGE natural key comes from the FAQ's "
                "natural_key_columns declaration (an engineer decision, not "
                "workbook evidence). Approve to proceed; correct the FAQ if "
                "the key is wrong."
            ),
        ))
    if seg.held_standard:
        held = "; ".join(
            f"{h.table} ({h.column_count} columns)" for h in seg.held_standard)
        items.append(RuleCandidate(
            feed_id=spec.feed_id,
            rule_text=(
                "ESCALATED CONFLICT — workbook defines a Standard layer; "
                f"FRD contract scopes this feed stage-only. Held: {held}"
            ),
            provider="segmented-extraction",
            response=None,
            grounded=True,
            failure_notes=[],
            kind="escalated_conflict",
            detail=(
                "Precedence rule: the FRD contract governs target layers. The "
                "workbook's Standard-layer content is parsed and preserved as "
                "evidence but NOT emitted (no standard DDL, no standard "
                "framework rows) until the source team rules which document is "
                "right. Nothing was deleted and nothing was silently resolved."
            ),
        ))
    return items


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
