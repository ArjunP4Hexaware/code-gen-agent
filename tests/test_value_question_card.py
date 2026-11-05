"""post169: a typed value question says what it needs, where the agent looked and
what a blank answer does (2026-11-04: a data engineer on the staging App could not
tell what "File format feeds[0].file_format — No document states this value ...
Several tables: separate them with ';'" wanted).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from codegen.config import load_config
from codegen.layout.hints import value_question, where_looked

REPO = Path(__file__).resolve().parents[1]
REFUSED = {"structured": {"feeds[0].file_format": {
    "kind": "multiline", "table": 6, "row": 4, "col": 2, "label": "Object/data Format"}},
    "field_provenance": {"feeds[0].file_format": {"table": 6, "row": 4, "label":
                                                  "Object/data Format"}},
    "feeds": [{"file_format": None}]}


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def test_a_refused_frd_row_is_named_with_its_coordinates():
    assert where_looked("feeds[0].file_format", REFUSED) == (
        "The FRD's 'Object/data Format' row (table 6, row 4) states it over several lines "
        "the agent can't read as one value, and no other document states it.")
    # a derived feed shares the FRD's one row
    assert "'Object/data Format' row" in where_looked("feeds[3].file_format", REFUSED)


@pytest.mark.parametrize("contract, says", [
    ({"field_provenance": {"feeds[0].frequency": {"table": 1, "row": 6, "label": "Frequency"}},
      "feeds": [{"frequency": None}]}, "'Frequency' row (table 1, row 6) is blank"),
    ({"field_provenance": {"feeds[0].frequency": {"table": 1, "row": 6, "label": "Frequency"}},
      "feeds": [{"frequency": "every so often"}]}, "states a value the agent can't use"),
    ({"feeds": [{}]}, "No FRD row is labelled for it, and no other document states it."),
    (None, "No document the agent read states it."),
])
def test_where_looked_says_what_the_contract_shows(contract, says):
    assert says in where_looked("feeds[0].frequency", contract)


def test_each_value_field_has_a_plain_question(config):
    assert value_question("feeds[2].file_format", config) == (
        "What format are the source files in?", "csv, txt, pipe-delimited text")
    question, example = value_question("feeds[0].archive_retention", config)
    assert question == "What is the archive schedule for this feed?" and example is None


def _card(tmp_path, key: str, contract: dict | None, config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import pending_question

    path = None
    if contract is not None:
        path = tmp_path / "frd.contract.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
    return pending_question(SimpleNamespace(reason="contract validation: value, unstated",
                                            candidates=[]), key, config, frd_contract=path)


def test_the_file_format_card(tmp_path, config):
    card = _card(tmp_path, "feeds[0].file_format", REFUSED, config)
    assert card["title"] == "What format are the source files in?"
    assert card["example"] == "csv, txt, pipe-delimited text"
    assert card["hint"].startswith("The FRD's 'Object/data Format' row (table 6, row 4)")
    # post170: a blankable value offers the deliberate blank instead of holding the feed
    assert "Leave blank and continue" in card["hint"]
    assert card["leave_blank"] == config.answers.leave_blank
    assert "Several tables" not in card["hint"]
    assert card["reason"] == "contract validation: value, unstated"     # kept, folded in the UI


def test_a_table_question_says_how_to_list_several(tmp_path, config):
    card = _card(tmp_path, "feeds[0].stage_target.tables", {"feeds": [{}]}, config)
    assert "separate with ';'" in card["example"]
    # a table can never be left blank (the DDL needs it): no blank choice, held back
    assert card["leave_blank"] is None
    assert "Left blank, the feed stays held back" in card["hint"]


def test_an_sttm_cell_question_never_points_at_the_frd(tmp_path, config):
    card = _card(tmp_path, "feeds[0].columns[3].target_type", REFUSED, config)
    assert card["hint"].startswith("No document states this value.")
    assert "FRD" not in card["hint"] and card["example"] is None
