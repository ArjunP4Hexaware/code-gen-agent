"""codegen.demo_sources: synthesis rules, document matching, endpoints.

Display-only helpers for the demo UI. Unit tests construct feeds in-test
(no fixture files needed); the endpoint tests that read the demo FRD
contract skip when the fixture is absent, like the rest of the suite. The
docx convention reader is tested against a SYNTHETIC docx built in-test —
never a client document.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from codegen.contracts.frd import FrdFeed, TargetSpec
from codegen.demo_sources import (
    feed_source_files,
    input_document_dirs,
    read_frd_convention,
    scan_reference_documents,
    shell_listing,
    source_files_payload,
)

REPO = Path(__file__).resolve().parents[1]


def _target(schema: str, table: str) -> TargetSpec:
    return TargetSpec.model_validate(
        {"catalog": None, "schema": schema, "tables": [table], "load_strategy": "Append"}
    )


def _feed(**overrides) -> FrdFeed:
    values = {
        "feed_name": "cv_test_feed",
        "source_system": "Civic Vantage (CV)",
        "file_name_patterns": ["extract_YYYY_MM.csv"],
        "file_format": "csv",
        "delimiter": None,
        "record_segments": [],
        "frequency": "Monthly",
        "load_windows_sla": [],
        "lobs": [],
        "domain": "Care Management",
        "sub_domain": "Public",
        "landing_location": None,
        "stage_target": _target("stg_x", "cv_test_feed"),
        "standard_target": _target("x", "cv_test_feed"),
        "validation_rules": [],
        "recycle_rule": None,
        "history_backfill": None,
        "archive_retention": None,
        "phi_pii_notes": None,
        "sttm_reference": None,
        "requirement_ids": [],
    }
    values.update(overrides)
    return FrdFeed.model_validate(values)


# -- synthesis rules ---------------------------------------------------------- #


def test_null_landing_is_templated_slugged_and_flagged(config):
    row = feed_source_files(_feed(), config)
    assert row["landing_root"] == {
        "value": "mftlanding/inbound/care_management/public/civic_vantage_cv",
        "synthetic": True,
    }


def test_contract_landing_passes_through_unflagged(config):
    row = feed_source_files(
        _feed(landing_location="mftlanding\\inbound\\sdh\\public\\civic_vantage"), config
    )
    # Backslash-separated contract paths normalize to forward slashes.
    assert row["landing_root"] == {
        "value": "mftlanding/inbound/sdh/public/civic_vantage",
        "synthetic": False,
    }


def test_null_domain_falls_back_but_stays_flagged(config):
    row = feed_source_files(_feed(domain=None, sub_domain=None), config)
    assert row["landing_root"]["synthetic"] is True
    assert (
        row["landing_root"]["value"]
        == "mftlanding/inbound/unknown_domain/unknown_subdomain/civic_vantage_cv"
    )


def test_load_strategy_is_always_the_config_stand_in(config):
    row = feed_source_files(_feed(), config)
    assert row["load_strategy"] == {
        "stage": "Truncate and Load",
        "standard": "Upsert",
        "synthetic": True,
    }


def test_frequency_and_targets_pass_through(config):
    row = feed_source_files(_feed(frequency=None), config)
    assert row["frequency"] is None  # UI renders "not stated in FRD"
    assert row["stage_target"] == "stg_x.cv_test_feed"
    assert row["standard_target"] == "x.cv_test_feed"


def test_shell_listing_one_command_then_patterns(config):
    rows = [feed_source_files(_feed(), config)]
    lines = shell_listing(rows, config)
    assert lines[0] == (
        "$ databricks fs ls dbfs:/Volumes/soham_workspace/codegen_agent/mftlanding/"
        "mftlanding/inbound/care_management/public/civic_vantage_cv/"
    )
    assert lines[1:] == ["extract_YYYY_MM.csv"]


def test_shell_listing_empty_patterns(config):
    # The contract model requires >=1 pattern; the display path must still
    # degrade honestly if that ever changes.
    row = feed_source_files(_feed(), config)
    row["file_name_patterns"] = []
    lines = shell_listing([row], config)
    assert lines[1] == "(no file name patterns in the FRD)"


# -- reference-document matching ---------------------------------------------- #


def _docs_config(config):
    """The tracked config's expected list drives matching in these tests."""
    return config.demo.input_documents.expected


