"""The EDH E2E profiler prints counts only; the synthetic gold fixtures rebuild byte for byte.

scripts/gold/profile_edh.py runs on D1 against the real extractor output and its stdout comes
home, so it must never echo a name it read: no table name, no region label.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "scripts" / "gold"
FIXTURES = REPO / "tests" / "fixtures" / "edh_gold_synthetic"
TOKEN = re.compile(r"[A-Za-z0-9_]+")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, GOLD / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _input_name_tokens(directory: Path) -> set[str]:
    """Tokens longer than 3 chars of every source_table, target_table and region key."""
    values: list[str] = []
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        tables = doc.get("tables") or []  # the manifest
        values += [t.get("target_table") or "" for t in tables]
        values.append(doc.get("target_table") or "")
        for row in doc.get("mappings") or []:
            values += [row.get("source_table") or "", row.get("target_table") or ""]
        values += list((doc.get("regional_table_structures") or {}).keys())
    return {t.lower() for v in values for t in TOKEN.findall(v) if len(t) > 3}


def test_profiler_output_carries_no_input_names():
    done = subprocess.run([sys.executable, str(GOLD / "profile_edh.py"), str(FIXTURES)],
                          capture_output=True, text=True, encoding="utf-8", check=True)
    names = _input_name_tokens(FIXTURES)
    assert len(names) > 20  # the check has something to bite on
    printed = {t.lower() for t in TOKEN.findall(done.stdout)}
    assert sorted(names & printed) == []


def test_profiler_counts_every_grammar_class_in_the_fixtures():
    out = _load("profile_edh").profile(FIXTURES)
    assert set(out["joins"]) == {"J1 using-column", "J1 using-column, filter before join",
                                 "J2 column named without using", "J3 alias-qualified equalities"}
    assert set(out["filters"]) == {"F1 equality", "F2 IN list", "F3 date window, relative",
                                   "F4 date window, as-of range", "F5 date window, between"}
    assert set(out["filter_per_cell"]) == {"equality", "date window", "free text", "join only"}
    assert set(out["edits"]) == {"literal NULL", "system value", "CAST", "substring slice",
                                 "COALESCE-equivalent", "CASE", "column reference (= source_field)",
                                 "column reference (another column)", "free text"}
    assert out["defects"]["top target_table not an identifier"] == 1
    assert out["defects"]["duplicated (block_index, target_attribute)"] == 1
    assert out["blocks"]["files with >1 block"] == 2
    assert out["blocks"]["rows without block_index"] == 0
    assert out["blocks"]["rows without source_row"] == 0
    assert out["defects"][">1 target_table in one block"] == 1
    assert out["blocks"]["files whose blocks load different tables"] == 1
    assert out["distinct_region_keys"] == 10
    assert out["regions"]["non-standard region keys"] == 2


def test_synthetic_fixtures_rebuild_byte_for_byte(tmp_path):
    written = _load("build_edh_synthetic").build(tmp_path)
    tracked = sorted(p.name for p in FIXTURES.glob("*.json"))
    assert written == tracked
    for name in tracked:
        assert (tmp_path / name).read_bytes() == (FIXTURES / name).read_bytes(), name
