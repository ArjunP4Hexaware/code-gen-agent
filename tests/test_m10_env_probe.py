"""M10 — environment reconciliation: a read-only probe, DDL / DML adjusted to
what exists.

Both probe targets (ACFC's Unity Catalog, ACFC's SQL Server metadata DB) live
only inside the operator's workspace; here they are FAKES (tests/env_fakes.py).
Covers: all four states for a table and for a row; artefacts byte-identical
with the probe disabled, with everything absent and with everything
unreadable; the DML staying INSERT-only (UPDATE candidate commented out,
``dml.emit_updates`` turns it live); only the probed environment's script
adjusted; status columns never touched; no credential / profile ever resolved
outside a Databricks runtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from codegen import cli
from codegen.emit.dml import validate_tsql
from codegen.emit.framework import emit_framework
from codegen.env.clients import build_clients, probe_settings, render_select
from codegen.env.expect import expected_from_json
from codegen.env.model import ExpectedRow, ExpectedTable
from codegen.env.probe import ProbeUnreadable, Unavailable, probe_feed
from codegen.env.reconcile import build_reconciler, persist_result, report_section
from codegen.faq import FaqAnswer, LoadPatternFaq
from env_fakes import FakeDb, FakeUc, identical_row

pytest.importorskip("sqlglot", reason="sqlglot validates the emitted T-SQL")

PROBED_AT = "2026-09-21T12:00:00Z"
ON = {"CODEGEN_ENV_PROBE": "1", "CODEGEN_ENV_PROBE_ENVIRONMENT": "q1"}


def _faq(**extra) -> LoadPatternFaq:
    return LoadPatternFaq(
        rfc_number=FaqAnswer(value="SYN001", source="engineer"),
        feed_abbreviation=FaqAnswer(value="ACCUM", source="engineer"),
        pipeline_id=FaqAnswer(value="9101", source="engineer"),
        parent_pipeline_id=FaqAnswer(value="0", source="engineer"),
        group_id=FaqAnswer(value="9201", source="engineer"),
        object_id=FaqAnswer(value="1", source="engineer"),
        source_host=FaqAnswer(value="mft.synthetic.example", source="engineer"),
        connection_ids={"SRC_CONNECTION_ID": "31", "SRC_ADLS_CONNECTION_ID": "32",
                        "METADATA_CONNECTION_ID": "33", "TGT_CONNECTION_ID": "34"},
        **extra)


def _emit(config, spec, out: Path, *, uc=None, db=None, faq=None, enabled=True,
          expected_dir: Path | None = None):
    reconciler = build_reconciler(
        config, env=ON if enabled else {}, clients=(uc or FakeUc(), db or FakeDb()),
        probed_at=PROBED_AT, expected_dir=expected_dir) if enabled else None
    artefacts = emit_framework(spec, faq or _faq(), [], config, out,
                               conventions_profile="acfc_prx", iig_template="iig_v2",
                               env=reconciler)
    return artefacts, reconciler


def _digest(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _text(artefacts, name: str) -> str:
    return next(p for p in artefacts.files if p.name == name).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def expected(pair1_config, pair1_spec, tmp_path_factory):
    """What the pair-1 artefacts expect to find: (tables, rows)."""
    tmp = tmp_path_factory.mktemp("m10_expected")
    _emit(pair1_config, pair1_spec, tmp / "out", expected_dir=tmp / "expected")
    tables, rows = expected_from_json(tmp / "expected" / f"{pair1_spec.feed_slug}"
                                                         ".env_expected.json")
    assert [t.layer for t in tables] == ["stage", "standard"]
    assert rows and all(r.natural_key for r in rows if not r.unkeyed_reason)
    return tables, rows


@pytest.fixture(scope="module")
def baseline(pair1_config, pair1_spec, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("m10_baseline")
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp, enabled=False)
    return artefacts, _digest(tmp)


# ------------------------------------------------------------ the classifier


def test_a_table_reads_all_four_states():
    table = ExpectedTable(qualified="c.s.t", layer="stage",
                          columns=[("A", "STRING"), ("B", "Decimal(17,2)"), ("C", "INT")])
    uc = FakeUc({"c.s.same": [("a", "string"), ("b", "decimal(17, 2)"), ("c", "integer")],
                 "c.s.drift": [("A", "string"), ("B", "decimal(15,2)"), ("OLD", "date")],
                 "c.s.denied": RuntimeError("PERMISSION_DENIED: no CAN USE on the warehouse")})
    states = {}
    for name in ("same", "drift", "denied", "missing"):
        result = probe_feed("f", [table.model_copy(update={"qualified": f"c.s.{name}"})], [],
                            uc, Unavailable("n/a"), PROBED_AT)
        states[name] = result.objects[0]
    assert states["missing"].state == "absent"
    assert states["same"].state == "identical" and not states["same"].diffs   # spelling-insensitive
    drift = states["drift"]
    assert drift.state == "different"
    assert {(d.column, d.kind) for d in drift.diffs} == {("B", "type"), ("C", "added"),
                                                         ("OLD", "removed")}
    assert states["denied"].state == "unreadable" and "PERMISSION_DENIED" in states["denied"].error
    assert drift.evidence.query == "DESCRIBE TABLE c.s.drift" and drift.evidence.at == PROBED_AT


def test_a_row_reads_all_four_states_and_status_columns_stay_out_of_the_diff():
    row = ExpectedRow(table="T", sheet="T", row_index=0, natural_key={"NAME": "WF_X"},
                      values={"NAME": "WF_X", "FREQ": "Daily", "N": "1", "ACTIVE_FLAG": "S"},
                      status_columns=["ACTIVE_FLAG"])

    def one(db):
        return probe_feed("f", [], [row], Unavailable("n/a"), db, PROBED_AT).objects[0]

    assert one(FakeDb()).state == "absent"
    same = one(FakeDb({"T": [{"NAME": "WF_X", "FREQ": "Daily", "N": 1.0, "ACTIVE_FLAG": "Y"}]}))
    assert same.state == "identical"            # 1 == 1.0; the status column is report-only
    assert [(d.column, d.actual) for d in same.status_diffs] == [("ACTIVE_FLAG", "Y")]
    assert same.compared == ["FREQ", "N"]
    diff = one(FakeDb({"T": [{"NAME": "WF_X", "FREQ": "Weekly", "N": 1, "ACTIVE_FLAG": "S"}]}))
    assert diff.state == "different"
    assert [(d.column, d.expected, d.actual) for d in diff.diffs] == [("FREQ", "Daily", "Weekly")]
    refused = one(FakeDb(refuse={"T": "login failed"}))
    assert refused.state == "unreadable" and refused.error == "login failed"
    assert refused.evidence.query.startswith("SELECT TOP 2 ")
    twice = one(FakeDb({"T": [{"NAME": "WF_X"}, {"NAME": "WF_X"}]}))
    assert twice.state == "unreadable" and "matched 2 rows" in twice.error
    unkeyed = probe_feed("f", [], [row.model_copy(update={
        "natural_key": {}, "unkeyed_reason": "natural key column GROUP_ID has no value"})],
        Unavailable("n/a"), FakeDb(), PROBED_AT).objects[0]
    assert unkeyed.state == "unreadable" and "GROUP_ID" in unkeyed.error


def test_a_query_that_never_answers_is_given_up_not_waited_for():
    table = ExpectedTable(qualified="c.s.slow", layer="stage", columns=[("A", "STRING")])
    result = probe_feed("f", [table], [], FakeUc({"c.s.slow": "hang"}), Unavailable("n/a"),
                        PROBED_AT, timeout_seconds=0.2)
    assert result.objects[0].state == "unreadable"
    assert "did not answer within 0.2s" in result.objects[0].error


def test_the_only_metadata_db_statement_is_a_keyed_select_from_validated_identifiers():
    sql = render_select("dbo", "T", ["A", "B"], {"K": "it's"})
    assert sql == "SELECT TOP 2 [A], [B] FROM [dbo].[T] WHERE [K] = N'it''s'"
    for bad in (("dbo", "T; DROP TABLE x", ["A"], {"K": "v"}),
                ("dbo", "T", ["A]"], {"K": "v"}),
                ("dbo", "T", ["A"], {}),                       # never a whole table
                ("dbo", "T", ["A"], {"K": "two\nlines"})):
        with pytest.raises(ProbeUnreadable):
            render_select(*bad)


# ------------------------------------------- disabled / absent / unreadable


def test_probe_disabled_is_the_tracked_default_and_changes_nothing(pair1_config, baseline):
    assert probe_settings(pair1_config, env={}).enabled is False
    assert build_reconciler(pair1_config, env={}) is None
    artefacts, _ = baseline
    assert artefacts.env_result is None
    assert not any(f.startswith("env_") for f in artefacts.flags)


def test_everything_absent_writes_the_same_bytes_as_a_disabled_probe(
        pair1_config, pair1_spec, baseline, tmp_path):
    artefacts, reconciler = _emit(pair1_config, pair1_spec, tmp_path)
    assert _digest(tmp_path) == baseline[1]
    objects = artefacts.env_result.objects
    assert {o.state for o in objects if o.kind == "uc_table"} == {"absent"}
    # Rows the artefact cannot key are not guessed at: the IIG leaves
    # PROCESS_NAME / TEMPLATE_NAME to the client, and the FAQ's one object_id
    # makes DATA_QUALITY_RULES' rows share a key.
    unreadable = [o for o in objects if o.state == "unreadable"]
    assert {o.sheet for o in unreadable} == {"ADLS_FIXED_WIDTH_HANDLER", "EMAIL_TEMPLATE_CONFIG",
                                             "DATA_QUALITY_RULES"}
    assert all("no value at generation time" in o.error or "shared by" in o.error
               for o in unreadable)
    assert {o.state for o in objects if o.kind == "config_row"} == {"absent", "unreadable"}
    assert sum(f.startswith("env_absent:") for f in artefacts.flags) == sum(
        o.state == "absent" for o in objects)
    assert reconciler.results[pair1_spec.feed_slug] is artefacts.env_result


def test_everything_unreadable_is_a_flag_never_a_stop(pair1_config, pair1_spec, baseline,
                                                      tmp_path):
    """The ACFC reality today: the App's service principal has no warehouse
    permission — every object reads unreadable and the run proceeds as ever."""
    reason = "PERMISSION_DENIED: the service principal lacks CAN USE on the warehouse"
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path,
                         uc=Unavailable(reason), db=Unavailable("no JDBC secrets"))
    assert _digest(tmp_path) == baseline[1]
    assert {o.state for o in artefacts.env_result.objects} == {"unreadable"}
    assert all(c.passed for c in artefacts.checks)          # a flag, never a FAIL
    assert any(f.startswith("env_unreadable:") and "CAN USE" in f for f in artefacts.flags)


# ------------------------------------------------------------------ the DDL


def test_an_identical_table_gets_a_comment_and_no_create(pair1_config, pair1_spec, expected,
                                                         tmp_path):
    tables, _rows = expected
    stage = tables[0]
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path,
                         uc=FakeUc({stage.qualified: stage.columns}))
    ddl = _text(artefacts, "ACCUM_DDL.txt")
    assert f"-- ENVIRONMENT identical: {stage.qualified} exists and matches this DDL" in ddl
    assert f"CREATE OR REPLACE TABLE {stage.qualified}" not in ddl
    assert f"CREATE OR REPLACE TABLE {tables[1].qualified}" in ddl     # absent: as ever
    assert any(f == f"env_identical:{stage.qualified}" for f in artefacts.flags)
    assert next(c for c in artefacts.checks if c.name == "sql_literals").passed


def test_a_different_table_gets_add_columns_and_a_review_block_never_a_drop(
        pair1_config, pair1_spec, expected, tmp_path):
    tables, _rows = expected
    standard = tables[1]
    actual = [(n, t) for n, t in standard.columns[:-2]]              # two columns missing
    actual[1] = (actual[1][0], "BINARY")                             # a type difference
    actual.append(("LEGACY_COL", "string"))                          # one the DDL lacks
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path,
                         uc=FakeUc({standard.qualified: actual}))
    ddl = _text(artefacts, "ACCUM_DDL.txt")
    assert f"CREATE OR REPLACE TABLE {standard.qualified}" not in ddl
    assert f"ALTER TABLE {standard.qualified} ADD COLUMNS (" in ddl
    for name, dtype in standard.columns[-2:]:
        assert f"  {name} {dtype}" in ddl
    assert "-- REVIEW - differences with NO statement" in ddl
    assert f"--   {standard.columns[1][0]}: type - this DDL {standard.columns[1][1]} | " \
           "environment BINARY" in ddl
    assert "--   LEGACY_COL: in the environment (string), not in this DDL" in ddl
    assert "DROP" not in ddl.replace("Never DROP", "")
    flag = next(f for f in artefacts.flags if f.startswith("env_different:"))
    assert "LEGACY_COL (removed)" in flag and "(added)" in flag and "(type)" in flag


def test_a_profile_without_reconcile_ddl_keeps_its_create_and_still_flags(
        pair1_config, pair1_spec, expected, baseline, tmp_path):
    """"Unchanged behaviour": the reference profile's default — its goldens stay
    byte-identical even with the probe on and the table present."""
    tables, _rows = expected
    profiles = dict(pair1_config.conventions.profiles)
    profiles["acfc_prx"] = profiles["acfc_prx"].model_copy(update={"reconcile_ddl": False})
    config = pair1_config.model_copy(update={"conventions": pair1_config.conventions.model_copy(
        update={"profiles": profiles})})
    assert pair1_config.conventions.profiles["edo_sfmc"].reconcile_ddl is False
    artefacts, _ = _emit(config, pair1_spec, tmp_path,
                         uc=FakeUc({tables[0].qualified: tables[0].columns}))
    assert _text(artefacts, "ACCUM_DDL.txt") == _text(baseline[0], "ACCUM_DDL.txt")
    assert any(f.startswith("env_identical:") for f in artefacts.flags)
    section = report_section(artefacts.env_result, False, False, "q1")
    assert "CREATE statement regardless (conventions reconcile_ddl is off)" in section


def test_the_two_file_layout_adjusts_per_table(pair1_config, pair1_spec, tmp_path):
    """edo_sfmc layout (two .txt files, per-column COMMENTs) with the knob on."""
    profiles = dict(pair1_config.conventions.profiles)
    profiles["edo_sfmc"] = profiles["edo_sfmc"].model_copy(update={"reconcile_ddl": True})
    config = pair1_config.model_copy(update={
        "output": pair1_config.output.model_copy(update={
            "dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")}),
        "conventions": pair1_config.conventions.model_copy(update={"profiles": profiles})})
    first = build_reconciler(config, env=ON, clients=(FakeUc(), FakeDb()), probed_at=PROBED_AT,
                             expected_dir=tmp_path / "expected")
    cli._generate_feed(pair1_spec, config, dry_run=True, skip_tests=True,
                       output_mode="framework", env=first)
    tables, _ = expected_from_json(tmp_path / "expected" / f"{pair1_spec.feed_slug}"
                                                           ".env_expected.json")
    stage = next(t for t in tables if t.layer == "stage")
    second = build_reconciler(config, env=ON, probed_at=PROBED_AT,
                              clients=(FakeUc({stage.qualified: stage.columns[1:]}), FakeDb()))
    gate = cli._generate_feed(pair1_spec, config, dry_run=True, skip_tests=True,
                              output_mode="framework", env=second)
    text = (tmp_path / "out" / pair1_spec.feed_slug / "framework"
            / f"{pair1_spec.feed_slug}_stage_table_creation.txt").read_text(encoding="utf-8")
    assert f"ALTER TABLE {stage.qualified} ADD COLUMNS (" in text
    assert f"  {stage.columns[0][0]} {stage.columns[0][1]} COMMENT '" in text
    assert f"CREATE OR REPLACE TABLE {stage.qualified} (" not in text
    assert gate.verdict != "FAIL"
    report = (tmp_path / "reports" / f"{pair1_spec.feed_slug}.md").read_text(encoding="utf-8")
    assert "## Environment" in report and "| Object | State | Evidence |" in report
    assert "ALTER TABLE ADD COLUMNS (1)" in report


# ------------------------------------------------------------------ the DML


def _db_with(rows, mutate=None) -> FakeDb:
    data: dict[str, list[dict]] = {}
    for row in rows:
        if row.unkeyed_reason:
            continue
        found = identical_row(row)
        if mutate:
            found = mutate(row, found)
        if found is not None:
            data.setdefault(row.table, []).append(found)
    return FakeDb(data)


def test_identical_rows_are_skipped_with_a_comment_and_an_assertion(
        pair1_config, pair1_spec, expected, baseline, tmp_path):
    _tables, rows = expected
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path, db=_db_with(rows))
    q1 = _text(artefacts, "config_inserts_q1.sql")
    keyed = [r for r in rows if not r.unkeyed_reason]
    assert q1.count("-- ENVIRONMENT identical: ") == len(keyed)
    assert q1.count("INSERT INTO [dbo].[") == 1 + len(rows) - len(keyed)   # +1: the connection
    assert "IF NOT EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE " \
           "[PIPELINE_NAME] = N'" in q1
    assert "was identical to this script, no longer" in q1
    # the unused-id assertions would refuse the very state the probe reported
    assert "PIPELINE_ID %d is already used" not in q1
    assert "ENVIRONMENT STATE = adjusted to the read-only probe of q1 at " + PROBED_AT in q1
    assert validate_tsql(q1) == []
    assert all(c.passed for c in artefacts.checks if c.name.startswith("dml_"))
    # a probe sees ONE metadata DB: the other environments' scripts are untouched
    for env in ("a2", "prod"):
        name = f"config_inserts_{env}.sql"
        assert _text(artefacts, name) == _text(baseline[0], name)


def test_a_different_row_stays_insert_only_with_a_commented_out_update_candidate(
        pair1_config, pair1_spec, expected, tmp_path):
    _tables, rows = expected
    target = next(r for r in rows if r.table == "DATA_FACTORY_PIPELINE_SCHEDULE")

    def mutate(row, found):
        if row is target:
            return {**found, "PIPELINE_FREQUENCY": "Hourly", "ACTIVE_FLAG": "N"}
        return None                                           # every other row: absent

    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path, db=_db_with(rows, mutate))
    q1 = _text(artefacts, "config_inserts_q1.sql")
    name = target.natural_key["PIPELINE_NAME"]
    label = f"DATA_FACTORY_PIPELINE_SCHEDULE[PIPELINE_NAME={name}]"
    assert f"-- REVIEW {label}: exists and DIFFERS from this row — INSERT skipped" in q1
    assert "--   [PIPELINE_FREQUENCY]: this script N'" in q1 and "| environment N'Hourly'" in q1
    assert "UPDATE candidate — NOT executed (dml.emit_updates is off" in q1
    candidate = next(ln for ln in q1.splitlines() if "UPDATE [dbo]." in ln)
    assert candidate.startswith("--   UPDATE [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] SET "
                                "[PIPELINE_FREQUENCY] = N'")
    assert "[UPDATED_BY] = @RFC_NUMBER, [UPDATED_DATE] = GETDATE() WHERE " \
           f"[PIPELINE_NAME] = N'{name}';" in candidate
    # status columns are reported, never touched: not in the diff, the candidate or an assertion
    assert "ACTIVE_FLAG" not in candidate
    assert not any("ACTIVE_FLAG" in ln for ln in q1.splitlines() if "RAISERROR" in ln)
    # no live UPDATE anywhere; the row is not inserted a second time
    assert not [ln for ln in q1.splitlines() if ln.startswith("UPDATE ")]
    inserted = [ln for ln in q1.splitlines()
                if ln.startswith("INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE]")]
    assert len(inserted) == 3 and not any(f"N'{name}'" in ln for ln in inserted)
    # ...and the script refuses to run while the row still differs
    assert f"{label} still differs from this script in PIPELINE_FREQUENCY" in q1
    # rows that were absent gain a "still absent" assertion in an adjusted script
    assert "was absent, now exists" in q1
    assert validate_tsql(q1) == []
    assert any(f.startswith(f"dml_review:{label}") for f in artefacts.flags)
    section = report_section(artefacts.env_result, True, False, "q1")
    assert "status columns differ and are NOT touched (ACTIVE_FLAG: this script S -> " \
           "environment N)" in section
    assert "UPDATE candidate commented out" in section


def test_emit_updates_turns_the_candidate_live(pair1_config, pair1_spec, expected, tmp_path):
    _tables, rows = expected
    target = next(r for r in rows if r.table == "DATA_FACTORY_PIPELINE_SCHEDULE")
    config = pair1_config.model_copy(update={
        "dml": pair1_config.dml.model_copy(update={"emit_updates": True})})
    assert pair1_config.dml.emit_updates is False              # the tracked default
    artefacts, _ = _emit(config, pair1_spec, tmp_path, db=_db_with(
        rows, lambda row, found: {**found, "PIPELINE_FREQUENCY": "Hourly"}
        if row is target else None))
    q1 = _text(artefacts, "config_inserts_q1.sql")
    live = [ln for ln in q1.splitlines() if ln.startswith("UPDATE ")]
    assert len(live) == 1 and "[PIPELINE_FREQUENCY] = N'" in live[0]
    assert "no longer holds the probed values of PIPELINE_FREQUENCY" in q1
    assert "[PIPELINE_FREQUENCY] = N'Hourly'" in q1            # the probed value is asserted
    assert validate_tsql(q1) == []


def test_the_faq_may_hand_the_status_columns_to_the_agent(pair1_config, pair1_spec, expected,
                                                          tmp_path):
    _tables, rows = expected
    target = next(r for r in rows if r.table == "DATA_FACTORY_PIPELINE_SCHEDULE")
    faq = _faq(manage_row_status=FaqAnswer(value="yes", source="engineer"))
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path, faq=faq, db=_db_with(
        rows, lambda row, found: {**found, "ACTIVE_FLAG": "N"} if row is target else None))
    q1 = _text(artefacts, "config_inserts_q1.sql")
    assert "--   [ACTIVE_FLAG]: this script N'S' | environment N'N'" in q1


def test_unassigned_ids_leave_their_rows_unreadable_not_guessed(pair1_config, pair1_spec,
                                                                baseline, tmp_path):
    """No FAQ ids -> GROUP_ID / OBJECT_ID are script variables still NULL: a row
    keyed on them cannot be looked up, and says so."""
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path, faq=LoadPatternFaq(
        feed_abbreviation=FaqAnswer(value="ACCUM", source="engineer")))
    unkeyed = [o for o in artefacts.env_result.objects
               if o.kind == "config_row" and o.state == "unreadable"]
    assert unkeyed and all("natural key column" in o.error for o in unkeyed)
    assert any(o.state == "absent" and o.table == "DATA_FACTORY_PIPELINE_SCHEDULE"
               for o in artefacts.env_result.objects)         # keyed by PIPELINE_NAME


# ----------------------------------------------- the edge: state, hand-off


def test_the_result_is_written_to_the_state_role_with_provenance(pair1_config, pair1_spec,
                                                                 expected, tmp_path):
    from codegen.storage import open_storage

    tables, _rows = expected
    artefacts, _ = _emit(pair1_config, pair1_spec, tmp_path / "out",
                         uc=FakeUc({tables[0].qualified: tables[0].columns}))
    stores = open_storage(pair1_config, tmp_path, env={
        "CODEGEN_STORAGE_STATE": f"local:{(tmp_path / 'state').as_posix()}"})
    (tmp_path / "state").mkdir()
    path = persist_result(artefacts.env_result, stores.state)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "state" / "env_probe" / f"{pair1_spec.feed_slug}.json"
    first = saved["objects"][0]
    assert first["state"] == "identical"
    # M13: evidence names WHO asked — the fake client declares no identity.
    assert first["evidence"] == {"source": "unity_catalog", "at": PROBED_AT,
                                 "query": f"DESCRIBE TABLE {tables[0].qualified}",
                                 "identity": None}


def test_a_result_probed_elsewhere_is_used_instead_of_asking(pair1_config, pair1_spec,
                                                             expected, tmp_path):
    """The notebook fallback probes in-process (spark + secrets live there) and
    hands the CLI a file: `generate --env-probe-result`."""
    tables, _rows = expected
    first, _ = _emit(pair1_config, pair1_spec, tmp_path / "a",
                     uc=FakeUc({tables[0].qualified: tables[0].columns}))
    handoff = tmp_path / "probe.json"
    handoff.write_text(first.env_result.model_dump_json(), encoding="utf-8")
    never = FakeUc()
    reconciler = build_reconciler(pair1_config, env={}, preset_path=handoff,
                                  clients=(never, FakeDb()))
    second = emit_framework(pair1_spec, _faq(), [], pair1_config, tmp_path / "b",
                            conventions_profile="acfc_prx", iig_template="iig_v2",
                            env=reconciler)
    assert never.asked == []
    assert _text(second, "ACCUM_DDL.txt") == _text(first, "ACCUM_DDL.txt")


# ------------------------------------- nothing local is ever resolved


def test_outside_a_databricks_runtime_no_client_is_built_and_no_profile_is_read(
        pair1_config, monkeypatch):
    import codegen.databricks as seam

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the probe must never resolve a CLI profile")

    monkeypatch.setattr(seam, "_client", forbidden)
    settings = probe_settings(pair1_config, env={**ON,
                                                 "CODEGEN_ENV_PROBE_WAREHOUSE_ID": "abc123"})
    uc, db = build_clients(pair1_config, settings, env={})
    assert isinstance(uc, Unavailable) and isinstance(db, Unavailable)
    assert "not inside a Databricks workspace runtime" in uc.reason


def test_the_probe_never_falls_back_to_the_databricks_section(pair1_config):
    """databricks.warehouse_id names ANOTHER workspace's warehouse."""
    assert pair1_config.databricks.warehouse_id          # still tracked, still ignored here
    settings = probe_settings(pair1_config, env=ON)
    assert settings.uc_warehouse_id == ""
    tracked = pair1_config.env.probe
    assert (tracked.enabled, tracked.environment, tracked.uc_warehouse_id) == (False, "", "")
    assert not any(tracked.metadata_db.model_dump().values())
    with pytest.raises(ValueError, match="expected one of"):
        probe_settings(pair1_config, env={"CODEGEN_ENV_PROBE_ENVIRONMENT": "staging"})


