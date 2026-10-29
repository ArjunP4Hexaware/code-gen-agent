"""post144: the header logo comes from the state root (``branding/logo.<ext>``),
never from the repo; with none there the App says so and serves nothing."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic"


@pytest.fixture
def state(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(tmp_path))
    return tmp_path


def test_no_logo_in_the_state_root_is_said_and_not_served(state):
    client = TestClient(main.app)
    assert client.get("/api/branding").json() == {"logo": False}
    assert client.get("/api/branding/logo").status_code == 404


def test_the_state_roots_logo_is_served_with_its_type(state):
    (state / "branding").mkdir()
    (state / "branding" / "logo.png").write_bytes(PNG)
    client = TestClient(main.app)
    assert client.get("/api/branding").json() == {"logo": True}
    response = client.get("/api/branding/logo")
    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"


def test_only_a_file_named_logo_is_served(state):
    (state / "branding").mkdir()
    (state / "branding" / "notes.txt").write_text("not served", encoding="utf-8")
    (state / "branding" / "logo.png").mkdir()            # a folder of that name is no logo
    client = TestClient(main.app)
    assert client.get("/api/branding").json() == {"logo": False}
    assert client.get("/api/branding/logo").status_code == 404
