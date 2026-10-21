"""post90: the Notebooks panel's "Download all" - every notebook of the loaded
run in one zip (``GET /api/notebooks.zip``).

The notebooks stay separate files, byte-identical to the generated ones; a feed
without a notebook is named in README.txt; the same run gives the same bytes.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402


class _Store:
    """The two things the route reads: the runs and their files."""

    def __init__(self, root: Path, runs: dict):
        self.root, self.runs = root, runs

    def read_generated_bytes(self, slug: str, path: str) -> bytes:
        return (self.root / slug / path).read_bytes()


def _run(slug: str, written: list[str]):
    return SimpleNamespace(spec=SimpleNamespace(feed_slug=slug), written_files=written)


@pytest.fixture
def served(monkeypatch, tmp_path):
    def serve(feeds: dict[str, bytes | None]) -> TestClient:
        runs = {}
        for slug, body in feeds.items():
            written = [f"out/{slug}/framework/{slug}_IIG.xlsx"]
            if body is not None:
                path = tmp_path / slug / "notebook" / f"{slug}.ipynb"
                path.parent.mkdir(parents=True)
                path.write_bytes(body)
                written += [f"out/{slug}/notebook/{slug}.ipynb", f"out/{slug}/notebook/{slug}.py"]
            runs[slug] = _run(slug, written)
        monkeypatch.setattr(main, "store", _Store(tmp_path, runs))
        return TestClient(main.app)
    return serve


def _entries(reply) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(reply.content)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_every_notebook_is_in_the_zip_byte_for_byte(served):
    client = served({"syn_b": b'{"cells": ["b"]}', "syn_a": b'{"cells": ["a"]}'})
    reply = client.get("/api/notebooks.zip")
    assert reply.status_code == 200
    assert reply.headers["content-type"] == "application/zip"
    assert reply.headers["content-disposition"] == 'attachment; filename="notebooks.zip"'
    entries = _entries(reply)
    assert list(entries) == ["syn_a.ipynb", "syn_b.ipynb", "README.txt"]   # sorted, then README
    assert entries["syn_a.ipynb"] == b'{"cells": ["a"]}'
    assert entries["syn_b.ipynb"] == b'{"cells": ["b"]}'
    assert "no notebook" not in entries["README.txt"].decode()


def test_a_feed_without_a_notebook_is_named_not_hidden(served):
    client = served({"syn_a": b"{}", "syn_withheld": None})
    entries = _entries(client.get("/api/notebooks.zip"))
    assert "syn_withheld.ipynb" not in entries
    readme = entries["README.txt"].decode()
    assert "syn_withheld" in readme and "blocking question" in readme


def test_the_same_run_gives_the_same_bytes(served):
    client = served({"syn_a": b"{}", "syn_b": b"[]"})
    assert client.get("/api/notebooks.zip").content == client.get("/api/notebooks.zip").content


def test_no_notebook_at_all_is_a_404(served):
    client = served({"syn_a": None})
    assert client.get("/api/notebooks.zip").status_code == 404
