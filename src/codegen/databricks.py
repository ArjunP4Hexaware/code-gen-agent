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
    """Every knob this seam uses. No secrets — auth is profile/env resolved."""

    profile: str      # ~/.databrickscfg profile name, e.g. DEFAULT
    catalog: str      # e.g. soham_workspace
    schema: str       # e.g. codegen_agent
    frd_volume: str   # raw FRD documents in
    sttm_volume: str  # raw STTM workbooks in


_YAML_KEYS = {
    "databricks_profile": "profile",
    "databricks_catalog": "catalog",
    "databricks_schema": "schema_name",
    "databricks_frd_volume": "frd_volume",
    "databricks_sttm_volume": "sttm_volume",
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
        "profile": knob("databricks_profile"),
        "catalog": knob("databricks_catalog"),
        "schema": knob("databricks_schema"),
        "frd_volume": knob("databricks_frd_volume"),
        "sttm_volume": knob("databricks_sttm_volume"),
    }
    missing = sorted(k for k, v in values.items() if not v)
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
