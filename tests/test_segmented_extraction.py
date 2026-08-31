"""Segmented-dialect extraction: declared assumptions, held conflicts, and
the flat-path regression tripwire.

Every case runs on the synthetic CAQH-shaped golden (tests/segmented_fixture
.py — zero client values; the scrub denylist scan below proves it), so no
client material is needed. The flat dialect's byte-stability is separately
guarded by tests/test_framework_output.py's notebook-mode snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen import cli
from codegen.extract import ExtractionError, extract_contract
from codegen.extract.workbook import SegmentedWorkbookError
from codegen.reasoning.engine import segmented_review_items
from codegen.resolve.resolver import resolve_pair
from segmented_fixture import (
    FAQ_ASSUMED,
    FAQ_CONFIRMED,
    FEED_SLUG,
    build_workbook,
    frd_contract_dict,
)

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def pair(tmp_path, config):
    """(workbook path, frd path, scoped config) with FAQ dir in tmp."""
    workbook_path = tmp_path / "synthetic_segmented.xlsx"
    build_workbook().save(workbook_path)
    frd_path = tmp_path / "synthetic_frd.contract.json"
    frd_path.write_text(json.dumps(frd_contract_dict()), encoding="utf-8")
    faq_dir = tmp_path / "faq"
    faq_dir.mkdir()
    scoped = config.model_copy(update={
        "load_pattern_faq": config.load_pattern_faq.model_copy(
            update={"per_feed_dir": str(faq_dir)}),
    })
    return workbook_path, frd_path, scoped, faq_dir


def _write_faq(faq_dir: Path, text: str) -> None:
    (faq_dir / f"{FEED_SLUG}.faq.yaml").write_text(text, encoding="utf-8")


def _extract(pair):
    workbook_path, frd_path, scoped, _ = pair
    return extract_contract(workbook_path, frd_path, scoped,
                            generated_date="2026-01-01")


# -- governance boundary 1: discriminators ------------------------------------ #


def test_no_declaration_refuses_with_evidence_and_remedy(pair):
    with pytest.raises(SegmentedWorkbookError) as excinfo:
        _extract(pair)
    message = str(excinfo.value)
    # v1's evidence list, unchanged...
    assert "segmented (metadata-block + band-row) layout family" in message
    assert "band labels" in message
    # ...plus the declare-to-proceed remedy naming the FAQ path.
    assert "REMEDY: declare record_type_discriminators" in message
    assert f"{FEED_SLUG}.faq.yaml" in message
    assert "will not infer them" in message


def test_assumed_declaration_extracts_with_review_material(pair):
    _write_faq(pair[3], FAQ_ASSUMED)
    contract = _extract(pair)
    (feed,) = contract.feeds
    seg = feed.segmented
    assert seg is not None
    assert seg.segments_found == ["Header", "Detail", "Trailer"]
    assert seg.row_counts == {"Header": 2, "Detail": 3, "Trailer": 2}
    assert seg.discriminators.status == "assumed_pending_source_team"
    # Detail payload only; envelope carries the H/T rows.
    assert feed.field_count == 3
    assert [e.field_name for e in seg.envelope] == [
        "Format Version", "Extract Date", "Record Count", "File Sequence"]
    assert {e.stage_table for e in seg.envelope} == {"EXT_SYN_HDR", "EXT_SYN_TRL"}
    # Natural key came from the FAQ declaration, and says so.
    assert seg.natural_key_declared == ["Widget ID"]
    assert feed.load_rules.not_null_columns == ["Widget ID"]
    assert any("Mandatory/Primary Key columns carry no signal" in n
               for n in seg.notes)
    # PII flag carried from the workbook.
    assert feed.load_rules.phi_columns == ["Widget Owner"]
    # FILE_TYPE audit column is part of the Detail audit block.
    assert [a.column for a in feed.audit_columns] == [
        "LOB", "FILE_TYPE", "SRC_FILE_NAME", "REC_CREATION_TIME",
        "REC_UPDATED_TIME"]


def test_workbook_mandatory_signal_wins_over_faq(pair, tmp_path):
    workbook_path = tmp_path / "with_mandatory.xlsx"
    build_workbook(mandatory_detail_field=True).save(workbook_path)
    _write_faq(pair[3], FAQ_ASSUMED)
    contract = extract_contract(workbook_path, pair[1], pair[2],
                                generated_date="2026-01-01")
    (feed,) = contract.feeds
    assert feed.load_rules.not_null_columns == ["Widget ID"]
    # Workbook signal -> not a declared assumption.
    assert feed.segmented.natural_key_declared == []


def test_no_natural_key_signal_and_no_declaration_refuses(pair):
    _write_faq(pair[3], FAQ_ASSUMED.split("natural_key_columns")[0])
    with pytest.raises(ExtractionError) as excinfo:
        _extract(pair)
    assert "will not invent a merge key" in str(excinfo.value)


# -- review items + resolution ------------------------------------------------ #


def _resolve(pair, faq_text):
    _write_faq(pair[3], faq_text)
    contract = _extract(pair)
    sttm_path = pair[0].parent / "extracted.json"
    from codegen.extract import contract_to_json

    sttm_path.write_text(contract_to_json(contract), encoding="utf-8")
    (spec,) = resolve_pair(pair[1], sttm_path, pair[2])
    return spec, sttm_path


def test_assumed_run_resolves_flat_shaped_with_review_items(pair):
    spec, _ = _resolve(pair, FAQ_ASSUMED)
    # Same spec shape flat yields: one Detail segment, no is_segmented split.
    assert [s.segment for s in spec.segments] == ["Detail"]
    assert spec.is_segmented is False
    assert spec.segmented_extraction is not None
    # Stage-only under the precedence rule; held standard preserved.
    assert spec.standard_table is None
    assert [(h.table, h.column_count)
            for h in spec.segmented_extraction.held_standard] == [
        ("EXT_SYN_DTL", 3), ("EXT_SYN_HDR", 2), ("EXT_SYN_TRL", 2)]
    items = segmented_review_items(spec)
    kinds = [i.kind for i in items]
    assert kinds == ["extraction_assumption", "extraction_assumption",
                     "escalated_conflict"]
    assert "Header='H'" in items[0].rule_text
    assert "natural key declared" in items[1].rule_text
    assert "stage-only" in items[2].rule_text


def test_confirmed_status_drops_the_discriminator_review_gate(pair):
    spec, _ = _resolve(pair, FAQ_CONFIRMED)
    kinds = [i.kind for i in segmented_review_items(spec)]
    # natural-key assumption + conflict remain; the confirmed discriminator
    # no longer gates review (provenance line still records it).
    assert kinds == ["extraction_assumption", "escalated_conflict"]
    assert spec.segmented_extraction.discriminators.status == "confirmed"


# -- generation: report carries envelope/held; DDL does not ------------------- #


@pytest.fixture()
def generated(pair, tmp_path):
    spec, _ = _resolve(pair, FAQ_ASSUMED)
    scoped = pair[2].model_copy(update={
        "output": pair[2].output.model_copy(update={
            "dir": str(tmp_path / "out"),
            "reports_dir": str(tmp_path / "reports"),
        })
    })
    gate = cli._generate_feed(spec, scoped, dry_run=True, skip_tests=True,
                              output_mode="both")
    return spec, gate, tmp_path


def test_generation_surfaces_assumptions_and_holds_conflict(generated):
    spec, gate, tmp = generated
    assert gate.verdict == "PASS_WITH_FLAGS"
    assert sum("extraction assumption pending" in f for f in gate.flags) == 2
    assert sum("escalated conflict held" in f for f in gate.flags) == 1

    report = (tmp / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")
    assert "## Segmented extraction" in report
    assert "ASSUMED" in report
    assert "### File envelope (Header/Trailer rows — report-only, never table DDL)" in report
    assert "Record Count" in report  # trailer envelope entry in the report
    assert "### Held back — workbook Standard layer (escalated conflict)" in report
    assert "nothing was deleted" in report.lower() or "nothing was silently" in report.lower()

    feed_dir = tmp / "out" / spec.feed_slug
    # Stage-only emit: no standard DDL source, and the framework standard
    # .txt says so instead of inventing one.
    assert not list((feed_dir / "ddl").glob("*.standard.sql"))
    standard_txt = (feed_dir / "framework" /
                    f"{spec.feed_slug}_standard_table_creation.txt").read_text(
        encoding="utf-8")
    assert "No standard-layer table for this feed" in standard_txt
    # Envelope fields never reach DDL.
    all_ddl = "".join(p.read_text(encoding="utf-8")
                      for p in (feed_dir / "ddl").glob("*.sql"))
    assert "SYN_REC_CNT" not in all_ddl
    assert "SYN_FMT_VER" not in all_ddl
    assert "EXT_SYN_HDR" not in all_ddl and "EXT_SYN_TRL" not in all_ddl
    # The declared assumption reaches the provenance banner of generated code.
    reader = (feed_dir / "pipeline" / "reader.py").read_text(encoding="utf-8")
    assert "Segmented extraction: discriminators Header=H Detail=D Trailer=T" in reader
    assert "ASSUMED" in reader
    # Review items are in the candidates artifact with their kinds.
    candidates = json.loads(
        (feed_dir / "candidates" / "candidates.json").read_text(encoding="utf-8"))
    assert [c.get("kind") for c in candidates[:3]] == [
        "extraction_assumption", "extraction_assumption", "escalated_conflict"]


def test_synthetic_fixture_passes_the_scrub_denylist(pair):
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from scrub_check import scan_paths

    hits = scan_paths([pair[0], pair[1]])
    assert hits == [], hits
