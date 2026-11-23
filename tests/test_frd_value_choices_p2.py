"""P2 of the question UX (2026-11-20; the second tester's run: ~16 cells per question,
shown by table / row): an FRD question a person may type offers VALUES - each choice
carries ``shown`` (what its cell / line would give the field), one choice per distinct
value (``also`` = the other places stating it), at most ``layout.frd_question_max_values``
of them, the layout model's proposal always kept. The pick is still a cell (the answer
path is unchanged) and ``shown`` never reaches the answers template. Synthetic text only."""

from __future__ import annotations

from pathlib import Path

from codegen.config import load_config
from codegen.extract.frd_docx import DocxContent
from codegen.layout.frd_profile import FrdLayoutProfile, FrdUnresolved
from codegen.layout.resolve import _frd_questions

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")


def _sr(number: int, requirement: str) -> list[list[str]]:
    return [[f"Solution Requirement: {number}"], ["Name", f"Syn file {number}"],
            ["Description", "Ingest the synthetic file."],
            ["Functional Requirement", requirement], ["IS Owner", "Syn Owner"],
            ["Impact Details", "none"]]


def _question(content: DocxContent, field: str, proposed: list[str] | None = None,
              config=CONFIG):
    profile = FrdLayoutProfile(
        fingerprint="f" * 64, family="F2", source="synonyms", fields={}, confidence={},
        unresolved=[FrdUnresolved(field=field, reason="no label in the document maps to "
                                                      "this field",
                                  candidates=proposed or [])])
    (q,) = _frd_questions(profile, content, config)
    return q


def test_the_config_caps_the_values():
    assert CONFIG.layout.frd_question_max_values == 5


def test_each_choice_shows_the_value_it_would_give():
    content = DocxContent(tables=[_sr(1, "Delimiter: Pipe\nFormat: pipe delimited text")],
                          paragraphs=[])
    q = _question(content, "feeds[0].delimiter")
    assert [c["shown"] for c in q.candidates] == ["Pipe", "pipe delimited text"]
    assert all("table" in c and "row" in c for c in q.candidates)    # the pick is a cell


def test_the_same_value_in_several_places_is_one_choice():
    # three requirements state the same delimiter (spaces / case differ): ONE choice
    content = DocxContent(tables=[_sr(1, "Delimiter: Pipe"), _sr(2, "Delimiter:  pipe"),
                                  _sr(3, "Delimiter: Comma")], paragraphs=[])
    q = _question(content, "feeds[0].delimiter")
    assert [(c["shown"], c["also"]) for c in q.candidates] == [("Pipe", 1), ("Comma", 0)]
    assert q.candidates[0]["table"] == 0                     # the first place it is stated


def test_the_choices_are_capped_and_the_proposal_kept():
    words = ["Pipe", "Comma", "Tab", "Semicolon", "Caret", "Tilde", "Colon"]
    tables = [_sr(i, f"Delimiter: {w}") for i, w in enumerate(words, start=1)]
    content = DocxContent(tables=tables, paragraphs=[])
    capped = CONFIG.model_copy(update={"layout": CONFIG.layout.model_copy(
        update={"frd_question_max_values": 3})})
    q = _question(content, "feeds[0].delimiter", config=capped)
    assert len(q.candidates) == 3
    # the layout model proposed the LAST one (table 6 row 3): kept although past the cap
    q = _question(content, "feeds[0].delimiter", proposed=["6:3:0"], config=capped)
    assert len(q.candidates) == 3 and q.candidates[-1]["table"] == 6


def test_a_duplicate_proposed_place_is_the_one_kept():
    content = DocxContent(tables=[_sr(1, "Delimiter: Pipe"), _sr(2, "Delimiter: Pipe")],
                          paragraphs=[])
    q = _question(content, "feeds[0].delimiter", proposed=["1:3:0"])
    assert [(c["table"], c["also"]) for c in q.candidates] == [(1, 1)]


def test_the_answers_template_never_carries_a_value():
    """``shown`` is not ``value``: cli._question_items writes value only for the question
    kinds that pick a value, never an FRD cell's text."""
    from codegen.cli import _question_items

    content = DocxContent(tables=[_sr(1, "Delimiter: Pipe")], paragraphs=[])
    q = _question(content, "feeds[0].delimiter")
    (item,) = _question_items([q])
    assert "Pipe" not in " ".join(item.candidates)


def test_a_proposal_with_no_value_text_is_still_offered():
    """The first post216 suites: the layout model proposed a label row whose cell holds no
    value text (tests/test_layout_frd_model_label.py) - the dedupe dropped it, and the
    proposal's pre-selection with it. The proposal is always offered."""
    from codegen.layout.resolve import _value_choices

    content = DocxContent(tables=[[["Structural Metadata", ""], ["Target Schema", ""],
                                   ["Delimiter", "Pipe"]]], paragraphs=[])
    offered = [{"table": 0, "row": 1, "col": 0, "label": "Target Schema"},
               {"table": 0, "row": 2, "col": 0, "label": "Delimiter"}]
    choices = _value_choices(offered, ["0:1:0"], content, 5)
    assert [(c["row"], c.get("shown")) for c in choices] == [(1, None), (2, "Pipe")]
    assert _value_choices(offered, [], content, 5) == [{**offered[1], "shown": "Pipe",
                                                         "also": 0}]
