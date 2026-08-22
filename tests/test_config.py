"""Config loader: valid file parses; unknown top-level section fails loudly."""

from __future__ import annotations

import pytest

from codegen.config import load_config


def test_real_config_loads(config):
    # pairs may be empty since 2026-08-22 (fixtures removed); the section and
    # its contracts dir must still parse.
    assert config.contracts.dir
    assert isinstance(config.contracts.pairs, list)
    assert config.masking.policy == "last4"
    assert config.gate.pytest_tail_lines > 0


def test_unknown_top_level_section_is_loud(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("contracts_typo:\n  dir: x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown top-level config section"):
        load_config(bad)


def test_non_mapping_config_is_loud(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a YAML mapping"):
        load_config(bad)
