"""post217 (a staging tester, 2026-11-23): her STTM template states each field's
description in the SOURCE band under the header "FieldDescription" (one word); the
source band's ``description`` role knew only "Description" / "Column Description", so
the column was never read: the DDL had no column COMMENT and a ``ddl_comment_blank``
flag per table. The fix is a synonym (``extractor.discovery.roles.source.description``
+ "field description"; headers match with spaces ignored, post198) - the existing path
then writes the text as the COMMENT on the stage and standard columns.

The workbook is synthetic, in that template's SHAPE only (band titles, header row);
the FRD is the Family E one (tests/post51_pairs.py).
"""

from __future__ import annotations

import re
from pathlib import Path

from acfc_shapes.common import band_row, merge_bands, new_workbook, write_rows
from codegen.config import load_config
from codegen.layout.discover import header_key
from post51_pairs import family_e_frd
from test_iig_cell_counts import _run

REPO = Path(__file__).resolve().parents[1]
SOURCE = ["S.No", "FieldName", "FieldDescription", "Required?", "PHI/ PII Indicator", "DataType"]
LAYER = ["Workspace", "Catalog", "Schema", "TableName", "ColumnName", "DataType"]
FIELDS = [("Claim Number", "The claim's number as the vendor sends it"),
          ("Member Id", "Unique member identifier from the plan"),
          ("Service Date", "Date the service was provided")]
TABLE = "feed_5_dtl"


def _template_workbook(path: Path) -> Path:
    wb = new_workbook()
    ws = wb.create_sheet("FEED_5_MAPPING")
    write_rows(ws, [["File(s)", "FEED_5_*.txt"], ["File Location", "inbound/vendor_e"],
                    ["LOB", "ALL"], ["File frequency", "Weekly"], ["Domain", "Claims"],
                    ["Sub-Domain", "Medical"], ["File type", "txt (pipe delimited |)"]],
               start_row=1)
    groups = [("Source FileLayout", len(SOURCE)), ("Stage Layer", len(LAYER)),
              ("Standard Layer", len(LAYER))]
    write_rows(ws, [band_row(groups)], start_row=10)
    merge_bands(ws, 10, groups)
    write_rows(ws, [SOURCE + LAYER + LAYER], start_row=11)
    rows = []
    for index, (name, description) in enumerate(FIELDS):
        column = name.upper().replace(" ", "_")
        rows.append([index + 1, name, description, "Y", "N", "varchar",
                     "syn_ws", "syn_dlk", "stg_clm", TABLE, column, "String",
                     "syn_ws", "syn_std", "clm", TABLE, column, "String"])
    for column, dtype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "timestamp")):
        # audit rows: the source side's field name is the audit marker NA, no description
        rows.append([None, "NA", None, None, None, None,
                     "syn_ws", "syn_dlk", "stg_clm", TABLE, column, dtype,
                     "syn_ws", "syn_std", "clm", TABLE, column, dtype])
    write_rows(ws, rows, start_row=12)
    wb.save(path)
    return path


def test_the_one_word_header_shares_the_synonyms_key():
    config = load_config(REPO / "config" / "config.yaml")
    synonyms = config.extractor.discovery.roles["source"]["description"]
    assert header_key("FieldDescription") in {header_key(s) for s in synonyms}


def test_a_source_band_field_description_is_each_columns_ddl_comment(tmp_path):
    workbook = _template_workbook(tmp_path / "template.xlsx")
    _done, _feed = _run(tmp_path, workbook, family_e_frd(tmp_path / "frd.json"))
    (ddl,) = [p for p in (tmp_path / "out").rglob("*_DDL.txt") if "combined" not in p.parts]
    text = ddl.read_text(encoding="utf-8")
    # stage + standard only: the reject table's columns carry no COMMENT (post212)
    body = text.split("--standard reject table", 1)[0]
    for name, description in FIELDS:
        column = name.upper().replace(" ", "_")
        lines = [ln for ln in body.splitlines() if ln.strip().startswith(f"{column} ")]
        assert len(lines) == 2, (column, lines)                    # stage + standard
        escaped = description.replace("'", "\\'")                  # DDL literal: \' (never '')
        assert all(f"COMMENT '{escaped}" in ln for ln in lines), lines
    assert "''" not in re.sub(r"COMMENT ''", "", body)
    flags = "\n".join(p.read_text(encoding="utf-8") for p in (tmp_path / "out").rglob("*.md"))
    # no field is left without its COMMENT (an audit column may still be flagged)
    for name, _description in FIELDS:
        assert not re.search(rf"ddl_comment_blank:[^\n]*\b{name.upper().replace(' ', '_')}\b",
                             flags), name
