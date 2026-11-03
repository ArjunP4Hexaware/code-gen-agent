"""The spiral-detector hook (../spiral_detector.py), driven by scripted event sequences
shaped like the documented PostToolUse / PostToolUseFailure input.

Run: python -m pytest -q  (from this folder or the hook folder; needs only pytest)."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "spiral_detector.py"

_spec = importlib.util.spec_from_file_location("spiral_detector", HOOK)
sd = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(sd)

PYTEST = "python -m pytest -q tests/test_x.py"
FAILURE = (
    "FAILED tests/test_x.py::test_one - AssertionError: assert 1 == 2\n"
    "1 failed, 3 passed in 0.42s"
)
OTHER_FAILURE = "FAILED tests/test_x.py::test_two - KeyError: 'feed'\n1 failed, 3 passed in 0.40s"
MESSAGE_RE = re.compile(
    r"^spiral-detector hook \(user-configured in ~/\.claude/settings\.json\): "
    r"signal \((a|b|c)\): [^\n]+\.$"
)
PIPED = "python -m pytest -q tests/test_x.py 2>&1 | tail -20"
PASSING = "4 passed in 0.31s"


class Session:
    """Feeds events to process() and records which signals fired."""

    def __init__(
        self, tmp_path: Path, session_id: str = "s1", tool: str = "Bash", repo: str = "repo"
    ) -> None:
        self.root = tmp_path / repo
        (self.root / ".git").mkdir(parents=True, exist_ok=True)
        self.home = tmp_path / "home"
        self.repo = repo
        self.session_id = session_id
        self.tool = tool
        self.fired: list[str] = []
        self.outputs: list[dict] = []

    def _send(self, event: dict) -> list[str]:
        event = {"session_id": self.session_id, "cwd": str(self.root), **event}
        out = sd.process(event, self.home, self.root)
        if out is None:
            return []
        self.outputs.append(out)
        msg = out["hookSpecificOutput"]["additionalContext"]
        assert out["hookSpecificOutput"]["hookEventName"] == event["hook_event_name"]
        assert out["systemMessage"] == msg
        signals = []
        for line in msg.split("\n"):
            m = MESSAGE_RE.match(line)
            assert m, line
            signals.append(m.group(1))
        self.fired += signals
        return signals

    def fail(self, command: str = PYTEST, output: str = FAILURE, code: int = 1) -> list[str]:
        return self._send({
            "hook_event_name": "PostToolUseFailure",
            "tool_name": self.tool,
            "tool_input": {"command": command, "description": "run"},
            "error": f"Exit code {code}\n{output}",
            "is_interrupt": False,
        })

    def ok(self, command: str = PYTEST, stdout: str = PASSING) -> list[str]:
        """Exit 0. For a piped command that is the pipe tail's exit, whatever the tool did."""
        return self._send({
            "hook_event_name": "PostToolUse",
            "tool_name": self.tool,
            "tool_input": {"command": command, "description": "run"},
            "tool_response": {
                "stdout": stdout, "stderr": "", "interrupted": False, "isImage": False,
            },
        })

    @property
    def state_file(self) -> Path:
        return self.home / sd.STATE_DIR / f"{self.repo}.json"

    def state(self) -> dict:
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def write(self, name: str, content: str) -> list[str]:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return self._send({
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(path), "content": content},
            "tool_response": {"filePath": str(path), "type": "update"},
        })

    def edit(self, name: str, old: str, new: str) -> list[str]:
        path = self.root / name
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1
        path.write_text(text.replace(old, new), encoding="utf-8")
        return self._send({
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(path), "old_string": old, "new_string": new,
                "replace_all": False,
            },
            "tool_response": {"filePath": str(path)},
        })

    def fires_log(self) -> list[dict]:
        path = self.home / sd.FIRES_FILE
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def s(tmp_path: Path) -> Session:
    return Session(tmp_path)


# --- Signal a ----------------------------------------------------------------------


def test_a_fires_on_the_second_same_signature_failure_not_the_first(s: Session) -> None:
    assert s.fail() == []
    assert s.fail() == ["a"]


def test_a_signature_ignores_timestamps_temp_paths_line_numbers_addresses(s: Session) -> None:
    first = (
        "2026-10-05T10:11:12Z start\n"
        r"C:\Users\x\AppData\Local\Temp\pytest-of-x\pytest-7\test_a0\in.txt not found" "\n"
        "tests/test_x.py:41: AssertionError at 0x7f3a2b10\n"
        'File "src/pkg/x.py", line 120, in f\n'
        "1 failed in 3.10s"
    )
    second = (
        "2026-10-05T10:19:55Z start\n"
        r"C:\Users\x\AppData\Local\Temp\pytest-of-x\pytest-8\test_a0\in.txt not found" "\n"
        "tests/test_x.py:44: AssertionError at 0x55e0c1d8\n"
        'File "src/pkg/x.py", line 123, in f\n'
        "1 failed in 2.95s"
    )
    assert sd.error_signature(first) == sd.error_signature(second)
    assert s.fail(output=first) == []
    assert s.fail(output=second) == ["a"]


def test_a_signature_covers_only_the_last_twenty_lines() -> None:
    tail = "\n".join(f"line of output {i}" for i in range(sd.SIGNATURE_TAIL_LINES))
    assert sd.error_signature("head A\n" + tail) == sd.error_signature("head B\n" + tail)
    assert sd.error_signature(tail + "\nX") != sd.error_signature(tail + "\nY")


