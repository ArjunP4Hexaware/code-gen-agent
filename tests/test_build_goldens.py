"""tools/build_goldens.py de-duplication (round 4, 2026-10-12).

Every GROUP_ID export of a pair repeats the pair-wide sheets (schedule,
email, all_files): the union counted each row once per export (pair_2: 36
schedule rows for 6 pipelines). The build now collapses rows that are equal
on every column outside iig_diff's IGNORED set and records the contributing
exports in ``_source_group_ids``.

Synthetic exports from the scrubbed SFMC reference (two groups): each group's
export holds its own rows of the grouped sheets and a FULL copy of the
pair-wide sheets, the second copy with different audit stamps (ignored
columns must not defeat the de-duplication).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
SFMC = REPO / "fixtures" / "reference" / "SFMC_IIG.xlsx"
_spec = importlib.util.spec_from_file_location("build_goldens",
                                               REPO / "tools" / "build_goldens.py")
build_goldens = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_goldens)

GROUPS = ["SYN-GRP-001", "SYN-GRP-002"]


def _exports(tmp_path: Path) -> Path:
    src = openpyxl.load_workbook(SFMC, data_only=True)
    out = tmp_path / "goldens"
    out.mkdir()
    for n, gid in enumerate(GROUPS):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for ws in src.worksheets:
            rows = [list(r) for r in ws.iter_rows(values_only=True)]
            header, body = rows[0], rows[1:]
            target = wb.create_sheet(ws.title)
            target.append(header)
            if "GROUP_ID" in header:
                g = header.index("GROUP_ID")
                body = [r for r in body if r[g] == gid]
            for r in body:
                if n == 1:   # the second export's copy: other audit stamps
                    for col in ("CREATED_BY", "UPDATED_BY", "CREATED_DATE", "UPDATED_DATE"):
                        if col in header:
                            r[header.index(col)] = f"SYN-EXPORT-{n}"
                target.append(r)
        wb.save(out / f"pair_sfmc_{gid}.xlsx")
    return out


def _rows(path: Path, sheet: str) -> tuple[list, list[list]]:
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    return rows[0], rows[1:]


def test_pair_wide_rows_collapse_and_keep_their_sources(tmp_path, capsys):
    goldens = _exports(tmp_path)
    report = build_goldens.build_one_pair(
        "sfmc", GROUPS, goldens, None, tmp_path / "no_index.csv", None, None,
        tmp_path / "out")
    printed = capsys.readouterr().out
    golden = tmp_path / "out" / "sfmc_iig_golden.xlsx"
    dedup = report["dedup"]

    # schedule: the two file pipelines AND their master / grand master (D1 post44
    # item 4: the parents of the pair's pipelines are the pair's too) arrived once
    # per export, audit stamps differing
    assert dedup["DATA_FACTORY_PIPELINE_SCHEDULE"] == {
        "before": 8, "after": 4, "contributing_groups": {2: 4}, "group_ids": []}
    header, rows = _rows(golden, "DATA_FACTORY_PIPELINE_SCHEDULE")
    src = header.index(build_goldens.SOURCE_COLUMN)
    assert {r[src] for r in rows} == {",".join(GROUPS)}
    # grouped sheets: each row from its own export, untouched
    assert dedup["ADLS_DELTA_INGESTION_DETAILS"] == {
        "before": 1, "after": 1, "contributing_groups": {1: 1}, "group_ids": ["SYN-GRP-001"]}
    assert dedup["STGDELTA_STDDELTA_INGESTION_DET"]["group_ids"] == ["SYN-GRP-002"]
    assert dedup["DATA_QUALITY_RULES"]["before"] == dedup["DATA_QUALITY_RULES"]["after"] == 6
    assert dedup["DATABRICKS_NOTEBOOK_DETAILS"]["contributing_groups"] == {1: 2}
    # the all_files filter ran first; its survivors were each seen twice
    files = dedup["ALL_FILES_STATIC_INFORMATION"]
    assert files["after"] * 2 == files["before"] and files["contributing_groups"] == {
        2: files["after"]}
    assert ("sfmc/DATA_FACTORY_PIPELINE_SCHEDULE: dedup 8 -> 4; rows by number of "
            "contributing exports {2: 4}") in printed
    assert "2 parent pipeline(s) kept" in printed
    assert "sfmc/ADLS_DELTA_INGESTION_DETAILS: dedup 1 -> 1" in printed
    assert "GROUP_ID on the rows: ['SYN-GRP-001']" in printed


def test_rows_differing_in_a_scored_column_never_collapse():
    headers = ["PIPELINE_NAME", "PIPELINE_ID", build_goldens.SOURCE_COLUMN]
    rows = [["PL_A", "1", "g1"], ["PL_A", "2", "g2"], ["PL_B", "1", "g1"]]
    kept, counts = build_goldens._dedup(headers, rows, build_goldens._ignored_globs())
    assert kept == [["PL_A", "1", "g1,g2"], ["PL_B", "1", "g1"]]
    assert counts == {1: 1, 2: 1}


def test_iig_diff_never_scores_the_provenance_and_shows_it_in_row_keys(tmp_path, capsys):
    spec = importlib.util.spec_from_file_location("iig_diff", REPO / "tools" / "iig_diff.py")
    iig_diff = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("iig_diff", iig_diff)     # its dataclasses look it up
    spec.loader.exec_module(sys.modules["iig_diff"])
    iig_diff = sys.modules["iig_diff"]
    build_goldens.build_one_pair("sfmc", GROUPS, _exports(tmp_path), None,
                                 tmp_path / "no_index.csv", None, None, tmp_path / "out")
    golden = tmp_path / "out" / "sfmc_iig_golden.xlsx"
    keys_path = REPO / "tools" / "iig_keys.yaml"
    payload, diffs, keys = iig_diff._run_pair(golden, SFMC, tmp_path / "diff", keys_path)
    assert all(c.column != build_goldens.SOURCE_COLUMN for d in diffs for c in d.cells)
    assert all(build_goldens.SOURCE_COLUMN not in d.columns["golden_only"] for d in diffs)
    deny = tmp_path / "deny.txt"
    deny.write_text("# none\n", encoding="utf-8")
    iig_diff.export_scrubbed(diffs, keys, tmp_path / "export", local_denylist=deny, harvest={})
    row_keys = (tmp_path / "export" / "row_keys.md").read_text(encoding="utf-8")
    assert "| golden row | key | status | agent row | source exports |" in row_keys
    schedule = row_keys.split("## DATA_FACTORY_PIPELINE_SCHEDULE", 1)[1].split("\n## ", 1)[0]
    assert schedule.count("| 2: ") == 4           # file pipelines + masters, both exports


def test_the_grand_master_and_master_above_the_pairs_pipelines_are_kept():
    """D1 post44 item 4: the corpus has a grand master / master for every group;
    the schedule filter keeps the pair's pipelines and every parent above them
    (PARENT_PIPELINE_ID, transitively; ids as text, '1.0' = '1'), never an
    unrelated pipeline."""
    headers = ["PIPELINE_ID", "PARENT_PIPELINE_ID", "PIPELINE_DESCRIPTION"]
    rows = [[11, 8.0, "file to stage"], [12, 8, "stage to standard"], [8, 9.0, "master"],
            [9.0, 0, "grand master"], [21, 7, "another group"], [7, 0, "its grand master"]]
    scope = build_goldens._with_ancestors(headers, rows, {"11", "12"})
    assert scope == {"11", "12", "8", "9", "9.0"}
    kept, dropped = build_goldens._filter_by_pipeline_id(headers, rows, scope)
    assert [r[0] for r in kept] == [11, 12, 8, 9] and dropped == 2
