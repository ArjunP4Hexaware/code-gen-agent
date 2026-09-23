"""VDD pairing never chooses an STTM workbook as the Vendor Data Dictionary.

A copy of the chosen STTM sitting next to the dictionary (an uploaded STTM
whose original is also in the pairs folder) scores a perfect content match
against itself. With a COLD document index (fresh container / new files) the
copy was still a candidate — the index did not know its kind yet — and
``DemoRunner._plan_pair`` read it for its pairing facts without looking at
the verdict of that read, so the STTM copy was chosen as the VDD. A workbook
whose verdict is ``sttm`` is never a dictionary, however warm the index; the
CLI's ``codegen pair`` applies the same content rule.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from ui.backend import main  # noqa: E402
from ui.backend import stores as ui_stores  # noqa: E402
from ui.backend.demo import DemoRunner  # noqa: E402
from ui.backend.service import GenerationStore  # noqa: E402

from codegen.cli import main as cli_main  # noqa: E402
from codegen.storage import open_storage  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
STTM = SHAPES / "sttm" / "pair_1_family_a.xlsx"
FRD = SHAPES / "frd" / "f1_pair_1.docx"
VDD = SHAPES / "vdd" / "pair_1_v1_segments.xlsx"
UPLOADED = "upload_pair_1_family_a.xlsx"


@pytest.fixture
def api(monkeypatch, tmp_path):
    """Local inputs / state roles on scratch directories and an extra input
    root holding the pair's documents (the STTM's ORIGINAL among them)."""
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    pairs = tmp_path / "pairs"
    pairs.mkdir()
    for source in (STTM, FRD, VDD):
        shutil.copyfile(source, pairs / source.name)
    for name in ("inputs", "state"):
        (tmp_path / name).mkdir()
    env = {"CODEGEN_STORAGE_INPUTS": f"local:{(tmp_path / 'inputs').as_posix()}",
           "CODEGEN_STORAGE_STATE": f"local:{(tmp_path / 'state').as_posix()}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
           "CODEGEN_EXTRA_INPUT_DIRS": f"local:{pairs.as_posix()}"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env))
    ui_stores.reset_stores()
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    runner = DemoRunner(store, work=lambda: None)
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(main, "runner", runner)
    yield TestClient(main.app), runner
    runner._index.wait_idle(30.0)
    ui_stores.reset_stores()


def _wait_job(client, job_id: str, timeout: float = 90.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get("/api/demo/status").json()
        job = status["selection_job"]
        # M15.2: done as soon as the STTM is classified; the pairs land behind.
        if (job is not None and job["id"] == job_id and job["state"] != "running"
                and not job.get("pairing_pending")):
            return status
        time.sleep(0.05)
    raise AssertionError(f"the selection job did not finish within {timeout:g}s")


def test_an_uploaded_sttm_never_pairs_its_own_copy_as_the_vdd(api):
    client, runner = api
    reply = client.post("/api/demo/upload", data={"kind": "sttm"},
                        files={"file": (UPLOADED, STTM.read_bytes())})
    assert reply.status_code == 201, reply.text
    job = reply.json()["job"]
    status = _wait_job(client, job["id"])
    finished = status["selection_job"]
    assert finished["error"] is None, finished
    vdd = finished["pairing"]["vdd"]
    # The STTM's own copy is not even a candidate — it reads as a mapping workbook.
    assert STTM.name not in {c["name"] for c in vdd["candidates"]}, vdd
    # The real dictionary is chosen or, when no content decides, OFFERED: it
    # is a candidate of the question the run asks (never replaced by an STTM).
    assert vdd["chosen"] in (VDD.name, None), vdd
    assert VDD.name in {c["name"] for c in vdd["candidates"]}, vdd
    assert vdd["chosen"] == VDD.name or vdd["question"], vdd
    assert status["selection"]["vdd"] in (VDD.name, None), status["selection"]
    assert runner.selected_vdd is None or runner.selected_vdd.name == VDD.name


def test_plan_pair_drops_a_workbook_read_as_an_sttm_with_a_cold_index(api):
    """The plan itself, on a cold index: every candidate is read on the
    request path; the one whose verdict is ``sttm`` is dropped."""
    client, runner = api
    reply = client.post("/api/demo/upload", data={"kind": "sttm"},
                        files={"file": (UPLOADED, STTM.read_bytes())})
    _wait_job(client, reply.json()["job"]["id"])
    # Forget every verdict: the plan below starts from a cold index again.
    runner._index.wait_idle(30.0)
    with runner._index._lock:
        runner._index._load().clear()
    plan = runner._plan_pair("vdd", UPLOADED, time.monotonic() + 60.0)
    names = {c["name"] for c in plan["outcome"]["candidates"]}
    assert STTM.name not in names, plan["outcome"]
    assert plan["decision"].chosen in (VDD.name, None), plan["outcome"]


def test_cli_pair_never_offers_an_sttm_workbook_as_the_vdd(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = tmp_path / "pair"
    folder.mkdir()
    shutil.copyfile(STTM, folder / UPLOADED)
    for source in (STTM, FRD, VDD):
        shutil.copyfile(source, folder / source.name)
    cli_main(["pair", "--config", str(REPO / "config" / "config.yaml"),
              "--sttm", str(folder / UPLOADED)])
    out = capsys.readouterr().out
    vdd_lines = [line for line in out.splitlines() if " vdd " in f" {line} " or "CANDIDATE" in line]
    assert not any(STTM.name in line for line in vdd_lines), out
