"""The SQL Server metadata DB side of ``metadata_inserts.sql`` (2026-10-08).

``config_inserts_<env>.sql`` is retired; its DB-side knowledge is ported into
``metadata_inserts.sql`` (``codegen.emit.metadata_inserts``):

* workbook -> DB value maps (``dml.db_value_map``: ACTIVE_FLAG 'Y' -> 'S',
  named in a header comment citing the walkthrough), blank audit dates ->
  GETDATE(), the walkthrough's "not populated" columns -> NULL;
* ``@RFC_NUMBER`` for blank CREATED_BY / UPDATED_BY, ``NULL -- ASSIGN``-style
  ``<<RFC_NUMBER>>`` + ``dml_unassigned`` when the FAQ does not answer it;
* GUARDS before the first INSERT — PIPELINE_ID / GROUP_ID / the (GROUP_ID,
  OBJECT_ID, PIPELINE_ID) key unused — and the connection reuse-or-insert
  lookup (SCOPE_IDENTITY), all inside SET XACT_ABORT ON + TRY / CATCH with
  one transaction: the script aborts rather than half-inserts;
* one INSERT per IIG row in dependency order, no line break inside a literal,
  every statement parses under sqlglot's tsql dialect (placeholders as NULL),
  the per-sheet counts equal the IIG's.

``emit_dml`` + ``dml.enabled`` now gate only the runner notebooks, which run
``metadata_inserts.sql`` and refuse while a placeholder is left.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from codegen import cli
from codegen.config import load_config
from codegen.emit.dml import validate_tsql
from codegen.emit.framework import emit_framework
from codegen.emit.metadata_inserts import FILE_NAME, placeholders_as_null
from codegen.faq import FaqAnswer, LoadPatternFaq
from conftest import with_dml

REPO = Path(__file__).resolve().parents[1]

pytest.importorskip("sqlglot", reason="sqlglot validates the emitted T-SQL")


def _scoped(config, tmp: Path):
    return config.model_copy(update={"output": config.output.model_copy(update={
        "dir": str(tmp / "out"), "reports_dir": str(tmp / "reports")})})


def _inserts(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("INSERT INTO [dbo].[")
            and "FILE_CONNECTION_DETAILS" not in ln]


@pytest.fixture(scope="module")
def pair1_dml(pair1_config, pair1_spec, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("pair1_dml")
    gate = cli._generate_feed(pair1_spec, _scoped(with_dml(pair1_config), tmp), dry_run=True,
                              skip_tests=True, output_mode="framework",
                              conventions_profile="acfc_prx", iig_template="iig_v2")
    framework = tmp / "out" / pair1_spec.feed_slug / "framework"
    return gate, framework, (framework / FILE_NAME).read_text(encoding="utf-8")


def test_the_retired_script_is_not_written_and_the_notebooks_run_metadata_inserts(pair1_dml):
    gate, framework_dir, _text = pair1_dml
    assert gate.verdict == "PASS_WITH_FLAGS", [c for c in gate.checks if not c.passed]
    assert not list(framework_dir.glob("config_inserts_*.sql"))
    for env in ("q1", "a2", "prod"):
        notebook = framework_dir / f"Insert_scripts_config_table_{env}.py"
        text = notebook.read_text(encoding="utf-8")
        assert f'SQL_NAME = "{FILE_NAME}"' in text and f"# ENVIRONMENT = {env}" in text
    assert not any(c.name.startswith(("dml_parse_", "dml_row_counts")) for c in gate.checks)


def test_db_values_header_and_cells(pair1_dml):
    _gate, _dir, text = pair1_dml
    header = text[:text.index("SET NOCOUNT ON;")]
    assert "-- DB VALUES (docs/acfc/METADATA_DB_SEMANTICS.md; config dml.*)" in header
    assert "--   ACTIVE_FLAG: workbook 'Y' -> 'S' (§1" in header and "UNCONFIRMED" in header
    inserts = _inserts(text)
    assert all("N'S'" in ln for ln in inserts if "[ACTIVE_FLAG]" in ln)
    assert not any("N'Y'" in ln for ln in inserts if "[ACTIVE_FLAG]" in ln)
    with_audit = [ln for ln in inserts if "[CREATED_BY]" in ln]
    assert with_audit and all(ln.rstrip(");").endswith(
        "@RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE()") or "GETDATE()" in ln
        for ln in with_audit)
    schedule = [ln for ln in inserts if "[DATA_FACTORY_PIPELINE_SCHEDULE]" in ln]
    assert len(schedule) == 4
    # DAY_OF_SCHEDULE: the workbook keeps the golden's '0'; the DB gets NULL (§2, §10)
    columns = re.search(r"\((.*?)\) VALUES", schedule[0])[1].split(", ")
    assert "[DAY_OF_SCHEDULE]" in columns


def test_variables_guards_and_the_connection_lookup(pair1_dml):
    gate, _dir, text = pair1_dml
    assert "DECLARE @RFC_NUMBER NVARCHAR(50) = <<RFC_NUMBER>>;" in text
    assert "DECLARE @SRC_HOST_NAME NVARCHAR(200) = <<SRC_HOST_NAME>>;" in text
    assert "DECLARE @SRC_ROOT_PATH NVARCHAR(400) = N'/Pharmacy/Accumulators/';" in text
    assert "DECLARE @SRC_CONNECTION_ID INT = NULL;" in text
    assert sorted(f.split(" — ")[0] for f in gate.flags if f.startswith("dml_unassigned:")) == [
        "dml_unassigned:@RFC_NUMBER", "dml_unassigned:@SRC_HOST_NAME"]
    assert any(f.startswith("dml_unconfirmed:connection_table") for f in gate.flags)
    for number in range(1, 5):
        assert (f"IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE "
                f"[PIPELINE_ID] = <<PIPELINE_ID#{number}>>) RAISERROR(") in text
        assert (f"IF EXISTS (SELECT 1 FROM [dbo].[ADLS_DELTA_INGESTION_DETAILS] WHERE "
                f"[GROUP_ID] = <<GROUP_ID#{number}>> AND [OBJECT_ID] = N'{number}' AND "
                f"[PIPELINE_ID] = <<PIPELINE_ID#{number}>>) RAISERROR(") in text
    assert ("IF EXISTS (SELECT 1 FROM [dbo].[FILE_ADLS_INGESTION_DETAILS] WHERE [GROUP_ID] = "
            "<<GROUP_ID#1>>) RAISERROR(") in text
    # an id filled in as NULL aborts (the retired script's IS NULL checks), per placeholder
    for line in ("IF <<PIPELINE_ID#4>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 4: "
                 "PIPELINE_ID is not assigned', 16, 1);",
                 "IF <<GROUP_ID#2>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 2: "
                 "GROUP_ID is not assigned', 16, 1);",
                 "IF <<OBJECT_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: "
                 "OBJECT_ID is not assigned', 16, 1);"):
        assert line in text
    assert "IF N'1' IS NULL" not in text                     # a literal id needs no check
    assert "IF @CONNECTION_MATCHES > 1 RAISERROR(" in text
    # a NULL host with no connection id aborts — never a connection row keyed by NULL
    host_guard = ("IF @SRC_CONNECTION_ID IS NULL AND @SRC_HOST_NAME IS NULL RAISERROR(N'SRC_HOST_"
                  "NAME is not assigned")
    assert host_guard in text
    assert text.index(host_guard) < text.index("INSERT INTO [dbo].[FILE_CONNECTION_DETAILS]")
    assert "SET @SRC_CONNECTION_ID = SCOPE_IDENTITY();" in text
    file_adls = next(ln for ln in _inserts(text) if "[FILE_ADLS_INGESTION_DETAILS]" in ln)
    assert "@SRC_CONNECTION_ID" in file_adls


def test_the_script_aborts_rather_than_half_inserts(pair1_dml):
    _gate, _dir, text = pair1_dml
    lines = [ln.strip() for ln in text.splitlines()]
    first_insert = next(i for i, ln in enumerate(lines) if ln.startswith("INSERT INTO [dbo].[")
                        and "FILE_CONNECTION_DETAILS" not in ln)
    begin = lines.index("BEGIN TRY")
    assert lines[lines.index("SET XACT_ABORT ON;") + 1] == "BEGIN TRY"
    assert lines[begin + 1] == "BEGIN TRANSACTION;"
    guards = [i for i, ln in enumerate(lines) if ln.startswith(("IF EXISTS", "IF @RFC_NUMBER",
                                                               "IF @CONNECTION_MATCHES",
                                                               "IF @SRC_CONNECTION_ID IS NULL AND",
                                                               "IF <<"))]
    assert guards and begin < min(guards) and max(guards) < first_insert
    assert lines[-6:] == ["COMMIT TRANSACTION;", "END TRY", "BEGIN CATCH",
                          "IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;", "THROW;", "END CATCH;"]


def test_counts_equal_the_iig_order_and_every_statement_parses(pair1_dml):
    gate, framework_dir, text = pair1_dml
    from openpyxl import load_workbook

    wb = load_workbook(framework_dir / "config_rows.xlsx")
    iig_counts = {ws.title: ws.max_row - 1 for ws in wb.worksheets if not ws.title.startswith("_")}
    counts = {m.group(1): int(m.group(2))
              for m in re.finditer(r"^-- ([A-Z_]+): (\d+) row\(s\)", text, re.M)}
    assert counts == iig_counts
    order = list(counts)
    assert order[:3] == ["DATA_FACTORY_PIPELINE_SCHEDULE", "FILE_ADLS_INGESTION_DETAILS",
                         "ADLS_DELTA_INGESTION_DETAILS"]
    assert any("table not yet described" in ln for ln in text.splitlines())
    assert validate_tsql(placeholders_as_null(text)) == []
    assert next(c for c in gate.checks if c.name == "metadata_inserts").passed


def test_no_literal_spans_lines_and_none_carries_pointer_text(pair1_dml):
    _gate, _dir, text = pair1_dml
    for match in re.finditer(r"N'((?:[^']|'')*)'", text):
        assert "\n" not in match.group(1)
        assert "refer to" not in match.group(1).lower()


def test_faq_answers_fill_the_variables(pair1_config, pair1_spec, tmp_path):
    faq = LoadPatternFaq(
        rfc_number=FaqAnswer(value="SYN001", source="engineer", evidence="ticket"),
        feed_abbreviation=FaqAnswer(value="ACCUM", source="engineer"),
        source_host=FaqAnswer(value="mft.synthetic.example", source="engineer",
                              evidence="platform team"),
        connection_ids={"SRC_CONNECTION_ID": "31"},
    )
    framework = emit_framework(pair1_spec, faq, [], with_dml(pair1_config), tmp_path,
                               conventions_profile="acfc_prx", iig_template="iig_v2")
    assert not any(f.startswith("dml_unassigned:") for f in framework.flags)
    text = (tmp_path / pair1_spec.feed_slug / "framework" / FILE_NAME).read_text(encoding="utf-8")
    # The audit cells carry the FAQ's RFC (IIG: RFC<n>); the connection row still needs it.
    assert "DECLARE @RFC_NUMBER NVARCHAR(50) = N'RFCSYN001';" in text
    assert "DECLARE @SRC_HOST_NAME NVARCHAR(200) = N'mft.synthetic.example';" in text
    assert "DECLARE @SRC_CONNECTION_ID INT = 31;" in text
    assert "<<RFC_NUMBER>>" not in text and "<<SRC_HOST_NAME>>" not in text
    assert next(c for c in framework.checks if c.name == "metadata_inserts").passed


def test_the_value_map_is_config(pair1_config, pair1_spec, tmp_path):
    dml = with_dml(pair1_config).dml.model_copy(update={"db_value_map": {}})
    config = with_dml(pair1_config).model_copy(update={"dml": dml})
    emit_framework(pair1_spec, LoadPatternFaq(), [], config, tmp_path,
                   conventions_profile="acfc_prx", iig_template="iig_v2")
    text = (tmp_path / pair1_spec.feed_slug / "framework" / FILE_NAME).read_text(encoding="utf-8")
    assert all("N'Y'" in ln for ln in _inserts(text) if "[ACTIVE_FLAG]" in ln)


def test_notebook_refuses_placeholders_and_names_secrets_only(pair1_dml, pair1_config):
    _gate, framework_dir, _text = pair1_dml
    text = (framework_dir / "Insert_scripts_config_table_q1.py").read_text(encoding="utf-8")
    assert text.startswith("# Databricks notebook source\n# TARGET SYSTEM = SQL Server metadata "
                           "DB\n# RUN FROM = Databricks notebook\n")
    assert f'SECRET_SCOPE = "{pair1_config.dml.secret_scope}"' in text
    assert "dbutils.secrets.get(SECRET_SCOPE, KEY_NAME_JDBC_URL)" in text
    assert "connection.setAutoCommit(False)" in text and "connection.rollback()" in text
    assert 'PLACEHOLDER = re.compile(r"<<[A-Za-z0-9_]+(?:#\\d+)?>>")' in text
    assert "placeholder(s) not filled" in text
    assert not re.search(r"password\s*=\s*['\"][^'\"]+['\"]", text, re.IGNORECASE)


def test_reference_profile_writes_metadata_inserts_but_no_notebook(pair1_config, pair1_spec,
                                                                   tmp_path):
    framework = emit_framework(pair1_spec, LoadPatternFaq(), [], pair1_config, tmp_path,
                               conventions_profile="edo_sfmc", iig_template="iig_v1")
    names = {p.name for p in framework.files}
    assert FILE_NAME in names
    assert not any(n.startswith(("config_inserts_", "Insert_scripts_config_table_"))
                   for n in names)


def test_multi_file_frd_takes_the_sttm_frequency_and_no_pointer_text(tmp_path):
    from test_derivations import FRD_CATALOG, _pair11_specs

    config = load_config(REPO / "config" / "config.yaml")
    (tmp_path / "contracts").mkdir()
    specs, _flags = _pair11_specs(FRD_CATALOG, tmp_path / "contracts", config)
    risk = next(s for s in specs if s.feed_slug == "vc_individual_risk")
    gate = cli._generate_feed(risk, _scoped(config, tmp_path), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")
    assert gate.verdict == "PASS_WITH_FLAGS", [c for c in gate.checks if not c.passed]
    text = (tmp_path / "out" / "vc_individual_risk" / "framework" / FILE_NAME
            ).read_text(encoding="utf-8")
    literals = [m.group(1) for m in re.finditer(r"N'((?:[^']|'')*)'", text)]
    assert "Monthly" in literals                       # FREQUENCY from the STTM File Details
    assert not any("refer to" in lit.lower() or "\n" in lit for lit in literals)
    assert "Vendor Files =" not in text                # the label-prefixed description never lands


def test_shipped_settings_write_metadata_inserts_and_no_notebook(pair1_config, pair1_spec,
                                                                 tmp_path):
    """emit_dml ships false: the runner notebooks are not written, the metadata
    rows are (they are the client's "DDL"), and the run report says so."""
    assert pair1_config.conventions.profiles["acfc_prx"].emit_dml is False
    cli._generate_feed(pair1_spec, _scoped(pair1_config, tmp_path), dry_run=True,
                       skip_tests=True, output_mode="framework",
                       conventions_profile="acfc_prx", iig_template="iig_v2")
    framework = tmp_path / "out" / pair1_spec.feed_slug / "framework"
    assert (framework / FILE_NAME).is_file()
    assert not list(framework.glob("Insert_scripts_config_table_*.py"))
    report = (tmp_path / "reports" / f"{pair1_spec.feed_slug}.md").read_text(encoding="utf-8")
    assert ("| DML | runner notebooks not generated (disabled) — conventions profile 'acfc_prx' "
            "has emit_dml: false; `metadata_inserts.sql` is written regardless |") in report
