"""``local:`` — a directory on this machine's disk (today's behaviour)."""

from __future__ import annotations

from pathlib import Path

from codegen.storage.base import (
    StorageBackend,
    StorageConfigError,
    StorageEntry,
    StorageError,
    StorageNotFound,
    clean_rel,
)

# Roots the local backend refuses by name: on serverless compute these are
# FUSE mounts (when mounted at all) and an App container has neither. The
# matching remote backend is the remedy.
_REMOTE_ROOTS = {"/Volumes": "volume:", "/Workspace": "workspace:"}


class LocalBackend(StorageBackend):
    """Root = a directory. ``create_root`` is granted only to roots inside
    the checkout (``local:./out`` on a fresh clone); an absolute root must
    already exist — it is never created, and neither is any ancestor."""

    scheme = "local"

    def __init__(self, root: Path, *, create_root: bool = False, display: str | None = None):
        self.path = Path(root)
        self.root = display if display is not None else self.path.as_posix()
        self._create_root = create_root

    @property
    def is_local(self) -> bool:
        return True

    def local_path(self, rel: str = "") -> Path:
        rel = clean_rel(rel)
        return self.path / rel if rel else self.path

    def _ensure_root(self) -> None:
        if self.path.is_dir():
            return
        if not self._create_root:
            raise StorageConfigError(
                f"storage root {self.uri()} does not exist — create it (or point the "
                "storage URI at an existing directory); a root is never created for you")
        # Inside the checkout: every missing level up to the base is ours.
        self.path.mkdir(parents=True, exist_ok=True)

    def list(self, rel: str = "") -> list[StorageEntry]:
        directory = self.local_path(rel)
        if not directory.is_dir():
            return []
        entries = []
        for child in sorted(directory.iterdir(), key=lambda p: p.name):
            is_dir = child.is_dir()
            entries.append(StorageEntry(child.name, is_dir,
                                        None if is_dir else child.stat().st_size))
        return entries

    def read_bytes(self, rel: str) -> bytes:
        path = self.local_path(rel)
        if not path.is_file():
            raise StorageNotFound(f"{self.uri(rel)} does not exist")
        return path.read_bytes()

    def write_bytes(self, rel: str, data: bytes) -> None:
        rel = clean_rel(rel)
        if not rel:
            raise StorageError("write_bytes needs a file path below the root")
        self.mkdir(rel.rsplit("/", 1)[0] if "/" in rel else "")
        self.local_path(rel).write_bytes(data)

    def exists(self, rel: str = "") -> bool:
        return self.local_path(rel).exists()

    def mkdir(self, rel: str) -> None:
        rel = clean_rel(rel)
        self._ensure_root()
        current = self.path
        for part in rel.split("/") if rel else []:
            current = current / part
            if not current.is_dir():
                current.mkdir()          # one level at a time, never parents=True


def refuse_remote_root(root: str) -> None:
    """``local:/Volumes/…`` is the serverless PermissionError waiting to
    happen; say which scheme to use instead."""
    normalized = root.replace("\\", "/")
    for prefix, scheme in _REMOTE_ROOTS.items():
        if normalized == prefix or normalized.startswith(prefix + "/"):
            raise StorageConfigError(
                f"local:{root} addresses {prefix} as a mounted filesystem — it is not one on "
                f"serverless compute or in an App container. Use {scheme}{normalized} instead.")
