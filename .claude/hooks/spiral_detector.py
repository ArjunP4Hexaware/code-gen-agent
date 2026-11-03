#!/usr/bin/env python3
"""Spiral detector: a Claude Code PostToolUse / PostToolUseFailure hook (user level).

Watches run/test/build commands and file edits. When one of three pre-registered
signals fires, it REPORTS the signal to Claude (and the user). What to do about it
lives in ~/.claude/CLAUDE.md, not in a tool result.

When the exit code cannot be trusted (a watched command piped into another, or
followed by ``;`` / ``||``), the tools' own summary lines decide pass or fail
(pytest, ruff, cargo test); a run with no summary is ignored.

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
- ``CLAUDE_PROJECT_DIR`` is the project root where the session started.

Stdlib only. Any internal error exits 0 silently: the hook never blocks or breaks
a session. Nothing is written inside any repo. Under the home directory
(``SPIRAL_BREAKER_HOME``, default ~/.claude/spiral-breaker):
- state/<repo>.json   per-repo state. <repo> is the basename of the git top level of
                      the repo the work happened in: for a shell command, the hook's
                      cwd moved by the command's leading `cd <dir> &&` / `;` (the cwd
                      field reflects a cd that stayed inside the project, not one that
                      left it); for an edit, the edited file's directory. Fallback:
                      CLAUDE_PROJECT_DIR.
- fires.jsonl         one line per firing: timestamp, repo, signal, command or
                      file, signature hash, signature basis; never command output.
- traces/<repo>.jsonl one line per processed event (a watched run, an edit): ts,
                      session_id, repo, kind, command key or file, is_doc, outcome,
                      signature, signature_basis, and for edits content hashes only.
                      Never output or file contents. Pruned past TRACE_RETENTION_DAYS.
                      hook/replay_traces.py replays them through ``step``, the one
                      function that decides the signals, live or replayed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- Configuration ------------------------------------------------------------
# Thresholds are PRE-REGISTERED (2026-10-05). Do not tune them without a retro.

# A shell command is watched when any segment of it matches one of these.
# Everything else (grep, rg, git, ls, npm install, ...) is ignored entirely.
WATCHED_PATTERNS: list[str] = [
    r"(?:^|[\s\\/])pytest(?:\.exe)?(?:\s|$)",  # pytest, .venv/bin/pytest
    r"(?:^|\s)-m\s+pytest(?:\s|$)",  # python -m pytest
    r"(?:^|[\s\\/])ruff(?:\.exe)?(?:\s|$)",  # ruff check / ruff format --check
    r"(?:^|\s)-m\s+ruff(?:\s|$)",  # python -m ruff
    r"(?:^|[\s\"'])(?:\./|\.\\)?scripts[\\/][\w.-]+\.py\b",  # a repo's scripts/*.py
    r"\bcodegen(?:\.cli)?\s+generate(?:-all)?\b.*--dry-run",  # code-gen-agent's mock smoke run
    r"(?:^|[\s\\/])cargo(?:\.exe)?\s+(?:\+\S+\s+)?(?:test|build|clippy)(?:\s|$)",
    r"(?:^|[\s\\/])npm(?:\.cmd)?\s+(?:test|t|run(?:-script)?\s+(?:test|build)[\w:.-]*)(?:\s|$)",
    r"(?:^|[\s\\/])pnpm(?:\.cmd)?\s+(?:run\s+)?(?:test|build)[\w:.-]*(?:\s|$)",
    r"(?:^|[\s\\/])tsc(?:\.cmd|\.exe)?(?:\s|$)",  # tsc, npx tsc, pnpm exec tsc
]
SIGNAL_A_SAME_SIGNATURE_FAILS = 2  # a: same command, same signature, N fails in a row
SIGNAL_B_EDITS_WHILE_FAILING = 4  # b: same file edited N+ times while failing
# d (cascade, PRE-REGISTERED 2026-10-31): N fix attempts in a row on one failing command,
# each leaving a test failing in a file that had no failing test before and that the
# attempt didn't touch. pytest IDs only (they carry the file). See retros/2026-10-31-hook.md.
SIGNAL_D_CASCADE_STEPS = 2
SIGNAL_D_MODE = "live"  # "live" | "shadow" (logged in fires.jsonl, not shown) | "off"
# Live by default (user decision 2026-11-01), so a machine that fails to apply its setting
# fails loud (an alarm it meant to quiet), never silent (an alarm that is off).
# Per machine, without forking the code: SPIRAL_BREAKER_D_MODE=live|shadow|off in the
# environment (e.g. the "env" block of ~/.claude/settings.json) overrides the default.
# Anything else falls back to the default. Each run records the mode it actually used
# in the repo's state file ("d_mode"): check that, not a shell's echo.
D_MODE_ENV = "SPIRAL_BREAKER_D_MODE"
_D_MODES = ("live", "shadow", "off")
RECENT_EDITS_KEPT = 500  # (edit number, file fingerprint) pairs kept for signal d
# Events already processed, by tool_use_id: a user-level and a project-level copy of this
# hook both run on every event (Claude Code merges only identical handlers) and share one
# home, so each event is processed once per repo, by whichever copy gets the lock first.
SEEN_EVENTS_KEPT = 200
SIGNATURE_TAIL_LINES = 20  # the error signature hashes the last N output lines

SHELL_TOOLS = {"Bash", "PowerShell"}
EDIT_TOOLS = {"Edit", "Write"}
HOME_ENV = "SPIRAL_BREAKER_HOME"
STATE_DIR = "state"
FIRES_FILE = "fires.jsonl"
TRACE_DIR = "traces"
TRACE_RETENTION_DAYS = 60  # trace lines older than this are pruned on write
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
# An edit counts as documentation (trace field is_doc) by suffix or by folder.
DOC_SUFFIXES = {".md", ".rst", ".txt", ".adoc"}
DOC_DIRS = {"docs", "doc"}
LOCK_WAIT_SECONDS = 3.0
LOCK_STALE_SECONDS = 30.0
GIT_TIMEOUT_SECONDS = 3.0
DETAIL_MAX_CHARS = 120

# How a failure's signature was computed (recorded in fires.jsonl, to measure the
# collision risk of summary-only signatures; no threshold depends on it).
BASIS_IDS = "summary+ids"  # a run summary plus failing test IDs / rule codes
BASIS_SUMMARY = "summary-only"  # a run summary alone (the IDs cut off, e.g. by a pipe)
BASIS_TAIL = "tail-hash"  # the last SIGNATURE_TAIL_LINES output lines

# A report, never an instruction: what to do about a signal lives in the user's own
# ~/.claude/CLAUDE.md.
MESSAGE = (
    "spiral-detector hook (user-configured in ~/.claude/settings.json): "
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
_UNSAFE_NAME = re.compile(r"[^\w.-]")
# A leading directory change: cd / chdir / pushd / Set-Location / sl <dir>
_CD = re.compile(
    r"""^(?:cd|chdir|pushd|set-location|sl)(?:\s+(?:/d|-path|-literalpath))?"""
    r"""\s+(?P<dir>"[^"]*"|'[^']*'|\S+)\s*$""",
    re.IGNORECASE,
)
_GIT_BASH_DRIVE = re.compile(r"^/([a-zA-Z])(/.*)?$")
_TOKEN = re.compile(r"(?:\"[^\"]*\"|'[^']*'|[^\s\"'])+")

