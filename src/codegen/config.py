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


class FileDetailsAnnotationConfig(BaseModel):
    """M11: how a FILE_DETAILS row is recognised as an ANNOTATION (a legend,
    a note to the reader) rather than a file. Such a row — and a row with no
    file name — is skipped and logged, never a parse error (the v0.6.2 ACFC
    run died on a legend row). Empty defaults = nothing is recognised, i.e.
    exactly the pre-M11 behaviour."""

    model_config = _MODEL_CONFIG

    # A vendor cell whose text contains one of these (case-insensitive).
    phrases: list[str] = Field(default_factory=list)
    # A vendor cell whose FONT is italic (legends are set in italic). Only
    # consulted when the reader can see the cell's style.
    italic: bool = False


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
    # M9.0: placeholders a meta VALUE cell writes for "nothing stated yet"
    # ("TBD") — read as blank, so the fallback chain looks further.
    meta_blank_values: list[str] = Field(default_factory=list)
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
    # M9.3: an inline LAYER BLOCK inside a target cell — a heading line
    # "<layer marker> <heading word>:" ("Staging Layer:"; the markers are
    # target_schema_markers) followed by "Label: value" lines. Heading words
    # and the label spellings per slot (table / schema / catalog) are data.
    layer_block_heading_words: list[str] = Field(default_factory=list)
    layer_block_labels: dict[str, list[str]] = Field(default_factory=dict)
    # M9.1b: an Object Name cell that is a BLOCK (several lines, or a nested
    # label | value table) is read per line / row: a value under a
    # `feed_name` label names the feed, a value under a `file_name` label —
    # or any file-like value under another label (a line of business) — is a
    # file name pattern. Raw block text never lands in a scalar.
    object_name_labels: dict[str, list[str]] = Field(default_factory=dict)
    # M10.1: a PATH cell whose text starts with one of these label tokens,
    # optional spaces and ':' ("/Path : <storage>/<landing>/…" — the v0.6.0
    # ACFC FRD) has the label stripped and recorded in the field's evidence
    # (`stripped_label`); the remainder is the value and goes through the
    # existing path validation. A leading slash before the label is covered.
    # Case-insensitive. Applies to landing_location only.
    value_label_prefixes: list[str] = Field(default_factory=list)
    # M11 item 9: how an F3 document's tables are CLASSIFIED — by the
    # normalized text their first row-0 cell starts with. Anything that
    # matches none is "other". Structure only; no value is read from them.
    table_classes: dict[str, list[str]] = Field(default_factory=dict)


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
    # M9.2: target-column cell texts (normalized) by which an STTM says a
    # source field is NOT mapped ("Do Not Map"). Such a field is left out of
    # both layers and flagged field_unmapped:<field>, citing the cell. Empty =
    # no marker is recognised (the row then fails loudly for its missing type).
    unmapped_markers: list[str] = Field(default_factory=list)
    file_details_headers: ExtractorFileDetailsHeaders
    file_details_annotation: FileDetailsAnnotationConfig = FileDetailsAnnotationConfig()
    # M11: format words / extensions that mean the source files are
    # SPREADSHEETS (.xlsx / .xls): no delimiter, no byte positions, a sheet.
    # Empty = nothing is a spreadsheet, i.e. the pre-M11 behaviour.
    spreadsheet_tokens: list[str] = Field(default_factory=list)
    # M11 item 11: a document worksheet is read up to its USED range — the
    # last row with a value before this many consecutive empty rows. A sheet
    # formatted a million rows down (SHAPES_ROUND2 §3) otherwise makes every
    # scan create a cell per row. 0 = trust max_row (the pre-M11 behaviour).
    used_range_empty_rows: int = Field(default=500, ge=0)
    # M11 item 13: a column whose values are these says which rows are in
    # scope; out-of-scope rows are skipped with one grouped flag. Found by
    # VALUE (the real header embeds a vendor name). Empty = no filtering.
    scope_in_values: list[str] = Field(default_factory=list)
    scope_out_values: list[str] = Field(default_factory=list)
    # M11 item 13: a Load Rules cell starting with one of these marks an
    # AUDIT row (even when it names a column in one layer only).
    audit_load_rule_markers: list[str] = Field(default_factory=list)
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


