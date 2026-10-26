"""codegen.gate.ddl_parse (2026-10-26): the engineer RUNS the DDL, so every emitted
DDL file must parse under sqlglot's databricks dialect — the acfc_prx run-safe
shape, the pair-1 golden's bare shape and edo_sfmc's two files alike."""

from __future__ import annotations

import builtins
import tempfile
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.emit.framework import _combined_ddl_text
from codegen.gate.ddl_parse import SQLGLOT_UNAVAILABLE, check_ddl_parses
from test_derivations import FRD_CATALOG, REPO, _pair11_specs
from test_m4_acceptance import GOLDEN_DDL, needs_golden

SFMC = [REPO / "fixtures" / "reference" / f"SFMC_{layer}_table_creation.txt"
        for layer in ("stage", "standard")]


@pytest.fixture(scope="module")
def shipped():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture(scope="module")
def pair11_ddl(shipped):
    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    return _combined_ddl_text(specs[0], shipped.conventions.get("acfc_prx"), [], shipped)


def test_the_shipped_gate_parses_under_databricks(shipped):
    assert shipped.gate.ddl_parse_dialect == "databricks"


def test_the_run_safe_ddl_parses(pair11_ddl):
    check = check_ddl_parses([("VC_DDL.txt", pair11_ddl)], "databricks")
    assert check.passed and not check.not_run
    assert check.details.startswith("4 statement(s) in 1 DDL file(s) parse")


@needs_golden
def test_the_pair1_golden_is_not_runnable_as_one_script_so_its_overlay_skips_the_gate(
        pair1_config):
    # its two CREATEs carry no ';' - one statement sqlglot cannot recognise
    check = check_ddl_parses([("ACCUM_DDL.txt", GOLDEN_DDL.read_text(encoding="utf-8"))],
                             "databricks")
    assert not check.passed and "statement 1 not recognised" in check.details
    assert pair1_config.gate.ddl_parse_dialect is None


def test_the_sfmc_reference_files_parse_but_are_not_run_safe():
    # they parse; their only finding is the CREATE OR REPLACE (post112), the very
    # form the agent no longer copies from them
    files = [(p.name, p.read_text(encoding="utf-8")) for p in SFMC if p.is_file()]
    if not files:
        pytest.skip("SFMC reference DDLs absent")
    check = check_ddl_parses(files, "databricks")
    problems = check.details.split("; ")
    assert not check.passed and len(problems) == len(files)
    assert all("statement 1 is CREATE OR REPLACE" in p for p in problems)


@pytest.mark.parametrize("break_it", [
    lambda t: t.replace("TBLPROPERTIES (", "TBLPROPERTIES ((", 1),     # parse error
    lambda t: t.replace("\n)\n", "\n", 1),                              # unclosed column list
    lambda t: t + "\n\nGRANT ALL ON THE TABLE;",                         # not a statement
])
def test_broken_ddl_fails_naming_the_file(pair11_ddl, break_it):
    check = check_ddl_parses([("VC_DDL.txt", break_it(pair11_ddl))], "databricks")
    assert not check.passed
    assert check.details.startswith("VC_DDL.txt: ")


def test_without_sqlglot_it_is_a_flag_never_a_fail(pair11_ddl, monkeypatch):
    real_import = builtins.__import__

    def no_sqlglot(name, *args, **kwargs):
        if name.startswith("sqlglot"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_sqlglot)
    check = check_ddl_parses([("VC_DDL.txt", pair11_ddl)], "databricks")
    assert check.passed and check.not_run and check.flag == SQLGLOT_UNAVAILABLE


def test_create_or_replace_fails_the_gate(pair11_ddl):
    # post112 (codeflow audit #15): the run-safe rule, enforced
    unsafe = pair11_ddl.replace("CREATE TABLE IF NOT EXISTS", "CREATE OR REPLACE TABLE", 1)
    check = check_ddl_parses([("VC_DDL.txt", unsafe)], "databricks")
    assert not check.passed
    assert "statement 1 is CREATE OR REPLACE" in check.details


# -- post122: the identifier rule, as a gate check -------------------------------- #


def _definitions(shipped, spec):
    from codegen.emit.framework import table_definitions

    return table_definitions(spec, shipped.conventions.get("acfc_prx"), [], shipped)


def test_plain_identifiers_pass(shipped):
    from codegen.gate.ddl_names import check_ddl_identifiers

    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    check = check_ddl_identifiers(_definitions(shipped, specs[0]))
    assert check.passed and check.name == "ddl_identifiers"


def test_a_column_name_with_a_space_fails_naming_table_layer_and_position(shipped):
    # the live pair_11 case (2026-10-26): an STTM Standard-band column name with a
    # stray space ("Word _Word") - sqlglot only said "Expecting )", the old text
    # scan read it as its first word and passed it
    from codegen.gate.ddl_names import check_ddl_identifiers, ddl_column_identifiers

    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    spec = specs[0]
    segment = spec.segments[0]
    bad = segment.fields[1].model_copy(update={"standard_column": "SYN_MEMBER _NAME"})
    spec = spec.model_copy(update={"segments": [
        segment.model_copy(update={"fields": [segment.fields[0], bad, *segment.fields[2:]]}),
        *spec.segments[1:]]})
    check = check_ddl_identifiers(_definitions(shipped, spec))
    assert not check.passed and check.violations == {"ddl_identifier": 1}
    assert "standard table" in check.details and "column 2 'SYN_MEMBER _NAME'" in check.details
    ddl = _combined_ddl_text(spec, shipped.conventions.get("acfc_prx"), [], shipped)
    assert "SYN_MEMBER" in ddl_column_identifiers(ddl)            # the old scan: passed
    assert not check_ddl_parses([("x_DDL.txt", ddl)], "databricks").passed
