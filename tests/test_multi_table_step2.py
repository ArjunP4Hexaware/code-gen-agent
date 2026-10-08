"""Multi-table Phase C step 2 — ``conventions.catalog_map`` (rule 7).

The STTM bands state LOGICAL catalogs (pair 4: PR_DLK / PR_STD); the
environment overlay maps them (d1: PR_DLK -> d1_dlk, PR_STD -> d1_std;
prod: identity). The resolver maps every catalog it puts on a ResolvedTable
and keeps the stated one (``catalog_logical``), so the qualified names, the
DDL and every IIG catalog cell carry the mapped catalog and the cell tooltip
cites the mapping. ``default_catalog`` stays the fallback for a blank band.
"""

from __future__ import annotations

import pytest

from acfc_shapes import FIXTURE_ROOT, pair4_nb
from codegen.config import load_config
from codegen.resolve.resolver import map_catalog
from codegen.resolve.resolver import resolve_pair as resolve_contracts
from conftest import REPO

PAIR4_OVERLAY = FIXTURE_ROOT / "pair_4" / "config_overlay.yaml"
ACFC_ENV = REPO / "config" / "overlays" / "acfc_env.yaml"


@pytest.fixture(scope="module")
def pair4_config():
    return load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY])


@pytest.fixture(scope="module")
def pair4_sttm(pair4_config):
    from codegen.extract import extract_contract

    return extract_contract(FIXTURE_ROOT / pair4_nb.STTM_PATH, FIXTURE_ROOT / pair4_nb.FRD_PATH,
                            pair4_config, generated_date="2026-10-07")


def _resolve(config, sttm, tmp_path):
    from codegen.extract import contract_to_json

    path = tmp_path / "sttm.contract.json"
    path.write_text(contract_to_json(sttm), encoding="utf-8")
    (spec,) = resolve_contracts(FIXTURE_ROOT / pair4_nb.FRD_PATH, path, config)
    return spec


@pytest.fixture(scope="module")
def pair4_spec(pair4_config, pair4_sttm, tmp_path_factory):
    return _resolve(pair4_config, pair4_sttm, tmp_path_factory.mktemp("pair4_step2"))


def _payload(config, spec):
    from codegen.metadata_sheet import metadata_sheet_payload

    return metadata_sheet_payload(config, REPO, specs=[spec],
                                  frd_path=FIXTURE_ROOT / pair4_nb.FRD_PATH, template="iig_v2",
                                  conventions_profile="acfc_prx")


# ------------------------------------------------------------------ map_catalog


def test_an_empty_map_is_identity(config):
    flags: list[str] = []
    assert config.conventions.catalog_map == {}
    assert map_catalog("PR_DLK", "stage", config, flags) == ("PR_DLK", None)
    assert flags == []


def test_the_map_is_case_insensitive_and_keeps_the_logical_catalog(pair4_config):
    flags: list[str] = []
    assert map_catalog("PR_DLK", "stage", pair4_config, flags) == ("d1_dlk", "PR_DLK")
    assert map_catalog("pr_std", "standard", pair4_config, flags) == ("d1_std", "pr_std")
    assert map_catalog(None, "stage", pair4_config, flags) == (None, None)
    assert flags == []


def test_an_unmapped_catalog_is_written_as_stated_and_flagged_once(pair4_config):
    flags: list[str] = []
    for _ in range(2):
        assert map_catalog("PR_OTHER", "stage", pair4_config, flags) == ("PR_OTHER", None)
    assert len(flags) == 1 and flags[0].startswith("catalog_unmapped:stage — 'PR_OTHER'")


def test_the_d1_environment_overlay_maps_pr_catalogs():
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_ENV])
    assert config.conventions.catalog_map == {"PR_DLK": "d1_dlk", "PR_STD": "d1_std"}


# ------------------------------------------------------------------ pair 4