class DerivationsConfig(BaseModel):
    """M7 derivation gate knobs (codegen.gate.derivations). The framework's
    own length limits are not documented: the defaults are CONSERVATIVE and
    say so; replace them with the framework team's figures when known."""

    model_config = _MODEL_CONFIG

    name_pattern: str = r"^[A-Za-z0-9_]+$"
    # IIG columns that must be identifiers (charset + cap).
    name_columns: list[str] = Field(default_factory=lambda: [
        "PIPELINE_NAME", "DATABRICKS_NOTEBOOK_NAME", "TGT_TABLE_NAME", "SRC_TABLE_NAME",
        "TGT_DATABASE_NAME", "TGT_SCHEMA_NAME", "SRC_SCHEMA_NAME", "TGT_CATALOG_NAME",
        "SRC_CATALOG_NAME", "TGT_RJT_TABLE_NAME", "RECYCL_TBL_NM"])
    # "default" + per-column caps (conservative; framework limits unknown).
    name_max_length: dict[str, int] = Field(default_factory=lambda: {"default": 128})
    path_column_suffixes: list[str] = Field(default_factory=lambda: ["_PATH", "_DIR", "_ROOT_DIR"])
    path_max_length: int = Field(default=1024, gt=0)
    # A WF_/NB_ name component longer than this after sanitizing is prose,
    # not a token: the component stays blank (and the name is flagged blank).
    max_name_token_length: int = Field(default=32, gt=0)
    sibling_suffixes: list[str] = Field(default_factory=lambda: [
        "_pct", "_pop", "_amt", "_dt", "_cd", "_id", "_nm", "_flg", "_cnt", "_ind", "_qty"])
    sibling_min_group: int = Field(default=3, ge=2)


class GateConfig(BaseModel):
    model_config = _MODEL_CONFIG

    run_generated_tests: bool
    ruff: bool
    structural_checks: bool
    debug_patterns: list[str]
    pytest_tail_lines: int = Field(gt=0)
    # M7: derived names / paths / SQL literals + sibling types (defaults so an
    # older config still loads).
    derivations: DerivationsConfig = DerivationsConfig()


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
    # auto (live when Layer 2 is live) | mock (never call a model) | live (the
    # recognizer calls the Foundation Model endpoint below on its own — also
    # when Layer 2 is mock-locked; dry-run and CODEGEN_FORCE_MOCK_LAYOUT still
    # force the mock). Env CODEGEN_LAYOUT_PROVIDER / CODEGEN_LAYOUT_ENDPOINT win.
    provider: Literal["auto", "mock", "live"] = "auto"
    # The serving endpoint `live` queries; None = databricks.serving_endpoint.
    endpoint: str | None = None
    max_tokens: int = Field(default=8192, gt=0)
    max_attempts: int = Field(default=2, gt=0)
    # Confidence a model-placed role starts with (validated, not trusted).
    model_confidence: float = Field(default=0.8, ge=0, le=1)
    # Confidence bump a cross-document agreement adds (capped at 1.0).
    crosscheck_bonus: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def _cache_paths_are_local(self) -> LayoutConfig:
        """The caches are LOCAL directories. A /Volumes or /Workspace path here
        is the serverless PermissionError (docs/acfc/RETROFIT_LOG.md §8): the
        durable runtime cache is ``storage.state`` (<state>/layout_profiles)."""
        runtime = self.runtime_cache_dir.replace("\\", "/").strip("./")
        if runtime.split("/")[0] == "fixtures" or runtime in {
                d.replace("\\", "/").strip("./") for d in self.cache_dirs}:
            raise ValueError(
                f"layout.runtime_cache_dir {self.runtime_cache_dir!r} is a tracked fixture "
                "directory — runtime profiles carry real sheet names and never land there")
        for value in (self.runtime_cache_dir, self.mock_dir, *self.cache_dirs):
            normalized = value.replace("\\", "/")
            if normalized.startswith(("/Volumes", "/Workspace")):
                raise ValueError(
                    f"layout cache path {value!r} addresses a Databricks mount — set "
                    "storage.state to a volume: / workspace: URI instead; the runtime "
                    "profile cache then lives at <state>/layout_profiles")
        return self


