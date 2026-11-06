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


def _sttm(path: Path, files: list[str] = FILES, stage: str = STAGE, *,
          segmented: bool = False, main: str = MAIN, sumry: str = SUMRY) -> Path:
    """``segmented`` (post180): a leading "Record Type" column (HR / DR / TR, the
    staging STTM's spelling) and a column (REC_SEQ) the header AND the detail
    record both carry - the header's into the summary table, the detail's into
    the main one."""
    wb = new_workbook()
    titles = ["Source File Layout", None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    rows = [  # (record type, field, stage column, standard table cell)
        ("HR", "batch_id", "BATCH_ID", sumry), ("HR", "batch_date", "BATCH_DATE", sumry),
        ("DR", "member_id", "MEMBER_ID", main), ("DR", "paid_amount", "PAID_AMOUNT", main),
        ("DR", "claim_ref", "CLAIM_REF", main),
    ]
    if segmented:
        rows = [("HR", "rec_seq", "REC_SEQ", sumry), *rows, ("DR", "rec_seq", "REC_SEQ", main),
                ("DR", "service_date", "SERVICE_DATE", main), ("DR", "payee_id", "PAYEE_ID", main),
                ("TR", "rec_count", "REC_COUNT", sumry)]
    body = [[name, f"{name} of the remit", "varchar", "N", "stg_nb_rm", stage, column,
             "String", "nb_rm", std, column, "String", None] for _rt, name, column, std in rows]
    for column, datatype in (("SRC_FILE_NAME", "String"), ("REC_CREATION_TIME", "Timestamp")):
        body.append(["NA", None, None, None, "stg_nb_rm", stage, column, datatype,
                     "nb_rm", main, column, datatype, None])
    if segmented:
        titles, header = ["Source File Layout", None, *titles[1:]], ["Record Type", *header]
        record_types = [rt for rt, *_ in rows] + ["DR", "DR"]
        body = [[rt, *line] for rt, line in zip(record_types, body, strict=True)]
    ws = _sheet(wb, "REMIT", [["Project Name", "Northwind Remittance Data"],
                              ["File Name", "\n".join(files)], [], titles, header, *body])
    merges = ((1, 5), (6, 9), (10, 13)) if segmented else ((1, 4), (5, 8), (9, 12))
    for first, last in merges:
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
    assert split_count(STAGE, FILES, [MAIN]) == 2
    assert split_count("claims history", ["claims.txt"], [MAIN]) is None
    assert split_count(STAGE, FILES[:1], [MAIN]) is None
    assert split_count("nb_a_remit", ["a.txt"], [MAIN]) is None
    # post182: the standard cells must list as many names too (a typo + its control
    # file is no list), and the files must not contradict the order
    assert split_count(STAGE, FILES, ["nb_rm_one"]) is None
    assert split_count("nb_inex_rm nb_ohex_rm", ["OHEX_A.txt", "INEX_B.txt"],
                       ["nb_inex nb_ohex"]) is None
    assert split_count("nb_inex_rm nb_ohex_rm", ["INEX_A.txt", "OHEX_B.txt"],
                       ["nb_inex nb_ohex"]) == 2


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


# --- post180: the Header / Detail / Trailer shape -----------------------------------

def test_a_record_type_column_makes_the_sheet_segmented_and_it_still_splits(env, capsys):
    """The staging STTM's "Record Type" column (HR / DR / TR) is the segment
    column: its fields 1..N per record no longer read as one flat list (the
    repeated source names broke the generated tests - ruff F601)."""
    _frd, sttm = _chain(env, capsys, _sttm(env / "STTM_seg.xlsx", segmented=True))
    assert [f.feed_id for f in sttm.feeds] == ["nb_a_remit", "nb_b_remit"]
    for feed in sttm.feeds:
        segments = {f.record_segment for f in feed.fields}
        assert segments == {"Header", "Detail", "Trailer"}
        assert any(f.startswith("sttm_list_cells_split:") for f in feed.extraction_flags)
        (flag,) = [f for f in feed.extraction_flags
                   if f.startswith("sttm_standard_table_not_built:")]
        assert f"{feed.stage.table}_sumry" in flag


def test_a_column_the_header_and_detail_share_keeps_its_standard_mapping(env, capsys):
    """One stage table feeds ONE standard table (DDL / IIG model): the header's
    summary-table rows are blank there, and the column the header shares with
    the detail record (REC_SEQ) still reaches the standard table - the first
    field standing for it used to be the header's, without a standard band."""
    from codegen.emit.framework import table_definitions

    frd, sttm = _chain(env, capsys, _sttm(env / "STTM_seg.xlsx", segmented=True))
    config = load_config(REPO / "config" / "config.yaml")
    specs = resolve_feeds(frd, sttm, config, frd_sha256="0" * 64, sttm_sha256="0" * 64)
    spec = next(s for s in specs if s.feed_id == "nb_a_remit")
    (definition,) = table_definitions(spec, config.conventions.get("acfc_prx"), config=config)
    stage = [c for c, _t in definition.stage.business]
    standard = [c for c, _t in definition.standard.business]
    assert definition.standard.table.table == "nb_a_remit"
    assert {"BATCH_ID", "REC_COUNT", "REC_SEQ", "MEMBER_ID"} <= set(stage)
    assert "REC_SEQ" in standard and "MEMBER_ID" in standard
    assert "BATCH_ID" not in standard and "REC_COUNT" not in standard


def test_the_shared_column_prefers_the_field_with_a_standard_band():
    from types import SimpleNamespace

    from codegen.metadata_template import _TableGroup

    header = SimpleNamespace(stage_column="REC_SEQ", standard_column=None)
    detail = SimpleNamespace(stage_column="REC_SEQ", standard_column="REC_SEQ")
    other = SimpleNamespace(stage_column="MEMBER_ID", standard_column="MEMBER_ID")
    group = _TableGroup(stage=None, standard=None,
                        segments=[SimpleNamespace(fields=[header]),
                                  SimpleNamespace(fields=[detail, other])])
    assert group.standard_fields == [detail, other]
    assert group.fields == [header, other]      # post182: the stage side keeps the first
    both = SimpleNamespace(stage_column="REC_SEQ", standard_column="SEQ_STD")
    group = _TableGroup(stage=None, standard=None,
                        segments=[SimpleNamespace(fields=[both, detail])])
    assert group.standard_fields == [both]                 # the first mapped one stays


# --- post181: one standard table per stage table, on every sheet --------------------

@pytest.mark.parametrize("segmented", [False, True])
def test_a_single_table_sheet_naming_a_second_standard_table_blanks_those_rows(
        env, capsys, segmented):
    """No list cells, no split: ONE stage table whose header rows name a summary
    standard table. The DDL / IIG build one standard table per stage table, so
    the summary rows keep stage and leave standard blank + flagged - before, a
    flat sheet kept the dominant table with a NOTE only and a segmented one took
    the first segment's (the summary) table, dropping the main one."""
    path = _sttm(env / f"STTM_one_{segmented}.xlsx", files=FILES[:1], stage="nb_a_remit",
                 segmented=segmented, main="nb_a_remit", sumry="nb_a_remit_sumry")
    frd, sttm = _chain(env, capsys, path)
    (feed,) = sttm.feeds
    assert feed.standard.table == "nb_a_remit"
    by_column = {}
    for f in feed.fields:
        by_column.setdefault(f.stage_column, []).append(f.standard_column)
    assert by_column["BATCH_ID"] == [None] and by_column["MEMBER_ID"] == ["MEMBER_ID"]
    (flag,) = [f for f in feed.extraction_flags
               if f.startswith("sttm_standard_table_not_built:")]
    assert "standard table 'nb_a_remit_sumry', not this feed's 'nb_a_remit'" in flag
    assert not [f for f in feed.extraction_flags if f.startswith("sttm_list")]
