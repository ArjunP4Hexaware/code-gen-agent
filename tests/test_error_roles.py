"""post57 (D1 post55 pairs 05 / 06): an extraction error line said "STTM
required element missing" / "STTM audit column invalid" and nothing of WHAT.
The coordinates tier now names the header ROLE (template vocabulary) and the
type KEYWORD of the cell (framework type vocabulary) — both allowlists, so a
cell's text still never reaches the line:

    FAIL            extract-sttm — STTM audit column invalid (role audit_column;
                    type tinyint) at STTM sheet 2 row 19 [ExtractionError]"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.contracts.sttm import AUDIT_DATATYPE_SPELLING
from codegen.emit.context import _SQL_TYPES
from codegen.layout.profile import Role
from codegen.run_errors import (
    OTHER_TYPE,
    ROLE_WORDS,
    TYPE_KEYWORDS,
    Coord,
    coordinate_line,
    error_marker,
    first_error_line,
    first_error_line_full,
    located,
    role_word,
    type_keyword,
)
from post51_pairs import AUDIT, family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
SENTINEL = "ZZSECRETTYPE"


def test_the_vocabularies_cover_the_template_and_the_framework():
    assert {r.value for r in Role} <= ROLE_WORDS
    assert set(_SQL_TYPES) | set(AUDIT_DATATYPE_SPELLING) | {"decimal"} <= TYPE_KEYWORDS


@pytest.mark.parametrize(("label", "role"), [
    ("stage DataType", "target_type"), ("standard ColumnName", "column"),
    ("stage TableName", "table"), ("source column", "source_column"),
    ("field_name", "field_name"), ("files", "file_pattern"), ("Mapping - Daily", None),
    (SENTINEL, None),
])
def test_role_words(label, role):
    assert role_word(label) == role


@pytest.mark.parametrize(("text", "keyword"), [
    ("Decimal(17,2)", "decimal"), ("TinyInt", "tinyint"), ("varchar(20)", "varchar"),
    ("timestamp", "timestamp"), (SENTINEL, OTHER_TYPE), ("", None), ("(12)", OTHER_TYPE),
])
def test_type_keywords(text, keyword):
    assert type_keyword(text) == keyword


def test_the_line_names_role_and_type_and_drops_anything_else():
    exc = located(ValueError(f"audit column has datatype {SENTINEL!r}"),
                  Coord("STTM", sheet=2, row=19), "sttm.audit", role="audit_column",
                  type_text=SENTINEL)
    line = coordinate_line(json.loads(
        error_marker("extract-sttm", "sttm.audit", exc=exc)[len("CODEGEN-ERROR "):]))
    assert line == (f"{'FAIL':<15} extract-sttm — STTM audit column invalid (role audit_column; "
                    "type other) at STTM sheet 2 row 19 [ValueError]")
    # a forged marker cannot smuggle text through role / type
    forged = coordinate_line({"stage": "extract-sttm", "reason": "sttm.missing",
                              "role": SENTINEL, "type": SENTINEL})
    assert forged == f"{'FAIL':<15} extract-sttm — STTM required element missing"
    missing = located(ValueError("x"), Coord("STTM", sheet=3, row=11), "sttm.missing",
                      role="stage DataType")
    assert "STTM required element missing (role target_type) at STTM sheet 3 row 11" in \
        coordinate_line(json.loads(
            error_marker("extract-sttm", "sttm.missing", exc=missing)[len("CODEGEN-ERROR "):]))


def _extract(tmp_path: Path, audit: list[tuple[str, str]]) -> subprocess.CompletedProcess:
    workbook = family_e_workbook(tmp_path / "p6.xlsx", [None], audit=audit)
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    return subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(family_e_frd(tmp_path / "frd.json")),
         "--out", str(tmp_path / "sttm.json"), "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)


@pytest.mark.parametrize(("raw", "keyword"), [("tinyint", "tinyint"), (SENTINEL, "other")])
def test_the_pair06_shape_names_the_role_and_the_type_keyword(tmp_path, raw, keyword):
    done = _extract(tmp_path, AUDIT + [("LOAD_ID", raw)])
    assert done.returncode == 1
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert line.startswith(f"{'FAIL':<15} extract-sttm — STTM audit column invalid "
                           f"(role audit_column; type {keyword}) at STTM sheet ")
    assert SENTINEL not in line and "LOAD_ID" not in line
    assert "LOAD_ID" in first_error_line_full(done.returncode, done.stderr, done.stdout)
