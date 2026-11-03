"""post75: the container runner — a stage exiting 3 ends the pair (the stages
after it SKIPPED, outcome NEEDS_ANSWERS), a failure ends it as FAIL, the state
dir's answers win over the pair folder's, feed ids in keys are masked, and each
stage's CODEGEN-USAGE line is kept. The codegen CLI is faked."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import container_harness as ch  # noqa: E402

sys.path.remove(str(REPO / "scripts"))

USAGE = 'CODEGEN-USAGE {"stage": "layer2", "provider": "databricks_fmapi", "seconds": 12.5, ' \
        '"calls": 3, "requests": 3, "failed": 0, "recovered": 0}'


def _pair(tmp_path: Path, answers: bool = False) -> argparse.Namespace:
    pair = tmp_path / "pairs" / "pair_7"
    pair.mkdir(parents=True)
    (pair / "STTM_syn.xlsx").write_bytes(b"x")
    (pair / "FRD_syn.docx").write_bytes(b"x")
    if answers:
        (pair / "answers.yaml").write_text("gaps: {}\n", encoding="utf-8")
    state = tmp_path / "state"
    state.mkdir()
    return argparse.Namespace(pairs_dir=tmp_path / "pairs", state_dir=state,
                              work=tmp_path / "work", output_mode=["notebook", "framework"],
                              dry_run=True, environment="D1", timeout_min=1)


def _fake(monkeypatch, codes: dict[str, int], seen: list) -> None:
    def run(cmd, **kw):
        sub = cmd[3]
        seen.append((sub, cmd))
        out = "QUESTION       feeds.syn_feed_name.notebook.landing_path — x\n" if \
            codes.get(sub) == 3 else ""
        return SimpleNamespace(returncode=codes.get(sub, 0), stdout=out,
                               stderr=USAGE if sub == "generate" else "")

    monkeypatch.setattr(subprocess, "run", run)


def test_an_exit_3_ends_the_pair_and_skips_the_rest(tmp_path: Path, monkeypatch) -> None:
    args = _pair(tmp_path)
    seen: list = []
    _fake(monkeypatch, {"extract-sttm": 3}, seen)
    run = ch.Runner(args, {}).run_pair(7)
    assert [s for s, _ in seen] == ["layout", "extract-sttm"]          # generate never ran
    assert run.stages["frd_extract"].status == "NEEDS_ANSWERS"
    assert run.stages["generate"].status == "SKIPPED"
    assert run.outcome == "NEEDS_ANSWERS"
    assert run.answer_keys() == ["feeds.feed_1.notebook.landing_path"]  # feed id masked


def test_a_failure_ends_the_pair_as_fail(tmp_path: Path, monkeypatch) -> None:
    args = _pair(tmp_path)
    seen: list = []
    _fake(monkeypatch, {"layout": 1}, seen)
    run = ch.Runner(args, {}).run_pair(7)
    assert [s for s, _ in seen] == ["layout"]
    assert run.outcome == "FAIL" and run.stages["frd_extract"].status == "SKIPPED"


def test_the_state_dirs_answers_win_and_usage_is_kept(tmp_path: Path, monkeypatch) -> None:
    args = _pair(tmp_path, answers=True)
    state_answers = args.state_dir / "answers" / "pair_7" / "answers.yaml"
    state_answers.parent.mkdir(parents=True)
    state_answers.write_text("gaps: {}\n", encoding="utf-8")
    seen: list = []
    _fake(monkeypatch, {}, seen)
    run = ch.Runner(args, {}).run_pair(7)
    assert run.answers_source == "state"
    generate = next(cmd for sub, cmd in seen if sub == "generate")
    assert str(state_answers) in generate
    assert generate.count("--output-mode") == 2
    assert run.stages["generate"].usage.startswith("layer2: 3 call(s) in 12.5s")


def test_the_report_carries_the_usage_line_per_stage(tmp_path: Path, monkeypatch) -> None:
    args = _pair(tmp_path)
    _fake(monkeypatch, {}, [])
    run = ch.Runner(args, {}).run_pair(7)
    md = ch.report_md("run_x", "abc", [run], {"provider": "mock"})
    assert "### Model usage" in md and "* generate: layer2: 3 call(s) in 12.5s" in md
    report = json.loads(ch.report_json("run_x", "abc", [run], {}))
    assert report["pairs"][0]["stages"]["generate"]["usage"].startswith("layer2: 3 call(s)")


def test_a_missing_dependency_is_listed_never_installed(monkeypatch) -> None:
    real = ch.md.version

    def version(name):
        if name == "openpyxl":
            raise ch.md.PackageNotFoundError(name)
        return real(name)

    monkeypatch.setattr(ch.md, "version", version)
    assert ch.missing_dependencies() == ["openpyxl"]


@pytest.mark.parametrize("name", ["PAYMENT_INTEGRITY_SYN_IIG.xlsx", "SYN_IIG.xlsx"])
def test_golden_iig_workbooks_are_never_an_input(tmp_path: Path, name: str) -> None:
    args = _pair(tmp_path)
    (args.pairs_dir / "pair_7" / name).write_bytes(b"x")
    docs = ch.discover(args.pairs_dir / "pair_7", args.state_dir)
    assert docs["sttm"].name == "STTM_syn.xlsx"
