"""Classify each FRD free-text validation rule against known templates.

Every classification is grounded: the outcome records the exact matched text
span. Rules that reference columns or features the STTM side does not
confirm are *flagged* (they degrade the gate to PASS_WITH_FLAGS), never
silently dropped and never silently compiled. Only rules nothing here can
classify go to Layer 2 (the LLM) as ``unmapped``.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

from codegen.contracts.resolved import ResolvedFeedSpec

Classification = Literal[
    "mappable",
    "orchestration_config",
    "notification",
    "out_of_scope",
    "flagged",
    "unmapped",
]

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class RuleOutcome(BaseModel):
    model_config = _MODEL_CONFIG

    feed_id: str
    rule_text: str
    classification: Classification
    # The generated feature that implements a mappable rule.
    feature: str | None
    # Exact substring of the rule text that fired the classification.
    grounding: str
    notes: str | None


_NULL_REJECT_RE = re.compile(r"If the (?P<column>\w+) column is NULL,? reject", re.IGNORECASE)
# FRD Data Quality phrasing (SFMC Email Campaign FRD, 2026-08-26): the
# incomplete-record rejection over the STTM's mandatory columns — exactly
# what rejects.py compiles from load_rules.not_null_columns.
_MANDATORY_REJECT_RE = re.compile(
    r"incomplete record rejection|mandatory columns?\b.{0,80}?\breject", re.IGNORECASE | re.DOTALL
)
_LAYOUT_RE = re.compile(r"fail when file layout is not as per source dictionary", re.IGNORECASE)
_DUPLICATE_FILE_RE = re.compile(r"Duplicate file name check.*?turned off", re.IGNORECASE)
_PIPE_DELIMITED_RE = re.compile(r"pipe[\s-]delimited", re.IGNORECASE)
_FACETS_VALIDATION_RE = re.compile(r"validation should be performed against Facets", re.IGNORECASE)
_AS_IS_RE = re.compile(r"(AS[-‑]IS|should not perform any data transformation)", re.IGNORECASE)
_RECYCLE_RE = re.compile(r"recycle", re.IGNORECASE)
# Both the legacy "notification will be sent" and the SFMC FRD / EDO coding
# standard phrasing ("Email notification should be sent to the Support
# team ... whenever there is an issue").
_NOTIFICATION_RE = re.compile(
    r"notification (?:will|should|shall) be sent|email notification", re.IGNORECASE
)
_AUDIT_POPULATE_RE = re.compile(
    r"populate (?P<fields>.+?) fields? in the target tables", re.IGNORECASE
)

# Free-text audit field phrases -> the audit column that satisfies them.
_AUDIT_FIELD_SYNONYMS = {
    "source file name": "SRC_FILE_NAME",
    "file name": "SRC_FILE_NAME",
    "load timestamp": "REC_CREATION_TIME",
    "lob id": "LOB",
    "lob": "LOB",
}


def _source_and_stage_columns(spec: ResolvedFeedSpec) -> set[str]:
    columns: set[str] = set()
    for segment in spec.segments:
        for field in segment.fields:
            columns.add(field.source_column.lower())
            columns.add(field.stage_column.lower())
    return columns


def _classify_null_reject(spec: ResolvedFeedSpec, rule: str, match: re.Match) -> RuleOutcome:
    column = match.group("column")
    known = _source_and_stage_columns(spec)
    if column.lower() not in known:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="flagged",
            feature=None,
            grounding=match.group(0),
            notes=(
                f"rule names column '{column}' which does not exist in this feed's "
                "STTM mapping — unconfirmed attribution (see FRD _provenance "
                "ambiguities); no code generated for it"
            ),
        )
    not_null = {c.lower() for c in spec.not_null_columns}
    if column.lower() not in not_null:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="flagged",
            feature=None,
            grounding=match.group(0),
            notes=(
                f"rule wants '{column}' rejected on NULL but the STTM does not mark "
                "it not-null — contracts disagree; resolve before compiling"
            ),
        )
    return RuleOutcome(
        feed_id=spec.feed_id,
        rule_text=rule,
        classification="mappable",
        feature="null_reject",
        grounding=match.group(0),
        notes=f"compiled: rejects.py enforces not-null on '{column}' into the errors table",
    )


def _classify_mandatory_reject(spec: ResolvedFeedSpec, rule: str, match: re.Match) -> RuleOutcome:
    if not spec.not_null_columns:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="flagged",
            feature=None,
            grounding=match.group(0),
            notes=(
                "rule wants incomplete records rejected but the STTM lists no "
                "not-null/mandatory columns — contracts disagree; resolve before compiling"
            ),
        )
    return RuleOutcome(
        feed_id=spec.feed_id,
        rule_text=rule,
        classification="mappable",
        feature="null_reject",
        grounding=match.group(0),
        notes=(
            f"compiled: rejects.py enforces not-null on the {len(spec.not_null_columns)} "
            "STTM mandatory column(s) into the errors table"
        ),
    )


def _classify_recycle(spec: ResolvedFeedSpec, rule: str, match: re.Match) -> RuleOutcome:
    if spec.recycle is None:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="flagged",
            feature=None,
            grounding=match.group(0),
            notes=(
                "FRD states a recycle rule but the STTM has no structured recycle "
                "spec for this feed — unconfirmed attribution; no recycle module "
                "generated"
            ),
        )
    return RuleOutcome(
        feed_id=spec.feed_id,
        rule_text=rule,
        classification="mappable",
        feature="recycle",
        grounding=match.group(0),
        notes=(
            f"compiled: recycle.py, {spec.recycle.spec.recycle_window_days}-day window "
            f"against {spec.recycle.reference_table}"
        ),
    )


def _classify_audit_populate(spec: ResolvedFeedSpec, rule: str, match: re.Match) -> RuleOutcome:
    raw_fields = re.split(r",| and ", match.group("fields"))
    audit_columns = {a.column for a in spec.audit_columns}
    unresolved: list[str] = []
    for raw in (f.strip().lower() for f in raw_fields if f.strip()):
        mapped = _AUDIT_FIELD_SYNONYMS.get(raw)
        if mapped is None or mapped not in audit_columns:
            unresolved.append(raw)
    if unresolved:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="unmapped",
            feature=None,
            grounding=match.group(0),
            notes=(
                f"audit-populate rule names field(s) {unresolved} that map to no "
                "known audit column — sent to Layer 2 for a reviewed candidate"
            ),
        )
    return RuleOutcome(
        feed_id=spec.feed_id,
        rule_text=rule,
        classification="mappable",
        feature="audit_columns",
        grounding=match.group(0),
        notes="compiled: audit.py populates the named audit columns",
    )


def compile_rules(spec: ResolvedFeedSpec) -> list[RuleOutcome]:
    """Classify every validation rule for one feed, in contract order."""
    outcomes: list[RuleOutcome] = []
    for rule in spec.validation_rules:
        outcomes.append(_classify_one(spec, rule))
    return outcomes


def _classify_one(spec: ResolvedFeedSpec, rule: str) -> RuleOutcome:
    match = _NULL_REJECT_RE.search(rule)
    if match:
        return _classify_null_reject(spec, rule, match)

    match = _MANDATORY_REJECT_RE.search(rule)
    if match:
        return _classify_mandatory_reject(spec, rule, match)

    match = _LAYOUT_RE.search(rule)
    if match:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="mappable",
            feature="drift_fail",
            grounding=match.group(0),
            notes="compiled: drift.py fails the file on layout drift",
        )

    match = _DUPLICATE_FILE_RE.search(rule)
    if match:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="orchestration_config",
            feature="allow_duplicate_file_name",
            grounding=match.group(0),
            notes="compiled: feed_spec.ALLOW_DUPLICATE_FILE_NAME = True",
        )

    match = _NOTIFICATION_RE.search(rule)
    if match:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="notification",
            feature=None,
            grounding=match.group(0),
            notes=(
                "job JSON carries an email_notifications block; recipients come "
                "from config (job.notification_emails)"
            ),
        )

    match = _AUDIT_POPULATE_RE.search(rule)
    if match:
        return _classify_audit_populate(spec, rule, match)

    match = _FACETS_VALIDATION_RE.search(rule)
    if match:
        if spec.recycle is None:
            return RuleOutcome(
                feed_id=spec.feed_id,
                rule_text=rule,
                classification="flagged",
                feature=None,
                grounding=match.group(0),
                notes=(
                    "rule wants Facets validation but the STTM has no recycle/"
                    "reference spec for this feed"
                ),
            )
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="mappable",
            feature="reference_validation",
            grounding=match.group(0),
            notes="compiled: reference.py + recycle.py validate against Facets",
        )

    match = _AS_IS_RE.search(rule)
    if match:
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification="mappable",
            feature="identity_mapping",
            grounding=match.group(0),
            notes="compiled: mapping.py is rename-only select, no transformation",
        )

    match = _RECYCLE_RE.search(rule)
    if match:
        return _classify_recycle(spec, rule, match)

    match = _PIPE_DELIMITED_RE.search(rule)
    if match:
        delimiter_note = (
            "confirmed: resolved delimiter is '|'"
            if spec.delimiter == "|"
            else f"MISMATCH: resolved delimiter is {spec.delimiter!r}"
        )
        classification = "orchestration_config" if spec.delimiter == "|" else "flagged"
        return RuleOutcome(
            feed_id=spec.feed_id,
            rule_text=rule,
            classification=classification,
            feature="delimiter",
            grounding=match.group(0),
            notes=delimiter_note,
        )

    return RuleOutcome(
        feed_id=spec.feed_id,
        rule_text=rule,
        classification="unmapped",
        feature=None,
        grounding=rule,
        notes="no deterministic template matches — sent to Layer 2 for a reviewed candidate",
    )
