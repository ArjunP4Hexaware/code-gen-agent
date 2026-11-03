"""D1 post51 pair_05: a Segment column reading 'NA' (and blank / '-') failed
with "segment spelling(s) ['NA'] are outside the Header/Detail/Trailer
vocabulary". Those cells say "no segment": the sheet is unsegmented unless
one real segment word is present (extractor.discovery.unsegmented_markers)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.extract import extract_contract
from codegen.run_errors import first_error_line
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("cells", [["NA"], ["NA", None, "-"], ["n/a", "None"]])
def test_marker_only_segment_cells_extract_unsegmented(config, tmp_path, cells):
    workbook = family_e_workbook(tmp_path / "p5.xlsx", cells)
    contract = extract_contract(workbook, family_e_frd(tmp_path / "frd.json"), config,
                                generated_date="2026-01-01")
    (feed,) = contract.feeds
    assert feed.field_count == 6
    assert {f.record_segment for f in feed.fields} == {None}
    assert feed.stage.table == "feed_5_dtl"
    assert [a.column for a in feed.audit_columns] == ["SRC_FILE_NAME", "REC_CREATION_TIME"]
    assert any("unsegmented_markers" in n and "read as unsegmented" in n
               for n in contract.notes)


def test_markers_are_configuration(config, tmp_path):
    disc = config.extractor.discovery.model_copy(update={"unsegmented_markers": []})
    narrowed = config.model_copy(update={"extractor": config.extractor.model_copy(
        update={"discovery": disc})})
    workbook = family_e_workbook(tmp_path / "p5.xlsx", ["NA"])
    with pytest.raises(Exception, match="outside the Header/Detail/Trailer vocabulary"):
        extract_contract(workbook, family_e_frd(tmp_path / "frd.json"), narrowed,
                         generated_date="2026-01-01")


def _extract(tmp_path: Path, cells: list) -> subprocess.CompletedProcess:
    workbook = family_e_workbook(tmp_path / "p5.xlsx", cells)
    frd = family_e_frd(tmp_path / "frd.json")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    return subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(frd), "--out", str(tmp_path / "sttm.json"),
         "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)


def test_pair05_shape_exits_zero_through_the_cli(tmp_path):
    done = _extract(tmp_path, ["NA", None, "-"])
    assert done.returncode == 0, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None


def test_a_marker_beside_a_real_segment_still_fails_with_coordinates(tmp_path):
    # Detail rows plus 'NA' rows: the NA rows cannot be placed in a segment.
    done = _extract(tmp_path, ["Detail", "NA"])
    assert done.returncode == 1
    assert first_error_line(done.returncode, done.stderr, done.stdout) == (
        f"{'FAIL':<15} extract-sttm — STTM record-type spelling outside the vocabulary at "
        "STTM sheet 2 row 13 col 9 [ExtractionError]")
