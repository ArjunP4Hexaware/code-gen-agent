"""post209 (the tester's report 2026-11-19, item 2; synthetic text only): her STTM states
the file type and delimiter on a separate "File Details" tab of ``<label> | <value>``
rows ("File Type | .txt", "File Delimitor | Pipe") the layout read nothing from (kind
``ignore``). Such a sheet's two-cell rows are read with the mapping sheets' meta-row
labels (``extractor.discovery.meta_synonyms``) for the file format / delimiter /
frequency gap fill; a mapping sheet's own meta row wins, and two sheets that disagree
fill nothing (the question stays)."""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from codegen.config import load_config
from codegen.layout.resolve import resolve_pair
from post73_pairs import frd, mapping_workbook

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _workbook(path: Path, *details: list[list], meta_format: str | None = None) -> Path:
    """The Family E pair's STTM with every format / delimiter statement removed (the
    post170 test's silent sheet), plus ``details``: one label | value sheet each."""
    workbook = openpyxl.load_workbook(mapping_workbook(path))
    sheet = workbook["FEED_5_MAPPING"]
    sheet["B1"], sheet["B8"], sheet["B9"] = "FEED_5_*", None, meta_format
    for n, rows in enumerate(details, start=1):
        ws = workbook.create_sheet(f"Details {n}")
        for row in rows:
            ws.append(row)
    workbook.save(path)
    return path


def _resolve(tmp_path, config, workbook: Path):
    contract = frd(tmp_path / "frd.contract.json", file_format=None, delimiter=None)
    return resolve_pair(workbook, contract, config, provider=None, use_cache=False,
                        runtime_cache_dir=tmp_path / "rt")


DETAILS = [["File Type", ".txt"], ["File Delimitor", "Pipe"], ["File Delivery Method", "SFTP"],
           [None, None], ["File Naming convention", None], [None, "Incremental File"]]


def test_file_delimitor_is_a_delimiter_label(config):
    assert "file delimitor" in config.extractor.discovery.meta_synonyms["delimiter"]


def test_a_label_value_sheet_states_the_format_and_delimiter(tmp_path, config):
    pair = _resolve(tmp_path, config, _workbook(tmp_path / "STTM.xlsx", DETAILS))
    feed = pair.frd_contract.feeds[0]
    assert (feed.file_format, feed.delimiter) == (".txt", "Pipe")
    fills = {f["field"]: str(f) for f in pair.gap_fills}
    assert "Details 1!B1 ('File Type')" in fills["feeds[0].file_format"]
    assert "Details 1!B2 ('File Delimitor')" in fills["feeds[0].delimiter"]


def test_without_the_sheet_both_stay_unstated(tmp_path, config):
    pair = _resolve(tmp_path, config, _workbook(tmp_path / "STTM.xlsx"))
    feed = pair.frd_contract.feeds[0]
    assert (feed.file_format, feed.delimiter) == (None, None)       # asked at generate


def test_two_sheets_that_disagree_fill_nothing(tmp_path, config):
    other = [["File Type", ".csv"], ["File Delimitor", "Pipe"]]
    pair = _resolve(tmp_path, config, _workbook(tmp_path / "STTM.xlsx", DETAILS, other))
    feed = pair.frd_contract.feeds[0]
    assert feed.file_format is None                                  # never a pick
    assert feed.delimiter == "Pipe"                                  # they agree on it


def test_a_mapping_sheet_meta_row_wins(tmp_path, config):
    pair = _resolve(tmp_path, config,
                    _workbook(tmp_path / "STTM.xlsx", DETAILS, meta_format="csv"))
    assert pair.frd_contract.feeds[0].file_format == "csv"


def test_a_row_of_more_than_two_cells_is_no_statement(tmp_path, config):
    rows = [["File Type", ".txt", "see the vendor's note"], ["File Delimitor", "Pipe"]]
    pair = _resolve(tmp_path, config, _workbook(tmp_path / "STTM.xlsx", rows))
    assert pair.frd_contract.feeds[0].file_format is None
