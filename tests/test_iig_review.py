"""IIG-first M3: every framework run writes the BSA review copy and the clean
copy of the IIG workbook.

* Clean copy (``<feed>_IIG.xlsx``): exactly the iig_v2 template's sheets and
  column order, values only — no fills, comments or summary sheet; on pair 1
  its data cells equal the run's ``config_rows.xlsx``.
* Review copy (``<feed>_IIG_REVIEW.xlsx``): the summary sheet first; its
  counts per owner equal the 2026-10-02 inventory (IIG_FIRST_PLAN.md) —
  pair 1: BSA 92, engineer 157, engineer-confirms 129, set-at-load 52;
  pair 11 (three feeds): 132, 141, 84, 42. Every open cell is filled and
  commented (reason, citation, owner).
* Owners come from the ``iig_review`` config table: a sheet + column key
  moves cells without a code change.
"""

from __future__ import annotations

import collections
from pathlib import Path

import pytest
from openpyxl import load_workbook

from codegen import cli
from codegen.config import IigReviewConfig, load_config
from test_derivations import FRD_CATALOG, REPO, _pair11_specs, _scoped

INVENTORY = {
    "pair1": {"BSA": 92, "Engineer": 157, "Engineer (confirm)": 129, "Set at load (CI/CD)": 52},
    "pair11": {"BSA": 132, "Engineer": 141, "Engineer (confirm)": 84, "Set at load (CI/CD)": 42},
}


def _run(specs, config, tmp: Path) -> list[Path]:
    for spec in specs:
        cli._generate_feed(spec, _scoped(config, tmp), dry_run=True, skip_tests=True,
                           output_mode="framework", conventions_profile="acfc_prx",
                           iig_template="iig_v2")
    return [tmp / "out" / spec.feed_slug / "framework" for spec in specs]


@pytest.fixture(scope="module")
def pair1_dirs(pair1_config, pair1_spec, tmp_path_factory):
    return _run([pair1_spec], pair1_config, tmp_path_factory.mktemp("iig_pair1"))


@pytest.fixture(scope="module")
def pair11_dirs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("iig_pair11")
    config = load_config(REPO / "config" / "config.yaml")
    (tmp / "contracts").mkdir()
    specs, _ = _pair11_specs(FRD_CATALOG, tmp / "contracts", config)
    return _run(specs, config, tmp)


def _only(framework: Path, suffix: str) -> Path:
    (path,) = [p for p in framework.glob("*.xlsx") if p.name.endswith(suffix)]
    return path


def _owner_totals(dirs: list[Path]) -> tuple[dict, int]:
    totals: collections.Counter = collections.Counter()
    groups = 0
    for framework in dirs:
        summary = load_workbook(_only(framework, "_IIG_REVIEW.xlsx"))["REVIEW_SUMMARY"]
        for row in summary.iter_rows(min_row=2, values_only=True):
            totals[row[3]] += row[4]
            groups += 1
    return dict(totals), groups


def test_both_workbooks_are_written_with_the_configured_names(pair1_dirs, pair1_spec):
    (framework,) = pair1_dirs
    assert (framework / f"{pair1_spec.feed_slug}_IIG.xlsx").is_file()
    assert (framework / f"{pair1_spec.feed_slug}_IIG_REVIEW.xlsx").is_file()
    assert (framework / "config_rows.xlsx").is_file()            # unchanged, still written


def test_clean_copy_matches_the_iig_v2_template_exactly(pair1_dirs, pair11_dirs, pair1_config):
    template = pair1_config.metadata.templates["iig_v2"]
    for framework in [*pair1_dirs, *pair11_dirs]:
        clean = load_workbook(_only(framework, "_IIG.xlsx"))
        assert clean.sheetnames == list(template.tabs)
        for name, tab in template.tabs.items():
            header = [c.value for c in clean[name][1]]
            assert header == tab.headers, name
        cells = [c for ws in clean for row in ws.iter_rows() for c in row]
        assert not any(c.comment for c in cells)
        assert not any(c.fill.fill_type for c in cells)


def test_pair1_clean_data_cells_equal_config_rows(pair1_dirs):
    (framework,) = pair1_dirs
    clean = load_workbook(_only(framework, "_IIG.xlsx"))
    rows = load_workbook(framework / "config_rows.xlsx")
    for name in clean.sheetnames:
        assert [list(r) for r in clean[name].iter_rows(values_only=True)] == \
               [list(r) for r in rows[name].iter_rows(values_only=True)], name