class StorageConfig(BaseModel):
    """Where inputs, state and outputs live (M8.1): one storage URI per role —
    ``local:<dir>`` (relative = inside the checkout), ``workspace:/Workspace/
    Users/<user>/…`` (Workspace API) or ``volume:/Volumes/<catalog>/<schema>/
    <volume>/…`` (Files API; never the /Volumes mount). Env
    ``CODEGEN_STORAGE_INPUTS`` / ``_STATE`` / ``_OUTPUTS`` win. A config
    without the section keeps the pre-M8 local directories."""

    model_config = _MODEL_CONFIG

    inputs: str = "local:./inputs"
    state: str = "local:./ui/backend/state"
    # None = the generator's own output.dir (local), as before M8.
    outputs: str | None = None
    # Local scratch for the working copies of a remote role (None = the
    # system temp dir). Never the record: recreated freely.
    scratch_dir: str | None = None

    @model_validator(mode="after")
    def _uris_parse(self) -> StorageConfig:
        from codegen.storage import parse_uri

        for uri in (self.inputs, self.state, self.outputs):
            if uri is not None:
                parse_uri(uri)
        return self


def _default_pair_weights() -> dict[str, float]:
    return {"feed_name": 2.0, "tables": 3.0, "schema": 1.0, "file_patterns": 3.0,
            "meta": 1.0, "ticket": 1.0, "name_stem": 1.0}


class PairingConfig(BaseModel):
    """Auto-pairing by content (M8.2, ``codegen.pairing``): signal weights —
    content signals outweigh the two name signals (ticket, name_stem) — and
    the decision rule: pair only when the best candidate reaches
    ``min_score`` AND leads the next by ``margin``; otherwise the top
    ``top_candidates`` become a question."""

    model_config = _MODEL_CONFIG

    weights: dict[str, float] = Field(default_factory=_default_pair_weights)
    min_score: float = Field(default=3.0, gt=0)
    margin: float = Field(default=2.0, gt=0)
    top_candidates: int = Field(default=4, gt=0)

    @model_validator(mode="after")
    def _weights_complete(self) -> PairingConfig:
        missing = sorted(set(_default_pair_weights()) - set(self.weights))
        if missing:
            raise ValueError(f"inputs.pairing.weights is missing {missing}")
        return self


class UpstreamConfig(BaseModel):
    """The upstream FRD→STTM agent's contract table (a SQL Warehouse read).
    OFF by default — the standalone doctrine: the agent runs from the documents
    themselves. Inside ACFC the App's service principal has no warehouse
    permission, and a lookup on a request path is a way to hang the App
    (docs/acfc/APP_CHOOSER_BUG.md). When ``enabled`` the listing runs in a
    background task with a hard timeout and is never awaited by a request."""

    model_config = _MODEL_CONFIG

    enabled: bool = False
    timeout_seconds: float = Field(default=20.0, gt=0)
    # A listing (or its failure) is reused this long before the next refresh.
    refresh_seconds: float = Field(default=300.0, ge=0)


