"""2026-10-16 (demo cleanup): the FRD picker's default is "none chosen".

The demo contract (``demo.frd``) is never preselected for a real STTM. An FRD
is shown only when it was chosen or when the selected STTM has a paired FRD /
contract in the pair index — then it is preselected and labelled "paired". A
chosen STTM with no FRD cannot run: the agent never guesses a pair."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from ui_select import select_sttm  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
UNPAIRED = "zz_syn_unpaired_mapping_book.xlsx"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ui.backend import main

    return TestClient(main.app)


def _done(client, job_id: int, timeout: float = 90.0) -> dict:
    """The status once selection job ``job_id`` and its pairing have landed."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get("/api/demo/status").json()
        job = status["selection_job"]
        if (job and job["id"] == job_id and job["state"] != "running"
                and not job.get("pairing_pending")):
            return status
        time.sleep(0.05)
    raise AssertionError(f"selection job {job_id} did not finish")


def _idle() -> None:
    from ui.backend import main

    if main.runner is not None:
        main.runner._index.wait_idle(30)


@pytest.fixture()
def unpaired_sttm(client):
    """A synthetic STTM whose name pairs with no FRD in the pair index —
    uploaded, so it lands wherever the App's uploads inbox is and the
    upload's own selection job chooses it."""
    data = (REPO / "fixtures" / "acfc_shapes" / "sttm" / "pair_2_family_b.xlsx").read_bytes()
    response = client.post("/api/demo/upload", data={"kind": "sttm"},
                           files={"file": (UNPAIRED, data, "application/octet-stream")})
    assert response.status_code == 201, response.text
    yield response.json()["job"]["id"]
    _idle()
    (REPO / "inputs" / "uploads" / UNPAIRED).unlink(missing_ok=True)


def test_nothing_chosen_shows_no_frd(client):
    client.delete("/api/demo/workbook")
    client.delete("/api/demo/frd")
    status = client.get("/api/demo/status").json()
    assert status["frd_name"] is None and status["frd_chosen"] is False
    assert "frd_warning" not in status
    current = client.get("/api/demo/frd-choices").json()["current"]
    assert current == {"label": None, "chosen": False, "paired": False}


def test_picking_an_sttm_with_no_pair_leaves_the_frd_field_empty(client, unpaired_sttm):
    from ui.backend import main

    try:
        status = _done(client, unpaired_sttm)
        job = status["selection_job"]
        assert job["state"] == "done", (job.get("error"), job.get("steps"))
        assert status["selection"]["sttm"] == UNPAIRED
        # never the demo contract beside a real STTM
        assert status["frd_name"] is None
        assert (status["frd_chosen"], status["frd_paired"]) == (False, False)
        current = client.get("/api/demo/frd-choices").json()["current"]
        assert current["label"] is None and current["chosen"] is False
        assert main.runner.effective_frd() is None
        if not (status.get("pair_candidates") or {}).get("frd"):
            # nothing to ask: the run is refused, naming the STTM
            with pytest.raises(ValueError, match=f"no FRD chosen for {UNPAIRED}"):
                main.runner.start_live()
    finally:
        client.delete("/api/demo/workbook")
        client.delete("/api/demo/frd")


def test_a_paired_sttm_preselects_its_frd_labelled_paired(client):
    if not (REPO / "fixtures" / "workbooks" / "demo_sttm_cv_golden.xlsx").is_file():
        pytest.skip("CV golden workbook not restored")
    try:
        status = select_sttm(client, "demo_sttm_cv_golden.xlsx")
        assert status["frd_name"] == "FRD_demo_cv_golden.contract.json"
        assert status["frd_paired"] is True
        current = client.get("/api/demo/frd-choices").json()["current"]
        assert current == {"label": "FRD_demo_cv_golden.contract.json", "chosen": True,
                           "paired": True}
    finally:
        client.delete("/api/demo/workbook")
        client.delete("/api/demo/frd")
