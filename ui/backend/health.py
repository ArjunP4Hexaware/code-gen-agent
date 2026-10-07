"""Storage-root health probe (2026-10-07): which env var / which grant is
missing when the App lists no documents.

For each root the App reads — every ``CODEGEN_EXTRA_INPUT_DIRS`` entry and
the ``CODEGEN_STORAGE_INPUTS`` / ``_STATE`` / ``_OUTPUTS`` roles — one row:
the env var, its value, and a LIVE probe (a listing of the root, bounded):

* ``readable``   — listed; ``detail`` says how many entries;
* ``empty``      — listed, nothing in it;
* ``not_shared`` — the API answers not-found / permission-denied. The
  Workspace API answers "does not exist" for a folder the caller may not see,
  so a missing folder and an unshared one look the same: the detail names
  the App's service principal and the grant it needs;
* ``unset``      — the env var is not set (the App falls back to its local
  default, wiped on every restart);
* ``invalid`` / ``error`` / ``timeout`` — a malformed URI, any other failure,
  no answer in time.

Read-only: listing only, nothing is created or written.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

from codegen.storage import open_backend
from codegen.storage.base import StorageConfigError, StorageNotFound

ROLE_ENVS = (("CODEGEN_STORAGE_INPUTS", "inputs", "Can Manage"),
             ("CODEGEN_STORAGE_STATE", "state", "Can Manage"),
             ("CODEGEN_STORAGE_OUTPUTS", "outputs", "Can Manage"))
EXTRA_ENV = "CODEGEN_EXTRA_INPUT_DIRS"
EXTRA_GRANT = "Can Read"
_DENIED_MARKERS = ("permission", "PermissionDenied", "PERMISSION_DENIED", "403", "Forbidden",
                   "does not have")


def _denied(error: BaseException) -> bool:
    """A permission refusal, judged on the error AND the SDK error the
    storage layer wrapped (its class name / error_code, never only the text)."""
    for exc in (error, error.__cause__):
        if exc is None:
            continue
        if type(exc).__name__ == "PermissionDenied" or \
                getattr(exc, "error_code", None) == "PERMISSION_DENIED":
            return True
        if any(m in f"{type(exc).__name__}: {exc}" for m in _DENIED_MARKERS):
            return True
    return False


def app_principal(client_factory: Callable | None) -> str:
    """The App's service principal as the platform names it: the workspace
    identity's display name (+ application id) when the API answers, else the
    injected ``DATABRICKS_CLIENT_ID``; outside an App, says so."""
    client_id = os.environ.get("DATABRICKS_CLIENT_ID", "").strip()
    if client_factory is not None and os.environ.get("DATABRICKS_HOST"):
        try:
            me = client_factory().current_user.me()
            name = getattr(me, "display_name", None) or getattr(me, "user_name", None)
            app_id = getattr(me, "user_name", None) or client_id
            if name:
                return f"{name} ({app_id})" if app_id and app_id != name else name
        except Exception:  # noqa: BLE001 — the probe must answer regardless
            pass
    if client_id:
        return f"the App's service principal ({client_id})"
    return "the App's service principal (not running as a Databricks App here)"


def _extra_entries(raw: str) -> list[str]:
    entries = []
    for entry in raw.replace("\n", ";").split(";"):
        entry = entry.strip()
        if not entry:
            continue
        if entry.partition(":")[0] not in ("local", "workspace", "volume"):
            normalized = entry.replace("\\", "/")
            if normalized.startswith("/Workspace/"):
                entry = f"workspace:{normalized}"
            elif normalized.startswith("/Volumes/"):
                entry = f"volume:{normalized}"
            else:
                entry = f"local:{entry}"
        entries.append(entry)
    return entries


def _probe(uri: str, base_dir: Path, client_factory: Callable | None,
           principal: str, grant: str, timeout: float) -> tuple[str, str]:
    result: dict = {}

    def work() -> None:
        try:
            backend = open_backend(uri, base_dir=base_dir, client_factory=client_factory,
                                   create_root=False)
            # exists() first: a remote list() answers [] for a root it cannot
            # see, which would read as "empty".
            if not backend.exists(""):
                result["missing"] = True
                return
            result["entries"] = backend.list("")
        except Exception as exc:  # noqa: BLE001 — classified below
            result["error"] = exc

    thread = threading.Thread(target=work, name="health-probe", daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return "timeout", f"no answer within {timeout:g}s"
    error = result.get("error")
    not_shared = (f"missing, or not shared with {principal} — share the folder with it "
                  f"({grant})")
    if result.get("missing"):
        return "not_shared", f"{not_shared}; the API says it does not exist"
    if error is None:
        entries = result.get("entries") or []
        if not entries:
            return "empty", "listed — the folder is empty"
        return "readable", f"listed — {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}"
    text = f"{type(error).__name__}: {error}"
    if isinstance(error, StorageConfigError):
        return "invalid", text
    if isinstance(error, StorageNotFound) or _denied(error):
        return "not_shared", f"{not_shared}; the API said: {error}"
    return "error", text


def probe_roots(base_dir: Path, *, env: Mapping[str, str] | None = None,
                client_factory: Callable | None = None, principal: str | None = None,
                timeout: float = 10.0) -> dict:
    """``{"principal": …, "roots": [{env, role, value, state, detail}, …]}``."""
    env = os.environ if env is None else env
    principal = principal or app_principal(client_factory)
    rows: list[dict] = []
    raw_extra = env.get(EXTRA_ENV, "").strip()
    if not raw_extra:
        rows.append({"env": EXTRA_ENV, "role": "pairs (documents)", "value": None,
                     "state": "unset", "detail": "not set — no pair folders are listed"})
    for uri in _extra_entries(raw_extra):
        state, detail = _probe(uri, base_dir, client_factory, principal, EXTRA_GRANT, timeout)
        rows.append({"env": EXTRA_ENV, "role": "pairs (documents)", "value": uri,
                     "state": state, "detail": detail})
    for name, role, grant in ROLE_ENVS:
        value = env.get(name, "").strip()
        if not value:
            rows.append({"env": name, "role": role, "value": None, "state": "unset",
                         "detail": "not set — the App uses its local default (wiped on "
                                   "every restart)"})
            continue
        state, detail = _probe(value, base_dir, client_factory, principal, grant, timeout)
        rows.append({"env": name, "role": role, "value": value, "state": state,
                     "detail": detail})
    return {"principal": principal, "roots": rows}


__all__ = ["app_principal", "probe_roots"]
