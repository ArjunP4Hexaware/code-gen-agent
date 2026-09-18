"""An in-memory stand-in for ``databricks.sdk.WorkspaceClient`` — just the
Workspace API and Files API calls ``codegen.storage`` makes. Every call is
recorded so a test can assert WHAT was asked of the workspace (e.g. that no
mkdir ever targeted a root or one of its ancestors)."""

from __future__ import annotations

import io
from types import SimpleNamespace


class NotFound(Exception):  # the SDK's class NAME is what the backend keys on
    error_code = "RESOURCE_DOES_NOT_EXIST"


class PermissionDenied(Exception):
    error_code = "PERMISSION_DENIED"


class _Tree:
    def __init__(self, existing_dirs: tuple[str, ...]):
        self.files: dict[str, bytes] = {}
        self.dirs: set[str] = set(existing_dirs)
        self.calls: list[tuple[str, str]] = []

    def children(self, path: str) -> list[tuple[str, bool, int | None]]:
        prefix = path.rstrip("/") + "/"
        names: dict[str, tuple[bool, int | None]] = {}
        for d in self.dirs:
            if d.startswith(prefix) and d != path:
                names.setdefault(d[len(prefix):].split("/", 1)[0], (True, None))
        for f, data in self.files.items():
            if f.startswith(prefix):
                rest = f[len(prefix):]
                if "/" in rest:
                    names.setdefault(rest.split("/", 1)[0], (True, None))
                else:
                    names[rest] = (False, len(data))
        return [(n, *names[n]) for n in sorted(names)]

    def mkdirs(self, path: str, writable_below: str) -> None:
        if not (path + "/").startswith(writable_below.rstrip("/") + "/") or path == writable_below:
            raise PermissionDenied(f"[Errno 13] Permission denied: {path!r}")
        parts = path.strip("/").split("/")
        for i in range(1, len(parts) + 1):
            self.dirs.add("/" + "/".join(parts[:i]))


class FakeWorkspaceClient:
    """``root`` paths are API-shaped: ``/Users/u/folder`` for the workspace
    (no /Workspace prefix), ``/Volumes/c/s/v`` for volumes. Only paths
    strictly below a root are writable — the root and its ancestors answer
    PermissionDenied, as the serverless mount does."""

    def __init__(self, workspace_root: str = "/Users/u/shared",
                 volume_root: str = "/Volumes/cat/sch/vol"):
        self.ws = _Tree((workspace_root,))
        self.vol = _Tree((volume_root,))
        self._ws_root, self._vol_root = workspace_root, volume_root
        self.workspace = SimpleNamespace(
            list=self._ws_list, download=self._ws_download, upload=self._ws_upload,
            mkdirs=self._ws_mkdirs, get_status=self._ws_status)
        self.files = SimpleNamespace(
            list_directory_contents=self._fs_list, download=self._fs_download,
            upload=self._fs_upload, create_directory=self._fs_mkdir,
            get_metadata=self._fs_meta, get_directory_metadata=self._fs_dir_meta)

    # -- Workspace API ------------------------------------------------------
    def _ws_list(self, path):
        self.ws.calls.append(("list", path))
        if path not in self.ws.dirs:
            raise NotFound(f"Path ({path}) doesn't exist.")
        return [SimpleNamespace(path=f"{path.rstrip('/')}/{name}",
                                object_type=SimpleNamespace(value="DIRECTORY" if d else "FILE"),
                                size=size)
                for name, d, size in self.ws.children(path)]

    def _ws_download(self, path, **_kw):
        self.ws.calls.append(("download", path))
        if path not in self.ws.files:
            raise NotFound(f"Path ({path}) doesn't exist.")
        return io.BytesIO(self.ws.files[path])

    def _ws_upload(self, path, content, overwrite=False, **_kw):
        self.ws.calls.append(("upload", path))
        parent = path.rsplit("/", 1)[0]
        if parent not in self.ws.dirs:
            raise NotFound(f"The parent folder ({parent}) does not exist.")
        self.ws.files[path] = content.read()

    def _ws_mkdirs(self, path):
        self.ws.calls.append(("mkdirs", path))
        self.ws.mkdirs(path, self._ws_root)

    def _ws_status(self, path):
        self.ws.calls.append(("get_status", path))
        if path not in self.ws.dirs and path not in self.ws.files:
            raise NotFound(f"Path ({path}) doesn't exist.")
        return SimpleNamespace(path=path)

    # -- Files API ------------------------------------------------------------
    def _fs_list(self, path):
        self.vol.calls.append(("list", path))
        if path not in self.vol.dirs:
            raise NotFound(f"{path} not found")
        return [SimpleNamespace(path=f"{path}/{name}", name=name, is_directory=d, file_size=size)
                for name, d, size in self.vol.children(path)]

    def _fs_download(self, path):
        self.vol.calls.append(("download", path))
        if path not in self.vol.files:
            raise NotFound(f"{path} not found")
        return SimpleNamespace(contents=io.BytesIO(self.vol.files[path]))

    def _fs_upload(self, path, content, overwrite=False):
        self.vol.calls.append(("upload", path))
        parent = path.rsplit("/", 1)[0]
        if parent not in self.vol.dirs:
            raise NotFound(f"parent {parent} not found")
        self.vol.files[path] = content.read()

    def _fs_mkdir(self, path):
        self.vol.calls.append(("create_directory", path))
        self.vol.mkdirs(path, self._vol_root)

    def _fs_meta(self, path):
        self.vol.calls.append(("get_metadata", path))
        if path not in self.vol.files:
            raise NotFound(f"{path} not found")

    def _fs_dir_meta(self, path):
        self.vol.calls.append(("get_directory_metadata", path))
        if path not in self.vol.dirs:
            raise NotFound(f"{path} not found")
