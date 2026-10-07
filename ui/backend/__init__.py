"""Make the demo backend run on the DEPLOYED tree's ``codegen``, never a stale
wheel (2026-10-07: the Apps venv kept an old pip-installed ``codegen`` that
predates ``iig_review`` while ``config/config.yaml`` came from the new tree →
"unknown top-level config section(s) ['iig_review']").

This package ``__init__`` runs before any ``ui.backend.*`` module imports
``codegen`` (``python -m ui.backend.main``, ``uvicorn ui.backend.main:app``,
``import ui.backend.main``). It loads the tree's ``src/codegen/_srcpath.py``
BY FILE PATH (never via ``import codegen``, which a stale install could
answer) and calls its ``ensure_src_first()``: ``<repo root>/src`` first on
``sys.path``, a ``codegen`` imported from elsewhere dropped. Child processes
get the same rule explicitly — every launch site passes
``env=codegen._srcpath.child_env()``. Stdlib only.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


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


def _load_srcpath(src: Path) -> ModuleType | None:
    path = src / "codegen" / "_srcpath.py"
    spec = importlib.util.spec_from_file_location("codegen_srcpath_bootstrap", path)
    if not path.is_file() or spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPO_ROOT = _repo_root()
TREE_SRC = REPO_ROOT / "src" if REPO_ROOT is not None else None
srcpath = _load_srcpath(TREE_SRC) if TREE_SRC is not None else None
if srcpath is not None:
    srcpath.ensure_src_first()