class InputsConfig(BaseModel):
    """Input discovery (M8.2): extra read-only roots scanned for documents
    (the root and its immediate subfolders — depth 1) next to the inboxes
    under ``storage.inputs``. Storage URIs; env ``CODEGEN_EXTRA_INPUT_DIRS``
    (';'-separated) is appended. Real folder names belong in an overlay."""

    model_config = _MODEL_CONFIG

    extra_dirs: list[str] = Field(default_factory=list)
    scan_depth: int = Field(default=1, ge=0, le=1)
    # A remote root's listing is an API call and the chooser polls: reuse a
    # listing this long (an upload / fetch drops it at once).
    listing_ttl_seconds: float = Field(default=30.0, ge=0)
    # M9.3: the chooser's list endpoints return listing metadata only; each
    # document is downloaded, classified (sttm | vdd | unclassified) and its
    # pairing facts read ONCE, in a background task, within this many seconds
    # per file — a file that exceeds it (or fails to open) is listed as
    # "unreadable" with the reason, never omitted and never retried in a loop.
    # A remote folder listing is waited for this long at most (M9.3 addendum): a
    # root that does not answer is reported and its last known listing served.
    listing_timeout_seconds: float = Field(default=30.0, gt=0)
    # The document parser is a child process (codegen.layout.docworker); its
    # START (interpreter + imports) has its own budget, apart from a file's.
    parser_start_timeout_seconds: float = Field(default=60.0, gt=0)
    # M12: whether that child CAN start is asked ONCE per process, within this
    # short budget. When it cannot (serverless compute; an App runtime that
    # never answers "ready"), documents are parsed in-process in a worker
    # thread under the same per-file timeout and the used-range loader, and
    # the status says so (parser_mode=inprocess) — a selection never waits on
    # a parser that did not start.
    parser_probe_seconds: float = Field(default=10.0, gt=0)
    classify_timeout_seconds: float = Field(default=60.0, gt=0)
    # M11: a workbook declaring more cells than this is `unreadable` with the
    # count and the cap, decided read-only BEFORE any scan — a 140k-cell STTM
    # used to run the parser past its budget and be killed. 0 = no cap.
    max_workbook_cells: int = Field(default=250_000, ge=0)
    # … and a selection's own downloads (the STTM, its pair) are bounded too.
    select_timeout_seconds: float = Field(default=120.0, gt=0)
    pairing: PairingConfig = PairingConfig()

    @model_validator(mode="after")
    def _uris_parse(self) -> InputsConfig:
        from codegen.storage import parse_uri

        for uri in self.extra_dirs:
            parse_uri(uri)
        return self


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
    # M7: every CREATE must name catalog.schema.table. The catalog resolves
    # FRD label -> STTM band -> default_catalog[layer] (each with provenance);
    # none -> that layer's DDL is NOT written and the gate FAILs
    # catalog_unstated:<layer>. False keeps the reference two-file output,
    # whose goldens carry no catalog (a two-part name there is today's
    # behaviour, unchanged).
    require_qualified_names: bool = False
    default_catalog: dict[str, str] = Field(default_factory=dict)
    # M7 §3: write the SQL Server DML deliverable (config_inserts_<env>.sql +
    # the runner notebook) next to the IIG. Off for the reference profile so
    # its byte-compared reports keep today's file list.
    emit_dml: bool = False
    # M7 §4: prefix every deployment DDL file with the target-system header
    # line. Off in both shipped profiles: the pair-1 combined DDL and the
    # SFMC two-file DDL are compared byte for byte with client goldens; the
    # target system is labelled in ADDITION.md / MANIFEST.md instead.
    target_system_header: bool = False
    # M11: audit columns may only be String / Timestamp under this profile
    # (the reference layout's own rule). A declared type outside those is
    # then the gate check `audit_types` = FAIL naming the column; with the
    # knob off the type is emitted as the STTM declares it, flagged
    # audit_type_nonstandard. True keeps the pre-M11 restriction.
    audit_types_restricted: bool = True
    # M10: when the environment probe found a table, adjust its DDL to what
    # exists (identical -> a comment, no CREATE; different -> ALTER TABLE ADD
    # COLUMNS + a REVIEW block; never DROP, never CREATE OR REPLACE over an
    # existing table). False = "unchanged behaviour": the profile's CREATE
    # statement regardless — the reference profile's default, so its golden
    # stays byte-identical even with the probe on. The probe's findings are
    # flagged and reported either way. With the probe disabled, or when every
    # table is absent / unreadable, this knob changes nothing.
    reconcile_ddl: bool = False


class ConventionsConfig(BaseModel):
    model_config = _MODEL_CONFIG

    profile: str = "edo_sfmc"
    profiles: dict[str, ConventionsProfileConfig] = Field(
        default_factory=lambda: {"edo_sfmc": ConventionsProfileConfig()})
    # M7.1: the LAST fallback of the catalog chain for every profile (a
    # profile's own default_catalog wins): pairs whose FRD / STTM state no
    # catalog resolve to it with provenance `config_default`. Empty = none.
    default_catalog: dict[str, str] = Field(default_factory=dict)
    # M9.2: the LAST link of the SCHEMA chain (layer -> schema): STTM target
    # band -> FRD 'Target Catalog and Schema' -> here, each with provenance;
    # none of the three = the extractor's hard stop. Empty = none.
    default_schema: dict[str, str] = Field(default_factory=dict)

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
    # M7 §5: CLAIM_TYPE_ID default for the ADLS→Delta rows ("null only or
    # even NA", METADATA_DB_SEMANTICS §7). None = blank (the goldens'
    # value); "NA" writes the constant with this citation.
    claim_type_id_default: str | None = None
    # M7.1: the iig_v1 synthetic TGT_ADLS_PATH's domain / subdomain segments
    # go through the same slug the WF_/NB_ names use (emit.context
    # _sanitize_name_part: upper-case, runs of non-alphanumerics -> '_'), so
    # the path passes the global path gate (no whitespace in a segment).
    synthetic_path_slug: bool = True

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


