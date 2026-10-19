"""Response schema every provider must satisfy. Validation failures retry
once with the error appended, then record a failure — never a silent skip.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class CandidateResponse(BaseModel):
    """What the provider returns for one unmapped rule."""

    model_config = _MODEL_CONFIG

    classification: Literal["mappable", "orchestration_config", "notification", "out_of_scope"]
    # Proposed implementation sketch; None for non-code classifications.
    code_candidate: str | None
    rationale: str = Field(min_length=1)
    # Exact substrings of the contract text the candidate grounds on.
    citations: list[str] = Field(min_length=1)


class ContextPack(BaseModel):
    """Everything the provider may ground on — nothing outside it counts."""

    model_config = _MODEL_CONFIG

    feed_id: str
    rule_text: str
    # Contract excerpts the model may cite (rule text + related contract facts).
    contract_excerpts: list[str]
    available_source_columns: list[str]
    available_stage_columns: list[str]
    audit_columns: list[str]


class BatchRule(BaseModel):
    """One unmapped rule inside a feed's batched request (post76)."""

    model_config = _MODEL_CONFIG

    rule: int                   # 1-based position in the request
    rule_text: str


class BatchPack(BaseModel):
    """post76: ONE request per feed — every unmapped rule of the feed plus the
    citable contract facts they share (a :class:`ContextPack` per rule, folded)."""

    model_config = _MODEL_CONFIG

    feed_id: str
    rules: list[BatchRule] = Field(min_length=1)
    contract_excerpts: list[str]
    available_source_columns: list[str]
    available_stage_columns: list[str]
    audit_columns: list[str]


class BatchCandidate(CandidateResponse):
    """One rule's answer inside a batched response: ``rule`` = its number."""

    rule: int


class BatchResponse(BaseModel):
    """What the provider returns for a feed's batched request."""

    model_config = _MODEL_CONFIG

    candidates: list[BatchCandidate] = Field(min_length=1)


def batch_pack(packs: list[ContextPack]) -> BatchPack:
    """The feed's packs folded into one request (the shared facts come from the
    first pack: every pack of a feed carries the same ones)."""
    first = packs[0]
    return BatchPack(
        feed_id=first.feed_id,
        rules=[BatchRule(rule=n, rule_text=p.rule_text) for n, p in enumerate(packs, 1)],
        contract_excerpts=first.contract_excerpts,
        available_source_columns=first.available_source_columns,
        available_stage_columns=first.available_stage_columns,
        audit_columns=first.audit_columns,
    )
