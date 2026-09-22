"""VDD workbook → :class:`VddContract`, read THROUGH a layout profile (M3).

The profile comes from :func:`codegen.layout.discover.discover_vdd` (or the
resolver: cache → synonyms → model → validate → user); this module only
copies cell values. Header patterns V1/V2/V3 of docs/acfc/SHAPES_FOR_PORT.md
§3 differ in columns, not in reading: a role the profile did not place reads
as empty. Segments come from the ``Segment`` column; one-sheet-per-table
dictionaries were already narrowed to the STTM's tables by discovery.
"""

from __future__ import annotations

import re
from pathlib import Path

from codegen.config import Config
from codegen.contracts.sttm import LayoutSummary
from codegen.contracts.vdd import CellRef, PositionRow, VddContract, VddField, VddFile
from codegen.layout.discover import Discovery, normalize, text
from codegen.layout.profile import LayoutProfile, Role, SheetProfile

_INT_RE = re.compile(r"^\s*0*(\d+)(?:\.0+)?\s*$")

_FILE_ROLES = {
    "pattern": Role.FILE_PATTERN, "title": Role.TITLE, "format": Role.FORMAT,
    "delimiter": Role.DELIMITER, "cadence": Role.CADENCE, "description": Role.DESCRIPTION,
    "field_sheet": Role.FIELD_SHEET, "multi_record": Role.MULTI_RECORD,
    "record_type_field": Role.RECORD_TYPE_FIELD, "header_row": Role.HEADER_ROW,
}
_FIELD_ROLES = {
    "position": Role.POSITION, "name": Role.FIELD_NAME, "data_type": Role.DATA_TYPE,
    "start": Role.START, "end": Role.END, "length": Role.LENGTH, "required": Role.REQUIRED,
    "phi": Role.PHI, "key": Role.KEY, "segment": Role.SEGMENT, "description": Role.DESCRIPTION,
    "example": Role.EXAMPLE,
}
_INT_ATTRS = ("position", "start", "end", "length")


class VddExtractionError(ValueError):
    """The VDD cannot be read as a dictionary; message names the spot."""


def _int(value: str | None) -> int | None:
    if value is None:
        return None
    match = _INT_RE.match(value)
    return int(match.group(1)) if match else None


def read_vdd(found: Discovery, name: str, config: Config, *, generated_date: str,
             contract_name: str | None = None) -> VddContract:
    profile: LayoutProfile = found.profile
    workbook = found.workbook
    segments = {normalize(s): canonical
                for canonical, spellings in config.extractor.discovery.segment_synonyms.items()
                for s in spellings}
    files: list[VddFile] = []
    fields: list[VddField] = []
    positions: list[PositionRow] = []
    field_sheets: list[str] = []
    ignored: list[str] = []
    notes = list(found.diagnostics)
    for sp in profile.sheets:
        if sp.kind == "vdd_files":
            files += _read_files(workbook[sp.name], sp, profile)
        elif sp.kind == "vdd_fields":
            field_sheets.append(sp.name)
            for field in _read_fields(workbook[sp.name], sp, profile, segments):
                fields.append(field)
                if field.start is not None or field.length is not None:
                    positions.append(PositionRow(
                        sheet=field.sheet, segment=field.segment_canonical or field.segment,
                        field=field.name, start=field.start, end=field.end,
                        length=field.length, cell=field.provenance))
        else:
            ignored.append(sp.name)
    if not files and not fields:
        raise VddExtractionError(f"{name}: no FILES sheet and no field sheet recognised")
    return VddContract(
        contract_name=contract_name or f"VDD contract extracted from {name}",
        generated_from_vdd=name,
        generated_date=generated_date,
        notes=["Extracted deterministically by `codegen extract-vdd` through a layout "
               f"profile (strategy {profile.strategy!r}, source {profile.source!r}); values "
               "verbatim, every value cited. The VDD never feeds the standard layer.",
               *notes],
        files=files,
        field_sheets=field_sheets,
        ignored_sheets=ignored,
        fields=fields,
        position_rows=positions,
        layout=LayoutSummary(
            strategy=profile.strategy, source=profile.source, fingerprint=profile.fingerprint,
            unresolved=[f"{u.sheet}/{u.layer}/{u.role}: {u.reason}" for u in profile.unresolved]),
    )


