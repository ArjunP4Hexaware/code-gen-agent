"""Layout discovery — every strategy ends in a :class:`LayoutProfile`.

Three deterministic strategies, tried in order; the first that applies
wins, so the two legacy paths keep today's behaviour byte for byte:

1. ``mapping_prefix`` — the ``MAPPING-`` sheet-name path (FILE_DETAILS +
   VERSION_HISTORY + per-sheet band row 1 / header row 2), resolved with
   the legacy functions in :mod:`codegen.extract.workbook`.
2. ``segmented_family`` — the CAQH-shaped family (key:value metadata block,
   band row with the ``Source Layout`` variant, per-row Segment column),
   resolved with the legacy block resolution in
   :mod:`codegen.extract.segmented`. Applies only when that resolution
   succeeds; otherwise the sheet falls through to strategy 3 and the
   profile notes say so.
3. ``content`` — content-driven discovery (M1): a mapping sheet is any
   sheet with a row carrying both a stage token and a standard token
   (``extractor.discovery.band_tokens``) and a header row beneath it (or
   the same row, when the layer prefixes live in the header texts);
   band spans come from merged ranges, else from band-text positions;
   header→role, meta-row and segment vocabularies come from
   ``extractor.discovery`` in config; auxiliary sheets are recognised by
   header signature; everything unresolved is listed, never guessed.

Every profile carries ``source="synonyms"`` here — a model or a person
(M2.5) can only ever refine what these tables leave unresolved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import DiscoveryConfig, ExtractorConfig
from codegen.layout.extent import load_document
from codegen.layout.fingerprint import fingerprint
from codegen.layout.profile import (
    BAND_LAYER_CHOICES,
    BAND_LAYER_ROLE,
    REQUIRED_ROLES,
    VALUE_EVIDENCE,
    BandProfile,
    LayoutProfile,
    MetaRow,
    Role,
    SheetProfile,
    UnresolvedRole,
    band_ref,
    confidence_key,
)

# Synonym-table hits are exact normalized matches: full confidence.
_SYNONYM_CONFIDENCE = 1.0
# Rows scanned for an auxiliary sheet's header signature.
_AUX_SCAN_ROWS = 12
# A header row must carry at least this many text cells.
_MIN_HEADER_CELLS = 3
# A band row carries a few group labels, never a full header's worth.
_MAX_BAND_LABELS = 5
# Diagnostic prefix: the legacy MAPPING- reader refused the workbook and the
# other strategies read it (parse_workbook re-raises the legacy text).
MAPPING_PREFIX_REFUSED = "MAPPING- reader refused the workbook: "


def normalize(value: object) -> str:
    """Comparison form for every header, label, token and marker: lowercase,
    every run of non-alphanumerics (space, _ / - ( ) ? : # . …) → one
    space, trimmed. "Target_Column_Name_in_DL" → "target column name in dl"."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def text(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


@dataclass
class Discovery:
    """A discovered layout plus the loaded workbook (loaded once, reused by
    the reader) and the diagnostics discovery logged on the way."""

    profile: LayoutProfile
    workbook: object
    diagnostics: list[str] = field(default_factory=list)
    # Chunk A: the legacy MAPPING- reader's refusal when another strategy read
    # the workbook instead (the flat API re-raises it, type and text intact).
    refused: Exception | None = None


class NoLayoutError(ValueError):
    """No discovery strategy applies to this workbook."""


def discover_vdd(path: Path, config: ExtractorConfig,
                 sttm_tables: list[str] | None = None) -> Discovery:
    """A Vendor Data Dictionary's layout (M3): the FILES sheet by header
    signature (roles from ``extractor.vdd.files_roles``), field sheets by
    the FILES sheet's ``Field Sheet`` column or by header signature (roles
    from ``field_roles``), segments by a Segment column. One-sheet-per-table
    dictionaries are narrowed to the sheets whose names match the STTM's
    table names (normalized); everything else is logged and ignored."""
    workbook = load_document(path, config.used_range_empty_rows)
    digest = fingerprint(workbook)
    vcfg = config.vdd
    diagnostics: list[str] = []
    sheets: list[SheetProfile] = []
    confidence: dict[str, float] = {}
    unresolved: list[UnresolvedRole] = []
    files_sheet: str | None = None
    listed: set[str] = set()
    for ws in workbook.worksheets:
        found = _signature_row(ws, vcfg.files_signature)
        if found is None or files_sheet is not None:
            continue
        header_row, header = found
        band = _resolve_flat_roles(ws.title, "files", header, vcfg.files_roles, confidence,
                                   unresolved, diagnostics)
        files_sheet = ws.title
        sheets.append(SheetProfile(name=ws.title, kind="vdd_files", header_row=header_row,
                                   bands=[band]))
        col = band.column(Role.FIELD_SHEET)
        if col is not None:
            for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
                value = text(row[col - 1]) if col - 1 < len(row) else None
                if value:
                    listed.add(value)
        diagnostics.append(f"sheet {ws.title!r}: VDD FILES sheet (header row {header_row})")
    normalized_tables = {normalize(t).replace(" ", "") for t in (sttm_tables or []) if t}
    for ws in workbook.worksheets:
        if ws.title == files_sheet:
            continue
        found = _signature_row(ws, vcfg.fields_signature)
        if found is None and ws.title not in listed:
            diagnostics.append(f"sheet {ws.title!r}: no VDD field-sheet signature; ignored")
            sheets.append(SheetProfile(name=ws.title, kind="ignore"))
            continue
        if found is None:
            diagnostics.append(f"sheet {ws.title!r}: listed in FILES but no field header "
                               "signature; ignored")
            sheets.append(SheetProfile(name=ws.title, kind="ignore"))
            continue
        header_row, header = found
        band = _resolve_flat_roles(ws.title, "fields", header, vcfg.field_roles, confidence,
                                   unresolved, diagnostics)
        segment_col = band.column(Role.SEGMENT)
        sheets.append(SheetProfile(
            name=ws.title, kind="vdd_fields", header_row=header_row, bands=[band],
            segment_strategy="column" if segment_col is not None else "none",
            segment_column=segment_col))
    field_sheets = [s for s in sheets if s.kind == "vdd_fields"]
    if normalized_tables and len(field_sheets) > 1:
        keep = {s.name for s in field_sheets
                if normalize(s.name).replace(" ", "") in normalized_tables
                or any(t.endswith(normalize(s.name).replace(" ", "")) for t in normalized_tables)}
        if keep:
            for index, sp in enumerate(sheets):
                if sp.kind == "vdd_fields" and sp.name not in keep:
                    diagnostics.append(f"sheet {sp.name!r}: not among the STTM's tables "
                                       f"{sorted(sttm_tables or [])}; ignored")
                    sheets[index] = sp.model_copy(update={"kind": "ignore", "bands": []})
                    unresolved[:] = [u for u in unresolved if u.sheet != sp.name]
        else:
            diagnostics.append("no field sheet matches an STTM table name; all kept")
    if not any(s.kind in ("vdd_files", "vdd_fields") for s in sheets):
        raise NoLayoutError(f"{path.name}: no FILES sheet and no field sheet signature found; "
                            f"sheets present: {workbook.sheetnames}")
    profile = LayoutProfile(fingerprint=digest, sheets=sheets, confidence=confidence,
                            source="synonyms", strategy="vdd", unresolved=unresolved,
                            notes=list(diagnostics))
    return Discovery(profile=profile, workbook=workbook, diagnostics=diagnostics)


def _signature_row(ws, alternatives: list[list[str]]) -> tuple[int, list] | None:
    rows = [list(r) for _, r in zip(range(_AUX_SCAN_ROWS), ws.iter_rows(values_only=True),
                                    strict=False)]
    for index, row in enumerate(rows, start=1):
        cells = [normalize(c) for c in row if text(c) is not None]
        if not cells:
            continue
        for tokens in alternatives:
            if all(any(normalize(t) == c for c in cells) for t in tokens):
                return index, row
    return None


def _resolve_flat_roles(sheet: str, layer: str, header: list, synonyms: dict[str, list[str]],
                        confidence: dict[str, float], unresolved: list[UnresolvedRole],
                        diagnostics: list[str]) -> BandProfile:
    table = {role: {normalize(s) for s in spellings} for role, spellings in synonyms.items()}
    roles: dict[str, int] = {}
    last_col = max((i + 1 for i, c in enumerate(header) if text(c) is not None), default=1)
    for col in range(1, last_col + 1):
        raw = header[col - 1] if col - 1 < len(header) else None
        value = normalize(raw)
        if not value:
            continue
        matches = [role for role, spellings in table.items() if value in spellings]
        if len(matches) == 1 and matches[0] not in roles:
            roles[matches[0]] = col
            confidence[confidence_key(sheet, layer, matches[0])] = _SYNONYM_CONFIDENCE
        elif not matches:
            diagnostics.append(f"sheet {sheet!r}: {layer} header {raw!r} (column {col}) matches "
                               "no VDD synonym; left unresolved")
    band = BandProfile(layer=layer, col_start=1, col_end=last_col, roles=roles)  # type: ignore[arg-type]
    for role in REQUIRED_ROLES.get(layer, ()):  # type: ignore[call-overload]
        if band.column(role) is None:
            unresolved.append(UnresolvedRole(
                sheet=sheet, layer=layer, role=role.value,  # type: ignore[arg-type]
                reason="required VDD role has no header matching its synonyms",
                candidates=[c for c in range(1, last_col + 1) if c not in roles.values()]))
    return band


def discover(path: Path, config: ExtractorConfig,
             band_layers: dict[str, str] | None = None, *,
             legacy_mapping: bool = False) -> Discovery:
    """``band_layers`` (Chunk A): a person's answers to the band-layer
    questions, ``{"<sheet>/band[<n>]": "source" | "stage" | "standard"}`` —
    the only evidence that outranks a band title.

    A workbook with ``MAPPING-`` sheets is read by the GENERAL reader first
    (``_mapping_general_first``): the legacy MAPPING- reader is a fallback for
    when the general reader finds nothing, and the reference its result is
    proven equal to. ``legacy_mapping`` = the legacy reader only, its errors
    raised as they are (the flat ``parse_workbook`` API)."""
    from codegen.extract.workbook import WorkbookParseError

    workbook = load_document(path, config.used_range_empty_rows)
    digest = fingerprint(workbook)
    diagnostics: list[str] = []
    refused: WorkbookParseError | None = None
    if not legacy_mapping and any(n.startswith(config.mapping_sheet_prefix)
                                  for n in workbook.sheetnames):
        unified = _mapping_general_first(workbook, config, path.name, digest, diagnostics,
                                         band_layers or {})
        if unified is not None:
            profile, refused = unified
            return Discovery(profile=profile, workbook=workbook, diagnostics=diagnostics,
                             refused=refused)
    for strategy in (_mapping_prefix, _segmented_family, _content):
        try:
            if strategy is _content:
                profile = _content(workbook, config, path.name, digest, diagnostics,
                                   band_layers=band_layers)
            else:
                profile = strategy(workbook, config, path.name, digest, diagnostics)
        except WorkbookParseError as exc:
            from codegen.extract.workbook import SegmentedWorkbookError

            if (strategy is not _mapping_prefix or legacy_mapping
                    or isinstance(exc, SegmentedWorkbookError)):
                # The segmented dialect on a MAPPING- sheet keeps its explicit
                # refusal ("segmented ... not supported by this extractor").
                raise
            # Chunk A: MAPPING- sheets whose band labels / headers the legacy
            # reader refuses (another title wording, another band order, one
            # unknown header) are read by content instead of stopping the run;
            # the legacy error stands when nothing else reads the workbook.
            refused = exc
            diagnostics.append(f"{MAPPING_PREFIX_REFUSED}{exc}; routed to the other strategies")
            continue
        if profile is not None:
            return Discovery(profile=profile, workbook=workbook, diagnostics=diagnostics,
                             refused=refused)
    if refused is not None:
        raise refused
    raise NoLayoutError(
        f"{path.name}: no mapping sheets found — no discovery strategy applies "
        f"(prefix {config.mapping_sheet_prefix!r}, segmented family, content-driven); "
        f"sheets present: {workbook.sheetnames}; diagnostics: {diagnostics}"
    )


# ------------------------------------------------ strategy 1: MAPPING- prefix

def _mapping_prefix(workbook, config: ExtractorConfig, name: str, digest: str,
                    diagnostics: list[str]) -> LayoutProfile | None:
    from codegen.extract import workbook as legacy

    mapping = [n for n in workbook.sheetnames if n.startswith(config.mapping_sheet_prefix)]
    if not mapping:
        return None
    sheets: list[SheetProfile] = []
    confidence: dict[str, float] = {}
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        if sheet_name in mapping:
            bands = legacy._find_bands(ws, config)
            headers = list(next(ws.iter_rows(min_row=2, max_row=2, values_only=True)))
            recycle_col = legacy._find_recycle_column(ws, headers, config)
            source = legacy._resolve_source_headers(ws, headers, bands.source, config, recycle_col)
            stage = legacy._resolve_table_headers(
                ws, headers, bands.stage, "stage", config, recycle_col)
            standard = (
                legacy._resolve_table_headers(
                    ws, headers, bands.standard, "standard", config, recycle_col)
                if bands.standard is not None else None
            )
            source_roles = legacy.LEGACY_SOURCE_ROLES
            table_roles = legacy.LEGACY_TABLE_ROLES
            profiles = [
                BandProfile(layer="source", col_start=bands.source[0] + 1,
                            col_end=bands.source[1],
                            roles={source_roles[k].value: v + 1 for k, v in source.items()},
                            label=config.band_labels.source),
                BandProfile(layer="stage", col_start=bands.stage[0] + 1, col_end=bands.stage[1],
                            roles={table_roles[k].value: v + 1 for k, v in stage.items()},
                            label=config.band_labels.stage),
            ]
            if standard is not None and bands.standard is not None:
                profiles.append(BandProfile(
                    layer="standard", col_start=bands.standard[0] + 1,
                    col_end=bands.standard[1],
                    roles={table_roles[k].value: v + 1 for k, v in standard.items()},
                    label=config.band_labels.standard))
            if recycle_col is not None:
                # The per-row recycle column may sit anywhere (the golden
                # workbook parks it beyond the standard band); attach it to
                # the band whose span holds it, else as a trailing band.
                col = recycle_col + 1
                holder = next((b for b in profiles if b.col_start <= col <= b.col_end), None)
                if holder is not None:
                    profiles[profiles.index(holder)] = holder.model_copy(
                        update={"roles": {**holder.roles, Role.RECYCLE_FLAG.value: col}})
                else:
                    profiles.append(BandProfile(layer="rules", col_start=col, col_end=col,
                                                roles={Role.RECYCLE_FLAG.value: col}))
            for band in profiles:
                for role in band.roles:
                    confidence[confidence_key(sheet_name, band.layer, role)] = _SYNONYM_CONFIDENCE
            sheets.append(SheetProfile(name=sheet_name, kind="mapping", header_row=2,
                                       band_row=1, bands=profiles))
        elif sheet_name == config.file_details_sheet:
            headers = [str(c) for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
                       if c is not None]
            sheets.append(SheetProfile(name=sheet_name, kind="file_details", header_row=1,
                                       headers=headers))
        elif sheet_name == config.version_history_sheet:
            sheets.append(SheetProfile(name=sheet_name, kind="version"))
        else:
            diagnostics.append(f"sheet {sheet_name!r}: not a MAPPING- sheet; ignored")
            sheets.append(SheetProfile(name=sheet_name, kind="ignore"))
    return LayoutProfile(fingerprint=digest, sheets=sheets, confidence=confidence,
                         source="synonyms", strategy="mapping_prefix")


# ------------------------- Chunk A addendum: MAPPING- sheets, general reader first

# Per-row columns outside the stage / standard label groups; which band the
# legacy reader hangs them on (the last band's span runs to max_column) is a
# representation, not a reading — compared as (role, column) pairs per sheet.
_TRAILING_ROLES = frozenset({Role.RECYCLE_FLAG.value, Role.DQ_MANDATORY.value})


def _mapping_general_first(workbook, config: ExtractorConfig, name: str, digest: str,
                           diagnostics: list[str], band_layers: dict[str, str]
                           ) -> tuple[LayoutProfile, Exception | None] | None:
    """The general reader reads a workbook's ``MAPPING-`` sheets first: band
    location by band row / label groups, layers by evidence (the band question
    included), family B's own source vocabulary on those sheets. When the
    legacy reader also reads them and both agree on every role and column, the
    profile is the legacy one exactly (byte-identical for every pinned
    workbook — proven, not assumed: ``mapping_differences``). When they
    disagree or the legacy reader refuses, the general reader's bands are used
    and every difference is a diagnostic. ``None`` = the general reader finds
    nothing (or a segment column: the segmented dialect keeps the legacy
    reader's explicit refusal) — the legacy reader decides."""
    from codegen.extract.workbook import SegmentedWorkbookError, WorkbookParseError

    names = [n for n in workbook.sheetnames if n.startswith(config.mapping_sheet_prefix)]
    general_notes: list[str] = []
    general = _content(workbook, config, name, digest, general_notes, band_layers=band_layers)
    found = [s for s in (general.sheets if general is not None else [])
             if s.kind == "mapping" and s.name in names]
    if general is None or not found:
        diagnostics.append("MAPPING- sheets: the general reader finds no band on them; the "
                           "legacy MAPPING- reader reads the workbook")
        return None
    if any(s.segment_column is not None or s.segment_strategy == "banner" for s in found):
        return None
    legacy_notes: list[str] = []
    refused: Exception | None = None
    try:
        legacy = _mapping_prefix(workbook, config, name, digest, legacy_notes)
    except SegmentedWorkbookError:
        raise
    except WorkbookParseError as exc:
        legacy, refused = None, exc
    if legacy is not None:
        differences = mapping_differences(legacy, general, names)
        if not differences:
            diagnostics.extend(legacy_notes)
            return legacy, None
        diagnostics.extend(f"MAPPING- readers disagree (the general reader's bands are used): "
                           f"{d}" for d in differences)
    else:
        diagnostics.append(f"{MAPPING_PREFIX_REFUSED}{refused}; the general reader's bands "
                           "are used")
    diagnostics.extend(general_notes)
    strategy = "mapping_prefix" if legacy_readable(general, names) else "content"
    return general.model_copy(update={"strategy": strategy}), refused


def mapping_differences(legacy: LayoutProfile, general: LayoutProfile,
                        names: list[str]) -> list[str]:
    """Every difference between the legacy MAPPING- reader's profile and the
    general reader's on ``names``: header / band rows, the source, stage and
    standard roles (role -> column), the per-row trailing columns, and any
    role the general reader leaves open. Empty = the same reading."""
    out: list[str] = []
    for n in names:
        ls, gs = legacy.sheet(n), general.sheet(n)
        if ls is None or ls.kind != "mapping":
            continue
        if gs is None or gs.kind != "mapping":
            out.append(f"{n}: the general reader reads no mapping sheet")
            continue
        if (ls.header_row, ls.band_row) != (gs.header_row, gs.band_row):
            out.append(f"{n}: header / band row legacy {(ls.header_row, ls.band_row)}, "
                       f"general {(gs.header_row, gs.band_row)}")
        for layer in ("source", "stage", "standard"):
            lb, gb = ls.band(layer), gs.band(layer)  # type: ignore[arg-type]
            lr = {r: c for r, c in (lb.roles if lb else {}).items() if r not in _TRAILING_ROLES}
            gr = {r: c for r, c in (gb.roles if gb else {}).items() if r not in _TRAILING_ROLES}
            if lr != gr:
                out.append(f"{n}/{layer}: legacy {lr}, general {gr}")
        lt = sorted((r, c) for b in ls.bands for r, c in b.roles.items() if r in _TRAILING_ROLES)
        gt = sorted((r, c) for b in gs.bands for r, c in b.roles.items() if r in _TRAILING_ROLES)
        if lt != gt:
            out.append(f"{n}: per-row columns legacy {lt}, general {gt}")
        open_roles = [f"{u.layer}/{u.role}" for u in general.unresolved_for(n)]
        if open_roles:
            out.append(f"{n}: the general reader leaves {open_roles} open")
    return out


def legacy_readable(profile: LayoutProfile, names: list[str]) -> bool:
    """The legacy MAPPING- extractor can read through ``profile``: every
    MAPPING- mapping sheet places the source roles it requires and the four
    target roles per band, and nothing is open (a band question holds the
    workbook on the generic extractor, which holds the sheet back)."""
    from codegen.extract.workbook import (
        LEGACY_REQUIRED_SOURCE,
        LEGACY_SOURCE_ROLES,
        LEGACY_TABLE_ROLES,
    )

    source_roles = {LEGACY_SOURCE_ROLES[k].value for k in LEGACY_REQUIRED_SOURCE}
    table_roles = {r.value for r in LEGACY_TABLE_ROLES.values()}
    sheets = [s for s in profile.mapping_sheets if s.name in names]
    if not sheets or profile.unresolved:
        return False
    for sp in sheets:
        source, stage = sp.band("source"), sp.band("stage")
        if source is None or stage is None or not source_roles <= set(source.roles):
            return False
        for band in (stage, sp.band("standard")):
            if band is not None and not table_roles <= set(band.roles):
                return False
    return True


# ------------------------------------------ strategy 2: segmented (CAQH) family

# Segmented logical names (codegen.extract.segmented) -> roles.
SEGMENTED_SOURCE_ROLES = {
    "ordinal": Role.ORDINAL,
    "field_name": Role.FIELD_NAME,
    "datatype": Role.SOURCE_TYPE,
    "length": Role.LENGTH,
    "fixed_width_length": Role.FIELD_LENGTH,
    "fixed_width_start": Role.START,
    "fixed_width_end": Role.END,
    "segment": Role.SEGMENT,
    "pii": Role.PII,
    "comments": Role.COMMENTS,
    "business_rule": Role.BUSINESS_RULE,
}
SEGMENTED_TABLE_ROLES = {
    "catalog": Role.CATALOG,
    "schema": Role.SCHEMA,
    "tablename": Role.TABLE,
    "columnname": Role.COLUMN,
    "datatype": Role.TARGET_TYPE,
    "mandatory column": Role.MANDATORY_COLUMN,
    "primary key": Role.PRIMARY_KEY,
    "field description": Role.FIELD_DESCRIPTION,
    "table description": Role.TABLE_DESCRIPTION,
    "transformations/data quality": Role.TRANSFORMATION,
}
SEGMENTED_FAMILY_NOTE = (
    "matches the segmented (metadata-block + band-row) layout family — see "
    "docs/SEGMENTED_MODE_DESIGN.md"
)


def _segmented_family(workbook, config: ExtractorConfig, name: str, digest: str,
                      diagnostics: list[str]) -> LayoutProfile | None:
    from codegen.extract import segmented as legacy
    from codegen.extract.workbook import WorkbookParseError, _norm

    seg = config.segmented
    labels = config.band_labels
    band_vocabulary = (
        {_norm(labels.source), _norm(labels.stage), _norm(labels.standard)}
        | {_norm(v) for v in seg.source_band_variants}
    )
    try:
        ws, band_index, rows = legacy._find_mapping_sheet(workbook, seg, band_vocabulary, name)
    except WorkbookParseError as exc:
        if "no sheet matches" in str(exc):
            return None
        diagnostics.append(f"segmented family signature: {exc}")
        return None
    diagnostics.append(f"sheet {ws.title!r}: {SEGMENTED_FAMILY_NOTE}")
    band_starts: dict[str, int] = {}
    source_variants = {_norm(labels.source)} | {_norm(v) for v in seg.source_band_variants}
    for index, cell in enumerate(rows[band_index]):
        value = _norm(cell)
        if not value:
            continue
        if value in source_variants:
            band_starts["source"] = index
        elif value == _norm(labels.stage):
            band_starts["stage"] = index
        elif value == _norm(labels.standard):
            band_starts["standard"] = index
    missing = [layer for layer in ("source", "stage") if layer not in band_starts]
    if missing:
        # The band row shares SOME of the family's labels (e.g. "Stage Layer"
        # under a plain "Source" band) — not this family; content-driven
        # discovery reads it (multi-table, 2026-10-07).
        diagnostics.append(
            f"sheet {ws.title!r}: segmented family band labels incomplete (no "
            f"{' / '.join(missing)} band); routed to content-driven discovery")
        return None
    try:
        facts = legacy._parse_metadata_block(rows, band_index, seg, ws.title)
        max_col = max(len(r) for r in rows) - 1
        header = list(rows[band_index + 1])
        blocks = legacy._resolve_blocks(header, band_starts, max_col, seg, ws.title)
    except WorkbookParseError as exc:
        diagnostics.append(
            f"sheet {ws.title!r}: segmented family signature matched but the segmented "
            f"extractor cannot resolve it ({exc}); routed to content-driven discovery")
        return None
    del facts
    stage_end = band_starts.get("standard", max_col + 1)
    bands = [
        BandProfile(layer="source", col_start=band_starts["source"] + 1,
                    col_end=band_starts["stage"],
                    roles={SEGMENTED_SOURCE_ROLES[k].value: v + 1
                           for k, v in blocks.source.items()},
                    label=text(rows[band_index][band_starts["source"]])),
        BandProfile(layer="stage", col_start=band_starts["stage"] + 1, col_end=stage_end,
                    roles={SEGMENTED_TABLE_ROLES[k].value: v + 1 for k, v in blocks.stage.items()},
                    label=text(rows[band_index][band_starts["stage"]])),
    ]
    if blocks.standard is not None and "standard" in band_starts:
        bands.append(BandProfile(
            layer="standard", col_start=band_starts["standard"] + 1, col_end=max_col + 1,
            roles={SEGMENTED_TABLE_ROLES[k].value: v + 1 for k, v in blocks.standard.items()},
            label=text(rows[band_index][band_starts["standard"]])))
    wanted = {_norm(label): logical for logical, label in seg.metadata_keys.items()}
    meta_rows = []
    for row_index, row in enumerate(rows[:band_index], start=1):
        label = text(row[0]) if row else None
        if label is None:
            continue
        meta_rows.append(MetaRow(row=row_index, col=1, label=label, key=wanted.get(_norm(label)),
                                 value_col=2))
    confidence = {confidence_key(ws.title, b.layer, r): _SYNONYM_CONFIDENCE
                  for b in bands for r in b.roles}
    sheets = []
    for sheet_name in workbook.sheetnames:
        if sheet_name == ws.title:
            sheets.append(SheetProfile(
                name=sheet_name, kind="mapping", header_row=band_index + 2,
                band_row=band_index + 1, bands=bands, meta_rows=meta_rows,
                segment_strategy="column", segment_column=blocks.source["segment"] + 1,
                notes=[SEGMENTED_FAMILY_NOTE]))
        else:
            diagnostics.append(f"sheet {sheet_name!r}: not the segmented mapping sheet; ignored")
            sheets.append(SheetProfile(name=sheet_name, kind="ignore"))
    return LayoutProfile(fingerprint=digest, sheets=sheets, confidence=confidence,
                         source="synonyms", strategy="segmented_family",
                         notes=[f"{ws.title}: {SEGMENTED_FAMILY_NOTE}"])


# -------------------------------------------- strategy 3: content-driven

_LAYER_ORDER = ("stage", "standard", "rules", "source")


def _band_layer(label: str, tokens: dict[str, list[str]]) -> str | None:
    normalized = normalize(label)
    for layer in _LAYER_ORDER:
        for token in tokens.get(layer, []):
            if normalize(token) in normalized:
                return layer
    return None


def _has_token(cells: list[str], tokens: list[str]) -> bool:
    return any(normalize(t) in c for c in cells for t in tokens if c)


def _content(workbook, config: ExtractorConfig, name: str, digest: str,
             diagnostics: list[str], band_layers: dict[str, str] | None = None
             ) -> LayoutProfile | None:
    disc = config.discovery
    if not disc.roles or not disc.band_tokens:
        diagnostics.append("content-driven discovery: extractor.discovery vocabulary is empty")
        return None
    # Pass 1: mapping sheets found by a band row naming stage AND standard (or
    # layer prefixes in the header texts) — the reading of every workbook
    # before 2026-10-09. Pass 2 (Chunk A), only when pass 1 finds NO mapping
    # sheet: a header row carrying a target-shaped label group makes a mapping
    # sheet (one band only, other title wording, no title row). A workbook
    # with mapping sheets keeps exactly its pass-1 set — a reference sheet
    # beside them ("STG - Dest 1 | STD - Dest2") is never read as a feed; a
    # sheet pass 2 would have taken is named in the diagnostics.
    for fallback in (False, True):
        sheets: list[SheetProfile] = []
        confidence: dict[str, float] = {}
        unresolved: list[UnresolvedRole] = []
        notes: list[str] = []
        for sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]
            mapping = _discover_mapping_sheet(ws, disc, config, confidence, unresolved, notes,
                                              band_layers=band_layers or {},
                                              group_fallback=fallback)
            if mapping is not None:
                sheets.append(mapping)
                continue
            sheets.append(_classify_auxiliary(ws, disc, notes))
        if any(s.kind == "mapping" for s in sheets):
            break
    mapping_sheets = [s for s in sheets if s.kind == "mapping"]
    if not mapping_sheets:
        diagnostics.extend(notes)
        return None
    if not fallback:
        for sp in sheets:
            if sp.kind != "mapping" and _group_header_row(workbook[sp.name], disc) is not None:
                notes.append(f"sheet {sp.name!r}: a header row carries target-shaped columns but "
                             "no band row names stage and standard; not read as a mapping sheet "
                             f"(the workbook's mapping sheets: {[s.name for s in mapping_sheets]})")
    diagnostics.extend(notes)
    sheets = _apply_sheet_segments(sheets, disc)
    return LayoutProfile(fingerprint=digest, sheets=sheets, confidence=confidence,
                         source="synonyms", strategy="content", unresolved=unresolved,
                         notes=list(diagnostics))


