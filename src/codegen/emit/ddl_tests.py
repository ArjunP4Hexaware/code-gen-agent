"""post128: the DDL test cases (Nikshit's review, 2026-10-23; Venu, 2026-10-27).

A SEPARATE framework artefact next to the combined DDL, never inside it, named
like the DDL with the profile's ``ddl_test_cases_suffix`` before the extension
(``ACCUM_DDL.txt`` -> ``ACCUM_DDL_TestCases.txt``). It is read-only SQL and
``--`` comments the ENGINEER runs after the DDL in a Databricks SQL editor; the
agent writes it and never runs it. Every statement is a SELECT or a SHOW (the
gate check ``ddl_tests_read_only`` proves it), so the file may be pasted whole.

Every value comes from the resolved feed (the FRD / STTM / VDD it was built
from) or from the DDL the same run wrote; a value no document states is OPEN in
the text and raises one ``ddl_tests_open:<case>`` flag - never a guess. The
cases and their order are the profile's ``ddl_test_cases`` list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from codegen.contracts.resolved import ResolvedFeedSpec

OPEN = "OPEN (no document states it)"
READ_ONLY_CHECK = "ddl_tests_read_only"
# the Spark CSV reader's default, said once in the mapping_mode case
_SPARK_POSITIONAL = ("Spark applies a given schema to a delimited file BY POSITION and ignores "
                     "the header names unless the header is validated (enforceSchema=false); "
                     "a fixed-width file is positional by definition.")


@dataclass(frozen=True)
class DdlTestCases:
    text: str
    flags: list[str] = field(default_factory=list)


def ddl_test_cases_name(ddl_name: str, suffix: str) -> str:
    """``ACCUM_DDL.txt`` + ``_TestCases`` -> ``ACCUM_DDL_TestCases.txt``."""
    stem, dot, extension = ddl_name.rpartition(".")
    return f"{stem}{suffix}.{extension}" if dot else f"{ddl_name}{suffix}"


def _prose(value) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def _literal(value: str) -> str:
    from codegen.emit.framework import _sql_comment

    return "'" + _sql_comment(value) + "'"


def _parts(qualified: str) -> tuple[str, str, str] | None:
    parts = qualified.split(".")
    return (parts[0], parts[1], parts[2]) if len(parts) == 3 else None


def _fields_of(spec: ResolvedFeedSpec, segments: tuple[str, ...]):
    return [f for s in spec.segments if s.segment in segments for f in s.fields]


def _tables(spec: ResolvedFeedSpec, definitions, profile) -> list[dict]:
    """Every table block the DDL wrote, with what its cases need."""
    tables = []
    required_sources = set(spec.not_null_columns)
    for definition in definitions:
        fields = _fields_of(spec, definition.segments)
        for block in (definition.stage, definition.standard):
            if block is None or not block.qualified:
                continue
            names = {name for name, _type in block.columns}
            if block.layer == "stage":
                column = [f.stage_column for f in fields]
                keyed = [f.stage_column for f in fields if f.primary_key]
                strategy = spec.stage_load_strategy
                properties = profile.stage_tblproperties or {}
            else:
                column = [f.standard_column for f in fields]
                keyed = [f.standard_column for f in fields
                         if (f.standard_primary_key if f.standard_primary_key is not None
                             else f.primary_key)]
                strategy = spec.standard_load_strategy
                properties = profile.standard_tblproperties or {}
            required = [c for f, c in zip(fields, column, strict=True)
                        if c and c in names and (f.source_column in required_sources
                                                 or c in keyed)]
            tables.append({
                "layer": block.layer, "qualified": block.qualified,
                "parts": _parts(block.qualified), "columns": list(block.columns),
                "comment_count": len(block.comments), "table_comment": block.table_comment,
                "key": [c for c in keyed if c in names],
                "required": list(dict.fromkeys(required)),
                "strategy": strategy, "properties": list(properties.items()),
                "mapping": [(f.source_column, f.stage_column, f.standard_column)
                            for f in fields] if block.layer == "stage" else [],
            })
    return tables


def _case(title: str, lines: list[str], sql: list[tuple[str, list[str]]] | None = None) -> dict:
    return {"title": title, "lines": lines,
            "sql": [{"statement": s, "expected": e} for s, e in (sql or [])]}


def build(spec: ResolvedFeedSpec, definitions, profile, ddl_name: str,
          banner: list[tuple[str, str]], tags: tuple[str, str] | None) -> DdlTestCases:
    """The test-cases text for one feed's combined DDL (``ddl_name``)."""
    from codegen.emit.emitter import _environment

    flags: list[str] = []
    tables = _tables(spec, definitions, profile)
    stage_tables = [t for t in tables if t["layer"] == "stage"]
    patterns = ", ".join(repr(p) for p in spec.file_name_patterns)
    cases: list[dict] = []

    def open_value(case: str, value, reason: str) -> str:
        if value:
            return _prose(value)
        flags.append(f"ddl_tests_open:{case} — {reason}; the case says OPEN")
        return OPEN

    for name in profile.ddl_test_cases:
        if name == "file_available":
            frequency = open_value(name, spec.frequency, "no document states the frequency")
            cases.append(_case("File available", [
                f"Check: a file matching {patterns} arrives for the run (frequency: {frequency}).",
                "Negative: no file for the run -> the load stops and reports the missing file; "
                "nothing is loaded.",
                "From: the FRD / STTM file name pattern; the FRD frequency."]))
        elif name == "file_location":
            landing = open_value(name, spec.landing_location,
                                 "no document states the landing location")
            cases.append(_case("File in the right location", [
                f"Check: the file is in the landing location: {landing}.",
                "Negative: the file sits in another folder -> it is reported missing, never "
                "picked up from there.",
                "From: the FRD landing location."]))
        elif name == "column_mapping":
            for table in stage_tables:
                cases.append(_case(f"Column mapping — {table['qualified']}", [
                    "Check: load a test file; each source column lands in the column the STTM "
                    "maps it to (source -> stage -> standard):",
                    *(f"  {s} -> {st} -> {sd or '(stage only)'}" for s, st, sd in
                      table["mapping"]),
                    "Negative: a test file missing one source column -> the load fails or "
                    "rejects the rows; no column is left silently empty.",
                    "From: the STTM mapping rows."]))
        elif name == "columns_populated":
            for table in tables:
                if not table["required"]:
                    cases.append(_case(f"Required columns populated — {table['qualified']}", [
                        "No document marks a column of this table required or as a key: no "
                        "check."]))
                    continue
                select = ", ".join(f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS "
                                   f"{c}_missing" for c in table["required"])
                cases.append(_case(f"Required columns populated — {table['qualified']}", [
                    f"Check: every row fills {', '.join(table['required'])}.",
                    f"Negative: a test file with {table['required'][0]} blank -> the row is "
                    "rejected or flagged, never loaded with a NULL.",
                    "From: the STTM / FRD required (not-null) and primary-key columns."],
                    [(f"SELECT {select} FROM {table['qualified']}", ["every column 0"])]))
        elif name == "column_shift":
            for table in stage_tables:
                columns = [c for c, _t in table["columns"]]
                cases.append(_case(f"Column shift — {table['qualified']}", [
                    f"Check: the file's {len(table['mapping'])} source columns arrive in the "
                    f"STTM order, first {table['mapping'][0][0]!r}, last "
                    f"{table['mapping'][-1][0]!r}; the table has {len(columns)} columns "
                    "(audit columns included).",
                    "Negative: a test file with two columns swapped, or one inserted -> the load "
                    "fails or rejects; no value ever lands one column over.",
                    "From: the STTM column order (and the VDD positions for a fixed-width "
                    "file). How this behaves depends on the next case."]))
        elif name == "mapping_mode":
            delimiter = (repr(spec.delimiter) if spec.delimiter
                         else "none (fixed width)")
            cases.append(_case("Columns matched by name or by position?", [
                f"File: format {_prose(spec.file_format)}, delimiter {delimiter}.",
                f"Note: {_SPARK_POSITIONAL}",
                "Question for the framework owners: does the framework validate the header row? "
                "If not, the column shift case loads shifted values silently - its negative "
                "test is the one that matters most."]))
        elif name == "record_count":
            for table in stage_tables:
                cases.append(_case(f"Record count — {table['qualified']}", [
                    "Check: every data record of the file is loaded (or rejected and counted).",
                    "From: the file itself at test time (its trailer count where it has one)."],
                    [(f"SELECT COUNT(*) AS rows_loaded FROM {table['qualified']}",
                      ["the file's data record count minus the rows the load rejected, "
                       "after a first load into the empty table"])]))
        elif name == "key_unique":
            for table in tables:
                if not table["key"]:
                    cases.append(_case(f"Primary key unique — {table['qualified']}", [
                        "No document states a primary key for this table: no check."]))
                    continue
                key = ", ".join(table["key"])
                strategy = _prose(table["strategy"]) if table["strategy"] else OPEN
                cases.append(_case(f"Primary key unique — {table['qualified']}", [
                    f"Check: the primary key ({key}) is unique (load strategy: {strategy}).",
                    "Negative: load the same file twice -> the key stays unique (an Upsert "
                    "updates the row; an Append is stopped by the processed-files check).",
                    "From: the STTM Primary Key cells; the FRD load strategy."],
                    [(f"SELECT {key}, COUNT(*) AS copies FROM {table['qualified']} "
                      f"GROUP BY {key} HAVING COUNT(*) > 1", ["no rows"])]))
        elif name in ("table_exists", "columns_match", "comments_present", "table_tags"):
            for table in tables:
                case = _schema_case(name, table, tags)
                if case is not None:
                    cases.append(case)
                elif table["parts"] is None:
                    flags.append(f"ddl_tests_unqualified:{table['qualified']} — not a "
                                 f"three-part name; no {name} case")
        elif name == "table_properties":
            for table in tables:
                if not table["properties"]:
                    continue
                cases.append(_case(f"Table properties — {table['qualified']}", [
                    "Check: the TBLPROPERTIES the DDL sets are on the deployed table.",
                    "From: the DDL (the profile's table properties)."],
                    [(f"SHOW TBLPROPERTIES {table['qualified']}",
                      [f"includes {k} = {v}" for k, v in table["properties"]])]))
        elif name == "ddl_rerun":
            cases.append(_case("The DDL is safe to run again", [
                f"Check: run {ddl_name} a second time against the deployed tables -> no error, "
                f"and every table keeps its rows (each statement is "
                f"{profile.create_statement}).",
                "Negative: none - a re-run never drops or empties a table.",
                "From: the DDL."]))
    for number, case in enumerate(cases, start=1):
        case["id"] = f"TC{number:02d}"
    text = _environment().get_template("framework/ddl_test_cases.txt.j2").render(
        ddl_name=ddl_name, feed=spec.feed_slug, banner=banner, cases=cases)
    return DdlTestCases(text=text, flags=flags)


