"""Option B: DDL scripts + config rows + SQL inserts for the ACFC framework.

The deck's "CodeGen Agent Architecture" slide: the approved STTM becomes
deployable artefacts — Option A a PySpark notebook (fresh pipeline, ~10% of
runs), or Option B an *addition* to the existing ingestion framework (~90%):
DDL scripts as a reviewable workbook, config rows as the approval artefact,
and SQL insert statements loaded into the framework database only after a
person approves. This module renders Option B into
``out/<feed_slug>/framework/``.

Row building is NOT duplicated here: ``codegen.metadata_sheet`` (the layout
named by ``framework.metadata_layout``) is the single source of truth — the
same tabs, headers, provenance badges and coverage the preview panel shows
are what gets approved and inserted. Framework-assigned ID columns
(``always_blank``) render as ``framework.id_placeholder`` and are flagged,
never invented. DDL stays engineer-run: nothing here creates tables, and
the inserts are plain INSERTs — idempotency belongs to the framework's own
load path.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.faq import LoadPatternFaq, summarize
from codegen.gate.derivations import check_iig_derivations, check_sql_literals, join_path
from codegen.gate.preflight import GateCheck
from codegen.metadata_sheet import (
    BADGE_LABELS,
    DERIVED_BADGES,
    build_workbook,
    metadata_sheet_payload,
)

_ADDITION_TEMPLATE = """\
# Framework addition — {slug}

{banner}

Option B output: an **addition to the existing ingestion framework** (the
~90% case), not a standalone pipeline. The DDL scripts and the insert SQL
are **add-ons to ACFC's master notebook** — the notebook the client
already has and runs; the agent never generates or edits that notebook,
it only produces the add-ons.

| File | What it is |
| --- | --- |
{ddl_row}
{rows_row}
{inserts_row}
| `ADDITION.md` | This manifest. |

Columns awaiting framework-assigned IDs (rendered as `{id_placeholder}`,
never invented): {blank_columns}.
{segmented_block}{target_block}
Layout note: the tab names and column headers are the client IIG template
(anonymized reference — `fixtures/reference/SFMC_IIG.xlsx`).

On approval: the config rows land in the ingestion framework database, and
the DDL + insert SQL are added on to ACFC's master notebook with the
framework-assigned IDs. The agent never inserts unapproved rows.
"""


# M7 §4: artefacts labelled by the system they run against.
TARGET_DDL = "DDL — Databricks (Unity Catalog)"
TARGET_DML = "DML — SQL Server metadata DB (run from notebook)"
TARGET_REVIEW = "Review sheets"
TARGET_NOTES = "Notes"
DDL_TARGET_HEADER = "-- TARGET SYSTEM = Databricks (Unity Catalog) — run in SQL editor/notebook"


def artefact_group(name: str) -> str:
    if name.endswith("_table_creation.txt") or name.endswith("_DDL.txt"):
        return TARGET_DDL
    if name.startswith("config_inserts_") and name.endswith(".sql"):
        return TARGET_DML
    if name.startswith("Insert_scripts_config_table_") and name.endswith(".py"):
        return TARGET_DML
    if name.endswith(".xlsx"):
        return TARGET_REVIEW
    return TARGET_NOTES


def artefact_groups(files: list[Path]) -> dict[str, list[str]]:
    """target system -> file names, groups in a fixed order."""
    out: dict[str, list[str]] = {}
    for group in (TARGET_DDL, TARGET_DML, TARGET_REVIEW, TARGET_NOTES):
        names = [p.name for p in files if artefact_group(p.name) == group]
        if names:
            out[group] = names
    return out


@dataclass(frozen=True)
class FrameworkArtefacts:
    """What one feed's Option B emit produced (for reports and the UI)."""

    files: list[Path]
    row_counts: dict[str, int]
    coverage: dict[str, int]
    flagged_blank_columns: list[str] = field(default_factory=list)
    # Segmented-extraction surfacing (empty/None on flat feeds): the ASSUMED
    # discriminator line and the held-back workbook Standard layer.
    assumed_notes: list[str] = field(default_factory=list)
    held_back: list[str] = field(default_factory=list)
    # M4: gate flags this emit raised (blank-and-flag IIG columns, a DDL
    # file name derived from the slug) — joined to the verdict by the caller.
    flags: list[str] = field(default_factory=list)
    # M7: gate CHECKS this emit ran (derived names / paths, SQL literals,
    # three-part qualification) — a failed one FAILs the feed.
    checks: list[GateCheck] = field(default_factory=list)
    # M7: the framework payload (IIG rows) the DML emitter renders from.
    payload: dict | None = None
    # M7 §4: file names grouped by target system (artefact_groups).
    groups: dict[str, list[str]] = field(default_factory=dict)
    # M10: what the environment probe found (None = disabled) and whether the
    # profile lets the DDL be adjusted to it (conventions reconcile_ddl).
    env_result: object | None = None
    env_reconcile_ddl: bool = False
    dml_emitted: bool = False


