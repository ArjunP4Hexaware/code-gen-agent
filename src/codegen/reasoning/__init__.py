"""Layer 2: LLM candidates for rules the deterministic compiler cannot map.

Candidates never land in generated modules — they go to a review artifact
awaiting engineer approval, and every citation is grounding-checked against
the contract text first.
"""

from codegen.reasoning.engine import RuleCandidate, run_reasoning
from codegen.reasoning.providers import build_provider

__all__ = ["RuleCandidate", "build_provider", "run_reasoning"]
