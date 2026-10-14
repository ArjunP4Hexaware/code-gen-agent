"""The LOB lookup (2026-10-14, D1 pair_12 ADLS_DELTA).

The FRD's LOB cell held a Region / LOB table and the agent wrote the whole table,
comma-joined, into every row's LOB cell. The golden has ONE LOB per file row,
keyed by the file's plan id (several files share one LOB). Now each file takes
ONE LOB from, in order: the FRD table's plan-id column, its region column (a
region token in the file name), the client ``conventions.lob_reference``; files
none of them keys are asked in ONE question for the feed (the files as keys,
the FRD's LOB codes as candidates) and their cells stay open. A single-code
column holding a list or a header word fails the gate (iig_single_value).

All names synthetic: plan ids 13xx in ``SYNCOB_1022_13xx_COBReport_*_P_I_1_T.txt``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from codegen import cli
from codegen.resolve.files import (
    key_files_by_lob_table,
    lob_table_from_lines,
    lob_table_from_rows,
    parse_lob_answer,
)
from test_iig_corpus_cells import _acfc, _pair11
from test_iig_v2_derivations import _rows, _write_overlay

ADLS, STG = "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET"
LOB_HEADERS = ["LOB", "Line of Business", "LOB Code"]
PLAN, REGION = ["Plan ID", "Plan"], ["Region", "REG#"]

# 18 files; 14 LOB codes; 7200 shared by FIVE files (the CAQH golden's shape)
PLANS = ["1340", "1341", "1342", "1343", "1364", "1356", "1357", "1345", "1346", "1347",
         "1355", "1353", "1352", "1354", "1358", "1359", "1362", "1363"]
LOBS = ["0100", "0500", "0530", "0540", "0550", "0900", "1200", "2400", "2600", "5400",
        "6400", "7100", "7200", "7200", "7200", "7200", "7200", "7700"]
PLAN_LOB = dict(zip(PLANS, LOBS, strict=True))
FILES = [f"SYNCOB_1022_{p}_COBReport_*_P_I_1_T.txt" for p in PLANS]
CODES = list(dict.fromkeys(LOBS))
# The home CAQH shape: region -> LOB only, no plan id (region tokens are not in
# the file names)
REGION_TABLE = [{"Region": f"REG#{1 + i // 3}", "LOB": code} for i, code in enumerate(CODES)]


def _with_feed(tmp_path, *, lob_table, overlay: Path | None = None):
    """pair_11's first feed with the 18 files + a LOB table (FRD contract)."""
    config, specs, (frd, sttm) = _pair11(tmp_path)
    if overlay is not None:
        from test_derivations import _scoped

        config = _scoped(_acfc(overlay), tmp_path)
    data = json.loads(frd.read_text(encoding="utf-8"))
    feed = next(f for f in data["feeds"]
                if cli.normalize_feed_name(f["feed_name"]) == specs[0].feed_id)
    feed["file_name_patterns"] = list(FILES)
    feed["lobs"] = list(CODES)
    feed["lob_table"] = lob_table
    frd.write_text(json.dumps(data), encoding="utf-8")
    return config, specs[0].feed_id, (frd, sttm)


def _generate(config, pair, feed, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True,
                          output_mode=["framework"], conventions_profile="acfc_prx",
                          iig_template="iig_v2", only_feed=feed, **kw)


def _xlsx(tmp_path, feed) -> Path:
    return next((tmp_path / "out").rglob("config_rows.xlsx"))


def _plan(pattern: str) -> str:
    return pattern.split("_")[2]


