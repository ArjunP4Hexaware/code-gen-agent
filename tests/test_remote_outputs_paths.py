"""A run whose outputs role is REMOTE writes outside the checkout (v0.5.7).

With `storage.outputs` pointing at a workspace / volume root, a run's working
copy lives in the role's temp directory (`/tmp/codegen_storage/outputs_<id>/…`),
not under the repo. `GenerationStore._generate_feed` used to make every written
file repo-relative, so `Path.relative_to` raised

    '/tmp/codegen_storage/outputs_…/<feed>/ddl/<x>.sql' is not in the subpath
    of '/app/python/source_code'

for every feed, and the App reported "live run produced no feeds" with nothing
published — the whole run lost at the last step, after the generation itself
had succeeded.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from ui.backend.service import REPO_ROOT, GenerationStore, display_path  # noqa: E402

from codegen.resolve.resolver import resolve_pair  # noqa: E402

CONTRACTS = REPO_ROOT / "fixtures" / "contracts"
CV = (CONTRACTS / "FRD_demo_cv_golden.contract.json",
      CONTRACTS / "sttm_mapping_contracts_cv_golden.json")


def test_display_path_is_repo_relative_inside_and_absolute_outside(tmp_path):
    inside = REPO_ROOT / "out" / "demo_1" / "feed" / "ddl" / "x.sql"
    assert display_path(inside) == "out/demo_1/feed/ddl/x.sql"
    # A remote outputs role's working copy: kept whole, never an exception.
    outside = tmp_path / "outputs_55dcd63bdd2a" / "demo_1" / "feed" / "ddl" / "x.sql"
    assert display_path(outside) == outside.as_posix()
    # What the UI needs from either form is the "/<feed_slug>/" segment.
    assert "/feed/" in display_path(outside)


def test_a_feed_generated_outside_the_checkout_still_reports_its_files(config, tmp_path):
    """The real path: generate into a root OUTSIDE the repo, as a remote
    outputs role does, and get the feed back with its files listed."""
    if not all(p.is_file() for p in CV):
        pytest.skip("demo fixture pair not restored (removed 2026-08-22)")
    cv_specs = resolve_pair(CV[0], CV[1], config)
    store = GenerationStore("config/config.yaml")
    outside = tmp_path / "codegen_storage" / "outputs_55dcd63bdd2a" / "demo_20260921"
    assert not outside.is_relative_to(REPO_ROOT)
    run = store._generate_feed(  # noqa: SLF001 — the UI's own generation path
        cv_specs[0], dry_run=True, skip_tests=True, out_root=outside,
        reports_dir=tmp_path / "reports")
    assert run.written_files, "a run that wrote files must report them"
    assert all(Path(f).is_absolute() for f in run.written_files)
    assert any(f"/{cv_specs[0].feed_slug}/" in f for f in run.written_files)
    assert any(f.endswith(".sql") for f in run.written_files)
