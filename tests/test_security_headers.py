"""post159 (pentest APP-CSP-1): every App response carries a Content-Security-
Policy that allows script from the App's own origin only (no inline script), plus
nosniff / no-referrer / same-origin framing - the layer behind the markdown
sanitiser (post158 P0-4)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402


def _directives(policy: str) -> dict[str, list[str]]:
    out = {}
    for part in policy.split(";"):
        words = part.split()
        if words:
            out[words[0]] = words[1:]
    return out


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(tmp_path))
    return TestClient(main.app)


@pytest.mark.parametrize("path", ["/", "/api/branding", "/api/no-such-route"])
def test_every_response_carries_the_security_headers(client, path):
    headers = client.get(path).headers
    policy = _directives(headers["content-security-policy"])
    assert policy["script-src"] == ["'self'"]
    assert policy["default-src"] == ["'self'"]
    assert policy["object-src"] == ["'none'"]
    assert "'unsafe-inline'" not in policy["script-src"]
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["x-frame-options"] == "SAMEORIGIN"


def test_the_built_shell_needs_no_inline_script():
    """script-src 'self' only works while dist/index.html loads its bundle by src."""
    from pathlib import Path

    html = (Path(main.__file__).resolve().parents[1] / "frontend" / "dist" /
            "index.html").read_text(encoding="utf-8")
    import re

    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", html, re.DOTALL)
    assert scripts and all("src=" in attrs and not body.strip() for attrs, body in scripts)
