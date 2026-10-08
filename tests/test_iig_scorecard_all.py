"""scripts/iig_scorecard.py --all-sheets (multi-table step 7): every IIG sheet
of the real workbook scored, rows paired by key — ADLS by file pattern,
STGDELTA by table, DATA_QUALITY_RULES by (file, RULE_CLASS) through the SAME
workbook's ADLS OBJECT_ID, the schedule by PIPELINE_NAME — a numeric score
per sheet and in total, CREATED_BY / UPDATED_BY never printed."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

from acfc_shapes.pair1 import alias_golden_iig
from codegen import cli
from codegen.config import load_config
from conftest import with_dml
from multi_table_golden import golden_rows, load_golden
from test_m4_acceptance import (
    FULL_DEVIATIONS,
    FULL_OPEN,
    FULL_SEQUENCE,
    GOLDEN_IIG,
    _scoped,
    needs_golden,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import iig_scorecard  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
IIG_V2_SHEETS = ["DATA_FACTORY_PIPELINE_SCHEDULE", "FILE_ADLS_INGESTION_DETAILS",
                 "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET",
                 "ADLS_FIXED_WIDTH_HANDLER", "DATABRICKS_NOTEBOOK_DETAILS",
                 "DATA_QUALITY_RULES", "EMAIL_TEMPLATE_CONFIG"]
SUMMARY = re.compile(r"^(?P<name>[A-Z_]+|TOTAL \(\d+ sheets\)): score (?P<score>\d+\.\d); "
                     r"paired (?P<paired>\d+), real-only (?P<real_only>\d+), "
                     r"generated-only (?P<generated_only>\d+); cells (?P<cells>\d+), ")


def _summaries(out: str) -> dict[str, dict]:
    found = {}
    for line in out.splitlines():
        match = SUMMARY.match(line)
        if match:
            name = "TOTAL" if match["name"].startswith("TOTAL") else match["name"]
            found[name] = {"score": match["score"], "paired": int(match["paired"]),
                           "real_only": int(match["real_only"]),
                           "generated_only": int(match["generated_only"]),
                           "cells": int(match["cells"])}
    return found


def _book(path: Path, sheets: dict[str, tuple[list[str], list[list]]]) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, (headers, rows) in sheets.items():
        ws = workbook.create_sheet(name)
        ws.append(headers)
        for row in rows:
            ws.append(row)
    workbook.save(path)
    return path


def _pair4_golden_xlsx(path: Path) -> Path:
    """IIG_EXPECTED.yaml as a workbook: the iig_v2 sheets and headers in
    template order, the golden's rows; a golden null / "" is a blank cell."""
    tabs = load_config(REPO / "config" / "config.yaml").metadata.templates["iig_v2"].tabs
    golden = load_golden()
    return _book(path, {name: (list(tab.headers),
                               [[row.get(h) or None for h in tab.headers]
                                for row in golden_rows(golden, name)])
                        for name, tab in tabs.items()})


def _run_all(capsys, generated: Path, real: Path, *extra: str) -> str:
    assert iig_scorecard.main(["--all-sheets", "--generated", str(generated),
                               "--real", str(real), *extra]) == 0
    return capsys.readouterr().out


# -- golden against itself: 100.0 everywhere ------------------------------------- #


def _assert_perfect(out: str, row_counts: dict[str, int]) -> None:
    summaries = _summaries(out)
    assert list(summaries) == [*IIG_V2_SHEETS, "TOTAL"]     # all eight, real order
    for name, numbers in summaries.items():
        assert numbers["score"] == "100.0", (name, numbers)
        assert numbers["real_only"] == numbers["generated_only"] == 0, name
    for name, rows in row_counts.items():
        assert summaries[name]["paired"] == rows, name
    assert summaries["TOTAL"]["paired"] == sum(row_counts.values())
    assert "unmatched 0" in out.splitlines()[-1]


@needs_golden
def test_pair1_golden_against_itself_scores_100_on_every_sheet(capsys):
    out = _run_all(capsys, GOLDEN_IIG, GOLDEN_IIG, "--summary-only")
    _assert_perfect(out, {
        "DATA_FACTORY_PIPELINE_SCHEDULE": 4, "FILE_ADLS_INGESTION_DETAILS": 1,
        "ADLS_DELTA_INGESTION_DETAILS": 4, "STGDELTA_STDDELTA_INGESTION_DET": 1,
        "ADLS_FIXED_WIDTH_HANDLER": 3, "DATABRICKS_NOTEBOOK_DETAILS": 3,
        "DATA_QUALITY_RULES": 8, "EMAIL_TEMPLATE_CONFIG": 2})
    assert len(out.splitlines()) == 9                      # 8 sheets + TOTAL, nothing else


