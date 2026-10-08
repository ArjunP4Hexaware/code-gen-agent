"""Run a feed's generated pytest suite in a subprocess.

The full environment passes through: the generated tests run real Spark, so
JAVA_HOME / HADOOP_HOME / PYSPARK_PYTHON must reach the child process. cwd
is the feed directory; the generated conftest handles sys.path itself.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from codegen._srcpath import child_env
from codegen.gate.preflight import GateCheck

SPARK_UNAVAILABLE = "spark_unavailable"
# PySpark's error class when no Spark session can be configured here (no JVM,
# no JAVA_HOME, a sandbox that refuses the gateway): the tests did not RUN.
_SPARK_UNAVAILABLE_MARKERS = ("CANNOT_CONFIGURE_SPARK", "JAVA_GATEWAY_EXITED")


def run_generated_tests(feed_dir: Path, tail_lines: int) -> GateCheck:
    """``tail_lines`` (config: gate.pytest_tail_lines) bounds the kept output."""
    # Absolute paths: cwd moves to the feed dir, so a config-relative
    # output path would no longer resolve.
    feed_dir = feed_dir.resolve()
    tests_dir = feed_dir / "tests"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-q"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(feed_dir),
        env=child_env(),
    )
    output_lines = (result.stdout + result.stderr).strip().splitlines()
    tail = "\n".join(output_lines[-tail_lines:])
    marker = next((m for m in _SPARK_UNAVAILABLE_MARKERS
                   if result.returncode != 0 and m in result.stdout + result.stderr), None)
    if marker is not None:
        # First real-row scorecard (2026-10-08): no Spark session here is not
        # a finding about the generated code — CHECK NOT RUN, flagged.
        line = next((ln for ln in output_lines if marker in ln), marker)
        return GateCheck(name="generated_tests", passed=True, not_run=True,
                         flag=SPARK_UNAVAILABLE,
                         details=f"a Spark session could not be configured ({marker}): "
                                 f"{line.strip()[:200]}")
    return GateCheck(
        name="generated_tests",
        passed=result.returncode == 0,
        details=tail if tail else "pytest produced no output",
    )
