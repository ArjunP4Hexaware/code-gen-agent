# ruff: noqa: E501  -- fixture data rows kept on one line
"""post179 (a staging run): one STTM mapping for two PARALLEL feeds - every stage
TableName cell lists both tables ("nb_a_remit nb_b_remit"), the File Names cell
lists both files (one per line), the FRD names no table. The whole cell reached
the resolver as ONE table name and the run stopped (TableNameError).

Now (codegen.extract.list_cells): the sheet is split by POSITION - feed i takes
the i-th name of every list cell and the i-th file - only when the File Names
cell states as many files as the cells list tables. Rows whose standard table
is not the feed's main one (a summary table) keep their stage mapping and leave
the standard one blank + flagged. Synthetic Northwind vocabulary only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from acfc_shapes.cold_pairs import _merge, _sheet
from acfc_shapes.common import new_workbook
from codegen import cli
from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract
from codegen.extract.list_cells import listed_tables, pick, split_count
from codegen.resolve.resolver import resolve_feeds

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-11-06"
FILES = ["NB_A_RA_YYYYMMDD.txt", "NB_B_RA_YYYYMMDD.txt"]
STAGE = "nb_a_remit nb_b_remit"
MAIN = "nb_a_remit nb_b_remit"
SUMRY = "nb_a_remit_sumry\nnb_b_remit_sumry"


def _sttm(path: Path, files: list[str] = FILES, stage: str = STAGE) -> Path:
    wb = new_workbook()
    titles = ["Source File Layout", None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    rows = [  # (field, stage column, standard table cell)
        ("batch_id", "BATCH_ID", SUMRY), ("batch_date", "BATCH_DATE", SUMRY),
        ("member_id", "MEMBER_ID", MAIN), ("paid_amount", "PAID_AMOUNT", MAIN),
        ("claim_ref", "CLAIM_REF", MAIN),
    ]
    body = [[name, f"{name} of the remit", "varchar", "N", "stg_nb_rm", stage, column,
             "String", "nb_rm", std, column, "String", None] for name, column, std in rows]
    for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")):
        body.append(["NA", None, None, None, "stg_nb_rm", stage, column, datatype,
                     "nb_rm", MAIN, column, datatype, None])
    ws = _sheet(wb, "REMIT", [["Project Name", "Northwind Remittance Data"],
                              ["File Name", "\n".join(files)], [], titles, header, *body])
    for first, last in ((1, 4), (5, 8), (9, 12)):
        _merge(ws, 4, first, last)
    wb.save(path)
    return path


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    return tmp_path


def _chain(tmp: Path, capsys, sttm: Path):
    frd = tmp / "FRD_remit.docx"
    frd.write_bytes(fm.build_frd([], name="Northwind Remittance Data", table=""))
    frd_out, sttm_out = tmp / "frd.json", tmp / "sttm.json"
    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(frd_out)]) == 0
    layout_out = capsys.readouterr().out
    code = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_out),
                     "--out", str(sttm_out), "--generated-date", DATE])
    printed = capsys.readouterr().out
    assert code == 0, layout_out + printed
    return (FrdContract.model_validate_json(frd_out.read_text(encoding="utf-8")),
            SttmContract.model_validate_json(sttm_out.read_text(encoding="utf-8")))


# --- the cell vocabulary ---------------------------------------------------------

def test_a_cell_lists_tables_only_when_every_word_is_an_identifier():
    assert listed_tables("nb_a_remit nb_b_remit") == ["nb_a_remit", "nb_b_remit"]
    assert listed_tables("nb_a_sumry\nnb_b_sumry") == ["nb_a_sumry", "nb_b_sumry"]
    assert listed_tables("nb_a_remit") is None
    assert listed_tables("nb a-remit") is None          # 'a-remit' is no identifier
    assert listed_tables(None) is None and listed_tables("  ") is None


def test_the_split_needs_as_many_files_as_tables():
    """Evidence, never a guess: 'claims history' with ONE file is a mistyped
    name (the resolver's TableNameError says so), not two feeds."""
    assert split_count(STAGE, FILES) == 2
    assert split_count("claims history", ["claims.txt"]) is None
    assert split_count(STAGE, FILES[:1]) is None
    assert split_count("nb_a_remit", ["a.txt"]) is None


def test_a_cell_gives_each_feed_its_position_or_nothing():
    assert pick(STAGE, 1, 2) == ("nb_b_remit", False)
    assert pick("stg_nb_rm", 1, 2) == ("stg_nb_rm", False)       # shared by both feeds
    assert pick("a_t b_t a_s b_s", 0, 2) == (None, True)         # another count: blank
    assert pick(None, 0, 2) == (None, False)


# --- the chain the harness runs ----------------------------------------------------

def test_one_sheet_listing_two_tables_is_two_feeds_by_position(env, capsys):
    frd, sttm = _chain(env, capsys, _sttm(env / "STTM_remit.xlsx"))
    assert [(f.feed_name, f.stage_target.tables, f.standard_target.tables,
             f.file_name_patterns) for f in frd.feeds] == [
        ("nb_a_remit", ["nb_a_remit"], ["nb_a_remit"], [FILES[0]]),
        ("nb_b_remit", ["nb_b_remit"], ["nb_b_remit"], [FILES[1]])]
    assert [(f.feed_id, f.stage.table, f.standard.table, f.source_file.name_pattern)
            for f in sttm.feeds] == [
        ("nb_a_remit", "nb_a_remit", "nb_a_remit", FILES[0]),
        ("nb_b_remit", "nb_b_remit", "nb_b_remit", FILES[1])]
    for index, feed in enumerate(sttm.feeds):
        (split,) = [f for f in feed.extraction_flags if f.startswith("sttm_list_cells_split:")]
        assert f"feed {index + 1} of 2 takes table {feed.stage.table!r}" in split
        assert repr(FILES[index]) in split


def test_rows_of_a_summary_table_keep_stage_and_leave_standard_blank(env, capsys):
    _frd, sttm = _chain(env, capsys, _sttm(env / "STTM_remit.xlsx"))
    for feed in sttm.feeds:
        by_column = {f.stage_column: f for f in feed.fields}
        assert set(by_column) == {"BATCH_ID", "BATCH_DATE", "MEMBER_ID", "PAID_AMOUNT",
                                  "CLAIM_REF"}
        assert by_column["BATCH_ID"].standard_column is None
        assert by_column["BATCH_DATE"].standard_column is None
        assert by_column["MEMBER_ID"].standard_column == "MEMBER_ID"
        (flag,) = [f for f in feed.extraction_flags
                   if f.startswith("sttm_standard_table_not_built:")]
        sumry = f"{feed.stage.table}_sumry"
        assert f"2 row(s) map to standard table {sumry!r}, not this feed's " in flag


def test_the_split_feeds_resolve_with_plain_table_names(env, capsys):
    """The resolver's TableNameError (the staging run) is gone: each feed's
    tables are plain identifiers."""
    frd, sttm = _chain(env, capsys, _sttm(env / "STTM_remit.xlsx"))
    specs = resolve_feeds(frd, sttm, load_config(REPO / "config" / "config.yaml"),
                          frd_sha256="0" * 64, sttm_sha256="0" * 64)
    assert sorted(s.feed_id for s in specs) == ["nb_a_remit", "nb_b_remit"]


def test_without_the_file_evidence_nothing_is_split(env, capsys):
    """One file for a two-word cell: no split - the cell is one (invalid) name
    and the resolver says so, as before."""
    frd, sttm = _chain(env, capsys, _sttm(env / "STTM_one.xlsx", files=FILES[:1]))
    assert len(sttm.feeds) == 1 and sttm.feeds[0].stage.table == STAGE
    assert not [f for f in sttm.feeds[0].extraction_flags if f.startswith("sttm_list")]
