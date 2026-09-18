"""Load and validate config/config.yaml.

Same convention as the Code Review Agent: every knob lives in the YAML, the
model is frozen with ``extra="forbid"``, and a typo'd *top-level* section name
is caught explicitly — pydantic's own ``extra="forbid"`` never sees keys that
were never passed to it.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

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
    # Option A ("notebook", the default — today's output exactly), Option B
    # ("framework": DDL scripts + config rows + insert statements for the
    # existing ingestion framework, no notebook/module tree), or "both".
    # "rfc" (M5): framework artefacts + the assembled RFC deployment package
    # (out/<slug>/RFC<number>_<Feed>/), see RfcConfig / PlaybookConfig.
    # "all" = notebook tree + framework artefacts + the RFC package.
    mode: Literal["notebook", "framework", "both", "rfc", "all"] = "notebook"


class FrameworkConfig(BaseModel):
    """Option B knobs — the additive output for ACFC's ingestion framework.

    The row layout is NOT duplicated here: ``metadata_layout`` names the
    single source of truth (``demo.metadata_sheet``) the config rows are
    built from. ``always_blank`` ID columns render as ``id_placeholder`` in
    the inserts — assigned by the client's framework, never invented.
    """

    model_config = _MODEL_CONFIG

    metadata_layout: str = "demo.metadata_sheet"
    sql_dialect: Literal["sqlserver", "lakebase"] = "sqlserver"
    id_placeholder: str = "NULL"
    # Optional per-tab table override, e.g. {file_layout: dbo.ig_file_layout}.
    tables: dict[str, str] = Field(default_factory=dict)
    # Prefix for the SYNTHETIC stage LOCATION in the deployment-team DDL .txt
    # files — clearly labeled, never a real container/storage account (the
    # real ones are assigned by the client platform).
    synthetic_location_prefix: str = (
        "abfss://syn-container-stage@synstorage.dfs.synthetic.example")
    # The deployment-team .txt files carry exactly the FRD's Target Table
    # Name list by default: the errors/processed-files side-tables are
    # CodeGen conventions absent from the FRD, the STTM, and the client
    # reference goldens. They remain in out/<slug>/ddl/ and in notebook mode
    # regardless.
    deployment_ddl_include_side_tables: bool = False


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


class SegmentedExtractorConfig(BaseModel):
    """Layout knobs for the segmented (CAQH-style) workbook family — one wide
    mapping sheet: key:value metadata block, band-label row (discovered by
    scan, not positional), header row beneath it, per-row Segment column,
    per-segment audit rows with empty source cells. Vocabulary transcribed
    from the real workbook's structural characterization
    (docs/SEGMENTED_MODE_DESIGN.md) — all matching is fuzzy (lowercased,
    whitespace-collapsed) like the flat extractor's."""

    model_config = _MODEL_CONFIG

    # Band-label variants this family uses for the source band.
    source_band_variants: list[str] = Field(
        default_factory=lambda: ["Source Layout", "Source File Layout"])
    # Metadata-block keys (col A) -> logical facts.
    metadata_keys: dict[str, str] = Field(default_factory=lambda: {
        "files": "File(s)",
        "generator": "File Generator",
        "location": "File Location",
        "lob": "LOB",
        "frequency": "File frequency",
        "domain": "Domain",
        "sub_domain": "Sub-Domain",
        "file_type": "File type",
    })
    # Source-block header synonyms (logical -> accepted spellings).
    source_headers: dict[str, list[str]] = Field(default_factory=lambda: {
        "ordinal": ["#"],
        "field_name": ["Field Name"],
        "datatype": ["Data Type"],
        "length": ["Length"],
        "fixed_width_length": ["Field Length (fixed width)"],
        "fixed_width_start": ["Start position (fixed width)"],
        "fixed_width_end": ["End Position (fixed width)"],
        "segment": ["Segment (Ex:Header,Trailer,Detail)", "Segment"],
        "pii": ["PII"],
        "comments": ["Comments"],
        "business_rule": ["Business Rule"],
    })
    # Stage/Standard block header vocabulary (identical for both bands).
    table_headers: list[str] = Field(default_factory=lambda: [
        "Catalog", "Schema", "TableName", "ColumnName", "DataType",
        "Mandatory Column", "Primary Key", "Field Description",
        "Table Description", "Transformations/Data Quality",
    ])
    # Canonical segment names as the Segment column spells them.
    segment_names: dict[str, str] = Field(default_factory=lambda: {
        "header": "Header", "detail": "Detail", "trailer": "Trailer",
    })
    # Member-existence recycle (FRD 1005034 Data Quality Functional
    # Requirement: "Perform Member Id validation for existence against the
    # Facets_Member table in the Stage layer. If Member doesn't exist, then
    # move the record to RECYCLE table."). The field name is matched against
    # the STTM's source Field Name; the reference table name is transcribed
    # from that FRD requirement — never invented by the agent.
    member_field: str = "Member ID"
    member_reference_table: str = "facets_member"


