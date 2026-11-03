"""The pair-4 multi-table golden (fixtures/acfc_shapes/pair_4/golden/IIG_EXPECTED.yaml)
as a comparison helper for the Phase C step tests (docs/acfc/MULTI_TABLE_DESIGN.md §6)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PAIR4 = REPO / "fixtures" / "acfc_shapes" / "pair_4"
PAIR4_OVERLAY = PAIR4 / "config_overlay.yaml"
GOLDEN = PAIR4 / "golden" / "IIG_EXPECTED.yaml"


def load_golden() -> dict:
    return yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))


def golden_rows(golden: dict, sheet: str) -> list[dict]:
    """A sheet's golden rows, annotations (``_…`` keys) dropped."""
    return [{k: v for k, v in row.items() if not k.startswith("_")}
            for row in golden[sheet]["rows"]]


def compare_to_golden(payload: dict, golden: dict, sheet: str) -> list[tuple]:
    """(row, column, expected, got) for every cell that differs; a golden
    null / "" means the cell must be blank. The row counts must match."""
    ours = payload["tabs"][sheet]["rows"]
    expected = golden_rows(golden, sheet)
    assert len(ours) == len(expected), (sheet, len(ours), len(expected))
    diffs = []
    for index, (row, want) in enumerate(zip(ours, expected, strict=True), start=1):
        for column, value in want.items():
            got = row["values"][column]
            got = "" if got is None else str(got)
            if got != (value or ""):
                diffs.append((index, column, value, got))
    return diffs
