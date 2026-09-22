"""The notebook's probe (M10; M13 routes it through the ``spark`` seam).

Runs IN the notebook process, where ``spark`` and ``dbutils.secrets`` exist
and the CLI subprocesses have neither. Since M13 the preferred path is
``codegen probe`` (called in-process from the notebook — acfc_run.py's
"probe" cell), which writes a probe SNAPSHOT that ``generate
--probe-snapshot`` and the App consume. ``probe_from_notebook`` stays for the
M10 two-pass flow (``generate --env-expected-out`` -> probe ->
``generate --env-probe-result``). Read-only throughout; unreadable is never a
stop.

UNVERIFIED (2026-09-22): has not run inside a real workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

from codegen.config import Config
from codegen.env.clients import probe_settings
from codegen.env.expect import expected_from_json
from codegen.env.model import EnvProbeResult
from codegen.env.probe import probe_feed
from codegen.env.reconcile import utc_now
from codegen.env.spark_seam import SparkUcClient, spark_clients

__all__ = ["SparkUcClient", "probe_from_notebook"]


def probe_from_notebook(config: Config, expected_dir: Path, out_path: Path, spark, dbutils,
                        env=None) -> list[EnvProbeResult]:
    settings = probe_settings(config, env)
    uc, db = spark_clients(config, settings, spark, dbutils)
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
