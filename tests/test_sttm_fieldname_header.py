"""post195: a source band whose field-name header is written as one word ("FieldName",
seen in a tester's multi-sheet STTM, 2026-11-17) resolves by synonyms - before, every
mapping sheet asked ``UNRESOLVED sheets[<i>]/source/field_name``. Synthetic workbook:
the header row's shape only, no client value."""

from __future__ import annotations

import pytest
from openpyxl import Workbook

from codegen.layout.discover import discover

TITLES = ["Source File", None, None, None, None, None, None,
          "Stage Layer", None, None, None, None, None, None,
          "Standard Layer", None, None, None, None, None]
SOURCE = ["S.No", "{field}", "FieldDescription", "Required?", "PHI/ PII Indicator", "DataType"]
TARGET = ["Workspace", "Catalog", "Schema", "TableName", "ColumnName", "DataType"]


def _workbook(path, field_header: str, sheets=("FEED_A", "FEED_B")):
    wb = Workbook()
    wb.remove(wb.active)
    header = [h.format(field=field_header) for h in SOURCE] + [None] + TARGET + [None] + TARGET
    for name in sheets:
        ws = wb.create_sheet(name)
        ws.append(TITLES)
        ws.append(header)
        for i, col in enumerate(("member_id", "claim_id", "svc_date"), 1):
            ws.append([i, col, f"{col} d", "Y", "N", "varchar", None,
                       "ws", "cat", "stg_x", "stg_t", col.upper(), "String", None,
                       "ws", "cat", "std_x", "std_t", col.upper(), "String"])
    wb.save(path)
    return path


@pytest.mark.parametrize("field_header", ["Field Name", "FieldName"])
def test_field_name_header_resolves_with_or_without_the_space(field_header, config, tmp_path):
    found = discover(_workbook(tmp_path / "s.xlsx", field_header), config.extractor)
    profile = found.profile
    for sheet in ("FEED_A", "FEED_B"):
        missing = [f"{u.layer}/{u.role}" for u in profile.unresolved_for(sheet)]
        assert "source/field_name" not in missing, (field_header, sheet, missing)
        sp = profile.sheet(sheet)
        source = [b for b in sp.bands if b.layer == "source"]
        assert source and "field_name" in source[0].roles
