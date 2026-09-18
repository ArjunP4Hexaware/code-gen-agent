"""Content-driven STTM extraction: read a workbook THROUGH a layout profile.

The profile (``codegen.layout``) says where things are; this module copies
what the cells say — verbatim — into the same STTM mapping contract the
resolver already consumes. Nothing here guesses: a role the profile could
not place reads as empty (and the profile's ``unresolved`` list says why),
a row that carries no field name is skipped and logged, a segment spelling
the vocabulary does not know is carried raw and refused loudly at contract
time, and every emitted field records the cell it came from.

Two stages:

- :func:`read_workbook` — profile + workbook → :class:`GenericIR` (meta
  facts, per-sheet field rows with provenance, audit rows, auxiliary
  sheets, skip log). No FRD needed; this is what the layout tests pin.
- :func:`build_generic_contract` — GenericIR + FRD contract → SttmContract
  (pairing by stage-table membership, then by file pattern, then a single
  feed to a single sheet — each recorded as a note).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config, DiscoveryConfig
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.sttm import (
    AuditColumn,
    AuxiliarySheet,
    FieldProvenance,
    LayoutSummary,
    LoadRules,
    RecycleSpec,
    SourceFile,
    SttmContract,
    SttmFeed,
    SttmField,
    TableRef,
)
from codegen.layout.discover import Discovery, normalize, text
from codegen.layout.profile import LayoutProfile, Role, SheetProfile

_AUDIT_DATATYPES = {"string": "String", "timestamp": "Timestamp"}
_CANONICAL_SEGMENTS = ("Header", "Detail", "Trailer")
_WINDOW_DAYS_RE = re.compile(r"(\d+)\s*days?", re.IGNORECASE)
_RECYCLE_FLAG_RE = re.compile(r"\bY\s*\(")


@dataclass(frozen=True)
class FieldRow:
    sheet: str
    row: int
    col: int                          # the field-name cell's column (provenance)
    segment_raw: str | None
    segment: str | None               # canonical Header/Detail/Trailer, else None
    values: dict[str, str | None]     # "<layer>.<role>" -> cell text


@dataclass(frozen=True)
class AuditRow:
    sheet: str
    row: int
    segment: str | None
    column: str
    datatype_raw: str
    table: str | None


@dataclass
class SheetData:
    profile: SheetProfile
    meta: dict[str, str]                       # resolved meta key -> value
    meta_raw: list[tuple[str, str | None]]     # every label:value row as seen
    fields: list[FieldRow] = field(default_factory=list)
    audit: list[AuditRow] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def rows_per_segment(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.fields:
            key = row.segment or row.segment_raw or "-"
            counts[key] = counts.get(key, 0) + 1
        return counts


@dataclass
class GenericIR:
    workbook_name: str
    profile: LayoutProfile
    sheets: list[SheetData]
    auxiliary: list[AuxiliarySheet]
    version: str | None
    diagnostics: list[str]


def layout_summary(profile: LayoutProfile) -> LayoutSummary:
    return LayoutSummary(
        strategy=profile.strategy,
        source=profile.source,
        fingerprint=profile.fingerprint,
        unresolved=[f"{u.sheet}/{u.layer}/{u.role}: {u.reason}" for u in profile.unresolved],
    )


# ----------------------------------------------------------------- reading


def read_workbook(found: Discovery, name: str, config: Config) -> GenericIR:
    disc = config.extractor.discovery
    workbook = found.workbook
    profile = found.profile
    sheets: list[SheetData] = []
    auxiliary: list[AuxiliarySheet] = []
    version: str | None = None
    diagnostics = list(found.diagnostics)
    for sp in profile.sheets:
        ws = workbook[sp.name]
        if sp.kind == "mapping":
            sheets.append(_read_mapping_sheet(ws, sp, disc, config, diagnostics))
        elif sp.kind == "version":
            version = _last_version(ws, sp) or version
        elif sp.kind != "ignore":
            auxiliary.append(_read_auxiliary(ws, sp))
    return GenericIR(workbook_name=name, profile=profile, sheets=sheets, auxiliary=auxiliary,
                     version=version, diagnostics=diagnostics)


def _read_auxiliary(ws, sp: SheetProfile) -> AuxiliarySheet:
    header_row = sp.header_row or 1
    rows = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        cells = [text(c) for c in row[: len(sp.headers)]]
        if any(c is not None for c in cells):
            rows.append(cells + [None] * (len(sp.headers) - len(cells)))
    return AuxiliarySheet(kind=sp.kind, sheet=sp.name, headers=list(sp.headers), rows=rows)


def _last_version(ws, sp: SheetProfile) -> str | None:
    header_row = sp.header_row
    if header_row is None:
        return None
    headers = [normalize(c) for c in next(ws.iter_rows(min_row=header_row, max_row=header_row,
                                                        values_only=True))]
    if "version" not in headers:
        return None
    col = headers.index("version")
    versions = [text(r[col]) for r in ws.iter_rows(min_row=header_row + 1, values_only=True)
                if col < len(r) and text(r[col]) is not None]
    return versions[-1] if versions else None


def _segment_lookup(disc: DiscoveryConfig) -> dict[str, str]:
    return {normalize(s): canonical for canonical, spellings in disc.segment_synonyms.items()
            for s in spellings}


def _read_mapping_sheet(ws, sp: SheetProfile, disc: DiscoveryConfig, config: Config,
                        diagnostics: list[str]) -> SheetData:
    header_row = sp.header_row or 1
    source = sp.band("source")
    stage = sp.band("stage")
    field_col = source.column(Role.FIELD_NAME) if source is not None else None
    stage_column_col = stage.column(Role.COLUMN) if stage is not None else None
    stage_table_col = stage.column(Role.TABLE) if stage is not None else None
    stage_type_col = stage.column(Role.TARGET_TYPE) if stage is not None else None
    segments = _segment_lookup(disc)
    audit_markers = {normalize(m) for m in config.extractor.audit_source_markers}

    meta: dict[str, str] = {}
    meta_raw: list[tuple[str, str | None]] = []
    for entry in sp.meta_rows:
        value = None
        if entry.value_col is not None:
            value = text(ws.cell(row=entry.row, column=entry.value_col).value)
        meta_raw.append((entry.label, value))
        if entry.key is not None and value is not None and entry.key not in meta:
            meta[entry.key] = value

    data = SheetData(profile=sp, meta=meta, meta_raw=meta_raw)
    current_segment_raw: str | None = None
    if sp.segment_strategy == "banner" and sp.band_row is not None and source is not None:
        current_segment_raw = text(ws.cell(row=sp.band_row, column=source.col_start).value)
    elif sp.segment_strategy == "sheet":
        current_segment_raw = sp.name

    for row_number, row in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True),
                                     start=header_row + 1):
        cells = [text(c) for c in row]
        if all(c is None for c in cells):
            continue
        filled = [(i + 1, c) for i, c in enumerate(cells) if c is not None]
        # In-sheet segment banner ("Detail Record"): one text cell inside the
        # source band, nothing on the target side.
        if (sp.segment_strategy == "banner" and len(filled) == 1 and source is not None
                and source.col_start <= filled[0][0] <= source.col_end):
            current_segment_raw = filled[0][1]
            data.skipped.append(f"row {row_number}: segment banner {filled[0][1]!r}")
            continue
        field_name = _cell(cells, field_col)
        stage_column = _cell(cells, stage_column_col)
        source_values = [c for i, c in filled if source is not None
                         and source.col_start <= i <= source.col_end]
        if sp.segment_strategy == "column" and sp.segment_column is not None:
            # An audit row leaves its Segment cell empty: it belongs to the
            # segment block it sits in (the last stated segment).
            stated = _cell(cells, sp.segment_column)
            if stated is not None:
                current_segment_raw = stated
            segment_raw = stated if stated is not None else current_segment_raw
        else:
            segment_raw = current_segment_raw
        is_audit = (field_name is not None and normalize(field_name) in audit_markers) or (
            field_name is None and stage_column is not None
            and all(normalize(v) in audit_markers for v in source_values))
        if is_audit:
            if stage_column is None:
                data.skipped.append(f"row {row_number}: audit marker without a stage column; "
                                    "skipped")
                continue
            data.audit.append(AuditRow(
                sheet=sp.name, row=row_number,
                segment=segments.get(normalize(segment_raw)) if segment_raw else None,
                column=stage_column, datatype_raw=_cell(cells, stage_type_col) or "",
                table=_cell(cells, stage_table_col)))
            continue
        if field_name is None:
            reason = ("field_name role unresolved" if field_col is None
                      else "no field name in the source band")
            data.skipped.append(f"row {row_number}: {reason}; skipped")
            continue
        values: dict[str, str | None] = {}
        for band in sp.bands:
            for role, col in band.roles.items():
                values[f"{band.layer}.{role}"] = _cell(cells, col)
        data.fields.append(FieldRow(
            sheet=sp.name, row=row_number, col=field_col or 0,
            segment_raw=segment_raw,
            segment=segments.get(normalize(segment_raw)) if segment_raw else None,
            values=values))
    for entry in data.skipped:
        diagnostics.append(f"sheet {sp.name!r}: {entry}")
    return data


def _cell(cells: list[str | None], col: int | None) -> str | None:
    if col is None or col < 1 or col > len(cells):
        return None
    return cells[col - 1]


# --------------------------------------------------------------- contract


class GenericExtractionError(ValueError):
    """The generic IR cannot be paired/emitted as a contract; names the spot."""


def _yes(value: str | None, disc: DiscoveryConfig) -> bool:
    return normalize(value) in {normalize(v) for v in disc.yes_values}


def _first(row: FieldRow, *keys: str) -> str | None:
    for key in keys:
        value = row.values.get(key)
        if value is not None:
            return value
    return None


def _dominant(values: list[str | None]) -> str | None:
    counts: dict[str, int] = {}
    for value in values:
        if value is not None:
            counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get) if counts else None


def _canonical_file_name(name: str) -> str:
    return name.strip().lower().replace("ccyy", "yyyy")


def _match_feed(sheet: SheetData, stage_table: str | None, frd: FrdContract,
                ir: GenericIR, notes: list[str]) -> FrdFeed:
    if stage_table is not None:
        matches = [f for f in frd.feeds if stage_table in f.stage_target.tables]
        if len(matches) == 1:
            return matches[0]
    patterns = _sheet_file_patterns(sheet, ir)
    canonical = {_canonical_file_name(p) for p in patterns}
    matches = [f for f in frd.feeds
               if canonical & {_canonical_file_name(p) for p in f.file_name_patterns}]
    if len(matches) == 1:
        notes.append(f"sheet {sheet.profile.name!r} paired to FRD feed "
                     f"{matches[0].feed_name!r} by file pattern")
        return matches[0]
    if len(frd.feeds) == 1 and len(ir.sheets) == 1:
        notes.append(f"sheet {sheet.profile.name!r} paired to the FRD's only feed "
                     f"{frd.feeds[0].feed_name!r} (single sheet, single feed)")
        return frd.feeds[0]
    raise GenericExtractionError(
        f"sheet {sheet.profile.name!r} (stage table {stage_table!r}, file patterns "
        f"{sorted(patterns)}) matches {len(matches)} FRD feeds "
        f"{[f.feed_name for f in frd.feeds]}; expected exactly one by stage table or "
        "file pattern"
    )


def _sheet_file_patterns(sheet: SheetData, ir: GenericIR) -> list[str]:
    patterns: list[str] = []
    for key in ("file_names", "file_name_example"):
        value = sheet.meta.get(key)
        if value:
            patterns += [p.strip() for p in re.split(r"[\n;,]+", value) if p.strip()]
    for aux in ir.auxiliary:
        if aux.kind != "file_details":
            continue
        headers = [normalize(h) for h in aux.headers]
        col = next((i for i, h in enumerate(headers) if h in ("filename", "file name",
                                                              "inbound file name")), None)
        if col is not None:
            patterns += [r[col] for r in aux.rows if col < len(r) and r[col]]
    return patterns


def _file_details_row(feed: FrdFeed, ir: GenericIR) -> dict[str, str] | None:
    canonical = {_canonical_file_name(p) for p in feed.file_name_patterns}
    for aux in ir.auxiliary:
        if aux.kind != "file_details":
            continue
        headers = [normalize(h) for h in aux.headers]
        for row in aux.rows:
            entry = {h: v for h, v in zip(headers, row, strict=False) if v}
            name = entry.get("filename") or entry.get("file name") or entry.get("inbound file name")
            if name and _canonical_file_name(name) in canonical:
                return entry
    return None


def _recycle(sheet: SheetData, config: Config, disc: DiscoveryConfig) -> RecycleSpec | None:
    flagged = [(row, row.values.get("rules.recycle_flag")) for row in sheet.fields
               if row.values.get("rules.recycle_flag")]
    if not flagged:
        return None
    row, raw = flagged[0]
    match = _RECYCLE_FLAG_RE.search(raw or "")
    if match is None:
        return None
    validation = raw[match.end():].strip().rstrip(")").rstrip()
    if not validation:
        return None
    window = _WINDOW_DAYS_RE.search(raw)
    days = int(window.group(1)) if window else config.defaults.recycle_window_days
    return RecycleSpec(
        applies_to=_first(row, "source.field_name") or "",
        enabled=True,
        validation=validation,
        on_match=config.extractor.recycle_on_match.format(window_days=days),
        on_no_match=config.extractor.recycle_on_no_match.format(window_days=days),
        recycle_window_days=days,
    )


def build_generic_contract(ir: GenericIR, frd: FrdContract, config: Config, *,
                           contract_name: str | None = None,
                           generated_date: str) -> SttmContract:
    disc = config.extractor.discovery
    notes: list[str] = []
    feeds: list[SttmFeed] = []
    for sheet in ir.sheets:
        feeds.append(_build_feed(sheet, ir, frd, config, disc, notes))
    return SttmContract(
        contract_name=contract_name or f"STTM mapping contract extracted from {ir.workbook_name}",
        generated_from_workbook=ir.workbook_name,
        sttm_version=ir.version or "unversioned (no version sheet recognised)",
        generated_date=generated_date,
        notes=[
            "Extracted deterministically by `codegen extract-sttm` (content-driven layout, "
            f"strategy {ir.profile.strategy!r}, source {ir.profile.source!r}) from the "
            f"workbook named above, paired with FRD contract '{frd.contract_name}'.",
            "Column facts are verbatim workbook values read through the layout profile; "
            "every field records the cell it came from.",
            *notes,
        ],
        feeds=feeds,
        auxiliary_sheets=ir.auxiliary,
        layout=layout_summary(ir.profile),
    )


def _build_feed(sheet: SheetData, ir: GenericIR, frd: FrdContract, config: Config,
                disc: DiscoveryConfig, notes: list[str]) -> SttmFeed:
    from codegen.resolve.resolver import _FORMAT_DELIMITERS, normalize_feed_name

    sp = sheet.profile
    name = sp.name
    if not sheet.fields:
        raise GenericExtractionError(
            f"sheet {name!r}: no field rows could be read "
            f"(skipped: {sheet.skipped[:3]}{'…' if len(sheet.skipped) > 3 else ''}; "
            f"unresolved: {[u.role for u in ir.profile.unresolved_for(name)]})")
    missing = [role for role in ("table", "column", "target_type")
               if all(r.values.get(f"stage.{role}") is None for r in sheet.fields)]
    if missing:
        raise GenericExtractionError(
            f"sheet {name!r}: the stage band has no values for {missing} (roles unresolved or "
            "empty) — a contract needs stage table, column and data type per field")
    stage_schema = _dominant([r.values.get("stage.schema") for r in sheet.fields])
    stage_table = _dominant([r.values.get("stage.table") for r in sheet.fields])
    stage_catalog = _dominant([r.values.get("stage.catalog") for r in sheet.fields])
    if stage_schema is None or stage_table is None:
        raise GenericExtractionError(f"sheet {name!r}: stage schema/table cells are empty")
    feed = _match_feed(sheet, stage_table, frd, ir, notes)
    feed_id = config.feed_aliases.get(feed.feed_name) or normalize_feed_name(feed.feed_name)

    has_standard = any(r.values.get("standard.column") for r in sheet.fields)
    standard_schema = _dominant([r.values.get("standard.schema") for r in sheet.fields])
    standard_table = _dominant([r.values.get("standard.table") for r in sheet.fields])
    standard_catalog = _dominant([r.values.get("standard.catalog") for r in sheet.fields])

    segmented = any(r.segment_raw is not None for r in sheet.fields)
    if segmented:
        unknown = sorted({r.segment_raw for r in sheet.fields if r.segment is None} - {None})
        if unknown:
            raise GenericExtractionError(
                f"sheet {name!r}: segment spelling(s) {unknown} are outside the "
                f"{'/'.join(_CANONICAL_SEGMENTS)} vocabulary (extractor.discovery."
                "segment_synonyms); the contract dialect cannot carry them")

    fields: list[SttmField] = []
    for row in sheet.fields:
        field_name = _first(row, "source.field_name")
        assert field_name is not None
        stage_column = _first(row, "stage.column")
        stage_type = _first(row, "stage.target_type")
        if stage_column is None or stage_type is None:
            raise GenericExtractionError(
                f"sheet {name!r} row {row.row}: field {field_name!r} has no stage "
                f"column/data type (column={stage_column!r}, type={stage_type!r})")
        # A NULLABLE column says "NULL"/"nullable"/"yes" for nullable and
        # "NOT NULL"/"no" for required — the null-ish spellings of no_values
        # (meant for yes/no columns) do not apply to it.
        nullable_text = normalize(_first(row, "source.nullable"))
        no_words = {normalize(v) for v in disc.no_values if "null" not in normalize(v)}
        not_null = (_yes(_first(row, "rules.not_null", "source.not_null"), disc)
                    or normalize(_first(row, "source.null_check")).startswith("not null")
                    or nullable_text.startswith("not null")
                    or (bool(nullable_text) and nullable_text in no_words))
        mandatory = _yes(_first(row, "source.required", "source.mandatory",
                                "rules.required", "stage.mandatory_column"), disc)
        pii = _yes(_first(row, "source.pii", "rules.pii"), disc)
        rule_parts = [v for v in (_first(row, "rules.load_rule", "source.load_rule"),
                                  _first(row, "stage.transformation"),
                                  _first(row, "source.business_rule")) if v]
        value_spec = "; ".join(rule_parts) if rule_parts else _first(row, "source.comments")
        fields.append(SttmField(
            source_column=field_name,
            description=_first(row, "source.description", "rules.data_definition",
                               "source.comments", "stage.field_description"),
            sample_value=_first(row, "source.sample_value", "source.example_value"),
            source_datatype=_first(row, "source.source_type") or "unstated",
            nullable=not (not_null or mandatory),
            phi=pii,
            mandatory=mandatory,
            stage_column=stage_column,
            stage_datatype=stage_type,
            standard_column=_first(row, "standard.column") if has_standard else None,
            standard_datatype=_first(row, "standard.target_type") if has_standard else None,
            value_spec=value_spec,
            source_length=_first(row, "source.length", "source.field_length"),
            source_start=_first(row, "source.start"),
            source_end=_first(row, "source.end"),
            record_segment=row.segment if segmented else None,  # type: ignore[arg-type]
            stage_table=(_first(row, "stage.table") or stage_table) if segmented else None,
            standard_table=(_first(row, "standard.table") if segmented and has_standard
                            else None),
            provenance=FieldProvenance(
                sheet=row.sheet, row=row.row, col=row.col,
                source=ir.profile.role_source(row.sheet, "source", "field_name")),
        ))

    audit: list[AuditColumn] = []
    seen: set[str] = set()
    for entry in sheet.audit:
        datatype = _AUDIT_DATATYPES.get(normalize(entry.datatype_raw))
        if datatype is None:
            raise GenericExtractionError(
                f"sheet {name!r} row {entry.row}: audit column {entry.column!r} has datatype "
                f"{entry.datatype_raw!r}; expected one of {sorted(_AUDIT_DATATYPES)}")
        if entry.column not in seen:
            seen.add(entry.column)
            audit.append(AuditColumn(column=entry.column, datatype=datatype))  # type: ignore[arg-type]
    if not audit:
        raise GenericExtractionError(
            f"sheet {name!r}: no audit rows (rows whose source-side field name is an audit "
            f"marker {config.extractor.audit_source_markers} with a stage column) — the "
            "contract requires at least one audit column; add them to the STTM")

    details = _file_details_row(feed, ir)
    patterns = _sheet_file_patterns(sheet, ir)
    frd_canonical = {_canonical_file_name(p): p for p in feed.file_name_patterns}
    name_pattern = next((p for p in patterns if _canonical_file_name(p) in frd_canonical), None)
    if name_pattern is None:
        name_pattern = feed.file_name_patterns[0]
        notes.append(f"feed {feed.feed_name!r}: file pattern taken from the FRD "
                     f"({name_pattern!r}); the workbook names none that matches")
    delimiter = feed.delimiter or sheet.meta.get("delimiter") or \
        _FORMAT_DELIMITERS.get(feed.file_format.lower())
    frequency = (details or {}).get("frequency") or sheet.meta.get("frequency") or feed.frequency
    source_system = (details or {}).get("vendor") or sheet.meta.get("file_generator") \
        or feed.source_system

    try:
        return SttmFeed(
            feed_id=feed_id,
            source_system=source_system,
            mapping_sheet=name,
            source_file=SourceFile(name_pattern=name_pattern, format=feed.file_format,
                                   delimiter=delimiter, frequency=frequency),
            stage=TableRef(schema=stage_schema, table=stage_table, catalog=stage_catalog),
            standard=(TableRef(schema=standard_schema or "", table=standard_table or "",
                               catalog=standard_catalog) if has_standard else None),
            load_rules=LoadRules(
                not_null_columns=[f.source_column for f in fields if not f.nullable],
                mandatory_columns=[f.source_column for f in fields if f.mandatory],
                phi_columns=[f.source_column for f in fields if f.phi],
                recycle=_recycle(sheet, config, disc),
            ),
            audit_columns=audit,
            field_count=len(fields),
            fields=fields,
            meta_rows=dict(sheet.meta),
            source_table=_dominant([r.values.get("source.source_table") for r in sheet.fields]),
        )
    except ValueError as exc:
        raise GenericExtractionError(
            f"feed {feed.feed_name!r}: extracted feed fails contract validation:\n{exc}"
        ) from exc


def extract_generic_contract(found: Discovery, workbook_path: Path, frd: FrdContract,
                             config: Config, *, contract_name: str | None,
                             generated_date: str) -> SttmContract:
    ir = read_workbook(found, workbook_path.name, config)
    return build_generic_contract(ir, frd, config, contract_name=contract_name,
                                  generated_date=generated_date)


__all__ = [
    "AuditRow",
    "FieldRow",
    "GenericExtractionError",
    "GenericIR",
    "SheetData",
    "build_generic_contract",
    "extract_generic_contract",
    "layout_summary",
    "read_workbook",
]
