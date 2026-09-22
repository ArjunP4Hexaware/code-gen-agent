"""The Notebook tab's "Download .ipynb" button.

It links to ``GET /api/feeds/{slug}/download?path=<slug>.ipynb`` — the same
contained download the framework artefacts use. The notebook comes back as
an attachment, byte-identical to the generated file, typed as a notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.resolve.resolver import resolve_pair  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"


@pytest.fixture
def served_feed(monkeypatch, tmp_path):
    if not (_FRD.is_file() and _STTM.is_file()):
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    spec = resolve_pair(_FRD, _STTM, store.config)[0]
    out_root, reports = tmp_path / "out", tmp_path / "reports"
    run = store._generate_feed(spec, dry_run=True, skip_tests=True, out_root=out_root,
                               reports_dir=reports, output_mode="notebook")
    store.adopt({spec.feed_slug: run}, [], mode="live", label="demo_20260922_120000",
                out_root=out_root, reports_root=reports)
    monkeypatch.setattr(main, "store", store)
    return TestClient(main.app), spec.feed_slug, out_root / spec.feed_slug


def test_the_notebook_downloads_as_an_ipynb_attachment(served_feed):
    client, slug, feed_dir = served_feed
    reply = client.get(f"/api/feeds/{slug}/download", params={"path": f"{slug}.ipynb"})
    assert reply.status_code == 200
    assert reply.headers["content-type"] == "application/x-ipynb+json"
    assert reply.headers["content-disposition"] == f'attachment; filename="{slug}.ipynb"'
    assert reply.content == (feed_dir / f"{slug}.ipynb").read_bytes()
    assert json.loads(reply.content)["cells"]


def test_the_download_stays_inside_the_feed_directory(served_feed):
    client, slug, _feed_dir = served_feed
    assert client.get(f"/api/feeds/{slug}/download",
                      params={"path": "../../reports/x.md"}).status_code == 400
    assert client.get(f"/api/feeds/{slug}/download",
                      params={"path": "missing.ipynb"}).status_code == 404
    assert client.get("/api/feeds/no_such_feed/download",
                      params={"path": "x.ipynb"}).status_code == 404
