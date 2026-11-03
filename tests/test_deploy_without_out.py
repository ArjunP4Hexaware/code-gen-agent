"""The App deploy needs no ``out/`` (2026-10-13, D1 live pairing check).

A ``source_code_path`` deployment failed: the snapshot of the D1 Git folder
could not find ``out/`` after the harness cleaned it between pair runs. The
App never needs that folder — ``app.yaml`` names no path under it, the
frontend it serves is the COMMITTED ``ui/frontend/dist``, and its outputs go
to the outputs role (``CODEGEN_STORAGE_OUTPUTS``, a workspace folder in
ACFC). docs/acfc/APP_DEPLOY_NO_OUT.md records the decision.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_app_yaml_names_nothing_under_out():
    text = (REPO / "app.yaml").read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert not re.search(r"(^|[\s\"'/])out(/|\b)", body), body
    assert "CODEGEN_STORAGE_OUTPUTS" in body          # outputs go to the role, not ./out


def test_the_served_frontend_is_committed():
    tracked = set(subprocess.run(["git", "ls-files", "ui/frontend/dist"], cwd=REPO,
                                 capture_output=True, text=True, check=True).stdout.split())
    assert "ui/frontend/dist/index.html" in tracked
    index = (REPO / "ui" / "frontend" / "dist" / "index.html").read_text(encoding="utf-8")
    for asset in re.findall(r'(?:src|href)="/?(assets/[^"]+)"', index):
        assert f"ui/frontend/dist/{asset}" in tracked, asset


def test_out_is_never_tracked():
    tracked = subprocess.run(["git", "ls-files", "out"], cwd=REPO, capture_output=True,
                             text=True, check=True).stdout.split()
    assert tracked == []


def test_the_app_answers_with_no_out_folder(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from ui.backend import main, stores

    missing = tmp_path / "no_out_here"
    monkeypatch.setattr(stores, "outputs_root", lambda config: missing)
    client = TestClient(main.app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 200                     # the committed dist
    assert not missing.exists()
