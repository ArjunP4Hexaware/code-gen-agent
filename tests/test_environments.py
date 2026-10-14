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

from codegen import cli
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
"""


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
    assert {"QA", "PROD"} <= set(config.environments)
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
    assert code == cli.EXIT_OK
    line = next(ln for ln in out.splitlines() if ln.startswith("INPUT_NEEDED   run.environment"))
    assert "assumed D1 (the default" in line
    d1 = config.environments["D1"]
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["SRC_CONTAINER_NAME"][0] == d1.containers["landing"]
    assert adls["TGT_CONTAINER_NAME"][0] == d1.containers["stage"]
    (stg,) = _rows(_xlsx(tmp_path, spec), STG)
    assert (stg["SRC_CONTAINER_NAME"][0], stg["TGT_CONTAINER_NAME"][0]) == (
        d1.containers["stage"], d1.containers["standard"])
    report = _report(tmp_path, spec)
    assert "environment: D1 (default)" in report
    assert "inputs needed: 2" in report                       # + ACTIVE_START_DATE
    assert (f"iig_env:{ADLS}.TGT_CONTAINER_NAME — '{d1.containers['stage']}' from environment "
            "D1 (default): containers.stage") in report
    template = (tmp_path / "out" / "answers_template.yaml").read_text(encoding="utf-8")
    assert '"run.environment":' in template


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
    report = _report(tmp_path, spec)
    assert "environment: QA (selected)" in report
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
    with pytest.raises(EnvironmentSelectionError, match="choices: D1, QA, PROD"):
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
    assert code == cli.EXIT_OK
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["TGT_CONTAINER_NAME"][0] == "syn-sb-stage"
    report = _report(tmp_path, spec)
    assert "environment: SANDBOX (custom)" in report
    assert "INPUT_NEEDED   run.environment" not in capsys.readouterr().out


def test_an_answers_file_input_selects_the_environment(tmp_path, capsys):
    config, spec, pair = _setup(tmp_path, QA)
    answers = tmp_path / "answers.yaml"
    answers.write_text('inputs:\n  "run.environment": {value: QA}\n', encoding="utf-8")
    assert _generate(config, pair, spec.feed_id, answers_path=answers) == cli.EXIT_OK
    assert "INPUT_NEEDED   run.environment" not in capsys.readouterr().out
    assert "environment: QA (selected)" in _report(tmp_path, spec)


def test_a_placeholder_environment_leaves_its_cells_open(tmp_path):
    """The shipped QA entry is placeholders: selecting it writes no container."""
    config, spec, pair = _setup(tmp_path)
    config = with_environment(config, select_environment(config, name="QA"))
    _generate(config, pair, spec.feed_id)
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["TGT_CONTAINER_NAME"][0] in (None, "")
    assert "<<QA:" not in str(adls["TGT_CONTAINER_NAME"][0])


def test_no_default_marked_fails_with_a_clear_message(tmp_path):
    overlay = _write_overlay(tmp_path, "environments:\n  D1: {default: false}\n")
    with pytest.raises(ValueError, match="exactly one environment must be marked "
                                         "`default: true`"):
        load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, overlay])


def test_the_app_offers_the_environments_and_takes_a_choice_or_other_values():
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
                             effective_output_parts=lambda: ["framework"])
    for name in ("run_environment", "select_environment", "environment_options",
                 "_environment_input"):
        setattr(runner, name, MethodType(getattr(DemoRunner, name), runner))
    options = runner.environment_options()
    assert [o["name"] for o in options["options"]] == ["D1", "QA", "PROD"]
    assert (options["default"], options["selected"], options["source"]) == ("D1", "D1",
                                                                          "default")
    assert options["fields"] == ["containers.landing", "containers.stage",
                                 "containers.standard", "storage_account"]
    (item,) = runner._environment_input(config, runner.run_environment())
    assert item["key"] == "run.environment" and "assumed D1" in item["question"]
    runner.select_environment(name="QA")
    assert runner.environment_options()["source"] == "selected"
    assert runner._environment_input(config, runner.run_environment()) == []
    runner.select_environment(custom={"containers.stage": "syn-other-stage"},
                              custom_name="SANDBOX")
    options = runner.environment_options()
    assert (options["selected"], options["source"]) == ("SANDBOX", "custom")
    assert options["custom"]["containers.stage"] == "syn-other-stage"
    with pytest.raises(EnvironmentSelectionError):
        runner.select_environment(name="nowhere")
    with pytest.raises(EnvironmentSelectionError, match="unknown key"):
        runner.select_environment(custom={"bogus": "x"})
    runner.select_environment()                                 # back to the default
    assert runner.environment_options()["source"] == "default"