class ValidateConfig(BaseModel):
    """Plausibility thresholds of the layout-profile validator (M2.5 §4):
    the share of data cells under a claimed header that must look the part
    before a model- or user-placed role is accepted."""

    model_config = _MODEL_CONFIG

    integer_like: float = Field(default=0.8, ge=0, le=1)
    type_like: float = Field(default=0.8, ge=0, le=1)
    yes_no_like: float = Field(default=0.8, ge=0, le=1)
    field_name_non_empty: float = Field(default=0.9, ge=0, le=1)
    # Type tokens the generator already accepts (emit.context._SQL_TYPES,
    # DECIMAL(p,s)) plus the COBOL-style pictures the source bands use.
    type_token_regex: str = (
        r"(?:[a-z]+(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?"
        r"|s?9\(\d+\)(?:v9+|v\d+)?|x\(\d+\)|an|n|x|9)")


class DiscoveryConfig(BaseModel):
    """Content-driven layout discovery vocabulary (M1) — the synonym tables
    behind ``codegen.layout.discover``. EVERYTHING here is data: band-label
    tokens per layer, header→role synonyms per band group, meta-row label
    synonyms, segment spellings, auxiliary-sheet header signatures, yes/no
    spellings. The model defaults are EMPTY on purpose: a config without the
    tables resolves nothing and discovery says so loudly, rather than
    carrying a second copy of the vocabulary in code."""

    model_config = _MODEL_CONFIG

    # How many leading rows are scanned for band / header / meta rows.
    scan_rows: int = Field(default=40, gt=0)
    # layer -> band-label tokens (normalized substring match).
    band_tokens: dict[str, list[str]] = Field(default_factory=dict)
    # band group ("source" | "rules" | "target" | "trailing") -> role -> header
    # spellings. "target" serves both the stage and the standard band.
    roles: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    # meta key -> label spellings (label:value rows above the band row).
    meta_synonyms: dict[str, list[str]] = Field(default_factory=dict)
    # canonical segment (Header/Detail/Trailer) -> spellings seen in Segment
    # columns, sheet names and in-sheet banner rows.
    segment_synonyms: dict[str, list[str]] = Field(default_factory=dict)
    # sheet kind -> alternatives, each a list of header tokens that must ALL
    # appear (normalized substring) on one of the first rows.
    auxiliary_sheets: dict[str, list[list[str]]] = Field(default_factory=dict)
    yes_values: list[str] = Field(default_factory=list)
    no_values: list[str] = Field(default_factory=list)
    # Validator thresholds (M2.5 §4).
    validate: ValidateConfig = ValidateConfig()

    @model_validator(mode="after")
    def _check_vocabulary(self) -> DiscoveryConfig:
        from codegen.layout.profile import Role

        known_roles = {r.value for r in Role}
        problems = []
        for group, table in self.roles.items():
            if group not in {"source", "rules", "target", "trailing"}:
                problems.append(f"unknown roles group {group!r}")
            unknown = set(table) - known_roles
            if unknown:
                problems.append(f"roles.{group}: unknown role(s) {sorted(unknown)}")
        for layer in self.band_tokens:
            if layer not in {"source", "rules", "stage", "standard"}:
                problems.append(f"band_tokens: unknown layer {layer!r}")
        if problems:
            raise ValueError("extractor.discovery config: " + "; ".join(problems))
        return self


