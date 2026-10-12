"""Which code produced this: the version + location of the imported ``codegen``
and the config overlays in effect (2026-10-07: a stale wheel in the Apps venv
shadowed the deployed tree and nothing said so).

``source_line()`` is printed first by every CLI command, by ``codegen doctor``,
written into a run's ``run_meta.json`` and into the generation report's
"Model usage" section. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DISTRIBUTION = "codegen-data-engineer-agent"
PRODUCED_BY_PREFIX = "- Produced by: "


def package_file() -> str:
    import codegen

    return str(codegen.__file__)


def tree_root() -> Path | None:
    """The checkout this ``codegen`` was imported from (``<root>/src/codegen``
    with a pyproject.toml at ``<root>``), else None (an installed wheel)."""
    package = Path(package_file()).resolve().parent
    root = package.parent.parent
    if package.parent.name == "src" and (root / "pyproject.toml").is_file():
        return root
    return None


def codegen_version() -> str:
    """The tree's pyproject version when imported from a checkout (an
    editable install's metadata can lag the tree), else the installed
    distribution's."""
    root = tree_root()
    if root is not None:
        match = re.search(r'^version\s*=\s*"([^"]+)"',
                          (root / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    try:
        return version(DISTRIBUTION)
    except PackageNotFoundError:
        return "unknown"


def settings_text(settings: dict[str, str] | None) -> str:
    """`` · profile: <p> · IIG template: <t>`` (Chunk D, 2026-10-09) — the
    conventions profile and IIG template the run uses, so a run the committed
    overlay switched to acfc_prx / iig_v2 says so in its first line. A value a
    flag set is marked ``(--profile)`` / ``(--iig-template)``; '' without
    settings."""
    if not settings:
        return ""
    parts = []
    for key, label, flag in (("profile", "profile", "--profile"),
                             ("iig_template", "IIG template", "--iig-template")):
        if settings.get(key):
            from_flag = f" ({flag})" if settings.get(f"{key}_from_flag") else ""
            parts.append(f" · {label}: {settings[key]}{from_flag}")
    return "".join(parts)


def source_line(overlays: list[str] | None = None,
                settings: dict[str, str] | None = None) -> str:
    """``codegen <version> from <codegen.__file__>[ · profile: <p> · IIG
    template: <t>] · overlays: <list>`` — ``overlays`` defaults to the ones
    the last ``load_config`` applied; ``settings`` (``codegen.config
    .active_defaults``, a flag's value marked) only on the CLI's first line and
    ``codegen doctor``."""
    if overlays is None:
        from codegen.config import last_applied_overlays

        overlays = last_applied_overlays()
    listed = " -> ".join(overlays) if overlays else "(none)"
    return (f"codegen {codegen_version()} from {package_file()}{settings_text(settings)} · "
            f"overlays: {listed}")


# -- which COMMIT this is (2026-10-12: "post26" named a range of commits) -------------
#
# Resolved in this order, the first that answers wins:
#   1. git          — a checkout with a .git (a desktop, a worktree, a harness clone);
#   2. stamp        — ``src/codegen/_build.py`` written at deploy by
#                     ``scripts/stamp_build.py`` (never committed: the pre-push hook
#                     refuses it);
#   3. env          — ``CODEGEN_BUILD_SHA`` [+ ``_BRANCH`` / ``_COMMITTED``];
#   4. src tree     — no .git, no stamp, no env (the Git-deployed App): the git TREE
#                     hash of ``src/`` computed from the files themselves, which
#                     ``python scripts/stamp_build.py --which <hash>`` maps to the
#                     commits carrying exactly that code. Never a guess.

_BUILD_CACHE: dict[str, str] | None = None
_GIT_TIMEOUT_SECONDS = 5


def _git(root: Path, *args: str) -> str | None:
    import subprocess

    try:
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, timeout=_GIT_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _from_git(root: Path) -> dict[str, str] | None:
    if not (root / ".git").exists():
        return None
    head = _git(root, "log", "-1", "--format=%h%x00%cI")
    if not head or "\0" not in head:
        return None
    sha, committed = head.split("\0", 1)
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no", "--",
                 "src", "ui/backend", "config")
    return {"sha": sha, "branch": "detached" if branch == "HEAD" else branch,
            "committed": committed, "source": "git",
            **({"dirty": "uncommitted changes in src/ui/config"} if dirty else {})}


def _from_stamp() -> dict[str, str] | None:
    try:
        from codegen import _build  # type: ignore[attr-defined]
    except ImportError:
        return None
    sha = getattr(_build, "SHA", None)
    if not sha:
        return None
    return {"sha": str(sha)[:12], "branch": str(getattr(_build, "BRANCH", "") or "unknown"),
            "committed": str(getattr(_build, "COMMITTED", "") or "unknown"), "source": "stamp"}


def _from_env() -> dict[str, str] | None:
    import os

    sha = os.environ.get("CODEGEN_BUILD_SHA", "").strip()
    if not sha:
        return None
    return {"sha": sha[:12], "branch": os.environ.get("CODEGEN_BUILD_BRANCH", "") or "unknown",
            "committed": os.environ.get("CODEGEN_BUILD_COMMITTED", "") or "unknown",
            "source": "env"}


def _blob_bytes(path: Path) -> bytes:
    """The file as git stores it: a text file's CRLF read as LF (what an
    autocrlf checkout's clean filter does; every src/ file is LF in the index)."""
    data = path.read_bytes()
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def src_tree_hash(src: Path) -> str:
    """The git tree id of ``src`` computed from the files on disk (the same
    bytes ``git rev-parse <commit>:src`` names), skipping ``__pycache__`` /
    ``*.pyc`` and the deploy stamp. Every src/ file is mode 100644."""
    import hashlib

    def obj(kind: bytes, body: bytes) -> bytes:
        return hashlib.sha1(kind + b" " + str(len(body)).encode() + b"\0" + body).digest()

    def tree(folder: Path) -> bytes | None:
        entries: list[tuple[bytes, bytes, bytes]] = []
        for child in folder.iterdir():
            # Never tracked: bytecode, the deploy stamp, and the egg-info `pip
            # install .` writes into src/ (an untracked file anywhere else in src/
            # changes the id — then --which finds no commit, never a wrong one).
            if (child.name in ("__pycache__", "_build.py") or child.suffix == ".pyc"
                    or child.name.endswith(".egg-info")):
                continue
            if child.is_dir():
                sub = tree(child)
                if sub is not None:
                    entries.append((child.name.encode() + b"/", b"40000 " + child.name.encode(),
                                    sub))
            else:
                entries.append((child.name.encode(), b"100644 " + child.name.encode(),
                                obj(b"blob", _blob_bytes(child))))
        if not entries:
            return None                                # git keeps no empty tree
        # git orders tree entries by name, a directory compared as "<name>/".
        body = b"".join(head + b"\0" + digest for _key, head, digest in sorted(entries))
        return obj(b"tree", body)

    digest = tree(src)
    return digest.hex() if digest is not None else "empty"


def build_identity() -> dict[str, str]:
    """``{sha, branch, committed, source[, dirty | src_tree]}`` — see the order above."""
    global _BUILD_CACHE
    if _BUILD_CACHE is None:
        root = tree_root()
        found = (_from_git(root) if root is not None else None) or _from_stamp() or _from_env()
        if found is None:
            package = Path(package_file()).resolve().parent
            found = {"sha": "unknown", "branch": "unknown", "committed": "unknown",
                     "source": "none", "src_tree": src_tree_hash(package.parent)[:12]}
        _BUILD_CACHE = found
    return dict(_BUILD_CACHE)


def build_text(identity: dict[str, str] | None = None) -> str:
    """``build <sha> on <branch>, committed <iso> (<source>)`` — or, with no
    commit known, the src tree hash and how to resolve it."""
    found = identity or build_identity()
    if found.get("source") == "none":
        tree = found.get("src_tree", "unknown")
        return (f"build unknown (no .git, no stamp, no CODEGEN_BUILD_SHA) · src tree {tree} "
                f"(resolve: python scripts/stamp_build.py --which {tree})")
    text = (f"build {found['sha']} on {found['branch']}, committed {found['committed']} "
            f"({found['source']})")
    return text + (f" · {found['dirty']}" if found.get("dirty") else "")


def doctor_lines(overlays: list[str], defaults: dict[str, str] | None = None) -> list[str]:
    """``codegen doctor``: the source line (with the active profile / template),
    the two defaults on lines of their own, python, sys.path, iig_review."""
    from codegen.config import Config

    lines = [source_line(overlays, defaults)]
    if defaults:
        lines += [
            f"conventions profile: {defaults.get('profile', '?')} (conventions.profile, the "
            "config + overlays above; generate --profile overrides)",
            f"IIG template: {defaults.get('iig_template', '?')} (metadata.template, the config + "
            "overlays above; generate --iig-template overrides)",
        ]
    return [
        *lines,
        build_text(),
        f"python: {sys.executable}",
        f"sys.path[0:3]: {sys.path[0:3]}",
        f"iig_review supported: {'iig_review' in Config.model_fields}",
    ]


__all__ = ["PRODUCED_BY_PREFIX", "build_identity", "build_text", "codegen_version",
           "doctor_lines", "package_file", "settings_text", "source_line", "src_tree_hash",
           "tree_root"]
