"""post221 (P4, 2026-11-24): a staging STTM had 34 standard type cells reading ONE note,
and post213 asked the same question 34 times. Cells of the STTM that read the same text
(case / spaces ignored) now share ONE question - the first cell's; its answer is used for
each of them (flagged per cell); a cell's own valid answer still wins; a different text is
its own question. Synthetic Family E workbooks only (tests/post73_pairs.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.extract import extract_contract
from post73_pairs import frd, mapping_workbook

DATE = "2026-01-01"
REPO = Path(__file__).resolve().parents[1]
FIRST = "feeds[0].columns[1].standard_type"


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _contract(config, tmp_path, cells, gaps=None):
    workbook = mapping_workbook(tmp_path / "p.xlsx",
                                {i: {"standard_type": t} for i, t in cells.items()})
    return extract_contract(workbook, frd(tmp_path / "frd.json"), config,
                            generated_date=DATE, gaps=gaps or {})


def test_cells_reading_the_same_note_share_one_question(config, tmp_path):
    contract = _contract(config, tmp_path, {1: "Derived", 2: "derived ", 3: "DERIVED"})
    (question,) = contract.needs_answers
    assert question.key == FIRST
    assert "2 other standard type cell(s) of this STTM read the same text" in question.reason
    assert all(f.standard_datatype.lower().strip() != "derived"
               for f in contract.feeds[0].fields)


def test_the_one_answer_is_used_for_every_cell_and_flagged(config, tmp_path):
    contract = _contract(config, tmp_path, {1: "Derived", 2: "Derived", 3: "Derived"},
                         gaps={FIRST: {"value": "String"}})
    assert contract.needs_answers == []
    flags = contract.feeds[0].extraction_flags
    assert any(f.startswith(f"answered_cell:{FIRST}") and "the person answered" in f
               for f in flags)
    shared = [f for f in flags if f"the answer to `{FIRST}` (the same text) is used" in f]
    assert len(shared) == 2


def test_a_cells_own_answer_wins(config, tmp_path):
    own = "feeds[0].columns[2].standard_type"
    contract = _contract(config, tmp_path, {1: "Derived", 2: "Derived"},
                         gaps={FIRST: {"value": "String"}, own: {"value": "Date"}})
    assert contract.needs_answers == []
    flags = contract.feeds[0].extraction_flags
    assert any(f.startswith(f"answered_cell:{own}") and "the person answered 'Date'" in f
               for f in flags)


def test_a_different_text_is_its_own_question(config, tmp_path):
    contract = _contract(config, tmp_path, {1: "Derived", 2: "See note", 3: "Derived"})
    keys = [q.key for q in contract.needs_answers]
    assert keys == [FIRST, "feeds[0].columns[2].standard_type"]
    assert "other standard type cell" not in contract.needs_answers[1].reason


def test_an_answer_that_is_no_type_keeps_the_one_question(config, tmp_path):
    contract = _contract(config, tmp_path, {1: "Derived", 2: "Derived"},
                         gaps={FIRST: {"value": "Derived too"}})
    (question,) = contract.needs_answers
    assert question.key == FIRST and "is no data type either" in question.reason
