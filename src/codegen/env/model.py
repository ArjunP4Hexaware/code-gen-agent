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

    @property
    def additive(self) -> list[FieldDiff]:
        return [d for d in self.diffs if d.kind == "added"]

    @property
    def needs_review(self) -> list[FieldDiff]:
        return [d for d in self.diffs if d.kind != "added"]


class EnvProbeResult(BaseModel):
    """Everything one probe run observed for one feed."""

    model_config = _MODEL_CONFIG

    feed_slug: str
    probed_at: str
    objects: list[ProbedObject] = Field(default_factory=list)

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
    for obj in result.objects:
        detail = obj.name
        if obj.state == "different":
            columns = ", ".join(f"{d.column} ({d.kind})" for d in obj.diffs)
            detail = f"{obj.name}: {columns}"
        elif obj.state == "unreadable":
            detail = f"{obj.name}: {(obj.error or 'no reason given').splitlines()[0][:160]}"
        flags.append(f"env_{obj.state}:{detail}")
    return flags
