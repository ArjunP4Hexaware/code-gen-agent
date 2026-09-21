"""What KIND of workbook is this — by what it says, never by its name (M9.3).

The document chooser used to list every ``.xlsx`` as an STTM and again as a
possible Vendor Data Dictionary; inside a workspace folder of pairs
(``…/pair_1/{FRD.docx, STTM.xlsx, VDD.xlsx}``) that doubles every list and
lets a dictionary be picked as the mapping. The discovery signatures already
tell the two apart:

* **sttm** — a mapping sheet is discoverable: a band row carrying a stage AND
  a standard token (content-driven), ``MAPPING-`` sheets, or the segmented
  family (``codegen.layout.discover.discover``);
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
from codegen.layout.discover import NoLayoutError, discover, discover_vdd

WorkbookKind = Literal["sttm", "vdd", "unclassified"]


@dataclass(frozen=True)
class WorkbookClass:
    kind: WorkbookKind
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "reason": self.reason}


def classify_workbook(path: Path, extractor: ExtractorConfig) -> WorkbookClass:
    try:
        found = discover(path, extractor)
        mapping = [s.name for s in found.profile.mapping_sheets]
        if mapping:
            return WorkbookClass("sttm", f"mapping sheet(s) {mapping} "
                                         f"({found.profile.strategy} discovery)")
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
    return WorkbookClass(
        "unclassified",
        "no band row with stage + standard labels (STTM) and no FILES / field-sheet header "
        "(Vendor Data Dictionary)")


__all__ = ["WorkbookClass", "WorkbookKind", "classify_workbook"]
