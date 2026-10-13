"""iig_diff: key-convention visibility (2026-10-13, D1 pair_12 CAQH).

Both templates scored 0.0 with 736 needs_assignment cells: rows on both sides
whose natural KEYS follow different conventions. Now (1) a D1-only section
(console + score.json, never the scrubbed export) lists per sheet the first 5
golden key values beside the first 5 agent ones; (2) the rows the key left
unpaired are paired a second way — by position when both sides left the same
number, else by best cell overlap — and that "positional" score is reported
SEPARATELY; the key-paired score is unchanged.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("iig_diff", REPO / "tools" / "iig_diff.py")
iig_diff = importlib.util.module_from_spec(_spec)
sys.modules["iig_diff"] = iig_diff
_spec.loader.exec_module(iig_diff)

KEYS = REPO / "tools" / "iig_keys.yaml"
PIPE = "DATA_FACTORY_PIPELINE_SCHEDULE"
HEAD = ["PIPELINE_ID", "PIPELINE_NAME", "PIPELINE_FREQUENCY", "PIPELINE_TYPE", "CREATED_BY"]


def _book(path: Path, rows: list[list]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = PIPE
    for row in [HEAD, *rows]:
        ws.append(row)
    wb.save(path)
    return path


def _stamp(folder: Path) -> None:
    (folder / "CODEGEN_BUILD.json").write_text(json.dumps(
        {"sha": "abc1234", "line": "codegen 0.0.test · build abc1234 on b"}), encoding="utf-8")


def test_equal_unpaired_counts_pair_by_position(tmp_path: Path) -> None:
    """Golden PL_<x> vs agent WF_<x>: nothing pairs by key (0.0, as before);
    by position every row lines up."""
    golden = _book(tmp_path / "g.xlsx", [[1, "PL_File_Alpha", "Daily", "Batch", "u1"],
                                         [2, "PL_File_Beta", "Weekly", "Batch", "u1"]])
    agent = _book(tmp_path / "a.xlsx", [[7, "WF_ALPHA", "Daily", "Batch", None],
                                        [8, "WF_BETA", "Weekly", "Batch", None]])
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)
    s = payload["sheets"][PIPE]
    assert s["rows"]["paired"] == 0 and s["comparable_score"] == 0.0      # unchanged
    positional = s["positional"]
    assert positional["method"] == "position" and positional["rows_paired"] == 2
    # PIPELINE_NAME differs, FREQUENCY + TYPE match: 4 of 6 scored cells
    assert positional["counts"]["mismatch"] == 2
    assert positional["score"] == round(100 * 4 / 6, 1)
    assert payload["totals"]["positional_score"] == positional["score"]
    assert payload["totals"]["comparable_score"] == 0.0


def test_unequal_counts_pair_by_best_cell_overlap(tmp_path: Path) -> None:
    golden = _book(tmp_path / "g.xlsx", [[1, "PL_A", "Daily", "Batch", "u1"],
                                         [2, "PL_B", "Weekly", "Stream", "u1"]])
    agent = _book(tmp_path / "a.xlsx", [[7, "WF_B", "Weekly", "Stream", None],
                                        [8, "WF_A", "Daily", "Batch", None],
                                        [9, "WF_C", "Monthly", "Other", None]])
    s = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)["sheets"][PIPE]
    positional = s["positional"]
    assert positional["method"] == "overlap" and positional["rows_paired"] == 2
    # B<->B and A<->A by overlap (frequency + type), WF_C left extra
    assert positional["counts"]["mismatch"] == 2
    assert positional["counts"]["extra-in-agent"] == 3


def test_key_paired_rows_need_no_secondary_pairing(tmp_path: Path) -> None:
    golden = _book(tmp_path / "g.xlsx", [[1, "A", "Daily", "Batch", "u1"]])
    agent = _book(tmp_path / "a.xlsx", [[9, "A", "Daily", "Batch", None]])
    s = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)["sheets"][PIPE]
    assert s["positional"] is None and s["score"] == 100.0


def test_key_samples_in_score_json_and_the_console_not_the_export(tmp_path: Path,
                                                                    capsys) -> None:
    golden = _book(tmp_path / "g.xlsx", [[i, f"PL_File_{i}", "Daily", "Batch", "u1"]
                                         for i in range(1, 8)])
    run = tmp_path / "run"
    run.mkdir()
    _stamp(run)
    agent = _book(run / "a_IIG.xlsx", [[i, f"WF_{i}", "Daily", "Batch", None]
                                       for i in range(1, 8)])
    out, export = tmp_path / "out", tmp_path / "export"
    assert iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out", str(out),
                          "--export-scrubbed", str(export)]) == 0
    printed = capsys.readouterr().out
    samples = json.loads((out / "score.json").read_text(encoding="utf-8"))[
        "sheets"][PIPE]["key_samples"]
    assert samples == {"key": ["PIPELINE_NAME"],
                       "golden": [f"PL_File_{i}" for i in range(1, 6)],
                       "agent": [f"WF_{i}" for i in range(1, 6)]}
    assert "KEY CONVENTIONS (D1 only - unscrubbed" in printed
    assert "PL_File_1" in printed and "| WF_1" in printed and "WF_6" not in printed
    assert "POSITIONAL: score" in printed and "positional 66.7 (position, 7 row(s))" in printed
    for name in ("mismatches.md", "row_keys.md", "SELF_CHECK.md"):
        text = (export / name).read_text(encoding="utf-8")
        assert "positional" not in text.lower() and "KEY CONVENTIONS" not in text
        assert "pos#" not in text and "overlap#" not in text
