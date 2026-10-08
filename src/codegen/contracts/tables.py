"""The tables an STTM feed defines (multi-table step 1).

docs/acfc/MULTI_TABLE_DESIGN.md rule 1: tables are the distinct (catalog,
schema, table) triples found in each STTM band — a segment never implies a
table by itself, the TableName cell decides (pair 1: three segments, one
table; pair 4: three segments, three tables). Rule 6: a table's stage_def and
standard_def take catalog and schema from their OWN band.

Everything here is DERIVED from an :class:`~codegen.contracts.sttm.SttmFeed`
(its fields + band references) and never stored in the contract, so every
existing STTM contract JSON stays byte-identical. Catalogs are the LOGICAL
catalogs the STTM states; the environment's ``conventions.catalog_map`` maps
them at resolve time (step 2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from codegen.contracts.frd import RecordSegment
from codegen.contracts.sttm import AuditColumn, SttmFeed, SttmField

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")
_SEGMENT_ORDER: tuple[RecordSegment, ...] = ("Header", "Detail", "Trailer")


class TableModelError(ValueError):
    """The STTM's bands do not describe one standard table per stage table."""


class ColumnDef(BaseModel):
    """One column of a table definition, as its band states it."""

    model_config = _MODEL_CONFIG

    name: str
    datatype: str | None
    mandatory: bool
    primary_key: bool
    source_column: str


class TableDef(BaseModel):
    """One layer's definition of a table: catalog / schema / table from the
    layer's own band, its columns in STTM order (deduplicated by name — the
    segments sharing a table list a shared column once) and audit columns."""

    model_config = _MODEL_CONFIG

    layer: Literal["stage", "standard"]
    catalog: str | None
    schema_name: str
    table: str
    columns: list[ColumnDef] = Field(min_length=1)
    audit_columns: list[AuditColumn]

    @property
    def triple(self) -> tuple[str | None, str, str]:
        return (self.catalog, self.schema_name, self.table)

    @property
    def qualified_name(self) -> str:
        return ".".join(p for p in self.triple if p)

    @property
    def primary_key(self) -> list[str]:
        return [c.name for c in self.columns if c.primary_key]

    @property
    def mandatory(self) -> list[str]:
        return [c.name for c in self.columns if c.mandatory]


class FeedFile(BaseModel):
    """One file the feed receives — one ADLS_DELTA_INGESTION_DETAILS row
    (rule 2; built by :mod:`codegen.resolve.files`)."""

    model_config = _MODEL_CONFIG

    pattern: str            # as stated, the LOB token replaced by this file's LOB
    lob: str | None         # the LOB of an expanded file; None = not a per-LOB file
    template: str           # the pattern exactly as stated
    provenance: str

    @property
    def partition_value(self) -> str | None:
        return self.lob


class SttmTable(BaseModel):
    """A table the feed defines: the segments whose rows land in it, its
    stage definition and (when the Standard band carries any of its rows) its
    standard definition."""

    model_config = _MODEL_CONFIG

    segments: list[RecordSegment]
    stage_def: TableDef
    standard_def: TableDef | None


def _stage_triple(feed: SttmFeed, f: SttmField) -> tuple[str | None, str, str]:
    return (f.stage_catalog or feed.stage.catalog,
            f.stage_schema or feed.stage.schema_name,
            f.stage_table or feed.stage.table)


def _standard_triple(feed: SttmFeed, f: SttmField) -> tuple[str | None, str, str] | None:
    if f.standard_column is None or feed.standard is None:
        return None                                  # the Standard band does not carry it
    return (f.standard_catalog or feed.standard.catalog,
            f.standard_schema or feed.standard.schema_name,
            f.standard_table or feed.standard.table)


def _audit(feed: SttmFeed, segments: list[RecordSegment]) -> list[AuditColumn]:
    """The segments' own audit rows when the segmented extractor stated them,
    else the feed's (the feed-wide set applies)."""
    per_segment = feed.segmented.segment_audit if feed.segmented is not None else {}
    if segments and all(s in per_segment for s in segments):
        seen: dict[str, AuditColumn] = {}
        for segment in segments:
            for column in per_segment[segment]:
                seen.setdefault(column.column, column)
        return list(seen.values())
    return list(feed.audit_columns)


