"""Multi-table Phase C step 3 — ADLS_DELTA rows = files, STGDELTA rows = tables.

docs/acfc/MULTI_TABLE_DESIGN.md rules 2–4: one ADLS row per file the feed
receives (pair 4: six, one per LOB; pair 1: four patterns, no LOB), every row
into the detail table, OBJECT_ID = the file's position; one STGDELTA row per
table (pair 4: three; pair 1: one), the target side from the table's standard
definition with the mapped catalog. Pair 4 is compared cell for cell with the
hand-written golden.
"""

from __future__ import annotations

from acfc_shapes import pair4_nb
from multi_table_golden import compare_to_golden

# ------------------------------------------------------------------ pair 4


def test_pair4_adls_rows_are_the_six_lob_files_and_match_the_golden(pair4_payload, pair4_golden):
    assert compare_to_golden(pair4_payload, pair4_golden, "ADLS_DELTA_INGESTION_DETAILS") == []


def test_pair4_stgdelta_rows_are_the_three_tables_and_match_the_golden(pair4_payload, pair4_golden):
    assert compare_to_golden(pair4_payload, pair4_golden, "STGDELTA_STDDELTA_INGESTION_DET") == []


def test_pair4_spec_carries_the_six_files(pair4_spec):
    assert [f.lob for f in pair4_spec.files] == pair4_nb.LOBS
    assert all("STTM header block" in f.provenance for f in pair4_spec.files)


def test_object_id_is_a_cited_convention_not_an_invented_id(pair4_payload):
    rows = pair4_payload["tabs"]["ADLS_DELTA_INGESTION_DETAILS"]["rows"]
    for index, row in enumerate(rows, start=1):
        entry = row["badges"]["OBJECT_ID"]
        assert row["values"]["OBJECT_ID"] == str(index)
        assert entry["badge"] == "synthetic" and "METADATA_DB_SEMANTICS.md §5" in entry["tooltip"]
    # GROUP_ID / PIPELINE_ID stay framework-assigned blanks.
    assert {r["values"]["GROUP_ID"] for r in rows} == {""}
    assert {r["values"]["PIPELINE_ID"] for r in rows} == {""}


# ------------------------------------------------------------------ pair 1


def test_pair1_four_files_without_lob_and_one_table(pair1_payload, pair1_spec):
    adls = pair1_payload["tabs"]["ADLS_DELTA_INGESTION_DETAILS"]["rows"]
    stg = pair1_payload["tabs"]["STGDELTA_STDDELTA_INGESTION_DET"]["rows"]
    assert len(adls) == 4 and len(stg) == 1
    assert [r["values"]["SRC_FILE_NAME"] for r in adls] == pair1_spec.file_name_patterns
    assert [r["values"]["OBJECT_ID"] for r in adls] == ["1", "2", "3", "4"]
    assert {r["values"]["LOB"] for r in adls} == {""}
    assert {r["values"]["TGT_PARTITION_COLUMN"] for r in adls} == {"NA"}
    assert {r["values"]["TGT_PARTITION_VALUE"] for r in adls} == {"NA"}
    assert {r["values"]["TGT_TABLE_NAME"] for r in adls} == {"vnd_p_accum_client"}
    (row,) = stg
    assert row["values"]["SRC_TABLE_NAME"] == row["values"]["TGT_TABLE_NAME"] == \
        "vnd_p_accum_client"
    assert row["values"]["LOB"] == ""
