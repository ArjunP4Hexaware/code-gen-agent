"""FRD gap handling — the fallback chain shared by the layout stage (the
`needs_layout` dialog) and the contract resolver (the CLI path).

Per field, when the FRD is silent:

* file format   ← STTM meta row ("File Format"), then the VDD FILES sheet
* delimiter     ← the same chain
* stage load strategy    ← STTM meta row "Load Strategy" when it states one
                            per layer, then the FAQ ``load_mode``
* standard load strategy ← STTM meta row only when stated per layer
* domain / subdomain      stay FRD-only (blank-and-flag if unstated)
* stage catalog / schema / tables: the STTM stage band is authoritative;
  never asked.

Every fill carries a provenance flag naming the source cell. Disagreement
between sources, or an ambiguous single source (one "Load Strategy" with no
layer, several VDD files of different formats), is a QUESTION for the
person — never a silent choice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from codegen.layout.discover import normalize

LOAD_STRATEGIES = ("Truncate and Load", "Append", "Upsert")
_STRATEGY_ALIASES = {
    "truncate and load": "Truncate and Load",
    "truncate load": "Truncate and Load",
    "truncate reload": "Truncate and Load",
    "full load": "Truncate and Load",
    "overwrite": "Truncate and Load",
    "append": "Append",
    "insert": "Append",
    "incremental": "Append",
    "upsert": "Upsert",
    "merge": "Upsert",
    "merge on keys": "Upsert",
}
# FAQ load_mode vocabulary -> LoadStrategy literal (inverse of faq._LOAD_STRATEGY_TO_MODE).
_LOAD_MODE_TO_STRATEGY = {
    "truncate_and_load": "Truncate and Load",
    "append": "Append",
    "merge_on_keys": "Upsert",
    "upsert": "Upsert",
}


@dataclass(frozen=True)
class Statement:
    """One document's statement of a field: the value, which document, the cell."""

    value: str
    source: str      # "STTM" | "VDD" | "FRD" | "FAQ" | "user"
    cell: str


def canonical_strategy(text: str | None) -> str | None:
    """A LoadStrategy literal for any spelling the documents use, else None."""
    key = normalize(text)
    if not key:
        return None
    for literal in LOAD_STRATEGIES:
        if key == normalize(literal):
            return literal
    return _STRATEGY_ALIASES.get(key)


def parse_load_strategy_text(text: str | None, markers: dict[str, list[str]]) -> dict[str, str]:
    """Parse an STTM "Load Strategy" cell.

    ``{"stage": v, "standard": v}`` when the text states one per layer
    ("STG: Append; STD: Upsert"), ``{"any": v}`` when it states ONE value
    with no layer ("Append" — ambiguous: the person says which layer), ``{}``
    when nothing parses. ``markers`` = extractor.frd.target_schema_markers.
    """
    if not text:
        return {}
    marker_layer = {normalize(m): layer for layer, words in markers.items() for m in words}
    out: dict[str, str] = {}
    unlabelled: list[str] = []
    for segment in re.split(r"[;\n]+", text):
        segment = segment.strip()
        if not segment:
            continue
        match = re.match(r"^\s*([A-Za-z][A-Za-z ()]{0,20}?)\s*[:=\-]\s*(.+)$", segment)
        layer = marker_layer.get(normalize(match.group(1))) if match else None
        if match and layer:
            value = canonical_strategy(match.group(2))
            if value:
                out[layer] = value
            continue
        value = canonical_strategy(segment)
        if value:
            unlabelled.append(value)
    if out:
        return out
    if len(set(unlabelled)) == 1:
        return {"any": unlabelled[0]}
    return {}


def strategy_from_faq(faq) -> Statement | None:
    """The FAQ's load_mode as a stage load strategy, when answered."""
    answer = getattr(faq, "load_mode", None)
    if answer is None or answer.source == "unknown":
        return None
    literal = _LOAD_MODE_TO_STRATEGY.get(str(answer.value))
    if literal is None:
        return None
    return Statement(literal, "FAQ", f"load_mode = {answer.value!r} (source: {answer.source})")


def same_value(a: str | None, b: str | None) -> bool:
    """Agreement as the cross-checks judge it: equal or one contains the other."""
    na, nb = normalize(a), normalize(b)
    return bool(na) and bool(nb) and (na == nb or na in nb or nb in na)


_BARE_EXTENSION_RE = re.compile(r"^\.?[A-Za-z0-9]{2,5}$")


def is_extension_only(value: str | None) -> bool:
    """True for a "file format" cell that names only a file EXTENSION
    (".dat", ".txt") — it says how the file is named, not how it is laid
    out."""
    text = (value or "").strip()
    return text.startswith(".") and bool(_BARE_EXTENSION_RE.match(text))


def format_statements(statements: list[Statement]) -> list[Statement]:
    """File-format statements worth comparing (M9.0): an extension-only cell
    (the real pair-1 STTM reads ".dat") is set aside whenever another
    document states a format — it cannot disagree with "Fixed Width". When it
    is the ONLY statement it stays (the last resort, as before)."""
    real = [s for s in statements if not is_extension_only(s.value)]
    return real or statements


def distinct(statements: list[Statement]) -> list[Statement]:
    """Statements with pairwise-different values (first spelling kept)."""
    out: list[Statement] = []
    for s in statements:
        if not any(same_value(s.value, o.value) for o in out):
            out.append(s)
    return out


def fill_flag(field: str, statement: Statement) -> str:
    return (f"frd_unstated:{field} source_used:{statement.source} {statement.cell}: "
            f"{statement.value!r}")


# ------------------------------------------------ M14: normalize, then compare