def test_scan_matches_case_insensitively_and_strips_upload_prefix(config, tmp_path):
    expected = _docs_config(config)
    assert expected, "tracked config must list expected reference documents"
    # Present via a numeric upload prefix + different case.
    (tmp_path / f"1787853350398_{expected[0].upper()}").write_bytes(b"")
    env = {"CODEGEN_INPUT_DOCS_DIR": str(tmp_path)}
    result = scan_reference_documents(config, REPO, env=env)
    assert [p["name"] for p in result["present"]] == [expected[0]]
    assert result["missing"] == expected[1:]
    assert result["expected"] == expected


def test_scan_all_present_and_none_present(config, tmp_path):
    expected = _docs_config(config)
    all_dir = tmp_path / "all"
    all_dir.mkdir()
    for name in expected:
        (all_dir / name).write_bytes(b"")
    result = scan_reference_documents(
        config, REPO, env={"CODEGEN_INPUT_DOCS_DIR": str(all_dir)}
    )
    assert result["missing"] == []
    assert len(result["present"]) == len(expected)

    empty_dir = tmp_path / "none"
    empty_dir.mkdir()
    result = scan_reference_documents(
        config, REPO, env={"CODEGEN_INPUT_DOCS_DIR": str(empty_dir)}
    )
    assert result["present"] == []
    assert result["missing"] == expected


def test_env_override_is_pathsep_separated(config, tmp_path):
    import os

    a, b = tmp_path / "a", tmp_path / "b"
    env = {"CODEGEN_INPUT_DOCS_DIR": os.pathsep.join([str(a), str(b)])}
    assert input_document_dirs(config, REPO, env=env) == [a, b]
    # Without the env var the YAML dirs resolve against the repo root.
    yaml_dirs = input_document_dirs(config, REPO, env={})
    assert (REPO / "inputs" / "sharepoint") in yaml_dirs


# -- shared document-name helpers (chooser dedupe + FRD pairing) --------------- #


def test_canonical_document_name_strips_prefix_copy_suffix_case():
    from codegen.demo_sources import canonical_document_name as canon

    assert canon("1787853350398_FRD_X.docx") == "frd_x.docx"
    assert canon("STTM_Mapping_1005034__ (1).xlsx") == "sttm_mapping_1005034__.xlsx"
    assert canon("Name (2)") == "name"
    # " (n)" strips only as a copy suffix, never from the middle of a name.
    assert canon("Vantage (CV) extract.xlsx") == "vantage (cv) extract.xlsx"
    assert canon("A.docx") == canon("123_a (1).DOCX")


def test_pairing_by_shared_ticket_number():
    from codegen.demo_sources import pair_sttm_with_frd

    sttm = ["STTM_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Mapping_1005034__ (1).xlsx",
            "STTM-Medicare Expansion-MIDS-Social Determine (1).xlsx"]
    frd = ["FRD_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Ingestion_1005034 (1).docx",
           "FRD_Medicare Expansion-MIDS - Socially Determined (1).docx"]
    pairs = pair_sttm_with_frd(sttm, frd)
    # 1005034 pairs; MIDS has no shared ticket → conservatively unpaired.
    assert pairs == {sttm[0]: frd[0]}


def test_pairing_is_conservative_on_ambiguity():
    from codegen.demo_sources import pair_sttm_with_frd

    # Two FRDs share the ticket → no pairing for that STTM.
    assert pair_sttm_with_frd(["STTM_1005034.xlsx"],
                              ["FRD_A_1005034.docx", "FRD_B_1005034.docx"]) == {}
    # Two STTMs claim one FRD → neither pairs.
    assert pair_sttm_with_frd(["STTM_A_1005034.xlsx", "STTM_B_1005034.xlsx"],
                              ["FRD_1005034.docx"]) == {}
    # No tickets anywhere → nothing pairs.
    assert pair_sttm_with_frd(["STTM_plain.xlsx"], ["FRD_plain.docx"]) == {}


# -- docx convention reader (synthetic document only) -------------------------- #

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _make_docx(path: Path, rows: list[list[list[str]]]) -> None:
    """rows: table rows -> cells -> paragraphs (each paragraph one run)."""

    def cell(paragraphs: list[str]) -> str:
        return "<w:tc>" + "".join(
            f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs
        ) + "</w:tc>"

    body = "".join(
        "<w:tr>" + "".join(cell(c if isinstance(c, list) else [c]) for c in row) + "</w:tr>"
        for row in rows
    )
    doc = f'<w:document xmlns:w="{_W_NS}"><w:body><w:tbl>{body}</w:tbl></w:body></w:document>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", doc)


