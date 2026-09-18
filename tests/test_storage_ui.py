"""M8.1: the UI backend over remote storage roles (fake SDK client) — the
chooser lists documents from a shared workspace folder at depth 1, a
selection downloads a working copy, state and run outputs are pushed up, and
with the default roles nothing moves at all."""

from __future__ import annotations

import json
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


@pytest.fixture
def remote(monkeypatch, tmp_path):
    """inputs / state on the fake workspace, outputs on the fake volume, one
    extra input root holding pair folders."""
    fake = FakeWorkspaceClient()
    # Roots exist up front (an admin / the user creates and shares them).
    fake.ws.dirs.update({f"{SHARED}/inputs", f"{SHARED}/state"})
    fake.vol.dirs.add("/Volumes/cat/sch/vol/runs")
    fake.ws.dirs.update({f"{SHARED}/pairs", f"{SHARED}/pairs/pair_1", f"{SHARED}/pairs/pair_2",
                         f"{SHARED}/pairs/pair_2/deeper"})
    fake.ws.files.update({
        f"{SHARED}/pairs/pair_1/STTM_alpha.xlsx": b"alpha",
        f"{SHARED}/pairs/pair_1/FRD_alpha.docx": b"frd-alpha",
        f"{SHARED}/pairs/pair_2/STTM_beta.xlsx": b"beta",
        f"{SHARED}/pairs/pair_2/~$STTM_beta.xlsx": b"lock",
        f"{SHARED}/pairs/pair_2/deeper/STTM_too_deep.xlsx": b"deep",
    })
    env = {"CODEGEN_STORAGE_INPUTS": f"workspace:/Workspace{SHARED}/inputs",
           "CODEGEN_STORAGE_STATE": f"workspace:/Workspace{SHARED}/state",
           "CODEGEN_STORAGE_OUTPUTS": "volume:/Volumes/cat/sch/vol/runs",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
           "CODEGEN_EXTRA_INPUT_DIRS": f"workspace:/Workspace{SHARED}/pairs"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env, client=fake))
    ui_stores.reset_stores()
    yield fake, tmp_path
    ui_stores.reset_stores()


@pytest.fixture
def runner():
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    return store, DemoRunner(store, work=lambda: None)


def test_chooser_lists_extra_root_at_depth_one(remote, runner):
    _store, demo = runner
    remote_rows = {c["name"]: c["source"] for c in demo.workbook_choices()
                   if c["source"].startswith("pairs")}
    assert remote_rows == {"STTM_alpha.xlsx": "pairs/pair_1", "STTM_beta.xlsx": "pairs/pair_2"}
    assert "FRD_alpha.docx" in demo.local_frd_candidates()


def test_selecting_a_remote_workbook_downloads_a_working_copy(remote, runner):
    _fake, tmp = remote
    _store, demo = runner
    path = demo.select_workbook("STTM_alpha.xlsx")
    assert path.read_bytes() == b"alpha" and tmp in path.parents
    assert [c["name"] for c in demo.workbook_choices() if c["selected"]] == ["STTM_alpha.xlsx"]
    frd = demo.fetch_frd_candidate("FRD_alpha.docx")
    assert frd is not None and frd.read_bytes() == b"frd-alpha"


def test_an_unreachable_root_is_reported_not_fatal(remote, runner):
    fake, _tmp = remote
    _store, demo = runner

    def boom(_path):
        raise RuntimeError("PERMISSION_DENIED: folder not shared with the app")

    fake.workspace.list = boom
    assert all(not c["source"].startswith("pairs") for c in demo.workbook_choices())
    assert "not shared" in demo.input_errors()["pairs"]


def test_state_and_run_outputs_are_pushed(remote, runner):
    fake, _tmp = remote
    store, _demo = runner
    store._write_all_decisions({"demo_1": {}})  # noqa: SLF001
    pushed = json.loads(fake.ws.files[f"{SHARED}/state/decisions.json"])
    assert pushed["runs"] == {"demo_1": {}}
    assert store._load_all_decisions() == {"demo_1": {}}  # noqa: SLF001

    run = ui_stores.outputs_root(store.config) / "demo_20260918_000000" / "feed"
    run.mkdir(parents=True)
    (run / "README.md").write_text("# feed\n", encoding="utf-8")
    assert ui_stores.push_run(store.config, "demo_20260918_000000") == [
        "demo_20260918_000000/feed/README.md"]
    assert "/Volumes/cat/sch/vol/runs/demo_20260918_000000/feed/README.md" in fake.vol.files
    assert ui_stores.remote_run_labels(store.config) == ["demo_20260918_000000"]


def test_default_roles_are_the_repo_directories_and_push_nothing(runner):
    ui_stores.reset_stores()
    store, _demo = runner
    default = REPO / "inputs" / "uploads"
    assert ui_stores.inbox_dir(store.config, "uploads", default) == default
    assert ui_stores.outputs_root(store.config) == REPO / store.config.output.dir
    assert ui_stores.layout_cache_dir(store.config) == (
        REPO / store.config.layout.runtime_cache_dir)
    assert ui_stores.push_run(store.config, "demo_x") == []
    assert ui_stores.remote_run_labels(store.config) == []


def test_a_missing_remote_root_is_a_named_configuration_error(remote, runner):
    fake, _tmp = remote
    store, _demo = runner
    fake.ws.dirs.discard(f"{SHARED}/state")
    with pytest.raises(Exception, match="storage root workspace:/Workspace/Users/u/shared/state"):
        store._write_all_decisions({})  # noqa: SLF001
    assert not any(op == "mkdirs" and path == f"{SHARED}/state" for op, path in fake.ws.calls)
