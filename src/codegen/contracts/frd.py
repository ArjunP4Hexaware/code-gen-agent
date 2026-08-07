"""FRD feed-level mapping contract (output of the BRD→FRD / STTM agent).

Mirrors the generator's JSON byte for byte — including ``_provenance`` and the
three-state ``status`` — so a contract that drifts from the frozen shape fails
validation loudly instead of being silently reinterpreted.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GateStatus = Literal["PASS", "PASS_WITH_FLAGS", "FAIL"]
LoadStrategy = Literal["Truncate and Load", "Append"]
RecordSegment = Literal["Header", "Detail", "Trailer"]

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class ProjectInfo(BaseModel):
    model_config = _MODEL_CONFIG

    project_id: str | None
    project_name: str
    business_context_summary: str | None


class AcdItem(BaseModel):
    """One assumption / constraint / dependency row from the FRD."""

    model_config = _MODEL_CONFIG

    name: str
    description: str
    acd_type: Literal["Assumption", "Constraint", "Dependency"]


class TargetSpec(BaseModel):
    """A stage or standard layer target: catalog.schema.tables + load strategy."""

    model_config = _MODEL_CONFIG

    catalog: str | None
    # "schema" shadows BaseModel.schema; keep the wire name via alias.
    schema_name: str | None = Field(alias="schema")
    tables: list[str]
    load_strategy: LoadStrategy


class GroundingSummary(BaseModel):
    model_config = _MODEL_CONFIG

    strict_checked: int
    strict_failed: list[str]
    advisory_checked: int
    advisory_flagged: list[str]


class AmbiguityContext(BaseModel):
    """Mirrors frd-to-sttm-agent's ``frdsttm.models.AmbiguityContext``.

    Which fields are populated depends on the ambiguity kind; the producer
    serializes with defaults omitted, so (unlike the rest of this module)
    absent keys here mean "not applicable", not drift.
    """

    model_config = _MODEL_CONFIG

    feed_names: list[str] = Field(default_factory=list)
    feed_indices: list[int] = Field(default_factory=list)
    rule: str | None = None
    field: str | None = None
    agent_value: str | None = None
    content_value: str | None = None
    path: str | None = None
    feed_index: int | None = None


class GatedAmbiguity(BaseModel):
    """Mirrors frd-to-sttm-agent's ``frdsttm.models.GatedAmbiguity`` — the
    structured ``_provenance.ambiguities`` entry current contracts carry
    (older contracts carry plain strings; both shapes are accepted)."""

    model_config = _MODEL_CONFIG

    id: str
    kind: Literal["attribution", "disagreement", "advisory_grounding"]
    text: str
    has_candidates: bool
    candidates: list[str] = Field(default_factory=list)
    context: AmbiguityContext = Field(default_factory=AmbiguityContext)


class Provenance(BaseModel):
    model_config = _MODEL_CONFIG

    enrichments: list[str]
    ambiguities: list[str | GatedAmbiguity]
    grounding: GroundingSummary


class FrdFeed(BaseModel):
    """One feed's worth of feed-level facts from the FRD contract."""

    model_config = _MODEL_CONFIG

    feed_name: str
    source_system: str
    file_name_patterns: list[str] = Field(min_length=1)
    file_format: str
    delimiter: str | None
    record_segments: list[RecordSegment]
    frequency: str | None
    load_windows_sla: list[str]
    lobs: list[str]
    domain: str | None
    sub_domain: str | None
    landing_location: str | None
    stage_target: TargetSpec
    standard_target: TargetSpec
    validation_rules: list[str]
    recycle_rule: str | None
    history_backfill: str | None
    archive_retention: str | None
    phi_pii_notes: str | None
    sttm_reference: str | None
    requirement_ids: list[str]

    @property
    def is_segmented(self) -> bool:
        return len(self.record_segments) > 0


class FrdContract(BaseModel):
    """Top-level FRD feed-level mapping contract."""

    model_config = _MODEL_CONFIG

    contract_name: str
    generated_from_frd: str
    generated_date: datetime
    generator: str
    status: GateStatus
    project: ProjectInfo
    in_scope: list[str]
    out_of_scope: list[str]
    assumptions_constraints_dependencies: list[AcdItem]
    feeds: list[FrdFeed] = Field(min_length=1)
    system_interfaces: list[str]
    open_items: list[str]
    provenance: Provenance | None = Field(default=None, alias="_provenance")
