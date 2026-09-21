"""M9.3 addendum — the App hang recorded in docs/acfc/APP_CHOOSER_BUG.md.

On site: ``POST /api/demo/workbook`` for the pair-1 STTM ran into the client's
180 s read timeout, and afterwards EVERY endpoint (``/api/demo/status``,
``/api/feeds``) timed out until the App was restarted; the FRD list carried an
upstream warehouse error at the same time. The fixes pinned here:

* the STTM selection is a JOB — the POST answers at once, each step
  (locate, download, classify, pair, record) has a timeout, and a late step
  is a visible error on the status, never a hung request;
* upstream contract lookups (a SQL Warehouse read) are OFF by default and
  never on a request path — on, they refresh in a background task with a
  hard timeout;
* documents are opened in a child process that is KILLED when it is late (a
  thread cannot be stopped; a runaway parse starved the process);
* the workbook list's ``selected`` and the status' selection are ONE record.

Everything runs on fakes — the fake workspace client, a fake upstream module,
a parser command that never answers.
"""

from __future__ import annotations

import sys
import threading
import time

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import docindex  # noqa: E402
from ui.backend import stores as ui_stores  # noqa: E402

from codegen import upstream_contracts  # noqa: E402
from test_m93_chooser import _Workspace  # noqa: E402

STEP_TIMEOUT = 1.5
# The POST, and every request made while the job is stuck, must answer in far
# less than one step's timeout.
PROMPT = 1.0


@pytest.fixture
def ws(monkeypatch, tmp_path):
    workspace = _Workspace(monkeypatch, tmp_path, select_timeout=STEP_TIMEOUT)
    yield workspace
    workspace.release()
    ui_stores.reset_stores()


class _BlockingUpstream:
    """A fake upstream client whose every call blocks until released."""

    def __init__(self, monkeypatch):
        self.release = threading.Event()
        self.calls: list[str] = []

        def list_contracts(config):
            self.calls.append("list_contracts")
            self.release.wait()
            return []

        def materialize(config, doc_id, base):
            self.calls.append("materialize")
            self.release.wait()
            raise RuntimeError("released")

        monkeypatch.setattr(upstream_contracts, "list_contracts", list_contracts)
        monkeypatch.setattr(upstream_contracts, "materialize", materialize)


@pytest.fixture
def upstream(monkeypatch):
    fake = _BlockingUpstream(monkeypatch)
    yield fake
    fake.release.set()


def _api(monkeypatch, ws, *, upstream_enabled: bool = False, upstream_timeout: float = 1.0):
    from ui.backend import main

    if main.store is None:
        pytest.skip("the UI backend has no store in this environment")
    config = ws.store.config
    monkeypatch.setattr(ws.store, "config", config.model_copy(update={
        "upstream": config.upstream.model_copy(update={
            "enabled": upstream_enabled, "timeout_seconds": upstream_timeout})}))
    runner = ws.runner()
    monkeypatch.setattr(main, "store", ws.store)
    monkeypatch.setattr(main, "runner", runner)
    return TestClient(main.app), runner


def _timed(call):
    started = time.monotonic()
    response = call()
    return response, time.monotonic() - started


