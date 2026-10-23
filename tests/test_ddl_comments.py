"""post104 (Nikshit's review, 2026-10-23): the acfc_prx combined DDL carries a
per-column COMMENT (the STTM field description), a primary-key note, a table
COMMENT naming the layer's FRD Load Strategy and the standard tables'
TBLPROPERTIES — four ``conventions.profiles.acfc_prx`` knobs, on in
config/config.yaml. The pair-1 fixture overlay switches them off, so the client
golden stays byte-identical (tests/test_m4_acceptance.py).

* pair 11 (``MAPPING-VC_DISENROLLMENT``): every business column has a source
  Description; the audit columns have none and are flagged;
* pair 4 (NB_COB): no descriptions, three Primary Key cells (Detail table);
* pair 1 with the knobs ON is the golden plus the additions only.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.contracts.sttm import SttmField
from codegen.emit.framework import _column_comment, _combined_ddl_text
from test_derivations import FRD_CATALOG, REPO, _pair11_specs
from test_m4_acceptance import GOLDEN_DDL, needs_golden

PROFILE_KNOBS = ("column_comments", "primary_key_note", "load_strategy_comment",
                 "standard_tblproperties")


@pytest.fixture(scope="module")
def shipped():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture(scope="module")
def pair11(shipped):
    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    (spec,) = [s for s in specs if s.feed_slug == "vc_disenrollment"]
    flags: list[str] = []
    ddl = _combined_ddl_text(spec, shipped.conventions.get("acfc_prx"), flags, shipped)
    return spec, ddl, flags


def _block(ddl: str, banner: str) -> str:
    start = ddl.index(banner)
    end = ddl.find("\n--", start + len(banner))
    return ddl[start:end if end != -1 else None]


def _strip_additions(ddl: str) -> str:
    ddl = re.sub(r" COMMENT '(?:[^']|'')*'", "", ddl)
    ddl = re.sub(r"\nCOMMENT '(?:[^']|'')*'", "", ddl)
    return re.sub(r"\nTBLPROPERTIES \((?:\n  '[^']*' = '[^']*'[,)])+", "", ddl)


def test_the_shipped_profile_switches_all_four_on(shipped):
    profile = shipped.conventions.get("acfc_prx")
    assert profile.column_comments is True
    assert profile.primary_key_note and profile.load_strategy_comment
    assert profile.standard_tblproperties
    assert shipped.conventions.get("edo_sfmc").column_comments is False   # other profile untouched


def test_column_comments_are_the_sttm_descriptions(pair11):
    spec, ddl, _flags = pair11
    by_column = {f.stage_column: f.ddl_description for s in spec.segments for f in s.fields}
    for layer in ("--stage table", "--standard table"):
        block = _block(ddl, layer)
        for column, description in by_column.items():
            assert description
            assert re.search(rf"^{column} \S+ COMMENT '{re.escape(description)}',$", block, re.M)


def test_the_table_comment_names_each_layers_frd_load_strategy(pair11):
    spec, ddl, _flags = pair11
    stage, standard = _block(ddl, "--stage table"), _block(ddl, "--standard table")
    assert (f"USING delta\nCOMMENT 'Load strategy: {spec.stage_load_strategy} "
            "(FRD Load Strategy STG)'") in stage
    assert (f"USING delta\nCOMMENT 'Load strategy: {spec.standard_load_strategy} "
            "(FRD Load Strategy STD)'") in standard


def test_tblproperties_only_on_the_standard_table_in_config_order(pair11, shipped):
    _spec, ddl, _flags = pair11
    assert "TBLPROPERTIES" not in _block(ddl, "--stage table")
    standard = _block(ddl, "--standard table")
    props = shipped.conventions.get("acfc_prx").standard_tblproperties
    lines = [f"  '{k}' = '{v}'" for k, v in props.items()]
    expected = "TBLPROPERTIES (\n" + ",\n".join(lines) + ")"
    assert standard.endswith(expected)
    assert list(props)[0] == "delta.autoOptimize.autoCompact"
    assert props["delta.parquet.compression.codec"] == "zstd"


def test_audit_columns_without_a_description_are_flagged_per_table(pair11):
    _spec, ddl, flags = pair11
    assert "\nSRC_FILE_NAME STRING,\n" in ddl                         # no COMMENT written
    blank = [f for f in flags if f.startswith("ddl_comment_blank:")]
    assert [f.split(" — ")[0] for f in blank] == [
        "ddl_comment_blank:stage:cat_syn.stg_dom_a.vc_disenrollment",
        "ddl_comment_blank:standard:cat_syn.dom_a.vc_disenrollment"]
    assert all("SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME" in f for f in blank)


def test_primary_key_cells_are_noted_and_missing_descriptions_flagged(pair4_config,
                                                                      pair4_spec):
    profile = pair4_config.conventions.get("acfc_prx")
    flags: list[str] = []
    ddl = _combined_ddl_text(pair4_spec, profile, flags, pair4_config)
    keyed = [f.stage_column for s in pair4_spec.segments for f in s.fields if f.primary_key]
    assert keyed == ["MEMBER_ID", "OTHER_CARRIER_ID", "COB_EFF_DATE"]
    dtl = _block(ddl, "CREATE OR REPLACE TABLE d1_dlk.stg_nb_cob.nb_cob_report_dtl")
    for column in keyed:
        assert f"\n{column} String COMMENT 'Primary key (STTM Primary Key)',\n" in dtl
    assert "\nSUBSCRIBER_ID String,\n" in dtl                         # no description, no key
    blank = [f for f in flags if f.startswith("ddl_comment_blank:stage:d1_dlk.stg_nb_cob."
                                             "nb_cob_report_dtl")]
    assert len(blank) == 1 and "MEMBER_ID" in blank[0] and "Field Description" in blank[0]


@needs_golden
def test_pair1_with_the_knobs_on_is_the_golden_plus_the_additions(pair1_config, pair1_spec,
                                                                  shipped):
    on = shipped.conventions.get("acfc_prx")
    profile = pair1_config.conventions.get("acfc_prx").model_copy(
        update={k: getattr(on, k) for k in PROFILE_KNOBS})
    ddl = _combined_ddl_text(pair1_spec, profile, [], pair1_config)
    assert ddl != GOLDEN_DDL.read_text(encoding="utf-8")
    assert ddl.count(" COMMENT '") == 2 * 21                         # 21 columns, both layers
    assert _strip_additions(ddl).encode("utf-8") == GOLDEN_DDL.read_bytes()


def _field(**update) -> SttmField:
    base = dict(source_column="X", description=None, sample_value=None, source_datatype="String",
                nullable=True, phi=False, mandatory=False, stage_column="X",
                stage_datatype="String", standard_column="X", standard_datatype="String")
    return SttmField(**{**base, **update})


def test_the_ddl_description_prefers_field_description_and_never_reads_comments():
    assert _field(description="Source text").ddl_description == "Source text"
    assert _field(description="Source text",
                  field_description="Target text").ddl_description == "Target text"
    assert _field(description="Rule: trim", description_from_comments=True
                  ).ddl_description is None
    assert _field(description="Rule: trim", description_from_comments=True,
                  field_description="Target text").ddl_description == "Target text"


def test_the_primary_key_note_follows_each_layers_cell(shipped):
    profile = shipped.conventions.get("acfc_prx")
    note = profile.primary_key_note
    both = _field(description="Member id", primary_key=True)
    assert _column_comment(both, "stage", profile) == f"Member id; {note}"
    assert _column_comment(both, "standard", profile) == f"Member id; {note}"
    stage_only = _field(primary_key=True, standard_primary_key=False)
    assert _column_comment(stage_only, "stage", profile) == note
    assert _column_comment(stage_only, "standard", profile) is None
    standard_only = _field(standard_primary_key=True)
    assert _column_comment(standard_only, "stage", profile) is None
    assert _column_comment(standard_only, "standard", profile) == note


def test_a_quote_in_a_description_is_escaped(pair11, shipped):
    spec, _ddl, _flags = pair11
    segment = spec.segments[0]
    fields = [segment.fields[0].model_copy(update={"description": "Member's id\n  (stated)"}),
              *segment.fields[1:]]
    quoted = spec.model_copy(update={"segments": [segment.model_copy(update={"fields": fields}),
                                                  *spec.segments[1:]]})
    ddl = _combined_ddl_text(quoted, shipped.conventions.get("acfc_prx"), [], shipped)
    assert "MEMBER_ID String COMMENT 'Member''s id (stated)'," in ddl


def test_the_comments_marker_is_written_only_when_it_says_something():
    from codegen.contracts.sttm import SttmField as F

    dumped = _field(description="Source text").model_dump(exclude_defaults=True)
    assert "field_description" not in dumped and "description_from_comments" not in dumped
    assert F.model_fields["description_from_comments"].default is False
