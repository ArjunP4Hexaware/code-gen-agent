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
    assert lines["TGT_DATA_TYPE"].startswith("MATCH")           # String / string mix
    assert "case-insensitive" in lines["TGT_DATA_TYPE"]
    assert lines["LOB"].startswith("ALIAS")                      # the fixture's own LOB
    assert lines["CLAIM_TYPE_ID"].startswith("MATCH")           # blank vs NULL
    assert lines["CREATED_BY"].startswith("DIFF") and "withheld" in lines["CREATED_BY"]
    assert lines["FILE_METADATA"].startswith("MATCH")           # not in the template, NULL
    assert "person-id-123" not in out and "RFCSYN" not in out
    assert out.splitlines()[-1] == ("filled 5/8, matched 3, alias 3, open 1 (BSA 0, "
                                    "Engineer 1, Engineer-confirm 0, CI/CD 0), diff 1")


def test_lob_and_primary_key_are_diffs_on_the_real_documents():
    real = {"TGT_TABLE_NAME": "t", "LOB": "MIDS", "TGT_PRIMARY_KEY": "NULL",
            "TGT_DATA_TYPE": "String,string"}
    generated = {"TGT_TABLE_NAME": "t", "LOB": "OTHER", "TGT_PRIMARY_KEY": "zip_code",
                 "TGT_DATA_TYPE": "STRING,String"}
    lines, counts = iig_scorecard.score(generated, real, {}, [], fixture=False)
    assert lines[1].startswith("DIFF  LOB")
    assert lines[2].startswith("DIFF  TGT_PRIMARY_KEY")         # a framework question
    assert lines[3].startswith("MATCH TGT_DATA_TYPE")
    assert counts["diff"] == 2
