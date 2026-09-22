"""The notebook fallback's probe (M10): runs IN the notebook process, where
``spark`` and ``dbutils.secrets`` exist and the CLI subprocesses have neither.

Flow (acfc_run.py): ``generate --env-expected-out <dir>`` writes what the
artefacts expect -> ``probe_from_notebook`` asks the environment (Unity
Catalog through the notebook's SparkSession, the metadata DB over JDBC) and
writes the result file -> ``generate --env-probe-result <file>`` emits the
adjusted artefacts. Read-only throughout; unreadable is never a stop.

UNVERIFIED (2026-09-21): has not run inside a real workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

from codegen.config import Config
from codegen.env.clients import SparkJdbcMetadataDbClient, probe_settings
from codegen.env.expect import expected_from_json
from codegen.env.model import EnvProbeResult
from codegen.env.probe import ProbeUnreadable, Unavailable, probe_feed
from codegen.env.reconcile import utc_now


class SparkUcClient:
    """DESCRIBE TABLE through the notebook's own SparkSession — no warehouse
    needed, the notebook's compute answers."""

    def __init__(self, spark) -> None:
        self._spark = spark

    def describe(self, qualified: str):
        parts = qualified.split(".")
        if len(parts) != 3 or not all(p.replace("_", "").isalnum() for p in parts):
            raise ProbeUnreadable(f"invalid table name {qualified!r}")
        statement = "DESCRIBE TABLE " + ".".join(f"`{p}`" for p in parts)
        try:
            rows = self._spark.sql(statement).collect()
        except Exception as exc:  # noqa: BLE001
            text = str(exc)
            if "TABLE_OR_VIEW_NOT_FOUND" in text or "cannot be found" in text.lower():
                return None, statement
            raise ProbeUnreadable(f"{type(exc).__name__}: {text.splitlines()[0][:200]}",
                                  statement) from exc
        columns: list[tuple[str, str]] = []
        for row in rows:
            name = (row[0] or "").strip()
            if not name or name.startswith("#"):
                break
            columns.append((name, (row[1] or "").strip()))
        return columns, statement


def probe_from_notebook(config: Config, expected_dir: Path, out_path: Path, spark, dbutils,
                        env=None) -> list[EnvProbeResult]:
    settings = probe_settings(config, env)
    uc = SparkUcClient(spark)
    db = Unavailable("env.probe.environment is not set — which of dml.environments this "
                     "metadata DB is; config rows are not probed")
    if settings.environment:
        missing = [n for n, v in (("secret_scope", settings.secret_scope),
                                  ("jdbc_url_secret", settings.jdbc_url_secret),
                                  ("user_secret", settings.user_secret),
                                  ("password_secret", settings.password_secret)) if not v]
        if missing:
            db = Unavailable("env.probe.metadata_db is not configured (secret NAMES missing: "
                             + ", ".join(missing) + ")")
        else:
            try:
                db = SparkJdbcMetadataDbClient(
                    spark, config.dml.schema,
                    dbutils.secrets.get(settings.secret_scope, settings.jdbc_url_secret),
                    dbutils.secrets.get(settings.secret_scope, settings.user_secret),
                    dbutils.secrets.get(settings.secret_scope, settings.password_secret),
                    settings.timeout_seconds)
            except Exception as exc:  # noqa: BLE001 — a secret NAME may appear, never a value
                db = Unavailable(f"the metadata-DB secrets could not be read from scope "
                                 f"{settings.secret_scope!r}: {type(exc).__name__}")
    probed_at = utc_now()
    results: list[EnvProbeResult] = []
    for path in sorted(Path(expected_dir).glob("*.env_expected.json")):
        feed_slug = path.name[: -len(".env_expected.json")]
        tables, rows = expected_from_json(path)
        results.append(probe_feed(feed_slug, tables, rows, uc, db, probed_at,
                                  settings.timeout_seconds))
    out_path.write_text(json.dumps([r.model_dump() for r in results], indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    return results
