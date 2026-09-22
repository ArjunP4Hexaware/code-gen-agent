"""Combine a parsed STTM workbook with its FRD feed contract into the STTM
mapping contract this repo consumes (``codegen.contracts.sttm``).

Pairing-aware by design (decision D2): the workbook alone cannot state the
join key or every feed-level fact, so both inputs are required —

- ``feed_id`` is ``normalize_feed_name(FRD feed_name)`` (or a
  ``config.feed_aliases`` override), exactly the resolver's join invariant.
  Stage-table names coincide with it on MIDS-shaped feeds but are NOT the
  invariant.
- sheets pair to FRD feeds by stage-table membership in the FRD's
  ``stage_target.tables``; FILE_DETAILS rows pair by FileName membership in
  the FRD's ``file_name_patterns``.
- format comes from the FRD; the delimiter is the FRD's when stated, else
  implied from the format (csv/psv) — a format with neither is an error
  here rather than later in the resolver.
- standard-target presence must agree between workbook and FRD; both ways
  of disagreeing are loud errors.

Recycle validation text is emitted VERBATIM from the workbook (decision D3);
the resolver's reference parser accepts the client phrasing. Everything
emitted is deterministic — no timestamps beyond the injectable
``generated_date``.
"""

from __future__ import annotations

import datetime
import json
import re
from collections.abc import Collection
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.sttm import (
    AuditColumn,
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
from codegen.extract.workbook import (
    FileDetailsRow,
    SegmentedWorkbookError,
    SheetIR,
    WorkbookIR,
    WorkbookParseError,
    parse_recycle_text,
    workbook_ir,
)
from codegen.layout.discover import NoLayoutError, discover
from codegen.layout.profile import LayoutProfile

# normalize_feed_name is THE feed_id join invariant (resolver.py defines it);
# _FORMAT_DELIMITERS is the resolver's own format->delimiter implication —
# imported so extractor and resolver can never disagree.
from codegen.resolve.resolver import _FORMAT_DELIMITERS, normalize_feed_name


class ExtractionError(ValueError):
    """Workbook and FRD contract cannot be combined; message names the feed."""


def extract_contract(
    workbook_path: Path,
    frd_path: Path,
    config: Config,
    *,
    contract_name: str | None = None,
    generated_date: str | None = None,
    layout: LayoutProfile | None = None,
    require_complete: bool = False,
    skip_stage_tables: Collection[str] = (),
    width_answers: dict[int, dict[str, int]] | None = None,
) -> SttmContract:
    """``width_answers`` (M9.2): the person's ``feeds[i].fields[<name>].width``
    answers (``codegen.resolve.widths.parse_width_answers``), carried on the
    fields for the resolver's width chain; content-driven path only.
    ``skip_stage_tables``: mapping sheets (by stage table) to leave out of
    the contract — the runner passes the tables of FRD feeds it has already
    set aside as failed (a feed the person left without a file), so the
    remaining feeds still extract. Classic MAPPING- path only; the default
    (nothing skipped) is byte-identical to before."""
    frd = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))
    # M1: one discovery pass -> a layout profile; every strategy's reader
    # then copies cell values through it. Strategy order keeps the two
    # legacy paths first, so their output is byte-identical to before.
    # M2.5: a resolved profile (cache / model / user) may be supplied
    # instead — the reader then never discovers, it only copies through it.
    if layout is not None:
        from codegen.layout.extent import load_document
        from codegen.layout.resolve import discovery_for

        found = discovery_for(layout, load_document(
            workbook_path, config.extractor.used_range_empty_rows))
    else:
        try:
            found = discover(workbook_path, config.extractor)
        except NoLayoutError as exc:
            raise WorkbookParseError(str(exc)) from exc
    profile = found.profile
    if require_complete and profile.unresolved:
        raise ExtractionError(
            f"{workbook_path.name}: layout has {len(profile.unresolved)} unresolved role(s) "
            "and --require-complete is set: "
            + "; ".join(f"{u.sheet}/{u.layer}/{u.role} ({u.reason})" for u in profile.unresolved)
        )
    if profile.strategy == "segmented_family":
        from codegen.extract.segmented import extract_segmented_contract

        return extract_segmented_contract(
            workbook_path, frd, config,
            refusal_evidence=profile.notes[0] if profile.notes else profile.strategy,
            contract_name=contract_name, generated_date=generated_date,
            profile=profile, workbook=found.workbook,
        )
    if profile.strategy == "content":
        from codegen.extract.generic import GenericExtractionError, extract_generic_contract

        try:
            return extract_generic_contract(
                found, workbook_path, frd, config, contract_name=contract_name,
                generated_date=generated_date or datetime.date.today().isoformat(),
                width_answers=width_answers,
            )
        except GenericExtractionError as exc:
            raise ExtractionError(str(exc)) from exc
    try:
        ir = workbook_ir(found, workbook_path.name, config.extractor)
    except SegmentedWorkbookError as detected:
        # v2 (2026-08-31): a MAPPING- sheet whose rows land in several stage
        # tables is the segmented dialect; the segmented extractor refuses
        # it with this exact evidence plus the remedy line.
        from codegen.extract.segmented import extract_segmented_contract

        return extract_segmented_contract(
            workbook_path,
            frd,
            config,
            refusal_evidence=str(detected),
            contract_name=contract_name,
            generated_date=generated_date,
        )

    skipped = {t for t in skip_stage_tables}
    sheets = [s for s in ir.sheets if s.stage_table not in skipped]
    feeds = [
        _build_feed(sheet, _match_frd_feed(sheet, frd), ir, config) for sheet in sheets
    ]

    sheet_tables = {s.stage_table for s in sheets}
    unmatched_frd = [
        f.feed_name
        for f in frd.feeds
        if not sheet_tables & set(f.stage_target.tables)
        and not set(f.stage_target.tables) <= skipped
    ]
    if unmatched_frd:
        raise ExtractionError(
            f"FRD feed(s) {unmatched_frd} have no mapping sheet in {ir.workbook_name} "
            f"(sheet stage tables: {sorted(sheet_tables)})"
        )

    return SttmContract(
        contract_name=contract_name
        or f"STTM mapping contract extracted from {ir.workbook_name}",
        generated_from_workbook=ir.workbook_name,
        sttm_version=ir.version,
        generated_date=generated_date or datetime.date.today().isoformat(),
        notes=[
            "Extracted deterministically by `codegen extract-sttm` from the workbook "
            f"named above, paired with FRD contract '{frd.contract_name}'.",
            "Column facts are verbatim workbook values; audit columns are peeled from "
            "trailing rows whose source-side cells read 'NA'.",
            "Recycle validation text is VERBATIM from the workbook's Recycle Flag cell "
            "(no canonical rewriting; the resolver accepts the client phrasing).",
        ],
        feeds=feeds,
        layout=LayoutSummary(
            strategy=profile.strategy, source=profile.source, fingerprint=profile.fingerprint,
            unresolved=[f"{u.sheet}/{u.layer}/{u.role}: {u.reason}" for u in profile.unresolved],
        ),
    )


