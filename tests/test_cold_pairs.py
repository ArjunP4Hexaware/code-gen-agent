"""Chunk B (2026-10-09) — the cold-pair drill.

Six synthetic FRD + STTM pairs designed BLIND to the reader code
(``tests/acfc_shapes/COLD_PAIRS.md``, builders ``tests/acfc_shapes/cold_pairs.py``,
fixtures ``fixtures/acfc_shapes/cold/<id>/``) run through the CLI chain the
way the ACFC harness runs it — ACFC overlay ON (``config/overlays/
acfc_env.yaml`` applies first), mock layout and Layer 2:

    layout --require-complete --frd-contract-out  ->  extract-frd  ->
    extract-sttm  ->  generate --output-mode framework --profile acfc_prx
                                --iig-template iig_v2

Pinned per pair (``expected_questions.yaml``): every stage's exit code and the
label + answers.yaml key of every QUESTION / UNRESOLVED line BEFORE answers
(parsed with the harness's own regex); every such key is settled by the
pair's ``answers.yaml``; and with that file the whole chain completes — exit 0
at every stage, no answer line left, no FAIL, every feed PASS_WITH_FLAGS.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from acfc_shapes import cold_pairs
from codegen import cli
from test_harness_answer_lines import _NEEDED_KEY_RE

REPO = Path(__file__).resolve().parents[1]
COLD = REPO / "fixtures" / "acfc_shapes" / "cold"
PAIRS = list(cold_pairs.PAIRS)
DATE = "2026-10-09"


@pytest.fixture()
def cold_env(monkeypatch, tmp_path):
    """The harness's environment: the ACFC overlay ON (conftest switches it
    off for the suite), mock layout + provider, state / outputs outside the repo."""
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.delenv("CODEGEN_CONFIG_OVERLAYS", raising=False)
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl.prodsupport@synthetic.example")
    state, outputs = tmp_path / "state", tmp_path / "outputs"
    state.mkdir()
    outputs.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{outputs.as_posix()}")
    return tmp_path


def _paths(pair: str) -> tuple[Path, Path]:
    return (REPO / "fixtures" / "acfc_shapes" / cold_pairs.sttm_path(pair),
            REPO / "fixtures" / "acfc_shapes" / cold_pairs.frd_path(pair))


def _needed(out: str) -> list[list[str]]:
    """[label, key] of every QUESTION / UNRESOLVED line, as the harness reads it."""
    return [[m.group(0).split()[0], m.group(1)] for line in out.splitlines()
            if (m := _NEEDED_KEY_RE.match(line))]


def _run(capsys, argv: list[str]) -> tuple[int, str]:
    capsys.readouterr()
    code = cli.main(argv)
    return code, capsys.readouterr().out


def _chain(pair: str, tmp: Path, capsys, answers: Path | None = None) -> dict:
    sttm, frd = _paths(pair)
    frd_out, sttm_out = tmp / "frd.contract.json", tmp / "sttm.contract.json"
    extra = ["--answers", str(answers)] if answers else []
    stages: dict = {}
    stages["layout"] = _run(capsys, [
        "layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run", "--no-cache",
        "--require-complete", "--frd-contract-out", str(frd_out), *extra])
    if answers is None:
        stages["extract_frd"] = _run(capsys, ["extract-frd", "--docx", str(frd), "--out",
                                              str(tmp / "frd_extract.contract.json")])
    stages["extract_sttm"] = _run(capsys, [
        "extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_out),
        "--out", str(sttm_out), "--generated-date", DATE, *extra])
    stages["generate"] = (_run(capsys, [
        "generate", "--frd-contract", str(frd_out), "--sttm-contract", str(sttm_out),
        "--dry-run", "--skip-tests", "--output-mode", "framework", "--profile", "acfc_prx",
        "--iig-template", "iig_v2"]) if sttm_out.exists() else None)
    return stages


def _expected(pair: str) -> dict:
    return yaml.safe_load((COLD / pair / "expected_questions.yaml").read_text(encoding="utf-8"))


def _answers(pair: str) -> dict:
    return yaml.safe_load((COLD / pair / "answers.yaml").read_text(encoding="utf-8"))


# ------------------------------------------------------------- before answers


@pytest.mark.parametrize("pair", PAIRS)
def test_cold_pair_asks_exactly_the_pinned_questions(pair, cold_env, capsys):
    stages = _chain(pair, cold_env, capsys)
    expected = _expected(pair)
    for stage in ("layout", "extract_frd", "extract_sttm"):
        code, out = stages[stage]
        lines = _needed(out)
        assert code == expected[stage]["exit"], (stage, out)
        assert lines == expected[stage]["lines"], (stage, lines)
        keys = [key for _label, key in lines]
        assert len(keys) == len(set(keys)), (stage, "duplicate answer lines")
        assert "Traceback" not in out
    # Every sheet is held back: extract-sttm writes no contract, generate never runs.
    assert stages["generate"] is None and expected["generate"] is None


@pytest.mark.parametrize("pair", PAIRS)
def test_every_pinned_key_is_settled_by_the_answers_file(pair):
    """No unanswerable key: an UNRESOLVED key is a column placement or a band
    layer under ``answers:``; a QUESTION key a value under ``gaps:``."""
    answers = _answers(pair)
    placed = {f"{a['sheet']}/{a['layer']}/{a['role']}" for a in answers.get("answers") or []}
    gaps = set(answers.get("gaps") or {})
    for stage in ("layout", "extract_frd", "extract_sttm"):
        for label, key in _expected(pair)[stage]["lines"]:
            if label == "UNRESOLVED":
                assert key in placed, (stage, key)
            else:
                assert key in gaps, (stage, key)


# -------------------------------------------------------------- with answers


@pytest.mark.parametrize("pair", PAIRS)
def test_cold_pair_completes_after_the_answers(pair, cold_env, capsys):
    stages = _chain(pair, cold_env, capsys, answers=COLD / pair / "answers.yaml")
    for stage in ("layout", "extract_sttm"):
        code, out = stages[stage]
        assert code == cli.EXIT_OK, (stage, out)
        assert _needed(out) == [], (stage, out)
    assert stages["generate"] is not None
    code, out = stages["generate"]
    assert code == cli.EXIT_OK, out
    assert _needed(out) == [] and not re.search(r"^FAIL ", out, re.MULTILINE), out
    verdicts = re.findall(r"^(PASS_WITH_FLAGS|PASS|FAIL)\s", out, re.MULTILINE)
    assert verdicts and set(verdicts) <= {"PASS", "PASS_WITH_FLAGS"}, out


def _contract(tmp: Path, name: str) -> dict:
    return json.loads((tmp / name).read_text(encoding="utf-8"))


def test_cold_1_answers_flow_into_the_contracts(cold_env, capsys):
    """The delimiter the person chose (FRD pipe over the STTM's comma) and the
    feed named by the FRD's Name row (its Object Name is a file pattern)."""
    _chain("cold_1", cold_env, capsys, answers=COLD / "cold_1" / "answers.yaml")
    frd = _contract(cold_env, "frd.contract.json")["feeds"][0]
    assert frd["feed_name"] == "ch_claims_daily"
    assert frd["file_name_patterns"] == ["CH_CLAIMS_DAILY_YYYYMMDD.psv"]
    assert frd["delimiter"] == "|"
    sttm = _contract(cold_env, "sttm.contract.json")["feeds"][0]
    assert sttm["source_file"]["delimiter"] == "|"
    assert sttm["stage"]["schema"] == "stg_ch_claims" and sttm["standard"]["schema"] == "ch_claims"


def test_cold_2_segmented_tables_and_named_audits(cold_env, capsys):
    """Three stage tables, Detail only to standard, the filler left out and
    LOAD_TS / BATCH_ID carried as the STTM names them."""
    stages = _chain("cold_2", cold_env, capsys, answers=COLD / "cold_2" / "answers.yaml")
    frd = _contract(cold_env, "frd.contract.json")["feeds"][0]
    assert frd["stage_target"]["tables"] == ["fc_elig_hdr", "fc_elig_dtl", "fc_elig_trl"]
    assert frd["lobs"] == ["MCD", "CHIP"]                     # STTM meta row 'LOB'
    sttm = _contract(cold_env, "sttm.contract.json")["feeds"][0]
    assert "filler" not in [f["source_column"] for f in sttm["fields"]]
    assert [a["column"] for a in sttm["audit_columns"]] == ["SRC_FILE_NAME", "LOAD_TS",
                                                             "BATCH_ID"]
    out = stages["generate"][1]
    assert "PASS_WITH_FLAGS" in out
    report = next((cold_env / "outputs" / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "audit_column_framework_populated:LOAD_TS,BATCH_ID" in report
    assert "field_unmapped:filler" in report
    assert "standard_type_blank" not in report           # header / trailer are stage-only


def test_cold_4_one_feed_per_mapping_sheet(cold_env, capsys):
    _chain("cold_4", cold_env, capsys, answers=COLD / "cold_4" / "answers.yaml")
    feeds = _contract(cold_env, "frd.contract.json")["feeds"]
    assert [f["feed_name"] for f in feeds] == ["ch_rx_claim", "ch_rx_reversal"]
    assert [f["file_name_patterns"] for f in feeds] == [["CH_RX_CLM_<LOB>_YYYYMMDD.csv"],
                                                        ["CH_RX_REV_YYYYMMDD.csv"]]


def test_cold_5_audit_columns_are_the_persons(cold_env, capsys):
    _chain("cold_5", cold_env, capsys, answers=COLD / "cold_5" / "answers.yaml")
    sttm = _contract(cold_env, "sttm.contract.json")["feeds"][0]
    assert [a["column"] for a in sttm["audit_columns"]] == [
        "SRC_FILE_NAME", "REC_CREATION_TIME", "REC_UPDATED_TIME"]
    assert any(f.startswith("audit_columns_from_user:") for f in sttm["extraction_flags"])
    frd = _contract(cold_env, "frd.contract.json")["feeds"][0]
    assert frd["feed_name"] == "fc_provider_directory"        # named after the STTM band
    assert frd["stage_target"]["load_strategy"] == "Truncate and Load"
    assert frd["frequency"] == "Weekly" and frd["domain"] == "Provider"
