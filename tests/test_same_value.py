"""post113 (codeflow audit #8, high + medium): ``gapfill.same_value`` / ``distinct``
judge whether two documents' statements agree. A punctuation-only value ('|',
',') normalizes to '' — so two identical delimiters disagreed (a needless
blocking choice in the layout dialog, no frd_unstated fill on the CLI) and the
layout cross-check, which tested ``'' in value``, let ANY two punctuation
delimiters "agree" (a ',' vs '|' conflict went unseen). With
``extractor.delimiter_words`` they are compared as the delimiter character each
side states."""

from __future__ import annotations

import pytest

from codegen.config import load_config
from codegen.resolve.gapfill import Statement, distinct, same_value
from test_derivations import REPO


@pytest.fixture(scope="module")
def words():
    return load_config(REPO / "config" / "config.yaml").extractor.delimiter_words


@pytest.mark.parametrize(("a", "b", "agree"), [
    ("|", "|", True),                         # identical delimiters disagreed before
    (",", ",", True),
    ("|", ",", False),
    ("~", "^", False),
    ("Pipe", "|", True),                      # the word and the character
    ("Pipe delimited (|)", "|", True),
    (",", "Comma", True),
    ("|", "Daily", False),
    ("Daily", "daily", True),                 # text values: unchanged behaviour
    ("CSV", "csv file", True),
])
def test_statements_agree_on_the_delimiter_character(words, a, b, agree):
    assert same_value(a, b, words) is agree
    assert same_value(b, a, words) is agree


def test_without_delimiter_words_punctuation_compares_as_written():
    assert same_value("|", "|") and not same_value("|", ",") and not same_value("", "")


def test_identical_delimiters_are_one_statement(words):
    sttm, vdd = Statement("|", "STTM", "meta row"), Statement("|", "VDD", "FILES row 2")
    assert distinct([sttm, vdd], words) == [sttm]
    assert len(distinct([sttm, Statement(",", "VDD", "FILES row 2")], words)) == 2