def test_describe_table_sql_renders_the_statement_and_refuses_anything_else():
    from types import SimpleNamespace

    import codegen.databricks as seam

    sent = {}

    def execute_statement(statement, warehouse_id, wait_timeout):
        sent.update(statement=statement, warehouse_id=warehouse_id, wait_timeout=wait_timeout)
        return SimpleNamespace(
            status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED"), error=None),
            result=SimpleNamespace(data_array=[["A", "string", None], ["B", "int", None],
                                               ["", "", ""], ["# Clustering", "", ""]]))

    client = SimpleNamespace(statement_execution=SimpleNamespace(
        execute_statement=execute_statement))
    columns, statement = seam.describe_table_sql(None, "cat.sch.tbl", "wh1", 20, client=client)
    assert statement == sent["statement"] == "DESCRIBE TABLE `cat`.`sch`.`tbl`"
    assert sent["warehouse_id"] == "wh1" and sent["wait_timeout"] == "20s"
    assert columns == [{"name": "A", "type": "string"}, {"name": "B", "type": "int"}]
    for bad in ("cat.sch", "cat.sch.tbl; DROP TABLE x", "cat.sch.`t`"):
        with pytest.raises(seam.DatabricksConfigError):
            seam.describe_table_sql(None, bad, "wh1", client=client)
    with pytest.raises(seam.DatabricksConfigError, match="no warehouse id"):
        seam.describe_table_sql(None, "cat.sch.tbl", "", client=client)

    def not_found(statement, warehouse_id, wait_timeout):
        return SimpleNamespace(status=SimpleNamespace(
            state=SimpleNamespace(value="FAILED"),
            error=SimpleNamespace(message="[TABLE_OR_VIEW_NOT_FOUND] The table cannot be found")),
            result=None)

    missing = SimpleNamespace(statement_execution=SimpleNamespace(execute_statement=not_found))
    with pytest.raises(seam.TableNotFound):
        seam.describe_table_sql(None, "cat.sch.tbl", "wh1", client=missing)
