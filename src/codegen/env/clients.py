"""The probe's two READ-ONLY transports — an EDGE, like ``codegen.storage``.

Never imported by resolve / rules / reasoning / emit / gate. Both targets
exist only inside the operator's workspace:

* Unity Catalog, through a SQL warehouse — ``DESCRIBE TABLE`` rendered in
  ``codegen.databricks.describe_table_sql`` from validated identifiers.
* The SQL Server metadata DB — ONE statement shape, a keyed ``SELECT``
  rendered HERE from validated identifiers and escaped single-line literals.
  Secret NAMES come from config; values are resolved inside the workspace
  and never logged, stored or put into an error message.

**Nothing here can run from a developer machine.** ``build_clients`` builds a
client ONLY inside a Databricks runtime (an App container or a cluster —
``codegen.reasoning.transport.detect_runtime``), and then only from the
runtime's own injected credentials: a CLI profile is never consulted, so a
laptop whose ``DEFAULT`` profile points at some other workspace cannot probe
it by accident. Outside a runtime both clients are ``Unavailable`` and every
object reads ``unreadable``.

UNVERIFIED (2026-09-21): neither transport has run against a real workspace
or a real SQL Server — the suite drives fakes. The first real probe happens
inside ACFC (docs/ACFC_DEPLOY.md).
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass

from codegen.config import Config
from codegen.env.probe import ProbeUnreadable, Unavailable

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")
_TRUE = ("1", "true", "yes", "on")


@dataclass(frozen=True)
class ProbeSettings:
    """``env.probe`` with the App-env overrides applied (env wins, read at
    the point of use — the house style of CODEGEN_LAYOUT_PROVIDER)."""

    enabled: bool
    environment: str
    uc_warehouse_id: str
    timeout_seconds: float
    secret_scope: str
    jdbc_url_secret: str
    user_secret: str
    password_secret: str


def probe_settings(config: Config, env=None) -> ProbeSettings:
    env = os.environ if env is None else env
    probe = config.env.probe
    db = probe.metadata_db

    def pick(name: str, fallback: str) -> str:
        return env.get(name, "").strip() or fallback

    toggle = env.get("CODEGEN_ENV_PROBE", "").strip().lower()
    enabled = probe.enabled if not toggle else toggle in _TRUE
    environment = pick("CODEGEN_ENV_PROBE_ENVIRONMENT", probe.environment)
    if environment and environment not in config.dml.environments:
        raise ValueError(f"env.probe.environment={environment!r}: expected one of "
                         f"{config.dml.environments} (dml.environments) or blank")
    return ProbeSettings(
        enabled=enabled,
        environment=environment,
        uc_warehouse_id=pick("CODEGEN_ENV_PROBE_WAREHOUSE_ID", probe.uc_warehouse_id),
        timeout_seconds=float(probe.timeout_seconds),
        secret_scope=pick("CODEGEN_ENV_PROBE_SECRET_SCOPE", db.secret_scope),
        jdbc_url_secret=pick("CODEGEN_ENV_PROBE_JDBC_URL_SECRET", db.jdbc_url_secret),
        user_secret=pick("CODEGEN_ENV_PROBE_USER_SECRET", db.user_secret),
        password_secret=pick("CODEGEN_ENV_PROBE_PASSWORD_SECRET", db.password_secret),
    )


# ------------------------------------------------------------ the one SELECT


def _literal(value: str) -> str:
    text = str(value)
    if "\n" in text or "\r" in text:
        raise ProbeUnreadable("a natural-key value spans lines — not rendered into a query")
    return "N'" + text.replace("'", "''") + "'"


def render_select(schema: str, table: str, columns: list[str], key: dict[str, str]) -> str:
    """The ONLY statement the metadata-DB probe sends. Identifiers are
    validated, literals escaped; there is no other code path to a query."""
    for name in (schema, table, *columns, *key):
        if not _IDENTIFIER_RE.match(name):
            raise ProbeUnreadable(f"invalid identifier {name!r} — not rendered into a query")
    if not key:
        raise ProbeUnreadable("no natural key — a probe never reads a whole table")
    selected = ", ".join(f"[{c}]" for c in dict.fromkeys(columns))
    where = " AND ".join(f"[{k}] = {_literal(v)}" for k, v in key.items())
    # TOP 2: one row is the answer, a second proves the key is not unique.
    return f"SELECT TOP 2 {selected} FROM [{schema}].[{table}] WHERE {where}"


# ------------------------------------------------------------- Unity Catalog


class WarehouseUcClient:
    transport = "warehouse"

    def __init__(self, workspace_client, warehouse_id: str, timeout_seconds: float,
                 identity: str | None = None) -> None:
        self._client = workspace_client
        self._warehouse_id = warehouse_id
        self._timeout = timeout_seconds
        self.identity = identity

    def describe(self, qualified: str):
        from codegen.databricks import (
            DatabricksConfigError,
            DatabricksTransportError,
            TableNotFound,
            describe_table_sql,
        )

        statement = f"DESCRIBE TABLE {qualified}"
        try:
            columns, statement = describe_table_sql(
                None, qualified, self._warehouse_id, self._timeout, client=self._client)
        except TableNotFound:
            return None, statement
        except (DatabricksConfigError, DatabricksTransportError) as exc:
            raise ProbeUnreadable(str(exc).splitlines()[0][:240], statement) from exc
        return [(c["name"], c["type"]) for c in columns], statement


# ----------------------------------------------------------- the metadata DB


def parse_jdbc_url(url: str) -> dict[str, str]:
    """``jdbc:sqlserver://host[:port];databaseName=x;…`` -> host/port/database."""
    match = re.match(r"^jdbc:sqlserver://([^;:/\\]+)(?:\\[^;:]+)?(?::(\d+))?(?:;(.*))?$",
                     url.strip(), flags=re.IGNORECASE)
    if not match:
        raise ProbeUnreadable("the JDBC URL secret is not a jdbc:sqlserver:// URL")
    props = dict(p.split("=", 1) for p in (match.group(3) or "").split(";") if "=" in p)
    lowered = {k.strip().lower(): v.strip() for k, v in props.items()}
    return {"host": match.group(1), "port": match.group(2) or "1433",
            "database": lowered.get("databasename") or lowered.get("database") or ""}


