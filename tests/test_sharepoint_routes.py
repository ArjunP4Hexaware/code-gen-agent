"""SharePoint routes for the demo UI (ui/backend/sharepoint_routes.py).

Needs the [ui] extra (fastapi); skipped cleanly when it isn't installed so
the core generator suite stays offline-and-extra-free.

No fixtures and no network: the Graph client is a stub, the generation store
is a stub, and artifact roots are tmp_path. These tests therefore keep
running after the 2026-08-22 fixture removal.

What they pin is the failure MAPPING and the two write gates — the parts
that decide whether a bad request becomes a client's problem or ours, and
whether a stray POST can write to the client's library.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
# TestClient is httpx-backed: with fastapi present but httpx absent the import
# below is a collection ERROR, not a skip. Guard both so a partial [ui] install
# degrades to "skipped", the same way a missing extra already does.
pytest.importorskip("httpx")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import sharepoint_routes  # noqa: E402

from codegen.config import SharePointSettings  # noqa: E402
from codegen.sharepoint import (  # noqa: E402
    GraphError,
    SharePointConfig,
    SharePointConfigError,
)

CFG = SharePointConfig(
    tenant_id="tid", client_id="cid", client_secret="SUPERSECRET",
    host="example.sharepoint.com", site_path="/sites/DataOffice",
    library="Project Docs", input_folder="Inbound", output_folder="Generated",
)


@dataclass
class Item:
    item_id: str
    name: str
    size: int = 10
    modified: str = "2026-08-22T00:00:00Z"
    web_url: str = "https://example/x"


class StubClient:
    """Graph client double. `fail` raises on every call; `listings` maps a
    folder to what it holds."""

    def __init__(self, listings=None, payload=b"XLSX", fail=None, upload=None):
        self.listings = listings or {}
        self.payload, self.fail, self.upload = payload, fail, upload
        self.uploaded = []

    def list_documents(self, suffixes=None, folder=None):
        if isinstance(self.fail, Exception):
            raise self.fail
        items = self.listings.get(folder if folder is not None else CFG.input_folder, [])
        if suffixes is not None:
            items = [i for i in items if Path(i.name).suffix.lower() in suffixes]
        return items

    def download_item(self, item_id):
        if isinstance(self.fail, Exception):
            raise self.fail
        return self.payload

    def upload_file(self, path, name=None):
        if isinstance(self.upload, Exception):
            raise self.upload
        self.uploaded.append((Path(path).name, name))
        return {"webUrl": f"https://example/{name}"}


class StubStore:
    """Only what the routes touch: config, runs, and the two artifact roots."""

    def __init__(self, tmp_path, runs=("tpl_caqh",), settings=None):
        self.out_root = tmp_path / "out"
        self.reports_root = tmp_path / "reports"
        self.runs = dict.fromkeys(runs, object())
        self.config = type("C", (), {"sharepoint": settings or SharePointSettings()})()


@pytest.fixture()
def wired(tmp_path, monkeypatch):
    """Bind a stub store and a stub Graph client; return both plus a client.

    The router is mounted on a bare FastAPI app rather than importing
    ui.backend.main, so no startup generation runs and nothing touches the
    real out/ tree.
    """
    store = StubStore(tmp_path)
    sharepoint_routes.bind_store(store)
    monkeypatch.setattr(sharepoint_routes, "INPUTS_DIR", tmp_path / "inputs")

    state = {"client": StubClient()}
    monkeypatch.setattr(sharepoint_routes, "config_for", lambda *a, **k: CFG)
    monkeypatch.setattr(sharepoint_routes, "build_client", lambda cfg: state["client"])

    app = FastAPI()
    app.include_router(sharepoint_routes.router)
    yield state, store, TestClient(app, raise_server_exceptions=False)
    sharepoint_routes.bind_store(None)


def _feed_artifacts(store, slug="tpl_caqh", *, report=True, notebook=True):
    """Create the two default publishables on disk."""
    (store.out_root / slug).mkdir(parents=True, exist_ok=True)
    store.reports_root.mkdir(parents=True, exist_ok=True)
    if report:
        (store.reports_root / f"{slug}.md").write_text("# report", encoding="utf-8")
    if notebook:
        (store.out_root / slug / f"{slug}.ipynb").write_text("{}", encoding="utf-8")


# --------------------------------------------------------------------------- #
# config endpoint — unconfigured is a normal state, never an error
# --------------------------------------------------------------------------- #

def test_config_reports_the_target_when_configured(wired):
    _state, _store, client = wired
    body = client.get("/api/sharepoint/config").json()
    assert body["configured"] is True
    assert body["site"] == "example.sharepoint.com/sites/DataOffice"
    assert (body["input_folder"], body["output_folder"]) == ("Inbound", "Generated")


def test_config_returns_false_instead_of_raising_when_unconfigured(wired, monkeypatch):
    _state, _store, client = wired

    def unconfigured(*a, **k):
        raise SharePointConfigError("not configured")

    monkeypatch.setattr(sharepoint_routes, "config_for", unconfigured)
    body = client.get("/api/sharepoint/config").json()
    assert body == {"configured": False, "site": None, "library": None,
                    "input_folder": None, "output_folder": None}


def test_config_never_echoes_the_secret(wired):
    _state, _store, client = wired
    assert "SUPERSECRET" not in client.get("/api/sharepoint/config").text


# --------------------------------------------------------------------------- #
# failure mapping — the status code says whose problem it is
# --------------------------------------------------------------------------- #

def test_unconfigured_tenant_is_503(wired, monkeypatch):
    state, _store, client = wired

    def unconfigured(*a, **k):
        raise SharePointConfigError("SharePoint is not configured — missing: tenant_id")

    monkeypatch.setattr(sharepoint_routes, "config_for", unconfigured)
    resp = client.get("/api/sharepoint/documents")
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"]


def test_sign_in_failure_is_502_and_hides_the_secret(wired, monkeypatch):
    _state, _store, client = wired

    def bad_token(cfg):
        raise GraphError(401, "u", "invalid_client", "bad secret", "req-9")

    monkeypatch.setattr(sharepoint_routes, "build_client", bad_token)
    resp = client.get("/api/sharepoint/documents")
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "invalid_client" in detail and "req-9" in detail
    assert "SUPERSECRET" not in detail


def test_graph_refusal_on_listing_is_502(wired):
    state, _store, client = wired
    state["client"] = StubClient(fail=GraphError(403, "u", "accessDenied", "no", None))
    resp = client.get("/api/sharepoint/documents")
    assert resp.status_code == 502
    assert "accessDenied" in resp.json()["detail"]


def test_wrong_library_name_is_503_not_502(wired):
    """A renamed library is a configuration problem, not Graph refusing."""
    state, _store, client = wired
    state["client"] = StubClient(fail=SharePointConfigError("library not found"))
    assert client.get("/api/sharepoint/documents").status_code == 503


# --------------------------------------------------------------------------- #
# listing / import
# --------------------------------------------------------------------------- #

def test_documents_lists_only_consumable_files(wired):
    state, _store, client = wired
    state["client"] = StubClient({CFG.input_folder: [
        Item("1", "sttm.xlsx"), Item("2", "frd.json"),
    ]})
    body = client.get("/api/sharepoint/documents").json()
    assert [d["name"] for d in body["documents"]] == ["sttm.xlsx", "frd.json"]
    assert body["folder"] == "Inbound"


def test_import_writes_the_file_and_leaves_no_part_file(wired, tmp_path):
    state, _store, client = wired
    state["client"] = StubClient(payload=b"WORKBOOK")
    resp = client.post("/api/sharepoint/import",
                       json={"item_id": "1", "name": "sttm.xlsx"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "workbook" and body["stem"] == "sttm"
    assert (tmp_path / "inputs" / "sttm.xlsx").read_bytes() == b"WORKBOOK"
    assert list((tmp_path / "inputs").glob("*.part")) == []


def test_import_rejects_a_type_the_generator_cannot_consume(wired):
    _state, _store, client = wired
    resp = client.post("/api/sharepoint/import",
                       json={"item_id": "1", "name": "notes.docx"})
    assert resp.status_code == 400
    assert ".xlsx" in resp.json()["detail"]


def test_import_sanitises_the_library_filename(wired, tmp_path):
    """A library name is attacker-adjacent input and must not escape.

    Two layers, in this order: `Path(name).name` drops the directory part
    entirely, then the character filter runs on what is left. So the
    traversal is gone before sanitisation rather than being encoded into the
    stored name — `../../evil name.xlsx` lands as `evil_name.xlsx`, flat
    inside INPUTS_DIR.
    """
    state, _store, client = wired
    state["client"] = StubClient(payload=b"X")
    body = client.post("/api/sharepoint/import",
                       json={"item_id": "1", "name": "../../evil name.xlsx"}).json()
    assert body["name"] == "evil_name.xlsx"
    landed = tmp_path / "inputs" / body["name"]
    assert landed.is_file()
    # The decisive property: whatever the name was, the file is inside the
    # inputs dir and no traversal survived into it.
    assert landed.resolve().parent == (tmp_path / "inputs").resolve()
    assert ".." not in body["name"]


def test_import_over_the_cap_is_413(wired, monkeypatch):
    state, _store, client = wired
    monkeypatch.setattr(sharepoint_routes, "INPUT_MAX_BYTES", 4)
    state["client"] = StubClient(payload=b"TOOBIG")
    assert client.post("/api/sharepoint/import",
                       json={"item_id": "1", "name": "s.xlsx"}).status_code == 413


# --------------------------------------------------------------------------- #
# locate — exact match or a human decision, never a best guess
# --------------------------------------------------------------------------- #

def test_locate_exact_match_imports_and_reports_prior_publishes(wired):
    state, _store, client = wired
    state["client"] = StubClient({
        CFG.input_folder: [Item("1", "caqh_sttm.xlsx")],
        CFG.output_folder: [Item("9", "caqh_sttm__bronze.py"), Item("8", "other.md")],
    })
    body = client.post("/api/sharepoint/locate", json={"name": "caqh_sttm"}).json()
    assert body["status"] == "ready"
    assert body["document"]["name"] == "caqh_sttm.xlsx"
    # Informational only — the app surfaces, it does not decide.
    assert [a["name"] for a in body["already_published"]] == ["caqh_sttm__bronze.py"]


def test_locate_ambiguous_name_returns_candidates_and_imports_nothing(wired, tmp_path):
    state, _store, client = wired
    state["client"] = StubClient({CFG.input_folder: [
        Item("1", "caqh_sttm_v1.xlsx"), Item("2", "caqh_sttm_v2.xlsx"),
    ]})
    body = client.post("/api/sharepoint/locate", json={"name": "caqh_sttm"}).json()
    assert body["status"] == "candidates"
    assert len(body["candidates"]) == 2
    assert not (tmp_path / "inputs").exists()   # nothing auto-picked


def test_locate_unknown_name_is_404_naming_where_it_looked(wired):
    state, _store, client = wired
    state["client"] = StubClient({CFG.input_folder: [Item("1", "a.xlsx")]})
    resp = client.post("/api/sharepoint/locate", json={"name": "missing"})
    assert resp.status_code == 404
    assert "Project Docs/Inbound" in resp.json()["detail"]


def test_locate_blank_name_is_400(wired):
    _state, _store, client = wired
    assert client.post("/api/sharepoint/locate", json={"name": "   "}).status_code == 400


# --------------------------------------------------------------------------- #
# artifact download — re-verified against the output folder listing
# --------------------------------------------------------------------------- #

def test_artifact_download_serves_a_published_item(wired):
    state, _store, client = wired
    state["client"] = StubClient({CFG.output_folder: [Item("9", "tpl_caqh.ipynb")]},
                                 payload=b"NOTEBOOK")
    resp = client.get("/api/sharepoint/artifact/9")
    assert resp.status_code == 200 and resp.content == b"NOTEBOOK"
    assert "tpl_caqh.ipynb" in resp.headers["content-disposition"]


def test_artifact_download_refuses_an_item_outside_the_output_folder(wired):
    """Otherwise this endpoint proxies anything the app identity can read."""
    state, _store, client = wired
    state["client"] = StubClient({CFG.output_folder: [Item("9", "ok.ipynb")]})
    assert client.get("/api/sharepoint/artifact/SOMETHING-ELSE").status_code == 404


# --------------------------------------------------------------------------- #
# publish — the write gate
# --------------------------------------------------------------------------- #

def test_publish_without_confirm_is_400_and_writes_nothing(wired):
    state, store, client = wired
    _feed_artifacts(store)
    resp = client.post("/api/sharepoint/publish", json={"feed_slug": "tpl_caqh"})
    assert resp.status_code == 400
    assert "confirm" in resp.json()["detail"]
    assert state["client"].uploaded == []


def test_publish_confirm_false_is_also_rejected(wired):
    state, store, client = wired
    _feed_artifacts(store)
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": False})
    assert resp.status_code == 400
    assert state["client"].uploaded == []


def test_publish_uploads_report_and_notebook_by_default(wired):
    state, store, client = wired
    _feed_artifacts(store)
    body = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": True}).json()
    assert body["published"] is True
    assert [a["name"] for a in body["artifacts"]] == ["tpl_caqh.md", "tpl_caqh.ipynb"]
    assert body["target"] == "example.sharepoint.com/sites/DataOffice/Project Docs/Generated"
    assert [n for _src, n in state["client"].uploaded] == ["tpl_caqh.md", "tpl_caqh.ipynb"]


def test_publish_qualifies_an_unqualified_module_name(wired):
    """Two feeds' bronze.py must not collide in one flat library folder."""
    state, store, client = wired
    _feed_artifacts(store)
    (store.out_root / "tpl_caqh" / "bronze.py").write_text("x", encoding="utf-8")
    client.post("/api/sharepoint/publish",
                json={"feed_slug": "tpl_caqh", "path": "bronze.py", "confirm": True})
    assert state["client"].uploaded == [("bronze.py", "tpl_caqh__bronze.py")]


