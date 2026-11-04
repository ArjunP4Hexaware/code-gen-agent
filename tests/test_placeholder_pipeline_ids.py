"""post166 (Soham, 2026-11-04): placeholder PIPELINE_IDs that show the flow.

Under the ACFC overlay (``placeholder_pipeline_ids: true``) the IIG workbook numbers the
``pipeline_roles`` from 0: grand master 0 (PARENT_PIPELINE_ID blank - NULL, not 0), master
1 (parent 0), File-to-Stage 2 and Stage-to-Standard 3 (both parent 1: children of one
master share it). The other sheets name the pipeline that runs their rows: the ADLS /
file-copy / fixed-width rows File-to-Stage's id, the STGDELTA rows Stage-to-Standard's,
each notebook row its flow's. Workbook only: metadata_inserts.sql keeps the open
``<<PIPELINE_ID#n>>`` markers. In the combined IIG each feed's own children follow the
previous feeds' (the shared grand master / master stay 0 / 1). Synthetic pair 11 shapes
(test_iig_v2_derivations).
"""

from __future__ import annotations

from codegen.config import load_config
from codegen.emit.metadata_inserts import cell_sql
from codegen.run_artefacts import merge_payloads
from test_derivations import FRD
from test_iig_v2_derivations import ACFC_OVERLAY, REPO, _rows, _run

SCHED, ADLS, STG = ("DATA_FACTORY_PIPELINE_SCHEDULE", "ADLS_DELTA_INGESTION_DETAILS",
                    "STGDELTA_STDDELTA_INGESTION_DET")


def _ids(rows, column="PIPELINE_ID"):
    return [None if r[column][0] in (None, "") else str(r[column][0]) for r in rows]


def _run_acfc(tmp_path):
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    return _run(FRD, config, tmp_path)


def test_the_schedule_shows_grand_master_master_and_children(tmp_path):
    _spec, _gate, xlsx = _run_acfc(tmp_path)
    rows = _rows(xlsx, SCHED)
    names = [str(r["PIPELINE_DESCRIPTION"][0]).lower() for r in rows]   # pipeline_roles order
    assert "grand master" in names[0] and "master" in names[1] and len(rows) == 4
    assert _ids(rows) == ["0", "1", "2", "3"]
    assert _ids(rows, "PARENT_PIPELINE_ID") == [None, "0", "1", "1"]   # the top one: blank


def test_the_other_sheets_name_the_pipeline_that_runs_them(tmp_path):
    _spec, _gate, xlsx = _run_acfc(tmp_path)
    assert set(_ids(_rows(xlsx, ADLS))) == {"2"}                        # File to Stage
    assert set(_ids(_rows(xlsx, STG))) == {"3"}                         # Stage to Standard


def test_the_insert_sql_keeps_the_open_marker():
    entry = {"badge": "synthetic", "placeholder_id": True, "convention": True}
    assert cell_sql("PIPELINE_ID", "2", entry, 4) == "<<PIPELINE_ID#4>>"
    assert cell_sql("PIPELINE_ID", "2", {"badge": "synthetic"}, 4) == "N'2'"   # a real value


def test_off_without_the_overlay(tmp_path):
    config = load_config(REPO / "config" / "config.yaml")
    assert not config.metadata.templates["iig_v2"].placeholder_pipeline_ids


def _payload(ids: list[tuple[str, str, bool]]) -> dict:
    """A one-sheet schedule payload: (PIPELINE_ID, PARENT_PIPELINE_ID, shared)."""
    rows = []
    for pid, parent, shared in ids:
        badge = {"badge": "synthetic", "placeholder_id": True, "placeholder_shared": shared}
        parent_badge = {"badge": "synthetic", "placeholder_id": bool(parent),
                        "placeholder_shared": True}
        rows.append({"values": {"PIPELINE_ID": pid, "PARENT_PIPELINE_ID": parent},
                     "badges": {"PIPELINE_ID": badge, "PARENT_PIPELINE_ID": parent_badge}})
    return {"tabs": {SCHED: {"headers": ["PIPELINE_ID", "PARENT_PIPELINE_ID"], "rows": rows}}}


def test_the_combined_iig_numbers_each_feeds_children_on():
    feed = [("0", "", True), ("1", "0", True), ("2", "1", False), ("3", "1", False)]
    merged = merge_payloads([("a", _payload(feed)), ("b", _payload(feed))], [SCHED])
    rows = merged.payload["tabs"][SCHED]["rows"]
    pairs = [(r["values"]["PIPELINE_ID"], r["values"]["PARENT_PIPELINE_ID"]) for r in rows]
    # the grand master / master once; feed b's children 4, 5 under the same master
    assert pairs == [("0", ""), ("1", "0"), ("2", "1"), ("3", "1"), ("4", "1"), ("5", "1")]