def _schema_case(name: str, table: dict, tags: tuple[str, str] | None) -> dict | None:
    """A structure case read from the catalog's information_schema."""
    if table["parts"] is None:
        return None
    catalog, schema, table_name = table["parts"]
    where = (f"WHERE table_schema = {_literal(schema)} AND table_name = "
             f"{_literal(table_name)}")
    label = f"{table['qualified']} ({table['layer']})"
    if name == "table_exists":
        return _case(f"Table exists — {label}", [
            "Check: the DDL created the table in the stated catalog and schema.",
            "From: the DDL."],
            [(f"SELECT COUNT(*) AS tables_found FROM {catalog}.information_schema.tables "
              f"{where}", ["1"])])
    if name == "columns_match":
        return _case(f"Columns and types match the DDL — {label}", [
            "Check: the deployed columns, their order and types are the DDL's (compare the "
            "type names case-insensitively).",
            "From: the DDL (the STTM columns and types)."],
            [(f"SELECT ordinal_position, column_name, full_data_type FROM "
              f"{catalog}.information_schema.columns {where} ORDER BY ordinal_position",
              [f"{len(table['columns'])} rows, in this order:",
               *(f"  {i} {c} {t}" for i, (c, t) in enumerate(table["columns"], start=1))])])
    if name == "comments_present":
        sql = [(f"SELECT COUNT(*) AS columns_with_comment FROM "
                f"{catalog}.information_schema.columns {where} AND comment IS NOT NULL",
                [str(table["comment_count"])])]
        if table["table_comment"]:
            sql.append((f"SELECT comment FROM {catalog}.information_schema.tables {where}",
                        [_prose(table["table_comment"])]))
        return _case(f"Comments present — {label}", [
            "Check: the column and table COMMENTs the DDL writes are on the deployed table.",
            "From: the DDL (the STTM descriptions, primary-key notes, the FRD load "
            "strategy)."], sql)
    if name == "table_tags":
        if tags is None:
            return None
        return _case(f"Tags — {label}", [
            "Check: the DOMAIN / SUBDOMAIN tags the DDL sets are on the deployed table.",
            "From: the FRD Domain / Sub-Domain."],
            [(f"SELECT tag_name, tag_value FROM {catalog}.information_schema.table_tags "
              f"WHERE schema_name = {_literal(schema)} AND table_name = "
              f"{_literal(table_name)} ORDER BY tag_name",
              [f"DOMAIN = {tags[0]}", f"SUBDOMAIN = {tags[1]}"])])
    return None
