"""Input discovery over storage backends (M8.1 / M8.2).

An ``InputCatalog`` is an ordered list of sources — (display label, role
store, folder, scan depth) — and answers "which documents can a run use".
The first source that holds a file name wins (the pre-M8 rule). A chosen
document is ``fetch``ed to a local working copy before anything reads it;
for a local source that IS the file itself, so paths, selections and every
existing comparison stay what they were.

Listings of remote sources are cached for ``ttl_seconds`` — the chooser
polls, and each remote listing is an API call.
"""

from __future__ import annotations

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

    @property
    def uri(self) -> str:
        return self.store.uri(self.rel)

    def local_path(self) -> Path:
        """Where the working copy lives (no I/O)."""
        return self.store.local_path(self.rel)

    def fetch(self) -> Path:
        return self.store.fetch(self.rel)


def local_source(label: str, directory: Path, depth: int = 0) -> InputSource:
    """A plain directory as a source; listing a missing one is just empty."""
    directory = Path(directory)
    return InputSource(label, RoleStore("inputs", LocalBackend(directory), directory), "", depth)


class InputCatalog:
    def __init__(self, sources: list[InputSource], ttl_seconds: float = 0.0):
        self.sources = list(sources)
        self._ttl = ttl_seconds
        self._cache: dict[int, tuple[float, list[InputDocument]]] = {}
        self.errors: dict[str, str] = {}     # label -> last listing failure (shown, not raised)

    def _listing(self, index: int, source: InputSource) -> list[InputDocument]:
        cached = self._cache.get(index)
        if cached and not source.store.is_local and time.monotonic() - cached[0] < self._ttl:
            return cached[1]
        try:
            found = source.store.backend.walk(source.folder, source.depth)
            self.errors.pop(source.label, None)
        except StorageError as exc:
            # One unreachable root must not empty the chooser: say so, carry on.
            self.errors[source.label] = str(exc)
            found = []
        documents = []
        for rel, _entry in found:
            inner = rel[len(source.folder):].lstrip("/") if source.folder else rel
            sub = inner.rsplit("/", 1)[0] if "/" in inner else ""
            documents.append(InputDocument(
                name=rel.rsplit("/", 1)[-1],
                source=f"{source.label}/{sub}" if sub else source.label,
                store=source.store, rel=rel))
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