def _match_frd_feed(sheet: SheetIR, frd: FrdContract) -> FrdFeed:
    matches = [f for f in frd.feeds if sheet.stage_table in f.stage_target.tables]
    if len(matches) != 1:
        raise ExtractionError(
            f"sheet {sheet.sheet_name!r} (stage table {sheet.stage_table!r}) matches "
            f"{len(matches)} FRD feeds "
            f"{[f.feed_name for f in matches] or [f.feed_name for f in frd.feeds]}; "
            "expected exactly one whose stage_target.tables contains it"
        )
    return matches[0]


def _canonical_file_name(name: str) -> str:
    """Comparison form for FILE_DETAILS↔FRD file-name matching: real pairs
    drift on date-placeholder notation only (FRD patterns say CCYY/CCYYMMDD
    where workbooks say YYYY/YYYYMMDD, sometimes with case drift in the
    surrounding name). Deliberately narrow — no similarity matching."""
    return name.strip().lower().replace("ccyy", "yyyy")


def _match_file_details(feed: FrdFeed, ir: WorkbookIR) -> FileDetailsRow:
    canonical_patterns = {_canonical_file_name(p) for p in feed.file_name_patterns}
    matches = [
        row
        for row in ir.file_details
        if _canonical_file_name(row.file_name) in canonical_patterns
    ]
    if len(matches) != 1:
        if not feed.file_name_patterns:
            raise ExtractionError(
                f"feed {feed.feed_name!r}: the FRD contract names NO file for it "
                f"(file_name_patterns is empty) while FILE_DETAILS lists "
                f"{[r.file_name for r in ir.file_details]}. Answer the layout dialog's "
                f"'File for table {feed.feed_name}' question (the run paused there) or add "
                "the file name to the FRD — the agent never guesses a file."
            )
        raise ExtractionError(
            f"feed {feed.feed_name!r}: {len(matches)} FILE_DETAILS rows match its "
            f"file_name_patterns {feed.file_name_patterns} "
            f"(FILE_DETAILS file names: {[r.file_name for r in ir.file_details]}; "
            "compared after date-placeholder canonicalization: CCYY->YYYY, "
            "case-insensitive)"
        )
    return matches[0]


