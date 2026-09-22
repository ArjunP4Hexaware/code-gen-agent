"""Gate: pre-flight the Code Review Agent's checks over generated output.

The gate never mutates generated files — it only observes and produces a
three-state verdict (PASS / PASS_WITH_FLAGS / FAIL) computed in code.
"""

from codegen.gate.preflight import GateCheck, natural_key_check, run_preflight
from codegen.gate.tests_runner import run_generated_tests
from codegen.gate.verdict import GateResult, Verdict, compute_verdict

__all__ = [
    "GateCheck",
    "GateResult",
    "Verdict",
    "compute_verdict",
    "natural_key_check",
    "run_generated_tests",
    "run_preflight",
]
