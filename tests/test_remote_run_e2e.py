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


def test_the_app_reads_probe_snapshots_from_a_remote_state_role(remote_run, monkeypatch):
    """M13: with env.probe.snapshots on, each feed's LATEST snapshot is read
    from <state>/probes/<feed>.json on the REMOTE state role (a workspace
    folder here). One feed has a snapshot (probed for nothing this run
    expects: every table is `not in the probe snapshot`), the others have
    none (`missing`) — and the run completes either way."""
    from codegen.env.model import EnvProbeResult, ProbeSnapshot

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    workbook = REPO / store.config.demo.workbook
    frd = REPO / store.config.contracts.dir / store.config.demo.frd
    if not (workbook.is_file() and frd.is_file()):
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")
    monkeypatch.setenv("CODEGEN_ENV_PROBE_SNAPSHOTS", "1")
    slug = "cv_community_risk"
    taken = "2026-09-22T09:00:00Z"
    snapshot = ProbeSnapshot(taken_at=taken, identity="analyst@synthetic.example",
                             feeds=[EnvProbeResult(feed_slug=slug, probed_at=taken)])
    remote_run.ws.files[f"{SHARED}/state/probes/{slug}.json"] = \
        snapshot.model_dump_json().encode("utf-8")

    runner = DemoRunner(store)
    runner.select_output_mode("framework")
    runner.start_live()
    deadline = __import__("time").monotonic() + 600
    while runner.state in ("running", "needs_layout"):
        assert __import__("time").monotonic() < deadline, "the live run did not finish"
        __import__("time").sleep(0.5)
    assert runner.state == "done", f"{runner.error}\n{runner.stages}"
    envs = {s: r.environment for s, r in store.runs.items()}
    assert slug in envs and all(e is not None for e in envs.values()), envs
    read = envs[slug]["snapshot"]
    assert read["where"].startswith("workspace:") and not read["missing"]
    assert read["identity"] == "analyst@synthetic.example"
    assert envs[slug]["headline"] == "UNKNOWN"          # it saw none of these tables
    for other, env in envs.items():
        if other != slug:
            assert env["snapshot"]["missing"] and env["headline"] == "UNKNOWN", other
