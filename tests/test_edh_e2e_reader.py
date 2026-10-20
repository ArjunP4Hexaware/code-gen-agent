"""The EDH E2E gold-mapping reader (codegen.layouts.edh_e2e) on the synthetic fixtures.

Every value here is fabricated (tests/fixtures/edh_gold_synthetic/, SYN_ names only). The rule
under test is the ingestion layouts' one: stated -> filled, derived -> proposed, unstated or
free text -> QUESTION — and never silence.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from codegen.config import EdhE2eConfig
from codegen.contracts.gold import ROLES, GoldContract
from codegen.layouts import edh_e2e
from codegen.layouts.edh_e2e import Untranslatable, read_dir, role_counts, translate_edit

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "edh_gold_synthetic"
QUALIFY = {"syn_a": "`SYN_T`.`SYN_A`"}


@pytest.fixture(scope="module")
def contract() -> GoldContract:
    return read_dir(FIXTURES, EdhE2eConfig())


def _feed(contract, json_prefix):
    return next(f for f in contract.feeds if f.json_file.startswith(json_prefix))


def _keys(feed, role=None):
    return {q.key for q in feed.questions if role is None or q.role == role}


def _proposed(feed, role=None):
    return {p.key for p in feed.proposals if role is None or p.role == role}


# ---- every value is filled, proposed or asked ---------------------------------------------


def test_every_mapping_row_gets_an_expression_or_a_question(contract):
    for feed in contract.feeds:
        for j, col in enumerate(feed.columns):
            key = f"feeds[{feed.index}].columns[{j}]"
            asked = {f"{key}.expression", f"{key}.source_table"} & _keys(feed)
            assert (col.expression is not None) != bool(asked), key
            if col.expression is not None:
                assert col.expression.startswith(
                    f"/* {feed.json_file} block_index={col.block_index} "
                    f"source_row={col.source_row} */ "
                )


def test_every_mapping_row_gets_a_type_or_a_question(contract):
    for feed in contract.feeds:
        for j, col in enumerate(feed.columns):
            key = f"feeds[{feed.index}].columns[{j}].target_type"
            assert (col.target_type is not None) != (key in _keys(feed)), key
            if col.target_type_status == "proposed":
                assert key in _proposed(feed)


def test_every_selection_criteria_cell_becomes_a_join_filter_or_question(contract):
    for feed in contract.feeds:
        cells = {}
        for col in feed.columns:
            text = next(
                r["selection_criteria"]
                for r in _rows(feed)
                if r["source_row"] == col.source_row and r["block_index"] == col.block_index
            )
            if text:
                cells.setdefault((col.block_index, text), []).append(col.source_row)
        for (block, text), rows in cells.items():
            sset = next(s for s in feed.source_sets if s.block_index == block)
            used = {r for j in sset.joins for r in j.rows} | {
                r for f in sset.filters for r in f.rows
            }
            asked = {
                q.where.source_row
                for q in feed.questions
                if q.quoted == text and q.where is not None
            }
            assert rows[0] in used | asked, (feed.json_file, block, rows[0])


def _rows(feed):
    doc = json.loads((FIXTURES / feed.json_file).read_text(encoding="utf-8"))
    return doc["mappings"]


def test_feed_level_roles_are_filled_or_asked(contract):
    for feed in contract.feeds:
        k = f"feeds[{feed.index}]"
        asked = _keys(feed)
        assert (feed.load_mode is not None) != (f"{k}.load_mode" in asked)
        assert (feed.target.schema_name is None) == (f"{k}.target_schema" in asked)
        assert f"{k}.scd2_mode" in asked and f"{k}.sk_strategy" in asked
        assert bool(feed.primary_key) != (f"{k}.primary_key" in asked)
        for s in feed.source_sets:
            for n, src in enumerate(s.sources):
                key = f"{k}.source_sets[{s.block_index}].sources[{n}].catalog_schema"
                assert (src.catalog_schema is None) == (key in asked)


def test_document_notes_and_rules_are_one_question_each(contract):
    for feed in contract.feeds:
        doc = json.loads((FIXTURES / feed.json_file).read_text(encoding="utf-8"))
        assert len(_keys(feed, "document_note")) == len(doc["document_notes"] or [])
        assert len(_keys(feed, "rule")) == len(doc["rules"] or [])
        for q in feed.questions:
            if q.role == "rule":
                assert q.quoted in doc["rules"]


def test_every_counted_role_is_in_the_vocabulary(contract):
    for feed in contract.feeds:
        assert set(role_counts(feed)) <= set(ROLES)


# ---- the profile fills what the documents never state -------------------------------------


def test_profile_values_fill_instead_of_asking():
    cfg = EdhE2eConfig(
        target_schema="syn_gold",
        source_catalog_map={"SYNFCT": "syn_cat.syn_src"},
        scd2_mode="syn_type2",
        sk_strategy="syn_identity",
        function_map={"SynBlank": "''"},
    )
    feed = read_dir(FIXTURES, cfg).feeds[0]
    asked = _keys(feed)
    assert not {
        r for r in ("target_schema", "scd2_mode", "sk_strategy") if f"feeds[0].{r}" in asked
    }
    assert not _keys(feed, "source_catalog_schema")
    assert feed.target.schema_name == "syn_gold"
    assert {s.catalog_schema for ss in feed.source_sets for s in ss.sources} == {"syn_cat.syn_src"}
    assert role_counts(feed)["scd2_mode"]["filled"] == 1
    # the mapped zero-argument function lets both empty / null tests translate
    exprs = [c.expression for c in feed.columns if c.edit_class == "COALESCE-equivalent"]
    assert exprs and all(e is not None for e in exprs)


def test_without_a_function_mapping_the_expression_is_asked_quoting_the_cell(contract):
    feed = _feed(contract, "syn_mbr_dim")
    q = [q for q in feed.questions if q.role == "expression" and "SynBlank" in (q.quoted or "")]
    assert q and all("edh_e2e.function_map" in x.reason for x in q)


# ---- the multi-block case -----------------------------------------------------------------


def test_two_blocks_yield_two_source_sets_for_one_target(contract):
    feed = _feed(contract, "syn_mbr_dim")
    assert [s.block_index for s in feed.source_sets] == [0, 1]
    first, second = ({src.table for src in s.sources} for s in feed.source_sets)
    assert first and second and not first & second
    assert {c.target_attribute for c in feed.columns if c.block_index == 1} < {
        c.target_attribute for c in feed.columns if c.block_index == 0
    }


# ---- joins / filters / keys / regions ------------------------------------------------------


def test_join_grammar(contract):
    feed = _feed(contract, "syn_elig_fact")
    joins = feed.source_sets[0].joins
    same_name = [j for j in joins if j.on_assumption == "same_name"]
    assert same_name and all(j.status == "proposed" and j.type == "INNER" for j in same_name)
    assert len(_proposed(feed, "join")) == len(same_name)
    # the second joined table of one cell is a second join with the same column
    by_rows = {}
    for j in same_name:
        by_rows.setdefault(tuple(j.rows), []).append(j.joined)
    assert any(len(v) == 2 for v in by_rows.values())
    assert any(len(j.on) == 2 for j in same_name)  # "using <col> & <col2>"
    explicit = [j for j in joins if j.on_assumption == "explicit"]
    assert {j.type for j in explicit} == {"INNER", "LEFT"}  # "*=" is the outer side
    assert all(j.pairs and j.base is None for j in explicit)
    assert len([q for q in feed.questions if q.key.endswith(".tables")]) == len(explicit)


def test_filter_grammar(contract):
    feed = _feed(contract, "syn_elig_fact")
    by_pattern = {}
    for f in feed.source_sets[0].filters:
        by_pattern.setdefault(f.pattern, []).append(f)
    assert set(by_pattern) == {"F1", "F2", "F3", "F4", "F5"}
    assert "date_sub(current_date(), 30)" in by_pattern["F3"][0].predicate
    assert by_pattern["F4"][0].status == "proposed"
    assert " AND " in by_pattern["F5"][0].predicate
    assert len(_keys(feed, "filter")) == 3  # the three free-text cells


def test_keys(contract):
    feed = _feed(contract, "syn_memo")
    assert feed.primary_key
    other = [q for q in feed.questions if q.role == "primary_key"]
    assert other and all(q.quoted for q in other)  # the non-PK indexes text, quoted


def test_regions_drift_is_a_proposal_and_sentinels_never_fill(contract):
    feed = _feed(contract, "syn_elig_fact")
    assert _proposed(feed, "region_drift")
    assert len({r.label for r in feed.regions}) == len(feed.regions)
    assert "edh_region_column_not_identifier:1" in feed.flags
    empty = _feed(contract, "syn_plan_ref")
    assert not empty.regions and len(_keys(empty, "target_type")) == len(empty.columns)


def test_drag_fill_is_flagged_and_kept(contract):
    feed = _feed(contract, "syn_memo")
    flagged = [x for x in feed.flags if x.startswith("edh_drag_fill:")]
    assert len(flagged) == 3
    j = int(flagged[0].split("columns[")[1].split("]")[0])
    assert feed.columns[j].source_format.upper().startswith("VARCHAR")


# ---- the expression translator (fabricated cells) ------------------------------------------


@pytest.mark.parametrize(
    "cell, sql",
    [
        ("set to NULL", "NULL"),
        ("set NULL", "NULL"),
        ("current timestamp", "current_timestamp()"),
        ("SYN_A[2,5]", "substr(`SYN_T`.`SYN_A`, 2, 4)"),
        ("TRIM(SYN_B)[1,3]", "substr(trim(`SYN_B`), 1, 3)"),
        ("if SYN_A IS NULL THEN 'X' ELSE SYN_A", "coalesce(`SYN_T`.`SYN_A`, 'X')"),
        ("if ISNULL(SYN_A) THEN 'X' ELSE SYN_A", "coalesce(`SYN_T`.`SYN_A`, 'X')"),
        (
            "if SYN_A IS a empty string OR NULL THEN 'X' ELSE SYN_A",
            "coalesce(nullif(`SYN_T`.`SYN_A`, ''), 'X')",
        ),
        (
            "if SYN_A IS an empty string THEN 'X' ELSE SYN_A",
            "CASE WHEN `SYN_T`.`SYN_A` = '' THEN 'X' ELSE `SYN_T`.`SYN_A` END",
        ),
        (
            "if SYN_B = 'P' THEN 'Q' ELSE if SYN_B = 'R' THEN 'S' ELSE 'T'",
            "CASE WHEN `SYN_B` = 'P' THEN 'Q' WHEN `SYN_B` = 'R' THEN 'S' ELSE 'T' END",
        ),
        ("SYN_B : '-' : SYN_C[1,2]", "concat(`SYN_B`, '-', substr(`SYN_C`, 1, 2))"),
        ("CAST(SYN_B AS DECIMAL(10,2))", "CAST(`SYN_B` AS DECIMAL(10,2))"),
        (
            "if SYN_B = < SYN_C THEN SYN_B ELSE SYN_C",
            "CASE WHEN `SYN_B` <= `SYN_C` THEN `SYN_B` ELSE `SYN_C` END",
        ),
    ],
)
def test_translated_classes(cell, sql):
    assert translate_edit(cell, qualify=QUALIFY, functions={}) == sql


@pytest.mark.parametrize(
    "cell",
    [
        "TRIM(CONVERT('SYN_X', 'SYN_Y', s.SYN_B))[1,9]",  # character-set arguments
        "if SYN_B IS NULL THEN SynFn() ELSE SYN_B",  # an unmapped function
        "only for SYN_REGION .",  # free text
        "SYN_B > 0",  # a predicate, not an expression
        "if (SYN_B >= SYN_C) AND (SYN_B = < SYN_D)",  # an if without THEN
    ],
)
def test_untranslatable_cells_raise(cell):
    with pytest.raises(Untranslatable):
        translate_edit(cell, qualify=QUALIFY, functions={})


# ---- the CLI and the shared grammar --------------------------------------------------------


def test_cli_prints_answer_lines_and_exits_3(tmp_path):
    out = tmp_path / "gold.json"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "codegen.cli",
            "read-edh-e2e",
            "--input",
            str(FIXTURES),
            "--out",
            str(out),
            "--table",
            "1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    )
    assert done.returncode == 3, done.stderr
    contract = GoldContract.model_validate_json(out.read_text(encoding="utf-8"))
    assert [f.index for f in contract.feeds] == [1]
    lines = [ln for ln in done.stdout.splitlines() if ln.startswith("QUESTION")]
    assert len(lines) == len(contract.feeds[0].questions)
    assert all(ln[15:].startswith("feeds[1].") and " — " in ln for ln in lines)


def test_reader_and_profiler_share_the_grammar():
    spec = importlib.util.spec_from_file_location(
        "profile_edh", REPO / "scripts" / "gold" / "profile_edh.py"
    )
    profiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profiler)
    for name in ("J_USING", "J_COLUMN_NO_USING", "J_EQUALITIES", "J_TABLE_ONLY", "PREAMBLE"):
        assert getattr(profiler, name).pattern == getattr(edh_e2e, name).pattern, name
    assert [(n, rx.pattern) for n, rx in profiler.F_PATTERNS] == [
        (n, rx.pattern) for n, rx in edh_e2e.F_PATTERNS
    ]
