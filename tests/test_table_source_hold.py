"""post155: a feed whose FRD states the source is a DATABASE TABLE is table
ingestion - and the table-ingestion (RDMS) sheet is not built. The feed writes
its DDL and DDL test cases (they do not depend on where the rows come from) and
HOLDS the IIG: no IIG, review copy, config rows or metadata inserts - file-
ingestion rows for a table source would be values no document gives. One flag,
a HELD BACK line, one NOTE line and a non-blocking open item say so: the run reads
PASS_WITH_OPEN_INPUTS, never PASS. Synthetic pair (pair_11 shape); the table-source
vocabulary is pointed at its stated file format by an overlay.
"""

from __future__ import annotations

import json

from codegen import run_stages
from test_iig_corpus_cells import _generate
from test_pipeline_name_choice import _pair

IIG_SIDE = ("_IIG.xlsx", "_IIG_REVIEW.xlsx", "config_rows.xlsx", "config_inserts.xlsx",
            "metadata_inserts.sql")


# the pair's three feeds state csv, csv and psv - every one is pointed at here
FORMATS = ["csv", "psv"]


def _held_run(tmp_path, capsys):
    overlay = tmp_path / "table_source.yaml"
    overlay.write_text("framework:\n  table_source_formats: " + json.dumps(FORMATS) + "\n",
                       encoding="utf-8")
    config, spec, pair = _pair(tmp_path / "held", overlay)
    capsys.readouterr()
    exit_code = _generate(config, pair, only_feed=None)
    return config, spec, tmp_path / "held" / "out", exit_code, capsys.readouterr().out


def test_a_table_source_writes_its_ddl_and_holds_the_iig(tmp_path, capsys):
    _config, spec, out, exit_code, printed = _held_run(tmp_path, capsys)
    framework = out / spec.feed_slug / "framework"
    names = sorted(p.name for p in framework.iterdir())
    assert any(n.endswith("_DDL.txt") for n in names)
    assert any(n.endswith("_DDL_TestCases.txt") for n in names)
    assert not [n for n in names if n.endswith(IIG_SIDE)], names
    addition = (framework / "ADDITION.md").read_text(encoding="utf-8")
    assert "**HELD BACK**" in addition and "table ingestion (the RDMS sheet)" in addition
    # the run says it once, and it is open - exit 0, never a clean PASS
    assert exit_code == 0
    assert "iig_held" in printed and "NOTE" in printed
    manifest = run_stages.read_stage_manifest(out)
    assert run_stages.pair_outcome({"generate": exit_code}, out) == "PASS_WITH_OPEN_INPUTS"
    held = [q for q in manifest["questions"] if q["key"].endswith(".iig_held")]
    assert held and not any(q["blocking"] for q in held)


def test_no_iig_input_is_asked_for_a_held_feed(tmp_path, capsys):
    """The IIG is not written, so its inputs (containers, landing, LOB, key) are
    never owed - the one open line is the hold."""
    _config, _spec, out, _exit, _printed = _held_run(tmp_path, capsys)
    feed_lines = [q for q in run_stages.read_stage_manifest(out)["questions"]
                  if q.get("scope") == "feed"]
    assert {q["key"].rsplit(".", 1)[-1] for q in feed_lines} == {"iig_held"}


def test_the_combined_set_carries_no_iig_for_a_held_feed(tmp_path, capsys):
    config, _spec, out, _exit, _printed = _held_run(tmp_path, capsys)
    (block,) = run_stages.read_stage_manifest(out)["combined"]
    assert "iig" not in block["files"] and "review" not in block["files"]
    assert "ddl" in block["files"] and "ddl_tests" in block["files"]


def test_the_hold_names_the_stated_format(tmp_path, capsys):
    """ADDITION.md says WHY - the FRD's own file format, as stated."""
    _config, spec, out, _exit, printed = _held_run(tmp_path, capsys)
    addition = (out / spec.feed_slug / "framework" / "ADDITION.md").read_text(encoding="utf-8")
    assert f"(file format {spec.file_format!r})" in addition
    assert f"(file format {spec.file_format!r})" in printed


def test_a_table_sources_test_cases_speak_of_loads_not_files(tmp_path, capsys):
    """post156: no file, so no file cases - a source table that has rows, test loads,
    a second load; never 'a file matching', the landing location or several files."""
    import re

    _config, spec, out, _exit, _printed = _held_run(tmp_path, capsys)
    text = next((out / spec.feed_slug / "framework").glob("*_TestCases.txt")).read_text(
        encoding="utf-8")
    titles = re.findall(r"^-- TC\d+ (.+)$", text, flags=re.M)
    assert "Source table available" in titles and "A second load" in titles
    for gone in ("File available", "File in the right location", "Several files at once",
                 "A second sample file", "Columns matched by name or by position?"):
        assert gone not in titles
    assert not any(t.startswith("Column shift") for t in titles)
    assert "load a test file" not in text and "run a test load" in text
