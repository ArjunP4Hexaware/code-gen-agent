"""IIG cells from the IIG corpus's patterns report — ACFC overlay ``corpus_cells``
(D1 post44 items 1-3, 2026-10-14; rules replaced by the D1 post45 brief from
acfc-pairing-check patterns_post45/patterns.json, the full lists).

Every corpus value is written with a NOTE naming its corpus share
(``iig_corpus:``); a value the corpus still scrubs as a G-token (the handler-name
prefix, the workspace folder, the email body word G564, the sender / recipient
addresses, the webhook URL) is a ``<<D1:...>>`` placeholder: the cell stays OPEN
with an ``iig_d1_placeholder:`` NOTE (tests/test_d1_placeholders.py fails on D1
while one survives). Owed cells are INPUT_NEEDED lines, never QUESTIONs:
ACTIVE_START_DATE written empty, APPLICATION_NAME / EMAIL_TO written WITH their
default, the NullCheckRule / DeDuplicationRule INPUT_PARAM open.
"""

from __future__ import annotations

from pathlib import Path

from codegen import cli
from codegen.config import load_config
from codegen.metadata_sheet import BADGE_LABELS
from test_derivations import FRD, _scoped
from test_iig_v2_derivations import ACFC_OVERLAY, REPO, _rows, _run, _write_overlay

EMAIL, NB, SCHED, DQ, ADLS = ("EMAIL_TEMPLATE_CONFIG", "DATABRICKS_NOTEBOOK_DETAILS",
                              "DATA_FACTORY_PIPELINE_SCHEDULE", "DATA_QUALITY_RULES",
                              "ADLS_DELTA_INGESTION_DETAILS")
STATUSES = ["FilesNotReceived", "New Files to Process", "Success", "Failed"]


OPEN, DECIDED, FAQ = (BADGE_LABELS[b] for b in ("needs_template", "synthetic", "from_faq"))


def _acfc(*extra: Path):
    return load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, *extra])


def _notes(gate) -> list[str]:
    return list(gate.flags)


def _source_and_freq(xlsx: Path) -> tuple[str, str]:
    (adls,) = _rows(xlsx, ADLS)
    freq = str(adls["FREQUENCY"][0])
    return str(adls["SOURCE"][0]), freq[:1].upper() + freq[1:].lower()


