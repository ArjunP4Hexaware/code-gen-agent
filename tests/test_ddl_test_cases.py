"""post128: the DDL test cases (Nikshit's review, 2026-10-23; Venu, 2026-10-27).

A SEPARATE framework artefact next to the combined DDL - never inside it -
named like the DDL with ``_TestCases`` before the extension. Read-only SQL and
comments the engineer runs after the DDL; every value from the documents, an
unstated one OPEN + a ``ddl_tests_open`` flag; the gate proves read-only.
"""

from __future__ import annotations

import re

import pytest

from codegen import cli
from codegen.emit.ddl_tests import OPEN, ddl_test_cases_name
from codegen.gate.ddl_parse import check_ddl_tests_read_only
from test_m4_acceptance import _scoped


def _run(config, spec, tmp_path):
    gate = cli._generate_feed(spec, _scoped(config, tmp_path), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")
    return gate, tmp_path / "out" / spec.feed_slug / "framework"


@pytest.fixture(scope="module")
def pair4_run(pair4_config, pair4_spec, tmp_path_factory):
    return _run(pair4_config, pair4_spec, tmp_path_factory.mktemp("pair4_tc"))


def _statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.startswith("--"))
    return [s.strip() for s in body.split(";") if s.strip()]


def test_the_name_is_the_ddls_with_the_suffix():
    assert ddl_test_cases_name("ACCUM_DDL.txt", "_TestCases") == "ACCUM_DDL_TestCases.txt"


def test_a_separate_file_next_to_the_ddl_and_nothing_inside_the_ddl(pair4_run):
    gate, framework = pair4_run
    (ddl,) = framework.glob("*_DDL.txt")
    (cases,) = framework.glob("*_TestCases.txt")
    assert cases.name == ddl.name.replace("_DDL.txt", "_DDL_TestCases.txt")
    assert "TC01" not in ddl.read_text(encoding="utf-8")
    checks = {c.name: c for c in gate.checks}
    # the DDL checks never read the test cases; their own check proves read-only
    assert checks["ddl_parses"].passed and checks["sql_literals"].passed
    assert checks["ddl_tests_read_only"].passed
    assert "read-only statement(s) in 1" in checks["ddl_tests_read_only"].details


def test_every_statement_is_read_only(pair4_run):
    _gate, framework = pair4_run
    (cases,) = framework.glob("*_TestCases.txt")
    statements = _statements(cases.read_text(encoding="utf-8"))
    assert statements
    assert all(re.match(r"(SELECT|SHOW) ", s) for s in statements), statements


def test_the_values_come_from_the_documents(pair4_run, pair4_spec):
    _gate, framework = pair4_run
    text = next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8")
    spec = pair4_spec
    assert OPEN not in text
    for pattern in spec.file_name_patterns:
        assert repr(pattern) in text
    assert spec.landing_location in text
    for segment in spec.segments:
        assert segment.stage_table.table in text
        for f in segment.fields:
            assert f"{f.source_column} -> {f.stage_column}" in text
    # Nikshit's six, then the structure checks, each once per table where it applies
    for title in ("File available", "File in the right location", "Column mapping",
                  "Required columns populated", "Column shift",
                  "Columns matched by name or by position?", "Record count",
                  "Primary key unique", "Table exists", "Columns and types match the DDL",
                  "Comments present", "Table properties", "Tags",
                  "The DDL is safe to run again"):
        assert f" {title}" in text, title
    ids = re.findall(r"^-- (TC\d+) ", text, flags=re.M)
    assert ids == [f"TC{n:02d}" for n in range(1, len(ids) + 1)]


def test_an_unstated_value_is_open_and_flagged(pair4_config, pair4_spec, tmp_path):
    spec = pair4_spec.model_copy(update={"landing_location": None})
    gate, framework = _run(pair4_config, spec, tmp_path)
    text = next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8")
    assert f"the landing location: {OPEN}." in text
    assert any(f.startswith("ddl_tests_open:file_location") for f in gate.flags)


def test_no_cases_configured_writes_no_file(pair4_config, pair4_spec, tmp_path):
    profiles = dict(pair4_config.conventions.profiles)
    profiles["acfc_prx"] = profiles["acfc_prx"].model_copy(update={"ddl_test_cases": []})
    config = pair4_config.model_copy(update={"conventions": pair4_config.conventions
                                             .model_copy(update={"profiles": profiles})})
    gate, framework = _run(config, pair4_spec, tmp_path)
    assert not list(framework.glob("*_TestCases.txt"))
    assert "ddl_tests_read_only" not in {c.name for c in gate.checks}


def test_the_same_inputs_write_the_same_bytes(pair4_config, pair4_spec, tmp_path):
    _g, first = _run(pair4_config, pair4_spec, tmp_path / "a")
    _g, second = _run(pair4_config, pair4_spec, tmp_path / "b")
    assert (next(first.glob("*_TestCases.txt")).read_bytes()
            == next(second.glob("*_TestCases.txt")).read_bytes())


def test_the_read_only_check_fails_a_write():
    pytest.importorskip("sqlglot")
    check = check_ddl_tests_read_only(
        [("x_TestCases.txt", "SELECT 1;\nSHOW TBLPROPERTIES a.b.c;\nDROP TABLE a.b.c;")],
        "databricks")
    assert not check.passed and "statement 3 is not read-only (Drop)" in check.details