def test_pair4_golden_against_itself_scores_100_on_every_sheet(capsys, tmp_path):
    golden = _pair4_golden_xlsx(tmp_path / "pair4_IIG.xlsx")
    out = _run_all(capsys, golden, golden)
    _assert_perfect(out, {
        "DATA_FACTORY_PIPELINE_SCHEDULE": 4, "FILE_ADLS_INGESTION_DETAILS": 1,
        "ADLS_DELTA_INGESTION_DETAILS": 6, "STGDELTA_STDDELTA_INGESTION_DET": 3,
        "ADLS_FIXED_WIDTH_HANDLER": 0, "DATABRICKS_NOTEBOOK_DETAILS": 1,
        "DATA_QUALITY_RULES": 6, "EMAIL_TEMPLATE_CONFIG": 2})
    # Compact by default: a perfect pair prints its row headers and per-row
    # summaries only — no MATCH line without --matches.
    assert not any(line.startswith("MATCH") for line in out.splitlines())
    assert _summaries(_run_all(capsys, golden, golden, "--matches")) == _summaries(out)


# -- row matching ---------------------------------------------------------------- #

ADLS = ["GROUP_ID", "OBJECT_ID", "SRC_FILE_NAME", "TGT_TABLE_NAME", "LOB", "CREATED_BY"]
DQ = ["GROUP_ID", "OBJECT_ID", "SEQUENCE_NO", "RULE_CLASS", "INPUT_PARAM", "UPDATED_BY"]
STG = ["OBJECT_NAME", "TGT_TABLE_NAME", "TGT_PRIMARY_KEY"]
SCHEDULE = ["PIPELINE_ID", "PIPELINE_NAME", "PIPELINE_FREQUENCY"]


def _matching_pair(tmp_path: Path) -> tuple[Path, Path]:
    """Real: objects SYN-OBJ-001..003 = files A, B, C. Generated: rows in
    another order, objects numbered 1..4 = C, A, B and an EXTRA file D; the
    DQ rows follow the generated numbering (so OBJECT_IDs never line up), the
    two DateFormatRule rows of file C swapped in sheet order; tables aliased
    (cv_ = sd_), the schedule reversed."""
    real = _book(tmp_path / "real.xlsx", {
        "DATA_FACTORY_PIPELINE_SCHEDULE": (SCHEDULE, [
            ["SYN-PL-1", "PL_GMSTR_X", "Monthly"], ["SYN-PL-2", "PL_MSTR_X", "Monthly"],
            ["SYN-PL-3", "PL_File_X_ADLS_To_Delta_Incr", "Monthly"]]),
        "ADLS_DELTA_INGESTION_DETAILS": (ADLS, [
            ["SYN-GRP-1", "SYN-OBJ-001", "A_*.txt", "sd_dtl", "110", "person-a"],
            ["SYN-GRP-1", "SYN-OBJ-002", "B_*.txt", "sd_dtl", "120", "person-b"],
            ["SYN-GRP-1", "SYN-OBJ-003", "C_*.txt", "sd_dtl", "210", "person-c"]]),
        "STGDELTA_STDDELTA_INGESTION_DET": (STG, [
            ["NB", "sd_hdr", "NA"], ["NB", "sd_dtl", "MEMBER_ID"]]),
        "DATA_QUALITY_RULES": (DQ, [
            ["SYN-GRP-1", "SYN-OBJ-001", "1", "DateFormatRule", "fmt-a", "person-a"],
            ["SYN-GRP-1", "SYN-OBJ-001", "2", "DataTypeCastRule", "cast-a", "person-a"],
            ["SYN-GRP-1", "SYN-OBJ-002", "1", "DateFormatRule", "fmt-b", "person-b"],
            ["SYN-GRP-1", "SYN-OBJ-003", "1", "DateFormatRule", "fmt-c1", "person-c"],
            ["SYN-GRP-1", "SYN-OBJ-003", "2", "DateFormatRule", "fmt-c2", "person-c"]]),
    })
    generated = _book(tmp_path / "gen_IIG.xlsx", {
        "DATA_FACTORY_PIPELINE_SCHEDULE": (SCHEDULE, [
            [None, "PL_File_X_ADLS_To_Delta_Incr", "Monthly"], [None, "PL_MSTR_X", "Monthly"],
            [None, "PL_GMSTR_X", "Monthly"]]),
        "ADLS_DELTA_INGESTION_DETAILS": (ADLS, [
            [None, "1", "C_*.txt", "cv_dtl", "210", "RFCSYN-1"],
            [None, "2", "A_*.txt", "cv_dtl", "110", "RFCSYN-1"],
            [None, "3", "B_*.txt", "cv_dtl", "120", "RFCSYN-1"],
            [None, "4", "D_*.txt", "cv_dtl", "310", "RFCSYN-1"]]),
        "STGDELTA_STDDELTA_INGESTION_DET": (STG, [
            ["NB", "cv_dtl", "MEMBER_ID"], ["NB", "cv_hdr", "NA"]]),
        "DATA_QUALITY_RULES": (DQ, [
            [None, "1", "2", "DateFormatRule", "fmt-c2", "RFCSYN-1"],
            [None, "1", "1", "DateFormatRule", "fmt-c1", "RFCSYN-1"],
            [None, "2", "2", "DataTypeCastRule", "cast-a", "RFCSYN-1"],
            [None, "2", "1", "DateFormatRule", "fmt-a", "RFCSYN-1"],
            [None, "3", "1", "DateFormatRule", "fmt-b", "RFCSYN-1"]]),
    })
    return real, generated


