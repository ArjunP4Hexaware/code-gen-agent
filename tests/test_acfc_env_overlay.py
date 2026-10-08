"""IIG-first (2026-10-07): the committed ACFC environment overlay
(config/overlays/acfc_env.yaml).

* It supplies the stage / standard catalogs, so a pair whose FRD and STTM
  state none no longer FAILs ``qualified_names`` under ``acfc_prx`` — the DDL
  is written with three-part names.
* Its six ADLS_DELTA_INGESTION_DETAILS constants fill their cells (badge
  synthetic, tooltip naming the overlay) and leave the always-blank list.
* load_config ALWAYS applies it first (every entry point);
  CODEGEN_CONFIG_OVERLAYS adds overlays on top (later wins);
  CODEGEN_SKIP_ENV_OVERLAY=1 opts out. The App's startup line and
  GET /api/health list the overlays in effect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli
from codegen.config import DEFAULT_OVERLAY, load_config, overlay_paths
from test_derivations import FRD, REPO, _pair11_specs, _scoped

OVERLAY = REPO / "config" / DEFAULT_OVERLAY
CV_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
CV_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
OVERLAY_CELLS = {"SRC_ADLS_CONNECTION_ID": "7", "METADATA_CONNECTION_ID": "4",
                 "TGT_CONNECTION_ID": "2", "SRC_CONTAINER_NAME": "mftlanding",
                 "TGT_CONTAINER_NAME": "z-use-d1-dlk-stage-01"}


def _generate(spec, config, tmp: Path):
    return cli._generate_feed(spec, _scoped(config, tmp), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")


def _adls_rows(tmp: Path, slug: str) -> list[tuple[dict, dict]]:
    from openpyxl import load_workbook

    workbook = load_workbook(tmp / "out" / slug / "framework" / "config_rows.xlsx")
    sheet = workbook["ADLS_DELTA_INGESTION_DETAILS"]
    headers = [c.value for c in sheet[1]]
    tooltips: dict[int, dict] = {}
    for tab, row, header, badge, tooltip in workbook["_provenance"].iter_rows(
            min_row=2, values_only=True):
        if tab == "ADLS_DELTA_INGESTION_DETAILS":
            tooltips.setdefault(row, {})[header] = (badge, tooltip)
    return [(dict(zip(headers, values, strict=False)), tooltips[index])
            for index, values in enumerate(sheet.iter_rows(min_row=2, values_only=True),
                                           start=2)]


def test_overlay_clears_the_catalog_fail_and_fills_the_environment_cells(tmp_path):
    plain = load_config(REPO / "config" / "config.yaml")
    with_overlay = load_config(REPO / "config" / "config.yaml", overlays=[OVERLAY])
    assert with_overlay.conventions.profiles["acfc_prx"].default_catalog == {
        "stage": "d1_dlk", "standard": "d1_std"}
    (tmp_path / "contracts").mkdir()
    specs, _flags = _pair11_specs(FRD, tmp_path / "contracts", plain)
    assert _generate(specs[0], plain, tmp_path / "plain").verdict == "FAIL"

    gate = _generate(specs[0], with_overlay, tmp_path / "acfc")
    assert gate.verdict != "FAIL"
    assert not [f for f in gate.flags if f.startswith("catalog_unstated")]
    (ddl,) = (tmp_path / "acfc" / "out" / specs[0].feed_slug / "framework").glob("*_DDL.txt")
    creates = [line for line in ddl.read_text(encoding="utf-8").splitlines()
               if line.startswith("CREATE")]
    assert creates and all(line.split()[4].count(".") == 2 for line in creates)
    assert any(" d1_dlk." in line for line in creates)
    assert any(" d1_std." in line for line in creates)
    for values, tooltips in _adls_rows(tmp_path / "acfc", specs[0].feed_slug):
        for header, expected in OVERLAY_CELLS.items():
            assert values[header] == expected
            badge, tooltip = tooltips[header]
            assert badge == "SYNTHETIC"
            assert "config/overlays/acfc_env.yaml" in tooltip
        # SCHEMA_DRIFT_FLAG is a feed-family setting since 2026-10-09: the
        # overlay pins the SD / CAQH-style family's Y, not a constant.
        assert values["SCHEMA_DRIFT_FLAG"] == "Y"
        badge, tooltip = tooltips["SCHEMA_DRIFT_FLAG"]
        assert badge == "SYNTHETIC"
        assert "family convention schema_drift_flag: Y — ACFC environment overlay" in tooltip


@pytest.mark.skipif(not (CV_FRD.is_file() and CV_STTM.is_file()),
                    reason="CV golden pair not restored (removed 2026-08-22)")
def test_cv_golden_pair_passes_with_the_overlay(tmp_path):
    from codegen.resolve.resolver import resolve_pair

    config = load_config(REPO / "config" / "config.yaml", overlays=[OVERLAY])
    (spec,) = [s for s in resolve_pair(CV_FRD, CV_STTM, config)
               if s.feed_id == "cv_community_demographic_risk"]
    gate = _generate(spec, config, tmp_path)
    assert gate.verdict == "PASS_WITH_FLAGS"
    assert not [f for f in gate.flags if f.startswith("catalog_unstated")]
    framework = tmp_path / "out" / spec.feed_slug / "framework"
    ddl = (framework / "CV_COMMUNITY_DEMOGRAPHIC_RISK_DDL.txt").read_text(encoding="utf-8")
    assert "CREATE OR REPLACE TABLE d1_dlk.stg_sdh.cv_community_demographic_risk" in ddl
    assert "CREATE OR REPLACE TABLE d1_std.sdh.cv_community_demographic_risk" in ddl


def _catalogs(config) -> dict:
    return config.conventions.profiles["acfc_prx"].default_catalog


def _default_on(monkeypatch) -> None:
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.delenv("CODEGEN_CONFIG_OVERLAYS", raising=False)


def test_default_overlay_is_always_applied(monkeypatch, capsys):
    _default_on(monkeypatch)
    config = load_config(REPO / "config" / "config.yaml")
    assert _catalogs(config) == {"stage": "d1_dlk", "standard": "d1_std"}
    constants = config.metadata.templates["iig_v2"].constants["ADLS_DELTA_INGESTION_DETAILS"]
    assert constants["TGT_CONNECTION_ID"] == "2"
    assert "SRC_CONTAINER_NAME" not in config.metadata.templates["iig_v2"].always_blank
    assert overlay_paths(REPO / "config" / "config.yaml") == [OVERLAY]


def test_an_env_overlay_goes_on_top_of_the_default(monkeypatch, tmp_path, capsys):
    _default_on(monkeypatch)
    other = tmp_path / "other.yaml"
    other.write_text("conventions: {profiles: {acfc_prx: {default_catalog: {stage: x_stg}}}}\n",
                     encoding="utf-8")
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", f"{OVERLAY};{other}")  # listed twice: once
    assert overlay_paths(REPO / "config" / "config.yaml") == [OVERLAY, other]
    config = load_config(REPO / "config" / "config.yaml")
    assert _catalogs(config) == {"stage": "x_stg", "standard": "d1_std"}  # later wins
    assert "SRC_CONTAINER_NAME" not in config.metadata.templates["iig_v2"].always_blank
    assert f"config overlays (in order): {OVERLAY} -> {other}" in capsys.readouterr().err


def test_skip_env_overlay_opts_out(monkeypatch, tmp_path):
    _default_on(monkeypatch)
    monkeypatch.setenv("CODEGEN_SKIP_ENV_OVERLAY", "1")
    assert overlay_paths(REPO / "config" / "config.yaml") == []
    config = load_config(REPO / "config" / "config.yaml")
    assert _catalogs(config) == {}
    assert "SRC_CONTAINER_NAME" in config.metadata.templates["iig_v2"].always_blank
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", "")            # "" no longer opts out
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY")
    assert _catalogs(load_config(REPO / "config" / "config.yaml"))["stage"] == "d1_dlk"


def test_no_default_without_the_file_next_to_the_config(monkeypatch, tmp_path):
    _default_on(monkeypatch)
    copy = tmp_path / "config.yaml"
    copy.write_text((REPO / "config" / "config.yaml").read_text(encoding="utf-8"),
                    encoding="utf-8")
    assert _catalogs(load_config(copy)) == {}


def test_app_health_and_startup_line_list_the_overlays(monkeypatch):
    pytest.importorskip("fastapi")
    from ui.backend import main as ui_main

    _default_on(monkeypatch)
    expected = [str(Path("config") / "overlays" / "acfc_env.yaml")]
    monkeypatch.chdir(REPO)
    assert ui_main._config_overlays() == expected
    body = ui_main.health()
    assert body["config_overlays"] == expected
    assert set(body) == {"status", "version", "codegen_source", "codegen_file",
                         "config_overlays", "startup_error", "principal", "roots"}
    monkeypatch.setenv("CODEGEN_SKIP_ENV_OVERLAY", "1")
    assert ui_main.health()["config_overlays"] == []


PATH_CELLS = ("SRC_ADLS_PATH", "SRC_ADLS_ARCHVL_PATH", "TGT_ADLS_PATH", "TGT_RJT_ADLS_PATH")


def test_overlay_path_shapes_cite_the_overlay_in_the_tooltip_and_review_copy(tmp_path):
    from openpyxl import load_workbook

    config = load_config(REPO / "config" / "config.yaml", overlays=[OVERLAY])
    (tmp_path / "contracts").mkdir()
    specs, _flags = _pair11_specs(FRD, tmp_path / "contracts", config)
    _generate(specs[0], config, tmp_path / "acfc")
    for _values, tooltips in _adls_rows(tmp_path / "acfc", specs[0].feed_slug):
        for header in PATH_CELLS:
            badge, tooltip = tooltips[header]
            assert badge == "SYNTHETIC"
            assert tooltip.startswith("synthetic path shape '")
            assert "config/overlays/acfc_env.yaml" in tooltip
            assert "from the template" not in tooltip
    framework = tmp_path / "acfc" / "out" / specs[0].feed_slug / "framework"
    (review,) = framework.glob("*_IIG_REVIEW.xlsx")
    summary = {(row[0], row[1]): row for row in load_workbook(review)["REVIEW_SUMMARY"]
               .iter_rows(min_row=2, values_only=True)}
    for header in PATH_CELLS:
        sheet, column, reason, _owner, _cells, _ref, citation = \
            summary[("ADLS_DELTA_INGESTION_DETAILS", header)]
        assert "path" in reason.lower()
        assert "config/overlays/acfc_env.yaml" in citation


def test_template_path_shapes_still_cite_the_template(tmp_path):
    config = load_config(REPO / "config" / "config.yaml")
    (tmp_path / "contracts").mkdir()
    specs, _flags = _pair11_specs(FRD, tmp_path / "contracts", config)
    _generate(specs[0], config, tmp_path / "plain")
    for _values, tooltips in _adls_rows(tmp_path / "plain", specs[0].feed_slug):
        assert tooltips["TGT_ADLS_PATH"][1].startswith("synthetic path shape from the template")