def _discover_mapping_sheet(ws, disc: DiscoveryConfig, config: ExtractorConfig,
                            confidence: dict[str, float], unresolved: list[UnresolvedRole],
                            diagnostics: list[str], band_layers: dict[str, str] | None = None,
                            group_fallback: bool = False) -> SheetProfile | None:
    rows = [list(r) for _, r in zip(range(disc.scan_rows),
                                    ws.iter_rows(values_only=True), strict=False)]
    band_index: int | None = None
    header_index: int | None = None
    field_tokens = disc.roles.get("source", {}).get(Role.FIELD_NAME.value, [])
    for index, row in enumerate(rows):
        cells = [normalize(c) for c in row]
        if not (_has_token(cells, disc.band_tokens.get("stage", []))
                and _has_token(cells, disc.band_tokens.get("standard", []))):
            continue
        below = rows[index + 1] if index + 1 < len(rows) else []
        below_cells = [normalize(c) for c in below]
        filled = sum(1 for c in cells if c)
        # (a) band row + header row beneath carrying a field-name header;
        # (b) the token row IS the header row (layer prefixes in the texts);
        # (c) a sparse band row (a few labels) over a wide header row whose
        #     field-name header is not in the vocabulary (pinned unresolved).
        if _has_token(below_cells, field_tokens):
            band_index, header_index = index, index + 1
            break
        if _has_token(cells, field_tokens):
            header_index = index
            break
        if (filled <= _MAX_BAND_LABELS
                and sum(1 for c in below_cells if c) >= _MIN_HEADER_CELLS):
            band_index, header_index = index, index + 1
            break
    legacy_found = header_index is not None
    if header_index is None:
        # Chunk A: no row carries both a stage and a standard token — the
        # sheet is still a mapping sheet when a header row carries a
        # target-shaped label group (one band only, another title wording,
        # no title row at all).
        header_index = _group_header_row(ws, disc, rows) if group_fallback else None
        if header_index is None:
            return None
        if header_index > 0 and _is_title_row(rows[header_index - 1],
                                              label_groups(rows[header_index], disc), disc):
            band_index = header_index - 1
    header = rows[header_index]
    last_col = max((i + 1 for i, c in enumerate(header) if text(c) is not None), default=0)
    groups = label_groups(header, disc)
    titles = (_title_spans(ws, rows[band_index], band_index + 1, last_col)
              if band_index is not None else [])
    _assign_layers(ws, groups, titles, header, header_index + 1, disc, band_layers or {})
    legacy: list[BandProfile] | None = None
    if legacy_found:
        legacy = (_bands_from_band_row(ws, rows[band_index], band_index + 1, last_col, disc)
                  if band_index is not None
                  else _bands_from_header_prefixes(header, last_col, disc))
    notes: list[str] = []
    if legacy is not None and _legacy_consistent(legacy, groups):
        # The band row / header prefixes and the label groups agree: the
        # profile is exactly the one read before 2026-10-09.
        bands = legacy
        if band_index is not None:
            notes.append(f"band row {band_index + 1}, header row {header_index + 1}")
        else:
            notes.append(f"no band row; layer prefixes in header row {header_index + 1}")
    else:
        bands = _bands_from_groups(header, last_col, groups, titles, disc)
        if not any(b.layer in ("stage", "standard") for b in bands) and not any(
                g.layer is None for g in groups):
            return None
        notes.append((f"band row {band_index + 1}, header row {header_index + 1}"
                       if band_index is not None else f"no band row; header row {header_index + 1}")
                     + "; bands located by their label groups (Chunk A)")
        for g in groups:
            notes.append(f"{band_ref(g.index)} {_span_text(g.start, g.end)}: "
                         + (f"{g.layer} ({g.evidence})" if g.layer else "layer unresolved"))
    if not _has_token([normalize(c) for c in header],
                      disc.roles.get("source", {}).get(Role.FIELD_NAME.value, [])):
        notes.append("header row carries no field-name synonym; field_name unresolved")
    resolved_bands: list[BandProfile] = []
    for band in bands:
        resolved_bands.append(_resolve_band_roles(ws.title, band, header, disc, confidence,
                                                  unresolved, diagnostics,
                                                  bands_before=list(resolved_bands),
                                                  extractor=config))
    meta_rows = _meta_rows(rows[: (band_index if band_index is not None else header_index)], disc,
                           ws.title, diagnostics)
    source = next((b for b in resolved_bands if b.layer == "source"), None)
    segment_column = source.column(Role.SEGMENT) if source is not None else None
    if segment_column is not None:
        strategy = "column"
    elif _has_banner_rows(ws, header_index + 1, resolved_bands, disc):
        strategy = "banner"
        notes.append("segments introduced by in-sheet label rows spanning the source group")
    else:
        strategy = "none"
    for layer, required in REQUIRED_ROLES.items():
        band = next((b for b in resolved_bands if b.layer == layer), None)
        if band is None:
            continue
        for role in required:
            if band.column(role) is None and not any(
                    u.sheet == ws.title and u.layer == layer and u.role == role.value
                    for u in unresolved):
                unresolved.append(UnresolvedRole(
                    sheet=ws.title, layer=layer, role=role.value,
                    reason="required role has no header matching its synonyms",
                    candidates=[c for c in range(band.col_start, band.col_end + 1)
                                if c not in band.roles.values()]))
    if bands is not legacy:
        for g in groups:
            if g.layer is None:
                unresolved.append(UnresolvedRole(
                    sheet=ws.title, layer=band_ref(g.index), role=BAND_LAYER_ROLE,
                    reason=_band_reason(g, header), candidates=list(range(g.start, g.end + 1))))
    for entry in notes:
        diagnostics.append(f"sheet {ws.title!r}: {entry}")
    return SheetProfile(name=ws.title, kind="mapping", header_row=header_index + 1,
                        band_row=None if band_index is None else band_index + 1,
                        bands=resolved_bands, meta_rows=meta_rows,
                        segment_strategy=strategy, segment_column=segment_column, notes=notes)


