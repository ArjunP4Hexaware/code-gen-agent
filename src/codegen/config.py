"""Load and validate config/config.yaml.

Same convention as the Code Review Agent: every knob lives in the YAML, the
model is frozen with ``extra="forbid"``, and a typo'd *top-level* section name
is caught explicitly — pydantic's own ``extra="forbid"`` never sees keys that
were never passed to it.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ExtractorBandLabels(BaseModel):
    model_config = _MODEL_CONFIG

    source: str
    stage: str
    standard: str


class ExtractorFileDetailsHeaders(BaseModel):
    model_config = _MODEL_CONFIG

    vendor: list[str]
    file_name: list[str]
    frequency: list[str]


# Logical source-block columns the workbook parser must be able to resolve.
_REQUIRED_HEADER_KEYS = {
    "source_column",
    "description",
    "sample_value",
    "source_datatype",
    "null_check",
    "phi",
    "mandatory",
}
_OPTIONAL_HEADER_KEYS = {"value_spec"}


class ExtractorConfig(BaseModel):
    model_config = _MODEL_CONFIG

    file_details_sheet: str
    version_history_sheet: str
    mapping_sheet_prefix: str
    band_labels: ExtractorBandLabels
    header_synonyms: dict[str, list[str]]
    table_block_headers: list[str] = Field(min_length=4, max_length=4)
    recycle_header_prefix: str
    audit_source_markers: list[str] = Field(min_length=1)
    file_details_headers: ExtractorFileDetailsHeaders
    recycle_on_match: str
    recycle_on_no_match: str

    @model_validator(mode="after")
    def _check_header_synonym_keys(self) -> ExtractorConfig:
        keys = set(self.header_synonyms)
        missing = _REQUIRED_HEADER_KEYS - keys
        unknown = keys - _REQUIRED_HEADER_KEYS - _OPTIONAL_HEADER_KEYS
        problems = []
        if missing:
            problems.append(f"missing required header_synonyms keys: {sorted(missing)}")
        if unknown:
            problems.append(f"unknown header_synonyms keys: {sorted(unknown)}")
        if problems:
            raise ValueError("extractor config: " + "; ".join(problems))
        return self


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
    extractor: ExtractorConfig
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