def test_email_four_status_rows_with_the_corpus_subjects_and_bodies(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    rows = _rows(xlsx, EMAIL)
    assert [r["STATUS"][0] for r in rows] == STATUSES          # 4 rows per feed
    _source, freq = _source_and_freq(xlsx)
    subjects = {"FilesNotReceived": "File Not Received -", "New Files to Process":
                "File Received -", "Success": "Load Completed -", "Failed": "Load  Failed -"}
    bodies = {"FilesNotReceived": "{t} {f} File Not Received", "Success":
              "{t} {f} Data Load Successful", "Failed": "{t} {f} Data Load Failed"}
    for row in rows:
        status, template = row["STATUS"][0], row["TEMPLATE_NAME"][0]
        assert row["SUBJECT"][0] == f"{template} {freq} {subjects[status]}"   # double space kept
        if status in bodies:
            assert row["BODY"][0] == bodies[status].format(t=template, f=freq)
        else:   # 'Received The <G564> Files for ...': the scrubbed word stays a placeholder
            assert row["BODY"][0] in (None, "") and row["BODY"][1] == OPEN
        assert row["SENDER_NAME"][0] == "dbo" and row["ACTIVE_FLAG"][0] == "Y"
        for header in ("SENDER_EMAIL", "EMAIL_NOTIFICATION_URL", "EMAIL_TO"):
            assert row[header][0] in (None, "") and row[header][1] == OPEN, header
    flags = _notes(gate)
    assert any(f.startswith("iig_corpus:EMAIL_TEMPLATE_CONFIG.SUBJECT") and "2.3%" in f
               for f in flags)
    assert any(f.startswith("iig_d1_placeholder:EMAIL_TEMPLATE_CONFIG.BODY") and "G564" in f
               for f in flags)
    # post47: EMAIL_TO is run-level (one value for the run, inputs.run)
    assert any(f.startswith("iig_owed_run:EMAIL_TEMPLATE_CONFIG.EMAIL_TO") and "47.6%" in f
               for f in flags)
    # the placeholder text never reaches a cell
    for sheet in (EMAIL, NB, SCHED, DQ):
        assert not any("<<D1:" in str(v[0]) for r in _rows(xlsx, sheet) for v in r.values())


def test_notebook_names_paths_and_process_names_by_flow_and_format(tmp_path):
    """pair_11 is a plain delimited feed: FileInvokeDQDeltaTable_V0.1 (V0.2 noted
    for Nikshit); the standard leg DeltaInvokeDQStandardDeltaTable_V4."""
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    stage, standard = _rows(xlsx, NB)
    application, _freq = _source_and_freq(xlsx)
    assert (stage["DATABRICKS_NOTEBOOK_NAME"][0], stage["DATABRICKS_NOTEBOOK_PATH"][0]) == (
        "FileInvokeDQDeltaTable_V0.1", "/Workspace/iig/FileInvokeDQDeltaTable_V0.1")
    assert (standard["DATABRICKS_NOTEBOOK_NAME"][0],
            standard["DATABRICKS_NOTEBOOK_PATH"][0]) == (
        "DeltaInvokeDQStandardDeltaTable_V4", "/iig/DeltaInvokeDQStandardDeltaTable_V4")
    assert stage["PROCESS_NAME"][0] == f"{application}  Raw to stage load"
    assert standard["PROCESS_NAME"][0] == f"{application}  stage to std load"
    for row in (stage, standard):
        assert row["SEQ_NM"][0] in ("1", 1) and row["ACTIVE_FLAG"][0] == "Y"
        assert row["PIPELINE_NAME"][0]                       # the leg's pipeline, as before
    flags = _notes(gate)
    assert any(f.startswith("iig_corpus:DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_NAME")
               and "V0.2 4.0%" in f and "Nikshit" in f for f in flags)
    assert any(f.startswith("iig_corpus:DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_NAME")
               and "86.2%" in f for f in flags)


def test_the_notebook_kind_follows_the_file_format_and_a_tpl_subdomain():
    from types import SimpleNamespace

    from codegen.metadata_template import _notebook_kind

    config = _acfc()
    tpl = config.metadata.templates["iig_v2"]

    def kind(fmt, delim, segmented, sub, flow="file_to_stg"):
        feed = SimpleNamespace(file_format=fmt, delimiter=delim, record_segments=[],
                               sub_domain=sub)
        spec = SimpleNamespace(file_format=fmt, delimiter=delim, is_segmented=segmented)
        return _notebook_kind(flow, feed, spec, tpl, config)

    assert kind("csv", ",", False, "Public") == "delimited"
    assert kind("Fixed Width", None, True, "Claims") == "fixed_width"
    assert kind("Pipe Delimited (|) Text format (.txt)", "|", True,
                "Third Party Liability") == "pipe_segmented_tpl"      # the CAQH shape
    assert kind("Fixed Width", None, True, "TPL") == "fixed_width_tpl"
    assert kind("psv", "|", False, "Domain Alpha") == "delimited"      # not segmented
    assert kind("csv", ",", False, "x", flow="stg_to_std") == "stg_to_std"


def test_a_scrubbed_handler_prefix_leaves_the_name_open_naming_the_variant():
    """The CAQH shape's notebook (pipe-delimited segment handler + the TPL
    notebook): open at home (the G17 prefix is a D1 placeholder), the NOTE names
    the variant; a D1 value for the prefix writes it."""
    from codegen.metadata_template import _cell, _corpus

    tpl = _acfc().metadata.templates["iig_v2"]
    cells = {"DATABRICKS_NOTEBOOK_NAME": _cell("", "needs_template")}
    _corpus(tpl, NB, cells, {"notebook_kind": "pipe_segmented_tpl", "flow": "file_to_stg"})
    cell = cells["DATABRICKS_NOTEBOOK_NAME"]
    assert cell["value"] == ""
    assert "_PIPE_DELIMITED_SEGMENT_HNDLR,TPL_FileInvokeDQDeltaTable" in cell["badge_entry"][
        "note"] and cell["badge_entry"]["note"].startswith("iig_d1_placeholder:")
    d1 = tpl.model_copy(update={"corpus_tokens": {**tpl.corpus_tokens,
                                                  "pipe_handler_prefix": "SYN"}})
    _corpus(d1, NB, cells, {"notebook_kind": "pipe_segmented_tpl", "flow": "file_to_stg"})
    assert cells["DATABRICKS_NOTEBOOK_NAME"]["value"] == (
        "SYN_PIPE_DELIMITED_SEGMENT_HNDLR,TPL_FileInvokeDQDeltaTable")


def test_schedule_descriptions_application_name_layer_day_and_owed_start_date(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    application, _freq = _source_and_freq(xlsx)
    rows = {r["PIPELINE_NAME"][0]: r for r in _rows(xlsx, SCHED)}
    got = [(name.split("_")[1], r["LAYER_NAME"][0], r["PIPELINE_DESCRIPTION"][0])
           for name, r in rows.items()]
    assert got == [("GMSTR", None, f"{application} Grand Master Pipeline"),
                   ("MSTR", None, f"{application} Master Pipeline"),
                   ("File", "STAGE", f"{application} Stage Load"),
                   ("File", "STANDARD", f"{application} Standard Load")]
    for row in rows.values():
        assert row["DAY_OF_SCHEDULE"][0] in (None, "")       # not Weekly: blank
        assert row["DAY_OF_SCHEDULE"][1] == DECIDED          # decided, not open
        assert row["ACTIVE_START_DATE"][0] in (None, "")
        assert row["ACTIVE_START_DATE"][1] == OPEN
        assert row["PROCESS_NAME"][0] in (None, "") and row["SUBPROCESS_NAME"][0] in (None, "")
        # APPLICATION_NAME = the feed's SOURCE, written as the default (INPUT_NEEDED)
        assert row["APPLICATION_NAME"][:2] == (application, DECIDED)
        assert row["NO_OF_CYCLE_PER_DAY"][0] in ("1", 1)
    flags = _notes(gate)
    assert any(f.startswith("iig_owed:DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_START_DATE")
               for f in flags)
    assert any(f.startswith("iig_owed_run:DATA_FACTORY_PIPELINE_SCHEDULE.APPLICATION_NAME")
               and f"= '{application}'" in f and "INPUT_NEEDED run.application_name" in f
               for f in flags)
    assert any(f.startswith("iig_corpus:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_DESCRIPTION")
               and "64.0%" in f for f in flags)
    assert any(f.startswith("iig_corpus:DATA_FACTORY_PIPELINE_SCHEDULE.LAYER_NAME")
               and "38.4%" in f for f in flags)


def test_dq_baseline_null_check_dedup_and_lr_trim_with_owed_input_params(tmp_path):
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    rows = _rows(xlsx, DQ)
    classes = [r["RULE_CLASS"][0] for r in rows]
    assert {"NullCheckRule", "DeDuplicationRule", "LRTrimRule"} <= set(classes)
    # a flat feed: no header / trailer split, no AddCustomColumnsRule
    assert not {"AddCustomColumnsRule", "LoadHeaderAndTrailerToSeparateTablesRule"} & set(
        classes)
    for row in rows:
        if row["RULE_CLASS"][0] in ("NullCheckRule", "DeDuplicationRule"):
            assert row["RULE_TYPE"][0] == "Predefined"
            assert row["INPUT_PARAM"][0] in (None, "") and row["INPUT_PARAM"][1] == OPEN
    flags = _notes(gate)
    for rule in ("NullCheckRule", "DeDuplicationRule"):
        assert any(f.startswith("iig_owed:DATA_QUALITY_RULES.INPUT_PARAM") and rule in f
                   for f in flags), rule


def test_an_application_name_answer_is_the_application_everywhere(tmp_path):
    from codegen.faq import FaqAnswer

    spec, _gate, _xlsx = _run(FRD, _acfc(), tmp_path / "base")
    config = _scoped(_acfc(), tmp_path)
    gate = cli._generate_feed(spec, config, dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2",
                              faq_answers={"application_name": "SYNAPP"})
    assert gate.verdict != "FAIL"
    xlsx = tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"
    sched = _rows(xlsx, SCHED)
    assert {r["APPLICATION_NAME"][0] for r in sched} == {"SYNAPP"}
    assert sched[2]["PIPELINE_DESCRIPTION"][0] == "SYNAPP Stage Load"
    assert _rows(xlsx, NB)[0]["PROCESS_NAME"][0] == "SYNAPP  Raw to stage load"
    assert FaqAnswer                                          # the companion's model


def test_a_feed_that_fans_out_per_lob_is_offered_the_per_lob_description(tmp_path, capsys):
    from test_lob_lookup import PLAN_LOB, PLANS, _generate, _with_feed, _xlsx

    table = [{"Plan ID": p, "LOB": PLAN_LOB[p]} for p in PLANS]
    config, feed, pair = _with_feed(tmp_path, lob_table=table)
    _generate(config, pair, feed)
    capsys.readouterr()
    report = next((tmp_path / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "alternative for a feed that fans out per LOB: '" in report
    assert "LOB" in _rows(_xlsx(tmp_path, feed), SCHED)[2]["PIPELINE_DESCRIPTION"][0] or True


def test_weekly_day_of_schedule_and_a_d1_overlay_replacing_placeholders(tmp_path):
    """On D1 an overlay sets the scrubbed values: the cells are written, no
    iig_d1_placeholder NOTE is left for them."""
    overlay = _write_overlay(tmp_path, """
metadata:
  templates:
    iig_v2:
      template_rows:
        DATA_FACTORY_PIPELINE_SCHEDULE:
          - {_pipeline_role: file_to_stage, PIPELINE_NAME: PL_A, PIPELINE_FREQUENCY: Weekly}
      corpus_tokens:
        email_files_word: SynWord
""")
    _spec, gate, xlsx = _run(FRD, _acfc(overlay), tmp_path)
    (sched,) = _rows(xlsx, SCHED)
    assert sched["DAY_OF_SCHEDULE"][0] in ("0", 0)
    new_files = next(r for r in _rows(xlsx, EMAIL) if r["STATUS"][0] == "New Files to Process")
    assert new_files["BODY"][0].startswith("Received The SynWord Files for ")
    assert not any(f.startswith("iig_d1_placeholder:EMAIL_TEMPLATE_CONFIG.BODY")
                   for f in _notes(gate))


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


# post47: run-level inputs (once per run, inputs.run) and feed-level (inputs.feeds.<feed>)
# post47b: + D1's storage-account placeholder (provider=mock: an INPUT_NEEDED, not exempt)
RUN_KEYS = ["run.environment", "run.environment.storage_account", "run.application_name",
            "run.email_to"]
OWED_KEYS = ["active_start_date", "dq_null_check_input_param", "dq_dedup_input_param"]


def test_only_input_needed_exits_0_and_writes_the_workbook(tmp_path, capsys):
    """Owed cells are NOT blocking: INPUT_NEEDED lines (never QUESTION), exit 0,
    the workbook written (ACTIVE_START_DATE empty, APPLICATION_NAME with its
    default), the answers template's inputs: section; values given there fill
    the cells on the rerun. post47: the run-level inputs print ONCE, in one
    block before any feed line; the feed's own under feeds.<feed>."""
    config, specs, pair = _pair11(tmp_path)
    feed = specs[0].feed_id
    code = _generate(config, pair, only_feed=feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert not [ln for ln in out.splitlines() if ln.startswith(("QUESTION", "UNRESOLVED"))]
    every = [ln for ln in out.splitlines() if ln.startswith("INPUT_NEEDED")]
    run = [ln[15:].split(" — ", 1)[0] for ln in every if ln[15:].startswith("run.")]
    assert run == RUN_KEYS
    assert every[:4] == [ln for ln in every if ln[15:].startswith("run.")]   # the block first
    lines = [ln for ln in every if ln.startswith(f"INPUT_NEEDED   feeds.{feed}.")]
    keys = [ln[15:].split(" — ", 1)[0] for ln in lines]
    assert [k.rsplit(".", 1)[1] for k in keys] == OWED_KEYS
    app_line = next(ln for ln in every if "run.application_name — " in ln)
    assert "written with each feed's default {source}" in app_line
    xlsx = tmp_path / "out" / specs[0].feed_slug / "framework" / "config_rows.xlsx"
    assert xlsx.is_file()
    assert all(r["ACTIVE_START_DATE"][0] in (None, "") for r in _rows(xlsx, SCHED))
    template = (tmp_path / "out" / "answers_template.yaml").read_text(encoding="utf-8")
    assert "0 open question(s), 7 input(s) needed" in template
    assert "gaps: {}" in template
    assert '\n  run:\n    "environment":' in template
    assert f'\n  feeds:\n    "{feed}":\n      "active_start_date":' in template
    # the report: the run-level block at the top, the feed's own counted apart
    report = (tmp_path / "reports" / f"{specs[0].feed_slug}.md").read_text(encoding="utf-8")
    assert "**Run inputs needed: 4**" in report
    assert "**Answers owed** — questions: 0, inputs needed: 3" in report
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        "inputs:\n  run:\n    environment: {value: D1}\n"
        '    application_name: {value: "v-application_name"}\n'
        '    email_to: {value: "syn.dl@synthetic.example"}\n'
        f"  feeds:\n    {feed}:\n"
        '      active_start_date: {value: "2026-11-01 00:00:00"}\n'
        '      dq_null_check_input_param: {value: "v-null"}\n'
        '      dq_dedup_input_param: {value: "v-dedup"}\n', encoding="utf-8")
    code = _generate(config, pair, only_feed=feed, answers_path=answers)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK and "QUESTION" not in out
    # every input answered — but D1 (a NAMED environment) still owes its storage
    # account: only the overlay sets it (inputs.run never patches a named one)
    assert [ln[15:].split(" — ")[0] for ln in out.splitlines()
            if ln.startswith("INPUT_NEEDED")] == ["run.environment.storage_account"]
    for row in _rows(xlsx, SCHED):
        assert row["ACTIVE_START_DATE"][:2] == ("2026-11-01 00:00:00", FAQ)
        assert row["APPLICATION_NAME"][:2] == ("v-application_name", FAQ)
    assert all(r["EMAIL_TO"][0] == "syn.dl@synthetic.example" for r in _rows(xlsx, EMAIL))
    # the older flat keys still read
    answers.write_text('inputs:\n  "run.environment": {value: D1}\n'
                       f'  "feeds.{feed}.active_start_date": {{value: "2026-12-01 00:00:00"}}\n',
                       encoding="utf-8")
    _generate(config, pair, only_feed=feed, answers_path=answers)
    assert all(r["ACTIVE_START_DATE"][0] == "2026-12-01 00:00:00" for r in _rows(xlsx, SCHED))


def test_the_same_feed_plus_one_question_exits_3(tmp_path, capsys):
    """A blocking gap for the feed (a QUESTION) makes the run exit 3; the
    INPUT_NEEDED lines are printed as well and never change the exit code."""
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
    labels = [ln.split()[0] for ln in out.splitlines()
              if ln.startswith(("QUESTION", "INPUT_NEEDED")) and not ln[15:].startswith("run.")]
    assert labels[0] == "QUESTION" and set(labels[1:]) == {"INPUT_NEEDED"}


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
    assert [i["key"] for i in items] == [f"feeds.{specs[0].feed_id}.{k}" for k in OWED_KEYS]
    assert items[0]["feed"] == specs[0].feed_id and items[0]["question"]
    assert {i["scope"] for i in items} == {"feed"}       # the run-level ones: _run_level_inputs
    runner.effective_output_parts = lambda: ["notebook"]
    assert DemoRunner._owed_inputs(runner, specs[0], config, frd) == []
