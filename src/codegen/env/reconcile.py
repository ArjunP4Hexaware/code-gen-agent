"""The EDGE of M10: builds the reconciler the emitters are handed, persists
what it found, and words the report. Imported by ``cli`` / ``ui.backend`` —
never by resolve / rules / reasoning / emit / gate (the emitters receive the
reconciler as a plain object and import only ``codegen.env.model``).
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from codegen.config import Config
from codegen.env.adjust import ddl_action, dml_action
from codegen.env.clients import ProbeSettings, build_clients, probe_settings
from codegen.env.expect import expected_rows, expected_to_json
from codegen.env.model import EnvProbeResult, ExpectedTable
from codegen.env.probe import probe_feed


class EnvReconciler:
    """What ``emit_framework(env=…)`` receives. One per run; ``results`` keeps
    every feed's observation for the state role and the report."""

    def __init__(self, config: Config, settings: ProbeSettings, uc, db, probed_at: str,
                 preset: dict[str, EnvProbeResult] | None = None,
                 expected_dir: Path | None = None) -> None:
        self._config = config
        self._settings = settings
        self._uc, self._db = uc, db
        self._probed_at = probed_at
        self._preset = preset or {}
        self._expected_dir = expected_dir
        self.results: dict[str, EnvProbeResult] = {}

    @property
    def environment(self) -> str:
        return self._settings.environment

    def probe(self, feed_slug: str, tables: list[ExpectedTable], payload: dict | None,
              faq) -> EnvProbeResult | None:
        rows = (expected_rows(payload, faq, self._config, self._settings.environment)
                if payload is not None else [])
        if self._expected_dir is not None:
            self._expected_dir.mkdir(parents=True, exist_ok=True)
            (self._expected_dir / f"{feed_slug}.env_expected.json").write_text(
                expected_to_json(tables, rows), encoding="utf-8", newline="\n")
        if feed_slug in self._preset:
            result = self._preset[feed_slug]
        else:
            result = probe_feed(feed_slug, tables, rows, self._uc, self._db, self._probed_at,
                                self._settings.timeout_seconds)
        self.results[feed_slug] = result
        return result


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_results(path: Path) -> dict[str, EnvProbeResult]:
    """A probe result file written elsewhere (the notebook fallback probes
    in-process, where spark and secrets exist) -> {feed_slug: result}."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    results = [EnvProbeResult.model_validate(item) for item in items]
    return {r.feed_slug: r for r in results}


def build_reconciler(config: Config, env=None, *, preset_path: Path | None = None,
                     expected_dir: Path | None = None, clients=None,
                     probed_at: str | None = None) -> EnvReconciler | None:
    """None when the probe is disabled (``env.probe.enabled`` / CODEGEN_ENV_PROBE)
    — the emitters then behave exactly as before M10. ``clients`` is the test
    seam: a (uc, db) pair of fakes; otherwise ``build_clients`` decides, and
    outside a Databricks runtime that is two ``Unavailable``s."""
    env = os.environ if env is None else env
    settings = probe_settings(config, env)
    if not settings.enabled and preset_path is None and expected_dir is None:
        return None
    uc, db = clients if clients is not None else build_clients(config, settings, env)
    return EnvReconciler(config, settings, uc, db, probed_at or utc_now(),
                         preset=load_results(preset_path) if preset_path else None,
                         expected_dir=expected_dir)


def persist_result(result: EnvProbeResult, store) -> Path | None:
    """``<state>/env_probe/<feed_slug>.json`` — the observation WITH its
    provenance (every query, the timestamp). ``store`` is the state RoleStore.
    A state role that cannot be written never stops a run."""
    rel = f"env_probe/{result.feed_slug}.json"
    with contextlib.suppress(Exception):
        path = store.local_path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8",
                        newline="\n")
        store.push(rel)
        return path
    return None


# ---------------------------------------------------------------------- report


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def environment_rows(result: EnvProbeResult, reconcile_ddl: bool, emit_updates: bool,
                     dml_emitted: bool = True) -> list[dict]:
    """object | state | evidence | what the artefact does about it — the one
    shape the markdown report and the UI both show."""
    dml_adjusted = dml_emitted and any(
        o.kind == "config_row" and o.state in ("identical", "different")
        for o in result.objects)
    rows = []
    for obj in result.objects:
        if obj.state == "unreadable":
            evidence = obj.error or "no reason given"
        else:
            evidence = f"{obj.evidence.query} @ {obj.evidence.at}" if obj.evidence else ""
        detail = "; ".join(
            f"{d.column}: {d.kind}" + (f" (this artefact {d.expected} -> environment {d.actual})"
                                       if d.kind in ("type", "value") else "")
            for d in obj.diffs)
        status = "; ".join(f"{d.column}: this script {d.expected} -> environment {d.actual}"
                           for d in obj.status_diffs)
        if obj.kind == "uc_table":
            action = ddl_action(obj, reconcile_ddl)
        elif not dml_emitted:
            action = "no DML script is emitted under this conventions profile"
        else:
            action = dml_action(obj, emit_updates, dml_adjusted)
        if status:
            action += f" — status columns differ and are NOT touched ({status})"
        rows.append({"object": obj.name, "kind": obj.kind, "state": obj.state,
                     "evidence": evidence, "differences": detail, "action": action})
    return rows


def report_section(result: EnvProbeResult, reconcile_ddl: bool, emit_updates: bool,
                   environment: str, dml_emitted: bool = True) -> str:
    counts = result.counts()
    lines = [
        "",
        "## Environment",
        "",
        f"Read-only probe at {result.probed_at}"
        + (f", metadata DB environment `{environment}`" if environment else "")
        + ": " + ", ".join(f"{n} {state}" for state, n in counts.items() if n) + ". "
        "`unreadable` is a flag, never a stop — those objects are emitted as without a probe.",
        "",
        "| Object | State | Evidence | What the artefact does about it |",
        "| --- | --- | --- | --- |",
    ]
    for row in environment_rows(result, reconcile_ddl, emit_updates, dml_emitted):
        evidence = row["evidence"] + (f" — {row['differences']}" if row["differences"] else "")
        lines.append(f"| `{_cell(row['object'])}` | {row['state']} | {_cell(evidence)} | "
                     f"{_cell(row['action'])} |")
    return "\n".join(lines) + "\n"
