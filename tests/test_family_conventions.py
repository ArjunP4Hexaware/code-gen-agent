"""Per-feed-family IIG conventions (correction 2026-10-08).

Two feed families fill four IIG cells differently — neither is an error:

| cell | pair-1 (PRX) family | CAQH-style family (pair 4) |
| --- | --- | --- |
| LOB (ADLS, STGDELTA) | blank | the LOB codes |
| STGDELTA TGT_PRIMARY_KEY, no Primary Key cell | 'NA' | blank (open) |
| STGDELTA OBJECT_NAME | the family's own form (transcribed) | the generalized file pattern |
| ADLS SCHEMA_DRIFT_FLAG (2026-10-09) | 'N' | 'Y' (the SD row and the CAQH IIG) |

``metadata.templates.iig_v2.family_conventions`` carries the four settings; each
fixture's overlay pins its own family, so both goldens pass the full-cell checks
unedited. Switching the family switches exactly these cells.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegen.config import FamilyConventionsConfig
from codegen.metadata_sheet import metadata_sheet_payload
from multi_table_golden import REPO

PAIR1_FAMILY = FamilyConventionsConfig(lob="blank", stgdelta_unknown_primary_key="NA",
                                       stgdelta_object_name="literal",
                                       stgdelta_object_name_literal="X_FORM",
                                       schema_drift_flag="N",
                                       # both goldens write N / NA / NA without a recycle
                                       recycle_unstated="N",
                                       citation="test: the pair-1 family")


def _payload_with(config, spec, family):
    from acfc_shapes import FIXTURE_ROOT, pair4_nb

    template = config.metadata.templates["iig_v2"].model_copy(
        update={"family_conventions": family})
    metadata = config.metadata.model_copy(update={
        "templates": {**config.metadata.templates, "iig_v2": template}})
    return metadata_sheet_payload(config.model_copy(update={"metadata": metadata}), REPO,
                                  specs=[spec], frd_path=FIXTURE_ROOT / pair4_nb.FRD_PATH,
                                  template="iig_v2", conventions_profile="acfc_prx")


def _cells(payload, sheet, column):
    return [r["values"][column] for r in payload["tabs"][sheet]["rows"]]


def test_each_fixture_overlay_pins_its_own_family(pair1_config, pair4_config):
    one = pair1_config.metadata.templates["iig_v2"].family_conventions
    four = pair4_config.metadata.templates["iig_v2"].family_conventions
    assert (one.lob, one.stgdelta_unknown_primary_key, one.stgdelta_object_name,
            one.schema_drift_flag) == ("blank", "NA", "literal", "N")
    assert (four.lob, four.stgdelta_unknown_primary_key, four.stgdelta_object_name,
            four.schema_drift_flag) == ("codes", "", "generalized_file_pattern", "Y")


def test_switching_the_family_switches_exactly_the_four_cells(pair4_config, pair4_spec,
                                                              pair4_payload):
    switched = _payload_with(pair4_config, pair4_spec, PAIR1_FAMILY)
    adls, stg = "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET"
    assert set(_cells(switched, adls, "LOB")) == {""}
    assert set(_cells(switched, stg, "LOB")) == {""}
    assert _cells(switched, stg, "OBJECT_NAME") == ["X_FORM"] * 3
    assert _cells(pair4_payload, adls, "SCHEMA_DRIFT_FLAG") == ["Y"] * 6
    assert _cells(switched, adls, "SCHEMA_DRIFT_FLAG") == ["N"] * 6
    # HDR / TRL state no Primary Key cell -> 'NA'; DTL keeps its keys.
    keys = _cells(switched, stg, "TGT_PRIMARY_KEY")
    assert keys[0] == keys[2] == "NA" and keys[1] == "MEMBER_ID,OTHER_CARRIER_ID,COB_EFF_DATE"
    # A blank LOB by convention is decided, not an open review cell.
    entry = switched["tabs"][adls]["rows"][0]["badges"]["LOB"]
    assert entry.get("deliberate_blank") is True
    # Nothing else moved.
    for sheet, tab in pair4_payload["tabs"].items():
        for before, after in zip(tab["rows"], switched["tabs"][sheet]["rows"], strict=True):
            moved = {c for c in tab["headers"] if before["values"][c] != after["values"][c]}
            allowed = ({"LOB", "SCHEMA_DRIFT_FLAG"} if sheet == adls
                       else {"LOB", "OBJECT_NAME", "TGT_PRIMARY_KEY"} if sheet == stg else set())
            assert moved <= allowed, (sheet, moved)


def test_table_name_object_name_is_available(pair4_config, pair4_spec):
    family = FamilyConventionsConfig(lob="codes", stgdelta_unknown_primary_key="",
                                     stgdelta_object_name="table_name")
    switched = _payload_with(pair4_config, pair4_spec, family)
    assert _cells(switched, "STGDELTA_STDDELTA_INGESTION_DET", "OBJECT_NAME") == [
        "nb_cob_report_hdr", "nb_cob_report_dtl", "nb_cob_report_trl"]


def test_a_literal_object_name_needs_its_value():
    with pytest.raises(ValidationError, match="needs stgdelta_object_name_literal"):
        FamilyConventionsConfig(stgdelta_object_name="literal")
