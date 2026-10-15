"""D1 post51 pair_06: "audit column 'DELETE_FLAG' has datatype 'tinyint';
expected one of ['string', 'timestamp']". A flag / indicator audit column
(*_FLAG / *_IND) may be tinyint / int / smallint / boolean; every other audit
column stays string / timestamp. The sets live on the conventions profile."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from codegen.config import ConventionsProfileConfig
from codegen.emit.context import sql_type
from codegen.extract import extract_contract
from codegen.extract.audit_types import accepted, audit_datatype
from codegen.run_errors import first_error_line
from post51_pairs import AUDIT, family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("column", "raw", "spelled"), [
    ("DELETE_FLAG", "tinyint", "TINYINT"), ("DELETE_FLAG", "TinyInt", "TINYINT"),
    ("ACTIVE_IND", "int", "INT"), ("purge_flag", "smallint", "SMALLINT"),
    ("ACTIVE_IND", "boolean", "BOOLEAN"), ("DELETE_FLAG", "string", "String"),
])
def test_flag_columns_accept_integer_and_boolean_types(config, tmp_path, column, raw, spelled):
    workbook = family_e_workbook(tmp_path / "p6.xlsx", [None], audit=AUDIT + [(column, raw)])
    contract = extract_contract(workbook, family_e_frd(tmp_path / "frd.json"), config,
                                generated_date="2026-01-01")
    (feed,) = contract.feeds
    assert [(a.column, a.datatype) for a in feed.audit_columns][-1] == (column, spelled)
    assert sql_type(spelled) == spelled.upper()


def test_other_audit_columns_keep_string_and_timestamp(config, tmp_path):
    workbook = family_e_workbook(tmp_path / "p6.xlsx", [None],
                                 audit=AUDIT + [("LOAD_ID", "tinyint")])
    with pytest.raises(Exception, match=r"audit column 'LOAD_ID' has datatype 'tinyint'; "
                                        r"expected one of \['string', 'timestamp'\]"):
        extract_contract(workbook, family_e_frd(tmp_path / "frd.json"), config,
                         generated_date="2026-01-01")


def test_the_accepted_sets_are_profile_configuration(config):
    profile = config.conventions.get("acfc_prx")
    assert profile.audit_datatypes == ["string", "timestamp"]
    assert profile.audit_flag_datatypes == ["tinyint", "int", "smallint", "boolean"]
    assert profile.audit_flag_suffixes == ["_flag", "_ind"]
    widened = profile.model_copy(update={"audit_datatypes": ["string", "timestamp", "bigint"]})
    profiles = {**config.conventions.profiles, "acfc_prx": widened}
    conventions = config.conventions.model_copy(update={"profile": "acfc_prx",
                                                        "profiles": profiles})
    overlaid = config.model_copy(update={"conventions": conventions})
    assert "bigint" in accepted("LOAD_ID", overlaid)
    assert audit_datatype("LOAD_ID", "bigint", overlaid) == "BIGINT"
    assert audit_datatype("LOAD_ID", "bigint", config) is None


def test_a_type_the_contract_cannot_spell_is_refused_at_load():
    with pytest.raises(ValidationError, match="no contract spelling"):
        ConventionsProfileConfig(audit_flag_datatypes=["tinyint", "date"])


def test_pair06_shape_exits_zero_through_the_cli(tmp_path):
    workbook = family_e_workbook(tmp_path / "p6.xlsx", [None],
                                 audit=AUDIT + [("DELETE_FLAG", "tinyint")])
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook", str(workbook),
         "--frd-contract", str(family_e_frd(tmp_path / "frd.json")),
         "--out", str(tmp_path / "sttm.json"), "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None
