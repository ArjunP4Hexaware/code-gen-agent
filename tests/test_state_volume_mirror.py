"""post72: CODEGEN_STATE_DIR on a UC volume. A Databricks App has no /Volumes
mount, so the state folder is copied read-only through the Files API
(``codegen.state_mirror``) and the resolver reads the copy; the state line
names the volume and the copy; a refresh picks up an edit on the volume, a
failed one keeps the previous copy. The Files API is the in-memory fake."""
from __future__ import annotations

import stat
from pathlib import Path

import pytest

from codegen import config as config_module
from codegen import state_mirror
from codegen.config import active_defaults, last_applied_overlays, load_config, state_root
from codegen.environments import profiles_dir, resolve, state_dirs_line
from storage_fakes import FakeWorkspaceClient, PermissionDenied

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"
VOLUME = "/Volumes/cat/sch/vol"
STATE = f"{VOLUME}/state"
ACCOUNT = "synacct01"
WRITES = {"upload", "mkdir", "delete", "delete_directory"}


@pytest.fixture
def volume(tmp_path, monkeypatch):
    """A fake volume holding a state folder; CODEGEN_STATE_DIR names it and
    the copies go under tmp_path. The suite's own folder variables removed."""
    monkeypatch.delenv("CODEGEN_ENVIRONMENTS_DIR", raising=False)
    monkeypatch.delenv("CODEGEN_STATE_OVERLAYS_DIR", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_DIR", STATE)
    monkeypatch.setenv(state_mirror.MIRROR_DIR_ENV, str(tmp_path / "mirror"))
    monkeypatch.setattr(state_mirror, "_status", None)
    monkeypatch.setattr(config_module, "_STATE_MIRRORS", {})
    fake = FakeWorkspaceClient(volume_root=VOLUME)
    fake.vol.dirs |= {STATE, f"{STATE}/environments", f"{STATE}/overlays"}
    fake.vol.files[f"{STATE}/environments/d1.yaml"] = f"storage_account: {ACCOUNT}\n".encode()
    profile = active_defaults(CONFIG)["profile"]
    fake.vol.files[f"{STATE}/overlays/{profile}.yaml"] = (
        b"metadata:\n  templates:\n    iig_v2:\n      email_status_default: [Success, Failed]\n")
    return fake


def _volume_writes(fake) -> list:
    return [call for call in fake.vol.calls if call[0] in WRITES]


def test_the_volume_is_copied_read_only_and_the_resolver_reads_the_copy(volume):
    result = state_mirror.refresh(client=volume)
    assert result.error is None and result.files == 2 and result.changed
    assert state_root() == result.local
    assert (profiles_dir() / "d1.yaml").read_text(encoding="utf-8").strip().endswith(ACCOUNT)
    copied = profiles_dir() / "d1.yaml"
    assert not copied.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    assert _volume_writes(volume) == []                       # never a write to the volume


def test_the_state_line_names_the_volume_and_the_local_copy(volume):
    state_mirror.refresh(client=volume)
    line = state_dirs_line()
    assert line.startswith(f"codegen-state root: {STATE} (CODEGEN_STATE_DIR; volume) -> "
                           "local copy ")
    assert "(2 files, copied " in line
    assert "[MISSING]" not in line
    assert f"environments {STATE}/environments" in line      # shown as the volume path


def test_the_storage_account_comes_from_the_volume_profile(volume):
    state_mirror.refresh(client=volume)
    config = load_config(CONFIG, overlays=[ACFC_OVERLAY])
    env = resolve(config)
    assert env.entry.storage_account == ACCOUNT
    assert env.sources["storage_account"] == f"profile {STATE}/environments/d1.yaml"


def test_the_volume_overlay_is_applied(volume):
    state_mirror.refresh(client=volume)
    config = load_config(CONFIG)
    profile = active_defaults(CONFIG)["profile"]
    assert any(Path(p).name == f"{profile}.yaml" for p in last_applied_overlays())
    assert config.metadata.templates["iig_v2"].email_status_default == ["Success", "Failed"]


def test_an_edit_on_the_volume_shows_after_a_refresh(volume):
    first = state_mirror.refresh(client=volume)
    again = state_mirror.refresh(client=volume)
    assert not again.changed and again.digest == first.digest
    volume.vol.files[f"{STATE}/environments/d1.yaml"] = b"storage_account: synacct02\n"
    edited = state_mirror.refresh(client=volume)
    assert edited.changed and edited.digest != first.digest
    assert (profiles_dir() / "d1.yaml").read_text(encoding="utf-8").strip().endswith("synacct02")
    copies = [p.name for p in state_mirror.mirror_base().iterdir() if p.name.startswith("gen-")]
    assert len(copies) == 2                                   # the new copy + the one replaced


def test_a_failed_first_copy_leaves_the_volume_path_missing(volume, monkeypatch):
    def denied(path):
        raise PermissionDenied(f"no READ VOLUME on {path}")

    monkeypatch.setattr(volume.files, "list_directory_contents", denied)
    monkeypatch.setattr(volume.files, "get_directory_metadata", denied)
    result = state_mirror.refresh(client=volume)
    assert result.error and result.local is None
    assert state_root() == Path(STATE)
    line = state_dirs_line()
    assert ("last refresh FAILED (StorageError <- PermissionDenied, error code "
            "PERMISSION_DENIED)") in line and "no copy [MISSING]" in line
    assert "no READ VOLUME" not in line                       # never the SDK's message


def test_a_failed_refresh_keeps_the_previous_copy(volume, monkeypatch):
    first = state_mirror.refresh(client=volume)

    def denied(path):
        raise PermissionDenied("grant revoked")

    monkeypatch.setattr(volume.files, "download", denied)
    later = state_mirror.refresh(client=volume)
    assert later.error and later.local == first.local and not later.changed
    assert state_root() == first.local
    assert "the previous copy stays in effect" in state_dirs_line()


def test_a_missing_state_folder_is_an_error_not_an_empty_copy(volume):
    volume.vol.dirs -= {STATE, f"{STATE}/environments", f"{STATE}/overlays"}
    volume.vol.files.clear()
    result = state_mirror.refresh(client=volume)
    assert result.local is None
    assert result.error == "StateDirNotFound, error code STATE_DIR_NOT_FOUND"


def test_a_local_or_unset_state_dir_is_not_copied(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mirror, "_status", None)
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(tmp_path))
    assert state_mirror.refresh(client=FakeWorkspaceClient()) is None
    monkeypatch.delenv("CODEGEN_STATE_DIR")
    assert state_mirror.refresh(client=FakeWorkspaceClient()) is None
    assert state_mirror.describe() is None


