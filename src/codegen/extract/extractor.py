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
from codegen.extract.audit_names import clean_audit_column
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
from codegen.run_errors import Coord, error_coord, located, sheet_number


class ExtractionError(ValueError):
    """Workbook and FRD contract cannot be combined; message names the feed."""


class NeedsAnswersError(ExtractionError):
    """Every mapping sheet was held back as NEEDS_ANSWERS (no document states
    a target): ``pending`` names the answers-file key of each."""

    def __init__(self, pending) -> None:
        # A band-layer key (Chunk A) is answered under answers:, every other
        # held-back key under gaps: (codegen.extract.generic.answers_section).
        from codegen.extract.generic import answers_section

        self.pending = list(pending)
        super().__init__("NEEDS_ANSWERS — " + "; ".join(
            f"feed {p.feed_name!r} (sheet {p.sheet!r}): answer `{p.key}` under "
            f"{answers_section(p.key)}: in the answers file — {p.reason}"
            for p in self.pending))


class UnresolvedLayoutError(ExtractionError):
    """--require-complete and the layout leaves roles open: nothing is
    extracted; ``unresolved`` names each role the answers file must place;
    ``sheet_names`` (post57) the workbook's sheets in order, for the printed keys."""

    def __init__(self, message: str, unresolved, sheet_names=()) -> None:
        self.unresolved = list(unresolved)
        self.sheet_names = list(sheet_names)
        super().__init__(message)


def _indexed(pending, workbook) -> list:
    """post57: each held-back answer with its sheet's workbook position."""
    names = list(getattr(workbook, "sheetnames", None) or [])
    return [p if p.sheet not in names or p.sheet_index is not None
            else p.model_copy(update={"sheet_index": names.index(p.sheet)}) for p in pending]


def extract_contract(workbook_path: Path, frd_path: Path, config: Config, **kwargs
                     ) -> SttmContract:
    """:func:`_extract_contract`, with every held-back answer carrying its
    sheet's workbook position (post57: printed keys say ``sheets[<i>]``)."""
    from codegen.layout.sheet_refs import workbook_sheet_names

    try:
        contract = _extract_contract(workbook_path, frd_path, config, **kwargs)
    except NeedsAnswersError as exc:
        exc.pending = _indexed(exc.pending, _Names(workbook_sheet_names(workbook_path)))
        raise
    contract = _with_model_placed_flags(contract, kwargs.get("layout"))
    if not contract.needs_answers:
        return contract
    return contract.model_copy(update={"needs_answers": _indexed(
        contract.needs_answers, _Names(workbook_sheet_names(workbook_path)))})


class _Names:
    def __init__(self, names: list[str]) -> None:
        self.sheetnames = names


# P1-1 (red team LM-1): the roles whose values become DDL / IIG identifiers.
_IDENTIFIER_ROLES = ("catalog", "schema", "table", "column", "target_type")
MODEL_PLACED = "layout_model_placed"


def model_placed_flags(profile: LayoutProfile | None, sheet: str) -> list[str]:
    """``layout_model_placed:<sheet>/<layer>/<role>`` for every identifier role
    of ``sheet``'s target bands the layout MODEL placed (validated against the
    workbook, never confirmed by a person) - carried to the gate, the review copy
    and the combined LOG.md. Only a resolved profile (``--layout``) can hold one:
    discovery alone never places a role by model."""
    if profile is None or (sp := profile.sheet(sheet)) is None:
        return []
    return [f"{MODEL_PLACED}:{sheet}/{band.layer}/{role} — the layout model placed this "
            "column (validated against the workbook, not confirmed by a person); check the "
            "values it supplies before approving"
            for band in sp.bands if band.layer in ("stage", "standard")
            for role in _IDENTIFIER_ROLES
            if role in band.roles and profile.role_source(sheet, band.layer, role) == "model"]


