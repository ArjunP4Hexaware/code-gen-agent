"""post190: the notebook-mode notebook against the Code Review agent's exact rules
(the next agent in the pipeline; Soham, 2026-11-10: "I don't want the handoff to have
known issues that I could just deal with here"). On the synthetic pair 4.

NM-001  the file name follows the Naming Standards pattern (option 1: + the source),
        every part from the FRD; an open part keeps the feed's name, flagged; a name
        over the standard's 30 characters is written and flagged
NB-001  the first cell states the purpose, the business owner(s) and the dependencies
NB-003  every code cell carries a title (DBTITLE in the .py, cell metadata in .ipynb)
PY-001  logging, never print()
PY-003  every Python line <= 79 characters, a comment <= 72 (a long IIG value is
        split into adjacent literals - the same value)
PS-009 / EFF-004 / EFF-012  no Spark action and no withColumn inside a loop; a frame
        written and counted is cached first
"""

from __future__ import annotations

import ast
import json
import re

import pytest

from codegen import cli
from codegen.emit import notebook_files as nbf
from codegen.emit.notebook_v2 import _block, _split_string, with_review
from test_m4_acceptance import _scoped


@pytest.fixture(scope="module")
def pair4_nb(pair4_config, pair4_spec, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("nb_cr")
    cli._generate_feed(pair4_spec, _scoped(pair4_config, tmp), dry_run=True, skip_tests=True,
                       output_mode="notebook", conventions_profile="acfc_prx",
                       iig_template="iig_v2")
    (ipynb,) = (tmp / "out").rglob("*.ipynb")
    return ipynb, ipynb.with_suffix(".py")


def _code_cells(ipynb) -> list[dict]:
    return [c for c in json.loads(ipynb.read_text(encoding="utf-8"))["cells"]
            if c["cell_type"] == "code"]


def test_every_python_line_fits_the_width(pair4_nb):
    _ipynb, source = pair4_nb
    long = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith(("# MAGIC", "# DBTITLE", "# Databricks notebook source")):
            continue
        limit = 72 if line.strip().startswith("#") else 79
        if len(line) > limit:
            long.append((number, len(line)))
    assert long == []


def test_every_code_cell_has_a_title_in_both_files(pair4_nb):
    ipynb, source = pair4_nb
    cells = _code_cells(ipynb)
    titles = [c["metadata"].get(nbf.TITLE_KEY, {}).get("title") for c in cells]
    assert all(titles), titles
    text = source.read_text(encoding="utf-8")
    assert text.count(nbf.DBTITLE) == len(cells)
    for block in text.split(nbf.COMMAND)[1:]:
        first = block.strip().splitlines()[0]
        assert first.startswith((nbf.DBTITLE, nbf.MAGIC)), first


def test_the_header_cell_states_purpose_owners_and_dependencies(pair4_nb):
    ipynb, _source = pair4_nb
    first = json.loads(ipynb.read_text(encoding="utf-8"))["cells"][0]
    assert first["cell_type"] == "markdown"
    header = "".join(first["source"])
    assert re.search(r"\*\*Purpose:\*\*", header)
    assert re.search(r"\*\*Business owner\(s\) / consumer\(s\):\*\* not stated", header)
    assert re.search(r"\*\*Dependencies:\*\*\n- source files `", header)


def test_no_print_no_action_or_withcolumn_in_a_loop(pair4_nb):
    ipynb, _source = pair4_nb
    for cell in _code_cells(ipynb):
        tree = ast.parse("".join(cell["source"]))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        assert not [c for c in calls if getattr(c.func, "id", None) == "print"], cell["id"]
        for loop in (n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))):
            inner = {getattr(n.func, "attr", None) for stmt in loop.body
                     for n in ast.walk(stmt) if isinstance(n, ast.Call)}
            assert not inner & {"count", "collect", "first", "withColumn",
                                "unionByName"}, \
                (cell["id"], inner)


def test_no_inline_sql_string(pair4_nb):
    ipynb, _source = pair4_nb
    for cell in _code_cells(ipynb):
        for node in ast.walk(ast.parse("".join(cell["source"]))):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "sql":
                assert not isinstance(node.args[0], (ast.Constant, ast.JoinedStr)), cell["id"]


