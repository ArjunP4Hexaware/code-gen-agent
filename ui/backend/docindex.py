"""The chooser's document index (M9.3) — content verdicts, computed OFF the
request path.

The list endpoints return listing metadata only (name, source, size,
modified): they never open — or download — a document. What needs a
document's CONTENT is computed once per file version by one background
worker and kept in the state role (``document_index.json``):

* a workbook's **kind** by content (``codegen.layout.classify``: sttm | vdd |
  unclassified) and every document's **pairing facts** (``codegen.pairing``:
  feed names, tables, schemas, file patterns, meta values), so choosing an STTM
  pairs from facts already read;
* each file within ``inputs.classify_timeout_seconds``. A file that exceeds it,
  cannot be downloaded or cannot be opened is recorded as **unreadable** with
  the reason — still listed, never retried in a loop (only when the listing
  shows a new size / modified, or a person asks: ``retry``).

Until its verdict exists a file's state is ``classifying``.
"""

from __future__ import annotations

import contextlib
import json
import queue
import threading
from collections.abc import Callable
from pathlib import Path

INDEX_FILE = "document_index.json"
CLASSIFYING = "classifying"
UNREADABLE = "unreadable"
_SUFFIX_KIND = {".docx": "frd", ".json": "frd"}


_fetch_locks: dict[str, threading.Lock] = {}
_fetch_locks_guard = threading.Lock()


def fetch_exclusive(doc) -> Path:
    """``doc.fetch()`` under a per-document lock: the background reader and a
    selection may want the same working copy at the same moment, and two
    writers of one file is a sharing violation (seen on Windows)."""
    with _fetch_locks_guard:
        lock = _fetch_locks.setdefault(doc.uri, threading.Lock())
    with lock:
        return doc.fetch()


class DocumentIndex:
    def __init__(self, get_config: Callable[[], object], state_path: Callable[[], Path],
                 push_state: Callable[[], None], base_dir: Path) -> None:
        self._get_config = get_config
        self._state_path = state_path
        self._push_state = push_state
        self._base_dir = base_dir
        self._lock = threading.Lock()
        self._entries: dict[str, dict] | None = None
        self._pending: set[str] = set()
        self._queue: queue.Queue = queue.Queue()
        self._worker: threading.Thread | None = None

    # -- state ------------------------------------------------------------------------

    def _load(self) -> dict[str, dict]:
        if self._entries is None:
            try:
                self._entries = json.loads(self._state_path().read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._entries = {}
        return self._entries

    def _save(self) -> None:
        with contextlib.suppress(Exception):      # a cache that cannot be written costs a re-read
            path = self._state_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                text = json.dumps(self._entries or {}, indent=2, sort_keys=True) + "\n"
            path.write_text(text, encoding="utf-8", newline="\n")
            self._push_state()

    # -- the request path: never blocks, never opens a document ------------------------

    def lookup(self, doc) -> dict:
        """``{state, reason}`` for a listed document — from the index, else
        ``classifying`` (and the file is queued, once)."""
        key = doc.version
        with self._lock:
            entry = self._load().get(key)
            if entry is not None:
                return {"state": entry["state"], "reason": entry.get("reason", "")}
            if key not in self._pending:
                self._pending.add(key)
                self._queue.put(doc)
                self._ensure_worker()
        return {"state": CLASSIFYING, "reason": "reading the document in the background"}

    def facts(self, doc):
        """The document's pairing facts when the index has them, else None."""
        from codegen.pairing import facts_from_dict

        with self._lock:
            entry = self._load().get(doc.version)
        if entry is None or not entry.get("facts"):
            return None
        return facts_from_dict(entry["facts"])

    def retry(self, doc) -> None:
        """A person asked: forget the verdict and read the file again (once)."""
        with self._lock:
            self._load().pop(doc.version, None)
        self.lookup(doc)

    def record(self, doc, local: Path) -> None:
        """A document the request path has just downloaded anyway (a selection):
        index it from the working copy so it is not read twice."""
        with self._lock:
            known = doc.version in self._load()
        if not known:
            self._store(doc, self._read(doc, local))

    def wait_idle(self, timeout: float = 30.0) -> bool:
        """Tests: block until the queue is drained (True) or ``timeout``."""
        done = threading.Event()

        def waiter() -> None:
            self._queue.join()
            done.set()

        threading.Thread(target=waiter, daemon=True).start()
        return done.wait(timeout)

    # -- the worker ----------------------------------------------------------------------

    def _ensure_worker(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._run, name="document-index", daemon=True)
            self._worker.start()

    def _run(self) -> None:
        while True:
            try:
                doc = self._queue.get(timeout=5.0)
            except queue.Empty:
                return                                  # idle: the next lookup restarts it
            try:
                self._store(doc, self._bounded(doc))
            finally:
                with self._lock:
                    self._pending.discard(doc.version)
                self._queue.task_done()

    def _bounded(self, doc) -> dict:
        """Download + read ONE document within the per-file timeout. The job
        runs in its own daemon thread: a download that hangs is abandoned (its
        result, should it ever arrive, is dropped), never waited for."""
        timeout = float(self._get_config().inputs.classify_timeout_seconds)
        result: dict = {}

        def job() -> None:
            try:
                result.update(self._read(doc, fetch_exclusive(doc)))
            except Exception as exc:  # noqa: BLE001 — every failure is a listed state
                result.update({"state": UNREADABLE,
                               "reason": f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
                               if str(exc) else type(exc).__name__})

        thread = threading.Thread(target=job, name=f"document-index:{doc.name}", daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            return {"state": UNREADABLE,
                    "reason": f"not read within {timeout:g}s (download / open timed out); "
                              "choose Retry to read it again"}
        return dict(result)

    def _read(self, doc, local: Path) -> dict:
        from codegen.layout.classify import classify_workbook
        from codegen.pairing import document_facts, facts_to_dict

        config = self._get_config()
        suffix = Path(doc.name).suffix.lower()
        if suffix == ".xlsx":
            verdict = classify_workbook(local, config.extractor)
            if verdict.reason.startswith("could not be read"):
                return {"state": UNREADABLE, "reason": verdict.reason}
            state, reason = verdict.kind, verdict.reason
        else:
            state, reason = _SUFFIX_KIND.get(suffix, "unclassified"), "an FRD document / contract"
        facts = None
        if state in ("sttm", "vdd", "frd"):
            with contextlib.suppress(Exception):      # facts are an optimisation, never a state
                facts = facts_to_dict(document_facts(state, local, config, self._base_dir))
        return {"state": state, "reason": reason, "facts": facts}

    def _store(self, doc, entry: dict) -> None:
        with self._lock:
            entries = self._load()
            for stale in [k for k in entries if k.split("#", 1)[0] == doc.uri]:
                del entries[stale]                     # one verdict per file
            entries[doc.version] = {"name": doc.name, **entry}
        self._save()


__all__ = ["CLASSIFYING", "INDEX_FILE", "UNREADABLE", "DocumentIndex", "fetch_exclusive"]