def test_rows_pair_by_key_not_by_position_or_object_id(tmp_path):
    real, generated = _matching_pair(tmp_path)
    aliases = [tuple(a.split("=", 1)) for a in iig_scorecard.DEFAULT_ALIASES]
    results, _lines = iig_scorecard.score_all(generated, real, None, aliases)
    by_name = {r.name: r for r in results}
    # (real worksheet row, generated worksheet row); data starts at row 2.
    adls = by_name["ADLS_DELTA_INGESTION_DETAILS"]
    assert adls.pairs == [(2, 3), (3, 4), (4, 2)]              # A, B, C by SRC_FILE_NAME
    assert adls.generated_only == [5] and adls.real_only == []  # D: the extra file
    assert adls.counts["unmatched"] == len(ADLS)
    dq = by_name["DATA_QUALITY_RULES"]
    # (file, RULE_CLASS) via each workbook's own ADLS OBJECT_ID; file C's two
    # DateFormatRule rows pair in SEQUENCE_NO order, not sheet order.
    assert dq.pairs == [(2, 5), (3, 4), (4, 6), (5, 3), (6, 2)]
    assert dq.real_only == dq.generated_only == []
    dq_diffs = [line.split()[1] for line in dq.lines if line.startswith("DIFF")]
    assert set(dq_diffs) == {"OBJECT_ID", "UPDATED_BY"}       # numbering + the audit stamp
    stg = by_name["STGDELTA_STDDELTA_INGESTION_DET"]
    assert stg.pairs == [(2, 3), (3, 2)]                       # by table, cv_ = sd_
    assert stg.counts["diff"] == 0 and stg.counts["alias"] == 2
    schedule = by_name["DATA_FACTORY_PIPELINE_SCHEDULE"]
    assert schedule.pairs == [(2, 4), (3, 3), (4, 2)]          # by PIPELINE_NAME
    assert schedule.counts["open"] == 3                        # the engineer's PIPELINE_IDs


def test_unmatched_rows_are_reported_and_count_against_the_score(tmp_path, capsys):
    real, generated = _matching_pair(tmp_path)
    out = _run_all(capsys, generated, real)
    assert "-- generated r5: generated-only (SRC_FILE_NAME 'D_*.txt'); 6 cells unmatched" in out
    adls = _summaries(out)["ADLS_DELTA_INGESTION_DETAILS"]
    assert (adls["paired"], adls["generated_only"], adls["cells"]) == (3, 1, 4 * len(ADLS))
    # Sheets of the generated workbook only are listed, never scored; a real
    # sheet the generated workbook lacks has every row real-only.
    real_only = _book(tmp_path / "real2.xlsx", {
        "EMAIL_TEMPLATE_CONFIG": (["STATUS", "TEMPLATE_NAME"], [["Success", "X"]])})
    out = _run_all(capsys, generated, real_only, "--summary-only")
    email = _summaries(out)["EMAIL_TEMPLATE_CONFIG"]
    assert (email["score"], email["real_only"], email["paired"]) == ("0.0", 1, 0)
    assert "not in the real workbook (not scored): DATA_FACTORY_PIPELINE_SCHEDULE" in out


def test_a_blank_key_never_decides_but_pairs_with_what_is_left():
    pairs, real_only, gen_only = iig_scorecard.pair_rows(
        [("PL_A",), ("PL_B",)], [("",), ("PL_A",)], [])
    assert (pairs, real_only, gen_only) == ([(0, 1), (1, 0)], [], [])
    pairs, real_only, gen_only = iig_scorecard.pair_rows([("PL_A",)], [("PL_Z",)], [])
    assert (pairs, real_only, gen_only) == ([], [0], [0])     # two different names
    pairs, _r, _g = iig_scorecard.pair_rows([(), ()], [(), ()], [])
    assert pairs == [(0, 0), (1, 1)]                          # a keyless sheet: position