def test_every_resolved_table_carries_the_mapped_catalog(pair4_spec):
    for segment in pair4_spec.segments:
        stage, standard = segment.stage_table, segment.standard_table
        assert (stage.catalog, stage.catalog_logical) == ("d1_dlk", pair4_nb.STAGE_CATALOG)
        assert standard is not None
        assert (standard.catalog, standard.catalog_logical) == ("d1_std",
                                                                pair4_nb.STANDARD_CATALOG)
        assert standard.schema_name == pair4_nb.STANDARD_SCHEMA
    for table in (pair4_spec.standard_table, pair4_spec.errors_table,
                  pair4_spec.processed_files_table):
        assert table.catalog in ("d1_dlk", "d1_std") and table.catalog_logical
    assert not [f for f in pair4_spec.provenance_flags if f.startswith("catalog_unmapped")]


def test_qualified_names_match_the_golden_table_definitions(pair4_spec):
    import yaml

    golden = yaml.safe_load((FIXTURE_ROOT / "pair_4" / "golden" / "IIG_EXPECTED.yaml")
                            .read_text(encoding="utf-8"))
    by_layer = {"stage": {}, "standard": {}}
    for segment in pair4_spec.segments:
        by_layer["stage"][segment.segment] = segment.stage_table
        by_layer["standard"][segment.segment] = segment.standard_table
    for entry in golden["TABLE_DEFINITIONS"]:
        table = by_layer[entry["layer"]][entry["segment"]]
        assert table.qualified_name == entry["mapped"]
        assert ".".join([table.catalog_logical, table.schema_name, table.table]) == \
            entry["logical"]


def test_iig_catalog_cells_carry_the_mapped_catalog_and_cite_the_map(pair4_config, pair4_spec):
    payload = _payload(pair4_config, pair4_spec)
    rows = payload["tabs"]["STGDELTA_STDDELTA_INGESTION_DET"]["rows"]   # one per table
    assert len(rows) == len(pair4_nb.TABLES)
    for row in rows:
        assert row["values"]["SRC_CATALOG_NAME"] == "d1_dlk"
        assert row["values"]["TGT_CATALOG_NAME"] == "d1_std"
        assert "catalog_map PR_DLK → d1_dlk" in row["badges"]["SRC_CATALOG_NAME"]["tooltip"]
        assert "catalog_map PR_STD → d1_std" in row["badges"]["TGT_CATALOG_NAME"]["tooltip"]
    cells = [str(r["values"].get(h, "")) for tab in payload["tabs"].values()
             for r in tab["rows"] for h in tab["headers"]]
    assert not [c for c in cells if "PR_DLK" in c or "PR_STD" in c or "syn_fallback" in c]


def test_the_ddl_names_every_table_by_its_mapped_three_part_name(pair4_config, pair4_spec):
    from codegen.emit.framework import _combined_ddl_text

    flags: list[str] = []
    text = _combined_ddl_text(pair4_spec, pair4_config.conventions.get("acfc_prx"), flags,
                              pair4_config)
    assert "d1_dlk.stg_nb_cob.nb_cob_report_dtl" in text
    assert "d1_std.nb_cob.nb_cob_report_dtl" in text
    assert "PR_DLK" not in text and "PR_STD" not in text and "syn_fallback" not in text
    assert not [f for f in flags if f.startswith(("catalog_from_config", "catalog_unstated"))]


def test_a_blank_band_catalog_falls_back_to_default_catalog_unmapped(pair4_config, pair4_sttm,
                                                                     tmp_path):
    from codegen.emit.framework import _combined_ddl_text

    (feed,) = pair4_sttm.feeds
    blank = feed.model_copy(update={
        "stage": feed.stage.model_copy(update={"catalog": None}),
        "standard": feed.standard.model_copy(update={"catalog": None})})
    spec = _resolve(pair4_config, pair4_sttm.model_copy(update={"feeds": [blank]}), tmp_path)
    assert {s.stage_table.catalog for s in spec.segments} == {None}
    flags: list[str] = []
    text = _combined_ddl_text(spec, pair4_config.conventions.get("acfc_prx"), flags,
                              pair4_config)
    assert "syn_fallback_dlk.stg_nb_cob.nb_cob_report_dtl" in text
    assert "syn_fallback_std.nb_cob.nb_cob_report_dtl" in text
    assert [f for f in flags if f.startswith("catalog_from_config")]


