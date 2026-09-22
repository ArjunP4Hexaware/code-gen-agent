"""Segmented (Header/Detail/Trailer) STTM workbook extraction — v2 dialect.

Corrected 2026-09-01 against the CAQH FRD (1005034) + STTM read verbatim:

- **Segments are TABLES, both layers.** FRD acceptance criterion 2: "Header,
  Detail, Trailer data should be mapped to respective HDR, DTL and TRL
  tables." Every data row becomes a field carrying ``record_segment`` +
  ``stage_table`` (+ ``standard_table`` when the standard layer is scoped) —
  the segmented dialect the resolver already consumes.
- **Both layers are scoped by Load Strategy, never inferred from the Target
  Schema block.** FRD Structural Metadata: "Load Strategy STG: Truncate and
  Load; Load Strategy STD: Append". When the FRD's standard table list is
  empty (its Target Schema block names stage targets only), the STD catalog/
  schema/tables come from the STTM's second target column group, with a
  cited provenance note.
- **Record identification is DERIVED from the STTM, not assumed.** Trailer =
  record whose first field equals the stated static marker (the STTM Trailer
  "Record Type" comment: "Contains the value ******"); header = first
  record; detail = all others. The FAQ ``record_type_discriminators`` is
  strictly an OVERRIDE (status ``confirmed`` only).
- **No natural-key requirement.** FRD Technical Metadata: Business/Primary/
  Unique Key all None; STG truncate + STD append → no MERGE exists. Empty
  STTM Mandatory/PK columns are consistent with the FRD — recorded as a
  cited provenance note, not an unknown.
- Every provenance note and review item MUST cite the exact FRD field or
  STTM cell it rests on — a note that cannot cite its evidence is a bug.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from codegen.config import Config, SegmentedExtractorConfig
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.sttm import (
    AuditColumn,
    FieldProvenance,
    LayoutSummary,
    LoadRules,
    ProvenanceNote,
    RecordIdentification,
    RecycleSpec,
    SegmentedExtraction,
    SourceFile,
    SttmContract,
    SttmFeed,
    SttmField,
    TableRef,
)
from codegen.extract.workbook import SegmentedWorkbookError, WorkbookParseError, _norm, _text
from codegen.faq import load_faq
from codegen.layout.profile import LayoutProfile, SheetProfile
from codegen.resolve.resolver import _FORMAT_DELIMITERS, normalize_feed_name

_AUDIT_DATATYPES = {"string": "String", "timestamp": "Timestamp"}
_YES_VALUES = {"yes", "y", "true"}
_DELIMITER_RE = re.compile(r"delimited\s*(\S)")
# The STTM trailer "Record Type" comment states the static marker, e.g.
# "Static text identifying the record as the trailer record.\nContains the
# value ******" — the derivation quotes this cell verbatim as its citation.
_TRAILER_MARKER_RE = re.compile(r"contains the value\s+(\S+)", re.IGNORECASE)
# FRD-driven AS-IS switch evidence (e.g. rule: "Process should load the files
# AS-IS ... and should not perform any data transformation"). The character
# class covers space, ASCII hyphen, and the non-breaking hyphen the real FRD
# uses.
_AS_IS_RE = re.compile(r"\bAS[\s\-‑]?IS\b", re.IGNORECASE)
_MEMBER_VALIDATION_RE = re.compile(
    r"validation.+against\s+facets|member\s*id.+facets", re.IGNORECASE)
_WINDOW_DAYS_RE = re.compile(r"(\d+)\s*days?", re.IGNORECASE)


@dataclass(frozen=True)
class _SegRow:
    row_number: int
    segment: str | None  # canonical Header/Detail/Trailer; None = audit row
    values: tuple


@dataclass(frozen=True)
class _Blocks:
    """Resolved column indexes for the three bands."""

    source: dict[str, int]
    stage: dict[str, int]
    standard: dict[str, int] | None


def _canonical_file_name(name: str) -> str:
    return name.strip().lower().replace("ccyy", "yyyy")


def _find_mapping_sheet(workbook, seg_config: SegmentedExtractorConfig,
                        band_vocabulary: set[str], name: str):
    """(worksheet, band_row_index, rows) — the one sheet matching the family
    signature (band row + metadata block above and/or Segment header below)."""
    candidates = []
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        for index, row in enumerate(rows):
            found = {v for v in (_norm(c) for c in row) if v in band_vocabulary}
            if len(found) < 2:
                continue
            metadata_above = any(
                r[0] is not None and len(r) > 1 and r[1] is not None
                for r in rows[:index]
            )
            header_row = rows[index + 1] if index + 1 < len(rows) else ()
            segment_header = any(_norm(c).startswith("segment") for c in header_row)
            if metadata_above or segment_header:
                candidates.append((ws, index, rows))
            break
    if not candidates:
        raise WorkbookParseError(
            f"{name}: no sheet matches the segmented layout family "
            "(band row + metadata block / Segment header)"
        )
    if len(candidates) > 1:
        raise WorkbookParseError(
            f"{name}: {len(candidates)} sheets match the segmented layout family "
            f"({[c[0].title for c in candidates]}); expected exactly one mapping sheet"
        )
    return candidates[0]


def _parse_metadata_block(rows, band_row: int, seg_config: SegmentedExtractorConfig,
                          sheet: str) -> dict[str, str]:
    wanted = {_norm(label): logical for logical, label in seg_config.metadata_keys.items()}
    facts: dict[str, str] = {}
    for row in rows[:band_row]:
        if not row or row[0] is None:
            continue
        key = _norm(row[0])
        value = _text(row[1]) if len(row) > 1 else None
        if key in wanted and value is not None:
            logical = wanted[key]
            if logical in facts:
                raise WorkbookParseError(
                    f"{sheet}: metadata key {row[0]!r} appears more than once")
            facts[logical] = value
    missing = {"files", "generator", "file_type"} - set(facts)
    if missing:
        raise WorkbookParseError(
            f"{sheet}: metadata block is missing key(s) "
            f"{sorted(seg_config.metadata_keys[m] for m in missing)}"
        )
    return facts


def _resolve_blocks(header: list, band_starts: dict[str, int], max_col: int,
                    seg_config: SegmentedExtractorConfig, sheet: str) -> _Blocks:
    source_start = band_starts["source"]
    stage_start = band_starts["stage"]
    standard_start = band_starts.get("standard")

    source_synonyms = {
        logical: {_norm(s) for s in names}
        for logical, names in seg_config.source_headers.items()
    }
    source: dict[str, int] = {}
    for index in range(source_start, stage_start):
        text = _norm(header[index]) if index < len(header) else ""
        if not text:
            continue
        matches = [
            logical for logical, names in source_synonyms.items()
            if text in names or any(text.startswith(n.split(" (")[0]) for n in names)
        ]
        if not matches:
            raise WorkbookParseError(
                f"{sheet}: unrecognized source-block header {header[index]!r} "
                f"(column {index + 1}); known: {seg_config.source_headers}"
            )
        source.setdefault(matches[0], index)
    required = {"field_name", "datatype", "segment"} - set(source)
    if required:
        raise WorkbookParseError(
            f"{sheet}: source block is missing required column(s) {sorted(required)}")

    def _table_block(start: int, end: int, band: str) -> dict[str, int]:
        known = {_norm(h): h for h in seg_config.table_headers}
        resolved: dict[str, int] = {}
        for index in range(start, end):
            text = _norm(header[index]) if index < len(header) else ""
            if not text:
                continue
            if text not in known:
                raise WorkbookParseError(
                    f"{sheet}: unrecognized {band}-block header {header[index]!r} "
                    f"(column {index + 1}); expected one of {seg_config.table_headers}"
                )
            resolved.setdefault(text, index)
        missing = {"schema", "tablename", "columnname", "datatype"} - set(resolved)
        if missing:
            raise WorkbookParseError(
                f"{sheet}: {band} block is missing column(s) {sorted(missing)}")
        return resolved

    stage = _table_block(stage_start, standard_start or (max_col + 1), "stage")
    standard = (
        _table_block(standard_start, max_col + 1, "standard")
        if standard_start is not None
        else None
    )
    return _Blocks(source=source, stage=stage, standard=standard)


def _segment_rows(rows, header_row: int, blocks: _Blocks,
                  seg_config: SegmentedExtractorConfig, sheet: str) -> list[_SegRow]:
    canonical = dict(seg_config.segment_names)
    out: list[_SegRow] = []
    for row_number, row in enumerate(rows[header_row + 1:], start=header_row + 2):
        if all(_text(cell) is None for cell in row):
            continue
        segment_raw = _cell(row, blocks.source["segment"])
        field_name = _cell(row, blocks.source["field_name"])
        segment = canonical.get(_norm(segment_raw)) if segment_raw is not None else None
        if segment_raw is not None and segment is None:
            raise WorkbookParseError(
                f"{sheet} row {row_number}: unrecognized Segment value {segment_raw!r} "
                f"(known: {sorted(seg_config.segment_names.values())})"
            )
        if segment is None and field_name is not None:
            raise WorkbookParseError(
                f"{sheet} row {row_number}: field {field_name!r} carries no Segment value"
            )
        out.append(_SegRow(row_number=row_number, segment=segment, values=row))
    if not out:
        raise WorkbookParseError(f"{sheet}: no data rows below the header row")
    return out


def _cell(row: tuple, index: int | None) -> str | None:
    if index is None or index >= len(row):
        return None
    return _text(row[index])


def _is_yes(value: str | None) -> bool:
    return _norm(value) in _YES_VALUES


def _derive_identification(seg_rows: list[_SegRow], blocks: _Blocks,
                           sheet: str) -> RecordIdentification:
    """Trailer marker from the STTM's own statement; header/detail positional.
    The citation is the verbatim STTM comment cell the derivation rests on."""
    trailer_rows = [r for r in seg_rows if r.segment == "Trailer"]
    if not trailer_rows:
        raise WorkbookParseError(f"{sheet}: no Trailer-segment rows found")
    first = trailer_rows[0]
    comment = _cell(first.values, blocks.source.get("comments")) or ""
    match = _TRAILER_MARKER_RE.search(comment)
    if match is None:
        raise WorkbookParseError(
            f"{sheet} row {first.row_number}: the Trailer record-type comment does "
            f"not state a static marker value (comment: {comment!r}); record "
            "identification cannot be derived — declare a confirmed "
            "record_type_discriminators override in the feed's FAQ instead"
        )
    return RecordIdentification(
        method="derived_from_sttm",
        trailer_marker=match.group(1),
        header_rule="first record of the file",
        detail_rule=(
            f"every record that is neither the first record nor a record whose "
            f"first field equals {match.group(1)!r}"
        ),
        citation=(
            f"STTM {sheet!r} row {first.row_number}, "
            f"{_cell(first.values, blocks.source.get('field_name'))!r} Comments: "
            f"{comment!r}"
        ),
    )


def _blocks_from_profile(sheet_profile: SheetProfile) -> _Blocks:
    """The legacy block dicts (logical name -> 0-based column) read back from
    the layout profile the segmented_family strategy produced."""
    from codegen.layout.discover import SEGMENTED_SOURCE_ROLES, SEGMENTED_TABLE_ROLES

    def _band(layer: str, roles: dict) -> dict[str, int] | None:
        band = sheet_profile.band(layer)  # type: ignore[arg-type]
        if band is None:
            return None
        return {legacy: band.roles[role.value] - 1 for legacy, role in roles.items()
                if role.value in band.roles}

    source = _band("source", SEGMENTED_SOURCE_ROLES)
    stage = _band("stage", SEGMENTED_TABLE_ROLES)
    assert source is not None and stage is not None
    return _Blocks(source=source, stage=stage, standard=_band("standard", SEGMENTED_TABLE_ROLES))


def extract_segmented_contract(
    workbook_path: Path,
    frd: FrdContract,
    config: Config,
    *,
    refusal_evidence: str,
    contract_name: str | None = None,
    generated_date: str | None = None,
    profile: LayoutProfile | None = None,
    workbook=None,
) -> SttmContract:
    """Parse a segmented workbook + its FRD feed into the STTM contract.

    M1: column positions come from the ``segmented_family`` layout profile
    (``codegen.layout.discover``); the cells are read here, verbatim."""
    from codegen.extract.extractor import ExtractionError  # local: avoid cycle

    seg_config = config.extractor.segmented

    if profile is None or workbook is None:
        from codegen.layout.discover import discover

        found = discover(workbook_path, config.extractor)
        profile, workbook = found.profile, found.workbook
    if profile.strategy != "segmented_family":
        raise SegmentedWorkbookError(
            f"{workbook_path.name}: {refusal_evidence}; the segmented extractor cannot "
            f"resolve this workbook (discovery strategy {profile.strategy!r})")
    sheet_profile = profile.mapping_sheets[0]
    ws = workbook[sheet_profile.name]
    rows = list(ws.iter_rows(values_only=True))
    assert sheet_profile.band_row is not None
    band_row = sheet_profile.band_row - 1

    facts = _parse_metadata_block(rows, band_row, seg_config, ws.title)
    blocks = _blocks_from_profile(sheet_profile)
    seg_rows = _segment_rows(rows, band_row + 1, blocks, seg_config, ws.title)

    frd_feed = _match_frd_feed(frd, facts, workbook_path.name)
    feed_id = config.feed_aliases.get(frd_feed.feed_name) or normalize_feed_name(
        frd_feed.feed_name)

    provenance_notes: list[ProvenanceNote] = []

    # ---- record identification: derived from the STTM; FAQ = override only -
    faq = load_faq(normalize_feed_name(feed_id), config)
    override = faq.record_type_discriminators
    if override is not None and override.status != "confirmed":
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: record_type_discriminators in the FAQ "
            "is an OVERRIDE and requires status 'confirmed' — record "
            "identification is derived from the STTM by default "
            f"(declared status: {override.status!r})"
        )
    if override is not None:
        identification = RecordIdentification(
            method="declared_override",
            trailer_marker=override.trailer,
            header_rule=f"records whose first field equals {override.header!r}",
            detail_rule=f"records whose first field equals {override.detail!r}",
            citation=(
                "FAQ record_type_discriminators override (status: confirmed): "
                f"header={override.header!r} detail={override.detail!r} "
                f"trailer={override.trailer!r}"
            ),
        )
    else:
        identification = _derive_identification(seg_rows, blocks, ws.title)

    # ---- group rows by segment; per-segment audit rows ---------------------
    fields_by_segment: dict[str, list[_SegRow]] = {}
    audit_by_segment: dict[str, list[tuple[str, str]]] = {}
    row_counts: dict[str, int] = {}
    segments_found: list[str] = []
    current_segment: str | None = None
    for seg_row in seg_rows:
        row = seg_row.values
        if seg_row.segment is not None:
            current_segment = seg_row.segment
            if seg_row.segment not in segments_found:
                segments_found.append(seg_row.segment)
            row_counts[seg_row.segment] = row_counts.get(seg_row.segment, 0) + 1
            fields_by_segment.setdefault(seg_row.segment, []).append(seg_row)
            continue
        column = _cell(row, blocks.stage.get("columnname"))
        datatype_raw = _cell(row, blocks.stage.get("datatype")) or ""
        if column is None or current_segment is None:
            raise WorkbookParseError(
                f"{ws.title} row {seg_row.row_number}: row carries neither a Segment "
                "value nor an audit-column identity"
            )
        datatype = _AUDIT_DATATYPES.get(_norm(datatype_raw))
        if datatype is None:
            # M11: carried verbatim, flagged by the gate (audit_types).
            datatype = (datatype_raw or "").strip()
            if not datatype:
                raise WorkbookParseError(
                    f"{ws.title} row {seg_row.row_number}: audit column {column!r} states "
                    "no datatype (the cell is empty)"
                )
        audit_by_segment.setdefault(current_segment, []).append((column, datatype))

    if "Detail" not in fields_by_segment:
        raise WorkbookParseError(f"{ws.title}: no Detail-segment rows found")

    # ---- both layers, scoped by Load Strategy — never by the schema block --
    sttm_has_standard = blocks.standard is not None and any(
        _cell(r.values, blocks.standard["tablename"]) is not None
        for rows_ in fields_by_segment.values() for r in rows_
    )
    frd_has_standard_tables = bool(frd_feed.standard_target.tables)
    emit_standard = sttm_has_standard
    if sttm_has_standard and not frd_has_standard_tables:
        standard_group = ".".join(p for p in (
            _first_standard(fields_by_segment, blocks, "catalog"),
            _first_standard(fields_by_segment, blocks, "schema"),
        ) if p)
        provenance_notes.append(ProvenanceNote(
            note=(
                "STD target schema sourced from STTM; FRD Structural Metadata "
                "names stage targets only. The standard layer is scoped by its "
                "Load Strategy, never inferred absent from the Target Schema "
                "block."
            ),
            citation=(
                f"FRD Load Strategy STD: {frd_feed.standard_target.load_strategy!r}; "
                f"STTM standard target group: {standard_group}"
            ),
        ))

    # ---- fields: every segment's rows, both layers -------------------------
    fields: list[SttmField] = []
    mandatory_sources: list[str] = []
    phi_sources: list[str] = []
    for segment in segments_found:
        for seg_row in fields_by_segment[segment]:
            row = seg_row.values
            field_name = _cell(row, blocks.source["field_name"])
            assert field_name is not None  # _segment_rows guarantees it
            mandatory = _is_yes(_cell(row, blocks.stage.get("mandatory column")))
            primary_key = _is_yes(_cell(row, blocks.stage.get("primary key")))
            phi = _is_yes(_cell(row, blocks.source.get("pii")))
            if mandatory or primary_key:
                mandatory_sources.append(field_name)
            if phi:
                phi_sources.append(field_name)
            value_parts = [
                part for part in (
                    _cell(row, blocks.stage.get("transformations/data quality")),
                    _cell(row, blocks.source.get("business_rule")),
                ) if part
            ]
            fields.append(SttmField(
                source_column=field_name,
                description=_cell(row, blocks.source.get("comments")),
                sample_value=None,
                source_datatype=_cell(row, blocks.source.get("datatype")) or "unstated",
                nullable=not (mandatory or primary_key),
                phi=phi,
                mandatory=mandatory,
                stage_column=_require(ws.title, seg_row.row_number,
                                      _cell(row, blocks.stage["columnname"]),
                                      "stage ColumnName"),
                stage_datatype=_require(ws.title, seg_row.row_number,
                                        _cell(row, blocks.stage["datatype"]),
                                        "stage DataType"),
                standard_column=(_cell(row, blocks.standard["columnname"])
                                 if emit_standard else None),
                standard_datatype=(_cell(row, blocks.standard["datatype"])
                                   if emit_standard else None),
                value_spec="; ".join(value_parts) if value_parts else None,
                record_segment=segment,  # type: ignore[arg-type]
                stage_table=_require(ws.title, seg_row.row_number,
                                     _cell(row, blocks.stage["tablename"]),
                                     "stage TableName"),
                standard_table=(_cell(row, blocks.standard["tablename"])
                                if emit_standard else None),
                provenance=FieldProvenance(
                    sheet=ws.title, row=seg_row.row_number,
                    col=blocks.source["field_name"] + 1,
                    source=profile.role_source(ws.title, "source", "field_name")),
            ))

    # ---- no natural-key requirement (FRD: no keys, no MERGE) ---------------
    provenance_notes.append(ProvenanceNote(
        note=(
            "No MERGE key required or derived: the FRD's Technical Metadata "
            "states Business Key / Primary Key / Unique Key(s) = None and the "
            "load strategies are truncate (STG) / append (STD). The STTM's "
            "empty Mandatory/Primary Key columns are consistent with the FRD."
        ),
        citation=(
            f"FRD Load Strategy STG: {frd_feed.stage_target.load_strategy!r}; "
            f"Load Strategy STD: {frd_feed.standard_target.load_strategy!r}"
        ),
    ))

    # ---- FRD-driven AS-IS switch (STRING everywhere except audit) ----------
    as_is_rules = [r for r in frd_feed.validation_rules if _AS_IS_RE.search(r)]
    if as_is_rules:
        provenance_notes.append(ProvenanceNote(
            note=(
                "AS-IS load: business columns are STRING in BOTH layers, audit "
                "date/timestamp fields excepted (FRD-driven switch, not a feed "
                "special case)."
            ),
            citation=f"FRD validation rule: {as_is_rules[0]!r}",
        ))

    # ---- recycle from the FRD's stated DQ requirement ----------------------
    recycle = _build_recycle(frd_feed, fields_by_segment, blocks, seg_config,
                             provenance_notes)

    detail_audit = audit_by_segment.get("Detail", [])
    if not detail_audit:
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: no Detail-segment audit rows found "
            "(rows with empty source cells inside the Detail block)"
        )

    segmented = SegmentedExtraction(
        segments_found=segments_found,
        row_counts=row_counts,
        identification=identification,
        provenance_notes=provenance_notes,
        # Per-segment audit columns exactly as the STTM lists them.
        segment_audit={
            segment: [AuditColumn(column=c, datatype=d) for c, d in columns]
            for segment, columns in audit_by_segment.items()
        },
    )

    detail_rows = fields_by_segment["Detail"]
    stage_schema = _require(ws.title, detail_rows[0].row_number,
                            _cell(detail_rows[0].values, blocks.stage["schema"]),
                            "stage Schema")
    stage_catalog = _cell(detail_rows[0].values, blocks.stage.get("catalog"))
    detail_stage_table = _require(ws.title, detail_rows[0].row_number,
                                  _cell(detail_rows[0].values, blocks.stage["tablename"]),
                                  "stage TableName")

    standard_ref = None
    if emit_standard:
        standard_ref = TableRef(
            schema=_first_standard(fields_by_segment, blocks, "schema") or "",
            table=(_cell(detail_rows[0].values, blocks.standard["tablename"]) or ""),
            catalog=_first_standard(fields_by_segment, blocks, "catalog"),
        )

    file_pattern = _match_file_pattern(facts["files"], frd_feed, workbook_path.name)
    from codegen.formats import is_spreadsheet

    delimiter = "" if is_spreadsheet(frd_feed.file_format, config,
                                     frd_feed.file_name_patterns) else (
        frd_feed.delimiter or _metadata_delimiter(facts)
        or _FORMAT_DELIMITERS.get(frd_feed.file_format.lower()))
    if delimiter is None:
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: no delimiter in the FRD, the metadata "
            f"block ({facts['file_type']!r}), or implied by format "
            f"{frd_feed.file_format!r}"
        )

    feed = SttmFeed(
        feed_id=feed_id,
        source_system=facts["generator"],
        mapping_sheet=ws.title,
        source_file=SourceFile(
            name_pattern=file_pattern,
            format=frd_feed.file_format,
            delimiter=delimiter,
            frequency=facts.get("frequency"),
        ),
        stage=TableRef(schema=stage_schema, table=detail_stage_table,
                       catalog=stage_catalog),
        standard=standard_ref,
        load_rules=LoadRules(
            not_null_columns=list(mandatory_sources),
            mandatory_columns=list(mandatory_sources),
            phi_columns=phi_sources,
            recycle=recycle,
        ),
        audit_columns=[AuditColumn(column=c, datatype=d) for c, d in detail_audit],
        field_count=len(fields),
        fields=fields,
        segmented=segmented,
    )

    return SttmContract(
        contract_name=contract_name
        or f"STTM mapping contract extracted from {workbook_path.name}",
        generated_from_workbook=workbook_path.name,
        sttm_version="unversioned (segmented workbook carries no VERSION_HISTORY sheet)",
        generated_date=generated_date or _today(),
        notes=[
            "Extracted deterministically by `codegen extract-sttm` (segmented "
            f"dialect) from the workbook named above, paired with FRD contract "
            f"'{frd.contract_name}'.",
            "Segments map to their own tables in both layers (FRD acceptance "
            "criterion: Header/Detail/Trailer data mapped to respective HDR, "
            "DTL and TRL tables).",
            "Record identification is derived from the STTM (trailer static "
            "marker + positional header) — see the feed's "
            "segmented.identification citation.",
        ],
        feeds=[feed],
        layout=LayoutSummary(
            strategy=profile.strategy, source=profile.source,
            fingerprint=profile.fingerprint,
            unresolved=[f"{u.sheet}/{u.layer}/{u.role}: {u.reason}"
                        for u in profile.unresolved]),
    )


def _first_standard(fields_by_segment, blocks: _Blocks, which: str) -> str | None:
    if blocks.standard is None or which not in blocks.standard:
        return None
    for rows_ in fields_by_segment.values():
        for seg_row in rows_:
            value = _cell(seg_row.values, blocks.standard[which])
            if value is not None:
                return value
    return None


def _build_recycle(frd_feed: FrdFeed, fields_by_segment, blocks: _Blocks,
                   seg_config: SegmentedExtractorConfig,
                   provenance_notes: list[ProvenanceNote]) -> RecycleSpec | None:
    """The FRD's stated member-existence DQ requirement, via the existing
    recycle pattern. Built ONLY when the FRD states both the recycle rule and
    the member-validation rule; the reference table name is a config knob
    transcribed from the FRD's DQ Functional Requirement (never invented)."""
    if not frd_feed.recycle_rule:
        return None
    member_rules = [r for r in frd_feed.validation_rules
                    if _MEMBER_VALIDATION_RE.search(r)]
    if not member_rules:
        provenance_notes.append(ProvenanceNote(
            note="FRD states a recycle rule but no member-validation rule; no "
                 "recycle module is generated.",
            citation=f"FRD recycle_rule: {frd_feed.recycle_rule!r}",
        ))
        return None
    member_field = next(
        (r for rows_ in fields_by_segment.values() for r in rows_
         if _norm(_cell(r.values, blocks.source["field_name"]))
         == _norm(seg_config.member_field)),
        None,
    )
    if member_field is None:
        provenance_notes.append(ProvenanceNote(
            note=(
                f"FRD states member validation but no field named "
                f"{seg_config.member_field!r} exists in the STTM; no recycle "
                "module is generated."
            ),
            citation=f"FRD validation rule: {member_rules[0]!r}",
        ))
        return None
    window = _WINDOW_DAYS_RE.search(frd_feed.recycle_rule)
    window_days = int(window.group(1)) if window else None
    stage_column = _cell(member_field.values, blocks.stage["columnname"])
    stage_catalog = _cell(member_field.values, blocks.stage.get("catalog"))
    stage_schema = _cell(member_field.values, blocks.stage["schema"])
    reference = ".".join(p for p in (
        stage_catalog, stage_schema, seg_config.member_reference_table) if p)
    days = window_days or 15
    provenance_notes.append(ProvenanceNote(
        note=(
            f"Recycle: {seg_config.member_field!r} existence checked against "
            f"{reference} in the stage layer; invalid records recycle for "
            f"{days} days."
        ),
        citation=(
            f"FRD validation rule: {member_rules[0]!r}; FRD recycle_rule: "
            f"{frd_feed.recycle_rule!r}"
        ),
    ))
    return RecycleSpec(
        applies_to=_cell(member_field.values, blocks.source["field_name"]) or "",
        enabled=True,
        validation=(
            f"Check with {stage_column} from {reference}, per FRD rule "
            f"{member_rules[0]!r}"
        ),
        on_match="Process record into stage table",
        on_no_match=(
            f"Load record to Recycle Table with recycle flag enabled for "
            f"{days} days; retry on subsequent runs"
        ),
        recycle_window_days=days,
    )


