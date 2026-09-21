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


__all__ = [
    "LOAD_STRATEGIES",
    "Statement",
    "canonical_strategy",
    "distinct",
    "fill_flag",
    "format_statements",
    "is_extension_only",
    "parse_load_strategy_text",
    "same_value",
    "strategy_from_faq",
]
