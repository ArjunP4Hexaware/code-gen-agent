"""Plain-language help on layout questions: title, hint, suggested candidate."""

from __future__ import annotations

from codegen.layout.hints import frd_field_help, role_help


def test_frd_field_help_names_the_field_and_suggests_the_usual_label(config):
    candidates = [
        {"table": 0, "row": 3, "col": 0, "label": "Data Source", "section": "descriptive"},
        {"table": 0, "row": 4, "col": 0, "label": "Frequency", "section": "descriptive"},
        {"table": 1, "row": 5, "col": 0, "label": "Load Strategy STD (View)",
         "section": "structural"},
    ]
    title, hint, suggested = frd_field_help("feeds[0].frequency", candidates, config)
    assert title == "Load frequency" and "Descriptive Metadata" in hint
    assert suggested == 1
    title, hint, suggested = frd_field_help("feeds[0].standard_target.load_strategy",
                                            candidates, config)
    assert title == "Standard load strategy" and suggested == 2
    title, hint, suggested = frd_field_help("feeds[1].source_system#fallback", candidates,
                                            config)
    assert title == "Source system / vendor" and suggested == 0
    # Unknown field: a generic sentence, no suggestion.
    title, hint, suggested = frd_field_help("feeds[0].mystery.thing", candidates, config)
    assert title and hint and suggested is None
    # No candidate matching the usual labels: no suggestion, help still there.
    assert frd_field_help("feeds[0].lobs", candidates, config)[2] is None


def test_role_help_titles_and_suggests_by_header_words():
    candidates = [{"col": 2, "header": "Attribute"}, {"col": 3, "header": "Source Field Name"},
                  {"col": 4, "header": "Type"}]
    title, hint, suggested = role_help("field_name", "source", candidates)
    assert title == "Field name" and "source band" in hint and suggested == 1
    title, hint, suggested = role_help("segment", "source", candidates)
    assert title == "Record segment" and suggested is None
    # Ambiguous roles are explained together; unknown roles get a generic line.
    title, hint, _ = role_help("length|field_length", "source", candidates)
    assert title == "Field length or Field length" or "Field length" in title
    title, hint, _ = role_help("something_new", "stage", [])
    assert title == "Something new" and "stage layer" in hint
