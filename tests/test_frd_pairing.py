"""FRD pairing precedence, allowlisted table reads, upstream loader,
truncated-sheet matching. All offline: the table read is stubbed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import codegen.databricks as db
from codegen.demo_sources import (
    auto_pair_frd,
    document_stem,
    pair_sttm_with_frd,
    suggest_pairs,
)

MIDS_STTM = "STTM-Medicare Expansion-MIDS-Social Determine (1).xlsx"
MIDS_FRD = "FRD_Medicare Expansion-MIDS - Socially Determined"
MIDS_MAP = {"sttm-medicare expansion-mids-social determine":
            "frd_medicare expansion-mids - socially determined"}
CAQH_STTM = "STTM_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Mapping_Document_1005034__ (1).xlsx"
CAQH_FRD = "FRD_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Ingestion_1005034"


def test_pairing_precedence_map_then_ticket():
    pairs = pair_sttm_with_frd([MIDS_STTM, CAQH_STTM], [MIDS_FRD, CAQH_FRD],
                               explicit_map=MIDS_MAP)
    assert pairs == {MIDS_STTM: MIDS_FRD, CAQH_STTM: CAQH_FRD}
    # Without the map, MIDS does not auto-pair (no shared ticket).
    assert pair_sttm_with_frd([MIDS_STTM], [MIDS_FRD]) == {}


def test_heuristic_is_suggestion_only():
    # The >=3-token heuristic finds MIDS…
    assert suggest_pairs([MIDS_STTM], [MIDS_FRD]) == {MIDS_STTM: MIDS_FRD}
    # …but never enters pair_sttm_with_frd without the map.
    assert pair_sttm_with_frd([MIDS_STTM], [MIDS_FRD]) == {}
    # Ambiguity suggests nothing.
    assert suggest_pairs([MIDS_STTM], [MIDS_FRD, MIDS_FRD + " v2"]) == {}


def test_auto_pair_rules_map_then_ticket_then_stem():
    """Selection-time pairing (2026-09-18): map, then ticket, then the unique
    name-stem match; ambiguity or no match pairs nothing."""
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD, CAQH_FRD], explicit_map=MIDS_MAP) == (
        MIDS_FRD, "pairing_map")
    assert auto_pair_frd(CAQH_STTM, [MIDS_FRD, CAQH_FRD]) == (CAQH_FRD, "ticket")
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD]) == (MIDS_FRD, "name_stem")
    # Role tokens and a ".contract" suffix are not content: the CV pair matches.
    assert auto_pair_frd("demo_sttm_cv_golden.xlsx", ["FRD_demo_cv_golden.contract.json"]) == (
        "FRD_demo_cv_golden.contract.json", "name_stem")
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD, MIDS_FRD + " v2"]) is None
    assert auto_pair_frd("unrelated.xlsx", [MIDS_FRD, CAQH_FRD]) is None


def test_auto_pair_vdd_same_rules_never_the_sttm_itself():
    from codegen.demo_sources import auto_pair_vdd

    workbooks = [CAQH_STTM, "VDD_PaymentIntegrity_CAQH_1005034.xlsx", "other.xlsx"]
    assert auto_pair_vdd(CAQH_STTM, workbooks) == (
        "VDD_PaymentIntegrity_CAQH_1005034.xlsx", "ticket")
    assert auto_pair_vdd("demo_sttm_cv_golden.xlsx",
                         ["demo_sttm_cv_golden.xlsx", "VDD_demo_cv_golden.xlsx"]) == (
        "VDD_demo_cv_golden.xlsx", "name_stem")
    assert auto_pair_vdd("pair_1_family_a.xlsx", ["pair_1_v1_segments.xlsx"],
                         explicit_map={"pair_1_family_a": "pair_1_v1_segments"}) == (
        "pair_1_v1_segments.xlsx", "pairing_map")
    assert auto_pair_vdd("pair_1_family_a.xlsx", ["pair_1_v1_segments.xlsx"]) is None


def test_document_stem_strips_role_noise():
    assert document_stem("123_STTM_X_1005034 (1).xlsx") == "sttm_x_1005034"


# -- read_table_rows: allowlist + statement construction ----------------------- #


def _settings(**overrides):
    values = {
        "profile": "DEFAULT", "schema_name": "codegen_agent",
        "catalog": "soham_workspace", "frd_volume": "frd_raw",
        "sttm_volume": "sttm_raw", "warehouse_id": "wh123",
        "readable_tables": ["soham_workspace.sttm_agent.frd_contracts"],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _stub_statement(rows, columns):
    def execute_statement(statement, warehouse_id, wait_timeout):
        execute_statement.last = statement
        return SimpleNamespace(
            status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED"), error=None),
            manifest=SimpleNamespace(schema=SimpleNamespace(
                columns=[SimpleNamespace(name=c) for c in columns])),
            result=SimpleNamespace(data_array=rows),
        )
    return execute_statement


def test_read_table_rows_allowlist_and_select_only():
    cfg = db.config_for(_settings(), env={})
    with pytest.raises(db.DatabricksConfigError, match="readable_tables"):
        db.read_table_rows(cfg, "soham_workspace.sttm_agent.other", client=object())
    with pytest.raises(db.DatabricksConfigError, match="invalid column"):
        db.read_table_rows(cfg, "soham_workspace.sttm_agent.frd_contracts",
                           columns=["doc_id; DROP TABLE x"], client=object())

    execute = _stub_statement([["a", "PASS"]], ["doc_id", "status"])
    client = SimpleNamespace(statement_execution=SimpleNamespace(
        execute_statement=execute))
    db._TABLE_READ_CACHE.clear()
    rows = db.read_table_rows(cfg, "soham_workspace.sttm_agent.frd_contracts",
                              columns=["doc_id", "status"], limit=5, client=client)
    assert rows == [{"doc_id": "a", "status": "PASS"}]
    assert execute.last == ("SELECT `doc_id`, `status` FROM `soham_workspace`."
                            "`sttm_agent`.`frd_contracts` LIMIT 5")
    # Cached: a second call does not re-execute.
    execute.last = None
    assert db.read_table_rows(cfg, "soham_workspace.sttm_agent.frd_contracts",
                              columns=["doc_id", "status"], limit=5,
                              client=client) == rows
    assert execute.last is None
    db._TABLE_READ_CACHE.clear()


# -- upstream loader ----------------------------------------------------------- #


def _contract_json() -> str:
    import json

    return json.dumps({
        "contract_name": "t", "generated_from_frd": "t.docx",
        "generated_date": "2026-01-01T00:00:00", "generator": "t",
        "status": "PASS",
        "project": {"project_id": None, "project_name": "t",
                    "business_context_summary": None},
        "in_scope": [], "out_of_scope": [],
        "assumptions_constraints_dependencies": [],
        "feeds": [{
            "feed_name": "f1", "source_system": "S",
            "file_name_patterns": ["a.csv"], "file_format": "csv",
            "delimiter": None, "record_segments": [], "frequency": None,
            "load_windows_sla": [], "lobs": ["All"], "domain": None,
            "sub_domain": None, "landing_location": None,
            "stage_target": {"catalog": None, "schema": "stg", "tables": ["t1"],
                             "load_strategy": "Truncate and Load"},
            "standard_target": {"catalog": None, "schema": "std", "tables": [],
                                "load_strategy": "Append"},
            "validation_rules": [], "recycle_rule": None,
            "history_backfill": None, "archive_retention": None,
            "phi_pii_notes": None, "sttm_reference": None,
            "requirement_ids": [],
        }],
        "system_interfaces": [], "open_items": [],
    })


def test_upstream_loader_and_materialize(config, tmp_path, monkeypatch):
    from codegen import upstream_contracts as up

    rows = [{"doc_id": "FRD_X", "status": "PASS", "n_feeds": "1",
             "audited_at": "2026-07-20T05:47:41Z", "contract": _contract_json()}]
    monkeypatch.setattr(db, "read_table_rows",
                        lambda cfg, fqn, columns=None, limit=500, client=None: rows)
    contract, meta = up.load_contract(config, "FRD_X")
    assert contract.feeds[0].feed_name == "f1"
    assert meta["status"] == "PASS"

    with pytest.raises(up.UpstreamContractError, match="run the FRD"):
        up.load_contract(config, "FRD_MISSING")

    bad = [{**rows[0], "contract": '{"contract_name": "broken"}'}]
    monkeypatch.setattr(db, "read_table_rows",
                        lambda cfg, fqn, columns=None, limit=500, client=None: bad)
    with pytest.raises(up.UpstreamContractError, match="failed validation"):
        up.load_contract(config, "FRD_X")

    monkeypatch.setattr(db, "read_table_rows",
                        lambda cfg, fqn, columns=None, limit=500, client=None: rows)
    path, contract, _meta = up.materialize(config, "FRD_X", tmp_path)
    assert path.is_file() and path.suffix == ".json"
    assert path.read_text(encoding="utf-8") == _contract_json()


# -- truncated sheet names ----------------------------------------------------- #


def test_matcher_keys_on_stage_table_not_sheet_name():
    """Excel truncates sheet names at 31 chars; the matcher must key on the
    stage-table CELL, so a truncated sheet still matches its feed."""
    import json

    from codegen.contracts.frd import FrdContract
    from codegen.extract.extractor import ExtractionError, _match_frd_feed

    contract = FrdContract.model_validate(json.loads(_contract_json()))
    sheet = SimpleNamespace(
        sheet_name="MAPPING-VERY_LONG_TRUNCATED_NAM",  # 31 chars, truncated
        stage_table="t1",
    )
    assert _match_frd_feed(sheet, contract).feed_name == "f1"
    wrong = SimpleNamespace(sheet_name="MAPPING-VERY_LONG_TRUNCATED_NAM",
                            stage_table="nope")
    with pytest.raises(ExtractionError, match="matches 0 FRD feeds"):
        _match_frd_feed(wrong, contract)