def _sanitize_abbrev(slug: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", slug).strip("_").upper()


def _config_default_catalog(config: Config | None, profile, layer: str) -> str | None:
    """The catalog chain's last link: the profile's default_catalog, else the
    global conventions.default_catalog (M7.1)."""
    own = profile.default_catalog.get(layer)
    if own or config is None:
        return own
    return config.conventions.default_catalog.get(layer)


def _qualify(table, layer: str, profile, spec: ResolvedFeedSpec,
             flags: list[str], config: Config) -> str | None:
    """catalog.schema.table for a CREATE, or None when the profile requires
    three parts and no source states the catalog / schema. Chain: the
    resolved table's catalog (FRD label, else the STTM band — the resolver
    carries whichever stated one) -> profile / conventions default_catalog
    (provenance config_default); each fallback is a provenance flag;
    nothing is invented."""
    catalog, schema, name = table.catalog, table.schema_name, table.table
    default = _config_default_catalog(config, profile, layer)
    if not catalog and default:
        catalog = default
        flags.append(f"catalog_from_config:{layer} — {schema}.{name}: no FRD / STTM catalog; "
                     f"provenance config_default (conventions default_catalog[{layer}] = "
                     f"{catalog!r})")
    if profile.require_qualified_names and not (catalog and schema):
        missing = "catalog" if not catalog else "schema"
        flags.append(f"{missing}_unstated:{layer} — {schema or '?'}.{name}: sources checked: "
                     "FRD Target Catalog and Schema label, STTM target band catalog column, "
                     f"conventions profile default_catalog[{layer}] — none states one; the "
                     f"{layer} DDL is not written (a two-part name is never written)")
        return None
    return ".".join(p for p in (catalog, schema, name) if p)


def _combined_ddl_text(spec: ResolvedFeedSpec, profile, flags: list[str] | None = None,
                       config: Config | None = None) -> str | None:
    """The combined-layout deployment DDL (M4, ``acfc_prx``) — build + render."""
    stage, standard = _combined_tables(spec, profile, flags, config)
    return _render_combined(profile, stage, standard)


def _render_combined(profile, stage: dict | None, standard: dict | None) -> str | None:
    from codegen.emit.emitter import _environment

    if stage is None and standard is None:
        return None
    template = _environment().get_template("framework/combined_ddl.txt.j2")
    return template.render(ddl=profile, stage=stage, standard=standard)


def _combined_tables(spec: ResolvedFeedSpec, profile, flags: list[str] | None = None,
                     config: Config | None = None) -> tuple[dict | None, dict | None]:
    """The combined layout's (stage, standard) tables: stage columns
    as the STTM stage band types them (distinct across segments, STTM
    order), audit columns in the profile's casing, standard = the stage
    list when the profile says so. Whitespace comes from the profile.
    M7: every CREATE is three-part or omitted (``_qualify``); None when a
    layer does not qualify. ``env_block`` (M10) is None until the environment
    probe says the table exists."""
    flags = flags if flags is not None else []

    seen: set[str] = set()
    stage_columns: list[tuple[str, str]] = []
    standard_columns: list[tuple[str, str]] = []
    for segment in spec.segments:
        for f in segment.fields:
            if f.stage_column in seen:
                continue
            seen.add(f.stage_column)
            stage_columns.append((f.stage_column, f.stage_datatype if profile.typed_stage
                                  else "STRING"))
            if f.standard_column is not None:
                standard_columns.append((f.standard_column, f.standard_datatype or ""))
    audit = [(a.column, profile.audit_type_casing.get(a.datatype, a.datatype))
             for a in spec.audit_columns]
    stage_table = spec.detail_segment.stage_table
    stage_qualified = _qualify(stage_table, "stage", profile, spec, flags, config)
    stage = ({"qualified": stage_qualified, "columns": stage_columns + audit,
              "env_block": None} if stage_qualified else None)
    standard = None
    if spec.standard_table is not None:
        columns = stage_columns if profile.standard_from_stage else standard_columns
        standard_qualified = _qualify(spec.standard_table, "standard", profile, spec, flags,
                                      config)
        if standard_qualified:
            standard = {"qualified": standard_qualified, "columns": columns + audit,
                        "env_block": None}
    return stage, standard


def _provenance_banner_rows(spec: ResolvedFeedSpec, faq: LoadPatternFaq,
                            config: Config, faq_sha: str) -> list[tuple[str, str]]:
    """The provenance banner as key/value rows — same inputs the generated
    files' banners carry, plus the FAQ and standards (inputs of this mode)."""
    faq_summary = summarize(faq)
    return [
        ("FRD contract", f"{spec.frd_contract_name} sha256 {spec.frd_contract_sha256}"),
        ("STTM contract", f"{spec.sttm_contract_name} sha256 {spec.sttm_contract_sha256}"),
        ("Load-pattern FAQ", f"sha256 {faq_sha} — {faq_summary['answered']} answered, "
                             f"{faq_summary['unknown']} unknown"),
        ("Engineering standards", config.engineering_standards.status),
        ("Layout", "client IIG template (anonymized reference — "
                   "fixtures/reference/SFMC_IIG.xlsx); values carry over"),
    ]


def _faq_sha(spec: ResolvedFeedSpec, config: Config, base_dir: Path | None) -> str:
    faq_dir = Path(config.load_pattern_faq.per_feed_dir)
    if base_dir is not None and not faq_dir.is_absolute():
        faq_dir = base_dir / faq_dir
    path = faq_dir / f"{spec.feed_slug}.faq.yaml"
    if not path.is_file():
        return "defaults (no FAQ file)"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _filter_payload_for_feed(payload: dict, slug: str) -> dict:
    """This feed's rows only, coverage recomputed for the filtered set."""
    tabs = {}
    derived = synthetic = needs_template = total = 0
    for name, tab in payload["tabs"].items():
        rows = [r for r in tab["rows"] if r.get("feed_slug") == slug]
        tabs[name] = {**tab, "rows": rows}
        for row in rows:
            for entry in row["badges"].values():
                total += 1
                badge = entry["badge"]
                if badge in DERIVED_BADGES:
                    derived += 1
                elif badge == "synthetic":
                    synthetic += 1
                else:
                    needs_template += 1
    return {
        **payload,
        "tabs": tabs,
        "coverage": {"derived": derived, "synthetic": synthetic,
                     "needs_template": needs_template, "total": total},
    }


# -- <slug>_stage/standard_table_creation.txt ---------------------------------- #
# Deployment-team DDL as two plain .txt files (run in the data lake by the
# deployment team), conformant to the client's reference goldens
# (fixtures/reference/SFMC_*_table_creation.txt). The .sql sources under
# out/<slug>/ddl/ stay untouched — these files are re-styled from them.


def _classify_ddl(file_name: str) -> tuple[str, str, str, str]:
    """(layer, schema, table, purpose) from the emitted DDL file name."""
    stem = file_name.removesuffix(".sql")
    if stem.endswith(".standard"):
        schema, _, table = stem.removesuffix(".standard").partition(".")
        return "standard", schema, table, "standard target table"
    schema, _, table = stem.partition(".")
    if table.lower().endswith("_errors"):
        return "stage", schema, table, "errors side-table"
    if table.lower().endswith("_processed_files"):
        return "stage", schema, table, "processed-files ledger"
    if table.lower().endswith("_recycle"):
        return "stage", schema, table, "recycle store"
    return "stage", schema, table, "stage target table"


# Section order inside each .txt: main target table first, side-tables after.
_DDL_PURPOSE_ORDER = {
    "stage target table": 0,
    "errors side-table": 1,
    "processed-files ledger": 2,
    "recycle store": 3,
    "standard target table": 0,
}

_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\S+)\s*\(")
_COLUMN_RE = re.compile(r"^\s*`(?P<name>[^`]+)`\s+(?P<dtype>[^,]+(?:\([^)]*\))?),?\s*$")


def _parse_ddl_statement(statement: str) -> tuple[str, list[tuple[str, str]]]:
    """(qualified table name, [(column, dtype)]) from an emitted .sql source."""
    match = _CREATE_RE.search(statement)
    if match is None:
        raise ValueError("DDL source has no CREATE TABLE statement")
    columns: list[tuple[str, str]] = []
    for line in statement.splitlines():
        col = _COLUMN_RE.match(line)
        if col:
            columns.append((col.group("name"), col.group("dtype").rstrip().rstrip(",")))
    return match.group(1), columns


def _sql_comment(text: str) -> str:
    # Single-line comment literals (the reference goldens' style): collapse
    # any embedded newlines/whitespace runs, escape quotes.
    return re.sub(r"\s+", " ", text).strip().replace("'", "''")


def _description_map(spec: ResolvedFeedSpec) -> dict[str, str]:
    """column name -> STTM description, for the per-column COMMENT clauses."""
    descriptions: dict[str, str] = {}
    for segment in spec.segments:
        for f in segment.fields:
            if f.description:
                descriptions.setdefault(f.stage_column, f.description)
                if f.standard_column:
                    descriptions.setdefault(f.standard_column, f.description)
    return descriptions


def _synthetic_location(spec: ResolvedFeedSpec, config: Config, table: str) -> str:
    # M7: assembled from normalized segments (gate.derivations.join_path) —
    # never a raw string concatenation; a bad segment is the gate's to FAIL.
    return join_path(config.framework.synthetic_location_prefix,
                     spec.landing_location or spec.feed_slug, table)


def _source_fragment(spec: ResolvedFeedSpec) -> str:
    """" (source: <vendor>)" for the table COMMENT — the vendor / source-
    system value only (Data Source / Vendor Metadata labels); omitted when
    unstated, multi-line or a label-prefixed description (M7 §2 h)."""
    source = (spec.source_system or "").strip()
    if not source or source.lower() == "unstated" or "\n" in source or "=" in source:
        return ""
    return f" (source: {source})"


def _table_creation_text(layer: str, entries: list[tuple[str, str, str]],
                         spec: ResolvedFeedSpec, config: Config,
                         banner: list[tuple[str, str]],
                         extra_banner_lines: list[str] | None = None,
                         profile=None, flags: list[str] | None = None) -> str:
    """Render one deployment-team .txt file for a layer's DDL entries."""
    tables = _layer_tables(layer, entries, spec, config, profile, flags)
    return _render_table_creation(layer, tables, banner, extra_banner_lines)


def _layer_tables(layer: str, entries: list[tuple[str, str, str]],
                  spec: ResolvedFeedSpec, config: Config,
                  profile=None, flags: list[str] | None = None) -> list[dict]:
    """One layer's tables as the template renders them.
    M7: under a profile requiring qualified names, an entry whose CREATE is
    not three-part is left out (flagged catalog_unstated:<layer>).
    ``env_block`` (M10) is None until the environment probe says the table
    exists."""
    flags = flags if flags is not None else []
    descriptions = _description_map(spec)
    tables = []
    for _file_name, statement, purpose in sorted(
            entries, key=lambda e: (_DDL_PURPOSE_ORDER.get(e[2], 9), e[0])):
        qualified, columns = _parse_ddl_statement(statement)
        if profile is not None and len(qualified.split(".")) < 3:
            default = _config_default_catalog(config, profile, layer)
            if default:
                flags.append(f"catalog_from_config:{layer} — {qualified}: no FRD / STTM catalog; "
                             f"provenance config_default (conventions default_catalog[{layer}] "
                             f"= {default!r})")
                qualified = f"{default}.{qualified}"
            elif profile.require_qualified_names:
                flags.append(f"catalog_unstated:{layer} — {qualified}: sources checked: FRD "
                             "Target Catalog and Schema label, STTM target band catalog "
                             f"column, conventions profile default_catalog[{layer}] — none "
                             f"states one; the {layer} DDL is not written (a two-part name is "
                             "never written)")
                continue
        rendered_columns = [
            {
                "name": name,
                "dtype": dtype,
                "comment": _sql_comment(
                    descriptions.get(name, name.replace("_", " ").title())),
            }
            for name, dtype in columns
        ]
        tables.append({
            "qualified": qualified,
            "columns": rendered_columns,
            "table_comment": _sql_comment(
                f"{purpose.capitalize()} for feed {spec.feed_name}"
                f"{_source_fragment(spec)}"),
            "location": (_synthetic_location(spec, config, qualified.rsplit(".", 1)[-1])
                         if layer == "stage" else None),
            "tags": ((spec.domain, spec.sub_domain)
                     if spec.domain and spec.sub_domain else None),
            "env_block": None,
        })
    return tables


def _render_table_creation(layer: str, tables: list[dict], banner: list[tuple[str, str]],
                           extra_banner_lines: list[str] | None = None) -> str:
    from codegen.emit.emitter import _environment

    banner_lines = [f"{key}: {value}" for key, value in banner
                    if key != "Layout"]
    banner_lines.append("DDL is engineer-run; the agent never creates target "
                        "tables (create_tables: false).")
    banner_lines.extend(extra_banner_lines or [])
    template = _environment().get_template("framework/table_creation.txt.j2")
    return template.render(layer=layer, tables=tables, banner_lines=banner_lines)


# -- config_inserts.sql -------------------------------------------------------- #


def _sql_value(value, dialect: str) -> str:
    if isinstance(value, bool):
        return ("1" if value else "0") if dialect == "sqlserver" else str(value).upper()
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace("'", "''")
    return f"N'{escaped}'" if dialect == "sqlserver" else f"'{escaped}'"


def _sql_identifier(name: str, dialect: str) -> str:
    if dialect == "sqlserver":
        return f"[{name}]"
    return '"' + name.replace('"', '""') + '"'


def _sql_table(name: str, dialect: str) -> str:
    return ".".join(_sql_identifier(part, dialect) for part in name.split("."))


def _insert_statement(headers: list[str], row: dict, table: str, dialect: str,
                      placeholder: str, always_blank: set[str]) -> str:
    values = []
    for header in headers:
        if header in always_blank:
            values.append(placeholder)
            continue
        value = row["values"][header]
        if value == "" or value is None:
            values.append("NULL")
        else:
            values.append(_sql_value(value, dialect))
    columns = ", ".join(_sql_identifier(h, dialect) for h in headers)
    return (f"INSERT INTO {_sql_table(table, dialect)} ({columns}) "
            f"VALUES ({', '.join(values)});")


def _config_inserts_workbook(payload: dict, spec: ResolvedFeedSpec,
                             config: Config, banner: list[tuple[str, str]]):
    """config_inserts.xlsx: one sheet per populated tab, value rows on the
    real IIG layout, the generated INSERT statement as the final column."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    from codegen.metadata_sheet import _pin_workbook_properties

    dialect = config.framework.sql_dialect
    placeholder = config.framework.id_placeholder
    always_blank = set(config.demo.metadata_sheet.always_blank)

    workbook = Workbook()
    _pin_workbook_properties(workbook)
    workbook.remove(workbook.active)
    # Excel's hard per-cell limit is 32,767 characters; a wide feed's INSERT
    # (SRC_COLUMNS/TGT_COLUMN_NAMES lists) can exceed it, so oversize
    # statements continue in INSERT_STATEMENT_PART<n> columns — lossless,
    # never silently truncated.
    cell_limit = 32000
    for tab_name, tab in payload["tabs"].items():
        if not tab["rows"]:
            continue
        table = config.framework.tables.get(tab_name, tab_name)
        sheet = workbook.create_sheet(title=tab_name[:31])
        rendered = []
        max_parts = 1
        for row in tab["rows"]:
            display = [placeholder if h in always_blank else row["values"][h]
                       for h in tab["headers"]]
            statement = _insert_statement(tab["headers"], row, table, dialect,
                                          placeholder, always_blank)
            parts = [statement[i:i + cell_limit]
                     for i in range(0, len(statement), cell_limit)]
            max_parts = max(max_parts, len(parts))
            rendered.append((display, parts))
        headers = [*tab["headers"], "INSERT_STATEMENT",
                   *(f"INSERT_STATEMENT_PART{n}" for n in range(2, max_parts + 1))]
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for display, parts in rendered:
            padded = parts + [""] * (max_parts - len(parts))
            sheet.append([*display, *padded])
        for index in range(1, len(tab["headers"]) + 1):
            sheet.column_dimensions[get_column_letter(index)].width = 24
        for index in range(len(tab["headers"]) + 1, len(headers) + 1):
            sheet.column_dimensions[get_column_letter(index)].width = 100

    provenance = workbook.create_sheet(title="_provenance")
    provenance.append(["input", "value"])
    for cell in provenance[1]:
        cell.font = Font(bold=True)
    for key, value in banner:
        provenance.append([key, value])
    provenance.append(["dialect", dialect])
    provenance.append(["note", "Run only after the config rows workbook is "
                               "approved; the client's ADF metadata path "
                               "inserts these rows. Plain INSERTs — "
                               "idempotency belongs to the framework's load "
                               "path."])
    return workbook


# -- the emit ------------------------------------------------------------------ #


def emit_framework(
    spec: ResolvedFeedSpec,
    faq: LoadPatternFaq,
    ddl_sources: list[tuple[str, str]],
    config: Config,
    out_root: Path,
    base_dir: Path | None = None,
    frd_path: Path | None = None,
    unmapped_rule_texts: set[str] | None = None,
    conventions_profile: str | None = None,
    iig_template: str | None = None,
    env=None,
) -> FrameworkArtefacts:
    """Render one feed's Option B artefacts into ``out/<slug>/framework/``.

    ``conventions_profile`` / ``iig_template`` (M4) select the DDL layout
    and the IIG workbook version; the defaults reproduce today's output.

    ``env`` (M10): the environment reconciler, injected from the EDGE (cli /
    service) — anything with ``.environment`` and ``.probe(feed_slug, tables,
    payload) -> EnvProbeResult | None``. This module never imports a
    transport. None (the probe is disabled) = today's output, byte for byte;
    so is a probe that found nothing of this feed."""
    framework_dir = out_root / spec.feed_slug / "framework"
    framework_dir.mkdir(parents=True, exist_ok=True)
    root = base_dir if base_dir is not None else Path(".")
    profile = config.conventions.get(conventions_profile)
    template_name, template_cfg = config.metadata.resolve(iig_template)
    flags: list[str] = []

    payload = metadata_sheet_payload(
        config, root,
        specs=[spec],
        unmapped_by_slug={spec.feed_slug: unmapped_rule_texts or set()},
        run_label=spec.feed_slug,
        faq_by_slug={spec.feed_slug: faq},
        frd_path=frd_path,
        template=template_name,
    )
    payload = _filter_payload_for_feed(payload, spec.feed_slug)
    if template_cfg is not None:
        from codegen.metadata_template import blank_flags, shape_flags

        flags.extend(blank_flags(payload))
        flags.extend(shape_flags(payload))
    banner = _provenance_banner_rows(spec, faq, config,
                                     _faq_sha(spec, config, base_dir))

    files: list[Path] = []

    from codegen.metadata_sheet import stable_workbook_bytes

    # Deployment-team DDL: two plain .txt files (stage / standard), run in the
    # data lake by the deployment team; conformant to the reference goldens.
    stage_entries: list[tuple[str, str, str]] = []
    standard_entries: list[tuple[str, str, str]] = []
    omitted_side_tables: list[str] = []
    side_table_purposes = ("errors side-table", "processed-files ledger")
    for file_name, statement in ddl_sources:
        layer, _schema, table, purpose = _classify_ddl(file_name)
        if (not config.framework.deployment_ddl_include_side_tables
                and purpose in side_table_purposes):
            # The deployment .txt carries exactly the FRD's Target Table
            # Name list; the side-tables are CodeGen conventions and stay in
            # out/<slug>/ddl/ (and in notebook mode) untouched.
            omitted_side_tables.append(table)
            continue
        target = stage_entries if layer == "stage" else standard_entries
        target.append((file_name, statement, purpose))
    frd_tables = [s.stage_table.table for s in spec.segments]
    if spec.recycle is not None:
        frd_tables.append(spec.recycle.recycle_table.table)
    extra_banner_lines: list[str] = []
    if omitted_side_tables:
        extra_banner_lines.append(
            f"side-tables omitted from deployment DDL — not in FRD Target "
            f"Table Name (FRD lists: {', '.join(frd_tables)}); omitted: "
            f"{', '.join(sorted(omitted_side_tables))} (CodeGen conventions, "
            "kept in ddl/)")
    # M10: build every table FIRST, ask the environment about them (and about
    # the config rows of `payload`), then render — adjusted where it exists.
    from codegen.env.adjust import ddl_env_block
    from codegen.env.model import ExpectedTable

    combined_tables: tuple[dict | None, dict | None] = (None, None)
    layer_tables: dict[str, list[dict]] = {}
    abbrev = ""
    if profile.ddl_layout == "combined":
        # (flag order is report text: the file-name flag precedes the catalog flags)
        abbrev_answer = getattr(faq, "feed_abbreviation", None)
        if abbrev_answer is not None and abbrev_answer.source != "unknown":
            abbrev = str(abbrev_answer.value)
        else:
            abbrev = _sanitize_abbrev(spec.feed_slug)
            flags.append(f"ddl_file_name_from_slug: no feed_abbreviation in the load-pattern "
                         f"FAQ; the combined DDL is named {abbrev!r} from the feed slug")
        combined_tables = _combined_tables(spec, profile, flags, config)
        built = [(layer, [t]) for layer, t in zip(("stage", "standard"), combined_tables,
                                                  strict=True) if t is not None]
    else:
        for layer, entries in (("stage", stage_entries), ("standard", standard_entries)):
            layer_tables[layer] = _layer_tables(layer, entries, spec, config, profile, flags)
        built = list(layer_tables.items())
    env_result = None
    if env is not None:
        expected_tables = [
            ExpectedTable(qualified=t["qualified"], layer=layer,
                          columns=[((c["name"], c["dtype"]) if isinstance(c, dict) else tuple(c))
                                   for c in t["columns"]])
            for layer, tables in built for t in tables]
        # Config rows are probed only when a DML script is emitted for them.
        env_result = env.probe(
            spec.feed_slug, expected_tables,
            payload if config.dml.enabled and profile.emit_dml else None, faq)
    if env_result is not None and profile.reconcile_ddl:
        for _layer, tables in built:
            for t in tables:
                columns = [c if isinstance(c, dict) else {"name": c[0], "dtype": c[1]}
                           for c in t["columns"]]
                t["env_block"] = ddl_env_block(env_result.table(t["qualified"]), columns,
                                               env_result.probed_at)
    if profile.ddl_layout == "combined":
        ddl_names = [profile.ddl_file_name_pattern.format(feed_abbrev=abbrev)]
        combined = _render_combined(profile, *combined_tables)
        if combined is not None:
            if profile.target_system_header:
                combined = DDL_TARGET_HEADER + "\n" + combined
            txt_path = framework_dir / ddl_names[0]
            txt_path.write_text(combined, encoding="utf-8", newline="")
            files.append(txt_path)
        else:
            ddl_names = []
    else:
        ddl_names = []
        for layer in ("stage", "standard"):
            txt_path = framework_dir / f"{spec.feed_slug}_{layer}_table_creation.txt"
            text = _render_table_creation(layer, layer_tables[layer], banner,
                                          extra_banner_lines=extra_banner_lines)
            if profile.target_system_header:
                text = DDL_TARGET_HEADER + "\n" + text
            txt_path.write_text(text, encoding="utf-8", newline="\n")
            files.append(txt_path)
            ddl_names.append(txt_path.name)
    # M7 §3: the SQL Server DML deliverable from the same rows.
    dml_artefacts = None
    if config.dml.enabled and profile.emit_dml:
        from codegen.emit.dml import emit_dml

        dml_artefacts = emit_dml(spec, faq, payload, config, framework_dir, banner,
                                 env_probe=env_result,
                                 probed_environment=getattr(env, "environment", "") or "")
        files.extend(dml_artefacts.files)
        flags.extend(dml_artefacts.flags)
    if env_result is not None:
        from codegen.env.model import env_flags

        flags.extend(env_flags(env_result))
    # M7 gate checks: unstated catalog / schema is a FAIL, not a flag.
    checks: list[GateCheck] = []
    if dml_artefacts is not None:
        checks.extend(dml_artefacts.checks)
    unqualified = [f for f in flags if f.startswith(("catalog_unstated:", "schema_unstated:"))]
    if unqualified:
        checks.append(GateCheck(name="qualified_names", passed=False,
                                details="; ".join(unqualified)))
    ddl_texts = [(p.name, p.read_text(encoding="utf-8")) for p in files if p.suffix == ".txt"]
    checks.append(check_sql_literals(ddl_texts, config))
    checks.append(check_iig_derivations(payload, config))

    rows_workbook = build_workbook(payload)
    inputs_sheet = rows_workbook.create_sheet(title="_inputs")
    inputs_sheet.append(["input", "value"])
    for key, value in banner:
        inputs_sheet.append([key, value])
    rows_path = framework_dir / "config_rows.xlsx"
    rows_path.write_bytes(stable_workbook_bytes(rows_workbook))
    files.append(rows_path)

    inserts_path = framework_dir / "config_inserts.xlsx"
    inserts_workbook = _config_inserts_workbook(payload, spec, config, banner)
    if config.dml.enabled and profile.emit_dml:
        # M7 §4: sheet 1 says this workbook is the REVIEW copy; the executable
        # script is the per-environment .sql next to it.
        readme = inserts_workbook.create_sheet(title="README", index=0)
        readme.append(["review copy — executable script is config_inserts_<env>.sql "
                       f"(environments: {', '.join(config.dml.environments)}); run it from "
                       f"{config.dml.notebook_file_name_pattern.format(env='<env>')} against "
                       "the SQL Server metadata DB after the config rows are approved"])
        readme.column_dimensions["A"].width = 140
    inserts_path.write_bytes(stable_workbook_bytes(inserts_workbook))
    files.append(inserts_path)

    blank_list = (template_cfg.always_blank if template_cfg is not None
                  else config.demo.metadata_sheet.always_blank)
    always_blank = [
        header
        for tab in payload["tabs"].values()
        for header in tab["headers"]
        if header in set(blank_list)
    ]
    flagged = sorted(set(always_blank))
    ddl_row = (
        f"| {' / '.join(f'`{name}`' for name in ddl_names)} | Deployment-team "
        "DDL, conformant to the client's reference format (the `.sql` "
        "sources sit in `../ddl/`). **Run in the data lake by the "
        "deployment team** — the agent never creates target tables. |"
    )
    rows_row = (
        "| `config_rows.xlsx` | The config rows for the framework DB — "
        "**this is the approval artefact**. Every cell carries a provenance "
        "badge; the `_provenance` sheet lists them all. |"
    )
    inserts_row = (
        f"| `config_inserts.xlsx` | One sheet per populated IIG tab; value "
        f"rows on the client layout plus the generated INSERT statement "
        f"({config.framework.sql_dialect} dialect) as the final column. "
        "**Run only after approval**, through the client's existing ADF "
        "metadata path. Plain INSERTs — idempotency belongs to the "
        "framework's load path. |"
    )
    assumed_notes: list[str] = []
    held_back: list[str] = []
    seg = spec.segmented_extraction
    if seg is not None:
        ident = seg.identification
        assumed_notes.append(
            f"record identification ({ident.method}): trailer marker "
            f"{ident.trailer_marker!r}, header = {ident.header_rule} — "
            f"evidence: {ident.citation}")
        assumed_notes += [
            f"{entry.note} — evidence: {entry.citation}"
            for entry in seg.provenance_notes
        ]

    segmented_lines = [f"- **PROVENANCE**: {note}" for note in assumed_notes]
    segmented_lines += [f"- **HELD BACK**: {held}" for held in held_back]
    segmented_block = ("\n" + "\n".join(segmented_lines) + "\n"
                       if segmented_lines else "")
    groups = artefact_groups(files + [framework_dir / "ADDITION.md"])
    target_block = ""
    if TARGET_DML in groups:
        target_lines = ["", "## By target system", ""]
        notes = {
            TARGET_DDL: "run in the Databricks SQL editor / a notebook by the deployment team",
            TARGET_DML: "run from the Databricks notebook against the SQL Server metadata DB, "
                        "in one transaction, after the review sheets are approved",
            TARGET_REVIEW: "review copies — `config_inserts.xlsx` sheet 1 says so; the "
                           "executable script is `config_inserts_<env>.sql`",
            TARGET_NOTES: "this manifest",
        }
        for group, names in groups.items():
            target_lines.append(f"- **{group}** — {notes[group]}: "
                                + ", ".join(f"`{n}`" for n in names))
        target_block = "\n".join(target_lines) + "\n"
    addition_path = framework_dir / "ADDITION.md"
    addition_path.write_text(
        _ADDITION_TEMPLATE.format(
            slug=spec.feed_slug,
            banner="\n".join(f"- {k}: {v}" for k, v in banner),
            ddl_row=ddl_row,
            rows_row=rows_row,
            inserts_row=inserts_row,
            id_placeholder=config.framework.id_placeholder,
            blank_columns=", ".join(f"`{c}`" for c in flagged) or "none",
            segmented_block=segmented_block,
            target_block=target_block,
        ),
        encoding="utf-8", newline="\n",
    )
    files.append(addition_path)

    return FrameworkArtefacts(
        files=files,
        row_counts={name: len(tab["rows"]) for name, tab in payload["tabs"].items()},
        coverage=payload["coverage"],
        flagged_blank_columns=flagged,
        assumed_notes=assumed_notes,
        held_back=held_back,
        flags=flags,
        checks=checks,
        payload=payload,
        groups=artefact_groups(files),
        env_result=env_result,
        env_reconcile_ddl=bool(profile.reconcile_ddl),
        dml_emitted=bool(config.dml.enabled and profile.emit_dml),
    )


def report_section(artefacts: FrameworkArtefacts) -> str:
    """The "Framework output" section appended to the generation report."""
    coverage = artefacts.coverage
    lines = [
        "",
        "## Framework output (Option B)",
        "",
        "Artefacts under `framework/` — an addition to the existing ingestion",
        "framework. The config rows workbook is the approval artefact; the DDL",
        "and insert SQL are add-ons to ACFC's master notebook (the client's own",
        "notebook — never generated or edited by the agent), applied only after",
        "approval.",
        "",
        "| Artefact | Detail |",
        "| --- | --- |",
    ]
    for path in artefacts.files:
        lines.append(f"| `{path.name}` | framework/{path.name} |")
    for tab, count in artefacts.row_counts.items():
        lines.append(f"| rows: {tab} | {count} |")
    lines.append(
        f"| badge coverage | {coverage['derived']}/{coverage['total']} derived · "
        f"{coverage['synthetic']} synthetic · {coverage['needs_template']} "
        f"await the client template |"
    )
    lines.append(
        "| framework-assigned IDs | "
        + (", ".join(f"`{c}`" for c in artefacts.flagged_blank_columns) or "none")
        + " — left blank, never invented |"
    )
    for note in artefacts.assumed_notes:
        lines.append(f"| **PROVENANCE** | {note} |")
    for held in artefacts.held_back:
        lines.append(f"| **HELD BACK** | {held} |")
    return "\n".join(lines) + "\n"


# Badge labels re-exported for the report/UI so the vocabulary stays single-
# sourced from metadata_sheet.
__all__ = ["FrameworkArtefacts", "emit_framework", "report_section", "BADGE_LABELS"]
