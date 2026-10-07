"""scripts/iig_scorecard.py — MATCH / ALIAS / OPEN / DIFF per column, the
summary line, CREATED_BY / UPDATED_BY never printed."""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import iig_scorecard  # noqa: E402

SHEET = "ADLS_DELTA_INGESTION_DETAILS"
HEADERS = ["GROUP_ID", "TGT_TABLE_NAME", "SRC_ADLS_PATH", "TGT_DATA_TYPE", "LOB",
           "CLAIM_TYPE_ID", "CREATED_BY", "FILE_METADATA"]


def _book(path: Path, sheet: str, headers: list[str], rows: list[list]) -> Path:
    workbook = Workbook()
    ws = workbook.active
    ws.title = sheet
    ws.append(headers)
    for row in rows:
        ws.append(row)
    workbook.save(path)
    return path


def test_scorecard_statuses_and_summary(tmp_path, capsys):
    real = _book(tmp_path / "real.xlsx", "Sheet1", [None, *HEADERS], [
        [None, 999001, "sd_x", "/inbound/sdoh/vendor/", "String,Timestamp", "MIDS", "NULL",
         "person-id-123", "NULL"]])
    generated = _book(tmp_path / "x_IIG.xlsx", SHEET, HEADERS[:-1], [
        ["", "cv_x", "/inbound/sdh/vendor/", "String,TIMESTAMP", "OHDS", "", "RFCSYN"]])
    _book(tmp_path / "x_IIG_REVIEW.xlsx", "REVIEW_SUMMARY",
          ["Sheet", "Column", "Reason", "Owner", "Cells"],
          [[SHEET, "GROUP_ID", "always_blank", "Engineer", 1]])
    assert iig_scorecard.main(["--generated", str(generated), "--real", str(real),
                               "--real-sheet", "Sheet1", "--real-table", "sd_x"]) == 0
    out = capsys.readouterr().out
    lines = {line.split()[1]: line for line in out.splitlines()[1:-1]}
    assert lines["GROUP_ID"].startswith("OPEN") and "owner: Engineer" in lines["GROUP_ID"]
    assert lines["TGT_TABLE_NAME"].startswith("ALIAS")
    assert lines["SRC_ADLS_PATH"].startswith("ALIAS")
    assert lines["TGT_DATA_TYPE"].startswith("DIFF") and "(case only)" in lines["TGT_DATA_TYPE"]
    assert lines["LOB"].startswith("DIFF")
    assert lines["CLAIM_TYPE_ID"].startswith("MATCH")           # blank vs NULL
    assert lines["CREATED_BY"].startswith("DIFF") and "withheld" in lines["CREATED_BY"]
    assert lines["FILE_METADATA"].startswith("MATCH")           # not in the template, NULL
    assert "person-id-123" not in out and "RFCSYN" not in out
    assert out.splitlines()[-1] == ("filled 5/8, matched 2, alias 2, open 1 (BSA 0, "
                                    "Engineer 1, Engineer-confirm 0, CI/CD 0), diff 3")
