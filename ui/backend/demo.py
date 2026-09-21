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

import re
import threading
import time
from datetime import datetime
from pathlib import Path

from codegen.extract import extract_to_file
from codegen.resolve.resolver import resolve_pair
from ui.backend.service import REPO_ROOT, FailedRun, FeedRun, GenerationStore


class LiveRunInProgress(RuntimeError):
    """A live run is already in flight (surface as HTTP 409)."""


# Output selection as independent PARTS (what the UI toggles) mapped onto
# the generator's single mode. "all" is its own part — selecting it is not
# the same UI state as ticking the three others, even though it generates
# the same set. An rfc part always carries the framework artefacts it is
# built from (the generator writes them either way).
OUTPUT_PARTS = ("notebook", "framework", "rfc", "all")
_MODE_TO_PARTS = {
    "notebook": ["notebook"],
    "framework": ["framework"],
    "both": ["notebook", "framework"],
    "rfc": ["rfc"],
    "all": ["all"],
}


def parts_for_mode(mode: str) -> list[str]:
    return list(_MODE_TO_PARTS[mode])


def mode_for_parts(parts: list[str]) -> str | None:
    """None when nothing is selected (a run is refused)."""
    chosen = set(parts)
    if not chosen:
        return None
    if "all" in chosen or ("notebook" in chosen and "rfc" in chosen):
        return "all"
    if "rfc" in chosen:
        return "rfc"
    if "notebook" in chosen and "framework" in chosen:
        return "both"
    return "framework" if "framework" in chosen else "notebook"


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

    def __init__(self, store: GenerationStore, work=None) -> None:
        self._store = store
        self._work = work or self._execute  # injectable for tests
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
            # FRD is actually selected (``fetch_frd_candidate``).
            found.setdefault(doc.name, doc.local_path())
        return found

    def fetch_frd_candidate(self, name: str) -> Path | None:
        """The named local FRD candidate as a file on disk (downloaded first
        when it lives in a remote input root); None when no source has it."""
        doc = self._frd_catalog().find(name, (".contract.json", ".docx"))
        return doc.fetch() if doc is not None else None

    def auto_pair_frd(self, sttm_name: str) -> dict | None:
        """Select the FRD associated with the chosen STTM when one is present
        (config pairing map -> shared ticket -> unique name stem). A manual
        FRD choice is replaced only when a pair is found; a stale automatic
        pair from a previous STTM is cleared."""
        candidates = self.local_frd_candidates()
        match = self._pair("frd", sttm_name, candidates,
                           self._store.config.demo.pairing_map)
        if match is None:
            if self.frd_auto_paired is not None:
                self.selected_frd = None
                self.selected_frd_label = None
                self.frd_auto_paired = None
            return None
        frd_name, rule = match
        self.selected_frd = self.fetch_frd_candidate(frd_name) or candidates[frd_name]
        self.selected_frd_label = frd_name
        self.frd_auto_paired = {"frd": frd_name, "rule": rule}
        return self.frd_auto_paired

    def _pair(self, kind: str, sttm_name: str, candidates: dict[str, Path],
              explicit_map: dict[str, str]) -> tuple[str, str] | None:
        """(document, rule) for the chosen STTM — by CONTENT (codegen.pairing:
        explicit map, then what the documents say, the ticket number one
        signal among several). An undecided result is kept in
        ``pair_decisions`` and asked in the layout dialog when the run starts."""
        from codegen.pairing import pair_by_content
        from codegen.storage import StorageError

        catalog = self._frd_catalog() if kind == "frd" else self._workbook_catalog()
        suffixes = (".contract.json", ".docx") if kind == "frd" else (".xlsx",)
        local: dict[str, Path] = {}
        for name in candidates:
            doc = catalog.find(name, suffixes)
            try:
                local[name] = doc.fetch() if doc is not None else candidates[name]
            except StorageError:
                continue                     # unreachable candidate: not a contender
        sttm_doc = self._workbook_catalog().find(sttm_name, (".xlsx",))
        sttm_path = (self.selected_workbook if self.selected_workbook is not None
                     and self.selected_workbook.name == sttm_name
                     else sttm_doc.fetch() if sttm_doc is not None else Path(sttm_name))
        decision = pair_by_content(kind, sttm_path, local, self._store.config, REPO_ROOT,
                                   explicit_map=explicit_map)
        self.pair_decisions[kind] = decision
        if decision.chosen is None:
            return None
        return decision.chosen, decision.rule or "content"

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
        candidates = {doc.name: doc.local_path()
                      for doc in self._workbook_catalog().documents((".xlsx",))
                      if doc.name != sttm_name}
        match = self._pair("vdd", sttm_name, candidates,
                           self._store.config.demo.vdd_pairing_map)
        if match is None:
            if self.vdd_auto_paired is not None:
                self.selected_vdd = None
                self.vdd_auto_paired = None
            return None
        vdd_name, rule = match
        doc = self._workbook_catalog().find(vdd_name, (".xlsx",))
        if doc is None:
            return None
        self.selected_vdd = doc.fetch()
        self.vdd_auto_paired = {"vdd": vdd_name, "rule": rule}
        return self.vdd_auto_paired

    @property
    def output_mode(self) -> str | None:
        """The generator mode the selected parts map onto; None = config
        default when nothing was selected, also None when the selection is
        empty (callers refuse a run in that case)."""
        if self.output_parts is None:
            return None
        return mode_for_parts(self.output_parts)

    def effective_output_parts(self) -> list[str]:
        if self.output_parts is not None:
            return list(self.output_parts)
        return parts_for_mode(self._store.config.output.mode)

    def select_output_mode(self, mode: str | None) -> None:
        """Compatibility entry: a single mode selects its parts."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress(
                    "cannot change the output mode while a live run is in progress"
                )
        if mode is not None and mode not in _MODE_TO_PARTS:
            raise ValueError(f"unknown output mode {mode!r}")
        self.output_parts = None if mode is None else parts_for_mode(mode)

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
        unknown = [p for p in parts if p not in OUTPUT_PARTS]
        if unknown:
            raise ValueError(f"unknown output part(s) {unknown!r}; expected {OUTPUT_PARTS}")
        self.output_parts = list(dict.fromkeys(parts))

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
        return (
            (configured.parent.relative_to(REPO_ROOT).as_posix(), configured.parent),
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
            cached = (config, InputCatalog(self._input_sources(first),
                                           ttl_seconds=config.inputs.listing_ttl_seconds))
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
        """
        effective = self.selected_workbook
        return [{"name": doc.name, "source": doc.source,
                 "selected": doc.local_path() == effective}
                for doc in self._workbook_catalog().documents((".xlsx",))]

    def select_workbook(self, name: str) -> Path:
        """Pick a workbook BY NAME from the scanned dirs — never a raw path."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
        doc = self._workbook_catalog().find(name, (".xlsx",))
        if doc is not None:
            self.selected_workbook = doc.fetch()
            self.auto_pair_frd(name)
            self.auto_pair_vdd(name)
            return self.selected_workbook
        raise FileNotFoundError(
            f"no STTM workbook named {name!r} in "
            + " or ".join(source.label for source in self._workbook_catalog().sources)
        )

    def clear_workbook(self) -> None:
        """Back to 'none chosen' — the presenter's reset for the choose step."""
        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("cannot change the STTM while a live run is in progress")
        self.selected_workbook = None
        self.pair_decisions = {}
        if self.frd_auto_paired is not None:
            self.selected_frd = None
            self.selected_frd_label = None
            self.frd_auto_paired = None
        if self.vdd_auto_paired is not None:
            self.selected_vdd = None
            self.vdd_auto_paired = None

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
        provider = build_layout_provider(self._store.config, dry_run=dry_run, base_dir=REPO_ROOT)
        response = provider.advise_layout(build_advice_request(self.layout_questions))
        self.layout_advice = {"provider": provider.name,
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
            raise ValueError("no output selected — choose at least one of notebook, "
                             "framework artefacts, RFC package, or All")

        with self._lock:
            if self.state == "running":
                raise LiveRunInProgress("a live demo run is already in progress")
            self.state = "running"
            self.stages = []
            self.error = None
        thread = threading.Thread(target=self._run, name="live-demo-run", daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            self._work()
            self.state = "done"
        except Exception as exc:  # noqa: BLE001 — must release the guard and surface, not crash
            self.error = f"{type(exc).__name__}: {exc}"
            self.state = "failed"

    def _attach_pairing_hint(self, exc: Exception, workbook_path: Path,
                             frd_label: str) -> None:
        """On a feed-match failure, name the FRD the run used and — when
        the pairing helpers know a companion — offer it. Information only;
        choosing remains the human's act, and there is no auto-retry."""
        if "matches 0 FRD feeds" not in str(exc):
            return
        try:
            from codegen.demo_sources import pair_sttm_with_frd, suggest_pairs
            from codegen.upstream_contracts import list_contracts

            doc_ids = [row["doc_id"] for row in list_contracts(self._store.config)]
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
                "output_mode": self.output_mode or config.output.mode,
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
                )
            except Exception as exc:  # noqa: BLE001 — one bad feed must not sink the run
                failures.append(FailedRun(label=slug, error=f"{type(exc).__name__}: {exc}"))
        if not runs:
            details = "; ".join(f"{f.label}: {f.error}" for f in failures) or "no feeds resolved"
            raise RuntimeError(f"live run produced no feeds — {details}")

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
        )
        self.last_run_label = label
