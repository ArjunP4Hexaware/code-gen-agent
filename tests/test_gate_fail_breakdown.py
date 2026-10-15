"""D1 post51 pair_01: "FAIL <feed> — 139 flag(s); ... derivations=FAIL". The
gate is NOT loosened; the run now says what failed. The full report (inside
ACFC) lists the flags grouped by type; the coordinates tier (pushed) carries
counts only — flags per type and the failed check's findings per rule.

Synthetic reproduction: a Family E pair whose FRD landing path has a space,
so every derived ADLS path fails the derivations path rule."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.gate.derivations import violation_kind
from codegen.run_errors import first_error_line, first_error_line_full, kind_counts
from codegen.run_stages import GATE_FAIL_FILE, QUARANTINE_DIR
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
FEED = "feed_5_claims"
LANDING = "inbound/vendor e//x."


@pytest.fixture(scope="module")
def gate_fail_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("gate_fail")
    frd = family_e_frd(root / "frd.json")
    data = json.loads(frd.read_text(encoding="utf-8"))
    data["feeds"][0]["landing_location"] = LANDING
    frd.write_text(json.dumps(data), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1",
           "CODEGEN_NOTIFICATION_EMAILS": "syn.dl.prodsupport@synthetic.example"}
    config = str(REPO / "config" / "config.yaml")
    extracted = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook",
         str(family_e_workbook(root / "p1.xlsx", [None])), "--frd-contract", str(frd),
         "--out", str(root / "sttm.json"), "--config", config],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=root)
    assert extracted.returncode == 0, extracted.stdout + extracted.stderr
    overlay = root / "overlay.yaml"
    overlay.write_text(f"output:\n  dir: {(root / 'out').as_posix()}\n"
                       f"  reports_dir: {(root / 'reports').as_posix()}\n", encoding="utf-8")
    env["CODEGEN_CONFIG_OVERLAYS"] = str(overlay)
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "generate", "--config", config, "--frd", str(frd),
         "--sttm", str(root / "sttm.json"), "--dry-run", "--skip-tests", "--output-mode",
         "framework", "--profile", "acfc_prx", "--iig-template", "iig_v2"],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=REPO)
    return root, done


def test_the_pair01_shape_fails_the_derivations_check(gate_fail_run):
    _root, done = gate_fail_run
    assert done.returncode == 1
    full = first_error_line_full(done.returncode, done.stderr, done.stdout)
    assert full.startswith(f"{'FAIL':<15} {FEED} — ") and "derivations=FAIL" in full


def test_the_coordinates_tier_carries_counts_per_type_only(gate_fail_run):
    _root, done = gate_fail_run
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert line.startswith(
        f"{'FAIL':<15} generate — gate verdict FAIL (complete, review only: quarantined) "
        "at feed 1 of 1 (failed checks: derivations [path_whitespace 9]; flags by type: "
        "path_normalised 9, ")
    assert "vendor" not in line and "inbound" not in line and FEED not in line
    # every flag type of the run is a vocabulary token with a count
    flags = line.split("flags by type: ", 1)[1].rsplit(")", 1)[0]
    assert all(part.rsplit(" ", 1)[1].isdigit() for part in flags.split(", "))


def test_the_full_report_groups_the_flags_by_type(gate_fail_run):
    root, done = gate_fail_run
    report = (root / "reports" / f"{FEED}.md").read_text(encoding="utf-8")
    total = int(first_error_line_full(done.returncode, done.stderr, done.stdout)
                .split(" — ", 1)[1].split(" flag(s)", 1)[0])
    assert f"Flags by type ({total}):" in report
    assert "### `path_normalised` — 9" in report
    section = report.split("### `path_normalised` — 9", 1)[1].split("###", 1)[0]
    assert section.count("\n- path_normalised:") == 9
    assert f"{'GATE_FLAGS':<15} path_normalised — 9" in done.stdout


def test_gate_fail_md_counts_the_findings_and_names_the_iig_diff_step(gate_fail_run):
    root, _done = gate_fail_run
    note = (root / "out" / FEED / QUARANTINE_DIR / GATE_FAIL_FILE).read_text(encoding="utf-8")
    assert "| `derivations` | `path_whitespace` | 9 |" in note
    assert "| `path_normalised` | 9 |" in note
    assert "python tools/iig_diff.py --golden" in note and "--export-scrubbed" in note
    assert "vendor" not in note


def test_kind_counts_keep_vocabulary_only():
    counts = {f"kind_{i:02d}": i + 1 for i in range(14)}
    counts.update({"Has Space": 99, "x" * 70: 99, "neg": 0, "flag": True})
    kept = kind_counts(counts)
    assert list(kept) == [f"kind_{i:02d}" for i in range(13, 1, -1)]
    assert kind_counts(None) == {}


@pytest.mark.parametrize(("problem", "kind"), [
    ("whitespace", "whitespace"), ("empty segment", "empty_segment"),
    ("doubled separator", "doubled_separator"), ("length 300 > 260", "length"),
    ("segment 'x.' ends in punctuation", "segment_punctuation"),
    ("authority 'a.' ends in punctuation", "authority_punctuation"),
    ("no authority after abfss://", "no_authority"), ("line break", "line_break"),
])
def test_violation_kinds_never_carry_the_value(problem, kind):
    assert violation_kind(problem) == kind
