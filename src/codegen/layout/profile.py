"""Layout profile — WHERE things are in a workbook, never WHAT they say.

The one read path of the STTM extractor (M1 onward): every strategy —
the legacy ``MAPPING-`` prefix path, the segmented (CAQH-shaped) family,
the content-driven discovery, and later a model or a person (M2.5) —
produces a :class:`LayoutProfile`, and the extractor reads cell VALUES
only through it. A profile carries column indexes, row numbers and role
names; it never carries a data value, so nothing a model emits can reach
a contract, DDL or IIG cell. ``source`` records who resolved the layout;
``confidence`` is per resolved role (``"<sheet>/<layer>/<role>"`` → 0–1).

Indexes are 1-based (row numbers and column numbers as a spreadsheet
shows them) so a profile is readable next to the workbook.
"""

from __future__ import annotations

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # Python 3.10 (the Databricks Apps floor): the same semantics by hand
    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """A str-valued enum whose str() / format() are the VALUE."""

        __str__ = str.__str__
        __format__ = str.__format__
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

ProfileSource = Literal["synonyms", "model", "user", "cache"]
# "files" / "fields": the two role-bearing sheet layers of a Vendor Data
# Dictionary (M3) — its FILES sheet and its field sheets.
Layer = Literal["source", "rules", "stage", "standard", "files", "fields"]
SheetKind = Literal[
    "mapping", "file_details", "table_details", "layout", "lob_crosswalk",
    "dq_rules", "version", "ignore", "vdd_files", "vdd_fields",
]
# Sheet kinds whose bands carry roles (validated like a mapping sheet).
ROLE_BEARING_KINDS = ("mapping", "vdd_files", "vdd_fields")
# "banner": segments introduced by in-sheet label rows ("Detail Record")
# spanning the source group — the family-A pair-8 shape (SHAPES_FOR_PORT
# §1); an addition to the column|sheet|none vocabulary of the M2.5 brief.
SegmentStrategy = Literal["column", "sheet", "banner", "none"]


class Role(StrEnum):
    """The single role vocabulary. Source-band roles first, then the rules
    band, then the target (stage/standard) bands, then trailing columns."""

    # source band
    ORDINAL = "ordinal"
    FIELD_NAME = "field_name"
    SOURCE_TYPE = "source_type"
    LENGTH = "length"
    FIELD_LENGTH = "field_length"
    START = "start"
    END = "end"
    SEGMENT = "segment"
    REQUIRED = "required"
    NULLABLE = "nullable"
    NULL_CHECK = "null_check"
    MANDATORY = "mandatory"
    PII = "pii"
    KEY = "key"
    DESCRIPTION = "description"
    COMMENTS = "comments"
    SAMPLE_VALUE = "sample_value"
    EXAMPLE_VALUE = "example_value"
    BUSINESS_RULE = "business_rule"
    SOURCE_DATABASE = "source_database"
    SOURCE_SCHEMA = "source_schema"
    SOURCE_TABLE = "source_table"
    SERVER = "server"
    INSCOPE = "inscope"
    LOB = "lob"
    # rules band
    DATA_DEFINITION = "data_definition"
    PRIMARY_KEY = "primary_key"
    CRITICAL = "critical"
    NOT_NULL = "not_null"
    LOAD_RULE = "load_rule"
    DQ_RULES = "dq_rules"
    # target bands (stage / standard)
    WORKSPACE = "workspace"
    CATALOG = "catalog"
    SCHEMA = "schema"
    TABLE = "table"
    COLUMN = "column"
    TARGET_TYPE = "target_type"
    MANDATORY_COLUMN = "mandatory_column"
    CONSTRAINTS = "constraints"
    FIELD_DESCRIPTION = "field_description"
    TABLE_DESCRIPTION = "table_description"
    TRANSFORMATION = "transformation"
    # trailing columns (after the standard band)
    RECYCLE_FLAG = "recycle_flag"
    DQ_MANDATORY = "dq_mandatory"
    # Vendor Data Dictionary field sheets (M3; V1/V2/V3 headers)
    POSITION = "position"
    DATA_TYPE = "data_type"
    PHI = "phi"
    EXAMPLE = "example"
    # Vendor Data Dictionary FILES sheet (M3)
    FILE_PATTERN = "file_pattern"
    TITLE = "title"
    FORMAT = "format"
    DELIMITER = "delimiter"
    CADENCE = "cadence"
    FIELD_SHEET = "field_sheet"
    MULTI_RECORD = "multi_record"
    RECORD_TYPE_FIELD = "record_type_field"
    HEADER_ROW = "header_row"


