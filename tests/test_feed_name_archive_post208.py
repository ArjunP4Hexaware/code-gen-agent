"""post208 (the tester's report 2026-11-19; synthetic text only):

1. Her FRD has no Descriptive Metadata table: its first F1 section table is Data
   Quality, whose "Name" row ("Data Quality rules") became the FEED's name. Only the
   sections in ``extractor.frd.feed_name_sections`` (descriptive) may name the feed
   now; a Name row elsewhere names its section (a note), and the layout stage names
   the feed after the STTM stage band as for any unnamed feed.
2. Her Solution Requirements state "Archive Location: (<note>)" with the path on the
   next line. It is read like the landing (``requirement_archive_labels``) into
   ``FrdFeed.archive_location`` and compared with the IIG's SRC_ADLS_ARCHVL_PATH shape
   (option C, Soham): the cell keeps the shape; a differing stated path is a review note
   ``iig_archive_path_differs:``; the JSON carries the field only when stated."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from acfc_shapes import family_e_multi as fm
from acfc_shapes.cold_pairs import _f1
from acfc_shapes.common import docx_bytes
from codegen.config import load_config
from codegen.extract.frd_docx import DocxContent, LabelSet, _labelled_path, requirement_landings
from codegen.layout.resolve import resolve_frd
from codegen.metadata_template import _note_stated_archive

REPO = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPO / "config" / "config.yaml")
FRD = CONFIG.extractor.frd


# ------------------------------------------------------------------ feed name


def _resolve(tmp_path, data: bytes):
    path = tmp_path / "FRD.docx"
    path.write_bytes(data)
    return resolve_frd(path, CONFIG, use_cache=False, runtime_cache_dir=tmp_path / "rt")


def test_only_the_descriptive_section_names_the_feed():
    assert FRD.feed_name_sections == ["descriptive"]


def test_a_data_quality_or_vendor_name_row_never_names_the_feed(tmp_path):
    doc, _content = _resolve(tmp_path, docx_bytes([
        _f1("DQ", "Data Quality", [("DQ-1", "Name", "Data Quality rules"),
                                   ("DQ-2", "Description", "the checks"),
                                   ("DQ-3", "Record Recycle Process", "Not applicable")]),
        _f1("VM", "Vendor Metadata", [("VM-1", "Name", "Vendor Metadata"),
                                      ("VM-2", "Vendor Name", "Syn Vendor")]),
    ]))
    assert "feeds[0].feed_name#fallback" not in doc.profile.fields
    assert sum("names the section, not the feed" in n for n in doc.profile.notes) == 2
    assert doc.profile.fields["feeds[0].source_system#fallback"].label == "Vendor Name"


def test_the_descriptive_name_row_still_names_the_feed(tmp_path):
    doc, _content = _resolve(tmp_path, fm.build_frd())
    source = doc.profile.fields["feeds[0].feed_name#fallback"]
    assert (source.section, source.label) == ("descriptive", "Name")


# ------------------------------------------------------------------ archive


ARCHIVE = LabelSet(FRD.requirement_archive_labels)


def test_a_bracketed_note_after_the_label_is_no_value():
    cell = "Archive Location: (Raw Layer - ADLS Gen 2 container)\nsynland/inbound/syn_v/Archive"
    assert _labelled_path(cell, ARCHIVE) == "synland/inbound/syn_v/Archive"


def test_a_stray_space_is_accepted_only_where_the_path_is_compared():
    cell = "Archive Location:\nsynland/inbound/syn_v/ Archive"
    assert _labelled_path(cell, ARCHIVE) is None                          # never written so
    assert _labelled_path(cell, ARCHIVE, spaced_ok=True) == "synland/inbound/syn_v/ Archive"


def _sr(name: str, requirement: str) -> list[list[str]]:
    return [["Solution Requirement: 1"], ["Name", name],
            ["Description", "Ingest the synthetic file into the lakehouse."],
            ["Functional Requirement", requirement],
            ["Impact Details", "none"], ["Solution Acceptance Criteria", "fields populated"],
            ["Priority", "High"], ["Traced/Related Requirements", "N/A"], ["IS Owner", ""]]


def test_a_requirement_states_its_archive_path():
    cell = ("Landing Location:\nsynland/inbound/syn_v\n"
            "Archive Location: (Raw Layer - ADLS Gen 2 container)\nsynland/inbound/syn_v/ Archive")
    content = DocxContent(tables=[_sr("Syn file", cell)], paragraphs=[])
    found = requirement_landings(content, FRD, FRD.requirement_archive_labels, spaced_ok=True)
    assert [path for _k, path, _t, _r in found] == ["synland/inbound/syn_v/ Archive"]
    landing = requirement_landings(content, FRD)
    assert [path for _k, path, _t, _r in landing] == ["synland/inbound/syn_v"]   # unchanged


def _cells(value: str) -> dict:
    return {"SRC_ADLS_ARCHVL_PATH": {"value": value, "badge_entry": {"badge": "synthetic"}}}


TPL = SimpleNamespace(path_patterns={"STGDELTA_STDDELTA_INGESTION_DET": {
    "SRC_ADLS_ARCHVL_PATH": "/Archive{landing}"}})
TAB = "STGDELTA_STDDELTA_INGESTION_DET"


def test_an_agreeing_stated_archive_leaves_the_cell_as_it_was():
    for stated in ("/inbound/syn_v/Archive/", "synland/inbound/syn_v/ archive",
                   "synland\\inbound\\syn_v\\Archive"):
        cells = _cells("/inbound/syn_v/Archive/")
        _note_stated_archive(TPL, TAB, SimpleNamespace(archive_location=stated), cells)
        assert "note" not in cells["SRC_ADLS_ARCHVL_PATH"]["badge_entry"], stated


def test_a_differing_stated_archive_is_a_review_note_the_cell_kept():
    cells = _cells("/Archive/inbound/syn_v/")
    stated = SimpleNamespace(archive_location="synland/inbound/syn_v/Archive")
    _note_stated_archive(TPL, TAB, stated, cells)
    cell = cells["SRC_ADLS_ARCHVL_PATH"]
    assert cell["value"] == "/Archive/inbound/syn_v/"                    # the shape kept
    assert cell["badge_entry"]["note"].startswith(
        "iig_archive_path_differs:STGDELTA_STDDELTA_INGESTION_DET.SRC_ADLS_ARCHVL_PATH — ")
    assert "'/Archive{landing}'" in cell["badge_entry"]["note"]


def test_no_stated_archive_no_note():
    cells = _cells("/Archive/inbound/syn_v/")
    _note_stated_archive(TPL, TAB, SimpleNamespace(archive_location=None), cells)
    assert "note" not in cells["SRC_ADLS_ARCHVL_PATH"]["badge_entry"]


def test_the_contract_carries_the_archive_only_when_stated(tmp_path):
    doc, content = _resolve(tmp_path, fm.build_frd())
    from codegen.extract.frd_docx import read_frd

    contract = read_frd(content, doc.profile, CONFIG, document_name="FRD.docx",
                        generated_date="2026-11-19")
    contract = contract[0] if isinstance(contract, tuple) else contract
    dumped = contract.model_dump(mode="json", by_alias=True, exclude_defaults=True)
    assert "archive_location" not in dumped["feeds"][0]
    stated = contract.feeds[0].model_copy(update={"archive_location": "a/b/Archive"})
    assert stated.model_dump(exclude_defaults=True)["archive_location"] == "a/b/Archive"
