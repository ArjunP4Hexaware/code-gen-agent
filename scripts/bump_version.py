"""Bump the version marker (2026-10-12) — pyproject.toml ``version`` and the
requirements.txt ``codegen-version-marker`` together, bytes otherwise kept
(each file's own line endings). The pre-push hook (scripts/git-hooks/pre-push)
refuses a code push to a deploy branch without it.

    python scripts/bump_version.py           0.5.8.post27 -> 0.5.8.post28
    python scripts/bump_version.py --sync    requirements.txt marker := pyproject version
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(rb'^version = "([^"]+)"', re.M)
MARKER_RE = re.compile(rb"^# codegen-version-marker: (\S+)", re.M)


def next_version(version: str) -> str:
    match = re.fullmatch(r"(.*\.post)(\d+)", version)
    if match is None:
        raise ValueError(f"{version!r} has no .postN to increment — set the version by hand")
    return f"{match.group(1)}{int(match.group(2)) + 1}"


def bump(root: Path = ROOT, *, sync_only: bool = False) -> tuple[str, str]:
    pyproject, requirements = root / "pyproject.toml", root / "requirements.txt"
    data = pyproject.read_bytes()
    match = VERSION_RE.search(data)
    if match is None:
        raise ValueError("pyproject.toml has no version line")
    old = match.group(1).decode()
    new = old if sync_only else next_version(old)
    if new != old:
        pyproject.write_bytes(data[:match.start(1)] + new.encode() + data[match.end(1):])
    req = requirements.read_bytes()
    marker = MARKER_RE.search(req)
    if marker is None:
        raise ValueError("requirements.txt has no codegen-version-marker line")
    requirements.write_bytes(req[:marker.start(1)] + new.encode() + req[marker.end(1):])
    return old, new


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sync", action="store_true",
                        help="only copy pyproject's version into requirements.txt")
    args = parser.parse_args(argv)
    old, new = bump(sync_only=args.sync)
    print(f"version {old} -> {new} (pyproject.toml + requirements.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