class PythonDriverMetadataDbClient:
    """A Databricks App container has no JVM: the probe needs a Python SQL
    Server driver (``pymssql``, the optional ``[envprobe]`` extra)."""

    transport = "python_driver"
    identity: str | None = None

    def __init__(self, schema: str, url: str, user: str, credential: str,
                 timeout_seconds: float) -> None:
        self._schema = schema
        self._target = parse_jdbc_url(url)
        self._user, self._credential = user, credential
        self._timeout = timeout_seconds

    def select_rows(self, table: str, columns: list[str], key: dict[str, str]):
        query = render_select(self._schema, table, columns, key)
        try:
            import pymssql
        except ImportError as exc:
            raise ProbeUnreadable(
                "no SQL Server driver in this runtime — install the optional extra "
                '(pip install -e ".[envprobe]") or probe from the notebook', query) from exc
        try:
            connection = pymssql.connect(
                server=self._target["host"], port=self._target["port"],
                user=self._user, password=self._credential,
                database=self._target["database"], login_timeout=int(self._timeout),
                timeout=int(self._timeout), as_dict=True)
        except Exception as exc:  # noqa: BLE001 — the driver's message, no credential in it
            raise ProbeUnreadable(f"connection failed: {type(exc).__name__}", query) from exc
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            return list(cursor.fetchall()), query
        except Exception as exc:  # noqa: BLE001
            raise ProbeUnreadable(
                f"{type(exc).__name__}: {(str(exc).splitlines() or [''])[0][:200]}",
                query) from exc
        finally:
            connection.close()


