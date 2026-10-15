"""The one way a leak-gate term is hashed (2026-10-15).

A term never enters git; its hash does. Three readers hash the same way:
the leak-ledger baseline (``docs/acfc/LEAK_LEDGER.md``, checked by
``tests/test_tracked_scrub.py``), ``tools/hit_lookup.py`` (classifying the
harness's per-hit records at home) and the ACFC harness's gate, which imports
:func:`term_sha256` so both sides agree byte for byte.

Normalization, in this order:

1. ``strip()`` — leading / trailing whitespace dropped;
2. ``casefold()`` — case-insensitive (``Foo`` == ``FOO``; stronger than lower());
3. Unicode NFC — composed form (``e`` + combining acute == ``é``);

then ``sha256`` of the UTF-8 bytes, lowercase hex (64 characters).

Caveat: a plain hash of a SHORT or low-cardinality term (a 6-digit id) can be
reversed by trying every candidate — exactly what ``tools/hit_lookup.py`` does
on purpose. A hash in git protects a term only as far as the term is
unguessable; the ledger hashes only terms that the tracked tree already holds.
"""

from __future__ import annotations

import hashlib
import unicodedata

STABLE = "strip, casefold, NFC, sha256 utf-8 hex"


def normalize_term(term: str) -> str:
    """The normalized form that is hashed (strip, casefold, NFC)."""
    return unicodedata.normalize("NFC", str(term).strip().casefold())


def term_sha256(term: str) -> str:
    """sha256 hex of :func:`normalize_term` — STABLE API (the harness imports it)."""
    return hashlib.sha256(normalize_term(term).encode("utf-8")).hexdigest()


__all__ = ["STABLE", "normalize_term", "term_sha256"]
