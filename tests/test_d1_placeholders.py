"""D1 post44 (2026-10-14): no ``<<D1:...>>`` placeholder may survive a D1 run.

The ACFC overlay (config/overlays/acfc_env.yaml) carries a placeholder wherever the
corpus patterns report (patterns.json) does not state the value the brief needs:
the email sender / recipient / webhook / extra statuses / SUBJECT and BODY per
status, the notebook name / path / process name per flow, the schedule's
description per flow and APPLICATION_NAME, the DQ split rule's storage account.
On D1 an overlay on top (CODEGEN_CONFIG_OVERLAYS) replaces every one.

On D1 this test FAILS while any placeholder is left in the effective config,
naming each one. At home it checks the placeholders are all reported (the list
is printed) and skips. D1 = ``CODEGEN_D1_RUN=1``, a Databricks runtime
(``DATABRICKS_RUNTIME_VERSION``), or the prod goldens present
(docs/acfc/iig_goldens/*.xlsx — gitignored, D1 only).
"""

from __future__ import annotations

import os

import pytest

from codegen.config import is_d1_placeholder, load_config
from test_iig_v2_derivations import ACFC_OVERLAY, REPO


def on_d1() -> bool:
    return (os.environ.get("CODEGEN_D1_RUN", "").strip() == "1"
            or bool(os.environ.get("DATABRICKS_RUNTIME_VERSION"))
            or any((REPO / "docs" / "acfc" / "iig_goldens").glob("*.xlsx")))


def placeholders(value, path: str = "") -> list[str]:
    """``path = value`` of every placeholder in a config dump."""
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in placeholders(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholders(v, f"{path}[{i}]")]
    return [f"{path.lstrip('.')} = {value}"] if is_d1_placeholder(value) else []


def test_no_d1_placeholder_survives_a_d1_run():
    # CODEGEN_CONFIG_OVERLAYS (the D1 overlay) is applied on top by load_config
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])
    left = [*placeholders(config.metadata.templates["iig_v2"].model_dump()),
            # 2026-10-14: the client lob_reference (plan id -> LOB)
            *placeholders(config.conventions.lob_reference, "conventions.lob_reference")]
    left += [f"conventions.lob_reference key = {k}"
             for k in config.conventions.lob_reference if is_d1_placeholder(k)]
    # 2026-10-14: the D1 environment's values (the storage account)
    left += placeholders(config.environments["D1"].model_dump(), "environments.D1")
    if on_d1():
        assert not left, ("D1 overlay missing values for:\n  " + "\n  ".join(left))
    assert left, "the ACFC overlay names its D1 placeholders (home)"
    pytest.skip(f"home run: {len(left)} D1 placeholder(s) open, by design:\n  "
                + "\n  ".join(left))
