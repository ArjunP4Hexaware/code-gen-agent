"""Hook event traces (traces/<repo>.jsonl) and replay_traces.py: the line format, no
output or content leaks, pruning, and that replaying the current detector over a
scripted history reproduces the live firings exactly."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOK_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


sd = _load("spiral_detector")
rt = _load("replay_traces")

T0 = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
FAIL = "FAILED tests/test_x.py::test_one - assert 1 == 2\n1 failed, 3 passed in 0.42s"
SECRET_OUT = "SENTINEL_OUTPUT_9q client cell value"
SECRET_FILE = "SENTINEL_CONTENT_7z private text"

RUN_KEYS = {"ts", "session_id", "repo", "kind", "key", "outcome", "signature",
            "signature_basis", "fail_ids"}
EDIT_KEYS = {"ts", "session_id", "repo", "kind", "file", "is_doc", "outcome",
             "content_hash", "before_hash"}
IGNORED_EDIT_KEYS = {"ts", "session_id", "repo", "kind", "file", "is_doc", "outcome"}


class Clock:
    def __init__(self, start: datetime = T0) -> None:
        self.now = start

    def tick(self, seconds: int = 1) -> datetime:
        self.now += timedelta(seconds=seconds)
        return self.now


class Driver:
    """Feeds live events to sd.process with a controllable clock."""

    def __init__(self, tmp_path: Path, clock: Clock | None = None) -> None:
        self.home = tmp_path / "home"
        self.project = tmp_path / "proj"
        (self.project / ".git").mkdir(parents=True, exist_ok=True)
        self.clock = clock or Clock()
        self.session = "s1"

    def repo(self, name: str) -> Path:
        path = self.project.parent / name
        (path / ".git").mkdir(parents=True, exist_ok=True)
        return path

    def _send(self, event: dict, cwd: Path) -> None:
        event = {"session_id": self.session, "cwd": str(cwd), **event}
        sd.process(event, self.home, self.project, now=self.clock.tick())

    def fail(self, cwd: Path, cmd: str = "python -m pytest -q", out: str = FAIL) -> None:
        self._send({"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                    "tool_input": {"command": cmd}, "error": f"Exit code 1\n{out}",
                    "is_interrupt": False}, cwd)

    def ok(
        self, cwd: Path, cmd: str = "python -m pytest -q", out: str = "4 passed in 0.1s"
    ) -> None:
        self._send({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                    "tool_input": {"command": cmd},
                    "tool_response": {"stdout": out, "stderr": ""}}, cwd)

    def write(self, file: Path, content: str) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        self._send({"hook_event_name": "PostToolUse", "tool_name": "Write",
                    "tool_input": {"file_path": str(file), "content": content},
                    "tool_response": {"filePath": str(file)}}, self.project)

    def edit(self, file: Path, old: str, new: str) -> None:
        file.write_text(file.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
        self._send({"hook_event_name": "PostToolUse", "tool_name": "Edit",
                    "tool_input": {"file_path": str(file), "old_string": old,
                                   "new_string": new, "replace_all": False},
                    "tool_response": {"filePath": str(file)}}, self.project)

    def failed_edit(self, file: Path) -> None:
        self._send({"hook_event_name": "PostToolUseFailure", "tool_name": "Edit",
                    "tool_input": {"file_path": str(file), "old_string": "x",
                                   "new_string": "y"}, "error": "String not found"},
                   self.project)

    def traces(self, repo: str = "proj") -> list[dict]:
        path = self.home / sd.TRACE_DIR / f"{repo}.jsonl"
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]

    def fires(self) -> list[dict]:
        path = self.home / sd.FIRES_FILE
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def d(tmp_path: Path) -> Driver:
    return Driver(tmp_path)


# --- Line format -------------------------------------------------------------------------


def test_trace_line_format(d: Driver) -> None:
    p = d.project
    d.fail(p)
    d.ok(p)
    d.ok(p, cmd="python -m pytest -q | tail -3", out="collecting ...")  # no summary
    d.write(p / "src" / "a.py", "x = 1\n")
    d.edit(p / "src" / "a.py", "x = 1", "x = 2")
    d.write(p / "docs" / "notes.txt", "n\n")
    d.write(p / "README.md", "r\n")
    d.failed_edit(p / "src" / "a.py")
    d.ok(p, cmd="git status")  # unwatched: not traced
    recs = d.traces()
    assert [r["kind"] for r in recs] == ["run"] * 3 + ["edit"] * 5
    assert [r["outcome"] for r in recs] == [
        "fail", "pass", "ignored", "pass", "pass", "pass", "pass", "ignored"]
    for r in recs[:3]:
        assert set(r) == RUN_KEYS
        assert r["key"] == "python -m pytest -q"
    assert recs[0]["signature"] and recs[0]["signature_basis"] == sd.BASIS_IDS
    assert recs[1]["signature"] == "" == recs[2]["signature"]
    for r in recs[3:7]:
        assert set(r) == EDIT_KEYS
    assert set(recs[7]) == IGNORED_EDIT_KEYS
    assert [r["file"] for r in recs[3:]] == [
        "src/a.py", "src/a.py", "docs/notes.txt", "README.md", "src/a.py"]
    assert [r["is_doc"] for r in recs[3:]] == [False, False, True, True, False]
    assert recs[3]["before_hash"] is None  # a Write can't be undone from its input
    assert recs[4]["before_hash"] == recs[3]["content_hash"]  # an Edit can
    for r in recs:
        assert r["repo"] == "proj" and r["session_id"] == "s1"
        datetime.strptime(r["ts"], sd.TS_FORMAT)


# --- Per-test fingerprints (fail_ids): which tests fail, hashed, never named ----------------


def _ids(*node_ids: str) -> list[str]:
    return sorted({sd.id_fingerprint(n) for n in node_ids})


def test_a_failing_run_records_one_fingerprint_per_failing_test(d: Driver) -> None:
    p = d.project
    d.fail(p, out="FAILED tests/test_x.py::test_one - assert 1\n"
                  "ERROR tests/test_y.py::test_two - boom\n1 failed, 1 error in 0.2s")
    rec = d.traces()[-1]
    assert rec["outcome"] == "fail"
    assert rec["fail_ids"] == _ids("tests/test_x.py::test_one", "tests/test_y.py::test_two")


def test_a_test_moving_from_error_to_failed_keeps_its_fingerprint(d: Driver) -> None:
    p = d.project
    d.fail(p, out="ERROR tests/test_x.py::test_one - ImportError\n1 error in 0.1s")
    d.fail(p, out="FAILED tests/test_x.py::test_one - assert 1\n1 failed in 0.1s")
    first, second = d.traces()[-2:]
    assert first["fail_ids"] == second["fail_ids"] == _ids("tests/test_x.py::test_one")


def test_piped_and_unpiped_runs_record_the_same_fingerprints(d: Driver) -> None:
    p = d.project
    d.fail(p)
    d.ok(p, cmd="python -m pytest -q 2>&1 | tail -40", out=FAIL)  # piped: judged by summary
    unpiped, piped = d.traces()[-2:]
    assert piped["outcome"] == "fail"
    assert unpiped["fail_ids"] == piped["fail_ids"] == _ids("tests/test_x.py::test_one")


def test_ruff_and_cargo_failures_record_fingerprints(d: Driver) -> None:
    p = d.project
    d.fail(p, cmd="ruff check src", out="src/a.py:1:1: F401 unused\nFound 1 error.")
    d.fail(p, cmd="cargo test", out="test m::t ... FAILED\n"
                                    "test result: FAILED. 2 passed; 1 failed; 0 ignored")
    ruff, cargo = d.traces()[-2:]
    assert ruff["fail_ids"] == _ids("F401")
    assert cargo["fail_ids"] == _ids("m::t")


def test_no_fingerprints_without_test_ids(d: Driver) -> None:
    p = d.project
    d.ok(p, cmd="python -m pytest -q | tail -1", out="1 failed in 0.1s")  # IDs cut off
    d.fail(p, out="Traceback: boom")  # no summary: tail-hash
    d.ok(p)
    summary_only, tail_hash, passed = d.traces()[-3:]
    assert summary_only["outcome"] == tail_hash["outcome"] == "fail"
    assert summary_only["fail_ids"] == tail_hash["fail_ids"] == passed["fail_ids"] == []


def test_fingerprints_never_reveal_the_test_name(d: Driver) -> None:
    d.fail(d.project)
    text = (d.home / sd.TRACE_DIR / "proj.jsonl").read_text(encoding="utf-8")
    assert "test_one" not in text and "test_x" not in text


def test_traces_hold_no_output_or_file_content(d: Driver) -> None:
    p = d.project
    d.fail(p, out=f"{SECRET_OUT}\n{FAIL}")
    d.fail(p, out=f"{SECRET_OUT}\nTraceback: boom")  # tail-hash path
    d.write(p / "mod.py", f"{SECRET_FILE}\n")
    d.edit(p / "mod.py", SECRET_FILE, f"{SECRET_FILE} v2")
    text = (d.home / sd.TRACE_DIR / "proj.jsonl").read_text(encoding="utf-8")
    for needle in ("SENTINEL", "client cell", "private text", "Traceback", "boom"):
        assert needle not in text


def test_traces_are_kept_per_repo_and_never_inside_a_repo(d: Driver) -> None:
    other = d.repo("other")
    d.fail(d.project)
    d.fail(d.project, cmd=f'cd "{other.as_posix()}" && python -m pytest -q')
    assert sorted(p.name for p in (d.home / sd.TRACE_DIR).iterdir()) == [
        "other.jsonl", "proj.jsonl"]
    assert len(d.traces("proj")) == len(d.traces("other")) == 1
    assert sorted(x.name for x in d.project.iterdir()) == [".git"]


# --- Pruning -------------------------------------------------------------------------------


def test_lines_older_than_the_retention_window_are_pruned_on_write(tmp_path: Path) -> None:
    clock = Clock(T0)
    d = Driver(tmp_path, clock)
    d.fail(d.project)  # day 0
    clock.now = T0 + timedelta(days=sd.TRACE_RETENTION_DAYS - 1)
    d.ok(d.project)  # day 59: kept later
    clock.now = T0 + timedelta(days=sd.TRACE_RETENTION_DAYS + 1)
    d.fail(d.project)  # day 61: the day-0 line is now past the window
    outcomes = [(r["ts"][:10], r["outcome"]) for r in d.traces()]
    assert outcomes == [
        ((T0 + timedelta(days=59)).strftime("%Y-%m-%d"), "pass"),
        ((T0 + timedelta(days=61)).strftime("%Y-%m-%d"), "fail"),
    ]


def test_nothing_is_pruned_inside_the_window(d: Driver) -> None:
    for _ in range(5):
        d.fail(d.project)
    assert len(d.traces()) == 5


# --- Replay ----------------------------------------------------------------------------------


def _scripted_history(d: Driver) -> None:
    """Two repos, two sessions, every signal, passes that re-arm, ignored runs."""
    p, other = d.project, d.repo("other")
    other_cmd = f'cd "{other.as_posix()}" && python -m pytest -q'
    d.fail(p)
    d.fail(p)  # (a) in proj
    d.write(p / "mod.py", "one\n")
    d.write(p / "mod.py", "two\n")
    d.write(p / "mod.py", "one\n")  # (c) restored
    d.write(p / "mod.py", "three\n")  # 4th edit: (b)
    d.ok(p, cmd="python -m pytest -q | tail -2", out="...")  # piped, no summary: ignored
    d.ok(p)  # pass: episode reset, re-armed
    d.fail(p, cmd=other_cmd)  # the hook's cwd stays the project; the cd is in the command
    d.fail(p, cmd=other_cmd)  # (a) in other
    d.session = "s2"  # a new session starts fresh state
    d.fail(p)
    d.fail(p)  # (a) again in s2
    d.write(p / "src" / "x.py", "1\n")
    d.edit(p / "src" / "x.py", "1", "2")
    d.edit(p / "src" / "x.py", "2", "1")  # (c) via an Edit's before-hash


def test_replaying_the_current_detector_reproduces_the_live_firings(d: Driver) -> None:
    _scripted_history(d)
    live = sorted(d.fires(), key=lambda f: (f["ts"], f["repo"], f["signal"]))
    assert [(f["repo"], f["signal"]) for f in live] == [
        ("proj", "a"), ("proj", "c"), ("proj", "b"), ("other", "a"), ("proj", "a"),
        ("proj", "c")]
    traces = rt.load_traces(d.home / sd.TRACE_DIR)
    replayed = rt.replay(rt.load_detector(), traces)
    assert replayed == live  # every field: ts, repo, signal, where, signature, basis


def test_a_flag_set_variant_changes_the_replayed_firings(d: Driver) -> None:
    _scripted_history(d)
    traces = rt.load_traces(d.home / sd.TRACE_DIR)
    strict = rt.replay(rt.load_detector(overrides={"SIGNAL_B_EDITS_WHILE_FAILING": 99}),
                       traces)
    current = rt.replay(rt.load_detector(), traces)
    only_current, only_strict = rt.compare(current, strict)
    assert [f["signal"] for f in only_current] == ["b"] and only_strict == []


def test_a_module_variant_is_loaded_from_a_path(d: Driver, tmp_path: Path) -> None:
    _scripted_history(d)
    src = (HOOK_DIR / "spiral_detector.py").read_text(encoding="utf-8")
    variant = tmp_path / "candidate.py"
    variant.write_text(src.replace("SIGNAL_A_SAME_SIGNATURE_FAILS = 2",
                                   "SIGNAL_A_SAME_SIGNATURE_FAILS = 3"), encoding="utf-8")
    traces = rt.load_traces(d.home / sd.TRACE_DIR)
    only_current, only_cand = rt.compare(rt.replay(rt.load_detector(), traces),
                                         rt.replay(rt.load_detector(variant), traces))
    assert sorted(f["signal"] for f in only_current) == ["a", "a", "a"] and only_cand == []


def test_an_unknown_setting_is_rejected() -> None:
    with pytest.raises(SystemExit, match="no setting"):
        rt.load_detector(overrides={"SIGNAL_TYPO": 1})


def test_replay_cli_end_to_end(d: Driver) -> None:
    _scripted_history(d)
    env = dict(os.environ, **{sd.HOME_ENV: str(d.home)})
    proc = subprocess.run(
        [sys.executable, str(HOOK_DIR / "replay_traces.py"), "--json"],
        capture_output=True, text=True, env=env, timeout=60, check=True,
    )
    assert json.loads(proc.stdout) == sorted(
        d.fires(), key=lambda f: (f["ts"], f["repo"], f["signal"]))
    cmp = subprocess.run(
        [sys.executable, str(HOOK_DIR / "replay_traces.py"), "--repo", "proj",
         "--compare-set", "SIGNAL_A_SAME_SIGNATURE_FAILS=3"],
        capture_output=True, text=True, env=env, timeout=60, check=True,
    )
    assert "only in base: 2" in cmp.stdout and "only in candidate: 0" in cmp.stdout
