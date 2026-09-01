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
    # Optional catalog (segmented dialect: the STTM's standard target group
    # states PR_STD.MBR; the FRD Structural Metadata names stage targets
    # only). None on flat contracts — serialization is unchanged.
    catalog: str | None = None


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


# ---- segmented-extraction block (v2 dialect; corrected 2026-09-01) ---------
# A segmented (Header/Detail/Trailer) workbook extracts to the SAME segmented
# dialect the resolver already consumes (record_segment + stage_table per
# field; segments are TABLES — FRD 1005034 acceptance criterion 2: "Header,
# Detail, Trailer data should be mapped to respective HDR, DTL and TRL
# tables"), plus this block: record identification DERIVED from the STTM (not
# assumed), and provenance notes that each cite the exact FRD field or STTM
# cell they rest on. A note without a citation is a bug.


class RecordTypeDiscriminators(BaseModel):
    """FAQ OVERRIDE ONLY (status must be ``confirmed``): record identification
    is derived from the STTM by default; this exists for a source team that
    later states literal record-type values."""

    model_config = _MODEL_CONFIG

    header: str
    detail: str
    trailer: str
    status: Literal["assumed_pending_source_team", "confirmed"]


class RecordIdentification(BaseModel):
    """How H/D/T records are told apart — DERIVED from the documents:
    trailer = record whose first field equals the STTM-stated static marker;
    header = first record of the file; detail = all others. The citation is
    the verbatim STTM cell the derivation rests on."""

    model_config = _MODEL_CONFIG

    method: Literal["derived_from_sttm", "declared_override"]
    trailer_marker: str
    header_rule: str
    detail_rule: str
    citation: str = Field(min_length=1)


class ProvenanceNote(BaseModel):
    """One extraction-time fact with the exact document evidence it rests on.
    ``citation`` is verbatim from the FRD contract or the STTM cell — a note
    that cannot cite its evidence must not be created."""

    model_config = _MODEL_CONFIG

    note: str = Field(min_length=1)
    citation: str = Field(min_length=1)


class SegmentedExtraction(BaseModel):
    model_config = _MODEL_CONFIG

    segments_found: list[str]
    row_counts: dict[str, int]
    identification: RecordIdentification
    provenance_notes: list[ProvenanceNote] = Field(default_factory=list)


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
    # Segmented dialect: per-segment STANDARD table (the STTM's second target
    # column group). None on flat feeds and on stage-only segmented feeds.
    standard_table: str | None = None


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
