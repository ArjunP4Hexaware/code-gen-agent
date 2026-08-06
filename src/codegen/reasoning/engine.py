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
    """One reviewed-artifact entry: the provider's proposal plus its audit trail."""

    model_config = _MODEL_CONFIG

    feed_id: str
    rule_text: str
    provider: str
    # None when the provider errored out; see failure_notes.
    response: CandidateResponse | None
    # True only when every citation passed the verbatim grounding check.
    grounded: bool
    failure_notes: list[str]


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
