"""D1 post51 (2026-10-15): the four static-denylist hits of the 12-pair report
were document text inside ``first_error_line``. A parser error on a synthetic
workbook whose cell holds SENTINEL_TERM: the coordinates tier (what the harness
pushes) must not carry it, the full tier (codegen-outputs/ inside ACFC) must."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook

from codegen.run_errors import MARKER, first_error_line, first_error_line_full

REPO = Path(__file__).resolve().parents[1]
FRD = REPO / "fixtures" / "acfc_shapes" / "pair_4" / "frd_nb_cob_report.contract.json"
SENTINEL = "SENTINEL_TERM"


def _sentinel_workbook(path: Path) -> Path:
    """A MAPPING- workbook whose audit row's stage column (a CELL) is the
    sentinel, typed outside the audit vocabulary (pair_06's shape)."""
    wb = Workbook()
    details = wb.active
    details.title = "FILE_DETAILS"
    details.append(["Vendor", "FileName", "File Description", "Location", "Frequency"])
    details.append(["Acme", "acme_YYYYMMDD.csv", None, None, "Monthly"])
    history = wb.create_sheet("VERSION_HISTORY")
    history.append(["Date", "Version", "Author(s)", "Description of Version/Change"])
    history.append(["2026-01-01", "1.0", "T. Author", "Initial"])
    ws = wb.create_sheet("MAPPING-ACME")
    ws.append(["Source File Layout"] + [None] * 6 + ["Stage Layer"] + [None] * 3
              + ["Standard Layer"] + [None] * 3)
    ws.append(["Database column Name", "NULL CHECK", "Description", "Sample Value", "DataType",
               "PHI Field", "Mandatory Field"] + ["Schema", "TableName", "ColumnName",
                                                  "DataType"] * 2)
    ws.append(["col_a", "Not NULL", "d", "1", "String", "No", "Yes", "stg_acme", "acme_table",
               "col_a", "String", "acme", "acme_table", "col_a", "String"])
    ws.append(["NA", None, None, None, None, None, None, "stg_acme", "acme_table", SENTINEL,
               "tinyint", "acme", "acme_table", SENTINEL, "tinyint"])
    wb.save(path)
    return path


def test_a_parser_error_cites_coordinates_never_the_cell(tmp_path):
    workbook = _sentinel_workbook(tmp_path / "acme.xlsx")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(FRD), "--out", str(tmp_path / "sttm.json"),
         "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode == 1, done.stdout + done.stderr
    assert SENTINEL in done.stdout                      # the CLI's own FAIL line quotes it

    full = first_error_line_full(done.returncode, done.stderr, done.stdout)
    assert SENTINEL in full and full.startswith("FAIL")
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert SENTINEL not in line
    # the audit row: sheet 3 (MAPPING-ACME), row 4, the stage ColumnName column
    assert line == (f"{'FAIL':<15} extract-sttm — STTM audit column invalid at STTM "
                    "sheet 3 row 4 col 11 [WorkbookParseError]")
    # no marker line ever carries document text either
    assert all(SENTINEL not in ln for ln in done.stderr.splitlines() if ln.startswith(MARKER))


def test_an_unreadable_workbook_names_no_sheet(tmp_path):
    wb = Workbook()
    wb.active.title = SENTINEL
    wb.active.append(["a", "b"])
    wb.save(tmp_path / "x.xlsx")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "layout", "--workbook", str(tmp_path / "x.xlsx"),
         "--config", str(REPO / "config" / "config.yaml"), "--provider", "mock"],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode == 1
    assert SENTINEL in first_error_line_full(done.returncode, done.stderr, done.stdout)
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert SENTINEL not in line and line.startswith(f"{'FAIL':<15} layout — ")
