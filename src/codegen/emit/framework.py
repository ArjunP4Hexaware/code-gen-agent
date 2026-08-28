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
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.faq import LoadPatternFaq, summarize
from codegen.metadata_sheet import (
    BADGE_LABELS,
    build_workbook,
    metadata_sheet_payload,
)

_ADDITION_TEMPLATE = """\
# Framework addition — {slug}

{banner}

Option B output: an **addition to the existing ingestion framework** (the
~90% case), not a standalone pipeline. On approval it is loaded into the
existing ingestion framework database.

| File | What it is |
| --- | --- |
{ddl_row}
{rows_row}
{inserts_row}
| `ADDITION.md` | This manifest. |

Columns awaiting framework-assigned IDs (rendered as `{id_placeholder}`,
never invented): {blank_columns}.

Layout note: the tab names and column headers are a stand-in until the
client's metadata template arrives — values carry over.

After approval, a workflow wraps the common notebook with the assigned IDs.
The agent never inserts unapproved rows.
"""


@dataclass(frozen=True)
class FrameworkArtefacts:
    """What one feed's Option B emit produced (for reports and the UI)."""

    files: list[Path]
    row_counts: dict[str, int]
    coverage: dict[str, int]
    flagged_blank_columns: list[str] = field(default_factory=list)


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
        ("Layout", "stand-in until the client's metadata template arrives; "
                   "values carry over"),
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
                if badge in ("from_sttm", "from_sttm_unmapped", "from_frd",
                             "from_faq"):
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


# -- ddl_scripts.xlsx ---------------------------------------------------------- #

_DDL_HEADERS = ["layer", "schema", "table", "purpose", "statement", "source_file"]


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


def _ddl_workbook(ddl_sources: list[tuple[str, str]],
                  banner: list[tuple[str, str]]):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    from codegen.metadata_sheet import _pin_workbook_properties

    workbook = Workbook()
    _pin_workbook_properties(workbook)
    sheet = workbook.active
    sheet.title = "ddl_scripts"
    sheet.append(_DDL_HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for file_name, statement in ddl_sources:
        layer, schema, table, purpose = _classify_ddl(file_name)
        sheet.append([layer, schema, table, purpose, statement, file_name])

    provenance = workbook.create_sheet(title="_provenance")
    provenance.append(["input", "value"])
    for cell in provenance[1]:
        cell.font = Font(bold=True)
    for key, value in banner:
        provenance.append([key, value])
    provenance.append(["note", "DDL is engineer-run; the agent never creates "
                               "target tables (create_tables: false)."])
    return workbook


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


def _config_inserts_sql(payload: dict, spec: ResolvedFeedSpec, config: Config,
                        banner: list[tuple[str, str]]) -> str:
    dialect = config.framework.sql_dialect
    placeholder = config.framework.id_placeholder
    always_blank = set(config.demo.metadata_sheet.always_blank)

    lines = [
        f"-- Framework config inserts — feed {spec.feed_slug} ({dialect} dialect)",
        "-- Run ONLY after the config rows workbook is approved, through the",
        "-- client's existing metadata path. Plain INSERTs: idempotency belongs",
        "-- to the framework's load path, not to these statements.",
    ]
    lines += [f"-- {key}: {value}" for key, value in banner]
    lines.append("")

    for tab_name, tab in payload["tabs"].items():
        if not tab["rows"]:
            continue
        table = config.framework.tables.get(tab_name, tab_name)
        lines.append(f"-- {tab_name}: {len(tab['rows'])} row(s) "
                     f"-> {table}")
        for row in tab["rows"]:
            headers = tab["headers"]
            blanks = [h for h in headers if h in always_blank]
            if blanks:
                lines.append(f"-- {', '.join(blanks)}: assigned by ACFC framework")
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
            lines.append(
                f"INSERT INTO {_sql_table(table, dialect)} ({columns}) "
                f"VALUES ({', '.join(values)});"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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

    ddl_path = framework_dir / "ddl_scripts.xlsx"
    ddl_path.write_bytes(stable_workbook_bytes(_ddl_workbook(ddl_sources, banner)))
    files.append(ddl_path)

    rows_workbook = build_workbook(payload)
    inputs_sheet = rows_workbook.create_sheet(title="_inputs")
    inputs_sheet.append(["input", "value"])
    for key, value in banner:
        inputs_sheet.append([key, value])
    rows_path = framework_dir / "config_rows.xlsx"
    rows_path.write_bytes(stable_workbook_bytes(rows_workbook))
    files.append(rows_path)

    inserts_path = framework_dir / "config_inserts.sql"
    inserts_path.write_text(_config_inserts_sql(payload, spec, config, banner),
                            encoding="utf-8", newline="\n")
    files.append(inserts_path)

    always_blank = [
        header
        for tab in payload["tabs"].values()
        for header in tab["headers"]
        if header in set(config.demo.metadata_sheet.always_blank)
    ]
    flagged = sorted(set(always_blank))
    ddl_row = (
        "| `ddl_scripts.xlsx` | Target table definitions as a reviewable "
        "workbook (one row per DDL statement; the `.sql` sources sit in "
        "`../ddl/`). **Engineer-run** — the agent never creates target "
        "tables. |"
    )
    rows_row = (
        "| `config_rows.xlsx` | The config rows for the framework DB — "
        "**this is the approval artefact**. Every cell carries a provenance "
        "badge; the `_provenance` sheet lists them all. |"
    )
    inserts_row = (
        f"| `config_inserts.sql` | One INSERT per approved row "
        f"({config.framework.sql_dialect} dialect). **Run only after "
        "approval**, through the client's existing metadata path (adapter "
        "to be built). Plain INSERTs — idempotency belongs to the "
        "framework's load path. |"
    )
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
        ),
        encoding="utf-8", newline="\n",
    )
    files.append(addition_path)

    return FrameworkArtefacts(
        files=files,
        row_counts={name: len(tab["rows"]) for name, tab in payload["tabs"].items()},
        coverage=payload["coverage"],
        flagged_blank_columns=flagged,
    )


def report_section(artefacts: FrameworkArtefacts) -> str:
    """The "Framework output" section appended to the generation report."""
    coverage = artefacts.coverage
    lines = [
        "",
        "## Framework output (Option B)",
        "",
        "Artefacts under `framework/` — an addition to the existing ingestion",
        "framework; the config rows workbook is the approval artefact and the",
        "inserts run only after approval through the client's metadata path.",
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
    return "\n".join(lines) + "\n"


# Badge labels re-exported for the report/UI so the vocabulary stays single-
# sourced from metadata_sheet.
__all__ = ["FrameworkArtefacts", "emit_framework", "report_section", "BADGE_LABELS"]
