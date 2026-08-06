"""Load and validate config/config.yaml.

Same convention as the Code Review Agent: every knob lives in the YAML, the
model is frozen with ``extra="forbid"``, and a typo'd *top-level* section name
is caught explicitly — pydantic's own ``extra="forbid"`` never sees keys that
were never passed to it.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


class ContractPair(BaseModel):
    model_config = _MODEL_CONFIG

    frd: str
    sttm: str


class ContractsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    dir: str
    pairs: list[ContractPair] = Field(min_length=1)


class OutputConfig(BaseModel):
    model_config = _MODEL_CONFIG

    dir: str
    reports_dir: str


class NamingConfig(BaseModel):
    model_config = _MODEL_CONFIG

    errors_table_suffix: str
    recycle_table_suffix: str
    processed_files_table_suffix: str


class DefaultsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    recycle_window_days: int = Field(gt=0)


class MaskingConfig(BaseModel):
    model_config = _MODEL_CONFIG

    policy: str
    visible_chars: int = Field(gt=0)
    mask_char: str = Field(min_length=1, max_length=1)


class SegmentsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    record_type_column: str
    record_type_values: dict[str, str]
    # Source column on the Trailer segment carrying the Detail record count.
    trailer_count_column: str


class ReasoningConfig(BaseModel):
    model_config = _MODEL_CONFIG

    model: str
    max_tokens: int = Field(gt=0)
    max_attempts: int = Field(gt=0)


class GateConfig(BaseModel):
    model_config = _MODEL_CONFIG

    run_generated_tests: bool
    ruff: bool
    structural_checks: bool
    debug_patterns: list[str]
    pytest_tail_lines: int = Field(gt=0)


class JobConfig(BaseModel):
    model_config = _MODEL_CONFIG

    notification_emails: list[str]
    spark_version: str
    node_type_id: str
    num_workers: int = Field(ge=0)


class Config(BaseModel):
    model_config = _MODEL_CONFIG

    contracts: ContractsConfig
    feed_aliases: dict[str, str]
    output: OutputConfig
    naming: NamingConfig
    defaults: DefaultsConfig
    masking: MaskingConfig
    segments: SegmentsConfig
    reasoning: ReasoningConfig
    gate: GateConfig
    job: JobConfig


_TOP_LEVEL_KEYS = set(Config.model_fields)


def load_config(path: str | Path) -> Config:
    """Load the YAML config, failing loudly on unknown top-level sections."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"config file {path} is not a YAML mapping")
    unknown = set(raw) - _TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(
            f"unknown top-level config section(s) {sorted(unknown)}; "
            f"expected only {sorted(_TOP_LEVEL_KEYS)}"
        )
    return Config.model_validate(raw)
