"""post201: a Comments column inside a stage / standard band (a staging STTM, 2026-11-18:
the standard band's last column, on every mapping sheet) is the row's rule text
(``value_spec``) as the source band's Comments is - before, the target role table knew
no Comments header, so the column was read by nothing and its notes (date formats,
SPLIT_PART) never reached the IIG / review copy. A Comments column after the last band
(``rules.comments``) was placed by the layout but never read either. Synthetic
workbook: the header shape only, no client value."""

from __future__ import annotations

import pytest
from openpyxl import Workbook

from codegen.extract import extract_contract
from codegen.extract.generic import FieldRow, _comments
from codegen.layout.discover import discover
from test_layout_discovery import GENERATED_DATE, _frd, _write_frd

TITLES = ["Source File", None, None, None, None, None, None,
          "Stage Layer", None, None, None, None, None, None,
          "Standard Layer", None, None, None, None, None, None]
SOURCE = ["S.No", "Field Name", "Field Description", "Required?", "PHI/ PII Indicator",
          "DataType"]
TARGET = ["Workspace", "Catalog", "Schema", "TableName", "ColumnName", "DataType"]
NOTES = {"member_id": None, "claim_id": "SPLIT_PART on '-' keep part 1",
         "svc_date": "date_format MM/DD/YYYY"}


def _workbook(path):
    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("FEED_A")
    ws.append(TITLES)
    ws.append(SOURCE + [None] + TARGET + [None] + TARGET + ["Comments"])
    for i, col in enumerate(NOTES, 1):
        ws.append([i, col, f"{col} d", "Y", "N", "varchar", None,
                   "ws", "cat", "stg_x", "stg_t", col.upper(), "String", None,
                   "ws", "cat", "std_x", "std_t", col.upper(), "String", NOTES[col]])
    ws.append([4, "NA", None, None, None, None, None,               # the audit row
               "ws", "cat", "stg_x", "stg_t", "SRC_FILE_NAME", "String", None,
               "ws", "cat", "std_x", "std_t", "SRC_FILE_NAME", "String", None])
    wb.save(path)
    return path


def test_the_standard_band_places_its_comments_column(config, tmp_path):
    profile = discover(_workbook(tmp_path / "s.xlsx"), config.extractor).profile
    standard = profile.sheet("FEED_A").band("standard")
    assert standard is not None and standard.roles.get("comments") == 21
    assert profile.unresolved_for("FEED_A") == []


def test_a_target_band_comments_cell_is_the_rows_rule_text(config, tmp_path):
    """Failed before post201: every field's value_spec was None."""
    frd = _write_frd(tmp_path, _frd("FEED_A", ["feed_a_YYYYMMDD.csv"], ["stg_t"], ["std_t"],
                                    stage_schema="stg_x", std_schema="std_x"))
    contract = extract_contract(_workbook(tmp_path / "s.xlsx"), frd, config,
                                generated_date=GENERATED_DATE)
    (feed,) = contract.feeds
    specs = {f.source_column.lower(): f.value_spec for f in feed.fields}
    assert specs == NOTES
    # rule text only: a Comments cell never becomes the column's description
    assert all(not f.description or f.description.endswith(" d") for f in feed.fields)


def _row(**values):
    return FieldRow(sheet="S", row=1, col=1, segment_raw=None, segment=None, values=values)


def test_every_bands_comments_join_once_in_band_order():
    assert _comments(_row(**{"standard.comments": "b", "source.comments": "a",
                             "rules.comments": "a", "stage.comments": None})) == "a; b"
    assert _comments(_row(**{"rules.comments": "t"})) == "t"
    assert _comments(_row(**{"source.field_name": "x"})) is None


@pytest.fixture(scope="module")
def config():
    from codegen.config import load_config
    from test_layout_discovery import REPO

    return load_config(REPO / "config" / "config.yaml")


def test_a_trailing_comments_column_never_widens_a_label_group_band(config):
    """post201 side effect (12-pair check, pair_07): on a sheet with no band title row,
    a band's span is the run of target-role headers; once Comments was a target role it
    stretched the band over the trailing Recycle Flag / DQ-mandatory / Comments columns
    and the DQ-mandatory column was read by nothing. Comments is placed inside a band,
    never span evidence."""
    from codegen.layout.discover import label_groups

    header = ["S.No", "Field Name", "Field Description", "DataType",
              "Schema", "Table Name", "Column Name", "Data Type",
              "Mandatory Fields Include in DQ Check", "Recycle Flag", "Comments"]
    groups = label_groups(header, config.extractor.discovery)
    assert [(g.start, g.end) for g in groups] == [(5, 8)]
