"""ResolvedFeedSpec — the single object every template consumes.

Built by ``codegen.resolve`` from one FRD feed joined with one STTM feed.
Nothing downstream of the resolver ever touches the raw contracts, and every
value here is already reconciled: the resolver raises a loud
``ContractMismatchError`` rather than construct a spec from disagreeing
inputs. Fields are fully materialized (no lazy lookups) so template
rendering is byte-stable given identical contracts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from codegen.contracts.frd import LoadStrategy, RecordSegment
from codegen.contracts.sttm import AuditColumn, RecycleSpec, SttmField

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class ResolvedTable(BaseModel):
    """A fully qualified physical table the generated code reads or writes."""

    model_config = _MODEL_CONFIG

    catalog: str | None
    schema_name: str
    table: str
    role: Literal["stage", "standard", "errors", "recycle", "processed_files"]

    @property
    def qualified_name(self) -> str:
        parts = [self.catalog, self.schema_name, self.table]
        return ".".join(p for p in parts if p is not None)


class SegmentSpec(BaseModel):
    """One record segment (Header/Detail/Trailer) → its stage table + fields.

    Flat feeds resolve to a single segment named ``Detail`` covering every
    field, so templates iterate segments uniformly instead of branching on
    dialect.
    """

    model_config = _MODEL_CONFIG

    segment: RecordSegment
    stage_table: ResolvedTable
    fields: list[SttmField] = Field(min_length=1)


class ResolvedRecycle(BaseModel):
    """Reconciled recycle rule: structured STTM spec + the FRD text it must agree with."""

    model_config = _MODEL_CONFIG

    spec: RecycleSpec
    frd_rule_text: str | None
    recycle_table: ResolvedTable
    # Parsed from spec.validation at resolve time (e.g. reference table
    # PR_STD.FACETS.CMC_SBSB_SUBSC, id column SBSB_ID, filter GRGR_CK = 31).
    reference_table: str
    reference_id_column: str
    reference_filter: str | None


class ResolvedFeedSpec(BaseModel):
    """Everything Layer 1 needs to generate one feed's pipeline."""

    model_config = _MODEL_CONFIG

    # Identity
    feed_id: str
    feed_slug: str  # python/table-identifier-safe form of feed_id
    feed_name: str  # the FRD's display name
    source_system: str
    lobs: list[str] = Field(min_length=1)
    # FRD business-domain placement, carried through for EDO-standard naming
    # (workflow/notebook name components). None on contracts predating this.
    domain: str | None = None
    sub_domain: str | None = None

    # Source file shape (delimiter already reconciled between contracts)
    file_name_patterns: list[str] = Field(min_length=1)
    file_format: str
    delimiter: str
    landing_location: str | None

    # Segments: exactly one entry ("Detail") for flat feeds
    segments: list[SegmentSpec] = Field(min_length=1)

    # Targets
    stage_load_strategy: LoadStrategy
    standard_table: ResolvedTable | None
    standard_load_strategy: LoadStrategy | None
    errors_table: ResolvedTable
    processed_files_table: ResolvedTable

    # Load semantics
    natural_key_columns: list[str] = Field(min_length=1)
    not_null_columns: list[str]
    phi_columns: list[str]
    audit_columns: list[AuditColumn] = Field(min_length=1)
    recycle: ResolvedRecycle | None

    # Rule compilation input (free text, verbatim from the FRD)
    validation_rules: list[str]
    load_windows_sla: list[str]
    frequency: str | None

    # Provenance for generated-file banners: name + sha256 of each contract
    frd_contract_name: str
    frd_contract_sha256: str
    sttm_contract_name: str
    sttm_contract_sha256: str
    sttm_is_synthetic: bool

    @property
    def is_segmented(self) -> bool:
        return len(self.segments) > 1

    @property
    def detail_segment(self) -> SegmentSpec:
        """The segment carrying the feed's data rows (the only one on flat feeds)."""
        for segment in self.segments:
            if segment.segment == "Detail":
                return segment
        raise ValueError(f"feed '{self.feed_id}' has no Detail segment")
