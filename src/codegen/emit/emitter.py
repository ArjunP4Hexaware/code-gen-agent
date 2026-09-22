"""Render the template set for one feed into ``out/<feed_slug>/``.

Also assembles ``<feed_slug>.ipynb`` — the whole pipeline as one runnable
Databricks notebook (see :mod:`codegen.emit.notebook`).

Deterministic: templates receive a fully-materialized context, files are
written LF/UTF-8, and nothing here consults a clock. Unknown spec features
raise :class:`TemplateGapError` so the gate FAILs instead of emitting a
half-covered pipeline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined

from codegen import lint_rules
from codegen.emit.context import KNOWN_AUDIT_COLUMNS as _KNOWN_AUDIT_COLUMNS  # noqa: F401
from codegen.emit.notebook import build_notebook


def _py_literal(value: Any) -> str:
    """Render a value as a Python literal (tojson emits JSON's null/true/false)."""
    if value is None:
        return "None"
    if value is True:
        return "True"
    if value is False:
        return "False"
    return json.dumps(value)


# A generated module must pass the lint config emitted next to it, and both
# come from codegen.lint_rules — the one place the rule set is stated.
_LINE_LENGTH = lint_rules.LINE_LENGTH
_INDENT = "    "


def _py_const(value: str, name: str) -> str:
    """``NAME = "literal"`` — or, when that line would exceed the emitted ruff
    line length (a free-text FRD value such as a long 'Data Source' cell), the
    same literal as a parenthesized implicit concatenation split at word
    boundaries. The text is transcribed verbatim either way (JSON escaping,
    exactly what ``tojson`` emitted before)."""
    literal = json.dumps(value)
    line = f"{name} = {literal}"
    if len(line) <= _LINE_LENGTH:
        return line
    budget = _LINE_LENGTH - len(_INDENT)
    words = [w for w in re.split(r"(?<=\s)", value) if w]
    chunks: list[str] = []
    current = ""
    for word in words:
        if current and len(json.dumps(current + word)) > budget:
            chunks.append(current)
            current = word
        else:
            current += word
    if current:
        chunks.append(current)
    body = "\n".join(f"{_INDENT}{json.dumps(c)}" for c in chunks)
    return f"{name} = (\n{body}\n)"


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("codegen", "templates"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["py"] = _py_literal
    env.filters["pyconst"] = _py_const
    return env


def _check_gaps(context: dict[str, Any]) -> None:
    """M11 item 13: an audit column no rule populates is no longer a stop —
    the audit module writes it as a typed NULL and the gate flags it
    (``audit_column_unpopulated``, from ``context["unpopulated_audit"]``)."""
    return None


def emit_feed(context: dict[str, Any], output_root: Path) -> list[Path]:
    """Render every applicable template; returns the written paths."""
    _check_gaps(context)
    env = _environment()
    feed_dir = output_root / context["feed"]["slug"]

    # (template, output path, extra context) — order fixed for determinism.
    renders: list[tuple[str, Path, dict[str, Any]]] = []

    ddl_dir = feed_dir / "ddl"
    qualified_prefix = f"{context['default_catalog']}." if context["default_catalog"] else ""
    for seg in context.get("stage_tables", context["segments"]):
        renders.append(
            (
                "ddl/stage_table.sql.j2",
                ddl_dir / f"{context['stage_schema']}.{seg['stage_table']}.sql",
                # Per-segment audit columns override the feed-wide set (equal
                # on flat feeds, so their rendering is byte-identical).
                {"seg": seg, "qualified_prefix": qualified_prefix,
                 "audit_columns": seg["audit_columns"]},
            )
        )
    renders.append(
        (
            "ddl/errors_table.sql.j2",
            ddl_dir / f"{context['stage_schema']}.{context['errors_table']}.sql",
            {"qualified_prefix": qualified_prefix},
        )
    )
    renders.append(
        (
            "ddl/processed_files_table.sql.j2",
            ddl_dir / f"{context['stage_schema']}.{context['processed_files_table']}.sql",
            {"qualified_prefix": qualified_prefix},
        )
    )
    if context["recycle"]:
        renders.append(
            (
                "ddl/recycle_table.sql.j2",
                ddl_dir / f"{context['stage_schema']}.{context['recycle']['table']}.sql",
                {"qualified_prefix": qualified_prefix},
            )
        )
    # One standard DDL per standard table: flat feeds carry exactly one; a
    # segmented feed maps each segment to its own table in BOTH layers.
    for standard in context["standard_tables"]:
        standard_prefix = f"{standard['catalog']}." if standard["catalog"] else ""
        renders.append(
            (
                "ddl/standard_table.sql.j2",
                ddl_dir / f"{standard['schema']}.{standard['table']}.standard.sql",
                {"standard": standard, "standard_qualified_prefix": standard_prefix,
                 "audit_columns": standard.get("audit_columns",
                                               context["audit_columns"])},
            )
        )

    pipeline_dir = feed_dir / "pipeline"
    modules = ["feed_spec", "masking", "reader", "drift", "mapping", "audit", "rejects"]
    if context["is_segmented"]:
        modules.insert(3, "segments")
    if context["recycle"]:
        modules += ["reference", "recycle"]
    modules += ["writer", "dq", "run_report", "orchestrator"]
    renders.append(("pyspark/__init__.py.j2", pipeline_dir / "__init__.py", {}))
    for module in modules:
        renders.append((f"pyspark/{module}.py.j2", pipeline_dir / f"{module}.py", {}))

    job_dir = feed_dir / "job"
    renders.append(("job/workflow.json.j2", job_dir / "workflow.json", {}))
    renders.append(("job/notebook_entrypoint.py.j2", job_dir / "notebook_entrypoint.py", {}))

    tests_dir = feed_dir / "tests"
    renders.append(("tests/conftest.py.j2", tests_dir / "conftest.py", {}))
    for module in modules:
        renders.append((f"tests/test_{module}.py.j2", tests_dir / f"test_{module}.py", {}))

    renders.append(("fixtures/make_fixtures.py.j2", feed_dir / "tools" / "make_fixtures.py", {}))
    renders.append(("ruff.toml.j2", feed_dir / "ruff.toml", lint_rules.template_context()))
    renders.append(("readme.md.j2", feed_dir / "README.md", {}))

    written: list[Path] = []
    rendered_by_path: dict[Path, str] = {}
    for template_name, output_path, extra in renders:
        template = env.get_template(template_name)
        rendered = template.render({**context, **extra})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        rendered_by_path[output_path] = rendered
        written.append(output_path)

    # Consolidated single-notebook artifact, assembled from the sources just
    # rendered so it can never drift from the module files.
    notebook_text = build_notebook(
        context,
        module_sources=[(m, rendered_by_path[pipeline_dir / f"{m}.py"]) for m in modules],
        ddl_sources=[
            (path.name, rendered_by_path[path])
            for _template, path, _extra in renders
            if path.parent == ddl_dir
        ],
        entrypoint_source=rendered_by_path[job_dir / "notebook_entrypoint.py"],
    )
    notebook_path = feed_dir / f"{context['feed']['slug']}.ipynb"
    notebook_path.write_text(notebook_text, encoding="utf-8", newline="\n")
    written.append(notebook_path)
    return written
