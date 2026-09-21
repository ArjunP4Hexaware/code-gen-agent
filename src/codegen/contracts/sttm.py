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

    # None (M9.1b): neither the FRD nor the workbook names a file pattern at
    # extract time — no longer a hard stop; the chain continues at resolve
    # time (VDD FILES sheet, the `feeds[i].file_patterns` gap answer).
    name_pattern: str | None
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


class AuditColumn(BaseModel):
    model_config = _MODEL_CONFIG

    column: str
    datatype: Literal["String", "Timestamp"]


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
    # Per-segment audit columns EXACTLY as the STTM lists them ("Metadata of
    # the tables is provided in the STTM") — HDR/TRL typically carry three,
    # Detail the full set. Empty dict on older contracts (feed-wide applies).
    segment_audit: dict[str, list[AuditColumn]] = Field(default_factory=dict)


class FieldProvenance(BaseModel):
    """The cell a field was read from (M1): sheet, 1-based row and column of
    the field-name cell, plus who resolved the layout role that read it
    (the layout profile's source). Part of the contract, not a side channel;
    defaults to None so pre-M1 contract JSON still loads."""

    model_config = _MODEL_CONFIG

    sheet: str
    row: int = Field(ge=1)
    col: int = Field(ge=1)
    source: Literal["synonyms", "model", "user", "cache"]


class AuxiliarySheet(BaseModel):
    """A non-mapping sheet recognised by header signature (file details,
    table details, LOB crosswalk, DQ rules, family-C layout) — attached
    verbatim (headers + rows), never interpreted here."""

    model_config = _MODEL_CONFIG

    kind: str
    sheet: str
    headers: list[str]
    rows: list[list[str | None]]


class LayoutSummary(BaseModel):
    """Which discovery strategy/source produced the layout profile the
    values were read through, its fingerprint, and what stayed unresolved
    ("sheet/layer/role: reason") — empty on fully resolved layouts."""

    model_config = _MODEL_CONFIG

    strategy: str
    source: Literal["synonyms", "model", "user", "cache"]
    fingerprint: str
    unresolved: list[str] = Field(default_factory=list)


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
    # M1: the cell this field came from + the layout source that read it.
    provenance: FieldProvenance | None = None
    # M4: the segment spelling as the workbook writes it (HDDR / DET / TRLR
    # …) — the framework's fixed-width handler rows carry it verbatim.
    record_segment_label: str | None = None
    # M3: the source band's length / start / end cells, verbatim, when the
    # layout carries those roles — compared against the VDD by the gate.
    source_length: str | None = None
    source_start: str | None = None
    source_end: str | None = None
    # M9.2 (codegen.resolve.widths): the fixed-width BYTE width when it is not
    # simply the integer ``source_length`` — the STTM span end-start+1, the
    # VDD's span, or the person's answer (each flagged with its cell). None =
    # ``source_length`` is the width (an integer), or nothing resolved one yet.
    source_width: int | None = None
    # A non-integer length ("10,2") is a precision, kept as such — never a width.
    source_precision: str | None = None
    # The person's answer to feeds[i].fields[<name>].width, carried by the
    # extractor; the resolver uses it only when the VDD states no span.
    width_answer: int | None = None

    @property
    def byte_width(self) -> int | None:
        """The resolved fixed-width byte width, or None."""
        from codegen.resolve.widths import as_integer

        return self.source_width if self.source_width is not None else as_integer(
            self.source_length)


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
    # M1: the mapping sheet's meta rows (resolved key -> verbatim value);
    # empty on the legacy MAPPING- path (its facts live in FILE_DETAILS).
    meta_rows: dict[str, str] = Field(default_factory=dict)
    # M3: database-table sources name their source table (dominant value of
    # the source band's table column); None on file sources.
    source_table: str | None = None
    # M9.2: what the extractor decided that a reviewer must see — a field the
    # STTM marks "Do Not Map" (field_unmapped:<field>), a schema taken from
    # the FRD / config because the band states none (sttm_unstated:…). Each
    # cites its cell; the resolver carries them to the gate. Empty (and absent
    # from the JSON) on every feed that raised none.
    extraction_flags: list[str] = Field(default_factory=list)

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
    # M1: auxiliary sheets attached verbatim + the layout the values were
    # read through. Both default so pre-M1 contract JSON still loads.
    auxiliary_sheets: list[AuxiliarySheet] = Field(default_factory=list)
    layout: LayoutSummary | None = None

    @model_validator(mode="after")
    def _check_unique_feed_ids(self) -> SttmContract:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for feed in self.feeds:
            (duplicates if feed.feed_id in seen else seen).add(feed.feed_id)
        if duplicates:
            raise ValueError(f"duplicate feed_id(s) in STTM contract: {sorted(duplicates)}")
        return self
