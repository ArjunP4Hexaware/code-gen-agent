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

**Documents are opened in a CHILD PROCESS** (``codegen.layout.docworker``,
APP_CHOOSER_BUG): parsing a workbook is CPU- / memory-bound work of unknown
size, a thread cannot be stopped, and a runaway parse inside the App starved
every endpoint until a restart. ``ParserProcess`` answers one document at a
time and is KILLED when a file exceeds its budget. Downloads stay in threads
(a stuck socket idles; it does not starve anyone).

**M12: when the child cannot start, documents are parsed IN-PROCESS.** On
serverless compute the child never starts, and in the v0.7.2 App run it never
said "ready": every selection's classify step waited out its whole budget.
Whether the child can start is now asked ONCE per process
(``inputs.parser_probe_seconds``, in the background at App start); when it
cannot, ``docworker.read_document`` runs in a worker thread of this process
with the same per-file timeout, the same used-range loader and the same cell
cap — one read per lane at a time, a late one abandoned (``timed_out``) and
holding its lane until it ends. The status says so once: ``parser_mode``.
"""

from __future__ import annotations

import atexit
import contextlib
import hashlib
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path

INDEX_FILE = "document_index.json"
CLASSIFYING = "classifying"
UNREADABLE = "unreadable"


class ParserTimeout(TimeoutError):
    """The parser process did not answer in time and was stopped."""


class ParserStartError(RuntimeError):
    """The parser process did not start (no ``{"ready": true}`` in time)."""


# M12: parser modes. ``subprocess`` is the M9.3 design (a killable child);
# ``inprocess`` is the fallback for an environment where the child cannot start
# (serverless compute; the App runtime of the v0.7.2 run, where it never said
# "ready" and every classify waited out its budget). ``probing`` = not yet known.
PARSER_PROBING = "probing"
PARSER_SUBPROCESS = "subprocess"
PARSER_INPROCESS = "inprocess"


def worker_command(config, base_dir: Path) -> list[str]:
    """The child process's command line (tests replace it with one that hangs).
    The config travels as the JSON of the parent's IN-MEMORY object (by alias —
    that is what round-trips), in a temp file named by its hash."""
    blob = config.model_dump_json(by_alias=True)
    folder = Path(tempfile.gettempdir()) / "codegen-docworker"
    path = folder / f"{hashlib.sha256(blob.encode('utf-8')).hexdigest()[:24]}.json"
    if not path.is_file():
        folder.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{threading.get_ident()}.part")
        tmp.write_text(blob, encoding="utf-8")
        tmp.replace(path)
    return [sys.executable, "-m", "codegen.layout.docworker", "--config-json", str(path),
            "--base-dir", str(base_dir)]


class ParserProcess:
    """One ``codegen.layout.docworker`` child: a request line in, an answer
    line out, killed (and restarted on the next request) when it is late. Its
    START (interpreter + imports, ``{"ready": true}``) has its own budget."""

    def __init__(self, command: list[str], cwd: Path, start_timeout: float = 60.0) -> None:
        self._command = command
        self._cwd = cwd
        self.start_timeout = start_timeout
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._lines: queue.Queue = queue.Queue()
        self.kills = 0
        self.used = time.monotonic()

    def _start(self) -> subprocess.Popen:
        proc = subprocess.Popen(  # noqa: S603 — our own interpreter, a fixed module
            self._command, cwd=self._cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
        lines: queue.Queue = queue.Queue()

        def pump() -> None:
            with contextlib.suppress(Exception):
                for line in proc.stdout:                 # type: ignore[union-attr]
                    lines.put(line)
            lines.put(None)                              # EOF: the process is gone

        threading.Thread(target=pump, name="document-parser-out", daemon=True).start()
        self._proc, self._lines = proc, lines
        try:
            hello = lines.get(timeout=self.start_timeout)
        except queue.Empty:
            hello = None
        try:
            ready = hello is not None and bool(json.loads(hello).get("ready"))
        except (ValueError, AttributeError):
            ready = False                                # not our protocol: not started
        if not ready:
            self.stop()
            raise ParserStartError("the document parser process did not start "
                                   f"(not ready within {self.start_timeout:g}s)")
        return proc

    def ensure(self) -> None:
        """Start the child when it is not running (its own budget — a file's
        time budget never pays for an interpreter start)."""
        with self._lock:
            if not self.alive:
                self._start()

    def parse(self, local: Path, name: str, timeout: float) -> dict:
        with self._lock:
            self.used = time.monotonic()
            proc = self._proc if self.alive else self._start()
            assert proc is not None
            while not self._lines.empty():               # nothing stale answers THIS request
                self._lines.get_nowait()
            try:
                proc.stdin.write(json.dumps({"path": str(local), "name": name}) + "\n")  # type: ignore[union-attr]
                proc.stdin.flush()                                                       # type: ignore[union-attr]
                line = self._lines.get(timeout=max(timeout, 0.05))
            except queue.Empty:
                self.stop()
                raise ParserTimeout(f"the document was not read within {timeout:g}s — the "
                                    "parser process was stopped") from None
            except OSError as exc:
                self.stop()
                raise RuntimeError(f"the document parser could not be reached: {exc}") from exc
            if line is None:
                self.stop()
                raise RuntimeError("the document parser exited while reading the document")
            return json.loads(line)

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            self.kills += 1
            with contextlib.suppress(Exception):
                proc.kill()
                proc.wait(timeout=5)

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None


# One parser per (command, lane): every runner of a process shares them (a test
# suite builds dozens of runners; an interpreter start costs a second or two).
# Lanes: "background" (the index task) and "request" (a selection job) — a
# selection never queues behind the background reader. At most ``_MAX_PARSERS``
# children exist; the least recently used one is stopped for a new config.
_parsers: dict[tuple, ParserProcess] = {}
_parsers_guard = threading.Lock()
_MAX_PARSERS = 4


def parser_for(command: list[str], cwd: Path, lane: str,
               start_timeout: float = 60.0) -> ParserProcess:
    with _parsers_guard:
        key = (tuple(command), str(cwd), lane)
        if key not in _parsers:
            while len(_parsers) >= _MAX_PARSERS:
                oldest = min(_parsers, key=lambda k: _parsers[k].used)
                _parsers.pop(oldest).stop()
            _parsers[key] = ParserProcess(command, cwd, start_timeout)
        _parsers[key].start_timeout = start_timeout
        return _parsers[key]


@atexit.register
def _stop_parsers() -> None:
    for parser in list(_parsers.values()):
        parser.stop()


# M12: can the child start HERE? Asked once per (command, cwd) per process —
# every runner shares the answer, as they share the children.
_modes: dict[tuple, dict] = {}
_modes_guard = threading.Lock()
# In-process reads, one at a time per lane (the subprocess lanes' semantics):
# a thread cannot be killed, so a read that outlives its budget is abandoned
# and HOLDS its lane until it ends — the next read waits within its own budget
# rather than piling a second runaway parse onto the same CPU.
_inprocess_lanes: dict[str, threading.Lock] = {"background": threading.Lock(),
                                               "request": threading.Lock()}


def _probe_parser(entry: dict, command: list[str], cwd: Path, timeout: float,
                  start_timeout: float) -> None:
    try:
        parser = parser_for(command, cwd, "request", timeout)
        parser.ensure()
        parser.start_timeout = start_timeout            # back to the per-start budget
        entry.update(mode=PARSER_SUBPROCESS, reason="")
    except Exception as exc:  # noqa: BLE001 — any failure to start means: not here
        entry.update(mode=PARSER_INPROCESS,
                     reason=(f"{str(exc) or type(exc).__name__} — documents are parsed "
                             "in-process (a worker thread, the same per-file timeout)"))
    finally:
        entry["done"].set()


def _demote(entry: dict, reason: str) -> None:
    """A child that started once and cannot start again: in-process from now on."""
    with _modes_guard:
        entry.update(mode=PARSER_INPROCESS,
                     reason=f"{reason} — documents are parsed in-process from now on")
        entry["done"].set()


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
        # Documents the REQUEST path had to read itself (tests: a selection
        # reads its own folder's documents, never the whole input tree).
        self.request_parses: list[str] = []
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

    def read_now(self, doc, local: Path, timeout: float) -> dict:
        """A selection needs this document's verdict NOW: the indexed one, else
        read through the (killable) parser within ``timeout`` and indexed. A
        late parse is an ``unreadable`` entry (``timed_out``) — never a hung
        request. An indexed ``unreadable`` is read AGAIN: a person chose the
        file, and the earlier failure may have been the download's."""
        with self._lock:
            entry = self._load().get(doc.version)
        if entry is None or entry["state"] == UNREADABLE:
            self.request_parses.append(doc.name)
            entry = self._parse(doc, local, timeout, "request")
            self._store(doc, entry)
        return entry

    def _parser(self, lane: str) -> ParserProcess:
        config = self._get_config()
        return parser_for(worker_command(config, self._base_dir), self._base_dir, lane,
                          float(config.inputs.parser_start_timeout_seconds))

    # -- M12: the parser mode --------------------------------------------------------

    def _mode_entry(self) -> dict:
        """This process's answer to "can the parser child start?" — probed once
        (in the background, within ``inputs.parser_probe_seconds``)."""
        config = self._get_config()
        command = worker_command(config, self._base_dir)
        key = (tuple(command), str(self._base_dir))
        with _modes_guard:
            entry = _modes.get(key)
            if entry is None:
                entry = _modes[key] = {"mode": PARSER_PROBING, "reason": "",
                                       "done": threading.Event()}
                threading.Thread(
                    target=_probe_parser, name="document-parser-probe", daemon=True,
                    args=(entry, command, self._base_dir,
                          float(config.inputs.parser_probe_seconds),
                          float(config.inputs.parser_start_timeout_seconds))).start()
        return entry

    def start_probe(self) -> None:
        """App start: ask the question in the background (never waited for)."""
        self._mode_entry()

    def parser_mode(self, wait: float = 0.0) -> dict:
        """``{mode: probing | subprocess | inprocess, reason}`` — the status
        field. ``wait`` > 0 waits (at most that long) for a running probe."""
        entry = self._mode_entry()
        if wait > 0:
            entry["done"].wait(wait)
        return {"mode": entry["mode"], "reason": entry["reason"]}

    def _settled_mode(self, budget: float) -> tuple[str, dict]:
        """The mode a parse runs under: the probe's answer, waited for no longer
        than the probe's own budget or the caller's — whichever is shorter. A
        probe that has not answered by then is treated as ``inprocess`` for
        this read (never block on a parser that has not started)."""
        entry = self._mode_entry()
        probe = float(self._get_config().inputs.parser_probe_seconds)
        entry["done"].wait(max(min(budget, probe), 0.0))
        mode = entry["mode"]
        return (PARSER_INPROCESS if mode == PARSER_PROBING else mode), entry

    def ensure_parser(self, lane: str = "request") -> str:
        """Make the lane's parser ready: start the child in subprocess mode;
        nothing to start in-process. Returns the mode the next read runs under.
        A child that no longer starts demotes the process to ``inprocess``."""
        probe = float(self._get_config().inputs.parser_probe_seconds)
        mode, entry = self._settled_mode(probe)
        if mode == PARSER_INPROCESS:
            return mode
        try:
            self._parser(lane).ensure()
        except ParserStartError as exc:
            _demote(entry, str(exc))
            return PARSER_INPROCESS
        return mode

    def _parse(self, doc, local: Path, timeout: float, lane: str) -> dict:
        deadline = time.monotonic() + timeout
        mode, entry = self._settled_mode(timeout)
        if mode == PARSER_SUBPROCESS:
            try:
                return self._parser(lane).parse(local, doc.name,
                                                max(deadline - time.monotonic(), 0.05))
            except ParserStartError as exc:
                # It started once (the probe said so) and no longer does: the
                # rest of THIS read's budget goes to the in-process reader.
                _demote(entry, str(exc))
            except Exception as exc:  # noqa: BLE001 — every failure is a listed state
                return {"state": UNREADABLE, "facts": None,
                        "timed_out": isinstance(exc, ParserTimeout),
                        "reason": str(exc) or type(exc).__name__}
        return self._parse_inprocess(doc, local, max(deadline - time.monotonic(), 0.05), lane)

    def _parse_inprocess(self, doc, local: Path, timeout: float, lane: str) -> dict:
        """The docworker's own ``read_document`` in a worker thread of THIS
        process: the same verdict, the same used-range loader and cell cap, the
        same per-file budget. A read past its budget is abandoned (``timed_out``)
        — it keeps its lane until it ends, so runaway reads never stack."""
        from codegen.layout.docworker import read_document

        deadline = time.monotonic() + timeout
        lane_lock = _inprocess_lanes.setdefault(lane, threading.Lock())
        if not lane_lock.acquire(timeout=max(timeout, 0.05)):
            return {"state": UNREADABLE, "facts": None, "timed_out": True,
                    "reason": f"the document was not read within {timeout:g}s — an earlier "
                              "in-process read of this lane is still running"}
        config, base_dir = self._get_config(), self._base_dir
        box: dict = {}
        finished = threading.Event()

        def read() -> None:
            try:
                box["result"] = read_document(local, doc.name, config, base_dir)
            except Exception as exc:  # noqa: BLE001 — every failure is an answer
                box["result"] = {"state": UNREADABLE, "facts": None,
                                 "reason": (f"{type(exc).__name__}: "
                                            f"{str(exc).splitlines()[0][:300]}"
                                            if str(exc) else type(exc).__name__)}
            finally:
                finished.set()
                lane_lock.release()

        threading.Thread(target=read, name=f"document-parser-inprocess:{doc.name}",
                         daemon=True).start()
        if not finished.wait(max(deadline - time.monotonic(), 0.05)):
            return {"state": UNREADABLE, "facts": None, "timed_out": True,
                    "reason": f"the document was not read within {timeout:g}s (in-process "
                              "parser; the read was abandoned)"}
        return box["result"]

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
        """Download + read ONE document within the per-file timeout: the
        download in a daemon thread (a hung transfer is abandoned, never waited
        for), the read in the parser PROCESS (a runaway parse is killed)."""
        timeout = float(self._get_config().inputs.classify_timeout_seconds)
        deadline = time.monotonic() + timeout
        box: dict = {}

        def download() -> None:
            try:
                box["path"] = fetch_exclusive(doc)
            except Exception as exc:  # noqa: BLE001 — every failure is a listed state
                box["error"] = (f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
                                if str(exc) else type(exc).__name__)

        thread = threading.Thread(target=download, name=f"document-index:{doc.name}",
                                  daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            return {"state": UNREADABLE, "facts": None,
                    "reason": f"not read within {timeout:g}s (the download timed out); "
                              "choose Retry to read it again"}
        if "error" in box:
            return {"state": UNREADABLE, "facts": None, "reason": box["error"]}
        try:
            self.ensure_parser("background")            # its own budget, not this file's
        except Exception as exc:  # noqa: BLE001 — every failure is a listed state
            return {"state": UNREADABLE, "facts": None, "reason": str(exc)}
        return self._parse(doc, box["path"], max(deadline - time.monotonic(), 0.05),
                           "background")

    def _store(self, doc, entry: dict) -> None:
        with self._lock:
            entries = self._load()
            for stale in [k for k in entries if k.split("#", 1)[0] == doc.uri]:
                del entries[stale]                     # one verdict per file
            entries[doc.version] = {"name": doc.name, **entry}
        self._save()


__all__ = ["CLASSIFYING", "INDEX_FILE", "PARSER_INPROCESS", "PARSER_PROBING",
           "PARSER_SUBPROCESS", "UNREADABLE", "DocumentIndex", "ParserStartError",
           "fetch_exclusive"]
