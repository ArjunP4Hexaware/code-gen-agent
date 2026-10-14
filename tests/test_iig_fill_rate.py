"""The IIG corpus's fill rate (2026-10-13): DATABRICKS_NOTEBOOK_DETAILS,
DATA_FACTORY_PIPELINE_SCHEDULE and EMAIL_TEMPLATE_CONFIG fill what the corpus
fills.

``tools/iig_fill_rate.py`` measures, per column, how many corpus rows fill it
against how many agent rows do. Every column the corpus fills in >90% of rows
that the agent left blank is now derived from the inputs, or written as the
corpus's dominant constant — ACFC overlay ``derived_cells``, one NOTE
(``iig_derived``) per column. Assigned columns (ids, the workspace URL /
secret / cluster, audit stamps) stay blank: never invented. ACTIVE_START_DATE
(a per-RFC go-live date) is the one gap left: no document states it and no
value dominates. The corpus here is the two committed goldens (the SFMC
reference IIG, the pair-1 golden); D1 runs the tool over the 199-IIG corpus.
"""

from __future__ import annotations

import importlib.util
import json
import sys

import openpyxl
import pytest

from codegen.config import load_config
from test_iig_v2_derivations import ACFC_OVERLAY, FRD, REPO, _rows, _run

_spec = importlib.util.spec_from_file_location("iig_fill_rate",
                                               REPO / "tools" / "iig_fill_rate.py")
fill_rate = importlib.util.module_from_spec(_spec)
sys.modules["iig_fill_rate"] = fill_rate
_spec.loader.exec_module(fill_rate)

CORPUS = [REPO / "fixtures" / "reference" / "SFMC_IIG.xlsx",
          REPO / "fixtures" / "acfc_shapes" / "pair_1" / "golden" / "RFC_ACCUMULATORS_IIG.xlsx"]
SCHED, NB, EMAIL = ("DATA_FACTORY_PIPELINE_SCHEDULE", "DATABRICKS_NOTEBOOK_DETAILS",
                    "EMAIL_TEMPLATE_CONFIG")
# Columns the corpus fills in >90% of rows that the agent wrote blank before
# 2026-10-13 (tools/iig_fill_rate.py, the home goldens) — each now filled.
FILLED_NOW = {
    SCHED: ["APPLICATION_NAME"],
    NB: ["PIPELINE_NAME", "PROCESS_NAME", "DATABRICKS_NOTEBOOK_PATH"],
    EMAIL: ["TEMPLATE_NAME", "PROCESS_NAME", "SUBJECT", "BODY", "SENDER_NAME", "SENDER_EMAIL"],
}
OPEN_GAPS = {SCHED: ["ACTIVE_START_DATE"], NB: [], EMAIL: []}

pytestmark = pytest.mark.skipif(not all(p.exists() for p in CORPUS),
                                reason="committed goldens absent")


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("fill_rate")
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    spec, gate, xlsx = _run(FRD, config, tmp)
    return spec, gate, xlsx, sorted(xlsx.parent.glob("*_IIG.xlsx"))


def test_every_corpus_filled_column_is_filled_now(generated):
    _spec, gate, xlsx, _iigs = generated
    for sheet, columns in FILLED_NOW.items():
        rows = _rows(xlsx, sheet)
        assert rows, sheet
        for row in rows:
            for column in columns:
                value = row[column][0]
                assert value not in (None, ""), (sheet, column)
    notebook = _rows(xlsx, NB)
    assert [r["PROCESS_NAME"][0].split(" Load for ")[0] for r in notebook] == ["Stage",
                                                                              "Standard"]
    assert all(r["DATABRICKS_NOTEBOOK_PATH"][0] == "/Workspace/iig/"
               + r["DATABRICKS_NOTEBOOK_NAME"][0] for r in notebook)
    schedule = {r["PIPELINE_DESCRIPTION"][0]: r["PIPELINE_NAME"][0] for r in _rows(xlsx, SCHED)}
    assert [r["PIPELINE_NAME"][0] for r in notebook] == [schedule["File to Stage"],
                                                         schedule["Stage to Standard"]]
    email = {r["STATUS"][0]: r for r in _rows(xlsx, EMAIL)}
    assert email["Success"]["SUBJECT"][0].endswith(" Load Completed")
    assert email["Failed"]["BODY"][0].endswith(" Files Load Process Failed")
    assert {r["SENDER_NAME"][0] for r in email.values()} == {"dbo"}
    assert {r["SENDER_EMAIL"][0] for r in email.values()} == {"syn.dl.sender@synthetic.example"}
    # one NOTE per derived column (the same text on every row: said once)
    derived = [f for f in gate.flags if f.startswith("iig_derived:")]
    assert len(derived) == sum(len(c) for c in FILLED_NOW.values()) == len(set(derived))


def test_the_fill_rate_tool_finds_only_the_documented_gap(generated, tmp_path, capsys):
    _spec, _gate, _xlsx, iigs = generated
    out = tmp_path / "fill.json"
    assert fill_rate.main(["--corpus", *map(str, CORPUS), "--agent", *map(str, iigs),
                           "--json", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    for sheet, expected in OPEN_GAPS.items():
        gaps = [h for h, c in report[sheet]["columns"].items() if c["status"] == "gap"]
        assert gaps == expected, sheet
        for column in FILLED_NOW[sheet]:
            assert report[sheet]["columns"][column]["agent_pct"] == 100.0, (sheet, column)
    # ids / workspace / audit stamps are assigned, never a gap to fill
    nb = report[NB]["columns"]
    for column in ("PIPELINE_ID", "GROUP_ID", "DATABRICKS_WORKSPACE_URL",
                   "DATABRICKS_CLUSTERID", "CLUSTER_DETAILS_ID", "CREATED_BY"):
        assert nb[column]["status"] == "assigned", column
    # corpus values are production text: withheld unless --show-values
    assert all(c["dominant_value"] is None for s in report.values()
               for c in s["columns"].values())
    assert "GAPS (1): ACTIVE_START_DATE" in capsys.readouterr().out


def test_fill_rate_statuses_on_a_synthetic_corpus(tmp_path):
    def book(path, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = EMAIL
        for row in rows:
            ws.append(row)
        wb.save(path)
        return path

    head = ["TEMPLATE_ID", "SUBJECT", "BODY_QUERY", "SENDER_NAME"]
    corpus = book(tmp_path / "corpus.xlsx", [head, [1, "a", None, "dbo"], [2, "b", None, "dbo"],
                                            [3, "c", "q", "NULL"]])
    agent = book(tmp_path / "agent_IIG.xlsx", [head, [None, "x", None, None]])
    report = fill_rate.fill_rates(fill_rate.sheet_rows([corpus], {EMAIL}),
                                  fill_rate.sheet_rows([agent], {EMAIL}), [EMAIL], 90.0,
                                  lambda h: h == "TEMPLATE_ID")[EMAIL]["columns"]
    assert report["TEMPLATE_ID"]["status"] == "assigned"
    assert report["SUBJECT"]["status"] == "ok"
    assert report["BODY_QUERY"]["status"] == "sparse"              # 1 of 3
    assert report["SENDER_NAME"]["status"] == "sparse"             # NULL is not a value
    assert report["SENDER_NAME"]["dominant_share"] == 100.0
