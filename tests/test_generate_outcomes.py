"""The generate stage's two failure outcomes (2026-10-15, post54), on the
synthetic PRX fixture (pair 1, profile acfc_prx, iig_v2). Exit code 1 for both.

- CRASHED — an exception mid-write: the feed's partial emit files are deleted,
  the emit stages SKIPPED (tests/test_emit_stages_skipped.py has more);
- GATE_FAIL — the files are complete, the gate said no: every artefact is KEPT,
  moved under <output>/<feed>/quarantine/ beside a GATE_FAIL.md (counts per flag
  type, no names / values), the emit stages PASS, and CODEGEN_STAGES.json says
  generate = GATE_FAIL with the quarantine path."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from codegen import cli, run_stages
from codegen.emit.context import TemplateGapError
from codegen.run_errors import first_error_line
from test_emit_stages_skipped import FEED, contracts  # noqa: F401 — the pair-1 chain

REPO = Path(__file__).resolve().parents[1]


def _fail_the_gate(monkeypatch):
    real = cli.compute_verdict

    def failing(*args, **kwargs):
        return real(*args, **kwargs).model_copy(update={"verdict": "FAIL"})

    monkeypatch.setattr(cli, "compute_verdict", failing)


def _workbooks(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.xlsx"))}


def test_gate_fail_keeps_every_artefact_in_quarantine(contracts, tmp_path, capsys,  # noqa: F811
                                                       monkeypatch):
    out = tmp_path / "out"
    feed_dir = out / FEED
    assert cli.main(contracts) == 0                      # the non-quarantined run
    clean = _workbooks(feed_dir)
    assert any(name.endswith("_IIG.xlsx") for name in clean)
    clean_files = sorted(p.relative_to(feed_dir).as_posix()
                         for p in feed_dir.rglob("*") if p.is_file())
    capsys.readouterr()

    _fail_the_gate(monkeypatch)
    code = cli.main(contracts)
    captured = capsys.readouterr()
    assert code == 1                                     # exit code unchanged

    q_dir = feed_dir / run_stages.QUARANTINE_DIR
    # every file, byte-identical, under quarantine/ at the same relative path
    assert _workbooks(q_dir) == clean
    assert sorted(p.relative_to(q_dir).as_posix() for p in q_dir.rglob("*")
                  if p.is_file() and p.name != run_stages.GATE_FAIL_FILE) == clean_files
    assert not [p for p in feed_dir.rglob("*") if p.is_file()
                and run_stages.QUARANTINE_DIR not in p.relative_to(feed_dir).parts]

    note = (q_dir / run_stages.GATE_FAIL_FILE).read_text(encoding="utf-8")
    assert note.startswith("# GATE_FAIL — complete, gate failed, review only")
    assert "| Flag type | Count |" in note and "Feed 1 of 1" in note
    assert FEED not in note                              # counts only, no names

    manifest = run_stages.read_stage_manifest(out)
    generate = manifest["stages"]["generate"]
    assert generate == {"status": "GATE_FAIL", "label": run_stages.REVIEW_ONLY,
                        "quarantine": [f"{FEED}/{run_stages.QUARANTINE_DIR}"]}
    for stage in ("ddl_emit", "iig_emit"):
        assert manifest["stages"][stage] == {"status": "PASS"}
    (feed,) = manifest["feeds"]
    assert feed["status"] == "GATE_FAIL" and feed["removed"] == 0
    assert feed["quarantine"] == f"{FEED}/{run_stages.QUARANTINE_DIR}"
    listed = {p for paths in feed["artefacts"].values() for p in paths}
    assert listed and all(p.startswith(f"{FEED}/{run_stages.QUARANTINE_DIR}/") for p in listed)
    assert all((out / p).is_file() for p in listed)

    assert "SKIPPED" not in captured.out
    assert f"{'GATE_FAIL':<15} {FEED}" in captured.out
    assert first_error_line(code, captured.err, captured.out) == (
        f"{'FAIL':<15} generate — gate verdict FAIL (complete, review only: quarantined) "
        "at feed 1 of 1")


def test_the_iig_diff_tool_still_finds_the_quarantined_build(contracts, tmp_path,  # noqa: F811
                                                              monkeypatch, capsys):
    _fail_the_gate(monkeypatch)
    assert cli.main(contracts) == 1
    capsys.readouterr()
    spec = importlib.util.spec_from_file_location("iig_diff_q", REPO / "tools" / "iig_diff.py")
    iig_diff = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "iig_diff_q", iig_diff)    # its dataclasses need it
    spec.loader.exec_module(iig_diff)
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    (workbook,) = [p for p in manifest["feeds"][0]["artefacts"]["iig_emit"]
                   if p.endswith("_IIG.xlsx")]
    build = iig_diff.find_build(tmp_path / "out" / workbook)
    assert build is not None and build.get("version")


def test_a_rerun_that_passes_clears_the_old_quarantine(contracts, tmp_path, monkeypatch,  # noqa: F811
                                                       capsys):
    real = cli.compute_verdict
    _fail_the_gate(monkeypatch)
    assert cli.main(contracts) == 1
    q_dir = tmp_path / "out" / FEED / run_stages.QUARANTINE_DIR
    assert q_dir.is_dir()
    monkeypatch.setattr(cli, "compute_verdict", real)
    assert cli.main(contracts) == 0
    assert not q_dir.exists()
    assert list((tmp_path / "out" / FEED).rglob("*_IIG.xlsx"))
    assert run_stages.read_stage_manifest(tmp_path / "out")["stages"]["generate"] == \
        {"status": "PASS"}
    capsys.readouterr()


def test_crashed_deletes_partials_and_skips_the_emit_stages(contracts, tmp_path,  # noqa: F811
                                                            capsys, monkeypatch):
    """The forced exception: the workbook is on disk when the feed crashes."""
    def crash(*args, **kwargs):
        assert list((tmp_path / "out" / FEED).rglob("*_IIG.xlsx"))
        raise TemplateGapError("forced mid-write")

    monkeypatch.setattr(cli, "write_generation_report", crash)
    code = cli.main(contracts)
    captured = capsys.readouterr()
    assert code == 1
    assert not list((tmp_path / "out" / FEED).rglob("*.xlsx"))
    assert not (tmp_path / "out" / FEED / run_stages.QUARANTINE_DIR).exists()
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["stages"]["generate"] == {"status": "CRASHED"}
    for stage in run_stages.EMIT_STAGES:
        assert manifest["stages"][stage]["status"] == "SKIPPED"
        assert f"{'SKIPPED':<15} {stage}" in captured.out
    assert manifest["feeds"][0]["status"] == "CRASHED" and manifest["feeds"][0]["removed"] > 0


def test_an_uncaught_crash_still_writes_the_manifest(contracts, tmp_path, monkeypatch,  # noqa: F811
                                                     capsys):
    monkeypatch.setattr(cli, "write_generation_report",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("forced")))
    with pytest.raises(RuntimeError):
        cli.main(contracts)
    capsys.readouterr()
    manifest = json.loads((tmp_path / "out" / run_stages.STAGES_FILE).read_text(
        encoding="utf-8"))
    assert manifest["exit"] == 1 and manifest["stages"]["generate"]["status"] == "CRASHED"
    assert not list((tmp_path / "out" / FEED).rglob("*.xlsx"))


def test_flag_types_are_vocabulary_never_text():
    assert run_stages.flag_type("iig_blank:SHEET_A: COL_1, COL_2") == "iig_blank"
    assert run_stages.flag_type("frd_unstated:feeds[0].x source_used:y") == "frd_unstated"
    assert run_stages.flag_type("provider_overridden: dry run") == "provider_overridden"
    assert run_stages.flag_type("SYN Client Name: something") == "other"
    assert run_stages.flag_type("") == "other"
