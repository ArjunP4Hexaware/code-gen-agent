"""post210 (the second tester's run, 2026-11-19; synthetic text only): every FRD
question offered EVERY labelled cell / line of the document (the same ~16 for each
field, none stating any of them), and an unplaced feed name was asked though it blocks
nothing. Now: no feed-name question; a field a person may type is offered only the
cells whose value reads as its value (its one reader - strategy, delimiter, format;
none for a field with no reader); the layout model's proposal is kept; a field a person
may not type keeps every cell."""

from __future__ import annotations

from pathlib import Path

from codegen.config import load_config
from codegen.extract.frd_docx import DocxContent
from codegen.layout.frd_profile import FrdLayoutProfile, FrdUnresolved
from codegen.layout.resolve import _frd_questions

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")


def _sr(requirement: str) -> list[list[str]]:
    return [["Solution Requirement: 1"], ["Name", "Syn file"],
            ["Description", "Ingest the synthetic file."],
            ["Functional Requirement", requirement], ["IS Owner", "Syn Owner"],
            ["Impact Details", "none"]]


CONTENT = DocxContent(tables=[_sr("Container Name: syn-raw\nLoad Type:\n"
                                  "Incremental: Truncate & load\nHistory: Append\n"
                                  "Delimiter: Pipe\nFormat: pipe delimited text")],
                      paragraphs=[])


def _questions(*fields: str, proposed: dict[str, list[str]] | None = None):
    profile = FrdLayoutProfile(
        fingerprint="f" * 64, family="F2", source="synonyms", fields={}, confidence={},
        unresolved=[FrdUnresolved(field=f, reason="no label in the document maps to this field",
                                  candidates=(proposed or {}).get(f, []))
                    for f in fields])
    return {q.key: q for q in _frd_questions(profile, CONTENT, CONFIG)}


def _lines(question) -> list[str]:
    return [c.get("line") or c["label"] for c in question.candidates]


def test_an_unplaced_feed_name_is_not_asked():
    assert "feeds[0].feed_name" not in _questions("feeds[0].feed_name", "feeds[0].lobs")


def test_a_strategy_is_offered_only_the_lines_that_read_as_one():
    q = _questions("feeds[0].stage_target.load_strategy")["feeds[0].stage_target.load_strategy"]
    assert _lines(q) == ["Incremental: Truncate & load", "History: Append"]


def test_a_delimiter_and_a_format_are_offered_their_own_lines():
    qs = _questions("feeds[0].delimiter", "feeds[0].file_format")
    assert "Delimiter: Pipe" in _lines(qs["feeds[0].delimiter"])
    assert "Container Name: syn-raw" not in _lines(qs["feeds[0].delimiter"])
    assert _lines(qs["feeds[0].file_format"]) == ["Delimiter: Pipe",
                                                   "Format: pipe delimited text"]


def test_a_field_with_no_reader_is_offered_no_cell():
    qs = _questions("feeds[0].lobs", "feeds[0].domain")
    assert qs["feeds[0].lobs"].candidates == [] and qs["feeds[0].domain"].candidates == []


def test_the_layout_models_proposal_is_kept():
    # the model proposed the requirement cell (table 0 row 3) for the LOBs: its lines stay
    q = _questions("feeds[0].lobs", proposed={"feeds[0].lobs": ["0:3:0"]})["feeds[0].lobs"]
    assert q.candidates and {(c["table"], c["row"]) for c in q.candidates} == {(0, 3)}


def test_a_model_claim_of_a_non_descriptive_name_row_is_a_proposal():
    """The second tester's LIVE run (the layout model): post208 held for the synonyms
    only - the model put the feed name on the Data Quality section's Name row."""
    from codegen.layout.frd_profile import FrdFieldSource, FrdSectionRef
    from codegen.layout.resolve import _model_label_reason

    def reason(section: str):
        profile = FrdLayoutProfile(
            fingerprint="f" * 64, family="F1", source="model", fields={}, confidence={},
            sections=[FrdSectionRef(table=0, section=section, title="T", feed_index=0)])
        source = FrdFieldSource(table=0, row=1, col=0, value_col=1, label="Name",
                                section=section)
        return _model_label_reason("feeds[0].feed_name", source, "Name", profile, CONFIG)

    assert "names the section, not the feed" in reason("data_quality")
    assert "kept as a proposal" in reason("vendor")
    assert reason("descriptive") is None


def test_a_frequency_is_offered_only_the_lines_naming_one():
    content = DocxContent(tables=[_sr("Cadence: Weekly\nLoad Type: History\nOwner: Syn")],
                          paragraphs=[])
    profile = FrdLayoutProfile(
        fingerprint="f" * 64, family="F2", source="synonyms", fields={}, confidence={},
        unresolved=[FrdUnresolved(field="feeds[0].frequency", reason="unplaced")])
    (q,) = _frd_questions(profile, content, CONFIG)
    assert [c["line"] for c in q.candidates] == ["Cadence: Weekly"]
