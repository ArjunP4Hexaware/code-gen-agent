"""A codegen subprocess's error, read from its exit code and output (2026-10-15).

D1 post50: a harness took the first stderr line of a ``codegen`` run as "the
run's error", and a Pydantic deprecation warning printed before the real
Traceback became the reported error (and a clean run with only warnings on
stderr read as failed). The rule here, shared by every reader in this repo
(``scripts/run_round.py``, ``acfc_run.py``) and importable by an outside
harness:

1. the exit code decides: 0 = no error, whatever stderr holds;
2. Python warning lines are never the error — ``<file>:<line>: <Name>Warning:
   ...`` (the ``warnings`` module's format, with the indented source line it
   prints under it), ``<Name>Warning: ...``, ``warnings.warn(...)`` and any line
   naming a ``PydanticDeprecatedSince*`` category;
3. of the remaining lines (stderr first, then stdout), the first that opens an
   error — ``Traceback``, ``FAIL`` / ``ERROR`` (the CLI's answer-line labels),
   ``<Name>Error:`` / ``<Name>Exception:`` — else the first non-empty one.

:func:`silence_pydantic_deprecations` stops the noise at its source (a filter
scoped to Pydantic's own deprecation category, nothing wider); the CLI calls
it at entry.
"""

from __future__ import annotations

import re
import warnings

# path:lineno: SomethingWarning: message   (warnings.formatwarning)
_WARN_LOCATED = re.compile(r"^.+:\d+: (?:[A-Za-z_][\w.]*)?Warning: ")
# any located category line (PydanticDeprecatedSince20 does not end in Warning)
_LOCATED = re.compile(r"^.+:\d+: [A-Za-z_][\w.]*: ")
# SomethingWarning: message                  (a bare category line)
_WARN_BARE = re.compile(r"^\s*(?:[A-Za-z_][\w.]*)?Warning: ")
_WARN_CALL = re.compile(r"^\s*warnings\.warn(?:_explicit)?\(")
_PYDANTIC = re.compile(r"PydanticDeprecat(?:edSince\d+|ionWarning)")
_ERROR_OPEN = re.compile(r"^(?:Traceback \(most recent call last\)|FAIL\b|ERROR\b|"
                         r"(?:[A-Za-z_][\w.]*)?(?:Error|Exception)\b:?)")


def is_warning_line(line: str) -> bool:
    """A line the ``warnings`` machinery printed (never an error)."""
    return bool(_WARN_LOCATED.match(line) or _WARN_BARE.match(line)
                or _WARN_CALL.match(line) or _PYDANTIC.search(line))


def without_warnings(text: str) -> list[str]:
    """``text``'s lines minus every warning line and the indented source line
    the ``warnings`` module prints under a located warning."""
    kept: list[str] = []
    skip_source = False
    for line in (text or "").splitlines():
        if skip_source and line[:1].isspace():
            skip_source = False
            continue
        skip_source = False
        if is_warning_line(line):
            skip_source = bool(_LOCATED.match(line))
            continue
        kept.append(line)
    return kept


def first_error_line(returncode: int, stderr: str | bytes | None = "",
                     stdout: str | bytes | None = "") -> str | None:
    """The error line of one finished ``codegen`` run.

    STABLE API (2026-10-15) — imported by the ACFC harness; the signature and
    the three outcomes below do not change without a version note:

    - ``returncode == 0`` -> ``None``: no error, whatever stderr holds
      (warnings, the ``config overlays`` line, anything);
    - otherwise the first line, stderr before stdout, that opens an error
      (``Traceback (most recent call last):``, a ``FAIL`` / ``ERROR`` answer
      line, ``<Name>Error:`` / ``<Name>Exception:``), Python warning lines and
      the source line printed under them skipped (:func:`is_warning_line`);
    - no such line -> the first non-empty non-warning line; none -> ``""``.

    ``stderr`` / ``stdout`` may be ``str``, ``bytes`` (decoded UTF-8, errors
    replaced) or ``None`` — ``subprocess.CompletedProcess`` fields as they come.
    """
    if not returncode:
        return None
    stderr, stdout = _text(stderr), _text(stdout)
    lines = [ln for ln in (*without_warnings(stderr), *without_warnings(stdout)) if ln.strip()]
    return next((ln for ln in lines if _ERROR_OPEN.match(ln.strip())),
                lines[0] if lines else "")


def _text(stream: str | bytes | None) -> str:
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode("utf-8", errors="replace")
    return stream


def silence_pydantic_deprecations() -> None:
    """Ignore Pydantic's deprecation category (and only it) in this process.
    No-op when pydantic does not define it."""
    try:
        from pydantic.warnings import PydanticDeprecationWarning
    except ImportError:         # pragma: no cover - pydantic < 2.0 / absent
        return
    warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)


__all__ = ["first_error_line", "is_warning_line", "silence_pydantic_deprecations",
           "without_warnings"]
