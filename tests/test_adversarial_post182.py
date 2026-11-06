# ruff: noqa: E501  -- fixture data rows kept on one line
"""post182: an adversarial review of post178-181 - each case fed an unusual but
plausible synthetic workbook and showed wrong output, a silent drop or a crash.
One test per finding (the review's numbering). Synthetic Northwind vocabulary.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from acfc_shapes import family_e_multi as fm
from acfc_shapes.cold_pairs import _merge, _sheet
from acfc_shapes.common import new_workbook
from codegen import cli
from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract
from codegen.resolve.resolver import resolve_feeds

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-11-06"
LIST = "nb_a_remit nb_b_remit"
TWO_FILES = ["A_YYYYMMDD.txt", "B_YYYYMMDD.txt"]


def _flat(path: Path, rows, files, *, meta_extra=(), vmerge_std=()) -> Path:
    """rows: (field, stage table, stage column, standard table, standard column, stage type)."""
    wb = new_workbook()
    titles = ["Source File Layout", None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    if not any(r[0] == "NA" for r in rows):
        rows = [*rows, ("NA", rows[-1][1], "SRC_FILE_NAME", rows[-1][3], "SRC_FILE_NAME", "String")]
    body = [[name, f"{name} desc", "varchar", "N", "stg_nb_rm", stage, column, stype,
             "nb_rm", std, scol, "String", None] for name, stage, column, std, scol, stype in rows]
    meta = [["Project Name", "Northwind Remittance Data"], ["File Name", "\n".join(files)],
            *meta_extra]
    ws = _sheet(wb, "REMIT", [*meta, [], titles, header, *body])
    head = len(meta) + 2
    for first, last in ((1, 4), (5, 8), (9, 12)):
        _merge(ws, head, first, last)
    for a, b in vmerge_std:        # data-row indexes, inclusive: a vertical merged cell
        ws.merge_cells(start_row=head + 2 + a, start_column=10, end_row=head + 2 + b,
                       end_column=10)
    wb.save(path)
    return path


def _segmented(path: Path, recs, files) -> Path:
    """recs: (record type, field, column, standard table, standard column, stage type)."""
    wb = new_workbook()
    titles = ["Source File Layout", None, None, None, None, "Stage Layer", None, None, None,
              "Standard Layer", None, None, None, None]
    header = ["Record Type", "Field Name", "Description", "Data Type", "Mandatory Field",
              "Schema", "TableName", "ColumnName", "DataType",
              "Schema", "TableName", "ColumnName", "DataType", "Recycle Flag"]
    body = [[rt, n, f"{n} d", "varchar", "N", "stg_x", "nb_x", c, t, "nb_rm", std, sc, "String", None]
            for rt, n, c, std, sc, t in recs]
    body.append([recs[-1][0], "NA", None, None, None, "stg_x", "nb_x", "SRC_FILE_NAME", "String",
                 "nb_rm", "nb_x", "SRC_FILE_NAME", "String", None])
    ws = _sheet(wb, "REMIT", [["Project Name", "Northwind Remittance Data"],
                              ["File Name", "\n".join(files)], [], titles, header, *body])
    for first, last in ((1, 5), (6, 9), (10, 13)):
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


def _mapped(feed) -> dict[str, str | None]:
    return {f.stage_column: f.standard_column for f in feed.fields}


# 1 - the main standard table: the stage table's namesake, else a strict majority
def test_a_tie_keeps_the_table_named_like_the_stage_table(env, capsys):
    rows = [("batch_id", "nb_x", "BATCH_ID", "nb_x_sumry", "BATCH_ID", "String"),
            ("batch_dt", "nb_x", "BATCH_DT", "nb_x_sumry", "BATCH_DT", "String"),
            ("member_id", "nb_x", "MEMBER_ID", "nb_x", "MEMBER_ID", "String"),
            ("paid_amt", "nb_x", "PAID_AMT", "nb_x", "PAID_AMT", "String")]
    _frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows, ["X_YYYYMMDD.txt"]))
    mapped = _mapped(sttm.feeds[0])
    assert mapped["MEMBER_ID"] == "MEMBER_ID" and mapped["PAID_AMT"] == "PAID_AMT"
    assert mapped["BATCH_ID"] is None and mapped["BATCH_DT"] is None


def test_a_tie_without_a_namesake_builds_no_standard_table_and_says_so(env, capsys):
    rows = [("a1", "nb_y", "A1", "nb_p", "A1", "String"), ("a2", "nb_y", "A2", "nb_p", "A2", "String"),
            ("b1", "nb_y", "B1", "nb_q", "B1", "String"), ("b2", "nb_y", "B2", "nb_q", "B2", "String"),
            ("NA", "nb_y", "SRC_FILE_NAME", None, "SRC_FILE_NAME", "String")]
    _frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows, ["Y_YYYYMMDD.txt"]))
    (feed,) = sttm.feeds
    assert all(v is None for k, v in _mapped(feed).items() if k != "SRC_FILE_NAME")
    (flag,) = [f for f in feed.extraction_flags if f.startswith("sttm_standard_table_ambiguous:")]
    assert "['nb_p', 'nb_q']" in flag


# 2 - a vertical merged standard TableName cell carries down within its stage block
@pytest.mark.parametrize("merges", [((0, 1), (2, 4)), ((0, 1), (3, 4))])
def test_a_merged_standard_cell_is_read_for_every_row_it_spans(env, capsys, merges):
    rows = [("batch_id", "nb_x", "BATCH_ID", "nb_x_sumry", "BATCH_ID", "String"),
            ("batch_dt", "nb_x", "BATCH_DT", None, "BATCH_DT", "String"),
            ("member_id", "nb_x", "MEMBER_ID", "nb_x", "MEMBER_ID", "String"),
            ("paid_amt", "nb_x", "PAID_AMT", "nb_x" if merges[1][0] == 3 else None, "PAID_AMT", "String"),
            ("claim_ref", "nb_x", "CLAIM_REF", None, "CLAIM_REF", "String"),
            ("NA", "nb_x", "SRC_FILE_NAME", "nb_x", "SRC_FILE_NAME", "String")]
    _frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows, ["X_YYYYMMDD.txt"],
                                           vmerge_std=merges))
    mapped = _mapped(sttm.feeds[0])
    assert mapped["BATCH_ID"] is None and mapped["BATCH_DT"] is None      # the summary block
    assert mapped["MEMBER_ID"] and mapped["PAID_AMT"] and mapped["CLAIM_REF"]


# 3 - a sheet named like ANOTHER sheet's file pairs with its own file's feed
def test_sheets_named_like_each_others_files_pair_with_their_own_file(env, capsys):
    rows = [(n, "nb_x", n.upper(), "nb_x", n.upper(), "String") for n in ("member_id", "paid_amt")]
    path = _flat(env / "s.xlsx", rows, ["PHARMACY_YYYYMMDD.txt"])
    wb = load_workbook(path)
    wb["REMIT"].title = "CLAIMS"
    other = wb.copy_worksheet(wb["CLAIMS"])
    other.title = "PHARMACY"
    other.cell(row=2, column=2).value = "CLAIMS_YYYYMMDD.txt"
    other.cell(row=6, column=1).value = "rx_only"
    other.cell(row=6, column=7).value = "RX_ONLY"
    other.cell(row=6, column=11).value = "RX_ONLY"
    wb.save(path)
    _frd, sttm = _chain(env, capsys, path)
    by_sheet = {f.mapping_sheet: f for f in sttm.feeds}
    assert by_sheet["CLAIMS"].source_file.name_pattern == "PHARMACY_YYYYMMDD.txt"
    assert by_sheet["PHARMACY"].source_file.name_pattern == "CLAIMS_YYYYMMDD.txt"
    assert "RX_ONLY" in {f.stage_column for f in by_sheet["PHARMACY"].fields}


# 4 - a two-word typo + a control file is no list
def test_a_two_word_name_with_a_file_and_its_control_file_is_not_split(env, capsys):
    rows = [(n, "nb_member elig", n.upper(), "nb_member_elig", n.upper(), "String")
            for n in ("member_id", "paid_amt")]
    _frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows,
                                           ["MEMBER_ELIG_YYYYMMDD.txt", "MEMBER_ELIG_YYYYMMDD.ctl"]))
    (feed,) = sttm.feeds
    assert feed.stage.table == "nb_member elig"           # the resolver says so, as before
    assert not [f for f in feed.extraction_flags if f.startswith("sttm_list")]


# 5 - a comma-separated list splits the same on both sides
def test_a_comma_separated_list_resolves(env, capsys):
    st = "nb_a_remit, nb_b_remit"
    rows = [(n, st, n.upper(), st, n.upper(), "String") for n in ("member_id", "paid_amt")]
    frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows, TWO_FILES))
    assert [f.stage_target.tables for f in frd.feeds] == [["nb_a_remit"], ["nb_b_remit"]]
    specs = resolve_feeds(frd, sttm, load_config(REPO / "config" / "config.yaml"),
                          frd_sha256="0" * 64, sttm_sha256="0" * 64)
    assert sorted(s.feed_id for s in specs) == ["nb_a_remit", "nb_b_remit"]
    assert all("'nb_a_remit,'" not in f for s in sttm.feeds for f in s.extraction_flags)


# 6 - layout and extraction decide the split from the same evidence
def test_a_file_name_example_row_does_not_change_the_split(env, capsys):
    rows = [(n, LIST, n.upper(), LIST, n.upper(), "String") for n in ("member_id", "paid_amt")]
    frd, sttm = _chain(env, capsys, _flat(env / "s.xlsx", rows, TWO_FILES, meta_extra=[
        ["File Name Example", "A_20261101.txt\nB_20261101.txt"]]))
    assert [f.feed_name for f in frd.feeds] == ["nb_a_remit", "nb_b_remit"]
    assert [f.feed_id for f in sttm.feeds] == ["nb_a_remit", "nb_b_remit"]


# 7 - the stage column keeps the first record's type; a conflict is flagged
def test_a_shared_stage_column_keeps_the_first_type_and_flags_the_conflict(env, capsys):
    from codegen.emit.framework import table_definitions

    recs = [("HR", "rec_seq", "REC_SEQ", "nb_x_sumry", "REC_SEQ", "String"),
            ("HR", "batch_id", "BATCH_ID", "nb_x_sumry", "BATCH_ID", "String"),
            ("DR", "rec_seq", "REC_SEQ", "nb_x", "REC_SEQ", "Integer"),
            ("DR", "member_id", "MEMBER_ID", "nb_x", "MEMBER_ID", "String"),
            ("DR", "paid", "PAID", "nb_x", "PAID", "String"),
            ("TR", "cnt", "CNT", "nb_x_sumry", "CNT", "String")]
    frd, sttm = _chain(env, capsys, _segmented(env / "s.xlsx", recs, ["X_YYYYMMDD.txt"]))
    config = load_config(REPO / "config" / "config.yaml")
    (spec,) = resolve_feeds(frd, sttm, config, frd_sha256="0" * 64, sttm_sha256="0" * 64)
    flags: list[str] = []
    (definition,) = table_definitions(spec, config.conventions.get("acfc_prx"), flags,
                                      config=config)
    assert dict(definition.stage.business)["REC_SEQ"].lower() == "string"
    assert "REC_SEQ" in dict(definition.standard.business)
    (conflict,) = [f for f in flags if f.startswith("stage_type_conflict:")]
    assert "'REC_SEQ'" in conflict and "Integer" in conflict


# 8 - flags cite the real sheet and the right feed
def test_a_split_after_another_sheet_cites_the_sheet_and_its_feed(env, capsys):
    rows = [(n, LIST, n.upper(), LIST, n.upper(), "String") for n in ("member_id", "paid_amt")]
    path = _flat(env / "s.xlsx", rows, TWO_FILES)
    wb = load_workbook(path)
    other = wb.copy_worksheet(wb["REMIT"])
    other.title = "AAA"
    other.cell(row=2, column=2).value = "C_YYYYMMDD.txt"
    for r in range(6, 9):
        other.cell(row=r, column=6).value = "nb_c_remit"
        other.cell(row=r, column=10).value = "nb_c_remit"
    wb.move_sheet("AAA", offset=-(len(wb.sheetnames) - 1))
    wb.save(path)
    frd, _sttm = _chain(env, capsys, path)
    assert not [f for f in frd.extraction_flags if " of 2]" in f]
    index = {f.feed_name: i for i, f in enumerate(frd.feeds)}
    a = index["nb_a_remit"]
    assert any(f.startswith(f"frd_unstated:feeds[{a}].file_name_patterns") and "'A_YYYYMMDD.txt'" in f
               for f in frd.extraction_flags)
    assert any(f.startswith(f"frd_unstated:feeds[{a}].stage_target.schema") and "'REMIT'" in f
               for f in frd.extraction_flags)


# 9 - a nested target-table cell: header under a title row, a list in a cell
def test_nested_table_names_handles_a_title_row_lists_and_a_second_table(config):
    from codegen.extract.frd_docx import nested_table_names

    frd = config.extractor.frd
    titled = [["Target Table", "Target Table"], ["Vendor", "Table Name"], ["Acme", "stg_a"],
              ["Beta", "stg_b"]]
    assert nested_table_names(titled, frd) == (["stg_a", "stg_b"], "Table Name")
    assert nested_table_names([["Vendor", "Target Table"], ["Acme", "stg_a, stg_b"]], frd) == (
        ["stg_a", "stg_b"], "Target Table")
    pooled = [["Vendor", "Target Table"], ["Acme", "stg_a"], ["Vendor", "Target Table"],
              ["Beta", "stg_b"]]
    assert nested_table_names(pooled, frd)[0] == ["stg_a"]
    assert nested_table_names([["Acme", "stg_a"], ["Beta", "stg_b"]], frd) == ([], None)


# the post180 regression - a "Record Type" column that is no segment column
def test_a_record_type_column_without_segment_words_reads_unsegmented(env, capsys):
    recs = [("Member", "member_id", "MEMBER_ID", "nb_x", "MEMBER_ID", "String"),
            ("Claim", "claim_id", "CLAIM_ID", "nb_x", "CLAIM_ID", "String")]
    _frd, sttm = _chain(env, capsys, _segmented(env / "s.xlsx", recs, ["X_YYYYMMDD.txt"]))
    (feed,) = sttm.feeds
    assert all(f.record_segment is None for f in feed.fields)
    (flag,) = [f for f in feed.extraction_flags if f.startswith("segment_column_not_segments:")]
    assert "'Record Type'" in flag
