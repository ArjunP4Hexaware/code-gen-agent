"""Feedback on the App itself: bug reports and suggestions, with screenshots (post215).

Ported from the STTM agent's App (its Feedback section, C46, itself from the Code Review
agent's C31) - the same shape, our storage roles and our words. A signed-in user sends a
bug report or a suggestion with a title, details, optionally one of this App's runs, and
up to MAX_IMAGES screenshots. People see their own submissions and their status; the
feedback admins see everyone's and set the status.

Who is signed in: the Databricks Apps proxy's ``x-forwarded-email`` header (then its
preferred-username / user headers); none = ``local`` (a local App). The admins: one
address per line in the STATE root's ``feedback_admins.txt`` (Soham, 2026-11-20: never in
git - the addresses carry the client's domain), compared case-insensitively; no file =
no admins.

Nothing here reaches a model or a run: feedback is stored for people to read.

Storage, in the OUTPUTS role beside the run folders (through ``RoleStore`` like every
other durable file, so local / Workspace / volume alike; "Clear past runs" deletes only
``demo_*`` folders, never these):

    app_feedback/<sub_id>/submission.json   the submission, its status and status history
    app_feedback/<sub_id>/img_<n>.<ext>     its screenshots (PNG, JPEG, GIF or WebP, from the bytes)

Nothing deletes a submission.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from codegen.storage import StorageError, StorageNotFound

ROOT = "app_feedback"
ADMINS_FILE = "feedback_admins.txt"
SUB_ID_RE = re.compile(r"^fb_\d{8}_\d{6}_[0-9a-f]{6}$")
IMAGE_NAME_RE = re.compile(r"^img_\d\.(png|jpg|gif|webp)$")
RUN_RE = re.compile(r"^demo_\d{8}_\d{6}$")
KINDS = ("bug", "suggestion")
STATUSES = ("new", "in_progress", "done", "declined")
MAX_IMAGES = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_TITLE, MAX_TEXT = 200, 10_000
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
USER_HEADERS = ("x-forwarded-email", "x-forwarded-preferred-username", "x-forwarded-user")
LOCAL_USER = "local"


class FeedbackError(ValueError):
    """A submission or request that can't be saved as given (the message is for the user)."""


# ---------------------------------------------------------------- who and the admins

def who(request: Request) -> str:
    """The signed-in user as the Apps proxy names them; ``local`` without the proxy."""
    for header in USER_HEADERS:
        value = (request.headers.get(header) or "").strip()
        if value:
            return value
    return LOCAL_USER


