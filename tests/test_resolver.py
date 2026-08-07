"""Resolver: real fixture pairs resolve; disagreeing contracts fail loudly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen.resolve.resolver import ContractMismatchError, _parse_reference, resolve_pair

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


# Recycle reference parsing accepts BOTH the canonical phrasing and the
# client phrasing carried verbatim from workbooks/FRDs (decision D3).


def test_reference_canonical_and_client_phrasings_agree():
    canonical = _parse_reference(
        "Match member_id against SUBS_ID in PR_STD.COREMEMBER.CM_SUBS_MASTER "
        "where GRP_CK = 47",
        "feed",
    )
    client = _parse_reference(
        "Check with SUBS_ID from CoreMember in the PR_STD.COREMEMBER.CM_SUBS_MASTER "
        "FOR GRP_CK = 47,\nif available process it else load this to the Recycle Table "
        "with Recycle Flag Enabled for 7 days.",
        "feed",
    )
    assert canonical == client == ("PR_STD.COREMEMBER.CM_SUBS_MASTER", "SUBS_ID", "GRP_CK = 47")


def test_client_phrasing_without_table_alias_parses():
    # The MIDS FRD's own phrasing: table directly after "from", no alias.
    assert _parse_reference(
        "Check with SBSB_ID from PR_STD.FACETS.CMC_SBSB_SUBSC FOR GRGR_CK = 31, "
        "if unavailable process to Recycle Table",
        "feed",
    ) == ("PR_STD.FACETS.CMC_SBSB_SUBSC", "SBSB_ID", "GRGR_CK = 31")


def test_malformed_reference_is_still_loud():
    with pytest.raises(ContractMismatchError, match="not parseable"):
        _parse_reference("recycle unmatched records nightly", "feed")


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
