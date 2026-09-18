"""Plain-language help for layout questions (the `needs_layout` dialog).

A question names a role or an FRD field the recognizer could not place. On
its own that is impenetrable ("feeds[0].frequency — no label maps to this
field"). Every question therefore carries a **title**, a **hint** (what
the field means and where it usually sits in the document) and, when one
of the candidate rows / columns matches the field's usual labels, a
**suggested** candidate the dialog pre-selects. The suggestion is only a
pre-selection: the merge step re-validates whatever the person confirms,
and nothing here ever writes a value.
"""

from __future__ import annotations

import re

from codegen.config import Config

# contract path (without the feeds[i]. prefix) -> (title, hint, label keys)
# The label keys index config extractor.frd.labels / fixed_rows.
FRD_FIELD_HELP: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "feed_name": (
        "Feed (object) name",
        "The name of the feed being ingested. In an F1 FRD it is the 'Object Name' row of "
        "the Descriptive Metadata table, or that section's 'Name' row.",
        ("object_name", "name")),
    "source_system": (
        "Source system / vendor",
        "The system or vendor the file comes from. Usually 'Data Source' in Descriptive "
        "Metadata, otherwise 'Vendor Name' in Vendor Metadata.",
        ("data_source", "vendor_name")),
    "file_format": (
        "File format",
        "How the file is laid out — csv, pipe-delimited, fixed width, JSON. Usually the "
        "'Object/data Format' row of Structural Metadata.",
        ("object_format",)),
    "frequency": (
        "Load frequency",
        "How often the file arrives (daily, weekly, monthly, ad hoc). Usually the 'Frequency' "
        "row of Descriptive Metadata.",
        ("frequency",)),
    "lobs": (
        "Lines of business",
        "Which lines of business the feed covers (or ALL). Usually the 'LOBs' row of "
        "Descriptive Metadata.",
        ("lobs",)),
    "domain": (
        "Domain and subdomain",
        "The data domain and subdomain the feed lands in, e.g. Pharmacy / Accumulators. "
        "Usually 'Domain and Subdomain' in Structural Metadata.",
        ("domain_subdomain",)),
    "sub_domain": (
        "Subdomain",
        "The subdomain half of 'Domain and Subdomain' in Structural Metadata.",
        ("domain_subdomain",)),
    "stage_target.schema": (
        "Stage catalog and schema",
        "Where the stage table is created. Usually 'Target Catalog and Schema' (or 'Target "
        "Schema') in Structural Metadata; the stage entry is the one marked STG.",
        ("target_schema",)),
    "stage_target.tables": (
        "Target table name(s)",
        "The table(s) the feed loads. Usually the 'Target Table Name' row of Structural "
        "Metadata.",
        ("target_table_name",)),
    "stage_target.load_strategy": (
        "Stage load strategy",
        "How the stage layer is loaded — Append, Truncate and Load, Upsert. Usually the "
        "'Load Strategy STG' row of Structural Metadata.",
        ("load_strategy_stg",)),
    "standard_target.load_strategy": (
        "Standard load strategy",
        "How the standard layer is loaded. Usually 'Load Strategy STD' (some FRDs write "
        "'Load Strategy STD (View)').",
        ("load_strategy_std",)),
    "landing_location": (
        "ADLS landing location",
        "The lake path the files land in. Usually 'ADLS Location' in Structural Metadata; "
        "'Inbound File Folder Path' confirms it.",
        ("adls_location", "inbound_folder")),
    "archive_retention": (
        "Archive schedule",
        "How long files are kept / when they are archived. Usually 'Archive Schedule'.",
        ("archive_schedule",)),
    "sttm_reference": (
        "Source data dictionary reference",
        "Which STTM / data dictionary the FRD points at. Usually 'Source Data Dictionary'.",
        ("source_data_dictionary",)),
    "phi_pii_notes": (
        "PII / PHI fields",
        "Which fields carry PII or PHI. Usually the 'PII Fields' row of Data Quality.",
        ("pii_fields",)),
    "recycle_rule": (
        "Record recycle process",
        "Whether rejected records are recycled and how. Usually 'Record Recycle Process "
        "(HARD - In pipeline)' in the Reject / Recycle Process section.",
        ("recycle_process",)),
    "requirement_ids": (
        "Traced requirements",
        "Requirement IDs this feed traces to. Usually 'Traced/Related Requirements'.",
        ("traced_requirements",)),
}

