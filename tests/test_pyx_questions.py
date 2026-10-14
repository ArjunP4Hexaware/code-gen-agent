"""The Pyx shape asks only what the documents cannot answer (2026-10-13, D1
pair_11 identity diff: 22 open questions, extract-sttm exit 3).

Synthetic stand-in (tests/acfc_shapes/family_e_multi.py ``build_*_reports``):
five report sheets, each its own stage table, a ``Table_Details`` sheet, the
FRD's format cell "Text files" against the STTM's csv, the FRD's file list
spelled differently from File Details. What the agent resolves itself:

a. ``Table_Details`` is metadata, never a feed: its nine UNRESOLVED roles go;
b. "Text files" + a csv / psv / tsv / txt extension: the extension, a NOTE;
c. each sheet's file by token overlap of its title / File Name row / table
   with the FRD's file names: a unique best match is taken (a NOTE), only a tie
   is asked — the tied files named in the question;
d. owed answers land in ``answers_template.yaml`` (key, question, candidates,
   empty value); filled in and passed back with --answers, one pass settles it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from acfc_shapes import family_e_multi as fm
from codegen import cli
from codegen.config import load_config
from codegen.layout.answers import load_answers
from codegen.layout.discover import discover
from codegen.layout.resolve import best_file_matches, file_identity

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-10-13"
OWED = ("QUESTION", "UNRESOLVED")


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    return tmp_path


def _opaque(names: dict[str, str] | None = None) -> dict[str, tuple[str, str, str]]:
    """The reports with table names that share no word with their files: only
    the sheet titles can pair them. ``names`` renames sheets."""
    out = {}
    for index, (sheet, (_table, frd, details)) in enumerate(fm.REPORTS.items()):
        out[(names or {}).get(sheet, sheet)] = (f"nb_cm_rpt_{index}", frd, details)
    return out


def _layout(tmp: Path, capsys, *extra: str, **sttm_kw) -> tuple[int, str, Path, Path]:
    sttm, frd = tmp / "STTM_nb_cm_reports.xlsx", tmp / "FRD_nb_cm_reports.docx"
    fm.build_sttm_reports(**sttm_kw).save(sttm)
    frd.write_bytes(fm.build_frd_reports())
    frd_out = tmp / "run" / "frd.contract.json"
    capsys.readouterr()
    code = cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(frd_out), "--require-complete",
                     *extra])
    return code, capsys.readouterr().out, sttm, frd_out


def _extract(sttm: Path, frd_out: Path, capsys, *extra: str) -> tuple[int, str, Path]:
    out = frd_out.parent / "sttm.contract.json"
    code = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_out),
                     "--out", str(out), "--generated-date", DATE, *extra])
    return code, capsys.readouterr().out, out


def _owed(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.split(" ", 1)[0] in OWED]


def _feeds(frd_out: Path) -> list[dict]:
    return json.loads(frd_out.read_text(encoding="utf-8"))["feeds"]


# --------------------------------------------------------------------- a.


def test_table_details_is_metadata_never_a_feed(tmp_path):
    path = tmp_path / "sttm.xlsx"
    fm.build_sttm_reports().save(path)
    config = load_config(REPO / "config" / "config.yaml")
    found = discover(path, config.extractor)
    kinds = {s.name: s.kind for s in found.profile.sheets}
    assert kinds[fm.TABLE_DETAILS] == "table_details"
    assert sorted(s.name for s in found.profile.mapping_sheets) == sorted(fm.REPORTS)
    assert not [u for u in found.profile.unresolved if u.sheet == fm.TABLE_DETAILS]
    assert any("Table_Details" in n and "metadata" in n for n in found.diagnostics)


def test_a_sheet_on_which_nothing_resolves_is_metadata_too(tmp_path):
    """Not by name: a mapping-shaped sheet with no role while others map fields."""
    path = tmp_path / "sttm.xlsx"
    wb = fm.build_sttm_reports()
    wb[fm.TABLE_DETAILS].title = "Report Targets"
    wb.save(path)
    found = discover(path, load_config(REPO / "config" / "config.yaml").extractor)
    assert {s.name: s.kind for s in found.profile.sheets}["Report Targets"] == "table_details"
    assert not [u for u in found.profile.unresolved if u.sheet == "Report Targets"]


# ------------------------------------------------------------- a + b + c.


def test_the_pyx_shape_asks_nothing(env, capsys):
    code, out, sttm, frd_out = _layout(env, capsys)
    assert code == 0, out
    assert _owed(out) == []
    assert "Table_Details" not in out.split("CROSSCHECK")[0]
    feeds = _feeds(frd_out)
    assert [f["feed_name"] for f in feeds] == [t for t, _f, _d in fm.REPORTS.values()]
    # b. "Text files" + csv: the extension decides, said as a NOTE per feed
    notes = [x for x in out.splitlines() if x.startswith("NOTE") and ".file_format" in x]
    assert len(notes) == len(fm.REPORTS)
    assert all("'Text files'" in x and "-> 'csv'" in x for x in notes)
    assert {f["file_format"] for f in feeds} == {"csv"}
    # c. each feed its OWN file, the FRD's spelling (one candidate per file)
    assert [f["file_name_patterns"] for f in feeds] == [[frd] for _t, frd, _d in
                                                        fm.REPORTS.values()]
    code, out, _contract = _extract(sttm, frd_out, capsys)
    assert code == 0, out
    assert f"{len(fm.REPORTS)} feed(s)" in out and _owed(out) == []


def test_sheet_titles_pair_the_files_when_the_tables_say_nothing(env, capsys):
    reports = _opaque()
    code, out, _sttm, frd_out = _layout(env, capsys, reports=reports)
    assert code == 0, out
    assert _owed(out) == []
    feeds = _feeds(frd_out)
    assert [f["file_name_patterns"] for f in feeds] == [[frd] for _t, frd, _d in
                                                        reports.values()]
    best = [x for x in out.splitlines() if x.startswith("NOTE") and "best name match" in x]
    assert len(best) == len(reports)
    # the cut title ("Repor") and the abbreviation ("Engmnt") still pair
    assert any("'Monthly Screening Repor'" in x and "screening" in x for x in best)
    assert any("'Monthly Engmnt Billing'" in x and "billing" in x for x in best)


def test_only_a_tie_is_asked_and_the_question_names_the_tied_files(env, capsys):
    """Two sheets name the same two files equally: both asked, tied files first."""
    dnc, outreach = (fm.REPORTS["Weekly DNC Report"][1],
                     fm.REPORTS["Monthly Outreach Report"][1])
    reports = _opaque({"Weekly DNC Report": "DNC Outreach One",
                       "Monthly Outreach Report": "DNC Outreach Two"})
    code, out, _sttm, _frd_out = _layout(env, capsys, reports=reports)
    owed = _owed(out)
    assert code == 3 and len(owed) == 2, out
    for line in owed:
        assert ".file_name_patterns" in line and "tie between" in line
        assert dnc in line and outreach in line
    template = yaml.safe_load((env / "run" / "answers_template.yaml").read_text(
        encoding="utf-8"))
    for entry in template["gaps"].values():
        assert entry["value"] == "" and entry["candidates"][:2] == [dnc, outreach]


def test_with_a_blank_stage_table_at_most_two_questions(env, capsys):
    """The brief's acceptance: after a-c the open questions are <= 2 — here the
    one the documents cannot answer, the blank stage TableName."""
    code, out, sttm, frd_out = _layout(env, capsys,
                                       blank_stage_tables=("Weekly DNC Report",))
    owed = _owed(out)
    assert code == 3 and len(owed) <= 2, out
    assert [x.split()[1] for x in owed] == ["feeds[4].stage_target.tables"]
    code, out, _contract = _extract(sttm, frd_out, capsys)
    assert code == 0 and "4 feed(s)" in out
    assert [x.split()[1] for x in _owed(out)] == ["feeds[4].stage_target.tables"]


def test_best_file_matches_takes_a_unique_best_and_reports_ties():
    files = ["NW_DNC_Report_*.csv", "NW_Outreach_Report_*.csv", "NW_Weekly_Activity_*.csv"]
    chosen, ties = best_file_matches({"Weekly DNC Report": {"weekly", "dnc"},
                                      "Weekly Activity Report": {"weekly", "activity"},
                                      "DNC Outreach": {"dnc", "outreach"}}, files)
    assert chosen["Weekly DNC Report"][0] == "NW_DNC_Report_*.csv"
    assert chosen["Weekly Activity Report"][0] == "NW_Weekly_Activity_*.csv"
    assert "DNC Outreach" in ties and {f for f, _s in ties["DNC Outreach"]} == {
        "NW_DNC_Report_*.csv", "NW_Outreach_Report_*.csv"}


def test_file_identity_joins_the_spellings_of_one_file():
    same = ["Northwind_CM_DNC_Report_MMDDYYYY.csv", "Northwind_CM_DNC_Report_*.csv",
            "in/northwind-cm-dnc-report-20261013.CSV"]
    assert len({file_identity(n) for n in same}) == 1
    assert file_identity("Northwind_CM_DNC_Report_*.csv") != file_identity(
        "Northwind_CM_Outreach_Report_*.csv")


# --------------------------------------------------------------------- d.


def test_exit_3_writes_the_answers_template_and_one_pass_settles_it(env, capsys):
    blank = ("Weekly DNC Report", "Monthly Outreach Report")
    code, out, sttm, frd_out = _layout(env, capsys, blank_stage_tables=blank,
                                       table_details=False,
                                       reports={s: fm.REPORTS[s] for s in blank})
    assert code == 3, out
    code, out, contract = _extract(sttm, frd_out, capsys)
    assert code == 3 and "NOT EXTRACTED" in out, out
    template = frd_out.parent / "answers_template.yaml"
    assert f"ANSWERS FILE    {template}" in out
    body = yaml.safe_load(template.read_text(encoding="utf-8"))
    keys = sorted(body["gaps"])
    assert keys == ["feeds[0].stage_target.tables", "feeds[1].stage_target.tables"]
    assert all(e["value"] == "" and e["question"] for e in body["gaps"].values())
    # left empty it is a valid answers file with no answer in it
    assert load_answers(template).gaps == {} and load_answers(template).entries == []

    # fill it in (the D1 step) and rerun with --answers: one pass
    filled = template.read_text(encoding="utf-8").replace(
        'value: ""', 'value: "nb_cm_answered"', 1)
    filled = filled.replace('value: ""', 'value: "nb_cm_answered_two"', 1)
    template.write_text(filled, encoding="utf-8")
    capsys.readouterr()
    code = cli.main(["layout", "--workbook", str(sttm), "--frd",
                     str(sttm.with_name("FRD_nb_cm_reports.docx")), "--dry-run", "--no-cache",
                     "--frd-contract-out", str(frd_out), "--require-complete",
                     "--answers", str(template)])
    out = capsys.readouterr().out
    assert code == 0 and _owed(out) == [], out
    code, out, contract = _extract(sttm, frd_out, capsys, "--answers", str(template))
    assert code == 0 and "2 feed(s)" in out, out
    feeds = json.loads(contract.read_text(encoding="utf-8"))["feeds"]
    assert sorted(f["stage"]["table"] for f in feeds) == ["nb_cm_answered",
                                                          "nb_cm_answered_two"]


def test_a_template_row_left_empty_is_skipped_but_a_filled_one_applies(tmp_path):
    path = tmp_path / "answers_template.yaml"
    from codegen.layout.answers_template import TemplateItem, write_answers_template

    write_answers_template(path, [
        TemplateItem("feeds[0].file_name_patterns", "which file?", ["a.csv", "b.csv"]),
        TemplateItem("feeds[1].file_format", "which format?", ["csv", "psv"]),
        TemplateItem("Sheet1/stage/table", "no header", ["F", "G"], "answers"),
        TemplateItem("Sheet1/band[2]/layer", "no evidence", ["source", "stage"], "answers"),
    ], stage="test")
    assert load_answers(path).gaps == {} and load_answers(path).entries == []
    body = yaml.safe_load(path.read_text(encoding="utf-8"))
    body["gaps"]["feeds[0].file_name_patterns"]["value"] = "a.csv"
    next(e for e in body["answers"] if e["role"] == "table")["column"] = "G"
    path.write_text(yaml.safe_dump(body, sort_keys=False), encoding="utf-8")
    answers = load_answers(path)
    assert list(answers.gaps) == ["feeds[0].file_name_patterns"]
    assert answers.gaps["feeds[0].file_name_patterns"]["value"] == "a.csv"
    assert [e["column"] for e in answers.entries] == ["G"]
