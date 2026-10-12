"""tools/iig_diff.py — golden vs agent IIG cell diff (step 0 of the IIG scoring work)."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import openpyxl
import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("iig_diff", REPO / "tools" / "iig_diff.py")
iig_diff = importlib.util.module_from_spec(_spec)
sys.modules["iig_diff"] = iig_diff  # dataclasses look their module up
_spec.loader.exec_module(iig_diff)

KEYS = REPO / "tools" / "iig_keys.yaml"
# There is no pair-5 IIG golden in the repo (pair 5 is an STTM-only fixture):
# the sanity test runs on the two real-shape IIG workbooks that exist.
GOLDENS = [
    REPO / "fixtures" / "acfc_shapes" / "pair_1" / "golden" / "RFC_ACCUMULATORS_IIG.xlsx",
    REPO / "fixtures" / "reference" / "SFMC_IIG.xlsx",
]


def _perturb(golden: Path, target: Path, n: int) -> list[tuple[str, str]]:
    """Copy ``golden`` to ``target`` with ``n`` filled, non-key, non-assigned
    cells changed, spread over the sheets; return (sheet, column) per change."""
    keys = iig_diff.load_keys(KEYS)
    wb = openpyxl.load_workbook(golden)
    candidates: list[list] = []
    for ws in wb.worksheets:
        if keys.is_ignored(ws.title):
            continue
        header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
        # key cells re-pair rows and table-name cells re-resolve OBJECT_IDs:
        # changing either is not a cell mismatch
        key = {k.upper() for k in keys.key_for(ws.title) or []}
        key |= {k.upper() for k in keys.object_source(ws.title) or []}
        cells = [
            (ws.title, header[cell.column - 1], cell)
            for row in ws.iter_rows(min_row=2)
            for cell in row
            if cell.column <= len(header)
            and header[cell.column - 1]
            and header[cell.column - 1].upper() not in key
            and not keys.is_assignment(header[cell.column - 1])
            and iig_diff.normalize(cell.value)
        ]
        if cells:
            candidates.append(cells)
    picked = []
    i = 0
    while len(picked) < n:
        sheet_cells = candidates[i % len(candidates)]
        idx = i // len(candidates)
        if idx < len(sheet_cells):
            picked.append(sheet_cells[idx])
        i += 1
    for _, _, cell in picked:
        cell.value = f"{cell.value}_PERTURBED"
    wb.save(target)
    return [(sheet, column) for sheet, column, _ in picked]


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda p: p.parent.name)
def test_self_diff_is_all_exact(golden: Path, tmp_path: Path) -> None:
    if not golden.exists():
        pytest.skip(f"{golden} absent")
    payload = iig_diff.run_pair(golden, golden, tmp_path, KEYS)
    t = payload["totals"]
    assert t["score"] == 100.0
    assert t["exact"] == t["scored_cells"] > 0
    # the only warning a golden may raise against itself: a key it repeats
    # (pair 1's four files load one table, so its DQ key repeats)
    assert all("is not unique" in w for w in payload["warnings"])
    dq = payload["sheets"]["DATA_QUALITY_RULES"]
    assert dq["key"] == ["OBJECT_ID -> table", "RULE_CLASS", "SOURCE_COLUMN"]
    assert dq["unresolved_object_ids"] == {"golden": [], "agent": []}


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda p: p.parent.name)
def test_five_perturbed_cells_are_exactly_five_mismatches(golden: Path, tmp_path: Path) -> None:
    if not golden.exists():
        pytest.skip(f"{golden} absent")
    agent = tmp_path / "agent.xlsx"
    changed = _perturb(golden, agent, 5)
    out = tmp_path / "out"
    iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out", str(out)])

    payload = json.loads((out / "score.json").read_text(encoding="utf-8"))
    t = payload["totals"]
    assert t["mismatch"] == 5
    assert t["missing-in-agent"] == t["extra-in-agent"] == t["normalized"] == 0
    assert t["exact"] == t["scored_cells"] - 5
    per_sheet = {name: s["counts"]["mismatch"] for name, s in payload["sheets"].items()}
    expected: dict[str, int] = {}
    for sheet, _ in changed:
        expected[sheet] = expected.get(sheet, 0) + 1
    assert {k: v for k, v in per_sheet.items() if v} == expected

    wb = openpyxl.load_workbook(out / "diff.xlsx", read_only=True)
    found = [
        (ws.title, row[3])
        for ws in wb.worksheets[1:]
        for row in ws.iter_rows(min_row=2, values_only=True)
        if row[6] == "mismatch"
    ]
    wb.close()
    assert sorted(found) == sorted(changed)

    with (out / "routing.csv").open(encoding="utf-8", newline="") as fh:
        routing = list(csv.DictReader(fh))
    assert list(routing[0]) == ["sheet", "column", "status_summary", "origin_tag"]
    assert all(r["origin_tag"] == "" for r in routing)
    flagged = {(r["sheet"], r["column"]) for r in routing if "mismatch=" in r["status_summary"]}
    assert flagged == set(changed)


@pytest.mark.parametrize(
    ("golden", "agent", "status"),
    [
        ("Weekly", "Weekly", "exact"),
        (None, "", "exact"),
        (1, "1", "exact"),
        ("Weekly", "weekly", "normalized"),
        ("a  b ", "a b", "normalized"),
        ("10.50", "10.5", "normalized"),
        (10.0, "10", "normalized"),
        (None, "NULL", "normalized"),
        ("inbound\\a\\b", "inbound/a/b/", "normalized"),
        ("abfss://c@acct/x//y", "abfss://c@acct/x/y", "normalized"),
        ("Weekly", "Daily", "mismatch"),
        ("007", "7", "mismatch"),
        ("Weekly", None, "missing-in-agent"),
        ("NULL", "x", "extra-in-agent"),
    ],
)
def test_classify(golden, agent, status) -> None:
    assert iig_diff.classify(golden, agent) == status


def _book(path: Path, sheets: dict[str, list[list]]) -> Path:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    wb.save(path)
    return path


PIPE = "DATA_FACTORY_PIPELINE_SCHEDULE"
HEAD = ["PIPELINE_ID", "PIPELINE_NAME", "PIPELINE_FREQUENCY", "CREATED_BY"]


def test_rows_pair_by_key_not_position(tmp_path: Path) -> None:
    golden = _book(
        tmp_path / "g.xlsx", {PIPE: [HEAD, [1, "A", "Daily", "u1"], [2, "B", "Weekly", "u1"]]}
    )
    agent = _book(
        tmp_path / "a.xlsx", {PIPE: [HEAD, [9, "B", "Weekly", None], [8, "A", "Daily", None]]}
    )
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)
    s = payload["sheets"][PIPE]
    assert s["rows"]["paired"] == 2
    assert s["counts"]["mismatch"] == 0
    assert s["counts"]["needs_assignment"] == 4  # PIPELINE_ID + CREATED_BY, never mismatch
    assert s["needs_assignment"]["PIPELINE_ID"] == {
        "cells": 2,
        "golden_filled": 2,
        "agent_filled": 2,
        "equal": 0,
    }
    assert s["score"] == 100.0


def test_created_by_values_are_withheld(tmp_path: Path) -> None:
    golden = _book(tmp_path / "g.xlsx", {PIPE: [HEAD, [1, "A", "Daily", "real.user"]]})
    iig_diff.run_pair(golden, golden, tmp_path / "out", KEYS)
    wb = openpyxl.load_workbook(tmp_path / "out" / "diff.xlsx", read_only=True)
    values = [v for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for v in row]
    wb.close()
    assert "real.user" not in values
    assert "<withheld>" in values


def test_missing_extra_rows_columns_and_sheets(tmp_path: Path) -> None:
    golden = _book(
        tmp_path / "g.xlsx",
        {
            PIPE: [HEAD, [1, "A", "Daily", None], [2, "GONE", "Weekly", None]],
            "EMAIL_TEMPLATE_CONFIG": [["TEMPLATE_NAME", "STATUS"], ["T", "Success"]],
        },
    )
    agent = _book(
        tmp_path / "a.xlsx",
        {
            PIPE: [["PIPELINE_NAME", "NEW_COL"], ["A", "x"], ["NEW", None]],
            "EXTRA_SHEET": [["X"], ["1"]],
        },
    )
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)
    s = payload["sheets"][PIPE]
    assert s["rows"] == {
        "golden": 2,
        "agent": 2,
        "paired": 1,
        "missing-in-agent": 1,
        "extra-in-agent": 1,
    }
    assert s["columns"] == {
        "golden_only": ["PIPELINE_ID", "PIPELINE_FREQUENCY", "CREATED_BY"],
        "agent_only": ["NEW_COL"],
    }
    # paired row: FREQUENCY missing (column absent), NEW_COL extra; the GONE
    # row: NAME + FREQUENCY missing; the NEW row: NAME + NEW_COL extra (a cell
    # neither workbook has — GONE x NEW_COL, NEW x FREQUENCY — is not counted)
    assert s["counts"]["missing-in-agent"] == 1 + 2
    assert s["counts"]["extra-in-agent"] == 1 + 2
    assert payload["sheets"]["EMAIL_TEMPLATE_CONFIG"]["presence"] == "golden-only"
    assert payload["sheets"]["EMAIL_TEMPLATE_CONFIG"]["counts"]["missing-in-agent"] == 2
    assert payload["sheets"]["EXTRA_SHEET"]["key"] == "position"
    assert payload["sheets"]["EXTRA_SHEET"]["counts"]["extra-in-agent"] == 1


def test_duplicate_key_is_flagged(tmp_path: Path) -> None:
    golden = _book(
        tmp_path / "g.xlsx", {PIPE: [HEAD, [1, "A", "Daily", None], [2, "A", "Weekly", None]]}
    )
    payload = iig_diff.run_pair(golden, golden, tmp_path / "out", KEYS)
    s = payload["sheets"][PIPE]
    assert s["key_unique"] == {"golden": False, "agent": False}
    assert s["duplicate_keys"]["golden"] == ["A"]
    assert any("not unique" in w for w in payload["warnings"])
    assert s["counts"]["mismatch"] == 0  # duplicates pair in sheet order


def test_batch_mode(tmp_path: Path) -> None:
    pairs = tmp_path / "pairs"
    (pairs / "p1").mkdir(parents=True)
    rows = {PIPE: [HEAD, [1, "A", "Daily", None]]}
    _book(pairs / "p1" / "p1_golden.xlsx", rows)
    _book(pairs / "p1" / "p1_agent.xlsx", {PIPE: [HEAD, [1, "A", "Weekly", None]]})
    _book(pairs / "p2_golden.xlsx", rows)
    _book(pairs / "p2_agent.xlsx", rows)
    _book(pairs / "lonely_golden.xlsx", rows)
    out = tmp_path / "out"
    assert iig_diff.main(["--batch", str(pairs), "--out", str(out)]) == 0
    summary = json.loads((out / "batch_summary.json").read_text(encoding="utf-8"))
    assert summary["pairs"]["p1"]["totals"]["mismatch"] == 1
    assert summary["pairs"]["p2"]["totals"]["score"] == 100.0
    assert summary["skipped"] == ["lonely: has no agent file"]
    for name in ("p1", "p2"):
        assert {p.name for p in (out / name).iterdir()} == {
            "score.json",
            "diff.xlsx",
            "routing.csv",
        }


ADLS = "ADLS_DELTA_INGESTION_DETAILS"
STG = "STGDELTA_STDDELTA_INGESTION_DET"
DQ = "DATA_QUALITY_RULES"
ADLS_HEAD = ["GROUP_ID", "OBJECT_ID", "OBJECT_NAME", "TGT_TABLE_NAME"]
DQ_HEAD = ["GROUP_ID", "OBJECT_ID", "RULE_CLASS", "SOURCE_COLUMN", "INPUT_PARAM"]


def test_dq_rows_pair_by_resolved_table_not_object_id(tmp_path: Path) -> None:
    # the agent numbers the two objects the other way round (and its groups differ)
    golden = _book(
        tmp_path / "g.xlsx",
        {
            ADLS: [ADLS_HEAD, [10, 1, "o_a", "tbl_a"], [10, 2, "o_b", "tbl_b"]],
            DQ: [
                DQ_HEAD,
                [10, 1, "DateFormatRule", "c1", "p_a"],
                [10, 2, "DateFormatRule", "c1", "p_b"],
            ],
        },
    )
    agent = _book(
        tmp_path / "a.xlsx",
        {
            ADLS: [ADLS_HEAD, [None, 1, "o_b", "tbl_b"], [None, 2, "o_a", "tbl_a"]],
            DQ: [
                DQ_HEAD,
                [None, 1, "DateFormatRule", "c1", "p_b"],
                [None, 2, "DateFormatRule", "c1", "p_a"],
            ],
        },
    )
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)
    dq = payload["sheets"][DQ]
    assert dq["key"] == ["OBJECT_ID -> table", "RULE_CLASS", "SOURCE_COLUMN"]
    assert dq["rows"]["paired"] == 2
    assert dq["counts"]["mismatch"] == 0  # INPUT_PARAM followed its table, not its id
    assert dq["unresolved_object_ids"] == {"golden": [], "agent": []}
    assert payload["totals"]["score"] == 100.0


def test_object_id_resolves_within_its_group_first(tmp_path: Path) -> None:
    keys = iig_diff.load_keys(KEYS)
    book = _book(
        tmp_path / "g.xlsx",
        {
            ADLS: [ADLS_HEAD, [10, 1, "o_a", "tbl_stage"]],
            STG.lower(): [ADLS_HEAD, [11, 1, "o_s", "tbl_std"]],  # sheet matched caselessly
        },
    )
    tables = iig_diff.ObjectTables(iig_diff.read_workbook(book, keys), keys)
    canon = {"GROUP_ID": "GROUP_ID", "OBJECT_ID": "OBJECT_ID"}
    assert tables.table_for({"GROUP_ID": 10, "OBJECT_ID": 1}, canon) == "tbl_stage"
    assert tables.table_for({"GROUP_ID": 11, "OBJECT_ID": "1"}, canon) == "tbl_std"
    # group unknown: OBJECT_ID 1 names two tables -> unresolved
    assert tables.table_for({"GROUP_ID": 99, "OBJECT_ID": 1}, canon) is None
    assert tables.table_for({"OBJECT_ID": 1}, {"OBJECT_ID": "OBJECT_ID"}) is None


def test_unresolved_object_ids_pair_by_position_and_are_flagged(tmp_path: Path) -> None:
    golden = _book(
        tmp_path / "g.xlsx",
        {
            ADLS: [ADLS_HEAD, [10, 1, "o_a", "tbl_a"]],
            DQ: [DQ_HEAD, [10, 1, "R", "c1", "p1"], [10, 7, "R", "c1", "p7"]],
        },
    )
    agent = _book(
        tmp_path / "a.xlsx",
        {
            ADLS: [ADLS_HEAD, [1, 1, "o_a", "tbl_a"]],
            DQ: [DQ_HEAD, [1, 1, "R", "c1", "p1"], [1, 8, "R", "c1", "p8"]],
        },
    )
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS)
    dq = payload["sheets"][DQ]
    assert dq["unresolved_object_ids"] == {"golden": ["7"], "agent": ["8"]}
    assert dq["rows"]["paired"] == 2
    assert dq["counts"]["mismatch"] == 1  # p7 vs p8, paired by position
    assert any("OBJECT_ID not resolved" in w for w in payload["warnings"])


def test_framework_table_names_match_iig_sheet_names() -> None:
    keys = iig_diff.load_keys(KEYS)
    assert keys.key_for("stgdelta_stddelta_ingestion_details") == ["OBJECT_NAME", "TGT_TABLE_NAME"]
    assert keys.object_source("rdbms_adls_ingestion_details") is not None
