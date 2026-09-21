"""STTM source band vs Vendor Data Dictionary — the cross-check gate (M3).

Fields match by normalized name (case, spaces, underscores, other
punctuation dropped; positions compared as integers so leading zeros do not
matter), segment-aware when both documents carry segments. Every mismatch
is ONE flag citing both cells; there is no "mostly matching" threshold. A
field-count difference adds one summary flag beside the per-field list.

Flag classes: ``vdd_mismatch:type`` (through the type-equivalence table in
``extractor.vdd.type_equivalence`` — CHAR/VARCHAR/String are one class),
``vdd_mismatch:length``, ``vdd_mismatch:position``, ``vdd_missing_in_sttm``,
``vdd_missing_in_vdd``, ``vdd_segment_mismatch``, ``vdd_field_count``.

The verdict stays PASS_WITH_FLAGS — except when the FRD says fixed-width
and the VDD supplies no positions: that is a failed gate check naming the
remedy, because the position rows are the one thing only the VDD provides.
"""

from __future__ import annotations

import re

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.contracts.sttm import SttmField
from codegen.contracts.vdd import VddContract, VddField
from codegen.gate.preflight import GateCheck

_PAREN_RE = re.compile(r"\(.*?\)")


def normalize_name(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def base_type(value: str | None) -> str:
    """"Decimal(17,2)" → "decimal", "X(10)" → "x", "varchar " → "varchar"."""
    return re.sub(r"\s+", "", _PAREN_RE.sub("", (value or "").lower()))


def _type_classes(value: str, classes: list[list[str]]) -> set[int]:
    """Every equivalence class the token belongs to ("numeric" sits in the
    integer AND the decimal class)."""
    return {index for index, members in enumerate(classes)
            if value in {m.lower() for m in members}}


def types_equivalent(sttm_type: str | None, vdd_type: str | None, config: Config) -> bool:
    a, b = base_type(sttm_type), base_type(vdd_type)
    if not a or not b or a == b:
        return True
    classes = config.extractor.vdd.type_equivalence
    return bool(_type_classes(a, classes) & _type_classes(b, classes))


def _select_sheets(spec: ResolvedFeedSpec, vdd: VddContract) -> list[str]:
    """One-sheet-per-table dictionaries: the sheet(s) named after the feed's
    source / stage table; a single field sheet always applies."""
    if len(vdd.field_sheets) <= 1:
        return list(vdd.field_sheets)
    candidates = {normalize_name(spec.feed_id), normalize_name(spec.feed_name)}
    for segment in spec.segments:
        candidates.add(normalize_name(segment.stage_table.table))
    source_table = spec.source_table
    if source_table:
        candidates.add(normalize_name(source_table))
    chosen = [s for s in vdd.field_sheets
              if normalize_name(s) in candidates
              or any(c.endswith(normalize_name(s)) for c in candidates if normalize_name(s))]
    return chosen or list(vdd.field_sheets)


def _sttm_cite(field: SttmField, what: str, value: str | None) -> str:
    where = (f"{field.provenance.sheet} row {field.provenance.row}" if field.provenance
             else "STTM")
    return f"STTM {where} ({what} {value!r})"


def _vdd_cite(field: VddField, attr: str, value) -> str:
    cell = field.cells.get(attr, field.provenance)
    return f"VDD {cell.a1} ({attr} {value!r})"


def vdd_cross_check(spec: ResolvedFeedSpec, config: Config) -> tuple[list[str], GateCheck | None]:
    """(flags, fixed-width position check or None) for one resolved feed."""
    vdd = spec.vdd
    if vdd is None:
        return [], None
    sheets = _select_sheets(spec, vdd)
    vdd_fields = [f for f in vdd.fields if f.sheet in sheets]
    sttm_segmented = spec.is_segmented
    vdd_segmented = any(f.segment for f in vdd_fields)
    by_segment = sttm_segmented and vdd_segmented

    def sttm_key(segment: str, field: SttmField) -> tuple[str | None, str]:
        return (segment if by_segment else None, normalize_name(field.source_column))

    def vdd_key(field: VddField) -> tuple[str | None, str]:
        return ((field.segment_canonical or field.segment) if by_segment else None,
                normalize_name(field.name))

    sttm_index: dict[tuple, tuple[str, SttmField]] = {}
    for segment in spec.segments:
        for field in segment.fields:
            sttm_index.setdefault(sttm_key(segment.segment, field), (segment.segment, field))
    vdd_index: dict[tuple, VddField] = {}
    for field in vdd_fields:
        vdd_index.setdefault(vdd_key(field), field)

    flags: list[str] = []
    matched_vdd: set[tuple] = set()
    for key, (segment_name, field) in sttm_index.items():
        vdd_field = vdd_index.get(key)
        if vdd_field is None:
            other = [v for k, v in vdd_index.items() if k[1] == key[1] and k != key]
            if other:
                flags.append(
                    f"vdd_segment_mismatch — {_sttm_cite(field, 'segment', segment_name)} vs "
                    f"{_vdd_cite(other[0], 'segment', other[0].segment)} (field "
                    f"{field.source_column!r})")
                matched_vdd.add(vdd_key(other[0]))
            else:
                cite = _sttm_cite(field, "field", field.source_column)
                flags.append(f"vdd_missing_in_vdd — {cite} has no row in the dictionary"
                             + (f" (sheets {sheets})" if sheets else ""))
            continue
        matched_vdd.add(key)
        if not types_equivalent(field.source_datatype, vdd_field.data_type, config):
            flags.append(f"vdd_mismatch:type — "
                         f"{_sttm_cite(field, 'type', field.source_datatype)} vs "
                         f"{_vdd_cite(vdd_field, 'data_type', vdd_field.data_type)} "
                         f"(field {field.source_column!r})")
        # M9.2: the STTM's RESOLVED byte width against the VDD's (its Length,
        # else its span) — a precision ("10,2") is never compared as a width.
        sttm_length = field.byte_width
        vdd_length = vdd_field.length
        vdd_attr = "length"
        if vdd_length is None and vdd_field.start is not None and vdd_field.end is not None:
            vdd_length, vdd_attr = vdd_field.end - vdd_field.start + 1, "end"
        if sttm_length is not None and vdd_length is not None and sttm_length != vdd_length:
            shown = (field.source_length if _as_int(field.source_length) is not None
                     else f"{sttm_length} (resolved width)")
            flags.append(f"vdd_mismatch:length — "
                         f"{_sttm_cite(field, 'length', shown)} vs "
                         f"{_vdd_cite(vdd_field, vdd_attr, vdd_length)} "
                         f"(field {field.source_column!r})")
        sttm_start, sttm_end = _as_int(field.source_start), _as_int(field.source_end)
        differences = []
        if sttm_start is not None and vdd_field.start is not None and sttm_start != vdd_field.start:
            differences.append(f"start {sttm_start} vs {vdd_field.start}")
        if sttm_end is not None and vdd_field.end is not None and sttm_end != vdd_field.end:
            differences.append(f"end {sttm_end} vs {vdd_field.end}")
        if differences:
            attr = "start" if differences[0].startswith("start") else "end"
            span = f"{field.source_start}-{field.source_end}"
            flags.append(f"vdd_mismatch:position — {_sttm_cite(field, 'position', span)}"
                         f" vs {_vdd_cite(vdd_field, attr, getattr(vdd_field, attr))}: "
                         f"{'; '.join(differences)} (field {field.source_column!r})")
    for key, vdd_field in vdd_index.items():
        if key not in matched_vdd:
            flags.append(f"vdd_missing_in_sttm — {_vdd_cite(vdd_field, 'field', vdd_field.name)} "
                         "has no source field in the STTM")
    if len(sttm_index) != len(vdd_index):
        flags.append(f"vdd_field_count — STTM {len(sttm_index)} source field(s) vs VDD "
                     f"{len(vdd_index)} field(s) on sheet(s) {sheets}")

    check: GateCheck | None = None
    fixed_tokens = [t.lower() for t in config.extractor.vdd.fixed_width_tokens]
    fmt = (spec.file_format or "").lower()
    if any(token in fmt for token in fixed_tokens):
        has_positions = any(r.sheet in sheets and r.start is not None
                            and (r.end is not None or r.length is not None)
                            for r in vdd.position_rows)
        check = GateCheck(
            name="vdd_positions",
            passed=has_positions,
            details=("fixed-width positions present in the VDD" if has_positions else
                     f"the FRD states a fixed-width format ({spec.file_format!r}) but the VDD "
                     f"sheet(s) {sheets} carry no start/end (or start+length) positions — "
                     "supply a dictionary with Start Position / End Position (or Length) per "
                     "field, or correct the FRD's Object/data Format"),
        )
    return flags, check


def _as_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.match(r"^\s*0*(\d+)(?:\.0+)?\s*$", value)
    return int(match.group(1)) if match else None


__all__ = ["base_type", "normalize_name", "types_equivalent", "vdd_cross_check"]