def test_a_generate_request_refreshes_and_reloads_the_config(volume, monkeypatch):
    pytest.importorskip("fastapi")
    from types import SimpleNamespace

    from ui.backend import main

    real_refresh = state_mirror.refresh
    monkeypatch.setattr(state_mirror, "refresh", lambda **kw: real_refresh(client=volume))
    holder = SimpleNamespace(config=None)
    monkeypatch.setattr(main, "store", holder)
    main._refresh_state()
    assert holder.config is not None                          # changed: config reloaded
    holder.config = None
    main._refresh_state()
    assert holder.config is None                              # unchanged: not reloaded


def test_the_sdk_config_dump_never_reaches_the_state_line(volume, monkeypatch):
    def forbidden(path):
        raise PermissionDenied("Forbidden. Config: host=https://syn.example, "
                               "client_id=00000000-syn, auth_type=oauth-m2m")

    monkeypatch.setattr(volume.files, "get_metadata", forbidden)
    monkeypatch.setattr(volume.files, "get_directory_metadata", forbidden)
    state_mirror.refresh(client=volume)
    line = state_dirs_line()
    assert "error code PERMISSION_DENIED" in line
    for leaked in ("Config:", "host=", "client_id", "auth_type", "syn.example"):
        assert leaked not in line


def test_a_workspace_folder_state_dir_is_copied_the_same_way(tmp_path, monkeypatch):
    """post81: CODEGEN_STATE_DIR=/Workspace/... is copied through the Workspace API
    (no Unity Catalog grant needed): the environment profile's storage account
    reaches the resolver, nothing is written to the folder."""
    folder = "/Users/u/shared/codegen-state"
    monkeypatch.delenv("CODEGEN_ENVIRONMENTS_DIR", raising=False)
    monkeypatch.delenv("CODEGEN_STATE_OVERLAYS_DIR", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_DIR", f"/Workspace{folder}")
    monkeypatch.setenv(state_mirror.MIRROR_DIR_ENV, str(tmp_path / "mirror"))
    monkeypatch.setattr(state_mirror, "_status", None)
    monkeypatch.setattr(config_module, "_STATE_MIRRORS", {})
    fake = FakeWorkspaceClient()
    fake.ws.dirs |= {folder, f"{folder}/environments"}
    fake.ws.files[f"{folder}/environments/d1.yaml"] = f"storage_account: {ACCOUNT}\n".encode()
    result = state_mirror.refresh(client=fake)
    assert result.error is None and result.files == 1
    assert state_root() == result.local
    env = resolve(load_config(CONFIG, overlays=[ACFC_OVERLAY]))
    assert env.entry.storage_account == ACCOUNT
    assert "(CODEGEN_STATE_DIR; workspace folder)" in state_dirs_line()
    assert [c for c in fake.ws.calls if c[0] in WRITES] == []
