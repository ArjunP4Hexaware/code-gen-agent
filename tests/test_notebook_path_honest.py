"""post68: the notebook output path goes through the same bookkeeping as the
workbook (codegen.generate_run.GenerateRun). Synthetic pair 11, mock only.

1. A feed with a blocking line open (its own, or a run-level one such as a
   required environment value) writes no notebook. On a notebook-only run it
   keeps no emit artefacts either and its manifest entry says ``written:
   false``. Next to Framework, the workbook is still written for review
   (post58); only the notebook files go. The required-environment check is the
   same for the CLI and the App whatever the output mode.
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
