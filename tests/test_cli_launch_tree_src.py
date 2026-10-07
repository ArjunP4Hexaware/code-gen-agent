"""The CLI runs the checkout's own ``codegen`` and says so (2026-10-07).

* ``acfc_run.py``'s launcher (``launch_codegen``) puts ``<repo>/src`` ahead of
  everything on PYTHONPATH, so a decoy ``codegen`` that raises on import, put
  ahead on PYTHONPATH, loses; the repo root comes from the launcher's own
  location (``repo_root_from``), never the cwd.
* Every command's first line is ``codegen <version> from <file> · overlays:
  <list>``; ``codegen doctor`` adds python, sys.path[0:3], iig_review.
* The report's Model usage section and run_meta.json carry the same line.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
LAUNCHER = REPO / "acfc_run.py"


def _launcher_functions() -> dict:
    """repo_root_from / codegen_env / launch_codegen as acfc_run.py defines
    them (the notebook's top level runs dbutils, so it is not importable)."""
    tree = ast.parse(LAUNCHER.read_text(encoding="utf-8"))
    wanted = {"repo_root_from", "codegen_env", "launch_codegen"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    assert {n.name for n in nodes} == wanted
    namespace: dict = {"os": os, "subprocess": subprocess, "sys": sys, "Path": Path}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(LAUNCHER), "exec"),  # noqa: S102
         namespace)
    return namespace


def _decoy(tmp: Path) -> Path:
    decoy = tmp / "decoy"
    (decoy / "codegen").mkdir(parents=True)
    (decoy / "codegen" / "__init__.py").write_text(
        'raise ImportError("decoy codegen imported — a stale install won")\n', encoding="utf-8")
    return decoy


def _first_line_path(stdout: str) -> Path:
    first = stdout.splitlines()[0]
    assert first.startswith("codegen "), first
    return Path(first.split(" from ", 1)[1].split(" · ", 1)[0])


def test_launcher_runs_the_tree_src_despite_a_decoy(tmp_path):
    fns = _launcher_functions()
    root = fns["repo_root_from"](LAUNCHER.parent)
    assert root == REPO
    decoy = _decoy(tmp_path)
    base = {**os.environ, "PYTHONPATH": str(decoy), "PYTHONUTF8": "1",
            "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    env = fns["codegen_env"](root, base)
    assert env["PYTHONPATH"].split(os.pathsep) == [str(SRC), str(decoy)]  # existing kept
    done = fns["launch_codegen"](root, "doctor", env=base)
    assert done.returncode == 0, done.stderr[-2000:]
    assert _first_line_path(done.stdout).resolve().is_relative_to(SRC.resolve())
    assert "iig_review supported: True" in done.stdout
    assert f"python: {sys.executable}" in done.stdout


def test_without_the_launcher_the_decoy_wins(tmp_path):
    """The control: the same command with the decoy ahead and no src/ prepended."""
    env = {**os.environ, "PYTHONPATH": str(_decoy(tmp_path)), "PYTHONUTF8": "1"}
    done = subprocess.run([sys.executable, "-m", "codegen.cli", "doctor"], cwd=REPO, env=env,
                          text=True, capture_output=True, check=False)
    assert done.returncode != 0 and "decoy codegen imported" in done.stderr


def test_every_command_prints_the_source_line_first(tmp_path):
    env = {**os.environ, "PYTHONUTF8": "1"}
    env.pop("CODEGEN_SKIP_ENV_OVERLAY", None)
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "generate", "--frd-contract",
         str(tmp_path / "missing.json"), "--sttm-contract", str(tmp_path / "missing.json"),
         "--dry-run"], cwd=REPO, env=env, text=True, capture_output=True, encoding="utf-8",
        check=False)
    first = done.stdout.splitlines()[0]
    assert first.startswith("codegen ") and " from " in first
    overlay = str(Path("config") / "overlays" / "acfc_env.yaml")
    assert first.endswith(f"· overlays: {overlay}")


def test_report_and_source_line_name_the_code(tmp_path):
    from codegen.build_info import PRODUCED_BY_PREFIX, codegen_version, source_line
    from codegen.reasoning.usage import StageUsage, report_lines

    line = source_line(["a.yaml", "b.yaml"])
    assert line == (f"codegen {codegen_version()} from {(SRC / 'codegen' / '__init__.py')} · "
                    "overlays: a.yaml -> b.yaml")
    lines = report_lines([StageUsage(stage="layer2", provider="mock", requests=0,
                                     mock_reason="test")])
    (produced,) = [entry for entry in lines if entry.startswith(PRODUCED_BY_PREFIX)]
    assert str(SRC / "codegen") in produced
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{codegen_version()}"' in pyproject