# Run summaries, read when the exit code cannot be trusted (and for every
# summarized failure's signature, so piped and unpiped forms hash alike).
_PYTEST_SUMMARY = re.compile(r"\b\d+ (?:failed|passed|errors?)\b.*\bin \d+(?:\.\d+)?s\b")
_PYTEST_COUNT = re.compile(r"\b(\d+) (failed|passed|errors?)\b")
_PYTEST_ID = re.compile(r"^(FAILED|ERROR)\s+(\S+\.py\b.*?)(?:\s+-\s.*)?$")  # node ids only
_RUFF_FOUND = re.compile(r"\bFound (\d+) errors?\b")
_RUFF_PASS = "All checks passed!"
_RUFF_CODE = re.compile(r"(?:^|:\d+:\d+:\s)([A-Z]{1,4}\d{2,4})\b")
_CARGO_RESULT = re.compile(r"^test result: (ok|FAILED)\. (\d+) passed; (\d+) failed\b")
_CARGO_TEST_FAILED = re.compile(r"^test (\S+) \.\.\. FAILED$")
_CARGO_STDOUT_HEADER = re.compile(r"^---- (\S+) stdout ----$")
_CARGO_LIST_NAME = re.compile(r"^[\w:<>]+$")

_KEY_PYTEST = re.compile(r"(?:^|[\s/])pytest(?:\.exe)?(?:\s|$)")
_KEY_RUFF = re.compile(r"(?:^|[\s/])ruff(?:\.exe)?(?:\s|$)")
_KEY_CARGO_TEST = re.compile(r"(?:^|[\s/])cargo(?:\.exe)?\s+(?:\+\S+\s+)?test(?:\s|$)")


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
    """Interpreter path -> ``python``; redirections dropped (``2>&1``, ``> log``).

    Tokens respect quotes, so a quoted interpreter path with spaces is one token."""
    tokens = _TOKEN.findall(segment.replace("\\", "/"))
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


