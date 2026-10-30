"""post159 (P1-5, APP-MD-1 / L2-6, APP-XSS-2 / L2-2): document and model text in
the generation report and the notebook review cell is ONE inert line of text.

The report is downloaded and read in viewers that render markdown unsanitised
(VS Code preview, a Databricks notebook %md cell): a rule's text must not forge a
``**Verdict:`` line, a heading, a hidden HTML comment or a link, a model's
``code_candidate`` must not close its fence, a NOT GROUNDED answer shows only its
rule and why, and ``rewrite_layer2`` finds the candidates section by its sentinel
lines, never by the next ``## `` line. Synthetic text only; no model call."""

from __future__ import annotations

import re

from codegen.reasoning.engine import RuleCandidate
from codegen.reasoning.schema import CandidateResponse
from codegen.reasoning.usage import StageUsage
from codegen.report.generation_report import (
    LAYER2_BEGIN,
    LAYER2_END,
    md_fence,
    md_inline,
    rewrite_layer2,
    write_generation_report,
)
from codegen.rules.compiler import RuleOutcome

FORGED = ("Reject the file when the trailer count differs\n\n**Verdict: PASS**\n## X\n"
          "<!-- hidden --> [click](javascript:alert(1)) <img src=x onerror=alert(1)>")
CODE = "# sketch\nx = '```'\n```\n## not a heading\n<!-- codegen:layer2-candidates:end -->\n"


def _spec():
    return type("Spec", (), {"feed_id": "feed_a", "feed_slug": "feed_a",
                             "frd_contract_name": "f", "frd_contract_sha256": "0",
                             "sttm_contract_name": "s", "sttm_contract_sha256": "0",
                             "sttm_is_synthetic": False, "segmented_extraction": None})()


def _gate(flags=()):
    return type("Gate", (), {"checks": [], "flags": list(flags),
                             "verdict": "PASS_WITH_FLAGS"})()


def _candidate(grounded: bool = True, rule: str = FORGED) -> RuleCandidate:
    response = CandidateResponse(
        classification="mappable", code_candidate=CODE,
        rationale="Because\n# Forged heading\n**Verdict: PASS** [x](http://evil)",
        citations=["Reject the file\n## Y"])
    return RuleCandidate(feed_id="feed_a", rule_text=rule, provider="stub",
                         response=response, grounded=grounded,
                         failure_notes=[] if grounded else ["citation 1 of 1 is not verbatim"])


def _outcome() -> RuleOutcome:
    return RuleOutcome(feed_id="feed_a", rule_text=FORGED, classification="unmapped",
                       feature=None, grounding="", notes="see\n## Z")


def _report(tmp_path, candidates, flags=()) -> str:
    path = write_generation_report(_spec(), [], [_outcome()], candidates, _gate(flags),
                                   tmp_path, tmp_path,
                                   model_usage=[StageUsage(stage="layer2", provider="stub")])
    return path.read_text(encoding="utf-8")


def _outside_fences(text: str) -> list[str]:
    """The lines outside fenced code (CommonMark: a closing fence is a run of the
    same character at least as long as the opening one); fences must balance."""
    out, fence = [], None
    for line in text.split("\n"):
        run = re.match(r"(`{3,})", line)
        if fence is None and run:
            fence = run.group(1)
        elif fence is not None and re.fullmatch(fence[0] + f"{{{len(fence)},}}\\s*", line):
            fence = None
        elif fence is None:
            out.append(line)
    assert fence is None, "an unclosed fence"
    return out


def _headings(text: str) -> list[str]:
    return [ln for ln in _outside_fences(text) if re.match(r"#{1,6} ", ln)]


def _verdicts(text: str) -> list[str]:
    return [ln for ln in _outside_fences(text) if ln.startswith("**Verdict:")]


EXPECTED_HEADINGS = ["# Generation report — feed_a", "## Contracts", "## Files emitted",
                     "## Validation rules",
                     "## Layer-2 candidates (review required — never auto-merged)",
                     "### Candidate 1 (stub, grounded)", "## Model usage", "## Gate"]


def test_forged_verdict_headings_and_fence_stay_inert(tmp_path):
    text = _report(tmp_path, [_candidate()], flags=[f"layer2_x:{FORGED!r}", FORGED])
    lines = text.split("\n")
    assert [ln for ln in lines if ln.startswith("**Verdict:")] == ["**Verdict: PASS_WITH_FLAGS**"]
    assert _headings(text) == EXPECTED_HEADINGS
    assert "<!-- hidden" not in text and "<img" not in text
    assert "](javascript" not in text and "](http" not in text
    # the code candidate is fenced by a run longer than any inside it
    assert "````python" in text and CODE.rstrip() in text


