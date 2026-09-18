"""Materialize the ACFC-shape fixture universe under fixtures/acfc_shapes/.

    python scripts/build_acfc_shapes.py

Builders live in tests/acfc_shapes/ (importable by the suite, which rebuilds
every fixture in memory and asserts the tracked bytes match).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "src"))

from acfc_shapes import FIXTURE_ROOT, materialize  # noqa: E402


def main() -> int:
    written = materialize()
    for path in written:
        print(path.relative_to(REPO).as_posix())
    print(f"{len(written)} fixture(s) written under {FIXTURE_ROOT.relative_to(REPO).as_posix()}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
