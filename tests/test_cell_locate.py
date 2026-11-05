"""post176: the model points, the code copies (docs/PARSER_SELF_EXTENSION.md step 3).

A refused cell of the ingested FRD (no grammar reads it, no other document fills the
field): the layout model names the LINE that states the field - never the value; the code
copies the line, the field's vocabulary validates it, the answer is cached per cell. A
wrong line, a value the vocabulary refuses, a line outside the cell or one the stored text
cut short leaves the field open. Every located value is flagged for review.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from codegen.config import load_config
from codegen.layout.cell_locate import CellLocator

REPO = Path(__file__).resolve().parents[1]
CELL = {"kind": "multiline", "table": 6, "row": 4, "label": "Object/data Format",
        "text": "Kind Of File: .txt\nSeparator: Pipe Delimited\nCadence: Weekly"}


class Points:
    """A provider stub: answers a fixed line per field, counts the calls."""

    def __init__(self, lines: dict[str, int | None]) -> None:
        self.lines = lines
        self.requests: list[dict] = []

    def locate_line(self, request: dict) -> dict:
        self.requests.append(request)
        return {"line": self.lines.get(request["field"])}


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def test_the_named_lines_are_copied_and_validated(config, tmp_path):
    provider = Points({"file_format": 1, "delimiter": 2, "frequency": 3})
    locate = CellLocator(provider, tmp_path, config)
    assert locate("file_format", CELL) == (1, ".txt")
    assert locate("delimiter", CELL) == (2, "Pipe Delimited")
    assert locate("frequency", CELL) == (3, "Weekly")
    # the model saw that one cell's lines and the field - nothing else
    assert set(provider.requests[0]) == {"field", "meaning", "lines"}
    assert [x["text"] for x in provider.requests[0]["lines"]] == CELL["text"].splitlines()


@pytest.mark.parametrize("answer", [None, 0, 4, 99, "1", True])
def test_no_line_or_a_line_outside_the_cell_leaves_it_open(config, tmp_path, answer):
    assert CellLocator(Points({"file_format": answer}), tmp_path, config)(
        "file_format", CELL) is None


def test_a_line_the_vocabulary_refuses_leaves_it_open(config, tmp_path):
    """The model names the Cadence line for the file format: 'Weekly' names no format."""
    assert CellLocator(Points({"file_format": 3}), tmp_path, config)("file_format", CELL) is None


def test_a_line_the_stored_text_cut_short_is_never_copied(config, tmp_path):
    cut = {**CELL, "text": "Kind Of File: .txt\nSeparator: Pip…"}
    assert CellLocator(Points({"delimiter": 2}), tmp_path, config)("delimiter", cut) is None


def test_only_a_refused_multiline_cell_of_a_locatable_field(config, tmp_path):
    locate = CellLocator(Points({"file_format": 1, "landing_location": 1}), tmp_path, config)
    assert locate("file_format", {**CELL, "kind": "pointer"}) is None
    assert locate("landing_location", CELL) is None


def test_the_answer_is_cached_per_cell(config, tmp_path):
    provider = Points({"file_format": 1})
    CellLocator(provider, tmp_path, config)("file_format", CELL)
    again = CellLocator(Points({"file_format": 3}), tmp_path, config)    # would be refused
    assert again("file_format", CELL) == (1, ".txt")                    # the cached line
    assert again.provider.requests == []
    cached = list((tmp_path / "cell_locate").glob("*.json"))
    assert len(cached) == 1 and ".txt" not in cached[0].read_text(encoding="utf-8")


# -- the layout stage, end to end -------------------------------------------------

def test_layout_fills_the_refused_cell_through_the_model_and_flags_it(tmp_path, monkeypatch,
                                                                     capsys):
    """`codegen layout` (the mock provider pointing at lines): the FRD's format cell
    has labels no reader knows; the model names the lines, the values are copied."""
    from codegen import cli
    from codegen.layout.model import MockLayoutProvider

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    (tmp_path / "state").mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setattr(MockLayoutProvider, "locate_answers", {"file_format": 1,
                                                                "delimiter": 2})
    sttm, frd, out = tmp_path / "STTM_nb.xlsx", tmp_path / "FRD_nb.docx", tmp_path / "frd.json"
    fm.build_sttm().save(sttm)
    frd.write_bytes(fm.build_frd(format_cell="Kind Of File: .txt\nSeparator: Pipe Delimited"))
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(out)]) == 0
    capsys.readouterr()
    contract = json.loads(out.read_text(encoding="utf-8"))
    assert {(f["file_format"], f["delimiter"]) for f in contract["feeds"]} == {
        (".txt", "Pipe Delimited")}
    flags = contract["extraction_flags"]
    assert any(f.startswith("frd_model_located:feeds[0].file_format") and "line 1" in f
               for f in flags), flags
    assert any(f.startswith("frd_model_located:feeds[0].delimiter") for f in flags)


def test_without_an_answer_the_layout_stage_is_unchanged(tmp_path, monkeypatch, capsys):
    from codegen import cli

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    (tmp_path / "state").mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    sttm, frd, out = tmp_path / "STTM_nb.xlsx", tmp_path / "FRD_nb.docx", tmp_path / "frd.json"
    fm.build_sttm().save(sttm)
    frd.write_bytes(fm.build_frd(format_cell="Kind Of File: .txt\nSeparator: Pipe Delimited"))
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(out)]) == 0
    capsys.readouterr()
    flags = json.loads(out.read_text(encoding="utf-8"))["extraction_flags"]
    assert not any(f.startswith("frd_model_located") for f in flags)
