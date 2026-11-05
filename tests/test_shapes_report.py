"""post173: the unfamiliar-shapes report (docs/PARSER_SELF_EXTENSION.md step 4).

The shapes the readers could not place - FRD cells refused (several lines, a table, a
pointer ...) and STTM roles no header placed - added up across runs, most runs first, so
the recurring ones are extended first. Coordinates and vocabulary only: a cell's text and
an STTM sheet name never reach the report."""

from __future__ import annotations

import json
from pathlib import Path

from codegen import cli
from codegen.shapes_report import render_markdown, run_shapes, summarize

CELL_TEXT = "PLANTED CELL TEXT 4242"
SHEET = "PLANTED_CLIENT_SHEET"


def _run(root: Path, label: str, *, structured: dict, unresolved: list[str]) -> None:
    folder = root / label
    folder.mkdir(parents=True)
    (folder / "frd.contract.json").write_text(json.dumps({"structured": structured}),
                                              encoding="utf-8")
    (folder / "extracted_sttm.contract.json").write_text(json.dumps(
        {"layout": {"strategy": "x", "source": "synonyms", "fingerprint": "f",
                    "unresolved": unresolved}}), encoding="utf-8")


MULTILINE = {"kind": "multiline", "table": 6, "row": 4, "col": 2,
             "label": "Object/data Format", "text": CELL_TEXT}


def _outputs(tmp_path: Path) -> Path:
    root = tmp_path / "outputs"
    _run(root, "demo_20261101_090000",
         structured={"feeds[0].file_format": MULTILINE,
                     "feeds[1].file_format": MULTILINE},          # a derived feed: once
         unresolved=[f"{SHEET}/stage/target_type: no header matches its synonyms"])
    _run(root, "demo_20261102_090000",
         structured={"feeds[0].file_format": {**MULTILINE, "table": 7},
                     "feeds[0].landing_location": {"kind": "pointer", "table": 2, "row": 9,
                                                   "label": "ADLS Location", "text": CELL_TEXT}},
         unresolved=[])
    (root / "not_a_run").mkdir()
    return root


def test_one_run_counts_a_cell_its_derived_feeds_share_once():
    shapes = run_shapes("r", {"structured": {"feeds[0].file_format": MULTILINE,
                                             "feeds[1].file_format": MULTILINE}}, None)
    assert len(shapes) == 1 and shapes[0].field == "file_format"


def test_shapes_are_added_up_across_runs_most_runs_first(tmp_path):
    from codegen.shapes_report import collect
    from codegen.storage import open_backend

    backend = open_backend(f"local:{_outputs(tmp_path).as_posix()}", base_dir=tmp_path)
    rows = summarize(collect(backend))
    first = rows[0]
    assert (first["document"], first["kind"], first["field"], first["runs"]) == (
        "FRD", "multiline", "file_format", 2)
    assert first["last"] == "demo_20261102_090000"
    assert first["where"] == ["table 6 row 4 ('Object/data Format')",
                              "table 7 row 4 ('Object/data Format')"]
    assert {(r["document"], r["kind"], r["field"], r["runs"]) for r in rows[1:]} == {
        ("FRD", "pointer", "landing_location", 1), ("STTM", "unresolved_role",
                                                    "stage/target_type", 1)}


def test_no_cell_text_and_no_sheet_name_reaches_the_report(tmp_path, capsys):
    root = _outputs(tmp_path)
    assert cli.main(["shapes-report", "--runs", str(root)]) == 0
    text = capsys.readouterr().out
    assert "| FRD | multiline | file_format | 2 |" in text
    assert "2 run(s) scanned" in text
    assert CELL_TEXT not in text and SHEET not in text


def test_the_report_can_be_written_to_a_file(tmp_path, capsys):
    out = tmp_path / "shapes.md"
    assert cli.main(["shapes-report", "--runs", f"local:{_outputs(tmp_path).as_posix()}",
                     "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("# Unfamiliar shapes")
    assert "SHAPES REPORT" in capsys.readouterr().out


def test_nothing_unfamiliar_says_so():
    assert "Nothing unfamiliar" in render_markdown([], 3)
