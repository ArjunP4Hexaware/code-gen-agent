"""Structural + lint pre-flight over one feed's generated output.

Mirrors the checks the Code Review Agent applies, so generated code never
reaches a PR carrying a known failure: ruff (against the generated
ruff.toml), debug-statement scan, secrets scan, and one test file per
pipeline module.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from codegen._srcpath import child_env
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
    # The flag kind a not-run check raises (default ``check_not_run:<name>``);
    # e.g. ``ruff_unavailable`` when the ruff module is not installed.
    flag: str | None = None
    # First real-row scorecard: the emitted .py files `ruff format` rewrote
    # before the lint (E501 never fails a feed) — the ruff_formatted flag.
    formatted: list[str] = []
    # First ACFC run: what the check FIXED before it judged (ruff's safe
    # fixes — cosmetic lint never FAILs a feed); the verdict flags it
    # ``ruff_fixed``. One "<file>: <code> xN" entry per fixed kind.
    fixes: list[str] = []


def _generated_text_files(feed_dir: Path) -> list[Path]:
    suffixes = {".py", ".sql", ".json", ".toml", ".md"}
    return sorted(p for p in feed_dir.rglob("*") if p.is_file() and p.suffix in suffixes)


RUFF_UNAVAILABLE = "ruff_unavailable"


def _ruff_unavailable(reason: str) -> GateCheck:
    """ruff is not installed where the gate runs: a FLAG naming why, never a
    FAIL — the generated code was not linted, and the verdict says so."""
    return GateCheck(name="ruff", passed=True, not_run=True, flag=RUFF_UNAVAILABLE,
                     details=f"ruff unavailable: {reason} (ruff is a base dependency of "
                             "codegen-data-engineer-agent — reinstall the package)")


def _ruff_json(feed_dir: Path, *extra: str):
    """(findings list | None, completed process) of ``ruff check`` over the
    feed with JSON output; ``extra`` = e.g. ``--fix``."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", *extra, "--output-format",
         "json", str(feed_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=child_env(),
    )
    try:
        findings = json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError:
        findings = None
    return (findings if isinstance(findings, list) else None), result


def _finding_key(item: dict, feed_dir: Path) -> tuple[str, str]:
    where = Path(str(item.get("filename") or ""))
    with contextlib.suppress(ValueError):
        where = where.resolve().relative_to(feed_dir.resolve())
    return where.as_posix(), str(item.get("code") or "syntax")


def _format_emitted(feed_dir: Path) -> tuple[list[str], str]:
    """`ruff format` over every emitted .py of the feed (the feed's own
    ruff.toml: line length, target) BEFORE the lint, so a long generated line
    is wrapped instead of failing E501. Returns (rewritten files relative to
    the feed, a problem note). The assembled notebook is re-synced when a
    module or the entrypoint changed."""
    files = sorted(feed_dir.rglob("*.py"))
    if not files:
        return [], ""
    before = {p: p.read_bytes() for p in files}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--no-cache", str(feed_dir)],
            capture_output=True, text=True, check=False, env=child_env())
    except OSError as exc:
        return [], f"ruff format could not be started: {exc}"
    if result.returncode != 0:
        return [], f"ruff format did not run (exit {result.returncode}): " + (
            (result.stdout + result.stderr).strip()[:200])
    changed = [p for p in files if p.read_bytes() != before[p]]
    rewritten = [p.relative_to(feed_dir).as_posix() for p in changed]
    notebook = feed_dir / f"{feed_dir.name}.ipynb"
    if notebook.is_file() and any(p.parent.name in ("pipeline", "job") for p in changed):
        from codegen.emit.context import TemplateGapError
        from codegen.emit.notebook import resync_notebook

        try:
            resync_notebook(notebook, feed_dir)
        except (TemplateGapError, SyntaxError) as exc:
            return rewritten, (f"the formatted modules no longer assemble into "
                               f"{notebook.name}: {exc}")
    return rewritten, ""


