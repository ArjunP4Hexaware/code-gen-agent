"""Run a feed's generated pytest suite in a subprocess.

The full environment passes through: the generated tests run real Spark, so
JAVA_HOME / HADOOP_HOME / PYSPARK_PYTHON must reach the child process. cwd
is the feed directory; the generated conftest handles sys.path itself.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from codegen.gate.preflight import GateCheck


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
        env=os.environ.copy(),
    )
    output_lines = (result.stdout + result.stderr).strip().splitlines()
    tail = "\n".join(output_lines[-tail_lines:])
    return GateCheck(
        name="generated_tests",
        passed=result.returncode == 0,
        details=tail if tail else "pytest produced no output",
    )
