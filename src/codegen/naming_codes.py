"""post186: the EDO Naming Standards' Product (table 3.2) and Sub-Product (table 3.3)
codes READ FROM THE FRD, never a constant (Soham, 2026-11-09: "instead of using the
naming standards abbreviation descriptions to dynamically name, you put in ... NSP").

Both tables map a "Project / Use Case" to its acronym (transcribed under
``engineering_standards.product_codes`` / ``sub_product_codes``, each entry with the
phrases a document states it by, ``stated_as``).

- **Product**: the 3.2 entry the FRD names as the platform the data is ingested
  INTO (``product_target_words`` + the phrase: "ingested into Lakehouse", "Ingestion
  to DL"). A consumer mention ("for HEDIS consumption") is not the product. One
  code stated = that code; none or several = no code (the names that carry it stay
  open, flagged - the pipeline-name question asks).
- **Sub-product**: a 3.3 entry the FRD names anywhere, as a whole word / phrase
  ("CDC via HVR tool"). One = that code; several = no code (flagged, asked); none =
  the table's own "No Sub-Product" code (``no_sub_product_code``), FLAGGED - never
  written silently (Soham, 2026-11-09: "NSP with a flag").

Every found code carries the FRD line it rests on (citation rule). A config without
the tables keeps the older constants (``product_code`` / ``sub_product_code``)."""

from __future__ import annotations

import re
from collections.abc import Iterable

from codegen.config import EngineeringStandardsConfig, NamingCode
from codegen.contracts.frd import NamingEvidence

PRODUCT = "product"
SUB_PRODUCT = "sub_product"
_QUOTE_CAP = 160


def _phrase_re(phrase: str) -> str:
    words = [re.escape(w) for w in phrase.split()]
    return r"(?<![A-Za-z0-9])" + r"\s+".join(words) + r"(?![A-Za-z0-9])"


def _quote(line: str, start: int, end: int) -> str:
    line = " ".join(line.split())
    if len(line) <= _QUOTE_CAP:
        return line
    middle = (start + end) // 2
    lo = max(0, middle - _QUOTE_CAP // 2)
    return ("…" if lo else "") + line[lo:lo + _QUOTE_CAP] + "…"


def _find(lines: Iterable[tuple[str, str]], table: list[NamingCode],
          prefix: str = "") -> NamingEvidence | None:
    """Every entry of ``table`` the lines state (``prefix`` before the phrase),
    in document order: one code per entry, the first line that states it."""
    codes: list[str] = []
    entries: list[str] = []
    quotes: list[str] = []
    patterns = [(entry, re.compile(prefix + "(?:" + "|".join(
        _phrase_re(p) for p in entry.stated_as) + ")", re.IGNORECASE))
        for entry in table if entry.stated_as]
    for where, line in lines:
        flat = " ".join(line.split())
        for entry, pattern in patterns:
            if entry.code in codes:
                continue
            match = pattern.search(flat)
            if match is not None:
                codes.append(entry.code)
                entries.append(entry.entry)
                quotes.append(f"{where}: {_quote(flat, match.start(), match.end())!r}")
    if not codes:
        return None
    return NamingEvidence(codes=codes, entries=entries, quotes=quotes)


def find_naming(lines: list[tuple[str, str]], standards: EngineeringStandardsConfig
                ) -> dict[str, NamingEvidence]:
    """What the FRD's lines ((where, text) pairs) state of tables 3.2 / 3.3."""
    found: dict[str, NamingEvidence] = {}
    if standards.product_codes and standards.product_target_words:
        target = r"(?<![A-Za-z0-9])(?:" + "|".join(
            _phrase_re(w) for w in standards.product_target_words) + r")\s+(?:the\s+)?"
        product = _find(lines, standards.product_codes, target)
        if product is not None:
            found[PRODUCT] = product
    if standards.sub_product_codes:
        sub = _find(lines, standards.sub_product_codes)
        if sub is not None:
            found[SUB_PRODUCT] = sub
    return found


def resolve_codes(naming: dict[str, NamingEvidence], standards: EngineeringStandardsConfig
                  ) -> tuple[str | None, str | None, list[str]]:
    """(product code, sub-product code, flags) for a feed of an FRD whose
    ``naming`` evidence is given. None = no code (the names stay open)."""
    if not standards.product_codes and not standards.sub_product_codes:
        return (standards.product_code or None, standards.sub_product_code or None, [])
    flags: list[str] = []
    product = naming.get(PRODUCT)
    product_code: str | None = None
    if product is None:
        flags.append("naming_product_unstated: the FRD names no Naming Standards table 3.2 "
                     "entry as the platform it ingests into - the product part of the "
                     "pipeline / job / notebook names is left open")
    elif len(product.codes) > 1:
        flags.append(f"naming_product_ambiguous: the FRD names {len(product.codes)} table "
                     f"3.2 entries as ingestion targets {product.entries} - none picked: "
                     + "; ".join(product.quotes))
    else:
        product_code = product.codes[0]
        flags.append(f"naming_product:{product_code} - Naming Standards 3.2 "
                     f"'{product.entries[0]}', from the FRD: {product.quotes[0]}")
    sub = naming.get(SUB_PRODUCT)
    sub_code: str | None = None
    if sub is None:
        sub_code = standards.no_sub_product_code or None
        flags.append(f"naming_sub_product_unstated:{sub_code or ''} - the FRD names no Naming "
                     "Standards table 3.3 entry; the table's 'No Sub-Product' code"
                     + (" is used" if sub_code else " is not configured - left open"))
    elif len(sub.codes) > 1:
        flags.append(f"naming_sub_product_ambiguous: the FRD names {len(sub.codes)} table 3.3 "
                     f"entries {sub.entries} - none picked: " + "; ".join(sub.quotes))
    else:
        sub_code = sub.codes[0]
        flags.append(f"naming_sub_product:{sub_code} - Naming Standards 3.3 "
                     f"'{sub.entries[0]}', from the FRD: {sub.quotes[0]}")
    return product_code, sub_code, flags


def spec_codes(spec, standards: EngineeringStandardsConfig) -> tuple[str, str]:
    """The (product, sub-product) codes a name uses for ``spec`` ('' = open). A
    config without the tables keeps the older constants."""
    if not standards.product_codes and not standards.sub_product_codes:
        return standards.product_code, standards.sub_product_code
    return (getattr(spec, "product_code", None) or "",
            getattr(spec, "sub_product_code", None) or "")


__all__ = ["PRODUCT", "SUB_PRODUCT", "find_naming", "resolve_codes", "spec_codes"]
