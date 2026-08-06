"""Contract models: real fixtures parse; unknown keys fail (extra=forbid)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from codegen.contracts.frd import FrdContract
from codegen.contracts.sttm import SttmContract

REPO = Path(__file__).resolve().parents[1]


def _load(config, name: str) -> dict:
    return json.loads((REPO / config.contracts.dir / name).read_text(encoding="utf-8"))


def test_both_frd_fixtures_parse(config):
    for pair in config.contracts.pairs:
        contract = FrdContract.model_validate(_load(config, pair.frd))
        assert contract.feeds


def test_both_sttm_fixtures_parse(config):
    for pair in config.contracts.pairs:
        contract = SttmContract.model_validate(_load(config, pair.sttm))
        assert contract.feeds


def test_synthetic_marker_is_carried(config):
    raw = _load(config, config.contracts.pairs[1].sttm)
    assert raw["synthetic"] is True


def test_unknown_key_is_rejected(config):
    raw = _load(config, config.contracts.pairs[0].frd)
    raw["surprise_key"] = "x"
    with pytest.raises(ValidationError):
        FrdContract.model_validate(raw)
