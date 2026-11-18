"""RESTART item 2(a), 2026-11-18: the unresolved-headers report named an FRD line choice
by its row label only, so two labelled lines of one cell read the same there. A line
candidate now shows its line label (a structural label, as written) - never the line
itself, which carries the value."""

from __future__ import annotations

from codegen.layout.answers import unresolved_report
from codegen.layout.resolve import LayoutQuestion


def test_two_line_choices_of_one_cell_differ_by_their_line_label():
    base = {"table": 3, "row": 2, "col": 0, "value_col": 1, "label": "Functional Requirement"}
    question = LayoutQuestion(
        document="frd", sheet=None, layer=None, role="feeds[0].frequency",
        reason="no label in the document maps to this field",
        candidates=[{**base, "inline_label": "File Frequency", "line": "File Frequency: SYNVAL1"},
                    {**base, "inline_label": "Delivery", "line": "Delivery: SYNVAL2"}])
    report = unresolved_report([question], {"frd": "FRD.docx"})
    assert "`0: Functional Requirement · File Frequency`" in report
    assert "`0: Functional Requirement · Delivery`" in report
    assert "SYNVAL" not in report                       # the line's value never appears
