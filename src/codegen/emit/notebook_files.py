"""post69: one notebook as cells -> the two files a workspace imports, and the
checks they must pass.

``<slug>.ipynb`` (nbformat 4.5) and ``<slug>.py``, a Databricks notebook source
(``# Databricks notebook source`` first, cells divided by ``# COMMAND
----------``, markdown cells as ``# MAGIC %md`` lines) — the two carry the
same cells, so either imports as the same notebook.

Checks (each a GateCheck): ``nbformat.validate`` on the .ipynb (not run, and
flagged, where nbformat is not installed — it is a dev dependency), every code
cell compiles (``compile``), ``ruff check`` on the .py (the generated
pipeline's rules; E501 ignored — a literal from the IIG cannot be wrapped),
and the scrub: no ADLS host literal and no e-mail address other than the
configured notification list in either file.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DATABRICKS_HEADER = "# Databricks notebook source"
COMMAND = "# COMMAND ----------"
MAGIC = "# MAGIC"
RUFF_SELECT = "E,F,I,UP,B,SIM"
RUFF_IGNORE = "E501"
_ADLS_HOST = re.compile(r"[\w-]+\.dfs\.core\.windows\.net")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


@dataclass(frozen=True)
class Cell:
    kind: str          # "markdown" | "code"
    cell_id: str
    text: str


def md(cell_id: str, text: str) -> Cell:
    return Cell("markdown", cell_id, text.rstrip("\n") + "\n")


def code(cell_id: str, text: str) -> Cell:
    return Cell("code", cell_id, text.rstrip("\n") + "\n")


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def ipynb_text(cells: list[Cell]) -> str:
    """The notebook as nbformat 4.5 JSON (byte-stable: sorted cell keys as v1)."""
    out = []
    for cell in cells:
        if cell.kind == "markdown":
            out.append({"cell_type": "markdown", "id": cell.cell_id, "metadata": {},
                        "source": _lines(cell.text)})
        else:
            out.append({"cell_type": "code", "id": cell.cell_id, "metadata": {},
                        "execution_count": None, "outputs": [],
                        "source": _lines(cell.text)})
    notebook = {
        "cells": out,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook, ensure_ascii=False, indent=1) + "\n"


def databricks_source(cells: list[Cell]) -> str:
    """The notebook as a Databricks ``.py`` source."""
    blocks = []
    for cell in cells:
        if cell.kind == "markdown":
            lines = ["%md", *cell.text.rstrip("\n").splitlines()]
            blocks.append("\n".join(f"{MAGIC} {line}".rstrip() for line in lines))
        else:
            blocks.append(cell.text.rstrip("\n"))
    return f"{DATABRICKS_HEADER}\n" + f"\n\n{COMMAND}\n\n".join(blocks) + "\n"


# ------------------------------------------------------------------- checks


def check_nbformat(text: str):
    from codegen.gate.preflight import GateCheck

    try:
        import nbformat
    except ImportError:
        return GateCheck(name="notebook_nbformat", passed=True, not_run=True,
                         details="nbformat is not installed here (a dev dependency): the "
                                 ".ipynb was not schema-validated")
    try:
        nbformat.validate(nbformat.reads(text, as_version=4))
    except Exception as exc:  # noqa: BLE001 — any schema error is the finding
        return GateCheck(name="notebook_nbformat", passed=False,
                         details=f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
    return GateCheck(name="notebook_nbformat", passed=True, details="nbformat 4.5 valid")


def check_cells_compile(cells: list[Cell]):
    from codegen.gate.preflight import GateCheck

    bad = []
    for cell in cells:
        if cell.kind != "code":
            continue
        try:
            compile(cell.text, f"<cell {cell.cell_id}>", "exec")
        except SyntaxError as exc:
            bad.append(f"{cell.cell_id}: line {exc.lineno}: {exc.msg}")
    return GateCheck(name="notebook_cells_compile", passed=not bad,
                     details="; ".join(bad) if bad else
                     f"{sum(c.kind == 'code' for c in cells)} code cell(s) compile",
                     violations={"syntax": len(bad)} if bad else {})


def check_ruff(source: str):
    from codegen._srcpath import child_env
    from codegen.gate.preflight import RUFF_UNAVAILABLE, GateCheck

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "notebook.py"
        path.write_text(source, encoding="utf-8", newline="\n")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--no-cache", "--isolated",
                 "--line-length", "100", "--target-version", "py311",
                 "--select", RUFF_SELECT, "--ignore", RUFF_IGNORE,
                 "--output-format", "json", str(path)],
                capture_output=True, text=True, check=False, env=child_env())
        except OSError as exc:
            return GateCheck(name="notebook_ruff", passed=True, not_run=True,
                             flag=RUFF_UNAVAILABLE, details=f"ruff could not start: {exc}")
    try:
        findings = json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError:
        findings = None
    if not isinstance(findings, list):
        return GateCheck(name="notebook_ruff", passed=True, not_run=True,
                         flag=RUFF_UNAVAILABLE,
                         details=f"ruff gave no JSON (exit {result.returncode})")
    counts: dict[str, int] = {}
    for item in findings:
        counts[str(item.get("code") or "syntax")] = counts.get(
            str(item.get("code") or "syntax"), 0) + 1
    return GateCheck(name="notebook_ruff", passed=not findings,
                     details=(", ".join(f"{k} x{n}" for k, n in sorted(counts.items()))
                              if findings else "ruff clean"),
                     violations=counts)


def check_scrub(texts: list[str], allowed_emails: list[str]):
    from codegen.gate.preflight import GateCheck

    allowed = {e.strip().lower() for e in allowed_emails}
    hosts = sum(len(_ADLS_HOST.findall(t)) for t in texts)
    emails = sum(1 for t in texts for m in _EMAIL.findall(t) if m.lower() not in allowed)
    found = {k: n for k, n in (("adls_host", hosts), ("email_address", emails)) if n}
    return GateCheck(name="notebook_scrub", passed=not found,
                     details=(", ".join(f"{k} x{n}" for k, n in found.items()) if found
                              else "no ADLS host literal, no document address"),
                     violations=found)


__all__ = ["Cell", "code", "databricks_source", "ipynb_text", "md", "check_cells_compile",
           "check_nbformat", "check_ruff", "check_scrub"]