# STTM / VDD role -> (title, hint). Roles not listed get a generic sentence.
ROLE_HELP: dict[str, tuple[str, str]] = {
    "field_name": ("Field name", "The column naming each source field — headers like 'Field "
                                 "Name', 'Column Name', 'Attribute', 'Element'."),
    "column": ("Column name", "The column that names the target column."),
    "datatype": ("Data type", "The column giving each field's data type (String, Decimal(17,2), "
                              "Date…)."),
    "type": ("Data type", "The column giving each field's data type."),
    "source_type": ("Source data type", "The data type as the source system declares it."),
    "length": ("Field length", "The width of the field (fixed-width files) or the max length."),
    "field_length": ("Field length", "The width of the field in a fixed-width record."),
    "start": ("Start position", "The 1-based start position of the field in a fixed-width "
                                "record."),
    "end": ("End position", "The end position of the field in a fixed-width record."),
    "segment": ("Record segment", "Which record type a row belongs to — Header, Detail or "
                                  "Trailer (HDDR / DET / TRLR, H / D / T)."),
    "required": ("Required", "Whether the field is mandatory (Y/N, Required, Mandatory)."),
    "nullable": ("Nullable", "Whether the field may be empty (NULL / NOT NULL)."),
    "null_check": ("Null check", "Whether a null check applies to the field."),
    "mandatory": ("Mandatory", "Whether the field must be present."),
    "not_null": ("Not null", "Whether the field may not be null in the target."),
    "pii": ("PII / PHI flag", "Whether the field carries PII / PHI."),
    "key": ("Key", "Whether the field is (part of) the record key."),
    "primary_key": ("Primary key", "Whether the field is part of the primary key."),
    "description": ("Description", "The business description of the field."),
    "data_definition": ("Data definition", "The business definition of the field."),
    "comments": ("Comments", "Free-text comments / notes on the field."),
    "sample_value": ("Sample value", "An example value of the field."),
    "example_value": ("Example value", "An example value of the field."),
    "business_rule": ("Business rule", "The rule text applied to the field (transformations, "
                                       "validations)."),
    "load_rule": ("Load rule", "How the field is loaded (Load as is, Convert yyyyMMdd to "
                               "yyyy-MM-dd…)."),
    "dq_rules": ("DQ rules", "The data-quality rule(s) applied to the field."),
    "recycle_flag": ("Recycle flag", "Whether a failed record is recycled, with the validation "
                                     "text."),
    "source_database": ("Source database", "The source database of a table-sourced feed."),
    "source_schema": ("Source schema", "The source schema of a table-sourced feed."),
    "source_table": ("Source table", "The source table of a table-sourced feed."),
    "server": ("Server", "The source server / environment."),
    "inscope": ("In scope", "Whether the field is in scope for the load."),
    "lob": ("Line of business", "Which line of business the field / row applies to."),
    "critical": ("Critical", "Whether the field is critical (drives reject handling)."),
    "workspace": ("Workspace", "The Databricks workspace of the target layer."),
    "catalog": ("Catalog", "The Unity Catalog catalog of the target table."),
    "schema": ("Schema", "The schema (database) of the target table."),
    "table": ("Table", "The target table name."),
    "ordinal": ("Ordinal / sequence", "The field's position number in the record."),
    "target_type": ("Target data type", "The data type of the target column."),
    "mandatory_column": ("Mandatory column", "Whether the target column is mandatory."),
    "constraints": ("Constraints", "Constraints on the target column (keys, nulls, checks)."),
    "field_description": ("Field description", "The description of the target column."),
    "table_description": ("Table description", "The description of the target table."),
    "transformation": ("Transformation", "The transformation applied on the way to the target."),
    "dq_mandatory": ("DQ mandatory", "Whether the data-quality check on the field is mandatory."),
    "position": ("Position", "The field's position in the record (fixed-width layouts)."),
    "data_type": ("Data type", "The field's data type as the data dictionary states it."),
}

_LAYER_WORDS = {"source": "source", "rules": "data rules", "stage": "stage layer",
                "standard": "standard layer", "files": "FILES sheet", "fields": "field sheet"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> set[str]:
    return set(_norm(text).split())


def frd_field_help(path: str, candidates: list[dict], config: Config
                   ) -> tuple[str, str, int | None]:
    """(title, hint, index of the suggested candidate or None) for an FRD
    question. The suggestion is the candidate whose label equals — else
    contains — one of the field's usual label synonyms (config
    extractor.frd.labels / fixed_rows)."""
    field = re.sub(r"^feeds\[\d+\]\.", "", path).replace("#fallback", "")
    title, hint, keys = FRD_FIELD_HELP.get(field, (
        field.replace("_", " ").replace(".", " → ").capitalize(),
        "A required FRD field the recognizer could not place; pick the row that states it.",
        ()))
    frd = config.extractor.frd
    synonyms = [s for key in keys for s in (frd.labels.get(key, []) + frd.fixed_rows.get(key, []))]
    normalized = [_norm(s) for s in synonyms]
    labels = [_norm(c.get("label") or "") for c in candidates]
    for i, label in enumerate(labels):
        if label and label in normalized:
            return title, hint, i
    for i, label in enumerate(labels):
        if label and any(s and (s in label or label in s) for s in normalized):
            return title, hint, i
    return title, hint, None


def role_help(role: str, layer: str | None, candidates: list[dict]
              ) -> tuple[str, str, int | None]:
    """(title, hint, suggested candidate index) for an STTM / VDD question.
    Ambiguous roles come as 'a|b'. The suggestion is the candidate header
    whose words contain the role's words (e.g. role 'field_name' ↔ header
    'Source Field Name')."""
    parts = role.split("|")
    helps = [ROLE_HELP.get(p, (p.replace("_", " ").capitalize(),
                                f"The column carrying the {p.replace('_', ' ')}.")) for p in parts]
    title = " or ".join(h[0] for h in helps)
    hint = " ".join(h[1] for h in helps)
    if layer in _LAYER_WORDS:
        hint += f" This question is about the {_LAYER_WORDS[layer]} band of the sheet."
    role_tokens = {t for p in parts for t in _tokens(p)}
    for i, c in enumerate(candidates):
        header = c.get("header") or c.get("label") or ""
        if role_tokens and role_tokens <= _tokens(header):
            return title, hint, i
    return title, hint, None


__all__ = ["FRD_FIELD_HELP", "ROLE_HELP", "frd_field_help", "role_help"]
