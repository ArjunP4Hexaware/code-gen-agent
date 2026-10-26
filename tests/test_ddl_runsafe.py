"""post105 (Soham, 2026-10-26): the acfc_prx DDL is RUN by the engineer, against
tables that may already be deployed — so it must be safe to re-run. Five
``conventions.profiles.acfc_prx`` knobs, on in config/config.yaml, transcribed
from ACFC's production DDL template (the SFMC files,
fixtures/reference/SFMC_{stage,standard}_table_creation.txt):

* ``create_statement: CREATE TABLE IF NOT EXISTS`` (OR REPLACE would empty a
  deployed table) and ``statement_terminator: ";"`` after every statement;
* ``cluster_by``: CLUSTER BY AUTO on both layers (the profile writes no LOCATION);
* ``stage_tblproperties``: the stage set, in prod's order;
* ``domain_tags``: ALTER TABLE ... SET TAGS ('DOMAIN', 'SUBDOMAIN') from the FRD;
  either blank = no tag statement + one ``ddl_tags_blank`` flag.

The pair-1 fixture overlay switches all five off (its golden is CREATE OR
REPLACE, unterminated: tests/test_m4_acceptance.py stays byte-identical).
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.emit.framework import _combined_ddl_text
from codegen.run_artefacts import merge_ddl
from test_derivations import FRD_CATALOG, REPO, _pair11_specs

BANNERS = ("--stage table", "--standard table")


@pytest.fixture(scope="module")
def shipped():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture(scope="module")
def pair11(shipped):
    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    (spec,) = [s for s in specs if s.feed_slug == "vc_disenrollment"]
    flags: list[str] = []
    ddl = _combined_ddl_text(spec, shipped.conventions.get("acfc_prx"), flags, shipped)
    return spec, ddl, flags


def _statements(ddl: str) -> list[str]:
    """Every SQL statement of the text (banner comment lines dropped), split on
    the terminator; the text after the last one must be blank."""
    body = "\n".join(line for line in ddl.split("\n") if not line.startswith("--"))
    *statements, rest = body.split(";")
    assert rest.strip() == "", f"text after the last ';': {rest!r}"
    return [s.strip() for s in statements]


def test_every_statement_is_rerunnable_and_terminated(pair11):
    spec, ddl, _flags = pair11
    assert "OR REPLACE" not in ddl
    statements = _statements(ddl)
    creates = [s for s in statements if s.startswith("CREATE")]
    alters = [s for s in statements if s.startswith("ALTER TABLE")]
    assert len(creates) == len(alters) == 2                       # stage + standard
    assert len(statements) == 4
    assert all(s.startswith("CREATE TABLE IF NOT EXISTS ") for s in creates)
    assert ddl.endswith(";")                                      # the golden's: no final newline


def test_cluster_by_auto_on_both_layers_before_tblproperties(pair11):
    _spec, ddl, _flags = pair11
    for create in [s for s in _statements(ddl) if s.startswith("CREATE")]:
        tail = create.split("\n)\n", 1)[1]
        assert re.search(r"\nCOMMENT '[^\n]*'\nCLUSTER BY AUTO\nTBLPROPERTIES \(\n", tail)


def test_stage_tblproperties_are_prods_stage_set(pair11, shipped):
    _spec, ddl, _flags = pair11
    stage = [s for s in _statements(ddl) if s.startswith("CREATE")][0]
    assert stage.endswith("TBLPROPERTIES (\n"
                          "  'delta.autoOptimize.autoCompact' = 'true',\n"
                          "  'delta.autoOptimize.optimizeWrite' = 'true',\n"
                          "  'delta.minReaderVersion' = '1',\n"
                          "  'delta.minWriterVersion' = '2')")
    reference = (REPO / "fixtures" / "reference" / "SFMC_stage_table_creation.txt")
    if reference.is_file():                                       # transcribed, not invented
        props = shipped.conventions.get("acfc_prx").stage_tblproperties
        text = reference.read_text(encoding="utf-8")
        assert all(f"'{k}' = '{v}'" in text for k, v in props.items())


def test_tags_follow_each_create_from_the_frd_domain(pair11):
    spec, ddl, flags = pair11
    assert spec.domain and spec.sub_domain
    statements = _statements(ddl)
    for create, alter in zip(statements[0::2], statements[1::2], strict=True):
        table = create.split("\n", 1)[0].split()[-1]
        assert alter == (f"ALTER TABLE {table} SET TAGS ('DOMAIN' = '{spec.domain}', "
                         f"'SUBDOMAIN' = '{spec.sub_domain}')")
    assert not [f for f in flags if f.startswith("ddl_tags_blank")]


def test_a_blank_sub_domain_writes_no_tags_and_one_flag(pair11, shipped):
    spec, _ddl, _flags = pair11
    flags: list[str] = []
    ddl = _combined_ddl_text(spec.model_copy(update={"sub_domain": None}),
                             shipped.conventions.get("acfc_prx"), flags, shipped)
    assert "SET TAGS" not in ddl
    (flag,) = [f for f in flags if f.startswith("ddl_tags_blank")]
    assert flag.startswith(f"ddl_tags_blank:{spec.feed_slug} — the FRD states no Sub-Domain;")
    assert len(_statements(ddl)) == 2                             # the two CREATEs, terminated


def test_a_quote_in_the_domain_is_backslash_escaped(pair11, shipped):
    spec, _ddl, _flags = pair11
    ddl = _combined_ddl_text(spec.model_copy(update={"domain": "Member's"}),
                             shipped.conventions.get("acfc_prx"), [], shipped)
    assert "'DOMAIN' = 'Member\\'s'" in ddl


def test_the_combined_set_keeps_each_tag_statement_with_its_create(pair11):
    _spec, ddl, _flags = pair11
    text, skipped, conflicts = merge_ddl([("a", ddl), ("b", ddl)], BANNERS)
    assert skipped == 2 and conflicts == []                       # identical blocks once
    assert text.count("CREATE TABLE IF NOT EXISTS") == text.count("SET TAGS") == 2
    assert len(_statements(text)) == 4


def test_the_pair1_overlay_switches_the_run_safe_knobs_off(pair1_config):
    profile = pair1_config.conventions.get("acfc_prx")
    assert profile.create_statement == "CREATE OR REPLACE TABLE"
    assert profile.statement_terminator == ""
    assert profile.cluster_by is None and profile.stage_tblproperties is None
    assert profile.domain_tags is False