def test_review_summary_comes_first_and_counts_match_the_inventory(pair1_dirs, pair11_dirs):
    review = load_workbook(_only(pair1_dirs[0], "_IIG_REVIEW.xlsx"))
    assert review.sheetnames[0] == "REVIEW_SUMMARY"
    assert [c.value for c in review["REVIEW_SUMMARY"][1]] == [
        "Sheet", "Column", "Reason", "Owner", "Cells", "Example cell", "Example citation"]
    assert _owner_totals(pair1_dirs)[0] == INVENTORY["pair1"]
    assert _owner_totals(pair11_dirs)[0] == INVENTORY["pair11"]


def test_every_open_cell_is_highlighted_and_commented(pair1_dirs):
    (framework,) = pair1_dirs
    review = load_workbook(_only(framework, "_IIG_REVIEW.xlsx"))
    commented = [c for ws in review.worksheets[1:] for row in ws.iter_rows() for c in row
                 if c.comment]
    assert len(commented) == sum(INVENTORY["pair1"].values())
    for cell in commented:
        text = cell.comment.text
        assert text.startswith("Reason: ") and "\nCitation: " in text and "\nOwner: " in text
        assert cell.fill.fill_type == "solid"
    # a cell an input states is neither commented nor filled
    first_data = review.worksheets[1]
    stated = [c for row in first_data.iter_rows(min_row=2) for c in row
              if c.value not in (None, "") and not c.comment]
    assert stated and not any(c.fill.fill_type for c in stated)


def test_owner_reassignment_is_a_config_change(pair1_config, pair1_spec, tmp_path):
    moved = "DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_START_DATE"
    owners = {**pair1_config.iig_review.owners, moved: "engineer"}
    config = pair1_config.model_copy(update={
        "iig_review": pair1_config.iig_review.model_copy(update={"owners": owners})})
    totals, _ = _owner_totals(_run([pair1_spec], config, tmp_path))
    assert totals["BSA"] == INVENTORY["pair1"]["BSA"] - 4          # 4 pipeline rows
    assert totals["Engineer"] == INVENTORY["pair1"]["Engineer"] + 4


def test_the_owner_table_is_validated():
    with pytest.raises(ValueError, match="must be <SHEET>.<COLUMN>"):
        IigReviewConfig(owners={"NO_DOT": "bsa"})
    with pytest.raises(ValueError):
        IigReviewConfig(owners={"S.C": "nobody"})
    assert IigReviewConfig(owners={"*.C": "bsa"}).owner_for("ANY", "C", "template_constant") \
        == "bsa"


def test_addition_lists_both_workbooks_and_both_switches(pair1_dirs, pair1_spec):
    (framework,) = pair1_dirs
    addition = (framework / "ADDITION.md").read_text(encoding="utf-8")
    assert f"| `{pair1_spec.feed_slug}_IIG_REVIEW.xlsx` | The BSA's review copy" in addition
    assert f"| `{pair1_spec.feed_slug}_IIG.xlsx` | The clean copy of the IIG" in addition
    assert "## Switches" in addition
    assert "`conventions.profiles.acfc_prx.emit_iig_review`: on" in addition
    assert ("`conventions.profiles.acfc_prx.emit_dml` (with `dml.enabled`): off — DML not "
            "generated (disabled)") in addition


def test_the_reference_profile_writes_no_iig_workbooks(pair1_config, pair1_spec, tmp_path):
    """edo_sfmc ships emit_iig_review: false — its framework output is as before M3."""
    assert pair1_config.conventions.profiles["edo_sfmc"].emit_iig_review is False
    assert pair1_config.conventions.profiles["acfc_prx"].emit_iig_review is True
    cli._generate_feed(pair1_spec, _scoped(pair1_config, tmp_path), dry_run=True,
                       skip_tests=True, output_mode="framework", conventions_profile="edo_sfmc",
                       iig_template="iig_v1")
    framework = tmp_path / "out" / pair1_spec.feed_slug / "framework"
    assert not [p for p in framework.iterdir() if p.name.endswith(("_IIG.xlsx",
                                                                    "_IIG_REVIEW.xlsx"))]
    assert "## Switches" not in (framework / "ADDITION.md").read_text(encoding="utf-8")
