"""post183 (a staging run): an STTM row marked unmapped in its TABLE cells too.

The pair-1 shape (Family A, segmented) with the unmapped field's stage / standard
Target Table and Schema cells reading the skip marker ("Do Not Map"), not only its
column cells. The layout's STTM facts read every non-blank table cell, so the marker
became a stage table; an FRD naming no stage table took the band's tables through the
gap fill, and the resolver failed "FRD stage tables not mapped by any STTM field:
['Do Not Map']". A marker cell names no table or schema. Synthetic only.
"""

from __future__ import annotations

import json
from pathlib import Path

from acfc_shapes import pair1
from acfc_shapes import sttm as sttm_fixtures
from codegen.config import load_config
from codegen.extract import contract_to_json as sttm_to_json
from codegen.extract import extract_contract
from codegen.extract.frd_docx import contract_to_json as frd_to_json
from codegen.layout.resolve import _sttm_facts, resolve_pair
from codegen.resolve.resolver import resolve_pair as resolve_contracts

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
PAIR_1_FRD = REPO / "fixtures" / "acfc_shapes" / "frd" / "f1_pair_1.docx"
DATE = "2026-01-01"
TABLE_HEADER = "Target Table Name in DL"
SCHEMA_HEADER = "Target Schema Name in DL"


def _marked_workbook(path: Path) -> Path:
    """Pair 1 with every Table / Schema cell of the unmapped row = the marker."""
    wb = sttm_fixtures.build_pair1()
    ws = wb["FEED_1_MAPPING"]
    header = next(r for r in ws.iter_rows() if any(c.value == TABLE_HEADER for c in r))
    targets = [c.column for c in header if c.value in (TABLE_HEADER, SCHEMA_HEADER)]
    assert len(targets) == 4                                     # both bands
    marked = 0
    for row in ws.iter_rows(min_row=header[0].row + 1):
        if row[2].value == pair1.UNMAPPED_FIELD[0]:
            for col in targets:
                ws.cell(row=row[0].row, column=col).value = pair1.UNMAPPED_MARKER
            marked += 1
    assert marked == 1
    wb.save(path)
    return path


def test_a_marker_table_cell_names_no_table(tmp_path):
    config = load_config(CONFIG)
    sttm = _marked_workbook(tmp_path / "sttm.xlsx")
    pair = resolve_pair(sttm, PAIR_1_FRD, config, provider=None, cache_dirs=[],
                        generated_date=DATE)
    from openpyxl import load_workbook

    facts = _sttm_facts(pair.sttm.profile, load_workbook(sttm), config)
    (entry,) = facts["sheet_tables"]
    assert entry["stage_tables"] == [pair1.TABLE]
    assert entry["standard_tables"] == [pair1.TABLE]
    assert all(pair1.UNMAPPED_MARKER not in cells for cells in entry["table_rows"])
    assert pair1.UNMAPPED_MARKER not in json.dumps(facts["schemas"])


def test_an_frd_naming_no_stage_table_resolves_past_the_marker_row(tmp_path):
    """The staging failure: the gap fill takes the band's tables for an FRD
    that names none - the marker must not be one of them."""
    config = load_config(CONFIG)
    sttm = _marked_workbook(tmp_path / "sttm.xlsx")
    first = resolve_pair(sttm, PAIR_1_FRD, config, provider=None, cache_dirs=[],
                         generated_date=DATE)
    data = json.loads(frd_to_json(first.frd_contract))
    data["feeds"][0]["stage_target"]["tables"] = []
    frd_in = tmp_path / "frd_in.json"
    frd_in.write_text(json.dumps(data), encoding="utf-8")
    pair = resolve_pair(sttm, frd_in, config, provider=None, cache_dirs=[],
                        generated_date=DATE)
    assert pair.frd_contract.feeds[0].stage_target.tables == [pair1.TABLE]
    frd_json, sttm_json = tmp_path / "frd.json", tmp_path / "sttm.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    contract = extract_contract(sttm, frd_json, config, generated_date=DATE,
                                layout=pair.sttm.profile, width_answers=pair.width_answers)
    sttm_json.write_text(sttm_to_json(contract), encoding="utf-8")
    specs = resolve_contracts(frd_json, sttm_json, config)
    assert len(specs) == 1
    columns = [f.stage_column for s in specs[0].segments for f in s.fields]
    assert pair1.UNMAPPED_MARKER not in columns
