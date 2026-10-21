"""The run's environment as an input (2026-10-14).

Container names, the storage account and other workspace-scoped values come from
the overlay's ``environments:`` block (D1, QA, PROD ...; exactly one marked
default), never silent constants. A run picks one: ``--environment <name>``,
``--environment-file <yaml>`` (custom), else the default — then an
``INPUT_NEEDED run.environment`` line records which one was assumed. Every cell
filled from the environment carries an ``iig_env:`` NOTE naming it; the report
header prints ``environment: D1 (default)`` / ``(selected)`` / ``(custom)``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli, run_stages
from codegen.config import load_config
from codegen.environments import (
    EnvironmentSelectionError,
    select_environment,
    with_environment,
)
from test_iig_corpus_cells import _acfc, _pair11
from test_iig_v2_derivations import ACFC_OVERLAY, REPO, _rows, _write_overlay

ADLS, STG = "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET"
QA = """
environments:
  QA:
    containers: {landing: syn-qa-landing, stage: syn-qa-stage, standard: syn-qa-std}
    storage_account: synqaacct
    catalog_map: {PR_DLK: syn_qa_dlk, PR_STD: syn_qa_std}
    default_catalog: {stage: syn_qa_dlk, standard: syn_qa_std}
    connection_ids: {src_adls: "17", metadata: "14", target: "12"}
