"""post61: two kinds of default (codegen.input_choices).

- profile_default: the value comes from the conventions profile or the ACFC
  overlay (the email status set, EMAIL_TO, the notebook names, the
  SRC_FILE_NAME style) — applied when unanswered, CODEGEN_STAGES.json source
  ``profile``, no gate flag, no open INPUT_NEEDED line, still listed (a NOTE
  line, the answers template, the App's panel) as changeable;
- agent_proposal: the value is rendered or derived by the agent (the
  PIPELINE_NAME template, APPLICATION_NAME from {source}, ACTIVE_START_DATE) —
  shown, never applied without confirmation.

The email status set goes back to the overlay's default when unanswered: an
overlay saying [Success, Failed] and no answer writes two rows. Synthetic
fixtures only."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import yaml

from codegen import cli, input_choices, run_stages
from codegen.layout.answers import AnswersFileError, load_answers
from codegen.owed_inputs import OwedInput
from test_iig_corpus_cells import ADLS, EMAIL, NB, OPEN, SCHED, _generate
from test_iig_v2_derivations import _rows, _write_overlay
from test_pipeline_name_choice import _answers, _feed_inputs, _pair, _report

TWO = """\
metadata:
  templates:
    iig_v2:
      email_status_default: [Success, Failed]
"""


def _xlsx(tmp_path, spec):
    return tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"


def _open_keys(tmp_path) -> list[str]:
    return [q["key"] for q in run_stages.read_stage_manifest(tmp_path / "out")["questions"]]


def test_the_overlay_status_set_is_written_when_unanswered(tmp_path, capsys):
    """THE brief's test: overlay [Success, Failed], no answer -> two rows,
    source profile, no gate flag, not an open input, still changeable."""
    config, spec, pair = _pair(tmp_path, _write_overlay(tmp_path, TWO))
    assert _generate(config, pair, only_feed=spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert [r["STATUS"][0] for r in _rows(_xlsx(tmp_path, spec), EMAIL)] == ["Success", "Failed"]
    record = _feed_inputs(tmp_path)["email_statuses"]
    assert (record["kind"], record["source"], record["chosen"]) == (
        "profile_default", "profile", False)
    assert record["proposed"] == "Success, Failed"
    # no gate flag: no NOTE on the STATUS cells, nothing "taken from other documents"
    report = _report(tmp_path, spec)
    assert "EMAIL_TEMPLATE_CONFIG.STATUS" not in report
    assert "frd_unstated:EMAIL_TEMPLATE_CONFIG" not in report
    # not open: no INPUT_NEEDED line, not in the manifest's questions ...
    assert "run.email_statuses" not in _open_keys(tmp_path)
    assert not [ln for ln in out.splitlines()
                if ln.startswith("INPUT_NEEDED") and "run.email_statuses" in ln]
    # ... but shown as changeable: a NOTE line and the answers template
    note = next(ln for ln in out.splitlines() if ln.startswith("NOTE           run.email_"
                                                                "statuses — "))
    assert "profile default applied: Success, Failed (Success, Failed (email_status_default))" \
        in note and "inputs.run" in note
    template = yaml.safe_load((tmp_path / "out" / "answers_template.yaml")
                              .read_text(encoding="utf-8"))
    entry = template["inputs"]["run"]["email_statuses"]
    assert entry["choice"] == "" and entry["applied"] == "Success, Failed"


def test_agent_proposals_stay_blank_in_the_same_run(tmp_path, capsys):
    """PIPELINE_NAME and APPLICATION_NAME are agent proposals: blank, open,
    kind agent_proposal — beside the profile default written above."""
    config, spec, pair = _pair(tmp_path, _write_overlay(tmp_path, TWO))
    _generate(config, pair, only_feed=spec.feed_id)
    capsys.readouterr()
    for row in _rows(_xlsx(tmp_path, spec), SCHED):
        assert row["PIPELINE_NAME"][:2] == (None, OPEN)
        assert row["APPLICATION_NAME"][0] in (None, "")
    records = _feed_inputs(tmp_path)
    assert records["application_name"]["kind"] == "agent_proposal"
    assert records["application_name"]["source"] == "blank"
    assert records["pipeline_name.master"]["kind"] == "agent_proposal"
    keys = _open_keys(tmp_path)
    assert "run.application_name" in keys
    assert f"feeds.{spec.feed_id}.pipeline_name.master" in keys
    assert f"feeds.{spec.feed_id}.active_start_date" in keys      # no default at all


def test_a_literal_overlay_default_is_a_profile_default(tmp_path, capsys):
    """EMAIL_TO: the overlay's value is written unanswered (no NOTE, no flag)."""
    overlay = _write_overlay(tmp_path, """\
metadata:
  templates:
    iig_v2:
      owed_cells:
        EMAIL_TEMPLATE_CONFIG:
          EMAIL_TO: {default: "syn.dl@synthetic.example"}
""")
    config, spec, pair = _pair(tmp_path, overlay)
    assert _generate(config, pair, only_feed=spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert {r["EMAIL_TO"][0] for r in _rows(_xlsx(tmp_path, spec), EMAIL)} == {
        "syn.dl@synthetic.example"}
    record = _feed_inputs(tmp_path)["email_to"]
    assert (record["kind"], record["source"]) == ("profile_default", "profile")
    assert "run.email_to" not in _open_keys(tmp_path)
    assert any(ln.startswith("NOTE           run.email_to — ") for ln in out.splitlines())
    assert "EMAIL_TEMPLATE_CONFIG.EMAIL_TO" not in _report(tmp_path, spec)


def test_the_notebook_names_and_the_file_name_style_are_profile_defaults(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path)
    _generate(config, pair, only_feed=spec.feed_id)
    out = capsys.readouterr().out
    records = _feed_inputs(tmp_path)
    names = [r["DATABRICKS_NOTEBOOK_NAME"][0] for r in _rows(_xlsx(tmp_path, spec), NB)]
    for leg, name in zip(("file_to_stg", "stg_to_std"), names, strict=True):
        record = records[f"notebook_name.{leg}"]
        assert (record["kind"], record["source"], record["proposed"]) == (
            "profile_default", "profile", name)
        assert any(ln.startswith(f"NOTE           feeds.{spec.feed_id}.notebook_name.{leg} — ")
                   for ln in out.splitlines())
    style = records["src_file_name_style"]
    assert (style["kind"], style["source"]) == ("profile_default", "profile")
    assert style["proposed"] in input_choices.STYLES
    assert not [k for k in _open_keys(tmp_path) if "notebook_name" in k or "style" in k]


def test_a_profile_default_is_changeable(tmp_path, capsys):
    """naming_standard replaces a profile default with the BSA's value; the
    status set without leave_blank."""
    config, spec, pair = _pair(tmp_path, _write_overlay(tmp_path, TWO))
    answers = _answers(tmp_path, (
        "inputs:\n  run:\n    email_statuses: {choice: naming_standard, standard: Failed}\n"
        f"  feeds:\n    {spec.feed_id}:\n"
        "      notebook_name.stg_to_std: {choice: naming_standard, standard: SYN_MyStd_V1}\n"
        "      notebook_name.file_to_stg: {choice: leave_blank}\n"
        "      src_file_name_style: {choice: naming_standard, standard: prefix_middle}\n"))
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    capsys.readouterr()
    xlsx = _xlsx(tmp_path, spec)
    assert [r["STATUS"][0] for r in _rows(xlsx, EMAIL)] == ["Failed"]
    assert [r["DATABRICKS_NOTEBOOK_NAME"][0] for r in _rows(xlsx, NB)] == [None, "SYN_MyStd_V1"]
    for row in _rows(xlsx, ADLS):
        assert str(row["SRC_FILE_NAME"][0]).startswith("*")
    records = _feed_inputs(tmp_path)
    assert records["email_statuses"]["source"] == "standard"
    assert records["notebook_name.stg_to_std"]["source"] == "standard"
    assert records["notebook_name.file_to_stg"]["source"] == "blank"
    assert records["src_file_name_style"]["chosen"] is True


def test_the_style_takes_only_a_style(tmp_path):
    for entry, problem in (("{choice: leave_blank}", "cannot be left blank"),
                           ("{choice: naming_standard, standard: wild}", "must be one of")):
        path = _answers(tmp_path, f"inputs:\n  feeds:\n    syn_f:\n      src_file_name_style: "
                                  f"{entry}\n")
        with pytest.raises(AnswersFileError, match=problem):
            load_answers(path)


@pytest.mark.parametrize(("default", "kind", "expected"), [
    ("{source}", None, "agent_proposal"),
    ("syn.dl@synthetic.example", None, "profile_default"),
    ("{source}", "profile_default", "profile_default"),
    ("all four", "agent_proposal", "agent_proposal"),
])
def test_the_kind_of_an_owed_default(default, kind, expected):
    rule = SimpleNamespace(default=default, default_kind=kind)
    assert input_choices.default_kind(rule) == expected


def test_the_panel_item_carries_its_kind_and_applied_value():
    item = OwedInput("run.email_statuses", "q", "", "run", options=("use_default",),
                     proposed="Success, Failed", template="t", kind="profile_default",
                     applied="Success, Failed")
    assert not item.is_open
    assert item.as_dict()["kind"] == "profile_default"
    assert item.as_dict()["applied"] == "Success, Failed"
    assert OwedInput("run.x", "q", "", "run").is_open
