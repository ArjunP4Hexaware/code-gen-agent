"""tools/ddl_shape.py (2026-10-23): the structure of DDL files and the comparison
of the agent's DDL with a reference set — over the tracked pair-1 golden, the SFMC
reference DDLs (the edo_sfmc format) and synthetic text; never a client value."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import ddl_shape  # noqa: E402

GOLDEN = REPO / "fixtures" / "acfc_shapes" / "pair_1" / "golden" / "ACCUM_DDL.txt"
SFMC_STAGE = REPO / "fixtures" / "reference" / "SFMC_stage_table_creation.txt"
SFMC_STANDARD = REPO / "fixtures" / "reference" / "SFMC_standard_table_creation.txt"

PROD_LIKE = """CREATE TABLE IF NOT EXISTS c.s.t1 (
  A String COMMENT 'the member\\'s id, (a) value',
  B Decimal(10,2) COMMENT 'amount; no -- comment here',
  SRC_FILE_NAME string COMMENT 'file'
)
USING delta
CLUSTER BY AUTO
COMMENT 'Standard table for t1'
TBLPROPERTIES (
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableDeletionVectors' = 'true'
);

ALTER TABLE c.s.t1 SET TAGS ('DOMAIN' = 'x', 'SUBDOMAIN' = 'y');
-- a trailing note (CREATE TABLE inside a comment is not a block)
CREATE TABLE c.s.t2 (
  K BIGINT NOT NULL COMMENT 'it''s doubled',
  CONSTRAINT pk_t2 PRIMARY KEY (K)
)
USING delta;
"""


def test_the_pair1_golden_is_the_bare_combined_shape():
    stage, standard = ddl_shape.profile_text(GOLDEN.read_text(encoding="utf-8"), GOLDEN.name)
    assert (stage["layer"], standard["layer"]) == ("stage", "standard")      # the banners
    for block in (stage, standard):
        assert block["create"] == "CREATE OR REPLACE"
        assert block["column_comment_share"] == 0.0 and not block["table_comment"]
        assert block["tblproperties"] == [] and block["set_tags"] == []
        assert not block["terminated"] and block["quote_escape"] == "none"
    assert stage["stage_all_string"] is False            # typed stage (Decimal)
    assert stage["columns"] == standard["columns"] == 24


def test_the_sfmc_reference_files_take_their_layer_from_the_file_name():
    (stage,) = ddl_shape.profile_paths([str(SFMC_STAGE)])
    (standard,) = ddl_shape.profile_paths([str(SFMC_STANDARD)])
    assert (stage["layer"], standard["layer"]) == ("stage", "standard")
    assert stage["location"] and not stage["cluster_by_auto"]
    assert standard["cluster_by_auto"] and not standard["location"]
    assert len(stage["tblproperties"]) == 4 and len(standard["tblproperties"]) == 13
    assert stage["set_tags"] == standard["set_tags"] == ["DOMAIN", "SUBDOMAIN"]
    assert stage["column_comment_share"] == 1.0 and stage["terminated"]


def test_literals_comments_and_constraints_do_not_confuse_the_shape():
    t1, t2 = ddl_shape.profile_text(PROD_LIKE, "pr_std_x.txt")
    assert t1["create"] == "CREATE IF NOT EXISTS" and t2["create"] == "CREATE"
    assert t1["columns"] == 3 and t1["column_comment_share"] == 1.0   # ',' / '(' in a COMMENT
    assert t1["cluster_by_auto"] and t1["table_comment"] and t1["terminated"]
    assert t1["tblproperties"] == ["delta.autoOptimize.autoCompact",
                                   "delta.enableDeletionVectors"]
    assert t1["set_tags"] == ["DOMAIN", "SUBDOMAIN"] and not t1["primary_key"]
    assert t1["quote_escape"] == "backslash"
    assert t2["columns"] == 1 and t2["primary_key"] and t2["not_null"]
    assert t2["quote_escape"] == "doubled" and t2["set_tags"] == []
    assert t1["layer"] == t2["layer"] == "standard"                     # pr_std_ file name


def test_the_comparison_scores_each_layer_against_the_reference_majority(tmp_path):
    ref = ddl_shape.profile_paths([str(SFMC_STAGE), str(SFMC_STANDARD)])
    report = ddl_shape.compare(ref, ddl_shape.profile_paths([str(GOLDEN)]))
    stage = {r["feature"]: r for r in report["stage"]["features"]}
    assert stage["tblproperties"]["verdict"] == "DIFF"
    assert stage["create"]["verdict"] == "MATCH"                    # both CREATE OR REPLACE
    assert stage["quote_escape"]["verdict"] == "n/a"                # no escaped quote anywhere
    assert report["stage"]["matched"] < report["stage"]["scored"]
    same = ddl_shape.compare(ref, ref)
    assert all(part["matched"] == part["scored"] for part in same.values())


def test_the_report_carries_no_names_or_text(tmp_path, capsys):
    out = tmp_path / "shape.json"
    agent = tmp_path / "agent_std.txt"
    agent.write_text(PROD_LIKE, encoding="utf-8")
    assert ddl_shape.main(["--reference", str(SFMC_STANDARD), "--agent", str(agent),
                           "--json", str(out)]) == 0
    printed = capsys.readouterr().out + out.read_text(encoding="utf-8")
    for leaked in ("c.s.t1", "member", "amount", "Standard table for t1", "pk_t2", "'x'"):
        assert leaked not in printed
    assert json.loads(out.read_text(encoding="utf-8"))["standard"]["agent_blocks"] == 2


def test_a_missing_path_is_refused():
    with pytest.raises(SystemExit):
        ddl_shape.profile_paths(["/no/such/ddl"])
