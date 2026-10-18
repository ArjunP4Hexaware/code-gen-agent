"""post68: the notebook output path goes through the same bookkeeping as the
workbook (codegen.generate_run.GenerateRun). Synthetic pair 11, mock only.

1. A feed with a blocking line open (its own, or a run-level one such as a
   required environment value) writes no notebook. On a notebook-only run it
   keeps no emit artefacts either and its manifest entry says ``written:
   false``. Next to Framework, the workbook is still written for review
   (post58); only the notebook files go. The required-environment check is the
   same for the CLI and the App whatever the output mode.
2. One input set: the answers file's run.environment, the owed inputs and the
   input choices apply on a notebook run exactly as on a framework run — the
   same open lines, the same counts.
"""

from __future__ import annotations

from codegen import cli, run_stages
from codegen.generate_run import run_level_lines
from test_iig_corpus_cells import _pair11


def _run(config, pair, parts, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True, output_mode=parts,
                          conventions_profile="acfc_prx", iig_template="iig_v2", **kw)


def _files(root, suffix: str) -> list:
    return sorted(p for p in root.rglob(f"*{suffix}") if run_stages.QUARANTINE_DIR not in p.parts)


# ------------------------------------------------- 1. blocking line -> no notebook


def test_without_a_blocking_line_the_notebook_is_written(tmp_path):
    config, specs, pair = _pair11(tmp_path)
    code = _run(config, pair, ["notebook"], only_feed=specs[0].feed_id)
    assert code == cli.EXIT_OK
    assert len(_files(tmp_path / "out", ".ipynb")) == 1
    (feed,) = run_stages.read_stage_manifest(tmp_path / "out")["feeds"]
    assert feed["written"] is True and "notebook_withheld" not in feed


def test_a_blocking_line_writes_no_notebook_on_a_notebook_only_run(
        tmp_path, capsys, no_environment_profiles):
    config, specs, pair = _pair11(tmp_path)
    feed_id = specs[0].feed_id
    code = _run(config, pair, ["notebook"], only_feed=feed_id)
    out = capsys.readouterr().out
    assert code == cli.EXIT_NEEDS_ANSWERS
    assert "QUESTION       run.environment.storage_account — " in out
    assert _files(tmp_path / "out", ".ipynb") == []
    feed_dir = tmp_path / "out" / specs[0].feed_slug
    assert not (feed_dir / "pipeline").exists() and not (feed_dir / "job").exists()
    assert _files(feed_dir, ".sql") == []                    # nothing deployable kept
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["stages"]["generate"]["status"] == "NEEDS_ANSWERS"
    (feed,) = manifest["feeds"]
    assert feed["written"] is False and feed["notebook_withheld"] > 0
    assert (f"NOTE           feeds.{feed_id}.notebook — not written — 1 blocking line(s) open "
            "(run.environment.storage_account); answer them and re-run") in out


def test_next_to_framework_only_the_notebook_is_withheld(tmp_path, no_environment_profiles):
    config, specs, pair = _pair11(tmp_path)
    code = _run(config, pair, ["notebook", "framework"], only_feed=specs[0].feed_id)
    assert code == cli.EXIT_NEEDS_ANSWERS
    out = tmp_path / "out"
    assert _files(out, ".ipynb") == []
    assert len(_files(out, "_IIG.xlsx")) == 1                 # the workbook, for review
    (feed,) = run_stages.read_stage_manifest(out)["feeds"]
    assert feed["written"] is True and feed["notebook_withheld"] > 0


def test_a_feed_level_blocking_line_withholds_that_feed_only(tmp_path):
    from codegen.generate_run import GenerateRun

    config, _specs, _pair = _pair11(tmp_path)
    run = GenerateRun(config, out_root=tmp_path, output_mode=["notebook"])
    run.open_items += [run_stages.open_item("QUESTION", "feeds[0].x", feed="a"),
                       run_stages.open_item("INPUT_NEEDED", "feeds.b.y", feed="b")]
    assert [i["key"] for i in run.blocking_for("a")] == ["feeds[0].x"]
    assert run.blocking_for("b") == []                         # INPUT_NEEDED never blocks


def test_the_required_environment_check_ignores_the_output_mode(tmp_path, no_environment_profiles):
    config, _specs, _pair = _pair11(tmp_path)
    asked = {}
    for parts in (["notebook"], ["framework"], ["notebook", "framework"]):
        questions, _items = run_level_lines(config, {}, output_mode=parts,
                                            iig_template="iig_v2")
        asked[tuple(parts)] = [key for key, _reason in questions]
    assert set(map(tuple, asked.values())) == {("run.environment.storage_account",)}


def test_the_app_lists_the_required_value_on_a_notebook_run(tmp_path, no_environment_profiles):
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    config, _specs, _pair = _pair11(tmp_path)
    runner = DemoRunner(GenerationStore("config/config.yaml"), work=lambda: None,
                        index_warmup=False)
    runner.output_parts = ["notebook"]
    runner.iig_template = "iig_v2"
    required = [i["key"] for i in runner._run_level_inputs(config) if i.get("required")]
    assert required == ["run.environment.storage_account"]


# ------------------------------------------------------------- 2. one input set


def _open_lines(out) -> tuple[list, list]:
    manifest = run_stages.read_stage_manifest(out)
    return (sorted((q["line"], q["key"]) for q in manifest["questions"]),
            [f["open"] for f in manifest["feeds"]])


def test_notebook_and_framework_runs_show_the_same_open_lines(tmp_path):
    config, specs, pair = _pair11(tmp_path)
    by_mode = {}
    for parts in (["notebook"], ["framework"]):
        out = tmp_path / parts[0]
        run_config = config.model_copy(update={"output": config.output.model_copy(
            update={"dir": str(out), "reports_dir": str(out / "reports")})})
        assert _run(run_config, pair, parts, only_feed=specs[0].feed_id) == cli.EXIT_OK
        by_mode[parts[0]] = _open_lines(out)
    assert by_mode["notebook"] == by_mode["framework"]
    lines, counts = by_mode["notebook"]
    assert ("INPUT_NEEDED", "run.environment") in lines          # the environment assumed
    assert counts[0]["non_blocking"] > 0                          # the owed feed inputs


def test_the_answers_file_environment_applies_on_a_notebook_run(
        tmp_path, capsys, no_environment_profiles):
    config, specs, pair = _pair11(tmp_path)
    answers = tmp_path / "answers.yaml"
    answers.write_text("inputs:\n  run:\n    environment: {value: D1}\n"
                       '    environment.storage_account: {value: "synstorageacct"}\n',
                       encoding="utf-8")
    code = _run(config, pair, ["notebook"], only_feed=specs[0].feed_id, answers_path=answers)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert "QUESTION       run.environment.storage_account" not in out
    assert "NOTE           run.environment — environment: D1" in out
    assert len(_files(tmp_path / "out", ".ipynb")) == 1
