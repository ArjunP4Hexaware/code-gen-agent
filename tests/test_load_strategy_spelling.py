"""post94 (pair_03): an FRD load strategy written "Truncate & Load (Delete existing
records and perform a full data reload)" is the canonical "Truncate and Load" -
a configured spelling (extractor.frd.load_strategy_synonyms), a trailing
parenthetical explanation ignored. Anything else stays an ambiguity, as before."""

from __future__ import annotations

import pytest

from codegen.config import load_config
from codegen.extract.frd_docx import _strategy

SYNONYMS = load_config("config/config.yaml").extractor.frd.load_strategy_synonyms


@pytest.mark.parametrize("cell", [
    "Truncate & Load",
    "Truncate & Load (Delete existing records and perform a full data reload)",
    "Truncate and Load (full reload)",
    "truncate and load",
])
def test_the_frds_spellings_read_as_truncate_and_load(cell):
    ambiguities: list[str] = []
    assert _strategy(cell, "feeds[0].stage_target.load_strategy", ambiguities,
                     SYNONYMS) == "Truncate and Load"
    assert ambiguities == []


def test_an_unknown_strategy_is_still_left_null_and_noted():
    ambiguities: list[str] = []
    assert _strategy("Insert New Records based on last run time", "p", ambiguities,
                     SYNONYMS) is None
    assert len(ambiguities) == 1 and "left null" in ambiguities[0]


def test_without_the_synonym_table_the_ampersand_is_not_guessed():
    assert _strategy("Truncate & Load", "p", [], {}) is None