def test_a_plan_id_column_keys_every_file_one_lob_shared_by_five(tmp_path, capsys):
    table = [{"Region": "REG#1", "Plan ID": p, "LOB": PLAN_LOB[p]} for p in PLANS]
    config, feed, pair = _with_feed(tmp_path, lob_table=table)
    code = _generate(config, pair, feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK, out
    assert "QUESTION" not in out
    rows = _rows(_xlsx(tmp_path, feed), ADLS)
    assert len(rows) == 18
    for row in rows:
        lob = row["LOB"][0]
        assert lob == PLAN_LOB[next(p for p in PLANS if p in str(row["SRC_FILE_NAME"][0]))]
        assert "," not in lob and row["TGT_PARTITION_VALUE"][0] == lob
    assert sum(r["LOB"][0] == "7200" for r in rows) == 5
    # the source that resolved it is a NOTE on the rows; STGDELTA (one row per
    # table, 14 LOBs among its files) stays open — never the list
    report = next((tmp_path / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "iig_lob:ADLS_DELTA_INGESTION_DETAILS.LOB — the file's LOB from the FRD LOB " \
           "table's plan-id column" in report
    (stg,) = _rows(_xlsx(tmp_path, feed), STG)
    assert stg["LOB"][0] in (None, "")
    assert "lob_multi_value_open:STGDELTA_STDDELTA_INGESTION_DET.LOB" in report


def test_the_home_caqh_shape_asks_one_question_with_18_keys(tmp_path, capsys):
    """A region-only table (no plan ids, no region token in the file names):
    ONE question for the feed, the 18 files as keys, the FRD codes as
    candidates; exit 3; the workbook is written with the LOB cells open."""
    config, feed, pair = _with_feed(tmp_path, lob_table=REGION_TABLE)
    code = _generate(config, pair, feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_NEEDS_ANSWERS
    questions = [ln for ln in out.splitlines() if ln.startswith("QUESTION")]
    assert len(questions) == 1
    assert questions[0].startswith("QUESTION       feeds[")
    assert ".lob_by_file — file-to-LOB mapping for 18 files; FRD lists LOB codes " \
           + ", ".join(CODES) in questions[0]
    from test_harness_answer_lines import _NEEDED_KEY_RE

    assert _NEEDED_KEY_RE.match(questions[0]) is not None
    template = yaml.safe_load((tmp_path / "out" / "answers_template.yaml")
                              .read_text(encoding="utf-8"))
    ((key, entry),) = template["gaps"].items()
    assert key.endswith(".lob_by_file")
    assert list(entry["files"]) == FILES and set(entry["files"].values()) == {""}
    assert entry["candidates"] == CODES
    rows = _rows(_xlsx(tmp_path, feed), ADLS)
    assert all(r["LOB"][0] in (None, "") for r in rows)       # never the table
    report = next((tmp_path / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "**Answers owed** — questions: 1," in report
    # one answers block fills all 18 (values quoted: YAML would read 0100 as 64)
    entry["files"] = {name: PLAN_LOB[_plan(name)] for name in FILES}
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"gaps": {key: {"files": entry["files"]}}},
                                      default_style='"'), encoding="utf-8")
    code = _generate(config, pair, feed, answers_path=answers)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK and "QUESTION" not in out
    rows = _rows(_xlsx(tmp_path, feed), ADLS)
    assert [r["LOB"][0] for r in rows] == [PLAN_LOB[_plan(f)] for f in FILES]


def test_the_same_shape_with_a_lob_reference_overlay_asks_nothing(tmp_path, capsys):
    overlay = _write_overlay(tmp_path, "conventions:\n  lob_reference:\n"
                             + "".join(f'    "{p}": "{lob}"\n' for p, lob in PLAN_LOB.items()))
    config, feed, pair = _with_feed(tmp_path, lob_table=REGION_TABLE, overlay=overlay)
    code = _generate(config, pair, feed)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK and "QUESTION" not in out
    rows = _rows(_xlsx(tmp_path, feed), ADLS)
    assert [r["LOB"][0] for r in rows] == [PLAN_LOB[_plan(f)] for f in FILES]
    report = next((tmp_path / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "the file's LOB from the client lob_reference table" in report


def test_the_lookup_order_plan_then_region_then_reference():
    from codegen.contracts.tables import FeedFile

    def file(name):
        return FeedFile(pattern=name, lob=None, template=name, provenance="p")

    table = [{"Region": "REG#1", "Plan ID": "1340", "LOB": "0100"},
             {"Region": "REG#2", "Plan ID": "", "LOB": "0900"}]
    files = [file("A_1340_X.txt"), file("B_REG2_X.txt"), file("C_1999_X.txt"),
             file("D_7777_X.txt")]
    keyed, unmatched = key_files_by_lob_table(
        files, table, "LOB", plan_headers=PLAN, region_headers=REGION,
        reference={"1999": "5400", "<<D1:LOB_REFERENCE.plan_id>>": "x"})
    assert [(f.lob, f.lob_source) for f in keyed] == [
        ("0100", "frd_plan"), ("0900", "frd_region"), ("5400", "lob_reference"), (None, None)]
    assert unmatched == ["D_7777_X.txt"]
    # an answer wins; a key shorter than 3 characters never matches ("_1_")
    keyed, unmatched = key_files_by_lob_table(
        [file("D_7777_X.txt"), file("E_1_X.txt")], [{"Plan": "1", "LOB": "0100"}], "LOB",
        plan_headers=PLAN, region_headers=REGION, answers=parse_lob_answer("7777=2600"))
    assert [f.lob for f in keyed] == ["2600", None] and unmatched == ["E_1_X.txt"]


def test_the_table_is_read_from_a_nested_table_or_flattened_lines():
    rows = [["Region", "LOB"], ["REG#1", "0100"], ["REG#1", "0500"], ["", ""]]
    assert lob_table_from_rows(rows, LOB_HEADERS) == [
        {"Region": "REG#1", "LOB": "0100"}, {"Region": "REG#1", "LOB": "0500"}]
    lines = ["Region", "LOB", "REG#1", "0100", "REG#2", "0900"]
    assert lob_table_from_lines(lines, LOB_HEADERS, [*PLAN, *REGION]) == [
        {"Region": "REG#1", "LOB": "0100"}, {"Region": "REG#2", "LOB": "0900"}]
    # a plain list of LOB codes is no table
    assert lob_table_from_lines(["0100", "0500"], LOB_HEADERS, [*PLAN, *REGION]) == []
    assert lob_table_from_lines(["Region", "LOB", "REG#1"], LOB_HEADERS, REGION) == []


def test_the_frd_reader_turns_the_lob_cell_table_into_codes_plus_rows():
    from types import SimpleNamespace

    from codegen.config import load_config
    from codegen.extract.frd_docx import DocxContent, _lobs_and_table
    from test_iig_v2_derivations import REPO

    frd_cfg = load_config(REPO / "config" / "config.yaml").extractor.frd
    source = SimpleNamespace(table=3, row=2, col=1)
    profile = SimpleNamespace(fields={"feeds[0].lobs": source})
    nested = [["Region", "LOB"], *([f"REG#{1 + i // 3}", c] for i, c in enumerate(CODES))]
    content = DocxContent(tables=[], paragraphs=[], nested={(3, 2, 1): nested})
    flags: list[str] = []
    lobs, table = _lobs_and_table(content, profile, "feeds[0]", "\n".join(sum(nested, [])),
                                  frd_cfg, flags, lambda _p: "table 3 row 2 ('LOB')")
    assert lobs == CODES and len(table) == len(CODES)
    assert flags[0].startswith("frd_lob_table:feeds[0].lobs — ")
    # an ordinary list cell is unchanged
    lobs, table = _lobs_and_table(DocxContent(tables=[], paragraphs=[]),
                                  SimpleNamespace(fields={}), "feeds[0]", "MD, PA", frd_cfg,
                                  [], lambda _p: "")
    assert (lobs, table) == (["MD", "PA"], [])


def test_answers_files_block_and_a_number_is_refused(tmp_path):
    from codegen.layout.answers import AnswersFileError, load_answers

    path = tmp_path / "a.yaml"
    path.write_text('gaps:\n  "feeds[0].lob_by_file":\n    files:\n      "A_1340.txt": "0100"\n'
                    '      "B_1341.txt": ""\n', encoding="utf-8")
    assert load_answers(path).gaps["feeds[0].lob_by_file"]["value"] == "A_1340.txt=0100"
    path.write_text('gaps:\n  "feeds[0].lob_by_file":\n    files:\n      "A_1340.txt": 0100\n',
                    encoding="utf-8")
    with pytest.raises(AnswersFileError, match="quoted"):
        load_answers(path)
    path.write_text('gaps:\n  "feeds[0].lob_by_file":\n    files:\n      "A.txt": ""\n',
                    encoding="utf-8")
    assert load_answers(path).gaps == {}                      # an empty block is no answer


def test_a_multi_value_single_code_cell_fails_the_gate_with_its_address(tmp_path):
    from openpyxl import Workbook

    from codegen.config import DerivationsConfig
    from codegen.gate.derivations import (
        check_iig_workbooks_single_value,
        single_value_problem,
    )

    cfg = DerivationsConfig()
    assert single_value_problem("LOB", "0100", cfg) is None
    assert single_value_problem("LOB", "Region,LOB,REG#1,0100", cfg).startswith("a list")
    assert single_value_problem("LOB", "REG#1", cfg) == "a header word ('REG#')"
    assert single_value_problem("CLAIM_TYPE_ID", "1;2", cfg).startswith("a list")
    assert single_value_problem("ACTIVE_FLAG", "Y", cfg) is None
    assert single_value_problem("SRC_COLUMNS", "a,b", cfg) is None      # not single-code
    path = tmp_path / "x_IIG.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = ADLS
    sheet.append(["OBJECT_ID", "LOB", "ACTIVE_FLAG"])
    sheet.append(["1", "0100", "Y"])
    sheet.append(["2", "Region,LOB,REG#1,0100", "Y"])
    workbook.save(path)
    check = check_iig_workbooks_single_value([path], cfg)
    assert not check.passed
    assert f"x_IIG.xlsx {ADLS}!B3 (LOB): a list" in check.details


def test_the_app_asks_the_lob_question_as_one_files_block_and_applies_it(tmp_path):
    """post47: the App's Answers-needed dialog — the feed's LOB question is ONE
    item, kind ``files`` (the 18 files as keys, the FRD's codes the dropdown),
    answered as a gaps value; the re-run keys every file, and the answers it
    applied are written as an answers file with every value quoted."""
    from codegen.layout.answers import load_answers
    from codegen.layout.answers_template import write_applied_answers
    from codegen.layout.resolve import parse_answers
    from codegen.resolve.resolver import lob_question_item, resolve_pair

    config, feed, (frd, sttm) = _with_feed(tmp_path, lob_table=REGION_TABLE)
    (spec,) = [s for s in resolve_pair(frd, sttm, config) if s.feed_id == feed]
    question = lob_question_item(spec)
    assert question["kind"] == "files" and question["key"] == spec.lob_question_key
    assert question["files"] == FILES                                  # 18 keys, one block
    assert [c["value"] for c in question["candidates"]] == CODES
    assert question["reason"].startswith("file-to-LOB mapping for 18 files; FRD lists")
    pytest.importorskip("fastapi")
    from ui.backend.demo import needs_answer_item

    item = needs_answer_item(question, feed_name=feed)
    assert (item["label"], item["section"], item["answer_as"]) == ("QUESTION", "gaps", "gap")
    # the dialog posts "<file>=<code>; ..." (codes as text — 0100, never 64)
    value = "; ".join(f"{name}={PLAN_LOB[_plan(name)]}" for name in FILES)
    posted = parse_answers({"gaps": {question["key"]: {"value": value, "source": "user"}}})
    gaps = {key: entry["value"] for key, entry in posted["gaps"].items()}
    (answered,) = [s for s in resolve_pair(frd, sttm, config, gaps=gaps) if s.feed_id == feed]
    assert lob_question_item(answered) is None
    assert [f.lob for f in answered.files] == [PLAN_LOB[_plan(name)] for name in FILES]
    # the applied answers, as an answers file: a files: block, every value quoted
    path = write_applied_answers(tmp_path / "answers.yaml", gaps, stage="this App run")
    text = path.read_text(encoding="utf-8")
    assert f'      "{FILES[0]}": "0100"' in text
    raw = yaml.safe_load(text)["gaps"][question["key"]]["files"]
    assert raw[FILES[0]] == "0100" and all(isinstance(v, str) for v in raw.values())
    assert load_answers(path).gaps[question["key"]]["value"] == value
