"""The unfamiliar-shapes report (post173; docs/PARSER_SELF_EXTENSION.md step 4).

Every run already records what its readers could not place: the FRD contract's
``structured`` entries (a cell refused as several lines, a nested table, per-file
blocks, a pointer, a label-prefixed value - with the FRD row label and the table /
row) and the STTM contract's ``layout.unresolved`` lines (a role no header placed).
This module adds them up ACROSS runs - which shape, which field / role, how many runs,
the last one - so the shapes that recur are extended first (vocabulary in config, a
grammar in code), instead of being rediscovered run by run.

Coordinates and vocabulary only: the FRD row label (the document's own label) and the
table / row; never a cell's text, never an STTM sheet name (it can carry client terms -
an unresolved role is reported by layer and role). Reads run folders through the storage
backends (``local:`` / ``workspace:`` / ``volume:``), so the App's outputs role works.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

RUN_FOLDER = re.compile(r"demo_\d{8}_\d{6}|run_[\w.-]+")
FRD_FILE = "frd.contract.json"
STTM_FILES = ("extracted_sttm.contract.json", "sttm.contract.json")
_FEED = re.compile(r"^feeds\[\d+\]\.")
_UNRESOLVED = re.compile(r"^(?P<sheet>.+)/(?P<layer>[a-z_]+)/(?P<role>[a-z_|]+)\s*[:—-]")


@dataclass(frozen=True)
class Shape:
    document: str        # "FRD" | "STTM"
    kind: str            # a StructuredValue kind, or "unresolved_role"
    field: str           # the FRD contract field (no feed index) / "<layer>/<role>"
    where: str           # "table 6 row 4 ('Object/data Format')" / "" for an STTM role
    run: str


def run_shapes(run: str, frd: dict | None, sttm: dict | None) -> list[Shape]:
    """The shapes one run's two contracts record."""
    shapes: list[Shape] = []
    for key, value in ((frd or {}).get("structured") or {}).items():
        if not isinstance(value, dict) or not value.get("kind"):
            continue
        label = value.get("label")
        where = (f"table {value.get('table')} row {value.get('row')}"
                 + (f" ({label!r})" if label else ""))
        shapes.append(Shape("FRD", str(value["kind"]), _FEED.sub("", key), where, run))
    layout = (sttm or {}).get("layout") or {}
    for line in layout.get("unresolved") or []:
        match = _UNRESOLVED.match(str(line))
        if match is not None:
            shapes.append(Shape("STTM", "unresolved_role",
                                f"{match.group('layer')}/{match.group('role')}", "", run))
    return list(dict.fromkeys(shapes))            # a derived feed repeats its FRD's cell


def collect(backend) -> list[Shape]:
    """Every run folder under ``backend``'s root (newest last)."""
    shapes: list[Shape] = []
    runs = sorted(e.name for e in backend.list("") if e.is_dir and RUN_FOLDER.fullmatch(e.name))
    for run in runs:
        frd = _json(backend, f"{run}/{FRD_FILE}")
        sttm = next((d for name in STTM_FILES if (d := _json(backend, f"{run}/{name}"))), None)
        shapes += run_shapes(run, frd, sttm)
    return shapes


def _json(backend, rel: str) -> dict | None:
    try:
        data = json.loads(backend.read_bytes(rel).decode("utf-8"))
    except Exception:  # noqa: BLE001 - an absent / unreadable file is no shape
        return None
    return data if isinstance(data, dict) else None


def summarize(shapes: Iterable[Shape]) -> list[dict]:
    """One row per (document, kind, field): runs, last run, the coordinates seen -
    most runs first."""
    groups: dict[tuple[str, str, str], dict] = {}
    for shape in shapes:
        group = groups.setdefault((shape.document, shape.kind, shape.field), {
            "document": shape.document, "kind": shape.kind, "field": shape.field,
            "runs": set(), "last": "", "where": []})
        group["runs"].add(shape.run)
        group["last"] = max(group["last"], shape.run)
        if shape.where and shape.where not in group["where"]:
            group["where"].append(shape.where)
    rows = [{**g, "runs": len(g["runs"])} for g in groups.values()]
    return sorted(rows, key=lambda r: (-r["runs"], r["document"], r["kind"], r["field"]))


def render_markdown(rows: list[dict], scanned: int) -> str:
    lines = ["# Unfamiliar shapes", "",
             f"{scanned} run(s) scanned; one row per shape the readers could not place, most "
             "runs first. Vocabulary goes in config; a grammar in code "
             "(docs/PARSER_SELF_EXTENSION.md).", ""]
    if not rows:
        return "\n".join([*lines, "Nothing unfamiliar in these runs.", ""])
    lines += ["| Document | Shape | Field / role | Runs | Last run | Where (coordinates) |",
              "|---|---|---|---|---|---|"]
    for r in rows:
        where = "; ".join(r["where"][:3]) + (" …" if len(r["where"]) > 3 else "")
        lines.append(f"| {r['document']} | {r['kind']} | {r['field']} | {r['runs']} | "
                     f"{r['last']} | {where} |")
    return "\n".join([*lines, ""])
