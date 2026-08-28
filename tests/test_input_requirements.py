"""codegen.input_requirements: deck parsing + contract evaluation.

The parser is tested against a SYNTHETIC deck built in-test — never a
client document — mirroring the convention-check tests' posture.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from codegen.contracts.frd import FrdContract
from codegen.input_requirements import (
    input_requirements_payload,
    read_requirements,
    requirements_check,
)

REPO = Path(__file__).resolve().parents[1]

_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def _make_deck(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    """A one-slide pptx holding the requirements table's paragraph stream."""
    paragraphs = ["Some heading", "HOW TO FILL IT"]
    for row in rows:
        paragraphs.extend(row)
    paragraphs.append("Zero of three FRDs name a data dictionary — closing text.")
    body = "".join(
        f'<a:p xmlns:a="{_A_NS}"><a:r><a:t>{p}</a:t></a:r></a:p>' for p in paragraphs
    )
    slide = (
        f'<p:sld xmlns:p="{_P_NS}" xmlns:a="{_A_NS}">'
        f"<p:cSld><p:spTree><p:sp><p:txBody>{body}</p:txBody></p:sp>"
        f"</p:spTree></p:cSld></p:sld>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)


_ROWS = [
    ("Object/data Format", "parsing", "3 / 3", "Give the delimiter literally"),
    ("Target Schema", "schemas", "3 / 3", "Name BOTH layers"),
    ("Source Data Dictionary", "the VDD", "0 / 3", "Name the VDD here"),
    ("Inbound File Folder Path", "route", "2 / 3", "A route, not a direction"),
]


def _contract(*feed_overrides: dict) -> FrdContract:
    def feed(overrides):
        values = {
            "feed_name": "f1",
            "source_system": "S",
            "file_name_patterns": ["a_YYYY.csv"],
            "file_format": "csv",
            "delimiter": None,
            "record_segments": [],
            "frequency": "Monthly",
            "load_windows_sla": [],
            "lobs": ["All"],
            "domain": "D",
            "sub_domain": "SD",
            "landing_location": "mft/in/a",
            "stage_target": {"catalog": None, "schema": "stg", "tables": ["t"],
                             "load_strategy": "Truncate and Load"},
            "standard_target": {"catalog": None, "schema": "std", "tables": ["t"],
                                "load_strategy": "Append"},
            "validation_rules": [],
            "recycle_rule": None,
            "history_backfill": None,
            "archive_retention": None,
            "phi_pii_notes": None,
            "sttm_reference": "the STTM",
            "requirement_ids": [],
        }
        values.update(overrides)
        return values

    return FrdContract.model_validate({
        "contract_name": "t", "generated_from_frd": "t.docx",
        "generated_date": "2026-01-01T00:00:00", "generator": "t",
        "status": "PASS",
        "project": {"project_id": None, "project_name": "t",
                    "business_context_summary": None},
        "in_scope": [], "out_of_scope": [],
        "assumptions_constraints_dependencies": [],
        "feeds": [feed(o) for o in (feed_overrides or ({},))],
        "system_interfaces": [], "open_items": [],
    })


def test_read_requirements_parses_rows_verbatim(tmp_path):
    deck = tmp_path / "reqs.pptx"
    _make_deck(deck, _ROWS)
    rows = read_requirements(deck)
    assert [r["row"] for r in rows] == [r[0] for r in _ROWS]
    assert rows[0]["how_to_fill"] == "Give the delimiter literally"


def test_read_requirements_absent_or_garbage_is_none(tmp_path):
    assert read_requirements(tmp_path / "absent.pptx") is None
    bad = tmp_path / "bad.pptx"
    bad.write_bytes(b"not a zip")
    assert read_requirements(bad) is None
    # A deck without the table markers parses to None, not an error.
    empty = tmp_path / "no_table.pptx"
    _make_deck(empty, [])
    assert read_requirements(empty) is None


def test_requirements_check_statuses(tmp_path):
    deck = tmp_path / "reqs.pptx"
    _make_deck(deck, _ROWS)
    check = requirements_check(deck, _contract({}))
    by_row = {r["row"]: r["status"] for r in check["rows"]}
    # csv present but delimiter null → partial.
    assert by_row["Object/data Format"] == "partial"
    assert by_row["Target Schema"] == "filled"
    # The deck's headline: no FRD names a VDD.
    assert by_row["Source Data Dictionary"] == "missing"
    # The contract shape has no field for this row — flagged, not guessed.
    assert by_row["Inbound File Folder Path"] == "not_captured"
    assert check["summary"] == {"filled": 1, "partial": 1, "missing": 1,
                                "not_captured": 1}


def test_requirements_check_worst_feed_status_wins(tmp_path):
    deck = tmp_path / "reqs.pptx"
    _make_deck(deck, [("Target Schema", "schemas", "1 / 2", "Name BOTH layers")])
    contract = _contract(
        {"feed_name": "good"},
        {"feed_name": "bad",
         "standard_target": {"catalog": None, "schema": None, "tables": [],
                             "load_strategy": "Append"}},
    )
    (row,) = requirements_check(deck, contract)["rows"]
    assert row["feeds"] == {"good": "filled", "bad": "partial"}
    assert row["status"] == "partial"


def test_payload_reason_when_deck_absent(config, tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(tmp_path))
    payload = input_requirements_payload(config, REPO)
    assert payload == {"check": None, "reason": "requirements document not present"}


# -- endpoint ------------------------------------------------------------------ #

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402

needs_demo_frd = pytest.mark.skipif(
    not (REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json").is_file(),
    reason="demo FRD fixture not restored",
)


@needs_demo_frd
def test_endpoint_with_synthetic_deck(monkeypatch, tmp_path):
    _make_deck(tmp_path / "FRD-and-Dictionary-Input-Requirements.pptx", _ROWS)
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(tmp_path))
    client = TestClient(ui_main.app)
    payload = client.get("/api/demo/input-requirements").json()
    assert payload["reason"] is None
    assert payload["check"]["source"] == "FRD-and-Dictionary-Input-Requirements.pptx"
    assert len(payload["check"]["rows"]) == len(_ROWS)
