"""M11 — the six causes of the v0.6.2 all-pairs run (1 of 10 passed).

The record is `docs/acfc/RUN_v062_all_pairs.md` on the unscrubbed
``acfc-runs`` branch; nothing from it is copied here. One section per cause:

1. a FILE_DETAILS legend row killed the parse (pair 2)
2. a Segment column reading 'NA' was outside the vocabulary (pair 5)
3. a `tinyint` audit column was refused (pair 6)
4. an .xlsx inbound file has no delimiter (pair 4)
5. a 140k-cell workbook outlived the parser's budget and was killed (pair 3)
6. layout questions were "proceeded unresolved" and then invisible (pair 7)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from acfc_shapes.common import xlsx_bytes
from codegen import cli
from codegen.emit.context import build_context
from codegen.extract import extract_contract
from codegen.extract.workbook import is_annotation
from codegen.formats import file_kind, is_fixed_width, is_spreadsheet
from codegen.gate import audit_type_check
from codegen.layout.size import WorkbookTooLarge, check_workbook_size, workbook_cells
from codegen.report.generation_report import layout_skipped_flags

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
PAIR_1_FRD = SHAPES / "frd" / "f1_pair_1.docx"


# ------------------------------------------------ 1. the FILE_DETAILS legend


def test_an_annotation_vendor_cell_is_recognised(config):
    annotation = ("Amber italic DataType = the vendor gave neither a data type nor an "
                  "example value for this column, so the default applies. Confirm before use.")
    assert is_annotation(annotation, False, config.extractor)
    assert is_annotation("a note", True, config.extractor)          # italic alone
    assert not is_annotation("VENDOR_A", False, config.extractor)
    assert not is_annotation(None, False, config.extractor)


def _file_details_workbook(rows: list[tuple], italic_rows: tuple[int, ...] = ()) -> Workbook:
    """A minimal FILE_DETAILS sheet: header + the given (vendor, file, freq)."""
    from openpyxl.styles import Font

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "FILE_DETAILS"
    sheet.append(["Vendor", "FileName", "Frequency"])
    for row in rows:
        sheet.append(list(row))
    for row_number in italic_rows:
        sheet.cell(row=row_number, column=1).font = Font(italic=True)
    return workbook


def test_a_legend_row_is_skipped_and_logged_never_a_parse_error(config, tmp_path):
    from codegen.extract.workbook import _parse_file_details

    workbook = _file_details_workbook([
        ("VENDOR_A", "feed_YYYYMMDD.csv", "Daily"),
        ("DataType = the vendor gave neither a data type nor an example value. "
         "Confirm before use.", None, None),
        ("a note set in italic", None, None),
        ("VENDOR_B", None, "Daily"),                       # no file name
        ("VENDOR_C", "other_YYYYMMDD.csv", "Weekly"),
    ], italic_rows=(4,))
    rows, skipped = _parse_file_details(workbook, config.extractor, "wb.xlsx")
    assert [r.file_name for r in rows] == ["feed_YYYYMMDD.csv", "other_YYYYMMDD.csv"]
    assert len(skipped) == 3
    assert "annotation, not a file" in skipped[0] and "row 3" in skipped[0]
    assert "annotation, not a file" in skipped[1] and "row 4" in skipped[1]   # italic
    assert "no file name" in skipped[2] and "row 5" in skipped[2]
    del tmp_path


def test_a_file_details_sheet_of_only_annotations_still_fails_loudly(config):
    from codegen.extract.workbook import WorkbookParseError, _parse_file_details

    workbook = _file_details_workbook([("Confirm before use.", None, None)])
    with pytest.raises(WorkbookParseError, match="no data rows"):
        _parse_file_details(workbook, config.extractor, "wb.xlsx")


# --------------------------------------------------------- 2. the NA segment


def _sheet_with_segments(values: list[str | None]) -> Workbook:
    """A one-sheet STTM whose Segment column holds ``values``."""
    workbook = load_workbook(SHAPES / "sttm" / "pair_1_family_a.xlsx")
    sheet = workbook["FEED_1_MAPPING"]
    row = 16
    index = 0
    while row <= sheet.max_row and index < len(values):
        if sheet.cell(row=row, column=3).value:          # a field row
            sheet.cell(row=row, column=2).value = values[index]
            index += 1
        row += 1
    return workbook


def test_a_segment_column_of_na_extracts_unsegmented_and_flags(pair1_config, tmp_path):
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.resolve import resolve_pair

    workbook = _sheet_with_segments(["NA"] * 60)
    sttm = tmp_path / "sttm_na.xlsx"
    sttm.write_bytes(xlsx_bytes(workbook))
    pair = resolve_pair(sttm, PAIR_1_FRD, pair1_config, provider=None, cache_dirs=[],
                        generated_date="2026-01-01")
    frd_json = tmp_path / "frd.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    contract = extract_contract(sttm, frd_json, pair1_config, generated_date="2026-01-01",
                                layout=pair.sttm.profile)
    feed = contract.feeds[0]
    assert all(f.record_segment is None for f in feed.fields)     # extracted flat
    assert any(f.startswith("segments_none:") and "'NA'" in f for f in feed.extraction_flags)


def test_an_unknown_segment_spelling_is_still_loud(pair1_config, tmp_path):
    from codegen.extract import ExtractionError
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.resolve import resolve_pair

    sttm = tmp_path / "sttm_odd.xlsx"
    sttm.write_bytes(xlsx_bytes(_sheet_with_segments(["ZZZ"] * 60)))
    pair = resolve_pair(sttm, PAIR_1_FRD, pair1_config, provider=None, cache_dirs=[],
                        generated_date="2026-01-01")
    frd_json = tmp_path / "frd.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    with pytest.raises(ExtractionError, match="outside the"):
        extract_contract(sttm, frd_json, pair1_config, generated_date="2026-01-01",
                         layout=pair.sttm.profile)


def test_the_none_class_is_never_a_segment_elsewhere(config):
    from codegen.layout.discover import none_segment_spellings, segment_spellings

    disc = config.extractor.discovery
    assert "na" in none_segment_spellings(disc)
    assert not (segment_spellings(disc) & none_segment_spellings(disc))
    assert {"header", "detail", "trailer"} <= segment_spellings(disc)


# -------------------------------------------------------- 3. the audit type


def test_a_nonstandard_audit_type_is_carried_and_flagged(pair1_config, tmp_path):
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.resolve import resolve_pair

    workbook = load_workbook(SHAPES / "sttm" / "pair_1_family_a.xlsx")
    sheet = workbook["FEED_1_MAPPING"]
    audit_rows = [r for r in range(16, sheet.max_row + 1)
                  if str(sheet.cell(row=r, column=3).value or "").strip() == "NA"]
    assert audit_rows, "the fixture has audit rows"
    sheet.cell(row=audit_rows[0], column=23).value = "tinyint"       # stage datatype
    sttm = tmp_path / "sttm_tinyint.xlsx"
    sttm.write_bytes(xlsx_bytes(workbook))
    pair = resolve_pair(sttm, PAIR_1_FRD, pair1_config, provider=None, cache_dirs=[],
                        generated_date="2026-01-01")
    frd_json = tmp_path / "frd.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    contract = extract_contract(sttm, frd_json, pair1_config, generated_date="2026-01-01",
                                layout=pair.sttm.profile)
    feed = contract.feeds[0]
    assert any(a.datatype == "tinyint" for a in feed.audit_columns)
    assert any(f.startswith("audit_type_nonstandard:") for f in feed.extraction_flags)


def test_the_profile_decides_whether_a_nonstandard_audit_type_is_acceptable(pair1_config):
    from types import SimpleNamespace

    spec = SimpleNamespace(
        segments=[], audit_columns=[SimpleNamespace(column="DELETE_FLAG", datatype="tinyint"),
                                    SimpleNamespace(column="SRC_FILE_NAME", datatype="String")])
    restricted = pair1_config.conventions.profiles["edo_sfmc"]
    accepting = pair1_config.conventions.profiles["acfc_prx"]
    assert restricted.audit_types_restricted and not accepting.audit_types_restricted
    failed = audit_type_check(spec, restricted)
    assert not failed.passed and "DELETE_FLAG (tinyint)" in failed.details
    passed = audit_type_check(spec, accepting)
    assert passed.passed and "DELETE_FLAG (tinyint)" in passed.details
    standard = SimpleNamespace(segments=[], audit_columns=[spec.audit_columns[1]])
    assert audit_type_check(standard, restricted).passed


def test_a_declared_type_reaches_the_ddl(config):
    from codegen.emit.context import sql_type

    assert sql_type("tinyint") == "TINYINT"
    assert sql_type("String") == "STRING"
    with pytest.raises(Exception, match="no SQL type mapping"):
        sql_type("a made up type")
    del config


# ------------------------------------------------------ 4. the xlsx inbound


@pytest.mark.parametrize("fmt, patterns, kind", [
    (".xlsx", [], "spreadsheet"),
    ("xlsx", [], "spreadsheet"),
    ("Excel workbook", [], "spreadsheet"),
    ("File Data Ingestion", ["feed_YYYYMMDD.xlsx"], "spreadsheet"),
    ("Fixed Width", [], "fixed_width"),
    ("csv", ["feed.csv"], "delimited"),
    ("File Data Ingestion", ["feed.csv"], "delimited"),
])
def test_file_kind(config, fmt, patterns, kind):
    assert file_kind(fmt, config, None, patterns) == kind


def test_a_spreadsheet_is_never_fixed_width_however_empty_its_delimiter(config):
    # The trap: `delimiter == ""` meant fixed width in two places before M11.
    assert is_spreadsheet(".xlsx", config)
    assert not is_fixed_width(".xlsx", config, "")
    assert is_fixed_width("Fixed Width", config, "")
    assert is_fixed_width("some format", config, "")        # unchanged for everything else


def _xlsx_pair(pair1_config, tmp_path):
    """The pair-1 documents with an .xlsx inbound format stated in the FRD."""
    from acfc_shapes import frd as frd_fixtures
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.resolve import resolve_pair
    from codegen.resolve.resolver import resolve_pair as resolve_contracts

    frd = tmp_path / "frd_xlsx.docx"
    frd.write_bytes(frd_fixtures.build_f1_pair1(object_format=".xlsx"))
    sttm = SHAPES / "sttm" / "pair_1_family_a.xlsx"
    pair = resolve_pair(sttm, frd, pair1_config, provider=None, cache_dirs=[],
                        generated_date="2026-01-01")
    frd_json, sttm_json = tmp_path / "frd.json", tmp_path / "sttm.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    from codegen.extract import contract_to_json as sttm_to_json

    contract = extract_contract(sttm, frd_json, pair1_config, generated_date="2026-01-01",
                                layout=pair.sttm.profile)
    sttm_json.write_text(sttm_to_json(contract), encoding="utf-8")
    (spec,) = resolve_contracts(frd_json, sttm_json, pair1_config)
    return pair, spec


def test_an_xlsx_feed_resolves_with_no_delimiter_and_a_sheet_question(pair1_config, tmp_path):
    pair, spec = _xlsx_pair(pair1_config, tmp_path)
    assert spec.file_format == ".xlsx"
    assert spec.delimiter == ""                      # a spreadsheet has none
    assert spec.sheet_name is None
    assert any(f.startswith("sheet_name_unstated") for f in spec.provenance_flags)
    asked = [q for q in pair.questions if q.key.endswith("sheet_name")]
    assert len(asked) == 1 and asked[0].kind == "text"
    assert "worksheet" in asked[0].reason


def test_the_xlsx_pipeline_reads_a_sheet_not_a_delimiter(pair1_config, tmp_path):
    _pair, spec = _xlsx_pair(pair1_config, tmp_path)
    context = build_context(spec, pair1_config, allow_duplicate_file_name=True,
                            duplicate_rule_text=None, notification_rule_texts=[])
    assert context["spreadsheet"] is True
    assert context["fixed_width"] is False           # the trap, pinned
    gate = cli._generate_feed(
        spec.model_copy(update={"sheet_name": "Accumulators"}),
        pair1_config.model_copy(update={"output": pair1_config.output.model_copy(
            update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})}),
        dry_run=True, skip_tests=True, output_mode="notebook")
    assert gate.verdict != "FAIL", [c for c in gate.checks if not c.passed]
    feed_dir = tmp_path / "out" / spec.feed_slug
    reader = (feed_dir / "pipeline" / "reader.py").read_text(encoding="utf-8")
    assert "read_excel" in reader and 'sheet_name="Accumulators"' in reader
    assert "spark.read.text" not in reader and ".csv(path)" not in reader
    feed_spec = (feed_dir / "pipeline" / "feed_spec.py").read_text(encoding="utf-8")
    assert 'SHEET_NAME: str | None = "Accumulators"' in feed_spec
    # pair 1 is segmented as well: a workbook carrying H/D/T RECORDS is a
    # shape no document has shown, and the run says so instead of assuming.
    assert any(f.startswith("spreadsheet_segmented:") for f in spec.provenance_flags)


def test_a_flat_spreadsheet_feed_writes_workbook_fixtures(pair1_config, tmp_path):
    """The flat case (the shape the ACFC run met): the generated fixture
    writer and test conftest write a WORKBOOK, not a delimited text file."""
    _pair, spec = _xlsx_pair(pair1_config, tmp_path)
    detail = spec.detail_segment
    flat = spec.model_copy(update={"segments": [detail],      # one segment = a flat feed
                                   "sheet_name": "Accumulators"})
    assert not flat.is_segmented
    config = pair1_config.model_copy(update={"output": pair1_config.output.model_copy(
        update={"dir": str(tmp_path / "out2"), "reports_dir": str(tmp_path / "reports2")})})
    cli._generate_feed(flat, config, dry_run=True, skip_tests=True, output_mode="notebook")
    feed_dir = tmp_path / "out2" / flat.feed_slug
    fixtures = (feed_dir / "tools" / "make_fixtures.py").read_text(encoding="utf-8")
    assert "from openpyxl import Workbook" in fixtures and "workbook.save(path)" in fixtures
    conftest = (feed_dir / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "workbook.save(path)" in conftest
    # (the spec's own flags are inherited from the segmented copy above; what
    # matters here is that the flat feed's artefacts are workbook-shaped)
    assert "DELIMITER.join" not in fixtures


def test_an_xlsx_feed_writes_no_fixed_width_handler_rows(pair1_config, tmp_path):
    """The IIG's fixed-width handler keys on `delimiter == ""` too — a
    spreadsheet feed must not land in it (it carries no byte positions)."""
    from codegen.emit.framework import emit_framework
    from codegen.faq import FaqAnswer, LoadPatternFaq

    _pair, spec = _xlsx_pair(pair1_config, tmp_path)
    artefacts = emit_framework(
        spec, LoadPatternFaq(feed_abbreviation=FaqAnswer(value="ACCUM", source="engineer")),
        [], pair1_config, tmp_path / "out", conventions_profile="acfc_prx",
        iig_template="iig_v2")
    handler = artefacts.payload["tabs"]["ADLS_FIXED_WIDTH_HANDLER"]
    assert handler["rows"] == []
    assert artefacts.row_counts["ADLS_FIXED_WIDTH_HANDLER"] == 0


# --------------------------------------------------- 5. the heavy workbook


def _big_workbook(path: Path, rows: int, columns: int) -> None:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("BIG")
    for r in range(rows):
        sheet.append([f"c{r}_{c}" for c in range(columns)])
    workbook.save(path)


def test_a_workbook_over_the_cap_is_a_verdict_not_a_killed_parse(config, tmp_path):
    big = tmp_path / "big.xlsx"
    _big_workbook(big, rows=2000, columns=100)          # 200k cells
    total, per_sheet, estimated = workbook_cells(big)
    assert total >= 200_000 and sum(per_sheet.values()) == total
    # openpyxl's write-only mode declares no dimension: the count is then an
    # estimate from the sheet XML's size, and the message says "about".
    assert estimated
    with pytest.raises(WorkbookTooLarge) as excinfo:
        check_workbook_size(big, config.inputs.max_workbook_cells)
    message = str(excinfo.value)
    assert "unreadable:" in message and "cells, > cap" in message
    check_workbook_size(big, 0)                          # 0 = no cap
    check_workbook_size(big, 10_000_000)


def test_the_size_probe_never_gives_a_verdict_of_its_own(tmp_path):
    not_a_workbook = tmp_path / "x.xlsx"
    not_a_workbook.write_bytes(b"not a zip")
    check_workbook_size(not_a_workbook, 1000)            # the reader reports it, not us


def test_the_worker_returns_unreadable_with_the_count(config, tmp_path):
    from codegen.layout.docworker import read_document

    big = tmp_path / "big.xlsx"
    _big_workbook(big, rows=2000, columns=100)
    verdict = read_document(big, "big.xlsx", config, REPO)
    assert verdict["state"] == "unreadable"
    assert "cells, > cap" in verdict["reason"] and verdict["facts"] is None


def test_the_tracked_cap_lets_every_fixture_through(config):
    assert config.inputs.max_workbook_cells == 250_000
    for workbook in sorted((SHAPES / "sttm").glob("*.xlsx")):
        check_workbook_size(workbook, config.inputs.max_workbook_cells)


# --------------------------------------------- 6. proceeded-unresolved


def test_skipped_questions_become_flags_and_a_report_section(tmp_path):
    from codegen.report.generation_report import _layout_section

    skipped = [{"key": "MAPPING_X/stage/column", "document": "sttm", "title": "Stage column",
                "reason": "no header matched"},
               {"key": "feeds[0].sheet_name", "document": "frd", "title": "Sheet name",
                "reason": "the source files are spreadsheets"}]
    flags = layout_skipped_flags(skipped)
    assert flags == [
        "layout_question_skipped:MAPPING_X/stage/column — no header matched",
        "layout_question_skipped:feeds[0].sheet_name — the source files are spreadsheets"]
    assert layout_skipped_flags(None) == []
    section = "\n".join(_layout_section(skipped))
    assert "## Layout questions left unanswered" in section
    assert "2 question(s) were skipped" in section
    assert "`MAPPING_X/stage/column`" in section and "Stage column" in section
    assert _layout_section([]) == [] and _layout_section(None) == []
    del tmp_path


def test_the_report_carries_the_section_and_the_flags(pair1_config, pair1_spec, tmp_path):
    skipped = [{"key": "MAPPING_X/stage/column", "document": "sttm", "title": "Stage column",
                "reason": "no header matched the role"}]
    config = pair1_config.model_copy(update={"output": pair1_config.output.model_copy(
        update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})})
    gate = cli._generate_feed(pair1_spec, config, dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2", layout_skipped=skipped)
    assert any(f.startswith("layout_question_skipped:MAPPING_X/stage/column")
               for f in gate.flags)
    assert gate.verdict != "FAIL"                      # a flag, never a FAIL
    report = (tmp_path / "reports" / f"{pair1_spec.feed_slug}.md").read_text(encoding="utf-8")
    assert "## Layout questions left unanswered" in report
    assert "MAPPING_X/stage/column" in report


def test_a_run_that_answered_everything_has_no_section(pair1_config, pair1_spec, tmp_path):
    config = pair1_config.model_copy(update={"output": pair1_config.output.model_copy(
        update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})})
    cli._generate_feed(pair1_spec, config, dry_run=True, skip_tests=True,
                       output_mode="framework", conventions_profile="acfc_prx",
                       iig_template="iig_v2")
    report = (tmp_path / "reports" / f"{pair1_spec.feed_slug}.md").read_text(encoding="utf-8")
    assert "Layout questions left unanswered" not in report


def test_the_runner_keeps_skipped_questions_on_the_status():
    """A proceed no longer erases them: `layout_skipped` outlives the dialog."""
    pytest.importorskip("fastapi")
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, work=lambda: None)
    assert runner.status()["layout_skipped"] == []
    runner.layout_skipped = [{"key": "MAPPING_X/stage/column", "document": "sttm",
                              "title": "Stage column", "reason": "no header matched"}]
    status = runner.status()
    assert [q["key"] for q in status["layout_skipped"]] == ["MAPPING_X/stage/column"]
