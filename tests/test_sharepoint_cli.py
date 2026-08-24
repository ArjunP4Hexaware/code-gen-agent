"""The two SharePoint CLI commands (codegen sharepoint-fetch / -publish).

These are this repo's equivalent of frd-to-sttm's `00_sharepoint_fetch` /
`05_sharepoint_publish` notebooks — that repo runs its pipeline as Databricks
notebook tasks, this one has a CLI, so the transport edges are subcommands.

Fully offline: the Graph client is a stub injected over
``codegen.sharepoint.build_client`` (the CLI imports it inside the command
functions, so patching the module attribute is enough), and ``config_for`` is
stubbed so no environment variable or .env is ever read. Nothing here opens a
socket or prompts for a credential.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import sharepoint as sp
from codegen.cli import main

REPO = Path(__file__).resolve().parents[1]
CONFIG = str(REPO / "config" / "config.yaml")

CFG = sp.SharePointConfig(
    tenant_id="tid", client_id="cid", client_secret="SUPERSECRET",
    host="example.sharepoint.com", site_path="/sites/DataOffice",
    library="Project Docs", input_folder="Inbound", output_folder="Generated",
)


class StubClient:
    def __init__(self, fetched=(), upload_error=None):
        self._fetched, self._upload_error = list(fetched), upload_error
        self.uploaded = []

    def fetch_to_dir(self, dest, suffixes=None):
        Path(dest).mkdir(parents=True, exist_ok=True)
        for item in self._fetched:
            (Path(dest) / item.name).write_bytes(b"X")
        return self._fetched

    def upload_file(self, path, name=None):
        if self._upload_error is not None:
            raise self._upload_error
        self.uploaded.append((Path(path).name, name))
        return {"webUrl": f"https://example/{name}"}


def _item(name, size=10):
    return sp.SharePointItem(item_id="1", name=name, size=size,
                             modified="2026-08-22T00:00:00Z", web_url="u")


@pytest.fixture()
def wired(monkeypatch):
    """Stub config + client. Returns a dict the test mutates to choose the
    client, so a test can install a failing one before invoking main()."""
    state = {"client": StubClient()}
    monkeypatch.setattr(sp, "config_for", lambda *a, **k: CFG)
    monkeypatch.setattr(sp, "build_client", lambda cfg: state["client"])
    return state


@pytest.fixture()
def workdir(tmp_path, monkeypatch):
    """out/ and reports/ are config-relative, so run from a scratch cwd."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# --------------------------------------------------------------------------- #
# fetch
# --------------------------------------------------------------------------- #

def test_fetch_downloads_and_reports_each_file(wired, workdir, capsys):
    wired["client"] = StubClient([_item("sttm.xlsx"), _item("frd.json")])
    assert main(["sharepoint-fetch", "--config", CONFIG, "--dest", "inbox"]) == 0
    out = capsys.readouterr().out
    assert "FETCHED" in out and "sttm.xlsx" in out and "frd.json" in out
    assert "2 file(s)" in out
    assert (workdir / "inbox" / "sttm.xlsx").is_file()


def test_fetch_of_an_empty_folder_fails_rather_than_reporting_success(wired, workdir, capsys):
    """An empty library folder and a successful fetch must not look the same
    to whatever runs next."""
    wired["client"] = StubClient([])
    assert main(["sharepoint-fetch", "--config", CONFIG, "--dest", "inbox"]) == 1
    assert "no supported documents" in capsys.readouterr().out


def test_fetch_surfaces_a_config_error_without_a_traceback(workdir, monkeypatch, capsys):
    """An unconfigured tenant is an operator message, not a stack trace."""
    def unconfigured(*a, **k):
        raise sp.SharePointConfigError("SharePoint is not configured — missing: tenant_id")

    monkeypatch.setattr(sp, "config_for", unconfigured)
    assert main(["sharepoint-fetch", "--config", CONFIG, "--dest", "inbox"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("FAIL") and "not configured" in out
    assert "Traceback" not in out


def test_fetch_surfaces_a_graph_error(wired, workdir, capsys):
    class Failing(StubClient):
        def fetch_to_dir(self, dest, suffixes=None):
            raise sp.GraphError(403, "u", "accessDenied", "no read", "req-1")

    wired["client"] = Failing()
    assert main(["sharepoint-fetch", "--config", CONFIG, "--dest", "inbox"]) == 1
    out = capsys.readouterr().out
    assert "accessDenied" in out and "req-1" in out


def test_fetch_never_prints_the_secret(wired, workdir, capsys):
    wired["client"] = StubClient([_item("sttm.xlsx")])
    main(["sharepoint-fetch", "--config", CONFIG, "--dest", "inbox"])
    assert "SUPERSECRET" not in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# publish
# --------------------------------------------------------------------------- #

def _artifacts(workdir, slug="tpl_caqh", *, report=True, notebook=True):
    (workdir / "out" / slug).mkdir(parents=True, exist_ok=True)
    (workdir / "reports").mkdir(parents=True, exist_ok=True)
    if report:
        (workdir / "reports" / f"{slug}.md").write_text("# r", encoding="utf-8")
    if notebook:
        (workdir / "out" / slug / f"{slug}.ipynb").write_text("{}", encoding="utf-8")


def test_publish_uploads_report_and_notebook_by_default(wired, workdir, capsys):
    _artifacts(workdir)
    assert main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh"]) == 0
    assert [n for _s, n in wired["client"].uploaded] == ["tpl_caqh.md", "tpl_caqh.ipynb"]
    assert "2 artifact(s) published" in capsys.readouterr().out


def test_publish_qualifies_an_unqualified_module_name(wired, workdir):
    _artifacts(workdir)
    (workdir / "out" / "tpl_caqh" / "bronze.py").write_text("x", encoding="utf-8")
    assert main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh",
                 "--path", "bronze.py"]) == 0
    assert wired["client"].uploaded == [("bronze.py", "tpl_caqh__bronze.py")]


def test_publish_refuses_a_path_escaping_the_feed_directory(wired, workdir, capsys):
    _artifacts(workdir)
    (workdir / "out" / "secret.txt").write_text("nope", encoding="utf-8")
    assert main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh",
                 "--path", "../secret.txt"]) == 1
    assert "escapes" in capsys.readouterr().out
    assert wired["client"].uploaded == []


def test_publish_with_nothing_generated_fails_loudly(wired, workdir, capsys):
    """Publishing nothing is an error: downstream a silent no-op is
    indistinguishable from a successful publish."""
    assert main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh"]) == 1
    out = capsys.readouterr().out
    assert "nothing to publish" in out and "generate" in out
    assert wired["client"].uploaded == []


def test_publish_stops_on_a_graph_failure(wired, workdir, capsys):
    _artifacts(workdir)
    wired["client"] = StubClient(
        upload_error=sp.GraphError(413, "u", "file_too_large", "big", None))
    assert main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh"]) == 1
    assert "file_too_large" in capsys.readouterr().out


def test_publish_never_prints_the_secret(wired, workdir, capsys):
    _artifacts(workdir)
    main(["sharepoint-publish", "--config", CONFIG, "--feed", "tpl_caqh"])
    assert "SUPERSECRET" not in capsys.readouterr().out
