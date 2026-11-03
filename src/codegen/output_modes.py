"""THE output vocabulary: a run produces Notebook and / or Framework artefacts.

A selection is a list of parts drawn from ``OUTPUT_OPTIONS``. The config
(``output.mode``), the CLI (``--output-mode``, repeatable), the API
(``/api/demo/output-parts``, ``/api/demo/output-mode``) and a past run's
``run_meta.json`` all normalize through ``output_parts``.

The retired spellings — ``both`` (the old name for the two together) and the
RFC-package modes ``rfc`` / ``all`` — are NEVER an error when a saved state or
a config still carries them: they map to Notebook + Framework artefacts and
the mapping is announced ONCE per (source, value) (logged, and kept in
``notices()`` for the UI). A value that was never valid still raises.
"""

from __future__ import annotations

import logging

OUTPUT_OPTIONS: tuple[str, ...] = ("notebook", "framework")
RETIRED: tuple[str, ...] = ("both", "rfc", "all")
_RETIRED_TO = ["notebook", "framework"]

_log = logging.getLogger(__name__)
_announced: set[tuple[str, str]] = set()
_notices: list[str] = []


def _announce(source: str, value: str) -> None:
    if (source, value) in _announced:
        return
    _announced.add((source, value))
    what = ("the old name for Notebook + Framework artefacts" if value == "both"
            else "the RFC package option, which is retired")
    message = (f"{source}: output {value!r} is {what} — generating Notebook + "
               "Framework artefacts instead")
    _notices.append(message)
    _log.warning(message)


def output_parts(value, *, source: str = "output selection") -> list[str]:
    """Normalize a stored / received selection (a string or a list of
    strings) to parts in ``OUTPUT_OPTIONS`` order. ``[]`` stays ``[]`` (the
    caller refuses a run on it)."""
    items = [value] if isinstance(value, str) else list(value or [])
    chosen: set[str] = set()
    for item in items:
        name = str(item).strip().lower()
        if name in OUTPUT_OPTIONS:
            chosen.add(name)
        elif name in RETIRED:
            _announce(source, name)
            chosen.update(_RETIRED_TO)
        else:
            raise ValueError(f"unknown output {item!r}; expected one of "
                             f"{list(OUTPUT_OPTIONS)}")
    return [p for p in OUTPUT_OPTIONS if p in chosen]


def notices() -> list[str]:
    """The retired-value mappings announced so far in this process."""
    return list(_notices)


__all__ = ["OUTPUT_OPTIONS", "RETIRED", "notices", "output_parts"]