class DmlVariableConfig(BaseModel):
    """One variable of the DML variables block (METADATA_DB_SEMANTICS §1–§5):
    who assigns it, the uniqueness rule, its T-SQL type and the FAQ
    companion that may supply the value."""

    model_config = _MODEL_CONFIG

    assigned_by: str
    rule: str
    sql_type: str = "INT"
    faq_field: str | None = None


class DmlConnectionTableConfig(BaseModel):
    """The file connection table AS SPOKEN in the walkthrough (§3) — not
    printed in the session, so flagged dml_unconfirmed until confirmed."""

    model_config = _MODEL_CONFIG

    name: str = "FILE_CONNECTION_DETAILS"
    id_column: str = "CONNECTION_ID"
    description_column: str = "CONNECTION_DESCRIPTION"
    host_column: str = "HOST_NAME"
    root_column: str = "ROOT_PATH"
    source_type_column: str = "SOURCE_TYPE"


class DmlConfig(BaseModel):
    """M7 §3: the SQL Server metadata-DB DML deliverable (emit/dml.py)."""

    model_config = _MODEL_CONFIG

    enabled: bool = True
    environments: list[str] = Field(default_factory=lambda: ["q1", "a2", "prod"])
    file_name_pattern: str = "config_inserts_{env}.sql"
    notebook_file_name_pattern: str = "Insert_scripts_config_table_{env}.py"
    schema: str = "dbo"
    # §1: rows the framework picks are ACTIVE_FLAG = 'S'.
    active_flag: str = "S"
    # §7: "populated with null only or even NA".
    claim_type_id_default: str | None = None
    # §9 dependency order (tables absent from the IIG payload are skipped).
    table_order: list[str] = Field(default_factory=lambda: [
        "DATA_FACTORY_PIPELINE_SCHEDULE", "FILE_ADLS_INGESTION_DETAILS",
        "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET",
        "ADLS_FIXED_WIDTH_HANDLER", "DATA_QUALITY_RULES", "DATABRICKS_NOTEBOOK_DETAILS",
        "EMAIL_TEMPLATE_CONFIG", "ALL_FILES_STATIC_INFORMATION"])
    # Tables the walkthrough described (§2, §5, §7); the rest are marked.
    described_tables: list[str] = Field(default_factory=lambda: [
        "DATA_FACTORY_PIPELINE_SCHEDULE", "FILE_ADLS_INGESTION_DETAILS",
        "ADLS_DELTA_INGESTION_DETAILS"])
    connection_table: DmlConnectionTableConfig = DmlConnectionTableConfig()
    connection_roles: list[str] = Field(default_factory=lambda: [
        "SRC_CONNECTION_ID", "SRC_ADLS_CONNECTION_ID", "METADATA_CONNECTION_ID",
        "TGT_CONNECTION_ID"])
    variables: dict[str, DmlVariableConfig] = Field(default_factory=lambda: {
        "RFC_NUMBER": DmlVariableConfig(
            assigned_by="engineer (the RFC / ATMT ticket)", sql_type="NVARCHAR(50)",
            rule="CREATED_BY and UPDATED_BY on every row (§1)", faq_field="rfc_number"),
        "PIPELINE_ID": DmlVariableConfig(
            assigned_by="engineer", rule="unique across DATA_FACTORY_PIPELINE_SCHEDULE, one per "
            "process (§2)", faq_field="pipeline_id"),
        "PARENT_PIPELINE_ID": DmlVariableConfig(
            assigned_by="engineer", rule="0 for a master pipeline, else the master's "
            "PIPELINE_ID (§2)", faq_field="parent_pipeline_id"),
        "GROUP_ID": DmlVariableConfig(
            assigned_by="engineer", rule="unique across the ingestion tables and never reused "
            "by another process (§5)", faq_field="group_id"),
        "OBJECT_ID": DmlVariableConfig(
            assigned_by="engineer", rule="1..n within the group, one per input file (§5)",
            faq_field="object_id"),
    })
    # Per-environment path prefix ('' = none); the body stays identical.
    env_path_prefix: dict[str, str] = Field(default_factory=dict)
    # M10: how the environment probe finds "the same row" in the metadata DB.
    # Keys as spoken in the walkthrough (METADATA_DB_SEMANTICS §2, §5, §7) for
    # the described tables; by analogy — UNCONFIRMED, flagged — for the rest
    # (§8, §11). A table with no entry is never probed (rows read unreadable).
    natural_keys: dict[str, list[str]] = Field(default_factory=lambda: {
        "DATA_FACTORY_PIPELINE_SCHEDULE": ["PIPELINE_NAME"],
        "FILE_ADLS_INGESTION_DETAILS": ["GROUP_ID", "OBJECT_ID"],
        "ADLS_DELTA_INGESTION_DETAILS": ["GROUP_ID", "OBJECT_ID", "OBJECT_NAME"],
        "STGDELTA_STDDELTA_INGESTION_DET": ["GROUP_ID", "OBJECT_ID", "OBJECT_NAME"],
        "ADLS_FIXED_WIDTH_HANDLER": ["PROCESS_NAME", "VERSION", "SEGMENT", "COL"],
        "DATA_QUALITY_RULES": ["GROUP_ID", "OBJECT_ID", "SEQUENCE_NO"],
        "DATABRICKS_NOTEBOOK_DETAILS": ["PIPELINE_NAME", "SEQ_NM"],
        "EMAIL_TEMPLATE_CONFIG": ["TEMPLATE_NAME", "PROCESS_NAME", "STATUS"],
    })
    # Row "status" columns: shown in the Environment report when they differ,
    # NEVER changed by the agent (no REVIEW diff, no UPDATE candidate, no
    # assertion) unless the load-pattern FAQ answers `manage_row_status: yes`.
    status_columns: list[str] = Field(
        default_factory=lambda: ["ACTIVE_FLAG", "ACTIVE_RULE_FLG",
                                 "ACTIVE_START_DATE", "ACTIVE_END_DATE"])
    # M11 item 13: the IIG tabs that describe a FILE source. For a feed whose
    # source is an RDBMS (source_kind=rdbms) their rows become a REVIEW block:
    # the RDBMS connection / ingestion tables are not described (§4, §6).
    file_source_tables: list[str] = Field(
        default_factory=lambda: ["FILE_ADLS_INGESTION_DETAILS"])
    # A row that exists and differs gets a REVIEW block with a COMMENTED-OUT
    # UPDATE candidate: the walkthrough describes no update path for config
    # rows (METADATA_DB_SEMANTICS §11 q19). True turns the candidate live —
    # only once the framework team confirms such a path exists.
    emit_updates: bool = False
    # NAMES of the Databricks secret scope and its keys — never values.
    secret_scope: str = "metadata-db"
    jdbc_url_secret: str = "jdbc-url"
    user_secret: str = "jdbc-user"
    password_secret: str = "jdbc-password"


