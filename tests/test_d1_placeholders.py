"""D1 post44 (2026-10-14): no ``<<D1:...>>`` placeholder may survive a LIVE D1 run.

The ACFC overlay (config/overlays/acfc_env.yaml) carries a placeholder wherever the
corpus patterns report (patterns.json) does not state the value the brief needs:
the email sender / recipient / webhook / extra statuses / SUBJECT and BODY per
status, the notebook name / path / process name per flow, the schedule's
description per flow and APPLICATION_NAME, the DQ split rule's storage account.
On D1 an overlay on top (CODEGEN_CONFIG_OVERLAYS) replaces every one.

post47b — the LIVE-ONLY check. A run under provider=mock tolerates the
placeholders (each environment key an INPUT_NEEDED line, its cells empty); a run
under provider=live fails on the environment's. This test mirrors that: started
with ``CODEGEN_PROVIDER=live`` (the suite remembers it as
``CODEGEN_PROVIDER_REQUESTED`` — it never calls a model) or with the config's
``reasoning.mode: live``, it FAILS while any placeholder is left in the effective
config, naming each one. Otherwise it checks the placeholders are all reported
(the list is printed) and skips.
"""

from __future__ import annotations

import os

import pytest

from codegen.config import is_d1_placeholder, load_config
from test_iig_v2_derivations import ACFC_OVERLAY, REPO


def live_requested(config) -> bool:
    return (os.environ.get("CODEGEN_PROVIDER_REQUESTED", "").strip().lower() == "live"
            or getattr(config.reasoning, "mode", None) == "live")


def placeholders(value, path: str = "") -> list[str]:
    """``path = value`` of every placeholder in a config dump."""
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in placeholders(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholders(v, f"{path}[{i}]")]
    return [f"{path.lstrip('.')} = {value}"] if is_d1_placeholder(value) else []


def test_no_d1_placeholder_survives_a_live_d1_run():
    # CODEGEN_CONFIG_OVERLAYS (the D1 overlay) is applied on top by load_config
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    left = [*placeholders(config.metadata.templates["iig_v2"].model_dump()),
            # 2026-10-14: the client lob_reference (plan id -> LOB)
            *placeholders(config.conventions.lob_reference, "conventions.lob_reference")]
    left += [f"conventions.lob_reference key = {k}"
             for k in config.conventions.lob_reference if is_d1_placeholder(k)]
    # 2026-10-14: the D1 environment's values (the storage account)
    left += placeholders(config.environments["D1"].model_dump(), "environments.D1")
    if live_requested(config):
        assert not left, ("D1 overlay missing values for:\n  " + "\n  ".join(left))
    assert left, "the ACFC overlay names its D1 placeholders (home)"
    pytest.skip(f"provider=mock: {len(left)} D1 placeholder(s) open, by design "
                "(a live run fails on them):\n  " + "\n  ".join(left))


def test_the_check_runs_under_live(monkeypatch):
    """The gate itself: a live request turns the skip into the assertion."""
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    monkeypatch.setenv("CODEGEN_PROVIDER_REQUESTED", "live")
    assert live_requested(config)
    monkeypatch.setenv("CODEGEN_PROVIDER_REQUESTED", "")
    assert not live_requested(config)