def _require(sheet: str, row_number: int, value: str | None, what: str) -> str:
    if value is None:
        raise WorkbookParseError(f"{sheet} row {row_number}: {what} is empty")
    return value


def _today() -> str:
    import datetime

    return datetime.date.today().isoformat()


def _match_frd_feed(frd: FrdContract, facts: dict[str, str], name: str) -> FrdFeed:
    """Pair by file patterns (canonicalized), same rule as the flat path."""
    workbook_patterns = {
        _canonical_file_name(line)
        for line in re.split(r"[\n,;]+", facts["files"])
        if line.strip()
    }
    matches = [
        feed for feed in frd.feeds
        if workbook_patterns & {_canonical_file_name(p) for p in feed.file_name_patterns}
    ]
    if len(matches) != 1:
        raise WorkbookParseError(
            f"{name}: {len(matches)} FRD feeds match the metadata File(s) patterns "
            f"{sorted(workbook_patterns)} (FRD feeds: {[f.feed_name for f in frd.feeds]})"
        )
    return matches[0]


def _match_file_pattern(files_value: str, frd_feed: FrdFeed, name: str) -> str:
    frd_canonical = {_canonical_file_name(p): p for p in frd_feed.file_name_patterns}
    for line in re.split(r"[\n,;]+", files_value):
        canonical = _canonical_file_name(line)
        if canonical in frd_canonical:
            return line.strip()
    raise WorkbookParseError(
        f"{name}: none of the metadata File(s) entries match the FRD's "
        f"file_name_patterns {frd_feed.file_name_patterns}"
    )


def _metadata_delimiter(facts: dict[str, str]) -> str | None:
    match = _DELIMITER_RE.search(facts.get("file_type", ""))
    if match and match.group(1) not in (")",):
        return match.group(1)
    return None


__all__ = ["SegmentedWorkbookError", "extract_segmented_contract"]
