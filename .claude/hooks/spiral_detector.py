#!/usr/bin/env python3
"""Spiral detector: a Claude Code PostToolUse / PostToolUseFailure hook.

Watches run/test commands and file edits. When one of three pre-registered signals
fires, it REPORTS the signal to Claude (and the user). What to do about it lives in
CLAUDE.md's Debugging section, not in a tool result.

When the exit code cannot be trusted (a watched command piped into another, or
followed by ``;`` / ``||``), pytest's and ruff's own summary lines decide pass or
fail; a run with neither summary is ignored.

Hook contract (Claude Code hooks reference, read 2026-10-05):
- stdin is one JSON object: session_id, cwd, hook_event_name, tool_name,
  tool_input, and either tool_response (PostToolUse) or error / is_interrupt
  (PostToolUseFailure).
- A shell command that exits non-zero fires PostToolUseFailure, whose ``error``
  starts with the line ``Exit code N`` followed by the command's output.
  PostToolUse fires only after a successful run (the Bash tool_response carries
  stdout / stderr / interrupted / isImage, no exit code), so PostToolUse on a
  shell tool means exit 0.
- To reach Claude: exit 0 and print {"hookSpecificOutput": {"hookEventName":
  <event>, "additionalContext": <text>}}; ``systemMessage`` shows it to the user.

Stdlib only. Any internal error exits 0 silently: the hook never blocks or breaks
a session. State: .local/spiral-state.json. Fires log: .local/spiral-hook-fires.jsonl
(timestamp, signal, command or file, signature hash; never command output).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ------------------------------------------------------------
# Thresholds are PRE-REGISTERED (2026-10-05). Do not tune them without a retro
# (.claude/commands/spiral-retro.md).

# A shell command is watched when any segment of it matches one of these.
# Everything else (grep, rg, git, ls, ...) is ignored entirely.
WATCHED_PATTERNS: list[str] = [
    r"(?:^|[\s\\/])pytest(?:\.exe)?(?:\s|$)",  # pytest, .venv/bin/pytest
    r"(?:^|\s)-m\s+pytest(?:\s|$)",  # python -m pytest
    r"(?:^|[\s\\/])ruff(?:\.exe)?(?:\s|$)",  # ruff check / ruff format --check
    r"(?:^|\s)-m\s+ruff(?:\s|$)",  # python -m ruff
    r"(?:^|[\s\"'])(?:\./|\.\\)?scripts[\\/][\w.-]+\.py\b",  # the repo's scripts/*.py
    r"\bcodegen(?:\.cli)?\s+generate(?:-all)?\b.*--dry-run",  # the mock smoke run
]
SIGNAL_A_SAME_SIGNATURE_FAILS = 2  # a: same command, same signature, N fails in a row
SIGNAL_B_EDITS_WHILE_FAILING = 4  # b: same file edited N+ times while failing
SIGNATURE_TAIL_LINES = 20  # the error signature hashes the last N output lines

SHELL_TOOLS = {"Bash", "PowerShell"}
EDIT_TOOLS = {"Edit", "Write"}
STATE_FILE = "spiral-state.json"
FIRES_FILE = "spiral-hook-fires.jsonl"
LOCK_FILE = "spiral-state.lock"
LOCK_WAIT_SECONDS = 3.0
LOCK_STALE_SECONDS = 30.0
DETAIL_MAX_CHARS = 120

# A report, never an instruction: what to do about a signal lives in CLAUDE.md
# ("Debugging"), the user's own file.
MESSAGE = (
    "spiral-detector hook (user-configured in .claude/settings.local.json): "
    "signal ({signal}): {detail}."
)

_WATCHED = [re.compile(p) for p in WATCHED_PATTERNS]

# Output normalization before hashing (order matters: paths before line numbers).
_NORMALIZERS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?"
            r"(?:Z|[+-]\d{2}:?\d{2})?"
        ),
        "<ts>",
    ),
    (
        re.compile(r"(?i)(?:[a-z]:)?(?:[\\/][^\s\"'\\/]+)*?[\\/](?:temp|tmp)[\\/][^\s\"':,)]*"),
        "<tmp>",
    ),
    (re.compile(r"(?i)\bpytest-of-[^\s\\/]+[\\/][^\s\"':,)]*"), "<tmp>"),
    (re.compile(r"0x[0-9a-fA-F]+"), "<addr>"),
    (re.compile(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\b"), "<time>"),
    (re.compile(r"(?i)\bline \d+"), "line <n>"),
    (re.compile(r":\d+(?::\d+)?(?=[:\s,)\]]|$)"), ":<n>"),
    (re.compile(r"\b\d+(?:\.\d+)?\s?(?:ms|s|sec|seconds)\b"), "<dur>"),
    (re.compile(r"\[\d+ characters truncated\]"), "[truncated]"),
]
_CLAUDE_INSERTED = re.compile(r"^(?:Command timed out after .*|Exit code -?\d+)$")
_EXIT_LINE = re.compile(r"^Exit code (-?\d+)\s*$")
_PYTHON_EXE = re.compile(r"(?i)^(?:.*[\\/])?python(?:\d+(?:\.\d+)?)?(?:\.exe)?$")
_REDIRECT = re.compile(r"^\d?>>?(?:&\d|\S*)$")

# Run summaries, read when the exit code cannot be trusted (and for every
# pytest / ruff failure's signature, so piped and unpiped forms hash alike).
_PYTEST_SUMMARY = re.compile(r"\b\d+ (?:failed|passed|errors?)\b.*\bin \d+(?:\.\d+)?s\b")
_PYTEST_COUNT = re.compile(r"\b(\d+) (failed|passed|errors?)\b")
_PYTEST_ID = re.compile(r"^(FAILED|ERROR)\s+(\S+\.py\b.*?)(?:\s+-\s.*)?$")  # node ids only
_RUFF_FOUND = re.compile(r"\bFound (\d+) errors?\b")
_RUFF_PASS = "All checks passed!"
_RUFF_CODE = re.compile(r"(?:^|:\d+:\d+:\s)([A-Z]{1,4}\d{2,4})\b")


# --- Command parsing ----------------------------------------------------------


def split_segments(command: str) -> list[tuple[str, str | None]]:
    """Split a shell command into (segment, operator-after) pairs.

    Operators: ``&&``, ``||``, ``|``, ``;`` and newline (read as ``;``). Quotes are
    respected; a single ``&`` is not an operator (PowerShell's call operator, and
    ``2>&1``).
    """
    segments: list[tuple[str, str | None]] = []
    buf: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        two = command[i : i + 2]
        op = None
        if two in ("&&", "||"):
            op, step = two, 2
        elif ch == "|":
            op, step = "|", 1
        elif ch in ";\n":
            op, step = ";", 1
        if op is None:
            buf.append(ch)
            i += 1
            continue
        segments.append(("".join(buf).strip(), op))
        buf = []
        i += step
    segments.append(("".join(buf).strip(), None))
    return [(s, op) for s, op in segments if s or op]


def _normalize_segment(segment: str) -> str:
    """Interpreter path -> ``python``; redirections dropped (``2>&1``, ``> log``)."""
    tokens = segment.replace("\\", "/").split()
    kept: list[str] = []
    skip_next = False
    for tok in tokens:
        if skip_next:
            skip_next = False
            continue
        if _REDIRECT.match(tok):
            skip_next = tok.endswith(">")  # "> file": the target is the next token
            continue
        kept.append("python" if _PYTHON_EXE.match(tok.strip("\"'")) else tok)
    return " ".join(kept)


def is_watched(segment: str, root: Path | None = None) -> bool:
    text = " " + segment
    if any(p.search(text) for p in _WATCHED):
        return True
    if root is not None:
        scripts = (root.as_posix().rstrip("/") + "/scripts/").lower()
        text = segment.replace("\\", "/").lower()
        return bool(re.search(re.escape(scripts) + r"[\w.-]+\.py\b", text))
    return False


def watched_run(command: str, root: Path | None = None) -> tuple[str, bool] | None:
    """(watched command key, exit code trusted), or None when nothing is watched.

    The exit code is NOT trusted when it may belong to some other command: a watched
    segment piped into another (without ``pipefail``), or a ``;`` / ``||`` / ``|``
    after the last watched segment. Such a run is judged from its output summary.
    """
    segs = split_segments(command)
    idx = [i for i, (seg, _) in enumerate(segs) if is_watched(seg, root)]
    if not idx:
        return None
    pipefail = "pipefail" in command
    trusted = pipefail or all(segs[i][1] != "|" for i in idx)
    last = idx[-1]
    for j in range(last, len(segs)):
        op = segs[j][1]
        if not (op is None or op == "&&" or (op == "|" and pipefail)):
            trusted = False
    first = last
    while first > 0 and segs[first - 1][1] == "&&":
        first -= 1
    chain = [_normalize_segment(segs[i][0]) for i in idx if first <= i <= last]
    return " && ".join(chain), trusted


def watched_key(command: str, root: Path | None = None) -> str | None:
    """The watched command key, whether or not its exit code can be trusted."""
    run = watched_run(command, root)
    return run[0] if run else None


# --- Error signature -----------------------------------------------------------


def error_signature(output: str) -> str:
    """sha256 (16 hex) of the last SIGNATURE_TAIL_LINES normalized output lines.

    Used for failures without a pytest / ruff summary (see ``read_summary``).
    """
    lines = [
        _normalize_line(line)
        for line in _lines(output)
        if line and not _CLAUDE_INSERTED.match(line)
    ]
    tail = "\n".join(lines[-SIGNATURE_TAIL_LINES:])
    return hashlib.sha256(tail.encode("utf-8")).hexdigest()[:16]


def parse_failure(error: str) -> tuple[int, str] | None:
    """(exit code, output) from a PostToolUseFailure ``error``; None without an exit line."""
    first, _, rest = error.partition("\n")
    m = _EXIT_LINE.match(first.strip())
    if not m:
        return None
    return int(m.group(1)), rest


def _normalize_line(line: str) -> str:
    for pattern, repl in _NORMALIZERS:
        line = pattern.sub(repl, line)
    return " ".join(line.split())


def _lines(output: str) -> list[str]:
    return [ln.strip() for ln in output.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _pytest_summary(lines: list[str]) -> tuple[str, str] | None:
    """("fail" | "pass", signature material) from pytest's final summary line."""
    summary = next((ln for ln in reversed(lines) if _PYTEST_SUMMARY.search(ln)), None)
    if summary is None:
        return None
    counts = {"failed": 0, "passed": 0, "error": 0}
    for n, word in _PYTEST_COUNT.findall(summary):
        counts["error" if word.startswith("error") else word] += int(n)
    material = _normalize_line(summary.strip("= "))
    if counts["failed"] + counts["error"] > 0:
        ids = sorted({
            f"{m.group(1)} {m.group(2).replace(chr(92), '/')}"
            for m in map(_PYTEST_ID.match, lines) if m
        })
        return "fail", "\n".join([material, *ids])
    return ("pass", material) if counts["passed"] > 0 else None


