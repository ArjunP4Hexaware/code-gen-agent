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


class DemoInputDocumentsConfig(BaseModel):
    """Reference documents the demo documents card checks for (display only).

    ``expected`` holds filenames as they appear in the client SharePoint
    library; matching is case-insensitive and strips a leading numeric upload
    prefix. ``dirs`` are repo-relative scan directories, overridable by the
    env var ``CODEGEN_INPUT_DOCS_DIR`` (``os.pathsep``-separated) — env >
    YAML, same as the SharePoint knobs. Both default empty: a config without
    the section loads and the card simply lists nothing as expected.
    """

    model_config = _MODEL_CONFIG

    expected: list[str] = Field(default_factory=list)
    dirs: list[str] = Field(default_factory=list)


class DemoLoadStrategyConfig(BaseModel):
    """Stand-in load strategies shown (badged SYNTHETIC) on the demo panel."""

    model_config = _MODEL_CONFIG

    stage: str = "Truncate and Load"
    standard: str = "Upsert"


class DemoSourceFilesConfig(BaseModel):
    """Synthesis knobs for the "source files this run will read" panel.

    ``landing_root_template`` encodes the client's landing-path CONVENTION
    (as stated in the real FRD's Structural Metadata) as a template — the
    literal client path never lives in this repo; it is displayed only when
    read from the document itself at runtime.
    """

    model_config = _MODEL_CONFIG

    landing_root_template: str = "mftlanding/inbound/{domain}/{sub_domain}/{source_system}"
    load_strategy: DemoLoadStrategyConfig = DemoLoadStrategyConfig()


class DemoDatabricksPathsConfig(BaseModel):
    """Placeholder UC volume coordinates for the synthetic shell listing.

    Placeholders until Databricks discovery replaces them with real values;
    the shell block stays labelled SYNTHETIC until a live listing exists.
    """

    model_config = _MODEL_CONFIG

    catalog: str = "hexaware_demo"
    # "schema" shadows BaseModel.schema; keep the YAML name via alias.
    schema_name: str = Field(default="landing", alias="schema")
    volume: str = "mft"


class DemoMetadataTabConfig(BaseModel):
    """One tab of the metadata-sheet preview: its column headers, in order."""

    model_config = _MODEL_CONFIG

    headers: list[str] = Field(min_length=1)


def _default_metadata_tabs() -> dict[str, DemoMetadataTabConfig]:
    return {
        "file_layout": DemoMetadataTabConfig(
            headers=[
                "pipeline_id", "group_id", "object_id", "feed_name", "source_system",
                "landing_path", "file_pattern", "file_format", "delimiter",
                "has_header", "has_trailer", "frequency",
            ]
        ),
        "load_config": DemoMetadataTabConfig(
            headers=[
                "pipeline_id", "object_id", "layer", "target_schema", "target_table",
                "load_strategy", "dedup_keys", "cluster_id", "service_principal",
            ]
        ),
        "columns": DemoMetadataTabConfig(
            headers=[
                "object_id", "ordinal", "column_name", "data_type", "nullable",
                "source_column", "transformation",
            ]
        ),
    }


class DemoMetadataSheetConfig(BaseModel):
    """Stand-in layout for the ACFC metadata-sheet preview (display only).

    The tab names and headers are OUR guess at the client's metadata Excel
    template; the client's template defines the real tabs and columns, and
    the panel says so on its face. ``always_blank`` headers are assigned by
    the client's framework (or manually, by client instruction) — the agent
    leaves them empty and flags them rather than guessing.
    """

    model_config = _MODEL_CONFIG

    tabs: dict[str, DemoMetadataTabConfig] = Field(default_factory=_default_metadata_tabs)
    always_blank: list[str] = Field(
        default_factory=lambda: [
            "pipeline_id", "group_id", "object_id", "cluster_id", "service_principal",
        ]
    )


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
    # Display-only panels (codegen.demo_sources); all default so an older
    # config still loads unchanged.
    input_documents: DemoInputDocumentsConfig = DemoInputDocumentsConfig()
    source_files: DemoSourceFilesConfig = DemoSourceFilesConfig()
    databricks_paths: DemoDatabricksPathsConfig = DemoDatabricksPathsConfig()
    metadata_sheet: DemoMetadataSheetConfig = DemoMetadataSheetConfig()


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