"""
# the keys a containers-only custom environment leaves unset (never taken from D1)
CUSTOM_UNSET = ["catalog_map.PR_DLK", "catalog_map.PR_STD", "default_catalog.stage",
                "default_catalog.standard", "connection_ids.src_adls",
                "connection_ids.metadata", "connection_ids.target"]


@pytest.fixture(autouse=True)
def _overlay_blocks_only(no_environment_profiles):
    """These tests pin the overlay blocks alone (no profile file)."""


def _generate(config, pair, feed, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True,
                          output_mode=["framework"], conventions_profile="acfc_prx",
                          iig_template="iig_v2", only_feed=feed, **kw)


def _setup(tmp_path, overlay_text: str | None = None):
    config, specs, pair = _pair11(tmp_path)
    if overlay_text is not None:
        from test_derivations import _scoped

        config = _scoped(_acfc(_write_overlay(tmp_path, overlay_text)), tmp_path)
    return config, specs[0], pair


def _report(tmp_path, spec) -> str:
    return (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")


def _xlsx(tmp_path, spec) -> Path:
    return tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"


def test_the_overlay_moves_the_containers_into_d1_the_default():
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    assert [n for n, e in config.environments.items() if e.default] == ["D1"]
    assert {"A2", "PR"} <= set(config.environments)
    # 2026-10-15: the profile schema — the Oct 14 rule's required keys
    assert config.environment_schema.required == [
        "storage_account", "containers.landing", "containers.stage", "containers.standard"]
    tpl = config.metadata.templates["iig_v2"]
    # no container is a silent constant any more: they are environment cells
    for tab in (ADLS, STG):
        for header in ("SRC_CONTAINER_NAME", "TGT_CONTAINER_NAME"):
            assert header not in tpl.constants.get(tab, {}), (tab, header)
            assert header in tpl.environment_cells[tab], (tab, header)
    assert "{storage_account}" in tpl.dq_split_location


def test_a_default_run_uses_d1_and_says_so_with_an_input_needed_line(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path)
    code = _generate(config, pair, spec.feed_id)
    out = capsys.readouterr().out
    # 2026-10-15: D1's storage account is a placeholder — a REQUIRED value: one
    # QUESTION, exit 3 (NEEDS_ANSWERS); the workbook is still written, the cells open
    assert code == cli.EXIT_NEEDS_ANSWERS
    # post58: blocking in the manifest, the workbook marked written for the App
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["stages"]["generate"]["status"] == "NEEDS_ANSWERS"
    assert [q["key"] for q in manifest["questions"] if q["blocking"]] == [
        "run.environment.storage_account"]
    assert [f["written"] for f in manifest["feeds"]] == [True]
    banner = ("NOTE           run.environment — environment: D1 (1 required missing: "
              "storage_account, from overlay environments.D1; default)")
    assert banner in out.splitlines()
    (question,) = [ln for ln in out.splitlines() if ln.startswith("QUESTION")]
    assert question.startswith("QUESTION       run.environment.storage_account — environment "
                               "D1 (default, from overlay environments.D1) states no "
                               "storage_account (<<D1:STORAGE_ACCOUNT>>)")
    line = next(ln for ln in out.splitlines() if ln.startswith("INPUT_NEEDED   run.environment"))
    assert "assumed D1 (the default" in line
    d1 = config.environments["D1"]
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["SRC_CONTAINER_NAME"][0] == d1.containers["landing"]
    assert adls["TGT_CONTAINER_NAME"][0] == d1.containers["stage"]
    (stg,) = _rows(_xlsx(tmp_path, spec), STG)
    assert (stg["SRC_CONTAINER_NAME"][0], stg["TGT_CONTAINER_NAME"][0]) == (
        d1.containers["stage"], d1.containers["standard"])
    # post47: the catalogs and the connection ids are D1's too, each cell NOTEd
    assert (adls["SRC_ADLS_CONNECTION_ID"][0], adls["METADATA_CONNECTION_ID"][0],
            adls["TGT_CONNECTION_ID"][0]) == ("7", "4", "2")
    assert (stg["SRC_CATALOG_NAME"][0], stg["TGT_CATALOG_NAME"][0]) == ("d1_dlk", "d1_std")
    report = _report(tmp_path, spec)
    assert ("environment: D1 (1 required missing: storage_account, from overlay "
            "environments.D1; default)") in report
    assert (f"iig_env:{ADLS}.SRC_ADLS_CONNECTION_ID — '7' from environment D1 (default): "
            "connection_ids.src_adls") in report
    assert (f"iig_env:{STG}.SRC_CATALOG_NAME — the catalog from environment D1 (default): "
            "catalog_map PR_DLK → d1_dlk, PR_STD → d1_std") in report
    # post47: the run-level block at the top; the feed's own below it. 2026-10-15:
    # the required storage account is a run QUESTION (blocking), not an input
    # post61: the email status set is a profile default (written), not an input needed
    # post81: application_name is written by default — 2 run inputs (environment, EMAIL_TO)
    assert report.index("**Run questions: 1**") < report.index("**Run inputs needed: 2**")
    assert report.index("- `run.environment.storage_account`") < report.index(
        "**Run inputs needed: 2**")
    assert "- `run.email_statuses`" not in report
    for key in ("run.environment", "run.email_to"):
        assert f"- `{key}`" in report
    # post81: the pipeline names (shipped convention) and the start date are written
    assert "**Answers owed**" not in report
    assert (f"iig_env:{ADLS}.TGT_CONTAINER_NAME — '{d1.containers['stage']}' from environment "
            "D1 (default): containers.stage") in report
    # post47: answers_template.yaml groups them: inputs.run once, inputs.feeds.<feed>
    import yaml

    from codegen.layout.answers import load_answers

    path = tmp_path / "out" / "answers_template.yaml"
    inputs = yaml.safe_load(path.read_text(encoding="utf-8"))["inputs"]
    assert list(inputs["run"]) == ["environment.storage_account", "environment",
                                   "email_to", "application_name", "email_statuses"]
    assert list(inputs["feeds"]) == [spec.feed_id]
    assert list(inputs["feeds"][spec.feed_id]) == [
        *(f"pipeline_name.{flow}" for flow in ("grand_master", "master", "file_to_stg",
                                               "stg_to_std")),
        "active_start_date",
        # post61: the profile defaults written (listed so the BSA can change them)
        "notebook_name.file_to_stg", "notebook_name.stg_to_std", "src_file_name_style",
        "pipeline_name"]            # post59: one choice / standard for all four flows
    assert inputs["run"]["environment"]["candidates"] == ["D1", "A2", "PR"]
    assert load_answers(path).inputs == {}            # every value empty: nothing answered


def test_environment_qa_takes_the_qa_values(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path, QA)
    config = with_environment(config, select_environment(config, name="qa"))
    code = _generate(config, pair, spec.feed_id)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK and "INPUT_NEEDED   run.environment" not in out
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert (adls["SRC_CONTAINER_NAME"][0], adls["TGT_CONTAINER_NAME"][0]) == (
        "syn-qa-landing", "syn-qa-stage")
    (stg,) = _rows(_xlsx(tmp_path, spec), STG)
    assert stg["TGT_CONTAINER_NAME"][0] == "syn-qa-std"
    # post47: QA's catalogs and connection ids, never D1's
    assert (stg["SRC_CATALOG_NAME"][0], stg["TGT_CATALOG_NAME"][0]) == ("syn_qa_dlk",
                                                                        "syn_qa_std")
    assert adls["TGT_CONNECTION_ID"][0] == "12"
    ddl = "".join(p.read_text(encoding="utf-8")
                  for p in (tmp_path / "out" / spec.feed_slug).rglob("*DDL*.txt"))
    assert "syn_qa_dlk." in ddl and "d1_dlk" not in ddl
    report = _report(tmp_path, spec)
    assert "environment: QA (complete, from overlay environments.QA; selected)" in report
    assert "'syn-qa-stage' from environment QA (selected): containers.stage" in report


def test_the_cli_flags_select_and_load_a_custom_file(tmp_path):
    config, _spec, _pair = _setup(tmp_path)
    env_file = tmp_path / "env.yaml"
    env_file.write_text("name: SANDBOX\ncontainers: {landing: syn-sb-landing, stage: "
                        "syn-sb-stage, standard: syn-sb-std}\nstorage_account: synsbacct\n",
                        encoding="utf-8")
    env = select_environment(config, file=env_file)
    assert (env.name, env.source, env.entry.containers["stage"]) == ("SANDBOX", "custom",
                                                                      "syn-sb-stage")
    assert env.origin == f"--environment-file {env_file.as_posix()}"
    with pytest.raises(EnvironmentSelectionError, match="choices: D1, A2, PR"):
        select_environment(config, name="nowhere")
    parsed = cli._parser().parse_args(["generate", "--frd", "a", "--sttm", "b",
                                       "--environment", "QA"])
    assert parsed.environment == "QA"
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["generate", "--frd", "a", "--sttm", "b", "--environment",
                                  "QA", "--environment-file", "x.yaml"])


def test_a_custom_environment_file_fills_the_custom_values(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path)
    env_file = tmp_path / "env.yaml"
    env_file.write_text("SANDBOX:\n  containers: {landing: syn-sb-landing, stage: "
                        "syn-sb-stage, standard: syn-sb-std}\n  storage_account: synsbacct\n",
                        encoding="utf-8")
    config = with_environment(config, select_environment(config, file=env_file))
    code = _generate(config, pair, spec.feed_id)
    assert code == cli.EXIT_OK                          # the run proceeds, workbook written
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["TGT_CONTAINER_NAME"][0] == "syn-sb-stage"
    # post47: a custom environment inherits NOTHING from D1 — the keys it leaves out
    # stay unset: the cells that would use them are empty, one INPUT_NEEDED each
    assert all(adls[h][0] in (None, "") for h in (
        "SRC_ADLS_CONNECTION_ID", "METADATA_CONNECTION_ID", "TGT_CONNECTION_ID"))
    (stg,) = _rows(_xlsx(tmp_path, spec), STG)
    assert stg["SRC_CATALOG_NAME"][0] in (None, "") and stg["TGT_CATALOG_NAME"][0] in (None, "")
    assert "d1_dlk" not in str(stg) and "d1_dlk" not in str(adls)
    # 2026-10-14: the NullCheckRule / DeDuplicationRule INPUT_PARAM is the target FQN —
    # its catalog unset here: open (the catalog's own INPUT_NEEDED asks), no DQ input
    for row in _rows(_xlsx(tmp_path, spec), "DATA_QUALITY_RULES"):
        if row["RULE_CLASS"][0] in ("NullCheckRule", "DeDuplicationRule"):
            assert row["INPUT_PARAM"][0] in (None, "")
    report = _report(tmp_path, spec)
    assert (f"environment: SANDBOX (7 keys unset, from --environment-file "
            f"{(tmp_path / 'env.yaml').as_posix()}; custom)") in report
    out = capsys.readouterr().out
    assert "INPUT_NEEDED   run.environment — " not in out           # nothing assumed
    lines = [ln for ln in out.splitlines() if ln.startswith("INPUT_NEEDED   run.environment.")]
    assert [ln.split()[1] for ln in lines] == [f"run.environment.{k}" for k in CUSTOM_UNSET]
    assert all("never taken from a named environment" in ln for ln in lines)
    for key in CUSTOM_UNSET:
        assert f"- `run.environment.{key}`" in report
    template = (tmp_path / "out" / "answers_template.yaml").read_text(encoding="utf-8")
    assert '"environment.catalog_map.PR_DLK":' in template


def test_an_answers_file_input_selects_the_environment(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path, QA)
    answers = tmp_path / "answers.yaml"
    answers.write_text('inputs:\n  "run.environment": {value: QA}\n', encoding="utf-8")
    assert _generate(config, pair, spec.feed_id, answers_path=answers) == cli.EXIT_OK
    assert "INPUT_NEEDED   run.environment" not in capsys.readouterr().out
    assert "environment: QA (complete, from overlay environments.QA; selected)" in _report(
        tmp_path, spec)


A2_REQUIRED = ["storage_account", "containers.landing", "containers.stage",
               "containers.standard"]
A2_UNSET = ["catalog_map.PR_DLK", "catalog_map.PR_STD", "default_catalog.stage",
            "default_catalog.standard", "connection_ids.src_adls", "connection_ids.metadata",
            "connection_ids.target"]


def test_a_named_environment_with_placeholders_is_fatal_under_live(tmp_path, capsys,
                                                                    monkeypatch):
    """post47b: under provider=live the shipped A2 (placeholders) fails, naming
    every NON-required unset key (2026-10-15: the required ones are QUESTIONs in
    every mode); nothing is written. (--dry-run asks for the mock: not live.)"""
    config, spec, pair = _setup(tmp_path)
    with pytest.raises(EnvironmentSelectionError) as caught:
        select_environment(config, name="A2", live=True)
    message = str(caught.value)
    assert message.startswith("environment A2 is not complete — 7 key(s) unset: "
                              + ", ".join(A2_UNSET))
    assert "provider=live needs every key" in message
    # the run: provider=live, no --dry-run — FAIL before anything is resolved or
    # written (the environment is chosen first; no model is reached)
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")
    answers = tmp_path / "answers.yaml"
    answers.write_text("inputs:\n  run:\n    environment: {value: A2}\n", encoding="utf-8")
    code = cli._run_pairs([pair], config, dry_run=False, skip_tests=True,
                          output_mode=["framework"], conventions_profile="acfc_prx",
                          iig_template="iig_v2", only_feed=spec.feed_id, answers_path=answers)
    out = capsys.readouterr().out
    assert code == 1
    assert "FAIL            environment — environment A2 is not complete" in out
    assert not (tmp_path / "out").exists() or not any((tmp_path / "out").rglob("*.xlsx"))


def test_a_named_environment_with_placeholders_is_input_needed_under_mock(tmp_path, capsys):
    """post47b: under provider=mock the same A2 runs: one INPUT_NEEDED
    run.environment.<key> per unset key, the cells that use them empty — never
    a placeholder, never D1's value; the workbook is written. 2026-10-15: its
    required keys are QUESTIONs (exit 3)."""
    config, spec, pair = _setup(tmp_path)
    env = select_environment(config, name="A2")                  # mock: no failure
    assert env.name == "A2" and env.source == "selected"
    config = with_environment(config, env)
    assert _generate(config, pair, spec.feed_id) == cli.EXIT_NEEDS_ANSWERS
    out = capsys.readouterr().out
    questions = [ln.split()[1] for ln in out.splitlines() if ln.startswith("QUESTION")]
    assert questions == [f"run.environment.{k}" for k in A2_REQUIRED]
    lines = [ln for ln in out.splitlines() if ln.startswith("INPUT_NEEDED   run.environment.")]
    assert [ln.split()[1] for ln in lines] == [f"run.environment.{k}" for k in A2_UNSET]
    assert all("environment A2 (selected) leaves" in ln and "provider=live fails on it" in ln
               for ln in lines)
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    (stg,) = _rows(_xlsx(tmp_path, spec), STG)
    for row, headers in ((adls, ("SRC_CONTAINER_NAME", "TGT_CONTAINER_NAME",
                                 "SRC_ADLS_CONNECTION_ID", "TGT_CONNECTION_ID")),
                         (stg, ("SRC_CATALOG_NAME", "TGT_CATALOG_NAME", "TGT_CONTAINER_NAME"))):
        for header in headers:
            assert row[header][0] in (None, ""), header
    values = [cell[0] for row in (adls, stg) for cell in row.values()]
    assert not any("<<A2:" in str(v) or "d1_" in str(v) for v in values)   # tooltips name it
    ddl = "".join(p.read_text(encoding="utf-8")
                  for p in (tmp_path / "out" / spec.feed_slug).rglob("*DDL*.txt"))
    assert "<<A2:" not in ddl and "d1_dlk" not in ddl
    report = _report(tmp_path, spec)
    assert "environment: A2 (4 required missing: " in report
    assert "catalog_env_unset:stage" in report and "FAIL" not in report.split("\n", 3)[2]


def test_a_custom_unset_key_given_under_inputs_run_fills_its_cells(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path)
    env_file = tmp_path / "env.yaml"
    env_file.write_text("name: SANDBOX\ncontainers: {landing: syn-sb-landing, stage: "
                        "syn-sb-stage, standard: syn-sb-std}\nstorage_account: synsbacct\n",
                        encoding="utf-8")
    config = with_environment(config, select_environment(config, file=env_file))
    answers = tmp_path / "answers.yaml"
    answers.write_text('inputs:\n  run:\n    "environment.connection_ids.target": '
                       '{value: "22"}\n', encoding="utf-8")
    assert _generate(config, pair, spec.feed_id, answers_path=answers) == cli.EXIT_OK
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["TGT_CONNECTION_ID"][0] == "22"
    out = capsys.readouterr().out
    assert "run.environment.connection_ids.target" not in out
    assert "INPUT_NEEDED   run.environment.connection_ids.src_adls" in out
    assert (f"environment: SANDBOX (6 keys unset, from --environment-file "
            f"{env_file.as_posix()} + the answers file; custom)") in _report(tmp_path, spec)


def test_no_default_marked_fails_with_a_clear_message(tmp_path):
    overlay = _write_overlay(tmp_path, "environments:\n  D1: {default: false}\n")
    with pytest.raises(ValueError, match="exactly one environment must be marked "
                                         "`default: true`"):
        load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, overlay])


def test_the_app_offers_the_environments_and_takes_a_choice_or_other_values(monkeypatch):
    """The App's run form: the overlay's environments, the default preselected
    (source default, a non-blocking banner item); a named choice (selected);
    "Other" values (custom); an unknown name refused."""
    pytest.importorskip("fastapi")
    import threading
    from types import MethodType, SimpleNamespace

    from ui.backend.demo import DemoRunner

    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    runner = SimpleNamespace(_store=SimpleNamespace(config=config), _lock=threading.Lock(),
                             state="idle", environment_choice=None, iig_template="iig_v2",
                             effective_output_parts=lambda: ["framework"], input_choices={})
    for name in ("run_environment", "select_environment", "environment_options",
                 "_run_level_inputs"):
        setattr(runner, name, MethodType(getattr(DemoRunner, name), runner))
    options = runner.environment_options()
    assert [o["name"] for o in options["options"]] == ["D1", "A2", "PR"]
    assert (options["default"], options["selected"], options["source"]) == ("D1", "D1",
                                                                          "default")
    # 2026-10-15: profiles — values prefilled with their origin, required keys
    assert options["required"] == ["storage_account", "containers.landing",
                                   "containers.stage", "containers.standard"]
    assert options["options"][0]["origin"] == "overlay environments.D1"
    assert options["options"][0]["missing_required"] == ["storage_account"]
    assert options["banner"] == ("D1 (1 required missing: storage_account, from overlay "
                                 "environments.D1; default)")
    assert options["fields"] == ["containers.landing", "containers.stage",
                                 "containers.standard", "storage_account",
                                 "catalog_map.PR_DLK", "catalog_map.PR_STD",
                                 "default_catalog.stage", "default_catalog.standard",
                                 "connection_ids.src_adls", "connection_ids.metadata",
                                 "connection_ids.target"]
    # post47: the run-level items, scope "run", once (environment + the run-scoped cells)
    items = runner._run_level_inputs(with_environment(config, runner.run_environment()))
    # post81: application_name is a profile default — listed after the open ones
    assert [i["key"] for i in items] == ["run.environment.storage_account", "run.environment",
                                         "run.email_to", "run.application_name",
                                         "run.email_statuses"]
    assert items[0]["required"] is True and "required" not in items[1]
    assert {i["scope"] for i in items} == {"run"} and "assumed D1" in items[1]["question"]
    # 2026-10-15: the form's edits of the default profile fill the required key
    runner.select_environment(overrides={"storage_account": "synacct01"})
    options = runner.environment_options()
    assert options["banner"] == ("D1 (complete, from overlay environments.D1 + the App form; "
                                 "default)")
    assert options["edited"] == {"storage_account": "synacct01"}
    assert not [i for i in runner._run_level_inputs(
        with_environment(config, runner.run_environment())) if i.get("required")]
    runner.select_environment()
    # post47b: the shipped A2 is placeholders — accepted under provider=mock (its
    # keys are banner items), refused under provider=live naming the unset keys
    runner.select_environment(name="A2")
    keys = [i["key"] for i in runner._run_level_inputs(
        with_environment(config, runner.run_environment()))]
    assert "run.environment.catalog_map.PR_DLK" in keys and "run.environment" not in keys
    runner.select_environment()
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")
    with pytest.raises(EnvironmentSelectionError, match="A2 is not complete"):
        runner.select_environment(name="A2")
    monkeypatch.delenv("CODEGEN_PROVIDER")
    runner.select_environment(custom={"containers.stage": "syn-other-stage"},
                              custom_name="SANDBOX")
    options = runner.environment_options()
    assert (options["selected"], options["source"]) == ("SANDBOX", "custom")
    assert options["custom"]["containers.stage"] == "syn-other-stage"
    keys = [i["key"] for i in runner._run_level_inputs(
        with_environment(config, runner.run_environment()))]
    assert "run.environment" not in keys and "run.environment.catalog_map.PR_DLK" in keys
    with pytest.raises(EnvironmentSelectionError):
        runner.select_environment(name="nowhere")
    with pytest.raises(EnvironmentSelectionError, match="unknown key"):
        runner.select_environment(custom={"bogus": "x"})
    runner.select_environment()                                 # back to the default
    assert runner.environment_options()["source"] == "default"
