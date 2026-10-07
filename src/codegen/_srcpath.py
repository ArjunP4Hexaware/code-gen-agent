"""The src-first rule, in one place (2026-10-07: a stale ``codegen`` wheel in
the Apps venv shadowed the deployed tree).

Stdlib only, and safe to load BY FILE PATH (``load_by_path``) before any
``import codegen`` — that is how ``ui/backend/__init__.py`` and
``acfc_run.py`` use it, so loading it never imports a possibly stale package.

* ``ensure_src_first()`` — ``<repo>/src`` first on ``sys.path``; an already
  imported ``codegen`` that does not live there is dropped from
  ``sys.modules`` (an editable install pointing at src/ is left alone).
* ``child_env(extra=None)`` — ``os.environ`` (or ``base``) with ``<src>``
  prepended to PYTHONPATH, existing entries kept: pass it as ``env=`` to every
  child process that may import ``codegen`` (the document parser, the gate's
  ruff / pytest, the CLI launcher).

``<src>`` is the directory holding THIS file's package: ``<repo>/src`` in a
checkout (then ``REPO_ROOT`` is the dir with pyproject.toml), the
site-packages dir for an installed wheel (harmless — that is where it came
from).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

SRC = Path(__file__).resolve().parents[1]
REPO_ROOT: Path | None = SRC.parent if (SRC.parent / "pyproject.toml").is_file() else None


def _inside(module_file: str | None, root: Path) -> bool:
    if not module_file:
        return False
    try:
        Path(module_file).resolve().relative_to(root)
    except ValueError:
        return False
    return True


def ensure_src_first() -> Path:
    """Put ``SRC`` first on sys.path and drop a ``codegen`` imported from
    anywhere else; return ``SRC``."""
    loaded = sys.modules.get("codegen")
    if loaded is not None and not _inside(getattr(loaded, "__file__", None), SRC):
        for name in [m for m in sys.modules if m == "codegen" or m.startswith("codegen.")]:
            del sys.modules[name]
    src = str(SRC)
    sys.path[:] = [src, *[p for p in sys.path if p != src]]
    return SRC


def child_env(extra: dict | None = None, base: dict | None = None) -> dict:
    """``base`` (default ``os.environ``) + ``extra``, with ``SRC`` prepended
    to PYTHONPATH (existing entries kept, ``SRC`` once)."""
    env = dict(os.environ if base is None else base)
    env.update(extra or {})
    src = str(SRC)
    rest = [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p and p != src]
    env["PYTHONPATH"] = os.pathsep.join([src, *rest])
    return env


def load_by_path(src_dir: Path) -> ModuleType:
    """This module loaded from ``<src_dir>/codegen/_srcpath.py`` without
    importing the ``codegen`` package (so a stale install cannot answer)."""
    path = Path(src_dir) / "codegen" / "_srcpath.py"
    spec = importlib.util.spec_from_file_location("codegen_srcpath_bootstrap", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


__all__ = ["REPO_ROOT", "SRC", "child_env", "ensure_src_first", "load_by_path"]
