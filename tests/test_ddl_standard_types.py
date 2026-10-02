"""acfc_prx standard-layer typing: with ``standard_from_stage`` the standard
table takes the stage column LIST and ORDER, but each column's TYPE from the
STTM standard band.

Pair 11 (``fixtures/acfc_shapes/sttm/pair_11_family_b.xlsx``), sheet
``MAPPING-VC_DISENROLLMENT``: stage band DataType in column L, standard band
DataType in column P.

* RISK_SCORE — L5 ``String``, P5 ``Decimal(18,4)`` -> standard DECIMAL(18,4)
* REPORT_DT  — L7 ``String``, P7 ``Date``          -> standard DATE

Before the fix the standard block copied the stage types (both ``String``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli
from codegen.config import load_config
from test_derivations import FRD_CATALOG, REPO, _pair11_specs, _scoped


def _block(ddl: str, banner: str) -> list[str]:
    start = ddl.index(banner)
    end = ddl.find("--", start + len(banner))
    return [line.strip().rstrip(",") for line in ddl[start:end if end != -1 else None].splitlines()]


@pytest.fixture(scope="module")
def disenrollment(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("std_types")
    config = load_config(REPO / "config" / "config.yaml")
    specs, _ = _pair11_specs(FRD_CATALOG, tmp, config)
    (spec,) = [s for s in specs if s.feed_slug == "vc_disenrollment"]
    gate = cli._generate_feed(spec, _scoped(config, tmp), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")
    ddl = (tmp / "out" / spec.feed_slug / "framework" / "VC_DISENROLLMENT_DDL.txt"
           ).read_text(encoding="utf-8")
    return ddl, gate


def test_standard_types_come_from_the_sttm_standard_band(disenrollment):
    ddl, _gate = disenrollment
    standard = _block(ddl, "--standard table")
    assert "REPORT_DT DATE" in standard                 # P7 'Date'
    assert "RISK_SCORE DECIMAL(18,4)" in standard       # P5 'Decimal(18,4)'


def test_stage_types_and_the_column_order_are_unchanged(disenrollment):
    ddl, _gate = disenrollment
    stage, standard = _block(ddl, "--stage table"), _block(ddl, "--standard table")
    assert "REPORT_DT String" in stage and "RISK_SCORE String" in stage   # L7 / L5
    names = lambda block: [line.split()[0] for line in block   # noqa: E731
                           if line and line.split()[0].isupper() and " " in line
                           and not line.startswith("CREATE")]
    assert names(stage) == names(standard)


def test_matching_types_keep_the_stage_text_and_raise_no_flag(disenrollment):
    ddl, gate = disenrollment
    standard = _block(ddl, "--standard table")
    assert "MEMBER_ID String" in standard               # stage and standard both 'String'
    assert not any(f.startswith(("standard_type_blank:", "standard_type_unmapped:"))
                   for f in gate.flags)


def _field(stage_type: str, standard: str | None):
    from types import SimpleNamespace

    return SimpleNamespace(stage_column="COL_X", standard_datatype=standard,
                           provenance=SimpleNamespace(sheet="MAPPING-X", row=9),
                           stage_datatype=stage_type)


def test_a_blank_standard_type_falls_back_to_stage_and_is_flagged():
    from codegen.emit.framework import _standard_from_stage_type

    flags: list[str] = []
    assert _standard_from_stage_type(_field("String", "  "), "String", flags) == "String"
    (flag,) = flags
    assert flag.startswith("standard_type_blank:COL_X") and "MAPPING-X row 9" in flag


def test_an_unmappable_standard_type_is_flagged_and_not_guessed():
    from codegen.emit.framework import _standard_from_stage_type

    flags: list[str] = []
    assert _standard_from_stage_type(_field("String", "Blobby"), "String", flags) == "Blobby"
    (flag,) = flags
    assert flag.startswith("standard_type_unmapped:COL_X") and "'Blobby'" in flag
    assert "MAPPING-X row 9" in flag


def test_pair_files_exist():
    assert Path(REPO / "fixtures" / "acfc_shapes" / "sttm" / "pair_11_family_b.xlsx").is_file()
