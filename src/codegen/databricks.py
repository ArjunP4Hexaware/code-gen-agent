"""codegen.databricks — Unity Catalog volumes transport for input documents.

Position in the pipeline: the same transport seam as ``codegen.sharepoint``,
deliberately outside ``resolve → rules → reasoning → emit → gate``. The
client's raw FRD documents and STTM workbooks live in UC volumes
(``<catalog>.<schema>.frd_raw`` / ``sttm_raw``); this module fetches them to
local disk BEFORE generation starts, and the generator's inputs remain files
on disk. Do NOT "simplify" this by reading volumes from inside the extractor
or the resolver — Layer 1 stays deterministic, offline and credential-free.

Document sources stay READ-ONLY: list and download, no deletes, ever. The
ONE write surface (added with the live shell block) is the landing-volume
seeder — ``ensure_volume`` / ``upload_file`` — constrained BY CONSTRUCTION
to ``WRITABLE_PREFIX`` (soham_workspace.codegen_agent.): any other
catalog/schema is refused before a client is even built. No table writes,
no SQL, no job runs live here.

Dependencies: ``databricks-sdk`` via the optional ``[databricks]`` extra.
This module imports cleanly with the extra absent and with zero environment
— the SDK import happens inside ``_client()``, and a missing SDK raises a
named error with the remedy. Auth is whatever the SDK's unified auth
resolves for the configured profile (on this machine: the CLI's OAuth token
from the OS keyring). No token is ever read, stored or logged here.

Config split per repo doctrine: non-secret knobs (profile, catalog, schema,
volume names) live in ``config/config.yaml`` under ``databricks:``, each
overridable by the uppercased ``DATABRICKS_*`` env var (env > YAML).
Credentials are env/keyring-only and never belong in the tracked config.
The section is OPTIONAL: unconfigured, every entry point fails loudly
naming the remedy and every other command is unaffected.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

# What the generator can consume from a volume: STTM workbooks for
# extract-sttm, FRD/STTM contract JSON for generate, and FRD .docx for the
# request-time document readers (convention check, input requirements).
SUPPORTED_SUFFIXES = {".xlsx", ".json", ".docx", ".pptx"}


class DatabricksConfigError(RuntimeError):
    """Configuration is missing or contradictory. Names the remedy."""


class DatabricksTransportError(RuntimeError):
    """A volumes call failed; carries the SDK's message verbatim."""


@dataclass(frozen=True)
class DatabricksVolumesConfig:
    """Every knob this seam uses. No secrets — auth is profile/env resolved
    (the SDK's unified auth; ``DATABRICKS_HOST``/``DATABRICKS_TOKEN`` remain
    supported env overrides, never stored here and never in ``repr``)."""

    profile: str      # ~/.databrickscfg profile name, e.g. DEFAULT
    catalog: str      # e.g. soham_workspace
    schema: str       # e.g. codegen_agent
    frd_volume: str   # raw FRD documents in
    sttm_volume: str  # raw STTM workbooks in
    # B1 additions — each empty until configured; the function needing one
    # raises the named remedy rather than guessing:
    warehouse_id: str = ""          # EXPLAIN-only; waking it bills DBUs
    serving_endpoint: str = ""      # FMAPI chat endpoint (Claude via Databricks)
    wrapper_notebook_path: str = ""  # no wrapper job exists in the Hexaware
    #                                  workspace; supplied by the client
    landing_volume: str = ""        # the ONE writable volume (see below)
    readable_tables: tuple = ()     # allowlist for read_table_rows


# The B1 surface grew beyond volumes; both names refer to the same config.
DatabricksConfig = DatabricksVolumesConfig


_YAML_KEYS = {
    "databricks_profile": "profile",
    "databricks_catalog": "catalog",
    "databricks_schema": "schema_name",
    "databricks_frd_volume": "frd_volume",
    "databricks_sttm_volume": "sttm_volume",
    "databricks_warehouse_id": "warehouse_id",
    "databricks_serving_endpoint": "serving_endpoint",
    "databricks_wrapper_notebook_path": "wrapper_notebook_path",
    "databricks_landing_volume": "landing_volume",
}
# readable_tables is list-valued and comes from YAML only (no env override).