def _bands_from_band_row(ws, band_row: list, band_row_number: int, last_col: int,
                         disc: DiscoveryConfig) -> list[BandProfile]:
    labels = [(i + 1, text(c)) for i, c in enumerate(band_row) if text(c) is not None]
    merged = {r.min_col: r.max_col for r in ws.merged_cells.ranges
              if r.min_row == band_row_number and r.max_row == band_row_number}
    bands: list[BandProfile] = []
    for position, (col, label) in enumerate(labels):
        if col in merged:
            end = merged[col]
        elif position + 1 < len(labels):
            end = labels[position + 1][0] - 1
        else:
            end = max(last_col, col)
        layer = _band_layer(label, disc.band_tokens)
        if layer is None:
            layer = "source" if position == 0 else "rules"
        bands.append(BandProfile(layer=layer, col_start=col, col_end=end, label=label))
    covered_to = max((b.col_end for b in bands), default=0)
    if last_col > covered_to:
        bands.append(BandProfile(layer="rules", col_start=covered_to + 1, col_end=last_col,
                                 label=None))
    return bands


def _bands_from_header_prefixes(header: list, last_col: int,
                                disc: DiscoveryConfig) -> list[BandProfile]:
    layers: list[str | None] = []
    for col in range(1, last_col + 1):
        value = normalize(header[col - 1]) if col - 1 < len(header) else ""
        layer = None
        for candidate in ("stage", "standard"):
            if any(value.startswith(normalize(t)) for t in disc.band_tokens.get(candidate, [])):
                layer = candidate
                break
        layers.append(layer)
    first_stage = next((i for i, layer in enumerate(layers) if layer == "stage"), None)
    last_target = max((i for i, layer in enumerate(layers) if layer in ("stage", "standard")),
                      default=-1)
    bands: list[BandProfile] = []
    if first_stage is None:
        return bands
    bands.append(BandProfile(layer="source", col_start=1, col_end=first_stage, label=None))
    for layer in ("stage", "standard"):
        cols = [i + 1 for i, item in enumerate(layers) if item == layer]
        if cols:
            bands.append(BandProfile(layer=layer, col_start=min(cols), col_end=max(cols),
                                     label=None))
    if last_target + 1 < last_col:
        bands.append(BandProfile(layer="rules", col_start=last_target + 2, col_end=last_col,
                                 label=None))
    return bands


