"""post91: the App serves the run's combined set - ``combined`` in GET /api/feeds
(from the run's manifest; only files that exist) and GET /api/combined/{name}
(only a name the manifest lists, from the run's combined folder)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402

FILES = {"ddl": "STTM_Syn_DDL.txt", "iig": "STTM_Syn_IIG.xlsx",
         "review": "STTM_Syn_IIG_REVIEW.xlsx", "log": "STTM_Syn_LOG.md"}


@pytest.fixture
def client(monkeypatch, tmp_path):
    folder = tmp_path / "combined"
    folder.mkdir()
    for name in FILES.values():
        (folder / name).write_bytes(name.encode())
    (tmp_path / "secret.txt").write_text("not served", encoding="utf-8")
    (tmp_path / "CODEGEN_STAGES.json").write_text(json.dumps({"combined": [
        {"sttm": "STTM_Syn", "dir": "combined", "files": FILES}]}), encoding="utf-8")
    store = SimpleNamespace(out_root=tmp_path, runs={}, failures=[], mode="live",
                            label="demo_x", model_usage=[], load_decisions=lambda: {},
                            config=SimpleNamespace(output=SimpleNamespace(
                                app_options=["framework"],
                                app_files=["ddl", "iig", "iig_review", "addition", "log"],
                                app_assign_ids={})))
    monkeypatch.setattr(main, "store", store)
    return TestClient(main.app)


def test_the_feeds_response_names_the_set_in_order(client):
    combined = client.get("/api/feeds").json()["combined"]
    assert combined == [{"sttm": "STTM_Syn", "files": [
        FILES["ddl"], FILES["iig"], FILES["review"], FILES["log"]]}]


def test_each_listed_file_downloads(client):
    reply = client.get(f"/api/combined/{FILES['log']}")
    assert reply.status_code == 200
    assert reply.content == FILES["log"].encode()
    assert reply.headers["content-disposition"] == f'attachment; filename="{FILES["log"]}"'
    assert client.get(f"/api/combined/{FILES['iig']}").headers["content-type"].startswith(
        "application/vnd.openxmlformats")


def test_a_name_the_manifest_does_not_list_is_refused(client):
    assert client.get("/api/combined/secret.txt").status_code == 404
    # an encoded ../ no longer matches the route (the App page answers): never the file
    assert b"not served" not in client.get("/api/combined/..%2Fsecret.txt").content


def test_a_run_without_a_combined_set_lists_none(client, tmp_path):
    (tmp_path / "CODEGEN_STAGES.json").write_text("{}", encoding="utf-8")
    assert client.get("/api/feeds").json()["combined"] == []


def test_a_kind_left_out_of_app_files_is_not_listed_but_still_downloads(client):
    """post98: output.app_files narrows what the App LISTS; the file is still
    written and still served by name."""
    main.store.config.output.app_files = ["ddl", "iig", "addition", "log"]
    reply = client.get("/api/feeds").json()
    assert reply["combined"] == [{"sttm": "STTM_Syn", "files": [
        FILES["ddl"], FILES["iig"], FILES["log"]]}]
    assert reply["app_files"] == ["ddl", "iig", "addition", "log"]
    assert client.get(f"/api/combined/{FILES['review']}").status_code == 200
