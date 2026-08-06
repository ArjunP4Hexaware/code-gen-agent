"""Build the ContextPack a provider may ground on.

The pack is assembled deterministically from the ResolvedFeedSpec — the
provider sees only contract-derived text, and the grounding check later
rejects any citation that is not verbatim inside it.
"""

from __future__ import annotations

from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.reasoning.schema import ContextPack
from codegen.rules.compiler import RuleOutcome


def build_context_pack(spec: ResolvedFeedSpec, outcome: RuleOutcome) -> ContextPack:
    """One pack per unmapped rule: the rule plus every citable contract fact."""
    excerpts: list[str] = list(spec.validation_rules)
    excerpts.extend(spec.load_windows_sla)
    if spec.frequency is not None:
        excerpts.append(spec.frequency)

    source_columns: list[str] = []
    stage_columns: list[str] = []
    for segment in spec.segments:
        for field in segment.fields:
            source_columns.append(field.source_column)
            stage_columns.append(field.stage_column)

    return ContextPack(
        feed_id=spec.feed_id,
        rule_text=outcome.rule_text,
        contract_excerpts=excerpts,
        available_source_columns=source_columns,
        available_stage_columns=stage_columns,
        audit_columns=[a.column for a in spec.audit_columns],
    )