# ------------------------- Chunk A (2026-10-09): label groups + layer evidence

# A target band's location roles, in the order a band states them (workspace
# before catalog …): a role ranked BELOW the previous one, once the run holds
# two location roles, starts the next band ("… ColumnName | DataType |
# Catalog | Schema …" is two bands, never one).
_LOCATION_RANK = {Role.WORKSPACE.value: -1, Role.CATALOG.value: 0, Role.SCHEMA.value: 1,
                  Role.TABLE.value: 2, Role.COLUMN.value: 3, Role.TARGET_TYPE.value: 4}
_LOCATION_ROLES = (Role.CATALOG.value, Role.SCHEMA.value, Role.TABLE.value, Role.COLUMN.value,
                   Role.TARGET_TYPE.value)
_NAMED_LAYERS = ("source", "stage", "standard")


@dataclass
class LabelGroup:
    """A target-shaped run of header cells — one band's label group
    (Catalog / Schema / TableName / ColumnName / DataType / Mandatory / Primary
    Key …, the ``roles.target`` synonyms), wherever it sits in the header row."""

    index: int                     # 1-based among the sheet's label groups
    start: int
    end: int
    roles: dict[str, int]          # target role -> column (1-based)
    layer: str | None = None       # source | rules | stage | standard; None = open
    evidence: str | None = None    # profile.LayerEvidence
    seen: list[str] = field(default_factory=list)

    @property
    def location_columns(self) -> list[int]:
        return [c for r, c in self.roles.items() if r in _LOCATION_ROLES]


