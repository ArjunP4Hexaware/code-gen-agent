"""M13 — probe snapshots: run the environment check AS THE USER, consume it
anywhere.

The probe's targets exist only inside ACFC; here they are FAKES — a fake
SparkSession (SQL + a JDBC reader) and fake dbutils — and the session-wide
socket guard (tests/conftest.py) fails any test that reaches the network.

Covers: the `spark` seam's statements (validated identifiers, read-only, the
information_schema / DESCRIBE TABLE EXTENDED split, the identity recorded);
`codegen probe` end to end on pair 1; `generate --probe-snapshot` adjusting
the artefacts EXACTLY as a live probe with the same answers; a snapshot
replayed against changed expectations; stale / missing snapshots; the App
setting reading <state>/probes/<feed>.json; the deployment headline; no
snapshot = no change.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from codegen import cli
from codegen.emit.framework import emit_framework
from codegen.env import spark_seam
from codegen.env.expect import expected_from_json
from codegen.env.model import (
    EnvProbeResult,
    ExpectedTable,
    ProbedObject,
    ProbeSnapshot,
    deployment_headline,
    env_flags,
)
from codegen.env.probe import ProbeUnreadable, Unavailable, probe_feed
from codegen.env.reconcile import build_reconciler, report_section
from codegen.env.snapshot import (
    SnapshotUcClient,
    load_snapshot,
    write_snapshot,
    write_to_state,
)
from env_fakes import FakeDb, FakeUc
from test_m10_env_probe import ON, PROBED_AT, _db_with, _digest, _faq

pytest.importorskip("sqlglot", reason="sqlglot validates the emitted T-SQL")

REPO = Path(__file__).resolve().parents[1]
PAIR1_OVERLAY = REPO / "fixtures" / "acfc_shapes" / "pair_1" / "config_overlay.yaml"
USER = "analyst@synthetic.example"
Q1 = {"CODEGEN_ENV_PROBE_ENVIRONMENT": "q1"}          # which DB; the LIVE probe stays off
SECRETS = {"CODEGEN_ENV_PROBE_SECRET_SCOPE": "syn-scope",
           "CODEGEN_ENV_PROBE_JDBC_URL_SECRET": "syn-url",
           "CODEGEN_ENV_PROBE_USER_SECRET": "syn-user",
           "CODEGEN_ENV_PROBE_PASSWORD_SECRET": "syn-pass"}
# Every statement the spark seam may send — anything else is a bug.
ALLOWED = [
    re.compile(r"^SELECT current_user\(\)$"),
    re.compile(r"^SELECT column_name, full_data_type FROM `\w+`\.information_schema\.columns "
               r"WHERE table_schema = '\w+' AND table_name = '\w+' ORDER BY ordinal_position$"),
    re.compile(r"^DESCRIBE TABLE EXTENDED `\w+`\.`\w+`\.`\w+`$"),
]


# ================================================================== fakes


class _Frame:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return list(self._rows)


class _Row(dict):
    def asDict(self):  # noqa: N802 — pyspark's name
        return dict(self)


class _JdbcReader:
    """``spark.read.format("jdbc").option(...).load()`` answering the ONE
    keyed SELECT from table -> rows, by parsing the rendered statement."""

    def __init__(self, session):
        self._session = session
        self._options: dict[str, str] = {}

    def format(self, name):
        assert name == "jdbc"
        return self

    def option(self, key, value):
        self._options[key] = value
        return self

    def load(self):
        query = self._options["query"]
        self._session.jdbc_queries.append(query)
        match = re.match(r"^SELECT TOP 2 .+ FROM \[\w+\]\.\[(\w+)\] WHERE (.+)$", query)
        assert match, query
        key = dict(re.findall(r"\[(\w+)\] = N'((?:[^']|'')*)'", match.group(2)))
        key = {k: v.replace("''", "'") for k, v in key.items()}
        found = [_Row(r) for r in self._session.db_rows.get(match.group(1), [])
                 if all(str(r.get(k)) == v for k, v in key.items())]
        return _Frame(found)


class FakeSpark:
    """``tables``: qualified (lower) -> [(column, type)] | "denied".
    ``invisible``: tables information_schema does not list (DESCRIBE does)."""

    def __init__(self, tables=None, db_rows=None, invisible=(), user=USER):
        self.tables = {k.lower(): v for k, v in (tables or {}).items()}
        self.db_rows = db_rows or {}
        self.invisible = {k.lower() for k in invisible}
        self.user = user
        self.statements: list[str] = []
        self.jdbc_queries: list[str] = []

    @property
    def read(self):
        return _JdbcReader(self)

    def sql(self, statement: str):
        self.statements.append(statement)
        if statement == "SELECT current_user()":
            return _Frame([(self.user,)])
        info = re.match(r"^SELECT .+ FROM `(\w+)`\.information_schema\.columns WHERE "
                        r"table_schema = '(\w+)' AND table_name = '(\w+)'", statement)
        if info:
            name = ".".join(info.groups()).lower()
            found = self.tables.get(name)
            if found is None or found == "denied" or name in self.invisible:
                return _Frame([])
            return _Frame([tuple(c) for c in found])
        described = re.match(r"^DESCRIBE TABLE EXTENDED `(\w+)`\.`(\w+)`\.`(\w+)`$", statement)
        if described:
            name = ".".join(described.groups()).lower()
            found = self.tables.get(name)
            if found is None:
                raise RuntimeError(f"[TABLE_OR_VIEW_NOT_FOUND] The table or view {name} "
                                   "cannot be found.")
            if found == "denied":
                raise RuntimeError("[INSUFFICIENT_PERMISSIONS] User does not have SELECT")
            return _Frame([*[(n, t, None) for n, t in found], ("", "", ""),
                           ("# Detailed Table Information", "", ""), ("Catalog", "x", "")])
        raise AssertionError(f"a statement the seam may never send: {statement}")


class FakeDbutils:
    def __init__(self):
        self.asked: list[tuple[str, str]] = []
        self.secrets = self

    def get(self, scope, key):
        self.asked.append((scope, key))
        return {"syn-url": "jdbc:sqlserver://db.example.invalid:1433;databaseName=meta",
                "syn-user": "syn_login", "syn-pass": "not-a-real-credential"}[key]


def _allowed(statements):
    return [s for s in statements if not any(p.match(s) for p in ALLOWED)]


# ============================================================ the spark seam


def test_the_seam_reads_as_the_user_with_validated_statements_only():
    spark = FakeSpark({"c.s.same": [("A", "string")], "c.s.hidden": [("A", "string")],
                       "c.s.denied": "denied"}, invisible=["c.s.hidden"])
    client = spark_seam.SparkUcClient(spark)
    assert client.identity == USER and client.transport == "spark"
    assert client.describe("c.s.same") == ([("A", "string")], spark.statements[-1])
    # not listed by information_schema, but there: DESCRIBE decides
    columns, statements = client.describe("c.s.hidden")
    assert columns == [("A", "string")] and "DESCRIBE TABLE EXTENDED" in statements
    columns, statements = client.describe("c.s.gone")
    assert columns is None and "information_schema" in statements
    with pytest.raises(ProbeUnreadable, match="INSUFFICIENT_PERMISSIONS"):
        client.describe("c.s.denied")
    before = list(spark.statements)
    for bad in ("c.s.t; DROP TABLE x", "c.s", "c.s.t`", "c.s.t'--"):
        with pytest.raises(ProbeUnreadable, match="invalid table name"):
            client.describe(bad)
    assert spark.statements == before                        # never sent
    assert _allowed(spark.statements) == []


def test_probe_clients_prefer_the_session_and_fall_back_to_the_warehouse_seam(pair1_config):
    from codegen.env.clients import probe_settings

    settings = probe_settings(pair1_config, {**Q1, **SECRETS})
    spark, dbutils = FakeSpark(), FakeDbutils()
    uc, db, transports = spark_seam.probe_clients(pair1_config, settings, {}, spark=spark,
                                                  dbutils=dbutils)
    assert transports == {"unity_catalog": "spark", "metadata_db": "spark_jdbc"}
    assert db.identity.startswith("the login in secret syn-scope/syn-user")
    assert "not-a-real-credential" not in db.identity
    assert {k for _s, k in dbutils.asked} == {"syn-url", "syn-user", "syn-pass"}
    # no session: the M10 seam — outside a runtime, nothing is built
    uc, db, transports = spark_seam.probe_clients(pair1_config, settings, {}, spark=None)
    assert transports == {"unity_catalog": "unavailable", "metadata_db": "unavailable"}
    # a session without dbutils: the tables are read, the rows say why not
    uc, db, transports = spark_seam.probe_clients(pair1_config, settings, {}, spark=spark)
    assert transports["unity_catalog"] == "spark" and isinstance(db, Unavailable)
    assert "dbutils" in db.reason


# ======================================================== codegen probe (CLI)


@pytest.fixture
def pair1_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(PAIR1_OVERLAY))
    for name, value in SECRETS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("CODEGEN_ENV_PROBE", raising=False)
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    monkeypatch.setattr(spark_seam, "_registered", {})
    return state


def _probe_args(contracts: dict, out: Path, *extra: str) -> list[str]:
    return ["probe", "--config", str(REPO / "config" / "config.yaml"),
            "--pair", str(contracts["sttm"]), "--frd", str(contracts["frd"]),
            "--vdd", str(contracts["vdd"]), "--profile", "acfc_prx",
            "--iig-template", "iig_v2", "--environment", "q1", "--out", str(out), *extra]


def test_codegen_probe_writes_a_snapshot_as_the_user(pair1_env, pair1_contracts, pair1_spec,
                                                     tmp_path, capsys):
    """Nothing deployed yet: both tables absent (the tracked FAQ leaves most
    ids unassigned, so most rows are unreadable) — the snapshot names who
    asked, how, and what each statement was."""
    spark, dbutils = FakeSpark(), FakeDbutils()
    spark_seam.register(spark=spark, dbutils=dbutils)
    out = tmp_path / "probe.json"
    assert cli.main(_probe_args(pair1_contracts, out, "--to-state")) == 0
    printed = capsys.readouterr().out
    snapshot = load_snapshot(out)
    assert snapshot.identity == USER and snapshot.environment == "q1"
    assert snapshot.transports == {"unity_catalog": "spark", "metadata_db": "spark_jdbc"}
    (feed,) = snapshot.feeds
    assert feed.feed_slug == pair1_spec.feed_slug
    tables = [o for o in feed.objects if o.kind == "uc_table"]
    assert [t.layer for t in tables] == ["stage", "standard"]
    for table in tables:
        assert table.state == "absent" and table.observation.columns is None
        assert table.evidence.identity == USER and table.evidence.at == snapshot.taken_at
        assert "information_schema" in table.evidence.query
    assert _allowed(spark.statements) == []
    assert f"PROBE           {feed.feed_slug} — " in printed and "SNAPSHOT" in printed
    headline, _ = deployment_headline(feed)
    assert f"— {headline}: " in printed
    # --to-state: the App's per-feed file
    per_feed = pair1_env / "probes" / f"{feed.feed_slug}.json"
    assert load_snapshot(per_feed).feeds == [feed]
    # no credential anywhere in the snapshot
    assert "not-a-real-credential" not in out.read_text(encoding="utf-8")


def test_codegen_probe_needs_the_frd(pair1_env, pair1_contracts, tmp_path, capsys):
    lonely = tmp_path / "alone" / "sttm.contract.json"
    lonely.parent.mkdir()
    lonely.write_bytes(Path(pair1_contracts["sttm"]).read_bytes())
    assert cli.main(["probe", "--config", str(REPO / "config" / "config.yaml"),
                     "--pair", str(lonely), "--out", str(tmp_path / "p.json")]) == 1
    assert "pass the pair's FRD contract with --frd" in capsys.readouterr().out


# ============================================ snapshot == live, as M10 adjusts


@pytest.fixture(scope="module")
def expected(pair1_config, pair1_spec, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("m13_expected")
    reconciler = build_reconciler(pair1_config, env=ON, clients=(FakeUc(), FakeDb()),
                                  probed_at=PROBED_AT, expected_dir=tmp / "expected")
    emit_framework(pair1_spec, _faq(), [], pair1_config, tmp / "out",
                   conventions_profile="acfc_prx", iig_template="iig_v2", env=reconciler)
    return expected_from_json(tmp / "expected" / f"{pair1_spec.feed_slug}.env_expected.json")


def _mixed(expected):
    """Stage identical, standard drifted, one config row different, the rest
    identical — every adjustment M10 makes, at once."""
    tables, rows = expected
    standard = tables[1]
    drifted = [*standard.columns[:-1], ("LEGACY_COL", "string")]
    target = next(r for r in rows if r.table == "DATA_FACTORY_PIPELINE_SCHEDULE"
                  and not r.unkeyed_reason)

    def mutate(row, found):
        return {**found, "PIPELINE_FREQUENCY": "Hourly"} if row is target else found

    return (FakeUc({tables[0].qualified: tables[0].columns, standard.qualified: drifted}),
            _db_with(rows, mutate))


def _emit(config, spec, out: Path, reconciler):
    return emit_framework(spec, _faq(), [], config, out, conventions_profile="acfc_prx",
                          iig_template="iig_v2", env=reconciler)


def _snapshot_of(reconciler, taken_at=PROBED_AT) -> ProbeSnapshot:
    return ProbeSnapshot(taken_at=taken_at, identity=USER, environment="q1",
                         transports={"unity_catalog": "spark", "metadata_db": "spark_jdbc"},
                         feeds=list(reconciler.results.values()))


def test_a_snapshot_adjusts_the_artefacts_exactly_as_a_live_probe(
        pair1_config, pair1_spec, expected, tmp_path):
    uc, db = _mixed(expected)
    live = build_reconciler(pair1_config, env=ON, clients=(uc, db), probed_at=PROBED_AT)
    live_artefacts = _emit(pair1_config, pair1_spec, tmp_path / "live", live)
    path = write_snapshot(_snapshot_of(live), tmp_path / "probe.json")

    replay = build_reconciler(pair1_config, env=Q1, snapshot_path=path, now=PROBED_AT)
    replayed = _emit(pair1_config, pair1_spec, tmp_path / "snap", replay)
    assert _digest(tmp_path / "snap") == _digest(tmp_path / "live")
    assert replayed.flags == live_artefacts.flags            # fresh: no snapshot flag
    result = replayed.env_result
    assert {o.state for o in result.objects} >= {"identical", "different"}
    assert result.snapshot.where == str(path) and not result.snapshot.stale
    # replayed evidence names who TOOK the snapshot (the fakes declared nobody)
    assert {o.evidence.identity for o in result.objects if o.evidence} == {USER}
    # the report says where the reading came from, and how far deployment got
    section = report_section(result, True, False, "q1")
    assert "**Deployment: PARTIAL**" in section and "From the probe snapshot" in section


def test_a_snapshot_older_than_max_age_is_used_and_flagged(pair1_config, pair1_spec, expected,
                                                           tmp_path):
    uc, db = _mixed(expected)
    live = build_reconciler(pair1_config, env=ON, clients=(uc, db), probed_at=PROBED_AT)
    _emit(pair1_config, pair1_spec, tmp_path / "live", live)
    path = write_snapshot(_snapshot_of(live), tmp_path / "probe.json")
    replay = build_reconciler(pair1_config, env=Q1, snapshot_path=path,
                              now="2026-09-23T12:00:00Z")          # 24 h later + max 24 h
    fresh = build_reconciler(pair1_config, env=Q1, snapshot_path=path,
                             now="2026-09-22T11:00:00Z")
    stale = _emit(pair1_config, pair1_spec, tmp_path / "stale", replay)
    _emit(pair1_config, pair1_spec, tmp_path / "fresh", fresh)
    info = stale.env_result.snapshot
    assert info.age_hours == 48.0 and info.stale                 # 21T12 -> 23T12
    (flag,) = [f for f in stale.flags if f.startswith("env_snapshot_stale:")]
    assert "48.0 h old" in flag and "max_age_hours 24" in flag and USER in flag
    assert _digest(tmp_path / "stale") == _digest(tmp_path / "fresh")   # used as it is
    assert "flagged `env_snapshot_stale`" in report_section(stale.env_result, True, False, "q1")


def test_a_snapshot_is_replayed_against_what_the_artefacts_expect_now():
    """The DDL changed after the probe: the OBSERVED columns are compared with
    the NEW expectation, and a table the snapshot never saw is unreadable."""
    old = ExpectedTable(qualified="c.s.t", layer="stage", columns=[("A", "STRING")])
    taken = probe_feed("f", [old], [], FakeUc({"c.s.t": [("A", "string")]}),
                       Unavailable("n/a"), PROBED_AT)
    assert taken.objects[0].state == "identical"
    now = ExpectedTable(qualified="c.s.t", layer="stage",
                        columns=[("A", "STRING"), ("B", "INT")])
    other = ExpectedTable(qualified="c.s.u", layer="standard", columns=[("A", "STRING")])
    replay = probe_feed("f", [now, other], [], SnapshotUcClient(taken, PROBED_AT, USER),
                        Unavailable("n/a"), PROBED_AT)
    first, second = replay.objects
    assert first.state == "different" and [(d.column, d.kind) for d in first.diffs] == [
        ("B", "added")]
    assert second.state == "unreadable" and "not in the probe snapshot" in second.error


# ================================================ the App setting: <state>/probes


def _local_state(tmp_path: Path, config):
    from codegen.storage import open_storage

    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    return open_storage(config, tmp_path, env={
        "CODEGEN_STORAGE_STATE": f"local:{state.as_posix()}"}).state


def test_the_app_setting_reads_the_latest_snapshot_per_feed(pair1_config, pair1_spec, expected,
                                                            tmp_path):
    uc, db = _mixed(expected)
    live = build_reconciler(pair1_config, env=ON, clients=(uc, db), probed_at=PROBED_AT)
    _emit(pair1_config, pair1_spec, tmp_path / "live", live)
    store = _local_state(tmp_path, pair1_config)
    (uri,) = write_to_state(_snapshot_of(live), store)
    assert uri.endswith(f"probes/{pair1_spec.feed_slug}.json")

    # the setting is OFF by default: a state store alone changes nothing
    assert build_reconciler(pair1_config, env=Q1, state_store=store) is None
    app = build_reconciler(pair1_config, env={**Q1, "CODEGEN_ENV_PROBE_SNAPSHOTS": "1"},
                           state_store=store, now=PROBED_AT)
    from_state = _emit(pair1_config, pair1_spec, tmp_path / "app", app)
    assert _digest(tmp_path / "app") == _digest(tmp_path / "live")
    assert from_state.env_result.snapshot.where == uri


def test_no_snapshot_for_the_feed_is_missing_and_changes_nothing(pair1_config, pair1_spec,
                                                                 tmp_path):
    store = _local_state(tmp_path, pair1_config)
    disabled = _emit(pair1_config, pair1_spec, tmp_path / "off", None)
    app = build_reconciler(pair1_config, env={**Q1, "CODEGEN_ENV_PROBE_SNAPSHOTS": "1"},
                           state_store=store, now=PROBED_AT)
    missing = _emit(pair1_config, pair1_spec, tmp_path / "missing", app)
    assert _digest(tmp_path / "missing") == _digest(tmp_path / "off")
    assert missing.env_result.snapshot.missing
    extra = [f for f in missing.flags if f not in disabled.flags]
    assert len(extra) == 1 and extra[0].startswith(
        f"env_snapshot_missing:{pair1_spec.feed_slug} — no probe snapshot at ")
    assert deployment_headline(missing.env_result)[0] == "UNKNOWN"


def test_generate_accepts_a_snapshot_and_refuses_what_is_not_one(tmp_path):
    bogus = tmp_path / "results.json"
    bogus.write_text(json.dumps([{"feed_slug": "x", "probed_at": PROBED_AT}]), encoding="utf-8")
    with pytest.raises(ValueError, match="not a probe snapshot"):
        load_snapshot(bogus)


def test_generate_probe_snapshot_flag_reaches_the_artefacts(pair1_env, pair1_contracts,
                                                            pair1_spec, tmp_path, monkeypatch):
    """The CLI flag end to end: `codegen probe` then `generate --probe-snapshot`
    (the notebook's two cells) — the report carries the headline."""
    spark_seam.register(spark=FakeSpark(), dbutils=FakeDbutils())
    snap = tmp_path / "probe.json"
    assert cli.main(_probe_args(pair1_contracts, snap)) == 0
    out = tmp_path / "out"
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{out.as_posix()}")
    out.mkdir()
    cli.main(["generate", "--config", str(REPO / "config" / "config.yaml"),
              "--frd-contract", str(pair1_contracts["frd"]),
              "--sttm-contract", str(pair1_contracts["sttm"]),
              "--vdd-contract", str(pair1_contracts["vdd"]), "--profile", "acfc_prx",
              "--iig-template", "iig_v2", "--output-mode", "framework", "--dry-run",
              "--skip-tests", "--probe-snapshot", str(snap)])
    report = (out / "reports" / f"{pair1_spec.feed_slug}.md").read_text(encoding="utf-8")
    # absent tables + rows the tracked FAQ leaves unkeyed: nothing proves more
    headline, _ = deployment_headline(load_snapshot(snap).feeds[0])
    assert headline == "UNKNOWN"
    assert "## Environment" in report and "**Deployment: UNKNOWN**" in report
    assert f"From the probe snapshot `{snap}`" in report


# ================================================================ headline


def _result(*states: str) -> EnvProbeResult:
    return EnvProbeResult(feed_slug="f", probed_at=PROBED_AT, objects=[
        ProbedObject(kind="uc_table", name=f"c.s.t{i}", state=s,
                     error="denied" if s == "unreadable" else None)
        for i, s in enumerate(states)])


@pytest.mark.parametrize(("states", "headline"), [
    (("identical", "identical"), "COMPLETE"),
    (("absent", "absent"), "NOT STARTED"),
    (("identical", "absent"), "PARTIAL"),
    (("different",), "PARTIAL"),
    (("identical", "absent", "unreadable"), "PARTIAL"),    # proven by the readable ones
    (("identical", "unreadable"), "UNKNOWN"),              # could be COMPLETE or PARTIAL
    (("absent", "unreadable"), "UNKNOWN"),                 # could be NOT STARTED or PARTIAL
    (("unreadable",), "UNKNOWN"),
    ((), "UNKNOWN"),
])
def test_the_headline_claims_only_what_the_states_prove(states, headline):
    got, reason = deployment_headline(_result(*states))
    assert got == headline, reason


def test_no_snapshot_no_probe_no_change(pair1_config):
    """The tracked default: no reconciler at all — the baselines' path."""
    assert build_reconciler(pair1_config, env={}) is None
    assert env_flags(None) == []


def test_the_notebook_has_a_probe_cell_writing_to_state():
    text = (REPO / "acfc_run.py").read_text(encoding="utf-8")
    assert "spark_seam.register(spark=spark, dbutils=dbutils)" in text
    assert '"probe", "--pair"' in text and '"--to-state"' in text
    assert '"--probe-snapshot"' in text