def _apply_safe_fixes(feed_dir: Path, findings: list) -> tuple[list | None, list[str], str]:
    """Apply ruff's SAFE fixes (``--fix`` without ``--unsafe-fixes``) when any
    finding has one. Returns (remaining findings | None when the fix run gave
    no JSON, "<file>: <code> xN" per fixed kind, a problem note). The
    assembled notebook is re-synced from the fixed modules."""
    safe = [f for f in findings if (f.get("fix") or {}).get("applicability") == "safe"]
    if not safe:
        return findings, [], ""
    tracked = [*sorted((feed_dir / "pipeline").glob("*.py")),
               feed_dir / "job" / "notebook_entrypoint.py"]
    before = {p: p.read_bytes() for p in tracked if p.is_file()}
    remaining, _result = _ruff_json(feed_dir, "--fix")
    if remaining is None:
        return None, [], "the ruff --fix run returned no JSON"
    left: dict[tuple[str, str], int] = {}
    for item in remaining:
        key = _finding_key(item, feed_dir)
        left[key] = left.get(key, 0) + 1
    counts: dict[tuple[str, str], int] = {}
    for item in safe:
        key = _finding_key(item, feed_dir)
        counts[key] = counts.get(key, 0) + 1
    unsafe: dict[tuple[str, str], int] = {}
    for item in findings:
        if item not in safe:
            key = _finding_key(item, feed_dir)
            unsafe[key] = unsafe.get(key, 0) + 1
    fixes = []
    for key in sorted(counts):
        # what is left of this kind beyond the findings that had no safe fix
        unfixed = max(0, left.get(key, 0) - unsafe.get(key, 0))
        if counts[key] - unfixed > 0:
            fixes.append(f"{key[0]}: {key[1]} x{counts[key] - unfixed}")
    notebook = feed_dir / f"{feed_dir.name}.ipynb"
    changed = any(p.read_bytes() != data for p, data in before.items())
    if changed and notebook.is_file():
        from codegen.emit.context import TemplateGapError
        from codegen.emit.notebook import resync_notebook

        try:
            resync_notebook(notebook, feed_dir)
        except (TemplateGapError, SyntaxError) as exc:
            return remaining, fixes, (f"the fixed modules no longer assemble into "
                                      f"{notebook.name}: {exc}")
    return remaining, fixes, ""


def _ruff_check(feed_dir: Path) -> GateCheck:
    # --no-cache: ruff would otherwise drop .ruff_cache/ inside out/<feed>/,
    # polluting the generated tree and breaking byte-stability of the output.
    # JSON output (M9.1b) separates the two ways `ruff check` exits non-zero:
    # it FOUND violations (a list of them on stdout — a finding, FAIL), or it
    # could not run at all (no module / no binary in this environment, a
    # config it rejects: no JSON — the code was NOT linted, which is a flag,
    # not a verdict on the code). A run inside ACFC came back `ruff=FAIL` with
    # nothing to tell the two apart.
    # First ACFC run: ruff's SAFE fixes are applied first (and recorded as
    # the ``ruff_fixed`` flag), so cosmetic lint never FAILs a feed; what
    # remains after them is the finding.
    if importlib.util.find_spec("ruff") is None:
        return _ruff_unavailable(f"the ruff module is not installed for {sys.executable}")
    formatted, format_problem = _format_emitted(feed_dir)
    if format_problem and formatted:
        return GateCheck(name="ruff", passed=False, formatted=formatted,
                         details=f"ruff format: {format_problem}")
    try:
        findings, result = _ruff_json(feed_dir)
    except OSError as exc:
        return GateCheck(name="ruff", passed=True, not_run=True,
                         details=f"ruff could not be started: {exc}")
    check = _judge_ruff(feed_dir, findings, result)
    if formatted:
        check = check.model_copy(update={"formatted": formatted})
    return check


def _judge_ruff(feed_dir: Path, findings, result) -> GateCheck:
    if findings is None:
        if result.returncode == 0:
            return GateCheck(name="ruff", passed=True, details="ruff clean")
        output = (result.stdout + result.stderr).strip()
        if "No module named ruff" in output:
            return _ruff_unavailable(output.splitlines()[-1])
        return GateCheck(name="ruff", passed=True, not_run=True,
                         details=f"ruff did not run (exit {result.returncode}): "
                                 f"{output or 'no output'}")
    if not findings:
        return GateCheck(name="ruff", passed=True, details="ruff clean")
    remaining, fixes, problem = _apply_safe_fixes(feed_dir, findings)
    if remaining is None:
        # The fix run itself did not report: the code was not judged.
        return GateCheck(name="ruff", passed=True, not_run=True,
                         details=f"ruff safe fixes: {problem}")
    if problem:
        return GateCheck(name="ruff", passed=False, fixes=fixes,
                         details=f"ruff safe fixes: {problem}")
    findings = remaining
    fixed_note = (f"{sum(int(f.rsplit('x', 1)[1]) for f in fixes)} safe fix(es) applied "
                  f"first ({'; '.join(fixes)})" if fixes else "")
    if not findings:
        return GateCheck(name="ruff", passed=True, fixes=fixes,
                         details="ruff clean" + (f" after {fixed_note}" if fixed_note else ""))
    lines = []
    for item in findings:
        where = Path(str(item.get("filename") or ""))
        with contextlib.suppress(ValueError):
            where = where.resolve().relative_to(feed_dir.resolve())
        location = item.get("location") or {}
        lines.append(f"{where.as_posix()}:{location.get('row', '?')}:"
                     f"{location.get('column', '?')}: {item.get('code') or 'syntax'} "
                     f"{item.get('message', '')}".rstrip())
    return GateCheck(name="ruff", passed=False, fixes=fixes,
                     details=f"{len(findings)} finding(s)"
                     + (f" remain after {fixed_note}" if fixed_note else "")
                     + "\n" + "\n".join(lines))


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
