"""Response schema every provider must satisfy. Validation failures retry
once with the error appended, then record a failure — never a silent skip.

post159 (P2-2, L2-5): the lengths of ``rationale``, ``code_candidate``, each
citation and the citations list are bounded by ``reasoning.response_limits``,
passed as the validation context (``limits_context``): an over-limit answer is
a schema failure like any other (the ask loop retries it, then records it).
Validated without that context (a model built in code), nothing is bounded.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")
LIMITS_KEY = "response_limits"


def limits_context(limits) -> dict:
    """The validation context that bounds a response (``ResponseLimitsConfig``)."""
    return {LIMITS_KEY: limits}


def _limits(info: ValidationInfo):
    return (info.context or {}).get(LIMITS_KEY)


def _bounded(value: str | None, limit: int, knob: str) -> str | None:
    """``value`` unchanged, or a ValueError naming the knob (never the text)."""
    if value is not None and len(value) > limit:
        raise ValueError(f"{len(value)} characters, more than "
                         f"reasoning.response_limits.{knob} ({limit})")
    return value


class CandidateResponse(BaseModel):
    """What the provider returns for one unmapped rule."""

    model_config = _MODEL_CONFIG

    classification: Literal["mappable", "orchestration_config", "notification", "out_of_scope"]
    # Proposed implementation sketch; None for non-code classifications.
    code_candidate: str | None
    rationale: str = Field(min_length=1)
    # Exact substrings of the contract text the candidate grounds on.
    citations: list[str] = Field(min_length=1)

    @field_validator("rationale")
    @classmethod
    def _rationale_bounded(cls, value: str, info: ValidationInfo) -> str:
        limits = _limits(info)
        return value if limits is None else _bounded(value, limits.rationale_max_chars,
                                                     "rationale_max_chars")

    @field_validator("code_candidate")
    @classmethod
    def _code_bounded(cls, value: str | None, info: ValidationInfo) -> str | None:
        limits = _limits(info)
        return value if limits is None else _bounded(value, limits.code_candidate_max_chars,
                                                     "code_candidate_max_chars")

    @field_validator("citations")
    @classmethod
    def _citations_bounded(cls, value: list[str], info: ValidationInfo) -> list[str]:
        limits = _limits(info)
        if limits is None:
            return value
        if len(value) > limits.citations_max_items:
            raise ValueError(f"{len(value)} citations, more than "
                             f"reasoning.response_limits.citations_max_items "
                             f"({limits.citations_max_items})")
        for citation in value:
            _bounded(citation, limits.citation_max_chars, "citation_max_chars")
        return value


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
