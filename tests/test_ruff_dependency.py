"""The gate's ruff check never goes missing silently (2026-10-07).

* ruff is a BASE dependency, so every install the Apps runtime / harness
  makes (`.`, `.[ui]`, `.[databricks]` — requirements.txt installs
  `.[ui,databricks]`) carries it.
* When the module is absent anyway, the gate raises a ``ruff_unavailable``
  FLAG naming the reason — PASS_WITH_FLAGS, never FAIL — and the console and
  the report say so.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from codegen.gate import preflight
from codegen.gate.preflight import RUFF_UNAVAILABLE, _ruff_check
from codegen.gate.verdict import compute_verdict

REPO = Path(__file__).resolve().parents[1]


def test_ruff_is_a_base_dependency_every_install_gets():
    tomllib = pytest.importorskip("tomllib")
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    names = [re.split(r"[<>=!~\[ ;]", dep, maxsplit=1)[0].lower()
             for dep in project["dependencies"]]
    assert "ruff" in names
    requirements = (REPO / "requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"^\.\[[^\]]*\]", requirements, re.M), "requirements.txt installs the package"


def _module_missing(monkeypatch):
    real = preflight.importlib.util.find_spec
    monkeypatch.setattr(preflight.importlib.util, "find_spec",
                        lambda name, *a: None if name == "ruff" else real(name, *a))


def test_a_missing_ruff_module_is_a_ruff_unavailable_flag(tmp_path, monkeypatch):
    (tmp_path / "bad.py").write_text("import os\n", encoding="utf-8")
    _module_missing(monkeypatch)
    check = _ruff_check(tmp_path)
    assert check.passed and check.not_run and check.flag == RUFF_UNAVAILABLE
    assert "the ruff module is not installed for" in check.details
    gate = compute_verdict("feed", [], [], [check], tests_skipped=False)
    assert gate.verdict == "PASS_WITH_FLAGS"
    (flag,) = gate.flags
    assert flag.startswith("ruff_unavailable — ruff unavailable: the ruff module is not "
                           "installed for ")
    assert flag.endswith("the generated code was NOT checked — PASS cannot be claimed")


def test_end_to_end_the_verdict_says_ruff_was_unavailable(tmp_path, monkeypatch, capsys):
    from test_m91_pattern_chain_and_exit_codes import _generate

    _module_missing(monkeypatch)
    code, out = _generate(tmp_path, monkeypatch, capsys)
    assert code == 0 and out.startswith("PASS_WITH_FLAGS ") and "ruff=not-run" in out
    assert "CHECK NOT RUN   ruff — ruff unavailable: the ruff module is not installed" in out
    report = next((tmp_path / "out" / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "| ruff | NOT RUN |" in report
    assert "ruff_unavailable — ruff unavailable: the ruff module is not installed" in report
