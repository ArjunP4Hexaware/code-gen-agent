"""Gold-layer mapping contract — what the EDH E2E reader (codegen.layouts.edh_e2e) emits.

A gold load is not an ingestion feed: it has no landing file, no stage band and no audit
rows, but it has joins, filters, column expressions and per-region table structures. So it
gets its own contract beside :mod:`codegen.contracts.sttm`, built the same way — frozen
models, ``extra="forbid"``, missing is ``None``.

Every value is one of three things, mirroring the ingestion layouts:

- **filled** — stated by the document (or by the ``edh_e2e`` profile); counted in
  ``GoldFeed.filled`` per role;
- **proposed** — derived (a join assumed on a same-named column, a type where the regions
  disagree, …): the value sits in the contract with ``status="proposed"`` and one
  :class:`GoldProposal` says what was derived and why (printed ``INPUT_NEEDED``);
- **question** — unstated or free text: the value is ``None`` and one :class:`GoldQuestion`
  names the answers key (``feeds[<i>].<role>`` / ``feeds[<i>].columns[<j>].<role>``),
  quoting the cell when it is free text (printed ``QUESTION``).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

Status = Literal["filled", "proposed"]

# The roles the reader counts (docs/acfc/EDH_E2E_READER_RUN.md); a key's last segment.
ROLES = (
    "target_catalog",
    "target_table",
    "target_schema",
    "load_mode",
    "primary_key",
    "scd2_mode",
    "sk_strategy",
    "source_table",
    "source_catalog_schema",
    "target_type",
    "nullable",
    "length",
    "expression",
    "join",
    "filter",
    "region_drift",
    "document_note",
    "rule",
)


class GoldWhere(BaseModel):
    """The document coordinates a value was read from (the extractor's own)."""

    model_config = _MODEL_CONFIG

    file: str
    block_index: int | None = None
    source_row: int | None = None


class GoldQuestion(BaseModel):
    model_config = _MODEL_CONFIG

    key: str  # e.g. feeds[3].columns[7].expression
    role: str  # one of ROLES
    reason: str
    quoted: str | None = None  # the free-text cell, verbatim
    where: GoldWhere | None = None
    candidates: list[str] = Field(default_factory=list)


class GoldAnswer(BaseModel):
    """A question a person answered (``--answers``: an answers.yaml ``gaps:`` entry or
    the filled questions workbook); counted as filled under its role."""

    model_config = _MODEL_CONFIG

    key: str
    role: str
    value: str


class GoldProposal(BaseModel):
    model_config = _MODEL_CONFIG

    key: str
    role: str
    value: str
    basis: str
    where: GoldWhere | None = None


class GoldTarget(BaseModel):
    model_config = _MODEL_CONFIG

    catalog: str | None
    schema_name: str | None = Field(alias="schema")
    table: str


class GoldSource(BaseModel):
    model_config = _MODEL_CONFIG

    database: str | None
    table: str | None
    # the UC "catalog.schema" the profile maps ``database`` to; None = a QUESTION
    catalog_schema: str | None = None


class GoldJoinPair(BaseModel):
    model_config = _MODEL_CONFIG

    left: str
    right: str


class GoldJoin(BaseModel):
    model_config = _MODEL_CONFIG

    type: Literal["INNER", "LEFT"]
    base: str | None  # the FROM table; None when the cell names aliases only
    joined: str | None
    on: list[str] = Field(default_factory=list)  # same-name columns
    pairs: list[GoldJoinPair] = Field(default_factory=list)  # explicit alias.col pairs
    on_assumption: Literal["same_name", "explicit", "none"]
    status: Status
    rows: list[int]  # source_row of every mapping row carrying the cell
    where: GoldWhere


class GoldFilter(BaseModel):
    model_config = _MODEL_CONFIG

    predicate: str  # Spark SQL
    pattern: str  # F1 … F5
    status: Status
    rows: list[int]
    where: GoldWhere


class GoldColumn(BaseModel):
    model_config = _MODEL_CONFIG

    target_attribute: str
    block_index: int
    source_row: int
    source_table: str | None
    source_field: str | None
    description: str | None
    source_format: str | None  # kept as written, a drag-fill suspect included (flagged)
    target_format: str | None = None  # the document's own target type cell, as written
    length: str | None = None  # field_length when it is a length; else from target_format
    length_status: Status | None = None
    target_type: str | None  # from the regional structure: comma stripped, NOT NULL split off
    target_type_status: Status | None = None
    nullable: bool | None = None
    nullable_status: Status | None = None
    expression: str | None = None  # Spark SQL, opening with a provenance comment
    expression_status: Status | None = None
    edit_class: str | None = None
    primary_key: bool = False


class GoldSourceSet(BaseModel):
    """One mapping block of the document: its sources, joins and filters."""

    model_config = _MODEL_CONFIG

    block_index: int
    sources: list[GoldSource]
    joins: list[GoldJoin] = Field(default_factory=list)
    filters: list[GoldFilter] = Field(default_factory=list)
    columns: list[int]  # indexes into GoldFeed.columns


class GoldRegion(BaseModel):
    model_config = _MODEL_CONFIG

    label: str  # the key's label part (before " - LOB")
    key: str  # the full key as the extractor wrote it
    columns: list[str]


class GoldFeed(BaseModel):
    model_config = _MODEL_CONFIG

    # One feed per TARGET TABLE (v2.2: a file whose blocks load different tables
    # yields one feed per table). ``index`` numbers the feeds over the whole
    # manifest, in manifest order then first-block order: keys say feeds[<index>].
    index: int
    manifest_index: int  # the file's position in _manifest.json
    blocks: list[int]  # the file's block_index values this feed carries
    json_file: str
    target: GoldTarget
    refresh_schedule: str | None
    load_mode: str | None  # "full" when stated; an answer's text otherwise
    primary_key: list[str]
    scd2_mode: str | None
    sk_strategy: str | None
    columns: list[GoldColumn]
    source_sets: list[GoldSourceSet]
    regions: list[GoldRegion]
    filled: dict[str, int]  # role -> count of filled values
    proposals: list[GoldProposal] = Field(default_factory=list)
    questions: list[GoldQuestion] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    answered: list[GoldAnswer] = Field(default_factory=list)


class GoldContract(BaseModel):
    model_config = _MODEL_CONFIG

    contract_name: str
    dialect: Literal["edh_e2e"] = "edh_e2e"
    extractor_version: str | None
    feeds: list[GoldFeed] = Field(min_length=1)
