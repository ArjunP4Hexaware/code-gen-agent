"""Name the commit a deployed tree was built from (2026-10-12).

Two uses:

* ``python scripts/stamp_build.py`` — at DEPLOY, in a checkout that is about to
  lose its .git (a Workspace Git folder snapshotted into a Databricks App):
  writes ``src/codegen/_build.py`` (SHA / BRANCH / COMMITTED) from git, or from
  ``--sha / --branch / --committed`` (e.g. the Repos API ``head_commit_id`` and
  ``branch`` of the Git folder). ``codegen.build_info.build_identity`` reads it
  when there is no .git. The file is never committed: the pre-push hook
  (``scripts/git-hooks/pre-push``) refuses a push that tracks it.
* ``python scripts/stamp_build.py --which <src-tree>`` — on a desktop: the
  commits whose ``src/`` tree is that hash (what ``/api/health`` prints as
  ``src tree <hash>`` when no commit is known), newest first.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMP = ROOT / "src" / "codegen" / "_build.py"


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def write_stamp(sha: str, branch: str, committed: str, path: Path = STAMP) -> Path:
    path.write_text(
        '"""Deploy stamp written by scripts/stamp_build.py — never commit this file."""\n\n'
        f"SHA = {sha!r}\nBRANCH = {branch!r}\nCOMMITTED = {committed!r}\n",
        encoding="utf-8", newline="\n")
    return path


def which(tree: str, limit: int = 2000) -> list[str]:
    """``<sha> <date> <subject>`` for every commit (all refs) whose src/ tree
    id starts with ``tree``."""
    tree = tree.lower()
    commits = [line.split("\0", 2) for line in
               _git("log", "--all", f"-{limit}", "--format=%h%x00%cI%x00%s").splitlines()]
    # One cat-file process, one output line per input line ("<oid> tree <size>",
    # or "<input> missing" for a commit without src/) — aligned with the input.
    lines = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch-check"],
                           input="".join(f"{sha}:src\n" for sha, _d, _s in commits),
                           capture_output=True, text=True, check=True).stdout.splitlines()
    return [f"{sha} {date} {subject}" for (sha, date, subject), line in zip(commits, lines,
                                                                           strict=True)
            if not line.endswith(" missing") and line.split()[0].startswith(tree)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha")
    parser.add_argument("--branch")
    parser.add_argument("--committed")
    parser.add_argument("--which", metavar="SRC_TREE",
                        help="list the commits whose src/ tree id starts with this")
    args = parser.parse_args(argv)
    if args.which:
        hits = which(args.which)
        print("\n".join(hits) if hits else f"no commit has src tree {args.which}")
        return 0 if hits else 1
    sha = args.sha or _git("rev-parse", "--short=12", "HEAD")
    branch = args.branch or _git("rev-parse", "--abbrev-ref", "HEAD")
    committed = args.committed or _git("log", "-1", "--format=%cI", sha)
    print(f"wrote {write_stamp(sha, branch, committed)}: {sha} on {branch}, committed {committed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
