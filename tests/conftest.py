"""Shared fixtures: the real config and both resolved contract pairs.

These tests exercise the GENERATOR (no Spark). Generated-code tests live in
``out/<feed>/tests`` and run under the gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _pair_paths(config, index: int) -> tuple[Path, Path]:
    pair = config.contracts.pairs[index]
    contracts_dir = REPO / config.contracts.dir
    return contracts_dir / pair.frd, contracts_dir / pair.sttm


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