class EnvProbeMetadataDbConfig(BaseModel):
    """NAMES of the secret scope / keys the read-only metadata-DB probe
    resolves inside the workspace — never values. Blank = that half of the
    probe is not configured (its rows read ``unreadable``). Deliberately NOT
    defaulted from ``dml.*_secret``: a read-only credential is the operator's
    explicit choice, not something the agent assumes."""

    model_config = _MODEL_CONFIG

    secret_scope: str = ""
    jdbc_url_secret: str = ""
    user_secret: str = ""
    password_secret: str = ""


class EnvProbeConfig(BaseModel):
    """M10 environment reconciliation — READ-ONLY, OFF by default.

    Both targets (Unity Catalog through a SQL warehouse, the SQL Server
    metadata DB through JDBC) exist only inside the operator's workspace. No
    workspace value lives in the tracked config: the warehouse id and the
    secret names come from an overlay or the App's env
    (CODEGEN_ENV_PROBE=1, CODEGEN_ENV_PROBE_WAREHOUSE_ID,
    CODEGEN_ENV_PROBE_ENVIRONMENT, CODEGEN_ENV_PROBE_SECRET_SCOPE — read at
    the point of use by codegen.env.probe). ``databricks.warehouse_id`` is
    NEVER a fallback. Outside a Databricks runtime nothing is resolved at all.
    """

    model_config = _MODEL_CONFIG

    enabled: bool = False
    # Which of dml.environments the probed workspace / metadata DB IS. The
    # probe sees ONE environment; only that environment's DML script is
    # adjusted. Blank = unstated: config rows are not probed.
    environment: str = ""
    uc_warehouse_id: str = ""
    # Per-query budget; a query that does not answer is `unreadable`.
    timeout_seconds: float = Field(default=20.0, gt=0)
    metadata_db: EnvProbeMetadataDbConfig = EnvProbeMetadataDbConfig()
    # M13: probe SNAPSHOTS (`codegen probe`, run as the user). `snapshots`
    # makes generation read the latest one per feed from
    # <state>/probes/<feed_slug>.json (App env CODEGEN_ENV_PROBE_SNAPSHOTS=1);
    # one older than max_age_hours is still used, flagged env_snapshot_stale.
    snapshots: bool = False
    max_age_hours: float = Field(default=24.0, gt=0)


