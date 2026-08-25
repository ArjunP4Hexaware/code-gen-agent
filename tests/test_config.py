"""Config loader: valid file parses; unknown top-level section fails loudly."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codegen.config import load_config

REPO = Path(__file__).resolve().parents[1]


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


def test_config_without_three_input_sections_still_loads(tmp_path):
    # Backward compat: engineering_standards / load_pattern_faq are optional.
    raw = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    raw.pop("engineering_standards", None)
    raw.pop("load_pattern_faq", None)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    config = load_config(path)
    assert config.engineering_standards.create_tables is False
    assert config.engineering_standards.status.startswith("STUB")
    assert config.load_pattern_faq.per_feed_dir == "fixtures/faq"


def test_typo_inside_three_input_section_is_loud(tmp_path):
    raw = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    raw["engineering_standards"]["job_prefix_typo"] = {}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="job_prefix_typo"):
        load_config(path)


def test_non_mapping_config_is_loud(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a YAML mapping"):
        load_config(bad)
