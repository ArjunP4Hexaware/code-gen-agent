"""The document parser as a CHILD PROCESS (M9.3, APP_CHOOSER_BUG).

Opening a workbook is CPU- and memory-bound work of unknown size — a client
sheet may declare 1,048,538 rows — and inside the App it ran on the request
path: selecting one STTM parsed every other workbook of the input folders,
the process starved and EVERY endpoint timed out until a restart. A thread
cannot be stopped; a process can. So everything that opens a document for the
chooser runs here, one request per line, and the parent kills the process when
a file exceeds its time budget.

    python -m codegen.layout.docworker --config-json <the parent's config, as JSON>

stdin  : one JSON object per line — {"path": <local file>, "name": <file name>}
stdout : {"ready": true} once the config is loaded, then one JSON object per
         request line — {"state", "reason", "facts"}
         state = sttm | vdd | unclassified | frd | unreadable

Nothing but those lines is written to stdout (warnings go to stderr).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

UNREADABLE = "unreadable"
_SUFFIX_KIND = {".docx": "frd", ".json": "frd"}


def read_document(local: Path, name: str, config, base_dir: Path) -> dict:
    """{state, reason, facts} of one document: a workbook's kind by content
    (``codegen.layout.classify``), and the pairing facts of an STTM / VDD /
    FRD (``codegen.pairing``)."""
    from codegen.layout.classify import classify_workbook
    from codegen.layout.size import WorkbookTooLarge, check_workbook_size
    from codegen.pairing import document_facts, facts_to_dict

    suffix = Path(name).suffix.lower()
    if suffix == ".xlsx":
        # M11: the cheap question first — a workbook over the cap is a
        # verdict, not a parse that outlives its budget and is killed.
        try:
            check_workbook_size(local, config.inputs.max_workbook_cells,
                                config.extractor.used_range_empty_rows)
        except WorkbookTooLarge as exc:
            return {"state": UNREADABLE, "reason": str(exc), "facts": None}
        verdict = classify_workbook(local, config.extractor)
        if verdict.reason.startswith("could not be read"):
            return {"state": UNREADABLE, "reason": verdict.reason, "facts": None}
        state, reason = verdict.kind, verdict.reason
    else:
        state, reason = _SUFFIX_KIND.get(suffix, "unclassified"), "an FRD document / contract"
    facts = None
    if state in ("sttm", "vdd", "frd"):
        with contextlib.suppress(Exception):          # facts are an optimisation, never a state
            facts = facts_to_dict(document_facts(state, local, config, base_dir))
    return {"state": state, "reason": reason, "facts": facts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codegen.layout.docworker", description=__doc__)
    # The parent's config AS IT IS IN MEMORY (overlays, env, test edits), dumped
    # by alias — not a path the child would have to resolve the same way.
    parser.add_argument("--config-json", required=True)
    parser.add_argument("--base-dir", default=".")
    args = parser.parse_args(argv)
    from codegen.config import Config

    config = Config.model_validate_json(Path(args.config_json).read_text(encoding="utf-8"))
    base_dir = Path(args.base_dir)
    out = sys.stdout
    # Anything a library prints must not corrupt the line protocol.
    sys.stdout = sys.stderr
    # The readers' imports are paid for HERE, inside the start budget — not by
    # the first document's.
    from codegen import pairing  # noqa: F401
    from codegen.layout import classify  # noqa: F401

    out.write(json.dumps({"ready": True}) + "\n")
    out.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            result = read_document(Path(request["path"]), request["name"], config, base_dir)
        except Exception as exc:  # noqa: BLE001 — every failure is an answer, never a crash
            result = {"state": UNREADABLE, "facts": None,
                      "reason": f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
                      if str(exc) else type(exc).__name__}
        out.write(json.dumps(result, ensure_ascii=False) + "\n")
        out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
