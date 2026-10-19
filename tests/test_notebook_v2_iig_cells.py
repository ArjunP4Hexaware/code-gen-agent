"""post70: the cells v1 had that v2 adds — only where an IIG cell states them.

- SCHEMA_DRIFT_FLAG = Y -> a drift-check cell before the stage cell (a missing
  column stops the run before anything is written);
- RECYCL_ENBL_FLG = Y -> a recycle cell over RECYCL_TBL_NM / RECYCL_ADLS_PATH /
  RECYCL_RETN_DAYS (each needed: an open one stops the run in the config cell);
- always, a final run-report cell: row counts per step and the DQ rule counts,
  appended to a ``<feed>_run_report`` table in the stage schema.

PHI masking has no IIG cell: v2 has none (docs/acfc/OPEN_QUESTIONS.md).
Every variant compiles and is ruff-clean (delimited and fixed width).
"""

from __future__ import annotations

import copy

import pytest

import notebook_v2_fixtures as fx
from codegen.emit import notebook_files as nbf
from codegen.emit import notebook_v2


def _payload(tmp_path, pair=None, config=None, spec_index=0):
    from codegen.faq import faq_for_spec
    from codegen.metadata_sheet import metadata_sheet_payload
    from codegen.resolve.resolver import resolve_pair

    config = config or fx.acfc_config(tmp_path)
    frd, sttm = pair or fx.sfmc_pair()
    spec = resolve_pair(frd, sttm, config)[spec_index]
    payload = metadata_sheet_payload(
        config, fx.REPO, [spec], {spec.feed_slug: set()}, "test",
        {spec.feed_slug: faq_for_spec(spec, config, base_dir=fx.REPO)}, frd,
        template="iig_v2", conventions_profile="acfc_prx")
    return spec, config, payload, frd


def _set(payload: dict, tab: str, **values) -> dict:
    payload = copy.deepcopy(payload)
    for row in payload["tabs"][tab]["rows"]:
        row["values"].update(values)
    return payload


def _render(spec, config, payload, frd):
    context, flags = notebook_v2.build_context(spec, config, payload, candidates=[],
                                               frd_path=frd, iig_template="iig_v2")
    cells = notebook_v2.render_cells(context)
    assert nbf.check_cells_compile(cells).passed
    source = nbf.databricks_source(cells)
    assert nbf.check_ruff(source).passed, nbf.check_ruff(source).details
    return context, flags, cells, {c.cell_id: c.text for c in cells}


ADLS = notebook_v2.ADLS


def test_schema_drift_flag_y_adds_a_drift_cell_before_the_stage(tmp_path):
    spec, config, payload, frd = _payload(tmp_path)
    _c, _f, cells, by_id = _render(spec, config, _set(payload, ADLS, SCHEMA_DRIFT_FLAG="N"),
                                   frd)
    assert "drift" not in by_id and "check_drift" not in by_id["run"]
    _c, _f, cells, by_id = _render(spec, config, _set(payload, ADLS, SCHEMA_DRIFT_FLAG="Y"),
                                   frd)
    ids = [c.cell_id for c in cells]
    assert ids.index("drift") < ids.index("stage") and "drift-provenance" in ids
    assert "def check_drift" in by_id["drift"] and "SRC_COLUMNS" in by_id["drift"]
    assert 'if source["schema_drift"]:' in by_id["run"]
    run = by_id["run"]
    assert run.index("check_drift(files, source)") < run.index("write_stage(")
    assert "SCHEMA_DRIFT_FLAG" in by_id["drift-provenance"]


def test_recycle_flag_y_adds_a_recycle_cell_from_the_three_cells(tmp_path):
    spec, config, payload, frd = _payload(tmp_path)
    context, _f, cells, by_id = _render(spec, config, payload, frd)    # SFMC: Y
    (source,) = context["sources"]
    assert source["recycle"] == {"table": source["recycle"]["table"],
                                 "path": source["recycle"]["path"], "days": 7}
    assert source["recycle"]["table"] and source["recycle"]["path"]
    assert "def recycle_backlog" in by_id["recycle"] and "RECYCL_RETN_DAYS" in by_id["recycle"]
    assert "keep_for_recycle(rejected, source)" in by_id["run"]
    assert "recycle_backlog(source)" in by_id["run"]
    for header in ("RECYCL_ENBL_FLG", "RECYCL_TBL_NM", "RECYCL_ADLS_PATH", "RECYCL_RETN_DAYS"):
        assert header in by_id["recycle-provenance"]
    _c, _f, _cells, by_id = _render(spec, config, _set(payload, ADLS, RECYCL_ENBL_FLG="N"), frd)
    assert "recycle" not in by_id and "recycle_backlog" not in by_id["run"]


