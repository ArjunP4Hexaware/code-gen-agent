"""scripts/git-hooks/pre-push + scripts/bump_version.py (2026-10-12): a code push
to a deploy branch must carry a new version marker; the deploy stamp is never
committed. The hook runs as git would run it — ``sh pre-push`` with the ref
lines on stdin — against a throwaway repository."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "git-hooks" / "pre-push"
ZERO = "0" * 40


def _sh() -> str | None:
    found = shutil.which("sh")
    if found:
        return found
    git = shutil.which("git")
    if git:                     # Git for Windows: <Git>/cmd/git.exe -> <Git>/usr/bin/sh.exe
        candidate = Path(git).resolve().parents[1] / "usr" / "bin" / "sh.exe"
        if candidate.exists():
            return str(candidate)
    return None


SH = _sh()
pytestmark = pytest.mark.skipif(SH is None or shutil.which("git") is None,
                                reason="needs git and a POSIX sh")


def _bump_module():
    spec = importlib.util.spec_from_file_location("bump_version",
                                                  ROOT / "scripts" / "bump_version.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Repo:
    def __init__(self, path: Path):
        self.path = path
        self.git("init", "-q")
        self.git("config", "user.email", "t@synthetic.example")
        self.git("config", "user.name", "t")
        self.git("config", "core.autocrlf", "false")
        self.write("pyproject.toml", '[project]\nversion = "0.5.8.post27"\n')
        self.write("requirements.txt", ".[ui]\n# codegen-version-marker: 0.5.8.post27\n")
        self.write("src/codegen/x.py", "x = 1\n")
        self.write("docs/a.md", "a\n")
        self.base = self.commit("base")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.path), *args], capture_output=True,
                              text=True, check=True).stdout.strip()

    def write(self, name: str, text: str) -> None:
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def push(self, local: str, remote: str, branch: str = "feature/multi-table"):
        line = f"refs/heads/{branch} {local} refs/heads/{branch} {remote}\n"
        # Bytes, as git writes them (a text-mode pipe on Windows would add CRs).
        done = subprocess.run([SH, str(HOOK), "origin", "url"], input=line.encode(),
                              cwd=self.path, capture_output=True, check=False)
        return subprocess.CompletedProcess(done.args, done.returncode,
                                           done.stdout.decode(), done.stderr.decode())


@pytest.fixture
def repo(tmp_path):
    return _Repo(tmp_path)


def test_a_code_change_without_a_bump_is_refused(repo):
    repo.write("src/codegen/x.py", "x = 2\n")
    tip = repo.commit("code")
    done = repo.push(tip, repo.base)
    assert done.returncode == 1
    assert "but the version is still 0.5.8.post27" in done.stderr
    assert "src/codegen/x.py" in done.stderr


def test_the_same_change_with_bump_version_passes(repo):
    repo.write("src/codegen/x.py", "x = 2\n")
    assert _bump_module().bump(repo.path) == ("0.5.8.post27", "0.5.8.post28")
    tip = repo.commit("code + marker")
    assert repo.push(tip, repo.base).returncode == 0
    assert '"0.5.8.post28"' in (repo.path / "pyproject.toml").read_text()
    assert "marker: 0.5.8.post28" in (repo.path / "requirements.txt").read_text()


def test_docs_only_other_branches_new_branches_and_deletions_pass(repo):
    repo.write("docs/a.md", "b\n")
    tip = repo.commit("docs")
    assert repo.push(tip, repo.base).returncode == 0                    # no code changed
    repo.write("src/codegen/x.py", "x = 3\n")
    code = repo.commit("code")
    assert repo.push(code, repo.base, branch="validation/x").returncode == 0
    assert repo.push(code, ZERO).returncode == 0                        # a new branch
    assert repo.push(ZERO, repo.base).returncode == 0                   # a deletion
    assert repo.push(code, repo.base, branch="feature/iig-first").returncode == 1


def test_a_marker_out_of_step_with_pyproject_is_refused(repo):
    repo.write("src/codegen/x.py", "x = 2\n")
    repo.write("pyproject.toml", '[project]\nversion = "0.5.8.post28"\n')
    tip = repo.commit("half a bump")
    done = repo.push(tip, repo.base)
    assert done.returncode == 1 and "marker '0.5.8.post27' != pyproject version" in done.stderr
    _bump_module().bump(repo.path, sync_only=True)
    assert repo.push(repo.commit("sync"), repo.base).returncode == 0


def test_a_tracked_deploy_stamp_is_refused(repo):
    repo.write("src/codegen/_build.py", "SHA = 'abc'\n")
    _bump_module().bump(repo.path)
    tip = repo.commit("oops")
    done = repo.push(tip, repo.base)
    assert done.returncode == 1 and "_build.py is tracked" in done.stderr


def test_a_remote_tip_not_fetched_is_refused(repo):
    repo.write("src/codegen/x.py", "x = 2\n")
    tip = repo.commit("code")
    done = repo.push(tip, "1" * 40)
    assert done.returncode == 1 and "git fetch first" in done.stderr


def test_bump_keeps_crlf_bytes(tmp_path):
    (tmp_path / "pyproject.toml").write_bytes(b'[project]\r\nversion = "1.0.post9"\r\n')
    (tmp_path / "requirements.txt").write_bytes(b"# codegen-version-marker: 1.0.post9\r\n")
    assert _bump_module().bump(tmp_path) == ("1.0.post9", "1.0.post10")
    assert (tmp_path / "pyproject.toml").read_bytes() == b'[project]\r\nversion = "1.0.post10"\r\n'
    marker = (tmp_path / "requirements.txt").read_bytes()
    assert marker == b"# codegen-version-marker: 1.0.post10\r\n"


def test_a_frontend_source_change_without_a_rebuilt_dist_is_refused(repo):
    repo.write("ui/frontend/src/pages/ModesPage.tsx", "export const a = 1;\n")
    repo.write("ui/frontend/dist/index.html", "<html>v1</html>\n")
    _bump_module().bump(repo.path)
    base = repo.commit("ui v1")
    repo.write("ui/frontend/src/pages/ModesPage.tsx", "export const a = 2;\n")
    _bump_module().bump(repo.path)
    tip = repo.commit("src only")
    done = repo.push(tip, base)
    assert done.returncode == 1 and "ui/frontend/dist was not rebuilt" in done.stderr
    repo.write("ui/frontend/dist/index.html", "<html>v2</html>\n")
    assert repo.push(repo.commit("rebuilt"), base).returncode == 0
    # a test file alone changes no bundle
    repo.write("ui/frontend/src/pages/ModesPage.test.tsx", "test('x', () => {});\n")
    _bump_module().bump(repo.path)
    head = repo.git("rev-parse", "HEAD")
    assert repo.push(repo.commit("test only"), head).returncode == 0
