"""The spiral-detector hook (.claude/hooks/spiral_detector.py), driven by scripted
event sequences shaped like the documented PostToolUse / PostToolUseFailure input."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "spiral_detector.py"

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
    r"^spiral-detector hook \(user-configured in \.claude/settings\.local\.json\): "
    r"signal \((a|b|c)\): [^\n]+\.$"
)
PIPED = "python -m pytest -q tests/test_x.py 2>&1 | tail -20"
PASSING = "4 passed in 0.31s"


class Session:
    """Feeds events to process() and records which signals fired."""

    def __init__(self, tmp_path: Path, session_id: str = "s1", tool: str = "Bash") -> None:
        self.root = tmp_path / "repo"
        self.root.mkdir(exist_ok=True)
        self.state_dir = self.root / ".local"
        self.session_id = session_id
        self.tool = tool
        self.fired: list[str] = []
        self.outputs: list[dict] = []

    def _send(self, event: dict) -> list[str]:
        event = {"session_id": self.session_id, "cwd": str(self.root), **event}
        out = sd.process(event, self.state_dir, self.root)
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
        """Exit 0. For a piped command that is the pipe tail's exit, whatever pytest did."""
        return self._send({
            "hook_event_name": "PostToolUse",
            "tool_name": self.tool,
            "tool_input": {"command": command, "description": "run"},
            "tool_response": {
                "stdout": stdout, "stderr": "", "interrupted": False, "isImage": False,
            },
        })

    def state(self) -> dict:
        return json.loads((self.state_dir / sd.STATE_FILE).read_text(encoding="utf-8"))

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
        path = self.state_dir / sd.FIRES_FILE
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
        'File "src/codegen/x.py", line 120, in f\n'
        "1 failed in 3.10s"
    )
    second = (
        "2026-10-05T10:19:55Z start\n"
        r"C:\Users\x\AppData\Local\Temp\pytest-of-x\pytest-8\test_a0\in.txt not found" "\n"
        "tests/test_x.py:44: AssertionError at 0x55e0c1d8\n"
        'File "src/codegen/x.py", line 123, in f\n'
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
    state = json.loads((s.state_dir / sd.STATE_FILE).read_text(encoding="utf-8"))
    assert state["failing"] == [] and state["commands"] == {} and state["episode"]["edits"] == {}


def test_a_watched_command_piped_into_rg_is_not_judged(s: Session) -> None:
    piped = "python -m pytest -q 2>&1 | rg FAILED"
    for _ in range(3):
        assert s.fail(command=piped, output="", code=1) == []
    assert s.fired == []


# --- Piped runs: judged from the pytest / ruff summary --------------------------------------


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


# --- Fires log -------------------------------------------------------------------------------


def test_fires_log_contains_no_command_output(s: Session) -> None:
    secret = "SENTINEL_OUTPUT_7f3a client cell value"
    output = f"{secret}\nFAILED tests/test_x.py::t\n1 failed"
    s.fail(output=output)
    s.fail(output=output)
    for i in range(4):
        s.write("mod.py", f"v{i % 2}\n")
    log_text = (s.state_dir / sd.FIRES_FILE).read_text(encoding="utf-8")
    state_text = (s.state_dir / sd.STATE_FILE).read_text(encoding="utf-8")
    assert "SENTINEL" not in log_text and "client cell" not in log_text
    assert "SENTINEL" not in state_text
    entries = s.fires_log()
    assert [e["signal"] for e in entries] == ["a", "c", "b"]  # c on the 3rd edit, b on the 4th
    sig = sd.error_signature(output)
    for e in entries:
        where = "command" if "command" in e else "file"
        assert set(e) == {"ts", "signal", where, "signature"}
        assert e["signature"] == sig
    assert entries[0]["command"] == "python -m pytest -q tests/test_x.py"
    assert {e.get("file") for e in entries[1:]} == {"mod.py"}


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
    ("grep -rn 'pytest' docs/", None),
    ("rg -n \"ruff check\" CLAUDE.md", None),
    ("git log --oneline", None),
    ("python .claude/skills/spiral-breaker/scripts/run_replay.py --runs 3", None),
    ("python -m codegen.cli generate --frd-contract a --sttm-contract b", None),
])
def test_watched_run(command: str, expected: tuple[str, bool] | None) -> None:
    assert sd.watched_run(command) == expected


def test_absolute_repo_script_path_is_watched(tmp_path: Path) -> None:
    cmd = f'python "{tmp_path.as_posix()}/scripts/scrub_check.py"'
    assert sd.watched_key(cmd, tmp_path) is not None
    assert sd.watched_key(cmd, tmp_path / "elsewhere") is None


# --- The script as Claude Code runs it ------------------------------------------------------------


def _run_hook(event: dict, state_dir: Path, root: Path) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env["SPIRAL_DETECTOR_STATE_DIR"] = str(state_dir)
    env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(event).encode("utf-8"),
        capture_output=True, env=env, timeout=30, check=False,
    )


def test_script_end_to_end_over_stdin(tmp_path: Path) -> None:
    event = {
        "session_id": "e2e", "cwd": str(tmp_path), "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash", "tool_input": {"command": "python -m pytest -q"},
        "tool_use_id": "toolu_1", "error": "Exit code 1\nFAILED t\n1 failed", "is_interrupt": False,
    }
    first = _run_hook(event, tmp_path / ".local", tmp_path)
    assert first.returncode == 0 and first.stdout == b""
    second = _run_hook(event, tmp_path / ".local", tmp_path)
    assert second.returncode == 0
    out = json.loads(second.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUseFailure"
    assert MESSAGE_RE.match(out["hookSpecificOutput"]["additionalContext"])


def test_script_never_fails_on_bad_input(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["SPIRAL_DETECTOR_STATE_DIR"] = str(tmp_path / ".local")
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=b"not json", capture_output=True,
        env=env, timeout=30, check=False,
    )
    assert proc.returncode == 0 and proc.stdout == b""
