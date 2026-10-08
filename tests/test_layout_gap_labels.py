"""A layout with two OPTIONAL columns and one REQUIRED column unplaced.

The synthetic fixture is the pair-1 workbook's ``layout_gaps`` variant
(``acfc_shapes.sttm.build_pair1(layout_gaps=True)``): the source headers 'Ref'
and 'Remarks', which a test overlay teaches to two optional roles each (so
each is AMBIGUOUS — the layout places neither), and the stage band's data-type
header renamed 'Value Kind (DL)', which no synonym knows (the required
``stage/target_type``). The shipped vocabulary has no synonym two roles of a
band share, so optional ambiguity needs the overlay; real client headers that
grow the tables can produce it.

Contract (docs/ACFC_DEPLOY.md "CLI exit codes"): ``layout --require-complete``
prints two NOTE lines and one UNRESOLVED line and exits 3; with the required
column placed through answers.yaml it prints the two NOTE lines, exits 0, and
the harness's ``_NEEDED_KEY_RE`` finds no key at all.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from acfc_shapes import sttm as sttm_fixtures
from acfc_shapes.common import xlsx_bytes
from codegen import cli
from test_harness_answer_lines import _NEEDED_KEY_RE

SHEET = "FEED_1_MAPPING"
GAPS = sttm_fixtures.LAYOUT_GAP_HEADERS
OPTIONAL_KEYS = [f"{SHEET}/source/comments|description",
                 f"{SHEET}/source/ordinal|sample_value"]
REQUIRED_KEY = f"{SHEET}/stage/target_type"


def _overlay(config, tmp: Path) -> Path:
    """Each changed source header joins the synonyms of TWO optional roles
    (overlay lists replace, so the shipped spellings are carried)."""
    source = config.extractor.discovery.roles["source"]
    extra = {"ordinal": GAPS["ordinal"], "sample_value": GAPS["ordinal"],
             "description": GAPS["description"], "comments": GAPS["description"]}
    roles = {role: [*source[role], word.lower()] for role, word in extra.items()}
    path = tmp / "gaps_overlay.yaml"
    path.write_text(yaml.safe_dump({"extractor": {"discovery": {"roles": {"source": roles}}}}),
                    encoding="utf-8")
    return path


def _labelled(out: str) -> dict[str, list[str]]:
    lines: dict[str, list[str]] = {}
    for line in out.splitlines():
        label = line.split(" ", 1)[0]
        if label in ("QUESTION", "UNRESOLVED", "NOTE") and " — " in line:
            # the key: column 15 up to the em-dash (the answer_line form)
            lines.setdefault(label, []).append(
                line[cli.ANSWER_LABEL_WIDTH:].split(" — ", 1)[0])
    return lines


def test_two_optional_and_one_required_unplaced(config, monkeypatch, tmp_path, capsys):
    workbook = tmp_path / "STTM_layout_gaps.xlsx"
    workbook.write_bytes(xlsx_bytes(sttm_fixtures.build_pair1(layout_gaps=True)))
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(_overlay(config, tmp_path)))
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    (tmp_path / "state").mkdir()
    argv = ["layout", "--workbook", str(workbook), "--dry-run", "--no-cache",
            "--require-complete"]

    # 1. Unplaced: two NOTE lines, one UNRESOLVED line, exit 3.
    capsys.readouterr()
    assert cli.main(argv) == cli.EXIT_NEEDS_ANSWERS
    out = capsys.readouterr().out
    lines = _labelled(out)
    assert sorted(lines.get("NOTE", [])) == OPTIONAL_KEYS
    assert lines.get("UNRESOLVED") == [REQUIRED_KEY]
    assert "QUESTION" not in lines
    assert [m.group(1) for ln in out.splitlines() if (m := _NEEDED_KEY_RE.match(ln))] == [
        REQUIRED_KEY]                               # the harness records exactly that key

    # 2. The required column placed through answers.yaml: two NOTE lines, exit 0,
    #    and the harness finds no key.
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"answers": [{
        "document": "sttm", "sheet": SHEET, "layer": "stage", "role": "target_type",
        "column": GAPS["stage_target_type"]}]}), encoding="utf-8")
    capsys.readouterr()
    assert cli.main([*argv, "--answers", str(answers)]) == cli.EXIT_OK
    out = capsys.readouterr().out
    lines = _labelled(out)
    assert sorted(lines.get("NOTE", [])) == OPTIONAL_KEYS
    assert "UNRESOLVED" not in lines and "QUESTION" not in lines
    assert [ln for ln in out.splitlines() if _NEEDED_KEY_RE.match(ln)] == []