class FrdExtractorConfig(BaseModel):
    """FRD .docx extractor vocabulary (M2, codegen.extract.frd_docx): section
    titles, label synonyms (ONLY the variants SHAPES_FOR_PORT §2 lists), the
    Solution Requirement table shape, and the separators used to split a
    cell into list values. Empty defaults = nothing resolves, loudly."""

    model_config = _MODEL_CONFIG

    section_titles: dict[str, list[str]] = Field(default_factory=dict)
    labels: dict[str, list[str]] = Field(default_factory=dict)
    # Rows 1-3 of every F1 section table (and the F2 SR rows) by label.
    fixed_rows: dict[str, list[str]] = Field(default_factory=dict)
    solution_requirement_prefix: str = "Solution Requirement"
    # 0-based row index whose first cell names the metadata section (F2).
    solution_requirement_section_row: int = Field(default=4, ge=1)
    inline_pair_separators: list[str] = Field(default_factory=lambda: [";"])
    list_separators: list[str] = Field(default_factory=lambda: [",", ";", "\n"])
    domain_separators: list[str] = Field(default_factory=lambda: ["/", ","])
    target_schema_markers: dict[str, list[str]] = Field(default_factory=dict)
    target_schema_separators: list[str] = Field(default_factory=lambda: ["/", ";"])
    acd_headers: list[str] = Field(default_factory=lambda: ["ACD Type", "Name", "Description"])
    # Cell texts that mean "blank" (a stated placeholder, never a value).
    blank_values: list[str] = Field(default_factory=list)
    # M7: a value containing one of these phrases points at another document
    # ("refer to the File Details tab of the mapping document"): UNSTATED +
    # flag frd_pointer, resolved through the fallback chain. Never a value.
    pointer_phrases: list[str] = Field(default_factory=list)
    # M7: fields whose value must be one line — a nested table, per-file
    # blocks, a label-prefixed description or remaining line breaks make
    # them unstated (StructuredValue) instead of a value.
    single_line_fields: list[str] = Field(default_factory=list)
    # M7: words that mark the first row of a nested table as a header row.
    nested_table_header_words: list[str] = Field(default_factory=list)
    # M7: how much of a refused cell's text the contract keeps (logged only).
    structured_text_max_chars: int = Field(default=200, gt=0)


