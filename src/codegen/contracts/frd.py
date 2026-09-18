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
# "Upsert" added 2026-08-26: the SFMC Email Campaign FRD declares a standard-
# layer "Upsert" strategy (stage stays Truncate and Load). The generated
# writer's MERGE already implements upsert semantics; the literal was the gap.
LoadStrategy = Literal["Truncate and Load", "Append", "Upsert"]
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
    # None only on docx-extracted contracts (M2) whose document states no
    # strategy — unsourced fields are null; the resolver refuses to generate
    # without one.
    load_strategy: LoadStrategy | None


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


class StructuredRow(BaseModel):
    """One row of a nested table (``key`` = first column) or one per-file
    block (``key`` = the heading line); ``values`` = header/label -> text."""

    model_config = _MODEL_CONFIG

    key: str
    values: dict[str, str] = Field(default_factory=dict)


class StructuredValue(BaseModel):
    """M7: a docx cell the reader refused to take as a scalar value — a
    nested table, per-file blocks, a pointer to another document, a
    label-prefixed description, or text that still spans lines. The feed
    field stays UNSTATED; this records what the cell held (text truncated,
    logged, never written to an output) so the layout stage can resolve a
    nested table / block per derived feed and the gate can flag the rest."""

    model_config = _MODEL_CONFIG

    kind: Literal["nested_table", "per_file_blocks", "pointer", "label_prefixed", "multiline"]
    table: int
    row: int
    col: int
    label: str
    text: str = ""
    # pointer: the document / place the sentence names.
    target: str | None = None
    # label_prefixed: the label seen in front of '='.
    prefix_label: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[StructuredRow] = Field(default_factory=list)


class FieldEvidence(BaseModel):
    """M2: where a docx-extracted field was read — Word table index, row and
    label cell, the label text as seen, the metadata section, the inline
    label when the value sat inside a free-text cell, and who resolved the
    layout. Keyed by contract path (``feeds[0].frequency``)."""

    model_config = _MODEL_CONFIG

    table: int
    row: int
    col: int
    label: str
    section: str | None = None
    inline_label: str | None = None
    source: Literal["synonyms", "model", "user", "cache"]


class FrdLayoutSummary(BaseModel):
    model_config = _MODEL_CONFIG

    family: str
    source: Literal["synonyms", "model", "user", "cache"]
    fingerprint: str
    unresolved: list[str] = Field(default_factory=list)


class FrdFeed(BaseModel):
    """One feed's worth of feed-level facts from the FRD contract."""

    model_config = _MODEL_CONFIG

    feed_name: str
    source_system: str
    # May be EMPTY only on docx-extracted contracts (M2): the F1/F2 label
    # families carry no file-pattern label, so the pattern comes from the
    # STTM at resolve time (M4). Upstream contracts always list >= 1.
    file_name_patterns: list[str]
    # None only on docx-extracted contracts whose document states no format.
    file_format: str | None
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
    # M2: per-field evidence + the layout the values were read through.
    # Both default so upstream contract JSON still loads unchanged.
    field_provenance: dict[str, FieldEvidence] = Field(default_factory=dict)
    layout: FrdLayoutSummary | None = None
    # M7: cells refused as scalar values (see StructuredValue), keyed by the
    # contract path they were read for. Default so older JSON loads unchanged.
    structured: dict[str, StructuredValue] = Field(default_factory=dict)
