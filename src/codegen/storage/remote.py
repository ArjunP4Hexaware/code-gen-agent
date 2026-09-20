"""``workspace:`` and ``volume:`` — the two Databricks backends.

Both talk to the REST APIs through ``databricks-sdk`` (the Workspace API and
the Files API). Neither ever touches ``/Workspace`` or ``/Volumes`` as a
filesystem path: an App container has no such mount, and on serverless
compute the FUSE mount refuses ``mkdir`` on its own mount point.

Auth is the SDK's unified auth, resolved by the caller-supplied client
factory (``codegen.databricks._client``: the App's ambient service
principal when ``DATABRICKS_HOST`` is injected, the notebook's own auth
inside a notebook, the named CLI profile on a laptop). The SDK is imported
lazily so this module imports with the ``[databricks]`` extra absent.
"""

from __future__ import annotations

import io
from collections.abc import Callable

from codegen.storage.base import (
    StorageBackend,
    StorageConfigError,
    StorageEntry,
    StorageError,
    StorageNotFound,
    clean_rel,
    parent_rel,
)

_NOT_FOUND_NAMES = {"NotFound", "ResourceDoesNotExist"}
_NOT_FOUND_CODES = ("RESOURCE_DOES_NOT_EXIST", "NOT_FOUND")
_EXISTS_NAMES = {"ResourceAlreadyExists", "AlreadyExists"}


def _is_not_found(exc: Exception) -> bool:
    if type(exc).__name__ in _NOT_FOUND_NAMES:
        return True
    # The error CODE only — a message quotes the path, and a path may contain
    # anything (a ticket number, the words "not found").
    code = str(getattr(exc, "error_code", "") or "")
    return code in _NOT_FOUND_CODES or "RESOURCE_DOES_NOT_EXIST" in str(exc)


def _already_exists(exc: Exception) -> bool:
    return (type(exc).__name__ in _EXISTS_NAMES
            or "ALREADY_EXISTS" in str(getattr(exc, "error_code", "") or ""))


def _format_kwarg(enum_name: str) -> dict:
    """``format=AUTO`` (a workspace FILE travels as raw bytes, whatever its
    extension); omitted when the SDK is absent (a test's fake client)."""
    try:
        from databricks.sdk.service import workspace as _ws
    except ImportError:
        return {}
    return {"format": getattr(_ws, enum_name).AUTO}