@dataclass(frozen=True)
class Canon:
    """What a candidate text MEANS for its field.

    ``key``: the canonical value (``csv``, ``fixed_width``, ``","``,
    ``weekly``…), or None when the vocabulary does not know the text — then
    the raw text is compared as before (``same_value``). ``weak``: yields to
    any other candidate (an extension that fits any layout, a vague cadence).
    ``drop``: not a candidate at all (a transport phrase, a date schedule),
    with the reason for the flag."""

    key: str | None
    text: str
    weak: bool = False
    drop: str | None = None


_TRAILING_FILES_RE = re.compile(r"\s+files?$")
_DATE_RE = re.compile(r"\b\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}\b")


def _norm(text: str | None) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return _TRAILING_FILES_RE.sub("", value).rstrip(" .:;").strip()   # a LEADING dot is kept


def _phrase_in(spelling: str, text: str) -> bool:
    """``spelling`` occurs in ``text`` as a whole phrase (no letter / digit
    touching either end)."""
    pattern = r"(?<![a-z0-9])" + re.escape(spelling) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _lookup(table: dict[str, list[str]], text: str) -> str | None:
    """The key whose LONGEST spelling occurs in ``text`` as a whole phrase."""
    best: tuple[int, str] | None = None
    for key, spellings in table.items():
        for spelling in spellings:
            s = _norm(spelling) if spelling.strip() not in (",", "|", ";") else spelling.strip()
            if s and (s == text or _phrase_in(s, text)) and (best is None or len(s) > best[0]):
                best = (len(s), key)
    return best[1] if best else None


def canonical(field: str, value: str | None, vocabulary) -> Canon:
    """``field``: file_format | delimiter | frequency (anything else: unknown)."""
    text = _norm(value)
    if field == "file_format":
        vocab = vocabulary.file_format
        if text in {_norm(p) for p in vocab.not_formats}:
            return Canon(None, text, drop="describes how the data is moved, not a file format")
        if is_extension_only(text):
            ext = "." + text.lstrip(".")
            kind = vocab.extensions.get(ext)
            if kind == "any":
                return Canon("any", text, weak=True)
            if kind:
                return Canon(kind, text)
        kind = _lookup(vocab.canonical, text)
        if kind:
            return Canon(kind, text)
        if any(_phrase_in(_norm(p), text) for p in vocab.not_formats):
            return Canon(None, text, drop="describes how the data is moved, not a file format")
        return Canon(None, text)
    if field == "delimiter":
        raw = str(value or "").strip()
        for key, spellings in vocabulary.delimiter.canonical.items():
            if raw in spellings or raw == key:
                return Canon(key, text)
        return Canon(_lookup(vocabulary.delimiter.canonical, text), text)
    if field == "frequency":
        vocab = vocabulary.frequency
        if len(_DATE_RE.findall(str(value or ""))) >= vocab.schedule_min_dates:
            return Canon(None, text, drop="lists dates — a load schedule, not a frequency")
        if text in {_norm(v) for v in vocab.vague}:
            return Canon("vague", text, weak=True)
        return Canon(_lookup(vocab.canonical, text), text)
    return Canon(None, text)


def _compatible(a: Canon, b: Canon, refines: dict[str, str]) -> bool:
    if a.key is None or b.key is None:
        return same_value(a.text, b.text)
    return a.key == b.key or refines.get(a.key) == b.key or refines.get(b.key) == a.key


@dataclass
class Reconciled:
    """``kept``: one representative per group of mutually compatible
    candidates — ONE means the documents agree, more is a real question.
    ``dropped``: (statement, reason) for the flag."""

    kept: list[Statement]
    dropped: list[tuple[Statement, str]]


def reconcile(field: str, statements: list[Statement], vocabulary) -> Reconciled:
    refines = vocabulary.file_format.refines if field == "file_format" else {}
    dropped: list[tuple[Statement, str]] = []
    entries: list[tuple[Statement, Canon]] = []
    for statement in statements:
        canon = canonical(field, statement.value, vocabulary)
        if canon.drop:
            dropped.append((statement, canon.drop))
        else:
            entries.append((statement, canon))
    strong = [e for e in entries if not e[1].weak]
    if strong and len(strong) < len(entries):
        for statement, canon in entries:
            if canon.weak and canon.key == "vague":
                dropped.append((statement, "a vague cadence — yields to the specific one stated "
                                           "elsewhere"))
        entries = strong               # an extension-only cell yields silently (M9.0)
    groups: list[list[tuple[Statement, Canon]]] = []
    for entry in entries:
        for group in groups:
            if all(_compatible(entry[1], other[1], refines) for other in group):
                group.append(entry)
                break
        else:
            groups.append([entry])

    def specificity(entry: tuple[Statement, Canon]) -> tuple[int, int]:
        statement, canon = entry
        refined = 1 if canon.key in refines else 0
        return (1 if statement.source == "FRD" else 0, refined)

    kept = [max(group, key=specificity)[0] for group in groups]
    return Reconciled(kept=kept, dropped=dropped)


def dropped_flag(field_key: str, statement: Statement, reason: str) -> str:
    return (f"candidate_dropped:{field_key} — {statement.value!r} ({statement.source} "
            f"{statement.cell}) {reason}")


__all__ = [
    "LOAD_STRATEGIES",
    "Canon",
    "Reconciled",
    "Statement",
    "canonical",
    "canonical_strategy",
    "distinct",
    "dropped_flag",
    "fill_flag",
    "reconcile",
    "format_statements",
    "is_extension_only",
    "parse_load_strategy_text",
    "same_value",
    "strategy_from_faq",
]
