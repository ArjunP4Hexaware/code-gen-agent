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
