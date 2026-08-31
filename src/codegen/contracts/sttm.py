"""STTM column-level mapping contract (``sttm_mapping_contracts.json`` shape).

The one dialect extension over the frozen MIDS shape is documented in
docs/DESIGN.md §1: on segmented feeds (CAQH Header/Detail/Trailer), each field
may carry ``record_segment`` and ``stage_table``. Absent on flat feeds;
their presence/absence is cross-validated against the FRD side at resolve
time, and within this model every column referenced by ``load_rules`` must
name a real field.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RecordSegment = Literal["Header", "Detail", "Trailer"]

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class SourceFile(BaseModel):
    model_config = _MODEL_CONFIG

    name_pattern: str
    format: str
    delimiter: str | None
    frequency: str | None


class TableRef(BaseModel):
    model_config = _MODEL_CONFIG

    schema_name: str = Field(alias="schema")
    table: str


class RecycleSpec(BaseModel):
    """Structured recycle rule — the executable side of the FRD's free text."""

    model_config = _MODEL_CONFIG

    applies_to: str
    enabled: bool
    validation: str
    on_match: str
    on_no_match: str
    recycle_window_days: int = Field(gt=0)


class LoadRules(BaseModel):
    model_config = _MODEL_CONFIG

    not_null_columns: list[str]
    mandatory_columns: list[str]
    phi_columns: list[str]
    recycle: RecycleSpec | None


# ---- segmented-extraction block (v2 dialect, 2026-08-31) --------------------
# A segmented (Header/Detail/Trailer) workbook extracts to the SAME flat feed
# shape (Detail rows are the payload), plus this block: what else the workbook
# declared, and the explicit, human-declared assumptions the run proceeds
# under. Nothing here is inferred — the two governance boundaries
# (discriminator values, FRD-vs-workbook layer conflict) surface for review
# instead of being guessed (docs/SEGMENTED_MODE_DESIGN.md blockers 1 and 2).


class RecordTypeDiscriminators(BaseModel):
    """The H/D/T record-type values — DECLARED, never inferred: the workbook
    confirms segment membership per field but states the literal values
    nowhere. ``assumed_pending_source_team`` gates a review item; ``confirmed``
    drops the gate but keeps the provenance line."""

    model_config = _MODEL_CONFIG

    header: str
    detail: str
    trailer: str
    status: Literal["assumed_pending_source_team", "confirmed"]


class EnvelopeEntry(BaseModel):
    """One Header/Trailer row — file envelope, not a target column: it appears
    in the generation report (record counts, file dates, sequence checks) and
    never in table DDL."""

    model_config = _MODEL_CONFIG

    segment: Literal["Header", "Trailer"]
    field_name: str
    datatype: str | None
    stage_table: str | None
    description: str | None
    rule: str | None


class HeldStandardTable(BaseModel):
    """Workbook-declared Standard-layer content held back under the precedence
    rule (the FRD contract governs target layers): preserved as evidence,
    never emitted."""

    model_config = _MODEL_CONFIG

    catalog: str | None
    schema_name: str | None = Field(default=None, alias="schema")
    table: str
    column_count: int
    reason: str


class SegmentedExtraction(BaseModel):
    model_config = _MODEL_CONFIG

    segments_found: list[str]
    row_counts: dict[str, int]
    envelope: list[EnvelopeEntry]
    discriminators: RecordTypeDiscriminators
    # FAQ-declared natural-key source columns, used only when the workbook's
    # Mandatory/Primary Key columns carry no signal (observed on the real
    # workbook) — declared by an engineer, never invented.
    natural_key_declared: list[str] = Field(default_factory=list)
    held_standard: list[HeldStandardTable] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AuditColumn(BaseModel):
    model_config = _MODEL_CONFIG

    column: str
    datatype: Literal["String", "Timestamp"]


