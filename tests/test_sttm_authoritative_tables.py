"""post160 (Soham, 2026-11-02): the STTM is authoritative for a feed's table set.

D1 pairs 05 / 08 / 09 FAILed with "contract mismatch ... N tables only in FRD": the
FRD lists stage tables no STTM field maps (prod ground truth for pair_05: only the
STTM's table was deployed). Those FRD tables are now SET ASIDE - never silently:

- the feed's provenance flag ``frd_tables_set_aside:stage`` (the names, full tier),
  which reaches the combined LOG.md "Check before approving" and the IIG review copy;
- one NOTE line with the COUNT only and one non-blocking INPUT_NEEDED open item
  ``feeds[<i>].tables_set_aside`` -> the run reads PASS_WITH_OPEN_INPUTS, never PASS.

Guards: only when the FRD-only stage tables are the feed's one disagreement (unstated
values stay questions). An STTM table the FRD does not name still FAILs; so does an
FRD whose tables the gap fill took FROM the STTM's band (the pair_09 shape - the STTM
does build them, the extractor read fewer: never "build 1 of 36"); and everything
when ``contracts.sttm_authoritative_tables`` is off. Synthetic only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from acfc_shapes import FIXTURE_ROOT
from codegen.config import load_config
from codegen.resolve import resolver
from codegen.resolve.resolver import UNSTATED, mismatch_item
from codegen.run_errors import first_error_line
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
EXTRA = ["feed_5_extra", "feed_5_more"]
PAIR4 = FIXTURE_ROOT / "pair_4"
PAIR4_FRD = PAIR4 / "frd_nb_cob_report.contract.json"
DATE = "2026-11-02"


def _env(tmp: Path, knob: str | None = None) -> dict:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1",
           "CODEGEN_NOTIFICATION_EMAILS": "syn.dl.prodsupport@synthetic.example"}
    overlay = tmp / "overlay.yaml"
    overlay.write_text((f"contracts:\n  sttm_authoritative_tables: {knob}\n" if knob else "")
                       + f"output:\n  dir: {(tmp / 'out').as_posix()}\n"
                       f"  reports_dir: {(tmp / 'reports').as_posix()}\n", encoding="utf-8")
    env["CODEGEN_CONFIG_OVERLAYS"] = str(overlay)
    return env


def _run(args: list[str], env: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "codegen.cli", *args], capture_output=True,
                          text=True, encoding="utf-8", check=False, env=env, cwd=cwd)


def _family_e(tmp: Path, tables_of) -> tuple[Path, Path]:
    """The family-E chain of test_table_set_mismatch: extract-sttm on the
    synthetic workbook, then the FRD's stage tables replaced by ``tables_of(old)``."""
    frd = family_e_frd(tmp / "frd.json")
    done = _run(["extract-sttm", "--workbook",
                 str(family_e_workbook(tmp / "p3.xlsx", [None])), "--frd-contract", str(frd),
                 "--out", str(tmp / "sttm.json"), "--config", str(CONFIG)], _env(tmp), tmp)
    assert done.returncode == 0, done.stdout + done.stderr
    data = json.loads(frd.read_text(encoding="utf-8"))
    target = data["feeds"][0]["stage_target"]
    target["tables"] = tables_of(target["tables"])
    frd.write_text(json.dumps(data), encoding="utf-8")
    return frd, tmp / "sttm.json"