_EXTENSION_DELIMITERS = {"csv": ",", "psv": "|", "tsv": "\t", "pipe": "|"}


def _extension_delimiter(file_name: str | None) -> str | None:
    """The delimiter a file extension implies (csv / psv / tsv), else None —
    the last resort when neither contract states one and the FRD's 'format'
    is prose ("File Data Ingestion")."""
    if not file_name:
        return None
    match = re.search(r"\.([a-z0-9]{2,4})$", file_name.strip(), re.IGNORECASE)
    return _EXTENSION_DELIMITERS.get(match.group(1).lower()) if match else None


def _resolve_delimiter(feed: FrdFeed, file_name: str | None = None) -> str:
    if feed.delimiter:
        return feed.delimiter
    implied = _FORMAT_DELIMITERS.get((feed.file_format or "").lower())
    if implied is None:
        implied = _extension_delimiter(file_name)
    if implied is None:
        raise ExtractionError(
            f"feed {feed.feed_name!r}: format {feed.file_format!r} has no implied "
            "delimiter, the FRD contract states none and the file name "
            f"{file_name!r} has no delimiter-bearing extension (csv / psv / tsv)"
        )
    return implied


def _build_feed(sheet: SheetIR, frd_feed: FrdFeed, ir: WorkbookIR, config: Config) -> SttmFeed:
    if frd_feed.is_segmented:
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: FRD declares record segments "
            f"{frd_feed.record_segments} — segmented feeds are not supported by this "
            "extractor (flat dialect only; see CLAUDE.md)"
        )

    file_details = _match_file_details(frd_feed, ir)
    feed_id = config.feed_aliases.get(frd_feed.feed_name) or normalize_feed_name(
        frd_feed.feed_name
    )

    frd_has_standard = bool(frd_feed.standard_target.tables)
    if frd_has_standard != (sheet.standard_table is not None):
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: standard-target presence disagrees — FRD "
            f"standard tables {frd_feed.standard_target.tables}, sheet "
            f"{sheet.sheet_name!r} standard table {sheet.standard_table!r}"
        )
    if sheet.standard_table is not None and sheet.standard_table not in (
        frd_feed.standard_target.tables
    ):
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: sheet standard table {sheet.standard_table!r} "
            f"is not among FRD standard tables {frd_feed.standard_target.tables}"
        )

    if not sheet.audit:
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: sheet {sheet.sheet_name!r} has no audit rows "
            "(trailing rows with source-side 'NA'); the contract requires at least one "
            "audit column"
        )

    recycle = None
    recycle_text = parse_recycle_text(sheet)
    if recycle_text is not None:
        window_days = recycle_text.window_days or config.defaults.recycle_window_days
        recycle = RecycleSpec(
            applies_to=recycle_text.applies_to,
            enabled=True,
            validation=recycle_text.validation,
            on_match=config.extractor.recycle_on_match.format(window_days=window_days),
            on_no_match=config.extractor.recycle_on_no_match.format(window_days=window_days),
            recycle_window_days=window_days,
        )

    fields = [
        SttmField(
            source_column=row.source_column,
            description=row.description,
            sample_value=row.sample_value,
            source_datatype=row.source_datatype,
            nullable=row.nullable,
            phi=row.phi,
            mandatory=row.mandatory,
            stage_column=row.stage_column,
            stage_datatype=row.stage_datatype,
            standard_column=row.standard_column,
            standard_datatype=row.standard_datatype,
            value_spec=row.value_spec,
            provenance=FieldProvenance(
                sheet=sheet.sheet_name, row=row.row_number, col=row.source_col,
                source=(ir.profile.role_source(sheet.sheet_name, "source", "field_name")
                        if ir.profile is not None else "synonyms")),
        )
        for row in sheet.rows
    ]

    try:
        return SttmFeed(
            feed_id=feed_id,
            source_system=file_details.vendor,
            mapping_sheet=sheet.sheet_name,
            source_file=SourceFile(
                name_pattern=file_details.file_name,
                format=frd_feed.file_format,
                delimiter=_resolve_delimiter(frd_feed, file_details.file_name),
                frequency=file_details.frequency,
            ),
            stage=TableRef(schema=sheet.stage_schema, table=sheet.stage_table),
            standard=(
                TableRef(schema=sheet.standard_schema, table=sheet.standard_table)
                if sheet.standard_table is not None
                else None
            ),
            load_rules=LoadRules(
                not_null_columns=[r.source_column for r in sheet.rows if not r.nullable],
                mandatory_columns=[r.source_column for r in sheet.rows if r.mandatory],
                phi_columns=[r.source_column for r in sheet.rows if r.phi],
                recycle=recycle,
            ),
            audit_columns=[
                AuditColumn(column=a.column, datatype=a.datatype) for a in sheet.audit
            ],
            field_count=len(fields),
            fields=fields,
        )
    except ValueError as exc:  # pydantic ValidationError is a ValueError
        raise ExtractionError(
            f"feed {frd_feed.feed_name!r}: extracted feed fails contract validation:\n{exc}"
        ) from exc


