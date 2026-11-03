"""Which commit runs (2026-10-12): "0.5.8.post26" named f37d1a1 AND the commits
pushed after it without a bump, so the health line could not say which code the
App ran. ``codegen.build_info.build_identity`` names the commit — git, a deploy
stamp, the env, else the src/ tree hash that ``scripts/stamp_build.py --which``
resolves — and every health surface prints it."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

from codegen import build_info

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
HAS_GIT = shutil.which("git") is not None and (ROOT / ".git").exists()


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _stamp_build():
    spec = importlib.util.spec_from_file_location("stamp_build",
                                                  ROOT / "scripts" / "stamp_build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.setattr(build_info, "_BUILD_CACHE", None)
    monkeypatch.delenv("CODEGEN_BUILD_SHA", raising=False)
    monkeypatch.delitem(sys.modules, "codegen._build", raising=False)
    yield
    build_info._BUILD_CACHE = None


@pytest.mark.skipif(not HAS_GIT, reason="needs git and a checkout")
def test_a_checkout_names_its_commit_branch_and_time():
    found = build_info.build_identity()
    assert found["source"] == "git"
    assert found["sha"] == _git("log", "-1", "--format=%h")
    assert found["committed"] == _git("log", "-1", "--format=%cI")
    text = build_info.build_text(found)
    assert text.startswith(f"build {found['sha']} on ") and "(git)" in text


def test_without_git_the_deploy_stamp_names_it(monkeypatch):
    monkeypatch.setattr(build_info, "tree_root", lambda: None)
    stamp = types.ModuleType("codegen._build")
    stamp.SHA, stamp.BRANCH, stamp.COMMITTED = "abc1234def56", "feature/x", "2026-10-12T15:00:00Z"
    monkeypatch.setitem(sys.modules, "codegen._build", stamp)
    assert build_info.build_text() == ("build abc1234def56 on feature/x, committed "
                                       "2026-10-12T15:00:00Z (stamp)")


def test_without_git_or_stamp_the_env_names_it(monkeypatch):
    monkeypatch.setattr(build_info, "tree_root", lambda: None)
    monkeypatch.setitem(sys.modules, "codegen._build", None)       # import fails
    monkeypatch.setenv("CODEGEN_BUILD_SHA", "0123456789abcdef")
    found = build_info.build_identity()
    assert (found["sha"], found["source"], found["branch"]) == ("0123456789ab", "env", "unknown")


def test_with_nothing_the_src_tree_hash_is_said_never_a_guess(monkeypatch):
    monkeypatch.setattr(build_info, "tree_root", lambda: None)
    monkeypatch.setitem(sys.modules, "codegen._build", None)
    found = build_info.build_identity()
    assert found["sha"] == "unknown" and found["source"] == "none"
    text = build_info.build_text(found)
    assert f"src tree {found['src_tree']}" in text
    assert f"stamp_build.py --which {found['src_tree']}" in text


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_the_src_tree_hash_is_the_git_tree_id(tmp_path):
    """Computed from the files, it equals ``git rev-parse <tree>:src`` — CRLF
    working copies (an autocrlf checkout) read as their LF blobs; caches and the
    deploy stamp are not part of it."""
    src = tmp_path / "src"
    (src / "pkg" / "sub").mkdir(parents=True)
    (src / "pkg" / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
    (src / "pkg" / "a-b.py").write_bytes(b"z = 3\n")          # '-' sorts before '.' and '/'
    (src / "pkg" / "sub" / "t.j2").write_bytes(b"{{ v }}\n")
    (src / "pkg" / "data.bin").write_bytes(b"\x00\r\n\x01")    # binary: bytes as they are
    (src / "top.txt").write_bytes(b"top\n")
    (src / "pkg" / "__pycache__").mkdir()
    (src / "pkg" / "__pycache__" / "a.cpython-311.pyc").write_bytes(b"\x00junk")
    (src / "pkg" / "_build.py").write_bytes(b"SHA = 'x'\n")
    (src / "pkg_dist.egg-info").mkdir()                       # what `pip install .` leaves
    (src / "pkg_dist.egg-info" / "PKG-INFO").write_bytes(b"Name: pkg\n")
    _git("init", "-q", cwd=tmp_path)
    _git("config", "core.autocrlf", "true", cwd=tmp_path)
    (tmp_path / ".gitignore").write_text("__pycache__/\n_build.py\n*.egg-info/\n",
                                         encoding="utf-8")
    _git("add", "src", cwd=tmp_path)
    tree = _git("write-tree", cwd=tmp_path)
    assert build_info.src_tree_hash(src) == _git("rev-parse", f"{tree}:src", cwd=tmp_path)


@pytest.mark.skipif(not HAS_GIT, reason="needs git and a checkout")
def test_which_resolves_a_src_tree_to_its_commits():
    stamp_build = _stamp_build()
    head_tree = _git("rev-parse", "HEAD:src")
    hits = stamp_build.which(head_tree[:12])
    assert any(hit.split()[0] == _git("log", "-1", "--format=%h") for hit in hits), hits


def test_write_stamp_round_trips(tmp_path):
    stamp_build = _stamp_build()
    path = stamp_build.write_stamp("abc1234", "feature/x", "2026-10-12T15:00:00Z",
                                   tmp_path / "_build.py")
    namespace: dict = {}
    exec(path.read_text(encoding="utf-8"), namespace)  # noqa: S102 — our own file
    assert (namespace["SHA"], namespace["BRANCH"]) == ("abc1234", "feature/x")


def test_the_health_line_carries_the_build():
    pytest.importorskip("fastapi")
    from ui.backend import errors

    line = errors.health_line({"version": "0.5.8.post27", "codegen_source": "codegen source: x",
                               "build": {"sha": "abc1234", "branch": "feature/multi-table",
                                         "committed": "2026-10-12T15:00:00Z", "source": "git"},
                               "config_overlays": [], "startup_error": None})
    assert line.startswith("version 0.5.8.post27 · build abc1234 on feature/multi-table, "
                           "committed 2026-10-12T15:00:00Z (git) · codegen source: x")
    # The App's codegen_source line already carries it: said once, never twice.
    build = {"sha": "abc1234", "branch": "b", "committed": "t", "source": "git"}
    source = "codegen source: x version v · build abc1234 on b, committed t (git) · config: c"
    line = errors.health_line({"version": "v", "codegen_source": source, "build": build,
                               "config_overlays": [], "startup_error": None})
    assert line.count("build abc1234") == 1 and line.startswith("version v · codegen source: x")


@pytest.mark.skipif(not HAS_GIT, reason="needs git and a checkout")
def test_this_checkouts_src_hashes_to_head_when_clean():
    """The real tree: equal to ``git rev-parse HEAD:src`` whenever src/ has no
    uncommitted change (the egg-info and caches of a dev install skipped)."""
    if _git("status", "--porcelain", "--untracked-files=normal", "--", "src"):
        pytest.skip("src/ has uncommitted or untracked changes")
    assert build_info.src_tree_hash(SRC) == _git("rev-parse", "HEAD:src")


def test_generate_stamps_its_output_root_and_iig_diff_finds_it(tmp_path, capsys):
    """`codegen generate` writes CODEGEN_BUILD.json into the output root (run
    level, outside every feed folder); tools/iig_diff.py accepts a workbook
    up to 5 folders below it."""
    from codegen import cli

    cli._write_build_stamp(tmp_path)
    stamp = json.loads((tmp_path / cli.BUILD_STAMP_FILE).read_text(encoding="utf-8"))
    assert stamp["line"] == f"codegen {stamp['version']} · {build_info.build_text()}"
    assert stamp["source"] in ("git", "stamp", "env", "none")
    assert capsys.readouterr().out == ""          # silent: the console order is a contract
    iig_diff = sys.modules.get("iig_diff")
    if iig_diff is None:
        spec = importlib.util.spec_from_file_location("iig_diff", ROOT / "tools" / "iig_diff.py")
        iig_diff = importlib.util.module_from_spec(spec)
        sys.modules["iig_diff"] = iig_diff            # dataclasses look their module up
        spec.loader.exec_module(iig_diff)
    workbook = tmp_path / "feed" / "RFC_x" / "FEED_IIG.xlsx"
    workbook.parent.mkdir(parents=True)
    assert iig_diff.find_build(workbook)["line"] == stamp["line"]