def _wait_job(client, job_id: int, limit: float) -> dict:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        job = client.get("/api/demo/status").json()["selection_job"]
        if job["id"] == job_id and job["state"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError(f"the selection job did not finish within {limit:g}s")


# --------------------------------------------------------------- the regression (addendum item 3)


def test_a_download_and_an_upstream_call_that_never_return_hang_nothing(monkeypatch, ws,
                                                                       upstream):
    """A fake backend whose download blocks indefinitely AND a fake upstream
    client that blocks indefinitely: POST select returns within the timeout,
    /api/feeds still answers, and the status the UI polls shows the failure."""
    ws.pairs("pair_1")
    ws.blocked["STTM_alpha.xlsx"] = threading.Event()             # never set by the test
    client, runner = _api(monkeypatch, ws, upstream_enabled=True)

    response, took = _timed(lambda: client.post("/api/demo/workbook",
                                                json={"name": "STTM_alpha.xlsx"}))
    assert response.status_code == 202 and took < PROMPT, (response.text, took)
    job = response.json()["job"]
    assert job["state"] == "running" and job["name"] == "STTM_alpha.xlsx"

    # While the download hangs, every endpoint answers — the FRD list too, whose
    # upstream section is a background refresh against a client that hangs.
    for path in ("/api/feeds", "/api/demo/status", "/api/demo/workbooks",
                 "/api/demo/frd-choices"):
        reply, took = _timed(lambda path=path: client.get(path))
        assert reply.status_code == 200 and took < PROMPT, (path, reply.status_code, took)
    choices = client.get("/api/demo/frd-choices").json()
    assert choices["upstream_enabled"] is True and choices["upstream_state"] == "loading"
    assert "list_contracts" in upstream.calls
    # State mutations elsewhere are not blocked by the running job (the lock
    # guards state only; nothing holds it across I/O).
    reply, took = _timed(lambda: client.post("/api/demo/output-mode", json={"mode": "rfc"}))
    assert reply.status_code == 200 and took < PROMPT
    # A second selection while one runs is a 409 at once — not a queue — and a
    # run is refused (never the config default while the choice is pending).
    reply, took = _timed(lambda: client.post("/api/demo/workbook",
                                             json={"name": "STTM_alpha.xlsx"}))
    assert reply.status_code == 409 and took < PROMPT
    with pytest.raises(ValueError, match="is still being selected"):
        runner.start_live()

    # The step times out and the failure is ON THE STATUS the UI polls.
    job = _wait_job(client, job["id"], STEP_TIMEOUT + 10)
    assert job["state"] == "failed" and job["error"]["code"] == "timeout", job
    assert "did not finish within" in job["error"]["message"]
    assert [(s["step"], s["state"]) for s in job["steps"]] == [("locate", "done"),
                                                              ("download", "timed_out")]
    status = client.get("/api/demo/status").json()
    assert status["selection"]["sttm"] is None and status["sttm_chosen"] is False
    assert "STTM 'STTM_alpha.xlsx' was NOT selected" in status["selection_error"]["message"]
    assert not any(r["selected"] for r in client.get("/api/demo/workbooks").json()["workbooks"])
    # The upstream refresh gave up too — said, never waited for.
    deadline = time.monotonic() + 10
    while client.get("/api/demo/frd-choices").json()["upstream_state"] == "loading":
        assert time.monotonic() < deadline
        time.sleep(0.05)
    choices = client.get("/api/demo/frd-choices").json()
    assert choices["upstream_state"] == "failed"
    assert "did not answer within" in choices["upstream_error"]
    # And the App is still the App: /api/feeds answers, a run is refused with the reason.
    assert client.get("/api/feeds").status_code == 200
    with pytest.raises(ValueError, match="was NOT selected"):
        runner.start_live()


def test_upstream_is_off_by_default_and_never_called(monkeypatch, ws, upstream):
    ws.pairs("pair_1")
    client, runner = _api(monkeypatch, ws)                       # the tracked default: off
    from ui.backend import main

    from codegen.config import load_config

    assert load_config(main.REPO_ROOT / "config" / "config.yaml").upstream.enabled is False
    choices = client.get("/api/demo/frd-choices").json()
    assert (choices["upstream_enabled"], choices["upstream_state"]) == (False, "disabled")
    assert choices["upstream"] == [] and choices["upstream_error"] is None
    job = _wait_job(client, client.post("/api/demo/workbook",
                                        json={"name": "STTM_alpha.xlsx"}).json()["job"]["id"], 60)
    assert job["state"] == "done", job
    # The failed-run hint reads the snapshot, never the table.
    runner._attach_pairing_hint(RuntimeError("matches 0 FRD feeds"),
                                runner.selected_workbook, "FRD_bravo.docx")
    reply = client.post("/api/demo/frd", json={"kind": "upstream", "id": "doc-1"})
    assert reply.status_code == 403 and "upstream.enabled: false" in reply.json()["detail"]
    assert upstream.calls == []


def test_an_upstream_frd_choice_is_a_job_with_a_hard_timeout(monkeypatch, ws, upstream):
    client, runner = _api(monkeypatch, ws, upstream_enabled=True, upstream_timeout=1.0)
    reply, took = _timed(lambda: client.post("/api/demo/frd",
                                             json={"kind": "upstream", "id": "doc-1"}))
    assert reply.status_code == 202 and took < PROMPT
    job = _wait_job(client, reply.json()["job"]["id"], 15)
    assert job["kind"] == "frd_upstream" and job["error"]["code"] == "timeout", job
    status = client.get("/api/demo/status").json()
    assert status["frd_chosen"] is False
    assert status["selection_error"]["kind"] == "frd"


# --------------------------------------------------------------- a runaway parse is killed


def test_a_parse_that_never_answers_is_killed_and_the_app_keeps_answering(monkeypatch, ws):
    """The parser child says it is ready, then never answers — the shape of a
    workbook whose sheets declare a million rows. The classify step times out,
    the child is KILLED (a thread could only have been abandoned), the
    selection fails visibly and the next request is served."""
    hang = [sys.executable, "-c",
            "import sys, time; print('{\"ready\": true}', flush=True); time.sleep(3600)"]
    monkeypatch.setattr(docindex, "worker_command", lambda config, base: hang)
    ws.pairs("pair_1")
    client, runner = _api(monkeypatch, ws)
    job_id = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"}).json()["job"]["id"]
    reply, took = _timed(lambda: client.get("/api/feeds"))
    assert reply.status_code == 200 and took < PROMPT
    job = _wait_job(client, job_id, STEP_TIMEOUT + 15)
    steps = {s["step"]: s for s in job["steps"]}
    assert steps["classify"]["state"] == "timed_out", job
    assert "parser process was stopped" in steps["classify"]["detail"]
    assert job["error"]["code"] == "timeout"
    request_parser = docindex.parser_for(hang, docindex.Path(docindex.__file__).parents[2],
                                         "request")
    assert request_parser.kills >= 1 and not request_parser.alive
    assert client.get("/api/demo/status").json()["selection"]["sttm"] is None


def test_the_parser_process_answers_and_restarts_after_a_kill(tmp_path, config):
    """The real child (codegen.layout.docworker): classifies a workbook, and a
    request after a kill starts a fresh process."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    workbook = repo / "fixtures" / "acfc_shapes" / "sttm" / "pair_1_family_a.xlsx"
    parser = docindex.ParserProcess(docindex.worker_command(config, repo), repo, 90.0)
    try:
        first = parser.parse(workbook, workbook.name, 60.0)
        assert first["state"] == "sttm" and first["facts"] is not None
        parser.stop()
        assert not parser.alive
        again = parser.parse(workbook, workbook.name, 60.0)
        assert again["state"] == "sttm" and parser.alive
        garbage = tmp_path / "not_a_workbook.xlsx"
        garbage.write_bytes(b"not a zip")
        assert parser.parse(garbage, garbage.name, 60.0)["state"] == "unreadable"
    finally:
        parser.stop()


# --------------------------------------------------------------- one source of truth (item 4)


def test_the_list_and_the_status_read_one_selection_record(monkeypatch, ws):
    ws.pairs("pair_1")
    client, runner = _api(monkeypatch, ws)
    job = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"}).json()["job"]
    # While the job runs NOTHING is selected — in the list and on the status alike.
    status = client.get("/api/demo/status").json()
    rows = client.get("/api/demo/workbooks").json()["workbooks"]
    assert status["selection"]["sttm"] is None and not any(r["selected"] for r in rows)
    assert _wait_job(client, job["id"], 60)["state"] == "done"
    status = client.get("/api/demo/status").json()
    rows = client.get("/api/demo/workbooks").json()["workbooks"]
    assert status["selection"] == {"sttm": "STTM_alpha.xlsx", "frd": "FRD_bravo.docx",
                                   "vdd": "VDD_charlie.xlsx"}
    assert status["sttm_workbook"] == "STTM_alpha.xlsx" and status["sttm_chosen"] is True
    assert {r["name"] for r in rows if r["selected"]} == {status["selection"]["sttm"]}
    # A Clear is seen by both at once.
    client.delete("/api/demo/workbook")
    status = client.get("/api/demo/status").json()
    rows = client.get("/api/demo/workbooks").json()["workbooks"]
    assert status["selection"]["sttm"] is None and not any(r["selected"] for r in rows)


def test_a_clear_supersedes_a_running_selection(monkeypatch, ws):
    ws.pairs("pair_1")
    gate = ws.blocked["STTM_alpha.xlsx"] = threading.Event()
    client, runner = _api(monkeypatch, ws)
    job = client.post("/api/demo/workbook", json={"name": "STTM_alpha.xlsx"}).json()["job"]
    assert client.delete("/api/demo/workbook").status_code == 200
    gate.set()                                   # the download completes AFTER the Clear …
    time.sleep(STEP_TIMEOUT + 1)
    status = client.get("/api/demo/status").json()
    assert status["selection_job"]["id"] == job["id"]
    assert status["selection_job"]["error"]["code"] == "superseded"
    assert status["selection"]["sttm"] is None   # … and selects nothing
