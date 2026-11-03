"""Tests run the same on every machine: a per-machine signal (d) mode in the environment
(SPIRAL_BREAKER_D_MODE, set to "live" where (d) is live) must not leak into them."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_machine_d_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SPIRAL_BREAKER_D_MODE", raising=False)
