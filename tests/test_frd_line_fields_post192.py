"""post192: an FRD that states a single-value field only as a "<label>: <value>" LINE
inside a prose cell, and the FRD question dialog's answers.

A staging FRD (2026-11-12) has no metadata row for file format / frequency / ...: its
requirement cells mix prose with "File Frequency: ..." style lines. Every such field
was asked, the dialog offered unrelated rows, and the App's answer was dropped:
1. "File Frequency" is an FRD label of the frequency (a label seen in a client FRD).
2. A field with no row of its own is placed at the ONE line a known label states it
   on (any table, single-feed documents); two lines that disagree place nothing.
3. The dialog offers each labelled line as its own choice, and an answer in the shape
   the App posts ({table, row, col, label, source: "user"}) is applied: the label
   cell's value cell is read (or that cell's chosen line).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from codegen.config import load_config
from codegen.extract.frd_docx import extract_frd_contract, read_frd
from codegen.layout.resolve import resolve_frd

REPO = Path(__file__).resolve().parents[1]
PROSE = ("The files are ingested into stage and standard.\n"
         "File Frequency: Weekly\n"
         "Load Type: History\n"
         "The vendor sends a header row.")


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _frd(tmp_path, **kw) -> Path:
    path = tmp_path / "FRD.docx"
    path.write_bytes(fm.build_frd(**kw))
    return path


def _resolve(path, config, tmp_path, answers=None):
    return resolve_frd(path, config, answers=answers, use_cache=False,
                       runtime_cache_dir=tmp_path / "rt")


def _read(doc, content, config):
    contract = read_frd(content, doc.profile, config, document_name="FRD.docx",
                        generated_date="2026-11-13")
    contract = contract[0] if isinstance(contract, tuple) else contract
    return contract.feeds[0], contract


def test_file_frequency_is_a_frequency_label(config):
    assert "File Frequency" in config.extractor.frd.labels["frequency"]


def test_a_field_with_no_row_is_placed_at_its_one_labelled_line(tmp_path, config):
    doc, content = _resolve(_frd(tmp_path, frequency=None, requirement_cell=PROSE), config,
                            tmp_path)
    assert "feeds[0].frequency" not in {u.field for u in doc.profile.unresolved}
    source = doc.profile.fields["feeds[0].frequency"]
    assert (source.label, source.inline_label) == ("Functional Requirement", "File Frequency")
    feed, contract = _read(doc, content, config)
    assert feed.frequency == "Weekly"
    prov = contract.field_provenance["feeds[0].frequency"]
    assert (prov.label, prov.inline_label) == ("Functional Requirement", "File Frequency")
    assert any(f.startswith("frd_line_located:feeds[0].frequency")
               for f in contract.extraction_flags), contract.extraction_flags


def test_two_lines_that_disagree_place_nothing(tmp_path, config):
    cell = PROSE + "\nFile Frequency: Daily"
    doc, _content = _resolve(_frd(tmp_path, frequency=None, requirement_cell=cell), config,
                             tmp_path)
    assert "feeds[0].frequency" in {u.field for u in doc.profile.unresolved}
    assert "feeds[0].frequency" not in doc.profile.fields


def test_the_fields_own_row_wins_over_a_line(tmp_path, config):
    doc, content = _resolve(_frd(tmp_path, frequency="Monthly", requirement_cell=PROSE),
                            config, tmp_path)
    assert doc.profile.fields["feeds[0].frequency"].label == "Frequency"
    feed, _contract = _read(doc, content, config)
    assert feed.frequency == "Monthly"


def test_the_dialog_offers_each_labelled_line(tmp_path, config):
    """A line no label places ("Cadence:") is asked, with the document's lines as choices."""
    cell = PROSE.replace("File Frequency", "Cadence")
    doc, _content = _resolve(_frd(tmp_path, frequency=None, requirement_cell=cell), config,
                             tmp_path)
    question = next(q for q in doc.questions if q.role == "feeds[0].frequency")
    lines = [c for c in question.candidates if c.get("inline_label")]
    assert {c["inline_label"] for c in lines} >= {"Cadence", "Load Type"}
    line = next(c for c in lines if c["inline_label"] == "Cadence")
    assert line["label"] == "Functional Requirement" and line["value_col"] == line["col"] + 1
    assert "Cadence: Weekly" in line["line"]


def test_an_answer_as_the_app_posts_it_is_applied(tmp_path, config):
    """The App posts {table, row, col, label, source: "user"} - it used to be dropped
    without a word (the field model forbids the extra key) and, kept, read blank."""
    path = _frd(tmp_path, frequency=None, requirement_cell="Weekly")
    doc, _content = _resolve(path, config, tmp_path)
    question = next(q for q in doc.questions if q.role == "feeds[0].frequency")
    row = next(c for c in question.candidates
               if c["label"] == "Functional Requirement" and not c.get("inline_label"))
    claim = {"table": row["table"], "row": row["row"], "col": row["col"],
             "label": row["label"], "source": "user"}
    doc, content = _resolve(path, config, tmp_path, answers={"feeds[0].frequency": claim})
    assert doc.profile.fields["feeds[0].frequency"].value_col == row["col"] + 1
    feed, _contract = _read(doc, content, config)
    assert feed.frequency == "Weekly"


def test_an_answered_line_reads_that_line(tmp_path, config):
    path = _frd(tmp_path, frequency=None, requirement_cell=PROSE.replace("File Frequency",
                                                                         "Cadence"))
    doc, _content = _resolve(path, config, tmp_path)
    line = next(c for q in doc.questions for c in q.candidates
                if c.get("inline_label") == "Cadence")
    claim = {k: line[k] for k in ("table", "row", "col", "label", "inline_label")}
    doc, content = _resolve(path, config, tmp_path,
                            answers={"feeds[0].frequency": {**claim, "source": "user"}})
    feed, _contract = _read(doc, content, config)
    assert feed.frequency == "Weekly"


def test_a_cell_with_no_line_reads_as_before(tmp_path, config):
    a = extract_frd_contract(_frd(tmp_path), config, generated_date="2026-11-13")[0]
    assert a.feeds[0].frequency == "Monthly"