_HEREDOC = re.compile(r"<<-?[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|\\?([A-Za-z_]\w*))")
_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_PREFIX_WORDS = {"&", "time"}  # PowerShell's call operator, the shell keyword
_SHELLS = {"bash", "sh", "zsh", "dash", "powershell", "pwsh", "cmd"}


def _heredoc_delimiters(line: str) -> list[str]:
    """Delimiters of the bash heredocs a line opens (``<<EOF``, ``<<-'EOF'``), skipping
    ``<<`` inside quotes, ``<<<`` here-strings and shifts such as ``$((1<<2))``."""
    found: list[str] = []
    quote = ""
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif line.startswith("<<", i) and not line.startswith("<<<", i) and (
            i == 0 or line[i - 1] != "<"
        ):
            m = _HEREDOC.match(line, i)
            if m:
                found.append(next(g for g in m.groups() if g))
                i = m.end()
                continue
        i += 1
    return found


def strip_heredocs(command: str) -> str:
    """The command without heredoc and PowerShell here-string bodies.

    A body is data fed to a command, not shell syntax: parsing it as commands made any
    script line that mentioned a watched command look like a run of it, and an
    apostrophe in a body swallowed the lines after it into one segment."""
    out: list[str] = []
    lines = command.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        stripped = line.rstrip()
        if stripped.endswith(("@'", '@"')):  # PowerShell here-string header
            close = stripped[-1] + "@"
            head = stripped[:-2] + "''"
            while i < len(lines) and not lines[i].lstrip().startswith(close):
                i += 1
            if i < len(lines):  # the rest of the closing line continues the statement
                head += " " + lines[i].lstrip()[len(close):].strip()
                i += 1
            out.append(head.rstrip())
            continue
        out.append(line)
        for delim in _heredoc_delimiters(line):
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1  # the delimiter line itself
    return "\n".join(out)


def _visible_text(segment: str) -> str:
    """The segment as the shell sees its command words: a quoted argument containing
    whitespace (script text, a message, a ``-k`` expression) is blanked, so a command
    named inside it doesn't count. The executable keeps its quotes (a path with
    spaces), and a shell wrapper (``bash -c "..."``) keeps everything, since it really
    runs its quoted command."""
    tokens = _TOKEN.findall(segment)
    exe = next(
        (j for j, t in enumerate(tokens) if not _ASSIGNMENT.match(t) and t not in _PREFIX_WORDS),
        None,
    )
    if exe is not None:
        name = re.split(r"[\\/]", tokens[exe].strip("\"'"))[-1].lower()
        if name.removesuffix(".exe") in _SHELLS:
            return segment
    kept = []
    for j, tok in enumerate(tokens):
        if j != exe and re.search(r"\"[^\"]*\s[^\"]*\"|'[^']*\s[^']*'", tok):
            tok = '""'
        kept.append(tok)
    return " ".join(kept)


def is_watched(segment: str, root: Path | None = None) -> bool:
    text = " " + _visible_text(segment)
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
    segs = split_segments(strip_heredocs(command))
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

    Used for failures without a run summary (see ``read_summary``).
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


# A reader returns None (output does not settle it), ("pass", material, False) or
# ("fail", material, has_ids), where has_ids says whether the material carries the
# failing test IDs / rule codes or the summary line alone.
Summary = tuple[str, str, bool]


def _pytest_summary(lines: list[str]) -> Summary | None:
    """From pytest's final summary line plus its FAILED / ERROR node ids."""
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
        return "fail", "\n".join([material, *ids]), bool(ids)
    return ("pass", material, False) if counts["passed"] > 0 else None


