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


# ------------------------------------------- 2026-10-14: --patterns, sheet matching

ADLS = "ADLS_DELTA_INGESTION_DETAILS"


def _corpus_book(path, feed: str, domain: str, *, email_name: str = EMAIL,
                 title_row: bool = False, group: int = 1):
    """A synthetic corpus workbook: one feed, its two legs, a master above them."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    table = f"stg_zq.{feed}"

    def sheet(name, head, rows, title=False):
        ws = wb.create_sheet(name)
        if title:
            ws.append(["exported table"])
        ws.append(head)
        for row in rows:
            ws.append(row)

    sheet(ADLS, ["GROUP_ID", "PIPELINE_ID", "OBJECT_NAME", "TGT_TABLE_NAME", "DOMAIN",
                 "SUBDOMAIN"], [[group, 10 * group + 1, f"{feed}_*", table, domain, "Risk"]])
    sheet(NB, ["PIPELINE_ID", "GROUP_ID", "PROCESS_NAME", "SEQ_NM"],
          [[10 * group + 1, group, f"Stage Load for {feed}", 1],
           [10 * group + 2, group, f"Standard Load for {feed}", 1]])
    sheet(SCHED, ["PIPELINE_ID", "PARENT_PIPELINE_ID", "PIPELINE_DESCRIPTION",
                  "PIPELINE_FREQUENCY", "DAY_OF_SCHEDULE", "ACTIVE_END_DATE"],
          [[10 * group + 9, None, "Grand master", "DAILY", None, "9999-12-31"],
           [10 * group + 8, 10 * group + 9, "Master", "DAILY", None, "9999-12-31"],
           [10 * group + 1, 10 * group + 8, f"{domain} file to stage", "DAILY", None,
            "9999-12-31"],
           [10 * group + 2, 10 * group + 8, f"{domain} stage to standard", "WEEKLY", 2,
            "9999-12-31"]])
    sheet(email_name, ["TEMPLATE_NAME", "STATUS", "SUBJECT"],
          [[f"{feed} TPL", "Success", f"{feed} Load Completed"],
           [f"{feed} TPL", "Failed", f"{feed} Load Failed"]], title=title_row)
    wb.save(path)
    return path


def test_sheet_names_match_without_case_or_separators_and_a_title_row():
    """D1 post43 3c: EMAIL_TEMPLATE_CONFIG read 0 corpus rows. A sheet name is
    compared with case and separators ignored (and Excel's 31-character cut);
    the header is the first of the top rows with two or more cells."""
    wanted = [*fill_rate.DEFAULT_SHEETS, *fill_rate.SLOT_SHEETS]
    for name in ("Email_Template_Config", "email template config", "EMAIL-TEMPLATE-CONFIG "):
        assert fill_rate.match_sheet(name, wanted) == EMAIL
    for name in ("STGDELTA_STDDELTA_INGESTION_DET", "stgdelta_stddelta_ingestion_details"):
        assert fill_rate.match_sheet(name, wanted) == "STGDELTA_STDDELTA_INGESTION_DETAILS"
    assert fill_rate.match_sheet("EMAIL_TEMPLATE", wanted) is None


def test_every_corpus_workbook_lists_its_sheets_and_a_csv_is_one_table(tmp_path, capsys):
    one = _corpus_book(tmp_path / "pair_a.xlsx", "zq_alpha_feed", "Member",
                       email_name="email_template_config", title_row=True)
    two = _corpus_book(tmp_path / "pair_b.xlsx", "zq_beta_feed", "Claims",
                       email_name="NOT_AN_EMAIL_SHEET", group=2)
    (tmp_path / "email_template_config.csv").write_text(
        "TEMPLATE_NAME,STATUS,SUBJECT\nX TPL,Success,X Load Completed\n", encoding="utf-8")
    books = fill_rate.read_books(fill_rate.workbooks([tmp_path]), list(fill_rate.DEFAULT_SHEETS))
    fill_rate.print_inventory(books, list(fill_rate.DEFAULT_SHEETS))
    out = capsys.readouterr().out
    assert f"{one.name}: 4 sheet(s)" in out and "EMAIL_TEMPLATE_CONFIG 2" in out
    assert f"{two.name}: 4 sheet(s)" in out and "NOT_AN_EMAIL_SHEET" in out
    assert "email_template_config.csv: 1 sheet(s)" in out
    assert f"{EMAIL}: in 2 of 3 corpus workbook(s)" in out
    rows = fill_rate.merge_books(books, {EMAIL})[EMAIL][1]
    assert len(rows) == 3 and {r["status"] for r in rows} == {"Success", "Failed"}


def test_patterns_slot_values_day_of_schedule_and_masters_scrubbed(tmp_path):
    corpus = [_corpus_book(tmp_path / f"pair_{n}.xlsx", feed, domain, group=n)
              for n, (feed, domain) in enumerate((("zqalphafeed", "Zqmember"),
                                                  ("zqbetafeed", "Zqclaims")), 1)]
    keys = fill_rate._diff_module().load_keys(fill_rate.TOOLS / "iig_keys.yaml")
    books = fill_rate.read_books(corpus, [*fill_rate.DEFAULT_SHEETS, *fill_rate.SLOT_SHEETS])
    out = tmp_path / "patterns"
    report = fill_rate.write_patterns(out, books, list(fill_rate.DEFAULT_SHEETS), keys,
                                      lambda h: keys.is_assignment(h))
    assert report["rescan"] == {}
    nb = report["sheets"][NB]["columns"]["PROCESS_NAME"]
    assert nb["dominant_value_share"] == 25.0                     # four different names
    assert (nb["dominant_pattern"], nb["dominant_pattern_share"]) in (
        ("Stage Load for {table}", 50.0), ("Standard Load for {table}", 50.0))
    assert nb["per_feed"] and nb["distinct_patterns"] == 2
    subject = report["sheets"][EMAIL]["columns"]["SUBJECT"]
    assert subject["distinct_patterns"] == 2 and subject["per_feed"]
    end = report["sheets"][SCHED]["columns"]["ACTIVE_END_DATE"]
    assert (end["dominant_value"], end["dominant_value_share"]) == ("9999-12-31", 100.0)
    day = report["day_of_schedule_by_frequency"]
    assert day["DAILY"] == {"rows": 6, "filled": 0, "filled_pct": 0.0, "dominant": None}
    assert day["WEEKLY"]["filled"] == 2 and day["WEEKLY"]["dominant"] == ["2", 100.0]
    masters = report["masters"]
    assert masters["rows_by_kind"] == {"grand_master": 2, "master": 2}
    assert masters["groups_under_a_master"] == {"1": 4}           # one GROUP_ID each
    assert masters["master_rows_per_group"] == {"2": 2}           # per group, not shared
    text = (out / "patterns.md").read_text(encoding="utf-8")
    for raw in ("zqalphafeed", "zqbetafeed", "Zqmember", "Zqclaims"):
        assert raw not in text and raw not in (out / "patterns.json").read_text(
            encoding="utf-8")
    assert "Stage Load for {table}" in text and "| WEEKLY | 2 | 2 | 100.0 | 2 | 100.0 |" in text
