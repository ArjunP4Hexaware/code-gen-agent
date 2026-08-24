"""Load and validate config/config.yaml.

Same convention as the Code Review Agent: every knob lives in the YAML, the
model is frozen with ``extra="forbid"``, and a typo'd *top-level* section name
is caught explicitly — pydantic's own ``extra="forbid"`` never sees keys that
were never passed to it.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")


def load_dotenv(path: str | Path = ".env") -> None:
    """Tiny KEY=VALUE loader; never overrides variables already in the env.

    Shared by every entry point (CLI and UI backend) so ANTHROPIC_API_KEY
    resolves the same way everywhere without a python-dotenv dependency.
    """
    path = Path(path)
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


class ContractPair(BaseModel):
    model_config = _MODEL_CONFIG

    frd: str
    sttm: str


class ContractsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    dir: str
    # May be empty (since 2026-08-22 the repo ships no contract fixtures);
    # generate-all refuses to run on an empty list instead of silently
    # succeeding -- see cli.py.
    pairs: list[ContractPair]


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


class DemoConfig(BaseModel):
    """The demo UI's Live/Replay pipeline inputs (CV/golden universe)."""

    model_config = _MODEL_CONFIG

    # Contract pair for replay + the FRD side of a live extract-sttm run.
    frd: str
    sttm: str
    # Workbook the live demo extracts from (repo-relative path).
    workbook: str
    # Cost-confirmation copy shown before a live run fires.
    estimated_calls: int = Field(gt=0)
    estimated_cost_usd: float = Field(gt=0)
    estimated_seconds: int = Field(gt=0)


class SharePointSettings(BaseModel):
    """Non-secret SharePoint knobs (codegen.sharepoint reads these).

    Identity and the client secret are deliberately absent: SHAREPOINT_
    TENANT_ID / _CLIENT_ID / _CLIENT_SECRET resolve from the environment, so
    a deployment's tenant never lands in the tracked config file. Every field
    here defaults to empty — SharePoint is optional, and an unconfigured repo
    must load its config and run the whole generator exactly as before.
    """

    model_config = _MODEL_CONFIG

    host: str = ""            # e.g. contoso.sharepoint.com
    site_path: str = ""       # server-relative, must start with '/'
    library: str = ""         # document library display name
    input_folder: str = ""    # workbooks + contracts in; "" = library root
    output_folder: str = ""   # generated artifacts out


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
    demo: DemoConfig
    gate: GateConfig
    job: JobConfig
    # Optional: a config.yaml with no `sharepoint:` section still loads, and
    # every SharePoint entry point then fails loudly on the missing values
    # rather than this being a load-time error for repos that never use it.
    sharepoint: SharePointSettings = SharePointSettings()


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
