"""post110 (codeflow audit #1): the generic (content-path) reader's recycle rule
from the per-row Recycle Flag cells. A no-value cell (N / No) is an unflagged
row; every other non-empty cell must be a ``Y ( <validation> )`` flag, as the
classic reader requires. Before this, the first non-empty cell decided alone: an
N above the Y row dropped the rule silently, and a second flagged row was never
read."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from codegen.config import load_config
from codegen.extract.generic import FieldRow, GenericExtractionError, SheetData, _recycle
from test_derivations import REPO

RULE = "Y ( Check with MBR_ID from SYN_MEMBERS for 7 days )"


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _sheet(*cells: str | None) -> SheetData:
    rows = [FieldRow(sheet="SYN_MAPPING", row=10 + i, col=1, segment_raw=None, segment=None,
                     values={"source.field_name": f"COL_{i}", "rules.recycle_flag": cell})
            for i, cell in enumerate(cells)]
    return SheetData(profile=SimpleNamespace(name="SYN_MAPPING"), meta={}, meta_raw=[],
                     fields=rows)


def _read(config, *cells):
    return _recycle(_sheet(*cells), config, config.extractor.discovery)


def test_an_n_above_the_flagged_row_no_longer_hides_the_rule(config):
    spec = _read(config, "N", None, "No", RULE, "N")
    assert spec is not None and spec.enabled
    assert spec.applies_to == "COL_3"
    assert spec.validation == "Check with MBR_ID from SYN_MEMBERS for 7 days"
    assert spec.recycle_window_days == 7


def test_only_no_values_or_blanks_is_no_recycle(config):
    assert _read(config, "N", None, "no", "N") is None
    assert _read(config, None, None) is None


def test_the_same_rule_on_several_rows_is_one_rule(config):
    spec = _read(config, "N", RULE, RULE)
    assert spec is not None and spec.applies_to == "COL_1"


def test_two_different_rules_stop_the_extraction(config):
    with pytest.raises(GenericExtractionError, match="different recycle rules") as caught:
        _read(config, RULE, "Y ( Check with SUBS_ID from SYN_SUBS for 30 days )")
    assert caught.value.reason == "sttm.conflict"


@pytest.mark.parametrize(("cell", "reason"), [
    ("Maybe", "sttm.value"),        # neither a no-value nor a Y ( ... ) flag
    ("Y ( )", "sttm.missing"),      # a flag with no validation text
])
def test_an_unreadable_flag_cell_stops_the_extraction(config, cell, reason):
    with pytest.raises(GenericExtractionError) as caught:
        _read(config, "N", cell)
    assert caught.value.reason == reason
    assert "row 11" in str(caught.value)


# -- post117 (codeflow audit #3): the recycle_unknown_column answer is applied -- #


def test_a_recycle_column_answer_is_applied(tmp_path, monkeypatch):
    """A recycle rule whose column is no source column of the sheet (the flag on a
    row the extractor does not keep as a field) asks feeds[i].recycle.applies_to.
    The answer was dropped unread (the answers parser kept only file_format /
    source_system), so the feed could only ask again."""
    from codegen.contracts.sttm import RecycleSpec
    from codegen.extract import NeedsAnswersError, extract_contract, generic
    from codegen.extract.generic import parse_cell_answers
    from test_layout_discovery import GENERATED_DATE, STTM, _frd, _write_frd

    config = load_config(REPO / "config" / "config.yaml")
    stray = RecycleSpec(applies_to="NOT_A_SOURCE_COLUMN", enabled=True,
                        validation="Check with MBR_ID from SYN_MEMBERS for 7 days",
                        on_match="m", on_no_match="n", recycle_window_days=7)
    monkeypatch.setattr(generic, "_recycle", lambda *_a: stray)
    frd = _write_frd(tmp_path, _frd("FEED_4 remit", ["feed_4_remit_YYYYMMDD.dat"],
                                    ["feed_4_remit"], ["feed_4_remit"], fmt="dat", delimiter="|",
                                    stage_schema="stg_remit", std_schema="remit"))
    workbook = STTM / "pair_4_family_d.xlsx"
    key = "feeds[0].recycle.applies_to"
    with pytest.raises(NeedsAnswersError) as asked:
        extract_contract(workbook, frd, config, generated_date=GENERATED_DATE)
    assert key in [p.key for p in asked.value.pending]
    assert parse_cell_answers({key: "REMIT_ID"}) == {key: "REMIT_ID"}
    contract = extract_contract(workbook, frd, config, generated_date=GENERATED_DATE,
                                gaps={key: "REMIT_ID"})
    assert not contract.needs_answers
    (feed,) = contract.feeds
    assert feed.load_rules.recycle.applies_to == "REMIT_ID"
    assert any(f.startswith(f"answered_value:{key}") for f in feed.extraction_flags)
