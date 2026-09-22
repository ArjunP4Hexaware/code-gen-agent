"""What a deployment DDL says about a table that already exists (M10). Pure.

``absent`` / ``unreadable`` / not probed -> no block: the CREATE is emitted
exactly as without a probe. ``identical`` -> a comment, no statement.
``different`` -> ``ALTER TABLE … ADD COLUMNS`` for ADDITIVE drift only, and a
REVIEW block that lists every type / removal difference with NO statement.
Never DROP. Never CREATE OR REPLACE over an existing table.
"""

from __future__ import annotations

from codegen.env.model import ProbedObject


def ddl_env_block(probed: ProbedObject | None, columns: list[dict],
                  probed_at: str) -> str | None:
    """``columns``: [{name, dtype, comment?}] as the DDL would create them."""
    if probed is None or probed.state not in ("identical", "different"):
        return None
    name = probed.name
    if probed.state == "identical":
        return (f"-- ENVIRONMENT identical: {name} exists and matches this DDL "
                f"(probed {probed_at}) - no change, no statement.")
    lines = [f"-- ENVIRONMENT different: {name} exists and DIFFERS from this DDL "
             f"(probed {probed_at}).",
             "-- Never DROP, never CREATE OR REPLACE over an existing table."]
    by_name = {c["name"].lower(): c for c in columns}
    additive = [by_name[d.column.lower()] for d in probed.additive
                if d.column.lower() in by_name]
    if additive:
        lines.append("-- additive drift: columns this DDL has and the table lacks")
        lines.append(f"ALTER TABLE {name} ADD COLUMNS (")
        for index, column in enumerate(additive):
            comment = f" COMMENT '{column['comment']}'" if column.get("comment") else ""
            closing = ");" if index == len(additive) - 1 else ","
            lines.append(f"  {column['name']} {column['dtype']}{comment}{closing}")
    review = probed.needs_review
    if review:
        lines.append("-- REVIEW - differences with NO statement (decide by hand):")
        for d in review:
            if d.kind == "type":
                lines.append(f"--   {d.column}: type - this DDL {d.expected} | "
                             f"environment {d.actual}")
            else:
                lines.append(f"--   {d.column}: in the environment ({d.actual}), "
                             "not in this DDL")
    return "\n".join(lines)


def ddl_action(probed: ProbedObject, reconcile: bool) -> str:
    """The report's "what the artefact does about it" cell for a table."""
    if probed.state == "absent":
        return "CREATE, as without a probe"
    if probed.state == "unreadable":
        return "CREATE, as without a probe (the environment could not be asked)"
    if not reconcile:
        return ("the profile's CREATE statement regardless (conventions reconcile_ddl is off) "
                "- REVIEW before running")
    if probed.state == "identical":
        return "comment only - no CREATE"
    parts = []
    if probed.additive:
        parts.append(f"ALTER TABLE ADD COLUMNS ({len(probed.additive)})")
    if probed.needs_review:
        parts.append(f"REVIEW block, no statement ({len(probed.needs_review)})")
    return "; ".join(parts) + " - no CREATE"


def dml_action(probed: ProbedObject, emit_updates: bool, adjusted: bool) -> str:
    """The report's "what the artefact does about it" cell for a config row."""
    if probed.state == "unreadable":
        return "INSERT, as without a probe (the environment could not be asked)"
    if probed.state == "absent":
        return ("INSERT + an expected-state assertion (still absent)" if adjusted
                else "INSERT, as without a probe")
    if probed.state == "identical":
        return "skipped with a comment + an assertion (still identical)"
    if emit_updates:
        return "REVIEW block + UPDATE of the differing columns (dml.emit_updates)"
    return ("REVIEW block, UPDATE candidate commented out + an assertion that fails while the "
            "row still differs")