class SttmField(BaseModel):
    """One source→stage→standard column mapping row."""

    model_config = _MODEL_CONFIG

    source_column: str
    description: str | None
    sample_value: str | None
    source_datatype: str
    nullable: bool
    phi: bool
    mandatory: bool
    stage_column: str
    stage_datatype: str
    standard_column: str | None
    standard_datatype: str | None
    value_spec: str | None = None
    # Segmented-dialect extension (CAQH) — see docs/DESIGN.md §1.
    record_segment: RecordSegment | None = None
    stage_table: str | None = None


class SttmFeed(BaseModel):
    """One feed's column-level mapping."""

    model_config = _MODEL_CONFIG

    feed_id: str
    source_system: str
    mapping_sheet: str | None
    source_file: SourceFile
    stage: TableRef
    standard: TableRef | None
    load_rules: LoadRules
    audit_columns: list[AuditColumn] = Field(min_length=1)
    field_count: int
    fields: list[SttmField] = Field(min_length=1)
    # Present only on feeds extracted from a segmented workbook (v2 dialect);
    # None on every flat feed, so existing contracts and the byte-compared
    # extractor output are untouched.
    segmented: SegmentedExtraction | None = None

    @model_validator(mode="after")
    def _check_internal_consistency(self) -> SttmFeed:
        errors: list[str] = []

        if self.field_count != len(self.fields):
            errors.append(
                f"field_count is {self.field_count} but fields[] has {len(self.fields)} entries"
            )

        source_columns = {f.source_column for f in self.fields}
        for rule_name in ("not_null_columns", "mandatory_columns", "phi_columns"):
            unknown = set(getattr(self.load_rules, rule_name)) - source_columns
            if unknown:
                errors.append(
                    f"load_rules.{rule_name} references columns not in fields[]: {sorted(unknown)}"
                )

        recycle = self.load_rules.recycle
        if recycle is not None and recycle.applies_to not in source_columns:
            errors.append(
                f"load_rules.recycle.applies_to '{recycle.applies_to}' is not a column in fields[]"
            )

        phi_flagged = {f.source_column for f in self.fields if f.phi}
        phi_listed = set(self.load_rules.phi_columns)
        if phi_flagged != phi_listed:
            errors.append(
                f"fields flagged phi=true {sorted(phi_flagged)} do not match "
                f"load_rules.phi_columns {sorted(phi_listed)}"
            )

        # Segment annotations must be all-or-nothing within a feed: a mix
        # means the contract is half-migrated to the segmented dialect.
        with_segment = [f.source_column for f in self.fields if f.record_segment]
        if with_segment and len(with_segment) != len(self.fields):
            missing = sorted(source_columns - set(with_segment))
            errors.append(f"some fields carry record_segment but these do not: {missing}")
        for f in self.fields:
            if (f.record_segment is None) != (f.stage_table is None):
                errors.append(
                    f"field '{f.source_column}' must set record_segment and "
                    "stage_table together or not at all"
                )

        if errors:
            raise ValueError(
                f"STTM feed '{self.feed_id}' failed validation:\n  - " + "\n  - ".join(errors)
            )
        return self

    @property
    def is_segmented(self) -> bool:
        return any(f.record_segment is not None for f in self.fields)


class SttmContract(BaseModel):
    """Top-level STTM mapping contract."""

    model_config = _MODEL_CONFIG

    contract_name: str
    generated_from_workbook: str
    sttm_version: str
    generated_date: str
    notes: list[str]
    feeds: list[SttmFeed] = Field(min_length=1)
    # True only on the clearly-labeled synthetic CAQH stand-in contract;
    # the real generator never emits this key, so it defaults False.
    synthetic: bool = False

    @model_validator(mode="after")
    def _check_unique_feed_ids(self) -> SttmContract:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for feed in self.feeds:
            (duplicates if feed.feed_id in seen else seen).add(feed.feed_id)
        if duplicates:
            raise ValueError(f"duplicate feed_id(s) in STTM contract: {sorted(duplicates)}")
        return self
