"""Which code produced this: the version + location of the imported ``codegen``
and the config overlays in effect (2026-10-07: a stale wheel in the Apps venv
shadowed the deployed tree and nothing said so).

``source_line()`` is printed first by every CLI command, by ``codegen doctor``,
written into a run's ``run_meta.json`` and into the generation report's
"Model usage" section. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DISTRIBUTION = "codegen-data-engineer-agent"
PRODUCED_BY_PREFIX = "- Produced by: "


def package_file() -> str:
    import codegen

    return str(codegen.__file__)


def tree_root() -> Path | None:
    """The checkout this ``codegen`` was imported from (``<root>/src/codegen``
    with a pyproject.toml at ``<root>``), else None (an installed wheel)."""
    package = Path(package_file()).resolve().parent
    root = package.parent.parent
    if package.parent.name == "src" and (root / "pyproject.toml").is_file():
        return root
    return None


def codegen_version() -> str:
    """The tree's pyproject version when imported from a checkout (an
    editable install's metadata can lag the tree), else the installed
    distribution's."""
    root = tree_root()
    if root is not None:
        match = re.search(r'^version\s*=\s*"([^"]+)"',
                          (root / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    try:
        return version(DISTRIBUTION)
    except PackageNotFoundError:
        return "unknown"


def source_line(overlays: list[str] | None = None) -> str:
    """``codegen <version> from <codegen.__file__> · overlays: <list>`` —
    ``overlays`` defaults to the ones the last ``load_config`` applied."""
    if overlays is None:
        from codegen.config import last_applied_overlays

        overlays = last_applied_overlays()
    listed = " -> ".join(overlays) if overlays else "(none)"
    return f"codegen {codegen_version()} from {package_file()} · overlays: {listed}"


def doctor_lines(overlays: list[str]) -> list[str]:
    from codegen.config import Config

    return [
        source_line(overlays),
        f"python: {sys.executable}",
        f"sys.path[0:3]: {sys.path[0:3]}",
        f"iig_review supported: {'iig_review' in Config.model_fields}",
    ]


__all__ = ["PRODUCED_BY_PREFIX", "codegen_version", "doctor_lines", "package_file",
           "source_line", "tree_root"]