def _words(value: object) -> set[str]:
    return set(normalize(value).split())


def _span_text(start: int, end: int) -> str:
    from openpyxl.utils import get_column_letter

    first, last = get_column_letter(start), get_column_letter(end)
    return f"(column {first})" if start == end else f"(columns {first}–{last})"


def label_groups(header: list, disc: DiscoveryConfig) -> list[LabelGroup]:
    """Every target-shaped band of a header row: a run of ``roles.target``
    headers placing at least ``group_min_location_roles`` of catalog / schema
    / table / column / data type, column or data type among them (a Table
    Details sheet's Catalog | Schema | Table Name is not a band). Order inside
    a band is free ("TableName | ColumnName | Schema | DataType" is one band);
    a run closes after more than ``group_max_gap`` other header cells, and a
    REPEATED role splits it — at the location-rank drop between the two
    occurrences that restarts lowest ("Data Type | Schema | TableName |
    ColumnName | DataType": the source's type is not the stage band's), else
    just before the repeat. A piece's leading non-location roles (a rules
    band's Primary Key beside the stage band) are not its own."""
    ev = disc.layer_evidence
    table = {role: {normalize(s) for s in spellings}
             for role, spellings in disc.roles.get("target", {}).items()}
    last_col = max((i + 1 for i, c in enumerate(header) if text(c) is not None), default=0)
    runs: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    gap = 0
    for col in range(1, last_col + 1):
        value = normalize(header[col - 1]) if col - 1 < len(header) else ""
        matches = [role for role, spellings in table.items() if value and value in spellings]
        if len(matches) != 1:
            if current:
                gap += 1
                if gap > ev.group_max_gap:
                    runs.append(current)
                    current, gap = [], 0
            continue
        gap = 0
        current.append((col, matches[0]))
    if current:
        runs.append(current)
    pieces: list[list[tuple[int, str]]] = []
    for run in runs:
        start = 0
        seen: dict[str, int] = {}
        for i, (_col, role) in enumerate(run):
            if role in seen:
                split = _split_point(run, seen[role], i)
                pieces.append(run[start:split])
                start = split
                seen = {r: k for k, (_c, r) in enumerate(run[start:i], start=start)}
            seen[role] = i
        pieces.append(run[start:])
    groups: list[LabelGroup] = []
    for piece in pieces:
        located = [c for c, r in piece if r in _LOCATION_RANK]
        if not located:
            continue
        kept = {r: c for c, r in piece if c >= min(located)}
        if (sum(1 for r in kept if r in _LOCATION_ROLES) >= ev.group_min_location_roles
                and {Role.COLUMN.value, Role.TARGET_TYPE.value} & set(kept)):
            groups.append(LabelGroup(index=len(groups) + 1, start=min(kept.values()),
                                     end=max(kept.values()), roles=kept))
    return groups