def _cell_ref(profile: LayoutProfile, sp: SheetProfile, layer: str, role: Role, row: int,
              col: int) -> CellRef:
    return CellRef(sheet=sp.name, row=row, col=col,
                   source=profile.role_source(sp.name, layer, role))


def _read_files(ws, sp: SheetProfile, profile: LayoutProfile) -> list[VddFile]:
    band = sp.band("files")  # type: ignore[arg-type]
    if band is None or sp.header_row is None:
        return []
    out: list[VddFile] = []
    for row_number, row in enumerate(ws.iter_rows(min_row=sp.header_row + 1, values_only=True),
                                     start=sp.header_row + 1):
        cells = [text(c) for c in row]
        if all(c is None for c in cells):
            continue
        values: dict[str, str | None] = {}
        refs: dict[str, CellRef] = {}
        for attr, role in _FILE_ROLES.items():
            col = band.column(role)
            values[attr] = cells[col - 1] if col is not None and col - 1 < len(cells) else None
            if col is not None and values[attr] is not None:
                refs[attr] = _cell_ref(profile, sp, "files", role, row_number, col)
        out.append(VddFile(row=row_number, cells=refs, **values))
    return out


def _read_fields(ws, sp: SheetProfile, profile: LayoutProfile,
                 segments: dict[str, str]) -> list[VddField]:
    band = sp.band("fields")  # type: ignore[arg-type]
    if band is None or sp.header_row is None:
        return []
    name_col = band.column(Role.FIELD_NAME)
    out: list[VddField] = []
    for row_number, row in enumerate(ws.iter_rows(min_row=sp.header_row + 1, values_only=True),
                                     start=sp.header_row + 1):
        cells = [text(c) for c in row]
        if all(c is None for c in cells):
            continue
        name = cells[name_col - 1] if name_col is not None and name_col - 1 < len(cells) else None
        if name is None:
            continue
        values: dict[str, str | None] = {}
        refs: dict[str, CellRef] = {}
        for attr, role in _FIELD_ROLES.items():
            col = band.column(role)
            values[attr] = cells[col - 1] if col is not None and col - 1 < len(cells) else None
            if col is not None and values[attr] is not None:
                refs[attr] = _cell_ref(profile, sp, "fields", role, row_number, col)
        raw: dict[str, str] = {}
        ints: dict[str, int | None] = {}
        for attr in _INT_ATTRS:
            parsed = _int(values[attr])
            ints[attr] = parsed
            if values[attr] is not None and parsed is None:
                raw[attr] = values[attr]  # type: ignore[index]
        segment = values["segment"]
        out.append(VddField(
            sheet=sp.name, row=row_number, position=ints["position"], name=name,
            data_type=values["data_type"], start=ints["start"], end=ints["end"],
            length=ints["length"], required=values["required"], phi=values["phi"],
            key=values["key"], segment=segment,
            segment_canonical=segments.get(normalize(segment)) if segment else None,
            description=values["description"], example=values["example"], raw=raw, cells=refs,
            provenance=_cell_ref(profile, sp, "fields", Role.FIELD_NAME, row_number,
                                 name_col),  # type: ignore[arg-type]
        ))
    return out


def extract_vdd_contract(path: Path, config: Config, *, sttm_tables: list[str] | None = None,
                         layout: LayoutProfile | None = None, generated_date: str | None = None,
                         contract_name: str | None = None) -> tuple[VddContract, LayoutProfile]:
    from codegen.layout.discover import discover_vdd
    from codegen.layout.resolve import discovery_for

    if layout is not None:
        from codegen.layout.extent import load_document

        found = discovery_for(layout, load_document(path, config.extractor.used_range_empty_rows))
    else:
        found = discover_vdd(path, config.extractor, sttm_tables=sttm_tables)
    import datetime

    contract = read_vdd(found, path.name, config,
                        generated_date=generated_date or datetime.date.today().isoformat(),
                        contract_name=contract_name)
    return contract, found.profile


def contract_to_json(contract: VddContract) -> str:
    import json

    payload = contract.model_dump(mode="json", exclude_defaults=True)
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


__all__ = ["VddExtractionError", "contract_to_json", "extract_vdd_contract", "read_vdd"]
