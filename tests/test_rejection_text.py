"""Audit #9 (medium list, 2026-10-26; post133): a rejection carries coordinates,
never text a model invented or a document cell holds.

Rejections go to the state role's rejection log (promised: "no workbook cell and
no model string is stored"), the run's REJECTED lines, ``layout_rejected:``
flags and the ``--report-unresolved`` file ("structural labels only"). Before:
a sheet the model invented was named, a label cell and the model's label were
quoted (STTM meta rows, FRD fields), a data cell was quoted when the claimed
header row was a data row, the model's section / inline label were quoted, and
an FRD claim under a path nobody asked about was merged and then quoted. Each
case below plants a marker the reason must not contain.
"""

from __future__ import annotations

import os
from pathlib import Path

import openpyxl
import pytest

from codegen.config import load_config
from codegen.extract.frd_docx import discover_frd, read_docx
from codegen.layout import resolve as rs
from codegen.layout.frd_profile import FrdUnresolved

REPO = Path(__file__).resolve().parents[1]
FRD = REPO / "fixtures" / "acfc_shapes" / "frd"
MODEL = "SYN_MODEL_TEXT_7Q"


@pytest.fixture(scope="module")
def config():
    os.environ.setdefault("CODEGEN_SKIP_ENV_OVERLAY", "1")
    return load_config(REPO / "config" / "config.yaml")


def _frd(config):
    content = read_docx(FRD / "f1_pair_1.docx", prose_ok=True)
    return content, discover_frd(content, config.extractor.frd)


def _model_claims(content, profile, config, target, update, extra=None):
    source = profile.fields[target]
    left = profile.model_copy(update={
        "fields": {k: v for k, v in profile.fields.items() if k != target},
        "unresolved": [*profile.unresolved, FrdUnresolved(field=target, reason="t")]})
    claims = {target: {**source.model_dump(mode="json"), **update}, **(extra or {})}
    merged = rs._merge_frd(left, claims, "model", 0.8,
                           allowed={u.field for u in left.unresolved})
    return rs._validate_frd(merged.model_copy(update={"source": "model"}), content, config,
                            {"model"})


def _texts(rejections) -> str:
    return " | ".join(r.render() for r in rejections)


def test_an_frd_label_mismatch_quotes_neither_the_cell_nor_the_model(config):
    content, profile = _frd(config)
    target = "feeds[0].frequency"
    cell = profile.fields[target].label
    _p, rejections = _model_claims(content, profile, config, target, {"label": MODEL})
    assert [r.role for r in rejections] == [target]
    text = _texts(rejections)
    assert MODEL not in text and cell not in text
    assert "table" in text and "row" in text and "col" in text          # coordinates


def test_a_model_section_and_inline_label_are_never_quoted(config):
    content, profile = _frd(config)
    target = "feeds[0].frequency"
    _p, rejections = _model_claims(content, profile, config, target, {"section": MODEL})
    assert rejections and MODEL not in _texts(rejections)
    _p, rejections = _model_claims(content, profile, config, target, {"inline_label": MODEL})
    assert rejections and MODEL not in _texts(rejections)


def test_a_model_claim_for_a_field_not_asked_is_dropped_unquoted(config):
    content, profile = _frd(config)
    target = "feeds[0].frequency"
    invented = f"feeds[0].{MODEL.lower()}"
    extra = {invented: profile.fields[target].model_dump(mode="json")}
    validated, rejections = _model_claims(content, profile, config, target, {}, extra)
    assert invented not in validated.fields
    assert MODEL.lower() not in _texts(rejections)


def _sttm(tmp_path: Path) -> openpyxl.Workbook:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SYN_MAPPING"
    ws.append(["File Name", "SYN_SECRET_META_VALUE"])
    ws.append(["Source Field", "Source Type", "Stage Column", "Stage Type"])
    ws.append([123456, "String", "A", "STRING"])
    return wb


def test_sttm_rejections_name_no_invented_sheet_no_label_and_no_cell(config, tmp_path):
    from codegen.layout.profile import BandProfile, LayoutProfile, MetaRow, SheetProfile
    from codegen.layout.validate import validate_profile

    wb = _sttm(tmp_path)
    profile = LayoutProfile(
        fingerprint="f" * 16, source="model", strategy="syn", sheets=[
            SheetProfile(name=MODEL, kind="mapping", header_row=2, bands=[]),
            SheetProfile(name="SYN_MAPPING", kind="mapping", header_row=3,
                         meta_rows=[MetaRow(row=1, col=1, value_col=2, key="file_name",
                                            label=MODEL)],
                         bands=[BandProfile(layer="source", col_start=1, col_end=2,
                                            roles={"field_name": 1})])])
    _profile, rejections = validate_profile(profile, wb, config.extractor,
                                           check_sources={"model"})
    text = _texts(rejections)
    assert rejections
    assert MODEL not in text
    assert "123456" not in text and "SYN_SECRET_META_VALUE" not in text and "File Name" not in text
