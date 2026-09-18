"""Drag-fill detector (M4): DECIMAL precision/scale that increments
monotonically across adjacent STTM columns is almost certainly a spreadsheet
fill-handle accident (``Decimal(17,2)`` … ``Decimal(22,2)``), not a design.
The gate FLAGS the run citing the columns and their STTM rows; the output is
NOT altered — the types are transcribed exactly as the STTM states them
(the client golden carries the very same run).
"""

from __future__ import annotations

import re

from codegen.contracts.resolved import ResolvedFeedSpec

_DECIMAL_RE = re.compile(r"^\s*(?:decimal|numeric|number)\s*\(\s*(\d+)\s*(?:,\s*(\d+))?\s*\)\s*$",
                         re.IGNORECASE)
# A run this long of +1 precision steps is a flag.
_MIN_RUN = 3


def _precision_scale(dtype: str | None) -> tuple[int, int] | None:
    match = _DECIMAL_RE.match(dtype or "")
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2) or 0)


_Run = list[tuple[str, str, int | None]]


def _runs(columns: list[tuple[str, str | None, int | None]]) -> list[_Run]:
    """Maximal runs of adjacent decimal columns whose precision rises by
    exactly one per step at constant scale."""
    runs: list[_Run] = []
    current: _Run = []
    previous: tuple[int, int] | None = None
    for name, dtype, row in columns:
        parsed = _precision_scale(dtype)
        if parsed is not None and previous is not None and parsed == (previous[0] + 1, previous[1]):
            current.append((name, dtype or "", row))
        else:
            if len(current) >= _MIN_RUN:
                runs.append(current)
            current = [(name, dtype or "", row)] if parsed is not None else []
        previous = parsed
    if len(current) >= _MIN_RUN:
        runs.append(current)
    return runs


def drag_fill_flags(spec: ResolvedFeedSpec) -> list[str]:
    flags: list[str] = []
    for segment in spec.segments:
        for layer, attr in (("stage", "stage_datatype"), ("standard", "standard_datatype")):
            columns = [
                (f.stage_column if layer == "stage" else (f.standard_column or f.stage_column),
                 getattr(f, attr), f.provenance.row if f.provenance else None)
                for f in segment.fields
            ]
            if layer == "standard" and all(
                    f.standard_datatype == f.stage_datatype for f in segment.fields):
                continue  # identical to the stage run already reported
            for run in _runs(columns):
                names = ", ".join(name for name, _t, _r in run)
                rows = [r for _n, _t, r in run if r is not None]
                where = (f" (STTM rows {rows[0]}–{rows[-1]})" if rows else "")
                flags.append(
                    f"drag_fill_suspect:{layer} — {segment.stage_table.table} columns {names}: "
                    f"{run[0][1]} → {run[-1][1]} increments by one per adjacent column"
                    f"{where}; transcribed as stated, confirm with the STTM author")
    return flags


__all__ = ["drag_fill_flags"]
