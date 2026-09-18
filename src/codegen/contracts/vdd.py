"""Vendor Data Dictionary contract (M3) — the pair's third input.

Read from the VDD workbook through a layout profile (``codegen.layout``:
roles on the ``FILES`` sheet and the field sheets), values verbatim, every
value with the cell it came from. The VDD is NEVER a source for the
standard layer; its values enter an output only as the fixed-width /
position rows (``position_rows``, emitted by the IIG v2 template in M4)
and as gate flags from the STTM-vs-VDD cross-check.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from codegen.contracts.sttm import LayoutSummary

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class CellRef(BaseModel):
    """One cell: sheet, 1-based row and column, and who placed the role."""

    model_config = _MODEL_CONFIG

    sheet: str
    row: int = Field(ge=1)
    col: int = Field(ge=1)
    source: Literal["synonyms", "model", "user", "cache"]

    @property
    def a1(self) -> str:
        from openpyxl.utils import get_column_letter

        return f"{self.sheet}!{get_column_letter(self.col)}{self.row}"


class VddFile(BaseModel):
    """One ``FILES`` sheet row (V1/V2/V3 share the ten-column header)."""

    model_config = _MODEL_CONFIG

    pattern: str | None
    title: str | None
    format: str | None
    delimiter: str | None
    cadence: str | None
    description: str | None
    field_sheet: str | None
    multi_record: str | None
    record_type_field: str | None
    header_row: str | None
    row: int = Field(ge=1)
    cells: dict[str, CellRef] = Field(default_factory=dict)   # attribute -> cell


class VddField(BaseModel):
    """One field-sheet row, verbatim; positions parsed to int when the cell
    is integer-like (leading zeros allowed), else None with the raw text
    kept in ``raw``."""

    model_config = _MODEL_CONFIG

    sheet: str
    row: int = Field(ge=1)
    position: int | None
    name: str
    data_type: str | None
    start: int | None
    end: int | None
    length: int | None
    required: str | None
    phi: str | None
    key: str | None
    segment: str | None            # as spelled in the workbook
    segment_canonical: str | None  # Header / Detail / Trailer when the spelling is known
    description: str | None
    example: str | None
    raw: dict[str, str] = Field(default_factory=dict)         # non-integer position texts
    cells: dict[str, CellRef] = Field(default_factory=dict)   # attribute -> cell
    provenance: CellRef


class PositionRow(BaseModel):
    """A fixed-width position row — the only VDD values an output may carry
    (IIG v2 ``ADLS_FIXED_WIDTH_HANDLER``: COL / LEN / start_ind per segment)."""

    model_config = _MODEL_CONFIG

    sheet: str
    segment: str | None
    field: str
    start: int | None
    end: int | None
    length: int | None
    cell: CellRef


class VddContract(BaseModel):
    model_config = _MODEL_CONFIG

    contract_name: str
    generated_from_vdd: str
    generated_date: str
    notes: list[str]
    files: list[VddFile]
    field_sheets: list[str]                 # the field sheets read (selected for the STTM)
    ignored_sheets: list[str] = Field(default_factory=list)
    fields: list[VddField]
    position_rows: list[PositionRow]
    layout: LayoutSummary | None = None

    def fields_for(self, sheet: str | None) -> list[VddField]:
        return [f for f in self.fields if sheet is None or f.sheet == sheet]

    @property
    def has_positions(self) -> bool:
        return any(r.start is not None and (r.end is not None or r.length is not None)
                   for r in self.position_rows)


__all__ = ["CellRef", "PositionRow", "VddContract", "VddField", "VddFile"]
