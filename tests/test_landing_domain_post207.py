"""post207 (the tester's report 2026-11-19, items 1 and 3; synthetic text only):

1. Her FRDs' Solution Requirements state the landing as "Landing Location:" with the
   path on the next line, once per environment block ("Prod:" / "QA:") - that label is
   a requirement landing label now (config), and a cell's landing lines are read only
   when they all state the same path (spaces ignored); paths that differ read nothing.
2. Her FRD states the domain in a cell of a label-less row: "Domain -<x>" /
   "Subdomain-<y>" (a hyphen, no colon). The domain-label grammar takes a hyphen /
   en dash, and a single-feed FRD with no domain row is placed at the ONE cell stating
   both labels (any column); cells that disagree place nothing."""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes import family_e_multi as fm
from codegen.config import load_config
from codegen.extract.frd_docx import (
    DocxContent,
    LabelSet,
    _labelled_path,
    read_frd,
    requirement_landings,
    split_domain_labels,
)
from codegen.layout.resolve import resolve_frd

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")
FRD = CONFIG.extractor.frd
LABELS = LabelSet(FRD.requirement_landing_labels)

ENV_BLOCKS = ("Prod:\nContainer Name: syn-pr-raw\nLanding Location:\n{prod}\n"
              "QA:\nContainer Name: syn-q1-raw\nLanding Location:\n{qa}\n"
              "Archive Location: (Raw Layer - ADLS Gen 2 container)\n{prod}/Archive")


# ------------------------------------------------------------------ landing


def test_landing_location_is_a_requirement_landing_label():
    assert "Landing Location" in FRD.requirement_landing_labels
    assert _labelled_path("Landing Location:\nsynland/inbound/syn_dom/syn_v", LABELS) == (
        "synland/inbound/syn_dom/syn_v")


def test_environment_blocks_stating_one_path_read_it_spaces_ignored():
    cell = ENV_BLOCKS.format(prod="synland/inbound/syn_dom/syn_v",
                             qa="synland/inbound/syn_dom/ syn_v")
    assert _labelled_path(cell, LABELS) == "synland/inbound/syn_dom/syn_v"   # the first


def test_environment_blocks_stating_different_paths_read_nothing():
    cell = ENV_BLOCKS.format(prod="synland/inbound/syn_dom/syn_v",
                             qa="synland/inbound/syn_qa/syn_v")
    assert _labelled_path(cell, LABELS) is None                             # never a pick


def _sr(name: str, requirement: str) -> list[list[str]]:
    return [["Solution Requirement: 1"], ["Name", name],
            ["Description", "Ingest the synthetic file into the lakehouse."],
            ["Functional Requirement", requirement],
            ["Impact Details", "none"], ["Solution Acceptance Criteria", "fields populated"],
            ["Priority", "High"], ["Traced/Related Requirements", "N/A"], ["IS Owner", ""]]


def test_a_requirement_with_environment_blocks_states_its_landing():
    cell = "<SYN_FILE.txt> is loaded.\n" + ENV_BLOCKS.format(
        prod="synland/inbound/syn_dom/syn_v", qa="synland/inbound/syn_dom/syn_v")
    found = requirement_landings(DocxContent(tables=[_sr("Syn file", cell)], paragraphs=[]),
                                 FRD)
    assert [(path, table, row) for _k, path, table, row in found] == [
        ("synland/inbound/syn_dom/syn_v", 0, 3)]


# ------------------------------------------------------------------ domain


@pytest.mark.parametrize("text", [
    "Domain -Care\nSubdomain-Programs",
    "Domain - Care\nSub-domain - Programs",
    "Domain – Care\nSub Domain – Programs",
])
def test_a_hyphen_separates_the_domain_labels(text):
    assert split_domain_labels(text) == ("Care", "Programs")


def test_a_hyphen_inside_a_value_is_kept():
    assert split_domain_labels("Domain: Care-Management\nSub Domain: Programs") == (
        "Care-Management", "Programs")


def _frd(tmp_path, *extra_rows) -> Path:
    path = tmp_path / "FRD.docx"
    path.write_bytes(fm.build_frd(domain_cell=None, extra_tables=tuple(
        [["", "", ""], *rows] for rows in extra_rows)))
    return path


def _resolve(path, tmp_path):
    return resolve_frd(path, CONFIG, use_cache=False, runtime_cache_dir=tmp_path / "rt")


def test_a_domain_cell_in_a_label_less_row_is_placed_and_split(tmp_path):
    doc, content = _resolve(_frd(tmp_path, [["Domain -Care\nSubdomain-Programs",
                                             "Stage-stg_x\nStandard-x", ""]]), tmp_path)
    assert "feeds[0].domain" not in {u.field for u in doc.profile.unresolved}
    source = doc.profile.fields["feeds[0].domain"]
    assert (source.col, source.value_col, source.label) == (0, 0, "Domain")
    contract = read_frd(content, doc.profile, CONFIG, document_name="FRD.docx",
                        generated_date="2026-11-19")
    contract = contract[0] if isinstance(contract, tuple) else contract
    feed = contract.feeds[0]
    assert (feed.domain, feed.sub_domain) == ("Care", "Programs")
    assert any(f.startswith("frd_domain_labels_split:feeds[0]")
               for f in contract.extraction_flags), contract.extraction_flags


def test_cells_that_disagree_place_no_domain(tmp_path):
    doc, _content = _resolve(_frd(tmp_path, [["Domain -Care\nSubdomain-Programs", "", ""]],
                                  [["Domain: Member\nSub Domain: Claims", "", ""]]), tmp_path)
    assert "feeds[0].domain" not in doc.profile.fields
    assert any("cells state the domain labels differently" in n for n in doc.profile.notes)


def test_a_domain_row_of_its_own_is_left_as_it_was(tmp_path):
    path = tmp_path / "FRD.docx"
    path.write_bytes(fm.build_frd(extra_tables=(
        [["", "", ""], ["Domain -Care\nSubdomain-Programs", "", ""]],)))
    doc, _content = _resolve(path, tmp_path)
    assert doc.profile.fields["feeds[0].domain"].label == "Domain and Subdomain"
