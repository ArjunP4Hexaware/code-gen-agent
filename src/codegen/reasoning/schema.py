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
