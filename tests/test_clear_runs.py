"""The "Clear past runs" button: one button deletes every past run folder.

Only folders named ``demo_<YYYYMMDD>_<HHMMSS>`` (what the live runner
creates) are deleted — in the outputs role's working copy AND, for a remote
role, the stored copy (else the listing pulls them straight back). The
outputs root and everything else in it are never touched; it needs
``confirm: true`` and is refused while a run is in progress; a loaded run
whose folder is deleted stops being served.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402
from ui.backend import stores as ui_stores  # noqa: E402
from ui.backend.demo import DemoRunner, LiveRunInProgress  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.storage import StorageError, open_storage  # noqa: E402
from codegen.storage.local import LocalBackend  # noqa: E402
from codegen.storage.remote import VolumeBackend, WorkspaceBackend  # noqa: E402
from storage_fakes import FakeWorkspaceClient  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RUNS = ["demo_20260901_111207", "demo_20260918_091827"]
KEPT = ["handoff", "cv_community_risk", "demo_notes", "replay_live_e2e_20260807"]


def _seed(root: Path) -> None:
    for name in RUNS:
        (root / name / "feed" / "ddl").mkdir(parents=True)
        (root / name / "feed" / "ddl" / "x.sql").write_text("select 1", encoding="utf-8")
        (root / name / "run_meta.json").write_text("{}", encoding="utf-8")
    for name in KEPT:
        (root / name).mkdir()
        (root / name / "keep.txt").write_text("keep", encoding="utf-8")


@pytest.fixture
def local_outputs(monkeypatch, tmp_path):
    """The outputs role on a scratch directory — never the checkout's out/."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    _seed(outputs)
    env = {"CODEGEN_STORAGE_OUTPUTS": f"local:{outputs.as_posix()}"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env))
    ui_stores.reset_stores()
    yield outputs
    ui_stores.reset_stores()


@pytest.fixture
def api(monkeypatch, local_outputs):
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, work=lambda: None)
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(main, "runner", runner)
    return TestClient(main.app), store, runner, local_outputs


# ------------------------------------------------------------------ the route


def test_it_lists_then_deletes_exactly_the_run_folders(api):
    client, _store, _runner, outputs = api
    assert client.get("/api/demo/runs").json() == {"runs": sorted(RUNS, reverse=True)}
    reply = client.post("/api/demo/runs/clear", json={"confirm": True})
    assert reply.status_code == 200
    assert sorted(reply.json()["deleted"]) == sorted(RUNS)
    assert sorted(p.name for p in outputs.iterdir()) == sorted(KEPT)
    assert all((outputs / name / "keep.txt").is_file() for name in KEPT)
    assert client.get("/api/demo/runs").json() == {"runs": []}
    # Clearing an empty list is a no-op, not an error.
    assert client.post("/api/demo/runs/clear", json={"confirm": True}).json()["deleted"] == []


def test_it_needs_an_explicit_confirm(api):
    client, _store, _runner, outputs = api
    assert client.post("/api/demo/runs/clear", json={}).status_code == 400
    assert all((outputs / name).is_dir() for name in RUNS)


@pytest.mark.parametrize("state", ["running", "needs_layout"])
def test_it_is_refused_while_a_run_is_in_progress(api, state):
    client, _store, runner, outputs = api
    runner.state = state
    reply = client.post("/api/demo/runs/clear", json={"confirm": True})
    assert reply.status_code == 409
    assert all((outputs / name).is_dir() for name in RUNS)


def test_a_run_cannot_start_while_runs_are_being_cleared(api):
    _client, _store, runner, _outputs = api
    runner._clearing = True
    with pytest.raises(LiveRunInProgress, match="being cleared"):
        runner.start_live()


def test_the_loaded_run_stops_being_served_when_its_folder_goes(api):
    client, store, runner, outputs = api
    label = RUNS[0]
    store.adopt({}, [], mode="live", label=label, out_root=outputs / label,
                reports_root=outputs / label / "reports")
    runner.last_run_label, runner.state = label, "done"
    reply = client.post("/api/demo/runs/clear", json={"confirm": True})
    assert reply.json()["unloaded_current"] is True
    assert store.label is None and store.mode == "mock" and not store.has_run
    assert runner.state == "idle" and runner.last_run_label is None
    assert client.get("/api/feeds").json()["label"] is None


# ------------------------------------------------------------------ the backends


def test_local_delete_tree_never_deletes_the_root(tmp_path):
    backend = LocalBackend(tmp_path)
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "f.txt").write_text("x", encoding="utf-8")
    for root_like in ("", ".", "/"):
        with pytest.raises(StorageError):
            backend.delete_tree(root_like)
    with pytest.raises(StorageError):
        backend.delete_tree("../elsewhere")
    backend.delete_tree("a")
    backend.delete_tree("a")                 # already gone: a no-op
    assert tmp_path.is_dir() and not (tmp_path / "a").exists()


def test_workspace_delete_tree_is_recursive_and_below_the_root():
    fake = FakeWorkspaceClient()
    backend = WorkspaceBackend("/Workspace/Users/u/shared", client=fake)
    backend.write_bytes("demo_20260901_111207/feed/x.sql", b"select 1")
    backend.write_bytes("handoff/keep.txt", b"keep")
    backend.delete_tree("demo_20260901_111207")
    assert [e.name for e in backend.list("")] == ["handoff"]
    with pytest.raises(StorageError):
        backend.delete_tree("")
    backend.delete_tree("demo_20260901_111207")        # absent: a no-op


def test_volume_delete_tree_empties_directories_deepest_first():
    fake = FakeWorkspaceClient()
    backend = VolumeBackend("/Volumes/cat/sch/vol", client=fake)
    backend.write_bytes("demo_20260901_111207/feed/ddl/x.sql", b"select 1")
    backend.write_bytes("demo_20260901_111207/run_meta.json", b"{}")
    backend.write_bytes("handoff/keep.txt", b"keep")
    backend.delete_tree("demo_20260901_111207")   # the fake refuses a non-empty directory
    assert [e.name for e in backend.list("")] == ["handoff"]
    assert fake.vol.files == {"/Volumes/cat/sch/vol/handoff/keep.txt": b"keep"}


def test_a_remote_outputs_role_loses_the_stored_copy_too(monkeypatch, tmp_path):
    """Clearing only the working copy would be undone by the next listing,
    which pulls remote-only runs back down."""
    fake = FakeWorkspaceClient()
    volume = "/Volumes/cat/sch/vol/runs"
    fake.vol.dirs.add(volume)
    env = {"CODEGEN_STORAGE_OUTPUTS": f"volume:{volume}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch")}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env, client=fake))
    ui_stores.reset_stores()
    try:
        store = GenerationStore(str(REPO / "config" / "config.yaml"))
        outputs = ui_stores.get_stores(store.config).outputs
        for name in RUNS:
            outputs.write_bytes(f"{name}/run_meta.json", b"{}")
        outputs.write_bytes("handoff/keep.txt", b"keep")
        assert ui_stores.run_labels(store.config) == sorted(RUNS, reverse=True)
        runner = DemoRunner(store, work=lambda: None)
        assert sorted(runner.clear_runs()["deleted"]) == sorted(RUNS)
        assert [e.name for e in outputs.list("")] == ["handoff"]
        assert not any((outputs.workdir / name).exists() for name in RUNS)
        assert ui_stores.run_labels(store.config) == []
    finally:
        ui_stores.reset_stores()
