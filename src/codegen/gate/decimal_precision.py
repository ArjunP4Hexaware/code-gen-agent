"""post92: a DECIMAL column the STTM gives no precision (pair_03: five standard
columns typed bare ``DECIMAL``).

The type is written exactly as stated (``emit.context.sql_type``: ``DECIMAL``,
valid Databricks SQL, which reads it as DECIMAL(10,0) - no fractional digits).
No precision is derived (a source length is a byte width, not a precision); each
such column gets one non-blocking flag so the reviewer confirms it with the STTM
author.
"""

from __future__ import annotations

import re

from codegen.contracts.resolved import ResolvedFeedSpec

_BARE_DECIMAL = re.compile(r"^\s*decimal\s*$", re.IGNORECASE)


def _table(table) -> str | None:
    return table.table if table is not None else None


def decimal_no_precision_flags(spec: ResolvedFeedSpec) -> list[str]:
    flags: list[str] = []
    for segment in spec.segments:
        for f in segment.fields:
            for layer, dtype, column, table in (
                    ("stage", f.stage_datatype, f.stage_column, segment.stage_table.table),
                    ("standard", f.standard_datatype, f.standard_column or f.stage_column,
                     _table(segment.standard_table or spec.standard_table))):
                if not dtype or not _BARE_DECIMAL.match(dtype):
                    continue
                row = f" (STTM row {f.provenance.row})" if f.provenance and f.provenance.row else ""
                where = f"{table}.{column}" if table else column
                flags.append(
                    f"decimal_no_precision:{layer} — {where}: the STTM states DECIMAL with no "
                    f"precision{row}; written as DECIMAL, which Databricks reads as "
                    "DECIMAL(10,0) (no fractional digits) — confirm the precision with the "
                    "STTM author")
    return flags


__all__ = ["decimal_no_precision_flags"]