def test_a_different_signature_on_the_second_failure_does_not_fire(s: Session) -> None:
    assert s.fail(output=FAILURE) == []
    assert s.fail(output=OTHER_FAILURE) == []
    # the streak restarted on the new signature: its own second occurrence fires
    assert s.fail(output=OTHER_FAILURE) == ["a"]


def test_a_needs_the_same_command(s: Session) -> None:
    assert s.fail(command=PYTEST) == []
    assert s.fail(command="ruff check src/ tests/") == []
    assert s.fired == []


def test_a_pass_between_failures_breaks_the_row(s: Session) -> None:
    assert s.fail() == []
    assert s.ok() == []
    assert s.fail() == []
    assert s.fired == []


# --- Signal b ----------------------------------------------------------------------


def test_b_fires_on_the_fourth_edit_while_failing_not_the_third(s: Session) -> None:
    s.write("mod.py", "v0\n")  # before any failure: not counted
    s.fail()
    for i in range(1, 4):
        assert s.edit("mod.py", f"v{i - 1}\n", f"v{i}\n") == [], i
    assert s.edit("mod.py", "v3\n", "v4\n") == ["b"]


def test_b_counts_per_file(s: Session) -> None:
    s.fail()
    for i in range(3):
        assert s.write("a.py", f"a{i}\n") == []
        assert s.write("b.py", f"b{i}\n") == []
    assert s.fired == []


def test_edits_without_a_failing_command_never_fire(s: Session) -> None:
    for i in range(8):
        assert s.write("mod.py", f"v{i % 2}\n") == []  # repeats content too
    assert s.fired == []
    assert s.fires_log() == []


# --- Signal c ----------------------------------------------------------------------


def test_c_fires_when_a_write_restores_an_earlier_version(s: Session) -> None:
    s.fail()
    assert s.write("mod.py", "one\n") == []
    assert s.write("mod.py", "two\n") == []
    assert s.write("mod.py", "one\n") == ["c"]


def test_c_fires_when_an_edit_is_reverted_to_the_pre_episode_content(s: Session) -> None:
    (s.root / "mod.py").write_text("x = 1\n", encoding="utf-8")
    s.fail()
    assert s.edit("mod.py", "x = 1", "x = 2") == []
    assert s.edit("mod.py", "x = 2", "x = 1") == ["c"]


def test_c_does_not_fire_on_new_content(s: Session) -> None:
    s.fail()
    assert s.write("mod.py", "one\n") == []
    assert s.write("mod.py", "two\n") == []
    assert s.write("mod.py", "three\n") == []
    assert s.fired == []


# --- Normal work, ignored commands, episodes ----------------------------------------------


def test_fail_then_pass_test_driven_work_never_fires(s: Session) -> None:
    (s.root / "mod.py").write_text("v0\n", encoding="utf-8")
    for cycle in range(5):
        s.fail()
        for i in range(3):
            s.write("mod.py", f"cycle{cycle} step{i}\n")
        s.ok()
    assert s.fired == []
    assert s.fires_log() == []


@pytest.mark.parametrize("command", [
    "grep -rn needle src/",
    "rg needle src",
    "git grep needle",
    "findstr needle file.txt",
    "Select-String -Path *.py -Pattern needle",
])
def test_grep_and_rg_exiting_1_never_count(s: Session, command: str) -> None:
    for _ in range(4):
        assert s.fail(command=command, output="", code=1) == []
    for i in range(5):
        assert s.write("mod.py", f"v{i}\n") == []
    assert s.fired == []
    state = s.state()
    assert state["failing"] == [] and state["commands"] == {} and state["episode"]["edits"] == {}


def test_a_watched_command_piped_into_rg_is_not_judged(s: Session) -> None:
    piped = "python -m pytest -q 2>&1 | rg FAILED"
    for _ in range(3):
        assert s.fail(command=piped, output="", code=1) == []
    assert s.fired == []


# --- Piped runs: judged from the pytest / ruff / cargo summary ------------------------------


PYTEST_OUTPUT = (
    "tests/test_x.py ..F.                                                  [100%]\n"
    "=================================== FAILURES ===================================\n"
    "___________________________________ test_one ___________________________________\n"
    "    def test_one():\n"
    ">       assert 1 == 2\n"
    "E       assert 1 == 2\n"
    "tests/test_x.py:7: AssertionError\n"
    "=========================== short test summary info ============================\n"
    "FAILED tests/test_x.py::test_one - assert 1 == 2\n"
    "1 failed, 3 passed in 0.42s\n"
)


def _tail(output: str, n: int) -> str:
    return "\n".join(output.rstrip("\n").split("\n")[-n:]) + "\n"


def test_piped_pytest_with_failures_counts(s: Session) -> None:
    # `pytest | tail` exits 0 (tail's code), so it arrives as PostToolUse
    assert s.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 20)) == []
    assert s.state()["failing"] == ["python -m pytest -q tests/test_x.py"]
    assert s.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 20)) == ["a"]


def test_piped_pytest_errors_count_as_failures(s: Session) -> None:
    out = "ERROR tests/test_x.py - ImportError: no module\n1 error in 0.20s\n"
    assert s.ok(command=PIPED, stdout=out) == []
    assert s.ok(command=PIPED, stdout=out) == ["a"]


