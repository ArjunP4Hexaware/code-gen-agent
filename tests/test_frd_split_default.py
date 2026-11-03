"""One FRD feed, several mapping sheets: split by default (2026-10-13, D1 pair_11).

The live D1 check failed pair_11 at extract-sttm: "all 5 mapping sheets paired
with the single unnamed FRD feed ... write the FRD contract with
--frd-contract-out". The split lived in the layout stage only; a contract that
did not come out of ``layout --frd-contract-out`` (``extract-frd``'s) reached
extract-sttm with ONE feed. Now extract-sttm splits it itself by the layout
stage's rule, records the derived feeds in the STTM contract, and generate
joins the same split from the one-feed FRD contract — no flag, no extra step.
An unnamed FRD feed is named per sheet (its File Name row, else the sheet).

The synthetic 5-sheet family-E fixture runs through the D1 recipe exactly as
docs/acfc/GENIE_RUN_pair_2.md lists it, and through the harness's
extract-frd path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from codegen import cli

FEEDS = ["nb_cm_north", "nb_cm_south", "nb_cm_east", "nb_cm_west", "nb_cm_additional"]
OVERLAY = Path(__file__).resolve().parents[1] / "config" / "overlays" / "acfc_env.yaml"


@pytest.fixture
def run_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(OVERLAY))   # acfc_prx catalogs
    for name in ("state", "out"):
        (tmp_path / name).mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    return tmp_path


def _documents(tmp_path, *, workbook=None, frd_bytes=None):
    sttm, frd = tmp_path / "STTM.xlsx", tmp_path / "FRD.docx"
    (workbook or fm.build_sttm()).save(sttm)
    frd.write_bytes(frd_bytes or fm.build_frd())
    return sttm, frd


def _generate(capsys, frd_json, sttm_json) -> tuple[int, str]:
    capsys.readouterr()
    code = cli.main(["generate", "--frd-contract", str(frd_json), "--sttm-contract",
                     str(sttm_json), "--output-mode", "framework", "--profile", "acfc_prx",
                     "--iig-template", "iig_v2", "--skip-tests"])
    return code, capsys.readouterr().out


def _verdicts(out: str) -> dict[str, str]:
    verdicts = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) > 1 and parts[0] in ("PASS", "PASS_WITH_FLAGS", "FAIL"):
            verdicts[parts[1]] = parts[0]
    return verdicts


def test_the_genie_run_recipe_exactly(run_env, capsys):
    """docs/acfc/GENIE_RUN_pair_2.md step 3, command for command."""
    sttm, frd = _documents(run_env)
    answers = run_env / "answers.yaml"
    answers.write_text("answers: []\n", encoding="utf-8")
    frd_json, sttm_json = run_env / "frd.json", run_env / "sttm.json"
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--require-complete",
                     "--frd-contract-out", str(frd_json), "--answers", str(answers)]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_json),
                     "--out", str(sttm_json), "--answers", str(answers)]) == 0
    code, out = _generate(capsys, frd_json, sttm_json)
    assert code == 0, out
    assert sorted(_verdicts(out)) == sorted(FEEDS)
    assert set(_verdicts(out).values()) == {"PASS_WITH_FLAGS"}


def test_an_extract_frd_contract_is_split_by_extract_sttm(run_env, capsys):
    """The harness's path: extract-frd's ONE-feed contract straight into
    extract-sttm and generate — five feeds, the same ids as the recipe."""
    sttm, frd = _documents(run_env)
    frd_json, sttm_json = run_env / "frd.json", run_env / "sttm.json"
    assert cli.main(["extract-frd", "--docx", str(frd), "--out", str(frd_json)]) == 0
    assert len(json.loads(frd_json.read_text(encoding="utf-8"))["feeds"]) == 1
    capsys.readouterr()
    assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_json),
                     "--out", str(sttm_json)]) == 0
    out = capsys.readouterr().out
    assert "NOTE           frd.split — frd_feeds_split_at_extract:" in out
    contract = json.loads(sttm_json.read_text(encoding="utf-8"))
    assert [f["feed_id"] for f in contract["feeds"]] == FEEDS
    assert len(contract["frd_split"]["feeds"]) == 5
    code, out = _generate(capsys, frd_json, sttm_json)
    assert code == 0, out
    assert sorted(_verdicts(out)) == sorted(FEEDS)
    (report,) = (run_env / "out").rglob("reports/nb_cm_north.md")
    assert "frd_feeds_split_at_extract:" in report.read_text(encoding="utf-8")


def test_an_unnamed_frd_feed_is_named_per_sheet_never_unnamed(run_env, capsys):
    """The FRD names no feed ("feed 1 (unnamed)"): each feed is named from its
    sheet's File Name row, else the sheet name."""
    frd_bytes = fm.build_frd(name="")
    for workbook, expected in ((fm.build_sttm(), FEEDS),
                               (fm.build_sttm(own_file_rows=False),
                                ["cm_north", "cm_south", "cm_east", "cm_west", "cm_additional"])):
        sttm, frd = _documents(run_env, workbook=workbook, frd_bytes=frd_bytes)
        frd_json, sttm_json = run_env / "frd.json", run_env / "sttm.json"
        assert cli.main(["extract-frd", "--docx", str(frd), "--out", str(frd_json)]) == 0
        (only,) = json.loads(frd_json.read_text(encoding="utf-8"))["feeds"]
        assert "(unnamed)" in only["feed_name"]
        assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract",
                         str(frd_json), "--out", str(sttm_json)]) == 0, capsys.readouterr().out
        contract = json.loads(sttm_json.read_text(encoding="utf-8"))
        assert [f["feed_id"] for f in contract["feeds"]] == expected
        assert not any("unnamed" in f["feed_name"] for f in contract["frd_split"]["feeds"])


