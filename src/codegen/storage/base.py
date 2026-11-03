"""The storage interface every backend implements (M8.1).

Five operations, all over paths RELATIVE to the backend root, POSIX
separators: ``list``, ``read_bytes``, ``write_bytes``, ``exists``,
``mkdir``. A relative path can never leave the root (``..``, a drive, a
leading ``/`` and a backslash are refused before any I/O).

mkdir semantics are the same everywhere and deliberate: a backend creates
directories only BELOW its root, never the root itself and never an
ancestor of it. Creating ``/Volumes`` (what ``Path.mkdir(parents=True)``
attempts on serverless compute when any ancestor looks absent) is the
``PermissionError: [Errno 13] … '/Volumes'`` recorded in
docs/acfc/RETROFIT_LOG.md. A root that does not exist is a configuration
error naming the URI — never something to create on the way to a write.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class StorageError(RuntimeError):
    """A storage call failed; carries the backend's message verbatim."""


class StorageConfigError(StorageError):
    """A storage URI / root is missing, malformed or refused. Names the remedy."""


class StorageNotFound(StorageError):
    """The relative path does not exist under the backend root."""


@dataclass(frozen=True)
class StorageEntry:
    """One child of a listed directory."""

    name: str
    is_dir: bool
    size: int | None = None
    # M9.3: last-modified as the backend reports it (epoch milliseconds), when
    # it does — listing metadata only, so a chooser can tell a changed file
    # from a known one without opening it.
    modified: int | None = None


def clean_rel(rel: str) -> str:
    """Normalize a root-relative path; refuse anything that could leave the root."""
    text = (rel or "").strip()
    if "\\" in text:
        raise StorageConfigError(f"storage paths use '/' separators, got {rel!r}")
    if text.startswith("/") or (len(text) > 1 and text[1] == ":"):
        raise StorageConfigError(f"storage paths are relative to the backend root, got {rel!r}")
    parts = [p for p in text.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise StorageConfigError(f"storage paths may not contain '..', got {rel!r}")
    return "/".join(parts)


def parent_rel(rel: str) -> str:
    return rel.rsplit("/", 1)[0] if "/" in rel else ""


class StorageBackend(ABC):
    """One root, five operations. ``scheme`` + ``root`` rebuild the URI."""

    scheme: str = ""
    root: str = ""

    def uri(self, rel: str = "") -> str:
        rel = clean_rel(rel)
        base = f"{self.scheme}:{self.root}"
        return f"{base.rstrip('/')}/{rel}" if rel else base

    @property
    def is_local(self) -> bool:
        return False

    @abstractmethod
    def list(self, rel: str = "") -> list[StorageEntry]:
        """Children of a directory, sorted by name; ``[]`` when it does not exist."""

    @abstractmethod
    def read_bytes(self, rel: str) -> bytes:
        """The file's bytes; ``StorageNotFound`` when absent."""

    @abstractmethod
    def write_bytes(self, rel: str, data: bytes) -> None:
        """Create / overwrite a file, creating missing directories BELOW the root."""

    @abstractmethod
    def exists(self, rel: str = "") -> bool:
        """A file or directory exists at the path ('' = the root itself)."""

    @abstractmethod
    def mkdir(self, rel: str) -> None:
        """Create the directory and its missing ancestors below the root.
        ``mkdir('')`` never creates anything: the root must already exist."""

    def delete_tree(self, rel: str) -> None:
        """Remove a file or a directory (recursively) BELOW the root; a path
        that does not exist is a no-op. The root itself is never deleted."""
        rel = clean_rel(rel)
        if not rel:
            raise StorageError(f"delete_tree refuses the root {self.uri()}")
        self._delete_tree(rel)

    def _delete_tree(self, rel: str) -> None:  # pragma: no cover - per backend
        raise StorageError(f"{self.scheme}: backends do not support delete")

    # -- helpers shared by every backend ---------------------------------

    def walk(self, rel: str = "", depth: int | None = None) -> list[tuple[str, StorageEntry]]:
        """Files under ``rel`` as ``(relative path, entry)``, depth-limited
        (``depth=0`` = the directory's own files, ``1`` = plus its immediate
        subdirectories', ``None`` = unlimited)."""
        rel = clean_rel(rel)
        found: list[tuple[str, StorageEntry]] = []
        for entry in self.list(rel):
            child = f"{rel}/{entry.name}" if rel else entry.name
            if entry.is_dir:
                if depth is None or depth > 0:
                    found.extend(self.walk(child, None if depth is None else depth - 1))
            else:
                found.append((child, entry))
        return found
