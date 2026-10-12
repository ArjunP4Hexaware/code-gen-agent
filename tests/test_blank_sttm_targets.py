"""Round 4 (2026-10-12): an STTM copy whose mapping sheets leave EVERY Schema /
TableName cell blank.

D1's copy of the SD STTM read that way and the run needed 14 answers plus a
hand-split FRD contract: ``split_frd_feeds_by_sttm`` only split when at least
one sheet named a table. Required now (owner's brief, amended):

- the split triggers on the mapping sheets alone (one feed per sheet);
- schema: the FRD's ONE structural-metadata schema per layer applies to every
  feed — a NOTE citing the FRD field, never a QUESTION; a schema cell that is
  a per-file-group list is not one schema and stays a QUESTION;
- table: no conventions rule derives a table name from a file name, so none
  is invented — one QUESTION per feed and layer (six for three feeds), the
  FRD 'Target Table Name' file quoted in it;
- frequency: the FRD's Frequency cell points to the File Details tab, whose
  row of the feed's file states it (the existing chain) — never asked here.

Synthetic pair 11 (the one-block / many-files FRD shape) with every target
cell blanked; the catalog variant's 'Target Schema' is one line per layer.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from acfc_shapes import frd as frd_fixtures
from acfc_shapes import sttm as sttm_fixtures
from acfc_shapes.common import xlsx_bytes
from codegen import cli
from test_harness_answer_lines import _NEEDED_KEY_RE

SHEETS = ["MAPPING-VC_ENROLLMENT", "MAPPING-VC_DISENROLLMENT", "MAPPING-VC_INDIVIDUAL_RISK"]
TABLE_KEYS = [f"feeds[{i}].{layer}_target.tables" for i in range(3)
              for layer in ("stage", "standard")]
SCHEMA_KEYS = [f"feeds[{i}].{layer}_target.schema" for i in range(3)
               for layer in ("stage", "standard")]


def _blank_sttm(tmp_path: Path) -> Path:
    wb = sttm_fixtures.build_pair11()
    for name in SHEETS:
        for row in wb[name].iter_rows(min_row=3):
            for index in (8, 9, 12, 13):    # stage Schema / TableName, standard Schema / TableName
                row[index].value = None
    path = tmp_path / "sttm_blank_targets.xlsx"
    path.write_bytes(xlsx_bytes(wb))
    return path


def _frd(tmp_path: Path, catalog: str | None) -> Path:
    path = tmp_path / f"frd_{catalog or 'multiline'}.docx"
    path.write_bytes(frd_fixtures.build_f1_pair11_multi_file(catalog=catalog))
    return path


def _env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    (tmp_path / "state").mkdir(exist_ok=True)


def _layout(sttm: Path, frd: Path, out_json: Path, capsys, answers: Path | None = None):
    argv = ["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run", "--no-cache",
            "--require-complete", "--frd-contract-out", str(out_json)]
    if answers is not None:
        argv += ["--answers", str(answers)]
    capsys.readouterr()
    rc = cli.main(argv)
    return rc, capsys.readouterr().out


def _keys(out: str, label: str) -> list[str]:
    return [line[cli.ANSWER_LABEL_WIDTH:].split(" — ", 1)[0] for line in out.splitlines()
            if line.split(" ", 1)[0] == label and " — " in line]


def test_blank_targets_split_fill_the_one_frd_schema_and_ask_six_tables(
        monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    sttm, frd = _blank_sttm(tmp_path), _frd(tmp_path, "cat_syn")
    rc, out = _layout(sttm, frd, tmp_path / "frd.json", capsys)

    assert rc == cli.EXIT_NEEDS_ANSWERS, out
    assert sorted(_keys(out, "QUESTION")) == sorted(TABLE_KEYS)     # six, nothing else
    assert not set(SCHEMA_KEYS) & set(_keys(out, "QUESTION"))
    assert sorted(k for k in _keys(out, "NOTE") if k in SCHEMA_KEYS) == sorted(SCHEMA_KEYS)
    assert sorted(m.group(1) for ln in out.splitlines()
                  if (m := _NEEDED_KEY_RE.match(ln))) == sorted(TABLE_KEYS)
    # each table question says why the FRD cannot answer it and quotes its file
    for index, name in enumerate(frd_fixtures.PAIR11_FILES):
        line = next(ln for ln in out.splitlines()
                    if ln.startswith("QUESTION") and f"feeds[{index}].stage_target.tables" in ln)
        assert f"names files ({name!r}), not tables" in line
        assert "no conventions rule derives a table name from a file name" in line
    # the schema NOTE cites the FRD field
    note = next(ln for ln in out.splitlines()
                if ln.startswith("NOTE") and "feeds[1].standard_target.schema" in ln)
    assert "('Target Schema')" in note and "'dom_a'" in note

    contract = json.loads((tmp_path / "frd.json").read_text(encoding="utf-8"))
    feeds = contract["feeds"]
    assert [f["feed_name"] for f in feeds] == [s.removeprefix("MAPPING-") for s in SHEETS]
    assert [f["file_name_patterns"] for f in feeds] == [[n] for n in frd_fixtures.PAIR11_FILES]
    assert [f["frequency"] for f in feeds] == ["Yearly Twice", "Yearly Twice", "Monthly"]
    assert {(f["stage_target"]["schema"], f["standard_target"]["schema"]) for f in feeds} == {
        ("stg_dom_a", "dom_a")}
    assert all(f["stage_target"]["tables"] == [] for f in feeds)        # never invented


def test_the_six_table_answers_complete_the_pair(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    sttm, frd = _blank_sttm(tmp_path), _frd(tmp_path, "cat_syn")
    tables = ["vc_enrollment", "vc_disenrollment", "vc_individual_risk"]
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"gaps": {
        f"feeds[{i}].{layer}_target.tables": {"value": table}
        for i, table in enumerate(tables) for layer in ("stage", "standard")}}),
        encoding="utf-8")
    frd_json = tmp_path / "frd.json"
    rc, out = _layout(sttm, frd, frd_json, capsys, answers=answers)
    assert rc == cli.EXIT_OK, out
    assert _keys(out, "QUESTION") == [] and _keys(out, "UNRESOLVED") == []

    sttm_json = tmp_path / "sttm.json"
    capsys.readouterr()
    rc = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_json),
                   "--out", str(sttm_json), "--generated-date", "2026-01-01"])
    out = capsys.readouterr().out
    assert rc == cli.EXIT_OK, out
    contract = json.loads(sttm_json.read_text(encoding="utf-8"))
    assert not contract.get("needs_answers")
    assert sorted(f["feed_id"] for f in contract["feeds"]) == sorted(tables)
    flags = [flag for f in contract["feeds"] for flag in f.get("extraction_flags", [])]
    assert sum("sttm_target_missing:stage.schema" in flag for flag in flags) == 3


def test_a_per_file_group_schema_list_is_not_one_schema(monkeypatch, tmp_path, capsys):
    """The SD-shaped 'Target Schema' cell (one 'stg_x/x – <files>' line per file
    group) names no single schema: each feed's schemas are asked as well."""
    _env(monkeypatch, tmp_path)
    sttm, frd = _blank_sttm(tmp_path), _frd(tmp_path, None)
    rc, out = _layout(sttm, frd, tmp_path / "frd.json", capsys)
    assert rc == cli.EXIT_NEEDS_ANSWERS, out
    assert sorted(_keys(out, "QUESTION")) == sorted(TABLE_KEYS + SCHEMA_KEYS)
    line = next(ln for ln in out.splitlines()
                if ln.startswith("QUESTION") and "feeds[0].stage_target.schema" in ln)
    assert "'Target Schema' cell is a multiline value (2 line(s)), not one schema" in line