def config_for(settings=None, env=None) -> DatabricksVolumesConfig:
    """YAML knobs + env overrides → config, failing loudly on gaps.

    Precedence per knob: DATABRICKS_* env var > config.yaml ``databricks:``
    section > nothing (an empty knob is an error naming both remedies).
    """
    env = os.environ if env is None else env

    def knob(name: str) -> str:
        from_env = env.get(name.upper(), "")
        if from_env:
            return from_env
        attr = _YAML_KEYS[name]
        if settings is not None:
            return getattr(settings, attr, "") or ""
        return ""

    values = {
        # DATABRICKS_PROFILE > the SDK's own DATABRICKS_CONFIG_PROFILE >
        # YAML > "DEFAULT" — a profile always resolves; auth may still fail
        # at SDK time, loudly.
        "profile": (knob("databricks_profile")
                    or env.get("DATABRICKS_CONFIG_PROFILE", "")
                    or "DEFAULT"),
        "catalog": knob("databricks_catalog"),
        "schema": knob("databricks_schema"),
        "frd_volume": knob("databricks_frd_volume"),
        "sttm_volume": knob("databricks_sttm_volume"),
        "warehouse_id": knob("databricks_warehouse_id"),
        "serving_endpoint": knob("databricks_serving_endpoint"),
        "wrapper_notebook_path": knob("databricks_wrapper_notebook_path"),
        "landing_volume": knob("databricks_landing_volume"),
        "readable_tables": tuple(getattr(settings, "readable_tables", ()) or ())
        if settings is not None else (),
    }
    required = ("catalog", "schema", "frd_volume", "sttm_volume")
    missing = sorted(k for k in required if not values[k])
    if missing:
        raise DatabricksConfigError(
            "Databricks volumes are not configured — missing: " + ", ".join(missing) + ". "
            "Set the `databricks:` section of config/config.yaml (profile, catalog, "
            "schema, frd_volume, sttm_volume) or the DATABRICKS_PROFILE / "
            "DATABRICKS_CATALOG / DATABRICKS_SCHEMA / DATABRICKS_FRD_VOLUME / "
            "DATABRICKS_STTM_VOLUME environment variables. Credentials come from "
            "the profile's own auth (CLI OAuth or token), never from this repo."
        )
    return DatabricksVolumesConfig(**values)


def _client(cfg: DatabricksVolumesConfig):
    """The one place the SDK is imported and a workspace client built."""
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise DatabricksConfigError(
            "databricks-sdk is not installed — install the optional extra: "
            'pip install -e ".[databricks]"'
        ) from exc
    # A Databricks Apps runtime (or any env-auth context) injects
    # DATABRICKS_HOST plus client credentials; the SDK's unified auth
    # resolves those on its own, and passing profile= would fail where no
    # ~/.databrickscfg exists. The named profile is the local-machine path.
    if os.environ.get("DATABRICKS_HOST"):
        return WorkspaceClient()
    return WorkspaceClient(profile=cfg.profile)


def volume_path(cfg: DatabricksVolumesConfig, volume: str, name: str = "") -> str:
    root = f"/Volumes/{cfg.catalog}/{cfg.schema}/{volume}"
    return f"{root}/{name}" if name else root


def list_documents(cfg: DatabricksVolumesConfig, client=None) -> dict[str, list[dict]]:
    """Supported files in both volumes: {kind: [{name, size, volume}]}.

    A missing/unreadable volume raises with the SDK's message — an empty
    listing and a broken one must not look the same to the caller.
    """
    client = client if client is not None else _client(cfg)
    result: dict[str, list[dict]] = {}
    for kind, volume in (("frd", cfg.frd_volume), ("sttm", cfg.sttm_volume)):
        try:
            entries = client.files.list_directory_contents(volume_path(cfg, volume))
            files = [
                {"name": e.name, "size": e.file_size or 0, "volume": volume}
                for e in entries
                if not e.is_directory
                and Path(e.name).suffix.lower() in SUPPORTED_SUFFIXES
            ]
        except Exception as exc:  # noqa: BLE001 — surfaced verbatim, never swallowed
            raise DatabricksTransportError(
                f"listing {volume_path(cfg, volume)} failed: {exc}"
            ) from exc
        result[kind] = sorted(files, key=lambda f: f["name"].lower())
    return result


def fetch_document(
    cfg: DatabricksVolumesConfig,
    volume: str,
    name: str,
    dest_dir: str | Path,
    client=None,
) -> Path:
    """Download one volume file into ``dest_dir``; returns the local path.

    Same fail-loud shape as the SharePoint fetch: written via a ``.part``
    temp file then renamed, so a broken transfer can never leave a
    truncated workbook for openpyxl to misread as a layout problem.
    """
    if Path(name).suffix.lower() not in SUPPORTED_SUFFIXES:
        raise DatabricksTransportError(
            f"{name!r} is not a supported input ({sorted(SUPPORTED_SUFFIXES)})"
        )
    if "/" in name or "\\" in name or name.startswith("."):
        raise DatabricksTransportError(f"invalid volume file name: {name!r}")
    client = client if client is not None else _client(cfg)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / f"{name}.part"
    try:
        response = client.files.download(volume_path(cfg, volume, name))
        with open(tmp, "wb") as handle:
            while True:
                chunk = response.contents.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    except Exception as exc:  # noqa: BLE001 — surfaced verbatim
        tmp.unlink(missing_ok=True)
        raise DatabricksTransportError(
            f"download of {volume_path(cfg, volume, name)} failed: {exc}"
        ) from exc
    target = dest / name
    tmp.replace(target)
    return target