def _split_point(run: list[tuple[int, str]], first: int, repeat: int) -> int:
    """Where the next band starts in ``run`` (first < k <= repeat): the
    location-rank drop whose restarting rank is lowest (the latest on a tie),
    else the repeated cell itself."""
    best: tuple[int, int] | None = None
    previous: int | None = None
    for k in range(first, repeat + 1):
        rank = _LOCATION_RANK.get(run[k][1])
        if rank is None:
            continue
        if previous is not None and rank < previous and k > first and (
                best is None or rank <= best[1]):
            best = (k, rank)
        previous = rank
    return best[0] if best is not None else repeat


def _group_header_row(ws, disc: DiscoveryConfig, rows: list[list] | None = None) -> int | None:
    """0-based index of the first scanned row that reads as a mapping header
    by its label groups: two or more groups, or one group plus a field-name
    header outside it (an auxiliary sheet with one table-shaped group — Table
    Details, a dictionary — is not a mapping sheet)."""
    if rows is None:
        rows = [list(r) for _, r in zip(range(disc.scan_rows),
                                        ws.iter_rows(values_only=True), strict=False)]
    fields = {normalize(s) for s in disc.roles.get("source", {}).get(Role.FIELD_NAME.value, [])}
    for i, row in enumerate(rows):
        groups = label_groups(row, disc)
        if len(groups) >= 2:
            return i
        if groups and any(normalize(cell) in fields for col, cell in enumerate(row, start=1)
                          if not any(g.start <= col <= g.end for g in groups)):
            return i
    return None


def _title_spans(ws, band_row: list, band_row_number: int, last_col: int
                 ) -> list[tuple[int, int, str]]:
    """(start, end, label) per band title — a merged range, else up to the
    next title (the reading ``_bands_from_band_row`` uses)."""
    labels = [(i + 1, text(c)) for i, c in enumerate(band_row) if text(c) is not None]
    merged = {r.min_col: r.max_col for r in ws.merged_cells.ranges
              if r.min_row == band_row_number and r.max_row == band_row_number}
    spans = []
    for position, (col, label) in enumerate(labels):
        if col in merged:
            end = merged[col]
        elif position + 1 < len(labels):
            end = labels[position + 1][0] - 1
        else:
            end = max(last_col, col)
        spans.append((col, end, str(label)))
    return spans


def _title_layer(label: str, disc: DiscoveryConfig) -> str | None:
    """The one layer a band title names (``layer_evidence.titles`` words, or
    a ``band_tokens`` token as the band row reads it); None = none / several."""
    words = _words(label)
    norm = normalize(label)
    layers = {layer for layer, tokens in disc.layer_evidence.titles.items()
              if words & {normalize(t) for t in tokens}}
    layers |= {layer for layer, tokens in disc.band_tokens.items()
               if any(normalize(t) and normalize(t) in norm for t in tokens)}
    named = layers & set(_NAMED_LAYERS)
    if len(named) == 1:
        return named.pop()
    if not named and "rules" in layers:
        return "rules"
    return None


def _is_title_row(row: list, groups: list[LabelGroup], disc: DiscoveryConfig) -> bool:
    """The row above a group-located header is its band title row when it
    is sparse and a cell names a layer or sits over a label group."""
    cells = [(i + 1, text(c)) for i, c in enumerate(row) if text(c) is not None]
    if not cells or len(cells) > _MAX_BAND_LABELS + len(groups):
        return False
    # A label:value meta row ("Notes | standard tables reload nightly") is
    # never a title row, nor is a row of prose.
    meta = {normalize(s) for spellings in disc.meta_synonyms.values() for s in spellings}
    if normalize(cells[0][1]) in meta or any(len(str(label).split()) > 6 for _, label in cells):
        return False
    if any(_title_layer(str(label), disc) for _, label in cells):
        return True
    return any(g.start <= col <= g.end for col, _ in cells for g in groups)


def _column_values(ws, header_row: int, col: int, limit: int) -> list[str]:
    values = []
    for row in ws.iter_rows(min_row=header_row + 1, max_row=header_row + limit,
                            min_col=col, max_col=col, values_only=True):
        value = text(row[0]) if row else None
        if value is not None:
            values.append(value)
    return values


def _value_layers(ws, header_row: int, col: int, kind: str, disc: DiscoveryConfig) -> set[str]:
    """The layers a band's Catalog (``catalog_value``) / Schema
    (``schema_value``) VALUES name — word / prefix matches."""
    ev = disc.layer_evidence
    layers: set[str] = set()
    for value in _column_values(ws, header_row, col, ev.value_scan_rows):
        if kind == "catalog_value":
            words = _words(value)
            layers |= {layer for layer, tokens in ev.catalog_words.items()
                       if words & {normalize(t) for t in tokens}}
        else:
            lowered = value.strip().lower()
            layers |= {layer for layer, prefixes in ev.schema_prefixes.items()
                       if any(lowered.startswith(p.lower()) for p in prefixes if p)}
    return layers