def _columns(fields: list[SttmField], layer: str) -> list[ColumnDef]:
    out: dict[str, ColumnDef] = {}
    for f in fields:
        if layer == "stage":
            column = ColumnDef(name=f.stage_column, datatype=f.stage_datatype,
                               mandatory=f.mandatory, primary_key=f.primary_key,
                               source_column=f.source_column)
        else:
            assert f.standard_column is not None
            column = ColumnDef(
                name=f.standard_column, datatype=f.standard_datatype,
                mandatory=(f.standard_mandatory if f.standard_mandatory is not None
                           else f.mandatory),
                primary_key=(f.standard_primary_key if f.standard_primary_key is not None
                             else f.primary_key),
                source_column=f.source_column)
        out.setdefault(column.name, column)
    return list(out.values())


def feed_tables(feed: SttmFeed) -> list[SttmTable]:
    """The feed's tables, one per distinct STAGE (catalog, schema, table)
    triple in first-seen order; each table's standard definition is the
    Standard band of the same rows (rows whose Standard band is blank are not
    carried). Raises :class:`TableModelError` when one stage table's rows name
    two standard tables."""
    groups: dict[tuple[str | None, str, str], list[SttmField]] = {}
    for f in feed.fields:
        groups.setdefault(_stage_triple(feed, f), []).append(f)
    tables: list[SttmTable] = []
    for (catalog, schema, table), fields in groups.items():
        segments = [s for s in _SEGMENT_ORDER if any(f.record_segment == s for f in fields)]
        audit = _audit(feed, segments)
        stage_def = TableDef(layer="stage", catalog=catalog, schema_name=schema, table=table,
                             columns=_columns(fields, "stage"), audit_columns=audit)
        carried = [f for f in fields if _standard_triple(feed, f) is not None]
        standard_triples = list(dict.fromkeys(_standard_triple(feed, f) for f in carried))
        if len(standard_triples) > 1:
            named = ", ".join(".".join(p for p in t if p) for t in standard_triples if t)
            raise TableModelError(
                f"feed {feed.feed_id!r}: stage table {stage_def.qualified_name} maps to "
                f"{len(standard_triples)} standard tables ({named}); one standard table per "
                "stage table (docs/acfc/MULTI_TABLE_DESIGN.md rule 1)")
        standard_def = None
        if standard_triples:
            s_catalog, s_schema, s_table = standard_triples[0]  # type: ignore[misc]
            standard_def = TableDef(layer="standard", catalog=s_catalog, schema_name=s_schema,
                                    table=s_table, columns=_columns(carried, "standard"),
                                    audit_columns=audit)
        tables.append(SttmTable(segments=segments, stage_def=stage_def,
                                standard_def=standard_def))
    return tables


def detail_table(tables: list[SttmTable]) -> SttmTable:
    """The table the feed's data rows land in: the one holding the Detail
    segment, else the sole table (rule 3: every ADLS row targets it)."""
    detail = [t for t in tables if "Detail" in t.segments]
    if len(detail) == 1:
        return detail[0]
    if len(tables) == 1:
        return tables[0]
    raise TableModelError(
        f"{len(tables)} tables and {len(detail)} hold the Detail segment — the detail table "
        f"is undetermined ({[t.stage_def.qualified_name for t in tables]})")


def split_tables(tables: list[SttmTable]) -> list[SttmTable]:
    """The Header / Trailer tables that are NOT the detail table — non-empty
    exactly when rule 5's header/trailer split row applies."""
    detail = detail_table(tables)
    return [t for t in tables if t is not detail
            and any(s in ("Header", "Trailer") for s in t.segments)]


__all__ = ["ColumnDef", "FeedFile", "SttmTable", "TableDef", "TableModelError", "detail_table",
           "feed_tables", "split_tables"]
