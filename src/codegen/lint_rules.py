"""THE one definition of the lint rules generated code is judged by (M12 item 2).

Two places need the same rule set and used to state it twice: the
``ruff.toml`` emitted next to a generated pipeline (``templates/
ruff.toml.j2``), and the gate's own ``ruff check`` (``gate.preflight``).
The gate never passed a config, so ruff DISCOVERED one — and what it found
depended on where the run happened to live:

* inside this checkout, ``out/<feed>/ruff.toml`` (or the repo's
  ``pyproject.toml``) — the intended rules, everything clean;
* inside ACFC, where an M8.1 outputs role puts the tree in a temp
  directory with no config above it, ruff's DEFAULTS — which flagged the
  runner notebooks for ``RUF100`` (a ``noqa`` naming a rule those defaults
  do not enable) and ``EXE002`` (the file is executable but has no
  shebang). The v0.7.2 all-pairs run read that as ``ruff=FAIL``.

So the gate pins the rules explicitly (``--isolated`` plus these values as
``--config`` overrides) and its verdict no longer depends on the tree's
address. ``EXE002`` is ignored outright: a file's mode is the filesystem's
business — a storage backend, an unzip or a volume mount decides it —
never a statement about the code.
"""

from __future__ import annotations

import json

LINE_LENGTH = 100
TARGET_VERSION = "py311"
# The assembled notebook duplicates already-linted module code cell by cell.
EXTEND_EXCLUDE = ["*.ipynb"]
SELECT = ["E", "F", "I", "UP", "B", "SIM"]
# Local modules of the generated package; conftest is imported by tests.
KNOWN_FIRST_PARTY = ["pipeline", "conftest"]
# Rules about the FILE, not the code: never a finding about what we generated.
GATE_IGNORE = ["EXE002"]


def toml_list(values: list[str]) -> str:
    """A TOML/JSON string array, spelled as the emitted ruff.toml spells it."""
    return json.dumps(values)


def template_context() -> dict:
    """What ``templates/ruff.toml.j2`` renders from."""
    return {
        "lint_line_length": LINE_LENGTH,
        "lint_target_version": TARGET_VERSION,
        "lint_extend_exclude": toml_list(EXTEND_EXCLUDE),
        "lint_select": toml_list(SELECT),
        "lint_known_first_party": toml_list(KNOWN_FIRST_PARTY),
    }


def ruff_config_args() -> list[str]:
    """The gate's pinned rule set as ruff command-line arguments: no config
    discovery, the emitted ruff.toml's rules, EXE002 ignored."""
    return [
        "--isolated",
        "--config", f"line-length = {LINE_LENGTH}",
        "--config", f'target-version = "{TARGET_VERSION}"',
        "--config", f"extend-exclude = {toml_list(EXTEND_EXCLUDE)}",
        "--config", f"lint.select = {toml_list(SELECT)}",
        "--config", f"lint.ignore = {toml_list(GATE_IGNORE)}",
        "--config", f"lint.isort.known-first-party = {toml_list(KNOWN_FIRST_PARTY)}",
    ]


__all__ = [
    "EXTEND_EXCLUDE",
    "GATE_IGNORE",
    "KNOWN_FIRST_PARTY",
    "LINE_LENGTH",
    "SELECT",
    "TARGET_VERSION",
    "ruff_config_args",
    "template_context",
    "toml_list",
]
