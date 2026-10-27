"""The emitted DDL parses as SQL (2026-10-26).

The DDL is RUN by the engineer, so "valid SQL" is a gate check, not a hope:
every DDL text is parsed with sqlglot under ``gate.ddl_parse_dialect``
(``databricks``). A parse error, or a statement sqlglot can only keep as a raw
``Command`` (it did not recognise the statement), fails the check. Offline: no
warehouse, no EXPLAIN.

post112 (codeflow audit #15): the same check enforces the run-safe rule — a
``CREATE OR REPLACE`` empties a deployed table when the engineer re-runs the
file, so it fails the check (the pair-1 golden, which needs it, runs with the
check off).

sqlglot not installed where the gate runs: a ``sqlglot_unavailable`` flag, never
a FAIL (the ``ruff_unavailable`` rule). ``ddl_parse_dialect: null`` = no check.
"""

from __future__ import annotations

from codegen.gate.preflight import GateCheck

SQLGLOT_UNAVAILABLE = "sqlglot_unavailable"
NAME = "ddl_parses"


def check_ddl_parses(ddl_texts: list[tuple[str, str]], dialect: str) -> GateCheck:
    """One check over every (file name, text) DDL of the feed (the caller runs it
    only when ``gate.ddl_parse_dialect`` is set)."""
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError:
        return GateCheck(name=NAME, passed=True, not_run=True, flag=SQLGLOT_UNAVAILABLE,
                         details="sqlglot unavailable: the DDL was not parsed (sqlglot is a "
                                 "base dependency of codegen-data-engineer-agent — reinstall "
                                 "the package)")
    problems: list[str] = []
    statements = 0
    for name, text in ddl_texts:
        try:
            parsed = [node for node in sqlglot.parse(text, read=dialect) if node is not None]
        except Exception as exc:  # noqa: BLE001 — the parser's message IS the finding
            problems.append(f"{name}: sqlglot {dialect}: {str(exc).splitlines()[0][:200]}")
            continue
        statements += len(parsed)
        for index, node in enumerate(parsed, start=1):
            if isinstance(node, exp.Command):
                problems.append(f"{name}: statement {index} not recognised by sqlglot "
                                f"{dialect} (kept as a raw command)")
            elif isinstance(node, exp.Create) and node.args.get("replace"):
                problems.append(f"{name}: statement {index} is CREATE OR REPLACE — not safe "
                                "to re-run against a deployed table (use the profile's "
                                "create_statement: CREATE TABLE IF NOT EXISTS)")
    if problems:
        return GateCheck(name=NAME, passed=False, details="; ".join(problems))
    return GateCheck(name=NAME, passed=True,
                     details=f"{statements} statement(s) in {len(ddl_texts)} DDL file(s) parse "
                             f"under sqlglot {dialect}")


READ_ONLY_NAME = "ddl_tests_read_only"


def check_ddl_tests_read_only(texts: list[tuple[str, str]], dialect: str) -> GateCheck:
    """post128: every statement of the DDL test-cases file(s) is read-only - a
    SELECT, a DESCRIBE or a SHOW - so the engineer may paste the file whole."""
    try:
        import logging

        import sqlglot
        from sqlglot import exp
    except ImportError:
        return GateCheck(name=READ_ONLY_NAME, passed=True, not_run=True,
                         flag=SQLGLOT_UNAVAILABLE,
                         details="sqlglot unavailable: the DDL test cases were not parsed")
    problems: list[str] = []
    statements = 0
    for name, text in texts:
        logger = logging.getLogger("sqlglot")
        level = logger.level
        logger.setLevel(logging.ERROR)          # SHOW is parsed as a raw command, said once
        try:
            parsed = [node for node in sqlglot.parse(text, read=dialect) if node is not None]
        except Exception as exc:  # noqa: BLE001 — the parser's message IS the finding
            problems.append(f"{name}: sqlglot {dialect}: {str(exc).splitlines()[0][:200]}")
            continue
        finally:
            logger.setLevel(level)
        statements += len(parsed)
        for index, node in enumerate(parsed, start=1):
            # an empty statement (sqlglot's Semicolon after a raw SHOW) writes nothing
            if isinstance(node, (exp.Select, exp.Describe, exp.Semicolon)):
                continue
            if isinstance(node, exp.Command) and str(node.this).upper() == "SHOW":
                continue
            problems.append(f"{name}: statement {index} is not read-only "
                            f"({type(node).__name__})")
    if problems:
        return GateCheck(name=READ_ONLY_NAME, passed=False, details="; ".join(problems))
    return GateCheck(name=READ_ONLY_NAME, passed=True,
                     details=f"{statements} read-only statement(s) in {len(texts)} DDL "
                             "test-cases file(s)")