def test_masked_sequence_id_scores_alias():
    lines, counts = iig_scorecard.score({"OBJECT_ID": "3"}, {"OBJECT_ID": "SYN-OBJ-003"}, {}, [])
    assert lines[0].startswith("ALIAS OBJECT_ID") and counts["alias"] == 1
    lines, counts = iig_scorecard.score({"OBJECT_ID": "2"}, {"OBJECT_ID": "SYN-OBJ-003"}, {}, [])
    assert lines[0].startswith("DIFF  OBJECT_ID") and counts["diff"] == 1


# -- withholding ------------------------------------------------------------------ #


def test_created_and_updated_by_are_never_printed_in_all_sheets_mode(tmp_path, capsys):
    real, generated = _matching_pair(tmp_path)
    secrets = ["person-a", "person-b", "person-c", "RFCSYN-1"]
    for flags in ([], ["--matches"], ["--summary-only"]):
        out = _run_all(capsys, generated, real, *flags)
        assert not [s for s in secrets if s in out], flags
    # An aliased audit value (cv_ = sd_) scores ALIAS without the value either.
    real = _book(tmp_path / "r.xlsx", {"EMAIL_TEMPLATE_CONFIG": (
        ["STATUS", "CREATED_BY"], [["Success", "sd_person"], ["Failed", "sd_person"]])})
    generated = _book(tmp_path / "g_IIG.xlsx", {"EMAIL_TEMPLATE_CONFIG": (
        ["STATUS", "CREATED_BY"], [["Failed", "cv_person"], ["Retry", "cv_person"]])})
    out = _run_all(capsys, generated, real, "--matches")
    assert "ALIAS CREATED_BY" in out and "person" not in out


def test_single_sheet_mode_still_needs_real_table(tmp_path):
    real, generated = _matching_pair(tmp_path)
    with pytest.raises(SystemExit) as raised:
        iig_scorecard.main(["--generated", str(generated), "--real", str(real)])
    assert raised.value.code == 2


# -- a real pair-1 framework run against the golden -------------------------------- #


@pytest.fixture(scope="module")
def pair1_scorecard(pair1_config, pair1_spec, tmp_path_factory):
    """The pair-1 framework run of test_m4_acceptance (DML on) and the aliased
    golden it is pinned against."""
    tmp = tmp_path_factory.mktemp("pair1_scorecard")
    cli._generate_feed(pair1_spec, _scoped(with_dml(pair1_config), tmp), dry_run=True,
                       skip_tests=True, output_mode="framework",
                       conventions_profile="acfc_prx", iig_template="iig_v2")
    generated = tmp / "out" / pair1_spec.feed_slug / "framework" / (
        f"{pair1_spec.feed_slug}_IIG.xlsx")
    real = tmp / "golden_IIG.xlsx"
    real.write_bytes(alias_golden_iig(GOLDEN_IIG))
    return generated, real


def _cells(results, status: str) -> set[tuple[str, str]]:
    return {(r.name, line.split()[1]) for r in results for line in r.lines
            if line.startswith(status + " ")}


@needs_golden
def test_generated_pair1_against_the_golden_pairs_every_row(pair1_scorecard, capsys):
    generated, real = pair1_scorecard
    review = generated.with_name(generated.name.replace("_IIG.xlsx", "_IIG_REVIEW.xlsx"))
    assert review.is_file()
    out = _run_all(capsys, generated, real)
    summaries = _summaries(out)
    assert list(summaries) == [*IIG_V2_SHEETS, "TOTAL"]
    for name, numbers in summaries.items():
        # Every golden row finds its generated row; the golden's engineer /
        # environment / audit values stay open in ours, so no sheet reaches 100.
        assert numbers["real_only"] == numbers["generated_only"] == 0, name
        assert 0.0 < float(numbers["score"]) < 100.0, (name, numbers)
    assert summaries["TOTAL"]["paired"] == 26
    # The open cells carry their review-copy owner, not "no review entry".
    assert "owner: no review entry" not in out
    assert "owner: BSA" in out and "owner: Engineer" in out
    # The scorecard agrees with Chunk A's every-cell classification
    # (test_m4_acceptance): a DIFF is a pinned deviation, an ALIAS a masked
    # sequence id, an OPEN cell one the golden fills and ours leaves open.
    aliases = [tuple(a.split("=", 1)) for a in iig_scorecard.DEFAULT_ALIASES]
    results, _lines = iig_scorecard.score_all(generated, real, review, aliases)
    assert _cells(results, "DIFF") <= set(FULL_DEVIATIONS)
    assert _cells(results, "ALIAS") == FULL_SEQUENCE
    assert _cells(results, "OPEN") <= {(s, c) for s, cols in FULL_OPEN.items() for c in cols}
