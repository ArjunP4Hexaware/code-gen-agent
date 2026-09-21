"""Input discovery over storage backends (M8.1 / M8.2).

An ``InputCatalog`` is an ordered list of sources — (display label, role
store, folder, scan depth) — and answers "which documents can a run use".
The first source that holds a file name wins (the pre-M8 rule). A chosen
document is ``fetch``ed to a local working copy before anything reads it;
for a local source that IS the file itself, so paths, selections and every
existing comparison stay what they were.

Listings of remote sources are cached for ``ttl_seconds`` — the chooser
polls, and each remote listing is an API call. With ``timeout_seconds`` a
remote listing is WAITED FOR that long at most: a root that does not answer is
reported (``errors``) and its last known listing served, the call left to
finish in the background — a caller (a request) never hangs on a listing, and a
second caller joins the listing in flight instead of starting another.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

from codegen.storage import LocalBackend, RoleStore, StorageError


@dataclass(frozen=True)
class InputSource:
    label: str
    store: RoleStore
    folder: str = ""
    depth: int = 0


@dataclass(frozen=True)
class InputDocument:
    name: str
    source: str             # display label, e.g. "inputs/uploads", "pairs/pair_1"
    store: RoleStore
    rel: str                # path inside the store
    size: int | None = None
    modified: int | None = None     # epoch ms, when the backend lists it (M9.3)

    @property
    def version(self) -> str:
        """Where the file lives + the listed size / modified — the identity a
        cached verdict about its CONTENT is keyed by (no I/O)."""
        return f"{self.uri}#{self.size}:{self.modified}"

    @property
    def uri(self) -> str:
        return self.store.uri(self.rel)

    def local_path(self) -> Path:
        """Where the working copy lives (no I/O)."""
        return self.store.local_path(self.rel)

    def fetch(self) -> Path:
        return self.store.fetch(self.rel, self.size)


def local_source(label: str, directory: Path, depth: int = 0) -> InputSource:
    """A plain directory as a source; listing a missing one is just empty."""
    directory = Path(directory)
    return InputSource(label, RoleStore("inputs", LocalBackend(directory), directory), "", depth)


class InputCatalog:
    def __init__(self, sources: list[InputSource], ttl_seconds: float = 0.0,
                 timeout_seconds: float | None = None):
        self.sources = list(sources)
        self._ttl = ttl_seconds
        self._timeout = timeout_seconds
        self._cache: dict[int, tuple[float, list[InputDocument]]] = {}
        self._walks: dict[int, tuple[threading.Thread, dict]] = {}
        self._guard = threading.Lock()
        self.errors: dict[str, str] = {}     # label -> last listing failure (shown, not raised)

    def _walk(self, index: int, source: InputSource):
        """The backend listing; a remote one bounded by ``timeout_seconds``."""
        if source.store.is_local or not self._timeout:
            return source.store.backend.walk(source.folder, source.depth)
        with self._guard:
            flight = self._walks.get(index)
            if flight is None or not flight[0].is_alive():
                box: dict = {}

                def call() -> None:
                    try:
                        box["found"] = source.store.backend.walk(source.folder, source.depth)
                    except BaseException as exc:  # noqa: BLE001 — re-raised by the caller
                        box["error"] = exc

                flight = (threading.Thread(target=call, name=f"listing:{source.label}",
                                           daemon=True), box)
                self._walks[index] = flight
                flight[0].start()
        thread, box = flight
        thread.join(self._timeout)
        if thread.is_alive():
            raise TimeoutError(f"listing {source.store.uri(source.folder)} did not answer "
                               f"within {self._timeout:g}s")
        if "error" in box:
            raise box["error"]
        return box["found"]

    def _listing(self, index: int, source: InputSource) -> list[InputDocument]:
        cached = self._cache.get(index)
        if cached and not source.store.is_local and time.monotonic() - cached[0] < self._ttl:
            return cached[1]
        try:
            found = self._walk(index, source)
            self.errors.pop(source.label, None)
        except TimeoutError as exc:
            # Say so, and keep serving what was last known (never an empty chooser
            # because one call is slow); the next caller joins the call in flight.
            self.errors[source.label] = str(exc)
            return cached[1] if cached else []
        except StorageError as exc:
            # One unreachable root must not empty the chooser: say so, carry on.
            self.errors[source.label] = str(exc)
            found = []
        documents = []
        for rel, entry in found:
            inner = rel[len(source.folder):].lstrip("/") if source.folder else rel
            sub = inner.rsplit("/", 1)[0] if "/" in inner else ""
            documents.append(InputDocument(
                name=rel.rsplit("/", 1)[-1],
                source=f"{source.label}/{sub}" if sub else source.label,
                store=source.store, rel=rel, size=entry.size,
                modified=getattr(entry, "modified", None)))
        self._cache[index] = (time.monotonic(), documents)
        return documents

    def refresh(self) -> None:
        self._cache.clear()

    def documents(self, suffixes: tuple[str, ...]) -> list[InputDocument]:
        """Every document with one of the suffixes, first source wins per
        name, Office lock files (``~$…``) skipped; source order, then name."""
        seen: set[str] = set()
        out: list[InputDocument] = []
        for index, source in enumerate(self.sources):
            for doc in sorted(self._listing(index, source), key=lambda d: (d.source, d.name)):
                lower = doc.name.lower()
                if doc.name.startswith("~$") or not lower.endswith(suffixes) or doc.name in seen:
                    continue
                seen.add(doc.name)
                out.append(doc)
        return out

    def find(self, name: str, suffixes: tuple[str, ...]) -> InputDocument | None:
        return next((d for d in self.documents(suffixes) if d.name == name), None)