class TypeMappingEntry(BaseModel):
    """One source→target datatype override from the client standards doc."""

    model_config = _MODEL_CONFIG

    source: str
    target: str


class EngineeringStandardsConfig(BaseModel):
    """Client engineering/coding standards (three-input model, input #2).

    The DEFAULTS here are still the honest STUB (a config.yaml without this
    section degrades to the legacy behavior and the gate flags it); the real
    values — from the EDO Data Engineering Naming Standards and EDO Data
    Engineering Coding Standards documents — live in config/config.yaml.

    Naming placeholders available to ``job_name_pattern`` /
    ``notebook_name_pattern`` (resolved in codegen.emit.context):
    ``{prefix}`` ``{slug}`` ``{feed}`` (the slug, sanitized uppercase)
    ``{product}`` ``{subproduct}`` ``{source}``
    ``{domain}`` ``{subdomain}`` ``{lob}`` ``{frequency}``. Unresolvable
    components render empty and consecutive underscores collapse, so a
    partially-known feed still gets a deterministic, legal name.
    """

    model_config = _MODEL_CONFIG

    status: str = "STUB — awaiting client engineering standards document"
    job_prefix_by_frequency: dict[str, str] = Field(
        default_factory=lambda: {
            "daily": "D_",
            "weekly": "W_",
            "monthly": "M_",
            "yearly": "Y_",
            "adhoc": "A_",
        }
    )
    job_name_pattern: str = "{prefix}ingest_{slug}"
    # EDO Databricks naming: NB_<product>_<subproduct>_<domain>_<subdomain>_
    # <functionality>. Empty = legacy "notebook_entrypoint" workspace leaf.
    notebook_name_pattern: str = ""
    # EDO naming-standard abbreviation tables (3-char product/sub-product
    # codes, source/domain/LOB/frequency abbreviations). Lookups are
    # case-insensitive on the normalized key; an unmapped value falls back to
    # its sanitized uppercase form rather than failing generation.
    product_code: str = ""
    sub_product_code: str = ""
    source_abbreviations: dict[str, str] = Field(default_factory=dict)
    domain_abbreviations: dict[str, str] = Field(default_factory=dict)
    lob_abbreviations: dict[str, str] = Field(default_factory=dict)
    frequency_abbreviations: dict[str, str] = Field(default_factory=dict)
    # A feed with no resolvable frequency ships unscheduled, i.e. it runs
    # ad hoc — the EDO abbreviation for that is the honest default.
    unknown_frequency_abbreviation: str = "ADH"
    # A feed spanning more than one LOB uses the EDO "All" abbreviation.
    multi_lob_abbreviation: str = "ALL"
    # MVP prerequisite: raw/stage/standard tables already exist in the target
    # environment; DDL is emitted as reference only and the notebook lists the
    # tables as prerequisites instead of creating them.
    create_tables: bool = False
    type_mapping: list[TypeMappingEntry] = Field(default_factory=list)


class LoadPatternFaqConfig(BaseModel):
    """Where per-feed load-pattern FAQ answer files live (codegen.faq)."""

    model_config = _MODEL_CONFIG

    schema_version: int = 1
    # <feed_slug>.faq.yaml per feed; a missing file means every answer
    # defaults with source "unknown" — never an error.
    per_feed_dir: str = "fixtures/faq"


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
    # EDO coding standard: never leave the default (7-day) timeout in place —
    # set it to expected execution hours + 1. Emitted as timeout_seconds.
    timeout_hours: int = Field(gt=0, default=2)
    # EDO coding standard: DBR >= 15.4 LTS with Photon enabled. Empty = omit
    # the runtime_engine key from the generated cluster spec.
    runtime_engine: str = ""


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
    # Optional (three-input model, added for the Raj feedback pass): both
    # sections default so an older config still loads unchanged.
    engineering_standards: EngineeringStandardsConfig = EngineeringStandardsConfig()
    load_pattern_faq: LoadPatternFaqConfig = LoadPatternFaqConfig()


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
