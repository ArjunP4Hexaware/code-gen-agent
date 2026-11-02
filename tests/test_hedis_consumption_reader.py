"""post161: the HEDIS Stage -> Consumption STTM reader, family H4 -> a gold contract.

Synthetic workbook (tests/acfc_shapes/hedis_h4.py) with the shape doc's drift. The rule
under test is the gold contract's: filled when the sheet states it, proposed with a
basis when derived (a SQL Server type's Spark equivalent - the platform is unconfirmed),
a QUESTION otherwise (catalog / schema / key never guessed)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

from acfc_shapes import hedis_h4
from codegen.config import load_config
from codegen.contracts.gold import GoldContract
from codegen.layouts.hedis_consumption import HedisReadError, read_workbook

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"


@pytest.fixture(scope="module")
def cfg():
    return load_config(CONFIG).hedis_consumption


@pytest.fixture()
def workbook(tmp_path) -> Path:
    path = tmp_path / "SYN_HEDIS_XREF.xlsx"
    hedis_h4.build().save(path)
    return path


def _feed(contract: GoldContract, table: str):
    return next(f for f in contract.feeds if f.target.table == table)


def _qkeys(feed) -> set[str]:
    return {q.key.split("].", 1)[1] for q in feed.questions}


def test_one_feed_per_mapping_sheet_in_workbook_order(workbook, cfg):
    contract = read_workbook(workbook, cfg)
    assert contract.dialect == "hedis_h4"
    assert [f.manifest_index for f in contract.feeds] == [1, 2, 3]   # CONTENTS / Notes skipped
    assert [f.index for f in contract.feeds] == [0, 1, 2]
    assert all(f.json_file.endswith(f"#sheets[{f.manifest_index}]") for f in contract.feeds)


def test_direct_hardcoded_and_audit_rows(workbook, cfg):
    alpha = _feed(read_workbook(workbook, cfg), "XREF_ALPHA")
    by = {c.target_attribute: c for c in alpha.columns}
    assert by["ALPHA_CODE"].expression == "ALPHA_CD" and by["ALPHA_CODE"].edit_class == "direct"
    assert by["ALPHA_DESC"].expression == "ALPHA_DSC"
    assert by["SOURCE_SYSTEM"].expression == "'SYN'"
    assert by["LOAD_TS"].expression is None and by["LOAD_TS"].edit_class == "audit"
    assert all(c.target_type_status == "filled" for c in alpha.columns)    # Spark as written
    assert alpha.load_mode == "full"                                       # CONTENTS
    assert any(f.startswith("hedis_audit_rows: 1") for f in alpha.flags)
    # never guessed: the catalog / schema / key / the 2-part source's catalog.schema
    assert _qkeys(alpha) == {"target_catalog", "target_schema", "primary_key",
                             "source_catalog_schema"}


def test_drifted_header_sql_types_proposed_and_prose_asked(workbook, cfg):
    beta = _feed(read_workbook(workbook, cfg), "XREF_BETA")        # header r3, column B
    assert [c.target_attribute for c in beta.columns] == [
        "BETA_CODE", "BETA_DATE", "BETA_AMOUNT", "BETA_FLAG"]
    proposed = {p.key.rsplit("columns", 1)[1]: p.value for p in beta.proposals}
    assert proposed == {"[0].target_type": "string", "[1].target_type": "timestamp",
                        "[3].target_type": "boolean"}
    # decimal(p,s) is spelled alike in both vocabularies: copied as stated (filled)
    assert beta.columns[2].target_type == "decimal(10,2)"
    assert beta.columns[2].target_type_status == "filled"
    assert all("platform is unconfirmed" in p.basis for p in beta.proposals)
    assert beta.columns[0].length == "20" and beta.columns[0].target_format == "varchar(20)"
    assert beta.source_sets[0].sources[0].catalog_schema == "syn_cat.syn_sch"   # 3-part
    assert "source_catalog_schema" not in _qkeys(beta)
    flag_q = next(q for q in beta.questions if q.key.endswith("columns[3].expression"))
    assert flag_q.quoted == "lookup SYN_REF on BETA_FLG"                 # cell quoted
    assert beta.load_mode == "full"                                       # case-insensitive


def test_what_the_sheet_cannot_say_is_a_question(workbook, cfg):
    gamma = next(f for f in read_workbook(workbook, cfg).feeds if f.manifest_index == 3)
    q = {k.split("].", 1)[1]: v for k, v in ((q.key, q) for q in gamma.questions)}
    assert q["target_table"].candidates == ["XREF_GAMMA", "XREF_GAMMA_OTHER"]
    assert q["load_mode"].quoted == "append"                    # unmapped criteria
    assert q["columns[1].target_type"].quoted == "geography"    # unknown type


def test_answers_close_questions_and_overlay_values_fill(workbook, cfg):
    answers = {"feeds[0].target_catalog": "syn_gold", "feeds[0].primary_key": "ALPHA_CODE"}
    alpha = _feed(read_workbook(workbook, cfg, answers=answers), "XREF_ALPHA")
    assert alpha.target.catalog == "syn_gold" and alpha.primary_key == ["ALPHA_CODE"]
    assert {a.key for a in alpha.answered} == set(answers)
    assert not {"target_catalog", "primary_key"} & _qkeys(alpha)
    set_cfg = cfg.model_copy(update={"target_schema": "syn_consumption"})
    alpha = _feed(read_workbook(workbook, set_cfg), "XREF_ALPHA")
    assert alpha.target.schema_name == "syn_consumption" and alpha.filled["target_schema"] == 1
    assert "target_schema" not in _qkeys(alpha)


def test_a_workbook_with_no_h4_sheet_is_refused(tmp_path, cfg):
    path = tmp_path / "other.xlsx"
    wb = Workbook()
    wb.active.append(["a", "b", "c"])
    wb.save(path)
    with pytest.raises(HedisReadError):
        read_workbook(path, cfg)


def _cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    return subprocess.run([sys.executable, "-m", "codegen.cli", *args, "--config", str(CONFIG)],
                          capture_output=True, text=True, encoding="utf-8", check=False,
                          env=env, cwd=cwd)


def test_the_cli_writes_the_contract_and_exits_3_while_questions_stay(workbook, tmp_path):
    out = tmp_path / "gold.json"
    done = _cli(["read-hedis", "--workbook", str(workbook), "--out", str(out)], tmp_path)
    assert done.returncode == 3, done.stdout + done.stderr
    contract = GoldContract.model_validate(json.loads(out.read_text("utf-8")))
    assert len(contract.feeds) == 3
    lines = done.stdout.splitlines()
    assert any(line.startswith("QUESTION") and "feeds[0].target_catalog" in line for line in lines)
    assert any(line.startswith("INPUT_NEEDED") and "feeds[1].columns[0].target_type" in line
               for line in lines)
    assert lines[-1].startswith("read-hedis: 3 table(s), ")
    answers = tmp_path / "answers.yaml"
    answers.write_text('gaps:\n  "feeds[0].target_catalog": {value: "syn_gold"}\n',
                       encoding="utf-8")
    again = _cli(["read-hedis", "--workbook", str(workbook), "--out", str(out),
                  "--answers", str(answers)], tmp_path)
    assert "1 answered" in again.stdout.splitlines()[-1]
    assert not any("feeds[0].target_catalog" in line for line in again.stdout.splitlines()
                   if line.startswith("QUESTION"))


def test_the_cli_refuses_a_non_h4_workbook(tmp_path):
    path = tmp_path / "other.xlsx"
    Workbook().save(path)
    done = _cli(["read-hedis", "--workbook", str(path), "--out", str(tmp_path / "o.json")],
                tmp_path)
    assert done.returncode == 1
    assert '"reason": "hedis.layout"' in done.stderr
