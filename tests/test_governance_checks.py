"""codegen.governance_checks + the FRD document-level requirements check.

Synthetic decks/documents only — never client files. The checks are
document-driven: a control appears only when the deck states it, and an
absent or unparseable deck contributes nothing.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from codegen.governance_checks import RunFacts, deck_checks, governance_checks_payload
from codegen.input_requirements import document_requirements_check

REPO = Path(__file__).resolve().parents[1]

_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _make_deck(path: Path, paragraphs: list[str]) -> None:
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


def _make_docx(path: Path, rows: list[tuple[str, str]]) -> None:
    def cell(text: str) -> str:
        return f"<w:tc><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"

    body = "".join(f"<w:tr>{cell(k)}{cell(v)}</w:tr>" for k, v in rows)
    doc = (
        f'<w:document xmlns:w="{_W_NS}"><w:body><w:tbl>{body}</w:tbl>'
        f"</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", doc)


_LOADED = RunFacts(
    loaded=True, mode="replay", feeds=2, fingerprinted_feeds=2,
    candidates=2, grounded_candidates=1, pending_reviews=2,
    reports_on_disk=2, candidate_providers=("anthropic", "anthropic"),
)


def test_governance_deck_controls_verbatim_and_evaluated(tmp_path):
    deck = tmp_path / "gov.pptx"
    _make_deck(deck, [
        "SHA-256 fingerprints · run manifests",
        "Grounding audit · human-in-the-loop",
        "Audit trail in a volume",
        "Unrelated slide text",
    ])
    checks = deck_checks(deck, "governance", _LOADED)
    controls = [c["control"] for c in checks]
    # The deck's own lines, verbatim; the grounding/HITL line backs two checks.
    assert controls == [
        "SHA-256 fingerprints · run manifests",
        "Grounding audit · human-in-the-loop",
        "Grounding audit · human-in-the-loop",
        "Audit trail in a volume",
    ]
    assert all(c["status"] == "verified" for c in checks)
    assert "1/2 candidate citations" in checks[1]["evidence"]
    assert "1 failed grounding" in checks[1]["evidence"]


def test_controls_absent_from_deck_produce_no_checks(tmp_path):
    deck = tmp_path / "gov.pptx"
    _make_deck(deck, ["Only the audit trail is mentioned here"])
    checks = deck_checks(deck, "governance", _LOADED)
    assert [c["control"] for c in checks] == ["Only the audit trail is mentioned here"]


def test_run_dependent_controls_wait_for_a_run(tmp_path):
    deck = tmp_path / "gov.pptx"
    _make_deck(deck, ["SHA-256 fingerprints everywhere"])
    (check,) = deck_checks(deck, "governance", RunFacts())
    assert check["status"] == "pending_run"


def test_solution_deck_structural_checks(tmp_path):
    deck = tmp_path / "sol.pptx"
    _make_deck(deck, [
        "sync on start-up — never writes back",
        "one call per document; everything else is deterministic code",
    ])
    checks = deck_checks(deck, "solution", _LOADED)
    assert [c["status"] for c in checks] == ["verified", "verified"]
    assert "list + download only" in checks[0]["evidence"]
    assert "zero live model calls" in checks[1]["evidence"]


def test_unparseable_deck_contributes_nothing(tmp_path, config, monkeypatch):
    bad_dir = tmp_path / "docs"
    bad_dir.mkdir()
    (bad_dir / "FRD-to-STTM-Agent-Data-Governance-Architecture.pptx").write_bytes(b"junk")
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(bad_dir))
    payload = governance_checks_payload(config, REPO, RunFacts())
    assert payload["checks"] == []
    assert set(payload["absent_decks"]) == {"governance", "solution"}


# -- FRD document vs the requirements deck ------------------------------------- #


def test_document_requirements_check(tmp_path):
    deck = tmp_path / "reqs.pptx"
    _make_deck(deck, [
        "HOW TO FILL IT",
        "Target Schema", "d", "3 / 3", "how",
        "Archive Schedule", "d", "1 / 3", "how",
        "Domain and Sub-domain", "d", "3 / 3", "how",
        "Zero of three FRDs name a data dictionary.",
    ])
    docx = tmp_path / "frd.docx"
    _make_docx(docx, [
        ("Target Schema", "Stage: stg_x Standard: x"),
        ("Archive Schedule", ""),          # label present, value empty
        ("Domain", "Member"),              # compound: one part present only
    ])
    check = document_requirements_check(deck, docx)
    by_row = {r["row"]: r["status"] for r in check["rows"]}
    assert by_row["Target Schema"] == "filled"
    assert by_row["Archive Schedule"] == "missing"
    assert by_row["Domain and Sub-domain"] == "partial"
    assert check["summary"] == {"filled": 1, "partial": 1, "missing": 1}


def test_document_check_none_when_either_side_unreadable(tmp_path):
    deck = tmp_path / "reqs.pptx"
    _make_deck(deck, ["HOW TO FILL IT", "A", "b", "c", "d", "Zero of three FRDs x"])
    assert document_requirements_check(deck, tmp_path / "absent.docx") is None
    bad = tmp_path / "bad.pptx"
    bad.write_bytes(b"junk")
    docx = tmp_path / "frd.docx"
    _make_docx(docx, [("A", "v")])
    assert document_requirements_check(bad, docx) is None


# -- endpoint ------------------------------------------------------------------ #

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main as ui_main  # noqa: E402


def test_governance_endpoint_pre_run(monkeypatch, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    _make_deck(
        docs / "FRD-to-STTM-Agent-Data-Governance-Architecture.pptx",
        ["SHA-256 fingerprints", "Grounding audit"],
    )
    _make_deck(
        docs / "FRD-to-STTM-Agent-Solution-Architecture.pptx",
        ["never writes back"],
    )
    monkeypatch.setenv("CODEGEN_INPUT_DOCS_DIR", str(docs))
    client = TestClient(ui_main.app)
    payload = client.get("/api/demo/governance-checks").json()
    statuses = {c["control"]: c["status"] for c in payload["checks"]}
    # TestClient skips startup generation: run-dependent checks wait, the
    # structural read-only check verifies immediately.
    assert statuses["SHA-256 fingerprints"] == "pending_run"
    assert statuses["never writes back"] == "verified"
    assert payload["summary"]["verified"] >= 1