def _assign_layers(ws, groups: list[LabelGroup], titles: list[tuple[int, int, str]],
                   header: list, header_row: int, disc: DiscoveryConfig,
                   band_layers: dict[str, str]) -> None:
    """Each group's layer from EVIDENCE only — an answer, the band title over
    its location columns, a word of its headers, its Catalog values, its
    Schema values (first that names exactly one layer wins). Two bands
    naming the same target layer both stay open (unless one was answered).
    Column order is never evidence."""
    words_by_layer = {layer: {normalize(t) for t in tokens}
                      for layer, tokens in disc.layer_evidence.header_words.items()}
    for g in groups:
        answer = band_layers.get(f"{ws.title}/{band_ref(g.index)}")
        if answer in BAND_LAYER_CHOICES:
            g.layer, g.evidence = answer, "answer"
            continue
        # 1. the band title row
        over = [(s, e, label) for s, e, label in titles
                if any(s <= c <= e for c in g.location_columns)]
        named = {_title_layer(label, disc) for _, _, label in over} - {None}
        if len(named) == 1:
            g.layer, g.evidence = named.pop(), "title"
            continue
        g.seen.append("no band title over it" if not over else
                      "band title(s) " + ", ".join(repr(label) for _, _, label in over)
                      + (" name no layer" if not named else f" name {sorted(named)}"))
        # 2. a word of its own header texts
        words = set().union(*(_words(header[c - 1]) for c in g.roles.values()))
        named = {layer for layer, tokens in words_by_layer.items() if words & tokens}
        if len(named) == 1:
            g.layer, g.evidence = named.pop(), "header"
            continue
        g.seen.append("no layer word in its headers" if not named
                      else f"its headers name {sorted(named)}")
        # 3. / 4. its Catalog values, its Schema values
        decided = False
        for kind, role, what in (("catalog_value", Role.CATALOG.value, "Catalog"),
                                 ("schema_value", Role.SCHEMA.value, "Schema")):
            col = g.roles.get(role)
            if col is None:
                g.seen.append(f"no {what} column")
                continue
            named = _value_layers(ws, header_row, col, kind, disc)
            if len(named) == 1:
                g.layer, g.evidence = named.pop(), kind
                decided = True
                break
            g.seen.append(f"its {what} values {_span_text(col, col)} carry no layer "
                          + ("pattern" if kind == "catalog_value" else "prefix")
                          if not named else f"its {what} values name {sorted(named)}")
        if not decided:
            g.layer = g.evidence = None
    for layer in ("stage", "standard"):
        claimants = [g for g in groups if g.layer == layer]
        if len(claimants) < 2:
            continue
        answered = [g for g in claimants if g.evidence == "answer"]
        keep = answered[0] if len(answered) == 1 else None
        refs = " and ".join(band_ref(g.index) for g in claimants)
        kinds = ", ".join(f"{band_ref(o.index)}: {o.evidence}" for o in claimants)
        answered_note = f"; {band_ref(keep.index)} was answered {layer}" if keep else ""
        for g in claimants:
            if g is keep:
                continue
            g.seen.append(f"{refs} each read as {layer} ({kinds}){answered_note}")
            g.layer = g.evidence = None
    # A layer is claimed once: with stage AND standard each held by an
    # evidenced band, the ONE band left open is the source (a database-shaped
    # source band under a title that names no layer).
    open_groups = [g for g in groups if g.layer is None]
    if len(open_groups) == 1 and {g.layer for g in groups} >= {"stage", "standard"}:
        open_groups[0].layer, open_groups[0].evidence = "source", "elimination"


def _band_reason(g: LabelGroup, header: list) -> str:
    headers = " | ".join(str(text(header[c - 1])) for c in range(g.start, g.end + 1)
                         if c - 1 < len(header) and text(header[c - 1]) is not None)
    seen = "; ".join(s for s in g.seen if s) or "no layer evidence"
    return (f"{band_ref(g.index)} {_span_text(g.start, g.end)}: {headers} — {seen}; "
            f"answer under answers: with {' | '.join(BAND_LAYER_CHOICES)}")


def _legacy_consistent(bands: list[BandProfile], groups: list[LabelGroup]) -> bool:
    """True when the band row / header-prefix reading and the evidence agree:
    every label group's location columns sit in exactly one band of the
    layer its evidence names, and no target band holds two groups."""
    for g in groups:
        if g.layer is None:
            return False
        holders = [b for b in bands
                   if all(b.col_start <= c <= b.col_end for c in g.location_columns)]
        if len(holders) != 1 or holders[0].layer != g.layer:
            return False
    for b in bands:
        if b.layer in ("stage", "standard") and sum(
                1 for g in groups
                if all(b.col_start <= c <= b.col_end for c in g.location_columns)) > 1:
            return False
    return True


def _bands_from_groups(header: list, last_col: int, groups: list[LabelGroup],
                       titles: list[tuple[int, int, str]], disc: DiscoveryConfig
                       ) -> list[BandProfile]:
    """Bands built from the label groups: a group with a layer is that band
    (``layer_evidence`` records what named it), an open group belongs to no
    band; a titled stage / standard band whose headers form no group keeps
    its title's columns; the remaining columns are the source band (the run
    holding the field-name header, else beside a source group, else the
    leftmost run — the source band is located by content, it is never a
    layer question) and rules bands."""
    owner: dict[int, str] = {}
    evidence: dict[str, str | None] = {}
    for g in groups:
        for c in range(g.start, g.end + 1):
            owner[c] = g.layer if g.layer is not None else "?"
        if g.layer in _NAMED_LAYERS:
            evidence.setdefault(g.layer, g.evidence)
    taken = {g.layer for g in groups if g.layer in ("stage", "standard")}
    for start, end, label in titles:
        layer = _title_layer(label, disc)
        if layer is None or (layer in ("stage", "standard") and layer in taken):
            continue
        if layer in ("stage", "standard"):
            taken.add(layer)
            evidence.setdefault(layer, "title")
        for c in range(start, min(end, last_col) + 1):
            owner.setdefault(c, layer)

    def named(c: int) -> bool:
        return c - 1 < len(header) and text(header[c - 1]) is not None

    # Maximal runs of unowned columns (blank header cells inside a run kept,
    # trimmed at its ends), with the owners on either side of the run.
    runs: list[tuple[list[int], str | None, str | None]] = []
    current: list[int] = []
    for c in range(1, last_col + 2):
        if c <= last_col and c not in owner:
            current.append(c)
            continue
        cells = [x for x in current if named(x)]
        if cells:
            runs.append((list(range(cells[0], cells[-1] + 1)),
                         owner.get(current[0] - 1), owner.get(current[-1] + 1)))
        current = []
    fields = {normalize(s) for s in disc.roles.get("source", {}).get(Role.FIELD_NAME.value, [])}
    chosen: list[int] | None = None
    if "source" not in owner.values():
        chosen = next((r for r, _, _ in runs
                       if any(normalize(header[c - 1]) in fields for c in r if named(c))),
                      runs[0][0] if runs else None)
    for run, left, right in runs:
        layer = "source" if run is chosen or "source" in (left, right) else "rules"
        for c in run:
            owner[c] = layer
    bands: list[BandProfile] = []
    col = 1
    while col <= last_col:
        layer = owner.get(col)
        if layer is None or layer == "?":
            col += 1
            continue
        start = col
        while col + 1 <= last_col and owner.get(col + 1) == layer:
            col += 1
        label = next((lab for s, e, lab in titles if s <= start <= e),
                     next((lab for s, e, lab in titles if s <= col and e >= start), None))
        bands.append(BandProfile(layer=layer, col_start=start, col_end=col,  # type: ignore[arg-type]
                                 label=label, layer_evidence=evidence.get(layer)))
        col += 1
    return bands


def value_layer(ws, header_row: int, band: BandProfile, disc: DiscoveryConfig
                ) -> tuple[str | None, str | None]:
    """(layer, evidence kind) the band's VALUES name, in evidence order:
    its Catalog values, then its Schema values; (None, None) when neither
    names exactly one layer."""
    for kind, role in (("catalog_value", Role.CATALOG), ("schema_value", Role.SCHEMA)):
        col = band.column(role)
        if col is None:
            continue
        layers = _value_layers(ws, header_row, col, kind, disc)
        if len(layers) == 1:
            return layers.pop(), kind
    return None, None