# --------------------------------------------------------------------------- #
# B1 surface: catalog reads, EXPLAIN, job read, FMAPI chat. READ-ONLY by
# construction — there is deliberately no execute, no create_job, no run_now
# anywhere in this module, and the governance "never writes back" check
# introspects for write-shaped names.
# --------------------------------------------------------------------------- #


def _require(cfg: DatabricksConfig, knob: str) -> str:
    value = getattr(cfg, knob)
    if not value:
        raise DatabricksConfigError(
            f"databricks.{knob} is not configured — set it in the `databricks:` "
            f"section of config/config.yaml or the DATABRICKS_{knob.upper()} "
            "environment variable."
        )
    return value


def table_exists(cfg: DatabricksConfig, full_name: str, client=None) -> bool:
    client = client if client is not None else _client(cfg)
    try:
        client.tables.get(full_name)
        return True
    except Exception as exc:  # noqa: BLE001 — only not-found maps to False
        if "does not exist" in str(exc).lower() or "not found" in str(exc).lower():
            return False
        raise DatabricksTransportError(
            f"tables.get({full_name!r}) failed: {exc}"
        ) from exc


def describe_table(cfg: DatabricksConfig, full_name: str, client=None) -> dict:
    """Columns and types, verbatim from Unity Catalog."""
    client = client if client is not None else _client(cfg)
    try:
        table = client.tables.get(full_name)
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(
            f"tables.get({full_name!r}) failed: {exc}"
        ) from exc
    return {
        "full_name": table.full_name,
        "table_type": str(table.table_type.value if table.table_type else ""),
        "columns": [
            {"name": c.name, "type": c.type_text} for c in (table.columns or [])
        ],
    }


def table_properties(cfg: DatabricksConfig, full_name: str, client=None) -> dict:
    client = client if client is not None else _client(cfg)
    try:
        table = client.tables.get(full_name)
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(
            f"tables.get({full_name!r}) failed: {exc}"
        ) from exc
    return dict(table.properties or {})


def explain(cfg: DatabricksConfig, sql: str, warehouse_id: str | None = None,
            client=None) -> str:
    """Run ``EXPLAIN`` for one statement on the SQL warehouse. NOTHING ELSE.

    The only statement shape this seam may send: anything not starting with
    EXPLAIN is prefixed, never executed as-is. COST: the configured
    warehouse auto-stops after 10 minutes — an EXPLAIN wakes it, and that
    wake bills DBUs from the shared pool. Call deliberately.
    """
    warehouse = warehouse_id or _require(cfg, "warehouse_id")
    statement = sql.strip().rstrip(";")
    if not statement.lower().startswith("explain"):
        statement = f"EXPLAIN {statement}"
    client = client if client is not None else _client(cfg)
    try:
        response = client.statement_execution.execute_statement(
            statement=statement, warehouse_id=warehouse, wait_timeout="50s"
        )
        state = str(response.status.state.value if response.status else "")
        if state != "SUCCEEDED":
            message = ""
            if response.status and response.status.error:
                message = response.status.error.message or ""
            raise DatabricksTransportError(
                f"EXPLAIN finished {state or 'without status'}: {message}"
            )
        rows = (response.result.data_array or []) if response.result else []
        return "\n".join(cell for row in rows for cell in row if cell)
    except DatabricksTransportError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(f"EXPLAIN failed: {exc}") from exc


def get_job(cfg: DatabricksConfig, job_id: int, client=None) -> dict:
    """Read one job's settings (name, tasks, parameters). Never runs it."""
    client = client if client is not None else _client(cfg)
    try:
        job = client.jobs.get(job_id=job_id)
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(f"jobs.get({job_id}) failed: {exc}") from exc
    settings = job.settings
    return {
        "job_id": job.job_id,
        "name": settings.name if settings else None,
        "tasks": [t.task_key for t in (settings.tasks or [])] if settings else [],
        "parameters": [p.name for p in (settings.parameters or [])] if settings else [],
    }


