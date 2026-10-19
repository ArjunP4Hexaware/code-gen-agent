"""One spelling per answers key (post74, D1 post73 item 5).

pair_04 asked ``feeds[0].Delimiter`` while pair_10 asked ``feeds[0].delimiter``:
the live layout model claimed an FRD field under its HEADER LABEL, and the
claimed path became the question's key. A key names a ROLE (the contract's
field name), never a label. :func:`canonical_key` is the one normaliser: the
key's path after its scope (``feeds[<i>].``, ``feeds.<feed>.``, ``run.``) is
lowercased and every run of other characters becomes ``_`` — a bracketed
index or name (``columns[2]``, ``fields[Amount (01)]``) and a ``#<suffix>``
are kept as written. The layout stage applies it to every path a model (or a
person) claims; the answers file is read through it, so either spelling
answers the question."""

from __future__ import annotations

import re

_SCOPED = re.compile(r"^(feeds\[\d+\]|feeds\.[^.\[\]]+|run)\.(.+)$")
_BRACKETS = re.compile(r"(\[[^\]]*\])")
_OTHER = re.compile(r"[^a-z0-9_]+")


def _word(segment: str) -> str:
    return _OTHER.sub("_", segment.strip().lower()).strip("_")


def canonical_key(key: str) -> str:
    """``key`` with its path spelled as role names (see the module
    docstring); a key outside the three scopes is returned unchanged."""
    text = str(key).strip()
    base, hash_mark, suffix = text.partition("#")
    match = _SCOPED.match(base)
    if match is None:
        return text
    head, path = match.groups()
    parts = []
    for piece in _BRACKETS.split(path):
        if piece.startswith("["):
            parts.append(piece)
        else:
            parts.append(".".join(_word(s) if s else s for s in piece.split(".")))
    return f"{head}.{''.join(parts)}" + (hash_mark + suffix if hash_mark else "")


def canonical_keys(mapping: dict) -> dict:
    """``mapping`` with every key through :func:`canonical_key`; a key already
    in canonical form wins over a differently spelled duplicate."""
    out: dict = {}
    for key, value in mapping.items():
        canonical = canonical_key(str(key))
        if canonical not in out or str(key) == canonical:
            out[canonical] = value
    return out


__all__ = ["canonical_key", "canonical_keys"]
