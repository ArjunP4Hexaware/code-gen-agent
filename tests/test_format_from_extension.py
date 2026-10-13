"""Round 7 (D1 App, VDD attached, 2026-10-13): an FRD 'Object/data Format' cell
that names no file format ("File Data Ingestion" — an ingestion type) is never a
file_format candidate; the file pattern's extension decides, with a NOTE, and a
VDD format that agrees confirms it. A conflict is still a QUESTION."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen import cli
from codegen.contracts.frd import FrdContract
from codegen.layout.resolve import fill_frd_gaps
from codegen.resolve.gapfill import format_delimiter, is_format_text

REPO = Path(__file__).resolve().parents[1]
CV_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
VDD_CELL = "VDD FILES!C2"


def _contract(fmt: str | None, patterns: list[str]) -> FrdContract:
    contract = FrdContract.model_validate(json.loads(CV_FRD.read_text(encoding="utf-8")))
    feed = contract.feeds[0].model_copy(update={
        "file_format": fmt, "delimiter": None, "file_name_patterns": patterns})
    return contract.model_copy(update={"feeds": [feed]})


def _fill(config, fmt, patterns, vdd_format=None):
    vdd = {"file_format": [(vdd_format, VDD_CELL)]} if vdd_format else {}
    return fill_frd_gaps(_contract(fmt, patterns), None, {}, vdd, {}, config, REPO)


def _format_questions(result):
    return [q for q in result.questions if q.key == "feeds[0].file_format"]


def test_an_ingestion_type_is_no_format_the_extension_decides_and_the_vdd_confirms(config):
    result = _fill(config, "File Data Ingestion", ["sd_risk_YYYYMMDD.csv"], vdd_format="csv")
    assert _format_questions(result) == []
    assert result.contract.feeds[0].file_format == "csv"
    flag = next(f for f in result.flags if f.startswith("format_from_extension:"))
    assert "file name pattern 'sd_risk_YYYYMMDD.csv' (extension .csv)" in flag
    assert f"confirmed by VDD {VDD_CELL}" in flag
    assert "'File Data Ingestion' names no file format" in flag


def test_the_note_line_cites_the_pattern(config, capsys):
    result = _fill(config, "File Data Ingestion", ["sd_risk_YYYYMMDD.psv"])
    assert result.contract.feeds[0].file_format == "psv"
    cli._print_file_elimination_notes(result.flags)
    out = capsys.readouterr().out
    assert out.startswith("NOTE")
    assert "feeds[0].file_format" in out and "extension .psv" in out


def test_a_format_that_names_another_delimiter_than_the_extension_is_asked(config):
    result = _fill(config, "pipe", ["sd_risk_YYYYMMDD.csv"])
    [question] = _format_questions(result)
    assert question.kind == "choice"
    assert [c["value"] for c in question.candidates] == ["pipe", "csv"]
    assert result.contract.feeds[0].file_format == "pipe"          # nothing written


def test_a_vdd_format_that_contradicts_the_extension_is_asked(config):
    result = _fill(config, "File Data Ingestion", ["sd_risk_YYYYMMDD.csv"], vdd_format="psv")
    [question] = _format_questions(result)
    assert [(c["value"], c["source"]) for c in question.candidates] == [
        ("csv", "file name"), ("psv", "VDD")]


def test_the_vdd_format_is_read_from_the_feeds_own_files_row(config):
    # One FILES row per file: the .psv file's row says psv; the first row's csv
    # belongs to another file and is no disagreement.
    vdd = {"file_patterns": [("a_YYYYMMDD.csv", "FILES!A2"), ("b_YYYYMMDD.psv", "FILES!A3")],
           "file_format": [("csv", "FILES!C2"), ("psv", "FILES!C3")]}
    result = fill_frd_gaps(_contract("File Data Ingestion", ["b_YYYYMMDD.psv"]), None, {}, vdd,
                           {}, config, REPO)
    assert _format_questions(result) == []
    assert result.contract.feeds[0].file_format == "psv"
    flag = next(f for f in result.flags if f.startswith("format_from_extension:"))
    assert "confirmed by VDD FILES!C3" in flag and "FILES!C2" not in flag


def test_an_ingestion_type_without_a_format_extension_takes_the_vdd(config):
    result = _fill(config, "File Data Ingestion", ["sd_risk_YYYYMMDD.txt"], vdd_format="csv")
    assert _format_questions(result) == []
    assert result.contract.feeds[0].file_format == "csv"
    assert any(f.startswith("frd_format_not_a_format:feeds[0].file_format")
               for f in result.flags)


@pytest.mark.parametrize("fmt", ["CSV, comma delimited", "csv"])
def test_a_format_the_extension_agrees_with_keeps_the_old_chain(config, fmt):
    result = _fill(config, fmt, ["x_YYYYMMDD.csv"], vdd_format="csv")
    assert _format_questions(result) == []
    assert result.contract.feeds[0].file_format == fmt
    assert not any(f.startswith("format_from_extension:") for f in result.flags)


@pytest.mark.parametrize(("text", "is_format"), [
    ("File Data Ingestion", False), ("csv", True), ("Pipe delimited (|) text file", True),
    ("Fixed Width Text", True), ("Parquet", True), ("Delimited", True), ("", False)])
def test_format_tokens(config, text, is_format):
    assert is_format_text(text, config.extractor.frd.format_tokens) is is_format


def test_an_empty_token_list_keeps_the_old_reading():
    assert is_format_text("File Data Ingestion", []) is True


@pytest.mark.parametrize(("text", "char"), [
    ("csv", ","), ("PSV", "|"), ("pipe", "|"), ("Pipe delimited (|)", "|"),
    ("Delimited", None), ("Fixed width, 120 bytes", None), ("File Data Ingestion", None)])
def test_format_delimiter(config, text, char):
    assert format_delimiter(text, config.extractor.delimiter_words) == char
