"""Pydantic models for the two input contracts and the resolved feed spec.

Everything crossing into generation is defined here. House style (shared with
the Code Review Agent): ``frozen=True``, ``extra="forbid"`` — unknown keys
fail loudly rather than being dropped; a missing value is ``None``, never a
default that could be mistaken for a real one.
"""

from codegen.contracts.frd import FrdContract, FrdFeed, TargetSpec
from codegen.contracts.resolved import ResolvedFeedSpec, SegmentSpec
from codegen.contracts.sttm import (
    AuditColumn,
    LoadRules,
    RecycleSpec,
    SttmContract,
    SttmFeed,
    SttmField,
)

__all__ = [
    "AuditColumn",
    "FrdContract",
    "FrdFeed",
    "LoadRules",
    "RecycleSpec",
    "ResolvedFeedSpec",
    "SegmentSpec",
    "SttmContract",
    "SttmFeed",
    "SttmField",
    "TargetSpec",
]
