"""RESTART item 2(b), 2026-11-18: a live layout answer carried an invalid top-level
``source`` - a field the CODE sets (it overwrites ``source`` / ``role_sources`` /
``field_sources`` after validation), yet the model's value failed the schema: the STTM
answer went to the salvage path with a "failed schema validation" report line, and an
FRD answer was discarded WHOLE (no salvage there). The code-owned fields are now set
before validation - the model's bookkeeping never fails an answer; every claim is still
validated as before."""

from __future__ import annotations

from codegen.layout.resolve import resolve_frd, resolve_workbook, salvage_layout_answer
from layout_attack import F1_FRD, StubProvider, frd_with_label, place_frd  # noqa: F401
from test_layout_answer_salvage import PAIR_1, _full_answer
from test_layout_frd_model_label import PAYLOAD, SCHEMA, _claim, _empty

BOGUS = {"source": "llm", "role_sources": {"anything": "guessed"},
         "field_sources": {"anything": "guessed"}}


def test_an_sttm_answers_own_source_value_is_no_schema_error(config):
    answer = {**_full_answer(config), **BOGUS}
    partial = resolve_workbook(PAIR_1, config, provider=None, cache_dirs=[])[0].profile
    profile, lines, errors = salvage_layout_answer(answer, partial)
    assert profile is not None and lines == [] and errors == []
    assert profile.source == "model" and profile.role_sources == {}


def test_an_frd_answers_own_source_value_does_not_discard_it(config, tmp_path):
    path = frd_with_label(tmp_path / "frd.docx", "Target Catalog and Schema", PAYLOAD)
    place = place_frd({SCHEMA: _claim(5, PAYLOAD)})
    stub = StubProvider(lambda request, partial: {**place(request, partial), **BOGUS})
    doc, _ = resolve_frd(path, config, provider=stub, cache_dirs=_empty(tmp_path))
    assert stub.requests
    reasons = [r.reason for r in doc.rejections]
    assert not any("failed schema validation" in r for r in reasons), reasons
    # the claim reached the workbook validation (and is refused there, as before)
    assert any(r.role == SCHEMA and "not a label of this field" in r.reason
               for r in doc.rejections)
