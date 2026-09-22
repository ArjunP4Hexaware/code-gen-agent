"""The EDGE of M10: builds the reconciler the emitters are handed, persists
what it found, and words the report. Imported by ``cli`` / ``ui.backend`` —
never by resolve / rules / reasoning / emit / gate (the emitters receive the
reconciler as a plain object and import only ``codegen.env.model``).
"""

from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from codegen.config import Config
from codegen.env.adjust import ddl_action, dml_action
from codegen.env.clients import ProbeSettings, build_clients, probe_settings
from codegen.env.expect import expected_rows, expected_to_json
from codegen.env.model import (
    EnvProbeResult,
    ExpectedTable,
    ProbeSnapshot,
    deployment_headline,
)
from codegen.env.probe import Unavailable, probe_feed

# feed_slug -> (the snapshot, or None when there is none; where it was looked for)
SnapshotSource = Callable[[str], tuple[ProbeSnapshot | None, str]]
_TRUE = ("1", "true", "yes", "on")


class EnvReconciler:
    """What ``emit_framework(env=…)`` receives. One per run; ``results`` keeps
    every feed's observation for the state role and the report."""

    def __init__(self, config: Config, settings: ProbeSettings, uc, db, probed_at: str,
                 preset: dict[str, EnvProbeResult] | None = None,
                 expected_dir: Path | None = None, *,
                 snapshot_source: SnapshotSource | None = None,
                 live: bool = True, now: str | None = None) -> None:
        self._config = config
        self._settings = settings
        self._uc, self._db = uc, db
        self._probed_at = probed_at
        self._preset = preset or {}
        self._expected_dir = expected_dir
        # M13: snapshots first; a feed without one falls back to a live probe
        # only when the probe is on (``live``), else it is `missing`.
        self._snapshot_source = snapshot_source
        self._live = live
        self._now = now
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
        elif self._snapshot_source is not None:
            result = self._from_snapshot(feed_slug, tables, rows)
        else:
            result = probe_feed(feed_slug, tables, rows, self._uc, self._db, self._probed_at,
                                self._settings.timeout_seconds)
        self.results[feed_slug] = result
        return result

    def _from_snapshot(self, feed_slug: str, tables, rows) -> EnvProbeResult:
        from codegen.env.snapshot import (
            SnapshotDbClient,
            SnapshotUcClient,
            missing_info,
            snapshot_info,
        )

        max_age = float(self._config.env.probe.max_age_hours)
        snapshot, where = self._snapshot_source(feed_slug)
        feed = snapshot.feed(feed_slug) if snapshot is not None else None
        if feed is None:
            if self._live:
                return probe_feed(feed_slug, tables, rows, self._uc, self._db,
                                  self._probed_at, self._settings.timeout_seconds)
            return EnvProbeResult(feed_slug=feed_slug, probed_at=self._probed_at,
                                  snapshot=missing_info(where, max_age))

        def identity(source: str) -> str:
            return next((o.evidence.identity for o in feed.objects
                         if o.evidence is not None and o.evidence.source == source
                         and o.evidence.identity), snapshot.identity)

        # The observations, replayed through the classifier against what the
        # artefacts expect NOW — never a state trusted by name.
        uc = SnapshotUcClient(feed, snapshot.taken_at, identity("unity_catalog"))
        db = SnapshotDbClient(feed, snapshot.taken_at, identity("metadata_db"))
        result = probe_feed(feed_slug, tables, rows, uc, db, snapshot.taken_at,
                            self._settings.timeout_seconds)
        return result.model_copy(update={"snapshot": snapshot_info(
            snapshot, where, self._now or utc_now(), max_age)})


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_results(path: Path) -> dict[str, EnvProbeResult]:
    """A probe result file written elsewhere (the notebook fallback probes
    in-process, where spark and secrets exist) -> {feed_slug: result}."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    results = [EnvProbeResult.model_validate(item) for item in items]
    return {r.feed_slug: r for r in results}


def snapshots_enabled(config: Config, env=None) -> bool:
    """``env.probe.snapshots``, the App env CODEGEN_ENV_PROBE_SNAPSHOTS winning."""
    env = os.environ if env is None else env
    toggle = env.get("CODEGEN_ENV_PROBE_SNAPSHOTS", "").strip().lower()
    return config.env.probe.snapshots if not toggle else toggle in _TRUE


def file_snapshot_source(path: Path) -> SnapshotSource:
    """``generate --probe-snapshot <file>``: read once, loudly (a file that is
    not a snapshot is an error, not a silent no-op)."""
    from codegen.env.snapshot import load_snapshot

    snapshot = load_snapshot(path)
    return lambda _slug: (snapshot, str(path))


def state_snapshot_source(state_store) -> SnapshotSource:
    """The App's setting: the LATEST snapshot for a feed, from
    ``<state>/probes/<feed_slug>.json`` (fetched per feed — a remote state
    role is read through its RoleStore). None found = `missing`."""
    from codegen.env.snapshot import feed_rel, load_snapshot

    def source(slug: str):
        rel = feed_rel(slug)
        where = state_store.uri(rel)
        try:
            local = state_store.fetch(rel)
        except Exception:  # noqa: BLE001 — not there (or not readable): missing, said so
            return None, where
        try:
            return load_snapshot(local), where
        except (OSError, ValueError) as exc:
            return None, f"{where} (could not be read: {str(exc).splitlines()[0][:160]})"

    return source


def build_reconciler(config: Config, env=None, *, preset_path: Path | None = None,
                     expected_dir: Path | None = None, clients=None,
                     probed_at: str | None = None, snapshot_path: Path | None = None,
                     state_store=None, now: str | None = None,
                     force: bool = False) -> EnvReconciler | None:
    """None when the probe is disabled (``env.probe.enabled`` / CODEGEN_ENV_PROBE)
    and no snapshot is to be read — the emitters then behave exactly as before
    M10. ``clients`` is the test seam: a (uc, db) pair of fakes; otherwise
    ``build_clients`` decides, and outside a Databricks runtime that is two
    ``Unavailable``s. M13: ``snapshot_path`` (``generate --probe-snapshot``)
    or, with ``env.probe.snapshots`` on, ``state_store`` supplies snapshots;
    ``force`` builds one regardless (``codegen probe``)."""
    env = os.environ if env is None else env
    settings = probe_settings(config, env)
    source: SnapshotSource | None = None
    if snapshot_path is not None:
        source = file_snapshot_source(Path(snapshot_path))
    elif state_store is not None and snapshots_enabled(config, env):
        source = state_snapshot_source(state_store)
    if (not settings.enabled and not force and preset_path is None and expected_dir is None
            and source is None):
        return None
    live = settings.enabled or force
    if clients is not None:
        uc, db = clients
    elif source is not None and not live:
        off = ("the live probe is off (env.probe.enabled / CODEGEN_ENV_PROBE) — only probe "
               "snapshots are read")
        uc, db = Unavailable(off), Unavailable(off)
    else:
        uc, db = build_clients(config, settings, env)
    return EnvReconciler(config, settings, uc, db, probed_at or utc_now(),
                         preset=load_results(preset_path) if preset_path else None,
                         expected_dir=expected_dir, snapshot_source=source,
                         live=live, now=now)


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


def headline_line(result: EnvProbeResult) -> str:
    headline, reason = deployment_headline(result)
    return f"**Deployment: {headline}** — {reason}."


def snapshot_line(result: EnvProbeResult) -> str | None:
    info = result.snapshot
    if info is None:
        return None
    if info.missing:
        return (f"No probe snapshot for this feed at `{info.where}` — the artefacts are "
                "emitted as without a probe (`env_snapshot_missing`).")
    age = "age unknown" if info.age_hours is None else f"{info.age_hours:g} h old"
    stale = (f" — older than env.probe.max_age_hours ({info.max_age_hours:g}); used as it is, "
             "flagged `env_snapshot_stale`" if info.stale else "")
    return (f"From the probe snapshot `{info.where}`, taken {info.taken_at} as "
            f"`{info.identity}` ({age}){stale}. Its observations were compared with what "
            "these artefacts expect now.")


def report_section(result: EnvProbeResult, reconcile_ddl: bool, emit_updates: bool,
                   environment: str, dml_emitted: bool = True) -> str:
    counts = result.counts()
    snapshot = snapshot_line(result)
    lines = [
        "",
        "## Environment",
        "",
        headline_line(result),
        "",
        *([snapshot, ""] if snapshot else []),
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