def _ruff_summary(lines: list[str]) -> Summary | None:
    """From ruff's "Found N errors" / "All checks passed!" line plus the rule codes."""
    found = next((m for m in map(_RUFF_FOUND.search, reversed(lines)) if m), None)
    if found is not None and int(found.group(1)) > 0:
        codes = sorted({m.group(1) for m in map(_RUFF_CODE.search, lines) if m})
        return "fail", "\n".join([_normalize_line(found.group(0)), *codes]), bool(codes)
    if any(ln == _RUFF_PASS for ln in lines):
        return "pass", _RUFF_PASS, False
    return None


def _cargo_failed_ids(lines: list[str]) -> list[str]:
    """Failing test names: ``test x ... FAILED``, ``---- x stdout ----`` and the
    bare names in the ``failures:`` list cargo prints just before its result line."""
    ids: set[str] = set()
    in_list = False
    for line in lines:
        m = _CARGO_TEST_FAILED.match(line) or _CARGO_STDOUT_HEADER.match(line)
        if m:
            ids.add(m.group(1))
            in_list = False
        elif line == "failures:":
            in_list = True
        elif line.startswith("test result:"):
            in_list = False
        elif in_list and _CARGO_LIST_NAME.match(line):
            ids.add(line)
    return sorted(ids)


def _cargo_summary(lines: list[str]) -> Summary | None:
    """From every ``test result: ok|FAILED. N passed; M failed`` line (one per test
    binary) plus the failing test names."""
    results = [m for m in map(_CARGO_RESULT.match, lines) if m]
    if not results:
        return None
    material = "\n".join(
        f"test result: {m.group(1)}. {m.group(2)} passed; {m.group(3)} failed"
        for m in results
    )
    if any(m.group(1) == "FAILED" or int(m.group(3)) > 0 for m in results):
        ids = _cargo_failed_ids(lines)
        return "fail", "\n".join([material, *ids]), bool(ids)
    return "pass", material, False


def _readers(key: str) -> list:
    readers = []
    padded = " " + key
    if _KEY_PYTEST.search(padded):
        readers.append(_pytest_summary)
    if _KEY_RUFF.search(padded):
        readers.append(_ruff_summary)
    if _KEY_CARGO_TEST.search(padded):
        readers.append(_cargo_summary)
    return readers


def _h8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


_PYTEST_FILE = re.compile(r"^(.+?\.py)(?:::|$)")


def file_fingerprint(path: str) -> str:
    """A repo-relative file path, hashed (forward slashes)."""
    return _h8(path.replace("\\", "/"))


def id_fingerprint(test_id: str) -> str:
    """A failing test's identity, hashed: traces record WHICH tests fail, never names.
    A pytest node (or a collection error, which is the bare file) is
    ``<file fingerprint>:<id fingerprint>``, so signal d can tell which file a failure is
    in; a ruff rule code or a cargo test path is just ``<id fingerprint>``."""
    m = _PYTEST_FILE.match(test_id)
    return f"{file_fingerprint(m.group(1))}:{_h8(test_id)}" if m else _h8(test_id)


def failing_ids(key: str, output: str) -> list[str]:
    """Fingerprints of the failing tests / rule codes in ``output``: sorted, deduplicated.
    Empty unless every failing summary carried its IDs (the BASIS_IDS case), so a
    partial list never reads as "these tests stopped failing". A pytest node keeps one
    fingerprint whether it shows as ERROR or FAILED."""
    lines = _lines(output)
    fails = [r for r in (reader(lines) for reader in _readers(key)) if r and r[0] == "fail"]
    if not fails or not all(r[2] for r in fails):
        return []
    ids: set[str] = set()
    for _, material, _ in fails:
        for line in material.split("\n")[1:]:
            if line.startswith("test result:"):  # cargo's per-binary result lines
                continue
            ids.add(re.sub(r"^(?:FAILED|ERROR) ", "", line))
    return sorted({id_fingerprint(i) for i in ids})


def read_summary(key: str, output: str) -> tuple[str | None, str, str]:
    """Verdict from the run summaries of the tools in ``key``:
    ("fail", signature, basis), ("pass", "", ""), or (None, "", "") when the output
    does not settle it.

    The failure signature hashes the normalized summary plus the failing test IDs /
    rule codes only, so the same failure hashes alike piped or not. The basis is
    BASIS_IDS when every failing summary carried its IDs, else BASIS_SUMMARY.
    """
    readers = _readers(key)
    if not readers:
        return None, "", ""
    lines = _lines(output)
    results = [reader(lines) for reader in readers]
    fails = [r for r in results if r and r[0] == "fail"]
    if fails:
        material = "\n--\n".join(r[1] for r in fails)
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
        basis = BASIS_IDS if all(r[2] for r in fails) else BASIS_SUMMARY
        return "fail", digest, basis
    if all(r and r[0] == "pass" for r in results):
        return "pass", "", ""
    return None, "", ""


