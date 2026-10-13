"""Column identifiers of generated DDL (D1 App demo, 2026-10-13).

Seven rounds scored the IIG only, and a framework-mode DDL carried a column named
"LOB(Hardcod to MIDS)". Every column identifier of a CREATE TABLE body must be a
plain identifier; scripts/run_round.py stops (exit 1) on one that is not.
"""

from __future__ import annotations

import re
from pathlib import Path

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CREATE_RE = re.compile(r"^\s*CREATE\b.*\bTABLE\b", re.IGNORECASE)
_NOT_A_COLUMN = ("constraint", "primary", "foreign", "key", "unique", "check", "index")


def ddl_column_identifiers(text: str) -> list[str]:
    """The column identifier of every line of every CREATE TABLE body (one
    column per line, as both DDL templates write them): a backticked name
    as written between the backticks, else the line's first token."""
    names: list[str] = []
    state = "outside"                      # outside -> header -> body -> outside
    for raw in text.splitlines():
        line = raw.strip()
        if state == "outside":
            if _CREATE_RE.match(raw):
                state = "body" if line.endswith("(") else "header"
            continue
        if state == "header":
            if line.startswith("("):
                state = "body"
                line = line[1:].strip()
                if not line:
                    continue
            else:
                continue
        if line.startswith(")"):
            state = "outside"
            continue
        if not line or line.startswith("--"):
            continue
        name = (line[1:].split("`", 1)[0] if line.startswith("`")
                else line.split()[0].rstrip(","))
        if name.lower() in _NOT_A_COLUMN:
            continue
        names.append(name)
    return names


def ddl_identifier_violations(paths: list[Path]) -> list[tuple[str, str]]:
    """``(file name, identifier)`` for every column identifier that is not
    ``^[A-Za-z_][A-Za-z0-9_]*$``."""
    out: list[tuple[str, str]] = []
    for path in paths:
        for name in ddl_column_identifiers(path.read_text(encoding="utf-8", errors="replace")):
            if not IDENTIFIER_RE.match(name):
                out.append((path.name, name))
    return out


def generated_ddl_files(root: Path) -> list[Path]:
    """Every DDL file a generate run writes under ``root``: the framework's
    ``*_DDL.txt`` / ``*_table_creation.txt`` and the notebook's ``ddl/*.sql``."""
    found = [*root.rglob("framework/*_DDL.txt"), *root.rglob("framework/*_table_creation.txt"),
             *root.rglob("ddl/*.sql")]
    return sorted(set(found))
