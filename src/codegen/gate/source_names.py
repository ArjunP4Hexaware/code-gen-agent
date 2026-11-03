"""post93 (pair_03): a source layout whose column names repeat (10 x Qualifier,
10 x Type - a repeating group; the stage / standard names are unique).

A repeated name identifies no field, so the IIG's SRC_COLUMNS takes its
positional form (``col<i>:<stage column>``, metadata_template._named_sources) and
a generated pipeline reading a file without a header row names the fields by
position too (emit.context.pipeline_source_names). One non-blocking flag per
segment names the repeated columns; a file WITH a header row keeps its header's
names, so the flag says the pipeline is not covered there.
"""

from __future__ import annotations

from collections import Counter

from codegen.contracts.resolved import ResolvedFeedSpec


def repeated_names(fields) -> dict[str, int]:
    """Source names given to more than one field, with their counts."""
    counts = Counter((f.source_column or "").strip() for f in fields)
    return {name: n for name, n in counts.items() if name and n > 1}


def repeated_source_name_flags(spec: ResolvedFeedSpec, *, headerless: bool) -> list[str]:
    flags: list[str] = []
    for segment in spec.segments:
        repeated = repeated_names(segment.fields)
        if not repeated:
            continue
        names = ", ".join(f"{name} x{n}" for name, n in repeated.items())
        pipeline = ("the generated pipeline names the fields by position too"
                    if headerless else
                    "the file has a header row: the generated pipeline keeps its names "
                    "(not covered - review)")
        flags.append(
            f"source_names_repeated:{segment.segment} — {segment.stage_table.table}: "
            f"source columns {names}; SRC_COLUMNS is positional (col<i>:<stage column>), "
            f"{pipeline}; the stage / standard names are unchanged")
    return flags


__all__ = ["repeated_names", "repeated_source_name_flags"]