# --- Repo and state ----------------------------------------------------------------


def _native_path(text: str) -> Path:
    """A ``cd`` argument as a path: quotes stripped, ``~`` expanded, and on Windows the
    Git Bash drive form ``/c/Users/...`` read as ``C:/Users/...``."""
    text = text.strip().strip("\"'")
    if text == "~" or text.startswith(("~/", "~\\")):
        text = str(Path.home()) + text[1:]
    if os.name == "nt":
        m = _GIT_BASH_DRIVE.match(text)
        if m:
            text = f"{m.group(1).upper()}:{m.group(2) or '/'}"
    return Path(text)


def _already_applied(current: Path, target: Path) -> bool:
    """True when a relative ``cd`` target is already the tail of ``current``: the hook's
    cwd reflects a ``cd`` that stayed inside the project, so applying it again would
    double it."""
    parts = [os.path.normcase(p) for p in target.parts if p != "."]
    if not parts or ".." in parts:
        return False
    tail = [os.path.normcase(p) for p in current.parts[-len(parts):]]
    return tail == parts


def command_dir(command: str, base: Path) -> Path:
    """The directory a shell command's watched part runs in: ``base`` (the hook input's
    cwd) moved by the command's leading ``cd <dir> &&`` / ``;`` segments.

    The cwd field reflects a ``cd`` that stayed inside the project (Claude Code keeps
    it) but not one that left the project (the shell is reset after the command), so
    a leading ``cd`` into another repo is read from the command itself."""
    current = base
    for segment, op in split_segments(command):
        m = _CD.match(segment)
        if m is None or op not in ("&&", ";"):
            break
        target = _native_path(m.group("dir"))
        if not target.is_absolute():
            if _already_applied(current, target):
                continue
            target = current / target
        if target.is_dir():
            current = target.resolve()
    return current


def _walk_up_top(path: Path) -> Path:
    path = path.resolve()
    return next((p for p in (path, *path.parents) if (p / ".git").exists()), path)


def repo_top(path: Path) -> Path:
    """The git top level containing ``path`` (``git rev-parse --show-toplevel``); when git
    can't say, the nearest directory holding a ``.git`` entry, else ``path`` itself."""
    try:
        done = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS, check=False,
        )
        top = done.stdout.strip()
        if done.returncode == 0 and top:
            return Path(top)
    except (OSError, subprocess.SubprocessError):
        pass
    return _walk_up_top(path)


def repo_name(path: Path) -> str:
    """Basename of the repo containing ``path`` (see ``repo_top``), safe as a file name."""
    name = _UNSAFE_NAME.sub("_", repo_top(path).name)
    return name or "unknown"


def default_home() -> Path:
    env = os.environ.get(HOME_ENV)
    return Path(env) if env else Path.home() / ".claude" / "spiral-breaker"


def _fresh_state(session_id: str) -> dict:
    return {"session_id": session_id, "commands": {}, "failing": [], "episode": _fresh_episode()}


def _fresh_episode() -> dict:
    return {"edits": {}, "hashes": {}, "fired": []}


def _load(state_file: Path, session_id: str) -> dict:
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _fresh_state(session_id)
    if not isinstance(state, dict) or state.get("session_id") != session_id:
        return _fresh_state(session_id)
    return state


def _save(state_file: Path, state: dict) -> None:
    tmp = state_file.with_name(state_file.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, state_file)
            return
        except PermissionError:  # Windows: target briefly open elsewhere
            time.sleep(0.05)
    tmp.unlink(missing_ok=True)


class _Lock:
    def __init__(self, path: Path) -> None:
        self.path = path
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


def _latest_failure(state: dict) -> tuple[str, str]:
    """(signature, basis) of the most recent failing command."""
    if not state["failing"]:
        return "", ""
    rec = state["commands"].get(state["failing"][-1], {})
    return rec.get("signature", ""), rec.get("basis", "")


def d_mode() -> str:
    """Signal d's mode on this machine: the environment's, if valid, else the default."""
    env = os.environ.get(D_MODE_ENV, "").strip().lower()
    return env if env in _D_MODES else SIGNAL_D_MODE


