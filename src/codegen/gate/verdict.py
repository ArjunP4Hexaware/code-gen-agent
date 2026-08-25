"""Compute the three-state gate verdict — in code, never by judgment.

FAIL    — any gate check failed (ruff, structural, generated tests). Contract
          validation errors, resolver mismatches, and TemplateGapError abort
          before the gate runs; the CLI reports those as FAIL directly.
PASS_WITH_FLAGS — everything passed but something needs a human: Layer-2
          candidates pending approval, or rules classified flagged /
          notification / out_of_scope, or tests skipped.
PASS    — all checks green and nothing pending.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from codegen.config import EngineeringStandardsConfig
from codegen.faq import WRITER_BEHAVIOR, LoadPatternFaq, answers
from codegen.gate.preflight import GateCheck
from codegen.reasoning.engine import RuleCandidate
from codegen.rules.compiler import RuleOutcome

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

Verdict = Literal["PASS", "PASS_WITH_FLAGS", "FAIL"]

# Rule classifications that need a human decision but are not defects.
_FLAG_CLASSIFICATIONS = {"flagged", "notification", "out_of_scope"}


class GateResult(BaseModel):
    model_config = _MODEL_CONFIG

    feed_id: str
    verdict: Verdict
    checks: list[GateCheck]
    flags: list[str]


def compute_verdict(
    feed_id: str,
    outcomes: list[RuleOutcome],
    candidates: list[RuleCandidate],
    checks: list[GateCheck],
    tests_skipped: bool,
    *,
    faq: LoadPatternFaq | None = None,
    standards: EngineeringStandardsConfig | None = None,
) -> GateResult:
    flags: list[str] = []
    # Three-input model honesty flags (never FAIL — same rule as Layer 2):
    # unanswered FAQ questions, a declared-but-not-enforced load mode, and a
    # stubbed standards document all need a human, not a red light.
    if faq is not None:
        for name, answer in answers(faq).items():
            if answer.source == "unknown":
                flags.append(f"faq_unanswered:{name}")
        if faq.load_mode.value != "unknown":
            flags.append(
                f"load_mode_not_enforced: declared {faq.load_mode.value}; "
                f"generated writer uses {WRITER_BEHAVIOR} (branching planned v2)"
            )
    if standards is not None and standards.status.startswith("STUB"):
        flags.append(f"standards_stub: {standards.status}")
    for outcome in outcomes:
        if outcome.classification in _FLAG_CLASSIFICATIONS:
            flags.append(
                f"rule classified {outcome.classification}: {outcome.rule_text!r}"
                + (f" — {outcome.notes}" if outcome.notes else "")
            )
    for candidate in candidates:
        if candidate.response is None:
            flags.append(
                f"Layer-2 provider failed for rule {candidate.rule_text!r}: "
                + "; ".join(candidate.failure_notes)
            )
        elif not candidate.grounded:
            flags.append(
                f"Layer-2 candidate NOT grounded for rule {candidate.rule_text!r}: "
                + "; ".join(candidate.failure_notes)
            )
        else:
            flags.append(f"Layer-2 candidate pending engineer approval: {candidate.rule_text!r}")
    if tests_skipped:
        flags.append("generated tests were skipped — PASS cannot be claimed")

    if any(not check.passed for check in checks):
        verdict: Verdict = "FAIL"
    elif flags:
        verdict = "PASS_WITH_FLAGS"
    else:
        verdict = "PASS"
    return GateResult(feed_id=feed_id, verdict=verdict, checks=checks, flags=flags)
