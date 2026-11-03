"""post57 (D1 post55 pair_01 IIG diff, score 3.2 / 710 cells): four scorer rules.

(a) an identity that carries a NAME (TGT_TABLE_NAME / TGT_TABLE / @file) which
    differs, both sides ONE feed and ONE flow: the rows left over pair by feed +
    flow + row order — the name is one mismatch cell, not an unpaired row each side;
(b) a column the agent's IIG template version has and the golden's sheet lacks is
    ``template-only``: never scored, listed once in the HEADERS section;
(c) a date equals the same date at midnight ("9999-12-31" == "9999-12-31 00:00:00");
(d) record-segment codes compare through the conventions profile's
    ``segment_codes`` (hddr / det / trlr == header / details / trailer), in the
    identity and in the cell.

And ``tools/iig_rescore_export.py`` rebuilds a scrubbed export so a score can be
re-run at home: a synthetic export re-scores to the export's own numbers."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


iig_diff = _load("iig_diff")
rescore = _load("iig_rescore_export")

KEYS = REPO / "tools" / "iig_keys.yaml"
TEMPLATE = iig_diff.template_headers()["iig_v2"]
PIPE, ADLS, FIXED = ("DATA_FACTORY_PIPELINE_SCHEDULE", "ADLS_DELTA_INGESTION_DETAILS",
                     "ADLS_FIXED_WIDTH_HANDLER")
# Template columns the golden's schedule lacks (on D1 the ACFC overlay's PROCESS_NAME
# ... IsFileCopyReqFlag; the suite runs without the overlay, so two base columns)
TEMPLATE_ONLY = ["ESTIMATED_START_TIME", "APPLICATION_NAME"]


def _sheet(ws, headers: list[str], rows: list[dict]) -> None:
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])


def _book(path: Path, rows: dict[str, list[dict]], *, golden: bool) -> Path:
    """Every iig_v2 sheet with its template headers (the golden's schedule
    without the template-only columns); ``rows`` per sheet."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, headers in TEMPLATE.items():
        if golden and name == PIPE:
            headers = [h for h in headers if h not in TEMPLATE_ONLY]
        _sheet(wb.create_sheet(name), headers, rows.get(name, []))
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def _adls(table: str, file: str) -> dict:
    return {"OBJECT_NAME": file, "TGT_TABLE_NAME": table, "SRC_FILE_NAME": file,
            "SRC_FORMAT": "txt", "TGT_LOAD_OPTION": "Overwrite"}


def _fixed(table: str, segment: str, cols: str) -> dict:
    return {"SEGMENT": segment, "TGT_TABLE": table, "COL": cols, "SEGMNT_TYP": "SS"}


def _pair(tmp_path: Path, *, agent_tables=("syn_tbl_b", "syn_tbl_b"),
          agent_files=("FEED_B_*.txt", "FEED_B2_*.txt")) -> tuple[Path, Path]:
    golden = _book(tmp_path / "golden.xlsx", {
        PIPE: [{"PIPELINE_DESCRIPTION": "Raw to Stage", "PIPELINE_FREQUENCY": "Daily",
                "ACTIVE_FLAG": "Y", "ACTIVE_END_DATE": "9999-12-31"}],
        ADLS: [_adls("syn_tbl_a", "FEED_A_*.txt"), _adls("syn_tbl_a", "FEED_A2_*.txt")],
        FIXED: [_fixed("syn_tbl_f", "hddr", "SEG_ID,REC"), _fixed("syn_tbl_f", "trlr", "SEG_ID")],
    }, golden=True)
    run = tmp_path / "run"
    agent = _book(run / "feed_x" / "feed_x_IIG.xlsx", {
        PIPE: [{"PIPELINE_DESCRIPTION": "Raw to Stage", "PIPELINE_FREQUENCY": "Daily",
                "ACTIVE_FLAG": "Y",
                "ACTIVE_END_DATE": dt.datetime(9999, 12, 31, 0, 0, 0),
                "APPLICATION_NAME": "SYN_APP"}],
        ADLS: [_adls(t, f) for t, f in zip(agent_tables, agent_files, strict=True)],
        FIXED: [_fixed("syn_tbl_f", "header", "SEG_ID,REC"),
                _fixed("syn_tbl_f", "trailer", "SEG_ID")],
    }, golden=False)
    (run / "CODEGEN_BUILD.json").write_text(json.dumps(
        {"sha": "abc1234", "line": "codegen 0.0.test · build abc1234 on b"}), encoding="utf-8")
    return golden, agent


def _score(tmp_path: Path, golden: Path, agent: Path) -> dict:
    return iig_diff.run_pair(golden, agent, tmp_path / "out", KEYS, group_index=[])