def _cascade_streak(state: dict, rec: dict, failed: bool, fail_ids: list[str]) -> int:
    """Signal d's count of consecutive cascade steps for one command, updated by a run.

    A cascade step: since this command's last (failing) run, at least one non-doc file
    was edited, and the run still fails with a test in a file that had no failing test
    last time and that none of those edits touched: the failure moved somewhere new.
    A pass, or an attempt that moved nothing, resets the count; a run with no edits
    since the last one, or one without test IDs, leaves it as is."""
    streak = int(rec.get("cascade", 0))
    if not failed:
        return 0
    prev_ids = rec.get("fail_ids") or []
    prev_seq = rec.get("edit_seq")
    if rec.get("last") != "fail" or not prev_ids or not fail_ids or prev_seq is None:
        return streak
    if state.get("edit_seq", 0) == prev_seq:
        return streak  # a plain re-run: no attempt was made
    edited = {fh for seq, fh in state.get("recent_edits", []) if seq > prev_seq}
    was_failing = {fid.split(":")[0] for fid in prev_ids if ":" in fid}
    moved = any(
        ":" in fid and fid.split(":")[0] not in was_failing | edited for fid in fail_ids
    )
    return streak + 1 if moved else 0


def _on_command(
    state: dict, key: str, failed: bool, signature: str, basis: str,
    fail_ids: list[str] | None = None,
) -> list[tuple[str, str, dict]]:
    fires: list[tuple[str, str, dict]] = []
    rec = state["commands"].get(key, {})
    fail_ids = list(fail_ids or [])
    cascade = _cascade_streak(state, rec, failed, fail_ids)
    edit_seq = state.get("edit_seq", 0)
    if not failed:
        state["commands"][key] = {"last": "pass", "signature": "", "basis": "", "streak": 0,
                                  "fail_ids": [], "edit_seq": edit_seq, "cascade": 0}
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
    state["commands"][key] = {
        "last": "fail", "signature": signature, "basis": basis, "streak": streak,
        "fail_ids": fail_ids, "edit_seq": edit_seq, "cascade": cascade,
    }
    if key not in state["failing"]:
        state["failing"].append(key)
    episode = state["episode"]
    if streak >= SIGNAL_A_SAME_SIGNATURE_FAILS and "a" not in episode["fired"]:
        episode["fired"].append("a")
        detail = (
            f"`{_one_line(key)}` failed {streak} times in a row "
            f"with the same error signature {signature}"
        )
        fires.append(("a", detail, {
            "command": key, "signature": signature, "signature_basis": basis,
        }))
    mode = d_mode()
    if (
        mode in ("live", "shadow")
        and cascade >= SIGNAL_D_CASCADE_STEPS
        and "d" not in episode["fired"]
    ):
        episode["fired"].append("d")
        detail = (
            f"`{_one_line(key)}`: {cascade} fix attempts in a row each left a test failing "
            "in a file that wasn't failing or being edited before (the failure is moving)"
        )
        fields = {"command": key, "signature": signature, "signature_basis": basis}
        if mode == "shadow":
            fields["shadow"] = True
        fires.append(("d", detail, fields))
    return fires


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


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
    state: dict, shown: str, after_hash: str, before_hash: str | None
) -> list[tuple[str, str, dict]]:
    """One applied edit of ``shown`` (repo-relative path), from content hashes only.
    ``before_hash`` is the pre-edit content hash when the edit can be undone, else None."""
    fires: list[tuple[str, str, dict]] = []
    if not state["failing"]:
        return fires  # edits count only while a watched command is failing
    episode = state["episode"]
    signature, basis = _latest_failure(state)
    failing = state["failing"][-1]
    fields = {"file": shown, "signature": signature, "signature_basis": basis}

    count = int(episode["edits"].get(shown, 0)) + 1
    episode["edits"][shown] = count
    if count >= SIGNAL_B_EDITS_WHILE_FAILING and "b" not in episode["fired"]:
        episode["fired"].append("b")
        detail = f"{shown} edited {count} times while `{_one_line(failing)}` is still failing"
        fires.append(("b", detail, dict(fields)))

    seen: list[str] = episode["hashes"].setdefault(shown, [])
    prior = before_hash if before_hash is not None else (seen[-1] if seen else None)
    if before_hash is not None and prior != after_hash and prior not in seen:
        seen.append(prior)
    restored = after_hash in seen and after_hash != prior
    if restored and "c" not in episode["fired"]:
        episode["fired"].append("c")
        detail = f"{shown} was restored to content it had earlier in this episode"
        fires.append(("c", detail, dict(fields)))
    if not seen or seen[-1] != after_hash:
        seen.append(after_hash)
    return fires


