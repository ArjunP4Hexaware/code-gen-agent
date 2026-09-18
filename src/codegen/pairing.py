"""Pairing by CONTENT (M8.2): which FRD / Vendor Data Dictionary belongs to
the chosen STTM.

Ticket numbers cannot decide it — in the ACFC inventory four pairs share one
ticket (docs/acfc/RETROFIT_LOG.md §7). So every candidate is scored against
what the STTM itself says, with the same deterministic readers the run uses
(synonyms only — never a model):

  FRD   feed / object name found in the STTM's header region; target tables
        and schemas against the STTM's stage / standard bands; file name
        patterns against the STTM's file-details rows (CCYY → YYYY)
  VDD   FILES-sheet file patterns / format / delimiter / cadence against the
        STTM's file rows and meta rows; one-sheet-per-table dictionaries by
        sheet name against the STTM's tables

plus two weak NAME signals — a shared ticket number and a shared name stem —
worth less than any content signal. A candidate is paired only when it wins
by ``inputs.pairing.margin`` and reaches ``min_score``; otherwise the top
candidates are returned as a QUESTION (the layout dialog / the CLI answers
file) and nothing is paired. An explicit ``demo.pairing_map`` entry still
overrides everything. Every signal carries the cells it rests on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config
from codegen.demo_sources import _pair_key, _token_prefix, auto_pair_document, document_stem
from codegen.layout.discover import normalize

_NAME_SIGNALS = ("ticket", "name_stem")


@dataclass(frozen=True)
class PairSignal:
    name: str
    weight: float
    detail: str


@dataclass(frozen=True)
class PairCandidate:
    name: str
    score: float
    signals: tuple[PairSignal, ...] = ()

    def summary(self) -> str:
        return "; ".join(f"{s.name} (+{s.weight:g}): {s.detail}" for s in self.signals) \
            or "no content in common"


@dataclass(frozen=True)
class PairDecision:
    kind: str                       # "frd" | "vdd"
    sttm: str
    chosen: str | None
    rule: str | None                # "pairing_map" | "content" | None
    candidates: tuple[PairCandidate, ...] = ()
    reason: str = ""

    min_score: float = 0.0

    @property
    def ambiguous(self) -> bool:
        """Undecided AND worth asking. An FRD is required, so any scored
        candidate is worth showing; a VDD is optional, so only candidates
        strong enough to have paired (a tie between real contenders)."""
        if self.chosen is not None or not self.candidates:
            return False
        best = self.candidates[0].score
        return best > 0 if self.kind == "frd" else best >= self.min_score

    def question(self) -> dict:
        """The decision as a layout-dialog ``choice`` question (same shape
        ``LayoutQuestion.as_dict`` produces; answered through ``gaps``)."""
        label = "FRD" if self.kind == "frd" else "Vendor Data Dictionary"
        return {
            "document": self.kind, "key": f"pair.{self.kind}", "sheet": None, "layer": None,
            "role": f"pair.{self.kind}", "kind": "choice",
            "title": f"Which {label} belongs to {self.sttm}?",
            "reason": self.reason,
            "hint": ("Scored by content: feed / object name, target schema and tables, file "
                     "patterns; ticket number and file name are weak signals only."),
            "header": [],
            "candidates": [{"value": c.name, "source": f"candidate {i} · score {c.score:g}",
                            "cell": c.summary()}
                           for i, c in enumerate(self.candidates, start=1)],
            "suggested": None, "suggested_reason": "",
        }


# -- facts ----------------------------------------------------------------------------

@dataclass
class _Facts:
    texts: list[tuple[str, str]] = field(default_factory=list)       # (citation, value)
    tables: dict[str, str] = field(default_factory=dict)            # normalized -> citation
    schemas: dict[str, str] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)             # canonical name -> citation
    meta: dict[str, tuple[str, str]] = field(default_factory=dict)  # key -> (value, citation)
    names: list[str] = field(default_factory=list)                  # feed / object names
    raw_tables: list[str] = field(default_factory=list)             # as written


_cache: dict[tuple, _Facts] = {}


_NAME_STEM_MIN = 4


def _canonical_file(name: str) -> str:
    """The extractor's comparison form (date placeholders CCYY → YYYY), then
    ``normalize`` — an FRD may write a file name with spaces where the STTM
    uses underscores."""
    return normalize(name.strip().lower().replace("ccyy", "yyyy"))


def _name_match(name: str, candidate: str) -> bool:
    """Stricter than the layout cross-check's stem match, because here a
    false positive pairs the WRONG documents: the whole name inside the text,
    or EVERY token of the name matching a word — short tokens exactly
    ("FEED_8" never matches "Feed Type"), longer ones by shared stem
    ("Accumulators" ↔ "ACCUM")."""
    a, b = normalize(name), normalize(candidate)
    if not a or not b:
        return False
    if a in b:
        return True
    words = b.split()

    def hit(token: str) -> bool:
        if len(token) < _NAME_STEM_MIN:
            return token in words
        return any(len(w) >= _NAME_STEM_MIN and (w.startswith(token) or token.startswith(w))
                   for w in words)

    tokens = a.split()
    return any(len(t) >= _NAME_STEM_MIN for t in tokens) and all(hit(t) for t in tokens)


def _key(path: Path, kind: str, extra: tuple = ()) -> tuple:
    stat = path.stat()
    return (kind, str(path), stat.st_mtime_ns, stat.st_size, *extra)


def sttm_facts(path: Path, config: Config, base_dir: Path) -> _Facts:
    key = _key(path, "sttm")
    if key in _cache:
        return _cache[key]
    from codegen.layout.resolve import _sttm_facts, resolve_workbook

    doc, workbook = resolve_workbook(path, config, provider=None, base_dir=base_dir)
    raw = _sttm_facts(doc.profile, workbook, config)
    facts = _Facts(texts=list(raw["texts"]))
    for entry in raw["sheet_tables"]:
        for layer in ("stage", "standard"):
            if entry.get(f"{layer}_table"):
                facts.raw_tables.append(entry[f"{layer}_table"])
                facts.tables[normalize(entry[f"{layer}_table"])] = (
                    f"{entry['sheet']} {layer} band")
            if entry.get(f"{layer}_schema"):
                facts.schemas[normalize(entry[f"{layer}_schema"])] = (
                    f"{entry['sheet']} {layer} band")
    for name, citation in raw["files"]:
        facts.files[_canonical_file(name)] = citation
    for meta_key, (value, citation) in raw["meta"].items():
        facts.meta[meta_key] = (value, citation)
    _cache[key] = facts
    return facts


def frd_facts(path: Path, config: Config, base_dir: Path) -> _Facts:
    key = _key(path, "frd")
    if key in _cache:
        return _cache[key]
    from codegen.contracts.frd import FrdContract

    if path.suffix.lower() == ".docx":
        from codegen.extract.frd_docx import read_frd
        from codegen.layout.resolve import resolve_frd

        doc, content = resolve_frd(path, config, provider=None, base_dir=base_dir)
        contract = read_frd(content, doc.profile, config, document_name=path.name,
                            generated_date="1970-01-01")
    else:
        contract = FrdContract.model_validate_json(path.read_text(encoding="utf-8"))
    facts = _Facts()
    for index, feed in enumerate(contract.feeds):
        where = f"{path.name} feeds[{index}]"
        if feed.feed_name:
            facts.names.append(feed.feed_name)
        for layer, target in (("stage", feed.stage_target), ("standard", feed.standard_target)):
            if target is None:
                continue
            for table in target.tables or []:
                facts.tables[normalize(table)] = f"{where}.{layer}_target.tables"
            if target.schema_name:
                facts.schemas[normalize(target.schema_name)] = f"{where}.{layer}_target.schema"
        for pattern in feed.file_name_patterns or []:
            facts.files[_canonical_file(pattern)] = f"{where}.file_name_patterns"
        for meta_key in ("file_format", "delimiter", "frequency"):
            value = getattr(feed, meta_key, None)
            if value:
                facts.meta.setdefault(meta_key, (value, f"{where}.{meta_key}"))
    _cache[key] = facts
    return facts


def vdd_facts(path: Path, config: Config, base_dir: Path, sttm_tables: tuple[str, ...]) -> _Facts:
    key = _key(path, "vdd", sttm_tables)
    if key in _cache:
        return _cache[key]
    from openpyxl.utils import get_column_letter

    from codegen.layout.profile import Role
    from codegen.layout.resolve import _vdd_facts, resolve_workbook, text

    doc, workbook = resolve_workbook(path, config, provider=None, base_dir=base_dir,
                                     document="vdd", sttm_tables=list(sttm_tables))
    facts = _Facts()
    for meta_key, values in _vdd_facts(doc.profile, workbook).items():
        if values:
            facts.meta[meta_key] = values[0]
    for sp in doc.profile.sheets:
        if sp.kind == "vdd_fields":
            facts.tables[normalize(sp.name)] = f"{path.name} sheet {sp.name!r}"
        band = sp.band("files") if sp.kind == "vdd_files" and sp.header_row else None
        col = band.column(Role.FILE_PATTERN) if band else None
        if col is None:
            continue
        rows = workbook[sp.name].iter_rows(min_row=sp.header_row + 1, values_only=True)
        for row_index, row in enumerate(rows, start=sp.header_row + 1):
            value = text(row[col - 1]) if col - 1 < len(row) else ""
            if value:
                facts.files[_canonical_file(value)] = (
                    f"{sp.name}!{get_column_letter(col)}{row_index}")
    _cache[key] = facts
    return facts


# -- scoring --------------------------------------------------------------------------

def _name_signals(sttm_name: str, candidate: str, weights: dict[str, float]) -> list[PairSignal]:
    signals = []
    shared = _pair_key(sttm_name) & _pair_key(candidate)
    if shared:
        signals.append(PairSignal("ticket", weights["ticket"],
                                  f"both names carry {', '.join(sorted(shared))}"))
    if _token_prefix(sttm_name) and _token_prefix(sttm_name) == _token_prefix(candidate):
        signals.append(PairSignal("name_stem", weights["name_stem"],
                                  f"names share the stem {' '.join(_token_prefix(sttm_name))!r}"))
    return signals


def _overlap(a: dict[str, str], b: dict[str, str]) -> list[str]:
    return [f"{k!r} ({a[k]} ↔ {b[k]})" for k in sorted(set(a) & set(b)) if k]


def score_frd(sttm: _Facts, frd: _Facts, weights: dict[str, float]) -> list[PairSignal]:
    signals = []
    for name in frd.names:
        hit = next(((cit, value) for cit, value in sttm.texts if _name_match(name, value)), None)
        if hit:
            signals.append(PairSignal("feed_name", weights["feed_name"],
                                      f"{name!r} ↔ {hit[1]!r} at {hit[0]}"))
            break
    # The one-block / many-files FRD shape lists FILE names under "Target Table
    # Name" (docs/acfc/SHAPES_FOR_PORT.md) — so its tables also meet the files.
    frd_files = {**frd.tables, **frd.files}
    for label, a, b in (("tables", frd.tables, sttm.tables), ("schema", frd.schemas, sttm.schemas),
                        ("file_patterns", frd_files, sttm.files)):
        common = _overlap(a, b)
        if common:
            signals.append(PairSignal(label, weights[label], "; ".join(common[:3])))
    return signals


def score_vdd(sttm: _Facts, vdd: _Facts, weights: dict[str, float]) -> list[PairSignal]:
    signals = []
    for label, a, b in (("file_patterns", vdd.files, sttm.files),
                        ("tables", vdd.tables, sttm.tables)):
        common = _overlap(a, b)
        if common:
            signals.append(PairSignal(label, weights[label], "; ".join(common[:3])))
    for meta_key in ("file_format", "delimiter", "frequency"):
        if meta_key in sttm.meta and meta_key in vdd.meta and (
                normalize(sttm.meta[meta_key][0]) == normalize(vdd.meta[meta_key][0])):
            signals.append(PairSignal(
                f"meta_{meta_key}", weights["meta"],
                f"{sttm.meta[meta_key][0]!r} at {sttm.meta[meta_key][1]} ↔ "
                f"{vdd.meta[meta_key][1]}"))
    return signals


def decide(kind: str, sttm_name: str, scored: list[PairCandidate], config: Config) -> PairDecision:
    knobs = config.inputs.pairing
    ranked = sorted(scored, key=lambda c: (-c.score, c.name))
    top = tuple(ranked[: knobs.top_candidates])
    if not ranked or ranked[0].score <= 0:
        return PairDecision(kind, sttm_name, None, None, top, "no candidate shares any content")
    if not any(s.name not in _NAME_SIGNALS for c in ranked for s in c.signals):
        # No document says anything in common: only the names speak, and the
        # pre-M8 name rules decide (unique shared ticket, else unique stem).
        legacy = auto_pair_document(sttm_name, [c.name for c in ranked])
        if legacy is not None:
            return PairDecision(kind, sttm_name, legacy[0], legacy[1], top,
                                f"no content signal; names alone: {legacy[1]}")
        return PairDecision(kind, sttm_name, None, None, top,
                            "no content signal and the names do not single one out")
    best = ranked[0]
    runner_up = ranked[1].score if len(ranked) > 1 else 0.0
    if best.score >= knobs.min_score and best.score - runner_up >= knobs.margin:
        legacy = auto_pair_document(sttm_name, [c.name for c in ranked])
        # The rule names what decided: a name rule when it alone would have
        # picked the same document, "content" when the documents had to speak.
        rule = legacy[1] if legacy is not None and legacy[0] == best.name else "content"
        return PairDecision(kind, sttm_name, best.name, rule, top,
                            f"{best.name} scores {best.score:g}, next {runner_up:g} "
                            f"(margin ≥ {knobs.margin:g})")
    return PairDecision(
        kind, sttm_name, None, None, top,
        f"no candidate wins by the margin: best {best.score:g}, next {runner_up:g} "
        f"(need ≥ {knobs.min_score:g} and a lead of {knobs.margin:g})",
        min_score=knobs.min_score)


def pair_by_content(kind: str, sttm_path: Path, candidates: dict[str, Path], config: Config,
                    base_dir: Path, explicit_map: dict[str, str] | None = None) -> PairDecision:
    """Decide the ``kind`` ("frd" | "vdd") companion of ``sttm_path`` among
    ``candidates`` (name -> local path). A candidate that cannot be read
    scores on its name alone — one unreadable file never blocks pairing."""
    sttm_name = sttm_path.name
    names = [n for n in candidates if n != sttm_name]
    explicit = {document_stem(k): document_stem(v) for k, v in (explicit_map or {}).items()}
    mapped = explicit.get(document_stem(sttm_name))
    by_stem = {document_stem(n): n for n in names}
    if mapped and mapped in by_stem:
        return PairDecision(kind, sttm_name, by_stem[mapped], "pairing_map", (),
                            "explicit pairing_map entry")
    weights = config.inputs.pairing.weights
    try:
        sttm = sttm_facts(sttm_path, config, base_dir)
    except Exception:  # noqa: BLE001 — an unreadable STTM still pairs by name
        sttm = _Facts()
    scored = []
    for name in names:
        signals: list[PairSignal] = []
        try:
            if kind == "frd":
                signals = score_frd(sttm, frd_facts(candidates[name], config, base_dir), weights)
            else:
                facts = vdd_facts(candidates[name], config, base_dir, tuple(sttm.raw_tables))
                signals = score_vdd(sttm, facts, weights)
        except Exception:  # noqa: BLE001, S110 — name signals below still apply
            pass
        signals = [*signals, *_name_signals(sttm_name, name, weights)]
        scored.append(PairCandidate(name, sum(s.weight for s in signals), tuple(signals)))
    return decide(kind, sttm_name, scored, config)