def test_a_differing_table_name_pairs_by_feed_flow_and_order(tmp_path: Path) -> None:
    payload = _score(tmp_path, *_pair(tmp_path))
    s = payload["sheets"][ADLS]
    assert s["pairing"]["order"] == 2 and s["unpaired"] == {"golden": 0, "agent": 0}
    assert s["column_counts"]["TGT_TABLE_NAME"]["mismatch"] == 2     # ONE cell per row
    assert s["rows"]["missing-in-agent"] == 0 and s["rows"]["extra-in-agent"] == 0
    assert any("paired by feed + flow + row order" in w for w in s["warnings"])
    assert payload["totals"]["pairing"]["order"] == 2


def test_order_pairing_only_with_one_feed_and_one_flow(tmp_path: Path) -> None:
    golden, agent = _pair(tmp_path)
    keys = iig_diff.load_keys(KEYS)
    a = iig_diff.read_agent_workbooks([agent], keys)
    g = iig_diff.read_workbook(golden, keys)
    # an identity without a name component keeps the old rule (rows unpaired)
    plain = iig_diff.replace(keys, name_components=())
    diffs = {d.name: d for d in iig_diff.diff_workbooks(golden, agent, plain, group_index=[])}
    assert diffs[ADLS].pairing["order"] == 0 and diffs[ADLS].unpaired == {"golden": 2,
                                                                           "agent": 2}
    assert len(g[ADLS].rows) == len(a[ADLS].rows) == 2


def test_template_only_columns_are_not_scored_and_listed_once(tmp_path: Path) -> None:
    payload = _score(tmp_path, *_pair(tmp_path))
    s = payload["sheets"][PIPE]
    assert s["columns"]["template_only"] == TEMPLATE_ONLY
    assert s["counts"]["template-only"] == len(TEMPLATE_ONLY)      # one row
    assert s["counts"]["extra-in-agent"] == 0
    assert not any(c in s["column_counts"] for c in TEMPLATE_ONLY)
    lines = iig_diff.header_lines(payload["headers"])
    listed = [ln for ln in lines if "template-only (not scored)" in ln]
    assert listed == [f"  {PIPE} vs golden: template-only (not scored) "
                      + ", ".join(TEMPLATE_ONLY)]
    assert payload["headers"]["issues"] == 0


def test_a_date_equals_its_midnight_datetime() -> None:
    assert iig_diff.classify("9999-12-31", "9999-12-31 00:00:00") == iig_diff.NORMALIZED
    assert iig_diff.classify("9999-12-31", dt.datetime(9999, 12, 31)) == iig_diff.NORMALIZED
    assert iig_diff.classify("2026-05-21", "2026-05-21T00:00:00.000") == iig_diff.NORMALIZED
    assert iig_diff.classify("9999-12-31", "9999-12-31 08:00:00") == iig_diff.MISMATCH


def test_the_pair_scores_the_end_date_normalized(tmp_path: Path) -> None:
    s = _score(tmp_path, *_pair(tmp_path))["sheets"][PIPE]
    assert s["column_counts"]["ACTIVE_END_DATE"]["normalized"] == 1


def test_segment_codes_pair_and_compare_through_the_profile(tmp_path: Path) -> None:
    keys = iig_diff.load_keys(KEYS)
    assert keys.segment_profile == "acfc_prx"
    assert keys.segment_code("HDDR") == "header" and keys.segment_code("det") == "details"
    assert keys.segment_code("trlr") == "trailer" and keys.segment_code("xyz") == "xyz"
    s = _score(tmp_path, *_pair(tmp_path))["sheets"][FIXED]
    assert s["pairing"]["identity"] == 2 and s["pairing"]["order"] == 0   # by identity
    assert s["column_counts"]["SEGMENT"] == {"exact": 0, "normalized": 2, "mismatch": 0,
                                             "missing-in-agent": 0, "extra-in-agent": 0}


def test_a_scrubbed_export_rescores_to_its_own_numbers(tmp_path: Path) -> None:
    golden, agent = _pair(tmp_path, agent_tables=("syn_tbl_b", "syn_tbl_b"))
    export = tmp_path / "export"
    assert iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out",
                          str(tmp_path / "scored"), "--export-scrubbed", str(export)]) == 0
    sheets = rescore.read_export(export)
    rebuilt_golden, rebuilt_agent = rescore.rebuild(sheets, tmp_path / "rebuilt")
    payload = rescore.score(REPO / "tools" / "iig_diff.py", KEYS, rebuilt_golden,
                            rebuilt_agent, tmp_path / "rescored", "iig_diff_rescore")
    for name, sheet in sheets.items():
        reported = sheet.reported["score"]
        again = payload["sheets"][name]
        assert str(again["score"] if not again.get("note") else "-") == reported, name