class EnvConfig(BaseModel):
    model_config = _MODEL_CONFIG

    probe: EnvProbeConfig = EnvProbeConfig()


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


class FormatVocabularyConfig(BaseModel):
    """M14: what a file-format cell MEANS. ``canonical`` maps a kind to its
    spellings (matched as whole phrases in the normalized text, longest
    first); ``refines`` says a kind is a specific case of another (csv of
    delimited) — the two never conflict, the specific one wins; ``extensions``
    maps an extension-only cell to a kind or to ``any`` (compatible with every
    kind — it names the file, not its layout); ``not_formats`` are transport /
    scope phrases ("File Data Ingestion"): dropped as candidates, flagged."""

    model_config = _MODEL_CONFIG

    canonical: dict[str, list[str]] = Field(default_factory=dict)
    refines: dict[str, str] = Field(default_factory=dict)
    extensions: dict[str, str] = Field(default_factory=dict)
    not_formats: list[str] = Field(default_factory=list)


class DelimiterVocabularyConfig(BaseModel):
    model_config = _MODEL_CONFIG

    canonical: dict[str, list[str]] = Field(default_factory=dict)


class FrequencyVocabularyConfig(BaseModel):
    """``vague`` terms (Periodic, TBD, As needed) yield to any specific
    cadence; a cell holding ``schedule_min_dates`` or more dates is a
    SCHEDULE, not a frequency — dropped as a candidate, flagged."""

    model_config = _MODEL_CONFIG

    canonical: dict[str, list[str]] = Field(default_factory=dict)
    vague: list[str] = Field(default_factory=list)
    schedule_min_dates: int = Field(default=2, ge=2)


class ValueVocabularyConfig(BaseModel):
    """M14: candidate texts are normalized to canonical values BEFORE the gap
    chain looks for a disagreement — only canonical values that genuinely
    differ produce a question (resolve/gapfill.py::reconcile). Top-level on
    purpose: the layout cache's vocabulary hash covers ``extractor:`` and
    this is not layout vocabulary."""

    model_config = _MODEL_CONFIG

    file_format: FormatVocabularyConfig = FormatVocabularyConfig()
    delimiter: DelimiterVocabularyConfig = DelimiterVocabularyConfig()
    frequency: FrequencyVocabularyConfig = FrequencyVocabularyConfig()
    # M14 item 2: an F2 / F3 FRD states its content fields in requirement
    # prose. The question is TEXT, shown with the document's own sentences
    # that mention the concept — field leaf name -> terms (whole phrases,
    # case-insensitive); at most ``max_evidence`` snippets of
    # ``evidence_chars`` characters each.
    evidence_terms: dict[str, list[str]] = Field(default_factory=dict)
    max_evidence: int = Field(default=6, ge=1)
    evidence_chars: int = Field(default=240, ge=40)


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
    value_vocabulary: ValueVocabularyConfig = ValueVocabularyConfig()
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
    # Optional (M7): the SQL Server metadata-DB DML deliverable.
    dml: DmlConfig = DmlConfig()
    # Optional (M8): storage backends per role + extra input roots.
    storage: StorageConfig = StorageConfig()
    inputs: InputsConfig = InputsConfig()
    upstream: UpstreamConfig = UpstreamConfig()
    # Optional (M10): read-only environment reconciliation, off by default.
    env: EnvConfig = EnvConfig()


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
