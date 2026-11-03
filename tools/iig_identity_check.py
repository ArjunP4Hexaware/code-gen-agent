"""Check the row identities of tools/iig_keys.yaml against a corpus of golden IIGs.

    python tools/iig_identity_check.py <golden.xlsx or dir> [...] [--group-index CSV ...]

Each golden is paired with ITSELF by identity (tools/iig_diff.py, the default
pairing): per sheet, how many rows have a complete identity, how many
identities repeat (rows that would pair in sheet order), which components no
row states (dropped). COUNTS only — no cell value is printed. Run it over the
199-IIG corpus on D1 before trusting an identity for a new sheet; a sheet whose
rows are mostly unidentified or repeated needs another identity column.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _iig_diff():
    spec = importlib.util.spec_from_file_location("iig_diff", HERE / "iig_diff.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["iig_diff"] = module
    spec.loader.exec_module(module)
    return module


def check(paths: list[Path], keys_path: Path, group_index: list[Path] | None) -> dict:
    iig_diff = _iig_diff()
    keys = iig_diff.load_keys(keys_path)
    sheets: dict[str, Counter] = defaultdict(Counter)
    dropped: dict[str, Counter] = defaultdict(Counter)
    files = 0
    for root in paths:
        for path in sorted(root.rglob("*.xlsx")) if root.is_dir() else [root]:
            if path.name.startswith("~$"):
                continue
            files += 1
            diffs = iig_diff.diff_workbooks(path, path, keys, scope_mode="all",
                                            group_index=group_index, self_check=True)
            for d in diffs:
                name = iig_diff.sheet_id(d.name)
                rows = d.rows["golden"]
                sheets[name]["rows"] += rows
                sheets[name]["identified"] += d.pairing.get(iig_diff.BY_IDENTITY, 0)
                sheets[name]["by_position"] += d.pairing.get(iig_diff.BY_POSITION, 0)
                sheets[name]["unpaired"] += d.unpaired.get("golden", 0)
                sheets[name]["repeated"] += len((d.facts.get("duplicate_keys") or {})
                                                .get("golden") or [])
                for item in d.facts.get("identity_dropped") or []:
                    dropped[name][item.split(" ")[0]] += 1
    return {"files": files, "sheets": dict(sheets), "dropped": dict(dropped)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--keys", type=Path, default=HERE / "iig_keys.yaml")
    ap.add_argument("--group-index", type=Path, action="append", metavar="CSV")
    args = ap.parse_args(argv)
    result = check(args.paths, args.keys, args.group_index)
    print(f"IDENTITY CHECK over {result['files']} golden(s) (counts only)")
    for name, c in sorted(result["sheets"].items()):
        line = (f"  {name}: rows {c['rows']}, identified {c['identified']}, by position "
                f"{c['by_position']}, unidentified {c['unpaired']}, repeated identities "
                f"{c['repeated']}")
        gone = result["dropped"].get(name)
        if gone:
            line += "; dropped " + ", ".join(f"{k} in {n} file(s)" for k, n in gone.items())
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
