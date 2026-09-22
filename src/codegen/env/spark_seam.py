"""The ``spark`` seam (M13): the probe asks AS THE USER, through a SparkSession.

Inside a notebook or a Genie Code session a SparkSession exists and runs with
the USER's identity — the identity that can already read ACFC's catalogs,
while the App's service principal has no grant. So when a session exists, the
probe's Unity Catalog reads go through it; otherwise the existing warehouse
seam (``codegen.env.clients``) answers, or nothing does.

READ-ONLY, and narrow by construction. The ONLY statements this module can
send are rendered here from VALIDATED identifiers (``[A-Za-z0-9_]+`` per
part — anything else is ``unreadable`` and never sent):

* ``SELECT current_user()`` — once, to record who asked;
* ``SELECT column_name, full_data_type FROM `<catalog>`.information_schema.
  columns WHERE table_schema = '<schema>' AND table_name = '<table>'
  ORDER BY ordinal_position`` — the columns, in the catalog's own spelling;
* ``DESCRIBE TABLE EXTENDED `<catalog>`.`<schema>`.`<table>``` — only when
  information_schema returned nothing: information_schema lists only what the
  identity can SEE, so an empty answer is "absent OR invisible", and DESCRIBE
  tells the two apart (not found = absent; any other error = unreadable).

The metadata DB is read over JDBC through the same session
(``SparkJdbcMetadataDbClient``), its URL / user / password resolved with
``dbutils.secrets`` from the secret-scope NAMES in config — values never
leave the session, and the identity recorded is the secret's NAME.

``register`` lets a notebook hand its own ``spark`` / ``dbutils`` over
explicitly (acfc_run.py does). Auto-detection is the fallback:
``SparkSession.getActiveSession()`` (pyspark present, a session running) and,
ONLY inside a Databricks runtime, ``databricks.sdk.runtime.dbutils`` — never
on a developer machine, where importing it could resolve a CLI profile.

UNVERIFIED (2026-09-22): has run only against the fakes in
``tests/test_m13_probe_snapshot.py``. Whether Unity Catalog reports a table
the user cannot see as "not found" (absent) or as a permission error
(unreadable) is not established — the evidence records the identity so a
person can judge.
"""

from __future__ import annotations

import re

from codegen.config import Config
from codegen.env.clients import ProbeSettings, SparkJdbcMetadataDbClient
from codegen.env.probe import ProbeUnreadable, Unavailable

_PART_RE = re.compile(r"^[A-Za-z0-9_]+$")
# Error texts that mean "not there" — anything else is `unreadable`.
_NOT_FOUND = ("TABLE_OR_VIEW_NOT_FOUND", "SCHEMA_NOT_FOUND", "NO_SUCH_CATALOG_EXCEPTION",
              "CATALOG_NOT_FOUND", "cannot be found", "does not exist")

_registered: dict[str, object] = {}


def register(spark=None, dbutils=None) -> None:
    """A notebook's own session and dbutils, handed over explicitly."""
    if spark is not None:
        _registered["spark"] = spark
    if dbutils is not None:
        _registered["dbutils"] = dbutils


def active_session():
    """The running SparkSession, or None (no pyspark / no session)."""
    if "spark" in _registered:
        return _registered["spark"]
    try:
        from pyspark.sql import SparkSession
    except Exception:  # noqa: BLE001 — no pyspark: no session
        return None
    try:
        return SparkSession.getActiveSession()
    except Exception:  # noqa: BLE001
        return None


def active_dbutils(env=None):
    """The notebook's dbutils: registered, else — ONLY inside a Databricks
    runtime — ``databricks.sdk.runtime.dbutils``; None everywhere else."""
    if "dbutils" in _registered:
        return _registered["dbutils"]
    from codegen.reasoning.transport import detect_runtime

    runtime, _marker = detect_runtime(env)
    if runtime == "local":
        return None
    try:
        from databricks.sdk.runtime import dbutils
    except Exception:  # noqa: BLE001
        return None
    return dbutils


# ------------------------------------------------------------ rendering


def split_qualified(qualified: str) -> tuple[str, str, str]:
    parts = qualified.split(".")
    if len(parts) != 3 or not all(_PART_RE.match(p) for p in parts):
        raise ProbeUnreadable(f"invalid table name {qualified!r} — not rendered into a "
                              "statement (catalog.schema.table, [A-Za-z0-9_] per part)")
    return parts[0], parts[1], parts[2]


def render_information_schema(catalog: str, schema: str, table: str) -> str:
    for part in (catalog, schema, table):
        if not _PART_RE.match(part):
            raise ProbeUnreadable(f"invalid identifier {part!r} — not rendered")
    return (f"SELECT column_name, full_data_type FROM `{catalog}`.information_schema.columns "
            f"WHERE table_schema = '{schema.lower()}' AND table_name = '{table.lower()}' "
            "ORDER BY ordinal_position")


def render_describe(catalog: str, schema: str, table: str) -> str:
    for part in (catalog, schema, table):
        if not _PART_RE.match(part):
            raise ProbeUnreadable(f"invalid identifier {part!r} — not rendered")
    return f"DESCRIBE TABLE EXTENDED `{catalog}`.`{schema}`.`{table}`"


