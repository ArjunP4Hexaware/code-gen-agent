"""A WHOLE live run under remote storage roles (fake SDK client), v0.5.7.

Two App-only failures in a row (v0.5.6 the picker, v0.5.7 "live run produced
no feeds") shared one cause: with `storage.*` on workspace / volume roots the
run happens OUTSIDE the checkout, and nothing exercised that end to end — the
existing remote test stubs the run (`work=lambda: None`), every other run test
uses the default local roles, so both bugs passed a green suite.

This drives `DemoRunner`'s real `_execute` with inputs / state on a fake
workspace and outputs on a fake volume: generate, list the files, push them
up. Layer 2 is mock-locked (CLAUDE.md: a test that touches the live path MUST
pin the provider — an unpinned FMAPI provider resolves from workspace auth
alone and fires real calls).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from ui.backend import stores as ui_stores  # noqa: E402
from ui.backend.demo import DemoRunner  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.storage import open_storage  # noqa: E402
from storage_fakes import FakeWorkspaceClient  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SHARED = "/Users/u/shared"
VOLUME = "/Volumes/cat/sch/vol/runs"


@pytest.fixture
def remote_run(monkeypatch, tmp_path):
    """inputs / state on the fake workspace, OUTPUTS on the fake volume —
    the App's shape: a run's working copy is a temp dir, not the checkout."""
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl@synthetic.example")
    fake = FakeWorkspaceClient()
    fake.ws.dirs.update({f"{SHARED}/inputs", f"{SHARED}/state"})
    fake.vol.dirs.add(VOLUME)
    env = {"CODEGEN_STORAGE_INPUTS": f"workspace:/Workspace{SHARED}/inputs",
           "CODEGEN_STORAGE_STATE": f"workspace:/Workspace{SHARED}/state",
           "CODEGEN_STORAGE_OUTPUTS": f"volume:{VOLUME}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch")}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env, client=fake))
    ui_stores.reset_stores()
    yield fake
    ui_stores.reset_stores()


def test_a_live_run_with_remote_roles_produces_feeds_and_pushes_them(remote_run):
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    workbook = REPO / store.config.demo.workbook
    frd = REPO / store.config.contracts.dir / store.config.demo.frd
    if not (workbook.is_file() and frd.is_file()):
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")

    # The run's working copy is the outputs role's temp dir — NOT the repo.
    run_root = ui_stores.outputs_root(store.config)
    assert not run_root.is_relative_to(REPO), run_root

    runner = DemoRunner(store)                       # the REAL _execute
    runner.start_live()
    deadline = __import__("time").monotonic() + 600
    while runner.state in ("running", "needs_layout"):
        assert __import__("time").monotonic() < deadline, "the live run did not finish"
        __import__("time").sleep(0.5)

    assert runner.state == "done", f"{runner.error}\n{runner.stages}"
    assert store.runs, "the run produced no feeds"
    for slug, run in store.runs.items():
        assert run.written_files, f"{slug} reported no files"
        # Outside the checkout the paths stay absolute (v0.5.7) and still
        # carry the segment the UI needs.
        assert any(f"/{slug}/" in f for f in run.written_files)
    # …and the artefacts reached the remote role.
    pushed = [p for p in remote_run.vol.files if p.startswith(VOLUME)]
    assert pushed, "nothing was pushed to the outputs role"
    assert any(p.endswith(".sql") for p in pushed), sorted(pushed)[:5]
    # run_meta.json says which code produced the run (codegen.build_info).
    (meta_path,) = [p for p in pushed if p.endswith("/run_meta.json")]
    meta = __import__("json").loads(remote_run.vol.files[meta_path])
    assert meta["codegen"].startswith("codegen ") and str(REPO / "src") in meta["codegen"]


# ---------------------------------------------- the held-back path (Chunk C)

PAIRS = f"{SHARED}/pairs"


@pytest.fixture
def remote_pairs(monkeypatch, tmp_path):
    """The ACFC shape for the held-back path: the STTM and its FRD in a pair
    folder of a workspace input root (CODEGEN_EXTRA_INPUT_DIRS), state on the
    workspace, outputs on the volume."""
    import json

    from acfc_shapes import bands
    from acfc_shapes.common import xlsx_bytes

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl@synthetic.example")
    fake = FakeWorkspaceClient()
    fake.ws.dirs.update({f"{SHARED}/inputs", f"{SHARED}/state", PAIRS, f"{PAIRS}/pair_9"})
    fake.vol.dirs.add(VOLUME)
    contract = bands.frd_contract(stage_schema="nb_land")
    contract["feeds"][0]["stage_target"]["catalog"] = "nb_dlk"
    contract["feeds"][0]["standard_target"]["catalog"] = "nb_std"
    fake.ws.files[f"{PAIRS}/pair_9/STTM_{bands.FEED}.xlsx"] = xlsx_bytes(bands.three_lookalike())
    fake.ws.files[f"{PAIRS}/pair_9/FRD_{bands.FEED}.contract.json"] = json.dumps(
        contract, indent=2).encode("utf-8")
    env = {"CODEGEN_STORAGE_INPUTS": f"workspace:/Workspace{SHARED}/inputs",
           "CODEGEN_STORAGE_STATE": f"workspace:/Workspace{SHARED}/state",
           "CODEGEN_STORAGE_OUTPUTS": f"volume:{VOLUME}",
           "CODEGEN_EXTRA_INPUT_DIRS": f"workspace:/Workspace{PAIRS}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch")}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env, client=fake))
    yield fake, bands


def _wait_state(runner, *states, timeout=300.0):
    import time

    deadline = time.monotonic() + timeout
    while runner.state not in states:
        assert time.monotonic() < deadline, f"stuck in {runner.state}: {runner.stages[-3:]}"
        time.sleep(0.1)
    return runner.state


def test_a_remote_run_whose_every_feed_is_held_back_asks_then_completes(remote_pairs):
    """v0.5.6 / v0.5.7 were App-only: the held-back path is driven here under
    remote roles too — documents downloaded from a workspace pair folder, the
    run's working copy outside the checkout, outputs pushed to the volume."""
    fake, bands = remote_pairs
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, index_warmup=False)
    sttm = f"STTM_{bands.FEED}.xlsx"
    runner.select_workbook(sttm)                          # download + classify + pair
    if runner.selected_frd is None:                       # paired by content, else chosen
        name = f"FRD_{bands.FEED}.contract.json"
        runner.select_frd(runner.fetch_frd_candidate(name), name)
    assert runner.selected_workbook is not None
    assert not runner.selected_workbook.is_relative_to(REPO)

    runner.start_live()
    assert _wait_state(runner, "needs_layout", "failed", "done") == "needs_layout", runner.error
    keys = [q["key"] for q in runner.status()["layout_questions"]]
    assert keys == [f"{bands.SHEET}/band[{n}]/layer" for n in (1, 2, 3)]
    runner.answer_layout({}, proceed=True)
    assert _wait_state(runner, "needs_answers", "failed", "done") == "needs_answers", (
        runner.error, runner.stages[-3:])
    status = runner.status()
    assert [i["key"] for i in status["needs_answers"]] == keys
    assert status["error"] is None
    assert not [p for p in fake.vol.files if p.startswith(VOLUME)], "a held-back run pushed"

    runner.rerun_with_answers({"sttm": dict(zip(keys, ("source", "stage", "standard"),
                                                strict=True))})
    state = _wait_state(runner, "done", "failed", "needs_answers", "needs_layout")
    if state == "needs_layout":
        # By now the background index has read the pair folder: the VDD pairing
        # (all candidates at score 0 — the quirk kept as found) is asked at run
        # start. A VDD is optional; answering nothing runs without one. The
        # band answers carried, so nothing else is asked.
        assert [q["key"] for q in runner.status()["layout_questions"]] == ["pair.vdd"]
        runner.answer_layout({})
        state = _wait_state(runner, "done", "failed", "needs_answers")
    assert state == "done", (runner.error, runner.stages[-5:])
    assert runner.status()["needs_answers"] == []
    assert store.runs and all(run.written_files for run in store.runs.values())
    pushed = [p for p in fake.vol.files if p.startswith(VOLUME)]
    assert any(p.endswith("/run_meta.json") for p in pushed), sorted(pushed)[:5]