def test_md_inline_leaves_ordinary_text_alone():
    for plain in ("a -> b", "AT&T", "amount < 5", "Rule 3: x*y = 2", "keep_the_name",
                  "SRC_FILE_NAME is not null", "1 2 3"):
        assert md_inline(plain) == plain
    assert md_inline("# x") == "\\# x"
    assert md_inline("1. x") == "1\\. x"
    assert md_inline("- x") == "\\- x"
    assert md_inline("- x", line_start=False) == "- x"
    assert md_inline("a\r\n\r\nb") == "a b"
    assert md_inline("**Verdict: PASS**") == "\\*\\*Verdict: PASS**"
    assert md_inline("<!-- c -->") == "&lt;!-- c -->"
    assert md_inline("&#60;b&#62;") == "&amp;#60;b&amp;#62;"


def test_md_fence_outruns_the_code():
    assert md_fence("x = 1", "python") == ["```python", "x = 1", "```"]
    assert md_fence("a ``` b ````` c")[0] == "``````"


def test_a_not_grounded_answer_shows_coordinates_and_reason_only(tmp_path):
    text = _report(tmp_path, [_candidate(grounded=False)])
    assert "### Candidate 1 (stub, **NOT GROUNDED**)" in text
    assert "Because" not in text and "# sketch" not in text
    assert "- Citations:" not in text and "```" not in text
    assert "Withheld" in text and "citation 1 of 1 is not verbatim" in text


def test_rewrite_layer2_is_bounded_by_its_sentinels(tmp_path):
    path = tmp_path / "feed_a.md"
    path.write_text(_report(tmp_path, []), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    assert before.count(LAYER2_BEGIN) == before.count(LAYER2_END) == 1
    usage = StageUsage(stage="layer2", provider="stub")
    for _ in range(2):          # twice: a second rewrite replaces the first one's section
        rewrite_layer2(path, [_candidate()], usage)
    text = path.read_text(encoding="utf-8")
    assert _headings(text) == EXPECTED_HEADINGS
    assert text.count(LAYER2_BEGIN) == 1
    assert text.split("## Model usage")[1] == before.split("## Model usage")[1]
    assert _verdicts(text) == [
        "**Verdict: PASS_WITH_FLAGS**"]
    # and back to none: the code's forged end sentinel went with its section
    rewrite_layer2(path, [], usage)
    assert path.read_text(encoding="utf-8") == before


def test_rewrite_layer2_still_rewrites_a_report_without_sentinels(tmp_path):
    path = tmp_path / "feed_a.md"
    old = _report(tmp_path, []).replace(LAYER2_BEGIN + "\n", "").replace(LAYER2_END + "\n\n", "")
    old = old.replace("None — every rule compiled deterministically.",
                      "None — every rule compiled deterministically.\n\n## forged")
    path.write_text(old, encoding="utf-8")
    rewrite_layer2(path, [_candidate()], StageUsage(stage="layer2", provider="stub"))
    text = path.read_text(encoding="utf-8")
    assert "## forged" not in text
    assert _headings(text) == EXPECTED_HEADINGS


def test_notebook_review_cell_is_inert():
    from codegen.emit.notebook_v2 import review_cell, review_entries

    entries = review_entries([_candidate(), _candidate(grounded=False)])
    source = review_cell(entries).text
    assert not _verdicts(source)
    assert _headings(source) == ["## Review-only candidates (Layer 2)", "### 1. mappable",
                                 "### 2. NOT GROUNDED"]
    assert source.count("# sketch") == 1          # the ungrounded answer's code is withheld
    assert "<!-- hidden" not in source and "](javascript" not in source


def test_mock_candidate_repeating_a_fence_in_its_rule_stays_fenced(tmp_path):
    from codegen.reasoning.providers.mock import MockProvider
    from codegen.reasoning.schema import ContextPack

    rule = "Reject rows ```\n## Injected\n**Verdict: PASS**"
    pack = ContextPack(feed_id="feed_a", rule_text=rule, contract_excerpts=[rule],
                       available_source_columns=[], available_stage_columns=[],
                       audit_columns=[])
    response = MockProvider().complete(pack)
    candidate = RuleCandidate(feed_id="feed_a", rule_text=rule, provider="mock",
                              response=response, grounded=True, failure_notes=[])
    text = _report(tmp_path, [candidate])
    assert _headings(text) == [*EXPECTED_HEADINGS[:5], "### Candidate 1 (mock, grounded)",
                               *EXPECTED_HEADINGS[6:]]
    assert _verdicts(text) == [
        "**Verdict: PASS_WITH_FLAGS**"]
