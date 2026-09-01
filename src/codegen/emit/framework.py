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
{segmented_block}
Layout note: the tab names and column headers are the client IIG template
(anonymized reference — `fixtures/reference/SFMC_IIG.xlsx`).

On approval: the config rows land in the ingestion framework database, and
the DDL + insert SQL are added on to ACFC's master notebook with the
framework-assigned IDs. The agent never inserts unapproved rows.
"""


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
    landing = (spec.landing_location or spec.feed_slug).replace("\\", "/").strip("/")
    prefix = config.framework.synthetic_location_prefix.rstrip("/")
    return f"{prefix}/{landing}/{table}"


def _table_creation_text(layer: str, entries: list[tuple[str, str, str]],
                         spec: ResolvedFeedSpec, config: Config,
                         banner: list[tuple[str, str]],
                         extra_banner_lines: list[str] | None = None) -> str:
    """Render one deployment-team .txt file for a layer's DDL entries."""
    from codegen.emit.emitter import _environment

    descriptions = _description_map(spec)
    tables = []
    for _file_name, statement, purpose in sorted(
            entries, key=lambda e: (_DDL_PURPOSE_ORDER.get(e[2], 9), e[0])):
        qualified, columns = _parse_ddl_statement(statement)
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
                f"{purpose.capitalize()} for feed {spec.feed_name} "
                f"(source: {spec.source_system})"),
            "location": (_synthetic_location(spec, config, qualified.rsplit(".", 1)[-1])
                         if layer == "stage" else None),
            "tags": ((spec.domain, spec.sub_domain)
                     if spec.domain and spec.sub_domain else None),
        })
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
) -> FrameworkArtefacts:
    """Render one feed's Option B artefacts into ``out/<slug>/framework/``."""
    framework_dir = out_root / spec.feed_slug / "framework"
    framework_dir.mkdir(parents=True, exist_ok=True)
    root = base_dir if base_dir is not None else Path(".")

    payload = metadata_sheet_payload(
        config, root,
        specs=[spec],
        unmapped_by_slug={spec.feed_slug: unmapped_rule_texts or set()},
        run_label=spec.feed_slug,
        faq_by_slug={spec.feed_slug: faq},
        frd_path=frd_path,
    )
    payload = _filter_payload_for_feed(payload, spec.feed_slug)
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
    for layer, entries in (("stage", stage_entries), ("standard", standard_entries)):
        txt_path = framework_dir / f"{spec.feed_slug}_{layer}_table_creation.txt"
        txt_path.write_text(
            _table_creation_text(layer, entries, spec, config, banner,
                                 extra_banner_lines=extra_banner_lines),
            encoding="utf-8", newline="\n")
        files.append(txt_path)

    rows_workbook = build_workbook(payload)
    inputs_sheet = rows_workbook.create_sheet(title="_inputs")
    inputs_sheet.append(["input", "value"])
    for key, value in banner:
        inputs_sheet.append([key, value])
    rows_path = framework_dir / "config_rows.xlsx"
    rows_path.write_bytes(stable_workbook_bytes(rows_workbook))
    files.append(rows_path)

    inserts_path = framework_dir / "config_inserts.xlsx"
    inserts_path.write_bytes(stable_workbook_bytes(
        _config_inserts_workbook(payload, spec, config, banner)))
    files.append(inserts_path)

    always_blank = [
        header
        for tab in payload["tabs"].values()
        for header in tab["headers"]
        if header in set(config.demo.metadata_sheet.always_blank)
    ]
    flagged = sorted(set(always_blank))
    ddl_row = (
        f"| `{spec.feed_slug}_stage_table_creation.txt` / "
        f"`{spec.feed_slug}_standard_table_creation.txt` | Deployment-team "
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