def chat(cfg: DatabricksConfig, messages: list[dict], endpoint: str | None = None,
         max_tokens: int = 1024, client=None) -> str:
    """One chat completion via a Foundation Model API serving endpoint.

    Anthropic remains the sole model vendor — FMAPI serving a Claude model
    is a TRANSPORT, not a vendor change. ``messages`` are
    ``{"role": ..., "content": ...}`` dicts; no sampling parameters, ever
    (same no-temperature rule as the Anthropic provider).
    """
    name = endpoint or _require(cfg, "serving_endpoint")
    client = client if client is not None else _client(cfg)
    try:
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

        sdk_messages = [
            ChatMessage(role=ChatMessageRole(m["role"]), content=m["content"])
            for m in messages
        ]
        response = client.serving_endpoints.query(
            name=name, messages=sdk_messages, max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""
    except DatabricksConfigError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(
            f"serving_endpoints.query({name!r}) failed: {exc}"
        ) from exc


# --------------------------------------------------------------------------- #
# Landing-volume write surface (the seam's first write task). The ONLY
# writable location, by construction: any target outside WRITABLE_PREFIX is
# refused before a client exists. Volume creation and file upload only —
# no deletes anywhere in this module, and no overwrite without force.
# --------------------------------------------------------------------------- #

WRITABLE_PREFIX = "soham_workspace.codegen_agent."


def _landing_full_name(cfg: DatabricksConfig) -> str:
    if not cfg.landing_volume:
        raise DatabricksConfigError(
            "databricks.landing_volume is not configured — set it in the "
            "`databricks:` section of config/config.yaml (or "
            "DATABRICKS_LANDING_VOLUME)."
        )
    full_name = f"{cfg.catalog}.{cfg.schema}.{cfg.landing_volume}"
    if not full_name.startswith(WRITABLE_PREFIX):
        raise DatabricksConfigError(
            f"refusing to write to {full_name!r}: the only writable location "
            f"is under {WRITABLE_PREFIX}* (session policy, enforced in code)."
        )
    return full_name


def ensure_volume(cfg: DatabricksConfig, client=None) -> dict:
    """Create the landing volume if absent. Returns {full_name, created}."""
    full_name = _landing_full_name(cfg)
    client = client if client is not None else _client(cfg)
    try:
        client.volumes.read(full_name)
        return {"full_name": full_name, "created": False}
    except Exception as exc:  # noqa: BLE001 — only not-found means "create it"
        message = str(exc).lower()
        if "does not exist" not in message and "not found" not in message:
            raise DatabricksTransportError(
                f"volumes.read({full_name!r}) failed: {exc}"
            ) from exc
    try:
        from databricks.sdk.service.catalog import VolumeType

        client.volumes.create(
            catalog_name=cfg.catalog,
            schema_name=cfg.schema,
            name=cfg.landing_volume,
            volume_type=VolumeType.MANAGED,
        )
        return {"full_name": full_name, "created": True}
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(
            f"volumes.create({full_name!r}) failed: {exc}"
        ) from exc


def upload_file(cfg: DatabricksConfig, relative_path: str, data: bytes,
                force: bool = False, client=None) -> str:
    """Upload one synthetic file into the landing volume; returns the path.

    ``relative_path`` is the volume-relative target (e.g.
    ``mftlanding/inbound/.../file.csv``). Refuses '..' segments and, without
    ``force``, refuses to overwrite an existing file.
    """
    full_name = _landing_full_name(cfg)
    clean = relative_path.replace("\\", "/").strip("/")
    if not clean or ".." in clean.split("/"):
        raise DatabricksTransportError(f"invalid landing path: {relative_path!r}")
    target = f"/Volumes/{full_name.replace('.', '/')}/{clean}"
    client = client if client is not None else _client(cfg)
    if not force:
        try:
            client.files.get_metadata(target)
            raise DatabricksTransportError(
                f"{target} already exists — re-run with --force to overwrite."
            )
        except DatabricksTransportError:
            raise
        except Exception:  # noqa: BLE001, S110 — absent file: proceed to upload
            pass
    try:
        import io

        client.files.upload(target, io.BytesIO(data), overwrite=force)
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(f"upload of {target} failed: {exc}") from exc
    return target


def list_landing(cfg: DatabricksConfig, prefix: str = "",
                 client=None) -> list[dict]:
    """Recursive listing of the landing volume: [{path, name, size, modified}].

    ``path`` is volume-relative (posix). Read-only; a missing volume raises
    (the shell block's auto mode treats that as "fall back to synthetic").
    """
    full_name = _landing_full_name(cfg)
    root = f"/Volumes/{full_name.replace('.', '/')}"
    start = f"{root}/{prefix.strip('/')}" if prefix.strip("/") else root
    client = client if client is not None else _client(cfg)

    entries: list[dict] = []

    def walk(directory: str) -> None:
        for entry in client.files.list_directory_contents(directory):
            if entry.is_directory:
                walk(entry.path)
            else:
                relative = entry.path[len(root):].lstrip("/")
                modified = ""
                if entry.last_modified:
                    from datetime import datetime

                    modified = datetime.fromtimestamp(
                        entry.last_modified / 1000, tz=UTC
                    ).strftime("%Y-%m-%d %H:%M:%S")
                entries.append({
                    "path": relative,
                    "name": entry.name,
                    "size": entry.file_size or 0,
                    "modified": modified,
                })

    try:
        walk(start)
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(
            f"listing {start} failed: {exc}"
        ) from exc
    return sorted(entries, key=lambda e: e["path"])


def landing_volume_exists(cfg: DatabricksConfig, client=None) -> bool:
    """Cheap existence probe for the shell block's auto mode."""
    full_name = _landing_full_name(cfg)
    client = client if client is not None else _client(cfg)
    try:
        client.volumes.read(full_name)
        return True
    except Exception as exc:  # noqa: BLE001
        message = str(exc).lower()
        if "does not exist" in message or "not found" in message:
            return False
        raise DatabricksTransportError(
            f"volumes.read({full_name!r}) failed: {exc}"
        ) from exc


# --------------------------------------------------------------------------- #
# Allowlisted table read (Statement Execution). SELECT-only BY CONSTRUCTION:
# the statement is rendered here from validated identifiers — no caller ever
# passes SQL — and only tables named in `databricks.readable_tables` are
# accepted. First use wakes the serverless warehouse (auto-stop 10 min):
# that wake is DBU spend from the shared pool.
# --------------------------------------------------------------------------- #

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")
_TABLE_READ_CACHE: dict = {}
_TABLE_READ_TTL_SECONDS = 60.0


def read_table_rows(cfg: DatabricksConfig, fqn: str,
                    columns: list[str] | None = None, limit: int = 500,
                    client=None) -> list[dict]:
    """Rows from ONE allowlisted table as dicts (values as returned strings).

    Refuses any fqn not in ``cfg.readable_tables`` and any identifier that
    is not a plain word — the SELECT is assembled here, never accepted from
    a caller. Results are cached for 60 s per (fqn, columns, limit).
    """
    allowed = tuple(cfg.readable_tables or ())
    if fqn not in allowed:
        raise DatabricksConfigError(
            f"refusing to read {fqn!r}: not in databricks.readable_tables "
            f"{list(allowed)} — add it there deliberately or leave it alone."
        )
    parts = fqn.split(".")
    if len(parts) != 3 or not all(_IDENTIFIER_RE.match(p) for p in parts):
        raise DatabricksConfigError(f"invalid table name: {fqn!r}")
    for column in columns or ():
        if not _IDENTIFIER_RE.match(column):
            raise DatabricksConfigError(f"invalid column name: {column!r}")
    if not (1 <= int(limit) <= 10_000):
        raise DatabricksConfigError(f"limit out of range: {limit}")
    warehouse = cfg.warehouse_id
    if not warehouse:
        raise DatabricksConfigError(
            "databricks.warehouse_id is not configured — required for table reads."
        )

    key = (fqn, tuple(columns or ()), int(limit))
    cached = _TABLE_READ_CACHE.get(key)
    if cached and time.time() - cached[0] < _TABLE_READ_TTL_SECONDS:
        return cached[1]

    selected = ", ".join(f"`{c}`" for c in columns) if columns else "*"
    statement = (
        f"SELECT {selected} FROM `{parts[0]}`.`{parts[1]}`.`{parts[2]}` "
        f"LIMIT {int(limit)}"
    )
    client = client if client is not None else _client(cfg)
    try:
        response = client.statement_execution.execute_statement(
            statement=statement, warehouse_id=warehouse, wait_timeout="50s"
        )
        state = str(response.status.state.value if response.status else "")
        if state != "SUCCEEDED":
            message = ""
            if response.status and response.status.error:
                message = response.status.error.message or ""
            raise DatabricksTransportError(
                f"table read finished {state or 'without status'}: {message}"
            )
        names = [c.name for c in response.manifest.schema.columns]
        rows = [
            dict(zip(names, row, strict=False))
            for row in ((response.result.data_array or []) if response.result else [])
        ]
    except DatabricksTransportError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DatabricksTransportError(f"table read failed: {exc}") from exc
    _TABLE_READ_CACHE[key] = (time.time(), rows)
    return rows
