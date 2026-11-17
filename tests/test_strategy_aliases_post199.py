"""post199: ONE load-strategy alias table (config ``extractor.frd.load_strategy_synonyms``)
for every document and answer. Before, the STTM / answers reader had its own table in
code (``resolve/gapfill.py``) and the FRD reader knew only one config spelling, so the
same word read differently by document ("Merge" = Upsert in an STTM, nothing in an FRD).
"Incremental" is dropped (Soham, 2026-11-17): FRDs write it as the load TYPE in front of
both "Truncate & load" and "Upsert" - it is no strategy."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.extract import frd_docx
from codegen.resolve import gapfill

REPO = Path(__file__).resolve().parents[1]
MARKERS = {"stage": ["STG"], "standard": ["STD"]}


@pytest.fixture(scope="module")
def words():
    return load_config(REPO / "config" / "config.yaml").extractor.frd.load_strategy_synonyms


@pytest.mark.parametrize("text, expected", [
    ("Merge", "Upsert"), ("merge on keys", "Upsert"), ("Full Load", "Truncate and Load"),
    ("OVERWRITE", "Truncate and Load"), ("Truncate & Load", "Truncate and Load"),
    ("truncate reload", "Truncate and Load"), ("Insert", "Append"), ("Upsert", "Upsert"),
    ("Truncate & Load (delete existing rows first)", "Truncate and Load"),
])
def test_a_word_reads_the_same_in_every_document(words, text, expected):
    assert gapfill.canonical_strategy(text, words) == expected          # STTM / answers
    assert frd_docx.canonical_strategy(text, words) == (expected, "")    # FRD


def test_incremental_is_no_strategy_anywhere(words):
    assert gapfill.canonical_strategy("Incremental", words) is None
    assert frd_docx.canonical_strategy("Incremental", words) == (None, "")
    assert gapfill.parse_load_strategy_text("STG: Incremental", MARKERS, words) == {}


def test_no_alias_table_hides_in_code():
    """Without the config table only the three canonical literals read."""
    assert not hasattr(gapfill, "_STRATEGY_ALIASES")
    assert gapfill.canonical_strategy("Merge", {}) is None
    assert gapfill.canonical_strategy("append", {}) == "Append"


def test_a_block_line_may_start_with_any_alias(words):
    assert frd_docx.canonical_strategy("Merge on keys A, B", words, leading=True) == (
        "Upsert", "A, B")
    assert frd_docx.canonical_strategy("Truncate & load daily", words, leading=True) == (
        "Truncate and Load", "daily")
