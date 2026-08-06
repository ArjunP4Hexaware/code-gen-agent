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
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined

from codegen.emit.context import TemplateGapError
from codegen.emit.notebook import build_notebook

# The only audit columns the generated audit module knows how to populate.
_KNOWN_AUDIT_COLUMNS = {"LOB", "SRC_FILE_NAME", "REC_CREATION_TIME", "REC_UPDATED_TIME"}


def _py_literal(value: Any) -> str:
    """Render a value as a Python literal (tojson emits JSON's null/true/false)."""
    if value is None:
        return "None"
    if value is True:
        return "True"
    if value is False:
        return "False"
    return json.dumps(value)


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("codegen", "templates"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["py"] = _py_literal
    return env


def _check_gaps(context: dict[str, Any]) -> None:
    unknown_audit = [
        name for name, _dtype in context["audit_columns"] if name not in _KNOWN_AUDIT_COLUMNS
    ]
    if unknown_audit:
        raise TemplateGapError(
            f"no template populates audit column(s) {unknown_audit}; "
            f"known: {sorted(_KNOWN_AUDIT_COLUMNS)}"
        )


def emit_feed(context: dict[str, Any], output_root: Path) -> list[Path]:
    """Render every applicable template; returns the written paths."""
    _check_gaps(context)
    env = _environment()
    feed_dir = output_root / context["feed"]["slug"]

    # (template, output path, extra context) — order fixed for determinism.
    renders: list[tuple[str, Path, dict[str, Any]]] = []

    ddl_dir = feed_dir / "ddl"
    qualified_prefix = f"{context['default_catalog']}." if context["default_catalog"] else ""
    for seg in context["segments"]:
        renders.append(
            (
                "ddl/stage_table.sql.j2",
                ddl_dir / f"{context['stage_schema']}.{seg['stage_table']}.sql",
                {"seg": seg, "qualified_prefix": qualified_prefix},
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
    if context["standard"]:
        standard = context["standard"]
        standard_prefix = f"{standard['catalog']}." if standard["catalog"] else ""
        renders.append(
            (
                "ddl/standard_table.sql.j2",
                ddl_dir / f"{standard['schema']}.{standard['table']}.standard.sql",
                {"standard_qualified_prefix": standard_prefix},
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
    renders.append(("ruff.toml.j2", feed_dir / "ruff.toml", {}))
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
