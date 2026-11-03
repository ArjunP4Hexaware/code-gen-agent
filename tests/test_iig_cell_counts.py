"""post56 (D1 post55 report): "Unpopulated IIG cells" printed the same nine
numbers for a 4-feed / 11-column pair and a 1-feed / 115-column pair — one
workbook counted for both. Each feed now records its own counts in
CODEGEN_STAGES.json (``iig_cells``, run_stages.iig_unpopulated), per sheet over
the data rows the generator wrote: ``open_for_bsa`` (an open cell the inputs
panel asks about), ``empty_other``, and ``template_blanks`` (the old used-range
count, kept one release)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.iig_review import asked_input, used_range_blanks
from codegen.run_stages import iig_unpopulated
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
CONFIG = str(REPO / "config" / "config.yaml")
ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"


def _env(root: Path) -> dict:
    overlay = root / "overlay.yaml"
    overlay.write_text(f"output:\n  dir: {(root / 'out').as_posix()}\n"
                       f"  reports_dir: {(root / 'reports').as_posix()}\n", encoding="utf-8")
    return {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
            # the ACFC overlay names the owed cells (metadata.templates.iig_v2.owed_cells)
            "CODEGEN_SKIP_ENV_OVERLAY": "1",
            "CODEGEN_CONFIG_OVERLAYS": f"{ACFC_OVERLAY};{overlay}",
            "CODEGEN_NOTIFICATION_EMAILS": "syn.dl.prodsupport@synthetic.example"}


def _run(root: Path, workbook: Path, frd: Path) -> tuple[subprocess.CompletedProcess, dict]:
    env = _env(root)
    extracted = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(frd), "--out", str(root / "sttm.json"), "--config", CONFIG],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=root)
    assert extracted.returncode == 0, extracted.stdout + extracted.stderr
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "generate", "--config", CONFIG, "--frd", str(frd),
         "--sttm", str(root / "sttm.json"), "--dry-run", "--skip-tests", "--output-mode",
         "framework", "--profile", "acfc_prx", "--iig-template", "iig_v2"],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr
    (feed,) = iig_unpopulated(root / "out")
    return done, feed


@pytest.fixture(scope="module")
def one_table(tmp_path_factory):
    root = tmp_path_factory.mktemp("one_table")
    return root, *_run(root, family_e_workbook(root / "e.xlsx", [None]),
                       family_e_frd(root / "frd.json"))


@pytest.fixture(scope="module")
def segmented(tmp_path_factory):
    # Family E pair 5: Header / Detail / Trailer, a table each -> more IIG rows
    from acfc_shapes.sttm import build_pair5

    root = tmp_path_factory.mktemp("segmented")
    workbook = root / "p5.xlsx"
    build_pair5().save(workbook)
    tables = ("feed_5_hdr", "feed_5_dtl", "feed_5_trl")
    return root, *_run(root, workbook, family_e_frd(root / "frd.json", tables=tables,
                                                    segments=("Header", "Detail", "Trailer")))


def test_two_feeds_with_different_rows_count_differently(one_table, segmented):
    _r1, _d1, small = one_table
    _r2, _d2, large = segmented
    rows = {name: s["rows"] for name, s in small["iig_cells"]["sheets"].items()}
    more = {name: s["rows"] for name, s in large["iig_cells"]["sheets"].items()}
    assert rows != more and sum(more.values()) > sum(rows.values())
    assert small["iig_cells"]["sheets"] != large["iig_cells"]["sheets"]
    assert small["iig_cells"]["totals"] != large["iig_cells"]["totals"]


@pytest.mark.parametrize("which", ["one_table", "segmented"])
def test_template_blanks_is_the_old_used_range_count(which, request):
    root, _done, feed = request.getfixturevalue(which)
    # post91: the per-feed IIG (the run's combined/ copy holds the same rows)
    (clean,) = [p for p in (root / "out").rglob("*_IIG.xlsx") if "combined" not in p.parts]
    old = used_range_blanks(clean)
    cells = feed["iig_cells"]["sheets"]
    assert {sheet: c["template_blanks"] for sheet, c in cells.items()} == old
    # the emitted rows carry no trailing blank region: the split adds up
    for counts in cells.values():
        assert counts["open_for_bsa"] + counts["empty_other"] == counts["template_blanks"]


@pytest.mark.parametrize("which", ["one_table", "segmented"])
def test_open_for_bsa_is_what_the_inputs_panel_listed(which, request):
    _root, done, feed = request.getfixturevalue(which)
    listed = set(re.findall(r"^INPUT_NEEDED\s+((?:run|feeds)\.\S+)", done.stdout, re.M))
    opened = set(feed["iig_cells"]["open_inputs"])
    assert opened and feed["iig_cells"]["totals"]["open_for_bsa"] >= len(opened)
    # every feed-level input the panel lists leaves its cells open, and nothing
    # else does; a run-level one may be written with its default instead
    assert {k for k in listed if k.startswith("feeds.")} == \
        {k for k in opened if k.startswith("feeds.")}
    assert opened <= listed


def test_asked_input_reads_the_owed_and_environment_notes():
    assert asked_input("iig_owed:DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_START_DATE — x; "
                       "INPUT_NEEDED feeds.<feed>.active_start_date: under inputs", "f1") \
        == "feeds.f1.active_start_date"
    assert asked_input("iig_owed_run:EMAIL_TEMPLATE_CONFIG.EMAIL_TO — q; INPUT_NEEDED "
                       "run.email_to: once for the run", "f1") == "run.email_to"
    assert asked_input("iig_env:ADLS_DELTA_INGESTION_DETAILS.STORAGE_ACCOUNT — environment "
                       "D1 (default) states no storage_account: left open", "f1") \
        == "run.environment.storage_account"
    assert asked_input("iig_corpus:X.Y — a corpus value", "f1") is None
    assert asked_input(None, "f1") is None


def test_the_manifest_carries_counts_only(one_table):
    root, _done, _feed = one_table
    manifest = json.loads((root / "out" / "CODEGEN_STAGES.json").read_text(encoding="utf-8"))
    cells = manifest["feeds"][0]["iig_cells"]
    for counts in cells["sheets"].values():
        assert set(counts) == {"rows", "open_for_bsa", "empty_other", "template_blanks"}
        assert all(isinstance(v, int) for v in counts.values())
