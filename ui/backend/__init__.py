"""Make the demo backend run on the DEPLOYED tree's ``codegen``, never a stale
wheel (2026-10-07: the Apps venv kept an old pip-installed ``codegen`` that
predates ``iig_review`` while ``config/config.yaml`` came from the new tree →
"unknown top-level config section(s) ['iig_review']").

This package ``__init__`` runs before any ``ui.backend.*`` module imports
``codegen`` (``python -m ui.backend.main``, ``uvicorn ui.backend.main:app``,
``import ui.backend.main``): it puts ``<repo root>/src`` first on ``sys.path``
and drops an already-imported ``codegen`` that lives elsewhere. An editable
install already pointing at ``<repo root>/src`` (the test suite) is left as
it is — its modules are never re-imported. Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def _from_tree(module_file: str | None, src: Path) -> bool:
    if not module_file:
        return False
    try:
        Path(module_file).resolve().relative_to(src.resolve())
    except ValueError:
        return False
    return True


REPO_ROOT = _repo_root()
TREE_SRC = REPO_ROOT / "src" if REPO_ROOT is not None else None

if TREE_SRC is not None and (TREE_SRC / "codegen").is_dir():
    loaded = sys.modules.get("codegen")
    if loaded is not None and not _from_tree(getattr(loaded, "__file__", None), TREE_SRC):
        for name in [m for m in sys.modules if m == "codegen" or m.startswith("codegen.")]:
            del sys.modules[name]
    src = str(TREE_SRC)
    sys.path[:] = [p for p in sys.path if p != src]
    sys.path.insert(0, src)
