"""post158 (pentest CS-3): ``ddl_parses`` is an allow-list, not a blocklist.

A DDL text may only CREATE TABLE / ALTER TABLE ... SET the tables the feed
defines. A DROP, DELETE, INSERT, GRANT, an ALTER that changes columns, a CREATE
TABLE AS SELECT or a CREATE of another table FAILs however well it parses - the
defence behind ``ddl_types`` (test_ddl_types_gate.py).
"""

from __future__ import annotations

import pytest

from codegen import cli
from codegen.emit import framework
from codegen.gate.ddl_parse import check_ddl_parses
from test_ddl_types_gate import PAYLOAD, _check, _with_types
from test_m4_acceptance import _scoped

TABLES = ["d1_dlk.stg_x.t1", "d1_std.x.t1"]
CLEAN = """CREATE TABLE IF NOT EXISTS d1_dlk.stg_x.t1 (
  A STRING
) USING DELTA CLUSTER BY AUTO;

ALTER TABLE d1_dlk.stg_x.t1 SET TAGS ('DOMAIN' = 'D', 'SUBDOMAIN' = 'S');

CREATE TABLE IF NOT EXISTS `d1_std`.`x`.`t1` (
  A STRING
) USING DELTA CLUSTER BY AUTO TBLPROPERTIES ('delta.feature.appendOnly' = 'supported');
"""

EXTRA = {
    "drop": "DROP TABLE d1_dlk.stg_x.t1;",
    "delete": "DELETE FROM d1_dlk.stg_x.t1;",
    "insert": "INSERT INTO d1_dlk.stg_x.t1 VALUES ('a');",
    "grant": "GRANT SELECT ON TABLE d1_dlk.stg_x.t1 TO `users`;",
    "update": "UPDATE d1_dlk.stg_x.t1 SET A = 'b';",
    "alter_add_column": "ALTER TABLE d1_dlk.stg_x.t1 ADD COLUMN B STRING;",
    "ctas": "CREATE TABLE IF NOT EXISTS d1_dlk.stg_x.t1 AS SELECT 1 AS A;",
    "other_table": "CREATE TABLE IF NOT EXISTS pwn.pwn.t (A INT);",
    "tags_on_other_table": "ALTER TABLE pwn.pwn.t SET TAGS ('DOMAIN' = 'D');",
    "drop_schema": "DROP SCHEMA d1_dlk.stg_x CASCADE;",
}


def test_the_feeds_own_create_and_set_statements_pass():
    check = check_ddl_parses([("X_DDL.txt", CLEAN)], "databricks", TABLES)
    assert check.passed, check.details


@pytest.mark.parametrize("kind", sorted(EXTRA))
def test_any_other_statement_fails_however_well_it_parses(kind):
    text = CLEAN + "\n" + EXTRA[kind] + "\n"
    check = check_ddl_parses([("X_DDL.txt", text)], "databricks", TABLES)
    assert not check.passed
    assert "statement 4" in check.details


def test_the_framework_run_passes_its_tables_to_the_allow_list(
        pair4_config, pair4_spec, tmp_path, monkeypatch):
    """With the type grammar switched off (the pre-post158 hole), the payload's
    DROP / CREATE reach the DDL text - and the allow-list FAILs the feed."""
    monkeypatch.setattr(framework, "_written_type", lambda dtype, config: dtype)
    spec = _with_types(pair4_spec, stage=PAYLOAD)
    gate = cli._generate_feed(spec, _scoped(pair4_config, tmp_path), dry_run=True,
                              skip_tests=True, output_mode="framework",
                              conventions_profile="acfc_prx", iig_template="iig_v2")
    check = _check(gate, "ddl_parses")
    assert not check.passed
    assert "the feed's own tables" in check.details
    assert gate.verdict == "FAIL"