ROLE_DEFINITIONS: dict[Role, str] = {
    Role.ORDINAL: "row/field ordinal within the sheet or segment",
    Role.FIELD_NAME: "the source field (column) name as the vendor spells it",
    Role.SOURCE_TYPE: "the source data type / format",
    Role.LENGTH: "the source field length",
    Role.FIELD_LENGTH: "fixed-width field length (when distinct from length)",
    Role.START: "fixed-width start position",
    Role.END: "fixed-width end position",
    Role.SEGMENT: "record segment the row belongs to (Header/Detail/Trailer …)",
    Role.REQUIRED: "required / mandatory-or-situational indicator",
    Role.NULLABLE: "nullable indicator",
    Role.NULL_CHECK: "NULL / NOT NULL check",
    Role.MANDATORY: "mandatory field indicator",
    Role.PII: "PII / PHI indicator",
    Role.KEY: "source key indicator",
    Role.DESCRIPTION: "field description",
    Role.COMMENTS: "free-text comments",
    Role.SAMPLE_VALUE: "sample value",
    Role.EXAMPLE_VALUE: "example value",
    Role.BUSINESS_RULE: "business rule text",
    Role.SOURCE_DATABASE: "source database / catalog (database-table sources)",
    Role.SOURCE_SCHEMA: "source schema (database-table sources)",
    Role.SOURCE_TABLE: "source table (database-table sources)",
    Role.SERVER: "source server name",
    Role.INSCOPE: "in-scope-for-implementation flag",
    Role.LOB: "LOB applicability column",
    Role.DATA_DEFINITION: "data definition text",
    Role.PRIMARY_KEY: "primary-key indicator",
    Role.CRITICAL: "critical data element indicator",
    Role.NOT_NULL: "not-null indicator",
    Role.LOAD_RULE: "load rule / transformation instruction",
    Role.DQ_RULES: "data-quality rule text",
    Role.WORKSPACE: "target workspace",
    Role.CATALOG: "target catalog",
    Role.SCHEMA: "target schema",
    Role.TABLE: "target table name",
    Role.COLUMN: "target column name",
    Role.TARGET_TYPE: "target data type",
    Role.MANDATORY_COLUMN: "target mandatory-column indicator",
    Role.CONSTRAINTS: "target constraints",
    Role.FIELD_DESCRIPTION: "target field description",
    Role.TABLE_DESCRIPTION: "target table description",
    Role.TRANSFORMATION: "transformations / data-quality text",
    Role.RECYCLE_FLAG: "per-row recycle flag text",
    Role.DQ_MANDATORY: "mandatory fields included in the DQ check",
    Role.POSITION: "VDD field ordinal within the file / table",
    Role.DATA_TYPE: "VDD data type",
    Role.PHI: "VDD PHI/PII indicator",
    Role.EXAMPLE: "VDD example value",
    Role.FILE_PATTERN: "VDD FILES: file name pattern",
    Role.TITLE: "VDD FILES: file title",
    Role.FORMAT: "VDD FILES: file format",
    Role.DELIMITER: "VDD FILES: delimiter",
    Role.CADENCE: "VDD FILES: delivery cadence",
    Role.FIELD_SHEET: "VDD FILES: the field sheet describing the file",
    Role.MULTI_RECORD: "VDD FILES: multi-record-type flag",
    Role.RECORD_TYPE_FIELD: "VDD FILES: the field that carries the record type",
    Role.HEADER_ROW: "VDD FILES: header-row flag",
}

# Roles a mapping sheet needs before any field can be emitted.
REQUIRED_ROLES: dict[Layer, tuple[Role, ...]] = {
    "source": (Role.FIELD_NAME,),
    "rules": (),
    # M9.1: the schema is REQUIRED in both target bands (a profile without it
    # extracted an empty schema inside ACFC and nothing asked); the catalog
    # stays optional — the catalog chain ends in a config default.
    "stage": (Role.SCHEMA, Role.TABLE, Role.COLUMN, Role.TARGET_TYPE),
    "standard": (Role.SCHEMA, Role.TABLE, Role.COLUMN, Role.TARGET_TYPE),
    "files": (Role.FILE_PATTERN,),
    "fields": (Role.FIELD_NAME, Role.DATA_TYPE, Role.LENGTH),
}


