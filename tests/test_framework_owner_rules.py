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


# -- rule 4: SRC_COLUMNS '<source>:<target>' in STTM order, verbatim ---------------


def _pair4_rows(spec, config, tab, **knobs):
    import json

    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from codegen.contracts.frd import FrdContract
    from codegen.metadata_template import template_tab_rows

    tpl = config.metadata.templates["iig_v2"].model_copy(update=knobs)
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    return template_tab_rows(tab, frd.feeds[0], config, spec, None, tpl)


def _with_sources(spec, rename):
    """The spec with every field's source_column = rename(field)."""
    segments = [s.model_copy(update={"fields": [f.model_copy(update={"source_column": rename(f)})
                                                for f in s.fields]})
                for s in spec.segments]
    return spec.model_copy(update={"segments": segments})


def test_src_columns_a_display_name_band_writes_the_stage_columns(pair4_spec, pair4_config):
    """A source band of DISPLAY names (the CAQH golden): every pair is the stage
    column, verbatim (its prefix kept), on both sides — even a one-word display
    name is not taken for an identifier when the band is display names."""
    spec = _with_sources(pair4_spec, lambda f: (
        "Member" if f.stage_column.upper().endswith("MEMBER_ID") else
        f.stage_column.replace("_", " ").title()))
    (row, *_more) = _pair4_rows(spec, pair4_config, ADLS, src_columns_style="source_target")
    detail = next(s for s in spec.segments if s.stage_table.table == row["TGT_TABLE_NAME"][
        "value"].rsplit(".", 1)[-1]) if "." in row["TGT_TABLE_NAME"]["value"] else None
    fields = (detail or spec.detail_segment).fields
    assert row["SRC_COLUMNS"]["value"] == ",".join(f"{f.stage_column}:{f.stage_column}"
                                                   for f in fields)


def test_src_columns_an_identifier_band_writes_source_target(pair4_spec, pair4_config):
    spec = _with_sources(pair4_spec, lambda f: f"src_{f.stage_column}")
    (row, *_more) = _pair4_rows(spec, pair4_config, ADLS, src_columns_style="source_target")
    pairs = row["SRC_COLUMNS"]["value"].split(",")
    assert all(p.split(":")[0] == f"src_{p.split(':')[1]}" for p in pairs)


def test_each_table_takes_the_sttm_audit_rows_of_its_own_segment(pair4_spec, pair4_config):
    """The CAQH golden: header / trailer tables carry their segments' 3 audit
    rows, the detail table its 5 — verbatim, in STTM order (never the family's
    list for every table)."""
    from codegen.contracts.sttm import AuditColumn

    own = {"Header": ["SRC_FILE_NAME", "REC_CREATION_TIME"],
           "Detail": ["LOB", "FILE_TYPE", "SRC_FILE_NAME", "REC_CREATION_TIME"],
           "Trailer": ["SRC_FILE_NAME", "REC_CREATION_TIME"]}
    segments = [s.model_copy(update={"audit_columns": [
        AuditColumn(column=c, datatype="String") for c in own[s.segment.title()]]})
        for s in pair4_spec.segments]
    spec = pair4_spec.model_copy(update={"segments": segments})
    rows = _pair4_rows(spec, pair4_config, "STGDELTA_STDDELTA_INGESTION_DET",
                       audit_columns_from_sttm=True)
    by_table = {r["SRC_TABLE_NAME"]["value"]: r["SRC_COLUMNS"]["value"].split(",") for r in rows}
    for segment in segments:
        left = [p.split(":")[0] for p in by_table[segment.stage_table.table]]
        data = {f.stage_column for f in segment.fields}
        # the segment's own audit rows after its data columns, in STTM order; one
        # that is already a data column of the table (pair 4's LOB) is not repeated
        expected = [c for c in own[segment.segment.title()] if c not in data]
        assert left[-len(expected):] == expected, segment.segment
        assert not [c for c in left[:-len(expected)] if c not in data]   # nothing else added