def contract_to_json(contract: SttmContract) -> str:
    """Serialize the way the fixture contracts are shaped: ``schema`` via
    alias, optional dialect keys (``value_spec``/``record_segment``/
    ``stage_table``/``synthetic``) omitted when at their defaults, required
    nullable keys kept as ``null``."""
    payload = contract.model_dump(mode="json", by_alias=True, exclude_defaults=True)
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def extract_to_file(
    workbook_path: Path,
    frd_path: Path,
    out_path: Path,
    config: Config,
    *,
    contract_name: str | None = None,
    generated_date: str | None = None,
    layout: LayoutProfile | None = None,
    require_complete: bool = False,
    skip_stage_tables: Collection[str] = (),
    width_answers: dict[int, dict[str, int]] | None = None,
) -> SttmContract:
    contract = extract_contract(
        workbook_path,
        frd_path,
        config,
        contract_name=contract_name,
        generated_date=generated_date,
        layout=layout,
        require_complete=require_complete,
        skip_stage_tables=skip_stage_tables,
        width_answers=width_answers,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(contract_to_json(contract), encoding="utf-8", newline="\n")
    return contract


__all__ = [
    "ExtractionError",
    "WorkbookParseError",
    "contract_to_json",
    "extract_contract",
    "extract_to_file",
]
