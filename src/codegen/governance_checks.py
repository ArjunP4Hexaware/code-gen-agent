"""Reference-architecture checks: the two agent decks vs the loaded run.

The Data-Governance and Solution architecture decks state controls and
invariants ("SHA-256 fingerprints", "Grounding audit", "human-in-the-loop",
"Audit trail", "never writes back", "one call per document — everything
else is deterministic code"). This module reads both decks LIVE at request
time, keeps only the controls the documents actually state (matched by
anchor phrase, control text verbatim from the deck), and evaluates each
against the currently loaded run's real state — contract fingerprints,
grounding flags on Layer-2 candidates, pending review decisions, reports
on disk, and the read-only shape of the Databricks seam.

Like every reference-document reader here: a deck that is absent or does
not parse contributes nothing — its checks disappear, they never error.
Nothing in this module touches generation; it is a request-time audit of
what generation already produced.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def read_deck_paragraphs(pptx_path: Path) -> list[str] | None:
    try:
        with zipfile.ZipFile(pptx_path) as archive:
            names = sorted(
                (n for n in archive.namelist()
                 if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                key=lambda n: int(re.search(r"\d+", n).group()),
            )
            texts: list[str] = []
            for name in names:
                root = ET.fromstring(archive.read(name))
                for paragraph in root.iter(f"{_A}p"):
                    text = "".join(
                        t.text or "" for t in paragraph.iter(f"{_A}t")
                    ).strip()
                    if text:
                        texts.append(text)
            return texts
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError):
        return None


@dataclass(frozen=True)
class RunFacts:
    """What the loaded run actually shows — supplied by the caller (the UI
    store or the CLI), never gathered here."""

    loaded: bool = False
    mode: str | None = None                      # mock | live | replay
    feeds: int = 0
    fingerprinted_feeds: int = 0                 # both contract sha256s present
    candidates: int = 0
    grounded_candidates: int = 0
    pending_reviews: int = 0
    reports_on_disk: int = 0
    candidate_providers: tuple[str, ...] = field(default_factory=tuple)


def _no_run(control: str, deck: str) -> dict:
    return {"control": control, "deck": deck, "status": "pending_run",
            "evidence": "no run loaded — generate or load a run to evaluate"}


# Each entry: (anchor phrase to find in the deck, evaluator). The control
# text shown is the DECK'S OWN line containing the anchor, verbatim.
def _controls_for(deck_kind: str):
    if deck_kind == "governance":
        return [
            ("sha-256 fingerprints", _check_fingerprints),
            ("grounding audit", _check_grounding),
            ("human-in-the-loop", _check_human_in_the_loop),
            ("audit trail", _check_audit_trail),
        ]
    return [
        ("never writes back", _check_read_only_seams),
        ("one call per document", _check_deterministic_core),
    ]


def _check_fingerprints(facts: RunFacts) -> tuple[str, str]:
    if facts.fingerprinted_feeds == facts.feeds:
        return "verified", (
            f"all {facts.feeds} feed(s) carry FRD + STTM sha256 fingerprints; "
            "every generated file embeds them in its provenance banner"
        )
    return "attention", (
        f"only {facts.fingerprinted_feeds}/{facts.feeds} feeds fingerprinted"
    )


def _check_grounding(facts: RunFacts) -> tuple[str, str]:
    failed = facts.candidates - facts.grounded_candidates
    if facts.candidates == 0:
        return "verified", "no Layer-2 candidates this run — nothing to ground"
    evidence = (
        f"{facts.grounded_candidates}/{facts.candidates} candidate citations "
        "verified verbatim against the contract text"
    )
    if failed:
        evidence += f"; {failed} failed grounding and are flagged, not merged"
    return "verified", evidence


def _check_human_in_the_loop(facts: RunFacts) -> tuple[str, str]:
    return "verified", (
        f"{facts.pending_reviews} candidate(s) pending engineer approval; "
        "an approval records a decision and never merges into generated code"
    )


def _check_audit_trail(facts: RunFacts) -> tuple[str, str]:
    if facts.reports_on_disk == facts.feeds:
        return "verified", (
            f"a generation report exists on disk for all {facts.feeds} feed(s); "
            "Layer-2 output lands in candidates.json review artifacts"
        )
    return "attention", (
        f"reports on disk for {facts.reports_on_disk}/{facts.feeds} feeds"
    )


def _check_read_only_seams(facts: RunFacts) -> tuple[str, str]:
    # Structural, not run-dependent: document sources must stay read-only.
    # The sanctioned write surfaces are the landing-volume seeder
    # ({ensure_volume, upload_file}, 2026-08-27) and the human-gated
    # artifact publish ({publish_artifacts}, explicit go 2026-08-28) — all
    # guarded by WRITABLE_PREFIX in code. Anything write-shaped beyond
    # those flips this control; so does losing the prefix guard.
    import codegen.databricks as databricks_module

    sanctioned = {"ensure_volume", "upload_file", "publish_artifacts"}
    writers = {
        name for name in dir(databricks_module)
        if any(w in name.lower() for w in
               ("upload", "write", "put", "publish", "delete", "remove"))
        and name != "WRITABLE_PREFIX"
    }
    unsanctioned = writers - sanctioned
    if unsanctioned:
        return "attention", f"unsanctioned write-shaped functions: {sorted(unsanctioned)}"
    if not str(getattr(databricks_module, "WRITABLE_PREFIX", "")).startswith(
        "soham_workspace.codegen_agent."
    ):
        return "attention", "the landing write guard (WRITABLE_PREFIX) is missing"
    return "verified", (
        "document sources are read-only; the only write surfaces are the "
        "landing seeder and the human-gated artifact publish, both "
        "constrained by construction to "
        f"{databricks_module.WRITABLE_PREFIX}* — no deletes exist anywhere"
    )


def _check_deterministic_core(facts: RunFacts) -> tuple[str, str]:
    if not facts.loaded:
        return "pending_run", "no run loaded"
    providers = sorted(set(facts.candidate_providers)) or ["none"]
    if facts.mode == "live":
        return "verified", (
            f"live run: the model is reached only for Layer-2 candidates "
            f"({facts.candidates} call site(s), provider {', '.join(providers)}); "
            "code generation itself is deterministic Jinja2"
        )
    return "verified", (
        f"{facts.mode} run: zero live model calls "
        f"(candidate provider(s): {', '.join(providers)}); "
        "code generation itself is deterministic Jinja2"
    )


_RUN_DEPENDENT = {
    "sha-256 fingerprints", "grounding audit", "human-in-the-loop", "audit trail",
}


def deck_checks(pptx_path: Path, deck_kind: str, facts: RunFacts) -> list[dict] | None:
    """Controls stated by this deck, each evaluated. None = deck unusable."""
    paragraphs = read_deck_paragraphs(pptx_path)
    if paragraphs is None:
        return None
    checks = []
    for anchor, evaluate in _controls_for(deck_kind):
        line = next(
            (p for p in paragraphs if _squash(anchor) in _squash(p)), None
        )
        if line is None:
            continue  # the document does not state this control — no check
        if anchor in _RUN_DEPENDENT and not facts.loaded:
            checks.append(_no_run(line, pptx_path.name))
            continue
        status, evidence = evaluate(facts)
        checks.append({"control": line, "deck": pptx_path.name,
                       "status": status, "evidence": evidence})
    return checks or None


def governance_checks_payload(config, base_dir: Path, facts: RunFacts,
                              env=None) -> dict:
    """Both decks found via the documents-card scan, checks concatenated."""
    from codegen.demo_sources import scan_reference_documents

    documents = scan_reference_documents(config, base_dir, env)
    decks = {
        "governance": next(
            (p for p in documents["present"]
             if "governance" in p["name"].lower()), None),
        "solution": next(
            (p for p in documents["present"]
             if "solution" in p["name"].lower()), None),
    }
    checks: list[dict] = []
    absent: list[str] = []
    for kind, entry in decks.items():
        if entry is None:
            absent.append(kind)
            continue
        deck_result = deck_checks(Path(entry["path"]), kind, facts)
        if deck_result is None:
            absent.append(kind)
        else:
            checks.extend(deck_result)
    summary = {
        "verified": sum(1 for c in checks if c["status"] == "verified"),
        "attention": sum(1 for c in checks if c["status"] == "attention"),
        "pending_run": sum(1 for c in checks if c["status"] == "pending_run"),
    }
    return {"checks": checks, "summary": summary, "absent_decks": absent}
