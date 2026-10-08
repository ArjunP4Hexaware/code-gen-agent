"""The answer lines the ACFC harness parses, and the exit-3 branches.

The harness (``codegen-watch`` / ``pull_and_run`` — not in this repo) reads
the needed answer keys of a pair from the CLI's stdout, at the end of EVERY
pair whatever the exit codes. Its contract is
``docs/acfc/HARNESS_EXIT_CODES.md`` on ``origin/acfc/harness-exit3``, whose
"Line format" section (517919c) gives the harness's own compiled regex,
``_NEEDED_KEY_RE`` in ``pull_and_run``. It is copied below VERBATIM; group 1
is the key. Every line the CLI prints for a missing answer must match it AND
have the exact form: the label padded to 15 columns, the answers.yaml key,
' — ', the reason — and the harness must capture the WHOLE key, spaces
included.

Exit codes (docs/ACFC_DEPLOY.md "CLI exit codes"): extract-sttm exits 3 only
when NO feed produced a usable contract (else 0, contract written, the
held-back sheets' QUESTION lines still printed); generate processes every feed
with a contract and exits 3 only when a feed it was asked for (--feed) had none.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from acfc_shapes import sttm as sttm_fixtures
from acfc_shapes.common import xlsx_bytes
from codegen import cli
from codegen.extract.frd_docx import contract_to_json as frd_to_json
from codegen.layout.model import MockLayoutProvider
from codegen.layout.resolve import resolve_pair

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
DATE = "2026-01-01"
BLANK_SHEET = "MAPPING-VC_DISENROLLMENT"
HELD_BACK_KEYS = ["feeds[2].stage_target.schema", "feeds[2].stage_target.tables",
                  "feeds[2].standard_target.schema", "feeds[2].standard_target.tables"]

# VERBATIM from docs/acfc/HARNESS_EXIT_CODES.md ("Line format") on
# origin/acfc/harness-exit3 — the harness's _NEEDED_KEY_RE in pull_and_run.
_NEEDED_KEY_RE = re.compile(r"^(?:QUESTION|UNRESOLVED)\s+(.+?)(?:\s+\u2014\s|$)")


def _answer_lines(out: str) -> list[dict]:
    """Every QUESTION / UNRESOLVED line, each parsed with the harness's own
    regex AND asserted to the exact column form; returns {label, key} per line
    (key = what the harness records)."""
    lines = [ln for ln in out.splitlines() if ln.startswith(("QUESTION", "UNRESOLVED"))]
    parsed = []
    for line in lines:
        match = _NEEDED_KEY_RE.match(line)
        assert match, f"the harness cannot parse {line!r}"
        label, key = line.split(" ", 1)[0], match.group(1)
        assert line[:cli.ANSWER_LABEL_WIDTH] == label.ljust(cli.ANSWER_LABEL_WIDTH), line
        assert line[cli.ANSWER_LABEL_WIDTH] != " ", line          # the key starts at column 15
        assert line[cli.ANSWER_LABEL_WIDTH:].startswith(key + " — "), line   # the WHOLE key
        assert "\n" not in line and " — " not in key
        parsed.append({"label": label, "key": key})
    return parsed


def test_a_key_with_spaces_is_captured_whole():
    key = "MAPPING- (demographics)/stage/schema"
    line = cli.answer_line("UNRESOLVED", key, "schema role unplaced (sttm)")
    assert line == ("UNRESOLVED     MAPPING- (demographics)/stage/schema — "
                    "schema role unplaced (sttm)")
    assert _NEEDED_KEY_RE.match(line).group(1) == key
    assert _answer_lines(line) == [{"label": "UNRESOLVED", "key": key}]
    # A key is printed verbatim: inner whitespace (a sheet name's double space)
    # survives; only a line break becomes a space.
    assert _answer_lines(cli.answer_line("QUESTION", "Sheet  A/stage/table", "r"))[0]["key"] \
        == "Sheet  A/stage/table"
    assert _answer_lines(cli.answer_line("QUESTION", "Sheet\nB/stage/table", "r"))[0]["key"] \
        == "Sheet B/stage/table"


def _keys(out: str, label: str = "QUESTION") -> list[str]:
    return [m["key"] for m in _answer_lines(out) if m["label"] == label]


def test_answer_line_is_the_harness_form():
    line = cli.answer_line("QUESTION", "feeds[2].stage_target.tables",
                           "every TableName cell is empty;\nno File Details target")
    assert line == ("QUESTION       feeds[2].stage_target.tables — every TableName cell "
                    "is empty; no File Details target")
    assert cli.answer_line("UNRESOLVED", "S/stage/schema", "r") == \
        "UNRESOLVED     S/stage/schema — r"
    assert _keys(line + "\n") == ["feeds[2].stage_target.tables"]


@pytest.fixture
def cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(REPO)
    return tmp_path


def _pair11_one_sheet_blank(tmp: Path, config):
    wb = sttm_fixtures.build_pair11()
    for row in wb[BLANK_SHEET].iter_rows(min_row=3):
        for index in (8, 9, 12, 13):
            row[index].value = None
    sttm = tmp / "p11.xlsx"
    sttm.write_bytes(xlsx_bytes(wb))
    pair = resolve_pair(sttm, SHAPES / "frd" / "f1_pair_11_multi_file.docx", config,
                        provider=MockLayoutProvider([]), cache_dirs=[], use_cache=False,
                        generated_date=DATE)
    frd = tmp / "frd.contract.json"
    frd.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    layout = tmp / "sttm.layout.json"
    layout.write_text(pair.sttm.profile.model_dump_json(), encoding="utf-8")
    return sttm, frd, layout


def _extract(capsys, sttm, frd, layout, out):
    capsys.readouterr()
    rc = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd),
                   "--out", str(out), "--layout", str(layout), "--generated-date", DATE])
    return rc, capsys.readouterr().out


def test_extract_with_a_usable_feed_exits_0_and_still_lists_the_held_back_answers(
        config, cli_env, capsys):
    sttm, frd, layout = _pair11_one_sheet_blank(cli_env, config)
    out_json = cli_env / "sttm.contract.json"
    rc, out = _extract(capsys, sttm, frd, layout, out_json)
    assert rc == cli.EXIT_OK, out
    assert out_json.is_file()                                       # the contract is written
    assert _keys(out) == HELD_BACK_KEYS
    # generate, NOT asked for the held-back feed: every feed with a contract runs, exit 0,
    # the held-back keys printed again.
    capsys.readouterr()
    rc = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(out_json),
                   "--output-mode", "framework", "--skip-tests", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == cli.EXIT_OK, out
    assert "PASS_WITH_FLAGS vc_enrollment" in out and "vc_individual_risk" in out
    assert _keys(out) == HELD_BACK_KEYS
    # generate ASKED for the held-back feed: exit 3, its keys only.
    capsys.readouterr()
    rc = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(out_json),
                   "--feed", "vc_disenrollment", "--output-mode", "framework",
                   "--skip-tests", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == cli.EXIT_NEEDS_ANSWERS, out
    assert _keys(out) == HELD_BACK_KEYS
    assert "PASS_WITH_FLAGS" not in out                             # nothing else generated
    # ... and asked for a feed WITH a contract: exit 0, no answer lines.
    capsys.readouterr()
    rc = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(out_json),
                   "--feed", "vc_enrollment", "--output-mode", "framework",
                   "--skip-tests", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == cli.EXIT_OK and _keys(out) == [], out


def test_extract_with_no_usable_feed_exits_3_and_writes_nothing(config, cli_env, capsys):
    sttm = cli_env / "p1.xlsx"
    sttm.write_bytes(xlsx_bytes(sttm_fixtures.build_pair1(blank_targets=True)))
    pair = resolve_pair(sttm, SHAPES / "frd" / "f1_pair_1.docx", config, provider=None,
                        cache_dirs=[], generated_date=DATE)
    frd = cli_env / "frd.contract.json"
    frd.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    layout = cli_env / "sttm.layout.json"
    layout.write_text(pair.sttm.profile.model_dump_json(), encoding="utf-8")
    out_json = cli_env / "sttm.contract.json"
    rc, out = _extract(capsys, sttm, frd, layout, out_json)
    assert rc == cli.EXIT_NEEDS_ANSWERS, out
    assert not out_json.exists()
    assert _keys(out) == ["feeds[0].stage_target.schema", "feeds[0].standard_target.schema"]


def test_unresolved_roles_under_require_complete_are_unresolved_lines(config, cli_env, capsys):
    # Family E pair 7 leaves roles open under synonyms alone (layout_truth.py).
    sttm = SHAPES / "sttm" / "pair_7_family_e.xlsx"
    frd = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
    capsys.readouterr()
    rc = cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd),
                   "--out", str(cli_env / "x.json"), "--require-complete",
                   "--generated-date", DATE])
    out = capsys.readouterr().out
    assert rc == cli.EXIT_NEEDS_ANSWERS, out
    keys = _keys(out, "UNRESOLVED")
    assert keys and all(k.count("/") == 2 for k in keys)          # <sheet>/<layer>/<role>
