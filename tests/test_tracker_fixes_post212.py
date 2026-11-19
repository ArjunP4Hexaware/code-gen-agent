"""post212: the incident tracker's re-opened / new CodeGen items (2026-11-19 triage), on
SYNTHETIC documents shaped like the real Accumulators FRD.

#5  - an FRD-stated wildcard pattern ("*_X_*_Y*") is SRC_FILE_NAME as stated; the family
      convention only shapes a pattern derived from a sample name.
#7 / #20 - the ADLS Location cell's "Archive Path:" lines: the first (the main one) is the
      feed's archive; on the raw-file sheets SRC_ADLS_ARCHVL_PATH = that path (Soham: "FRD
      path wins"), in SRC_ADLS_PATH's form (the landing + the archive's own tail).
#18 - the combined DDL writes the standard reject table the STGDELTA row names.
#19 - the table COMMENT's description: the FRD's Descriptive Metadata Description when
      the STTM states no Table Description.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from acfc_shapes import family_e_multi as fm
from codegen.config import load_config
from codegen.extract.frd_docx import extract_frd_contract

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")
RAW = "synacct01/mftlanding/inbound/vendor_e/care_mgmt"


def _tpl(style: str):
    _name, tpl = CONFIG.metadata.resolve("iig_v2")
    return tpl.model_copy(update={"family_conventions": tpl.family_conventions.model_copy(
        update={"src_file_name": style})})


# #5 ------------------------------------------------------------------------------
def test_an_frd_stated_glob_is_written_as_stated():
    from codegen.metadata_template import _src_file_name_cell

    cell = _src_file_name_cell(_tpl("prefix_star"), "*_SYNRX_*_CMACCUM*", "*_SYNRX_*_CMACCUM*",
                               "from_frd")
    assert cell["value"] == "*_SYNRX_*_CMACCUM*"


def test_a_pattern_derived_from_a_sample_keeps_the_family_convention():
    from codegen.metadata_template import _src_file_name_cell

    # a sample name with date tokens (no wildcard stated): the convention shapes it
    cell = _src_file_name_cell(_tpl("prefix_star"), "SYNRX_CMACCUM_*.txt",
                               "SYNRX_CMACCUM_YYYYMMDD.txt", "from_frd")
    assert cell["value"] == "SYNRX_CMACCUM*"


def test_a_stated_glob_from_the_sttm_keeps_the_convention():
    from codegen.metadata_template import _src_file_name_cell

    cell = _src_file_name_cell(_tpl("prefix_star"), "*_SYNRX_*_CMACCUM*", "*_SYNRX_*_CMACCUM*",
                               "from_sttm")
    assert cell["value"] != "*_SYNRX_*_CMACCUM*"


# #7 / #20 ------------------------------------------------------------------------
ADLS_CELL = (f"Raw Path:\n{RAW}/<File.extn>\n"
             f"Archive Path:\n{RAW}/archive/<File.extn>\n"
             f"Archive Path:\n{RAW}/daily/archive/<File.extn>")


def _read(tmp_path, **kwargs):
    path = tmp_path / "FRD.docx"
    path.write_bytes(fm.build_frd(**kwargs))
    contract, _ = extract_frd_contract(path, CONFIG, generated_date="2026-11-19")
    return contract


def test_every_labelled_path_of_a_cell_in_order():
    from codegen.extract.frd_docx import _labelled_paths

    assert _labelled_paths(ADLS_CELL, {"archive path"}) == [
        f"{RAW}/archive/<File.extn>", f"{RAW}/daily/archive/<File.extn>"]


def test_the_first_archive_path_is_the_feeds_and_the_others_are_named(tmp_path):
    contract = _read(tmp_path, adls_location=ADLS_CELL)
    feed = contract.feeds[0]
    assert feed.landing_location == RAW + "/"
    assert feed.archive_location == RAW + "/archive/"              # <File.extn> dropped
    (flag,) = [f for f in contract.extraction_flags if f.startswith("frd_archive_main:")]
    assert "2 archive paths" in flag


def test_no_archive_line_no_archive(tmp_path):
    assert _read(tmp_path).feeds[0].archive_location is None


def test_the_archive_tail_under_the_landing():
    from codegen.metadata_template import _stated_archive_tail

    feed = SimpleNamespace(landing_location="mftlanding/inbound/v/cm/",
                           archive_location="mftlanding/inbound/v/cm/archive/")
    assert _stated_archive_tail(feed) == "archive/"
    other = SimpleNamespace(landing_location="mftlanding/inbound/v/cm/",
                            archive_location="mftlanding/archive/v/cm/")
    assert _stated_archive_tail(other) is None                   # not under: the shape stays
    assert _stated_archive_tail(SimpleNamespace(landing_location="a/b/",
                                                archive_location=None)) is None


def test_the_raw_file_sheets_take_the_stated_archive():
    assert CONFIG.metadata.resolve("iig_v2")[1].stated_archive_tabs == [
        "ADLS_DELTA_INGESTION_DETAILS", "ADLS_FIXED_WIDTH_HANDLER"]


# #18 -----------------------------------------------------------------------------
def _rule():
    from codegen.config import StandardRejectTableConfig

    return StandardRejectTableConfig(banner="--standard reject table", suffix="_reject",
                                     column_type="String",
                                     extra_columns={"REJECT_REASON": "String",
                                                    "SRC_TABLE_NAME": "String",
                                                    "RUNID": "String"},
                                     citation="synthetic")


def _definition(standard_qualified: str | None):
    standard = (SimpleNamespace(qualified=standard_qualified,
                                columns=[("MBR_ID", "String"), ("AMT", "Decimal(12,2)"),
                                         ("REC_CREATION_TIME", "TIMESTAMP")])
                if standard_qualified else None)
    return SimpleNamespace(stage=SimpleNamespace(table=SimpleNamespace(table="syn_feed")),
                           standard=standard)


def _profile(rule):
    return SimpleNamespace(standard_reject_table=rule, block_using_prefix={},
                           cluster_by={"standard": "CLUSTER BY AUTO"},
                           standard_tblproperties={"delta.minReaderVersion": "1"})


def test_the_standard_reject_table_is_named_as_the_iig_names_it():
    from codegen.emit.framework import _standard_reject_blocks

    flags: list[str] = []
    (block,) = _standard_reject_blocks([_definition("d1_std.syn.syn_feed")], _profile(_rule()),
                                       None, flags)
    assert block["qualified"] == "d1_std.syn.syn_feed_reject"
    assert block["columns"] == [("MBR_ID", "String", None), ("AMT", "String", None),
                                ("REC_CREATION_TIME", "String", None),
                                ("REJECT_REASON", "String", None),
                                ("SRC_TABLE_NAME", "String", None), ("RUNID", "String", None)]
    assert block["table_comment"] is None and block["cluster_by"] == "CLUSTER BY AUTO"
    commented = _rule().model_copy(update={"comment": "Rejected by {table}"})
    (block,) = _standard_reject_blocks([_definition("d1_std.syn.syn_feed")], _profile(commented),
                                       None, None)
    assert block["table_comment"] == "Rejected by d1_std.syn.syn_feed"
    assert flags and flags[0].startswith("ddl_standard_reject_table:d1_std.syn.syn_feed_reject")


def test_no_rule_or_no_standard_table_no_reject_block():
    from codegen.emit.framework import _standard_reject_blocks

    assert _standard_reject_blocks([_definition("d1_std.syn.syn_feed")], _profile(None),
                                   None, None) == []
    assert _standard_reject_blocks([_definition(None)], _profile(_rule()), None, None) == []


def test_the_acfc_profile_writes_it_and_the_pair1_golden_does_not():
    assert CONFIG.conventions.profiles["acfc_prx"].standard_reject_table is not None
    overlay = (REPO / "fixtures" / "acfc_shapes" / "pair_1" / "config_overlay.yaml").read_text(
        encoding="utf-8")
    assert "standard_reject_table: null" in overlay


# #19 -----------------------------------------------------------------------------
PROFILE = SimpleNamespace(table_description_comment=True, column_comment_separator=" — ",
                          load_strategy_comment="Load strategy: {strategy} ({layer})")


def test_the_frd_description_is_the_table_comment_when_the_sttm_states_none():
    from codegen.emit.framework import _table_comment

    spec = SimpleNamespace(table_descriptions={}, frd_description="Synthetic member claims")
    undescribed: list[str] = []
    comment = _table_comment(PROFILE, spec, "standard", SimpleNamespace(table="t"), "Append",
                             "STD", undescribed)
    assert comment == "Synthetic member claims — Load strategy: Append (STD)"
    assert undescribed == []


def test_the_sttm_table_description_still_wins():
    from codegen.emit.framework import _table_comment

    spec = SimpleNamespace(table_descriptions={"standard.t": "STTM text"},
                           frd_description="FRD text")
    assert _table_comment(PROFILE, spec, "standard", SimpleNamespace(table="t"), "Append",
                          "STD", []).startswith("STTM text")


def test_the_descriptive_description_row_is_read(tmp_path):
    assert _read(tmp_path).feeds[0].description == (
        "Monthly care management extracts from Northwind Benefits")