def _ruff_summary(lines: list[str]) -> tuple[str, str] | None:
    """("fail" | "pass", signature material) from ruff's "Found N errors" / pass line."""
    found = next((m for m in map(_RUFF_FOUND.search, reversed(lines)) if m), None)
    if found is not None and int(found.group(1)) > 0:
        codes = sorted({m.group(1) for m in map(_RUFF_CODE.search, lines) if m})
        return "fail", "\n".join([_normalize_line(found.group(0)), *codes])
    if any(ln == _RUFF_PASS for ln in lines):
        return "pass", _RUFF_PASS
    return None


def read_summary(key: str, output: str) -> tuple[str | None, str]:
    """Verdict from the run summaries of the tools in ``key``: ("fail", signature),
    ("pass", ""), or (None, "") when the output does not settle it.

    The failure signature hashes the normalized summary plus the failing test IDs /
    rule codes only, so the same failure hashes alike piped or not.
    """
    readers = []
    if re.search(r"(?:^|[\s/])pytest(?:\.exe)?(?:\s|$)", " " + key):
        readers.append(_pytest_summary)
    if re.search(r"(?:^|[\s/])ruff(?:\.exe)?(?:\s|$)", " " + key):
        readers.append(_ruff_summary)
    if not readers:
        return None, ""
    lines = _lines(output)
    results = [reader(lines) for reader in readers]
    fails = [r[1] for r in results if r and r[0] == "fail"]
    if fails:
        digest = hashlib.sha256("\n--\n".join(fails).encode("utf-8")).hexdigest()[:16]
        return "fail", digest
    if all(r and r[0] == "pass" for r in results):
        return "pass", ""
    return None, ""


