"""codegen.databricks — Unity Catalog volumes transport for input documents.

Position in the pipeline: the same transport seam as ``codegen.sharepoint``,
deliberately outside ``resolve → rules → reasoning → emit → gate``. The
client's raw FRD documents and STTM workbooks live in UC volumes
(``<catalog>.<schema>.frd_raw`` / ``sttm_raw``); this module fetches them to
local disk BEFORE generation starts, and the generator's inputs remain files
on disk. Do NOT "simplify" this by reading volumes from inside the extractor
or the resolver — Layer 1 stays deterministic, offline and credential-free.

READ-ONLY by policy for this seam: list and download. No table writes, no
SQL, no job runs live here; those belong to the (separately gated) B1 work.

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
from dataclasses import dataclass
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
}


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
