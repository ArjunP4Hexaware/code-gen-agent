"""Probe SNAPSHOTS (M13): probe as the user once, consume the result anywhere.

``codegen probe`` runs where the user's identity can read (a notebook / Genie
session: the ``spark`` seam) and writes a :class:`~codegen.env.model.
ProbeSnapshot`. ``generate --probe-snapshot <file>`` and the App
(``env.probe.snapshots``: ``<state>/probes/<feed_slug>.json``) consume it.

A snapshot is never applied by NAME alone. Every probed object carries its
raw :class:`~codegen.env.model.Observation` — the columns found, the rows the
keyed SELECT returned — and consuming a snapshot REPLAYS those observations
through the M10 classifier against what the artefacts expect NOW
(:class:`SnapshotUcClient` / :class:`SnapshotDbClient` answer like the real
clients). So a table whose expected columns changed since the probe is
compared again; an object the snapshot never saw reads ``unreadable`` ("not
in the snapshot"); the artefacts then adjust exactly as M10 does for the four
states. A snapshot older than ``env.probe.max_age_hours`` is still used, and
flagged ``env_snapshot_stale``.

Pure file / model work: no transport, no network. The state role is reached
through a ``RoleStore`` the caller hands in.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from codegen.env.model import (
    SNAPSHOT_FORMAT,
    EnvProbeResult,
    ProbeSnapshot,
    SnapshotInfo,
)
from codegen.env.probe import ProbeUnreadable

PROBES_DIR = "probes"


def feed_rel(feed_slug: str) -> str:
    """Where the App looks for a feed's latest snapshot, under the state role."""
    return f"{PROBES_DIR}/{feed_slug}.json"


def snapshot_json(snapshot: ProbeSnapshot) -> str:
    return snapshot.model_dump_json(indent=2) + "\n"


def load_snapshot(path: Path) -> ProbeSnapshot:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("format") != SNAPSHOT_FORMAT:
        raise ValueError(f"{path}: not a probe snapshot (expected format {SNAPSHOT_FORMAT!r}; "
                         "an M10 result list goes to --env-probe-result)")
    return ProbeSnapshot.model_validate(raw)


def write_snapshot(snapshot: ProbeSnapshot, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot_json(snapshot), encoding="utf-8", newline="\n")
    return path


def per_feed(snapshot: ProbeSnapshot) -> dict[str, ProbeSnapshot]:
    """One single-feed snapshot per feed — the App's per-feed files."""
    return {f.feed_slug: snapshot.model_copy(update={"feeds": [f]}) for f in snapshot.feeds}


def write_to_state(snapshot: ProbeSnapshot, state_store) -> list[str]:
    """``<state>/probes/<feed_slug>.json`` for every feed (the LATEST replaces
    the previous one). Returns the state-role URIs written."""
    written = []
    for slug, single in per_feed(snapshot).items():
        rel = feed_rel(slug)
        state_store.write_bytes(rel, snapshot_json(single).encode("utf-8"))
        written.append(state_store.uri(rel))
    return written


# ------------------------------------------------------------------ age


def _parse(at: str) -> datetime | None:
    try:
        parsed = datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc)


def snapshot_info(snapshot: ProbeSnapshot, where: str, now: str,
                  max_age_hours: float) -> SnapshotInfo:
    taken, current = _parse(snapshot.taken_at), _parse(now)
    age = None if taken is None or current is None else (
        round((current - taken).total_seconds() / 3600.0, 2))
    return SnapshotInfo(taken_at=snapshot.taken_at, identity=snapshot.identity, where=where,
                        age_hours=age, max_age_hours=max_age_hours,
                        # An age that cannot be told is not a fresh one.
                        stale=age is None or age > max_age_hours)


def missing_info(where: str, max_age_hours: float) -> SnapshotInfo:
    return SnapshotInfo(taken_at="", identity="", where=where,
                        max_age_hours=max_age_hours, missing=True)


# --------------------------------------------------------- replay clients


class _Replay:
    def __init__(self, result: EnvProbeResult | None, taken_at: str) -> None:
        self._objects = result.objects if result is not None else []
        self._taken_at = taken_at

    def _not_in(self, what: str) -> ProbeUnreadable:
        return ProbeUnreadable(f"{what} is not in the probe snapshot taken {self._taken_at} "
                               "(probed for other expectations) — probe again")


class SnapshotUcClient(_Replay):
    """Answers ``describe`` from a snapshot's observations, as the real
    client did when the snapshot was taken."""

    transport = "snapshot"

    def __init__(self, result: EnvProbeResult | None, taken_at: str, identity: str) -> None:
        super().__init__(result, taken_at)
        self.identity = identity

    def describe(self, qualified: str):
        wanted = qualified.lower()
        obj = next((o for o in self._objects
                    if o.kind == "uc_table" and o.name.lower() == wanted), None)
        if obj is None:
            raise self._not_in(qualified)
        query = obj.evidence.query if obj.evidence is not None else ""
        if obj.state == "unreadable":
            raise ProbeUnreadable(obj.error or "unreadable when the snapshot was taken", query)
        if obj.observation is None:
            raise ProbeUnreadable(f"the snapshot holds no observation for {qualified} "
                                  "(a pre-M13 result) — probe again", query)
        columns = obj.observation.columns
        return (None if columns is None else [tuple(c) for c in columns]), query


class SnapshotDbClient(_Replay):
    """Answers ``select_rows`` from a snapshot's observations, by table and
    natural key — the rows the keyed SELECT returned then."""

    transport = "snapshot"

    def __init__(self, result: EnvProbeResult | None, taken_at: str, identity: str) -> None:
        super().__init__(result, taken_at)
        self.identity = identity

    def select_rows(self, table: str, columns: list[str], key: dict[str, str]):
        obj = next((o for o in self._objects
                    if o.kind == "config_row" and o.table == table
                    and o.natural_key == dict(key) and o.natural_key), None)
        if obj is None:
            label = ", ".join(f"{k}={v}" for k, v in key.items())
            raise self._not_in(f"{table}[{label}]")
        query = obj.evidence.query if obj.evidence is not None else ""
        if obj.observation is None or obj.observation.rows is None:
            raise ProbeUnreadable(obj.error or "unreadable when the snapshot was taken", query)
        return [dict(row) for row in obj.observation.rows], query


__all__ = [
    "PROBES_DIR",
    "SnapshotDbClient",
    "SnapshotUcClient",
    "feed_rel",
    "load_snapshot",
    "missing_info",
    "per_feed",
    "snapshot_info",
    "snapshot_json",
    "write_snapshot",
    "write_to_state",
]
