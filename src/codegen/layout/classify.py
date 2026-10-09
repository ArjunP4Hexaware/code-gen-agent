"""What KIND of workbook is this — by what it says, never by its name (M9.3).

The document chooser used to list every ``.xlsx`` as an STTM and again as a
possible Vendor Data Dictionary; inside a workspace folder of pairs
(``…/pair_1/{FRD.docx, STTM.xlsx, VDD.xlsx}``) that doubles every list and
lets a dictionary be picked as the mapping. The discovery signatures already
tell the two apart:

* **sttm** — a mapping sheet is discoverable: a band row carrying a stage AND
  a standard token (content-driven), ``MAPPING-`` sheets, or the segmented
  family (``codegen.layout.discover.discover``) — and (Chunk A, 2026-10-09)
  one of its bands carries EVIDENCE of a target layer; target-shaped columns
  nothing names are ``unclassified`` with a reason starting ``confirm:``;
* **vdd** — a FILES sheet or a field sheet by header signature
  (``discover_vdd``; checked second — an STTM's "Layout" sheet may carry
  field-sheet-like headers);
* **unclassified** — neither. Never hidden: the chooser lists it with a badge,
  because a workbook the signatures do not know is exactly the one a person
  must be able to pick.

Pure and offline: a path in, a verdict and its reason (structural labels
only — sheet names and the strategy) out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from codegen.config import ExtractorConfig
from codegen.layout.discover import (
    CANDIDATE_SHEET_NOTE,
    NoLayoutError,
    discover,
    discover_vdd,
)

WorkbookKind = Literal["sttm", "vdd", "unclassified"]


@dataclass(frozen=True)
class WorkbookClass:
    kind: WorkbookKind
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "reason": self.reason}


def classify_workbook(path: Path, extractor: ExtractorConfig) -> WorkbookClass:
    unconfirmed: list[str] = []
    candidates: list[str] = []
    try:
        found = discover(path, extractor)
        # Chunk A: an STTM only when a band carries EVIDENCE of a target layer
        # (a stage / standard band). Target-shaped columns nothing names — a
        # dictionary or IIG sheet looks the same — are "unclassified —
        # confirm", never silently an STTM.
        # Chunk B: a CANDIDATE mapping sheet (pass 3 - read by its band title
        # spans or shared header qualifiers, no band row, no label group) is
        # never an STTM by itself: an IIG / dictionary sheet ("SRC_… / TGT_…")
        # has the same shape. "Confirm" - a person picks it as the STTM.
        candidates = [s.name for s in found.profile.mapping_sheets
                      if any(n.startswith(CANDIDATE_SHEET_NOTE) for n in s.notes)]
        mapping = [s.name for s in found.profile.mapping_sheets
                   if any(b.layer in ("stage", "standard") for b in s.bands)
                   and s.name not in candidates]
        if mapping:
            return WorkbookClass("sttm", f"mapping sheet(s) {mapping} "
                                         f"({found.profile.strategy} discovery)")
        unconfirmed = [s.name for s in found.profile.mapping_sheets if s.name not in candidates]
    except NoLayoutError:
        pass
    except Exception as exc:  # noqa: BLE001 — a workbook that cannot be opened is a fact to show
        return WorkbookClass("unclassified", f"could not be read: {type(exc).__name__}: {exc}")
    try:
        found = discover_vdd(path, extractor)
        sheets = [f"{s.name} ({s.kind})" for s in found.profile.sheets
                  if s.kind in ("vdd_files", "vdd_fields")]
        return WorkbookClass("vdd", f"dictionary sheet(s) {sheets}")
    except NoLayoutError:
        pass
    except Exception as exc:  # noqa: BLE001
        return WorkbookClass("unclassified", f"could not be read: {type(exc).__name__}: {exc}")
    if candidates and not unconfirmed:
        return WorkbookClass(
            "unclassified",
            "confirm: no band row with stage + standard labels (STTM) and no FILES / "
            f"field-sheet header (Vendor Data Dictionary); sheet(s) {candidates} read as "
            "CANDIDATE mapping sheets only (band title spans / shared header qualifiers) - an "
            "IIG or dictionary sheet has the same shape; pick it as the STTM to read it as one")
    if unconfirmed:
        return WorkbookClass(
            "unclassified",
            f"confirm: sheet(s) {unconfirmed} carry target-shaped columns (schema / table / "
            "column / data type) but no band title, header word, catalog or schema value names "
            "a stage or standard layer — pick it as the STTM to answer the band questions")
    return WorkbookClass(
        "unclassified",
        "no band row with stage + standard labels (STTM) and no FILES / field-sheet header "
        "(Vendor Data Dictionary)")


__all__ = ["WorkbookClass", "WorkbookKind", "classify_workbook"]
