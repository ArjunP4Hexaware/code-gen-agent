#!/usr/bin/env python3
"""Gate a run directory into results/approved/.

Runs scrub_check over every file in the directory, then writes
.scrub_manifest — a SHA-256 manifest of every file that was scanned and
passed.  The pre-commit hook refuses any file under results/approved/
that is not listed in a .scrub_manifest with a matching hash.

Usage:
    python scripts/gate_approve.py <run_dir> [--scrub-check <path>]

Requires: the code-gen-agent checkout (for scrub_check.py).  Set
CODEGEN_REPO to point at it, or accept the default (../code-gen-agent
relative to this repo's root).
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CODEGEN_REPO = Path(os.environ.get(
    "CODEGEN_REPO",
    REPO.parent / "code-gen-agent"))

MANIFEST_NAME = ".scrub_manifest"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--scrub-check", type=Path, default=None,
                    help="path to scrub_check.py (default: <CODEGEN_REPO>/scripts/scrub_check.py)")
    args = ap.parse_args(argv)

    run_dir: Path = args.run_dir.resolve()
    if not run_dir.is_dir():
        print(f"ERROR: {run_dir} is not a directory", file=sys.stderr)
        return 1

    scrub = args.scrub_check or CODEGEN_REPO / "scripts" / "scrub_check.py"
    if not scrub.is_file():
        print(f"ERROR: scrub_check.py not found at {scrub}\n"
              f"  Set CODEGEN_REPO or pass --scrub-check", file=sys.stderr)
        return 1

    # Build env for scrub_check
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(CODEGEN_REPO / "src") + os.pathsep
        + str(CODEGEN_REPO / "scripts") + os.pathsep
        + env.get("PYTHONPATH", ""))

    # Run scrub_check on the directory
    print(f"gate: scanning {run_dir.name} ...")
    done = subprocess.run(
        [sys.executable, str(scrub), str(run_dir)],
        capture_output=True, text=True, env=env, cwd=str(CODEGEN_REPO))

    if done.returncode != 0:
        print(f"GATE BLOCKED — scrub_check found hits:\n{done.stdout}", file=sys.stderr)
        return 1

    # Build manifest: one "sha256  relative_path" per file
    files = sorted(f for f in run_dir.rglob("*")
                   if f.is_file() and f.name != MANIFEST_NAME)
    lines = []
    for f in files:
        rel = f.relative_to(run_dir).as_posix()
        lines.append(f"{sha256_file(f)}  {rel}")

    manifest = run_dir / MANIFEST_NAME
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"gate: PASSED — {len(files)} file(s) scanned, manifest written to {MANIFEST_NAME}")
    for line in lines:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
