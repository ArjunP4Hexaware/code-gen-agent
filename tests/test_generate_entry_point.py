"""post60: the App's generate path writes CODEGEN_STAGES.json through the CLI's
entry point.

``codegen generate`` (``cli._run_pairs``) and the App's live run
(``DemoRunner._generate_specs``) both drive ``codegen.generate_run.GenerateRun``
over ``cli.generate_feed_result``. The manifest (questions with ``blocking``,
each feed's ``written`` / ``open`` / ``inputs`` / ``iig_cells``, the outcome)
comes from the same code, so the same synthetic pair gives byte-identical
manifests from both (the manifest carries no timestamp) — post76: under the
same Layer-2 mode (its ``layer2`` block). The App's run state reads the
outcome and ``written`` from it."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import run_stages
from codegen.resolve.resolver import pending_answers, resolve_pair
from test_iig_corpus_cells import _generate
from test_pipeline_name_choice import _pair

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def app(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    for role in ("state", "outputs"):
        (tmp_path / role).mkdir()
        monkeypatch.setenv(f"CODEGEN_STORAGE_{role.upper()}",
                           f"local:{(tmp_path / role).as_posix()}")
    monkeypatch.chdir(REPO)
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, index_warmup=False)
    runner.iig_template = "iig_v2"
    runner.conventions_profile = "acfc_prx"
    runner.output_parts = ["framework"]
    return runner


def _app_run(runner, config, frd: Path, sttm: Path, root: Path, *, choices=None):
    runner._store.config = config                     # noqa: SLF001 — the fixture's config
    runner.input_choices = dict(choices or {})
    specs = resolve_pair(frd, sttm, config)
    return runner._generate_specs(                    # noqa: SLF001 — the App's own path
        specs, config, run_env=None, frd_path=frd, run_root=root / "app",
        reports_root=root / "app_reports", held=list(pending_answers(sttm)), unstated=[],
        extra_flags=[], layout_usage=None)


def test_the_app_and_the_cli_write_the_same_manifest(app, tmp_path):
    config, spec, (frd, sttm) = _pair(tmp_path / "cli")
    # post76: the same Layer-2 mode (the App defers it by default) = the same manifest
    assert _generate(config, (frd, sttm), only_feed=None,
                     layer2=config.reasoning.layer2_app) == 0
    cli_manifest = (tmp_path / "cli" / "out" / run_stages.STAGES_FILE).read_bytes()
    runs, failures, manifest = _app_run(app, config, frd, sttm, tmp_path)
    app_manifest = (tmp_path / "app" / run_stages.STAGES_FILE).read_bytes()
    assert app_manifest == cli_manifest
    specs = resolve_pair(frd, sttm, config)
    assert failures == [] and list(runs) == [s.feed_slug for s in specs]
    # the App's state comes from the manifest
    assert app.outcome == manifest["stages"]["generate"]["status"] == "PASS_WITH_OPEN_INPUTS"
    assert [f["written"] for f in manifest["feeds"]] == [True] * len(specs)
    assert all(f["iig_cells"] for f in manifest["feeds"])   # the same counts as the CLI's
    assert any(q["line"] == "INPUT_NEEDED" and not q["blocking"]
               for q in manifest["questions"])


def test_a_confirmed_choice_gives_the_same_manifest_as_the_answers_file(app, tmp_path):
    from codegen.input_choices import Choice

    config, spec, (frd, sttm) = _pair(tmp_path / "cli")
    answers = tmp_path / "answers.yaml"
    answers.write_text(f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
                       "      pipeline_name: {choice: use_default}\n", encoding="utf-8")
    _generate(config, (frd, sttm), only_feed=None, answers_path=answers,
              layer2=config.reasoning.layer2_app)
    cli_manifest = (tmp_path / "cli" / "out" / run_stages.STAGES_FILE).read_bytes()
    _app_run(app, config, frd, sttm, tmp_path, choices={
        f"feeds.{spec.feed_id}.pipeline_name": Choice("use_default")})
    assert (tmp_path / "app" / run_stages.STAGES_FILE).read_bytes() == cli_manifest
    manifest = run_stages.read_stage_manifest(tmp_path / "app")
    assert manifest["feeds"][0]["inputs"]["pipeline_name.master"]["source"] == "default"


def test_a_gate_fail_is_quarantined_by_the_app_too(app, tmp_path, monkeypatch):
    """The App no longer infers: a feed whose gate says FAIL is GATE_FAIL in its
    manifest, its files under quarantine/ — and the run's FeedRun points there."""
    from codegen import cli

    real = cli.compute_verdict
    monkeypatch.setattr(cli, "compute_verdict", lambda *a, **kw: real(*a, **kw).model_copy(
        update={"verdict": "FAIL"}))
    config, spec, (frd, sttm) = _pair(tmp_path / "cli")
    runs, _failures, manifest = _app_run(app, config, frd, sttm, tmp_path)
    assert app.outcome == "GATE_FAIL"
    entry = next(e for e in manifest["feeds"]
                 if e.get("quarantine", "").startswith(f"{spec.feed_slug}/"))
    assert all(e["status"] == "GATE_FAIL" and e["written"] for e in manifest["feeds"])
    assert entry["quarantine"] == f"{spec.feed_slug}/{run_stages.QUARANTINE_DIR}"
    workbooks = [p for p in runs[spec.feed_slug].written_files if p.endswith(".xlsx")]
    assert workbooks and all(f"/{spec.feed_slug}/quarantine/" in p for p in workbooks)
    assert all(Path(p).is_file() for p in workbooks)