def test_piped_pytest_with_a_passing_summary_resets_the_episode(s: Session) -> None:
    s.fail(output=PYTEST_OUTPUT)
    for i in range(3):
        s.write("mod.py", f"v{i}\n")
    assert s.ok(command=PIPED, stdout="....  [100%]\n4 passed in 0.31s\n") == []
    assert s.state()["failing"] == []
    assert s.write("mod.py", "v3\n") == []  # a 4th edit, but the episode was reset
    assert s.fired == []
    # and the signals are armed again
    s.fail(output=PYTEST_OUTPUT)
    assert s.fail(output=PYTEST_OUTPUT) == ["a"]


def test_piped_run_without_a_summary_is_ignored(s: Session) -> None:
    s.fail(output=PYTEST_OUTPUT)  # an episode is open
    for stdout in ("collecting ...", "", "Traceback (most recent call last):"):
        assert s.ok(command=PIPED, stdout=stdout) == []
        assert s._send({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
            "tool_input": {"command": PIPED}, "error": f"Exit code 1\n{stdout}",
        }) == []
    # neither a pass (the episode is still open) nor a failure (no signal a)
    assert s.state()["failing"] == ["python -m pytest -q tests/test_x.py"]
    assert s.fired == []


def test_piped_script_runs_stay_ignored(s: Session) -> None:
    cmd = "python scripts/scrub_check.py docs/x.md | tail -3"
    for _ in range(3):
        assert s.ok(command=cmd, stdout="hit: line 4\nFound 1 error") == []
    assert s.fired == []


def test_signature_is_stable_across_piped_and_unpiped_forms() -> None:
    key = "python -m pytest -q tests/test_x.py"
    full = sd.read_summary(key, PYTEST_OUTPUT)
    later = PYTEST_OUTPUT.replace("0.42s", "1.97s").replace(":7:", ":9:")
    assert full[0] == "fail"
    assert sd.read_summary(key, _tail(PYTEST_OUTPUT, 20)) == full
    assert sd.read_summary(key, _tail(later, 2)) == full
    other = PYTEST_OUTPUT.replace("test_one", "test_two")
    assert sd.read_summary(key, other)[1] != full[1]


def test_unpiped_then_piped_same_failure_fires_a(s: Session) -> None:
    assert s.fail(command=PYTEST, output=PYTEST_OUTPUT) == []
    assert s.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 5)) == ["a"]


def test_piped_ruff(s: Session) -> None:
    cmd = "ruff check src/ tests/ 2>&1 | tail -15"
    full = (
        "F401 [*] `os` imported but unused\n --> src/a.py:1:8\n"
        "E501 Line too long (108 > 100)\n --> src/b.py:72:101\n"
        "Found 2 errors.\n[*] 1 fixable with the `--fix` option.\n"
    )
    concise = "src/a.py:1:8: F401 [*] `os` imported\nsrc/b.py:9:101: E501 too long\nFound 2 errors."
    assert s.ok(command=cmd, stdout=full) == []
    assert s.ok(command=cmd, stdout=full) == ["a"]
    assert sd.read_summary("ruff check src/", full) == sd.read_summary("ruff check src/", concise)
    assert s.ok(command=cmd, stdout="All checks passed!\n") == []
    assert s.state()["failing"] == []


CARGO_OUTPUT = (
    "   Compiling demo v0.1.0 (C:\\work\\demo)\n"
    "    Finished `test` profile [unoptimized + debuginfo] target(s) in 1.20s\n"
    "     Running unittests src/lib.rs (target\\debug\\deps\\demo-1a2b3c4d)\n"
    "\n"
    "running 3 tests\n"
    "test tests::adds ... ok\n"
    "test tests::parses ... FAILED\n"
    "test tests::splits ... ok\n"
    "\n"
    "failures:\n"
    "\n"
    "---- tests::parses stdout ----\n"
    "thread 'tests::parses' panicked at src/lib.rs:41:9:\n"
    "assertion `left == right` failed\n"
    "  left: 1\n"
    " right: 2\n"
    "note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\n"
    "\n"
    "\n"
    "failures:\n"
    "    tests::parses\n"
    "\n"
    "test result: FAILED. 2 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; "
    "finished in 0.01s\n"
    "\n"
    "error: test failed, to rerun pass `--lib`\n"
)
CARGO_PIPED = "cargo test 2>&1 | tail -30"


def test_cargo_summary_reads_failures_and_ids() -> None:
    lines = sd._lines(CARGO_OUTPUT)
    assert sd._cargo_failed_ids(lines) == ["tests::parses"]
    verdict, sig, basis = sd.read_summary("cargo test", CARGO_OUTPUT)
    assert verdict == "fail" and basis == sd.BASIS_IDS
    # the timing and the panic location do not change the signature
    later = CARGO_OUTPUT.replace("0.01s", "0.07s").replace(":41:9", ":44:9")
    assert sd.read_summary("cargo test", later) == (verdict, sig, basis)
    other = CARGO_OUTPUT.replace("parses", "splits_badly")
    assert sd.read_summary("cargo test", other)[1] != sig


def test_cargo_ids_from_the_failures_list_alone() -> None:
    # `| tail -5` keeps the bare-name list and the result line only
    verdict, sig, basis = sd.read_summary("cargo test", _tail(CARGO_OUTPUT, 6))
    assert (verdict, basis) == ("fail", sd.BASIS_IDS)
    assert sig == sd.read_summary("cargo test", CARGO_OUTPUT)[1]


