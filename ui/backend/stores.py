"""The UI backend's storage roles (M8.1): inputs / state / outputs + the
extra input roots, opened once from the store's config and the environment.

Every route and the runner resolve their directories here. With the default
(local) roles each helper returns exactly the pre-M8 path — the module
constants tests patch (``FETCH_DIR``, ``INPUTS_DIR``, ``DECISIONS_PATH``)
keep working — and the push / pull calls are no-ops. With a remote role the
path is the role's local working copy and the helper moves the bytes.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from codegen.storage import RoleStore, StorageNotFound, StorageSet, open_storage

REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_INPUTS = REPO_ROOT / "inputs"
_DEFAULT_STATE = Path(__file__).resolve().parent / "state"

_stores: StorageSet | None = None
_config = None      # the config object the stores were opened for (identity)


def get_stores(config) -> StorageSet:
    """The role stores for this config (rebuilt when the config object changes)."""
    global _stores, _config  # noqa: PLW0603 — one process-wide set, like the routes' store
    if _stores is None or _config is not config:
        _stores = open_storage(config, REPO_ROOT)
        _config = config
    return _stores


def reset_stores() -> None:
    global _stores, _config  # noqa: PLW0603
    _stores, _config = None, None


def _is_default(store: RoleStore, default: Path) -> bool:
    return store.is_local and store.workdir == default


def inbox_dir(config, sub: str, default: Path) -> Path:
    """Local directory an inbox (``sharepoint`` / ``databricks`` / ``uploads``)
    is written to: ``default`` under the default inputs role, else the inputs
    role's working copy of ``<sub>/``."""
    store = get_stores(config).inputs
    return default if _is_default(store, _DEFAULT_INPUTS) else store.local_path(sub)


def push_input(config, sub: str, name: str) -> None:
    """After a document landed in an inbox's local directory: send it up."""
    get_stores(config).inputs.push(f"{sub}/{name}")


def state_file(config, name: str, default: Path) -> Path:
    """Local path of a state file; a remote state role is pulled first."""
    store = get_stores(config).state
    if _is_default(store, _DEFAULT_STATE):
        return default
    if not store.is_local:
        with contextlib.suppress(StorageNotFound):     # first write creates it
            store.fetch(name)
    return store.local_path(name)


def state_is_default(config) -> bool:
    """True under the default (local, in-checkout) state role."""
    return _is_default(get_stores(config).state, _DEFAULT_STATE)


def push_state(config, name: str) -> None:
    store = get_stores(config).state
    if not _is_default(store, _DEFAULT_STATE):
        store.push(name)


def layout_cache_dir(config) -> Path:
    """The runtime layout-profile cache directory, pulled from a remote
    state role; ``layout.runtime_cache_dir`` under the default state role."""
    from codegen.storage import runtime_layout_cache

    return runtime_layout_cache(config, REPO_ROOT, stores=get_stores(config))[0]


def push_layout_cache(config) -> None:
    store = get_stores(config).state
    if not _is_default(store, _DEFAULT_STATE) and store.local_path("layout_profiles").is_dir():
        store.push_tree("layout_profiles")


def outputs_root(config) -> Path:
    """Local directory run folders are generated into."""
    return get_stores(config).outputs.workdir


def push_run(config, label: str) -> list[str]:
    return get_stores(config).outputs.push_tree(label)


def pull_run(config, label: str) -> Path:
    return get_stores(config).outputs.fetch_tree(label)


def remote_run_labels(config, prefix: str = "demo_") -> list[str]:
    """Run folders that exist only in a remote outputs role (a restarted App
    container lost its local copies); ``[]`` for a local role."""
    store = get_stores(config).outputs
    if store.is_local:
        return []
    return [e.name for e in store.list("") if e.is_dir and e.name.startswith(prefix)]