def test_a_map_without_the_stated_catalog_flags_it_on_the_spec(pair4_config, pair4_sttm,
                                                               tmp_path):
    other = pair4_config.model_copy(update={"conventions": pair4_config.conventions.model_copy(
        update={"catalog_map": {"PR_ELSEWHERE": "x"}})})
    spec = _resolve(other, pair4_sttm, tmp_path)
    assert {s.stage_table.catalog for s in spec.segments} == {pair4_nb.STAGE_CATALOG}
    unmapped = sorted(f.split(" — ")[0] for f in spec.provenance_flags
                      if f.startswith("catalog_unmapped"))
    assert unmapped == ["catalog_unmapped:stage", "catalog_unmapped:standard"]


# ------------------------------------------------------------------ pair 1


def test_pair1_identity_map_is_applied_and_changes_no_name(pair1_spec):
    (segment, *_rest) = pair1_spec.segments
    stage = segment.stage_table
    assert stage.catalog == stage.catalog_logical == "pr_dlk_vnd_p"
    assert pair1_spec.standard_table.catalog == "pr_std_vnd_p"
    assert pair1_spec.standard_table.catalog_logical == "pr_std_vnd_p"
    assert not [f for f in pair1_spec.provenance_flags if f.startswith("catalog_unmapped")]


# ------------------------------------------------------------------ precedence (decision b, c)


def _frd_with_catalogs(tmp_path, stage, standard):
    import json

    data = json.loads((FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8"))
    data["feeds"][0]["stage_target"]["catalog"] = stage
    data["feeds"][0]["standard_target"]["catalog"] = standard
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _resolve_with(config, sttm, frd_path, tmp_path):
    from codegen.extract import contract_to_json

    path = tmp_path / "sttm.contract.json"
    path.write_text(contract_to_json(sttm), encoding="utf-8")
    (spec,) = resolve_contracts(frd_path, path, config)
    return spec


def test_the_band_wins_over_a_disagreeing_frd_label_and_says_so(pair4_config, pair4_sttm,
                                                                tmp_path):
    frd = _frd_with_catalogs(tmp_path, "PR_FRD_STG", "pr_std")      # standard agrees (case)
    spec = _resolve_with(pair4_config, pair4_sttm, frd, tmp_path)
    assert {s.stage_table.catalog for s in spec.segments} == {"d1_dlk"}
    conflicts = [f for f in spec.provenance_flags if f.startswith("catalog_conflict")]
    assert conflicts == ["catalog_conflict:stage — STTM band 'PR_DLK' vs FRD label "
                         "'PR_FRD_STG'; the band is used (docs/acfc/MULTI_TABLE_DESIGN.md "
                         "rule 6)"]


def test_the_frd_label_fills_a_blank_band_before_default_catalog(pair4_config, pair4_sttm,
                                                                 tmp_path):
    (feed,) = pair4_sttm.feeds
    blank = feed.model_copy(update={
        "stage": feed.stage.model_copy(update={"catalog": None}),
        "standard": feed.standard.model_copy(update={"catalog": None})})
    frd = _frd_with_catalogs(tmp_path, "PR_DLK", "PR_STD")
    spec = _resolve_with(pair4_config, pair4_sttm.model_copy(update={"feeds": [blank]}), frd,
                         tmp_path)
    assert {s.stage_table.catalog for s in spec.segments} == {"d1_dlk"}
    assert {s.standard_table.catalog for s in spec.segments} == {"d1_std"}
    assert not [f for f in spec.provenance_flags if f.startswith("catalog_conflict")]


def test_the_map_emits_lowercase(pair4_config):
    upper = pair4_config.model_copy(update={"conventions": pair4_config.conventions.model_copy(
        update={"catalog_map": {"pr_dlk": "D1_DLK"}})})
    assert map_catalog("PR_DLK", "stage", upper, []) == ("d1_dlk", "PR_DLK")
