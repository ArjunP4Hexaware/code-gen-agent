"""D1 post51 (2026-10-15): DDL / IIG workbook / DML emit read PASS on pairs
whose Generate FAILED (pairs 03 / 04 / 07 carried pair_02's exact unpopulated
counts). The emit stages are SKIPPED when generation CRASHED (or failed before
writing), the exit code is unchanged, a crashed feed's emit artefacts are
deleted, and CODEGEN_STAGES.json (codegen.run_stages) records what the run
actually wrote. A GATE_FAIL keeps its files in quarantine:
tests/test_generate_outcomes.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli, run_stages
from codegen.emit.context import TemplateGapError
from codegen.run_errors import MARKER, first_error_line

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
PAIR_1 = SHAPES / "sttm" / "pair_1_family_a.xlsx"
PAIR_1_FRD = SHAPES / "frd" / "f1_pair_1.docx"
VDD = SHAPES / "vdd" / "pair_1_v1_segments.xlsx"
DML_ON = REPO / "tests" / "fixtures" / "dml_on_overlay.yaml"
DATE = "2026-09-18"
FEED = "vnd_p_accum_client"
EMIT_SUFFIXES = (".xlsx", ".sql")


@pytest.fixture()
def contracts(tmp_path, monkeypatch, capsys):
    """pair 1's contracts (the synthetic family-A shape), outputs under tmp_path."""
    for path in (PAIR_1, PAIR_1_FRD, VDD):
        if not path.is_file():
            pytest.skip(f"synthetic fixture absent: {path.name}")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    overlays = [SHAPES / "pair_1" / "config_overlay.yaml"]
    if DML_ON.is_file():
        overlays.append(DML_ON)
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", ";".join(str(p) for p in overlays))
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    (tmp_path / "state").mkdir()
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(REPO)
    frd, sttm, vdd, layout = (tmp_path / n for n in (
        "frd.contract.json", "sttm.contract.json", "vdd.contract.json", "sttm.layout.json"))
    assert cli.main(["layout", "--workbook", str(PAIR_1), "--frd", str(PAIR_1_FRD), "--vdd",
                     str(VDD), "--dry-run", "--no-cache", "--profile-out", str(layout),
                     "--frd-contract-out", str(frd), "--require-complete"]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(PAIR_1), "--frd-contract", str(frd),
                     "--out", str(sttm), "--layout", str(layout),
                     "--generated-date", DATE]) == 0
    assert cli.main(["extract-vdd", "--vdd", str(VDD), "--out", str(vdd),
                     "--generated-date", DATE]) == 0
    capsys.readouterr()
    return ["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm),
            "--vdd", str(vdd), "--output-mode", "framework", "--profile", "acfc_prx",
            "--iig-template", "iig_v2", "--skip-tests", "--dry-run"]


def _emit_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and run_stages.emit_stage(p))


def test_a_passing_run_lists_what_it_wrote(contracts, tmp_path, capsys):
    assert cli.main(contracts) == 0
    out = capsys.readouterr().out
    assert "SKIPPED" not in out
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["exit"] == 0 and manifest["stages"]["generate"] == {"status": "PASS"}
    assert manifest["stages"]["iig_emit"] == {"status": "PASS"}
    assert manifest["stages"]["ddl_emit"] == {"status": "PASS"}
    (feed,) = manifest["feeds"]
    assert feed["n"] == 1 and feed["of"] == 1 and feed["removed"] == 0
    listed = {p for paths in feed["artefacts"].values() for p in paths}
    assert any(p.endswith("_IIG.xlsx") for p in listed)
    assert all((tmp_path / "out" / p).is_file() for p in listed)


def _assert_skipped(code, out, err, tmp_path, reason):
    assert code == 1                                            # exit code unchanged
    for stage in run_stages.EMIT_STAGES:
        assert f"{'SKIPPED':<15} {stage} — {run_stages.SKIPPED_UPSTREAM}" in out
    assert not _emit_files(tmp_path / "out" / FEED), "a partial emit artefact survived"
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["exit"] == 1 and manifest["stages"]["generate"]["status"] == "CRASHED"
    for stage in run_stages.EMIT_STAGES:
        assert manifest["stages"][stage] == {"status": "SKIPPED",
                                             "reason": run_stages.SKIPPED_UPSTREAM}
    (feed,) = manifest["feeds"]
    assert feed["status"] == "CRASHED" and feed["removed"] > 0
    assert all(not paths for paths in feed["artefacts"].values())
    assert any(ln.startswith(MARKER) for ln in err.splitlines())
    assert first_error_line(code, err, out).startswith(f"{'FAIL':<15} generate — {reason}")


def test_a_failure_after_the_workbook_was_written_removes_it(contracts, tmp_path, capsys,
                                                             monkeypatch):
    """The forced Generate failure: the IIG workbook is on disk when it fails."""
    def gap(*args, **kwargs):
        assert _emit_files(tmp_path / "out" / FEED), "the workbook should exist by now"
        raise TemplateGapError("forced after emit")

    monkeypatch.setattr(cli, "write_generation_report", gap)
    code = cli.main(contracts)
    captured = capsys.readouterr()
    _assert_skipped(code, captured.out, captured.err, tmp_path, "template gap at feed 1 of 1")


def test_an_earlier_passing_run_then_a_failing_one_leaves_no_workbook(contracts, tmp_path,
                                                                      capsys, monkeypatch):
    assert cli.main(contracts) == 0
    assert _emit_files(tmp_path / "out" / FEED)
    monkeypatch.setattr(cli, "write_generation_report",
                        lambda *a, **k: (_ for _ in ()).throw(TemplateGapError("forced")))
    assert cli.main(contracts) == 1
    assert not _emit_files(tmp_path / "out" / FEED)     # rewritten by the failing run: gone
    capsys.readouterr()


def test_an_uncaught_error_mid_feed_removes_partials_and_still_raises(contracts, tmp_path,
                                                                      capsys, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("forced")

    monkeypatch.setattr(cli, "write_generation_report", boom)
    with pytest.raises(RuntimeError):
        cli.main(contracts)
    assert not _emit_files(tmp_path / "out" / FEED)
    err = capsys.readouterr().err
    assert first_error_line(1, err) == \
        f"{'FAIL':<15} generate — uncaught exception [RuntimeError]"


def test_emit_stage_classification():
    assert run_stages.emit_stage(Path("f/framework/FEED_IIG.xlsx")) == "iig_emit"
    assert run_stages.emit_stage(Path("f/framework/config_inserts.xlsx")) == "dml_emit"
    assert run_stages.emit_stage(Path("f/framework/metadata_inserts.sql")) == "dml_emit"
    assert run_stages.emit_stage(Path("f/ddl/stage.sql")) == "ddl_emit"
    assert run_stages.emit_stage(Path("f/framework/ACCUM_DDL.txt")) == "ddl_emit"
    assert run_stages.emit_stage(Path("f/x_standard_table_creation.txt")) == "ddl_emit"
    assert run_stages.emit_stage(Path("f/module/pipeline.py")) is None
    assert run_stages.emit_stage(Path("f/framework/ADDITION.md")) is None
