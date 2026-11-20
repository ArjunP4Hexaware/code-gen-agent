"""post215: feedback on the App - bug reports and suggestions with screenshots
(ui/backend/feedback.py, ported from the STTM agent's App; synthetic users only).

The outputs role holds the submissions (app_feedback/<id>/), the state root the admins
(feedback_admins.txt); the signed-in user comes from the Apps proxy's x-forwarded-email.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import feedback, main  # noqa: E402
from ui.backend import stores as ui_stores  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.storage import open_storage  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 32
SVG = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
ALICE = {"x-forwarded-email": "alice@example.com"}
BOB = {"x-forwarded-email": "bob@example.com"}
ADMIN = {"x-forwarded-email": "Boss@Example.com"}      # matched case-insensitively
RUN = "demo_20261120_100000"


def b64(data: bytes, data_url: bool = False) -> str:
    text = base64.b64encode(data).decode()
    return f"data:image/png;base64,{text}" if data_url else text


def _roles(monkeypatch, tmp_path, admins: str | None):
    outputs, state = tmp_path / "outputs", tmp_path / "state"
    (outputs / RUN).mkdir(parents=True)
    (outputs / "handoff").mkdir()                       # not a run folder: never offered
    state.mkdir()
    if admins is not None:
        (state / "feedback_admins.txt").write_text(admins, encoding="utf-8")
    env = {"CODEGEN_STORAGE_OUTPUTS": f"local:{outputs.as_posix()}",
           "CODEGEN_STORAGE_STATE": f"local:{state.as_posix()}"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env))
    ui_stores.reset_stores()
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    monkeypatch.setattr(main, "store", store)
    return outputs


@pytest.fixture
def app(monkeypatch, tmp_path):
    outputs = _roles(monkeypatch, tmp_path, "# feedback admins\n boss@example.com \n\n"
                                            "other@example.com  # a comment\n")
    yield {"client": TestClient(main.app), "root": outputs / "app_feedback"}
    ui_stores.reset_stores()


def _send(client, headers=ALICE, **kw):
    body = {"kind": "bug", "title": "Blank column", "text": "A column was left blank."}
    body.update(kw)
    return client.post("/api/feedback", json=body, headers=headers)


def test_image_types_come_from_the_bytes():
    assert [feedback.image_ext(x) for x in (PNG, JPG, GIF, WEBP)] == ["png", "jpg", "gif", "webp"]
    assert feedback.image_ext(SVG) is None
    assert feedback.image_ext(b"") is None


def test_submit_saves_the_submission_and_its_screenshots(app):
    reply = _send(app["client"], images=[{"data": b64(PNG)}, {"data": b64(JPG, data_url=True)}],
                  run=RUN)
    assert reply.status_code == 201, reply.text
    sub = reply.json()
    assert (sub["user"], sub["status"], sub["kind"], sub["run"]) == (
        "alice@example.com", "new", "bug", RUN)
    assert sub["images"] == ["img_1.png", "img_2.jpg"]
    folder = app["root"] / sub["sub_id"]
    assert (folder / "img_1.png").read_bytes() == PNG
    assert (folder / "img_2.jpg").read_bytes() == JPG
    saved = json.loads((folder / "submission.json").read_text(encoding="utf-8"))
    assert saved["status_history"][0]["status"] == "new"


def test_refusals_save_nothing(app):
    client = app["client"]
    assert _send(client, images=[{"data": b64(SVG)}]).status_code == 400
    assert _send(client, images=[{"data": "not base64!!"}]).status_code == 400
    assert _send(client, images=[{"data": b64(PNG)}] * 6).status_code == 422
    assert _send(client, kind="complaint").status_code == 422
    assert _send(client, title="").status_code == 422
    assert _send(client, text="   ").status_code == 400            # blank once stripped
    assert _send(client, run="../etc").status_code == 422
    assert _send(client, run="demo_20261120_120000").status_code == 404   # no such run
    assert _send(client, extra="x").status_code == 422
    assert not app["root"].exists() or not any(app["root"].iterdir())


def test_an_oversized_screenshot_is_refused(app):
    big = PNG + b"\x00" * (5 * 1024 * 1024)
    reply = _send(app["client"], images=[{"data": b64(big)}])
    assert reply.status_code == 400 and "5 MB" in reply.json()["detail"]


def test_people_see_only_their_own(app):
    client = app["client"]
    _send(client, title="Alice's")
    _send(client, headers=BOB, title="Bob's", kind="suggestion")
    mine = client.get("/api/feedback", headers=ALICE).json()
    assert [s["title"] for s in mine["items"]] == ["Alice's"] and mine["is_admin"] is False
    assert client.get("/api/feedback?all=true", headers=ALICE).status_code == 403


def test_admins_see_everyone_and_set_the_status(app):
    client = app["client"]
    sub = _send(client, images=[{"data": b64(GIF)}]).json()
    _send(client, headers=BOB, title="Bob's")
    every = client.get("/api/feedback?all=true", headers=ADMIN).json()
    assert every["is_admin"] is True and len(every["items"]) == 2
    url = f"/api/feedback/{sub['sub_id']}/status"
    assert client.post(url, json={"status": "done"}, headers=ALICE).status_code == 403
    reply = client.post(url, json={"status": "in_progress"}, headers=ADMIN)
    assert reply.status_code == 200 and reply.json()["status"] == "in_progress"
    assert [h["status"] for h in reply.json()["status_history"]] == ["new", "in_progress"]
    assert reply.json()["status_history"][-1]["by"] == "Boss@Example.com"
    assert client.post(url, json={"status": "gone"}, headers=ADMIN).status_code == 422
    assert client.get("/api/feedback", headers=ALICE).json()["items"][0]["status"] == \
        "in_progress"


def test_the_comment_line_admin_is_read_too(app):
    assert app["client"].get("/api/feedback",
                             headers={"x-forwarded-email": "OTHER@example.com"}
                             ).json()["is_admin"] is True


def test_screenshots_are_served_to_their_owner_and_admins_only(app):
    client = app["client"]
    sub = _send(client, images=[{"data": b64(WEBP)}]).json()
    url = f"/api/feedback/{sub['sub_id']}/images/img_1.webp"
    reply = client.get(url, headers=ALICE)
    assert reply.status_code == 200 and reply.content == WEBP
    assert reply.headers["content-type"] == "image/webp"
    assert reply.headers["x-content-type-options"] == "nosniff"
    assert reply.headers["content-security-policy"] == "default-src 'none'"
    assert client.get(url, headers=ADMIN).status_code == 200
    assert client.get(url, headers=BOB).status_code == 403
    missing = f"/api/feedback/{sub['sub_id']}/images/img_2.webp"
    assert client.get(missing, headers=ALICE).status_code == 404
    other = f"/api/feedback/{sub['sub_id']}/images/submission.json"
    assert client.get(other, headers=ALICE).status_code == 400
    assert client.get("/api/feedback/fb_bad/images/img_1.webp", headers=ALICE).status_code == 400


def test_related_runs_are_this_apps_run_folders_only(app):
    assert app["client"].get("/api/feedback/runs", headers=ALICE).json() == {"runs": [RUN]}


def test_no_admins_file_means_no_admins(monkeypatch, tmp_path):
    _roles(monkeypatch, tmp_path, None)
    try:
        client = TestClient(main.app)
        assert client.get("/api/feedback", headers=ADMIN).json()["is_admin"] is False
        assert client.get("/api/feedback?all=true", headers=ADMIN).status_code == 403
    finally:
        ui_stores.reset_stores()


def test_without_the_proxy_the_user_is_local(app):
    sub = _send(app["client"], headers={}).json()
    assert sub["user"] == "local"


def test_clearing_past_runs_keeps_the_feedback(app):
    """'Clear past runs' deletes demo_* folders only - never app_feedback/."""
    from ui.backend.demo import DemoRunner

    sub = _send(app["client"]).json()
    runner = DemoRunner(main.store, work=lambda: None)
    runner.clear_runs()
    assert (app["root"] / sub["sub_id"] / "submission.json").is_file()


def test_a_workspace_outputs_role_stores_it_remotely(monkeypatch, tmp_path):
    """Nothing assumes a local role: the submission goes through the backend."""
    from codegen.storage import RoleStore
    from codegen.storage.remote import WorkspaceBackend
    from storage_fakes import FakeWorkspaceClient

    fake = FakeWorkspaceClient()
    backend = WorkspaceBackend("/Workspace/Users/u/shared/out", client=fake)
    outputs = RoleStore("outputs", backend, tmp_path / "work")
    sub = feedback.new(outputs, "alice@example.com", "suggestion", "t", "d", [PNG])
    assert feedback.get(outputs, sub["sub_id"])["title"] == "t"
    assert feedback.image(outputs, sub["sub_id"], "img_1.png") == PNG
    assert [s["sub_id"] for s in feedback.list_for(outputs, "ALICE@example.com")] == \
        [sub["sub_id"]]