def test_cargo_summary_only_when_the_ids_are_cut_off() -> None:
    verdict, _, basis = sd.read_summary("cargo test", _tail(CARGO_OUTPUT, 3))
    assert (verdict, basis) == ("fail", sd.BASIS_SUMMARY)


def test_cargo_passing_and_multi_binary_results() -> None:
    ok = (
        "test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; "
        "finished in 0.00s\n"
        "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; "
        "finished in 0.02s\n"
    )
    assert sd.read_summary("cargo test", ok) == ("pass", "", "")
    mixed = ok + CARGO_OUTPUT
    assert sd.read_summary("cargo test --workspace", mixed)[0] == "fail"
    # a compile error prints no result line: nothing to settle it
    assert sd.read_summary("cargo test", "error[E0425]: cannot find value `x`\n") == (
        None, "", "",
    )


def test_piped_cargo_test_counts_and_a_pass_resets(s: Session) -> None:
    assert s.ok(command=CARGO_PIPED, stdout=CARGO_OUTPUT) == []
    assert s.state()["failing"] == ["cargo test"]
    assert s.ok(command=CARGO_PIPED, stdout=CARGO_OUTPUT) == ["a"]
    passing = "test result: ok. 3 passed; 0 failed; 0 ignored; finished in 0.00s\n"
    assert s.ok(command=CARGO_PIPED, stdout=passing) == []
    assert s.state()["failing"] == []


def test_unpiped_cargo_test_failure_uses_the_summary(s: Session) -> None:
    assert s.fail(command="cargo test", output=CARGO_OUTPUT, code=101) == []
    assert s.ok(command=CARGO_PIPED, stdout=_tail(CARGO_OUTPUT, 6)) == ["a"]
    assert s.fires_log()[0]["signature_basis"] == sd.BASIS_IDS


def test_piped_cargo_build_without_a_summary_is_ignored(s: Session) -> None:
    for _ in range(3):
        assert s.ok(command="cargo build 2>&1 | tail -5", stdout="error: could not compile") == []
    assert s.fired == []


def test_no_double_firing_in_one_episode(s: Session) -> None:
    s.fail()
    for _ in range(5):
        s.fail()
    for i in range(10):
        s.write("mod.py", f"v{i % 3}\n")
    assert sorted(s.fired) == ["a", "b", "c"]
    assert len(s.fires_log()) == 3


def test_signals_re_arm_after_the_failing_command_passes(s: Session) -> None:
    s.fail()
    assert s.fail() == ["a"]
    assert s.fail() == []
    s.ok()
    assert s.fail() == []
    assert s.fail() == ["a"]
    for i in range(4):
        s.write("mod.py", f"r{i}\n")
    assert s.fired == ["a", "a", "b"]


def test_episode_lasts_until_every_failing_command_passes(s: Session) -> None:
    s.fail(command=PYTEST)
    s.fail(command="ruff check src/", output="F401 unused import")
    s.ok(command="ruff check src/")
    for i in range(4):
        s.write("mod.py", f"v{i}\n")
    assert s.fired == ["b"]


def test_a_new_session_starts_a_fresh_state(tmp_path: Path) -> None:
    first = Session(tmp_path, session_id="s1")
    first.fail()
    second = Session(tmp_path, session_id="s2")
    assert second.fail() == []


def test_powershell_tool_is_watched_the_same_way(tmp_path: Path) -> None:
    ps = Session(tmp_path, tool="PowerShell")
    cmd = r".venv\Scripts\python.exe -m pytest -q tests\test_x.py"
    assert ps.fail(command=cmd) == []
    assert ps.fail(command=cmd) == ["a"]


def test_failure_without_an_exit_line_or_interrupted_is_ignored(s: Session) -> None:
    for _ in range(3):
        s._send({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
            "tool_input": {"command": PYTEST}, "error": "could not start shell",
        })
        s._send({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
            "tool_input": {"command": PYTEST}, "error": "Exit code 1\nx", "is_interrupt": True,
        })
    assert s.fired == []


# --- Where state and firings live ------------------------------------------------------------


def test_nothing_is_written_inside_the_repo(s: Session) -> None:
    s.fail()
    s.fail()
    for i in range(4):
        s.write("mod.py", f"v{i}\n")
    assert s.fired == ["a", "b"]
    written = sorted(p.name for p in s.root.iterdir())
    assert written == [".git", "mod.py"]  # mod.py is the test's own edit target
    assert s.state_file.exists()
    assert (s.home / sd.FIRES_FILE).exists()


def test_state_is_kept_per_repo(tmp_path: Path) -> None:
    one = Session(tmp_path, repo="alpha")
    two = Session(tmp_path, repo="beta")
    assert one.fail() == []
    assert two.fail() == []  # beta's first failure, whatever alpha did
    assert one.fail() == ["a"]
    assert two.fail() == ["a"]
    assert {e["repo"] for e in one.fires_log()} == {"alpha", "beta"}
    assert sorted(p.name for p in (tmp_path / "home" / sd.STATE_DIR).glob("*.json")) == [
        "alpha.json", "beta.json",
    ]


