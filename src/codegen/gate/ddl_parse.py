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

post158 (pentest CS-3): with the feed's own table names (``expected_tables``) the
check is an ALLOW-LIST - a statement is a ``CREATE TABLE`` (no ``AS SELECT``) or an
``ALTER TABLE ... SET`` (tags / properties) on a table the feed defines. Anything
else - a DROP, DELETE, INSERT, MERGE, GRANT, a CREATE of another table - FAILs,
however well it parses.

sqlglot not installed where the gate runs: a ``sqlglot_unavailable`` flag, never
a FAIL (the ``ruff_unavailable`` rule). ``ddl_parse_dialect: null`` = no check.
"""

from __future__ import annotations

from codegen.gate.preflight import GateCheck

SQLGLOT_UNAVAILABLE = "sqlglot_unavailable"
NAME = "ddl_parses"


def _table_name(node) -> str | None:
    """The lower-cased dotted name a CREATE / ALTER statement targets, quotes dropped."""
    from sqlglot import exp

    target = node.this.this if isinstance(node.this, exp.Schema) else node.this
    if not isinstance(target, exp.Table):
        return None
    return ".".join(part.name for part in target.parts).lower()


def _not_allowed(node, expected: set[str]) -> str | None:
    """Why ``node`` is outside the allow-list, or None when it is allowed."""
    from sqlglot import exp

    kind = str(node.args.get("kind") or "").upper()
    if isinstance(node, exp.Create):
        if kind != "TABLE" or node.args.get("expression") is not None:
            return "a CREATE that is not a plain CREATE TABLE"
    elif isinstance(node, exp.Alter):
        if kind != "TABLE" or not all(isinstance(a, exp.AlterSet)
                                      for a in node.args.get("actions") or []):
            return "an ALTER that is not ALTER TABLE ... SET"
    else:
        return f"a {type(node).__name__} statement"
    if _table_name(node) not in expected:
        return "on a table this feed does not define"
    return None


def check_ddl_parses(ddl_texts: list[tuple[str, str]], dialect: str,
                     expected_tables: list[str] | None = None) -> GateCheck:
    """One check over every (file name, text) DDL of the feed (the caller runs it
    only when ``gate.ddl_parse_dialect`` is set). ``expected_tables``: the
    feed's qualified table names - every statement must be allowed for them."""
    expected = ({name.replace("`", "").lower() for name in expected_tables}
                if expected_tables is not None else None)
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
            elif expected is not None and (why := _not_allowed(node, expected)):
                problems.append(f"{name}: statement {index} is {why} — the DDL may only "
                                "CREATE TABLE / ALTER TABLE ... SET the feed's own tables")
    if problems:
        return GateCheck(name=NAME, passed=False, details="; ".join(problems))
    return GateCheck(name=NAME, passed=True,
                     details=f"{statements} statement(s) in {len(ddl_texts)} DDL file(s) parse "
                             f"under sqlglot {dialect}")


READ_ONLY_NAME = "ddl_tests_read_only"


# post159 (P2-9, CS-2): the emitter writes every statement of the test-cases file
# on ONE physical line (``ddl_tests._prose``) and every other line as a ``--``
# comment; a line that is neither - document text whose line break escaped its
# comment - fails whatever the parser makes of it.
_READ_ONLY_LINE_STARTS = ("SELECT ", "SHOW ", "DESCRIBE ")


def _stray_lines(text: str) -> list[int]:
    """1-based numbers of the lines that are not blank, not a ``--`` comment and
    not a whole read-only statement (``SELECT`` / ``SHOW`` / ``DESCRIBE`` ...
    ``;``). Line breaks as Python reads them (``splitlines``: CR, VT, FF, NEL,
    U+2028 too) - a SQL editor may break on any of them."""
    stray = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith(_READ_ONLY_LINE_STARTS) and stripped.endswith(";"):
            continue
        stray.append(number)
    return stray


def check_ddl_tests_read_only(texts: list[tuple[str, str]], dialect: str) -> GateCheck:
    """post128: every statement of the DDL test-cases file(s) is read-only - a
    SELECT, a DESCRIBE or a SHOW - so the engineer may paste the file whole.
    post159 (P2-9): first, line by line (no parser needed): every line is a
    ``--`` comment or one whole read-only statement."""
    stray = [(name, numbers) for name, text in texts if (numbers := _stray_lines(text))]
    problems: list[str] = [
        f"{name}: line(s) {', '.join(map(str, numbers[:10]))}"
        + (f" (+{len(numbers) - 10})" if len(numbers) > 10 else "")
        + " neither a -- comment nor one read-only statement" for name, numbers in stray]
    try:
        import logging

        import sqlglot
        from sqlglot import exp
    except ImportError:
        if problems:            # the line check needs no parser: still a FAIL
            return GateCheck(name=READ_ONLY_NAME, passed=False, details="; ".join(problems))
        return GateCheck(name=READ_ONLY_NAME, passed=True, not_run=True,
                         flag=SQLGLOT_UNAVAILABLE,
                         details="sqlglot unavailable: the DDL test cases were not parsed")
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
