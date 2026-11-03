"""post74 (D1 post73 pair_08): "STTM required element missing (role
target_type) at STTM sheet 1 row 96 col 17". A required element missing on ONE
row never fails the feed:

- the row names no target column either -> not a mapping row: skipped,
  counted in the feed's skipped_rows flag;
- otherwise -> a blocking QUESTION for that cell, keyed
  ``feeds[i].columns[j].target_type`` and cited by coordinates; the rest of the
  feed extracts (the column waits for the answer).

At bcb6105 (before this change) the same fixture stopped extract-sttm with
``... STTM required element missing (role target_type) at STTM sheet 2 row 14
col 15 [ExtractionError]``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from codegen.extract import extract_contract
from codegen.run_errors import first_error_line
from post73_pairs import FIRST_DATA_ROW, STAGE_TYPE_COL, frd, mapping_workbook

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-01-01"
KEY = "feeds[0].columns[2].target_type"


def _pair08(tmp_path):
    return mapping_workbook(tmp_path / "p8.xlsx", {2: {"stage_type": None}})


def test_one_row_without_a_type_is_a_cell_question_the_feed_proceeds(config, tmp_path):
    contract = extract_contract(_pair08(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    (feed,) = contract.feeds
    assert feed.field_count == 5
    assert "SERVICE_DATE" not in [f.stage_column for f in feed.fields]
    (question,) = contract.needs_answers
    assert question.key == KEY
    assert (f"the stage data type cell at STTM sheet 2 row {FIRST_DATA_ROW + 2} "
            f"col {STAGE_TYPE_COL} is empty") in question.reason


def test_the_answer_fills_the_cell(config, tmp_path):
    gaps = {KEY: {"value": "Date"}}
    contract = extract_contract(_pair08(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE, gaps=gaps)
    (feed,) = contract.feeds
    assert not contract.needs_answers
    by_column = {f.stage_column: f for f in feed.fields}
    assert by_column["SERVICE_DATE"].stage_datatype == "Date"
    assert any(f.startswith(f"answered_cell:{KEY} — STTM sheet 2 row {FIRST_DATA_ROW + 2}")
               for f in feed.extraction_flags)


def test_a_row_without_a_target_column_is_not_a_mapping_row(config, tmp_path):
    workbook = mapping_workbook(tmp_path / "p8.xlsx", {3: {"stage_column": None},
                                                       4: {"stage_column": None,
                                                           "stage_type": None}})
    contract = extract_contract(workbook, frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    (feed,) = contract.feeds
    assert feed.field_count == 4 and not contract.needs_answers
    (flag,) = [f for f in feed.extraction_flags if f.startswith("skipped_rows:")]
    assert "2 row(s) left out" in flag
    assert (f"2 name no target column (not a mapping row): FEED_5_MAPPING!O{FIRST_DATA_ROW + 3}, "
            f"FEED_5_MAPPING!O{FIRST_DATA_ROW + 4}") in flag


def _cli(tmp_path, *extra):
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    return subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook",
         str(_pair08(tmp_path)), "--frd-contract", str(frd(tmp_path / "frd.json")),
         "--out", str(tmp_path / "sttm.json"), "--config", str(REPO / "config" / "config.yaml"),
         *extra],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)


def test_pair08_shape_through_the_cli_writes_the_contract_and_asks(tmp_path):
    done = _cli(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None
    assert any(line.startswith(f"QUESTION       {KEY} — ") for line in done.stdout.splitlines())
    assert (tmp_path / "sttm.json").is_file()
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"gaps": {KEY: {"value": "Date"}}}), encoding="utf-8")
    again = _cli(tmp_path, "--answers", str(answers))
    assert again.returncode == 0, again.stdout + again.stderr
    assert "QUESTION" not in again.stdout