# --- State -----------------------------------------------------------------------


def _fresh_state(session_id: str) -> dict:
    return {"session_id": session_id, "commands": {}, "failing": [], "episode": _fresh_episode()}


def _fresh_episode() -> dict:
    return {"edits": {}, "hashes": {}, "fired": []}


def _load(state_dir: Path, session_id: str) -> dict:
    try:
        state = json.loads((state_dir / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _fresh_state(session_id)
    if not isinstance(state, dict) or state.get("session_id") != session_id:
        return _fresh_state(session_id)
    return state


def _save(state_dir: Path, state: dict) -> None:
    target = state_dir / STATE_FILE
    tmp = state_dir / (STATE_FILE + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, target)
            return
        except PermissionError:  # Windows: target briefly open elsewhere
            time.sleep(0.05)
    tmp.unlink(missing_ok=True)


class _Lock:
    def __init__(self, state_dir: Path) -> None:
        self.path = state_dir / LOCK_FILE
        self.held = False

    def __enter__(self) -> _Lock:
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > LOCK_STALE_SECONDS:
                        self.path.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    return self
                time.sleep(0.02)

    def __exit__(self, *exc: object) -> None:
        if self.held:
            self.path.unlink(missing_ok=True)


# --- Signals ---------------------------------------------------------------------


def _one_line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= DETAIL_MAX_CHARS else text[: DETAIL_MAX_CHARS - 3] + "..."


def _display_path(path: str, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return Path(path).as_posix()


def _latest_signature(state: dict) -> str:
    sigs = [state["commands"].get(k, {}).get("signature", "") for k in state["failing"]]
    return sigs[-1] if sigs else ""


def _on_command(state: dict, key: str, failed: bool, signature: str) -> list[tuple[str, str, dict]]:
    fires: list[tuple[str, str, dict]] = []
    rec = state["commands"].get(key, {})
    if not failed:
        state["commands"][key] = {"last": "pass", "signature": "", "streak": 0}
        if key in state["failing"]:
            state["failing"].remove(key)
            if not state["failing"]:
                state["episode"] = _fresh_episode()
        return fires
    if not state["failing"]:
        state["episode"] = _fresh_episode()
    if rec.get("last") == "fail" and rec.get("signature") == signature:
        streak = int(rec.get("streak", 1)) + 1
    else:
        streak = 1
    state["commands"][key] = {"last": "fail", "signature": signature, "streak": streak}
    if key not in state["failing"]:
        state["failing"].append(key)
    episode = state["episode"]
    if streak >= SIGNAL_A_SAME_SIGNATURE_FAILS and "a" not in episode["fired"]:
        episode["fired"].append("a")
        detail = (
            f"`{_one_line(key)}` failed {streak} times in a row "
            f"with the same error signature {signature}"
        )
        fires.append(("a", detail, {"command": key, "signature": signature}))
    return fires


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _previous_text(tool_name: str, tool_input: dict, after: str) -> str | None:
    """Pre-edit content of an Edit, when the edit can be undone unambiguously."""
    if tool_name != "Edit" or tool_input.get("replace_all"):
        return None
    old, new = tool_input.get("old_string"), tool_input.get("new_string")
    if not isinstance(old, str) or not isinstance(new, str) or not new:
        return None
    text = after.replace("\r\n", "\n")
    new = new.replace("\r\n", "\n")
    if text.count(new) != 1:
        return None
    return text.replace(new, old.replace("\r\n", "\n"), 1)


def _on_edit(
    state: dict, tool_name: str, tool_input: dict, root: Path
) -> list[tuple[str, str, dict]]:
    fires: list[tuple[str, str, dict]] = []
    if not state["failing"]:
        return fires  # edits count only while a watched command is failing
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not path:
        return fires
    try:
        after = Path(path).read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return fires
    file_key = os.path.normcase(os.path.abspath(path))
    shown = _display_path(path, root)
    episode = state["episode"]
    signature = _latest_signature(state)
    failing = state["failing"][-1]

    count = int(episode["edits"].get(file_key, 0)) + 1
    episode["edits"][file_key] = count
    if count >= SIGNAL_B_EDITS_WHILE_FAILING and "b" not in episode["fired"]:
        episode["fired"].append("b")
        detail = f"{shown} edited {count} times while `{_one_line(failing)}` is still failing"
        fires.append(("b", detail, {"file": shown, "signature": signature}))

    seen: list[str] = episode["hashes"].setdefault(file_key, [])
    after_hash = _text_hash(after)
    before = _previous_text(tool_name, tool_input, after)
    before_hash = _text_hash(before) if before is not None else (seen[-1] if seen else None)
    if before is not None and before_hash != after_hash and before_hash not in seen:
        seen.append(before_hash)
    restored = after_hash in seen and after_hash != before_hash
    if restored and "c" not in episode["fired"]:
        episode["fired"].append("c")
        detail = f"{shown} was restored to content it had earlier in this episode"
        fires.append(("c", detail, {"file": shown, "signature": signature}))
    if not seen or seen[-1] != after_hash:
        seen.append(after_hash)
    return fires


# --- Entry points -------------------------------------------------------------------


def _log_fire(state_dir: Path, signal: str, fields: dict) -> None:
    entry = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "signal": signal}
    entry.update(fields)
    with (state_dir / FIRES_FILE).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def process(event: dict, state_dir: Path, root: Path) -> dict | None:
    """Handle one hook event; return the hook's JSON output, or None for no output."""
    hook = event.get("hook_event_name")
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") or {}
    if hook not in ("PostToolUse", "PostToolUseFailure") or not isinstance(tool_input, dict):
        return None

    if tool in SHELL_TOOLS:
        command = tool_input.get("command")
        if not isinstance(command, str) or tool_input.get("run_in_background"):
            return None
        run = watched_run(command, root)
        if run is None:
            return None
        key, trusted = run
        if hook == "PostToolUse":
            response = event.get("tool_response")
            response = response if isinstance(response, dict) else {}
            exit_ok = True
            output = f"{response.get('stdout') or ''}\n{response.get('stderr') or ''}"
        else:
            if event.get("is_interrupt"):
                return None
            parsed = parse_failure(str(event.get("error") or ""))
            if parsed is None or parsed[0] == 0:
                return None  # the shell never started, or no exit status to judge
            exit_ok, output = False, parsed[1]
        verdict, summary_sig = read_summary(key, output)
        if trusted:
            failed = not exit_ok
            if not failed:
                signature = ""
            elif verdict == "fail":
                signature = summary_sig
            else:
                signature = error_signature(output)
        elif verdict is None:
            return None  # exit code not the watched command's, and no summary to read
        else:
            failed, signature = verdict == "fail", summary_sig
    elif tool in EDIT_TOOLS:
        if hook != "PostToolUse":
            return None  # a failed edit changed nothing
        key = None
    else:
        return None

    state_dir.mkdir(parents=True, exist_ok=True)
    with _Lock(state_dir) as lock:
        if not lock.held:
            return None
        state = _load(state_dir, str(event.get("session_id") or ""))
        if key is not None:
            fires = _on_command(state, key, failed, signature)
        else:
            fires = _on_edit(state, str(tool), tool_input, root)
        _save(state_dir, state)
        for signal, _, fields in fires:
            _log_fire(state_dir, signal, fields)

    if not fires:
        return None
    message = "\n".join(MESSAGE.format(signal=s, detail=d) for s, d, _ in fires)
    return {
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": hook, "additionalContext": message},
    }


def _root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        root = _root()
        state_dir = Path(os.environ.get("SPIRAL_DETECTOR_STATE_DIR") or root / ".local")
        out = process(event, state_dir, root) if isinstance(event, dict) else None
        if out is not None:
            sys.stdout.write(json.dumps(out))
            sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001 - a hook must never break the session
        sys.stderr.write(f"spiral_detector: {type(exc).__name__}\n")  # debug log only
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
