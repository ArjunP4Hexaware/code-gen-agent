"""post84 (D1 pair_11): the Pyx FRD's metadata "ADLS Location" cell lists two
paths on two lines (refused as multiline: every feed's landing unstated), while
each Solution Requirement states its own file's landing — "Raw ADLS Location :
<path>", the path on the same line or the next. The reader gives those per-file
blocks keyed by the requirement (its Name + the identifiers only it names), and
the layout stage's per-feed matcher gives each derived feed its own — a
descriptive Name ("Full member roster …") is matched through the identifier its
text names; anything unmatched stays unstated. Synthetic text only."""

from __future__ import annotations

from types import SimpleNamespace

from codegen.config import load_config
from codegen.extract.frd_docx import (
    DocxContent,
    _labelled_path,
    _requirement_landing_blocks,
    requirement_landings,
)
from codegen.layout.resolve import _match_rows_to_feeds
from test_iig_corpus_cells import REPO

CONFIG = load_config(REPO / "config" / "config.yaml").extractor.frd
LABELS = {"raw adls location", "adls location"}


def _sr(n: int, name: str, requirement: str) -> list[list[str]]:
    return [[f"Solution Requirement: {n}"], ["Name", name],
            ["Description", "Ingest the synthetic file into the lakehouse."],
            ["Functional Requirement", requirement],
            ["Impact Details", "none"], ["Solution Acceptance Criteria", "fields populated"],
            ["Priority", "High"], ["Traced/Related Requirements", "N/A"], ["IS Owner", ""],
            ["Notes", "see syn_mapping_doc"]]


def _content() -> DocxContent:
    return DocxContent(tables=[
        _sr(1, "Alpha report", "File: SYN_ALPHA_MMDDYYYY in syn_mapping_doc\n\n"
                               "Raw ADLS Location : \nsynland/inbound/syn_dom/sub_a/syn_vendor"),
        _sr(2, "Roster of every enrolled person",
            "Loads syn_vendor_weekly_roster from syn_mapping_doc\n\n"
            "Raw ADLS Location: synland/inbound/syn_dom/sub_b/syn_vendor"),
    ], paragraphs=[])


def test_the_label_line_and_the_next_line_both_state_the_path():
    assert _labelled_path("x\nRaw ADLS Location : a/b/c", LABELS) == "a/b/c"
    assert _labelled_path("Raw ADLS Location : \n\n a/b/c", LABELS) == "a/b/c"
    assert _labelled_path("Raw ADLS Location : to be decided", LABELS) is None   # not a path
    assert _labelled_path("SFG Location: a/b/c", LABELS) is None                  # other label


def test_each_requirement_is_keyed_by_its_name_and_its_own_identifiers():
    found = requirement_landings(_content(), CONFIG)
    assert [(path, table) for _key, path, table, _row in found] == [
        ("synland/inbound/syn_dom/sub_a/syn_vendor", 0),
        ("synland/inbound/syn_dom/sub_b/syn_vendor", 1)]
    keys = [key for key, *_ in found]
    assert keys[0].startswith("Alpha report ") and "syn_alpha_mmddyyyy" in keys[0]
    assert "syn_vendor_weekly_roster" in keys[1]
    assert not any("syn_mapping_doc" in key for key in keys)       # named by both: dropped


def test_a_descriptive_name_still_reaches_its_feed_through_its_identifier():
    keys = [key for key, *_ in requirement_landings(_content(), CONFIG)]
    def feed(table: str, pattern: str):
        return SimpleNamespace(file_name_patterns=[pattern],
                               stage_target=SimpleNamespace(tables=[table]))

    feeds = [feed("syn_vendor_weekly_roster", "Syn_Vendor_Weekly_Roster*"),
             feed("syn_vendor_alpha_report", "SYN_ALPHA_*")]
    assert _match_rows_to_feeds(keys, feeds) == {1: 0, 0: 1}


def test_only_an_unstated_landing_gets_the_blocks():
    found = _requirement_landing_blocks(
        _content(), CONFIG, {}, [SimpleNamespace(landing_location=None)], [])
    block = found["feeds[0].landing_location"]
    assert block.kind == "per_file_blocks" and len(block.rows) == 2
    assert block.rows[0].values == {"path": "synland/inbound/syn_dom/sub_a/syn_vendor"}
    stated = [SimpleNamespace(landing_location="synland/inbound/stated")]
    assert _requirement_landing_blocks(_content(), CONFIG, {}, stated, []) == {}