def _with_model_placed_flags(contract: SttmContract, profile: LayoutProfile | None
                             ) -> SttmContract:
    if profile is None:
        return contract
    feeds = []
    for feed in contract.feeds:
        added = [f for f in model_placed_flags(profile, feed.mapping_sheet)
                 if f not in feed.extraction_flags]
        feeds.append(feed.model_copy(update={"extraction_flags": [*feed.extraction_flags,
                                                                  *added]})
                     if added else feed)
    return contract.model_copy(update={"feeds": feeds})


def _extract_contract(
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
    audit_answers: dict[int, list[tuple[str, str]]] | None = None,
    gaps: dict | None = None,
) -> SttmContract:
    """``gaps`` (2026-10-13): the answers file's ``gaps:`` — read when a
    one-feed FRD contract is split per mapping sheet here (a file question).
    ``audit_answers`` (Chunk B): the person's ``feeds[i].audit_columns``
    answers (``codegen.extract.generic.parse_audit_answers``) for a sheet
    whose STTM lists no audit row; content-driven path only.
    ``width_answers`` (M9.2): the person's ``feeds[i].fields[<name>].width``
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
    # --require-complete stops on the REQUIRED roles left open only: an optional
    # role the layout could not place reads as empty and is no answer owed.
    from codegen.layout.profile import is_required_role

    owed = [u for u in profile.unresolved if is_required_role(u.layer, u.role)]
    if require_complete and owed:
        raise located(UnresolvedLayoutError(
            f"{workbook_path.name}: layout has {len(owed)} unresolved required role(s) "
            "and --require-complete is set: "
            + "; ".join(f"{u.sheet}/{u.layer}/{u.role} ({u.reason})" for u in owed),
            owed, found.workbook.sheetnames,
        ), Coord("STTM", sheet=sheet_number(found.workbook, owed[0].sheet)),
            "layout.unresolved")
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
        from codegen.layout.resolve import split_single_frd_feed

        # 2026-10-13 (D1 pair_11): ONE FRD feed for several mapping sheets is
        # split here, by the layout stage's rule — no flag, no extra step.
        split = split_single_frd_feed(frd, profile, found.workbook, config, gaps)
        if split is not None:
            frd = frd.model_copy(update={"feeds": split.feeds, "extraction_flags": [
                *frd.extraction_flags, *split.flags]})
        from codegen.extract.generic import parse_cell_answers

        try:
            contract = extract_generic_contract(
                found, workbook_path, frd, config, contract_name=contract_name,
                generated_date=generated_date or datetime.date.today().isoformat(),
                width_answers=width_answers, audit_answers=audit_answers,
                cell_answers=parse_cell_answers(gaps),
            )
        except GenericExtractionError as exc:
            raise ExtractionError(str(exc)) from exc
        if split is not None:
            contract = contract.model_copy(update={
                "frd_split": split, "notes": [*contract.notes, *split.flags]})
        return contract
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

    from codegen.contracts.sttm import PendingAnswer
    from codegen.extract.generic import NeedsAnswers

    skipped = {t for t in skip_stage_tables}
    sheets = [s for s in ir.sheets if s.stage_table not in skipped]

    # Multi-file FRD: split a single feed with >1 table and >1 pattern
    # into one feed per target table so each sheet pairs with exactly
    # one feed and one FILE_DETAILS row.
    frd = _expand_multi_file_frd(frd, len(sheets))
    feeds = []
    pending: list[PendingAnswer] = []
    for sheet in sheets:
        try:
            matched = _match_frd_feed(sheet, frd, sheets)
            feeds.append(_build_feed(sheet, matched, ir, config, frd.feeds.index(matched)))
        except NeedsAnswers as held:
            # One sheet without a stated target holds back ITS feed only.
            pending.extend(held.pending)
        except ExtractionError as exc:
            # The raise sites name the sheet in their text; the coordinates
            # tier gets its position here (the IR carries no sheet order).
            if error_coord(exc) is None:
                located(exc, Coord("STTM", sheet=sheet_number(found.workbook, sheet.sheet_name)),
                        getattr(exc, "reason", None))
            raise
    if not feeds and pending:
        raise NeedsAnswersError(pending)
    if ir.file_details_skipped:
        from codegen.extract.annotations import flag

        feeds = [f.model_copy(update={"extraction_flags": [
            *f.extraction_flags, *(flag(e) for e in ir.file_details_skipped)]}) for f in feeds]

    sheet_tables = {f.stage.table for f in feeds}
    held_back = {p.feed_name for p in pending}
    unmatched_frd = [
        f.feed_name
        for f in frd.feeds
        if not sheet_tables & set(f.stage_target.tables)
        and not set(f.stage_target.tables) <= skipped
        and f.feed_name not in held_back
    ]
    if unmatched_frd:
        raise located(ExtractionError(
            f"FRD feed(s) {unmatched_frd} have no mapping sheet in {ir.workbook_name} "
            f"(sheet stage tables: {sorted(sheet_tables)})"
        ), Coord("feed", n=[f.feed_name for f in frd.feeds].index(unmatched_frd[0]) + 1,
                 of=len(frd.feeds)), "sttm.missing", role="mapping_sheet")

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
            *(f"FILE_DETAILS annotation row skipped (not read as a file): {e}"
              for e in ir.file_details_skipped),
            *(f"sheet {p.sheet!r}: feed {p.feed_name!r} NEEDS_ANSWERS — answer `{p.key}` "
              f"under gaps: ({p.reason})" for p in pending),
        ],
        feeds=feeds,
        layout=LayoutSummary(
            strategy=profile.strategy, source=profile.source, fingerprint=profile.fingerprint,
            unresolved=[f"{u.sheet}/{u.layer}/{u.role}: {u.reason}" for u in profile.unresolved],
        ),
        needs_answers=pending,
    )



def _expand_multi_file_frd(
    frd: FrdContract, n_sheets: int,
) -> FrdContract:
    """Split a single multi-file FRD feed into one feed per target table when
    there are at least as many STTM sheets as there are target tables.

    Each split feed gets exactly one table, one file pattern (paired by name
    similarity), and a unique feed_name (the table stem without extension).
    Returns the FRD unchanged when no split is needed."""
    if len(frd.feeds) != 1:
        return frd
    feed = frd.feeds[0]
    tables = feed.stage_target.tables
    patterns = feed.file_name_patterns
    if len(tables) <= 1 or len(patterns) <= 1:
        return frd
    if n_sheets < len(tables):
        return frd
    from codegen.extract.frd_docx import _name_similarity

    remaining = list(patterns)
    expanded: list[FrdFeed] = []
    for idx, table in enumerate(tables):
        if not remaining:
            best = None
        else:
            best = max(
                remaining,
                key=lambda p: _name_similarity(p, table),
            )
            remaining.remove(best)
        extra = remaining if idx == len(tables) - 1 else []
        pats = ([best] if best else []) + extra
        split_name = re.sub(
            r"\.[a-z0-9]{2,4}$", "", table, flags=re.IGNORECASE,
        )
        expanded.append(feed.model_copy(update={
            "feed_name": split_name,
            "file_name_patterns": pats,
            "stage_target": feed.stage_target.model_copy(
                update={"tables": [table]}),
            "standard_target": feed.standard_target.model_copy(
                update={
                    "tables": (
                        [table]
                        if feed.standard_target.tables
                        else []
                    ),
                }),
        }))
    return frd.model_copy(update={"feeds": expanded})


def _match_frd_feed(sheet: SheetIR, frd: FrdContract,
                    sheets: list[SheetIR] | None = None) -> FrdFeed:
    if sheet.stage_table is None:
        # Blank TableName cells (first ACFC run): the feed the layout stage
        # derived for this sheet (named after it), else the only FRD feed no
        # table-stating sheet claims — never a guess among several.
        from codegen.resolve.gapfill import blank_sheet_feed_name

        named = [f for f in frd.feeds
                 if f.feed_name.lower() == blank_sheet_feed_name(sheet.sheet_name).lower()]
        if len(named) == 1:
            return named[0]
        claimed = {s.stage_table for s in sheets or [] if s.stage_table is not None}
        free = [f for f in frd.feeds if not claimed & set(f.stage_target.tables)]
        if len(free) == 1:
            return free[0]
        # Multi-file FRD: N blank sheets ↔ N free feeds — match by
        # position (nth blank sheet → nth free feed).  This is the
        # natural mapping after _expand_multi_file_frd splits one
        # feed into one-per-table ordered by the FRD's table list.
        blank_sheets = [s for s in sheets or []
                        if s.stage_table is None]
        if len(free) == len(blank_sheets) >= 2:
            try:
                pos = [s.sheet_name for s in blank_sheets].index(
                    sheet.sheet_name)
                return free[pos]
            except (ValueError, IndexError):
                pass
        raise located(ExtractionError(
            f"sheet {sheet.sheet_name!r}: every TableName cell is blank and "
            f"{len(free)} FRD feed(s) {[f.feed_name for f in free]} are claimed by no other "
            "sheet — the sheet cannot be paired; state the table in the STTM"),
            None, "sttm.missing", role="table")
    matches = [f for f in frd.feeds if sheet.stage_table in f.stage_target.tables]
    if len(matches) != 1:
        raise located(ExtractionError(
            f"sheet {sheet.sheet_name!r} (stage table {sheet.stage_table!r}) matches "
            f"{len(matches)} FRD feeds "
            f"{[f.feed_name for f in matches] or [f.feed_name for f in frd.feeds]}; "
            "expected exactly one whose stage_target.tables contains it"
        ), None, "sttm.conflict")
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
        if any(
            _canonical_file_name(part) in canonical_patterns
            for part in re.split(r"[;\n]", row.file_name)
            if part.strip()
        )
    ]
    if len(matches) != 1:
        if not feed.file_name_patterns:
            raise located(ExtractionError(
                f"feed {feed.feed_name!r}: the FRD contract names NO file for it "
                f"(file_name_patterns is empty) while FILE_DETAILS lists "
                f"{[r.file_name for r in ir.file_details]}. Answer the layout dialog's "
                f"'File for table {feed.feed_name}' question (the run paused there) or add "
                "the file name to the FRD — the agent never guesses a file."
            ), None, "frd.missing", role="file_pattern")
        raise located(ExtractionError(
            f"feed {feed.feed_name!r}: {len(matches)} FILE_DETAILS rows match its "
            f"file_name_patterns {feed.file_name_patterns} "
            f"(FILE_DETAILS file names: {[r.file_name for r in ir.file_details]}; "
            "compared after date-placeholder canonicalization: CCYY->YYYY, "
            "case-insensitive)"
        ), None, "sttm.conflict")
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
        raise located(ExtractionError(
            f"feed {feed.feed_name!r}: format {feed.file_format!r} has no implied "
            "delimiter, the FRD contract states none and the file name "
            f"{file_name!r} has no delimiter-bearing extension (csv / psv / tsv)"
        ), None, "frd.missing", role="delimiter")
    return implied


def _resolve_targets(sheet: SheetIR, frd_feed: FrdFeed, file_details: FileDetailsRow,
                     feed_index: int, config: Config, flags: list[str]) -> SheetIR:
    """A sheet whose Schema / TableName cells are ALL blank (first ACFC run):
    table from the feed's File Details row (its target-table cell) or the
    FRD's only table, schema from the FRD or the layer convention — each a
    ``sttm_target_missing`` flag naming the source — else NEEDS_ANSWERS with
    the answers-file key. A sheet stating both is returned unchanged."""
    if not sheet.blank_targets:
        return sheet
    from dataclasses import replace

    from codegen.contracts.sttm import PendingAnswer
    from codegen.extract.generic import NeedsAnswers, _schema_chain, _table_chain

    cells = dict(sheet.blank_targets)
    prefix = f"feeds[{feed_index}]."
    pending: list[PendingAnswer] = []
    notes: list[str] = []          # the classic contract's notes stay fixed
    values = {"stage.schema": sheet.stage_schema, "stage.table": sheet.stage_table,
              "standard.schema": sheet.standard_schema, "standard.table": sheet.standard_table}
    for key, provenance in sheet.blank_targets:
        layer, _dot, role = key.partition(".")
        target = frd_feed.stage_target if layer == "stage" else frd_feed.standard_target
        if role == "table":
            details = ((file_details.target_table, f"{file_details.target_cell} (the row of "
                        "this feed's file)") if layer == "stage" and file_details.target_table
                       else None)
            value = _table_chain(layer, None, provenance, details, list(target.tables),
                                 sheet.sheet_name, notes, flags)
        else:
            value = _schema_chain(layer, None, provenance, target.schema_name, config,
                                  sheet.sheet_name, notes, flags)
        if value is None:
            pending.append(PendingAnswer(
                feed_name=frd_feed.feed_name, sheet=sheet.sheet_name,
                key=f"{prefix}{layer}_target.{'tables' if role == 'table' else 'schema'}",
                reason=f"{cells[key]}; no File Details target / FRD statement / layer "
                       "convention supplies it"))
        values[key] = value
    if pending:
        raise NeedsAnswers(pending)
    return replace(sheet, stage_schema=values["stage.schema"], stage_table=values["stage.table"],
                   standard_schema=values["standard.schema"],
                   standard_table=values["standard.table"])


def _build_feed(sheet: SheetIR, frd_feed: FrdFeed, ir: WorkbookIR, config: Config,
                feed_index: int = 0) -> SttmFeed:
    if frd_feed.is_segmented:
        raise located(ExtractionError(
            f"feed {frd_feed.feed_name!r}: FRD declares record segments "
            f"{frd_feed.record_segments} — segmented feeds are not supported by this "
            "extractor (flat dialect only; see CLAUDE.md)"
        ), None, "sttm.segment")

    file_details = _match_file_details(frd_feed, ir)
    feed_id = config.feed_aliases.get(frd_feed.feed_name) or normalize_feed_name(
        frd_feed.feed_name
    )
    flags: list[str] = []
    sheet = _resolve_targets(sheet, frd_feed, file_details, feed_index, config, flags)

    frd_has_standard = bool(frd_feed.standard_target.tables)
    if frd_has_standard != (sheet.standard_table is not None):
        raise located(ExtractionError(
            f"feed {frd_feed.feed_name!r}: standard-target presence disagrees — FRD "
            f"standard tables {frd_feed.standard_target.tables}, sheet "
            f"{sheet.sheet_name!r} standard table {sheet.standard_table!r}"
        ), None, "contract.mismatch")
    if sheet.standard_table is not None and sheet.standard_table not in (
        frd_feed.standard_target.tables
    ):
        raise located(ExtractionError(
            f"feed {frd_feed.feed_name!r}: sheet standard table {sheet.standard_table!r} "
            f"is not among FRD standard tables {frd_feed.standard_target.tables}"
        ), None, "contract.mismatch")

    if not sheet.audit:
        raise located(ExtractionError(
            f"feed {frd_feed.feed_name!r}: sheet {sheet.sheet_name!r} has no audit rows "
            "(trailing rows with source-side 'NA'); the contract requires at least one "
            "audit column"
        ), None, "sttm.audit", role="audit_column")

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
                AuditColumn(column=clean_audit_column(
                    a.column, "audit_columns", f"sheet {sheet.sheet_name!r} audit row", flags),
                    datatype=a.datatype, description=a.description)
                for a in sheet.audit
            ],
            field_count=len(fields),
            fields=fields,
            extraction_flags=flags,
        )
    except ValueError as exc:  # pydantic ValidationError is a ValueError
        # post74: the rules by name (classic path: FAIL with each rule's count)
        from codegen.contracts.validation import classify
        from codegen.extract.generic import contract_invalid

        raise contract_invalid(ExtractionError, frd_feed.feed_name, classify(exc), None) \
            from exc


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
    audit_answers: dict[int, list[tuple[str, str]]] | None = None,
    gaps: dict | None = None,
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
        audit_answers=audit_answers,
        gaps=gaps,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(contract_to_json(contract), encoding="utf-8", newline="\n")
    return contract


__all__ = [
    "ExtractionError",
    "NeedsAnswersError",
    "UnresolvedLayoutError",
    "WorkbookParseError",
    "contract_to_json",
    "extract_contract",
    "extract_to_file",
]