def test_a_long_pair_in_a_list_is_broken_over_lines():
    pairs = [("a_long_source_column_name_number_one", "a_long_stage_column_name_one"),
             ("x", "y")]
    rendered = _block({"src_columns": pairs}, 8)
    assert all(len(line) <= 79 for line in rendered.splitlines())
    assert ast.literal_eval(rendered) == {"src_columns": pairs}


def test_a_frame_written_then_counted_is_cached_first(pair4_nb):
    ipynb, _source = pair4_nb
    code = "\n".join("".join(c["source"]) for c in _code_cells(ipynb))
    assert re.search(r"rejected = rejected\.drop\(\"_recycled_at\"\)\.cache\(\)", code)
    assert "cached = [frame.cache() for frame in frames.values()]" in code
    assert "frame.unpersist()" in code


@pytest.mark.parametrize("value", [
    "/membership/cob/northwind_benefits/reject/nb_cob_report_dtl_reject_with_a_long_tail",
    "x" * 200,
    'a "quoted" path/' * 9,
])
def test_a_long_value_is_split_into_literals_with_the_same_value(value):
    rendered = _block({"reject_path": value, "short": "s"}, 8)
    assert all(len(line) <= 79 for line in rendered.splitlines())
    assert ast.literal_eval(rendered) == {"reject_path": value, "short": "s"}
    assert ast.literal_eval(_split_string(value, 12)) == value


# NM-001 -------------------------------------------------------------------------
def _named(pair4_config, spec, **codes):
    from codegen.emit.context import resolve_notebook_file_name

    return resolve_notebook_file_name(spec.model_copy(update=codes), pair4_config)


def test_the_notebook_name_follows_the_standard_when_every_part_is_stated(pair4_config,
                                                                         pair4_spec):
    name, flags = _named(pair4_config, pair4_spec, product_code="DLK",
                         sub_product_code="NSP")
    assert name.startswith("NB_DLK_NSP_") and name.endswith("_INGEST")
    assert flags[0].startswith(f"notebook_name_from_standard:{name}")
    assert (len(name) > 30) == any(f.startswith("notebook_name_too_long:") for f in flags)


def test_an_open_part_keeps_the_feed_name_flagged(pair4_config, pair4_spec):
    name, flags = _named(pair4_config, pair4_spec, product_code=None)
    assert name == pair4_spec.feed_slug
    (flag,) = flags
    assert flag.startswith(f"notebook_name_open:{pair4_spec.feed_slug}") and "product" in flag


def test_the_review_rewrite_finds_a_standard_named_notebook_and_keeps_titles(tmp_path):
    cells = [nbf.md("title", "# t"), nbf.code("run", "x = 1", "Run")]
    folder = tmp_path / "notebook"
    folder.mkdir()
    (folder / "NB_DLK_NSP_X_Y_Z_INGEST.ipynb").write_text(nbf.ipynb_text(cells),
                                                          encoding="utf-8")
    (folder / "NB_DLK_NSP_X_Y_Z_INGEST.py").write_text(nbf.databricks_source(cells),
                                                       encoding="utf-8")
    written = with_review(tmp_path, "feed_slug", [])
    assert [p.name for p in written] == ["NB_DLK_NSP_X_Y_Z_INGEST.ipynb",
                                         "NB_DLK_NSP_X_Y_Z_INGEST.py"]
    assert f"{nbf.DBTITLE}Run" in written[1].read_text(encoding="utf-8")


# the recycle + shared-segment paths pair 4 does not take: the templates rendered alone
@pytest.mark.parametrize(("template", "context"), [
    ("run.py.j2", {"drift": False, "fixed_width": True, "recycle": True}),
    ("recycle.py.j2", {}),
])
def test_the_recycle_and_shared_segment_paths_pass_the_rules(template, context):
    from codegen.emit.notebook_v2 import _environment

    text = _environment().get_template(template).render(**context)
    tree = ast.parse(text)
    for loop in (n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))):
        inner = {getattr(n.func, "attr", None) for stmt in loop.body
                 for n in ast.walk(stmt) if isinstance(n, ast.Call)}
        assert not inner & {"count", "collect", "first", "withColumn", "unionByName"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "sql":
            assert not isinstance(node.args[0], (ast.Constant, ast.JoinedStr))
    if context.get("recycle"):
        assert "backlog.unpersist()" in text
