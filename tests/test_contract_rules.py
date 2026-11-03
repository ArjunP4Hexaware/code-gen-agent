"""post74 (D1 post73 pair_10): "Contract fails validation at STTM sheet 2" named
no rule. Every check the STTM contract model can fail is a named rule
(codegen.run_errors.CONTRACT_RULES) with a disposition: a ``question`` holds
the feed back with one blocking QUESTION per value; a ``fail`` FAILs with
"contract validation: <rule> (<n>)" on the coordinates line, the details in
the full tier.

The pair_10 shape: the FRD and the STTM state no file format. At bcb6105 the
synthetic fixture stopped with "FAIL            extract-sttm — contract fails
validation at STTM sheet 2 [ExtractionError]"."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from codegen.contracts.sttm import SttmFeed
from codegen.contracts.validation import classify, rule_counts
from codegen.extract import extract_contract
from codegen.extract.extractor import NeedsAnswersError
from codegen.extract.generic import GenericExtractionError, contract_invalid
from codegen.run_errors import (
    CONTRACT_RULES,
    MARKER,
    Coord,
    coordinate_line,
    error_marker,
    first_error_line,
)
from post73_pairs import frd, mapping_workbook

REPO = Path(__file__).resolve().parents[1]
DATE = "2026-01-01"


def test_every_rule_has_a_disposition_and_the_model_raises_only_named_rules():
    assert {d for d, _what in CONTRACT_RULES.values()} == {"question", "fail"}
    source = (REPO / "src" / "codegen" / "contracts" / "sttm.py").read_text(encoding="utf-8")
    raised = set(re.findall(r'\("([a-z_]+)",\s*\n?\s*f?"', source)) & {
        r for r in re.findall(r'"([a-z]+(?:_[a-z]+)+)"', source)}
    model_rules = {r for r in raised if r in CONTRACT_RULES or r.endswith(("_mismatch",
                                                                          "_column", "_table",
                                                                          "_fields", "_id"))}
    assert model_rules and model_rules <= set(CONTRACT_RULES)


def test_most_rules_are_questions():
    questions = [r for r, (d, _w) in CONTRACT_RULES.items() if d == "question"]
    assert len(questions) > len(CONTRACT_RULES) / 2


def test_pair10_shape_is_a_question_not_a_fail(config, tmp_path):
    with pytest.raises(NeedsAnswersError) as caught:
        extract_contract(mapping_workbook(tmp_path / "p10.xlsx"),
                         frd(tmp_path / "frd.json", file_format=None, delimiter=None), config,
                         generated_date=DATE)
    (pending,) = caught.value.pending
    assert pending.key == "feeds[0].file_format"
    assert pending.reason.startswith("contract validation: value_unstated")


def test_the_answer_fills_the_value(config, tmp_path):
    contract = extract_contract(
        mapping_workbook(tmp_path / "p10.xlsx"),
        frd(tmp_path / "frd.json", file_format=None, delimiter=None), config,
        generated_date=DATE, gaps={"feeds[0].file_format": {"value": "txt"}})
    (feed,) = contract.feeds
    assert feed.source_file.format == "txt"
    assert any(f.startswith("answered_value:feeds[0].file_format") for f in feed.extraction_flags)


def test_a_fail_rule_names_itself_and_its_count_on_the_first_line(config, tmp_path):
    contract = extract_contract(mapping_workbook(tmp_path / "p.xlsx"),
                                frd(tmp_path / "frd.json"), config, generated_date=DATE)
    data = contract.feeds[0].model_dump(by_alias=True)
    data["field_count"] = 99
    data["load_rules"]["phi_columns"] = ["Claim Number"]
    with pytest.raises(ValueError) as caught:
        SttmFeed.model_validate(data)
    hits = classify(caught.value)
    assert rule_counts(hits) == {"field_count_mismatch": 1, "phi_mismatch": 1}
    exc = contract_invalid(GenericExtractionError, "FEED_5 claims", hits,
                           Coord("STTM", sheet=2))
    marker = error_marker("extract-sttm", "sttm.unreadable", Coord("STTM"), exc=exc)
    assert coordinate_line(json.loads(marker[len(MARKER):])) == (
        "FAIL            extract-sttm — contract validation: field_count_mismatch (1), "
        "phi_mismatch (1) at STTM sheet 2 [GenericExtractionError]")
    assert "field_count is 99" in str(exc)            # the details: full tier only


def test_the_coordinates_line_names_rules_and_counts():
    line = coordinate_line({"stage": "extract-sttm", "reason": "contract.invalid",
                            "coord": {"doc": "STTM", "sheet": 2},
                            "rules": {"segment_without_table": 2, "not_a_rule": 1}})
    assert line == ("FAIL            extract-sttm — contract validation: "
                    "segment_without_table (2) at STTM sheet 2")


def test_pair10_shape_through_the_cli_exits_3_and_asks(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    args = [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook",
            str(mapping_workbook(tmp_path / "p10.xlsx")), "--frd-contract",
            str(frd(tmp_path / "frd.json", file_format=None, delimiter=None)),
            "--out", str(tmp_path / "sttm.json"),
            "--config", str(REPO / "config" / "config.yaml")]
    done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False,
                          env=env, cwd=tmp_path)
    assert done.returncode == 3, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None
    assert any(line.startswith("QUESTION       feeds[0].file_format — ")
               for line in done.stdout.splitlines())
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"gaps": {"feeds[0].file_format": {"value": "txt"}}}),
                       encoding="utf-8")
    again = subprocess.run([*args, "--answers", str(answers)], capture_output=True, text=True,
                           encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert again.returncode == 0, again.stdout + again.stderr
