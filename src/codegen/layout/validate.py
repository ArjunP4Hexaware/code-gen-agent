"""Profile validator — every claim a model (or a person) makes about a
layout is checked against the workbook before a single value is read.

Checks (M2.5 §4), thresholds from ``extractor.discovery.validate``:

- the sheet exists; ``header_row`` exists and the header cell at every
  claimed role column is non-empty text;
- ``band_row`` (when claimed) carries a stage token and a standard token at
  or spanning the claimed stage/standard spans; band spans do not overlap;
  the stage and standard bands each resolve at least ``table`` + ``column``;
- a role appears at most once per band;
- content plausibility over the data rows under the header: length /
  start / end columns >= 80% integer-like, source_type / target_type >= 80%
  type-token-like, yes/no roles >= 80% Y/N-like or blank, field_name >= 90%
  non-empty;
- meta rows: the label cell text matches the claimed key's synonym set (or
  the claimed label text exactly) and the value cell sits to its right;
- auxiliary kinds require their header signatures.

A failed check drops that role (or that sheet kind) to unresolved with a
reason string; nothing is ever edited or filled in. Roles the synonym
tables resolved are trusted (their evidence is the header text itself);
``check_sources`` selects which sources are validated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from codegen.config import ExtractorConfig
from codegen.layout.discover import _band_layer, _has_token, normalize, text
from codegen.layout.profile import (
    REQUIRED_ROLES,
    BandProfile,
    LayoutProfile,
    MetaRow,
    Role,
    SheetProfile,
    UnresolvedRole,
    confidence_key,
)

_INTEGER_ROLES = {Role.LENGTH.value, Role.FIELD_LENGTH.value, Role.START.value, Role.END.value,
                  Role.ORDINAL.value}
_TYPE_ROLES = {Role.SOURCE_TYPE.value, Role.TARGET_TYPE.value}
_YES_NO_ROLES = {Role.PRIMARY_KEY.value, Role.PII.value, Role.REQUIRED.value,
                 Role.NOT_NULL.value, Role.MANDATORY.value, Role.MANDATORY_COLUMN.value,
                 Role.CRITICAL.value, Role.KEY.value, Role.INSCOPE.value}
_YES_NO_RE = re.compile(r"^(y|n|yes|no|true|false|x|m|s|null|not null|nullable|required|"
                        r"optional|situational|mandatory)$", re.IGNORECASE)
_MIN_DATA_CELLS = 2


@dataclass(frozen=True)
class Rejection:
    document: str            # "sttm" | "frd"
    sheet: str | None
    layer: str | None
    role: str | None
    reason: str

    def render(self) -> str:
        where = "/".join(p for p in (self.sheet, self.layer, self.role) if p)
        return f"{self.document} {where}: {self.reason}"


def _data_rows(ws, header_row: int) -> list[list]:
    rows = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        cells = [text(c) for c in row]
        if sum(1 for c in cells if c is not None) >= _MIN_DATA_CELLS:
            rows.append(cells)
    return rows


def _ratio(values: list, predicate) -> float:
    if not values:
        return 1.0
    return sum(1 for v in values if predicate(v)) / len(values)


def _integer_like(value) -> bool:
    if value is None:
        return True
    return re.fullmatch(r"\d+(\.0+)?", str(value).strip()) is not None


def validate_profile(profile: LayoutProfile, workbook, config: ExtractorConfig, *,
                     check_sources: set[str] | None = None,
                     document: str = "sttm") -> tuple[LayoutProfile, list[Rejection]]:
    """Return (profile with rejected claims dropped, rejections)."""
    disc = config.discovery
    thresholds = disc.validate
    type_re = re.compile(thresholds.type_token_regex, re.IGNORECASE)
    sources = check_sources or {"model", "user"}
    rejections: list[Rejection] = []
    sheets: list[SheetProfile] = []
    confidence = dict(profile.confidence)
    role_sources = dict(profile.role_sources)
    unresolved = [u for u in profile.unresolved]

    def reject(sheet, layer, role, reason):
        rejections.append(Rejection(document, sheet, layer, role, reason))
        key = confidence_key(sheet, layer, role) if layer and role else None
        if key:
            confidence.pop(key, None)
            role_sources.pop(key, None)

    def checked(sheet: str, layer: str, role: str) -> bool:
        return role_sources.get(confidence_key(sheet, layer, role), profile.source) in sources

    for sp in profile.sheets:
        if sp.name not in workbook.sheetnames:
            reject(sp.name, None, None, "sheet does not exist in the workbook")
            continue
        ws = workbook[sp.name]
        if sp.kind != "mapping":
            sheets.append(_validate_auxiliary(sp, ws, disc, reject))
            continue
        if sp.header_row is None or sp.header_row > ws.max_row:
            reject(sp.name, None, None, f"header row {sp.header_row} does not exist")
            sheets.append(sp.model_copy(update={"kind": "ignore", "bands": []}))
            continue
        raw_header = list(next(ws.iter_rows(min_row=sp.header_row, max_row=sp.header_row,
                                            values_only=True)))
        header = [text(c) for c in raw_header]
        data = _data_rows(ws, sp.header_row)
        bands = _validate_band_spans(sp, ws, header, disc, reject)
        validated: list[BandProfile] = []
        for band in bands:
            roles: dict[str, int] = {}
            seen_cols: dict[int, str] = {}
            for role, col in band.roles.items():
                if not checked(sp.name, band.layer, role):
                    roles[role] = col
                    seen_cols[col] = role
                    continue
                cell = header[col - 1] if 0 < col <= len(header) else None
                if cell is None:
                    reject(sp.name, band.layer, role, f"header cell at column {col} is empty")
                    continue
                raw = raw_header[col - 1]
                if not isinstance(raw, str):
                    # A header is text; a numeric cell means the claimed
                    # header row is a data row.
                    reject(sp.name, band.layer, role,
                           f"header cell at column {col} is not text ({raw!r}) — row "
                           f"{sp.header_row} is a data row")
                    continue
                if col in seen_cols:
                    reject(sp.name, band.layer, role,
                           f"column {col} already carries role {seen_cols[col]!r}")
                    continue
                if not (band.col_start <= col <= band.col_end):
                    reject(sp.name, band.layer, role,
                           f"column {col} lies outside the {band.layer} band "
                           f"{band.col_start}-{band.col_end}")
                    continue
                column_values = [r[col - 1] if col - 1 < len(r) else None for r in data]
                problem = _plausibility(role, column_values, thresholds, type_re)
                if problem:
                    reject(sp.name, band.layer, role, problem)
                    continue
                roles[role] = col
                seen_cols[col] = role
            validated.append(band.model_copy(update={"roles": roles}))
        for band in validated:
            for role in REQUIRED_ROLES.get(band.layer, ()):
                if band.column(role) is None and not any(
                        u.sheet == sp.name and u.layer == band.layer and u.role == role.value
                        for u in unresolved):
                    unresolved.append(UnresolvedRole(
                        sheet=sp.name, layer=band.layer, role=role.value,
                        reason="required role unresolved after validation",
                        candidates=[c for c in range(band.col_start, band.col_end + 1)
                                    if c not in band.roles.values()
                                    and 0 < c <= len(header) and header[c - 1]]))
        meta_rows = _validate_meta_rows(sp, ws, disc, reject)
        segment_column = sp.segment_column
        source_band = next((b for b in validated if b.layer == "source"), None)
        if segment_column is not None and (source_band is None
                                           or source_band.column(Role.SEGMENT) != segment_column):
            segment_column = source_band.column(Role.SEGMENT) if source_band else None
        sheets.append(sp.model_copy(update={
            "bands": validated, "meta_rows": meta_rows, "segment_column": segment_column,
            "segment_strategy": ("column" if segment_column is not None
                                 else sp.segment_strategy if sp.segment_strategy != "column"
                                 else "none"),
        }))
    # Drop unresolved entries that a surviving role now covers.
    unresolved = [u for u in unresolved if not any(
        s.name == u.sheet and any(b.layer == u.layer and u.role in b.roles for b in s.bands)
        for s in sheets)]
    # Rejected roles go back to unresolved with their reason.
    for r in rejections:
        if r.role and r.layer and not any(u.sheet == r.sheet and u.layer == r.layer
                                          and u.role == r.role for u in unresolved):
            unresolved.append(UnresolvedRole(sheet=r.sheet or "", layer=r.layer,  # type: ignore[arg-type]
                                             role=r.role, reason=f"rejected: {r.reason}"))
    return profile.model_copy(update={
        "sheets": sheets, "confidence": confidence, "role_sources": role_sources,
        "unresolved": unresolved,
    }), rejections


def _plausibility(role: str, values: list, thresholds, type_re) -> str | None:
    if role in _INTEGER_ROLES:
        ratio = _ratio(values, _integer_like)
        if ratio < thresholds.integer_like:
            return (f"only {ratio:.0%} of the values under the header are integer-like "
                    f"(threshold {thresholds.integer_like:.0%})")
    elif role in _TYPE_ROLES:
        ratio = _ratio(values, lambda v: v is None or type_re.fullmatch(str(v).strip()))
        if ratio < thresholds.type_like:
            return (f"only {ratio:.0%} of the values look like data types "
                    f"(threshold {thresholds.type_like:.0%})")
    elif role in _YES_NO_ROLES:
        ratio = _ratio(values, lambda v: v is None or _YES_NO_RE.match(str(v).strip()))
        if ratio < thresholds.yes_no_like:
            return (f"only {ratio:.0%} of the values are Y/N-like or blank "
                    f"(threshold {thresholds.yes_no_like:.0%})")
    elif role == Role.FIELD_NAME.value:
        ratio = _ratio(values, lambda v: v is not None)
        if ratio < thresholds.field_name_non_empty:
            return (f"only {ratio:.0%} of the field-name cells are non-empty "
                    f"(threshold {thresholds.field_name_non_empty:.0%})")
    return None


def _validate_band_spans(sp: SheetProfile, ws, header: list, disc, reject) -> list[BandProfile]:
    bands = list(sp.bands)
    if sp.band_row is not None:
        if sp.band_row > ws.max_row:
            reject(sp.name, None, None, f"band row {sp.band_row} does not exist")
            return []
        band_cells = [text(c) for c in next(ws.iter_rows(min_row=sp.band_row,
                                                          max_row=sp.band_row,
                                                          values_only=True))]
        merged = {r.min_col: r.max_col for r in ws.merged_cells.ranges
                  if r.min_row == sp.band_row}
        for band in bands:
            if band.layer not in ("stage", "standard"):
                continue
            covering = [normalize(c) for i, c in enumerate(band_cells, start=1)
                        if c and (band.col_start <= i <= band.col_end
                                  or (i in merged and i <= band.col_start <= merged[i]))]
            tokens = disc.band_tokens.get(band.layer, [])
            if not _has_token(covering, tokens) and not (
                    band.label and _band_layer(band.label, disc.band_tokens) == band.layer):
                for role in list(band.roles):
                    reject(sp.name, band.layer, role,
                           f"band row {sp.band_row} carries no {band.layer} token over "
                           f"columns {band.col_start}-{band.col_end}")
                bands[bands.index(band)] = band.model_copy(update={"roles": {}})
    ordered = sorted(bands, key=lambda b: b.col_start)
    for first, second in zip(ordered, ordered[1:], strict=False):
        if second.col_start <= first.col_end:
            for role in list(second.roles):
                reject(sp.name, second.layer, role,
                       f"{second.layer} band {second.col_start}-{second.col_end} overlaps "
                       f"{first.layer} band {first.col_start}-{first.col_end}")
            bands[bands.index(second)] = second.model_copy(update={"roles": {}})
    return bands


def _validate_meta_rows(sp: SheetProfile, ws, disc, reject) -> list[MetaRow]:
    synonyms = {normalize(s): key for key, spellings in disc.meta_synonyms.items()
                for s in spellings}
    out: list[MetaRow] = []
    for entry in sp.meta_rows:
        if entry.row > ws.max_row:
            reject(sp.name, None, None, f"meta row {entry.row} does not exist")
            continue
        label = text(ws.cell(row=entry.row, column=entry.col).value)
        if label is None or (normalize(label) != normalize(entry.label)
                             and synonyms.get(normalize(label)) != entry.key):
            reject(sp.name, None, None,
                   f"meta row {entry.row}: label cell reads {label!r}, not {entry.label!r}")
            continue
        if entry.value_col is not None and entry.value_col <= entry.col:
            reject(sp.name, None, None,
                   f"meta row {entry.row}: value column {entry.value_col} is not to the "
                   f"right of the label column {entry.col}")
            out.append(entry.model_copy(update={"value_col": None}))
            continue
        if entry.key is not None and synonyms.get(normalize(label)) != entry.key:
            reject(sp.name, None, None,
                   f"meta row {entry.row}: label {label!r} is not a synonym of {entry.key!r}")
            out.append(entry.model_copy(update={"key": None}))
            continue
        out.append(entry)
    return out


def _validate_auxiliary(sp: SheetProfile, ws, disc, reject) -> SheetProfile:
    if sp.kind in ("ignore", "version"):
        return sp
    alternatives = disc.auxiliary_sheets.get(sp.kind, [])
    header_row = sp.header_row or 1
    if header_row > ws.max_row:
        reject(sp.name, None, None, f"{sp.kind}: header row {header_row} does not exist")
        return sp.model_copy(update={"kind": "ignore"})
    cells = [normalize(c) for c in next(ws.iter_rows(min_row=header_row, max_row=header_row,
                                                      values_only=True)) if text(c)]
    if not any(all(any(normalize(t) in c for c in cells) for t in tokens)
               for tokens in alternatives):
        reject(sp.name, None, None,
               f"{sp.kind}: header row {header_row} lacks the signature {alternatives}")
        return sp.model_copy(update={"kind": "ignore"})
    return sp


__all__ = ["Rejection", "validate_profile"]
