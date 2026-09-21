"""Choosing the STTM over the API is a JOB (M9.3 addendum): ``POST
/api/demo/workbook`` answers 202 with the job at once, the status carries its
progress and outcome. Tests that are not ABOUT that contract use this helper:
post, poll the status like the UI does, return the final status."""

from __future__ import annotations

import time


def select_sttm(client, name: str, timeout: float = 90.0) -> dict:
    """POST the selection, poll ``/api/demo/status`` until the job has finished,
    return that status (``selection_job``, ``selection``, ``pairing`` …)."""
    response = client.post("/api/demo/workbook", json={"name": name})
    assert response.status_code == 202, response.text
    job_id = response.json()["job"]["id"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get("/api/demo/status").json()
        job = status["selection_job"]
        if job is not None and job["id"] == job_id and job["state"] != "running":
            return status
        time.sleep(0.05)
    raise AssertionError(f"the selection of {name!r} did not finish within {timeout:g}s")
