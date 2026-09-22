"""Environment reconciliation (M10) — the DATA the rest of the agent reads.

Pure models, no I/O: what the artefacts EXPECT to find in the target
environment (``ExpectedTable`` / ``ExpectedRow``) and what a probe FOUND
(``ProbedObject`` inside an ``EnvProbeResult``). The emitters and the report
import only this module; the transports that actually ask an environment
live in ``codegen.env.probe`` / ``codegen.env.clients`` and are an EDGE, like
``codegen.storage`` — resolve / rules / reasoning / emit / gate never import
them.

Four states, one meaning each:

``absent``      the object is not there — the artefact creates / inserts it,
                exactly as it does with the probe disabled.
``identical``   it is there and matches — the artefact does nothing about it.
``different``   it is there and differs — ``diffs`` says how, column by column.
``unreadable``  the environment could not be asked (no permission, no
                connection, no runtime, a timeout) — ``error`` says why. NEVER a
                stop: the artefact is emitted as if the probe were disabled.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

ObjectState = Literal["absent", "identical", "different", "unreadable"]
STATES: tuple[str, ...] = ("absent", "identical", "different", "unreadable")

# What a column difference is. ``added``: expected by the artefact, missing in
# the environment (additive drift — the only kind a statement is emitted for).
# ``removed``: in the environment, not in the artefact. ``type``: both have
# the column, the types differ. ``value``: a config-row cell differs.
DiffKind = Literal["added", "removed", "type", "value"]


class FieldDiff(BaseModel):
    model_config = _MODEL_CONFIG

    column: str
    kind: DiffKind
    expected: str | None = None   # what the artefact states (None for `removed`)
    actual: str | None = None     # what the environment holds (None for `added`)


class Evidence(BaseModel):
    """Provenance of one observation: the query that was sent and when."""

    model_config = _MODEL_CONFIG

    source: Literal["unity_catalog", "metadata_db"]
    query: str
    at: str  # ISO-8601, UTC — injected by the caller, never read from a clock here
    # M13: WHO asked — the notebook user (``current_user()`` of the session),
    # the runtime's identity, or the NAME of the secret holding the DB login.
    # Never a credential. None = not recorded (a pre-M13 result).
    identity: str | None = None


class ExpectedTable(BaseModel):
    """A Unity Catalog table the deployment DDL would create."""

    model_config = _MODEL_CONFIG

    qualified: str                      # catalog.schema.table as the DDL writes it
    layer: str                          # stage | standard
    columns: list[tuple[str, str]]      # (name, type) in DDL order


class ExpectedRow(BaseModel):
    """One metadata-DB config row the DML would insert.

    ``values`` holds ONLY the cells whose value is a literal known at
    generation time; a cell that is a script variable (``@PIPELINE_ID``), an
    environment expression (``CONCAT(@PATH_PREFIX, …)``) or an audit value
    (``GETDATE()``) cannot be compared from here and is listed in
    ``not_compared`` instead. ``status_columns`` (ACTIVE_FLAG …) are compared
    for the REPORT only — the agent never changes them.
    """

    model_config = _MODEL_CONFIG

    table: str                                   # SQL Server table name
    sheet: str                                   # the IIG sheet the row came from
    row_index: int                               # position within that sheet (0-based)
    natural_key: dict[str, str]                  # column -> literal value
    values: dict[str, str | None] = Field(default_factory=dict)
    not_compared: list[str] = Field(default_factory=list)
    status_columns: list[str] = Field(default_factory=list)
    unkeyed_reason: str | None = None            # why the row cannot be looked up

    @property
    def key_label(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in self.natural_key.items())

    @property
    def name(self) -> str:
        return f"{self.table}[{self.key_label}]" if self.natural_key else (
            f"{self.table}[row {self.row_index + 1}]")


class Observation(BaseModel):
    """M13: what the environment ANSWERED, raw — kept so a snapshot can be
    re-classified against the expectations of a LATER generation (a table's
    columns may have changed since the probe; a replayed snapshot is compared
    with what the artefacts expect NOW, never trusted by name alone)."""

    model_config = _MODEL_CONFIG

    # uc_table: the columns found; None = the table is not there.
    columns: list[tuple[str, str]] | None = None
    # config_row: every row the keyed SELECT returned (0, 1 or 2), as text.
    rows: list[dict[str, str | None]] | None = None


class ProbedObject(BaseModel):
    model_config = _MODEL_CONFIG

    kind: Literal["uc_table", "config_row"]
    name: str                            # qualified table | TABLE[key=value, …]
    state: ObjectState
    diffs: list[FieldDiff] = Field(default_factory=list)
    status_diffs: list[FieldDiff] = Field(default_factory=list)  # report-only
    # config_row: the columns that WERE compared (never the key, never a
    # status column) — what an "identical" assertion may assert.
    compared: list[str] = Field(default_factory=list)
    evidence: Evidence | None = None
    error: str | None = None             # set when state == unreadable
    # Addressing, so an emitter finds "its" object without parsing `name`.
    layer: str | None = None             # uc_table
    table: str | None = None             # config_row: SQL Server table
    sheet: str | None = None             # config_row: IIG sheet
    row_index: int | None = None         # config_row: position in the sheet
    natural_key: dict[str, str] = Field(default_factory=dict)
    observation: Observation | None = None   # M13: None when nothing was answered

    @property
    def additive(self) -> list[FieldDiff]:
        return [d for d in self.diffs if d.kind == "added"]

    @property
    def needs_review(self) -> list[FieldDiff]:
        return [d for d in self.diffs if d.kind != "added"]


class SnapshotInfo(BaseModel):
    """M13: the result was REPLAYED from a probe snapshot, not asked now."""

    model_config = _MODEL_CONFIG

    taken_at: str
    identity: str
    where: str                      # the file / state-role path it was read from
    age_hours: float | None = None  # None when ``taken_at`` does not parse
    max_age_hours: float
    stale: bool = False
    missing: bool = False           # no snapshot for this feed at ``where``


class EnvProbeResult(BaseModel):
    """Everything one probe run observed for one feed."""

    model_config = _MODEL_CONFIG

    feed_slug: str
    probed_at: str
    objects: list[ProbedObject] = Field(default_factory=list)
    snapshot: SnapshotInfo | None = None

    def table(self, qualified: str) -> ProbedObject | None:
        wanted = qualified.lower()
        return next((o for o in self.objects
                     if o.kind == "uc_table" and o.name.lower() == wanted), None)

    def row(self, sheet: str, row_index: int) -> ProbedObject | None:
        return next((o for o in self.objects
                     if o.kind == "config_row" and o.sheet == sheet
                     and o.row_index == row_index), None)

    def counts(self) -> dict[str, int]:
        return {state: sum(1 for o in self.objects if o.state == state) for state in STATES}


def adjusts_artefacts(result: EnvProbeResult | None) -> bool:
    """True when at least one observation changes what an artefact says.

    ``absent`` and ``unreadable`` change nothing — the artefacts are byte for
    byte what they are with the probe disabled.
    """
    return result is not None and any(
        o.state in ("identical", "different") for o in result.objects)


def env_flags(result: EnvProbeResult | None) -> list[str]:
    """Gate flags, one per object, grouped by prefix: env_absent /
    env_identical / env_different / env_unreadable. Flags never FAIL."""
    if result is None:
        return []
    flags: list[str] = []
    info = result.snapshot
    if info is not None and info.missing:
        flags.append(f"env_snapshot_missing:{result.feed_slug} — no probe snapshot at "
                     f"{info.where}; the artefacts are emitted as without a probe")
    elif info is not None and info.stale:
        age = "age unknown" if info.age_hours is None else f"{info.age_hours:.1f} h old"
        flags.append(f"env_snapshot_stale:{result.feed_slug} — taken {info.taken_at} by "
                     f"{info.identity}, {age} (env.probe.max_age_hours {info.max_age_hours:g}); "
                     "used as it is — probe again for a current reading")
    for obj in result.objects:
        detail = obj.name
        if obj.state == "different":
            columns = ", ".join(f"{d.column} ({d.kind})" for d in obj.diffs)
            detail = f"{obj.name}: {columns}"
        elif obj.state == "unreadable":
            detail = f"{obj.name}: {(obj.error or 'no reason given').splitlines()[0][:160]}"
        flags.append(f"env_{obj.state}:{detail}")
    return flags


# ------------------------------------------------------------ M13: headline

Headline = Literal["NOT STARTED", "PARTIAL", "COMPLETE", "UNKNOWN"]


def deployment_headline(result: EnvProbeResult) -> tuple[Headline, str]:
    """How far the feed's deployment has got, claiming ONLY what the object
    states prove:

    ``COMPLETE``     every object is there and matches (none unreadable);
    ``NOT STARTED``  every object is absent (none unreadable);
    ``PARTIAL``      something is there and something is missing or differs —
                     proven by the readable objects alone, whatever the rest;
    ``UNKNOWN``      nothing was readable, or the readable objects agree but
                     unreadable ones could still change the answer.
    """
    counts = result.counts()
    total = sum(counts.values())
    summary = ", ".join(f"{n} {state}" for state, n in counts.items() if n) or "no objects"
    present = counts["identical"] + counts["different"]
    unreadable = counts["unreadable"]
    if total == 0 or unreadable == total:
        return "UNKNOWN", f"nothing could be read ({summary})"
    if present and (counts["absent"] or counts["different"]):
        return "PARTIAL", summary
    if unreadable:
        return "UNKNOWN", (f"{summary} — the {unreadable} unreadable object(s) decide between "
                           + ("COMPLETE and PARTIAL" if present else "NOT STARTED and PARTIAL"))
    if counts["identical"] == total:
        return "COMPLETE", summary
    return "NOT STARTED", summary


# ------------------------------------------------------ M13: the snapshot file

SNAPSHOT_FORMAT = "codegen.probe_snapshot/1"


class ProbeSnapshot(BaseModel):
    """What ``codegen probe`` writes: one probe run, taken where the user's
    identity can read (a notebook / Genie session), consumed anywhere
    (``generate --probe-snapshot``, the App's ``env.probe.snapshots``)."""

    model_config = _MODEL_CONFIG

    format: Literal["codegen.probe_snapshot/1"] = SNAPSHOT_FORMAT
    taken_at: str
    identity: str
    environment: str = ""                       # which of dml.environments the DB is
    transports: dict[str, str] = Field(default_factory=dict)   # target -> seam used
    feeds: list[EnvProbeResult] = Field(default_factory=list)

    def feed(self, feed_slug: str) -> EnvProbeResult | None:
        return next((f for f in self.feeds if f.feed_slug == feed_slug), None)

