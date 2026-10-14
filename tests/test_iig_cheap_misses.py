"""The good sheets' cheap misses (2026-10-14, D1 post43 item 4): ADLS_DELTA
FILE_HEADER_FLAG / FILE_METADATA, STGDELTA SRC / TGT_CONTAINER_NAME and
SRC_DATA_TYPE, under the ACFC environment overlay.

D1 pair_2 per column: FILE_HEADER_FLAG and FILE_METADATA missing on every ADLS
row, both STGDELTA containers missing, STGDELTA SRC_DATA_TYPE a mismatch on all
three rows. The golden values (acfc-results round7 pair_2, scrubbed): the
delimited SD files' FILE_HEADER_FLAG 'Y'; FILE_METADATA NULL (the prod table's
55th column, which the iig_v2 template lacked); the stage container in and the
standard container out; 'String:Decimal(10,2)' where the agent wrote
'String:Decimal'.
"""

from __future__ import annotations

import re

import pytest

from codegen.config import load_config
from test_iig_v2_derivations import ACFC_OVERLAY, FRD, _rows, _run

ADLS, STG = "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET"


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cheap_misses")
    config = load_config(REPO_CONFIG, overlays=[ACFC_OVERLAY])
    spec, gate, xlsx = _run(FRD, config, tmp)
    return spec, gate, xlsx


REPO_CONFIG = ACFC_OVERLAY.parent.parent / "config.yaml"


def test_adls_file_header_flag_by_format_and_file_metadata_decided_blank(generated):
    spec, gate, xlsx = generated
    rows = _rows(xlsx, ADLS)
    assert rows and spec.delimiter                       # the fixture's file is delimited
    for row in rows:
        value, badge, _tooltip = row["FILE_HEADER_FLAG"]
        assert value == "Y" and badge.lower() == "synthetic"
        assert "FILE_METADATA" in row and row["FILE_METADATA"][0] in (None, "")
    notes = [f for f in gate.flags
             if f.startswith("iig_derived:ADLS_DELTA_INGESTION_DETAILS.FILE_HEADER_FLAG")]
    assert len(notes) == 1 and "delimited file -> 'Y'" in notes[0]
    # FILE_METADATA is decided blank: NULL in the database script, never a placeholder
    sql = (xlsx.parent / "metadata_inserts.sql").read_text(encoding="utf-8")
    adls_inserts = [line for line in sql.splitlines()
                    if line.startswith("INSERT INTO") and "ADLS_DELTA_INGESTION_DETAILS" in line]
    assert adls_inserts and all("[FILE_METADATA])" in line for line in adls_inserts)
    assert all(line.rstrip().endswith("NULL);") for line in adls_inserts)
    assert "FILE_METADATA#" not in sql


def test_stgdelta_containers_and_full_data_types(generated):
    _spec, _gate, xlsx = generated
    rows = _rows(xlsx, STG)
    assert rows
    adls_tgt = {r["TGT_CONTAINER_NAME"][0] for r in _rows(xlsx, ADLS)}
    for row in rows:
        assert {row["SRC_CONTAINER_NAME"][0]} == adls_tgt          # the stage container in
        assert row["TGT_CONTAINER_NAME"][0].endswith("-std-01")   # the standard container out
        # the standard side as the STTM states it (precision kept): the pairs'
        # right-hand sides are TGT_DATA_TYPE, type for type
        src, tgt = row["SRC_DATA_TYPE"][0], row["TGT_DATA_TYPE"][0]
        right_sides = re.sub(r"(^|,)[^,:()]+(?:\([^)]*\))?:", r"\1", src)
        assert right_sides == tgt
        assert "(" in tgt                     # the fixture states a precision
