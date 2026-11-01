"""Signal (d), cascade: consecutive fix attempts that each leave a test failing somewhere
new (a file with no failing tests before, not touched by the attempt). Fix A causes
error B, fixing B causes error C: the drift spiral the skill was written for.

Acceptance (pre-registered 2026-10-31, retros/2026-10-31-hook.md addendum):
1. fires on every synthetic cascade below, at its 2nd cascade step;
2. fires on no synthetic test-first / normal-work sequence below;
3. leaves signals a / b / c unchanged (the replay of all traces is unchanged);
4. (later, real traces) fewer false alarms than signal (b) over the same window.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "spiral_detector.py"
_spec = importlib.util.spec_from_file_location("spiral_detector_cascade", HOOK)
sd = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(sd)

KEY = "python -m pytest -q"
_hashes = itertools.count()

A, B, C, D = (f"tests/test_{x}.py::t" for x in "abcd")


def run(*ids: str, key: str = KEY, with_ids: bool = True) -> dict:
    """A traced pytest run: fails with ``ids`` (passes when none)."""
    sig = hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()[:16] if ids else ""
    return {"kind": "run", "key": key, "outcome": "fail" if ids else "pass",
            "signature": sig, "signature_basis": sd.BASIS_IDS if ids else "",
            "fail_ids": sorted(sd.id_fingerprint(i) for i in ids) if with_ids else []}


def edit(path: str, doc: bool = False) -> dict:
    return {"kind": "edit", "file": path, "is_doc": doc, "outcome": "pass",
            "content_hash": f"h{next(_hashes)}", "before_hash": None}


def fired(records: list[dict], monkeypatch: pytest.MonkeyPatch, mode: str = "live") -> list:
    """[(signal, index of the record that fired it)] over a fresh session."""
    monkeypatch.setattr(sd, "SIGNAL_D_MODE", mode)
    state = sd._fresh_state("s")
    return [(sig, i) for i, rec in enumerate(records) for sig, _, _ in sd.step(state, rec)]


# --- 1. Cascades: must fire at the 2nd cascade step -------------------------------------------

CASCADES = {
    # fix A breaks B, fixing B breaks C (the user's 30-hour shape)
    "a-to-b-to-c": [run(A), edit("src/a.py"), run(B), edit("src/b.py"), run(C)],
    # the failures pile up and spread while the fixes spread across files
    "spreading": [run(A), edit("src/a.py"), run(A, B),
                  edit("src/b.py"), edit("src/a.py"), run(A, B, C)],
    # a plain re-run and a doc edit in between change nothing
    "with-noise": [run(A), edit("src/a.py"), run(B), run(B), edit("README.md", doc=True),
                   edit("src/b.py"), run(C)],
    # monkeypatches in modules far from the failure
    "monkeypatches": [run(A), edit("src/a.py"), edit("src/util.py"), run(B, C),
                      edit("src/patch.py"), run(D)],
}


@pytest.mark.parametrize("name", list(CASCADES))
def test_d_fires_on_a_cascade_at_its_second_step(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = CASCADES[name]  # (a) may also fire, e.g. on with-noise's identical re-run
    assert [f for f in fired(records, monkeypatch) if f[0] == "d"] == [("d", len(records) - 1)]


def test_d_does_not_fire_on_the_first_cascade_step(monkeypatch: pytest.MonkeyPatch) -> None:
    assert fired([run(A), edit("src/a.py"), run(B)], monkeypatch) == []


# --- 2. Test-first and normal work: must never fire ----------------------------------------------

NORMAL = {
    # a new test file: collection error, then its tests appear one by one (same file)
    "new-test-file": [edit("tests/test_n.py"), run("tests/test_n.py"),
                      edit("src/m.py"), run("tests/test_n.py"),
                      edit("src/m.py"), run("tests/test_n.py::t1", "tests/test_n.py::t2"),
                      edit("src/m.py"), run("tests/test_n.py::t2"),
                      edit("src/m.py"), run()],
    # tests added one at a time, each made to pass
    "one-test-at-a-time": [edit("tests/test_a.py"), run(A), edit("src/a.py"), run(),
                           edit("tests/test_a.py"), run("tests/test_a.py::t2"),
                           edit("src/a.py"), run()],
    # new test files written while an old failure stays open
    "new-tests-beside-old-failure": [run(A), edit("tests/test_b.py"), run(A, B),
                                     edit("tests/test_c.py"), run(A, B, C)],
    # a refactor whose failures shrink
    "shrinking": [run(A, B, C), edit("src/x.py"), run(B, C), edit("src/y.py"), run(C),
                  edit("src/z.py"), run()],
    # one fix breaks one thing, which is then fixed
    "one-slip": [run(A), edit("src/a.py"), run(B), edit("src/b.py"), run()],
    # the Oct 13 shape: a collection error whose missing name moves, many module edits
    "moving-import-error": [edit("tests/test_p.py"), run("tests/test_p.py"),
                            *[edit("src/demo.py") for _ in range(6)], run("tests/test_p.py")],
    # no test IDs (summary-only or tail-hash): no evidence, no firing
    "no-ids": [run(A), edit("src/a.py"), run(B, with_ids=False),
               edit("src/b.py"), run(C, with_ids=False)],
}


@pytest.mark.parametrize("name", list(NORMAL))
def test_d_never_fires_on_normal_work(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    assert [s for s, _ in fired(NORMAL[name], monkeypatch) if s == "d"] == []


def test_d_is_kept_per_command(monkeypatch: pytest.MonkeyPatch) -> None:
    other = "python -m pytest -q tests/test_b.py"
    records = [run(A), edit("src/a.py"), run(B, key=other), edit("src/b.py"), run(C)]
    assert fired(records, monkeypatch) == []


def test_d_off_never_fires(monkeypatch: pytest.MonkeyPatch) -> None:
    assert fired(CASCADES["a-to-b-to-c"], monkeypatch, mode="off") == []


def test_d_pre_registered_settings() -> None:
    assert sd.SIGNAL_D_CASCADE_STEPS == 2
    assert sd.SIGNAL_D_MODE == "shadow"
    assert sd.D_MODE_ENV == "SPIRAL_BREAKER_D_MODE"


@pytest.mark.parametrize(("env", "mode"), [
    (None, "shadow"),            # unset: the module default
    ("live", "live"),            # a machine where (d) is live
    (" LIVE ", "live"),          # tolerant of case and spaces
    ("off", "off"),
    ("loud", "shadow"),          # unknown: the safe default, never an error
])
def test_the_environment_sets_d_mode_per_machine(
    env: str | None, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if env is not None:
        monkeypatch.setenv(sd.D_MODE_ENV, env)
    assert sd.d_mode() == mode


def test_live_from_the_environment_reports_the_cascade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(sd.D_MODE_ENV, "live")
    outs, fires = _drive(tmp_path)
    assert outs[4] is not None and "signal (d)" in outs[4]["systemMessage"]
    assert [(f["signal"], f.get("shadow")) for f in fires] == [("d", None)]


# --- Fingerprints: a pytest node's file part matches the edited file's fingerprint ----------


def test_fingerprints_carry_the_test_file() -> None:
    node, collection = sd.id_fingerprint(A), sd.id_fingerprint("tests/test_a.py")
    assert node.split(":")[0] == collection.split(":")[0] == sd.file_fingerprint(
        "tests/test_a.py")
    assert node != collection
    assert ":" not in sd.id_fingerprint("F401")  # a ruff rule code: no file
    assert ":" not in sd.id_fingerprint("m::t")  # a cargo test path: no file


# --- Shadow vs live, through the hook entry point ---------------------------------------------


def _drive(tmp_path: Path) -> tuple[list[dict | None], list[dict]]:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    (root / "src").mkdir()
    home = tmp_path / "home"
    outs: list[dict | None] = []

    def send(event: dict) -> None:
        outs.append(sd.process({"session_id": "s", "cwd": str(root), **event}, home, root))

    def fail(test: str) -> None:
        send({"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
              "tool_input": {"command": KEY}, "is_interrupt": False,
              "error": f"Exit code 1\nFAILED {test} - boom\n1 failed in 0.1s"})

    def write(name: str) -> None:
        path = root / name
        path.write_text(f"{name} {len(outs)}\n", encoding="utf-8")
        send({"hook_event_name": "PostToolUse", "tool_name": "Write",
              "tool_input": {"file_path": str(path), "content": "x"},
              "tool_response": {"filePath": str(path)}})

    fail(A)
    write("src/a.py")
    fail(B)
    write("src/b.py")
    fail(C)
    fires_file = home / sd.FIRES_FILE
    fires = [json.loads(x) for x in fires_file.read_text(encoding="utf-8").splitlines()] \
        if fires_file.exists() else []
    return outs, fires


def test_shadow_mode_logs_the_firing_but_tells_claude_nothing(tmp_path: Path) -> None:
    outs, fires = _drive(tmp_path)  # default mode: shadow
    assert outs == [None] * 5
    assert [(f["signal"], f.get("shadow")) for f in fires] == [("d", True)]


def test_live_mode_reports_the_cascade(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sd, "SIGNAL_D_MODE", "live")
    outs, fires = _drive(tmp_path)
    assert outs[:4] == [None] * 4 and outs[4] is not None
    assert "signal (d)" in outs[4]["hookSpecificOutput"]["additionalContext"]
    assert [(f["signal"], f.get("shadow")) for f in fires] == [("d", None)]