def test_repo_name_is_the_git_top_level(tmp_path: Path) -> None:
    top = tmp_path / "my-repo"
    sub = top / "pkg" / "deep"
    sub.mkdir(parents=True)
    (top / ".git").mkdir()
    assert sd.repo_name(sub) == "my-repo"
    assert sd.repo_name(top) == "my-repo"
    worktree = tmp_path / "wt one"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")  # linked worktree
    assert sd.repo_name(worktree) == "wt_one"
    plain = tmp_path / "no-git"
    plain.mkdir()
    assert sd.repo_name(plain) in ("no-git", sd.repo_name(tmp_path))


# --- Fires log -------------------------------------------------------------------------------


def test_fires_log_contains_no_command_output(s: Session) -> None:
    secret = "SENTINEL_OUTPUT_7f3a client cell value"
    output = f"{secret}\nFAILED tests/test_x.py::t\n1 failed"
    s.fail(output=output)
    s.fail(output=output)
    for i in range(4):
        s.write("mod.py", f"v{i % 2}\n")
    log_text = (s.home / sd.FIRES_FILE).read_text(encoding="utf-8")
    state_text = s.state_file.read_text(encoding="utf-8")
    assert "SENTINEL" not in log_text and "client cell" not in log_text
    assert "SENTINEL" not in state_text
    entries = s.fires_log()
    assert [e["signal"] for e in entries] == ["a", "c", "b"]  # c on the 3rd edit, b on the 4th
    sig = sd.error_signature(output)
    for e in entries:
        where = "command" if "command" in e else "file"
        assert set(e) == {"ts", "repo", "signal", where, "signature", "signature_basis"}
        assert e["signature"] == sig
        assert e["repo"] == "repo"
        assert e["signature_basis"] == sd.BASIS_TAIL  # no "in N s" summary in that output
    assert entries[0]["command"] == "python -m pytest -q tests/test_x.py"
    assert {e.get("file") for e in entries[1:]} == {"mod.py"}


def test_signature_basis_summary_ids_vs_summary_only(tmp_path: Path) -> None:
    with_ids = Session(tmp_path, repo="ids")
    with_ids.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 2))
    with_ids.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 2))
    only = Session(tmp_path, repo="only")
    only.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 1))  # the FAILED line cut off
    assert only.ok(command=PIPED, stdout=_tail(PYTEST_OUTPUT, 1)) == ["a"]
    for _ in range(4):
        only.write("mod.py", f"{_}\n")
    by_repo = {(e["repo"], e["signal"]): e["signature_basis"] for e in only.fires_log()}
    assert by_repo == {
        ("ids", "a"): sd.BASIS_IDS,
        ("only", "a"): sd.BASIS_SUMMARY,
        ("only", "b"): sd.BASIS_SUMMARY,  # edits carry the failing command's basis
    }


# --- Duplicate delivery: two registered copies of the hook see the same event ----------------
# A user-level and a project-level registration of different files both run (Claude Code
# only merges identical handlers). They share one home, so without a guard every event
# counts twice: signal (a) after ONE failure. The guard: an event's tool_use_id is
# processed once per repo.


def _event(root: Path, tool_use_id: str | None, **fields: object) -> dict:
    event = {"session_id": "s1", "cwd": str(root), **fields}
    if tool_use_id is not None:
        event["tool_use_id"] = tool_use_id
    return event


def _fail_event(root: Path, tool_use_id: str | None) -> dict:
    return _event(root, tool_use_id, hook_event_name="PostToolUseFailure", tool_name="Bash",
                  tool_input={"command": PYTEST}, error=f"Exit code 1\n{FAILURE}",
                  is_interrupt=False)


def _write_event(root: Path, name: str, content: str, tool_use_id: str | None) -> dict:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return _event(root, tool_use_id, hook_event_name="PostToolUse", tool_name="Write",
                  tool_input={"file_path": str(path), "content": content},
                  tool_response={"filePath": str(path)})


def _twice(event: dict, home: Path, root: Path) -> list[dict | None]:
    return [sd.process(event, home, root), sd.process(event, home, root)]