def _distinct_tables_workbook():
    """Each mapping sheet maps into its OWN table; the FRD names only the
    first — the shape the old rule left unsplit (extract-sttm then stopped)."""
    workbook = fm.build_sttm()
    for sheet in fm.FILES:
        ws = workbook[sheet]
        for row in ws.iter_rows():
            for cell in row:
                if cell.value == fm.TABLE:
                    cell.value = f"{fm.TABLE}_{sheet.lower()}"
    return workbook


def test_one_feed_and_n_sheets_always_splits(run_env, capsys):
    frd_bytes = fm.build_frd(table=f"{fm.TABLE}_cm_north")
    sttm, frd = _documents(run_env, workbook=_distinct_tables_workbook(), frd_bytes=frd_bytes)
    frd_json, sttm_json = run_env / "frd.json", run_env / "sttm.json"
    # the layout stage splits it ...
    assert cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd),
                     "--frd-contract-out", str(frd_json)]) == 0
    assert len(json.loads(frd_json.read_text(encoding="utf-8"))["feeds"]) == 5
    # ... and so does extract-sttm when handed extract-frd's one feed.
    assert cli.main(["extract-frd", "--docx", str(frd), "--out", str(frd_json)]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_json),
                     "--out", str(sttm_json)]) == 0, capsys.readouterr().out
    assert len(json.loads(sttm_json.read_text(encoding="utf-8"))["feeds"]) == 5


def test_a_contract_that_split_nothing_has_no_frd_split_key(run_env):
    """A one-sheet workbook: nothing to split, the STTM contract JSON has no
    ``frd_split`` key (every existing contract stays byte-identical)."""
    workbook = fm.build_sttm({"CM_NORTH": fm.FILES["CM_NORTH"]})
    sttm, frd = _documents(run_env, workbook=workbook,
                           frd_bytes=fm.build_frd([fm.FILES["CM_NORTH"]]))
    frd_json, sttm_json = run_env / "frd.json", run_env / "sttm.json"
    assert cli.main(["extract-frd", "--docx", str(frd), "--out", str(frd_json)]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_json),
                     "--out", str(sttm_json)]) == 0
    assert "frd_split" not in json.loads(sttm_json.read_text(encoding="utf-8"))
