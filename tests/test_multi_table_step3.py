"""Multi-table Phase C step 3 — ADLS_DELTA rows = files, STGDELTA rows = tables.

docs/acfc/MULTI_TABLE_DESIGN.md rules 2–4: one ADLS row per file the feed
receives (pair 4: six, one per LOB; pair 1: four patterns, no LOB), every row
into the detail table, OBJECT_ID = the file's position; one STGDELTA row per
table (pair 4: three; pair 1: one), the target side from the table's standard
definition with the mapped catalog. Pair 4 is compared cell for cell with the
hand-written golden.
"""

from __future__ import annotations

import pytest
import yaml

from acfc_shapes import FIXTURE_ROOT, pair4_nb
from codegen.config import load_config
from codegen.metadata_sheet import metadata_sheet_payload
from codegen.resolve.resolver import resolve_pair as resolve_contracts
from conftest import REPO

PAIR4_OVERLAY = FIXTURE_ROOT / "pair_4" / "config_overlay.yaml"
GOLDEN = FIXTURE_ROOT / "pair_4" / "golden" / "IIG_EXPECTED.yaml"


@pytest.fixture(scope="module")
def pair4_config():
    return load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY])


@pytest.fixture(scope="module")
def pair4_spec(pair4_config, tmp_path_factory):
    from codegen.extract import contract_to_json, extract_contract

    sttm = extract_contract(FIXTURE_ROOT / pair4_nb.STTM_PATH, FIXTURE_ROOT / pair4_nb.FRD_PATH,
                            pair4_config, generated_date="2026-10-07")
    path = tmp_path_factory.mktemp("pair4_step3") / "sttm.contract.json"
    path.write_text(contract_to_json(sttm), encoding="utf-8")
    (spec,) = resolve_contracts(FIXTURE_ROOT / pair4_nb.FRD_PATH, path, pair4_config)
    return spec


@pytest.fixture(scope="module")
def pair4_payload(pair4_config, pair4_spec):
    return metadata_sheet_payload(pair4_config, REPO, specs=[pair4_spec],
                                  frd_path=FIXTURE_ROOT / pair4_nb.FRD_PATH, template="iig_v2",
                                  conventions_profile="acfc_prx")


@pytest.fixture(scope="module")
def golden() -> dict:
    return yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pair1_payload(pair1_config, pair1_spec, tmp_path_factory):
    import json

    frd = tmp_path_factory.mktemp("pair1_step3") / "frd.contract.json"
    feed = {"feed_name": pair1_spec.feed_name, "source_system": pair1_spec.source_system,
            "file_name_patterns": pair1_spec.file_name_patterns,
            "file_format": pair1_spec.file_format, "delimiter": pair1_spec.delimiter,
            "record_segments": [], "frequency": pair1_spec.frequency, "load_windows_sla": [],
            "lobs": pair1_spec.lobs, "domain": pair1_spec.domain,
            "sub_domain": pair1_spec.sub_domain, "landing_location": pair1_spec.landing_location,
            "stage_target": {"catalog": None, "schema": None, "tables": [], "load_strategy": None},
            "standard_target": {"catalog": None, "schema": None, "tables": [],
                                "load_strategy": None},
            "validation_rules": [], "recycle_rule": None, "history_backfill": None,
            "archive_retention": None, "phi_pii_notes": None, "sttm_reference": None,
            "requirement_ids": []}
    frd.write_text(json.dumps({
        "contract_name": "pair-1 preview", "generated_from_frd": "x", "status": "PASS",
        "generated_date": "2026-01-01T00:00:00+00:00", "generator": "test",
        "project": {"project_id": None, "project_name": "x", "business_context_summary": None},
        "in_scope": [], "out_of_scope": [], "assumptions_constraints_dependencies": [],
        "feeds": [feed], "system_interfaces": [], "open_items": []}), encoding="utf-8")
    return metadata_sheet_payload(pair1_config, REPO, specs=[pair1_spec], frd_path=frd,
                                  template="iig_v2", conventions_profile="acfc_prx")


def _expanded(golden: dict, sheet: str) -> list[dict]:
    return [{k: v for k, v in row.items() if not k.startswith("_")}
            for row in golden[sheet]["rows"]]


def compare_to_golden(payload: dict, golden: dict, sheet: str) -> list[tuple]:
    """(row, column, expected, got) for every cell that differs; a golden
    null / "" means the cell must be blank."""
    ours = payload["tabs"][sheet]["rows"]
    expected = _expanded(golden, sheet)
    assert len(ours) == len(expected), (sheet, len(ours), len(expected))
    diffs = []
    for index, (row, want) in enumerate(zip(ours, expected, strict=True), start=1):
        for column, value in want.items():
            got = row["values"][column]
            got = "" if got is None else str(got)
            if got != (value or ""):
                diffs.append((index, column, value, got))
    return diffs


# ------------------------------------------------------------------ pair 4


def test_pair4_adls_rows_are_the_six_lob_files_and_match_the_golden(pair4_payload, golden):
    assert compare_to_golden(pair4_payload, golden, "ADLS_DELTA_INGESTION_DETAILS") == []


def test_pair4_stgdelta_rows_are_the_three_tables_and_match_the_golden(pair4_payload, golden):
    assert compare_to_golden(pair4_payload, golden, "STGDELTA_STDDELTA_INGESTION_DET") == []


def test_pair4_spec_carries_the_six_files(pair4_spec):
    assert [f.lob for f in pair4_spec.files] == pair4_nb.LOBS
    assert all("STTM header block" in f.provenance for f in pair4_spec.files)


def test_object_id_is_a_cited_convention_not_an_invented_id(pair4_payload):
    rows = pair4_payload["tabs"]["ADLS_DELTA_INGESTION_DETAILS"]["rows"]
    for index, row in enumerate(rows, start=1):
        entry = row["badges"]["OBJECT_ID"]
        assert row["values"]["OBJECT_ID"] == str(index)
        assert entry["badge"] == "synthetic" and "METADATA_DB_SEMANTICS.md §5" in entry["tooltip"]
    # GROUP_ID / PIPELINE_ID stay framework-assigned blanks.
    assert {r["values"]["GROUP_ID"] for r in rows} == {""}
    assert {r["values"]["PIPELINE_ID"] for r in rows} == {""}


# ------------------------------------------------------------------ pair 1


def test_pair1_four_files_without_lob_and_one_table(pair1_payload, pair1_spec):
    adls = pair1_payload["tabs"]["ADLS_DELTA_INGESTION_DETAILS"]["rows"]
    stg = pair1_payload["tabs"]["STGDELTA_STDDELTA_INGESTION_DET"]["rows"]
    assert len(adls) == 4 and len(stg) == 1
    assert [r["values"]["SRC_FILE_NAME"] for r in adls] == pair1_spec.file_name_patterns
    assert [r["values"]["OBJECT_ID"] for r in adls] == ["1", "2", "3", "4"]
    assert {r["values"]["LOB"] for r in adls} == {""}
    assert {r["values"]["TGT_PARTITION_COLUMN"] for r in adls} == {"NA"}
    assert {r["values"]["TGT_PARTITION_VALUE"] for r in adls} == {"NA"}
    assert {r["values"]["TGT_TABLE_NAME"] for r in adls} == {"vnd_p_accum_client"}
    (row,) = stg
    assert row["values"]["SRC_TABLE_NAME"] == row["values"]["TGT_TABLE_NAME"] == \
        "vnd_p_accum_client"
    assert row["values"]["LOB"] == ""
