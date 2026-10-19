"""post74 (D1 post73 pair_05): "STTM required element missing (role column) at
STTM sheet 4 row 59 col 15". A mapping row whose target column reads a skip
marker ("Do Not Map", "Not Mapped", "N/A" — the conventions profile's
skip_row_markers) is left out before the required-element checks; the feed
carries ONE skipped_rows flag with the count."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.extract import extract_contract
from codegen.run_errors import first_error_line
from post73_pairs import (
    FIRST_DATA_ROW,
    frd,
    mapping_workbook,
    without_markers,
)

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-01-01"


def _extract(config, tmp_path, overrides):
    return extract_contract(mapping_workbook(tmp_path / "p5.xlsx", overrides),
                            frd(tmp_path / "frd.json"), config, generated_date=DATE)


def test_without_markers_the_row_is_still_no_mapping_row(config, tmp_path):
    # pair_05's shape: stage ColumnName blank, the stage DataType cell 'N/A'. Before
    # post74 (97f42e9) it stopped extract-sttm with "FAIL            extract-sttm —
    # STTM required element missing (role column) at STTM sheet 2 row 14 col 15
    # [ExtractionError]". With no marker list at all, the row names no stage column:
    # not a mapping row (post74 item 3), counted in the same flag.
    contract = _extract(without_markers(config), tmp_path, {2: {"stage_column": None,
                                                                "stage_type": "N/A"}})
    (feed,) = contract.feeds
    assert feed.field_count == 5 and not contract.needs_answers
    (flag,) = [f for f in feed.extraction_flags if f.startswith("skipped_rows:")]
    assert f"1 name no target column (not a mapping row): FEED_5_MAPPING!O{FIRST_DATA_ROW + 2}" \
        in flag


@pytest.mark.parametrize(("cells", "marker_cell"), [
    ({"stage_column": None, "stage_type": "N/A"}, "P"),
    ({"stage_column": "Do Not Map"}, "O"),
    ({"stage_column": None, "stage_type": None, "standard_column": "Not Mapped"}, "Z"),
    ({"stage_column": "not mapped", "stage_type": None}, "O"),
])
def test_a_marked_row_is_skipped_with_one_count_flag(config, tmp_path, cells, marker_cell):
    contract = _extract(config, tmp_path, {2: cells})
    (feed,) = contract.feeds
    assert feed.field_count == 5
    assert "Service Date" not in [f.source_column for f in feed.fields]
    skipped = [f for f in feed.extraction_flags if f.startswith("skipped_rows:")]
    assert len(skipped) == 1
    assert skipped[0].startswith(
        "skipped_rows:feeds[0] — 1 row(s) left out of both layers before the required-element "
        "checks: 1 read a skip marker (conventions profile skip_row_markers): "
        f"FEED_5_MAPPING!{marker_cell}{FIRST_DATA_ROW + 2} ")
    assert not any(f.startswith("field_unmapped:") for f in feed.extraction_flags)


def test_one_flag_per_feed_counts_every_marked_row(config, tmp_path):
    contract = _extract(config, tmp_path, {1: {"stage_column": "Do Not Map"},
                                           3: {"stage_column": None, "stage_type": "N/A"},
                                           4: {"stage_column": None, "stage_type": "n/a"}})
    (feed,) = contract.feeds
    assert feed.field_count == 3
    (flag,) = [f for f in feed.extraction_flags if f.startswith("skipped_rows:")]
    assert " — 3 row(s) left out " in flag and "3 read a skip marker" in flag


def test_a_standard_band_marker_beside_a_real_stage_column_stays_mapped(config, tmp_path):
    contract = _extract(config, tmp_path, {2: {"standard_column": "N/A"}})
    (feed,) = contract.feeds
    assert feed.field_count == 6
    assert not any(f.startswith("skipped_rows:") for f in feed.extraction_flags)


def test_the_markers_are_conventions_profile_configuration(config):
    profile = config.conventions.get("acfc_prx")
    assert profile.skip_row_markers == ["do not map", "not mapped", "n/a"]


def test_pair05_shape_exits_zero_through_the_cli(tmp_path):
    workbook = mapping_workbook(tmp_path / "p5.xlsx", {2: {"stage_column": None,
                                                           "stage_type": "N/A"}})
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(frd(tmp_path / "frd.json")),
         "--out", str(tmp_path / "sttm.json"), "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None
