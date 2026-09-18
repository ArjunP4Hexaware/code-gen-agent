"""M8.1 storage backends: one contract, three backends (local on tmp_path,
workspace + volume against the fake SDK client in ``storage_fakes``)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.storage import (
    LocalBackend,
    StorageConfigError,
    StorageNotFound,
    VolumeBackend,
    WorkspaceBackend,
    open_backend,
    open_storage,
    parse_uri,
)
from storage_fakes import FakeWorkspaceClient

REPO = Path(__file__).resolve().parents[1]
WS_URI = "workspace:/Workspace/Users/u/shared"
VOL_URI = "volume:/Volumes/cat/sch/vol"


@pytest.fixture
def fake():
    return FakeWorkspaceClient()


@pytest.fixture(params=["local", "workspace", "volume"])
def backend(request, tmp_path, fake):
    if request.param == "local":
        root = tmp_path / "root"
        root.mkdir()
        return LocalBackend(root)
    uri = WS_URI if request.param == "workspace" else VOL_URI
    return open_backend(uri, base_dir=tmp_path, client=fake)


# -- the contract, identical for every backend ---------------------------------

def test_write_read_list_exists_round_trip(backend):
    assert backend.list() == []
    assert backend.exists("") is True
    assert backend.exists("uploads/a.xlsx") is False
    backend.write_bytes("uploads/a.xlsx", b"\x00\x01binary")
    backend.write_bytes("uploads/pair_1/b.docx", b"doc")
    backend.write_bytes("top.json", b"{}")
    assert backend.read_bytes("uploads/a.xlsx") == b"\x00\x01binary"
    assert backend.exists("uploads/a.xlsx") and backend.exists("uploads")
    assert [(e.name, e.is_dir) for e in backend.list()] == [("top.json", False),
                                                           ("uploads", True)]
    assert [(e.name, e.is_dir, e.size) for e in backend.list("uploads")] == [
        ("a.xlsx", False, 8), ("pair_1", True, None)]
    backend.write_bytes("top.json", b"[1]")                       # overwrite
    assert backend.read_bytes("top.json") == b"[1]"


def test_missing_paths(backend):
    assert backend.list("nowhere") == []
    with pytest.raises(StorageNotFound):
        backend.read_bytes("nowhere/x.json")


def test_walk_is_depth_limited(backend):
    for rel in ("a.xlsx", "pair_1/b.xlsx", "pair_1/deep/c.xlsx"):
        backend.write_bytes(rel, b"x")
    assert [r for r, _ in backend.walk("", 0)] == ["a.xlsx"]
    assert [r for r, _ in backend.walk("", 1)] == ["a.xlsx", "pair_1/b.xlsx"]
    assert len(backend.walk("")) == 3


@pytest.mark.parametrize("rel", ["../x", "a/../../x", "/abs", "C:/x", "a\\b"])
def test_paths_cannot_leave_the_root(backend, rel):
    with pytest.raises(StorageConfigError):
        backend.write_bytes(rel, b"x")


def test_mkdir_never_targets_the_root(backend):
    backend.mkdir("")                       # a no-op, not a creation
    backend.mkdir("state/layout_profiles")
    assert backend.exists("state/layout_profiles")


# -- mkdir semantics: the serverless PermissionError ---------------------------

def test_remote_mkdir_calls_stay_below_the_root(fake, tmp_path):
    """The fake answers PermissionDenied for the root and every ancestor (as
    the /Volumes mount does). A write two levels down must succeed, and no
    mkdir call may name the root or anything above it."""
    for uri, tree, root in ((WS_URI, fake.ws, "/Users/u/shared"),
                            (VOL_URI, fake.vol, "/Volumes/cat/sch/vol")):
        backend = open_backend(uri, base_dir=tmp_path, client=fake)
        backend.write_bytes("demo/pair_1/out.txt", b"x")
        made = [path for op, path in tree.calls if op in ("mkdirs", "create_directory")]
        assert made and all(p.startswith(root + "/") for p in made), made


def test_absolute_local_root_is_never_created(tmp_path):
    backend = open_backend(f"local:{(tmp_path / 'absent').as_posix()}", base_dir=tmp_path)
    with pytest.raises(StorageConfigError, match="never created"):
        backend.write_bytes("x.json", b"{}")
    assert not (tmp_path / "absent").exists()


def test_relative_local_root_is_created_inside_the_checkout(tmp_path):
    backend = open_backend("local:./ui/backend/state", base_dir=tmp_path)
    backend.write_bytes("decisions.json", b"{}")
    assert (tmp_path / "ui/backend/state/decisions.json").read_bytes() == b"{}"


@pytest.mark.parametrize("uri", ["local:/Volumes/cat/sch/vol/state", "local:/Workspace/Users/u/x"])
def test_local_refuses_a_databricks_mount_path(uri, tmp_path):
    with pytest.raises(StorageConfigError, match="mounted filesystem"):
        open_backend(uri, base_dir=tmp_path)


# -- URIs ---------------------------------------------------------------------------

@pytest.mark.parametrize("uri", ["", "inputs", "/Volumes/c/s/v", "s3:bucket", "local:"])
def test_bad_uris_are_refused(uri):
    with pytest.raises(StorageConfigError):
        parse_uri(uri)


@pytest.mark.parametrize("uri", ["volume:/Volumes/cat/sch", "volume:/Workspace/Users/u",
                                 "workspace:/Volumes/c/s/v", "workspace:/Workspace"])
def test_remote_roots_must_have_the_right_shape(uri, tmp_path):
    with pytest.raises(StorageConfigError):
        open_backend(uri, base_dir=tmp_path, client=object())


def test_workspace_api_paths_drop_the_workspace_prefix(fake, tmp_path):
    backend = open_backend(WS_URI, base_dir=tmp_path, client=fake)
    backend.write_bytes("a.json", b"{}")
    assert ("upload", "/Users/u/shared/a.json") in fake.ws.calls
    assert backend.uri("a.json") == "workspace:/Workspace/Users/u/shared/a.json"


def test_remote_backend_without_a_client_names_the_remedy(tmp_path):
    backend = open_backend(VOL_URI, base_dir=tmp_path)
    with pytest.raises(StorageConfigError, match="databricks"):
        backend.list()


# -- role stores ------------------------------------------------------------------

def test_default_storage_is_the_pre_m8_local_layout():
    config = load_config(REPO / "config" / "config.yaml")
    stores = open_storage(config, REPO, env={})
    assert stores.inputs.workdir == REPO / "inputs"
    assert stores.state.workdir == REPO / "ui" / "backend" / "state"
    assert stores.outputs.workdir == REPO / config.output.dir
    assert all(s.is_local for s in (stores.inputs, stores.state, stores.outputs))
    assert stores.extra_inputs == []


def test_env_overrides_and_remote_working_copies(fake, tmp_path):
    config = load_config(REPO / "config" / "config.yaml")
    env = {"CODEGEN_STORAGE_INPUTS": WS_URI + "/inputs", "CODEGEN_STORAGE_OUTPUTS": VOL_URI,
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
           "CODEGEN_EXTRA_INPUT_DIRS":
               "/Workspace/Users/u/shared/pairs;volume:/Volumes/cat/sch/vol"}
    stores = open_storage(config, REPO, env=env, client=fake)
    assert isinstance(stores.inputs.backend, WorkspaceBackend)
    assert isinstance(stores.outputs.backend, VolumeBackend)
    assert [s.uri() for s in stores.extra_inputs] == [
        "workspace:/Workspace/Users/u/shared/pairs", "volume:/Volumes/cat/sch/vol"]
    # write-through leaves a working copy; fetch re-downloads; push_tree uploads
    local = stores.inputs.write_bytes("uploads/a.xlsx", b"wb")
    assert local.read_bytes() == b"wb" and tmp_path in local.parents
    assert fake.ws.files["/Users/u/shared/inputs/uploads/a.xlsx"] == b"wb"
    local.unlink()
    assert stores.inputs.fetch("uploads/a.xlsx").read_bytes() == b"wb"
    run = stores.outputs.local_path("demo_1/feed")
    run.mkdir(parents=True)
    (run / "README.md").write_bytes(b"# r")
    assert stores.outputs.push_tree("demo_1") == ["demo_1/feed/README.md"]
    assert fake.vol.files["/Volumes/cat/sch/vol/demo_1/feed/README.md"] == b"# r"


# -- the rule: src/ never treats /Volumes or /Workspace as a filesystem -------------

_MOUNT_AS_PATH = re.compile(
    r"""(Path|open|os\.(makedirs|listdir|mkdir))\(\s*f?["']/(Volumes|Workspace)""")


def test_src_never_opens_a_databricks_mount_as_a_path():
    offenders = [f"{p.relative_to(REPO)}:{n}"
                 for root in ("src", "ui/backend")
                 for p in sorted((REPO / root).rglob("*.py"))
                 for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                 if _MOUNT_AS_PATH.search(line)]
    assert offenders == []


def test_layout_cache_paths_may_not_be_databricks_mounts():
    from pydantic import ValidationError

    from codegen.config import LayoutConfig

    with pytest.raises(ValidationError, match="storage.state"):
        LayoutConfig(runtime_cache_dir="/Volumes/cat/sch/vol/state/layout_profiles")


_CV_PAIR = (REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json",
            REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json")


@pytest.mark.skipif(not all(p.is_file() for p in _CV_PAIR),
                    reason="demo fixture pair not restored (removed 2026-08-22)")
def test_cli_generate_lands_in_the_outputs_role(tmp_path, monkeypatch, capsys):
    from codegen import cli

    role = tmp_path / "outputs_role"
    role.mkdir()
    monkeypatch.chdir(REPO)
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{role.as_posix()}")
    assert cli.main(["generate", "--frd-contract", str(_CV_PAIR[0]), "--sttm-contract",
                     str(_CV_PAIR[1]), "--feed", "cv_individual_risk", "--dry-run",
                     "--skip-tests"]) == 0
    capsys.readouterr()
    assert (role / "cv_individual_risk" / "README.md").is_file()
    assert (role / "reports" / "cv_individual_risk.md").is_file()
