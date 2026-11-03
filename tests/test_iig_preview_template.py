"""IIG-first M2: the store records the IIG template version the served run
used, and forgets it with the run.

2026-10-16 (post65): the metadata-sheet preview routes that read it are gone
(the Dashboard section was removed); the store still records the version.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")


def test_the_store_records_and_forgets_the_runs_template(tmp_path):
    from ui.backend.service import REPO_ROOT, GenerationStore

    store = GenerationStore(str(REPO_ROOT / "config" / "config.yaml"))
    assert store.iig_template is None
    store.adopt({}, [], mode="live", label="demo_x", out_root=tmp_path, reports_root=tmp_path,
                iig_template="iig_v2")
    assert store.iig_template == "iig_v2"
    assert store.forget_runs(["demo_x"]) is True
    assert store.iig_template is None
