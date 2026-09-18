"""FRD layout profile — WHERE each contract field lives in a .docx.

The docx twin of :mod:`codegen.layout.profile` (M2.5 §7, pulled forward
into M2): a profile names, for every FrdContract field, the Word table
index, row and label cell it is read from, plus the label text as seen and
the metadata section it sits in. It never carries a value. Family F1
(six metadata section tables) and F2 (Solution Requirement tables whose
row-4 label names the section) share the schema; ``source`` records who
resolved the layout; ``confidence`` is per resolved field (0–1).

Field keys are contract paths: ``feeds[0].frequency``,
``feeds[0].stage_target.load_strategy``, ``feeds[0].validation_rules[2]``.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

FrdFamily = Literal["F1", "F2"]
ProfileSource = Literal["synonyms", "model", "user", "cache"]


class FrdFieldSource(BaseModel):
    """One contract field's cell: label cell (table, row, col) and the value
    cell to its right; ``inline_label`` when the value is a ``Label: value``
    pair inside a free-text cell (F2 row-4 text)."""

    model_config = _MODEL_CONFIG

    table: int = Field(ge=0)
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    value_col: int | None = None
    label: str                      # label text exactly as seen
    section: str | None = None      # descriptive|structural|…|data_quality|vendor
    inline_label: str | None = None
    feed_index: int = Field(default=0, ge=0)
    # True for the positional Data Quality rule rows: the rule text is
    # "<label>: <value>" because the label IS the rule name.
    labelled_rule: bool = False


class FrdUnresolved(BaseModel):
    model_config = _MODEL_CONFIG

    field: str
    feed_index: int = Field(default=0, ge=0)
    reason: str
    candidates: list[str] = Field(default_factory=list)


class FrdSectionRef(BaseModel):
    model_config = _MODEL_CONFIG

    table: int = Field(ge=0)
    section: str
    title: str                      # section title text as seen
    feed_index: int = Field(default=0, ge=0)


class FrdLayoutProfile(BaseModel):
    model_config = _MODEL_CONFIG

    fingerprint: str
    family: FrdFamily
    source: ProfileSource
    fields: dict[str, FrdFieldSource] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    unresolved: list[FrdUnresolved] = Field(default_factory=list)
    sections: list[FrdSectionRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def feed_count(self) -> int:
        indexes = ({s.feed_index for s in self.sections}
                   | {f.feed_index for f in self.fields.values()})
        return (max(indexes) + 1) if indexes else 0


def frd_fingerprint(tables: list[list[list[str]]]) -> str:
    """sha256 over each table's title row and its label texts: every row's
    first cell, plus the second cell on rows whose first cell repeats the
    table title (the F1 section-prefix column). Values never enter it."""
    digest = hashlib.sha256()
    for index, rows in enumerate(tables):
        title = " | ".join(c.strip() for c in rows[0]) if rows else ""
        digest.update(f"table {index}: {title}\n".encode())
        first_title = rows[0][0].strip() if rows and rows[0] else ""
        for row in rows[1:]:
            if not row:
                continue
            label = row[0].strip()
            if label == first_title and len(row) > 1:
                label = f"{label} / {row[1].strip()}"
            digest.update(f"  {label}\n".encode())
        digest.update(b"---\n")
    return digest.hexdigest()


__all__ = [
    "FrdFamily",
    "FrdFieldSource",
    "FrdLayoutProfile",
    "FrdSectionRef",
    "FrdUnresolved",
    "frd_fingerprint",
]
