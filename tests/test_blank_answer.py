"""post170: a blank answer lets the run through (Soham, 2026-11-05).

A data engineer could not answer "What format are the source files in?" and the
feed stayed held back - no workbook at all. "A blank answer is still better than
no answer because there's still a partial workbook": for the values that only fill
IIG / config cells (``answers.blankable_fields``: file format, delimiter,
frequency), the card's "Leave blank and continue" answers the reserved token
``answers.leave_blank``. The feed is generated; the cells that value fills are
blank and flagged; the run reports a non-blocking open input, never NEEDS_ANSWERS;
the DDL is byte-identical to the run with the value typed in (it never used it).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from codegen import cli
from codegen.config import load_config
from post73_pairs import frd, mapping_workbook

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-01-01"


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _run(tmp_path: Path, monkeypatch, capsys, answer: str) -> tuple[int, int, str, Path]:
    """extract-sttm + generate (framework, acfc_prx, iig_v2, mock) on the pair_10
    shape - neither document states a file format - with ``answer`` for it."""
    work = tmp_path / answer.strip("()<> ").replace(" ", "_")
    (work / "out").mkdir(parents=True)
    overlay = work / "overlay.yaml"
    overlay.write_text(f"output:\n  dir: {(work / 'out').as_posix()}\n", encoding="utf-8")
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(overlay))
    answers = work / "answers.yaml"
    delimiter = "|" if answer == "txt" else answer      # no format = no delimiter either
    answers.write_text(yaml.safe_dump({"gaps": {"feeds[0].file_format": {"value": answer},
                                                "feeds[0].delimiter": {"value": delimiter}}}),
                       encoding="utf-8")
    frd_path = frd(work / "frd.json", file_format=None, delimiter=None)
    sttm = work / "sttm.contract.json"
    extract = cli.main(["extract-sttm", "--workbook", str(mapping_workbook(work / "p10.xlsx")),
                        "--frd-contract", str(frd_path), "--out", str(sttm),
                        "--generated-date", DATE, "--answers", str(answers)])
    generate = -1
    if extract == 0:
        generate = cli.main(["generate", "--frd-contract", str(frd_path), "--sttm-contract",
                             str(sttm), "--output-mode", "framework", "--profile", "acfc_prx",
                             "--iig-template", "iig_v2", "--skip-tests", "--dry-run",
                             "--answers", str(answers)])
    return extract, generate, capsys.readouterr().out, work / "out"


def _ddl(out: Path) -> bytes:
    (ddl,) = list(out.glob("*/framework/*_DDL.txt"))
    return ddl.read_bytes()


def test_the_blank_token_and_the_blankable_fields_are_config(config):
    assert config.answers.leave_blank
    assert set(config.answers.blankable_fields) == {"file_format", "delimiter", "frequency"}


def test_a_blank_file_format_generates_the_feed(tmp_path, monkeypatch, capsys, config):
    extract, generate, out, root = _run(tmp_path, monkeypatch, capsys,
                                        config.answers.leave_blank)
    assert (extract, generate) == (0, 0), out
    assert "NEEDS_ANSWERS" not in out
    assert "INPUT_NEEDED" in out and "feeds[0].file_format" in out
    sttm = json.loads((root.parent / "sttm.contract.json").read_text(encoding="utf-8"))
    assert sttm["feeds"][0]["source_file"]["format"] == ""          # blank, never a value
    assert any(f.startswith("answered_blank:feeds[0].file_format")
               for f in sttm["feeds"][0]["extraction_flags"])
    assert list(root.glob("*/framework/*_IIG.xlsx"))           # the partial workbook


def test_the_ddl_never_depends_on_the_file_format(tmp_path, monkeypatch, capsys, config):
    blank = _run(tmp_path, monkeypatch, capsys, config.answers.leave_blank)
    typed = _run(tmp_path, monkeypatch, capsys, "txt")
    assert blank[:2] == typed[:2] == (0, 0)
    assert _ddl(blank[3]) == _ddl(typed[3])


def test_an_empty_answer_is_still_no_answer(tmp_path, monkeypatch, capsys):
    extract, _generate, _out, _root = _run(tmp_path, monkeypatch, capsys, "")
    assert extract == 3                                   # NEEDS_ANSWERS, as before


def test_a_blank_answer_on_a_field_that_cannot_be_blank_is_refused(config):
    from codegen.layout.answers import AnswersFileError, blank_answer

    assert blank_answer("feeds[0].file_format", config.answers.leave_blank, config)
    assert not blank_answer("feeds[0].file_format", "txt", config)
    with pytest.raises(AnswersFileError, match="stage_target.tables"):
        blank_answer("feeds[0].stage_target.tables", config.answers.leave_blank, config)


def test_only_the_cells_the_value_fills_change_and_the_token_never_leaks(
        tmp_path, monkeypatch, capsys, config):
    import openpyxl

    blank = _run(tmp_path, monkeypatch, capsys, config.answers.leave_blank)
    typed = _run(tmp_path, monkeypatch, capsys, "txt")
    assert "PASS_WITH_OPEN_INPUTS" in blank[2]
    assert [line.split()[1] for line in blank[2].splitlines()
            if line.startswith("INPUT_NEEDED")] == ["feeds[0].delimiter", "feeds[0].file_format"]
    token = config.answers.leave_blank.encode()
    assert not [p for p in blank[3].rglob("*") if p.is_file() and token in p.read_bytes()]
    (a,) = blank[3].glob("*/framework/*_IIG.xlsx")
    (b,) = typed[3].glob("*/framework/*_IIG.xlsx")
    wa, wb = openpyxl.load_workbook(a), openpyxl.load_workbook(b)
    changed = {}
    for sheet in wa.sheetnames:
        rows_a = list(wa[sheet].iter_rows(values_only=True))
        rows_b = list(wb[sheet].iter_rows(values_only=True))
        assert len(rows_a) == len(rows_b), sheet
        for ra, rb in zip(rows_a[1:], rows_b[1:], strict=True):
            for header, u, v in zip(rows_a[0], ra, rb, strict=False):
                if u != v:
                    changed[f"{sheet}.{header}"] = (u, v)
    assert changed == {"ADLS_DELTA_INGESTION_DETAILS.SRC_FILE_DELIMITER": (None, "|")}


# -- the App path (DemoRunner, mock, tmp storage roles) ------------------------------

@pytest.fixture()
def app_roles(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    for role in ("state", "outputs"):
        (tmp_path / role).mkdir()
        monkeypatch.setenv(f"CODEGEN_STORAGE_{role.upper()}",
                           f"local:{(tmp_path / role).as_posix()}")
    return tmp_path


def _wait(runner, *states: str, timeout: float = 300.0) -> str:
    import time

    deadline = time.monotonic() + timeout
    while runner.state not in states:
        assert time.monotonic() < deadline, f"stuck in {runner.state}: {runner.stages[-3:]}"
        time.sleep(0.05)
    return runner.state


def _left(runner, state: str, timeout: float = 60.0) -> None:
    import time

    deadline = time.monotonic() + timeout
    while runner.state == state:
        assert time.monotonic() < deadline, f"still {state}: the answers were not taken"
        time.sleep(0.05)


def _silent_workbook(path: Path) -> Path:
    """The pair_10 mapping sheet with every format statement removed - the App's
    layout stage reads the STTM's meta rows and the file extension too: its "File type"
    and NOTE rows cleared, the file pattern without an extension."""
    import openpyxl

    workbook = openpyxl.load_workbook(mapping_workbook(path))
    sheet = workbook["FEED_5_MAPPING"]
    sheet["B1"], sheet["B8"], sheet["B9"] = "FEED_5_*", None, None
    workbook.save(path)
    return path


def test_the_app_asks_offers_the_blank_and_finishes_with_open_inputs(app_roles, config):
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, index_warmup=False)
    runner.selected_workbook = _silent_workbook(app_roles / "STTM_feed_5.xlsx")
    runner.select_frd(frd(app_roles / "frd.contract.json", file_format=None, delimiter=None),
                      "frd.contract.json")
    token = config.answers.leave_blank
    runner.start_live()
    gaps: dict[str, str] = {}
    for _round in range(4):
        state = _wait(runner, "needs_answers", "needs_layout", "failed", "done")
        if state == "needs_layout":
            # the before-generate dialog: the same typed questions, the same blank choice
            questions = runner.status()["layout_questions"]
            for question in questions:
                assert question["leave_blank"] == token, question["key"]
                gaps[question["key"]] = token
            runner.answer_layout({"gaps": {k: {"value": v} for k, v in gaps.items()}})
            _left(runner, "needs_layout")       # the worker takes the answers first
            continue
        if state != "needs_answers":
            break
        items = runner.status()["needs_answers"]
        assert items, runner.status()["error"]
        for item in items:
            # every value this pair leaves open may be left blank on purpose
            assert item["question"]["leave_blank"] == token, item["key"]
            gaps[item["key"]] = token
        runner.rerun_with_answers({"gaps": {k: {"value": v} for k, v in gaps.items()}})
    status = runner.status()
    assert status["state"] == "done", (status["state"], status["error"], status["stages"][-3:])
    assert sorted(gaps) == ["feeds[0].delimiter", "feeds[0].file_format"]
    assert status.get("outcome") in (None, "PASS_WITH_OPEN_INPUTS") or \
        "OPEN_INPUTS" in json.dumps(status)
    open_keys = {i["key"] for i in status["inputs_needed"]}
    assert {"feeds[0].file_format", "feeds[0].delimiter"} <= open_keys
    # the reserved answer is never a value: only the answers record may carry it
    leaks = [p.relative_to(app_roles).as_posix()
             for p in (app_roles / "outputs").rglob("*")
             if p.is_file() and p.name != "answers.yaml" and token.encode() in p.read_bytes()]
    assert leaks == []
