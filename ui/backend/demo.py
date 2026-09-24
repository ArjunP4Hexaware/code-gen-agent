"""Live demo runner: the FULL pipeline with real Layer-2 reasoning.

extract-sttm on the demo workbook → resolve against the demo FRD →
per-feed generate with ``dry_run=False`` → gate. Runs on a background
thread so the UI can poll stage-level progress; a single-run guard rejects
concurrent live runs; any failure lands in ``state="failed"`` with the
error message and never crashes the server.

Isolation: every live run writes under ``out/demo_<timestamp>/`` — never
the default out/ tree and never the tracked replay fixtures.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from codegen.extract import extract_to_file
from codegen.output_modes import OUTPUT_OPTIONS, output_parts
from codegen.output_modes import notices as output_notices
from codegen.resolve.resolver import resolve_pair
from ui.backend.docindex import (
    CLASSIFYING,
    INDEX_FILE,
    UNREADABLE,
    DocumentIndex,
    fetch_exclusive,
)
from ui.backend.service import REPO_ROOT, STATE_DIR, FailedRun, FeedRun, GenerationStore

# State files under the default (local) state role — module constants so tests
# can point them elsewhere, like service.DECISIONS_PATH.
INDEX_PATH = STATE_DIR / INDEX_FILE
SELECTION_FILE = "selection.json"
SELECTION_PATH = STATE_DIR / SELECTION_FILE


class SelectionFailed(RuntimeError):
    """A chosen document could not be brought in (download / pairing /
    recording the choice failed). The selection is NOT made and nothing falls
    back to the config default: the message is the API response (4xx) and the
    status' ``selection_error`` (M9.3)."""


class SelectionInProgress(RuntimeError):
    """One document selection at a time — another one is still running."""


class StepTimeout(TimeoutError):
    """One step of a selection did not finish within its budget."""


# A step's own work is bounded by its deadline (a download thread that is
# abandoned, a parser process that is killed); the job waits this much longer
# for the step to come back before it gives the step up.
_STEP_GRACE_SECONDS = 2.0
# M15d.2: a workbook that LOOKS like a Vendor Data Dictionary by name — read
# early by the start-up warm-up, before its verdict exists.
_LIKELY_VDD = re.compile(r"vdd|data[ _-]?dictionary|dictionary", re.IGNORECASE)
log = logging.getLogger("codegen.ui.index")


class LiveRunInProgress(RuntimeError):
    """A live run is already in flight (surface as HTTP 409)."""


# Output selection as independent PARTS (what the UI toggles): exactly
# Notebook and Framework artefacts (codegen.output_modes). A retired value
# (both / rfc / all) from a saved state maps to both parts with a one-time
# notice, never an error.
OUTPUT_PARTS = OUTPUT_OPTIONS


def feeds_left_without_a_file(questions, contract) -> list[tuple[int, object]]:
    """FRD feeds whose 'which file feeds this table' question the person
    left unanswered (Proceed unresolved): ``[(index, feed)]``. The runner
    sets them aside as failed feeds — with the remedy — so the rest of the
    run proceeds; it never picks a file for them."""
    out: list[tuple[int, object]] = []
    for q in questions:
        key = q.key if hasattr(q, "key") else q.get("key", "")
        kind = q.kind if hasattr(q, "kind") else q.get("kind")
        match = re.fullmatch(r"feeds\[(\d+)\]\.file_name_patterns", key or "")
        if kind != "choice" or not match or contract is None:
            continue
        index = int(match.group(1))
        if index < len(contract.feeds) and not contract.feeds[index].file_name_patterns:
            out.append((index, contract.feeds[index]))
    return out


