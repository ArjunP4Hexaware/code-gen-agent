"""post69: notebook v1 vs v2 on one pair — what v1 did that v2 does not.

Generates the pair twice (mock, notebook output, the same contracts, overlay,
environment and answers; only ``conventions.profiles.<profile>.notebook_version``
differs) and reports per feed: the cell counts, the stages each notebook has,
the constants both state and whether their values agree, and what only v1 does.

post70: a v1 stage v2 renders from an IIG cell is reported "IIG-driven" (the
cell, its value, whether v2 has the cell) rather than "only v1"; only a stage
no IIG cell states stays "only v1" (PHI masking: docs/acfc/OPEN_QUESTIONS.md).
The file-name pattern differing is expected: v2 writes the IIG's SRC_FILE_NAME.

    python tools/notebook_parity.py --frd <frd.contract.json> --sttm <sttm.contract.json>
        [--answers answers.yaml] [--profile acfc_prx] --out <scratch dir> [--show-values]

Values are printed only with ``--show-values`` (synthetic pairs; never for a
client pair outside its environment): by default a differing constant is named
with its kind of difference, never its value.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# v1 module (its markdown heading) -> the stage it implements
V1_STAGES = {
    "reader": "read", "drift": "schema drift check", "mapping": "stage (column mapping)",
    "audit": "stage (audit columns)", "rejects": "rejects (not-null)",
    "reference": "recycle (reference lookup)", "recycle": "recycle", "writer": "stage (write)",
    "dq": "post-load DQ", "masking": "PHI masking", "run_report": "run report",
    "orchestrator": "run", "feed_spec": "config",
}
V2_STAGES = {
    "config": "config", "read": "read", "stage": "stage (write)", "standard": "standard",
    "dq": "DQ rules (DATA_QUALITY_RULES)", "run": "run", "review-candidates": "review-only",
    "drift": "schema drift check", "recycle": "recycle", "run-report": "run report",
}
# post70: a v1 stage v2 renders from an IIG cell -> (the cell, the v2 cell id)
IIG_DRIVEN = {
    "schema drift check": ("SCHEMA_DRIFT_FLAG", "drift"),
    "recycle": ("RECYCL_ENBL_FLG", "recycle"),
    "run report": ("always, the stage schema's _run_report table", "run-report"),
    "post-load DQ": ("DATA_QUALITY_RULES, run before the write", "dq"),
    "recycle (reference lookup)": ("DATA_QUALITY_RULES ReferentialCheckRule", None),
}
# a v1 stage no IIG cell states
NO_IIG_CELL = {"PHI masking": "no IIG cell, docs/acfc/OPEN_QUESTIONS.md §4"}
# a constant whose difference is by construction
EXPECTED = {
    "FILE_NAME_PATTERNS": "expected: v2 writes the IIG's SRC_FILE_NAME (Aruna's convention)",
}
NOTES = {
    "NATURAL_KEY_COLUMNS": "v1's list is the not-null columns; v2's is the IIG TGT_PRIMARY_KEY",
}
# (v1 feed_spec constant, a function of the v2 config constants)
COMPARED = [
    ("DELIMITER", lambda v: v["SOURCES"][0]["delimiter"]),
    ("FILE_FORMAT", lambda v: v["SOURCES"][0]["file_format"]),
    ("FILE_NAME_PATTERNS", lambda v: [s["file_pattern"] for s in v["SOURCES"]]),
    ("LOBS", lambda v: [s["lob"] for s in v["SOURCES"]]),
    ("DEFAULT_CATALOG", lambda v: v["STAGE_CATALOG"]),
    ("STAGE_SCHEMA", lambda v: v["SOURCES"][0]["schema"]),
    ("NOT_NULL_COLUMNS", lambda v: v["SOURCES"][0]["mandatory"]),
    ("NATURAL_KEY_COLUMNS", lambda v: v["SOURCES"][0]["primary_key"]),
    ("STANDARD_CATALOG", lambda v: v["STANDARDS"][0]["catalog"] if v["STANDARDS"] else None),
    ("STANDARD_SCHEMA", lambda v: v["STANDARDS"][0]["schema"] if v["STANDARDS"] else None),
    ("STORAGE_ACCOUNT", lambda v: v["STORAGE_ACCOUNT"]),
    ("LANDING_PATH", lambda v: v["SOURCES"][0]["landing_path"]),
    ("ARCHIVE_PATH", lambda v: v["SOURCES"][0]["archive_path"]),
    ("REJECT_PATH", lambda v: v["SOURCES"][0]["reject_path"]),
]


def constants(source: str) -> dict:
    values = {}
    for node in ast.parse(source).body:
        target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1
                  else node.target if isinstance(node, ast.AnnAssign) else None)
        if isinstance(target, ast.Name) and node.value is not None:
            try:
                values[target.id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return values


def _cells(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def _generate(frd: Path, sttm: Path, answers: Path | None, profile: str, version: str,
              out: Path, overlays: list[Path] | None = None) -> int:
    from codegen import cli
    from codegen.config import load_config

    config = load_config(REPO / "config" / "config.yaml", overlays=overlays or [])
    profiles = dict(config.conventions.profiles)
    profiles[profile] = profiles[profile].model_copy(update={"notebook_version": version})
    config = config.model_copy(update={
        "conventions": config.conventions.model_copy(update={"profiles": profiles}),
        "output": config.output.model_copy(update={"dir": str(out / "out"),
                                                   "reports_dir": str(out / "reports")})})
    return cli._run_pairs([(frd, sttm)], config, dry_run=True, skip_tests=True,
                          output_mode=["notebook"], only_feed=None,
                          conventions_profile=profile, iig_template="iig_v2",
                          answers_path=answers)


def _kind(v1, v2) -> str:
    if v1 == v2:
        return "same"
    if v1 in (None, "", []) and v2 not in (None, "", []):
        return "only v2 states it"
    if v2 in (None, "", []) and v1 not in (None, "", []):
        return "only v1 states it"
    if isinstance(v1, list) and isinstance(v2, list):
        return (f"differs ({len(set(map(str, v1)) & set(map(str, v2)))} of "
                f"{len(v1)} / {len(v2)} shared)")
    return "differs"


def compare(v1_out: Path, v2_out: Path, *, show_values: bool) -> list[str]:
    lines = []
    feeds = sorted(p.parent.name for p in v1_out.glob("*/pipeline"))
    for feed in feeds:
        v1_book = v1_out / feed / f"{feed}.ipynb"
        v2_book = v2_out / feed / "notebook" / f"{feed}.ipynb"
        lines.append(f"== {feed}")
        if not v1_book.is_file() or not v2_book.is_file():
            lines.append(f"   notebook missing: v1 {v1_book.is_file()}, v2 {v2_book.is_file()}")
            continue
        v1_cells, v2_cells = _cells(v1_book), _cells(v2_book)
        v1_code = sum(c["cell_type"] == "code" for c in v1_cells)
        v2_code = sum(c["cell_type"] == "code" for c in v2_cells)
        lines.append(f"   cells: v1 {len(v1_cells)} ({v1_code} code) | "
                     f"v2 {len(v2_cells)} ({v2_code} code)")
        v1_stages = sorted({V1_STAGES[c["id"]] for c in v1_cells if c["id"] in V1_STAGES})
        v2_stages = {V2_STAGES[c["id"]] for c in v2_cells if c["id"] in V2_STAGES}
        if any("def split_mandatory" in "".join(c["source"]) for c in v2_cells):
            v2_stages.add("rejects (not-null)")      # the read cell's MANDATORY_FIELD_LIST
        v2_stages = sorted(v2_stages)
        lines.append(f"   stages v1: {', '.join(v1_stages)}")
        lines.append(f"   stages v2: {', '.join(v2_stages)} (+ a provenance cell per stage)")
        missing = [c for c in v2_cells if c["id"].startswith("dq-not-implemented-")]
        (config_cell,) = [c for c in v2_cells if c["id"] == "config"]
        v2_values = constants("".join(config_cell["source"]))
        v2_ids = {c["id"] for c in v2_cells}
        driven, only_v1 = [], []
        for stage in (s for s in v1_stages if not s.startswith("stage")):
            if stage in IIG_DRIVEN:
                driven.append(f"{stage} ({_driven(stage, v2_values, v2_ids, missing)})")
            elif stage not in v2_stages:
                only_v1.append(f"{stage} ({NO_IIG_CELL.get(stage, 'no IIG cell')})")
        lines.append(f"   IIG-driven: {', '.join(driven) or 'nothing'}")
        lines.append(f"   v1 only: {', '.join(only_v1) or 'nothing'}")
        lines.append(f"   v2 DQ rows not implemented: {len(missing)}")
        v1_spec = constants((v1_out / feed / "pipeline" / "feed_spec.py").read_text(
            encoding="utf-8"))
        for name, pick in COMPARED:
            try:
                v2 = pick(v2_values)
            except (KeyError, IndexError):
                v2 = None
            v1 = v1_spec.get(name)
            kind = _kind(v1, v2)
            if kind != "same" and name in EXPECTED:
                kind = f"{EXPECTED[name]} ({kind})"
            elif kind != "same" and name in NOTES:
                kind = f"{kind} — {NOTES[name]}"
            text = f"   {name:<20} {kind}"
            if show_values and kind != "same":
                text += f": v1 {v1!r} | v2 {v2!r}"
            lines.append(text)
    return lines


def _driven(stage: str, values: dict, ids: set[str], missing: list[dict]) -> str:
    """How v2 covers a v1 stage an IIG cell drives: the cell, its value, the cell
    v2 rendered (or not)."""
    cell, v2_id = IIG_DRIVEN[stage]
    sources = values.get("SOURCES") or []
    if stage == "schema drift check":
        stated = "Y" if any(s.get("schema_drift") for s in sources) else "N"
        return f"{cell} = {stated}: " + ("in v2" if v2_id in ids else "not generated")
    if stage == "recycle":
        stated = "Y" if any(s.get("recycle") for s in sources) else "N"
        return f"{cell} = {stated}: " + ("in v2" if v2_id in ids else "not generated")
    if v2_id is None:
        named = any("ReferentialCheckRule" in "".join(c["source"]) for c in missing)
        return f"{cell}: " + ("a 'rule not implemented' cell in v2" if named
                              else "no such row in the IIG")
    return f"{cell}: " + ("in v2" if v2_id in ids else "not generated")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frd", type=Path, required=True)
    parser.add_argument("--sttm", type=Path, required=True)
    parser.add_argument("--answers", type=Path, default=None)
    parser.add_argument("--profile", default="acfc_prx")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--show-values", action="store_true")
    parser.add_argument("--overlay", type=Path, action="append", default=[],
                        help="config overlay(s) on top of the always-applied acfc_env.yaml")
    args = parser.parse_args(argv)
    for version in ("v1", "v2"):
        code = _generate(args.frd, args.sttm, args.answers, args.profile, version,
                         args.out / version, args.overlay)
        print(f"generate ({version}) exit {code}")
    for line in compare(args.out / "v1" / "out", args.out / "v2" / "out",
                        show_values=args.show_values):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