class _SdkBackend(StorageBackend):
    """Shared plumbing: lazy client, absolute-path join, error wrapping."""

    _root_prefix = ""       # "/Workspace" | "/Volumes"
    _min_root_parts = 0     # segments a usable root needs after the prefix

    def __init__(self, root: str, *, client=None, client_factory: Callable | None = None):
        normalized = "/" + "/".join(p for p in root.replace("\\", "/").split("/") if p)
        if not (normalized == self._root_prefix
                or normalized.startswith(self._root_prefix + "/")):
            raise StorageConfigError(
                f"{self.scheme}: roots start with {self._root_prefix}/ — got {root!r}")
        parts = normalized[len(self._root_prefix):].strip("/").split("/")
        if len([p for p in parts if p]) < self._min_root_parts or ".." in parts:
            raise StorageConfigError(
                f"{self.scheme}:{root} is not a usable root — expected "
                f"{self._root_shape}")
        self.root = normalized
        self._client = client
        self._client_factory = client_factory

    _root_shape = ""

    @property
    def client(self):
        if self._client is None:
            if self._client_factory is None:
                raise StorageConfigError(
                    f"{self.uri()} needs a Databricks workspace client — install the "
                    '[databricks] extra and configure the `databricks:` section / '
                    "DATABRICKS_* environment")
            self._client = self._client_factory()
        return self._client

    def _abs(self, rel: str = "") -> str:
        rel = clean_rel(rel)
        return f"{self.root}/{rel}" if rel else self.root

    def _fail(self, action: str, rel: str, exc: Exception) -> StorageError:
        if isinstance(exc, StorageError):
            return exc                  # already ours (no client configured, bad path)
        if _is_not_found(exc):
            return StorageNotFound(f"{self.uri(rel)} does not exist ({action}): {exc}")
        return StorageError(f"{action} {self.uri(rel)} failed: {exc}")

    def write_bytes(self, rel: str, data: bytes) -> None:
        rel = clean_rel(rel)
        if not rel:
            raise StorageError("write_bytes needs a file path below the root")
        self.mkdir(parent_rel(rel))
        try:
            self._upload(self._abs(rel), data)
        except Exception as exc:  # noqa: BLE001 — surfaced with the SDK's message
            if _is_not_found(exc) and not parent_rel(rel):
                # Every folder below the root was just created, so the missing
                # parent IS the root — which is never created from here.
                raise StorageConfigError(
                    f"storage root {self.uri()} does not exist — create the folder and share "
                    f"it with the calling principal (docs/ACFC_DEPLOY.md); a root is never "
                    f"created for you: {exc}") from exc
            raise self._fail("write", rel, exc) from exc

    def mkdir(self, rel: str) -> None:
        rel = clean_rel(rel)
        if not rel:
            return                      # the root is never created (module docstring)
        try:
            self._mkdirs(self._abs(rel))
        except Exception as exc:  # noqa: BLE001
            if not _already_exists(exc):
                raise self._fail("mkdir", rel, exc) from exc

    def _upload(self, path: str, data: bytes) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def _mkdirs(self, path: str) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class WorkspaceBackend(_SdkBackend):
    """Workspace files (``/Workspace/Users/<user>/…``) via the Workspace API:
    list / export / import / mkdirs / get-status. The folder only has to be
    shared with the caller (the App's service principal: CAN_EDIT on a folder
    it writes to, CAN_READ on a read-only one) — no Unity Catalog grant is
    involved.

    The API addresses objects WITHOUT the ``/Workspace`` prefix, so it is
    stripped at the call boundary and kept in every URI a person reads."""

    scheme = "workspace"
    _root_prefix = "/Workspace"
    _min_root_parts = 1
    _root_shape = "workspace:/Workspace/Users/<user>/<folder>"

    def _api(self, rel: str = "") -> str:
        return self._abs(rel)[len(self._root_prefix):] or "/"

    def list(self, rel: str = "") -> list[StorageEntry]:
        try:
            objects = list(self.client.workspace.list(self._api(rel)))
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                return []
            raise self._fail("list", rel, exc) from exc
        entries = []
        for obj in objects:
            kind = str(getattr(obj.object_type, "value", obj.object_type) or "")
            name = str(obj.path or "").rstrip("/").rsplit("/", 1)[-1]
            if not name:
                continue
            is_dir = kind in ("DIRECTORY", "REPO")
            size = None if is_dir else getattr(obj, "size", None)
            entries.append(StorageEntry(name, is_dir, size))
        return sorted(entries, key=lambda e: e.name)

    def read_bytes(self, rel: str) -> bytes:
        try:
            with self.client.workspace.download(self._api(rel),
                                                **_format_kwarg("ExportFormat")) as fh:
                return fh.read()
        except Exception as exc:  # noqa: BLE001
            raise self._fail("read", rel, exc) from exc

    def exists(self, rel: str = "") -> bool:
        try:
            self.client.workspace.get_status(self._api(rel))
            return True
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                return False
            raise self._fail("stat", rel, exc) from exc

    def _upload(self, path: str, data: bytes) -> None:
        self.client.workspace.upload(path[len(self._root_prefix):], io.BytesIO(data),
                                     overwrite=True, **_format_kwarg("ImportFormat"))

    def _mkdirs(self, path: str) -> None:
        self.client.workspace.mkdirs(path[len(self._root_prefix):])


class VolumeBackend(_SdkBackend):
    """Unity Catalog volumes via the Files API (``/api/2.0/fs``) — never the
    ``/Volumes`` mount. Needs USE CATALOG / USE SCHEMA plus READ VOLUME
    (and WRITE VOLUME for state / outputs) for the calling principal."""

    scheme = "volume"
    _root_prefix = "/Volumes"
    _min_root_parts = 3
    _root_shape = "volume:/Volumes/<catalog>/<schema>/<volume>[/<folder>]"

    def list(self, rel: str = "") -> list[StorageEntry]:
        try:
            listed = list(self.client.files.list_directory_contents(self._abs(rel)))
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                return []
            raise self._fail("list", rel, exc) from exc
        entries = []
        for item in listed:
            name = item.name or str(item.path or "").rstrip("/").rsplit("/", 1)[-1]
            is_dir = bool(item.is_directory)
            entries.append(StorageEntry(name, is_dir, None if is_dir else item.file_size))
        return sorted(entries, key=lambda e: e.name)

    def read_bytes(self, rel: str) -> bytes:
        try:
            return self.client.files.download(self._abs(rel)).contents.read()
        except Exception as exc:  # noqa: BLE001
            raise self._fail("read", rel, exc) from exc

    def exists(self, rel: str = "") -> bool:
        path = self._abs(rel)
        for probe in (self.client.files.get_metadata, self.client.files.get_directory_metadata):
            try:
                probe(path)
                return True
            except Exception as exc:  # noqa: BLE001
                if not _is_not_found(exc):
                    raise self._fail("stat", rel, exc) from exc
        return False

    def _upload(self, path: str, data: bytes) -> None:
        self.client.files.upload(path, io.BytesIO(data), overwrite=True)

    def _mkdirs(self, path: str) -> None:
        self.client.files.create_directory(path)