class DemoRunner:
    """One live run at a time; stage list is append-only per run."""

    def __init__(self, store: GenerationStore, work=None, *, index_warmup: bool = True) -> None:
        self._store = store
        self._work = work or self._execute  # injectable for tests
        # M15d.3: VDD candidates the last pairing scored by NAME only (the
        # index had not reached them); when the index stores one, the VDD
        # pairing is re-scored and the chip updated — deferred past a run in
        # progress (``_deferred_vdd_plan``), applied when it ends.
        self._vdd_watch: set[str] = set()
        self._repair_lock = threading.Lock()
        self._repair_busy = False
        self._repair_again = False
        self._deferred_vdd_plan: dict | None = None
        # M15d.2: the likely dictionaries the start-up warm-up queued; logged
        # once when all of them are indexed. ``_warmup_done`` is set when the
        # warm-up has queued everything (tests wait on it); ``_restored_folder``
        # is the folder selection.json named, kept first in the queue.
        self._vdd_warmup_pending: set[str] = set()
        self._warmup_done = threading.Event()
        self._restored_folder: str | None = None
        self._lock = threading.Lock()
        self.state: str = "idle"  # idle | running | needs_layout | done | failed
        # M2.5 layout resolution: while a run waits for the human to place
        # unresolved roles, ``layout_questions`` holds the question list
        # (grouped by document in the UI) and ``_layout_answers`` the reply.
        self.layout_questions: list[dict] = []
        self.layout_report: dict | None = None
        # Model advice for the pending questions (POST /api/demo/layout-advice):
        # {"provider": name, "advice": {key: {index, rationale}}}; reset when the
        # question set changes. Display + a pre-selection — never a value.
        self.layout_advice: dict | None = None
        # FRD fields taken from another document / the person's choice while
        # resolving the layout: [{field, title, value, source, cell}].
        self.layout_fills: list[dict] = []
        # M9.1 "re-resolve layout": the next layout resolution bypasses every
        # cached profile and overwrites the runtime entries (one shot — set
        # before a run, or from the needs_layout dialog).
        self.layout_refresh: bool = False
        self._layout_event = threading.Event()
        # What the current / last run did with a model, per stage (list of
        # codegen.reasoning.usage.StageUsage.as_dict — each carries its label).
        # Built from the providers the run actually used, never from config.
        self.model_usage: list[dict] = []
        self._layout_providers: list = []
        # "Clear past runs" in progress: a run must not start into it.
        self._clearing = False
        # Recording the selection (selection.json in the state role) happens
        # OFF the selection path: one background writer, the newest payload
        # wins. It used to be the job's last step, BEFORE the choice was
        # applied — a slow state-role write (Workspace API) kept the STTM
        # unselected, and Generate disabled, for up to the step budget.
        self._record_lock = threading.Lock()
        self._record_pending: tuple[dict, dict | None] | None = None
        self._record_busy = False
        self._record_idle = threading.Event()
        self._record_idle.set()
        self._layout_answers: dict | None = None
        self.stages: list[dict] = []
        self.error: str | None = None
        # Label of the most recent COMPLETED run, so the UI can restore its
        # results (via the past-live-run loader) from any later state.
        self.last_run_label: str | None = None
        # Feeds the last run set aside (no file, question unanswered): [{label, error}]
        self.set_aside: list[dict] = []
        # The operator's chosen STTM workbook. None = the config default.
        # In-memory only: a restart returns to config.demo.workbook.
        self.selected_workbook: Path | None = None
        # Output selection (parts, see OUTPUT_PARTS). None = the config
        # default; [] = nothing selected (Generate refused); in-memory only.
        self.output_parts: list[str] | None = None
        # The chosen FRD contract path. None = the demo golden (config.demo
        # .frd) — the pinned default that keeps the golden path byte-
        # identical. Set via /api/demo/frd (local file or a materialized
        # upstream contract); in-memory only.
        self.selected_frd: Path | None = None
        self.selected_frd_label: str | None = None
        # {"frd": name, "rule": pairing_map|ticket|name_stem} when the FRD was
        # selected automatically for the chosen STTM; None for a manual pick.
        self.frd_auto_paired: dict | None = None
        # M3: optional Vendor Data Dictionary (third input); None = no VDD.
        self.selected_vdd: Path | None = None
        # {"vdd": name, "rule": …} when choosing the STTM selected it; None manual.
        self.vdd_auto_paired: dict | None = None
        # M4/M5 generation options (None = the config default each): the
        # conventions profile, the IIG template version and the playbook
        # template. In-memory only, like the output mode.
        self.conventions_profile: str | None = None
        self.iig_template: str | None = None
        self.playbook_template: str | None = None
        # Structured hint for the failed-run card: when a feed-match
        # failure has a known companion FRD, the UI renders a one-click
        # "choose the pair" button from this. Never an auto-retry.
        self.error_hint: dict | None = None
        # M8.1: input catalogs (sources + cached remote listings), per kind.
        self._catalogs: dict[str, tuple] = {}
        # M8.2: the last content-pairing decision per kind ("frd" / "vdd").
        self.pair_decisions: dict = {}
        # M9.3: the last selection that FAILED — {kind, name, message}. While
        # set (and no STTM is chosen) a run is refused — never a silent fall
        # back to the config default; cleared by the next successful selection
        # or a Clear.
        self.selection_error: dict | None = None
        # M9.3: what choosing the STTM paired (or asks), per kind — returned by
        # the select call itself and kept on the status.
        self.last_pairing: dict = {}
        # M9.3 addendum (APP_CHOOSER_BUG): choosing the STTM is a JOB — locate,
        # download, classify, pair, record, each step in its own thread with a
        # timeout. The POST returns the job at once, the status reports it, and
        # nothing is selected until every step has succeeded. ``_lock`` guards
        # state mutation only; no I/O ever happens under it.
        self.selection_job: dict | None = None
        self._job_seq = 0
        self._job_done = threading.Event()
        self._job_done.set()
        # M15.2: the job is DONE (the STTM applied, Generate enabled) as soon
        # as the workbook is classified; its FRD / VDD pairing lands behind it.
        # Clear while a pairing is on its way; a run started meanwhile waits.
        self._pairing_done = threading.Event()
        self._pairing_done.set()
        # Upstream contract listing (upstream.enabled only): refreshed in a
        # background task with a hard timeout; request paths read this snapshot.
        self._upstream: dict = {"state": "idle", "rows": [], "error": None, "at": 0.0}
        self._upstream_seq = 0
        # M9.3: content verdicts (workbook kind, pairing facts) computed in the
        # background, kept in the state role — the list endpoints never open a
        # document (ui/backend/docindex.py).
        self._index = DocumentIndex(
            lambda: self._store.config, self._index_path,
            lambda: self._push_state_file(INDEX_FILE), REPO_ROOT,
            local_path=self._index_local_path)
        self._index.add_listener(self._on_indexed)
        self._start_restore()
        if index_warmup:
            threading.Thread(target=self._index_warmup, name="index-warmup",
                             daemon=True).start()
        else:
            self._warmup_done.set()

    def _index_path(self) -> Path:
        """The index file, PULLED from a remote state role (the read after a restart)."""
        from ui.backend import stores as ui_stores

        return ui_stores.state_file(self._store.config, INDEX_FILE, INDEX_PATH)

    def _index_local_path(self) -> Path:
        """The index file's local path, no pull (the writer overwrites it whole)."""
        from ui.backend import stores as ui_stores

        return ui_stores.state_local_path(self._store.config, INDEX_FILE, INDEX_PATH)

    def _index_folder_first(self, source: str) -> None:
        """Queue the documents of ``source`` (a listing label — the folder of the
        STTM being selected, or of the one selection.json names at App start,
        M15b.7) for the background index and read them before anything else
        waiting (M15.8). A listing problem is reported elsewhere; never fatal."""
        try:
            docs = [*self._workbook_catalog().documents((".xlsx",)),
                    *self._frd_catalog().documents((".contract.json", ".docx"))]
        except Exception:  # noqa: BLE001 — status.input_errors carries it
            return
        for doc in docs:
            if doc.source == source:
                self._index.lookup(doc)
        self._index.prioritize(source)

    def _index_warmup(self) -> None:
        """M15d.2: at App start the background index reads, in this order, the
        folder selection.json names (the restore job queues it first), then
        every workbook the index already classified as a VDD or that looks
        like one by name, then everything else. Logged when all the likely
        dictionaries are indexed. Never on a request thread."""
        try:
            self._job_done.wait(float(self._store.config.inputs.select_timeout_seconds) * 4)
            try:
                workbooks = self._workbook_catalog().documents((".xlsx",))
                frds = self._frd_catalog().documents((".contract.json", ".docx"))
            except Exception:  # noqa: BLE001 — status.input_errors carries it
                return

            def likely_vdd(doc) -> bool:
                with self._index._lock:
                    entry = self._index._load().get(doc.version)
                return (entry["state"] == "vdd") if entry else bool(_LIKELY_VDD.search(doc.name))

            likely = [d for d in workbooks if likely_vdd(d)]
            pending = set()
            for doc in likely:
                if self._index.lookup(doc)["state"] == CLASSIFYING:
                    pending.add(doc.version)
            for doc in [*workbooks, *frds]:
                self._index.lookup(doc)
            self._vdd_warmup_pending = pending
            if pending:
                likely_versions = {d.version for d in likely}
                self._index.prioritize(select=lambda d: d.version in likely_versions)
                log.info("index warm-up: %d likely VDD candidate(s) queued first", len(pending))
            else:
                log.info("index warm-up: all %d VDD candidate(s) already indexed", len(likely))
            if self._restored_folder:
                self._index.prioritize(self._restored_folder)   # the recorded folder stays first
        finally:
            self._warmup_done.set()

    def _on_indexed(self, doc, entry: dict) -> None:
        """Index listener (off the request path): the warm-up log, and the VDD
        re-pairing when a name-only candidate just got its verdict (M15d.3)."""
        if self._vdd_warmup_pending:
            self._vdd_warmup_pending.discard(doc.version)
            if not self._vdd_warmup_pending:
                log.info("index warm-up: all VDD candidates indexed")
        if doc.name in self._vdd_watch and entry.get("state") != CLASSIFYING:
            with self._repair_lock:
                if self._repair_busy:
                    self._repair_again = True       # the running re-scoring goes once more
                    return
                self._repair_busy, self._repair_again = True, False
            threading.Thread(target=self._repair_vdd, name="repair-vdd", daemon=True).start()

    def _repair_vdd(self) -> None:
        """Re-score the VDD pairing from the index (no download, no parse) and
        apply it when a candidate now WINS over the name-only pick; never
        over a manual pick; deferred past a run in progress. Loops while
        verdicts kept landing during a pass."""
        while True:
            try:
                self._repair_vdd_once()
            except Exception as exc:  # noqa: BLE001 — a re-scoring never breaks anything
                log.warning("VDD re-scoring failed: %s: %s", type(exc).__name__, exc)
            with self._repair_lock:
                if not self._repair_again:
                    self._repair_busy = False
                    return
                self._repair_again = False

    def _repair_vdd_once(self) -> None:
        job = self.selection_job
        sttm = self.selected_workbook
        manual_vdd = self.selected_vdd is not None and self.vdd_auto_paired is None
        if job is None or job["kind"] != "sttm" or sttm is None or manual_vdd:
            return
        plan = self._plan_pair("vdd", sttm.name)
        chosen = plan["decision"].chosen
        current = (self.vdd_auto_paired or {}).get("vdd")
        with self._lock:
            if self.selection_job is not job:
                return
            self._vdd_watch = set(plan["outcome"].get("not_indexed", []))
            if chosen is None or chosen == current:
                return
            plan["outcome"]["upgraded_from"] = current
            if self.state == "running":
                self._deferred_vdd_plan = plan      # the run is not affected; the next one is
                return
            self._apply_pair("vdd", plan)
            job["pairing"]["vdd"] = plan["outcome"]
        log.info("VDD pairing re-scored: %s (was %s)", chosen, current)

    def _push_state_file(self, name: str) -> None:
        from ui.backend import stores as ui_stores

        ui_stores.push_state(self._store.config, name)

    def _fetch(self, doc, timeout: float | None = None) -> Path:
        """A selection's download, bounded by ``inputs.select_timeout_seconds``
        (a hung transfer is a StorageError, never a hung request)."""
        from codegen.storage import StorageError

        if timeout is None:
            timeout = float(self._store.config.inputs.select_timeout_seconds)
        box: dict = {}

        def job() -> None:
            try:
                box["path"] = fetch_exclusive(doc)
            except Exception as exc:  # noqa: BLE001 — re-raised on the request thread
                box["error"] = exc

        thread = threading.Thread(target=job, name=f"fetch:{doc.name}", daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            # An OSError like any failed download (callers catch those), and a
            # TIMEOUT on the selection job.
            raise StepTimeout(f"downloading {doc.uri} did not finish within {timeout:g}s")
        if "error" in box:
            raise box["error"]
        if not box["path"].is_file():
            raise StorageError(f"downloading {doc.uri} left no file at {box['path']}")
        return box["path"]

    def effective_frd(self) -> Path:
        return self.selected_frd or (
            REPO_ROOT / self._store.config.contracts.dir / self._store.config.demo.frd
        )

    def select_frd(self, path: Path, label: str) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the FRD while a live run is in progress"
                )
        self.selected_frd = path
        self.selected_frd_label = label
        self.frd_auto_paired = None

    def select_vdd(self, path: Path | None) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the VDD while a live run is in progress")
        self.selected_vdd = path
        self.vdd_auto_paired = None

    def clear_frd(self) -> None:
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the FRD while a live run is in progress"
                )
        self.selected_frd = None
        self.selected_frd_label = None
        self.frd_auto_paired = None

    def local_frd_candidates(self) -> dict[str, Path]:
        """FRDs a run can use without a network call: contract JSONs and
        FRD-named .docx in the contracts dir and the three inboxes (any .docx
        in the uploads inbox — only a kind=frd upload puts one there)."""
        from codegen.demo_sources import canonical_document_name

        found: dict[str, Path] = {}
        for doc in self._frd_catalog().documents((".contract.json", ".docx")):
            if doc.name.lower().endswith(".docx") and not (
                    doc.source == "inputs/uploads"
                    or canonical_document_name(doc.name).startswith("frd")):
                continue
            # The working-copy path; a remote document is downloaded when the
            # FRD is actually selected (``fetch_frd_candidate``). Listing queues
            # its pairing facts for the background index — it never opens it.
            if doc.name not in found:
                self._index.lookup(doc)
            found.setdefault(doc.name, doc.local_path())
        return found

    def fetch_frd_candidate(self, name: str) -> Path | None:
        """The named local FRD candidate as a file on disk (downloaded first
        when it lives in a remote input root); None when no source has it."""
        doc = self._frd_catalog().find(name, (".contract.json", ".docx"))
        return self._fetch(doc) if doc is not None else None

    def auto_pair_frd(self, sttm_name: str) -> dict | None:
        """Select the FRD associated with the chosen STTM when one is present
        (config pairing map -> shared ticket -> unique name stem). A manual
        FRD choice is replaced only when a pair is found; a stale automatic
        pair from a previous STTM is cleared."""
        self._apply_pair("frd", self._plan_pair("frd", sttm_name))
        return self.frd_auto_paired

    def _plan_pair(self, kind: str, sttm_name: str, deadline: float | None = None) -> dict:
        """The ``kind`` ("frd" | "vdd") companion of the chosen STTM — by
        CONTENT (codegen.pairing: explicit map, then what the documents say, the
        ticket number one signal among several). COMPUTES only — a plan
        ``_apply_pair`` records — so a step that is given up cannot change the
        selection later. No document is opened in this process: facts come from
        the index, else from the (killable) parser while the step's budget
        lasts; a candidate that is unreadable or not read in time scores on its
        name alone (``unread``)."""
        from dataclasses import replace

        from codegen.pairing import empty_facts, pair_by_content
        from codegen.storage import StorageError

        config = self._store.config
        if deadline is None:
            deadline = time.monotonic() + float(config.inputs.select_timeout_seconds)
        if kind == "frd":
            candidates = self.local_frd_candidates()
            explicit_map = config.demo.pairing_map
            catalog, suffixes = self._frd_catalog(), (".contract.json", ".docx")
        else:
            # By CONTENT — a workbook the index knows as an STTM is never a
            # dictionary candidate; one still classifying / unclassified /
            # unreadable stays a candidate.
            candidates = {doc.name: doc.local_path()
                          for doc in self._workbook_catalog().documents((".xlsx",))
                          if doc.name != sttm_name and self._index.lookup(doc)["state"] != "sttm"}
            explicit_map = config.demo.vdd_pairing_map
            catalog, suffixes = self._workbook_catalog(), (".xlsx",)
        sttm_doc = self._workbook_catalog().find(sttm_name, (".xlsx",))
        sttm_path = sttm_doc.local_path() if sttm_doc is not None else Path(sttm_name)
        docs = {name: catalog.find(name, suffixes) for name in candidates}
        sttm_facts = self._index.facts(sttm_doc) if sttm_doc is not None else None
        known = {sttm_name: sttm_facts if sttm_facts is not None else empty_facts()}
        unread: list[str] = []
        # M15d.1: VDD candidates the background index has not reached yet —
        # scored by NAME only, said so on the outcome, re-scored when indexed.
        not_indexed: list[str] = []
        # A workbook whose verdict -- once read, here or by the background index
        # meanwhile -- is "sttm" is never a dictionary: dropped in every scope
        # (a copy of the chosen STTM in the pair folder would otherwise score
        # a perfect content match and be chosen as the VDD).
        not_a_vdd: set[str] = set()
        # M9.3: the STTM's OWN folder first (…/pair_1/{FRD, STTM, VDD}); the
        # other input roots only when that folder holds no candidate.
        folder = sttm_doc.source if sttm_doc is not None else None
        in_folder = [n for n, d in docs.items() if d is not None and d.source == folder]
        scopes = ([("same_folder", in_folder)] if in_folder else []) + [("all", list(candidates))]
        # M15c: an explicit pairing_map entry decides WITHOUT reading anything
        # (``_plan_pair`` used to read every candidate first, then let
        # ``pair_by_content`` return the map's answer).
        from codegen.demo_sources import document_stem

        explicit = {document_stem(k): document_stem(v) for k, v in (explicit_map or {}).items()}
        by_stem = {document_stem(n): n for n in candidates}
        mapped = explicit.get(document_stem(sttm_name))
        if mapped in by_stem:
            scopes = [("pairing_map", [by_stem[mapped]])]
        decision, scope = None, "all"
        for scope, names in scopes:
            local: dict[str, Path] = {}
            for name in names:
                if name in not_a_vdd:
                    continue
                doc = docs[name]
                local[name] = doc.local_path() if doc is not None else candidates[name]
                if name in known:
                    continue
                facts = self._index.facts(doc) if doc is not None else None
                state = self._index.lookup(doc)["state"] if doc is not None else None
                # M15c: on the request path only the STTM's OWN folder and the
                # LOCAL sources are read. REMOTE roots outside the folder score
                # from indexed facts or names (``unread``) — a download + parse
                # of every workbook of every pair folder for an inbox STTM took
                # minutes, and the run waited for it; the background index
                # (folder-first) closes the gap behind the person.
                # M15d.1: a VDD candidate is NEVER downloaded or parsed on the
                # request path — the index's stored facts score it in memory.
                if (facts is None and doc is not None and state != UNREADABLE
                        and kind != "vdd"
                        and (scope == "same_folder" or doc.store.is_local)):
                    left = deadline - time.monotonic()
                    if left > 0:
                        try:
                            state = self._index.read_now(
                                doc, self._fetch(doc, left),
                                max(deadline - time.monotonic(), 0.05),
                                lane="request" if kind == "frd" else "request-vdd")["state"]
                        except StepTimeout:
                            # M15.5: not read IN TIME is not unreachable — the
                            # candidate stays, scored on its name (``unread``).
                            pass
                        except (StorageError, OSError):
                            del local[name]           # unreachable candidate: not a contender
                            continue
                        facts = self._index.facts(doc)
                if kind == "vdd" and state == "sttm":
                    not_a_vdd.add(name)               # it reads as a mapping workbook
                    del local[name]
                    continue
                if facts is None:
                    if kind == "vdd" and state == CLASSIFYING:
                        not_indexed.append(name)      # not reached yet: re-scored when it is
                    else:
                        unread.append(name)           # its NAME still speaks
                known[name] = facts if facts is not None else empty_facts()
            decision = pair_by_content(kind, sttm_path, local, config, REPO_ROOT,
                                       explicit_map=explicit_map, known_facts=known)
            nested = sttm_doc is not None and "/" in sttm_doc.rel
            if (decision.chosen is None and scope == "same_folder" and nested
                    and len(local) == 1):
                # A pair folder holding exactly ONE candidate of the kind: the
                # folder is the person's pairing, whatever the content score
                # (M15.4 — a weak score used to block this rescue). Never
                # applied to a flat inbox.
                (only,) = local
                decision = replace(
                    decision, chosen=only, rule="same_folder",
                    reason=f"the only {kind.upper()} in the STTM's folder {folder!r} "
                           f"(the content did not decide: {decision.reason})")
            if decision.chosen is not None or decision.ambiguous:
                break                        # decided, or a question among THESE candidates
        assert decision is not None
        path = None
        if decision.chosen is not None:
            doc = docs.get(decision.chosen)
            try:
                path = (self._fetch(doc, max(deadline - time.monotonic(), 0.05))
                        if doc is not None else candidates[decision.chosen])
            except (StorageError, OSError) as exc:
                # M15.5: chosen, but its file did not arrive in time — said on
                # the outcome (the candidate stays listed), nothing selected.
                decision = replace(
                    decision, chosen=None, rule=None,
                    reason=f"{decision.chosen} was chosen but could not be downloaded "
                           f"within the step's budget ({exc}); choose it again or pick it "
                           "in the chooser")
        outcome = {
            "chosen": decision.chosen, "rule": decision.rule, "reason": decision.reason,
            "scope": scope, "folder": folder,
            "candidates": [{"name": c.name, "score": c.score, "signals": c.summary()}
                           for c in decision.candidates],
            "question": decision.question() if decision.ambiguous else None,
            # Candidates scored on their NAME alone (unreadable / not read in time).
            "unread": sorted(set(unread) & {c.name for c in decision.candidates}),
            # M15d: VDD candidates the index has not reached yet (name-only for
            # now; the pairing is re-scored when they are indexed).
            "not_indexed": sorted(set(not_indexed) & {c.name for c in decision.candidates}),
        }
        return {"decision": decision, "outcome": outcome, "path": path}

    def _apply_pair(self, kind: str, plan: dict) -> None:
        """Record a pairing plan: a manual choice is replaced only when a pair
        was found; a stale automatic pair from a previous STTM is cleared."""
        decision = plan["decision"]
        self.pair_decisions[kind] = decision
        self.last_pairing[kind] = plan["outcome"]
        rule = decision.rule or "content"
        if kind == "vdd":
            # M15d.3: the candidates scored by name only — re-scored when indexed.
            self._vdd_watch = set(plan["outcome"].get("not_indexed", []))
        if decision.chosen is None:
            self._drop_auto_pair(kind)
            return
        if kind == "frd":
            self.selected_frd, self.selected_frd_label = plan["path"], decision.chosen
            self.frd_auto_paired = {"frd": decision.chosen, "rule": rule}
        else:
            self.selected_vdd = plan["path"]
            self.vdd_auto_paired = {"vdd": decision.chosen, "rule": rule}

    def _drop_auto_pair(self, kind: str) -> None:
        """Forget an AUTOMATIC pair (a manual pick stays). M15.3: called for the
        previous STTM's pairs the moment a new STTM is applied, and for a
        pairing step that returns nothing — an automatic pair from a prior
        STTM never survives a new selection."""
        if kind == "frd":
            if self.frd_auto_paired is not None:
                self.selected_frd = self.selected_frd_label = self.frd_auto_paired = None
        elif self.vdd_auto_paired is not None:
            self.selected_vdd = self.vdd_auto_paired = None

    def _ask_pairing(self) -> None:
        """Run start: an undecided pairing becomes a question in the layout
        dialog (top candidates with their scores and the cells behind them).
        A manual pick in the chooser always wins and is never asked about."""
        pending = []
        if self.selected_frd is None and "frd" in self.pair_decisions \
                and self.pair_decisions["frd"].ambiguous:
            pending.append(self.pair_decisions["frd"])
        if self.selected_vdd is None and "vdd" in self.pair_decisions \
                and self.pair_decisions["vdd"].ambiguous:
            pending.append(self.pair_decisions["vdd"])
        if not pending:
            return
        self.layout_questions = [d.question() for d in pending]
        self.layout_advice = None
        self._layout_answers = None
        self._layout_event.clear()
        self.state = "needs_layout"
        self._stage("needs pairing", "; ".join(d.reason for d in pending))
        self._layout_event.wait()
        self.state = "running"
        reply = self._layout_answers or {}
        self.layout_questions = []
        if reply.get("cancel"):
            raise RuntimeError("pairing cancelled by the user")
        gaps = (reply.get("answers") or {}).get("gaps") or {}
        for decision in pending:
            picked = (gaps.get(f"pair.{decision.kind}") or {}).get("value")
            if picked not in {c.name for c in decision.candidates}:
                if decision.kind == "frd":
                    raise RuntimeError(
                        f"no FRD chosen for {decision.sttm}: {decision.reason}. Choose the "
                        "FRD in the document chooser (or answer the question) and run again "
                        "— the agent never guesses a pair.")
                continue                                   # a VDD is optional
            if decision.kind == "frd":
                self.selected_frd = self.fetch_frd_candidate(picked)
                self.selected_frd_label = picked
                self.frd_auto_paired = None                # the person chose
            else:
                doc = self._workbook_catalog().find(picked, (".xlsx",))
                self.selected_vdd = doc.fetch() if doc is not None else None
                self.vdd_auto_paired = None
            self._stage("paired", f"{decision.kind.upper()}: {picked} (chosen by the user)")

    def auto_pair_vdd(self, sttm_name: str) -> dict | None:
        """Select the Vendor Data Dictionary associated with the chosen STTM
        when one is present among the listed workbooks (config vdd_pairing_map
        -> shared ticket -> unique name stem); same override rules as the FRD."""
        self._apply_pair("vdd", self._plan_pair("vdd", sttm_name))
        return self.vdd_auto_paired

    @property
    def output_mode(self) -> list[str] | None:
        """The selected parts as the generator takes them; None = config
        default when nothing was selected, also None when the selection is
        empty (callers refuse a run in that case)."""
        if not self.output_parts:
            return None
        return list(self.output_parts)

    def effective_output_parts(self) -> list[str]:
        if self.output_parts is not None:
            return list(self.output_parts)
        return output_parts(self._store.config.output.mode, source="config output.mode")

    def select_output_mode(self, mode: str | None) -> None:
        """Compatibility entry: a single mode selects its parts."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output mode while a live run is in progress"
                )
        # A retired mode maps (with a notice); an unknown one is a ValueError.
        self.output_parts = (None if mode is None
                             else output_parts(mode, source="output-mode request"))

    def select_output_parts(self, parts: list[str] | None) -> None:
        """The UI's toggles: any subset of OUTPUT_PARTS, empty allowed
        (Generate is refused until one is chosen); None = config default."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output while a live run is in progress"
                )
        if parts is None:
            self.output_parts = None
            return
        self.output_parts = output_parts(parts, source="output-parts request")

    def select_generation_options(self, *, conventions_profile: str | None = None,
                                  iig_template: str | None = None,
                                  playbook_template: str | None = None) -> None:
        """Validate against the config and record the choice (None = default)."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change generation options while a live run is in progress")
        config = self._store.config
        config.conventions.get(conventions_profile)      # raises ValueError when unknown
        config.metadata.resolve(iig_template)
        config.playbook.resolve(playbook_template)
        self.conventions_profile = conventions_profile
        self.iig_template = iig_template
        self.playbook_template = playbook_template

    def generation_options(self) -> dict:
        """What the selectors offer + what is selected (None = config default)."""
        config = self._store.config
        return {
            "conventions_profile": {
                "options": sorted(config.conventions.profiles),
                "default": config.conventions.profile,
                "selected": self.conventions_profile,
            },
            "iig_template": {
                "options": ["iig_v1", *sorted(config.metadata.templates)],
                "default": config.metadata.template,
                "selected": self.iig_template,
            },
            "playbook_template": {
                "options": sorted(config.playbook.templates),
                "default": config.playbook.template,
                "selected": self.playbook_template,
            },
        }

    # -- STTM workbook choice ------------------------------------------------

    def _workbook_dirs(self) -> tuple[tuple[str, Path], ...]:
        """Directories a live run's STTM may come from, with display labels.

        The config workbook's own directory, plus the SharePoint landing dir
        (where ``sharepoint-fetch --dest`` and the UI picker deliver files).
        """
        configured = REPO_ROOT / self._store.config.demo.workbook
        try:                      # an absolute demo.workbook is outside the repo
            label = configured.parent.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            label = configured.parent.as_posix()
        return (
            (label, configured.parent),
            ("inputs/sharepoint", REPO_ROOT / "inputs" / "sharepoint"),
            # Where `codegen databricks-fetch` and the UI's volume fetch land
            # documents — same treatment as the SharePoint inbox.
            ("inputs/databricks", REPO_ROOT / "inputs" / "databricks"),
            # Where the UI's from-device upload (POST /api/demo/upload) lands
            # documents — same treatment as the other two inboxes.
            ("inputs/uploads", REPO_ROOT / "inputs" / "uploads"),
        )

    def _input_sources(self, first: tuple[str, Path]):
        """``first`` (a repo directory), the three inboxes of the inputs role,
        then every extra input root at the configured scan depth."""
        from codegen.storage.catalog import InputSource, local_source
        from ui.backend import stores as ui_stores

        config = self._store.config
        stores = ui_stores.get_stores(config)
        sources = [local_source(*first)]
        for sub in ("sharepoint", "databricks", "uploads"):
            default = REPO_ROOT / "inputs" / sub
            if ui_stores.inbox_dir(config, sub, default) == default:
                sources.append(local_source(f"inputs/{sub}", default))
            else:
                sources.append(InputSource(f"inputs/{sub}", stores.inputs, sub, 0))
        for extra in stores.extra_inputs:
            label = extra.backend.root.rstrip("/").rsplit("/", 1)[-1] or extra.uri()
            sources.append(InputSource(label, extra, "", config.inputs.scan_depth))
        return sources

    def _catalog(self, key: str, first: tuple[str, Path]):
        from codegen.storage.catalog import InputCatalog

        cached = self._catalogs.get(key)
        if cached is None or cached[0] is not self._store.config:
            config = self._store.config
            cached = (config, InputCatalog(
                self._input_sources(first), ttl_seconds=config.inputs.listing_ttl_seconds,
                timeout_seconds=config.inputs.listing_timeout_seconds))
            self._catalogs[key] = cached
        return cached[1]

    def _workbook_catalog(self):
        label, directory = self._workbook_dirs()[0]
        return self._catalog("workbooks", (label, directory))

    def _frd_catalog(self):
        contracts_dir = REPO_ROOT / self._store.config.contracts.dir
        return self._catalog("frds", (self._store.config.contracts.dir, contracts_dir))

    def refresh_inputs(self) -> None:
        """Drop cached remote listings (after an upload / a fetch)."""
        for _config, catalog in self._catalogs.values():
            catalog.refresh()

    def input_errors(self) -> dict[str, str]:
        """Input roots whose last listing failed: label -> message."""
        errors: dict[str, str] = {}
        for _config, catalog in self._catalogs.values():
            errors.update(catalog.errors)
        return errors

    def effective_workbook(self) -> Path:
        return self.selected_workbook or (REPO_ROOT / self._store.config.demo.workbook)

    def workbook_choices(self) -> list[dict]:
        """Every .xlsx a live run could consume, flagged with the selection.

        Only an EXPLICIT pick counts as selected — before one, the UI shows
        "none chosen" and no row is badged, even though a run would fall
        back to the config default.

        M9.3: listing METADATA only (name, source, size, modified) — bounded
        time, no workbook is downloaded or opened here. ``kind`` is the
        background index's verdict by content (sttm | vdd | unclassified),
        ``classifying`` until it exists, ``unreadable`` (with the reason) for a
        file that failed or timed out — listed all the same, never retried in a
        loop.
        """
        chosen = self.selection()
        choices = []
        for doc in self._workbook_catalog().documents((".xlsx",)):
            verdict = self._index.lookup(doc)
            choices.append({"name": doc.name, "source": doc.source, "size": doc.size,
                            "modified": doc.modified,
                            # The SAME record the status reports (``selection``).
                            "selected": doc.name == chosen["sttm"],
                            "selected_as": next((k for k in ("sttm", "vdd")
                                                 if chosen[k] == doc.name), None),
                            "kind": verdict["state"], "kind_reason": verdict["reason"]})
        return choices

    def reclassify_workbook(self, name: str) -> None:
        """A person asked for an ``unreadable`` workbook to be read again."""
        doc = self._workbook_catalog().find(name, (".xlsx",))
        if doc is None:
            raise FileNotFoundError(f"no workbook named {name!r} in the input folders")
        self._index.retry(doc)

    # -- selection: succeed, or say why (M9.3) ---------------------------------

    def _fail_selection(self, kind: str, name: str, exc: Exception, step: str) -> SelectionFailed:
        message = (f"{kind.upper()} {name!r} was NOT selected — {step} failed: "
                   f"{type(exc).__name__}: {exc}")
        self.selection_error = {"kind": kind, "name": name, "message": message}
        return SelectionFailed(message)

    def selection(self) -> dict:
        """THE record of what is selected — the status, the workbook list's
        ``selected`` flag and ``selection.json`` all read it (on site the list
        and the chooser disagreed: two derivations of one fact). Names, or None
        = not chosen."""
        return {"sttm": self.selected_workbook.name if self.selected_workbook else None,
                "frd": self.selected_frd_label if self.selected_frd else None,
                "vdd": self.selected_vdd.name if self.selected_vdd else None}

    def _persist_selection(self, payload: dict | None = None) -> None:
        """Record the chosen documents in the state role (a REMOTE one only: an
        App container restart otherwise returns to 'none chosen' while the
        person believes the pair is set). Raises on failure — the caller turns
        that into a failed selection."""
        from ui.backend import stores as ui_stores

        if ui_stores.state_is_default(self._store.config):
            return
        # No pull before the write (M15.1): the file is overwritten whole.
        path = ui_stores.state_local_path(self._store.config, SELECTION_FILE, SELECTION_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = payload if payload is not None else self.selection()
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
        ui_stores.push_state(self._store.config, SELECTION_FILE)

    def _record_later(self, payload: dict | None = None, job: dict | None = None) -> None:
        """Record ``payload`` (default: the selection now) in the state role in
        the background; never blocks the caller. A failure or a timeout is a
        ``record`` warning on ``job`` — the choice stands either way."""
        from ui.backend import stores as ui_stores

        if ui_stores.state_is_default(self._store.config):
            return                                 # the default role records nothing
        payload = dict(payload if payload is not None else self.selection())
        with self._record_lock:
            self._record_pending = (payload, job)
            if self._record_busy:
                return                             # the running writer picks it up
            self._record_busy = True
            self._record_idle.clear()
        threading.Thread(target=self._record_loop, name="record-selection",
                         daemon=True).start()

    def _record_loop(self) -> None:
        timeout = float(self._store.config.inputs.select_timeout_seconds)
        while True:
            with self._record_lock:
                item, self._record_pending = self._record_pending, None
                if item is None:
                    self._record_busy = False
                    self._record_idle.set()
                    return
            payload, job = item
            box: dict = {}

            def write(payload=payload, box=box) -> None:
                try:
                    self._persist_selection(payload)
                except BaseException as exc:  # noqa: BLE001 — reported on the job
                    box["error"] = exc

            writer = threading.Thread(target=write, name="record-selection-write", daemon=True)
            started = time.monotonic()
            writer.start()
            writer.join(timeout)
            seconds = round(time.monotonic() - started, 2)
            if writer.is_alive():
                problem = (f"no answer from the state role within {timeout:g}s — the choice "
                           "stands, but is not remembered across an App restart")
            elif "error" in box:
                problem = f"{type(box['error']).__name__}: {box['error']}"
            else:
                problem = None
            if job is not None:
                job["steps"].append({"step": "record", "state": "warning" if problem else "done",
                                     "detail": problem or "", "seconds": seconds})
                if problem:
                    job.setdefault("warnings", []).append(f"record: {problem}")

    def wait_recorded(self, timeout: float = 60.0) -> bool:
        """Tests / scripts: block until the background recorder is idle."""
        return self._record_idle.wait(timeout)

    # -- the selection job (M9.3 addendum) ------------------------------------------

    def _new_job(self, kind: str, name: str) -> dict:
        """Under ``_lock``: register the one running job. A person's choice
        supersedes a startup RESTORE still in flight (its results are dropped)."""
        current = self.selection_job
        if current is not None and current["state"] == "running" and current["kind"] == "restore":
            self._supersede(current, "superseded by a new selection")
        elif current is not None and current["state"] == "running":
            raise SelectionInProgress(
                f"{self.selection_job['name']!r} is still being selected — wait for it "
                "(each step has a timeout) and choose again")
        self._job_seq += 1
        job = {"id": self._job_seq, "kind": kind, "name": name, "state": "running",
               "steps": [], "error": None, "pairing": {}, "result": None, "warnings": [],
               # M15.2: the pairs still on their way once the job is done.
               "pairing_pending": []}
        self.selection_job = job
        self._job_done.clear()
        self._pairing_done.set()                  # a previous job's pairing is moot
        return job

    def _new_step(self, job: dict, step: str) -> dict:
        """Append a step entry to the job's trace and return it. M15.6: every
        step carries how long it took (``seconds``, null while it runs)."""
        entry = {"step": step, "state": "running", "detail": "", "seconds": None}
        job["steps"].append(entry)
        return entry

    def _try_step(self, job: dict, step: str, work, timeout: float, fallback):
        """A step that must NEVER discard the person's choice: pairing is an
        assist and recording is a convenience — a failure is a ``warning`` on
        the job (and a note the UI shows), not a failed selection. Only
        locating and reading the document itself can fail a selection. The
        entry is this step's OWN (M15b.6: two pairing steps run at once —
        ``steps[-1]`` may be the other one's)."""
        entry = self._new_step(job, step)
        try:
            return self._step(job, step, work, timeout, entry=entry)
        except Exception as exc:  # noqa: BLE001 — said on the step, never fatal
            entry["state"] = "warning"
            job.setdefault("warnings", []).append(f"{step}: {exc}")
            return fallback

    def _step(self, job: dict, step: str, work, timeout: float, entry: dict | None = None):
        """Run ONE step in its own thread and wait ``timeout`` for it. ``work``
        takes the step's deadline (time.monotonic) and returns a value — it must
        not change the runner: a step that is given up keeps running nowhere
        that matters. Late = ``StepTimeout``, shown on the job."""
        started = time.monotonic()
        if entry is None:
            entry = self._new_step(job, step)
        deadline = started + timeout
        box: dict = {}

        def run() -> None:
            try:
                box["value"] = work(deadline)
            except BaseException as exc:  # noqa: BLE001 — re-raised on the job thread
                box["error"] = exc

        thread = threading.Thread(target=run, name=f"select:{step}", daemon=True)
        thread.start()
        thread.join(timeout + _STEP_GRACE_SECONDS)
        entry["seconds"] = round(time.monotonic() - started, 2)
        if thread.is_alive():
            entry.update(state="timed_out", detail=f"no answer within {timeout:g}s")
            raise StepTimeout(f"no answer within {timeout:g}s")
        if "error" in box:
            late = isinstance(box["error"], StepTimeout)
            entry.update(state="timed_out" if late else "failed",
                         detail=f"{type(box['error']).__name__}: {box['error']}")
            raise box["error"]
        entry["state"] = "done"
        return box["value"]

    def _supersede(self, job: dict, why: str) -> None:
        """Under ``_lock``: the job's results will be dropped (its steps are
        bounded; it ends on its own and changes nothing)."""
        job["state"], job["error"] = "failed", {"code": "superseded", "message": why}
        job["pairing_pending"] = []
        self._job_done.set()
        self._pairing_done.set()

    def _finish_job(self, job: dict, error: dict | None = None) -> None:
        if self.selection_job is not job:
            return                                  # superseded: a newer job owns the status
        job["error"] = error
        job["state"] = "failed" if error else "done"
        self._job_done.set()

    def job_view(self) -> dict | None:
        job = self.selection_job
        if job is None:
            return None
        return {**job, "steps": [dict(s) for s in job["steps"]],
                "warnings": list(job.get("warnings", [])),
                "pairing_pending": list(job.get("pairing_pending", []))}

    def wait_selection(self, timeout: float = 60.0) -> dict | None:
        """Block until the current selection job has finished AND its pairing
        has landed (tests, the upload route's own bounded wait). Returns the
        job. M15.2: the job is done before the pairs are; a caller that wants
        only the STTM waits on ``_job_done``."""
        deadline = time.monotonic() + timeout
        self._job_done.wait(timeout)
        self._pairing_done.wait(max(deadline - time.monotonic(), 0.0))
        return self.job_view()

    def wait_paired(self, timeout: float = 60.0) -> bool:
        """Tests / scripts: block until the current job's FRD / VDD pairing landed."""
        return self._pairing_done.wait(timeout)

    def start_selection(self, name: str) -> dict:
        """Choose the STTM: returns the JOB at once. Progress, the pairing and
        any failure are on the status (``selection_job``)."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
            job = self._new_job("sttm", name)
        threading.Thread(target=self._run_selection, args=(job,),
                         name=f"select:{name}", daemon=True).start()
        return self.job_view() or job

    def _run_selection(self, job: dict) -> None:
        name = job["name"]
        timeout = float(self._store.config.inputs.select_timeout_seconds)
        step = "locating it in the input folders"
        try:
            doc = self._step(job, "locate",
                             lambda _d: self._workbook_catalog().find(name, (".xlsx",)), timeout)
            if doc is None:
                sources = " or ".join(s.label for s in self._workbook_catalog().sources)
                self._finish_job(job, {"code": "not_found",
                                       "message": f"no STTM workbook named {name!r} in {sources}"})
                return
            # M15.8: the background index reads THIS folder's documents next,
            # so the pairing steps find their facts indexed more often.
            self._index_folder_first(doc.source)
            step = f"downloading {doc.uri}"
            local = self._step(job, "download", lambda _d: self._fetch(doc, timeout), timeout)
            step = "starting the document parser"
            try:
                # Two request lanes (M15b.6): the FRD and VDD pairings read in
                # parallel, each on its own parser process.
                self._step(job, "start parser",
                           lambda _d: [self._index.ensure_parser(lane)
                                       for lane in ("request", "request-vdd")],
                           float(self._store.config.inputs.parser_start_timeout_seconds))
            except Exception:  # noqa: BLE001 — said on the step; the choice still stands
                # No parser (an environment that cannot start a child process):
                # the documents go unread — pairing falls back to names and the
                # folder — rather than every selection being refused.
                job["steps"][-1]["state"] = "warning"
            step = "reading the workbook"
            verdict = self._step(
                job, "classify",
                lambda d: self._index.read_now(doc, local, max(d - time.monotonic(), 0.05)),
                timeout)
            job["steps"][-1]["detail"] = f"{verdict['state']}: {verdict.get('reason', '')}"
            if verdict.get("timed_out"):
                # A workbook the parser cannot read within the budget would hang
                # the RUN too (which reads it in-process): refuse it, visibly.
                job["steps"][-1]["state"] = "timed_out"
                raise StepTimeout(verdict["reason"])
            if verdict["state"] == UNREADABLE:
                # Not a reason to refuse the person's choice (the run will say
                # what is wrong with the file) — but said: it pairs by name only.
                job["steps"][-1]["state"] = "warning"
            # From here on the STTM IS the person's choice — applied NOW, the
            # job done, Generate enabled (M15.2). Pairing it is an assist that
            # lands BEHIND the job (its steps keep appending to the trace and
            # ``pairing_pending`` names what is still on its way; a run started
            # meanwhile waits for it in ``_await_pairing``), and recording it is
            # a convenience — neither is ever a reason to throw the choice away.
            step = "applying the choice"
            with self._lock:                       # state mutation ONLY — no I/O in here
                if self.selection_job is not job or job["state"] != "running":
                    return                           # superseded (a Clear): change nothing
                if self.state == "running":
                    raise LiveRunInProgress("a live run started while the STTM was being "
                                            "selected — the selection was not applied")
                self.selected_workbook = local
                self.last_pairing = {}
                self.pair_decisions = {}
                # M15.3: the PREVIOUS STTM's automatic pairs go the moment the
                # new STTM is applied — never shown as this STTM's.
                self._drop_auto_pair("frd")
                self._drop_auto_pair("vdd")
                self.selection_error = None
                job["pairing_pending"] = ["frd", "vdd"]
                self._pairing_done.clear()
            self._finish_job(job)
            step = "pairing its FRD / VDD"

            # M15b.6: the FRD and the VDD pairing run in PARALLEL threads (own
            # step entry, own parser lane, nothing shared until ``_apply_pair``
            # under the lock) and each is applied as it lands — total pairing
            # time is max(frd, vdd), and the FRD chip never waits for the VDD.
            def pair(kind: str) -> None:
                plan = self._try_step(job, f"pair {kind.upper()}",
                                      lambda d, k=kind: self._plan_pair(k, name, d),
                                      timeout, None)
                if plan is not None:
                    job["pairing"][kind] = plan["outcome"]
                with self._lock:                   # state mutation ONLY
                    if self.selection_job is not job:
                        return                       # superseded: a newer choice owns the pairs
                    if plan is not None:
                        self._apply_pair(kind, plan)
                    else:
                        self._drop_auto_pair(kind)   # M15.3: nothing paired = nothing kept
                    job["pairing_pending"] = [k for k in job["pairing_pending"] if k != kind]
                    if not job["pairing_pending"]:
                        # Remembering the choice across a restart is a background
                        # write — queued BEFORE the event, so a waiter that sees
                        # "paired" also sees the record in flight.
                        self._record_later(self.selection(), job)
                        self._pairing_done.set()

            threads = [threading.Thread(target=pair, args=(kind,), name=f"select:pair-{kind}",
                                        daemon=True) for kind in ("frd", "vdd")]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        except BaseException as exc:  # noqa: BLE001 — a job thread must end in a visible state
            # Nothing half-selected, nothing from before, and NOT the config
            # default: the person sees why and chooses again.
            with self._lock:
                if self.selection_job is not job or job["state"] != "running":
                    return                           # superseded: the status is not ours
                self.selected_workbook = None
                self.selected_frd = self.selected_frd_label = self.frd_auto_paired = None
                self.selected_vdd = self.vdd_auto_paired = None
                self.pair_decisions = {}
                self.last_pairing = {}
                failed = self._fail_selection("sttm", name, exc, step)
            self._finish_job(job, {
                "code": "timeout" if isinstance(exc, StepTimeout) else "failed",
                "message": str(failed)})
        finally:
            with self._lock:                       # a run waiting on the pairing never hangs
                if self.selection_job is job:
                    job["pairing_pending"] = []
                    self._pairing_done.set()

    def _start_restore(self) -> None:
        """After a restart under a remote state role: bring the recorded pair
        back IN THE BACKGROUND (a job like any selection — App start never waits
        for a download), or say which document could not be."""
        from ui.backend import stores as ui_stores

        try:
            if ui_stores.state_is_default(self._store.config):
                return
        except Exception:  # noqa: BLE001 — no usable state role: nothing to restore
            return
        with self._lock:
            job = self._new_job("restore", "the recorded selection")
        threading.Thread(target=self._run_restore, args=(job,), name="select:restore",
                         daemon=True).start()

    def _run_restore(self, job: dict) -> None:
        try:
            self._restore_selection(job)
            self._finish_job(job, None if self.selection_error is None else {
                "code": "failed", "message": self.selection_error["message"]})
        except BaseException as exc:  # noqa: BLE001 — visible, never a dead thread
            self._finish_job(job, {"code": "failed", "message": f"{type(exc).__name__}: {exc}"})

    def _restore_selection(self, job: dict) -> None:
        from ui.backend import stores as ui_stores

        timeout = float(self._store.config.inputs.select_timeout_seconds)

        def read(_deadline):
            path = ui_stores.state_file(self._store.config, SELECTION_FILE, SELECTION_PATH)
            return json.loads(path.read_text(encoding="utf-8"))

        try:
            recorded = self._step(job, "read selection.json", read, timeout)
        except Exception:  # noqa: BLE001 — nothing recorded (or unreadable): none chosen
            job["steps"][-1].update(state="done", detail="nothing recorded")
            return
        for kind, catalog, suffixes in (
                ("sttm", self._workbook_catalog, (".xlsx",)),
                ("frd", self._frd_catalog, (".contract.json", ".docx")),
                ("vdd", self._workbook_catalog, (".xlsx",))):
            name = recorded.get(kind)
            if not name:
                continue
            def locate(_deadline, name=name, kind=kind, catalog=catalog, suffixes=suffixes):
                doc = catalog().find(name, suffixes)
                if doc is None:
                    raise FileNotFoundError(f"{name!r} is no longer in the input folders")
                if kind == "sttm":
                    # M15b.7: at App start, the folder selection.json names is
                    # indexed first — before any person acts.
                    self._restored_folder = doc.source
                    self._index_folder_first(doc.source)
                return self._fetch(doc, timeout)

            try:
                local = self._step(job, f"restore {kind}", locate, timeout)
            except Exception as exc:  # noqa: BLE001 — surfaced; the rest still restores
                if self.selection_job is job:
                    self._fail_selection(kind, name, exc, "restoring the recorded selection")
                continue
            with self._lock:
                if self.selection_job is not job:
                    return                              # the person chose meanwhile
                if kind == "sttm":
                    self.selected_workbook = local
                elif kind == "frd":
                    self.selected_frd, self.selected_frd_label = local, name
                else:
                    self.selected_vdd = local

    def select_workbook(self, name: str) -> Path:
        """``start_selection`` and WAIT for the job — for callers that are not a
        request (tests, scripts). Every step is bounded, so this returns; a
        failed job is ``SelectionFailed`` (``FileNotFoundError`` for an unknown
        name), the STTM left UNSELECTED with ``selection_error`` set."""
        started = self.start_selection(name)
        self._job_done.wait()
        self._pairing_done.wait()
        self.wait_recorded(float(self._store.config.inputs.select_timeout_seconds) + 5)
        job = self.selection_job
        if job is None or job["id"] != started["id"]:
            raise SelectionFailed(f"the selection of {name!r} was superseded")
        if job["error"] is not None:
            if job["error"]["code"] == "not_found":
                raise FileNotFoundError(job["error"]["message"])
            raise SelectionFailed(job["error"]["message"])
        assert self.selected_workbook is not None
        return self.selected_workbook

    def select_vdd_by_name(self, name: str) -> Path:
        """M9.3: a VDD from ANY input root (the route used to look in the local
        directories only — a dictionary in a workspace folder was a 404)."""
        from codegen.storage import StorageError

        doc = self._workbook_catalog().find(name, (".xlsx",))
        if doc is None:
            raise FileNotFoundError(f"no workbook named {name!r} in the input folders")
        try:
            local = self._fetch(doc)
            self.select_vdd(local)
            self._record_later()
        except (StorageError, OSError) as exc:
            raise self._fail_selection("vdd", name, exc, f"downloading {doc.uri}") from exc
        if self.selection_error and self.selection_error.get("kind") == "vdd":
            self.selection_error = None
        return local

    def clear_workbook(self) -> None:
        """Back to 'none chosen' — the presenter's reset for the choose step. A
        selection still running is superseded (it will change nothing)."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
            job = self.selection_job
            if job is not None and job["state"] == "running":
                self._supersede(job, "cleared while it was running")
        self.selected_workbook = None
        self.pair_decisions = {}
        self.selection_error = None
        self.last_pairing = {}
        self._vdd_watch = set()
        self._deferred_vdd_plan = None
        if self.frd_auto_paired is not None:
            self.selected_frd = None
            self.selected_frd_label = None
            self.frd_auto_paired = None
        if self.vdd_auto_paired is not None:
            self.selected_vdd = None
            self.vdd_auto_paired = None
        self._record_later()

    def status(self) -> dict:
        return {
            "state": self.state,
            "stages": list(self.stages),
            "error": self.error,
            "last_run_label": self.last_run_label,
            "set_aside": list(self.set_aside),
            "layout_questions": list(self.layout_questions),
            "layout_report": self.layout_report,
            "layout_advice": self.layout_advice,
            "layout_fills": list(self.layout_fills),
            "layout_refresh": self.layout_refresh,
            # M9.3: the last FAILED selection ({kind, name, message}) and what
            # choosing the STTM paired / asks, per kind.
            "selection_error": self.selection_error,
            "pairing": dict(self.last_pairing),
            # M9.3 addendum: THE record of what is selected (names; None = not
            # chosen) and the selection job — {id, kind, name, state: running |
            # done | failed, steps: [{step, state, detail}], error: {code,
            # message}, pairing}.
            "selection": self.selection(),
            "selection_job": self.job_view(),
            "frd_auto_paired": self.frd_auto_paired,
            "vdd_auto_paired": self.vdd_auto_paired,
            # M8.1: input roots whose last listing failed (label -> API message).
            "input_errors": self.input_errors(),
            # M8.2: undecided pairings (asked in the dialog when the run starts).
            "pair_candidates": {
                kind: {"reason": d.reason,
                       "candidates": [{"name": c.name, "score": c.score, "signals": c.summary()}
                                      for c in d.candidates]}
                for kind, d in self.pair_decisions.items() if d.ambiguous},
            "output_parts": self.effective_output_parts(),
            # Retired output values met in config / saved state / requests,
            # each announced once (codegen.output_modes).
            "output_notices": output_notices(),
            "model_usage": list(self.model_usage),
        }

    def advise_layout(self, *, dry_run: bool = False) -> dict:
        """One model call over the pending questions' texts and candidate
        labels (never a data row); the validated advice is stored on the
        runner and shown in the dialog. The mock provider (dry-run / mock
        lock / no transport) answers with offline heuristics and says so."""
        from codegen.layout.model import (
            build_advice_request,
            build_layout_provider,
            validate_advice,
        )

        if self.state != "needs_layout" or not self.layout_questions:
            raise LiveRunInProgress("no live run is waiting for layout answers")
        from codegen.reasoning.usage import layout_usage

        provider = build_layout_provider(self._store.config, dry_run=dry_run, base_dir=REPO_ROOT)
        # The advice call belongs to this run's layout stage record.
        self._layout_providers.append(provider)
        response = provider.advise_layout(build_advice_request(self.layout_questions))
        self.layout_advice = {"provider": provider.name,
                              "usage": layout_usage(provider).as_dict(),
                              "advice": validate_advice(response, self.layout_questions)}
        return self.layout_advice

    def answer_layout(self, answers: dict | None, *, proceed: bool = False,
                      cancel: bool = False, refresh: bool = False) -> None:
        """Deliver the human's role placements to the waiting run (or tell
        it to proceed with empties / to stop). ``refresh`` (M9.1) re-resolves
        the layout past every cached profile instead."""
        if self.state != "needs_layout":
            raise LiveRunInProgress("no live run is waiting for layout answers")
        self._layout_answers = {"answers": answers or {}, "proceed": proceed, "cancel": cancel,
                                "refresh": refresh}
        self._layout_event.set()

    def set_layout_refresh(self, enabled: bool) -> None:
        """Arm / disarm "re-resolve layout" for the NEXT run (one shot)."""
        if self.state in ("running", "needs_layout"):
            raise LiveRunInProgress("a live run is in progress — re-resolve from its layout "
                                    "dialog, or wait for it to finish")
        self.layout_refresh = bool(enabled)

    def _resolve_layout(self, workbook_path: Path, frd_path: Path, config,
                        vdd_path: Path | None = None):
        """cache -> synonyms -> model -> validate -> user, pausing the run in
        ``needs_layout`` until every question is answered or the human
        chooses to proceed with the unresolved roles read as empty."""
        from codegen.layout.model import build_layout_provider
        from codegen.layout.resolve import parse_answers, resolve_pair
        from ui.backend import stores as ui_stores

        provider = build_layout_provider(config, dry_run=False, base_dir=REPO_ROOT)
        self._layout_providers.append(provider)
        runtime_cache = ui_stores.layout_cache_dir(config)
        answers: dict = {"sttm": {}, "frd": {}, "vdd": {}, "gaps": {}}
        refresh, self.layout_refresh = self.layout_refresh, False        # one shot
        while True:
            if refresh:
                self._stage("re-resolve layout", "cached layout profiles bypassed; the runtime "
                                                 "entries are overwritten")
            result = resolve_pair(workbook_path, frd_path, config, provider=provider,
                                  answers=answers, runtime_cache_dir=runtime_cache,
                                  base_dir=REPO_ROOT, vdd_path=vdd_path, refresh=refresh)
            refresh = False
            self.layout_report = result.report()
            self.layout_fills = list(result.gap_fills)
            if not result.questions:
                ui_stores.push_layout_cache(config)
                return result
            self.layout_questions = [q.as_dict() for q in result.questions]
            self.layout_advice = None
            self._layout_answers = None
            self._layout_event.clear()
            self.state = "needs_layout"
            self._stage("needs layout", f"{len(result.questions)} unresolved role(s) — "
                                        "waiting for the human")
            self._layout_event.wait()
            self.state = "running"
            reply = self._layout_answers or {}
            self.layout_questions = []
            if reply.get("cancel"):
                raise RuntimeError("layout resolution cancelled by the user")
            if reply.get("refresh"):
                # Start over past the caches: the answers given so far were
                # answers to the OLD profile's questions.
                answers = {"sttm": {}, "frd": {}, "vdd": {}, "gaps": {}}
                refresh = True
                continue
            merged = parse_answers(reply.get("answers") or {})
            answers = {"sttm": {**answers["sttm"], **merged["sttm"]},
                       "frd": {**answers["frd"], **merged["frd"]},
                       "vdd": {**answers.get("vdd", {}), **merged.get("vdd", {})},
                       "gaps": {**answers.get("gaps", {}), **merged.get("gaps", {})}}
            if reply.get("proceed"):
                result = resolve_pair(workbook_path, frd_path, config, provider=provider,
                                      answers=answers, runtime_cache_dir=runtime_cache,
                                      base_dir=REPO_ROOT, vdd_path=vdd_path)
                self.layout_report = result.report()
                self.layout_fills = list(result.gap_fills)
                ui_stores.push_layout_cache(config)
                return result

    def start_live(self) -> None:
        if self.output_parts == []:
            raise ValueError("no output selected — choose Notebook, Framework artefacts, "
                             "or both")

        job = self.selection_job
        if job is not None and job["state"] == "running" and job["kind"] == "restore":
            # The startup restore is not the person's act: starting a run
            # supersedes it (as choosing a document does), so a slow workspace
            # cannot refuse Generate for as long as the restore takes.
            with self._lock:
                if self.selection_job is job and job["state"] == "running":
                    self._supersede(job, "a run was started before it finished")
        elif job is not None and job["state"] == "running" and job["kind"] != "frd_upstream":
            # The documents are still being chosen: never the config default meanwhile.
            raise ValueError(f"{job['name']!r} is still being selected — wait for it to "
                             "finish before generating")
        if self.selection_error is not None and self.selected_workbook is None:
            # Never the config default in place of a document that failed to load.
            raise ValueError(f"{self.selection_error['message']} — choose the STTM again (or "
                             "Clear it) before generating")
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("a live demo run is already in progress")
            if self._clearing:
                raise LiveRunInProgress("past runs are being cleared — generate when it finishes")
            self.state = "running"
            self.stages = []
            self.error = None
            self.model_usage = []
            self._layout_providers = []
        thread = threading.Thread(target=self._run, name="live-demo-run", daemon=True)
        thread.start()

    def clear_runs(self) -> dict:
        """Delete every past run folder in the outputs role (a remote role's
        copy too). Refused while a run is in progress — it writes into one."""
        from ui.backend import stores as ui_stores

        with self._lock:                       # state mutation ONLY — no I/O in here
            if self.state in ("running", "needs_layout"):
                raise LiveRunInProgress("a live run is in progress — clear runs after it "
                                        "finishes")
            if self._clearing:
                raise LiveRunInProgress("past runs are already being cleared")
            self._clearing = True              # start_live refuses meanwhile
        try:
            deleted = ui_stores.clear_runs(self._store.config)
        finally:
            with self._lock:
                self._clearing = False
        unloaded = self._store.forget_runs(deleted)
        with self._lock:
            if self.last_run_label in deleted and self.state in ("done", "failed", "idle"):
                self.last_run_label = None
                self.state = "idle"
                self.stages = []
                self.error = None
                self.model_usage = []
        return {"deleted": deleted, "unloaded_current": unloaded}

    def _await_pairing(self) -> None:
        """M15.2: Generate enables as soon as the STTM is classified; a run that
        starts while the FRD / VDD pairing is still landing waits for it here
        (every pairing step is bounded), so a run never takes the config
        default in place of a pair that is on its way."""
        job = self.selection_job
        if self._pairing_done.is_set() or job is None:
            return

        def frd_pending() -> bool:
            current = self.selection_job
            return (current is job and self.selected_frd is None
                    and "frd" in job.get("pairing_pending", []))

        # M15c: wait ONLY for an FRD still on its way while NONE is selected (a
        # run cannot proceed without one). Never for the VDD — it is optional,
        # and one that lands later is simply not part of this run. In ACFC the
        # run sat on "waiting for the FRD / VDD pairing" for minutes while the
        # VDD scan of every folder ran, with the FRD long since paired.
        if not frd_pending():
            return
        self._stage("pairing", f"waiting for the FRD pairing of {job['name']!r} to finish "
                               "(no FRD is selected yet)")
        deadline = time.monotonic() + float(
            self._store.config.inputs.select_timeout_seconds) + _STEP_GRACE_SECONDS
        while time.monotonic() < deadline:
            if not frd_pending():
                return
            time.sleep(0.1)
        self._stage("pairing", "the FRD pairing did not finish in time — running with what is "
                               "selected now")

    def _run(self) -> None:
        try:
            self._await_pairing()
            self._work()
            self.state = "done"
        except Exception as exc:  # noqa: BLE001 — must release the guard and surface, not crash
            self.error = f"{type(exc).__name__}: {exc}"
            self.state = "failed"
        finally:
            # M15d.3: a VDD re-scored while the run was in progress lands now —
            # that run was not affected; the next one is.
            with self._lock:
                plan, self._deferred_vdd_plan = self._deferred_vdd_plan, None
                manual_vdd = self.selected_vdd is not None and self.vdd_auto_paired is None
                if plan is not None and self.selection_job is not None and not manual_vdd:
                    self._apply_pair("vdd", plan)
                    self.selection_job["pairing"]["vdd"] = plan["outcome"]

    def upstream_snapshot(self) -> dict:
        """The upstream contract listing as last read — NEVER a call: with
        ``upstream.enabled`` a stale snapshot starts a background refresh (hard
        timeout ``upstream.timeout_seconds``) and this returns what is known
        now; disabled (the default, standalone doctrine) nothing is ever
        called. {enabled, state: disabled | loading | ready | failed, rows,
        error}."""
        cfg = self._store.config.upstream
        if not cfg.enabled:
            return {"enabled": False, "state": "disabled", "rows": [], "error": None}
        with self._lock:
            snap = self._upstream
            stale = snap["state"] == "idle" or (
                snap["state"] != "loading"
                and time.monotonic() - snap["at"] >= cfg.refresh_seconds)
            if stale:
                self._upstream_seq += 1
                snap = self._upstream = {**snap, "state": "loading"}
                threading.Thread(target=self._refresh_upstream,
                                 args=(self._upstream_seq, float(cfg.timeout_seconds)),
                                 name="upstream-contracts", daemon=True).start()
        return {"enabled": True, "state": snap["state"], "rows": list(snap["rows"]),
                "error": snap["error"]}

    def _refresh_upstream(self, seq: int, timeout: float) -> None:
        box: dict = {}

        def call() -> None:
            try:
                from codegen import upstream_contracts

                box["rows"] = upstream_contracts.list_contracts(self._store.config)
            except Exception as exc:  # noqa: BLE001 — the chooser stays usable offline
                box["error"] = (str(exc).splitlines() or [type(exc).__name__])[0][:160]

        thread = threading.Thread(target=call, name="upstream-contracts-call", daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            box = {"error": f"the FRD→STTM contract table did not answer within {timeout:g}s "
                            "(the query was given up)"}
        with self._lock:
            if seq != self._upstream_seq:
                return                                  # a newer refresh owns the snapshot
            self._upstream = {"state": "failed" if "error" in box else "ready",
                              "rows": box.get("rows", []), "error": box.get("error"),
                              "at": time.monotonic()}

    def start_upstream_frd(self, doc_id: str) -> dict:
        """Select an UPSTREAM contract (a warehouse read): a job, never awaited
        by the request. Refused while ``upstream.enabled`` is false."""
        cfg = self._store.config.upstream
        if not cfg.enabled:
            raise PermissionError(
                "upstream contract lookups are off (upstream.enabled: false) — choose an FRD "
                "document from the input folders")
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the FRD while a live run is in progress")
            job = self._new_job("frd_upstream", doc_id)

        def run() -> None:
            def read(_deadline):
                from codegen import upstream_contracts

                return upstream_contracts.materialize(self._store.config, doc_id, REPO_ROOT)

            try:
                path, contract, meta = self._step(job, "read the contract", read,
                                                  float(cfg.timeout_seconds))
                self.select_frd(path, doc_id)
                job["result"] = {
                    "selected": doc_id, "kind": "upstream", "audited_at": meta["audited_at"],
                    "feeds": [{
                        "feed_name": f.feed_name,
                        "stage": f"{f.stage_target.schema_name}."
                                 f"{','.join(f.stage_target.tables)}",
                        "standard": (f"{f.standard_target.schema_name}."
                                     f"{','.join(f.standard_target.tables)}"
                                     if f.standard_target.tables else None),
                    } for f in contract.feeds]}
                self._finish_job(job)
            except BaseException as exc:  # noqa: BLE001 — visible, never a dead thread
                failed = self._fail_selection("frd", doc_id, exc, "reading the upstream contract")
                self._finish_job(job, {
                    "code": "timeout" if isinstance(exc, StepTimeout) else "failed",
                    "message": str(failed)})

        threading.Thread(target=run, name=f"select:upstream:{doc_id}", daemon=True).start()
        return self.job_view() or job

    def _attach_pairing_hint(self, exc: Exception, workbook_path: Path,
                             frd_label: str) -> None:
        """On a feed-match failure, name the FRD the run used and — when
        the pairing helpers know a companion — offer it. Information only;
        choosing remains the human's act, and there is no auto-retry. Reads the
        upstream SNAPSHOT only (nothing when ``upstream.enabled`` is false)."""
        if "matches 0 FRD feeds" not in str(exc):
            return
        try:
            from codegen.demo_sources import pair_sttm_with_frd, suggest_pairs

            doc_ids = [row["doc_id"] for row in self.upstream_snapshot()["rows"]]
            explicit = pair_sttm_with_frd(
                [workbook_path.name], doc_ids,
                explicit_map=self._store.config.demo.pairing_map,
            )
            suggested = suggest_pairs([workbook_path.name], doc_ids)
            candidate = explicit.get(workbook_path.name) or suggested.get(
                workbook_path.name
            )
        except Exception:  # noqa: BLE001, S110 — offline: the hint is optional
            candidate = None
        if candidate:
            self.error_hint = {
                "sttm": workbook_path.name,
                "frd_used": frd_label,
                "candidate_doc_id": candidate,
                "message": (
                    f"This run used FRD '{frd_label}'. A companion FRD "
                    f"'{candidate}' is available from the FRD→STTM agent; "
                    "choose it in the STTM picker."
                ),
            }

    def _stage(self, name: str, detail: str = "") -> None:
        self.stages.append({"stage": name, "detail": detail, "at": time.time()})

    def _execute(self) -> None:
        config = self._store.config
        label = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        from ui.backend import stores as ui_stores

        # Generated into the outputs role's local directory (./out by default;
        # a remote role's working copy otherwise) and pushed up once complete.
        run_root = ui_stores.outputs_root(config) / label
        reports_root = run_root / "reports"
        run_root.mkdir(parents=True, exist_ok=True)

        frd_path = self.effective_frd()
        frd_label = self.selected_frd_label or frd_path.name
        workbook_path = self.effective_workbook()
        contract_path = run_root / "extracted_sttm.contract.json"

        self.error_hint = None
        self._ask_pairing()
        frd_path = self.effective_frd()
        frd_label = self.selected_frd_label or frd_path.name
        # Self-contained run directory: copy the FRD the run actually used
        # (content-identical => provenance hashes unchanged) and record run
        # metadata, so a past run reloads with ITS pair — never the pinned
        # demo golden (the View-results bug of 2026-08-27).
        import json as json_module
        import shutil

        run_frd = run_root / "frd.contract.json"
        frd_is_docx = frd_path.suffix.lower() == ".docx"
        # Layout first: the resolved layout also produces the FRD contract
        # (a .docx read through its profile, with any FRD gaps filled from the
        # STTM / VDD / FAQ or the person's choice — resolve/gapfill.py).
        self._stage("resolving layout", f"{workbook_path.name} (+ {frd_label})")
        resolution = self._resolve_layout(workbook_path, frd_path, config,
                                          vdd_path=self.selected_vdd)
        from codegen.reasoning.usage import layout_usage as _layout_usage
        from codegen.reasoning.usage import run_usage

        layout_usage = _layout_usage(*self._layout_providers)
        self.model_usage = [layout_usage.as_dict()]
        self._stage("layout recognizer", layout_usage.label)
        from codegen.extract.frd_docx import contract_to_json

        # A feed the person left without a file (Proceed unresolved on its
        # 'File for table …' question) cannot be extracted: set it aside as
        # a failed feed WITH the remedy and carry on with the others.
        set_aside = feeds_left_without_a_file(resolution.questions, resolution.frd_contract)
        pre_failures: list[FailedRun] = []
        skip_tables: set[str] = set()
        if set_aside:
            kept = [f for i, f in enumerate(resolution.frd_contract.feeds)
                    if i not in {i for i, _f in set_aside}]
            for _i, feed in set_aside:
                skip_tables.update(feed.stage_target.tables)
                pre_failures.append(FailedRun(
                    label=feed.feed_name,
                    error=(f"skipped: no document names the file that feeds stage table(s) "
                           f"{feed.stage_target.tables} and the question 'File for table "
                           f"{feed.feed_name}' was left unanswered. Re-run and answer it, or "
                           "add the file name to the FRD — the agent never guesses a file."),
                ))
            resolution.frd_contract = resolution.frd_contract.model_copy(update={"feeds": kept})
            self._stage("feeds set aside",
                        f"{len(set_aside)} feed(s) without a file: "
                        + ", ".join(f.feed_name for _i, f in set_aside))
        if frd_is_docx or resolution.gap_fills or set_aside:
            self._stage("extracting FRD" if frd_is_docx else "filling FRD gaps",
                        f"{frd_path.name} → FRD feed contract"
                        + (f" ({len(resolution.gap_fills)} field(s) from other documents)"
                           if resolution.gap_fills else ""))
            run_frd.write_text(contract_to_json(resolution.frd_contract), encoding="utf-8",
                               newline="\n")
        else:
            shutil.copyfile(frd_path, run_frd)  # content-identical: hashes unchanged
        (run_root / "run_meta.json").write_text(
            json_module.dumps({
                "frd_label": frd_label,
                "sttm_workbook": workbook_path.name,
                "output_mode": self.output_mode or output_parts(
                    config.output.mode, source="config output.mode"),
                "conventions_profile": self.conventions_profile or config.conventions.profile,
                "iig_template": self.iig_template or config.metadata.template,
                "playbook_template": self.playbook_template or config.playbook.template,
            }, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        frd_path = run_frd
        layout_flags = list(resolution.flags)
        vdd_contract_path: Path | None = None
        if self.selected_vdd is not None and resolution.vdd is not None:
            from codegen.extract.vdd import contract_to_json as vdd_to_json
            from codegen.extract.vdd import extract_vdd_contract

            self._stage("extracting VDD", f"{self.selected_vdd.name} → VDD contract")
            vdd_contract, _ = extract_vdd_contract(self.selected_vdd, config,
                                                   layout=resolution.vdd.profile)
            vdd_contract_path = run_root / "vdd.contract.json"
            vdd_contract_path.write_text(vdd_to_json(vdd_contract), encoding="utf-8",
                                         newline="\n")

        self._stage("extracting workbook",
                    f"{workbook_path.name} → STTM mapping contract (FRD: {frd_label})")
        try:
            extract_to_file(workbook_path, frd_path, contract_path, config,
                            layout=resolution.sttm.profile,
                            skip_stage_tables=sorted(skip_tables),
                            # M9.2: the dialog's byte-width answers ride on the fields.
                            width_answers=getattr(resolution, "width_answers", None) or None)
        except Exception as exc:
            self._attach_pairing_hint(exc, workbook_path, frd_label)
            raise

        self._stage("resolving contracts", f"{frd_label} ⋈ extracted contract")
        specs = resolve_pair(frd_path, contract_path, config, vdd_path=vdd_contract_path)

        runs: dict[str, FeedRun] = {}
        failures: list[FailedRun] = list(pre_failures)
        for spec in specs:
            slug = spec.feed_slug
            try:
                runs[slug] = self._store._generate_feed(  # noqa: SLF001
                    spec,
                    dry_run=False,
                    skip_tests=True,
                    out_root=run_root,
                    reports_dir=reports_root,
                    on_stage=lambda detail, slug=slug: self._stage(f"{slug}: {detail}"),
                    output_mode=self.output_mode,
                    extra_flags=layout_flags,
                    conventions_profile=self.conventions_profile,
                    iig_template=self.iig_template,
                    playbook_template=self.playbook_template,
                    layout_usage=layout_usage,
                )
            except Exception as exc:  # noqa: BLE001 — one bad feed must not sink the run
                failures.append(FailedRun(label=slug, error=f"{type(exc).__name__}: {exc}"))
        if not runs:
            details = "; ".join(f"{f.label}: {f.error}" for f in failures) or "no feeds resolved"
            raise RuntimeError(f"live run produced no feeds — {details}")

        self.model_usage = run_usage([r.model_usage or [] for r in runs.values()], layout_usage)
        self._stage("model usage", "; ".join(f"{u['stage']}: {u['label']}"
                                             for u in self.model_usage))
        self.set_aside = [f.model_dump() for f in pre_failures]
        sent = ui_stores.push_run(config, label)
        if sent:
            self._stage("storing outputs", f"{len(sent)} file(s) → "
                        f"{ui_stores.get_stores(config).outputs.uri(label)}")
        self._stage("publishing results", f"{len(runs)} feed(s), {len(failures)} failure(s)")
        self._store.adopt(
            runs,
            failures,
            mode="live",
            label=label,
            out_root=run_root,
            reports_root=reports_root,
            layout_usage=layout_usage,
        )
        self.last_run_label = label