def step(state: dict, rec: dict) -> list[tuple[str, str, dict]]:
    """Apply one trace record to a repo's state; return the firings. The ONE place the
    signals are decided: the live hook and replay_traces.py both call it."""
    if rec.get("outcome") == "ignored":
        return []
    if rec.get("kind") == "run":
        failed = rec["outcome"] == "fail"
        return _on_command(
            state, rec["key"], failed, rec.get("signature", ""), rec.get("signature_basis", ""),
            rec.get("fail_ids"),
        )
    if rec.get("kind") == "edit":
        if not rec.get("is_doc"):  # signal d: which code files each fix attempt touched
            seq = state["edit_seq"] = state.get("edit_seq", 0) + 1
            recent = state.setdefault("recent_edits", [])
            recent.append([seq, file_fingerprint(rec["file"])])
            del recent[:-RECENT_EDITS_KEPT]
        return _on_edit(state, rec["file"], rec["content_hash"], rec.get("before_hash"))
    return []


# --- Traces (the hook's oracle: every processed event, replayable) --------------------


def is_doc_path(shown: str) -> bool:
    """A documentation file: a DOC_SUFFIXES file, or anything under a DOC_DIRS folder."""
    parts = [p.lower() for p in shown.replace("\\", "/").split("/") if p]
    if not parts:
        return False
    return Path(parts[-1]).suffix in DOC_SUFFIXES or any(p in DOC_DIRS for p in parts[:-1])