class SparkJdbcMetadataDbClient:
    """Notebook path: a SparkSession reads the one SELECT over JDBC (works on
    classic and serverless compute; the JVM gateway does not exist on the
    latter). Built by ``codegen.env.notebook`` with the notebook's own
    ``spark`` and secrets — never by the CLI, which has neither."""

    transport = "spark_jdbc"
    identity: str | None = None

    def __init__(self, spark, schema: str, url: str, user: str, credential: str,
                 timeout_seconds: float) -> None:
        self._spark, self._schema = spark, schema
        self._url, self._user, self._credential = url, user, credential
        self._timeout = timeout_seconds

    def select_rows(self, table: str, columns: list[str], key: dict[str, str]):
        query = render_select(self._schema, table, columns, key)
        try:
            frame = (self._spark.read.format("jdbc")
                     .option("url", self._url).option("user", self._user)
                     .option("password", self._credential).option("query", query)
                     .option("queryTimeout", str(int(self._timeout))).load())
            return [row.asDict() for row in frame.collect()], query
        except Exception as exc:  # noqa: BLE001
            raise ProbeUnreadable(
                f"{type(exc).__name__}: {(str(exc).splitlines() or [''])[0][:200]}",
                query) from exc


# -------------------------------------------------------------------- builder


def _db_names_missing(settings: ProbeSettings) -> list[str]:
    return [name for name, value in (
        ("secret_scope", settings.secret_scope), ("jdbc_url_secret", settings.jdbc_url_secret),
        ("user_secret", settings.user_secret), ("password_secret", settings.password_secret))
        if not value]


def build_clients(config: Config, settings: ProbeSettings, env=None):
    """(uc, db) — real clients inside a Databricks runtime, ``Unavailable``
    everywhere else. NEVER resolves a CLI profile."""
    from codegen.reasoning.transport import detect_runtime

    env = os.environ if env is None else env
    runtime, _marker = detect_runtime(env)
    if runtime == "local":
        reason = ("not inside a Databricks workspace runtime — the probe's targets exist only "
                  "there, and no local credential is ever resolved")
        return Unavailable(reason), Unavailable(reason)
    try:
        from databricks.sdk import WorkspaceClient

        workspace = WorkspaceClient()  # the runtime's injected credentials ONLY — no profile=
    except Exception as exc:  # noqa: BLE001
        reason = (f"the workspace client could not be built from the runtime's credentials: "
                  f"{type(exc).__name__}: {(str(exc).splitlines() or [''])[0][:160]}")
        return Unavailable(reason), Unavailable(reason)

    try:  # M13: who the warehouse is asked as (the runtime's identity), best-effort
        me = workspace.current_user.me()
        identity = str(getattr(me, "user_name", None) or getattr(me, "display_name", None)
                       or "unknown")
    except Exception:  # noqa: BLE001
        identity = "unknown (the runtime identity could not be read)"
    uc = (WarehouseUcClient(workspace, settings.uc_warehouse_id, settings.timeout_seconds,
                            identity=identity)
          if settings.uc_warehouse_id else
          Unavailable("env.probe.uc_warehouse_id is not set (CODEGEN_ENV_PROBE_WAREHOUSE_ID) — "
                      "the App's service principal needs CAN USE on a SQL warehouse"))

    if not settings.environment:
        db = Unavailable("env.probe.environment is not set — which of dml.environments this "
                         "metadata DB is; config rows are not probed")
    elif _db_names_missing(settings):
        db = Unavailable("env.probe.metadata_db is not configured (secret NAMES missing: "
                         + ", ".join(_db_names_missing(settings)) + ")")
    else:
        try:
            def secret(key: str) -> str:
                raw = workspace.secrets.get_secret(settings.secret_scope, key).value or ""
                return base64.b64decode(raw).decode("utf-8")

            db = PythonDriverMetadataDbClient(
                config.dml.schema, secret(settings.jdbc_url_secret),
                secret(settings.user_secret), secret(settings.password_secret),
                settings.timeout_seconds)
            db.identity = f"the login in secret {settings.secret_scope}/{settings.user_secret}"
        except ProbeUnreadable as exc:
            db = Unavailable(str(exc))
        except Exception as exc:  # noqa: BLE001 — a secret's NAME may appear, never its value
            db = Unavailable(f"the metadata-DB secrets could not be read from scope "
                             f"{settings.secret_scope!r}: {type(exc).__name__}")
    return uc, db
