"""Environment PROFILES (2026-10-15, D1 post50 item 2).

A profile = the overlay's ``environments.<NAME>`` block (its per-field defaults)
with ``codegen-state/environments/<name>.yaml`` laid over it (outside the
tracked tree; CODEGEN_ENVIRONMENTS_DIR moves it — conftest points it at a
folder that does not exist). Resolution: --environment-file > --environment
<name> (else the default name) > INPUT_NEEDED. ``environment_schema.required``
(storage account, containers) left blank / a placeholder = a QUESTION, exit 3.
The banner names the environment, its completeness and where its values came
from; no ``<<ENV:...>>`` token reaches an emitted file."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from codegen import cli
from codegen.config import PLACEHOLDER_RE, load_config
from codegen.environments import (
    EnvironmentSelectionError,
    apply_environment,
    banner,
    missing_required,
    select_environment,
    with_environment,
)
from test_environments import ADLS, _generate, _report, _setup, _xlsx
from test_iig_v2_derivations import ACFC_OVERLAY, REPO, _rows, _write_overlay

EXAMPLE = REPO / "config" / "environments" / "example.yaml"


@pytest.fixture
def profiles(tmp_path, monkeypatch) -> Path:
    folder = tmp_path / "codegen-state" / "environments"
    folder.mkdir(parents=True)
    monkeypatch.setenv("CODEGEN_ENVIRONMENTS_DIR", str(folder))
    return folder


def _acfc():
    return load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])


# ---- the schema --------------------------------------------------------------

def test_the_schema_names_every_required_key_as_a_field():
    config = _acfc()
    schema = config.environment_schema
    assert set(schema.required) <= set(schema.fields)
    assert {"storage_account", "containers.stage"} <= set(schema.required)


def test_a_required_key_absent_from_the_fields_fails_the_load(tmp_path):
    bad = _write_overlay(tmp_path, "environment_schema:\n  required: [values.nowhere]\n")
    with pytest.raises(ValueError, match="values.nowhere"):
        load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, bad])


def test_the_tracked_example_profile_is_synthetic_and_complete():
    config = _acfc()
    env = select_environment(config, file=EXAMPLE)
    assert env.name == "SYN-EXAMPLE" and env.source == "custom"
    assert missing_required(config, env.entry) == []
    text = EXAMPLE.read_text(encoding="utf-8")
    values = [str(v) for v in yaml.safe_load(text).values() if not isinstance(v, dict)] + [
        str(v) for block in yaml.safe_load(text).values() if isinstance(block, dict)
        for v in block.values()]
    assert all(v.lower().startswith("syn") or v.isdigit() for v in values), values


# ---- resolution order --------------------------------------------------------

def test_a_named_profile_file_lies_over_the_overlay_block(profiles):
    (profiles / "d1.yaml").write_text("storage_account: synd1acct\n", encoding="utf-8")
    config = _acfc()
    env = select_environment(config, name="d1")
    assert (env.name, env.source) == ("D1", "selected")
    assert env.origin == (profiles / "d1.yaml").as_posix()
    assert env.entry.storage_account == "synd1acct"
    assert env.entry.containers == config.environments["D1"].containers   # the defaults
    assert banner(config, env) == f"D1 (complete, from {env.origin}; selected)"


def test_the_default_name_reads_its_profile_file_too(profiles):
    (profiles / "D1.yml").write_text("storage_account: synd1acct\n", encoding="utf-8")
    env = select_environment(_acfc())
    assert (env.name, env.source, env.entry.storage_account) == ("D1", "default", "synd1acct")


def test_no_profile_file_is_the_overlay_block(profiles):
    config = _acfc()
    env = select_environment(config, name="D1")
    assert env.origin == "overlay environments.D1"
    assert banner(config, env) == ("D1 (1 required missing: storage_account, from overlay "
                                   "environments.D1; selected)")


def test_the_environment_file_wins_over_a_name(profiles):
    (profiles / "d1.yaml").write_text("storage_account: synd1acct\n", encoding="utf-8")
    env = select_environment(_acfc(), name="D1", file=EXAMPLE)
    assert (env.name, env.source) == ("SYN-EXAMPLE", "custom")
    assert env.entry.storage_account == "synexamplestorage01"


def test_a_profile_only_in_the_state_folder_is_a_choice(profiles):
    (profiles / "sbx.yaml").write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    env = select_environment(_acfc(), name="sbx")
    assert (env.name, env.source, env.entry.containers["stage"]) == ("SBX", "selected",
                                                                     "syn-stage-01")
    with pytest.raises(EnvironmentSelectionError, match="choices: D1, A2, PR"):
        select_environment(_acfc(), name="nowhere")


def test_a_profile_file_with_an_unknown_key_is_refused(profiles):
    (profiles / "d1.yaml").write_text("storage_acount: typo\n", encoding="utf-8")
    with pytest.raises(EnvironmentSelectionError, match="unknown key 'storage_acount'"):
        select_environment(_acfc(), name="D1")


# ---- the run -----------------------------------------------------------------

def test_a_complete_profile_runs_clean_and_leaves_no_placeholder(tmp_path, profiles, capsys):
    """exit 0 (INPUT_NEEDED never blocks); the banner names the profile file; no
    environment token (<<ENV:STORAGE_ACCOUNT>> / CONTAINER / CATALOG /
    CONNECTION_ID) in any emitted file, and no placeholder at all in an IIG data
    sheet or the DDL / SQL (the _provenance notes and the answers template may
    quote a corpus placeholder to say why a cell is open)."""
    config, spec, pair = _setup(tmp_path)
    (profiles / "d1.yaml").write_text("storage_account: synd1acct\n", encoding="utf-8")
    config = with_environment(config, select_environment(config, name="d1"))
    assert _generate(config, pair, spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    origin = (profiles / "d1.yaml").as_posix()
    assert (f"NOTE           run.environment — environment: D1 (complete, from {origin}; "
            "selected)") in out.splitlines()
    assert not [ln for ln in out.splitlines() if ln.startswith("QUESTION")]
    assert f"environment: D1 (complete, from {origin}; selected)" in _report(tmp_path, spec)
    env_token = re.compile(r"<<[A-Z][A-Z0-9_]*:(?:STORAGE_ACCOUNT|CONTAINER|CATALOG|"
                           r"CONNECTION_ID)[^>]*>>")
    leaks = []
    for path in (tmp_path / "out").rglob("*"):
        if path.suffix == ".xlsx":
            import openpyxl

            book = openpyxl.load_workbook(path, read_only=True)
            for sheet in book.worksheets:
                strict = not sheet.title.startswith("_")
                leaks += [f"{path.name}:{sheet.title}" for row in sheet.iter_rows(values_only=True)
                          for v in row if isinstance(v, str) and (
                              env_token.search(v) or (strict and PLACEHOLDER_RE.search(v)))]
            book.close()
        elif path.suffix in (".sql", ".txt", ".md", ".json", ".yaml") and path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if env_token.search(text) or (path.suffix in (".sql", ".txt")
                                          and PLACEHOLDER_RE.search(text)):
                leaks.append(path.name)
    assert not leaks, leaks


def test_a_missing_required_value_is_a_question_and_exit_3(tmp_path, profiles, capsys):
    config, spec, pair = _setup(tmp_path)
    (profiles / "d1.yaml").write_text("containers: {stage: ''}\n", encoding="utf-8")
    config = with_environment(config, select_environment(config, name="d1"))
    assert _generate(config, pair, spec.feed_id) == cli.EXIT_NEEDS_ANSWERS
    questions = [ln.split()[1] for ln in capsys.readouterr().out.splitlines()
                 if ln.startswith("QUESTION")]
    assert questions == ["run.environment.storage_account"]   # a blank never clears a default
    (adls,) = _rows(_xlsx(tmp_path, spec), ADLS)
    assert adls["TGT_CONTAINER_NAME"][0] == config.environments["D1"].containers["stage"]


def test_an_answers_file_value_completes_a_named_profile(tmp_path, profiles, capsys):
    config, spec, pair = _setup(tmp_path)
    answers = tmp_path / "answers.yaml"
    answers.write_text('inputs:\n  run:\n    "environment.storage_account": '
                       '{value: synansweracct}\n', encoding="utf-8")
    assert _generate(config, pair, spec.feed_id, answers_path=answers) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert ("NOTE           run.environment — environment: D1 (complete, from overlay "
            "environments.D1 + the answers file; default)") in out.splitlines()


def test_the_cli_flag_resolves_the_profile_file(tmp_path, profiles):
    (profiles / "d1.yaml").write_text("storage_account: synd1acct\n", encoding="utf-8")
    args = cli._parser().parse_args(["generate", "--frd", "a", "--sttm", "b",
                                     "--environment", "d1"])
    env = select_environment(_acfc(), name=args.environment)
    assert env.origin.endswith("codegen-state/environments/d1.yaml")


# ---- the DQ split location never carries a placeholder storage account --------

DQ = "DATA_QUALITY_RULES"
DQ_KEYS = ("dq_rules", "dq_rule_classes", "dq_rule_types", "dq_params", "dq_citations",
           "dq_split_style", "dq_split_location", "environment_cells")


def _split_target(pair4_spec, tmp_path, account: str) -> dict:
    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from multi_table_golden import PAIR4_OVERLAY

    from codegen.contracts.frd import FrdContract
    from codegen.metadata_template import template_tab_rows

    acfc = yaml.safe_load(ACFC_OVERLAY.read_text(encoding="utf-8"))
    knobs = {k: v for k, v in acfc["metadata"]["templates"]["iig_v2"].items() if k in DQ_KEYS}
    env = {"SYN": {"default": True, "storage_account": account,
                   "containers": {"landing": "syn-landing", "stage": "syn-stage",
                                  "standard": "syn-std"}}}
    overlay = tmp_path / f"dq_{len(account)}.yaml"
    overlay.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": knobs}},
                                       "environments": env}), encoding="utf-8")
    config = load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY, overlay])
    config = with_environment(config, select_environment(config, live=False))
    tpl = apply_environment(config.metadata.templates["iig_v2"], config)
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    rows = template_tab_rows(DQ, frd.feeds[0], config, pair4_spec, None, tpl)
    splits = [r for r in rows if "|" in str((r.get("SOURCE_COLUMN") or {}).get("value"))]
    assert splits
    return [r["TARGET_COLUMN"] for r in splits]


def test_a_real_storage_account_builds_the_split_location(pair4_spec, tmp_path):
    for target in _split_target(pair4_spec, tmp_path, "synacct01"):
        assert "abfss://syn-stage@synacct01.dfs.core.windows.net/" in target["value"]


def test_a_placeholder_storage_account_leaves_the_split_location_open(pair4_spec, tmp_path):
    for target in _split_target(pair4_spec, tmp_path, "<<SYN:STORAGE_ACCOUNT>>"):
        assert target["value"] in (None, "")
        assert not re.search(r"<<", json.dumps(target))
        assert "QUESTION run.environment.storage_account" in target["badge_entry"]["note"]
