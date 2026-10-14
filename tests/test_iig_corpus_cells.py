"""D1 post44 items 1-3 (2026-10-14): EMAIL_TEMPLATE_CONFIG, DATABRICKS_NOTEBOOK_DETAILS
and DATA_FACTORY_PIPELINE_SCHEDULE cells from the 199-IIG corpus's patterns report
(acfc-pairing-check patterns_post44/patterns.json) — ACFC overlay ``corpus_cells``.

Only values patterns.json states are written, each with a NOTE naming its corpus
share (``iig_corpus:``); a value it does not carry is a ``<<D1:...>>`` placeholder:
the cell stays OPEN with an ``iig_d1_placeholder:`` NOTE and the placeholder never
reaches a cell (tests/test_d1_placeholders.py fails on D1 while one survives). An
overlay on D1 replaces them (simulated here). ACTIVE_START_DATE is owed: generate
prints a QUESTION and writes the answers template; ``generate --answers`` fills it.
"""

from __future__ import annotations

from pathlib import Path

from codegen import cli
from codegen.config import load_config
from codegen.metadata_sheet import BADGE_LABELS
from test_derivations import FRD, _scoped
from test_iig_v2_derivations import ACFC_OVERLAY, REPO, _rows, _run, _write_overlay

EMAIL, NB, SCHED = ("EMAIL_TEMPLATE_CONFIG", "DATABRICKS_NOTEBOOK_DETAILS",
                    "DATA_FACTORY_PIPELINE_SCHEDULE")


OPEN, DECIDED, FAQ = (BADGE_LABELS[b] for b in ("needs_template", "synthetic", "from_faq"))


def _acfc(*extra: Path):
    return load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, *extra])


def _notes(gate) -> list[str]:
    return list(gate.flags)


