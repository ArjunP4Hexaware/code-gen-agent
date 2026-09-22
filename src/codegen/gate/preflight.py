"""Structural + lint pre-flight over one feed's generated output.

Mirrors the checks the Code Review Agent applies, so generated code never
reaches a PR carrying a known failure: ruff (against the generated
ruff.toml), debug-statement scan, secrets scan, and one test file per
pipeline module.
"""

from __future__ import annotations

import contextlib
import json
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
    # M9.1b: the check could not be PERFORMED (the tool did not run) — not a
    # finding about the generated code. Never a FAIL: the verdict carries a
    # `check_not_run:<name>` flag instead ("PASS cannot be claimed"), like
    # skipped tests. ``passed`` is True on such a check by construction.
    not_run: bool = False


def _generated_text_files(feed_dir: Path) -> list[Path]:
    suffixes = {".py", ".sql", ".json", ".toml", ".md"}
    return sorted(p for p in feed_dir.rglob("*") if p.is_file() and p.suffix in suffixes)


def _ruff_check(feed_dir: Path) -> GateCheck:
    # --no-cache: ruff would otherwise drop .ruff_cache/ inside out/<feed>/,
    # polluting the generated tree and breaking byte-stability of the output.
    # JSON output (M9.1b) separates the two ways `ruff check` exits non-zero:
    # it FOUND violations (a list of them on stdout — a finding, FAIL), or it
    # could not run at all (no module / no binary in this environment, a
    # config it rejects: no JSON — the code was NOT linted, which is a flag,
    # not a verdict on the code). A run inside ACFC came back `ruff=FAIL` with
    # nothing to tell the two apart.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format", "json",
             str(feed_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return GateCheck(name="ruff", passed=True, not_run=True,
                         details=f"ruff could not be started: {exc}")
    try:
        findings = json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError:
        findings = None
    if not isinstance(findings, list):
        if result.returncode == 0:
            return GateCheck(name="ruff", passed=True, details="ruff clean")
        output = (result.stdout + result.stderr).strip()
        return GateCheck(name="ruff", passed=True, not_run=True,
                         details=f"ruff did not run (exit {result.returncode}): "
                                 f"{output or 'no output'}")
    if not findings:
        return GateCheck(name="ruff", passed=True, details="ruff clean")
    lines = []
    for item in findings:
        where = Path(str(item.get("filename") or ""))
        with contextlib.suppress(ValueError):
            where = where.resolve().relative_to(feed_dir.resolve())
        location = item.get("location") or {}
        lines.append(f"{where.as_posix()}:{location.get('row', '?')}:"
                     f"{location.get('column', '?')}: {item.get('code') or 'syntax'} "
                     f"{item.get('message', '')}".rstrip())
    return GateCheck(name="ruff", passed=False,
                     details=f"{len(findings)} finding(s)\n" + "\n".join(lines))


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


def audit_type_check(spec, profile) -> GateCheck:
    """M11: audit columns whose declared type is outside String / Timestamp.
    Under a profile that restricts them this is a FAIL naming each column;
    otherwise the type is emitted as declared (flag audit_type_nonstandard).
    """
    standard = {"string", "timestamp"}
    columns = [(a.column, a.datatype) for s in spec.segments
               for a in (s.audit_columns or [])] or []
    columns += [(a.column, a.datatype) for a in spec.audit_columns]
    nonstandard = sorted({f"{c} ({t})" for c, t in columns if t.strip().lower() not in standard})
    if nonstandard and getattr(profile, "audit_types_restricted", True):
        return GateCheck(
            name="audit_types", passed=False,
            details=(f"audit column(s) {', '.join(nonstandard)} declare a type outside "
                     "String / Timestamp, which this conventions profile restricts "
                     "(conventions.profiles.<profile>.audit_types_restricted) — state a "
                     "standard type in the STTM or select a profile that accepts it"))
    return GateCheck(
        name="audit_types", passed=True,
        details=(f"audit column(s) {', '.join(nonstandard)} carry the type the STTM declares"
                 if nonstandard else "every audit column is String / Timestamp"))


def natural_key_check(context: dict) -> GateCheck:
    """M10.1: every natural-key column must be a stage column of SOME segment.
    A column no segment carries used to be a KeyError inside build_context
    (the v0.6.0 ACFC run, a trailer record-type column in the key); it is a
    FAIL that names the column and the segments that were searched."""
    missing = list(context.get("natural_key_missing") or [])
    segments = [s.get("name") for s in context.get("segments") or []]
    if missing:
        return GateCheck(
            name="natural_key_columns", passed=False,
            details=(f"natural key column(s) {', '.join(missing)} exist in no segment "
                     f"(searched: {', '.join(str(s) for s in segments) or 'the feed'}); "
                     "the STTM's key must name stage columns the mapping defines"))
    placed = context.get("natural_key_segments") or {}
    return GateCheck(
        name="natural_key_columns", passed=True,
        details=("every natural key column is a stage column of a segment: "
                 + ", ".join(f"{c} ({seg})" for c, seg in placed.items())
                 if placed else "the feed declares no natural key"))


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
