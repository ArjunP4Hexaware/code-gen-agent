"""post223: a stated delimiter that the file format or a file pattern's extension
contradicts (pair_02: a .psv file, the STTM states "Comma") is used as stated - and
flagged for review, never changed."""

from types import SimpleNamespace

import pytest

from codegen.config import load_config
from codegen.resolve.resolver import _resolve_delimiter

REPO_CONFIG = "config/config.yaml"


@pytest.fixture(scope="module")
def config():
    return load_config(REPO_CONFIG)


def _inputs(frd_delim=None, sttm_delim=None, patterns=(), fmt=None, sttm_pattern=None):
    frd = SimpleNamespace(delimiter=frd_delim, file_format=fmt,
                          file_name_patterns=list(patterns))
    sttm = SimpleNamespace(source_file=SimpleNamespace(delimiter=sttm_delim,
                                                       name_pattern=sttm_pattern))
    return frd, sttm


def _codes(flags):
    return [f.split(" — ")[0] for f in flags]


def test_a_stated_comma_on_a_psv_file_is_used_and_flagged(config):
    errors, flags = [], []
    got = _resolve_delimiter(*_inputs(sttm_delim="Comma", patterns=("x_YYYYMMDD.psv",)),
                             errors, config, flags)
    assert got == "," and errors == []
    (flag,) = flags
    assert flag.startswith("delimiter_implied_differs:','")
    assert "'x_YYYYMMDD.psv' implies '|'" in flag


def test_a_format_that_implies_another_delimiter_is_flagged(config):
    errors, flags = [], []
    assert _resolve_delimiter(*_inputs(frd_delim="|", fmt="CSV"), errors, config, flags) == "|"
    assert _codes(flags) == ["delimiter_implied_differs:'|'"]
    assert "the FRD file format 'CSV' implies ','" in flags[0]


@pytest.mark.parametrize("kw", [
    {"sttm_delim": "Pipe", "patterns": ("a.psv",)},          # they agree
    {"frd_delim": ",", "patterns": ("a.csv",), "fmt": "csv"},
    {"frd_delim": "|", "patterns": ("a.txt", "b.dat")},       # no implied delimiter
    {"frd_delim": "|", "fmt": "Delimited"},
])
def test_no_flag_when_nothing_contradicts_the_stated_delimiter(config, kw):
    errors, flags = [], []
    _resolve_delimiter(*_inputs(**kw), errors, config, flags)
    assert not [f for f in flags if f.startswith("delimiter_implied_differs:")]


def test_every_contradicting_pattern_is_named_once(config):
    errors, flags = [], []
    _resolve_delimiter(*_inputs(frd_delim=",", patterns=("a.psv", "a.psv", "b.csv"),
                                sttm_pattern="a.psv"), errors, config, flags)
    assert _codes(flags) == ["delimiter_implied_differs:','"]