def test_read_frd_convention_parses_structural_metadata(tmp_path):
    docx = tmp_path / "synthetic_frd.docx"
    _make_docx(
        docx,
        [
            ["Structural Metadata", "ADLS Location", "mftlanding/inbound/a/b/c"],
            # Multi-paragraph value joins with a space.
            ["", "Target Schema", ["Stage: stg_a", "Standard: a"]],
            ["", "Load Strategy STG", "Truncate and Load"],
            ["", "Load Strategy STD", "Upsert"],
            # Second occurrence (template "Do Not Use" section): first wins.
            ["", "ADLS Location", "template/do/not/use"],
        ],
    )
    result = read_frd_convention(docx)
    assert result == {
        "source": "synthetic_frd.docx",
        "adls_location": "mftlanding/inbound/a/b/c",
        "target_schema": "Stage: stg_a Standard: a",
        "load_strategy_stg": "Truncate and Load",
        "load_strategy_std": "Upsert",
    }


def test_read_frd_convention_unparseable_returns_none(tmp_path):
    bad = tmp_path / "not_a_docx.docx"
    bad.write_bytes(b"not a zip")
    assert read_frd_convention(bad) is None
    assert read_frd_convention(tmp_path / "absent.docx") is None


# -- payload + endpoints ------------------------------------------------------- #

_DEMO_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
needs_demo_frd = pytest.mark.skipif(
    not _DEMO_FRD.is_file(),
    reason="demo FRD fixture not restored (removed 2026-08-22)",
)


@needs_demo_frd
def test_source_files_payload_reads_demo_frd(config, tmp_path):
    payload = source_files_payload(
        config, REPO, env={"CODEGEN_INPUT_DOCS_DIR": str(tmp_path)}
    )
    assert payload["frd_contract"] == "FRD_demo_cv_golden.contract.json"
    assert len(payload["feeds"]) == 3
    for row in payload["feeds"]:
        assert row["file_name_patterns"], "CV feeds all state patterns"
        assert row["load_strategy"]["synthetic"] is True
    commands = [line for line in payload["shell_listing"] if line.startswith("$ ")]
    assert len(commands) == 3
    assert payload["convention_check"] is None  # no docx in the scanned dir


def test_source_files_payload_missing_contract_raises(config, tmp_path, monkeypatch):
    with pytest.raises(FileNotFoundError):
        source_files_payload(config, tmp_path, env={})


pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(ui_main.app)


@needs_demo_frd
def test_source_files_endpoint(client, monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(tmp_path))
    payload = client.get("/api/demo/source-files").json()
    assert {"frd_contract", "feeds", "shell_listing", "convention_check"} <= set(payload)
    assert len(payload["feeds"]) == 3


@needs_demo_frd
def test_convention_panel_absent_where_document_absent(client, monkeypatch, tmp_path):
    """Portability guard: the convention panel reads a client FRD that lives
    OUTSIDE the repo. On a machine without it (the ACFC port reads the
    client's own inputs dir), the endpoint must answer 200 with the panel
    simply absent — no error, no stack trace, no local path leaking."""
    monkeypatch.delenv("CODEGEN_INPUT_DOCS_DIR", raising=False)
    # Stand in for a checkout whose inputs/ dirs hold no matching document.
    store = ui_main._require_store()
    empty = tmp_path / "empty"
    empty.mkdir()
    demo = store.config.demo.model_copy(
        update={
            "input_documents": store.config.demo.input_documents.model_copy(
                update={"dirs": [str(empty)]}
            )
        }
    )
    monkeypatch.setattr(store, "config", store.config.model_copy(update={"demo": demo}))

    response = client.get("/api/demo/source-files")
    assert response.status_code == 200
    payload = response.json()
    assert payload["convention_check"] is None
    assert ".docx" not in response.text
    assert "Traceback" not in response.text


def _reference_documents(client) -> dict:
    docs = client.get("/api/demo/input-documents").json()["documents"]
    by_kind = {d["kind"]: d for d in docs}
    # The frd kind is unchanged by the documents card work.
    assert "stand_in" in by_kind["frd"]
    return by_kind["reference_documents"]


def test_input_documents_card_states(client, monkeypatch, tmp_path, config):
    expected = _docs_config(config)

    empty = tmp_path / "none"
    empty.mkdir()
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(empty))
    scan = _reference_documents(client)
    assert scan["present"] == [] and scan["missing"] == expected

    partial = tmp_path / "partial"
    partial.mkdir()
    (partial / expected[0]).write_bytes(b"")
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(partial))
    scan = _reference_documents(client)
    assert [p["name"] for p in scan["present"]] == [expected[0]]
    assert scan["missing"] == expected[1:]

    full = tmp_path / "all"
    full.mkdir()
    for name in expected:
        (full / name).write_bytes(b"")
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(full))
    scan = _reference_documents(client)
    assert scan["missing"] == [] and len(scan["present"]) == len(expected)
