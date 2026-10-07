"""The demo App imports the DEPLOYED tree's ``codegen`` (``<repo>/src``), never
a stale installed one (2026-10-07: an old wheel in the Apps venv predated
``iig_review`` → "unknown top-level config section(s) ['iig_review']").

A decoy ``codegen`` package that raises on import is put AHEAD on PYTHONPATH;
``import ui.backend.main`` must still resolve ``codegen`` from ``<repo>/src``,
and ``GET /api/health`` must name that path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"

PROBE = ("import json, ui.backend.main as m; import codegen; print(codegen.__file__); "
         "print(json.dumps(m.health()))")


def test_app_imports_codegen_from_the_tree_src_despite_a_decoy(tmp_path):
    decoy = tmp_path / "decoy"
    (decoy / "codegen").mkdir(parents=True)
    (decoy / "codegen" / "__init__.py").write_text(
        'raise ImportError("decoy codegen imported — a stale install won")\n', encoding="utf-8")
    env = {**os.environ,
           "PYTHONPATH": os.pathsep.join([str(decoy), os.environ.get("PYTHONPATH", "")]).rstrip(
               os.pathsep),
           "CODEGEN_SKIP_ENV_OVERLAY": "1", "PYTHONUTF8": "1"}
    done = subprocess.run([sys.executable, "-c", PROBE], cwd=REPO, env=env, text=True,
                          capture_output=True, encoding="utf-8", timeout=300, check=False)
    assert done.returncode == 0, done.stderr[-2000:]
    lines = done.stdout.strip().splitlines()
    codegen_file = Path(lines[-2])
    assert codegen_file.resolve().is_relative_to(SRC.resolve())
    health = json.loads(lines[-1])
    assert Path(health["codegen_file"]).resolve().is_relative_to(SRC.resolve())
    assert str(SRC / "codegen") in health["codegen_source"]
    assert "iig_review supported: True" in health["codegen_source"]
    assert health["codegen_source"] in done.stdout             # the startup line printed


def test_the_shim_without_a_decoy_keeps_an_editable_install(tmp_path):
    """In-process (the suite's editable install already points at src/):
    nothing is re-imported, src/ is on sys.path (first when the shim ran; later
    tests may insert their own entries ahead of it)."""
    import ui.backend as backend

    import codegen

    assert Path(codegen.__file__).resolve().is_relative_to(SRC.resolve())
    assert backend.TREE_SRC == SRC
    assert str(SRC) in sys.path