class BandProfile(BaseModel):
    model_config = _MODEL_CONFIG

    layer: Layer
    col_start: int = Field(ge=1)
    col_end: int = Field(ge=1)
    roles: dict[str, int] = Field(default_factory=dict)   # Role value -> column (1-based)
    # Band label text as seen on the band row (None on headerless-band sheets).
    label: str | None = None

    def column(self, role: Role | str) -> int | None:
        return self.roles.get(role.value if isinstance(role, Role) else role)


class MetaRow(BaseModel):
    model_config = _MODEL_CONFIG

    row: int = Field(ge=1)
    col: int = Field(ge=1)          # the LABEL cell; the value sits to its right
    label: str                       # label text as seen
    key: str | None = None           # resolved meta key; None = unrecognised (logged)
    value_col: int | None = None


class SheetProfile(BaseModel):
    model_config = _MODEL_CONFIG

    name: str
    kind: SheetKind
    header_row: int | None = None
    band_row: int | None = None
    bands: list[BandProfile] = Field(default_factory=list)
    meta_rows: list[MetaRow] = Field(default_factory=list)
    segment_strategy: SegmentStrategy = "none"
    segment_column: int | None = None
    # Auxiliary sheets: the header row the signature matched.
    headers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def band(self, layer: Layer) -> BandProfile | None:
        for band in self.bands:
            if band.layer == layer:
                return band
        return None


class UnresolvedRole(BaseModel):
    """A role no strategy could place — carried into the report and, in
    M2.5, into the model prompt / the user dialog."""

    model_config = _MODEL_CONFIG

    sheet: str
    layer: Layer
    role: str
    reason: str
    candidates: list[int] = Field(default_factory=list)   # candidate columns


class LayoutProfile(BaseModel):
    model_config = _MODEL_CONFIG

    fingerprint: str
    sheets: list[SheetProfile]
    confidence: dict[str, float] = Field(default_factory=dict)
    source: ProfileSource
    # Per-role source (same keys as ``confidence``): who placed each role —
    # synonyms, the model, a person, or the cache. A role absent here took
    # the profile-level ``source``.
    role_sources: dict[str, ProfileSource] = Field(default_factory=dict)
    # Which discovery strategy produced the profile: "mapping_prefix" (the
    # legacy MAPPING- path), "segmented_family" (CAQH-shaped), "content"
    # (content-driven discovery); later "model"/"user"/"cache" sources.
    strategy: str
    unresolved: list[UnresolvedRole] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def sheet(self, name: str) -> SheetProfile | None:
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        return None

    @property
    def mapping_sheets(self) -> list[SheetProfile]:
        return [s for s in self.sheets if s.kind == "mapping"]

    @property
    def role_sheets(self) -> list[SheetProfile]:
        return [s for s in self.sheets if s.kind in ROLE_BEARING_KINDS]

    def unresolved_for(self, sheet: str) -> list[UnresolvedRole]:
        return [u for u in self.unresolved if u.sheet == sheet]

    def role_source(self, sheet: str, layer: str, role: Role | str) -> ProfileSource:
        return self.role_sources.get(confidence_key(sheet, layer, role), self.source)


def confidence_key(sheet: str, layer: str, role: Role | str) -> str:
    return f"{sheet}/{layer}/{role.value if isinstance(role, Role) else role}"


def missing_required_roles(profile: LayoutProfile) -> list[str]:
    """``"<sheet>/<layer>/<role>"`` for every REQUIRED role a role-bearing
    sheet's band does not place (M9.1). Independent of ``profile.unresolved``
    — a cached or model-made profile can omit a role AND the note that it is
    missing; such a profile is never cached and never trusted from a cache."""
    missing: list[str] = []
    for sheet in profile.role_sheets:
        for band in sheet.bands:
            for role in REQUIRED_ROLES.get(band.layer, ()):
                if band.column(role) is None:
                    missing.append(confidence_key(sheet.name, band.layer, role))
    return missing


__all__ = [
    "ROLE_BEARING_KINDS",
    "ROLE_DEFINITIONS",
    "REQUIRED_ROLES",
    "BandProfile",
    "Layer",
    "LayoutProfile",
    "MetaRow",
    "ProfileSource",
    "Role",
    "SegmentStrategy",
    "SheetKind",
    "SheetProfile",
    "UnresolvedRole",
    "confidence_key",
    "missing_required_roles",
]