class VddExtractorConfig(BaseModel):
    """Vendor Data Dictionary vocabulary (M3): FILES-sheet and field-sheet
    role synonyms — ONLY the V1/V2/V3 headers of SHAPES_FOR_PORT §3 —
    header signatures, the type-equivalence classes of the STTM-vs-VDD
    cross-check and the fixed-width format tokens. Empty = nothing
    resolves, loudly."""

    model_config = _MODEL_CONFIG

    files_signature: list[list[str]] = Field(default_factory=list)
    fields_signature: list[list[str]] = Field(default_factory=list)
    files_roles: dict[str, list[str]] = Field(default_factory=dict)
    field_roles: dict[str, list[str]] = Field(default_factory=dict)
    # Type tokens that are one class (never a vdd_mismatch:type).
    type_equivalence: list[list[str]] = Field(default_factory=list)
    # FRD file-format words that mean fixed width (positions required).
    fixed_width_tokens: list[str] = Field(default_factory=list)


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
    # Segmented (CAQH-style) family knobs — all defaulted, so a config
    # without the section still loads.
    segmented: SegmentedExtractorConfig = SegmentedExtractorConfig()
    # Content-driven discovery vocabulary (M1); empty tables = nothing
    # resolves beyond the two legacy strategies, loudly.
    discovery: DiscoveryConfig = DiscoveryConfig()
    # FRD .docx extractor vocabulary (M2); empty = nothing resolves, loudly.
    frd: FrdExtractorConfig = FrdExtractorConfig()
    # Vendor Data Dictionary vocabulary (M3); empty = nothing resolves, loudly.
    vdd: VddExtractorConfig = VddExtractorConfig()

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
    # Layer-2 transport: "anthropic" (default, direct API) or
    # "databricks_fmapi" (the same Claude model served by Databricks
    # Foundation Model APIs — a transport, not a vendor change; Anthropic
    # remains the sole model vendor). Mock always wins on dry-run.
    provider: str = "anthropic"


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
    """UC volume coordinates the shell block renders/lists against.

    Real since 2026-08-27: the landing volume is created and seeded with
    SYNTHETIC files by `codegen databricks-seed-landing`; live mode lists
    it through the volumes seam, synthetic mode stays the offline fallback.
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
    # Selection-time VDD pairing (2026-09-18): canonical STTM stem -> VDD
    # stem, tried before the shared-ticket and name-stem rules. Optional.
    vdd_pairing_map: dict[str, str] = Field(default_factory=dict)
    # Workbook the live demo extracts from (repo-relative path).
    workbook: str
    # Cost-confirmation copy shown before a live run fires.
    estimated_calls: int = Field(gt=0)
    estimated_cost_usd: float = Field(gt=0)
    estimated_seconds: int = Field(gt=0)
    # Display-only panels (codegen.demo_sources); all default so an older
    # config still loads unchanged.
    # Shell-block source: live (list the real landing volume) | synthetic
    # (offline renderer) | auto (live when creds resolve and the volume
    # exists, else synthetic — the response says which branch ran).
    shell_listing: Literal["live", "synthetic", "auto"] = "synthetic"
    input_documents: DemoInputDocumentsConfig = DemoInputDocumentsConfig()
    # Explicit STTM->FRD pairing by canonical document stem — checked FIRST
    # (before ticket numbers); the token heuristic is a UI suggestion only.
    pairing_map: dict[str, str] = Field(default_factory=dict)
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


class DatabricksSettings(BaseModel):
    """Non-secret Databricks volumes knobs (codegen.databricks reads these).

    Credentials are deliberately absent: auth is whatever the named profile
    resolves (CLI OAuth keyring, or DATABRICKS_HOST/TOKEN env for a
    deployment). Every field defaults empty — Databricks is optional, and an
    unconfigured repo loads its config and runs the whole generator exactly
    as before. Each knob is overridable by the uppercased DATABRICKS_* env
    var of the same name (env > YAML).
    """

    model_config = _MODEL_CONFIG

    profile: str = ""       # ~/.databrickscfg profile name
    catalog: str = ""       # e.g. soham_workspace
    # "schema" shadows BaseModel.schema; keep the YAML name via alias.
    schema_name: str = Field(default="", alias="schema")
    frd_volume: str = ""    # raw client FRD documents in
    sttm_volume: str = ""   # raw client STTM workbooks in
    # B1 knobs — empty means the function needing one fails loudly:
    warehouse_id: str = ""           # EXPLAIN-only; waking it bills DBUs
    serving_endpoint: str = ""       # FMAPI chat endpoint (Claude transport)
    wrapper_notebook_path: str = ""  # client-supplied; none exists here yet
    # The writable volumes (codegen.databricks.WRITABLE_PREFIX guards both
    # by construction): landing_volume is seeded with synthetic files by
    # databricks-seed-landing; output_volume receives reviewed artifacts via
    # the human-gated `databricks-publish` (2026-08-28 explicit go).
    landing_volume: str = ""
    output_volume: str = ""
    # Allowlist for read_table_rows (SELECT-only, statement rendered in
    # code). Reading any table NOT listed here is refused. First read wakes
    # the serverless warehouse = DBU spend.
    readable_tables: list[str] = Field(default_factory=list)


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


class LayoutConfig(BaseModel):
    """Layout recognition (M2.5): profile caches, the mock answer directory,
    the provider posture and the confidence a model-placed role starts with.
    Paths are repo-relative. A config without the section still loads."""

    model_config = _MODEL_CONFIG

    # Repo cache(s) of completed profiles, searched in order, keyed by the
    # ``fingerprint`` field inside each JSON file.
    cache_dirs: list[str] = Field(default_factory=lambda: ["fixtures/layout_profiles"])
    # Runtime cache (gitignored under ui/backend/state/) for profiles a
    # model + validation or a person completed.
    runtime_cache_dir: str = "ui/backend/state/layout_profiles"
    # Mock provider answers (adversarial + hand-written), then cache_dirs.
    mock_dir: str = "fixtures/layout_profiles/mock"
    # auto (live when Layer 2 is live) | mock (never call a model).
    provider: Literal["auto", "mock"] = "auto"
    max_tokens: int = Field(default=8192, gt=0)
    max_attempts: int = Field(default=2, gt=0)
    # Confidence a model-placed role starts with (validated, not trusted).
    model_confidence: float = Field(default=0.8, ge=0, le=1)
    # Confidence bump a cross-document agreement adds (capped at 1.0).
    crosscheck_bonus: float = Field(default=0.1, ge=0, le=1)


class ConventionsProfileConfig(BaseModel):
    """One client conventions profile (M4): how the deployment DDL is laid
    out. ``edo_sfmc`` (two files, the SFMC reference goldens) is today's
    output exactly; ``acfc_prx`` is the pair-1 combined-file shape. Every
    whitespace knob is data because the client golden is compared byte for
    byte."""

    model_config = _MODEL_CONFIG

    # two_files: <slug>_stage/_standard_table_creation.txt (today) |
    # combined: ONE file with '--stage table' / '--standard table' banners.
    ddl_layout: Literal["two_files", "combined"] = "two_files"
    # combined-layout file name; {feed_abbrev} = the FAQ's feed_abbreviation
    # (client-assigned), else the sanitized slug + a flag.
    ddl_file_name_pattern: str = "{feed_abbrev}_DDL.txt"
    # Stage columns typed as the STTM stage band states them (not STRING).
    typed_stage: bool = False
    # Standard table column list = the stage list (client convention).
    standard_from_stage: bool = False
    create_statement: str = "CREATE OR REPLACE TABLE"
    using_clause: str = "USING delta"
    stage_banner: str = "--stage table"
    standard_banner: str = "--standard table"
    leading_newline: bool = False
    trailing_newline: bool = True
    # Text between the closing ')' line and the USING clause, per block.
    block_using_prefix: dict[str, str] = Field(default_factory=dict)
    # Audit-column type spelling in the DDL (contract enum -> as written).
    audit_type_casing: dict[str, str] = Field(default_factory=dict)


class ConventionsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    profile: str = "edo_sfmc"
    profiles: dict[str, ConventionsProfileConfig] = Field(
        default_factory=lambda: {"edo_sfmc": ConventionsProfileConfig()})

    @model_validator(mode="after")
    def _profile_exists(self) -> ConventionsConfig:
        if self.profile not in self.profiles:
            raise ValueError(f"conventions.profile {self.profile!r} is not one of "
                             f"{sorted(self.profiles)}")
        return self

    def get(self, name: str | None) -> ConventionsProfileConfig:
        key = name or self.profile
        if key not in self.profiles:
            raise ValueError(f"unknown conventions profile {key!r}; expected one of "
                             f"{sorted(self.profiles)}")
        return self.profiles[key]


class MetadataTemplateConfig(BaseModel):
    """An IIG workbook template version (M4) other than the default
    ``iig_v1`` (= ``demo.metadata_sheet``): sheets + headers transcribed
    from the client's golden, the framework-assigned always-blank columns,
    and the derivation knobs the row builders read. ``constants`` /
    ``template_rows`` are framework vocabulary the config carries WITH its
    citation — never a guess."""

    model_config = _MODEL_CONFIG

    tabs: dict[str, DemoMetadataTabConfig]
    always_blank: list[str] = Field(default_factory=list)
    citation: str = ""
    # SRC_COLUMNS: name_pair 'src:stage' | positional 'col<i>:<stage>'.
    src_columns_style: Literal["name_pair", "positional"] = "name_pair"
    # SRC_DATA_TYPE pairs: full types | base types ('Decimal' for Decimal(17,2)).
    data_type_style: Literal["full", "base"] = "full"
    rows_per_file_pattern: bool = False
    object_name_from_pattern: bool = False
    reject_table_suffix: str | None = None
    segment_filter_pattern: str | None = None
    dq_rules: list[Literal["date_format", "data_type_cast"]] = Field(default_factory=list)
    dq_rule_classes: dict[str, str] = Field(default_factory=dict)
    date_format_rule_regex: str = r"^\s*Convert\s+(\S+)\s+to\s+(\S+)\s*$"
    date_format_param_joiner: str = "--"
    cast_type_order: list[str] = Field(default_factory=list)
    audit_type_casing: dict[str, str] = Field(default_factory=dict)
    # tab -> header -> path shape with {landing} {stage_table} {reject_table}
    # (the golden spells the archive path differently per sheet).
    path_patterns: dict[str, dict[str, str]] = Field(default_factory=dict)
    constants: dict[str, dict[str, str]] = Field(default_factory=dict)
    # tab -> rows of header -> value; keys starting with '_' steer the
    # builder (e.g. _layer: standard) and never render.
    template_rows: dict[str, list[dict[str, str]]] = Field(default_factory=dict)


class MetadataConfig(BaseModel):
    model_config = _MODEL_CONFIG

    # iig_v1 = demo.metadata_sheet (today's layout, byte for byte).
    template: str = "iig_v1"
    templates: dict[str, MetadataTemplateConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _template_exists(self) -> MetadataConfig:
        if self.template != "iig_v1" and self.template not in self.templates:
            raise ValueError(f"metadata.template {self.template!r} is neither iig_v1 nor one of "
                             f"{sorted(self.templates)}")
        return self

    def resolve(self, name: str | None) -> tuple[str, MetadataTemplateConfig | None]:
        key = name or self.template
        if key == "iig_v1":
            return key, None
        if key not in self.templates:
            raise ValueError(f"unknown IIG template {key!r}; expected iig_v1 or one of "
                             f"{sorted(self.templates)}")
        return key, self.templates[key]


class RfcConfig(BaseModel):
    """`rfc` output mode (M5): the INGESTION-family package tree of
    RFC_PACKAGE_SHAPES §1. Tokens: {rfc_number} (FAQ rfc_number, else
    number_placeholder + flag), {feed_slug} / {feed} (FAQ feed_abbreviation,
    else the sanitized feed slug + flag)."""

    model_config = _MODEL_CONFIG

    dir_pattern: str = "RFC{rfc_number}_{feed_slug}"
    iig_file_name: str = "{feed_slug}_IIG.xlsx"
    playbook_file_name: str = "RFC{rfc_number}_{feed_slug}_Deployment_Playbook.xlsx"
    manifest_file_name: str = "MANIFEST.md"
    # The shapes document's own masked spelling of an RFC number.
    number_placeholder: str = "######"
    file_log_information: bool = False
    file_log_file_name: str = "FILE_LOG_INFORMATION.txt"
    file_log_header_line: str = "CREATE TABLE [dbo].[FILE_LOG_INFORMATION]("
    # Column definitions in the documented T-SQL shape; a masked value such
    # as <length> is transcribed as documented and flagged.
    file_log_columns: list[str] = Field(default_factory=list)


class PlaybookTaskConfig(BaseModel):
    model_config = _MODEL_CONFIG

    task: str
    detail: str = ""


class PlaybookTasksConfig(BaseModel):
    """Task rows per playbook section. A row is here or the cell is blank."""

    model_config = _MODEL_CONFIG

    pre_production: list[PlaybookTaskConfig] = Field(default_factory=list)
    production: list[PlaybookTaskConfig] = Field(default_factory=list)
    post_production: list[PlaybookTaskConfig] = Field(default_factory=list)
    rollback_execution: list[PlaybookTaskConfig] = Field(default_factory=list)
    rollback_validation: list[PlaybookTaskConfig] = Field(default_factory=list)


class PlaybookTemplateConfig(BaseModel):
    """sfmc_7sheet: the 7-sheet IS-methodology template read from the
    scrubbed reference workbook (structure kept, values blank-and-flag);
    main_single: the single 'Main' sheet of the PRX packages (header
    pattern per RFC_PACKAGE_SHAPES §1)."""

    model_config = _MODEL_CONFIG

    kind: Literal["sfmc_7sheet", "main_single"]
    # sfmc_7sheet
    source: str | None = None
    header_row: int = 2
    task_sheet: str | None = None
    rollback_execution_sheet: str | None = None
    rollback_validation_sheet: str | None = None
    contact_sheet: str | None = None
    cover_sheet: str | None = None
    overview_sheet: str | None = None
    section_labels: dict[str, str] = Field(default_factory=dict)
    # Cover-page cells: value cells to blank (coordinate -> flag label) and
    # label cells to (re)write (coordinate -> label text).
    cover_value_cells: dict[str, str] = Field(default_factory=dict)
    cover_label_cells: dict[str, str] = Field(default_factory=dict)
    # main_single
    sheet: str = "Main"
    headers: list[str] = Field(default_factory=list)


class PlaybookConfig(BaseModel):
    model_config = _MODEL_CONFIG

    template: str = "sfmc_7sheet"
    templates: dict[str, PlaybookTemplateConfig] = Field(default_factory=dict)
    # conventions profile name -> task rows ("default" when a profile has none).
    tasks: dict[str, PlaybookTasksConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _template_exists(self) -> PlaybookConfig:
        if self.templates and self.template not in self.templates:
            raise ValueError(f"playbook.template {self.template!r} is not one of "
                             f"{sorted(self.templates)}")
        return self

    def resolve(self, name: str | None) -> tuple[str, PlaybookTemplateConfig]:
        key = name or self.template
        if key not in self.templates:
            raise ValueError(f"unknown playbook template {key!r}; expected one of "
                             f"{sorted(self.templates)}")
        return key, self.templates[key]

    def tasks_for(self, profile: str) -> PlaybookTasksConfig:
        return self.tasks.get(profile) or self.tasks.get("default") or PlaybookTasksConfig()


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
    # Optional, same posture: the Databricks volumes transport seam.
    databricks: DatabricksSettings = DatabricksSettings()
    # Optional (three-input model, added for the Raj feedback pass): both
    # sections default so an older config still loads unchanged.
    engineering_standards: EngineeringStandardsConfig = EngineeringStandardsConfig()
    load_pattern_faq: LoadPatternFaqConfig = LoadPatternFaqConfig()
    # Optional: Option B output knobs (see FrameworkConfig).
    framework: FrameworkConfig = FrameworkConfig()
    # Optional: layout recognition caches / provider posture (M2.5).
    layout: LayoutConfig = LayoutConfig()
    # Optional (M4): client conventions profiles + IIG template versions.
    conventions: ConventionsConfig = ConventionsConfig()
    metadata: MetadataConfig = MetadataConfig()
    # Optional (M5): the rfc output mode's package layout + playbook templates.
    rfc: RfcConfig = RfcConfig()
    playbook: PlaybookConfig = PlaybookConfig()


_TOP_LEVEL_KEYS = set(Config.model_fields)


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursive mapping merge: overlay mappings merge into base mappings,
    every other overlay value (lists included) replaces the base value."""
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path, overlays: list[str | Path] | None = None) -> Config:
    """Load the YAML config, failing loudly on unknown top-level sections.

    ``overlays`` (and the env ``CODEGEN_CONFIG_OVERLAYS``, ``;``/``,``
    separated paths, applied after them) are YAML mappings deep-merged onto
    the file before validation — the M5 home for client-shaped vocabulary
    (e.g. the pair-1 IIG template rows under fixtures/) so the shipped
    config carries none of it. Unknown sections are refused after the merge.

    ``CODEGEN_NOTIFICATION_EMAILS`` (comma/semicolon-separated) overrides
    ``job.notification_emails`` — env > YAML, like the SharePoint knobs. It
    exists so a CLIENT prod-support DL (a client value) can drive a local
    client-document run via the gitignored ``.env`` while the tracked YAML
    keeps its synthetic stand-in.
    """
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"config file {path} is not a YAML mapping")
    overlay_paths = [Path(p) for p in (overlays or [])]
    env_overlays = os.environ.get("CODEGEN_CONFIG_OVERLAYS", "").strip()
    if env_overlays:
        overlay_paths += [Path(p.strip()) for p in re.split(r"[;,]", env_overlays) if p.strip()]
    for overlay_path in overlay_paths:
        overlay = yaml.safe_load(overlay_path.read_text(encoding="utf-8"))
        if not isinstance(overlay, dict):
            raise ValueError(f"config overlay {overlay_path} is not a YAML mapping")
        raw = _deep_merge(raw, overlay)
    unknown = set(raw) - _TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(
            f"unknown top-level config section(s) {sorted(unknown)}; "
            f"expected only {sorted(_TOP_LEVEL_KEYS)}"
        )
    emails_env = os.environ.get("CODEGEN_NOTIFICATION_EMAILS", "").strip()
    if emails_env:
        emails = [e.strip() for e in re.split(r"[,;]", emails_env) if e.strip()]
        if emails:
            raw.setdefault("job", {})["notification_emails"] = emails
    return Config.model_validate(raw)