def test_one_failure_seen_by_two_copies_counts_once(tmp_path: Path) -> None:
    s = Session(tmp_path)
    assert _twice(_fail_event(s.root, "toolu_1"), s.home, s.root) == [None, None]
    assert s.state()["commands"][PYTEST]["streak"] == 1
    traces = (s.home / sd.TRACE_DIR / "repo.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(traces) == 1


def test_a_still_fires_on_the_second_real_failure_under_two_copies(tmp_path: Path) -> None:
    s = Session(tmp_path)
    _twice(_fail_event(s.root, "toolu_1"), s.home, s.root)
    first, second = _twice(_fail_event(s.root, "toolu_2"), s.home, s.root)
    assert first is not None and "signal (a)" in first["systemMessage"]
    assert second is None  # the second copy says nothing: one report per real event
    assert [f["signal"] for f in s.fires_log()] == ["a"]


def test_b_counts_real_edits_not_deliveries(tmp_path: Path) -> None:
    s = Session(tmp_path)
    _twice(_fail_event(s.root, "toolu_f"), s.home, s.root)
    outs = []
    for i in range(4):
        outs += _twice(_write_event(s.root, "mod.py", f"v{i}\n", f"toolu_e{i}"), s.home, s.root)
    assert outs[:6] == [None] * 6  # 3 real edits, delivered twice each: no (b) yet
    assert outs[6] is not None and "signal (b)" in outs[6]["systemMessage"]
    assert outs[7] is None


def test_without_a_tool_use_id_every_delivery_is_processed(tmp_path: Path) -> None:
    s = Session(tmp_path)  # older Claude Code: no id, so no dedup (behavior unchanged)
    first, second = _twice(_fail_event(s.root, None), s.home, s.root)
    assert first is None and second is not None and "signal (a)" in second["systemMessage"]


def test_the_seen_list_is_bounded(tmp_path: Path) -> None:
    s = Session(tmp_path)
    for i in range(sd.SEEN_EVENTS_KEPT + 20):
        sd.process(_fail_event(s.root, f"toolu_{i}"), s.home, s.root)
    assert len(s.state()["seen"]) == sd.SEEN_EVENTS_KEPT


# --- Command classification ------------------------------------------------------------------


@pytest.mark.parametrize(("command", "expected"), [
    ("pytest -q", ("pytest -q", True)),
    (".venv/bin/python -m pytest -q", ("python -m pytest -q", True)),
    ("cd /x && python -m pytest tests/a.py -q", ("python -m pytest tests/a.py -q", True)),
    ("ruff check src/ tests/", ("ruff check src/ tests/", True)),
    ("python scripts/scrub_check.py docs/x.md", ("python scripts/scrub_check.py docs/x.md", True)),
    ("python -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests",
     ("python -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests",
      True)),
    ("ruff check src && python -m pytest -q", ("ruff check src && python -m pytest -q", True)),
    ("set -o pipefail; python -m pytest -q | tail -5", ("python -m pytest -q", True)),
    ("python -m pytest -q && echo ok", ("python -m pytest -q", True)),
    ("python -m pytest -q 2>&1 > out.log", ("python -m pytest -q", True)),
    ("python -m pytest -q | tail -5", ("python -m pytest -q", False)),
    ("python -m pytest -q 2>&1 | tail -5", ("python -m pytest -q", False)),
    ("python -m pytest -q; echo done", ("python -m pytest -q", False)),
    ("python -m pytest -q || true", ("python -m pytest -q", False)),
    ("cargo test", ("cargo test", True)),
    ("cargo test -q --workspace", ("cargo test -q --workspace", True)),
    ("cargo +nightly test", ("cargo +nightly test", True)),
    ("cargo build --release", ("cargo build --release", True)),
    ("cargo clippy -- -D warnings", ("cargo clippy -- -D warnings", True)),
    ("cargo test 2>&1 | tail -30", ("cargo test", False)),
    ("npm test", ("npm test", True)),
    ("npm run test:unit", ("npm run test:unit", True)),
    ("npm run build", ("npm run build", True)),
    ("cd ui/frontend && npm run build", ("npm run build", True)),
    ("pnpm test", ("pnpm test", True)),
    ("pnpm build", ("pnpm build", True)),
    ("pnpm run test:e2e", ("pnpm run test:e2e", True)),
    ("tsc --noEmit", ("tsc --noEmit", True)),
    ("npx tsc -b", ("npx tsc -b", True)),
    ("pnpm exec tsc --noEmit", ("pnpm exec tsc --noEmit", True)),
    ("grep -rn 'pytest' docs/", None),
    ("rg -n \"ruff check\" CLAUDE.md", None),
    ("git log --oneline", None),
    ("python .claude/skills/spiral-breaker/scripts/run_replay.py --runs 3", None),
    ("python -m codegen.cli generate --frd-contract a --sttm-contract b", None),
    ("cargo run", None),
    ("cargo fmt --check", None),
    ("cargo add serde", None),
    ("npm install", None),
    ("npm run dev", None),
    ("pnpm add react", None),
    ("pnpm install", None),
    ("rg tsconfig .", None),
    ('"C:/Users/Some One/proj/.venv/Scripts/python.exe" -m pytest -q t.py',
     ("python -m pytest -q t.py", True)),
    ("'/home/a b/venv/bin/python' -m pytest -q", ("python -m pytest -q", True)),
    ('python -m pytest -q -k "not slow" t.py', ('python -m pytest -q -k "not slow" t.py', True)),
])
def test_watched_run(command: str, expected: tuple[str, bool] | None) -> None:
    assert sd.watched_run(command) == expected


# Inline scripts that only MENTION a watched command are not runs of it (proposals.md,
# 2026-10-05 bug: classification matched 'pytest' as a substring of script text).
@pytest.mark.parametrize("command", [
    # the 2026-10-05 reproduction: a heredoc script holding a pytest command string
    'python - <<\'EOF\'\nkey = "python -m pytest -q -rf tests/test_zz_spiral_check.py"\n'
    "print(key)\nEOF",
    # a heredoc writing a doc that mentions a pytest run (an apostrophe in the body)
    "cat > SETUP.md <<'EOF'\n# Setup\nThe hook's tests: python -m pytest -q hook/tests\nEOF",
    # unquoted and dash-stripped delimiters
    "cat > a.md <<EOF\nrun pytest -q to check\nEOF",
    "cat > a.md <<-END\n\tpython -m pytest -q\n\tEND",
    # quoted script text passed to an interpreter
    "python -c \"print('later: python -m pytest -q tests')\"",
    # a PowerShell here-string piped into python
    "@'\nkey = \"python -m pytest -q\"\n'@ | python -",
])
def test_inline_script_mentioning_pytest_is_not_a_watched_run(command: str) -> None:
    assert sd.watched_run(command) is None


@pytest.mark.parametrize(("command", "expected"), [
    # a real run after a heredoc keeps a clean key, even when the body has an apostrophe
    ("python - <<'EOF'\n# don't touch the header\np.write_text(s)\nEOF\n"
     "python -m pytest -q -rf tests/t.py | grep -E \"passed|failed\"",
     ("python -m pytest -q -rf tests/t.py", False)),
    ("cat > f.py <<'EOF'\nx = 1\nEOF\npython -m pytest -q", ("python -m pytest -q", True)),
    # a heredoc fed to the watched command itself is still that run
    ("python -m pytest -q - <<'EOF'\nignored\nEOF", ("python -m pytest -q - <<'EOF'", True)),
    # shell wrappers really run their quoted command
    ('bash -c "python -m pytest -q"', ('bash -c "python -m pytest -q"', True)),
    # the PowerShell call operator
    ("& python -m pytest -q", ("& python -m pytest -q", True)),
    # an env-var prefix
    ('PYTHONPATH="$SP/site" python -m pytest -q t.py',
     ('PYTHONPATH="$SP/site" python -m pytest -q t.py', True)),
    # a shift, not a heredoc
    ("echo $((1<<2)) && python -m pytest -q", ("python -m pytest -q", True)),
])
def test_real_runs_around_inline_scripts_stay_watched(
    command: str, expected: tuple[str, bool]
) -> None:
    assert sd.watched_run(command) == expected


def test_absolute_repo_script_path_is_watched(tmp_path: Path) -> None:
    cmd = f'python "{tmp_path.as_posix()}/scripts/scrub_check.py"'
    assert sd.watched_key(cmd, tmp_path) is not None
    assert sd.watched_key(cmd, tmp_path / "elsewhere") is None


# --- The script as Claude Code runs it ------------------------------------------------------------


def _run_hook(
    event: dict, home: Path, root: Path, interpreter: list[str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env[sd.HOME_ENV] = str(home)
    env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        [*(interpreter or [sys.executable]), str(HOOK)], input=json.dumps(event).encode("utf-8"),
        capture_output=True, env=env, timeout=30, check=False,
    )


def _e2e(tmp_path: Path, interpreter: list[str] | None = None) -> None:
    root = tmp_path / "proj"
    (root / ".git").mkdir(parents=True)
    home = tmp_path / "home"
    event = {
        "session_id": "e2e", "cwd": str(root), "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash", "tool_input": {"command": "python -m pytest -q"},
        "tool_use_id": "toolu_1", "error": "Exit code 1\nFAILED t\n1 failed", "is_interrupt": False,
    }
    first = _run_hook(event, home, root, interpreter)
    assert first.returncode == 0 and first.stdout == b"", first.stderr
    # a second, separate failure: its own tool_use_id (the same id would be a duplicate
    # delivery of the first, which the hook skips)
    second = _run_hook({**event, "tool_use_id": "toolu_2"}, home, root, interpreter)
    assert second.returncode == 0, second.stderr
    out = json.loads(second.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUseFailure"
    assert MESSAGE_RE.match(out["hookSpecificOutput"]["additionalContext"])
    assert (home / sd.STATE_DIR / "proj.json").exists()
    fires = (home / sd.FIRES_FILE).read_text(encoding="utf-8").splitlines()
    assert json.loads(fires[0])["repo"] == "proj"
    assert sorted(p.name for p in root.iterdir()) == [".git"]


def test_script_end_to_end_over_stdin(tmp_path: Path) -> None:
    _e2e(tmp_path)


@pytest.mark.skipif(shutil.which("py") is None, reason="no py launcher (Windows only)")
def test_script_end_to_end_under_the_py_launcher(tmp_path: Path) -> None:
    """The interpreter ~/.claude/settings.json registers: `py -3`, no repo venv."""
    _e2e(tmp_path, ["py", "-3"])


def test_script_never_fails_on_bad_input(tmp_path: Path) -> None:
    env = dict(os.environ)
    env[sd.HOME_ENV] = str(tmp_path / "home")
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=b"not json", capture_output=True,
        env=env, timeout=30, check=False,
    )
    assert proc.returncode == 0 and proc.stdout == b""


# --- Repo attribution: the repo a command ran in, not CLAUDE_PROJECT_DIR -----------------------


FAIL_OUT = "FAILED tests/test_x.py::test_one - assert 1 == 2\n1 failed, 3 passed in 0.42s"


def _repo(path: Path) -> Path:
    (path / ".git").mkdir(parents=True, exist_ok=True)
    return path


def _shell_fail(home: Path, project: Path, command: str, cwd: Path | None) -> list[str]:
    event = {
        "session_id": "attr", "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
        "tool_input": {"command": command}, "error": f"Exit code 1\n{FAIL_OUT}",
        "is_interrupt": False,
    }
    if cwd is not None:
        event["cwd"] = str(cwd)
    out = sd.process(event, home, project)
    if out is None:
        return []
    return [MESSAGE_RE.match(ln).group(1) for ln in out["systemMessage"].split("\n")]


def _edit(home: Path, project: Path, file: Path, content: str) -> list[str]:
    file.write_text(content, encoding="utf-8")
    event = {
        "session_id": "attr", "cwd": str(project), "hook_event_name": "PostToolUse",
        "tool_name": "Write", "tool_input": {"file_path": str(file), "content": content},
        "tool_response": {"filePath": str(file)},
    }
    out = sd.process(event, home, project)
    return [] if out is None else ["fired"]


def _state(home: Path, repo: str) -> dict:
    path = home / sd.STATE_DIR / f"{repo}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _fires(home: Path) -> list[dict]:
    path = home / sd.FIRES_FILE
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def test_a_command_run_in_repo_x_is_keyed_to_x_not_the_project(tmp_path: Path) -> None:
    """Case a (the 2026-10-05 bug): the hook's cwd is the project (a cd outside it is
    reset after the command), but the command ran in X after `cd X &&`."""
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    x = _repo(tmp_path / "repo_x")
    cmd = f'cd "{x.as_posix()}" && python -m pytest -q'
    assert _shell_fail(home, project, cmd, cwd=project) == []
    assert _shell_fail(home, project, cmd, cwd=project) == ["a"]
    assert _state(home, "repo_x")["failing"] == ["python -m pytest -q"]
    assert _state(home, "proj_y") == {}
    assert [f["repo"] for f in _fires(home)] == ["repo_x"]


@pytest.mark.parametrize("cd_arg", ["../team", "team"])
def test_b_a_cd_already_reflected_in_cwd_is_not_applied_twice(tmp_path: Path, cd_arg: str) -> None:
    """Case b: the hook's cwd already reflects the cd (repo_b/team, inside repo_b). A
    doubled `cd team` would land in repo_b/team/team, its own repo named "team"."""
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    repo_b = _repo(tmp_path / "repo_b")
    cwd = repo_b / "team"
    _repo(cwd / "team")  # the trap
    cmd = f"cd {cd_arg} && python -m pytest -q"
    assert sd.command_dir(cmd, cwd) == cwd.resolve()
    _shell_fail(home, project, cmd, cwd=cwd)
    assert _shell_fail(home, project, cmd, cwd=cwd) == ["a"]
    assert [f["repo"] for f in _fires(home)] == ["repo_b"]
    assert sorted(p.name for p in (home / sd.STATE_DIR).glob("*.json")) == ["repo_b.json"]


def test_c_an_edit_under_dot_claude_does_not_count_against_the_project(tmp_path: Path) -> None:
    """Case c: repo Y has an open failure; edits to a file in the central folder (its own
    repo under ~/.claude) are filed under that repo and never count toward Y's episode."""
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    central = _repo(tmp_path / "dot_claude" / "spiral-breaker")
    (central / "hook").mkdir()
    target = central / "hook" / "spiral_detector.py"
    _shell_fail(home, project, "python -m pytest -q", cwd=project)  # Y: open failure
    for i in range(5):
        assert _edit(home, project, target, f"v{i}\n") == []
    assert _fires(home) == []
    assert _state(home, "proj_y")["episode"]["edits"] == {}


def test_the_hook_cwd_field_decides_the_repo(tmp_path: Path) -> None:
    """A cd that stayed inside the project persists; the hook's cwd reflects it."""
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    x = _repo(project / "vendor" / "repo_x")  # a nested repo inside the project
    _shell_fail(home, project, "python -m pytest -q", cwd=x)
    assert _shell_fail(home, project, "python -m pytest -q", cwd=x) == ["a"]
    assert [f["repo"] for f in _fires(home)] == ["repo_x"]


def test_without_a_cwd_field_the_project_dir_is_the_fallback(tmp_path: Path) -> None:
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    _shell_fail(home, project, "python -m pytest -q", cwd=None)
    assert _shell_fail(home, project, "python -m pytest -q", cwd=None) == ["a"]
    assert [f["repo"] for f in _fires(home)] == ["proj_y"]


def test_episodes_in_two_repos_do_not_mix(tmp_path: Path) -> None:
    """The same command failing once in each of two repos is not a streak of two, and
    edits in X count only toward X's own episode, never toward Y's failure."""
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    x = _repo(tmp_path / "repo_x")
    cmd = "python -m pytest -q"
    assert _shell_fail(home, project, cmd, cwd=project) == []
    assert _shell_fail(home, project, f'cd "{x.as_posix()}" && {cmd}', cwd=project) == []
    assert _fires(home) == []  # one failure in each repo: no streak of two
    for i in range(5):
        _edit(home, project, x / "mod.py", f"v{i}\n")
    assert [(f["repo"], f["signal"]) for f in _fires(home)] == [("repo_x", "b")]
    assert _state(home, "proj_y")["failing"] == [cmd]
    assert _state(home, "repo_x")["failing"] == [cmd]
    assert _state(home, "proj_y")["episode"]["edits"] == {}


@pytest.mark.skipif(os.name != "nt", reason="Git Bash drive paths exist only on Windows")
def test_a_git_bash_drive_path_cd_is_resolved(tmp_path: Path) -> None:
    home, project = tmp_path / "home", _repo(tmp_path / "proj_y")
    x = _repo(tmp_path / "repo_x")
    drive, rest = x.as_posix().split(":", 1)
    cmd = f'cd "/{drive.lower()}{rest}" && python -m pytest -q'
    _shell_fail(home, project, cmd, cwd=project)
    assert _shell_fail(home, project, cmd, cwd=project) == ["a"]
    assert [f["repo"] for f in _fires(home)] == ["repo_x"]


def test_repo_top_asks_git(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    real = tmp_path / "real-repo"
    (real / "a" / "b").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(real)], check=True)
    assert sd.repo_top(real / "a" / "b").resolve() == real.resolve()
    assert sd.repo_name(real / "a" / "b") == "real-repo"