def test_the_app_status_names_every_blocking_line(app, tmp_path):
    """post80: a notebook run whose landing no document states stops at a
    blocking QUESTION the App lists nowhere else — the status names it, so the
    Generate page sends the person to it instead of "View results"."""
    from test_landing_question import _without_landing

    config, spec, (frd, sttm) = _pair(tmp_path / "cli")
    _without_landing((frd, sttm))                       # the Pyx FRD states no landing
    app.output_parts = ["notebook", "framework"]
    _app_run(app, config, frd, sttm, tmp_path)
    manifest = run_stages.read_stage_manifest(tmp_path / "app")
    blocking = [q["key"] for q in manifest["questions"] if q["blocking"]]
    status = app.status()
    assert status["outcome"] == manifest["stages"]["generate"]["status"]
    assert blocking, "the fixture pair must leave a blocking line open on a notebook run"
    assert [b["key"] for b in status["blocking"]] == list(dict.fromkeys(blocking))
    assert status["outcome"] == "NEEDS_ANSWERS"
    assert any(k.endswith(".src_adls_path") for k in blocking)
    # post80: the landing is ANSWERABLE in the App — a typed gaps: answer
    landing = [b["key"] for b in status["blocking"] if b["key"].endswith(".src_adls_path")]
    items = {i["key"]: i for i in app._run_items}            # noqa: SLF001 — the run's list
    for key in landing:
        item = items[key]
        assert (item["label"], item["section"], item["answer_as"]) == ("QUESTION", "gaps", "gap")
        assert item["question"]["kind"] == "text"


def test_a_landing_answered_in_the_app_writes_the_notebook(app, tmp_path):
    """post80: the App's answer to the landing question, posted as gaps: (the
    shape rerun_with_answers sends), reaches the resolver; the notebook is
    written and nothing blocks."""
    from codegen.layout.resolve import parse_answers
    from test_landing_question import _without_landing

    config, spec, (frd, sttm) = _pair(tmp_path / "cli")
    _without_landing((frd, sttm))
    app.output_parts = ["notebook", "framework"]
    _app_run(app, config, frd, sttm, tmp_path / "first")
    (key,) = [b["key"] for b in app.status()["blocking"] if b["key"].endswith(".src_adls_path")]
    posted = parse_answers({"gaps": {key: {"value": "/inbound/syn/vendor_k/"}}})
    gaps = {k: v["value"] for k, v in posted["gaps"].items()}
    specs = resolve_pair(frd, sttm, config, gaps=gaps)
    app._store.config = config                       # noqa: SLF001
    app._generate_specs(                             # noqa: SLF001 — the App's own path
        specs, config, run_env=None, frd_path=frd, run_root=tmp_path / "second",
        reports_root=tmp_path / "second_reports", held=list(pending_answers(sttm)),
        unstated=[], extra_flags=[], layout_usage=None)
    assert not [b for b in app.status()["blocking"] if b["key"] == key]
    assert list((tmp_path / "second" / specs[0].feed_slug).rglob("*.ipynb"))



def test_the_summary_names_the_notebook_where_it_was_written():
    """post81: the App's feed summary carries the notebook's feed-relative path —
    v2 writes notebook/<slug>.ipynb, which the old <slug>.ipynb lookup missed."""
    from types import SimpleNamespace

    pytest.importorskip("fastapi")
    from ui.backend.main import _notebook_path

    def run(*files):
        return SimpleNamespace(spec=SimpleNamespace(feed_slug="syn_a"), written_files=list(files))

    assert _notebook_path(run("out/syn_a/notebook/syn_a.py",
                              "out/syn_a/notebook/syn_a.ipynb")) == "notebook/syn_a.ipynb"
    assert _notebook_path(run("/tmp/x/syn_a/syn_a.ipynb")) == "syn_a.ipynb"     # v1
    assert _notebook_path(run("out/syn_a/framework/SYN_DDL.txt")) is None
