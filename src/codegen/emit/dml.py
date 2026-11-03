"""The SQL Server metadata-DB runner notebook (M7 §3; retired SQL 2026-10-08).

The metadata rows themselves are ``metadata_inserts.sql``
(:mod:`codegen.emit.metadata_inserts`): the client's "DDL", written on every
framework run from the same cells as the IIG, one ``<<COLUMN#n>>`` placeholder
per open cell. Its predecessor, ``config_inserts_<env>.sql`` — one script per
environment with a variables block — is RETIRED (2026-10-08): its single
``@OBJECT_ID`` / ``@PIPELINE_ID`` / ``@GROUP_ID`` per script gave every row the
same id, a primary-key collision on any feed with more than one object or
pipeline; the per-row placeholders replace it.

What remains here, behind the profile's ``emit_dml`` + ``dml.enabled``
switches, is the Databricks notebook source that RUNS ``metadata_inserts.sql``
against the metadata DB over JDBC — one per environment
(``dml.notebook_file_name_pattern``), the secret-scope NAMES from config, ONE
transaction, and a refusal to send anything while a placeholder is left.

The T-SQL helpers (``_ident``, ``_table``, ``validate_tsql``) are shared with
``metadata_inserts``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config
from codegen.gate.preflight import GateCheck

_SEMANTICS = "docs/acfc/METADATA_DB_SEMANTICS.md"


@dataclass(frozen=True)
class DmlArtefacts:
    files: list[Path]
    flags: list[str] = field(default_factory=list)
    checks: list[GateCheck] = field(default_factory=list)


# ------------------------------------------------------------------- SQL bits


def _ident(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def _table(schema: str, name: str) -> str:
    return f"{_ident(schema)}.{_ident(name)}"


def _strip_comment(line: str) -> str:
    """The line without its trailing ``--`` comment (a ``--`` inside a quoted
    literal is kept)."""
    in_quote = False
    for i, ch in enumerate(line):
        if ch == "'":
            in_quote = not in_quote
        elif not in_quote and line.startswith("--", i):
            return line[:i].rstrip()
    return line


_OPENERS = ("BEGIN", "BEGIN TRY", "BEGIN CATCH")
_CLOSERS = ("END", "END TRY", "END CATCH", "END CATCH;")


def _statements(text: str) -> list[str]:
    """Top-level statements of the script: comments dropped, BEGIN / END (and
    the TRY / CATCH wrapper's BEGIN TRY … END CATCH) lines are structure
    (balanced separately), everything else accumulates until a line ending
    in ';'."""
    statements: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = _strip_comment(raw.strip())
        if not line:
            continue
        if line in _OPENERS or line in _CLOSERS:
            continue
        current.append(line)
        if line.endswith(";"):
            statements.append(" ".join(current))
            current = []
    if current:
        statements.append(" ".join(current))
    return statements


def validate_tsql(text: str) -> list[str]:
    """Parse problems, statement by statement, under sqlglot's tsql dialect —
    a statement sqlglot can only keep as a raw ``Command`` counts as a
    problem, so the check is real, not a fallback. Without sqlglot: a
    structural check (balanced quotes / parentheses / BEGIN-END)."""
    problems: list[str] = []
    stripped = [_strip_comment(ln.strip()) for ln in text.splitlines()]
    opened = sum(ln in _OPENERS for ln in stripped)
    closed = sum(ln in _CLOSERS for ln in stripped)
    if opened != closed:
        problems.append(f"BEGIN/END unbalanced ({opened} vs {closed})")
    body = "\n".join(ln for ln in stripped if ln)
    if body.replace("''", "").count("'") % 2:
        problems.append("unbalanced single quotes")
    if body.count("(") != body.count(")"):
        problems.append("unbalanced parentheses")
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError:  # pragma: no cover — the structural fallback above is the check
        return problems
    for statement in _statements(text):
        try:
            parsed = sqlglot.parse(statement, read="tsql")
        except Exception as exc:  # noqa: BLE001 — the parser's message IS the finding
            problems.append(f"sqlglot tsql: {statement[:80]!r}: {str(exc)[:160]}")
            continue
        for node in parsed:
            if node is None or isinstance(node, exp.Command):
                problems.append(f"sqlglot tsql: {statement[:80]!r}: not recognised as a "
                                "statement (parsed as a raw command)")
    return problems


# -------------------------------------------------------------------- notebook


def _notebook_source(env: str, sql_name: str, config: Config) -> str:
    from codegen.emit.emitter import _environment

    template = _environment().get_template("framework/insert_scripts_notebook.py.j2")
    return template.render(env=env, sql_name=sql_name,
                           secret_scope=config.dml.secret_scope,
                           jdbc_url_secret=config.dml.jdbc_url_secret,
                           user_secret=config.dml.user_secret,
                           password_secret=config.dml.password_secret,
                           semantics=_SEMANTICS)


# ------------------------------------------------------------------------ emit


def emit_dml(config: Config, framework_dir: Path, sql_name: str) -> DmlArtefacts:
    """The runner notebook per environment for ``sql_name`` (the feed's
    ``metadata_inserts.sql``, written next to it)."""
    files: list[Path] = []
    for env in config.dml.environments:
        notebook = framework_dir / config.dml.notebook_file_name_pattern.format(env=env)
        notebook.write_text(_notebook_source(env, sql_name, config), encoding="utf-8",
                            newline="\n")
        files.append(notebook)
    return DmlArtefacts(files=files)


__all__ = ["DmlArtefacts", "emit_dml", "validate_tsql"]
