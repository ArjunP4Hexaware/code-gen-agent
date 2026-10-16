"""post57 (D1 post55 pairs 03 / 04): a contract "mismatch" whose only kind is
``value.unstated`` — a value NO document states — is NEEDS_ANSWERS: exit 3,
one QUESTION per unstated value naming the contract field and the places
searched (vocabulary only), answered under ``gaps:`` and applied on the rerun.
FAIL stays for genuine conflicts (two documents, two values); the feeds that
resolve still generate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from codegen import cli
from codegen.config import load_config
from codegen.extract.extractor import contract_to_json, extract_contract
from codegen.resolve.resolver import (
    ContractMismatchError,
    ContractUnstatedError,
    resolve_pair,
)
from codegen.run_errors import MARKER, first_error_line
from post51_pairs import family_e_frd, family_e_workbook
from test_harness_answer_lines import _NEEDED_KEY_RE

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
GENERATE = ["--skip-tests", "--dry-run", "--output-mode", "framework", "--profile", "acfc_prx",
            "--iig-template", "iig_v2"]


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    (tmp_path / "out").mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    monkeypatch.chdir(REPO)
    return tmp_path


def _pair(tmp_path: Path, **frd_changes) -> tuple[Path, Path]:
    """The Family E pair (tests/post51_pairs.py) with FRD feed 0 edited."""
    frd = family_e_frd(tmp_path / "frd.json")
    data = json.loads(frd.read_text(encoding="utf-8"))
    for dotted, value in frd_changes.items():
        target = data["feeds"][0]
        *head, last = dotted.split("__")
        for part in head:
            target = target[part]
        target[last] = value
    frd.write_text(json.dumps(data), encoding="utf-8")
    sttm = tmp_path / "sttm.json"
    contract = extract_contract(family_e_workbook(tmp_path / "e.xlsx", [None]), frd,
                                load_config(CONFIG), generated_date="2026-10-15")
    sttm.write_text(contract_to_json(contract), encoding="utf-8")
    return frd, sttm


def _questions(out: str) -> list[str]:
    return [m.group(1) for ln in out.splitlines() if (m := _NEEDED_KEY_RE.match(ln))]


UNSTATED = {"lobs": [], "stage_target__load_strategy": None}


def test_unstated_values_raise_questions_not_a_mismatch(env):
    frd, sttm = _pair(env, **UNSTATED)
    with pytest.raises(ContractUnstatedError) as caught:
        resolve_pair(frd, sttm, load_config(CONFIG))
    questions = {q.key: q for q in caught.value.questions}
    assert set(questions) == {"feeds[0].lobs", "feeds[0].stage_target.load_strategy"}
    strategy = questions["feeds[0].stage_target.load_strategy"]
    assert strategy.field == "stage_target.load_strategy"
    assert "FRD Load Strategy STG" in strategy.searched and "FAQ load_mode" in strategy.searched
    assert caught.value.specs == []            # the one feed waits for its answers


def test_generate_exits_3_with_one_question_per_value_then_completes(env, capsys):
    frd, sttm = _pair(env, **UNSTATED)
    capsys.readouterr()
    code = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm),
                     *GENERATE])
    captured = capsys.readouterr()
    assert code == cli.EXIT_NEEDS_ANSWERS, captured.out
    assert sorted(_questions(captured.out)) == ["feeds[0].lobs",
                                                "feeds[0].stage_target.load_strategy"]
    line = next(ln for ln in captured.out.splitlines()
                if ln.startswith("QUESTION       feeds[0].lobs"))
    assert "value stated in no document (feed 1 of 1; contract field lobs); searched: FRD LOB" \
        in line
    assert "FAIL" not in captured.out and MARKER not in captured.err
    assert first_error_line(code, captured.err, captured.out) is None

    answers = env / "answers.yaml"
    answers.write_text(yaml.safe_dump({"gaps": {
        "feeds[0].lobs": {"value": "ALL"},
        "feeds[0].stage_target.load_strategy": {"value": "Truncate and Load"}}}),
        encoding="utf-8")
    code = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm),
                     "--answers", str(answers), *GENERATE])
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK, out
    assert _questions(out) == []


def test_a_genuine_conflict_still_fails(env, capsys):
    """Two documents, two values: the FRD says pipe, the STTM comma."""
    frd, sttm = _pair(env, lobs=[])
    contract = json.loads(sttm.read_text(encoding="utf-8"))
    contract["feeds"][0]["source_file"]["delimiter"] = ","
    sttm.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ContractMismatchError) as caught:
        resolve_pair(frd, sttm, load_config(CONFIG))
    assert not isinstance(caught.value, ContractUnstatedError)
    assert caught.value.counts == {"value.conflict": 1, "value.unstated": 1}
    capsys.readouterr()
    assert cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm),
                     *GENERATE]) == 1
    assert "FAIL" in capsys.readouterr().out
