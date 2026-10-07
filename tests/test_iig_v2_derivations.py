"""IIG-first P1 (2026-10-07): iig_v2 derivation fixes, scored against the
real ACFC rows (the real values themselves are not in the repo).

a. STGDELTA SRC_ / TGT_CATALOG_NAME = the DDL's catalog chain.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from codegen import cli
from codegen.config import load_config
from test_derivations import FRD, FRD_CATALOG, REPO, _pair11_specs, _scoped

ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"


def _write_overlay(tmp: Path, text: str) -> Path:
    path = tmp / "overlay.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _run(frd: Path, config, tmp: Path, index: int = 0):
    (tmp / "contracts").mkdir(parents=True, exist_ok=True)
    specs, _ = _pair11_specs(frd, tmp / "contracts", config)
    spec = specs[index]
    gate = cli._generate_feed(spec, _scoped(config, tmp), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")
    return spec, gate, tmp / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"


def _rows(xlsx: Path, sheet: str) -> list[dict[str, tuple]]:
    """[{header: (value, badge, tooltip)}] for one sheet of config_rows.xlsx."""
    workbook = load_workbook(xlsx)
    ws = workbook[sheet]
    headers = [c.value for c in ws[1]]
    prov: dict[tuple[int, str], tuple] = {}
    for tab, row, header, badge, tooltip in workbook["_provenance"].iter_rows(
            min_row=2, values_only=True):
        if tab == sheet:
            prov[(row, header)] = (badge, tooltip)
    out = []
    for index, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        out.append({h: (v, *prov.get((index, h), (None, None)))
                    for h, v in zip(headers, values, strict=False)})
    return out


# -- a. catalogs ----------------------------------------------------------------- #


def test_stg_std_catalogs_follow_the_ddl_chain_default_catalog(tmp_path):
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    _spec, gate, xlsx = _run(FRD, config, tmp_path)            # FRD + STTM state no catalog
    assert gate.verdict != "FAIL"
    (row,) = _rows(xlsx, "STGDELTA_STDDELTA_INGESTION_DET")
    assert row["SRC_CATALOG_NAME"][:2] == ("d1_dlk", "SYNTHETIC")
    assert row["TGT_CATALOG_NAME"][:2] == ("d1_std", "SYNTHETIC")
    assert "config_default" in row["SRC_CATALOG_NAME"][2]
    assert "default_catalog[standard]" in row["TGT_CATALOG_NAME"][2]


def test_stg_std_catalogs_stated_by_the_frd_win(tmp_path):
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    spec, _gate, xlsx = _run(FRD_CATALOG, config, tmp_path)
    (row,) = _rows(xlsx, "STGDELTA_STDDELTA_INGESTION_DET")
    assert row["SRC_CATALOG_NAME"][0] == spec.detail_segment.stage_table.catalog != "d1_dlk"
    assert row["TGT_CATALOG_NAME"][0] == spec.standard_table.catalog
    assert row["SRC_CATALOG_NAME"][1] == "from FRD"


def test_unresolved_catalog_leaves_the_cell_to_a_constant(tmp_path):
    overlay = _write_overlay(tmp_path, (
        "metadata: {templates: {iig_v2: {constants: {STGDELTA_STDDELTA_INGESTION_DET: "
        "{SRC_CATALOG_NAME: const_stg}}}}}\n"))
    config = load_config(REPO / "config" / "config.yaml", overlays=[overlay])
    _spec, _gate, xlsx = _run(FRD, config, tmp_path)
    (row,) = _rows(xlsx, "STGDELTA_STDDELTA_INGESTION_DET")
    assert row["SRC_CATALOG_NAME"][0] == "const_stg"           # was always blank before
    assert row["TGT_CATALOG_NAME"][0] in (None, "")             # still open, never guessed