def test_publish_refuses_a_path_escaping_the_feed_directory(wired):
    state, store, client = wired
    _feed_artifacts(store)
    (store.out_root / "secret.txt").write_text("nope", encoding="utf-8")
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "path": "../secret.txt",
                             "confirm": True})
    assert resp.status_code == 400
    assert "escapes" in resp.json()["detail"]
    assert state["client"].uploaded == []


def test_publish_unknown_feed_is_404(wired):
    state, _store, client = wired
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "nope", "confirm": True})
    assert resp.status_code == 404
    assert state["client"].uploaded == []


def test_publish_missing_artifact_is_404_not_a_silent_success(wired):
    state, store, client = wired
    _feed_artifacts(store, notebook=False)
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": True})
    assert resp.status_code == 404
    assert "tpl_caqh.ipynb" in resp.json()["detail"]


def test_publish_graph_413_maps_to_413_not_502(wired):
    state, store, client = wired
    _feed_artifacts(store)
    state["client"] = StubClient(
        upload=GraphError(413, "u", "file_too_large", "too big", None))
    assert client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": True}).status_code == 413


def test_publish_other_graph_failure_maps_to_502(wired):
    state, store, client = wired
    _feed_artifacts(store)
    state["client"] = StubClient(
        upload=GraphError(403, "u", "accessDenied", "no write", "req-3"))
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": True})
    assert resp.status_code == 502
    assert "req-3" in resp.json()["detail"]


def test_routes_answer_503_when_no_store_is_bound(wired):
    _state, _store, client = wired
    sharepoint_routes.bind_store(None)
    resp = client.post("/api/sharepoint/publish",
                       json={"feed_slug": "tpl_caqh", "confirm": True})
    assert resp.status_code == 503
