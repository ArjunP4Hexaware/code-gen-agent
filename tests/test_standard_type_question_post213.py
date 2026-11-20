"""post213 (a tester's live run CRASHED, 2026-11-19): one STTM row's standard data type
cell read a note ("Derived") instead of a type. The DDL's guard (post158, pentest CS-1)
rightly stops any non-type before the DDL - but the run then CRASHED. Now the STTM read
asks for that ONE cell (a blocking QUESTION, the row left out until answered, as a blank
stage type is - post74); a type answer is applied and flagged; an answer that is no type
keeps the question open (post158's guard is never reached by a non-type).

Synthetic Family E workbooks only (tests/post73_pairs.py).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from codegen.config import load_config
from codegen.extract import extract_contract
from post73_pairs import frd, mapping_workbook

DATE = "2026-01-01"
KEY = "feeds[0].columns[2].standard_type"
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _sheet(tmp_path):
    return mapping_workbook(tmp_path / "p.xlsx", {2: {"standard_type": "Derived"}})


def test_a_note_in_a_standard_type_cell_is_one_question_not_a_crash(config, tmp_path):
    contract = extract_contract(_sheet(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    (question,) = contract.needs_answers
    assert question.key == KEY
    assert "reads 'Derived', which is no data type" in question.reason
    stage = [f.stage_column for f in contract.feeds[0].fields]
    assert len(stage) == len(set(stage)) and len(contract.feeds[0].fields) >= 1
    assert all(f.standard_datatype != "Derived" for f in contract.feeds[0].fields)


def test_a_type_answer_is_applied_and_flagged(config, tmp_path):
    contract = extract_contract(_sheet(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE, gaps={KEY: {"value": "String"}})
    assert contract.needs_answers == []
    assert "String" in [f.standard_datatype for f in contract.feeds[0].fields]
    assert any(f.startswith(f"answered_cell:{KEY}")
               for f in contract.feeds[0].extraction_flags)


def test_an_answer_that_is_no_type_keeps_the_question(config, tmp_path):
    contract = extract_contract(_sheet(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE, gaps={KEY: {"value": "Derived too"}})
    (question,) = contract.needs_answers
    assert question.key == KEY and "is no data type either" in question.reason


def test_real_type_spellings_are_no_question(config, tmp_path):
    workbook = mapping_workbook(tmp_path / "p.xlsx", {
        0: {"standard_type": "Decimal(12,2)"}, 1: {"standard_type": "Date"},
        2: {"standard_type": "timestamp(YYYY-MM-DD HH:MM:SS)"}, 3: {"standard_type": "BIG INT"}})
    contract = extract_contract(workbook, frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    assert contract.needs_answers == []


def test_the_app_asks_it_in_plain_words(config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import pending_question

    reason = ("the standard data type cell at STTM sheet 1 row 14 col 27 reads 'Derived', "
              "which is no data type; answer the standard column's data type")
    q = pending_question(SimpleNamespace(reason=reason, candidates=[]), KEY, config)
    assert q["title"] == "What is the standard data type of this STTM row's column?"
    assert q["hint"].startswith("The standard data type cell at STTM sheet 1 row 14")
    assert "No document states this value" not in q["hint"]
    assert (q["kind"], q["example"], q["leave_blank"]) == ("text", "String", None)
