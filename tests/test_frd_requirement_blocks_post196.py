"""post196: a staging FRD (2026-11-17) of a new shape - two F1 section tables (Data
Quality, Vendor Metadata) next to Solution Requirement tables whose Functional
Requirement cell opens with "<file name.csv>" and states the load strategy as a block:

    Load Type:
    STG:-
    Incremental:- Truncate & load
    STD:-
    Incremental:- Upsert using keys ...

The reader took the F1 family and never read the requirements: load strategy, file
names and (from them) the file format were all asked. Synthetic documents only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from acfc_shapes.cold_pairs import _sr, _tbl
from acfc_shapes.common import docx_bytes
from codegen.config import load_config
from codegen.extract.frd_docx import canonical_strategy, load_type_block, read_frd
from codegen.layout.resolve import resolve_frd

REPO = Path(__file__).resolve().parents[1]
MARKERS = {"stg": "stage", "stage": "stage", "std": "standard", "standard": "standard"}


def _cell(file: str, stage: str = "Incremental:- Truncate & load",
          standard: str = "Incremental:- Upsert using keys LOB, MEMBER_ID") -> str:
    return (f"<{file}> will be received by the vendor team and placed at the shared "
            "location.\nLanding Location:\nsyn/inbound/feed\nLoad Type:\nSTG:-\n"
            f"{stage}\n\nSTD:-\n{standard}\nArchive Location: (raw layer)\nsyn/archive\n"
            "Below is the csv layout the vendor will share.")


def _frd(tmp_path, cells: list[str]) -> Path:
    parts = [_tbl([["Data Quality: SYN1", ""], ["Name", "Data Quality rules"],
                   ["Description", "Rules for the files"],
                   ["Functional Requirement", "The DQ team defines the rules."]]),
             _tbl([["Vendor Metadata: SYN2", ""], ["Name", "Vendor Metadata"],
                   ["Description", ""], ["Functional Requirement", ""]])]
    for n, cell in enumerate(cells, start=1):
        parts.append(_sr(n, [("Name", f"Ingest file {n} into the lake"),
                             ("Description", f"Ingest file {n}."),
                             ("Functional Requirement", cell),
                             ("Impact Details", "Reporting is impacted."),
                             ("Solution Acceptance Criteria", "All files are loaded."),
                             ("IS Owner", "Data Engineering")]))
    path = tmp_path / "FRD.docx"
    path.write_bytes(docx_bytes(parts))
    return path


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _run(path, config, tmp_path):
    doc, content = resolve_frd(path, config, use_cache=False,
                               runtime_cache_dir=tmp_path / "rt")
    contract = read_frd(content, doc.profile, config, document_name="FRD.docx",
                        generated_date="2026-11-17")
    contract = contract[0] if isinstance(contract, tuple) else contract
    return doc, contract


FILES = ["SYN_VENDOR_Enrollment_MMDDYYYY_HHMMSS.csv", "SYN_VENDOR_Hedis_MMDDYYYY_HHMMSS.csv"]


def test_requirement_load_type_blocks_and_file_names_are_read(tmp_path, config):
    doc, contract = _run(_frd(tmp_path, [_cell(f) for f in FILES]), config, tmp_path)
    assert doc.profile.family == "F1"            # the section tables still decide
    unresolved = {u.field for u in doc.profile.unresolved}
    for layer in ("stage", "standard"):
        path = f"feeds[0].{layer}_target.load_strategy"
        assert path not in unresolved
        source = doc.profile.fields[path]
        assert (source.label, source.inline_label, source.block_layer) == (
            "Functional Requirement", "Load Type", layer)
    (feed,) = contract.feeds
    assert feed.stage_target.load_strategy == "Truncate and Load"
    assert feed.standard_target.load_strategy == "Upsert"
    assert feed.file_name_patterns == FILES
    flags = contract.extraction_flags
    assert any(f.startswith("frd_requirement_file_names:feeds[0]") for f in flags), flags
    std = [f for f in flags if f.startswith(
        "frd_load_type_block:feeds[0].standard_target.load_strategy")]
    assert std and "the rest ('using keys LOB, MEMBER_ID') is not read" in std[0], flags


def test_requirements_that_disagree_place_no_strategy(tmp_path, config):
    cells = [_cell(FILES[0]), _cell(FILES[1], stage="Incremental:- Append")]
    doc, contract = _run(_frd(tmp_path, cells), config, tmp_path)
    assert "feeds[0].stage_target.load_strategy" not in doc.profile.fields
    assert "feeds[0].stage_target.load_strategy" in {u.field for u in doc.profile.unresolved}
    assert any("feeds[0].stage_target.load_strategy: 2 Load Type block(s)" in n
               for n in doc.profile.notes), doc.profile.notes
    # the layer they agree on is still placed
    assert contract.feeds[0].standard_target.load_strategy == "Upsert"


def test_a_layer_with_two_strategy_lines_is_never_picked(tmp_path, config):
    two = "Incremental:- Truncate & load\nFull:- Append"
    doc, _contract = _run(_frd(tmp_path, [_cell(FILES[0], stage=two)]), config, tmp_path)
    assert "feeds[0].stage_target.load_strategy" not in doc.profile.fields


def test_the_block_parser():
    text = _cell(FILES[0])
    block = load_type_block(text, {"load type"}, MARKERS)
    assert block == {"stage": ("Truncate & load", ""),
                     "standard": ("Upsert using keys LOB, MEMBER_ID",
                                  "Archive Location: (raw layer)")}
    assert load_type_block("Load Type: Full\nSTG:-\nAppend", {"load type"}, MARKERS) is None
    assert load_type_block("no block here", {"load type"}, MARKERS) is None


def test_a_leading_strategy_is_read_only_when_asked_for(config):
    synonyms = config.extractor.frd.load_strategy_synonyms
    assert canonical_strategy("Upsert using keys A, B", synonyms) == (None, "")
    assert canonical_strategy("Upsert using keys A, B", synonyms, leading=True) == (
        "Upsert", "using keys A, B")
    assert canonical_strategy("Truncate & load", synonyms) == ("Truncate and Load", "")
    assert canonical_strategy("Upserting rows", synonyms, leading=True) == (None, "")
