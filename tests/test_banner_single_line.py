"""post159 (P1-4 / P2-9, pentest CS-2): document text can never leave its comment.

A banner-bound value (FRD ``contract_name`` / ``feed_name`` / ``source_system``,
STTM ``contract_name`` / trailer marker) holding a line break used to end the
``#`` banner of every generated module and .ipynb cell - and the ``--`` lines of
the DDL files - so the rest of the value became generated code, caught only by
ruff F404 (and shipped PASS_WITH_FLAGS where ruff is missing). Three layers now:

1. the contract refuses it (``contracts.frd.BannerText``; the .docx reader as a
   located ``frd.value`` error naming the cell by position);
2. behind it, every template puts document text in a comment through
   ``|comment1`` (one line, byte-identical for a clean value);
3. behind that, the ``python_compiles`` gate check compiles every generated
   ``.py`` and notebook code cell - a break FAILs the feed without ruff.

P2-9: the DDL test-cases file is checked line by line (every line a ``--``
comment or one whole read-only statement), with or without sqlglot.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from codegen import cli
from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract
from codegen.gate import preflight
from codegen.gate.ddl_parse import check_ddl_tests_read_only
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]
_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
_DOCX = REPO / "fixtures" / "acfc_shapes" / "frd" / "f1_pair_2_variant.docx"
PAYLOAD = "\nX = 1"
BREAKS = ["\n", "\r", "\r\n", "\x0b", "\x0c", "\x85", " ", "\t", "\x00"]

needs_demo_pair = pytest.mark.skipif(not (_FRD.is_file() and _STTM.is_file()),
                                     reason="demo fixture pair not present")


def _frd_json() -> dict:
    return json.loads(_FRD.read_text(encoding="utf-8"))


# ------------------------------------------------------------- 1. the contract


@needs_demo_pair
@pytest.mark.parametrize("brk", BREAKS)
def test_a_contract_name_with_a_line_break_is_a_contract_error(brk):
    data = _frd_json()
    data["contract_name"] = data["contract_name"] + brk + "X = 1"
    with pytest.raises(ValidationError) as caught:
        FrdContract.model_validate(data)
    (error,) = caught.value.errors()
    assert error["loc"] == ("contract_name",)
    assert "one printable line" in error["msg"]


@needs_demo_pair
@pytest.mark.parametrize("field", ["feed_name", "source_system"])
def test_a_feed_field_with_a_line_break_is_a_contract_error(field):
    data = _frd_json()
    data["feeds"][0][field] = data["feeds"][0][field] + PAYLOAD
    with pytest.raises(ValidationError) as caught:
        FrdContract.model_validate(data)
    assert [e["loc"] for e in caught.value.errors()] == [("feeds", 0, field)]


@needs_demo_pair
def test_the_sttm_contract_name_is_one_line_too():
    data = json.loads(_STTM.read_text(encoding="utf-8"))
    data["contract_name"] += PAYLOAD
    with pytest.raises(ValidationError) as caught:
        SttmContract.model_validate(data)
    assert [e["loc"] for e in caught.value.errors()] == [("contract_name",)]


@needs_demo_pair
def test_the_generate_path_refuses_the_pair(tmp_path, config):
    data = _frd_json()
    data["contract_name"] += PAYLOAD
    frd = tmp_path / "frd.contract.json"
    frd.write_text(json.dumps(data), encoding="utf-8")
    # a ValueError: the CLI's resolve step turns it into a contract.invalid FAIL
    with pytest.raises(ValueError, match="one printable line"):
        resolve_pair(frd, _STTM, config)


@needs_demo_pair
def test_clean_values_still_load_unchanged():
    data = _frd_json()
    contract = FrdContract.model_validate(data)
    assert contract.contract_name == data["contract_name"]
    # a non-breaking space or a doubled space is one printable line: kept as is
    data["feeds"][0]["feed_name"] = "A B  C"
    assert FrdContract.model_validate(data).feeds[0].feed_name == "A B  C"


def _docx_with(tmp_path: Path, old: str, new: str) -> Path:
    out = tmp_path / _DOCX.name
    with zipfile.ZipFile(_DOCX) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/document.xml":
                text = data.decode("utf-8")
                assert f">{old}<" in text
                data = text.replace(f">{old}<", f">{new}<").encode("utf-8")
            dst.writestr(item, data)
    return out


@pytest.mark.skipif(not _DOCX.is_file(), reason="F1 fixture absent")
def test_the_docx_reader_names_the_cell_of_a_carriage_return(tmp_path, config):
    """A ``&#13;`` survives XML parsing as a CR - a Python line break the
    multi-line refusal (which looks for LF) never saw. (No ``=`` in the payload:
    a ``Label = value`` cell is refused as label-prefixed before this.)"""
    from codegen.extract.frd_docx import FrdDocxError, extract_frd_contract, read_docx
    from codegen.run_errors import error_coord, error_reason

    contract, _profile = extract_frd_contract(_DOCX, config, generated_date="2026-01-01")
    name = contract.feeds[0].feed_name
    docx = _docx_with(tmp_path, name, name + "&#13;print(1)")
    with pytest.raises(FrdDocxError) as caught:
        extract_frd_contract(docx, config, generated_date="2026-01-01")
    assert error_reason(caught.value) == "frd.value"
    coord = error_coord(caught.value)
    assert coord.doc == "FRD" and "print" not in str(coord)
    # the coordinates (1-based) name the very cell that holds the CR
    row = read_docx(docx, prose_ok=True).tables[coord.table - 1][coord.row - 1]
    assert any(f"{name}\rprint(1)" in cell for cell in row)


# ------------------------------------- 2./3. the templates and the gate behind it


def _ruff_missing(monkeypatch):
    real = preflight.importlib.util.find_spec
    monkeypatch.setattr(preflight.importlib.util, "find_spec",
                        lambda name, *a: None if name == "ruff" else real(name, *a))


def _hostile_run(config, tmp_path, monkeypatch, *, feed_name: bool = True,
                 payload: str = PAYLOAD):
    """The demo pair's first feed, its names carrying the payload AFTER the
    contract (model_copy does not validate: the layers behind it are tested),
    rendered in notebook mode with ruff missing. ``feed_name`` False: the FRD
    contract name only (its banner line is ``#   <name>``, so a broken-out
    statement parses - only the compiler, seeing ``from __future__`` after it,
    refuses it)."""
    scoped = config.model_copy(update={"output": config.output.model_copy(update={
        "dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports"),
        "mode": "notebook"})})
    spec = resolve_pair(_FRD, _STTM, scoped)[0]
    update = {"frd_contract_name": spec.frd_contract_name + payload}
    if feed_name:
        update["feed_name"] = spec.feed_name + payload
    spec = spec.model_copy(update=update)
    _ruff_missing(monkeypatch)
    gate = cli._generate_feed(spec, scoped, dry_run=True, skip_tests=True,
                              output_mode="notebook")
    return gate, tmp_path / "out" / spec.feed_slug


def _python_sources(feed_dir: Path) -> list[tuple[str, str]]:
    sources = [(p.relative_to(feed_dir).as_posix(), p.read_text(encoding="utf-8"))
               for p in sorted(feed_dir.rglob("*.py"))]
    for path in sorted(feed_dir.rglob("*.ipynb")):
        cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
        sources += [(f"{path.name}[{i}]", "".join(c["source"])) for i, c in enumerate(cells)
                    if c["cell_type"] == "code"]
    return sources


@needs_demo_pair
def test_behind_the_contract_the_payload_stays_on_one_comment_line(config, tmp_path,
                                                                   monkeypatch):
    gate, feed_dir = _hostile_run(config, tmp_path, monkeypatch)
    sources = _python_sources(feed_dir)
    assert any(".ipynb[" in name for name, _ in sources)
    banners = 0
    for name, text in sources:
        lines = text.splitlines()
        assert "X = 1" not in lines, name                 # never a line of code
        for line in lines:
            if "X = 1" in line and "\\nX = 1" not in line:  # not inside a string literal
                banners += 1
                assert line.lstrip().startswith("#"), (name, line)
    assert banners, "the payload reached no banner - the test proves nothing"
    assert gate.verdict != "FAIL", [c.name for c in gate.checks if not c.passed]
    assert {c.name: c.passed for c in gate.checks}["python_compiles"]


@needs_demo_pair
def test_without_the_filter_the_compile_check_fails_the_feed_without_ruff(config, tmp_path,
                                                                          monkeypatch):
    """Layer 3 alone: the comment filter switched off, ruff missing - the broken
    banner must not ship."""
    from codegen.emit import emitter, notebook

    monkeypatch.setattr(emitter, "comment1", lambda value: str(value))
    monkeypatch.setattr(notebook, "comment1", lambda value: str(value))
    # an expression, not a binding: every module carries it, and a NAME bound in
    # each would stop the notebook assembly first (a namespace collision)
    gate, feed_dir = _hostile_run(config, tmp_path, monkeypatch, feed_name=False,
                                  payload="\nprint(1)")
    assert any("print(1)" in t.splitlines() for _n, t in _python_sources(feed_dir)), \
        "the filter was not off - the test proves nothing"
    checks = {c.name: c for c in gate.checks}
    assert checks["ruff"].not_run                       # ruff really was missing
    assert gate.verdict == "FAIL"
    assert [c.name for c in gate.checks if not c.passed] == ["python_compiles"]
    assert checks["python_compiles"].violations["syntax"] >= 1
    assert "print" not in checks["python_compiles"].details   # kinds and places only


def test_the_compile_check_reads_every_py_and_every_code_cell(tmp_path):
    (tmp_path / "pipeline").mkdir()
    (tmp_path / "pipeline" / "ok.py").write_text("X = 1\n", encoding="utf-8")
    late = "# banner\nX = 1\nfrom __future__ import annotations\n"     # parses, never compiles
    (tmp_path / "pipeline" / "late.py").write_text(late, encoding="utf-8")
    (tmp_path / "nb.ipynb").write_text(json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# not code\n", "X = = 1\n"]},
        {"cell_type": "code", "source": ["Y = 2\n"]},
        {"cell_type": "code", "source": ["def f(:\n"]}]}), encoding="utf-8")
    check = preflight._python_compiles_check(tmp_path)
    assert not check.passed and check.violations == {"syntax": 2}
    assert "pipeline/late.py:3: SyntaxError" in check.details
    assert "nb.ipynb[cell 3]:1: SyntaxError" in check.details
    (tmp_path / "pipeline" / "late.py").unlink()
    (tmp_path / "nb.ipynb").unlink()
    ok = preflight._python_compiles_check(tmp_path)
    assert ok.passed and ok.details == "1 .py file(s) and 0 notebook code cell(s) compile"


def test_comment1_keeps_a_clean_value_and_collapses_a_break():
    from codegen.emit.metadata_inserts import comment1

    for clean in ("FEED_2 Claims", "a  b ", "x y", "", "Données"):
        assert comment1(clean) == clean
    for brk in BREAKS:
        assert comment1(f"Name{brk}X = 1") == "Name X = 1"
    assert comment1(None) == "None" and comment1(3) == "3"      # as Jinja printed them


# ------------------------------------------------- P2-9: the DDL test-cases file


def _with_hostile_field(spec):
    segment = spec.segments[0]
    field = segment.fields[0].model_copy(update={"source_column": "X\nDROP TABLE t;"})
    segment = segment.model_copy(update={"fields": [field, *segment.fields[1:]]})
    return spec.model_copy(update={"segments": [segment, *spec.segments[1:]]})


def test_a_hostile_field_name_leaves_no_non_comment_line(pair4_config, pair4_spec, tmp_path):
    """A regression pin: the field name reaches the case lines, which the
    emitter collapses to one ``--`` line each; the check proves it."""
    from test_ddl_test_cases import _run

    gate, framework = _run(pair4_config, _with_hostile_field(pair4_spec), tmp_path)
    text = next(framework.glob("*_TestCases.txt")).read_text(encoding="utf-8")
    assert "X DROP TABLE t;" in text                     # it did reach the file
    for line in text.splitlines():
        stripped = line.strip()
        assert (not stripped or stripped.startswith("--")
                or stripped.startswith(("SELECT ", "SHOW "))), line
        assert not stripped.upper().startswith("DROP"), line
    assert {c.name: c for c in gate.checks}["ddl_tests_read_only"].passed


def test_a_stray_line_fails_the_read_only_check_even_without_sqlglot(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_sqlglot(name, *args, **kwargs):
        if name == "sqlglot" or name.startswith("sqlglot."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    text = ("-- TC01 Column mapping\n--   Check: X\nDROP TABLE t;\n"
            "SELECT 'TC01' AS test_id;\nSHOW TBLPROPERTIES a.b.c;\n")
    monkeypatch.setattr(builtins, "__import__", no_sqlglot)
    check = check_ddl_tests_read_only([("x_TestCases.txt", text)], "databricks")
    assert not check.passed and not check.not_run
    assert check.details == ("x_TestCases.txt: line(s) 3 neither a -- comment nor one "
                             "read-only statement")
    clean = check_ddl_tests_read_only([("x_TestCases.txt", text.replace("DROP TABLE t;\n",
                                                                        ""))], "databricks")
    assert clean.passed and clean.not_run           # sqlglot missing: flagged, as before


def test_a_read_only_word_inside_a_comment_break_is_still_stray():
    pytest.importorskip("sqlglot")
    # a break that leaves a bare identifier line: neither comment nor statement
    text = "--   Check: column X\nY\nSELECT 1;\n"
    check = check_ddl_tests_read_only([("x_TestCases.txt", text)], "databricks")
    assert not check.passed and "line(s) 2 neither" in check.details