def test_email_one_row_per_status_constants_with_shares_placeholders_open(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    rows = _rows(xlsx, EMAIL)
    assert len(rows) == 4                                   # 4 statuses per feed (pair_2)
    assert [r["STATUS"][0] for r in rows[:2]] == ["Success", "Failed"]
    assert all(r["STATUS"][0] in (None, "") and r["STATUS"][1] == OPEN
               for r in rows[2:])                           # TODO D1: the other two statuses
    for row in rows:
        assert row["SENDER_NAME"][0] == "dbo" and row["ACTIVE_FLAG"][0] == "Y"
        for header in ("SENDER_EMAIL", "EMAIL_TO", "EMAIL_NOTIFICATION_URL", "SUBJECT", "BODY"):
            assert row[header][0] in (None, "") and row[header][1] == OPEN, header
    flags = _notes(gate)
    assert any(f.startswith("iig_corpus:EMAIL_TEMPLATE_CONFIG.SENDER_NAME") and "97.8%" in f
               for f in flags)
    assert any(f.startswith("iig_d1_placeholder:EMAIL_TEMPLATE_CONFIG.EMAIL_TO") and "47.6%" in f
               for f in flags)
    assert any(f.startswith("iig_d1_placeholder:EMAIL_TEMPLATE_CONFIG.SUBJECT")
               and "status 'Success'" in f for f in flags)
    # the placeholder text never reaches a cell
    for sheet in (EMAIL, NB, SCHED):
        assert not any("<<D1:" in str(v[0]) for r in _rows(xlsx, sheet) for v in r.values())


def test_notebook_name_path_process_name_by_flow(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    rows = _rows(xlsx, NB)
    assert len(rows) == 2
    for row in rows:
        assert row["SEQ_NM"][0] in ("1", 1) and row["ACTIVE_FLAG"][0] == "Y"
        for header in ("DATABRICKS_NOTEBOOK_NAME", "DATABRICKS_NOTEBOOK_PATH", "PROCESS_NAME"):
            assert row[header][0] in (None, "") and row[header][1] == OPEN, header
        assert row["PIPELINE_NAME"][0]                       # the leg's pipeline, as before
    flags = _notes(gate)
    for flow in ("file_to_stg", "stg_to_std"):
        assert any(f.startswith("iig_d1_placeholder:DATABRICKS_NOTEBOOK_DETAILS."
                                "DATABRICKS_NOTEBOOK_NAME") and f"flow '{flow}'" in f
                   for f in flags)
    assert any(f.startswith("iig_corpus:DATABRICKS_NOTEBOOK_DETAILS.SEQ_NM") and "64.6%" in f
               for f in flags)


def test_schedule_layer_by_flow_day_by_frequency_owed_start_date(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    rows = {r["PIPELINE_NAME"][0]: r for r in _rows(xlsx, SCHED)}
    layers = [(name.split("_")[1], r["LAYER_NAME"][0]) for name, r in rows.items()]
    assert layers == [("GMSTR", None), ("MSTR", None), ("File", "STAGE"), ("File", "STANDARD")]
    for row in rows.values():
        assert row["DAY_OF_SCHEDULE"][0] in (None, "")       # not Weekly: blank
        assert row["DAY_OF_SCHEDULE"][1] == DECIDED          # decided, not open
        assert row["ACTIVE_START_DATE"][0] in (None, "")
        assert row["ACTIVE_START_DATE"][1] == OPEN
        assert row["PROCESS_NAME"][0] in (None, "") and row["SUBPROCESS_NAME"][0] in (None, "")
        assert row["APPLICATION_NAME"][1] == OPEN
        assert row["NO_OF_CYCLE_PER_DAY"][0] in ("1", 1)
    flags = _notes(gate)
    assert any(f.startswith("iig_owed:DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_START_DATE")
               for f in flags)
    assert any(f.startswith("iig_corpus:DATA_FACTORY_PIPELINE_SCHEDULE.LAYER_NAME")
               and "38.4%" in f for f in flags)


def test_weekly_day_of_schedule_and_a_d1_overlay_replacing_placeholders(tmp_path):
    """On D1 an overlay sets every placeholder: the cells are written, no
    iig_d1_placeholder NOTE is left (a shape may carry {source} / {feed})."""
    overlay = _write_overlay(tmp_path, """
metadata:
  templates:
    iig_v2:
      template_rows:
        DATA_FACTORY_PIPELINE_SCHEDULE:
          - {_pipeline_role: file_to_stage, PIPELINE_NAME: PL_A, PIPELINE_FREQUENCY: Weekly}
        DATABRICKS_NOTEBOOK_DETAILS:
          - {_layer: stage, _pipeline_role: file_to_stage}
        EMAIL_TEMPLATE_CONFIG:
          - {STATUS: Success}
      corpus_cells:
        DATABRICKS_NOTEBOOK_DETAILS:
          DATABRICKS_NOTEBOOK_NAME:
            by: flow
            values: {file_to_stg: SynFileNotebook_V1, stg_to_std: SynStdNotebook_V1}
            share: "synthetic D1 share"
          PROCESS_NAME:
            by: flow
            values: {file_to_stg: "{source} Raw to stage load"}
            share: "synthetic D1 share"
""")
    _spec, gate, xlsx = _run(FRD, _acfc(overlay), tmp_path)
    (nb,) = _rows(xlsx, NB)
    assert nb["DATABRICKS_NOTEBOOK_NAME"][0] == "SynFileNotebook_V1"
    assert nb["PROCESS_NAME"][0].endswith(" Raw to stage load")
    assert not any(f.startswith("iig_d1_placeholder:DATABRICKS_NOTEBOOK_DETAILS."
                                "DATABRICKS_NOTEBOOK_NAME") for f in _notes(gate))


def test_corpus_frequency_key_is_caseless_and_weekly_writes_the_dominant():
    from codegen.config import CorpusCellConfig, MetadataTemplateConfig
    from codegen.metadata_template import _cell, _corpus

    tpl = MetadataTemplateConfig(tabs={}, corpus_cells={SCHED: {"DAY_OF_SCHEDULE": CorpusCellConfig(
        by="frequency", values={"Weekly": "0"}, share="s")}})
    for frequency, value, badge in (("WEEKLY", "0", "synthetic"), ("Monthly", "", "synthetic")):
        cells = {"DAY_OF_SCHEDULE": _cell("0", "synthetic", "template constant")}
        _corpus(tpl, SCHED, cells, {"frequency": frequency})
        assert (cells["DAY_OF_SCHEDULE"]["value"], cells["DAY_OF_SCHEDULE"]["badge_entry"][
            "badge"]) == (value, badge)
    # an input-stated value is never replaced
    cells = {"DAY_OF_SCHEDULE": _cell("3", "from_faq", "FAQ")}
    _corpus(tpl, SCHED, cells, {"frequency": "Monthly"})
    assert cells["DAY_OF_SCHEDULE"]["value"] == "3"


def _pair11(tmp_path):
    from test_derivations import _pair11_specs

    config = _scoped(_acfc(), tmp_path)
    contracts = tmp_path / "contracts"
    contracts.mkdir()
    specs, _flags = _pair11_specs(FRD, contracts, config)
    return config, specs, (contracts / "frd.contract.json", contracts / "sttm.contract.json")


def _generate(config, pair, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True,
                          output_mode=["framework"], conventions_profile="acfc_prx",
                          iig_template="iig_v2", **kw)


def test_only_input_needed_exits_0_and_writes_the_workbook(tmp_path, capsys):
    """ACTIVE_START_DATE is owed but NOT blocking: INPUT_NEEDED (never QUESTION),
    exit 0, the workbook written with the cell empty, the answers template's
    inputs: section; a value given there fills the cell on the rerun."""
    config, specs, pair = _pair11(tmp_path)
    feed = specs[0].feed_id
    code = _generate(config, pair, only_feed=feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    lines = [ln for ln in out.splitlines() if ln.startswith(("QUESTION", "UNRESOLVED",
                                                              "INPUT_NEEDED"))]
    assert len(lines) == 1 and lines[0].startswith("INPUT_NEEDED   feeds[")
    key = lines[0][15:].split(" — ", 1)[0]
    assert key.endswith(".active_start_date")
    xlsx = tmp_path / "out" / specs[0].feed_slug / "framework" / "config_rows.xlsx"
    assert xlsx.is_file()
    assert all(r["ACTIVE_START_DATE"][0] in (None, "") for r in _rows(xlsx, SCHED))
    template = (tmp_path / "out" / "answers_template.yaml").read_text(encoding="utf-8")
    assert "0 open question(s), 1 input(s) needed" in template
    assert "gaps: {}" in template and f'inputs:\n  "{key}":' in template
    # the report counts them apart
    report = (tmp_path / "reports" / f"{specs[0].feed_slug}.md").read_text(encoding="utf-8")
    assert "**Answers owed** — questions: 0, inputs needed: 1" in report
    answers = tmp_path / "answers.yaml"
    answers.write_text(f'inputs:\n  "{key}": {{value: "2026-11-01 00:00:00"}}\n',
                       encoding="utf-8")
    code = _generate(config, pair, only_feed=feed, answers_path=answers)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK and "INPUT_NEEDED" not in out and "QUESTION" not in out
    for row in _rows(xlsx, SCHED):
        assert row["ACTIVE_START_DATE"][:2] == ("2026-11-01 00:00:00", FAQ)


def test_the_same_feed_plus_one_question_exits_3(tmp_path, capsys):
    """A blocking gap for the feed (a QUESTION) makes the run exit 3; the
    INPUT_NEEDED line is printed as well and never changes the exit code."""
    import json

    config, specs, (frd, sttm) = _pair11(tmp_path)
    feed = specs[0].feed_id
    index = json.loads(frd.read_text(encoding="utf-8"))["feeds"]
    from codegen.owed_inputs import frd_feed_index

    i = frd_feed_index(frd, feed, config)
    contract = json.loads(sttm.read_text(encoding="utf-8"))
    contract["needs_answers"] = [{"feed_name": index[i]["feed_name"], "sheet": "S1",
                                  "key": f"feeds[{i}].stage_target.schema",
                                  "reason": "no document states the stage schema"}]
    sttm.write_text(json.dumps(contract), encoding="utf-8")
    code = _generate(config, (frd, sttm), only_feed=feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_NEEDS_ANSWERS
    assert [ln.split()[0] for ln in out.splitlines()
            if ln.startswith(("QUESTION", "INPUT_NEEDED"))] == ["QUESTION", "INPUT_NEEDED"]


def test_the_harness_regex_never_reads_an_input_needed_line():
    """NEEDS_ANSWERS is triggered by QUESTION / UNRESOLVED lines only."""
    from codegen.owed_inputs import OwedInput, input_line
    from test_harness_answer_lines import _NEEDED_KEY_RE

    line = input_line(OwedInput("feeds[0].active_start_date", "the go-live date", "zq"))
    assert line.startswith("INPUT_NEEDED   feeds[0].active_start_date — ")
    assert _NEEDED_KEY_RE.match(line) is None


def test_the_app_lists_inputs_needed_as_a_banner_item(tmp_path):
    """The App's status.inputs_needed (a banner, never the needs_answers pause):
    one item per owed cell of each generated feed, keyed as the CLI keys it."""
    import pytest

    pytest.importorskip("fastapi")
    from types import SimpleNamespace

    from ui.backend.demo import DemoRunner

    config, specs, (frd, _sttm) = _pair11(tmp_path)
    runner = SimpleNamespace(effective_output_parts=lambda: ["framework"],
                             iig_template="iig_v2")
    items = DemoRunner._owed_inputs(runner, specs[0], config, frd)
    assert [i["key"].rsplit(".", 1)[1] for i in items] == ["active_start_date"]
    assert items[0]["feed"] == specs[0].feed_id and items[0]["question"]
    runner.effective_output_parts = lambda: ["notebook"]
    assert DemoRunner._owed_inputs(runner, specs[0], config, frd) == []
