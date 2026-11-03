"""post156: ONE STTM mapping sheet mapping SEVERAL tables (the pair_09 shape).

The FRD's one block names N target tables; the STTM maps all N on one sheet
(its stage TableName column, a table per block of rows). Read as one table, the
other N-1 met nothing (ContractMismatchError "N-1 tables only in FRD"). Now each
table is its own feed - every pairing from the documents' rows or an exact name,
never a guess - and, the source being a database table, each writes its DDL and
test cases and holds its IIG (post155). Chain as the harness runs it: layout
--frd-contract-out -> extract-sttm -> the resolver's FRD ⋈ STTM join. Synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from acfc_shapes import one_sheet_tables as ost
from codegen import cli
from codegen.config import load_config
from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract
from codegen.layout.resolve import split_frd_feeds_by_sttm
from codegen.resolve.resolver import resolve_feeds

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
DATE = "2026-10-29"
STAGES = [stage for stage, _std, _cols in ost.TABLES.values()]
PAIR4_FRD = REPO / "fixtures" / "acfc_shapes" / "pair_4" / "frd_nb_cob_report.contract.json"


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    return tmp_path


def _chain(tmp: Path, capsys, *, blank_repeats: bool = False, tag: str = "a"):
    sttm, frd = tmp / f"STTM_nb_provider_{tag}.xlsx", tmp / f"FRD_nb_provider_{tag}.docx"
    ost.build_sttm(blank_repeats=blank_repeats).save(sttm)
    frd.write_bytes(ost.build_frd())
    frd_out, sttm_out = tmp / f"frd_{tag}.contract.json", tmp / f"sttm_{tag}.contract.json"
    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(frd_out)]) == 0
    layout_out = capsys.readouterr().out
    code = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_out),
                     "--out", str(sttm_out), "--generated-date", DATE])
    out = capsys.readouterr().out
    assert code == 0, layout_out + out
    return frd_out, sttm_out, layout_out


def _contracts(frd_out: Path, sttm_out: Path):
    return (FrdContract.model_validate(json.loads(frd_out.read_text(encoding="utf-8"))),
            SttmContract.model_validate(json.loads(sttm_out.read_text(encoding="utf-8"))))


def test_each_table_of_the_sheet_is_its_own_feed(env, capsys):
    frd_out, sttm_out, layout_out = _chain(env, capsys)
    frd, sttm = _contracts(frd_out, sttm_out)
    assert [f.stage_target.tables for f in frd.feeds] == [[t] for t in STAGES]
    assert [f.feed_name for f in frd.feeds] == STAGES          # named after its table
    assert sorted(f.stage.table for f in sttm.feeds) == sorted(STAGES)
    # the split travels with the contract (a CLI generate raises the same flag)
    assert "frd_feeds_split_per_table" in frd_out.read_text(encoding="utf-8")


def test_each_feed_has_only_its_own_rows(env, capsys):
    frd_out, sttm_out, _out = _chain(env, capsys)
    _frd, sttm = _contracts(frd_out, sttm_out)
    for feed in sttm.feeds:
        source = next(s for s, (stage, _std, _c) in ost.TABLES.items() if stage == feed.stage.table)
        assert [f.source_column for f in feed.fields] == [c for c, *_ in ost.TABLES[source][2]]


def test_a_blank_table_cell_belongs_to_the_block_above(env, capsys):
    frd_out, sttm_out, _out = _chain(env, capsys, blank_repeats=True, tag="b")
    _frd, sttm = _contracts(frd_out, sttm_out)
    sizes = {f.stage.table: len(f.fields) for f in sttm.feeds}
    assert sizes == {stage: len(cols) for stage, _std, cols in ost.TABLES.values()}


def test_the_standard_table_comes_from_the_rows_and_the_join_holds(env, capsys):
    frd_out, sttm_out, _out = _chain(env, capsys)
    frd, sttm = _contracts(frd_out, sttm_out)
    pairs = {f.stage_target.tables[0]: f.standard_target.tables for f in frd.feeds}
    assert pairs == {stage: [std] for stage, std, _c in ost.TABLES.values()}
    specs = resolve_feeds(frd, sttm, load_config(CONFIG), frd_sha256="0" * 64,
                          sttm_sha256="0" * 64)                  # no ContractMismatchError
    assert sorted(s.feed_slug for s in specs) == sorted(STAGES)


# ---- the strict split, by its rules (no workbook) ------------------------------


def _one_feed(tables, patterns=(), standard=()):
    frd = FrdContract.model_validate(json.loads((PAIR4_FRD).read_text("utf-8")))
    feed = frd.feeds[0]
    feed = feed.model_copy(update={
        "file_name_patterns": list(patterns),
        "stage_target": feed.stage_target.model_copy(update={"tables": list(tables)}),
        "standard_target": feed.standard_target.model_copy(update={"tables": list(standard)})})
    return frd.model_copy(update={"feeds": [feed]})


def _facts(tables, rows, *, segmented=False):
    return {"sheet_tables": [{"sheet": "Mapping", "stage_table": tables[0],
                              "stage_tables": list(tables), "table_rows": rows,
                              "segmented": segmented, "standard_table": None,
                              "standard_tables": [], "own_files": []}]}


def _split(frd, facts):
    return split_frd_feeds_by_sttm(frd, facts, {}, load_config(CONFIG))


@pytest.mark.skipif(not PAIR4_FRD.exists(), reason="pair_4 FRD contract fixture absent")
class TestTheRules:
    def test_a_file_pattern_is_taken_only_by_exact_identity(self):
        frd = _one_feed(["t_a", "t_b"], patterns=["T_A_YYYYMMDD.txt", "T_BEE.txt"])
        out, flags, _q = _split(frd, _facts(["t_a", "t_b"], [("t_a", None, None),
                                                            ("t_b", None, None)]))
        assert [f.file_name_patterns for f in out.feeds] == [["T_A_YYYYMMDD.txt"], []]
        assert any("feeds[1].file_name_patterns" in f for f in flags)   # never "t_bee"

    def test_two_standard_tables_for_one_stage_table_pair_neither(self):
        frd = _one_feed(["t_a", "t_b"], standard=["s_a", "s_x", "s_b"])
        out, flags, _q = _split(frd, _facts(["t_a", "t_b"], [
            ("t_a", "s_a", None), ("t_a", "s_x", None), ("t_b", "s_b", None)]))
        assert [f.standard_target.tables for f in out.feeds] == [[], ["s_b"]]
        assert any(f.startswith("table_split_standard_unpaired:t_a") for f in flags)

    def test_a_segmented_sheet_is_never_split_per_table(self):
        frd = _one_feed(["t_hdr", "t_dtl"])
        out, _flags, _q = _split(frd, _facts(["t_hdr", "t_dtl"], [("t_hdr", None, None),
                                                                ("t_dtl", None, None)],
                                             segmented=True))
        assert len(out.feeds) == 1

    def test_tables_the_frd_does_not_name_are_not_split_here(self):
        frd = _one_feed(["t_a", "t_b"])
        out, flags, _q = _split(frd, _facts(["t_a", "t_c"], [("t_a", None, None),
                                                            ("t_c", None, None)]))
        assert not any("frd_feeds_split_per_table" in f for f in flags)

