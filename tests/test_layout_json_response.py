"""The live layout recognizer reads the JSON object out of what the model
actually sends (2026-10-13, D1 pair_11: "no JSON profile after 2 attempt(s);
last error: Expecting value: line 1 column 1 (char 0)" — the body was never
parsed).

A response may arrive in markdown fences, after a preamble, or followed by
prose: the outermost balanced object is taken. When the first attempt is not
JSON, ONE retry is sent with "respond with JSON only, no fences" appended.
Every rejected response is logged (first 500 characters) on stderr and in the
runtime cache's rejections folder — D1-only diagnostics, never a tracked file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.layout.model import (
    RAW_LOG_CHARS,
    RETRY_INSTRUCTION,
    FmapiLayoutProvider,
    LayoutProviderError,
    parse_json_response,
)
from codegen.layout.resolve import resolve_workbook

REPO = Path(__file__).resolve().parents[1]
PAIR_1 = REPO / "fixtures" / "acfc_shapes" / "sttm" / "pair_1_family_a.xlsx"
TRUTH = REPO / "fixtures" / "layout_profiles" / "sttm_pair_1_family_a.layout.json"
PROFILE = TRUTH.read_text(encoding="utf-8")

FENCED = f"```json\n{PROFILE}\n```"
PREAMBLED = ("Here is the completed layout profile for the {sheet} you sent. I placed "
             "every open role I could find:\n\n" + PROFILE + "\n\nLet me know if a role "
             "should move.")


@pytest.fixture(scope="module")
def config():
    import pre_m9_vocabulary       # pair 1 leaves its target roles open: a model call

    shipped = load_config(REPO / "config" / "config.yaml")
    stripped = pre_m9_vocabulary.strip(shipped)
    return stripped.model_copy(update={"layout": stripped.layout.model_copy(
        update={"provider": "live"})})


def _live(config, monkeypatch, responses: list[str]) -> tuple[FmapiLayoutProvider, list[str]]:
    import codegen.databricks as seam

    prompts: list[str] = []
    queue = list(responses)

    def fake_chat(cfg, messages, endpoint=None, max_tokens=0, client=None):
        prompts.append(messages[-1]["content"])
        return queue.pop(0)

    monkeypatch.setattr(seam, "chat", fake_chat)
    return FmapiLayoutProvider(config, endpoint="ep-under-test"), prompts


@pytest.mark.parametrize("wrapped", [FENCED, PREAMBLED, f"```\n{PROFILE}```",
                                     f"Sure.\n```json\n{PROFILE}\n```\nDone."])
def test_a_fenced_or_preambled_response_parses(wrapped):
    assert parse_json_response(wrapped) == json.loads(PROFILE)


def test_the_outermost_object_is_taken_never_a_nested_one():
    # the object is followed by prose with braces; a nested dict is not "the" object
    text = 'Profile: {"a": {"b": 1}, "c": "x}y"} — note {not json}'
    assert parse_json_response(text) == {"a": {"b": 1}, "c": "x}y"}
    # an invalid outer object never falls back to its inner dict
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_json_response('{"a": {"b": 1},}')


@pytest.mark.parametrize(("text", "why"), [
    ("", "empty response"),
    ("I cannot determine the layout.", "no '{'"),
    ('```json\n{"fingerprint": "abc", "sheets": [', "ends inside the JSON object"),
])
def test_no_object_names_why(text, why):
    with pytest.raises(ValueError, match=why):
        parse_json_response(text)


@pytest.mark.parametrize("wrapped", [FENCED, PREAMBLED])
def test_the_live_recognizer_reads_a_wrapped_profile_in_one_call(config, monkeypatch, wrapped):
    live, prompts = _live(config, monkeypatch, [wrapped])
    doc, _wb = resolve_workbook(PAIR_1, config, provider=live, use_cache=False)
    assert len(prompts) == 1 and live.calls == 1
    assert doc.questions == []
    assert not [r for r in doc.rejections if "no JSON" in r.reason]


def test_a_non_json_first_answer_is_retried_once_with_json_only(config, monkeypatch):
    live, prompts = _live(config, monkeypatch, ["I need more context.", PROFILE])
    doc, _wb = resolve_workbook(PAIR_1, config, provider=live, use_cache=False)
    assert len(prompts) == 2 and live.calls == 2
    assert RETRY_INSTRUCTION not in prompts[0]
    assert prompts[1].endswith(RETRY_INSTRUCTION)
    assert doc.questions == []


def test_every_rejected_response_is_logged_d1_only(config, monkeypatch, tmp_path, capsys):
    long_prose = "The layout is unclear. " * 60            # > 500 chars, no object
    live, prompts = _live(config, monkeypatch, [long_prose, "", "never sent"])
    runtime = tmp_path / "state" / "layout_profiles"
    doc, _wb = resolve_workbook(PAIR_1, config, provider=live, use_cache=False,
                                runtime_cache_dir=runtime)
    assert len(prompts) == 2                                 # first + one retry, no more
    reasons = [r.reason for r in doc.rejections if r.reason.startswith("model:")]
    assert reasons == ["model: no JSON profile after 2 attempt(s); last error: empty response"]

    err = capsys.readouterr().err
    raw_lines = [x for x in err.splitlines() if x.startswith("RAW (D1 only)")]
    assert len(raw_lines) == 2
    assert repr(long_prose[:RAW_LOG_CHARS]) in raw_lines[0]
    assert long_prose[:RAW_LOG_CHARS + 1] not in err          # first 500 chars only

    logged = list((runtime / "rejections").glob("*.raw.json"))
    assert len(logged) == 1
    payload = json.loads(logged[0].read_text(encoding="utf-8"))
    assert payload["responses"] == [long_prose[:RAW_LOG_CHARS], ""]
    assert payload["document"] == "sttm" and payload["chars"] == RAW_LOG_CHARS


def test_the_error_carries_the_raw_responses(config, monkeypatch):
    live, _prompts = _live(config, monkeypatch, ["nope", "still nope"])
    with pytest.raises(LayoutProviderError) as caught:
        live.complete_layout({"fingerprint": "abc"})
    assert caught.value.raw == ["nope", "still nope"]
    assert "no JSON profile after 2 attempt(s)" in str(caught.value)
