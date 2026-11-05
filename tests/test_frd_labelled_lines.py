"""post168: an FRD cell made of "<label>: <value>" lines is read line by line.

The 2026-11-04 exchange FRD (staging App) states its format in the Structural
Metadata "Object/data Format" row as two labelled lines - "File Format: .txt" then
"Delimiter: Pipe Delimited". The reader refused the cell as multi-line, the STTM
states no format, so the run asked the person for a value the FRD states. Now
every line whose label ``extractor.frd.cell_line_labels`` knows goes to its own
field (the label as written cited); any other line keeps the refusal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from codegen.config import load_config
from codegen.extract.frd_docx import extract_frd_contract, labelled_cell_lines

REPO = Path(__file__).resolve().parents[1]
CELL = "File Format: .txt\nDelimiter: Pipe Delimited"
LABELS = {"file_format": ["File Format"], "delimiter": ["Delimiter"]}


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _feed(tmp_path, config, cell: str):
    frd = tmp_path / "FRD.docx"
    frd.write_bytes(fm.build_frd(format_cell=cell))
    contract, _ = extract_frd_contract(frd, config, generated_date="2026-11-04")
    (feed,) = contract.feeds
    return feed, contract


def test_the_exact_cell_reads_one_value_per_labelled_line():
    assert labelled_cell_lines(CELL, LABELS) == [
        ("file_format", "File Format", ".txt"), ("delimiter", "Delimiter", "Pipe Delimited")]


@pytest.mark.parametrize("text", [
    None, "", "File Format: .txt",                          # one line: read as before
    "File Format: .txt\nEncoding: UTF-8",                   # a label no field knows
    "File Format: .txt\nfirst row is a header",             # an unlabelled line
    "File Format: .txt\nFile Format: .csv",                 # the same field twice
])
def test_any_other_cell_is_not_split(text):
    assert labelled_cell_lines(text, LABELS) is None


def test_the_reader_takes_the_format_and_the_delimiter_from_their_lines(tmp_path, config):
    feed, contract = _feed(tmp_path, config, CELL)
    assert (feed.file_format, feed.delimiter) == (".txt", "Pipe Delimited")
    # each value cited at the cell, under the label the document writes on its line
    prov = contract.field_provenance
    assert prov["feeds[0].file_format"].inline_label == "File Format"
    assert prov["feeds[0].delimiter"].inline_label == "Delimiter"
    assert prov["feeds[0].delimiter"].label == "Object/data Format"
    assert any(f.startswith("frd_labelled_lines:feeds[0].file_format") and "'Delimiter'" in f
               for f in contract.extraction_flags), contract.extraction_flags
    assert not any("frd_multiline:feeds[0].file_format" in a
                   for a in contract.provenance.ambiguities)


def test_a_cell_with_an_unknown_line_stays_refused(tmp_path, config):
    feed, contract = _feed(tmp_path, config, "File Format: .txt\nEncoding: UTF-8")
    assert (feed.file_format, feed.delimiter) == (None, None)
    assert any("frd_multiline:feeds[0].file_format" in str(a)
               for a in contract.provenance.ambiguities)


def test_a_plain_format_cell_reads_as_before(tmp_path, config):
    feed, contract = _feed(tmp_path, config, "Pipe delimited text, first row is a header")
    assert feed.file_format == "Pipe delimited text, first row is a header"
    assert feed.delimiter is None
    assert not any(f.startswith("frd_labelled_lines") for f in contract.extraction_flags)


def test_a_placeholder_line_is_a_stated_blank(tmp_path, config):
    feed, _ = _feed(tmp_path, config, "File Format: .txt\nDelimiter: N/A")
    assert (feed.file_format, feed.delimiter) == (".txt", None)


def test_layout_gives_every_derived_feed_the_frds_format_and_delimiter(tmp_path, monkeypatch,
                                                                       capsys):
    """The run path (``codegen layout``, mock): before post168 the pair's FRD
    contract carried no format and no delimiter for any feed, so an STTM that
    states neither left the person a question the FRD answers."""
    import json

    from codegen import cli

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    (tmp_path / "state").mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    sttm, frd, out = tmp_path / "STTM_nb.xlsx", tmp_path / "FRD_nb.docx", tmp_path / "frd.json"
    fm.build_sttm().save(sttm)
    frd.write_bytes(fm.build_frd(format_cell=CELL))
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(out)]) == 0
    capsys.readouterr()
    feeds = json.loads(out.read_text(encoding="utf-8"))["feeds"]
    assert len(feeds) == len(fm.FILES)
    assert {(f["file_format"], f["delimiter"]) for f in feeds} == {("txt", "Pipe Delimited")}