def _write_trace(home: Path, repo: str, rec: dict, now: datetime) -> None:
    """Append ``rec`` to traces/<repo>.jsonl; first drop lines older than the retention
    window (checked on the oldest line only, so a rewrite happens at most once a day)."""
    trace_dir = home / TRACE_DIR
    trace_dir.mkdir(parents=True, exist_ok=True)
    path = trace_dir / f"{repo}.jsonl"
    cutoff = (now - timedelta(days=TRACE_RETENTION_DAYS)).strftime(TS_FORMAT)
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            first = fh.readline()
        try:
            stale = bool(first) and json.loads(first).get("ts", "") < cutoff
        except ValueError:
            stale = True
        if stale:
            kept = []
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    if json.loads(line).get("ts", "") >= cutoff:
                        kept.append(line)
                except ValueError:
                    continue
            path.write_text("".join(f"{line}\n" for line in kept), encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


# --- Entry points -------------------------------------------------------------------


def _log_fire(home: Path, repo: str, signal: str, fields: dict, now: datetime) -> None:
    entry = {"ts": now.strftime(TS_FORMAT), "repo": repo, "signal": signal}
    entry.update(fields)
    with (home / FIRES_FILE).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _event_cwd(event: dict) -> Path | None:
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd and Path(cwd).is_dir():
        return Path(cwd)
    return None


def _run_record(event: dict, hook: str, command: str, key: str, trusted: bool) -> dict:
    """The trace record of a watched run: outcome fail | pass | ignored, signature, basis."""
    rec = {"kind": "run", "key": key, "outcome": "ignored", "signature": "",
           "signature_basis": "", "fail_ids": []}
    if event.get("tool_input", {}).get("run_in_background"):
        return rec
    if hook == "PostToolUse":
        response = event.get("tool_response")
        response = response if isinstance(response, dict) else {}
        exit_ok = True
        output = f"{response.get('stdout') or ''}\n{response.get('stderr') or ''}"
    else:
        if event.get("is_interrupt"):
            return rec
        parsed = parse_failure(str(event.get("error") or ""))
        if parsed is None or parsed[0] == 0:
            return rec  # the shell never started, or no exit status to judge
        exit_ok, output = False, parsed[1]
    verdict, summary_sig, summary_basis = read_summary(key, output)
    if trusted:
        if exit_ok:
            rec["outcome"] = "pass"
        elif verdict == "fail":
            rec.update(outcome="fail", signature=summary_sig, signature_basis=summary_basis,
                       fail_ids=failing_ids(key, output))
        else:
            rec.update(outcome="fail", signature=error_signature(output),
                       signature_basis=BASIS_TAIL)
    elif verdict == "fail":
        rec.update(outcome="fail", signature=summary_sig, signature_basis=summary_basis,
                   fail_ids=failing_ids(key, output))
    elif verdict == "pass":
        rec["outcome"] = "pass"
    # else: exit code not the watched command's and no summary to read -> ignored
    return rec


def _edit_record(event: dict, hook: str, path: str, top: Path) -> dict:
    """The trace record of an edit: repo-relative path, is_doc, content hashes only."""
    shown = _display_path(path, top)
    rec = {"kind": "edit", "file": shown, "is_doc": is_doc_path(shown), "outcome": "ignored"}
    if hook != "PostToolUse":
        return rec  # a failed edit changed nothing
    try:
        after = Path(path).read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return rec
    tool_input = event.get("tool_input") or {}
    before = _previous_text(str(event.get("tool_name")), tool_input, after)
    rec.update(outcome="pass", content_hash=_text_hash(after),
               before_hash=_text_hash(before) if before is not None else None)
    return rec


def process(
    event: dict, home: Path, project_dir: Path, now: datetime | None = None
) -> dict | None:
    """Handle one hook event; return the hook's JSON output, or None for no output.

    ``home`` holds state/, traces/ and fires.jsonl; ``project_dir`` (CLAUDE_PROJECT_DIR)
    is only the last fallback. State is keyed by the repo the work happened in: for a
    shell command, the hook's cwd moved by the command's leading ``cd``; for an edit,
    the edited file's directory. Each resolved through git (``repo_top``). Every
    processed event (a watched run, an edit) becomes one trace record, and ``step``
    decides the signals from that record alone.
    """
    hook = event.get("hook_event_name")
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") or {}
    if hook not in ("PostToolUse", "PostToolUseFailure") or not isinstance(tool_input, dict):
        return None
    now = now or datetime.now(timezone.utc)

    base = _event_cwd(event) or project_dir
    if tool in SHELL_TOOLS:
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        if watched_run(command) is None and "scripts" not in command.replace("\\", "/"):
            return None  # cheap exit: nothing watched, no git call
        top = repo_top(command_dir(command, base))
        run = watched_run(command, top)
        if run is None:
            return None
        rec = _run_record(event, str(hook), command, *run)
    elif tool in EDIT_TOOLS:
        path = tool_input.get("file_path")
        if not isinstance(path, str) or not path:
            return None
        top = repo_top(Path(path).parent)  # filed under the edited file's repo
        rec = _edit_record(event, str(hook), path, top)
    else:
        return None

    repo = _UNSAFE_NAME.sub("_", top.name) or "unknown"
    session_id = str(event.get("session_id") or "")
    rec = {"ts": now.strftime(TS_FORMAT), "session_id": session_id, "repo": repo, **rec}
    state_dir = home / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{repo}.json"
    with _Lock(state_dir / f"{repo}.lock") as lock:
        if not lock.held:
            return None
        state = _load(state_file, session_id)
        tool_use_id = event.get("tool_use_id")
        if isinstance(tool_use_id, str) and tool_use_id:
            ident = f"{hook}:{tool_use_id}"
            seen = state.setdefault("seen", [])
            if ident in seen:
                return None  # another copy of this hook already processed this event
            seen.append(ident)
            del seen[:-SEEN_EVENTS_KEPT]
        _write_trace(home, repo, rec, now)
        state["d_mode"] = d_mode()  # what THIS process saw: proof the setting arrived
        fires = step(state, rec)
        _save(state_file, state)
        for signal, _, fields in fires:
            _log_fire(home, repo, signal, fields, now)

    shown = [f for f in fires if not f[2].get("shadow")]  # shadow firings: logged only
    if not shown:
        return None
    message = "\n".join(MESSAGE.format(signal=s, detail=d) for s, d, _ in shown)
    return {
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": hook, "additionalContext": message},
    }


def _project_dir() -> Path:
    """The last-resort fallback: CLAUDE_PROJECT_DIR, else the process's cwd."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path.cwd()


def main() -> int:
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if isinstance(event, dict):
            out = process(event, default_home(), _project_dir())
            if out is not None:
                sys.stdout.write(json.dumps(out))
                sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001 - a hook must never break the session
        sys.stderr.write(f"spiral_detector: {type(exc).__name__}\n")  # debug log only
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