@pytest.mark.parametrize("header", ["RECYCL_TBL_NM", "RECYCL_ADLS_PATH", "RECYCL_RETN_DAYS"])
def test_an_open_recycle_cell_stops_the_run_in_the_config_cell(tmp_path, header):
    spec, config, payload, frd = _payload(tmp_path)
    context, flags, _cells, _by = _render(spec, config, _set(payload, ADLS, **{header: ""}), frd)
    assert any(c.startswith(f"{ADLS}.{header}") for c in context["open_cells"])
    assert any(f.startswith(f"notebook_iig_cell_open:{ADLS}.{header}") for f in flags)


def test_a_retention_that_is_not_whole_days_is_open(tmp_path):
    spec, config, payload, frd = _payload(tmp_path)
    context, _f, _c, _b = _render(spec, config, _set(payload, ADLS, RECYCL_RETN_DAYS="1 week"),
                                  frd)
    assert any("RECYCL_RETN_DAYS" in c and "whole number" in c for c in context["open_cells"])


def test_the_run_report_is_the_last_cell_and_writes_to_the_stage_schema(tmp_path):
    spec, config, payload, frd = _payload(tmp_path)
    context, _f, cells, by_id = _render(spec, config, payload, frd)
    assert [c.cell_id for c in cells][-2:] == ["run-report", "run-report-provenance"]
    report = by_id["run-report"]
    assert 'table_name(STAGE_CATALOG, SOURCES[0]["schema"], RUN_REPORT_TABLE)' in report
    assert f'RUN_REPORT_TABLE = "{spec.feed_slug}_run_report"' in by_id["config"]
    # row counts per step and the DQ counts are tallied as the run goes
    assert 'tally("read"' in by_id["run"]
    assert "tally(f\"written" in by_id["stage"]
    assert "tally(\"rejects" in by_id["read"]
    if any(c["kind"] == "dedup" for c in context["stage_calls"] + context["std_calls"]):
        assert "dq DeDuplicationRule" in by_id["dq"]
    assert "TGT_DATABASE_NAME" in by_id["run-report-provenance"]


def test_no_phi_masking_cell_without_an_iig_cell(tmp_path):
    spec, config, payload, frd = _payload(tmp_path)
    _c, _f, cells, by_id = _render(spec, config, payload, frd)
    assert not any("mask" in cid for cid in by_id)
    assert "mask" not in "".join(by_id.values()).lower()


def test_fixed_width_drift_and_recycle_compile(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    config = fx.acfc_config(tmp_path, fx.PAIR1_OVERLAY)
    frd, sttm, _vdd = fx.prx_pair(tmp_path, config)
    spec, config, payload, frd = _payload(tmp_path, (frd, sttm), config)
    payload = _set(payload, ADLS, SCHEMA_DRIFT_FLAG="Y", RECYCL_ENBL_FLG="Y",
                   RECYCL_TBL_NM="syn_recycle", RECYCL_ADLS_PATH="/syn/recycle",
                   RECYCL_RETN_DAYS="30")
    context, _f, _cells, by_id = _render(spec, config, payload, frd)
    assert context["fixed_width"]
    assert "F.length(\"value\") < width" in by_id["drift"]
    assert "def keep_for_recycle" in by_id["recycle"]


def test_the_overlay_default_is_y_and_a_feed_override_sets_n(tmp_path):
    """post70: SCHEMA_DRIFT_FLAG Y by the ACFC overlay (the SD golden); a feed
    whose golden says N sets feed_overrides.<feed>.schema_drift_flag."""
    from codegen.config import FeedOverrideConfig

    spec, config, payload, frd = _payload(tmp_path)
    assert {r["values"]["SCHEMA_DRIFT_FLAG"] for r in payload["tabs"][ADLS]["rows"]} == {"Y"}
    _c, _f, cells, by_id = _render(spec, config, payload, frd)
    assert "drift" in by_id
    tpl = config.metadata.templates["iig_v2"]
    tpl = tpl.model_copy(update={"feed_overrides": {
        **tpl.feed_overrides, spec.feed_id: FeedOverrideConfig(schema_drift_flag="N")}})
    config = config.model_copy(update={"metadata": config.metadata.model_copy(
        update={"templates": {**config.metadata.templates, "iig_v2": tpl}})})
    spec, config, payload, frd = _payload(tmp_path / "n", config=config)
    assert {r["values"]["SCHEMA_DRIFT_FLAG"] for r in payload["tabs"][ADLS]["rows"]} == {"N"}
    _c, _f, cells, by_id = _render(spec, config, payload, frd)
    assert "drift" not in by_id
