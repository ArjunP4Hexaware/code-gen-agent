"""The client framework owner's rules (2026-10-14), the ones not pinned elsewhere.

Rule 3 — FILE_ADLS_INGESTION_DETAILS is EMPTY for an MFT-landed feed: the landing
path / container names ``mftlanding`` as a path segment (SD and CAQH both) — the
sheet is written with its headers only, plus an ``iig_file_adls_mft`` NOTE. Any
other feed gets one FILE_ADLS row per ADLS_DELTA_INGESTION_DETAILS row (its file),
the landing container / path copied from that row. iig_diff: for an MFT agent the
golden's ALL_FILES file rows pair with the agent's ADLS_DELTA rows on the file
identity, and FILE_ADLS reports "empty by rule (MFT)", never missing.
"""

from __future__ import annotations

from openpyxl import load_workbook

from test_iig_corpus_cells import _acfc, _notes
from test_iig_v2_derivations import FRD, _rows, _run, _write_overlay

FILE_ADLS, ADLS = "FILE_ADLS_INGESTION_DETAILS", "ADLS_DELTA_INGESTION_DETAILS"


def test_an_mft_landed_feed_writes_file_adls_with_headers_only(tmp_path):
    """The D1 environment lands files in the mftlanding container: MFT."""
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    (adls,) = _rows(xlsx, ADLS)
    assert adls["SRC_CONTAINER_NAME"][0] == "mftlanding"
    workbook = load_workbook(xlsx)
    sheet = workbook[FILE_ADLS]
    assert sheet.max_row == 1                                     # the headers, no row
    assert [c.value for c in sheet[1]][:4] == ["GROUP_ID", "OBJECT_ID", "DOMAIN", "SUBDOMAIN"]
    notes = [f for f in _notes(gate) if f.startswith("iig_file_adls_mft:")]
    assert len(notes) == 1 and "lands by MFT (its landing names 'mftlanding')" in notes[0]
    assert "rule 3" in notes[0]


def test_a_non_mft_feed_gets_one_file_adls_row_per_adls_delta_row(tmp_path):
    """The pair_11 FRD's landing itself sits under mftlanding — here the landing
    container is another and the MFT marker list names neither: not MFT."""
    overlay = _write_overlay(tmp_path, "environments:\n  D1:\n    containers:\n"
                                       "      landing: syn-landing-01\n"
                                       "metadata:\n  templates:\n    iig_v2:\n"
                                       "      mft_landing_markers: [syn-mft-only]\n")
    _spec, gate, xlsx = _run(FRD, _acfc(overlay), tmp_path)
    adls_rows, file_rows = _rows(xlsx, ADLS), _rows(xlsx, FILE_ADLS)
    assert len(file_rows) == len(adls_rows) >= 1
    for adls, row in zip(adls_rows, file_rows, strict=True):
        assert row["TGT_CONTAINER_NAME"][0] == adls["SRC_CONTAINER_NAME"][0] == "syn-landing-01"
        assert row["TGT_ADLS_PATH"][0] == adls["SRC_ADLS_PATH"][0]
        assert row["DOMAIN"][0] == adls["DOMAIN"][0]
        assert "the ADLS_DELTA_INGESTION_DETAILS row of" in row["TGT_ADLS_PATH"][2]
        assert row["SOURCE_TYPE"][0] == "File"                    # the template constant
    assert not [f for f in _notes(gate) if f.startswith("iig_file_adls_mft:")]