CURRENT_USER = "SELECT current_user()"


def _first_line(exc: Exception) -> str:
    return f"{type(exc).__name__}: {(str(exc).splitlines() or [''])[0][:200]}"


def session_identity(spark) -> str:
    try:
        rows = spark.sql(CURRENT_USER).collect()
        value = rows[0][0] if rows else None
    except Exception:  # noqa: BLE001 — an identity we cannot read is said so
        return "unknown (current_user() could not be read)"
    return str(value) if value else "unknown"


# --------------------------------------------------------------- the client


class SparkUcClient:
    """Unity Catalog through a SparkSession, as the session's user."""

    transport = "spark"

    def __init__(self, spark, identity: str | None = None) -> None:
        self._spark = spark
        self.identity = identity if identity is not None else session_identity(spark)

    def describe(self, qualified: str):
        catalog, schema, table = split_qualified(qualified)
        info = render_information_schema(catalog, schema, table)
        sent = [info]
        try:
            rows = self._spark.sql(info).collect()
        except Exception:  # noqa: BLE001 — DESCRIBE below decides; said in the evidence
            rows = []
        if rows:
            return [(str(r[0]), str(r[1])) for r in rows], info
        # Empty: absent, or not visible to this identity — DESCRIBE decides.
        describe = render_describe(catalog, schema, table)
        sent.append(describe)
        statements = "; ".join(sent)
        try:
            described = self._spark.sql(describe).collect()
        except Exception as exc:  # noqa: BLE001
            if any(marker.lower() in str(exc).lower() for marker in _NOT_FOUND):
                return None, statements
            raise ProbeUnreadable(_first_line(exc), statements) from exc
        columns: list[tuple[str, str]] = []
        for row in described:
            name = str(row[0] or "").strip()
            if not name or name.startswith("#"):
                break                        # the extended block follows the columns
            columns.append((name, str(row[1] or "").strip()))
        return columns, statements


# ----------------------------------------------------------------- builder


def _db_names_missing(settings: ProbeSettings) -> list[str]:
    return [name for name, value in (
        ("secret_scope", settings.secret_scope), ("jdbc_url_secret", settings.jdbc_url_secret),
        ("user_secret", settings.user_secret), ("password_secret", settings.password_secret))
        if not value]


def spark_clients(config: Config, settings: ProbeSettings, spark, dbutils):
    """(uc, db) through the session. The DB needs dbutils (secrets); without
    it the rows read ``unreadable`` with the reason."""
    uc = SparkUcClient(spark)
    if not settings.environment:
        return uc, Unavailable("env.probe.environment is not set — which of dml.environments "
                               "this metadata DB is; config rows are not probed")
    missing = _db_names_missing(settings)
    if missing:
        return uc, Unavailable("env.probe.metadata_db is not configured (secret NAMES missing: "
                               + ", ".join(missing) + ")")
    if dbutils is None:
        return uc, Unavailable("no dbutils in this session — the metadata-DB secrets are read "
                               "with dbutils.secrets inside a notebook")
    try:
        db = SparkJdbcMetadataDbClient(
            spark, config.dml.schema,
            dbutils.secrets.get(settings.secret_scope, settings.jdbc_url_secret),
            dbutils.secrets.get(settings.secret_scope, settings.user_secret),
            dbutils.secrets.get(settings.secret_scope, settings.password_secret),
            settings.timeout_seconds)
    except Exception as exc:  # noqa: BLE001 — a secret NAME may appear, never a value
        return uc, Unavailable(f"the metadata-DB secrets could not be read from scope "
                               f"{settings.secret_scope!r}: {type(exc).__name__}")
    db.identity = (f"the login in secret {settings.secret_scope}/{settings.user_secret} "
                   f"(JDBC through the session of {uc.identity})")
    return uc, db


def probe_clients(config: Config, settings: ProbeSettings, env=None, *, spark=None,
                  dbutils=None):
    """(uc, db, transports). A SparkSession wins (the user's identity); else
    the M10 warehouse / Python-driver seam, which outside a Databricks runtime
    is two ``Unavailable``s."""
    from codegen.env.clients import build_clients

    spark = spark if spark is not None else active_session()
    if spark is not None:
        dbutils = dbutils if dbutils is not None else active_dbutils(env)
        uc, db = spark_clients(config, settings, spark, dbutils)
    else:
        uc, db = build_clients(config, settings, env)
    return uc, db, {"unity_catalog": _transport(uc), "metadata_db": _transport(db)}


def _transport(client) -> str:
    if isinstance(client, Unavailable):
        return "unavailable"
    return str(getattr(client, "transport", type(client).__name__))


__all__ = [
    "CURRENT_USER",
    "SparkUcClient",
    "active_dbutils",
    "active_session",
    "probe_clients",
    "register",
    "render_describe",
    "render_information_schema",
    "session_identity",
    "spark_clients",
    "split_qualified",
]
