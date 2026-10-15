"""D1 post51 pairs 03 / 04: "contract mismatch for feed '...':" — the post51
line stopped at the colon. Reproduced through the CLI with a synthetic pair
whose FRD names stage tables the STTM never maps: since post52 / post53 the
coordinates tier prints the summary as COUNTS per kind, never the names.

Still exit 1 (FAIL) by decision (2026-10-15): which mismatch kinds become
NEEDS_ANSWERS waits for the D1 counts of pairs 03 / 04 under post55. Note the
FRD contract carries no column list — the resolver's set differences are
tables and segments (``run_errors.MISMATCH_LABELS``), not columns."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from codegen.run_errors import first_error_line, first_error_line_full
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
EXTRA = ["feed_5_extra", "feed_5_more"]


def test_a_table_set_difference_prints_counts_only(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1",
           "CODEGEN_NOTIFICATION_EMAILS": "syn.dl.prodsupport@synthetic.example"}
    config = str(REPO / "config" / "config.yaml")
    frd = family_e_frd(tmp_path / "frd.json")
    extracted = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook",
         str(family_e_workbook(tmp_path / "p3.xlsx", [None])), "--frd-contract", str(frd),
         "--out", str(tmp_path / "sttm.json"), "--config", config],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert extracted.returncode == 0, extracted.stdout + extracted.stderr
    data = json.loads(frd.read_text(encoding="utf-8"))
    data["feeds"][0]["stage_target"]["tables"] += EXTRA
    frd.write_text(json.dumps(data), encoding="utf-8")
    overlay = tmp_path / "overlay.yaml"
    overlay.write_text(f"output:\n  dir: {(tmp_path / 'out').as_posix()}\n"
                       f"  reports_dir: {(tmp_path / 'reports').as_posix()}\n", encoding="utf-8")
    env["CODEGEN_CONFIG_OVERLAYS"] = str(overlay)
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "generate", "--config", config, "--frd", str(frd),
         "--sttm", str(tmp_path / "sttm.json"), "--dry-run", "--skip-tests", "--output-mode",
         "framework", "--profile", "acfc_prx", "--iig-template", "iig_v2"],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=REPO)
    assert done.returncode == 1
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert line == (f"{'FAIL':<15} generate — contract mismatch, feed 1 of 1: "
                    "2 tables only in FRD [ContractMismatchError]")
    full = first_error_line_full(done.returncode, done.stderr, done.stdout)
    assert "(2 tables only in FRD):" in full
    assert all(name in done.stdout for name in EXTRA)          # the bullets: full tier only
    assert not any(name in line for name in EXTRA)
