"""Option B (framework output): snapshot-guarded Option A + framework mode.

The notebook-mode snapshot (``tests/snapshots/notebook_mode.json``) was
generated from the pre-change emitter at the start of the Option B session;
the suite regenerates the three CV feeds in notebook mode and asserts every
emitted file's sha256 against it — Option A stays byte-identical or this
fails. Framework-mode tests assert the artefact contract: workbooks open,
sheets match the configured layout, IDs are placeholders, banners present,
inserts are dialect-sane, verdict identical across modes, and a second
render is byte-identical.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from codegen import cli
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]
_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
_SNAPSHOT = REPO / "tests" / "snapshots" / "notebook_mode.json"

needs_demo_pair = pytest.mark.skipif(
    not (_FRD.is_file() and _STTM.is_file()),
    reason="demo fixture pair not restored (removed 2026-08-22)",
)


def _config_into(config, tmp: Path, mode: str):
    return config.model_copy(update={
        "output": config.output.model_copy(update={
            "dir": str(tmp / "out"), "reports_dir": str(tmp / "reports"),
            "mode": mode,
        })
    })


def _generate_all(config, tmp: Path, mode: str, output_mode: str | None = None):
    scoped = _config_into(config, tmp, mode)
    specs = resolve_pair(_FRD, _STTM, scoped)
    for spec in specs:
        gate = cli._generate_feed(spec, scoped, dry_run=True, skip_tests=True,
                                  output_mode=output_mode)
        yield spec, gate


def _manifest(tmp: Path) -> dict[str, str]:
    manifest = {}
    for base, label in ((tmp / "out", "out"), (tmp / "reports", "reports")):
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rel = f"{label}/{p.relative_to(base).as_posix()}"
                manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return manifest


@needs_demo_pair
def test_notebook_mode_matches_pre_change_snapshot(config, tmp_path):
    for _spec, _gate in _generate_all(config, tmp_path, "notebook"):
        pass
    snapshot = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    assert _manifest(tmp_path) == snapshot


@pytest.fixture(scope="module")
def framework_run(config, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("framework_mode")
    results = list(_generate_all(config, tmp, "framework"))
    return tmp, results


@needs_demo_pair
def test_framework_mode_tree_and_verdicts(config, framework_run, tmp_path):
    tmp, results = framework_run
    notebook_gates = {
        spec.feed_slug: gate.verdict
        for spec, gate in _generate_all(config, tmp_path, "notebook")
    }
    for spec, gate in results:
        feed_dir = tmp / "out" / spec.feed_slug
        # Verdict identical across modes — the gate ran on the full render.
        assert gate.verdict == notebook_gates[spec.feed_slug] == "PASS_WITH_FLAGS"
        # No notebook, no module tree; ddl + framework + candidates only.
        assert not (feed_dir / f"{spec.feed_slug}.ipynb").exists()
        assert not (feed_dir / "pipeline").exists()
        assert (feed_dir / "ddl").is_dir()
        names = sorted(p.name for p in (feed_dir / "framework").iterdir())
        assert names == ["ADDITION.md", "config_inserts.sql",
                         "config_rows.xlsx", "ddl_scripts.xlsx"]


@needs_demo_pair
def test_framework_workbooks_layout_and_provenance(config, framework_run):
    tmp, results = framework_run
    layout = config.demo.metadata_sheet
    for spec, _gate in results:
        framework_dir = tmp / "out" / spec.feed_slug / "framework"

        rows_workbook = load_workbook(framework_dir / "config_rows.xlsx")
        assert rows_workbook.sheetnames == [*layout.tabs, "_provenance", "_inputs"]
        for name, tab in layout.tabs.items():
            assert [c.value for c in rows_workbook[name][1]] == tab.headers
        inputs = {row[0].value: row[1].value
                  for row in rows_workbook["_inputs"].iter_rows(min_row=2)}
        assert spec.frd_contract_sha256 in inputs["FRD contract"]
        assert spec.sttm_contract_sha256 in inputs["STTM contract"]
        assert "Load-pattern FAQ" in inputs
        assert "stand-in" in inputs["Layout"]

        ddl_workbook = load_workbook(framework_dir / "ddl_scripts.xlsx")
        assert ddl_workbook.sheetnames == ["ddl_scripts", "_provenance"]
        ddl_rows = list(ddl_workbook["ddl_scripts"].iter_rows(min_row=2,
                                                              values_only=True))
        assert len(ddl_rows) == len(list((tmp / "out" / spec.feed_slug /
                                          "ddl").glob("*.sql")))
        assert all(row[4].startswith("--") or "CREATE" in row[4]
                   for row in ddl_rows)  # statement column holds real SQL


@needs_demo_pair
def test_framework_inserts_ids_are_placeholders(config, framework_run):
    tmp, results = framework_run
    for spec, _gate in results:
        sql = (tmp / "out" / spec.feed_slug / "framework" /
               "config_inserts.sql").read_text(encoding="utf-8")
        assert f"feed {spec.feed_slug} (sqlserver dialect)" in sql
        assert spec.frd_contract_sha256 in sql  # provenance header comment
        assert "assigned by ACFC framework" in sql
        assert "idempotency belongs" in sql
        # sqlserver dialect shapes; row count = 1 file_layout + 2 load_config
        # + one per mapped column.
        inserts = [line for line in sql.splitlines()
                   if line.startswith("INSERT INTO ")]
        columns = sum(len(seg.fields) for seg in spec.segments)
        assert len(inserts) == 1 + 2 + columns
        assert all(line.startswith("INSERT INTO [") for line in inserts)
        first = inserts[0]
        # The three file_layout ID columns render as the placeholder.
        assert first.split("VALUES (")[1].startswith("NULL, NULL, NULL")


@needs_demo_pair
def test_lakebase_dialect(config, tmp_path):
    lakebase = config.model_copy(update={
        "framework": config.framework.model_copy(update={
            "sql_dialect": "lakebase",
            "tables": {"file_layout": "meta.ig_file_layout"},
        })
    })
    results = list(_generate_all(lakebase, tmp_path, "framework"))
    spec, _gate = results[0]
    sql = (tmp_path / "out" / spec.feed_slug / "framework" /
           "config_inserts.sql").read_text(encoding="utf-8")
    assert 'INSERT INTO "meta"."ig_file_layout" ("pipeline_id"' in sql
    assert "N'" not in sql  # no sqlserver unicode literals in lakebase


@needs_demo_pair
def test_both_mode_is_the_union(config, tmp_path):
    for spec, gate in _generate_all(config, tmp_path, "both"):
        feed_dir = tmp_path / "out" / spec.feed_slug
        assert gate.verdict == "PASS_WITH_FLAGS"
        assert (feed_dir / f"{spec.feed_slug}.ipynb").is_file()
        assert (feed_dir / "pipeline").is_dir()
        assert (feed_dir / "framework" / "config_rows.xlsx").is_file()
        report = (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(
            encoding="utf-8")
        assert "## Framework output (Option B)" in report


@needs_demo_pair
def test_framework_mode_rendered_twice_is_byte_identical(config, tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    for tmp in (first, second):
        for _ in _generate_all(config, tmp, "framework"):
            pass
    assert _manifest(first) == _manifest(second)