def _generate(tmp: Path, frd: Path, sttm: Path, knob: str | None = None,
              extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return _run(["generate", "--config", str(CONFIG), "--frd", str(frd), "--sttm", str(sttm),
                 "--dry-run", "--skip-tests", "--output-mode", "framework", "--profile",
                 "acfc_prx", "--iig-template", "iig_v2", *(extra or [])],
                _env(tmp, knob), REPO)


def _lines(text: str, label: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(label)]


# ---- the fallback through the CLI ------------------------------------------------


def test_frd_only_stage_tables_are_set_aside_loudly(tmp_path):
    frd, sttm = _family_e(tmp_path, lambda old: [*old, *EXTRA])
    done = _generate(tmp_path, frd, sttm)
    assert done.returncode == 0, done.stdout + done.stderr
    out = done.stdout + done.stderr
    outcome = _lines(out, "OUTCOME")
    assert outcome and "PASS_WITH_OPEN_INPUTS" in outcome[0]       # never a plain PASS
    note = [n for n in _lines(out, "NOTE") if "feeds[0].tables_set_aside" in n]
    assert len(note) == 1 and "2 FRD stage tables" in note[0]
    assert not any(name in note[0] for name in EXTRA)              # count only on the line
    manifest = json.loads((tmp_path / "out" / "CODEGEN_STAGES.json").read_text("utf-8"))
    assert "feeds[0].tables_set_aside" in json.dumps(manifest)     # the open item
    ddl = "".join(p.read_text("utf-8") for p in (tmp_path / "out").rglob("*_DDL.txt"))
    assert ddl and not any(name in ddl for name in EXTRA)          # not built
    logs = "".join(p.read_text("utf-8") for p in (tmp_path / "out").rglob("*_LOG.md"))
    assert "frd_tables_set_aside:stage: 2 FRD stage table(s)" in logs
    report = "".join(p.read_text("utf-8") for p in (tmp_path / "reports").rglob("*.md"))
    assert all(name in report for name in EXTRA)                   # the names: full tier


def test_an_sttm_table_the_frd_does_not_name_still_fails(tmp_path):
    frd, sttm = _family_e(tmp_path, lambda old: list(EXTRA))       # the STTM's table dropped
    done = _generate(tmp_path, frd, sttm)
    assert done.returncode == 1
    assert first_error_line(done.returncode, done.stderr, done.stdout) == (
        f"{'FAIL':<15} generate — contract mismatch, feed 1 of 1: "
        "2 tables only in FRD, 1 table only in STTM [ContractMismatchError]")


def test_the_knob_off_is_the_pre_post160_mismatch(tmp_path):
    frd, sttm = _family_e(tmp_path, lambda old: [*old, *EXTRA])
    done = _generate(tmp_path, frd, sttm, knob="false")
    assert done.returncode == 1
    assert first_error_line(done.returncode, done.stderr, done.stdout) == (
        f"{'FAIL':<15} generate — contract mismatch, feed 1 of 1: "
        "2 tables only in FRD [ContractMismatchError]")
    assert "tables_set_aside" not in done.stdout


@pytest.mark.skipif(not PAIR4_FRD.exists(), reason="pair_4 fixture absent")
def test_a_segmented_feed_sets_aside_an_extra_frd_table_too(tmp_path):
    """The pair_08 shape: a header / detail / trailer feed whose FRD names one
    more stage table than its segments map."""
    frd = tmp_path / "frd.json"
    data = json.loads(PAIR4_FRD.read_text(encoding="utf-8"))
    data["feeds"][0]["stage_target"]["tables"].append("nb_cob_report_extra")
    frd.write_text(json.dumps(data), encoding="utf-8")
    env = _env(tmp_path)
    env["CODEGEN_CONFIG_OVERLAYS"] = ";".join(           # the variable's separator
        [str(PAIR4 / "config_overlay.yaml"), env["CODEGEN_CONFIG_OVERLAYS"]])
    done = _run(["extract-sttm", "--workbook", str(PAIR4 / "sttm_nb_cob_report.xlsx"),
                 "--frd-contract", str(frd), "--out", str(tmp_path / "sttm.json"),
                 "--config", str(CONFIG), "--generated-date", DATE], env, tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    gen = _run(["generate", "--config", str(CONFIG), "--frd", str(frd), "--sttm",
                str(tmp_path / "sttm.json"), "--dry-run", "--skip-tests", "--output-mode",
                "framework"], env, REPO)
    out = gen.stdout + gen.stderr
    assert "contract mismatch" not in out, out
    assert any("tables_set_aside" in n and "1 FRD stage table " in n
               for n in _lines(out, "NOTE")), out


# ---- the guard, unit level -------------------------------------------------------


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG)


def test_unstated_values_stay_questions_beside_a_set_aside(config):
    stage = mismatch_item("table.frd_only", "x", names=["t_x"])
    unstated = mismatch_item(UNSTATED, "y", field="file_format")
    errors, flags = [stage, unstated], []
    assert resolver._set_aside_frd_tables(errors, stage, config, flags) == ["t_x"]
    assert errors == [unstated] and errors[0] is unstated
    assert flags and flags[0].startswith("frd_tables_set_aside:stage: 1 FRD stage table(s)")


@pytest.mark.parametrize("kind", ["table.sttm_only", "table.conflict", "segment.frd_only",
                                  "value.conflict", "table.frd_only"])
def test_any_other_disagreement_keeps_the_mismatch(config, kind):
    stage = mismatch_item("table.frd_only", "x", names=["t_x"])
    other = mismatch_item(kind, "other text", names=["t_y"])   # e.g. the standard layer
    errors, flags = [stage, other], []
    assert resolver._set_aside_frd_tables(errors, stage, config, flags) == []
    assert errors == [stage, other] and not flags


def test_equal_text_is_removed_by_identity_not_by_value(config):
    stage = mismatch_item("table.frd_only", "same", names=["t_x"])
    twin = mismatch_item(UNSTATED, "same", field="file_format")   # == stage as a str
    errors = [twin, stage]
    resolver._set_aside_frd_tables(errors, stage, config, [])
    assert len(errors) == 1 and errors[0] is twin


def test_tables_the_gap_fill_took_from_the_sttm_are_never_set_aside(config):
    stage = mismatch_item("table.frd_only", "x", names=[f"t_{i}" for i in range(35)])
    errors, flags = [stage], []
    assert resolver._set_aside_frd_tables(errors, stage, config, flags,
                                          tables_from_sttm=True) == []
    assert errors == [stage] and not flags


def test_an_frd_whose_tables_came_from_the_sttm_still_fails(tmp_path):
    """The pair_09 shape through the CLI: the FRD's stage tables carry the layout
    stage's gap-fill flag (taken from the STTM band), more than the STTM feed
    maps - a contract mismatch, not a set-aside."""
    frd, sttm = _family_e(tmp_path, lambda old: [*old, *EXTRA])
    data = json.loads(frd.read_text(encoding="utf-8"))
    data.setdefault("extraction_flags", []).append(
        "frd_unstated:feeds[0].stage_target.tables source_used:STTM stage band "
        "(authoritative; never asked)")
    frd.write_text(json.dumps(data), encoding="utf-8")
    done = _generate(tmp_path, frd, sttm)
    assert done.returncode == 1, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) == (
        f"{'FAIL':<15} generate — contract mismatch, feed 1 of 1: "
        "2 tables only in FRD [ContractMismatchError]")
    assert "tables_set_aside" not in done.stdout
