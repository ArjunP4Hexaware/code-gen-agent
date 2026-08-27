"""codegen.metadata_sheet: row rules per tab, coverage arithmetic, xlsx.

Display-only ACFC metadata-sheet preview. Unit tests build their own FRD
contract in tmp (no fixture files needed); the tests that exercise the
STTM-derived cells resolve the demo fixture pair and skip when it is
absent, like the rest of the suite.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from codegen.contracts.frd import FrdContract
from codegen.metadata_sheet import (
    NO_RUN_STATE,
    build_workbook,
    metadata_sheet_payload,
    workbook_bytes,
    workbook_filename,
)
from codegen.resolve.resolver import resolve_pair
from codegen.rules.compiler import compile_rules

REPO = Path(__file__).resolve().parents[1]


def _frd_feed(**overrides) -> dict:
    values = {
        "feed_name": "cv_test_feed",
        "source_system": "Civic Vantage (CV)",
        "file_name_patterns": ["extract_YYYY_MM.csv", "extract_CCYY_MM.csv"],
        "file_format": "csv",
        "delimiter": None,
        "record_segments": [],
        "frequency": "Monthly",
        "load_windows_sla": [],
        "lobs": ["All"],
        "domain": "Care Management",
        "sub_domain": "Public",
        "landing_location": None,
        "stage_target": {
            "catalog": None, "schema": "stg_x", "tables": ["cv_test_feed"],
            "load_strategy": "Truncate and Load",
        },
        "standard_target": {
            "catalog": None, "schema": "x", "tables": ["cv_test_feed"],
            "load_strategy": "Append",
        },
        "validation_rules": [],
        "recycle_rule": None,
        "history_backfill": None,
        "archive_retention": None,
        "phi_pii_notes": None,
        "sttm_reference": None,
        "requirement_ids": [],
    }
    values.update(overrides)
    return values


def _base_dir_with_contract(tmp_path: Path, config, feeds: list[dict]) -> Path:
    contract = {
        "contract_name": "test",
        "generated_from_frd": "test.docx",
        "generated_date": "2026-01-01T00:00:00",
        "generator": "test",
        "status": "PASS",
        "project": {"project_id": None, "project_name": "t", "business_context_summary": None},
        "in_scope": [],
        "out_of_scope": [],
        "assumptions_constraints_dependencies": [],
        "feeds": feeds,
        "system_interfaces": [],
        "open_items": [],
    }
    FrdContract.model_validate(contract)  # fail here, not inside the payload
    target = tmp_path / config.contracts.dir / config.demo.frd
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(contract), encoding="utf-8")
    return tmp_path


def _payload(config, tmp_path, feeds=None, **kwargs) -> dict:
    base = _base_dir_with_contract(tmp_path, config, feeds or [_frd_feed()])
    return metadata_sheet_payload(config, base, **kwargs)


def _cells(row: dict) -> dict:
    return {h: (row["values"][h], row["badges"][h]["badge"]) for h in row["values"]}


# -- file_layout --------------------------------------------------------------- #


def test_file_layout_frd_sourced_and_synthesized(config, tmp_path):
    payload = _payload(config, tmp_path)
    (row,) = payload["tabs"]["file_layout"]["rows"]
    cells = _cells(row)
    assert cells["feed_name"] == ("cv_test_feed", "from_frd")
    assert cells["source_system"] == ("Civic Vantage (CV)", "from_frd")
    # Null landing_location → Part A's synthesis, flagged.
    assert cells["landing_path"] == (
        "mftlanding/inbound/care_management/public/civic_vantage_cv", "synthetic"
    )
    assert cells["file_pattern"] == ("extract_YYYY_MM.csv; extract_CCYY_MM.csv", "from_frd")
    assert cells["file_format"] == ("csv", "from_frd")
    assert cells["frequency"] == ("Monthly", "from_frd")
    # No column-header-row indicator exists in the FRD contract shape.
    assert cells["has_header"] == ("", "needs_template")
    # record_segments empty → no trailer, and the contract says so.
    assert cells["has_trailer"] == ("no", "from_frd")
    # Null delimiter, no run → cannot be known from documents yet.
    assert cells["delimiter"] == ("", "needs_template")


def test_file_layout_contract_landing_and_trailer(config, tmp_path):
    payload = _payload(
        config, tmp_path,
        feeds=[_frd_feed(
            landing_location="mftlanding\\inbound\\a\\b\\c",
            record_segments=["Header", "Detail", "Trailer"],
            delimiter="|",
        )],
    )
    cells = _cells(payload["tabs"]["file_layout"]["rows"][0])
    assert cells["landing_path"] == ("mftlanding/inbound/a/b/c", "from_frd")
    assert cells["has_trailer"] == ("yes", "from_frd")
    assert cells["delimiter"] == ("|", "from_frd")


def test_always_blank_headers_are_empty_and_flagged(config, tmp_path):
    payload = _payload(config, tmp_path)
    for tab in payload["tabs"].values():
        for row in tab["rows"]:
            for header in config.demo.metadata_sheet.always_blank:
                if header in row["values"]:
                    assert row["values"][header] == ""
                    assert row["badges"][header]["badge"] == "needs_template"
                    assert "ACFC framework" in row["badges"][header]["tooltip"]


# -- load_config --------------------------------------------------------------- #


def test_load_config_two_rows_strategy_synthetic(config, tmp_path):
    payload = _payload(config, tmp_path)
    rows = payload["tabs"]["load_config"]["rows"]
    assert [r["values"]["layer"] for r in rows] == ["stage", "standard"]
    stage, standard = rows
    assert _cells(stage)["target_schema"] == ("stg_x", "from_frd")
    assert _cells(standard)["target_table"] == ("cv_test_feed", "from_frd")
    # Always the config stand-in, always flagged — never the contract value.
    assert _cells(stage)["load_strategy"] == ("Truncate and Load", "synthetic")
    assert _cells(standard)["load_strategy"] == ("Upsert", "synthetic")
    # No run yet: key columns come from the mapping contract.
    assert _cells(standard)["dedup_keys"] == ("", "needs_template")


def test_load_config_stage_only_feed(config, tmp_path):
    payload = _payload(
        config, tmp_path,
        feeds=[_frd_feed(standard_target={
            "catalog": None, "schema": None, "tables": [], "load_strategy": "Append",
        })],
    )
    rows = payload["tabs"]["load_config"]["rows"]
    assert [r["values"]["layer"] for r in rows] == ["stage"]


# -- columns + no-run state ---------------------------------------------------- #


def test_columns_empty_with_state_before_a_run(config, tmp_path):
    payload = _payload(config, tmp_path)
    columns = payload["tabs"]["columns"]
    assert columns["rows"] == []
    assert columns["state"] == NO_RUN_STATE


# -- coverage arithmetic ------------------------------------------------------- #


def test_coverage_counts_add_up(config, tmp_path):
    payload = _payload(config, tmp_path)
    coverage = payload["coverage"]
    cells = sum(
        len(row["badges"]) for tab in payload["tabs"].values() for row in tab["rows"]
    )
    assert coverage["total"] == cells
    assert (
        coverage["derived"] + coverage["synthetic"] + coverage["needs_template"]
        == coverage["total"]
    )
    assert coverage["synthetic"] >= 2  # landing_path + the two load strategies


# -- with the demo fixture pair (STTM-derived cells) --------------------------- #

_DEMO_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_DEMO_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
needs_demo_pair = pytest.mark.skipif(
    not (_DEMO_FRD.is_file() and _DEMO_STTM.is_file()),
    reason="demo fixture pair not restored (removed 2026-08-22)",
)


@pytest.fixture(scope="module")
def demo_specs(config):
    if not (_DEMO_FRD.is_file() and _DEMO_STTM.is_file()):
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")
    return resolve_pair(_DEMO_FRD, _DEMO_STTM, config)


@needs_demo_pair
def test_columns_populate_from_mapping_contract(config, demo_specs):
    unmapped = {
        spec.feed_slug: {
            o.rule_text for o in compile_rules(spec) if o.classification == "unmapped"
        }
        for spec in demo_specs
    }
    payload = metadata_sheet_payload(
        config, REPO, specs=demo_specs, unmapped_by_slug=unmapped, run_label="test_run"
    )
    columns = payload["tabs"]["columns"]
    assert "state" not in columns
    expected_fields = sum(
        len(seg.fields) for spec in demo_specs for seg in spec.segments
    )
    assert len(columns["rows"]) == expected_fields
    first = columns["rows"][0]
    assert first["badges"]["column_name"]["badge"] == "from_sttm"
    assert first["values"]["ordinal"] == 1
    # Ordinals restart per feed.
    slugs = {row["feed_slug"] for row in columns["rows"]}
    assert len(slugs) == len(demo_specs)
    # dedup_keys fill on standard rows from the mapping contract's keys.
    standard_rows = [
        r for r in payload["tabs"]["load_config"]["rows"]
        if r["values"]["layer"] == "standard"
    ]
    assert standard_rows and all(
        r["badges"]["dedup_keys"]["badge"] == "from_sttm" and r["values"]["dedup_keys"]
        for r in standard_rows
    )
    # CV FRD states no delimiter; with a run it resolves from the STTM.
    for row in payload["tabs"]["file_layout"]["rows"]:
        assert row["badges"]["delimiter"]["badge"] == "from_sttm"
        assert row["values"]["delimiter"]


# -- xlsx ---------------------------------------------------------------------- #


def test_workbook_structure_and_provenance(config, tmp_path):
    payload = _payload(config, tmp_path)
    out = tmp_path / "preview.xlsx"
    build_workbook(payload).save(out)
    workbook = load_workbook(out)
    assert workbook.sheetnames == [*config.demo.metadata_sheet.tabs, "_provenance"]
    for name, tab in config.demo.metadata_sheet.tabs.items():
        headers = [c.value for c in workbook[name][1]]
        assert headers == tab.headers
    provenance = workbook["_provenance"]
    assert provenance.max_row - 1 == payload["coverage"]["total"]
    assert [c.value for c in provenance[1]] == ["tab", "row", "header", "badge", "tooltip"]


def test_workbook_bytes_and_filename(config, tmp_path):
    payload = _payload(config, tmp_path)
    workbook = load_workbook(io.BytesIO(workbook_bytes(payload)))
    assert "_provenance" in workbook.sheetnames
    assert workbook_filename(payload) == "metadata_sheet_preview_pre-run.xlsx"
    payload["run_label"] = "demo_x"
    assert workbook_filename(payload) == "metadata_sheet_preview_demo_x.xlsx"


# -- endpoints ----------------------------------------------------------------- #

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402

needs_demo_frd = pytest.mark.skipif(
    not _DEMO_FRD.is_file(), reason="demo FRD fixture not restored"
)


@pytest.fixture()
def client():
    return TestClient(ui_main.app)


@needs_demo_frd
def test_metadata_sheet_endpoint_no_run_state(client):
    payload = client.get("/api/demo/metadata-sheet").json()
    assert {"layout_note", "tabs", "coverage"} <= set(payload)
    # TestClient skips the startup generate, so no run is loaded.
    assert payload["tabs"]["columns"]["state"] == NO_RUN_STATE


@needs_demo_frd
def test_metadata_sheet_xlsx_endpoint(client):
    response = client.get("/api/demo/metadata-sheet.xlsx")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml"
    )
    assert "metadata_sheet_preview_" in response.headers["content-disposition"]
    workbook = load_workbook(io.BytesIO(response.content))
    assert "_provenance" in workbook.sheetnames