def test_the_combined_set_carries_every_feeds_cases(tmp_path):
    from codegen import run_stages
    from test_iig_corpus_cells import _generate
    from test_pipeline_name_choice import _pair

    config, _spec, pair = _pair(tmp_path)
    assert _generate(config, pair, only_feed=None) == 0
    out = tmp_path / "out"
    (block,) = run_stages.read_stage_manifest(out)["combined"]
    name = block["files"]["ddl_tests"]
    assert name == config.combined.ddl_test_cases_file_pattern.format(sttm=block["sttm"])
    text = (out / config.combined.dir / name).read_text(encoding="utf-8")
    for feed in block["feeds"]:
        (own,) = (out / feed / "framework").glob("*_TestCases.txt")
        assert own.read_text(encoding="utf-8").rstrip("\n") in text
    log = (out / config.combined.dir / block["files"]["log"]).read_text(encoding="utf-8")
    assert f"`{name}`" in log


def test_a_value_with_a_line_break_never_leaves_its_comment(pair4_config, pair4_spec, tmp_path):
    """The 12-pair check (post128): an STTM source column name spanning two lines
    ("Name\\n(Type)") split a mapping line, its second half outside the comment -
    the file stopped parsing and the gate failed the feed."""
    segments = [s.model_copy(update={"fields": [
        f.model_copy(update={"source_column": f"{f.source_column}\n(two lines)"})
        for f in s.fields]}) for s in pair4_spec.segments]
    spec = pair4_spec.model_copy(update={"segments": segments,
                                         "domain": f"{pair4_spec.domain}\nsecond line"})
    gate, framework = _run(pair4_config, spec, tmp_path)
    text = next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8")
    stray = [line for line in text.splitlines()
             if line and not line.startswith("--") and not re.match(r"(SELECT|SHOW) ", line)]
    assert stray == []
    assert {c.name: c for c in gate.checks}["ddl_tests_read_only"].passed


def _cases(text: str) -> list[tuple[str, list[str]]]:
    """(case id, its statements) per case block."""
    blocks = re.split(r"^-- (TC\d+) ", text, flags=re.M)[1:]
    # each block opens with the rest of its title line
    return [(blocks[i], _statements(blocks[i + 1].partition("\n")[2]))
            for i in range(0, len(blocks), 2)]


def test_every_select_checks_itself(pair4_run):
    """post134: a SELECT returns one row - test_id, result PASS / FAIL (NO DATA on an
    empty table), found, expected - instead of a value the engineer compares by eye."""
    _gate, framework = pair4_run
    cases = _cases(next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8"))
    selects = [(tc, s) for tc, statements in cases for s in statements
               if s.startswith("SELECT ")]
    assert len(selects) > 20
    for tc, statement in selects:
        assert statement.startswith(f"SELECT '{tc}' AS test_id, CASE "), statement
        assert "THEN 'PASS' ELSE 'FAIL' END AS result" in statement, statement
        assert " AS found, " in statement and " AS expected FROM " in statement, statement
    # the data checks say NO DATA on an empty table, never a vacuous PASS
    populated = [s for _tc, s in selects if "required column empty" in s]
    assert populated and all("THEN 'NO DATA'" in s for s in populated)


def test_each_record_count_case_has_its_own_parameter(pair4_run):
    _gate, framework = pair4_run
    cases = _cases(next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8"))
    counted = [(tc, s) for tc, statements in cases for s in statements
               if "AS BIGINT)" in s]
    assert len(counted) == 3                     # pair 4: header / detail / trailer
    for tc, statement in counted:
        assert set(re.findall(r":(\w+)", statement)) == {f"expected_rows_{tc.lower()}"}


def test_the_column_check_lists_the_ddls_columns_in_the_catalogs_spelling(pair4_run):
    _gate, framework = pair4_run
    ddl = next(framework.glob("*_DDL.txt")).read_text(encoding="utf-8")
    text = next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8")
    assert re.search(r"\bCOB_ORDER\s+INT(EGER)?\b", ddl, flags=re.I)   # the standard table
    assert "(13, 'cob_order', 'int')" in text
    assert "(1, 'record_type', 'string')" in text
    assert "full_data_type" in text and "FULL OUTER JOIN VALUES" in text


def test_a_ddl_type_in_the_catalogs_spelling(pair4_config):
    from codegen.emit.ddl_tests import catalog_type

    profile = pair4_config.conventions.profiles["acfc_prx"]
    for ddl_type, spelled in (("INTEGER", "int"), ("Long", "bigint"), ("STRING", "string"),
                              ("DECIMAL(10, 2)", "decimal(10,2)"), ("DECIMAL", "decimal(10,0)"),
                              ("NUMERIC", "decimal(10,0)"), ("dec(5,2)", "decimal(5,2)"),
                              ("VARCHAR(50)", "varchar(50)"), ("TIMESTAMP", "timestamp")):
        assert catalog_type(ddl_type, profile) == spelled, ddl_type


def test_catalog_names_are_compared_in_lower_case(pair4_config):
    """Unity Catalog stores schema and table names in lower case: a DDL naming
    STG.MY_TABLE is found as stg / my_table in information_schema."""
    from codegen.emit.ddl_tests import _schema_case

    profile = pair4_config.conventions.profiles["acfc_prx"]
    table = {"qualified": "D1_DLK.STG_X.MY_TABLE", "parts": ("D1_DLK", "STG_X", "MY_TABLE"),
             "layer": "stage", "columns": [("ID", "INTEGER")], "comment_count": 0,
             "table_comment": None}
    for name in ("table_exists", "columns_match", "table_tags"):
        (statement, _expected), = [(q["statement"], q["expected"])
                                   for q in _schema_case(name, table, ("D", "S"), profile)["sql"]]
        assert "'stg_x'" in statement and "'my_table'" in statement, name
        assert "'STG_X'" not in statement and "'MY_TABLE'" not in statement, name