def same_user(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def admins(stores) -> set[str]:
    """The feedback admins (lower case) from the state root's ``feedback_admins.txt``: one
    address per line, ``#`` starts a comment; no file (or an unreadable one) = none."""
    try:
        raw = stores.state.read_bytes(ADMINS_FILE)
    except (StorageError, OSError):
        return set()
    out = set()
    for line in raw.decode("utf-8", errors="replace").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            out.add(line)
    return out


# ---------------------------------------------------------------- the store

def image_ext(data: bytes) -> str | None:
    """The image type from its first bytes (never from a file name or a claimed type)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _check_sub_id(sub_id: str) -> None:
    if not SUB_ID_RE.match(sub_id or ""):
        raise FeedbackError("Bad submission id")


def _put(outputs, sub: dict) -> None:
    outputs.write_bytes(f"{ROOT}/{sub['sub_id']}/submission.json",
                        json.dumps(sub, indent=2, ensure_ascii=False).encode("utf-8"))


def new(outputs, user: str, kind: str, title: str, text: str, images: list[bytes],
        run: str | None = None) -> dict:
    """Save a bug report or suggestion with up to MAX_IMAGES screenshots - every check
    here, not in the caller."""
    if kind not in KINDS:
        raise FeedbackError(f"The type must be one of {', '.join(KINDS)}.")
    title, text = (title or "").strip(), (text or "").strip()
    if not title or not text:
        raise FeedbackError("A title and some details are required.")
    if run is not None and not RUN_RE.match(run):
        raise FeedbackError("Bad run name")
    if len(images) > MAX_IMAGES:
        raise FeedbackError(f"At most {MAX_IMAGES} screenshots.")
    names = []
    for index, data in enumerate(images, start=1):
        ext = image_ext(data)
        if ext is None:
            raise FeedbackError(f"Screenshot {index} is not a PNG, JPEG, GIF or WebP image.")
        if len(data) > MAX_IMAGE_BYTES:
            raise FeedbackError(f"Screenshot {index} is over "
                                f"{MAX_IMAGE_BYTES // (1024 * 1024)} MB.")
        names.append(f"img_{index}.{ext}")
    sub_id = datetime.now(timezone.utc).strftime("fb_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    for name, data in zip(names, images, strict=True):
        outputs.write_bytes(f"{ROOT}/{sub_id}/{name}", data)
    sub = {"sub_id": sub_id, "created_at": _now(), "user": user, "kind": kind,
           "title": title[:MAX_TITLE], "text": text[:MAX_TEXT], "run": run, "images": names,
           "status": "new", "status_history": [{"status": "new", "by": user, "at": _now()}]}
    _put(outputs, sub)          # written last: a submission exists once its submission.json does
    return sub


def get(outputs, sub_id: str) -> dict | None:
    _check_sub_id(sub_id)
    try:
        raw = outputs.read_bytes(f"{ROOT}/{sub_id}/submission.json")
    except (StorageNotFound, FileNotFoundError):
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return None


def list_for(outputs, user: str | None = None, limit: int = 200) -> list[dict]:
    """Newest first: one user's submissions (case-insensitive), or everyone's (None)."""
    out = []
    try:
        entries = outputs.list(ROOT)
    except (StorageNotFound, FileNotFoundError):
        return []
    for sub_id in sorted((e.name for e in entries if e.is_dir), reverse=True):
        if not SUB_ID_RE.match(sub_id):
            continue
        sub = get(outputs, sub_id)
        if sub and (user is None or same_user(sub.get("user"), user)):
            out.append(sub)
            if len(out) >= limit:
                break
    return out


def image(outputs, sub_id: str, name: str) -> bytes | None:
    _check_sub_id(sub_id)
    if not IMAGE_NAME_RE.match(name or ""):
        raise FeedbackError("Bad image name")
    try:
        return outputs.read_bytes(f"{ROOT}/{sub_id}/{name}")
    except (StorageNotFound, FileNotFoundError):
        return None


def set_status(outputs, sub_id: str, status: str, by: str) -> dict:
    if status not in STATUSES:
        raise FeedbackError(f"The status must be one of {', '.join(STATUSES)}.")
    sub = get(outputs, sub_id)
    if sub is None:
        raise FeedbackError("No such submission")
    sub["status"] = status
    sub.setdefault("status_history", []).append({"status": status, "by": by, "at": _now()})
    _put(outputs, sub)
    return sub


def view(sub: dict) -> dict:
    """What the API returns for a submission."""
    return {k: sub.get(k) for k in ("sub_id", "created_at", "user", "kind", "title", "text",
                                    "run", "images", "status", "status_history")}


# ---------------------------------------------------------------- the routes

router = APIRouter()


class FeedbackImage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: str = Field(..., min_length=8, max_length=7_200_000)   # base64 / a data URL, <= 5 MB


class FeedbackSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., pattern=r"^(bug|suggestion)$")
    title: str = Field(..., min_length=1, max_length=MAX_TITLE)
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    run: str | None = Field(None, pattern=RUN_RE.pattern)
    images: list[FeedbackImage] = Field(default_factory=list, max_length=MAX_IMAGES)


class FeedbackStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern=r"^(new|in_progress|done|declined)$")


def _stores():
    from ui.backend import main, stores

    return stores.get_stores(main._require_store().config)


def _run_names() -> list[str]:
    from ui.backend import main, stores

    return stores.run_labels(main._require_store().config)


def _readable(outputs, sub_id: str, user: str, is_admin: bool) -> dict:
    try:
        sub = get(outputs, sub_id)
    except FeedbackError as exc:
        raise HTTPException(400, str(exc)) from exc
    if sub is None:
        raise HTTPException(404, "Feedback not found")
    if not same_user(sub.get("user"), user) and not is_admin:
        raise HTTPException(403, "You can only open your own feedback.")
    return sub


@router.get("/api/feedback/runs")
def feedback_runs() -> dict:
    """This App's runs (folder names = their start time), newest first, for the form's
    "Related run"."""
    try:
        return {"runs": _run_names()}
    except Exception as exc:  # noqa: BLE001 - a remote listing error is a 502
        raise HTTPException(502, f"could not list the runs: {exc}") from exc


@router.post("/api/feedback", status_code=201)
def submit_feedback(body: FeedbackSubmission, request: Request) -> dict:
    """A bug report or suggestion, with up to MAX_IMAGES screenshots sent base64 in JSON."""
    stores = _stores()
    user = who(request)
    if body.run is not None and body.run not in _run_names():
        raise HTTPException(404, f"No such run on this App: {body.run}")
    try:
        images = [base64.b64decode(i.data.split(",", 1)[-1], validate=True) for i in body.images]
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(400, "A screenshot could not be read (bad base64).") from exc
    try:
        return view(new(stores.outputs, user, body.kind, body.title, body.text, images,
                        body.run))
    except FeedbackError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/api/feedback")
def list_feedback(request: Request, all: bool = False) -> dict:  # noqa: A002 - the API's word
    """Your submissions; with all=true (feedback admins only), everyone's."""
    stores = _stores()
    user = who(request)
    is_admin = user.lower() in admins(stores)
    if all and not is_admin:
        raise HTTPException(403, "Only feedback admins can see everyone's feedback.")
    subs = list_for(stores.outputs, None if all else user)
    return {"user": user, "is_admin": is_admin, "all": all, "items": [view(s) for s in subs]}


@router.get("/api/feedback/{sub_id}/images/{name}")
def feedback_image(sub_id: str, name: str, request: Request) -> Response:
    stores = _stores()
    user = who(request)
    _readable(stores.outputs, sub_id, user, user.lower() in admins(stores))
    try:
        data = image(stores.outputs, sub_id, name)
    except FeedbackError as exc:
        raise HTTPException(400, str(exc)) from exc
    if data is None:
        raise HTTPException(404, "Screenshot not found")
    return Response(data, media_type=IMAGE_TYPES[name.rsplit(".", 1)[1]],
                    headers={"X-Content-Type-Options": "nosniff",
                             "Cache-Control": "private, max-age=3600",
                             "Content-Security-Policy": "default-src 'none'"})


@router.post("/api/feedback/{sub_id}/status")
def set_feedback_status(sub_id: str, body: FeedbackStatus, request: Request) -> dict:
    stores = _stores()
    user = who(request)
    if user.lower() not in admins(stores):
        raise HTTPException(403, "Only feedback admins can change the status.")
    _readable(stores.outputs, sub_id, user, True)
    try:
        return view(set_status(stores.outputs, sub_id, body.status, user))
    except FeedbackError as exc:
        raise HTTPException(400, str(exc)) from exc


__all__ = ["router", "who", "admins", "new", "get", "list_for", "image", "set_status",
           "view", "FeedbackError"]
