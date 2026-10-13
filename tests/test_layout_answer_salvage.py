"""A model layout answer with schema errors keeps its valid parts (2026-10-13).

D1 pair_11: the live STTM layout answer was REJECTED with "8 validation
errors" and every role it placed was discarded — the report kept only the
first line. Now every error is a REJECTED line (CLI and the unresolved
report), a role mapped to ``null`` is read as "not found" (no error), and the
sheets / bands that validate go on to the same workbook validation a whole
answer meets: a usable answer minus one bad part still places its roles.
"""

from __future__ import annotations

import json
from pathlib import Path

import pre_m9_vocabulary
from codegen.layout.model import MockLayoutProvider
from codegen.layout.resolve import resolve_workbook, salvage_layout_answer

REPO = Path(__file__).resolve().parents[1]
PAIR_1 = REPO / "fixtures" / "acfc_shapes" / "sttm" / "pair_1_family_a.xlsx"
SHEET = "FEED_1_MAPPING"


def _full_answer(config) -> dict:
    """The complete pair-1 profile — what a correct model answer looks like."""
    doc, _ = resolve_workbook(PAIR_1, config, provider=None, cache_dirs=[])
    assert not doc.questions
    return doc.profile.model_dump(mode="json")


def _broken(answer: dict) -> dict:
    """A usable answer with three schema problems: a sheet the workbook does
    not have whose one band names no layer, a top-level confidence that is
    not a number, and a role the model says it did not find (``null``)."""
    answer = json.loads(json.dumps(answer))
    sheet = next(s for s in answer["sheets"] if s["name"] == SHEET)
    sheet["bands"][0]["roles"]["catalog"] = None
    answer["sheets"].append({"name": "Table_Details", "kind": "table_details",
                             "bands": [{"layer": "target", "col_start": 0, "col_end": 5,
                                        "roles": {"schema": 2}}]})
    answer["confidence"] = {"x": "high"}
    return answer


def test_the_valid_parts_are_kept_and_every_error_reported(config):
    partial = resolve_workbook(PAIR_1, pre_m9_vocabulary.strip(config), provider=None,
                               cache_dirs=[])[0].profile
    profile, lines, errors = salvage_layout_answer(_broken(_full_answer(config)), partial)
    assert profile is not None
    assert [s.name for s in profile.sheets] == [s["name"] for s in
                                                _broken(_full_answer(config))["sheets"]]
    assert profile.sheet("Table_Details").bands == []          # its one bad band dropped
    assert lines[0].startswith("model response failed schema validation: ")
    assert "kept" in lines[0] and "1 band(s) dropped" in lines[0]
    assert len(lines) == 1 + len(errors) and len(errors) == 3  # layer, col_start, confidence
    assert all(line.startswith("model answer schema error at ") for line in lines[1:])
    assert not any("catalog" in line for line in lines)       # null = not found, no error
    assert not any("high" in line or "target" in line for line in lines[1:])  # no input value


def test_a_schema_valid_answer_reports_nothing(config):
    answer = _full_answer(config)
    partial = resolve_workbook(PAIR_1, config, provider=None, cache_dirs=[])[0].profile
    profile, lines, errors = salvage_layout_answer(answer, partial)
    assert profile is not None and lines == [] and errors == []


def test_a_salvaged_answer_still_places_the_open_roles(config, tmp_path):
    """Before: one schema error -> the whole answer discarded, the roles the
    synonyms left open stayed UNRESOLVED. Now the valid part places them."""
    pre_m9 = pre_m9_vocabulary.strip(config)
    answer = tmp_path / "answer.json"
    answer.write_text(json.dumps(_broken(_full_answer(config))), encoding="utf-8")
    doc, _ = resolve_workbook(PAIR_1, pre_m9, provider=MockLayoutProvider([], override=answer),
                              cache_dirs=[], runtime_cache_dir=tmp_path / "runtime",
                              refresh=True)
    assert doc.provider_calls == 1
    assert not doc.questions, [q.key for q in doc.questions]
    reasons = [r.reason for r in doc.rejections]
    assert reasons[0].startswith("model response failed schema validation: 3 error(s); kept")
    assert sum(r.startswith("model answer schema error at ") for r in reasons) == 3


def test_the_unresolved_report_lists_the_rejections(config, tmp_path, monkeypatch, capsys):
    from codegen import cli

    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{tmp_path.as_posix()}")
    bad = tmp_path / "answer.json"
    bad.write_text(json.dumps({"fingerprint": "x", "source": "model", "strategy": "content",
                               "sheets": [{"name": SHEET, "kind": "mapping",
                                           "header_row": "fifteen"}]}), encoding="utf-8")
    from codegen.layout import resolve as layout_resolve

    original = layout_resolve.resolve_workbook

    def with_bad_model(path, cfg, **kwargs):
        kwargs["provider"] = MockLayoutProvider([], override=bad)
        return original(path, pre_m9_vocabulary.strip(cfg), **kwargs)

    monkeypatch.setattr(layout_resolve, "resolve_workbook", with_bad_model)
    report = tmp_path / "unresolved.md"
    cli.main(["layout", "--workbook", str(PAIR_1), "--no-cache", "--report-unresolved",
              str(report)])
    out = capsys.readouterr().out
    rejected = [line for line in out.splitlines() if line.startswith("REJECTED")]
    assert any("model answer schema error at sheets.0.header_row" in line for line in rejected)
    text = report.read_text(encoding="utf-8")
    assert "## Model answer rejected" in text
    assert "model answer schema error at sheets.0.header_row" in text
    assert "fifteen" not in text
