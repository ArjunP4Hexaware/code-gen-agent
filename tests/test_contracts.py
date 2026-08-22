"""Contract models: real fixtures parse; unknown keys fail (extra=forbid)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.conftest import require_fixture_files

from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract

REPO = Path(__file__).resolve().parents[1]


def _load(config, name: str) -> dict:
    path = REPO / config.contracts.dir / name
    require_fixture_files(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _require_pairs(config, count: int = 1) -> None:
    if len(config.contracts.pairs) < count:
        pytest.skip("contract fixtures removed from the repo 2026-08-22; pairs not configured")


def test_both_frd_fixtures_parse(config):
    _require_pairs(config)
    for pair in config.contracts.pairs:
        contract = FrdContract.model_validate(_load(config, pair.frd))
        assert contract.feeds


def test_both_sttm_fixtures_parse(config):
    _require_pairs(config)
    for pair in config.contracts.pairs:
        contract = SttmContract.model_validate(_load(config, pair.sttm))
        assert contract.feeds


def test_synthetic_marker_is_carried(config):
    _require_pairs(config, 2)
    raw = _load(config, config.contracts.pairs[1].sttm)
    assert raw["synthetic"] is True


def test_unknown_key_is_rejected(config):
    _require_pairs(config)
    raw = _load(config, config.contracts.pairs[0].frd)
    raw["surprise_key"] = "x"
    with pytest.raises(ValidationError):
        FrdContract.model_validate(raw)
