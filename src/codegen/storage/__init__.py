"""codegen.storage — where inputs, state and outputs live (M8.1).

One interface (``StorageBackend``: list, read_bytes, write_bytes, exists,
mkdir-below-the-root) and three backends selected by URI:

    local:./inputs                                   a directory on disk (default)
    workspace:/Workspace/Users/<user>/<folder>       Workspace API (databricks-sdk)
    volume:/Volumes/<catalog>/<schema>/<volume>/…    UC Volumes via the Files API

Config ``storage.inputs`` / ``storage.state`` / ``storage.outputs`` (env
``CODEGEN_STORAGE_INPUTS`` / ``_STATE`` / ``_OUTPUTS`` win) pick one per
role; ``inputs.extra_dirs`` adds read-only input roots (M8.2).

Position in the pipeline: the same EDGE as the SharePoint and volumes seams.
The extractors, the resolver, the emitter and the gate keep reading and
writing LOCAL files — a ``RoleStore`` pairs a backend with a local working
directory: ``fetch`` brings a document down before it is read, ``push`` /
``push_tree`` send results up after they are written. For a ``local:``
backend the working directory IS the root and both are no-ops, which is
what keeps every pre-M8 behaviour and byte-compared baseline unchanged.
Nothing in here is imported by resolve / rules / reasoning / emit / gate.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from codegen.storage.base import (
    StorageBackend,
    StorageConfigError,
    StorageEntry,
    StorageError,
    StorageNotFound,
    clean_rel,
)
from codegen.storage.local import LocalBackend, refuse_remote_root
from codegen.storage.remote import VolumeBackend, WorkspaceBackend

__all__ = [
    "DEFAULT_URIS", "ENV_OVERRIDES", "LocalBackend", "RoleStore", "StorageBackend",
    "StorageConfigError", "StorageEntry", "StorageError", "StorageNotFound", "StorageSet",
    "VolumeBackend", "WorkspaceBackend", "clean_rel", "open_backend", "open_storage",
    "parse_uri", "runtime_layout_cache",
]

SCHEMES = ("local", "workspace", "volume")
ROLES = ("inputs", "state", "outputs")
DEFAULT_URIS = {"inputs": "local:./inputs", "state": "local:./ui/backend/state"}
ENV_OVERRIDES = {role: f"CODEGEN_STORAGE_{role.upper()}" for role in ROLES}
EXTRA_INPUTS_ENV = "CODEGEN_EXTRA_INPUT_DIRS"


def parse_uri(uri: str) -> tuple[str, str]:
    """``scheme:root`` → (scheme, root). A bare path is refused: the scheme
    is what says whether ``/Workspace/…`` means an API or a mount."""
    text = (uri or "").strip()
    scheme, sep, root = text.partition(":")
    if not sep or scheme not in SCHEMES or not root.strip():
        raise StorageConfigError(
            f"storage URI {uri!r} is not <scheme>:<root> with scheme in {SCHEMES} — e.g. "
            "local:./inputs, workspace:/Workspace/Users/<user>/codegen/inputs, "
            "volume:/Volumes/<catalog>/<schema>/<volume>/inputs")
    return scheme, root.strip()


def open_backend(uri: str, *, base_dir: Path, client=None,
                 client_factory: Callable | None = None,
                 create_root: bool | None = None) -> StorageBackend:
    scheme, root = parse_uri(uri)
    if scheme == "local":
        refuse_remote_root(root)
        path = Path(root)
        if path.is_absolute():
            return LocalBackend(path, create_root=bool(create_root))
        # Relative = inside the checkout: the one place a root may be created.
        return LocalBackend(Path(base_dir) / path,
                            create_root=True if create_root is None else create_root,
                            display=path.as_posix())
    backend_cls = WorkspaceBackend if scheme == "workspace" else VolumeBackend
    return backend_cls(root, client=client, client_factory=client_factory)


class RoleStore:
    """A backend plus the local working directory the generator reads and
    writes. Local backend: the working directory is the root (zero copies).
    Remote backend: a scratch directory, filled by ``fetch`` and drained by
    ``push`` — local temp space, recreated freely, never the record."""

    def __init__(self, role: str, backend: StorageBackend, workdir: Path):
        self.role = role
        self.backend = backend
        self.workdir = Path(workdir)

    @property
    def is_local(self) -> bool:
        return self.backend.is_local

    def uri(self, rel: str = "") -> str:
        return self.backend.uri(rel)

    def local_path(self, rel: str = "") -> Path:
        rel = clean_rel(rel)
        return self.workdir / rel if rel else self.workdir

    # -- the five operations, passed through --------------------------------

    def list(self, rel: str = "") -> list[StorageEntry]:
        return self.backend.list(rel)

    def exists(self, rel: str = "") -> bool:
        return self.backend.exists(rel)

    def read_bytes(self, rel: str) -> bytes:
        return self.backend.read_bytes(rel)

    def mkdir(self, rel: str) -> Path:
        self.backend.mkdir(rel)
        target = self.local_path(rel)
        if not self.is_local:
            target.mkdir(parents=True, exist_ok=True)     # scratch space only
        return target

    def write_bytes(self, rel: str, data: bytes) -> Path:
        """Write through the backend AND leave the working copy in place."""
        self.backend.write_bytes(rel, data)
        target = self.local_path(rel)
        if not self.is_local:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return target

    # -- working copies -------------------------------------------------------

    def fetch(self, rel: str, size: int | None = None) -> Path:
        """The document as a local file (downloaded for a remote backend; a
        working copy whose size equals the listed ``size`` is reused)."""
        target = self.local_path(rel)
        if self.is_local:
            if not target.is_file():
                raise StorageNotFound(f"{self.uri(rel)} does not exist")
            return target
        if size is not None and target.is_file() and target.stat().st_size == size:
            return target
        data = self.backend.read_bytes(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def fetch_tree(self, rel: str = "", depth: int | None = None) -> Path:
        if not self.is_local:
            for child, _entry in self.backend.walk(rel, depth):
                self.fetch(child)
        return self.local_path(rel)

    def push(self, rel: str) -> None:
        """Send one working-copy file up (no-op for a local backend)."""
        if not self.is_local:
            self.backend.write_bytes(rel, self.local_path(rel).read_bytes())

    def push_tree(self, rel: str = "") -> list[str]:
        """Send every file under the working directory's ``rel`` up; the list
        of relative paths sent (empty for a local backend: already there)."""
        if self.is_local:
            return []
        base = self.local_path(rel)
        sent = []
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            child = path.relative_to(self.workdir).as_posix()
            self.backend.write_bytes(child, path.read_bytes())
            sent.append(child)
        return sent


@dataclass
class StorageSet:
    inputs: RoleStore
    state: RoleStore
    outputs: RoleStore
    extra_inputs: list[RoleStore] = field(default_factory=list)

    def describe(self) -> dict[str, object]:
        return {"inputs": self.inputs.uri(), "state": self.state.uri(),
                "outputs": self.outputs.uri(),
                "extra_inputs": [s.uri() for s in self.extra_inputs]}


def default_client_factory(config) -> Callable:
    """The seam's one client builder (``codegen.databricks._client``): the
    App's ambient service principal / a notebook's own auth when
    ``DATABRICKS_HOST`` is set, else the named CLI profile."""

    def factory():
        from types import SimpleNamespace

        from codegen import databricks as seam

        settings = getattr(config, "databricks", None)
        profile = (os.environ.get("DATABRICKS_PROFILE")
                   or os.environ.get("DATABRICKS_CONFIG_PROFILE")
                   or getattr(settings, "profile", "") or "DEFAULT")
        return seam._client(SimpleNamespace(profile=profile))

    return factory


def _scratch_root(config, env: Mapping[str, str]) -> Path:
    configured = env.get("CODEGEN_STORAGE_SCRATCH") or getattr(
        getattr(config, "storage", None), "scratch_dir", None)
    return Path(configured) if configured else Path(tempfile.gettempdir()) / "codegen_storage"


def _workdir(backend: StorageBackend, scratch: Path, role: str) -> Path:
    if isinstance(backend, LocalBackend):
        return backend.path
    digest = hashlib.sha256(backend.uri().encode("utf-8")).hexdigest()[:12]
    return scratch / f"{role}_{digest}"


def extra_input_uris(config, env: Mapping[str, str]) -> list[str]:
    """``inputs.extra_dirs`` then ``CODEGEN_EXTRA_INPUT_DIRS`` (';'- or
    newline-separated URIs; a bare ``/Workspace/…`` or ``/Volumes/…`` entry
    — the pre-M8 form — is read as the matching remote scheme, any other
    bare path as ``local:``)."""
    uris = list(getattr(getattr(config, "inputs", None), "extra_dirs", []) or [])
    raw = env.get(EXTRA_INPUTS_ENV, "")
    for entry in raw.replace("\n", ";").split(";"):
        entry = entry.strip()
        if not entry:
            continue
        if entry.partition(":")[0] not in SCHEMES:
            normalized = entry.replace("\\", "/")
            if normalized.startswith("/Workspace/"):
                entry = f"workspace:{normalized}"
            elif normalized.startswith("/Volumes/"):
                entry = f"volume:{normalized}"
            else:
                entry = f"local:{entry}"
        uris.append(entry)
    return list(dict.fromkeys(uris))


def runtime_layout_cache(config, base_dir: Path, *, stores: StorageSet | None = None,
                         env: Mapping[str, str] | None = None
                         ) -> tuple[Path, Callable[[], list[str]]]:
    """(local directory, push) for the RUNTIME layout-profile cache. Under the
    default state role that is ``layout.runtime_cache_dir`` inside the
    checkout and ``push`` does nothing; otherwise the cache lives in the
    state role at ``layout_profiles/`` — pulled now, pushed by ``push()``."""
    env = os.environ if env is None else env
    stores = stores or open_storage(config, base_dir, env=env)
    state = stores.state
    default = Path(base_dir) / Path(DEFAULT_URIS["state"].partition(":")[2])
    if state.is_local and state.workdir == default:
        return Path(base_dir) / config.layout.runtime_cache_dir, lambda: []
    state.fetch_tree("layout_profiles")

    def push() -> list[str]:
        if not state.local_path("layout_profiles").is_dir():
            return []
        return state.push_tree("layout_profiles")

    return state.local_path("layout_profiles"), push


def open_storage(config, base_dir: Path, *, env: Mapping[str, str] | None = None,
                 client=None, client_factory: Callable | None = None) -> StorageSet:
    """The three role stores + the extra input roots for this config / env."""
    env = os.environ if env is None else env
    section = getattr(config, "storage", None)
    factory = client_factory or default_client_factory(config)
    scratch = _scratch_root(config, env)
    # A config without an `output:` section (a test stub) still gets ./out.
    output_dir = Path(getattr(getattr(config, "output", None), "dir", "out")).as_posix()

    def role_uri(role: str) -> str:
        override = env.get(ENV_OVERRIDES[role], "").strip()
        if override:
            return override
        configured = getattr(section, role, None)
        if configured:
            return configured
        if role == "outputs":
            # No storage.outputs: the generator's own output.dir, created on
            # demand exactly as before M8 (absolute in tests, ./out in the repo).
            return "local:" + output_dir
        return DEFAULT_URIS[role]

    def store(role: str, uri: str) -> RoleStore:
        derived = role == "outputs" and uri == "local:" + output_dir
        backend = open_backend(uri, base_dir=base_dir, client=client, client_factory=factory,
                               create_root=True if derived else None)
        return RoleStore(role, backend, _workdir(backend, scratch, role))

    return StorageSet(
        inputs=store("inputs", role_uri("inputs")),
        state=store("state", role_uri("state")),
        outputs=store("outputs", role_uri("outputs")),
        extra_inputs=[store("extra_inputs", uri) for uri in extra_input_uris(config, env)],
    )
