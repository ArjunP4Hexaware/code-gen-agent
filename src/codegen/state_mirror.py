"""post72: ``CODEGEN_STATE_DIR`` on a Unity Catalog volume.

A Databricks App has no ``/Volumes`` mount (only the Files API reaches a
volume), so a ``CODEGEN_STATE_DIR=/Volumes/<catalog>/<schema>/<volume>[/…]``
that is not a local folder is COPIED, read-only, into
``<tmp>/codegen-state-volume/current`` through the Files API
(:class:`codegen.storage.remote.VolumeBackend`: list + download, never a
write to the volume), and :func:`codegen.config.state_root` answers the copy
for that value. Job compute that mounts ``/Volumes`` reads the folder as it
is — no copy.

:func:`refresh` runs at App startup (before the config is loaded, so the
volume's ``overlays/<profile>.yaml`` is applied) and again on every generate
request, so an edit on the volume shows without a redeploy. A copy is built
in its own folder (``gen-<content sha>``) and swapped in with one atomic
symlink rename — a run reading the state never sees a half-written copy. A
failed refresh keeps the previous copy (and says so on the state line); with
no copy at all the root stays the volume path, which the state line marks
``[MISSING]``.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from codegen.config import STATE_DIR_ENV, register_state_mirror

VOLUME_PREFIX = "/Volumes/"
MIRROR_DIR_ENV = "CODEGEN_STATE_MIRROR_DIR"     # where the copies go (default <tmp>)
CURRENT = "current"


@dataclass(frozen=True)
class MirrorStatus:
    """The last copy of the volume: where it is, how many files, its content
    digest; ``error`` = the last refresh's failure (the copy, if any, is the
    previous one)."""

    volume: str
    local: Path | None = None
    files: int = 0
    digest: str = ""
    copied_at: str = ""
    error: str | None = None
    changed: bool = False


_lock = threading.Lock()
_status: MirrorStatus | None = None


class StateDirNotFound(FileNotFoundError):
    """The volume folder is absent, or the principal cannot see it."""

    error_code = "STATE_DIR_NOT_FOUND"


def error_text(exc: BaseException) -> str:
    """post73: a refresh failure as exception types + error code ONLY — the
    SDK's message carries its config dump (host, client id, auth type), which
    must never reach the log or the state line."""
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    names = list(dict.fromkeys(type(e).__name__ for e in chain))
    code = next((str(e.error_code) for e in chain if getattr(e, "error_code", None)), None)
    return f"{' <- '.join(names)}, error code {code or 'none'}"


def volume_state_dir() -> str | None:
    """The ``CODEGEN_STATE_DIR`` value when it names a volume this process
    cannot read as a folder; None otherwise (unset, local, or mounted)."""
    value = (os.environ.get(STATE_DIR_ENV) or "").strip()
    if not value.startswith(VOLUME_PREFIX) or Path(value).is_dir():
        return None
    return value.rstrip("/")


def mirror_base() -> Path:
    return Path(os.environ.get(MIRROR_DIR_ENV) or tempfile.gettempdir()) / "codegen-state-volume"


def status() -> MirrorStatus | None:
    """The last refresh's outcome (None: no volume state dir, or never run)."""
    return _status


def _default_factory() -> Callable:
    from codegen.storage import default_client_factory

    return default_client_factory(None)


def _digest(files: dict[str, bytes]) -> str:
    sha = hashlib.sha256()
    for rel in sorted(files):
        sha.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(files[rel]).digest())
    return sha.hexdigest()


def _write_copy(base: Path, digest: str, files: dict[str, bytes]) -> Path:
    target = base / f"gen-{digest[:16]}"
    if not target.is_dir():
        staging = Path(tempfile.mkdtemp(prefix="staging-", dir=base))
        for rel, data in files.items():
            path = staging.joinpath(*rel.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)     # a read-only copy
        # the top-level folders the resolver looks for exist even when empty on the volume
        for folder in ("environments", "overlays"):
            (staging / folder).mkdir(exist_ok=True)
        staging.rename(target)
    link = base / CURRENT
    tmp_link = base / f".{CURRENT}-{os.getpid()}-{threading.get_ident()}"
    if tmp_link.is_symlink() or tmp_link.exists():
        tmp_link.unlink()
    tmp_link.symlink_to(target.name, target_is_directory=True)
    os.replace(tmp_link, link)                                       # atomic swap
    return target


def _prune(base: Path, keep: set[str]) -> None:
    """Every older copy but the one just replaced (a run may still read it)."""
    for child in base.iterdir():
        if child.name.startswith("gen-") and child.name not in keep:
            shutil.rmtree(child, ignore_errors=True)


def refresh(*, client=None, client_factory: Callable | None = None) -> MirrorStatus | None:
    """Copy the volume's state folder (every file below it) to the local
    mirror and point the state root at it. None when ``CODEGEN_STATE_DIR``
    is not an unmounted volume path. Never raises: a failure is the status's
    ``error`` and the previous copy stays in effect."""
    global _status
    from codegen.storage.remote import VolumeBackend

    volume = volume_state_dir()
    if volume is None:
        return None
    with _lock:
        previous = _status if _status is not None and _status.volume == volume else None
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            backend = VolumeBackend(volume, client=client,
                                    client_factory=client_factory or _default_factory())
            if not backend.exists():
                raise StateDirNotFound(volume)
            files = {rel: backend.read_bytes(rel) for rel, _entry in backend.walk()}
            digest = _digest(files)
            base = mirror_base()
            base.mkdir(parents=True, exist_ok=True)
            old = (base / CURRENT).resolve().name if (base / CURRENT).is_symlink() else ""
            target = _write_copy(base, digest, files)
            _prune(base, {target.name, old})
            local = base / CURRENT
            register_state_mirror(volume, local)
            _status = MirrorStatus(volume=volume, local=local, files=len(files), digest=digest,
                                   copied_at=now, changed=previous is None
                                   or previous.digest != digest)
        except Exception as exc:  # noqa: BLE001 — reported on the state line, never fatal
            error = error_text(exc)
            _status = (replace(previous, error=error, changed=False) if previous is not None
                       else MirrorStatus(volume=volume, error=error))
        return _status


def describe() -> str | None:
    """The state line's root part for a volume state dir: the volume, the
    local copy and how many files it holds (or why there is none)."""
    current = _status
    volume = volume_state_dir()
    if volume is None:
        return None
    if current is None or current.volume != volume:
        return f"{volume} ({STATE_DIR_ENV}; volume, not copied yet) [MISSING]"
    text = f"{volume} ({STATE_DIR_ENV}; volume)"
    if current.local is not None:
        text += (f" -> local copy {current.local.as_posix()} ({current.files} files, "
                 f"copied {current.copied_at})")
    if current.error:
        text += (f" — last refresh FAILED ({current.error}); "
                 + ("the previous copy stays in effect" if current.local is not None
                    else "no copy [MISSING]"))
    return text


def volume_display(path: Path) -> str | None:
    """A path inside the local copy as the volume path it was copied from
    (the picker's "profile /Volumes/…/environments/d1.yaml"); None otherwise."""
    current = _status
    if current is None or current.local is None:
        return None
    try:
        rel = Path(path).resolve().relative_to(current.local.resolve())
    except (OSError, ValueError):
        return None
    return f"{current.volume}/{rel.as_posix()}" if rel.parts else current.volume
