"""post204: ONE delimiter reader (``resolve.gapfill.delimiter_reading``) and ONE
format / extension table (``extractor.format_delimiters``, config) - the third generic
win of READER_GENERALIZATION §5 (one value normaliser per field type).

Before: ``resolver.delimiter_char`` (stated cells), ``gapfill._delimiter_of`` (both
sides of an agreement check) and three code tables disagreed - '|' and 'Pipe (|)' did
not agree, "Comma or pipe" read as a comma (a silent pick), the sentence comma of
"Fixed width, 120 bytes" read as a delimiter, and a "TSV" format implied tab on one path
only. Synthetic values only."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from codegen.resolve.gapfill import delimiter_reading, same_value
from codegen.resolve.resolver import delimiter_char

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("text", "char"), [
    ("|", "|"), (",", ","), ("\t", "\t"), ("\\t", "\t"), (" | ", "|"),
    ("Pipe", "|"), ("pipe delimited", "|"), ("Pipe (|)", "|"), ("Pipe delimited (|)", "|"),
    ("pipe|", "|"), ("Comma (,)", ","), ("comma separated", ","), ("csv, comma delimited", ","),
    ("tab-delimited", "\t"), ("~ (tilde)", "~"), ("Text file (pipe)", "|"), ("Colon", ":"),
    # none, or two - never a pick
    ("Fixed width, 120 bytes", None), ("File Data Ingestion", None), ("Delimited", None),
    ("Comma or pipe", None), ("Pipe:", "|"), ("", None), (None, None),
])
def test_one_reading_for_every_stated_delimiter(config, text, char):
    words = config.extractor.delimiter_words
    assert delimiter_reading(text, words) == char
    assert delimiter_char(text, words) == char            # the resolver's name, same reader


@pytest.mark.parametrize(("a", "b"), [("|", "Pipe (|)"), ("\\t", "Tab"), ("pipe|", "|"),
                                      ("~", "~ (tilde)")])
def test_two_documents_naming_one_character_agree(config, a, b):
    """Failed before post204: the agreement check had its own narrower reading."""
    assert same_value(a, b, config.extractor.delimiter_words)


def test_two_different_characters_never_agree(config):
    assert not same_value("|", "Comma", config.extractor.delimiter_words)


def test_the_format_table_is_config_and_tsv_implies_tab(config):
    formats = config.extractor.format_delimiters
    assert formats == {"csv": ",", "psv": "|", "tsv": "\t", "pipe": "|"}


def test_no_format_or_extension_delimiter_table_lives_in_code():
    """The post199 rule: an alias table lives in config, never in code."""
    pattern = re.compile(r"""\{\s*["'](?:csv|psv|tsv)["']\s*:\s*["'][,|]""")
    hits = [str(p.relative_to(REPO)) for p in (REPO / "src" / "codegen").rglob("*.py")
            if pattern.search(p.read_text(encoding="utf-8"))
            and p.name != "config.py"]                 # the model's default mirrors config
    assert hits == []