def stale_value_evidence(profile: LayoutProfile, workbook, config: ExtractorConfig
                         ) -> str | None:
    """Value-derived layer evidence is never trusted from a cache (Chunk A):
    re-derive every ``catalog_value`` / ``schema_value`` band layer from the
    workbook in hand through the SAME value chain discovery uses (Catalog
    values first, then Schema values). A reason string when the cached layer
    or its evidence kind no longer holds, else None."""
    disc = config.discovery
    for sp in profile.sheets:
        for band in sp.bands:
            if band.layer_evidence not in VALUE_EVIDENCE:
                continue
            if sp.name not in workbook.sheetnames or sp.header_row is None:
                return (f"cached {band.layer} band of sheet {sp.name!r} took its layer from "
                        "values that cannot be re-read")
            layer, kind = value_layer(workbook[sp.name], sp.header_row, band, disc)
            if (layer, kind) != (band.layer, band.layer_evidence):
                return (f"cached {band.layer} band of sheet {sp.name!r} took its layer from "
                        f"{band.layer_evidence}; re-derived from this workbook the values name "
                        f"{layer or 'no layer'} ({kind or 'no value evidence'})")
    return None


def _roles_group(band: BandProfile, bands_before: list[BandProfile]) -> str:
    if band.layer in ("stage", "standard"):
        return "target"
    if band.layer == "source":
        return "source"
    # A rules band AFTER a target band is the trailing group (recycle flag,
    # DQ mandatory list, comments); before it, the data-rules band.
    return "trailing" if any(b.layer in ("stage", "standard") for b in bands_before) else "rules"


def _mapping_source_vocabulary(table: dict[str, set[str]], extractor: ExtractorConfig
                               ) -> dict[str, set[str]]:
    """A ``MAPPING-`` sheet's source band speaks family B's vocabulary
    (``extractor.header_synonyms``, the legacy reader's table): its spellings
    name the legacy role and no other ("Mandatory" is ``mandatory`` there,
    ``required`` on the content families)."""
    from codegen.extract.workbook import LEGACY_SOURCE_ROLES

    out = {role: set(spellings) for role, spellings in table.items()}
    for logical, spellings in extractor.header_synonyms.items():
        role = LEGACY_SOURCE_ROLES.get(logical)
        if role is None:
            continue
        for spelling in (normalize(s) for s in spellings):
            for others in out.values():
                others.discard(spelling)
            out.setdefault(role.value, set()).add(spelling)
    return out


def _resolve_band_roles(sheet: str, band: BandProfile, header: list, disc: DiscoveryConfig,
                        confidence: dict[str, float], unresolved: list[UnresolvedRole],
                        diagnostics: list[str], bands_before: list[BandProfile] | None = None,
                        extractor: ExtractorConfig | None = None) -> BandProfile:
    group = _roles_group(band, bands_before or [])
    table = {role: {normalize(s) for s in spellings}
             for role, spellings in disc.roles.get(group, {}).items()}
    if (extractor is not None and group == "source"
            and sheet.startswith(extractor.mapping_sheet_prefix)):
        table = _mapping_source_vocabulary(table, extractor)
    # The per-row recycle column: its header STARTS with the prefix ("Recycle
    # Flag ( Enabled for 7 Days)") — the legacy reader's rule, wherever it sits.
    recycle = normalize(extractor.recycle_header_prefix) if extractor is not None else ""
    roles: dict[str, int] = {}
    for col in range(band.col_start, band.col_end + 1):
        raw = header[col - 1] if col - 1 < len(header) else None
        value = normalize(raw)
        if not value:
            continue
        if recycle and value.startswith(recycle) and Role.RECYCLE_FLAG.value not in roles \
                and not any(value in spellings for spellings in table.values()):
            roles[Role.RECYCLE_FLAG.value] = col
            confidence[confidence_key(sheet, band.layer, Role.RECYCLE_FLAG)] = _SYNONYM_CONFIDENCE
            continue
        matches = [role for role, spellings in table.items() if value in spellings]
        if len(matches) == 1:
            role = matches[0]
            if role in roles:
                diagnostics.append(
                    f"sheet {sheet!r}: header {raw!r} (column {col}) also matches "
                    f"{role!r}, already taken by column {roles[role]}; kept the first")
                continue
            roles[role] = col
            confidence[confidence_key(sheet, band.layer, role)] = _SYNONYM_CONFIDENCE
        elif len(matches) > 1:
            unresolved.append(UnresolvedRole(
                sheet=sheet, layer=band.layer, role="|".join(sorted(matches)),
                reason=f"header {raw!r} (column {col}) is ambiguous between {sorted(matches)}",
                candidates=[col]))
        else:
            diagnostics.append(
                f"sheet {sheet!r}: {band.layer} header {raw!r} (column {col}) matches no "
                f"{group} synonym; left unresolved")
    return band.model_copy(update={"roles": roles})


def _meta_rows(rows_above: list[list], disc: DiscoveryConfig, sheet: str,
               diagnostics: list[str]) -> list[MetaRow]:
    synonyms = {normalize(s): key for key, spellings in disc.meta_synonyms.items()
                for s in spellings}
    out: list[MetaRow] = []
    for index, row in enumerate(rows_above, start=1):
        cells = [(i + 1, text(c)) for i, c in enumerate(row) if text(c) is not None]
        if not cells:
            continue
        label_col, label = cells[0]
        value_col = cells[1][0] if len(cells) > 1 else None
        key = synonyms.get(normalize(label))
        if key is None:
            diagnostics.append(f"sheet {sheet!r} row {index}: meta label {label!r} unrecognised")
        out.append(MetaRow(row=index, col=label_col, label=label, key=key, value_col=value_col))
    return out


def _has_banner_rows(ws, header_row: int, bands: list[BandProfile],
                     disc: DiscoveryConfig) -> bool:
    source = next((b for b in bands if b.layer == "source"), None)
    if source is None:
        return False
    spellings = {normalize(s) for values in disc.segment_synonyms.values() for s in values}
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        filled = [(i + 1, text(c)) for i, c in enumerate(row) if text(c) is not None]
        if len(filled) != 1:
            continue
        col, value = filled[0]
        if source.col_start <= col <= source.col_end and normalize(value) in spellings:
            return True
    return False


def _apply_sheet_segments(sheets: list[SheetProfile], disc: DiscoveryConfig) -> list[SheetProfile]:
    """One-sheet-per-segment: every mapping sheet's name spells a segment."""
    mapping = [s for s in sheets if s.kind == "mapping"]
    if len(mapping) < 2:
        return sheets
    spellings = {normalize(s) for values in disc.segment_synonyms.values() for s in values}
    if all(normalize(s.name) in spellings or normalize(s.name).split(" ")[-1] in spellings
           for s in mapping):
        return [s.model_copy(update={"segment_strategy": "sheet"}) if s.kind == "mapping"
                and s.segment_strategy == "none" else s for s in sheets]
    return sheets


def _classify_auxiliary(ws, disc: DiscoveryConfig, diagnostics: list[str]) -> SheetProfile:
    rows = [list(r) for _, r in zip(range(_AUX_SCAN_ROWS), ws.iter_rows(values_only=True),
                                    strict=False)]
    for kind, alternatives in disc.auxiliary_sheets.items():
        for index, row in enumerate(rows, start=1):
            cells = [normalize(c) for c in row if text(c) is not None]
            if len(cells) < 1:
                continue
            for tokens in alternatives:
                if all(any(normalize(t) in c for c in cells) for t in tokens):
                    headers = [str(text(c)) for c in row if text(c) is not None]
                    diagnostics.append(f"sheet {ws.title!r}: auxiliary {kind} (header row {index})")
                    return SheetProfile(name=ws.title, kind=kind, header_row=index,  # type: ignore[arg-type]
                                        headers=headers)
    diagnostics.append(f"sheet {ws.title!r}: no mapping structure or auxiliary signature; ignored")
    return SheetProfile(name=ws.title, kind="ignore")


__all__ = [
    "MAPPING_PREFIX_REFUSED",
    "Discovery",
    "LabelGroup",
    "NoLayoutError",
    "discover_vdd",
    "SEGMENTED_FAMILY_NOTE",
    "SEGMENTED_SOURCE_ROLES",
    "SEGMENTED_TABLE_ROLES",
    "discover",
    "label_groups",
    "legacy_readable",
    "mapping_differences",
    "normalize",
    "stale_value_evidence",
    "text",
    "value_layer",
]
