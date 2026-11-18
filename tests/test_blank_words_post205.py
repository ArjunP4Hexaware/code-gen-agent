"""post205: ONE "states nothing" word list (``extractor.blank_words``) for the exact-match
readers - the FRD's placeholder cells (``extractor.frd.blank_values``), the STTM meta
values (``discovery.meta_blank_values``) and the Segment cells
(``discovery.unsegmented_markers``). The three lists had drifted: "null" was a blank in a
Segment cell only, "TBD" nowhere in a Segment cell, "Not applicable" in none of them.
The base list is merged into each at load (each keeps its own extra words). The FRD
DQ section's ``dq_no_check_words`` is NOT merged: it matches by "starts with", where a
"-" would swallow a bulleted rule. Synthetic values only."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.layout.discover import is_blank_placeholder

REPO = Path(__file__).resolve().parents[1]
BASE = ["none", "n/a", "na", "-", "tbd", "null", "not applicable"]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _has_all(words, base=BASE):
    have = {str(w).strip().lower() for w in words}
    return [b for b in base if b not in have]


def test_the_base_list_is_config(config):
    assert list(config.extractor.blank_words) == BASE


def test_every_exact_match_reader_holds_the_base_words(config):
    ex = config.extractor
    assert _has_all(ex.frd.blank_values) == []
    assert _has_all(ex.discovery.meta_blank_values) == []
    assert _has_all(ex.discovery.unsegmented_markers) == []


def test_the_dq_starts_with_list_is_not_merged(config):
    tpl = config.metadata.templates["iig_v2"]
    assert "-" not in {w.strip().lower() for w in tpl.dq_no_check_words}


@pytest.mark.parametrize("value", ["Null", "Not applicable", "TBD", "n/a", "-"])
def test_an_sttm_meta_value_stating_nothing_is_blank(config, value):
    assert is_blank_placeholder(value, list(config.extractor.discovery.meta_blank_values))


def test_a_delimiter_character_is_still_a_value(config):
    for char in (",", "|", "~"):
        assert not is_blank_placeholder(char, list(config.extractor.discovery.meta_blank_values))


def test_an_frd_placeholder_cell_reads_blank(config):
    from codegen.extract.frd_docx import DocxContent, _value
    from codegen.layout.frd_profile import FrdFieldSource

    for text in ("Not applicable", "Null", "TBD"):
        content = DocxContent(tables=[[["Frequency", text]]], paragraphs=[], nested={})
        source = FrdFieldSource(table=0, row=0, col=0, value_col=1, label="Frequency",
                                section=None, feed_index=0)
        assert _value(content, source, config.extractor.frd) == "", text
