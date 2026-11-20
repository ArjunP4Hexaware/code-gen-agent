"""post214: the MandatoryColumnCheckRule (the first tester's ask; Soham, 2026-11-20: a
standard rule; synthetic text only).

Her answers: RULE_TYPE STDDelta; SOURCE_COLUMN = TARGET_COLUMN = the standard columns of
the fields the STTM marks Required; INPUT_PARAM = the error code the feed's FRD states
for a missing mandatory field (its error table - not a fixed code); her framework keeps
ADLS MANDATORY_FIELD_LIST blank and checks the fields through the DQ rule.

Soham's calls: MANDATORY_FIELD_LIST becomes a decided blank whenever the rule row is
written; an FRD with no error table still gets the row, INPUT_PARAM open with a
non-blocking review note. An FRD stating "No Rejection" (post193) gets no row.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from acfc_shapes.common import paragraph, table
from codegen.config import load_config
from codegen.extract.frd_docx import DocxContent, mandatory_error_codes, read_frd
from codegen.layout.resolve import resolve_frd
from codegen.metadata_template import dq_not_generated_flags, mandatory_rule_written
from test_dq_stated_only import NULLS, _with
from test_iig_dq_rules import DQ, _v
from test_tracker_incidents_post193 import ADLS, _rows, acfc  # noqa: F401 (fixture)

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")
FRD = CONFIG.extractor.frd
HEADER = ["ERROR  CODE", "ERROR DESCRIPTION", "Fields/Comment"]


def _error_table(*rows):
    return [HEADER, *[list(r) for r in rows]]


def _content(grid, nested=True) -> DocxContent:
    if nested:
        return DocxContent(tables=[[["Requirement", "text"]]], paragraphs=[],
                           nested={(0, 0, 1): grid})
    return DocxContent(tables=[grid], paragraphs=[])


# ------------------------------------------------------------------ the reader

def test_the_config_names_the_error_tables_headers_and_row():
    assert FRD.error_code_headers and FRD.error_description_headers
    assert FRD.mandatory_error_descriptions


@pytest.mark.parametrize("nested", [True, False])
def test_the_mandatory_rows_code_is_read_inside_a_cell_or_at_top_level(nested):
    grid = _error_table(("9001", "Mandatory field missing (header) - <field name>", "all"),
                        ("9002", "Invalid value (header) - <field name>", "x"))
    found = mandatory_error_codes(_content(grid, nested), FRD)
    assert [code for code, _t, _w in found] == ["9001"]
    _code, text, where = found[0]
    assert text.startswith("Mandatory field missing")
    assert "row 2" in where


@pytest.mark.parametrize("grid", [
    [["Code", "Description"], ["9001", "Mandatory field missing"]],      # other headers
    _error_table(("", "Mandatory field missing", "")),                  # no code
    _error_table(("9001\n9002", "Mandatory field missing", "")),        # not one value
    _error_table(("9001", "Field is not mandatory field missing", "")),  # not its first words
])
def test_nothing_else_is_read_as_the_code(grid):
    assert mandatory_error_codes(_content(grid), FRD) == []


def _with_error_table(data: bytes, grid) -> bytes:
    """The fixture FRD + a requirement table holding ``grid`` inside a cell."""
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for info in src.infolist():
            body = src.read(info)
            if info.filename == "word/document.xml":
                extra = paragraph("Error handling") + table([["Errors", grid]])
                body = body.replace(b"<w:sectPr/>", extra.encode("utf-8") + b"<w:sectPr/>")
            archive.writestr(info, body)
    return out.getvalue()


def _contract(tmp_path, grid):
    path = tmp_path / "FRD.docx"
    path.write_bytes(_with_error_table(fm.build_frd(), grid))
    doc, content = resolve_frd(path, CONFIG, use_cache=False, runtime_cache_dir=tmp_path / "rt")
    contract = read_frd(content, doc.profile, CONFIG, document_name="FRD.docx",
                        generated_date="2026-11-20")
    return contract[0] if isinstance(contract, tuple) else contract


def test_the_contract_carries_the_code_and_where_it_is_stated(tmp_path):
    contract = _contract(tmp_path, _error_table(
        ("9001", "Mandatory field missing (header) - <field name>", "all")))
    feed = contract.feeds[0]
    assert feed.mandatory_error_code == "9001"
    assert "Mandatory field missing (header)" in feed.mandatory_error_source


def test_two_different_codes_are_none_and_flagged(tmp_path):
    contract = _contract(tmp_path, _error_table(("9001", "Mandatory field missing", ""),
                                                ("9003", "Mandatory field missing (detail)", "")))
    assert contract.feeds[0].mandatory_error_code is None
    assert any(f.startswith("frd_mandatory_error_code:") for f in contract.extraction_flags)


def test_unstated_the_json_carries_no_code_field(tmp_path):
    path = tmp_path / "FRD.docx"
    path.write_bytes(fm.build_frd())
    doc, content = resolve_frd(path, CONFIG, use_cache=False, runtime_cache_dir=tmp_path / "rt")
    contract = read_frd(content, doc.profile, CONFIG, document_name="FRD.docx",
                        generated_date="2026-11-20")
    contract = contract[0] if isinstance(contract, tuple) else contract
    assert contract.feeds[0].mandatory_error_code is None
    dumped = contract.model_dump(mode="json", by_alias=True, exclude_defaults=True)
    assert "mandatory_error_code" not in dumped["feeds"][0]
    assert "mandatory_error_source" not in dumped["feeds"][0]


# ------------------------------------------------------------------ the IIG rows

def _mandatory_rows(acfc, spec):  # noqa: F811
    return [r for r in _rows(acfc, DQ, spec) if _v(r, "RULE_CLASS") == "MandatoryColumnCheckRule"]


def _standard_required(spec):
    required = set(spec.not_null_columns)
    return list(dict.fromkeys(f.standard_column for s in spec.segments for f in s.fields
                              if f.standard_column and f.stage_column in required))


def test_the_rule_row_stddelta_on_the_required_fields_standard_columns(acfc, pair4_spec):  # noqa: F811
    config, tpl, feed = acfc
    feed = feed.model_copy(update={"mandatory_error_code": "9001",
                                   "mandatory_error_source": "table 9, row 2: 'Mandatory "
                                                             "field missing'"})
    spec = _with(pair4_spec, rules=[])
    rows = [r for r in _rows((config, tpl, feed), DQ, spec)
            if _v(r, "RULE_CLASS") == "MandatoryColumnCheckRule"]
    assert rows, "one row per standard table holding a required field"
    expected = _standard_required(spec)
    assert expected
    written = [c for r in rows for c in _v(r, "SOURCE_COLUMN").split(",")]
    assert set(written) == set(expected)          # a column two tables share: in each
    for row in rows:
        assert _v(row, "RULE_TYPE") == "STDDelta"
        assert _v(row, "TARGET_COLUMN") == _v(row, "SOURCE_COLUMN")
        assert _v(row, "INPUT_PARAM") == "9001"
        assert row["INPUT_PARAM"]["badge_entry"]["badge"] == "from_frd"
        assert "Mandatory field missing" in row["INPUT_PARAM"]["badge_entry"]["tooltip"]


def test_no_error_code_the_row_is_written_with_the_code_open(acfc, pair4_spec):  # noqa: F811
    _config, _tpl, feed = acfc
    assert feed.mandatory_error_code is None
    rows = _mandatory_rows(acfc, _with(pair4_spec, rules=[]))
    assert rows
    for row in rows:
        cell = row["INPUT_PARAM"]
        assert cell["value"] in ("", None)
        assert cell["badge_entry"]["badge"] == "needs_template"
        assert cell["badge_entry"]["note"].startswith("iig_dq_open:DATA_QUALITY_RULES.INPUT_PARAM")


def test_no_rejection_no_row_and_the_list_keeps_post193s_reason(acfc, pair4_spec):  # noqa: F811
    _config, tpl, _feed = acfc
    spec = _with(pair4_spec, rules=[f"{NULLS}: No Rejection (Load As-IS)"])
    assert _mandatory_rows(acfc, spec) == []
    assert not mandatory_rule_written(spec, tpl)
    for row in _rows(acfc, ADLS, spec):
        assert "No Rejection" in row["MANDATORY_FIELD_LIST"]["badge_entry"]["tooltip"]


def test_no_required_field_no_row_and_no_blanked_list(acfc, pair4_spec):  # noqa: F811
    _config, tpl, _feed = acfc
    spec = _with(pair4_spec, rules=[]).model_copy(update={"not_null_columns": []})
    assert _mandatory_rows(acfc, spec) == []
    assert not mandatory_rule_written(spec, tpl)


def test_the_null_check_suggestion_is_not_made_when_the_rule_covers_it(acfc, pair4_spec):  # noqa: F811
    _config, tpl, _feed = acfc
    spec = _with(pair4_spec, rules=[])
    assert mandatory_rule_written(spec, tpl)
    flags = dq_not_generated_flags(spec, tpl)
    assert not any("required column(s), but no document states a null-check" in f
                   for f in flags)


def test_the_notebook_runs_the_rule_as_a_null_check():
    from codegen.emit.notebook_v2 import RULES

    assert RULES["MandatoryColumnCheckRule"] == "null_check"


def test_a_run_rebuilds_the_feed_from_the_spec_with_the_code(pair4_spec):
    """The real run path: the IIG's FRD feed is rebuilt from the resolved spec
    (metadata_sheet._feed_from_spec) - the code must survive it (the tester pairs' mock
    run left INPUT_PARAM open before this)."""
    from codegen.metadata_sheet import _feed_from_spec

    spec = pair4_spec.model_copy(update={"frd_mandatory_error_code": "9001",
                                         "frd_mandatory_error_source": "table 9, row 2"})
    feed = _feed_from_spec(spec)
    assert (feed.mandatory_error_code, feed.mandatory_error_source) == ("9001", "table 9, row 2")


def test_the_review_copy_does_not_ask_for_the_blanked_list(acfc, pair4_spec):  # noqa: F811
    """As post193's decided blank: the empty MANDATORY_FIELD_LIST is no open cell."""
    from codegen.iig_review import _reason

    config, _tpl, _feed = acfc
    for row in _rows(acfc, ADLS, _with(pair4_spec, rules=[])):
        entry = row["MANDATORY_FIELD_LIST"]["badge_entry"]
        assert entry.get("deliberate_blank") is True
        assert _reason("MANDATORY_FIELD_LIST", "", entry, set(), config.iig_review) is None
