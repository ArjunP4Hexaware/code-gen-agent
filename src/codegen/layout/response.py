"""What a layout model may SAY — placement only, provenance never (M12 item 1).

A model answers WHERE things are. Who resolved them, how sure we are and
which strategy found them are facts about OUR resolution, not about the
document — the model has no standing to state them, and it never did: the
resolver overwrites ``source`` / ``role_sources`` with its own stamp the
moment an answer survives the validator.

Until M12 the answer was nevertheless validated against
:class:`~codegen.layout.profile.LayoutProfile`, whose ``source`` is a
Literal of four words. The prompt showed the model a partial profile
carrying those provenance fields, so the model filled them in — and a
plausible-but-unlisted word (``"synonym"``, ``"inferred"``, …) failed
``LayoutProfile`` validation and threw away an otherwise good answer:
inside ACFC five of ten pairs lost every model-placed role that way
(`RUN_v072_details.md` §4 — the literal_error on ``source`` plus one per
``role_sources`` key).

So the wire schema is its own model. It carries placement and nothing
else, it IGNORES extra keys (a model that still volunteers ``source`` is
not punished for it — the value is dropped), and
:func:`layout_profile_from_response` / :func:`frd_profile_from_response`
build the profile and stamp the provenance here. The prompt's schema is
generated from these models, so what the model is asked for and what it
is judged against are the same thing by construction.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from codegen.layout.frd_profile import (
    FrdFamily,
    FrdFieldSource,
    FrdLayoutProfile,
)
from codegen.layout.profile import (
    BandProfile,
    Layer,
    LayoutProfile,
    MetaRow,
    SegmentStrategy,
    SheetKind,
    SheetProfile,
    confidence_key,
)

# extra="ignore", not "forbid": provenance a model volunteers is DROPPED,
# never a rejection. Nothing here is a value — only rows, columns and the
# structural labels the fingerprint was hashed over.
_RESPONSE_CONFIG = ConfigDict(frozen=True, extra="ignore")


class BandResponse(BaseModel):
    """A band the model places: its layer, its column span and its roles."""

    model_config = _RESPONSE_CONFIG

    layer: Layer
    col_start: int = Field(ge=1)
    col_end: int = Field(ge=1)
    roles: dict[str, int] = Field(default_factory=dict)
    label: str | None = None


class MetaRowResponse(BaseModel):
    model_config = _RESPONSE_CONFIG

    row: int = Field(ge=1)
    col: int = Field(ge=1)
    label: str
    key: str | None = None
    value_col: int | None = None


class SheetResponse(BaseModel):
    model_config = _RESPONSE_CONFIG

    name: str
    kind: SheetKind
    header_row: int | None = None
    band_row: int | None = None
    bands: list[BandResponse] = Field(default_factory=list)
    meta_rows: list[MetaRowResponse] = Field(default_factory=list)
    segment_strategy: SegmentStrategy = "none"
    segment_column: int | None = None
    headers: list[str] = Field(default_factory=list)


class LayoutResponse(BaseModel):
    """The completed workbook layout as a model may state it."""

    model_config = _RESPONSE_CONFIG

    sheets: list[SheetResponse] = Field(default_factory=list)


class FrdFieldResponse(BaseModel):
    model_config = _RESPONSE_CONFIG

    table: int = Field(ge=0)
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    value_col: int | None = None
    label: str
    section: str | None = None
    inline_label: str | None = None
    feed_index: int = Field(default=0, ge=0)
    labelled_rule: bool = False


class FrdLayoutResponse(BaseModel):
    """The completed document layout as a model may state it."""

    model_config = _RESPONSE_CONFIG

    fields: dict[str, FrdFieldResponse] = Field(default_factory=dict)


def layout_profile_from_response(payload: dict, fingerprint: str) -> LayoutProfile:
    """Validate a workbook answer against :class:`LayoutResponse` and stamp OUR
    provenance on it: ``source="model"``, every placed role ``"model"``, the
    fingerprint the document actually has (never the one the answer claims).

    Raises ``pydantic.ValidationError`` when the PLACEMENT does not parse —
    the only thing a model can get wrong here.
    """
    response = LayoutResponse.model_validate(payload)
    sheets = [
        SheetProfile(
            name=sheet.name,
            kind=sheet.kind,
            header_row=sheet.header_row,
            band_row=sheet.band_row,
            bands=[BandProfile(layer=band.layer, col_start=band.col_start,
                               col_end=band.col_end, roles=dict(band.roles), label=band.label)
                   for band in sheet.bands],
            meta_rows=[MetaRow(row=meta.row, col=meta.col, label=meta.label, key=meta.key,
                               value_col=meta.value_col)
                       for meta in sheet.meta_rows],
            segment_strategy=sheet.segment_strategy,
            segment_column=sheet.segment_column,
            headers=list(sheet.headers),
        )
        for sheet in response.sheets
    ]
    keys = [confidence_key(s.name, b.layer, role)
            for s in sheets for b in s.bands for role in b.roles]
    return LayoutProfile(
        fingerprint=fingerprint,
        sheets=sheets,
        source="model",
        role_sources=dict.fromkeys(keys, "model"),
        strategy="model",
    )


def frd_profile_from_response(payload: dict, fingerprint: str,
                              family: FrdFamily) -> FrdLayoutProfile:
    """The docx twin: placement out of :class:`FrdLayoutResponse`, provenance
    stamped here. ``family`` is what the DISCOVERY found — a model does not
    reclassify the document."""
    response = FrdLayoutResponse.model_validate(payload)
    fields = {key: FrdFieldSource(table=claim.table, row=claim.row, col=claim.col,
                                  value_col=claim.value_col, label=claim.label,
                                  section=claim.section, inline_label=claim.inline_label,
                                  feed_index=claim.feed_index,
                                  labelled_rule=claim.labelled_rule)
              for key, claim in response.fields.items()}
    return FrdLayoutProfile(
        fingerprint=fingerprint,
        family=family,
        source="model",
        fields=fields,
        field_sources=dict.fromkeys(fields, "model"),
    )


def layout_partial(profile: LayoutProfile) -> dict:
    """The partial profile as the model is shown it: the placement it must
    complete, with every provenance field dropped."""
    return LayoutResponse.model_validate(profile.model_dump(mode="json")).model_dump(mode="json")


def frd_partial(profile: FrdLayoutProfile) -> dict:
    return FrdLayoutResponse.model_validate(
        profile.model_dump(mode="json")).model_dump(mode="json")


def layout_response_schema() -> dict:
    return LayoutResponse.model_json_schema()


def frd_response_schema() -> dict:
    return FrdLayoutResponse.model_json_schema()


__all__ = [
    "BandResponse",
    "FrdFieldResponse",
    "FrdLayoutResponse",
    "LayoutResponse",
    "MetaRowResponse",
    "SheetResponse",
    "frd_partial",
    "frd_profile_from_response",
    "frd_response_schema",
    "layout_partial",
    "layout_profile_from_response",
    "layout_response_schema",
]
