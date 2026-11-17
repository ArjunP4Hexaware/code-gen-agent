"""Document text inside a ONE-line comment (post159, P1-4 / CS-2).

Moved here from ``emit/metadata_inserts.py`` when that file was retired (post194):
the notebook, the emitter and notebook v2 still print banners through it.
"""

from __future__ import annotations

from codegen.contracts.frd import banner_text_problem


def _one_line(text) -> str:
    return " ".join(str(text).split())


def comment1(value) -> str:
    """post159 (P1-4, CS-2): document text placed in a ONE-line comment (``#`` /
    ``--``), defence in depth behind the contract's single-line rule
    (``contracts.frd.BannerText``). A value that is already one printable line
    is returned UNCHANGED (byte-stable banners); one holding a line break or a
    control character is collapsed by :func:`_one_line`, each refused character
    read as a space - it can never end the comment it sits in. Any value is
    read as ``str(value)``, exactly what the template printed before."""
    text = str(value)
    if banner_text_problem(text) is None:
        return text
    return _one_line("".join(" " if banner_text_problem(ch) else ch for ch in text))


__all__ = ["comment1"]
