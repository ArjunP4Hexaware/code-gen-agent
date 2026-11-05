"""The model points, the code copies (post176; docs/PARSER_SELF_EXTENSION.md step 3).

A cell of the INGESTED FRD that the reader refused (several lines no grammar reads) and
that no other document fills: the layout model is asked WHICH LINE states one field -
never the value. The code copies that line (its value after the label when the line is
"<label>: <value>"), and the field's own vocabulary validates it: a file format must name
one of ``extractor.frd.format_tokens`` / ``generic_text_formats``, a delimiter must be a
character ``delimiter_char`` reads, a frequency a cadence word. Anything else, a line
outside the cell, or a line the stored text cut short is discarded - the field stays
open (the question is asked). The answer is cached per (field, cell text) in the runtime
layout cache, so a template asks once.

Soham, 2026-11-05: allowed for a refused cell of the ingested FRD / STTM - the only two
inputs; the model sees that one cell's lines, nothing else (no data row, no other file).
Every value it leads to is flagged ``frd_model_located:`` (the review copy lists it).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

LOCATABLE = ("file_format", "delimiter", "frequency")
TRUNCATED = "…"
_PAIR = re.compile(r"^\s*([^:]{1,60}?)\s*:\s*(.*)$")
_CADENCE = re.compile(r"\b(daily|weekly|monthly|quarterly|yearly|annual(?:ly)?|"
                      r"bi-?weekly|semi-?monthly|one time|adhoc|ad hoc|on demand)\b",
                      re.IGNORECASE)

SYSTEM_PROMPT = (
    "You locate ONE field inside ONE cell of a functional-requirements document. You "
    "receive the field's name and meaning and the cell's lines, numbered from 1. Respond "
    "with ONLY a JSON object {\"line\": <the number of the line that states the field>} - "
    "or {\"line\": null} when no line states it. Never rewrite, summarise or invent a "
    "value; never answer with text from the cell."
)


def cell_lines(text: str) -> list[str]:
    return [line for line in (text or "").splitlines() if line.strip()]


def build_request(field: str, meaning: str, lines: list[str]) -> dict:
    return {"field": field, "meaning": meaning,
            "lines": [{"n": i, "text": line} for i, line in enumerate(lines, start=1)]}


def copy_line(line: str) -> str:
    """The value a line states: after its label when it is "<label>: <value>"."""
    match = _PAIR.match(line)
    return (match.group(2) if match else line).strip()


def valid(field: str, value: str, config) -> bool:
    """The field's own vocabulary accepts the copied value."""
    if not value:
        return False
    frd = config.extractor.frd
    if field == "file_format":
        words = " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
        tokens = [" ".join(re.sub(r"[^a-z0-9]+", " ", t.lower()).split())
                  for t in [*frd.format_tokens, *frd.generic_text_formats]]
        return any(t and re.search(rf"\b{re.escape(t)}\b", words) for t in tokens)
    if field == "delimiter":
        from codegen.resolve.resolver import delimiter_char

        return delimiter_char(value, config.extractor.delimiter_words) is not None
    if field == "frequency":
        return _CADENCE.search(value) is not None
    return False


class CellLocator:
    """``locator(field, cell) -> (line number, value) | None`` for one refused cell
    (a StructuredValue dict: kind, table, row, label, text)."""

    def __init__(self, provider, cache_dir: Path | None, config) -> None:
        self.provider = provider
        self.cache_dir = Path(cache_dir) / "cell_locate" if cache_dir is not None else None
        self.config = config
        self.calls = 0

    def _key(self, field: str, lines: list[str]) -> str:
        return hashlib.sha256((field + "\0" + "\n".join(lines)).encode("utf-8")).hexdigest()[:24]

    def _ask(self, field: str, meaning: str, lines: list[str]) -> int | None:
        path = (self.cache_dir / f"{self._key(field, lines)}.json"
                if self.cache_dir is not None else None)
        if path is not None and path.is_file():
            return json.loads(path.read_text(encoding="utf-8")).get("line")
        ask = getattr(self.provider, "locate_line", None)
        if ask is None:
            return None
        self.calls += 1
        try:
            answer = ask(build_request(field, meaning, lines))
        except Exception:  # noqa: BLE001 - a failed call leaves the field open
            return None
        line = answer.get("line") if isinstance(answer, dict) else None
        line = line if isinstance(line, int) and not isinstance(line, bool) else None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"field": field, "line": line}) + "\n",
                            encoding="utf-8")
        return line

    def __call__(self, field: str, cell: dict, meaning: str = "") -> tuple[int, str] | None:
        if field not in LOCATABLE or (cell or {}).get("kind") != "multiline":
            return None
        text = str(cell.get("text") or "")
        lines = cell_lines(text)
        if len(lines) < 2:
            return None
        line = self._ask(field, meaning or field.replace("_", " "), lines)
        if line is None or not 1 <= line <= len(lines):
            return None
        if line == len(lines) and text.endswith(TRUNCATED):
            return None                    # the stored text cut that line short
        value = copy_line(lines[line - 1])
        return (line, value) if valid(field, value, self.config) else None
