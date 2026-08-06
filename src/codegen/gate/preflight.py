"""Structural + lint pre-flight over one feed's generated output.

Mirrors the checks the Code Review Agent applies, so generated code never
reaches a PR carrying a known failure: ruff (against the generated
ruff.toml), debug-statement scan, secrets scan, and one test file per
pipeline module.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from codegen.config import Config

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

# Directories under out/<feed>/ whose modules do not require a test file.
_TEST_EXEMPT_DIRS = {"job", "tools", "tests"}

_SECRET_RE = re.compile(
    r"""(?ix)
    (?:api[_-]?key|secret|password|passwd|token|credential)\s*[=:]\s*
    ['"][^'"]+['"]
    """
)


class GateCheck(BaseModel):
    model_config = _MODEL_CONFIG

    name: str
    passed: bool
    details: str


def _generated_text_files(feed_dir: Path) -> list[Path]:
    suffixes = {".py", ".sql", ".json", ".toml", ".md"}
    return sorted(p for p in feed_dir.rglob("*") if p.is_file() and p.suffix in suffixes)


def _ruff_check(feed_dir: Path) -> GateCheck:
    # --no-cache: ruff would otherwise drop .ruff_cache/ inside out/<feed>/,
    # polluting the generated tree and breaking byte-stability of the output.
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", str(feed_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    return GateCheck(
        name="ruff",
        passed=result.returncode == 0,
        details=output if result.returncode != 0 else "ruff clean",
    )


def _debug_pattern_check(feed_dir: Path, patterns: list[str]) -> GateCheck:
    hits: list[str] = []
    for path in _generated_text_files(feed_dir):
        if path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern in text:
                hits.append(f"{path.relative_to(feed_dir)}: contains {pattern!r}")
    return GateCheck(
        name="debug_patterns",
        passed=not hits,
        details="; ".join(hits) if hits else "no debug statements",
    )


def _secrets_check(feed_dir: Path) -> GateCheck:
    hits: list[str] = []
    for path in _generated_text_files(feed_dir):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _SECRET_RE.search(line):
                # Report location only — never echo the matched value.
                hits.append(f"{path.relative_to(feed_dir)}:{line_no}")
    return GateCheck(
        name="secrets",
        passed=not hits,
        details=(
            "possible hardcoded secret(s) at: " + "; ".join(hits)
            if hits
            else "no hardcoded secrets"
        ),
    )


def _test_per_module_check(feed_dir: Path) -> GateCheck:
    pipeline_dir = feed_dir / "pipeline"
    tests_dir = feed_dir / "tests"
    missing: list[str] = []
    for module in sorted(pipeline_dir.glob("*.py")):
        if module.stem == "__init__":
            continue
        if module.parent.name in _TEST_EXEMPT_DIRS:
            continue
        expected = tests_dir / f"test_{module.stem}.py"
        if not expected.is_file():
            missing.append(f"pipeline/{module.name} has no tests/test_{module.stem}.py")
    return GateCheck(
        name="test_per_module",
        passed=not missing,
        details="; ".join(missing) if missing else "every pipeline module has a test file",
    )


def run_preflight(feed_dir: Path, config: Config) -> list[GateCheck]:
    """Run the enabled pre-flight checks over ``out/<feed_slug>/``."""
    checks: list[GateCheck] = []
    if config.gate.ruff:
        checks.append(_ruff_check(feed_dir))
    if config.gate.structural_checks:
        checks.append(_debug_pattern_check(feed_dir, config.gate.debug_patterns))
        checks.append(_secrets_check(feed_dir))
        checks.append(_test_per_module_check(feed_dir))
    return checks
