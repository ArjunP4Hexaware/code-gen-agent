"""Resolver: real fixture pairs resolve; disagreeing contracts fail loudly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen.resolve.resolver import ContractMismatchError, resolve_pair

REPO = Path(__file__).resolve().parents[1]

MIDS_FEED_IDS = {
    "sd_community_demographic_risk",
    "sd_community_risk",
    "sd_individual_risk",
}


def test_mids_pair_resolves_three_flat_feeds(mids_specs):
    assert {spec.feed_id for spec in mids_specs} == MIDS_FEED_IDS
    for spec in mids_specs:
        assert not spec.is_segmented
        assert [segment.segment for segment in spec.segments] == ["Detail"]


def test_caqh_resolves_segmented_with_recycle(caqh_spec):
    assert caqh_spec.feed_id == "caqh_tpl_inbound_files"
    assert caqh_spec.is_segmented
    assert {segment.segment for segment in caqh_spec.segments} == {
        "Header",
        "Detail",
        "Trailer",
    }
    assert caqh_spec.delimiter == "|"
    assert caqh_spec.recycle is not None
    assert caqh_spec.recycle.spec.recycle_window_days == 15
    assert caqh_spec.sttm_is_synthetic
    # Stage-only feed: FRD's standard target is empty ("load AS-IS").
    assert caqh_spec.standard_table is None


def test_side_tables_follow_stage_table_case(caqh_spec):
    assert caqh_spec.errors_table.table == "EXT_TPL_CAQH_DTL_ERRORS"
    assert caqh_spec.recycle.recycle_table.table == "EXT_TPL_CAQH_DTL_RECYCLE"


def test_delimiter_mismatch_is_loud(config, tmp_path):
    pair = config.contracts.pairs[1]
    contracts_dir = REPO / config.contracts.dir
    raw = json.loads((contracts_dir / pair.frd).read_text(encoding="utf-8"))
    for feed in raw["feeds"]:
        feed["delimiter"] = ","
    frd_path = tmp_path / "frd.json"
    frd_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ContractMismatchError):
        resolve_pair(frd_path, contracts_dir / pair.sttm, config)
