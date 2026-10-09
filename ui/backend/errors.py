"""Readable errors for the App (2026-10-09): an exception nobody caught must
reach the person as a card they can act on, never an HTML 500 page or a white
screen.

``error_detail(exc)`` is the one shape — the API's unhandled-exception handler
(``ui/backend/main.py``) answers it as JSON, a run that crashed in its thread
carries it on the status (``error_detail``), and the frontend's error card
renders it:

- ``type`` / ``message`` — the exception, the message on its own;
- ``where`` — the FIRST line to read of the traceback: its innermost frame,
  ``file:line in function`` (repo-relative when the file is in the checkout);
- ``cause`` — the same for the exception it was raised from, when there is one;
- ``health`` / ``health_line`` — the facts ``GET /api/health`` reports about
  this process (version, codegen source, config overlays, startup error), so a
  card read on another machine still says WHICH code failed.

Never an environment value: a message that happens to carry the value of a
secret-named environment variable has it masked. Paths and file names are fine.
"""

from __future__ import annotations

import os
import re
import traceback
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Long enough for any message the agent raises (the held-back lists), short
# enough that a runaway repr cannot flood the card.
MESSAGE_LIMIT = 4000
_SECRET_NAME = re.compile(r"TOKEN|SECRET|PASSW|API_KEY|ACCESS_KEY|CREDENTIAL|CLIENT_KEY",
                          re.IGNORECASE)
_MIN_SECRET_LENGTH = 6

_provider: Callable[[], dict] | None = None


def set_health_provider(provider: Callable[[], dict] | None) -> None:
    """The App module registers the facts it serves at ``GET /api/health``
    (it owns the startup error); without one, ``health_facts`` computes them
    from ``codegen.build_info``."""
    global _provider
    _provider = provider


def health_facts() -> dict:
    """``{version, codegen_source, config_overlays, startup_error}`` — the
    static part of ``GET /api/health``. Never the storage probe: an error card
    must not wait on the workspace."""
    if _provider is not None:
        try:
            return dict(_provider())
        except Exception as exc:  # noqa: BLE001 — the card must still render
            fallback = _computed_facts()
            fallback["startup_error"] = (fallback["startup_error"]
                                         or f"health facts unavailable: {type(exc).__name__}")
            return fallback
    return _computed_facts()


def _computed_facts() -> dict:
    from codegen.build_info import codegen_version, source_line
    from codegen.config import last_applied_overlays

    return {"version": codegen_version(), "codegen_source": source_line(),
            "config_overlays": [str(p) for p in last_applied_overlays()],
            "startup_error": None}


def health_line(facts: dict) -> str:
    """One line: ``version … · <codegen source> · overlays: a -> b · startup error: none``."""
    overlays = [str(o) for o in facts.get("config_overlays") or []]
    return " · ".join([
        f"version {facts.get('version') or 'unknown'}",
        str(facts.get("codegen_source") or "codegen source unknown"),
        "overlays: " + (" -> ".join(overlays) if overlays else "(none)"),
        f"startup error: {facts.get('startup_error') or 'none'}",
    ])


def display_path(filename: str) -> str:
    """Repo-relative (forward slashes) inside the checkout, else as given."""
    path = Path(filename)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def where(exc: BaseException) -> str:
    """The innermost frame of ``exc``'s traceback: ``file:line in function``."""
    frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
    if not frames:
        return "(no traceback)"
    frame = frames[-1]
    return f"{display_path(frame.filename)}:{frame.lineno} in {frame.name}"


def redact(text: str) -> str:
    """Mask the value of any secret-named environment variable in ``text``."""
    for name, value in os.environ.items():
        if value and len(value) >= _MIN_SECRET_LENGTH and _SECRET_NAME.search(name) \
                and value in text:
            text = text.replace(value, f"<{name} masked>")
    return text


def _message(exc: BaseException) -> str:
    message = redact(str(exc)) or "(no message)"
    if len(message) > MESSAGE_LIMIT:
        message = message[:MESSAGE_LIMIT] + f"… ({len(message) - MESSAGE_LIMIT} more characters)"
    return message


def error_detail(exc: BaseException) -> dict:
    """The one error shape the App answers (see the module docstring)."""
    facts = health_facts()
    detail = {"type": type(exc).__name__, "message": _message(exc), "where": where(exc),
              "cause": None, "health": facts, "health_line": health_line(facts)}
    cause = exc.__cause__ or (None if exc.__suppress_context__ else exc.__context__)
    if cause is not None:
        detail["cause"] = f"{type(cause).__name__}: {_message(cause)} ({where(cause)})"
    return detail


__all__ = ["display_path", "error_detail", "health_facts", "health_line", "redact",
           "set_health_provider", "where"]
