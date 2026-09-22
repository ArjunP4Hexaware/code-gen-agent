"""Deterministic mock provider — the default Layer 2 backend.

Produces the same generic, clearly-labeled sketch for any rule: enough to
exercise the grounding check, the candidates artifact, and the gate's
PASS_WITH_FLAGS path without a model or network. The sketch is a comment
block, not runnable code, so it cannot be mistaken for an implementation.
"""

from __future__ import annotations

from codegen.reasoning.schema import CandidateResponse, ContextPack


class MockProvider:
    name = "mock"
    calls = 0   # a mock never sends a model call (codegen.reasoning.usage)

    def __init__(self, reason: str | None = None) -> None:
        # Why the mock answered: a lock env var, an unreachable endpoint,
        # dry-run — set by build_provider; "test" when constructed directly.
        self.mock_reason = reason or "test"

    def complete(self, pack: ContextPack) -> CandidateResponse:
        sketch = (
            f"# LAYER-2 CANDIDATE (mock provider) — feed {pack.feed_id}\n"
            f"# Rule: {pack.rule_text}\n"
            "# Sketch: implement this rule using only columns the STTM defines\n"
            "# (see available_stage_columns / audit_columns in the context pack).\n"
            "# An engineer must replace this sketch before any code lands.\n"
        )
        return CandidateResponse(
            classification="mappable",
            code_candidate=sketch,
            rationale=(
                "Mock provider: deterministic stand-in generated without model "
                "access, grounded on the rule text alone. Requires engineer review."
            ),
            citations=[pack.rule_text],
        )
