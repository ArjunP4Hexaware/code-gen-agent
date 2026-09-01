"""Shared fixtures: the real config and both resolved contract pairs.

These tests exercise the GENERATOR (no Spark). Generated-code tests live in
``out/<feed>/tests`` and run under the gate.

2026-08-22: the contract/workbook/replay fixtures were removed from the repo
(no client documents, raw or derived, in the repository). Everything that
needs them SKIPS when they are absent instead of failing -- see
``require_fixture_files`` / ``_pair_paths`` below. Restore anonymized fixtures
at the configured paths and the full suite runs again unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]

# Importing ui.backend.main (test_demo_ui and friends) runs load_dotenv as an
# import side effect, which can put the OPERATOR'S machine-local env overrides
# (e.g. CODEGEN_NOTIFICATION_EMAILS — a client value) into this process. The
# suite must run against the tracked config's synthetic values only, so the
# override is stripped before every test.
_MACHINE_LOCAL_ENV = ("CODEGEN_NOTIFICATION_EMAILS",)


@pytest.fixture(autouse=True, scope="session")
def _strip_machine_local_env():
    # Session-scoped + autouse: runs after collection (when ui.backend.main's
    # import-time load_dotenv may have fired) and before any other session
    # fixture builds a Config.
    for name in _MACHINE_LOCAL_ENV:
        os.environ.pop(name, None)
    yield

FIXTURES_REMOVED = (
    "contract/workbook fixtures are not in the repo (removed 2026-08-22 -- no "
    "client documents in the repository); restore anonymized fixtures to run"
)


def require_fixture_files(*paths: Path) -> None:
    """Skip the calling test/fixture unless every path exists."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        pytest.skip(f"{FIXTURES_REMOVED}: missing {', '.join(p.name for p in missing)}")


@pytest.fixture(scope="session")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _pair_paths(config, index: int) -> tuple[Path, Path]:
    if len(config.contracts.pairs) <= index:
        pytest.skip(f"{FIXTURES_REMOVED}: config.contracts.pairs[{index}] not configured")
    pair = config.contracts.pairs[index]
    contracts_dir = REPO / config.contracts.dir
    frd, sttm = contracts_dir / pair.frd, contracts_dir / pair.sttm
    require_fixture_files(frd, sttm)
    return frd, sttm


@pytest.fixture(scope="session")
def mids_specs(config):
    frd, sttm = _pair_paths(config, 0)
    return resolve_pair(frd, sttm, config)


@pytest.fixture(scope="session")
def caqh_spec(config):
    frd, sttm = _pair_paths(config, 1)
    specs = resolve_pair(frd, sttm, config)
    assert len(specs) == 1
    return specs[0]


@pytest.fixture(scope="session")
def specs_by_id(mids_specs, caqh_spec):
    return {spec.feed_id: spec for spec in [*mids_specs, caqh_spec]}
