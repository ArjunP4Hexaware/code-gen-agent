"""post197: the merge columns a Solution Requirement's Load Type line names ("STD:-" /
"Incremental:- Upsert using keys LOB, MEMBER_ID") are the requirement's key statement:
one set for every requirement -> the feed's; sets that differ -> per-file blocks, each
derived feed taking the keys of the requirement whose file is its own. A key may name
the table's audit columns (the STTM's audit rows; the DDL creates them). Synthetic only.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from codegen import primary_key
from codegen.config import load_config
from codegen.extract.frd_docx import read_frd
from codegen.layout.resolve import resolve_frd, resolve_structured_fields
from test_frd_requirement_blocks_post196 import FILES, _cell, _frd

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _contract(path, config, tmp_path):
    doc, content = resolve_frd(path, config, use_cache=False,
                               runtime_cache_dir=tmp_path / "rt")
    contract = read_frd(content, doc.profile, config, document_name="FRD.docx",
                        generated_date="2026-11-17")
    return contract[0] if isinstance(contract, tuple) else contract


def test_one_key_set_for_every_requirement_is_the_feeds(tmp_path, config):
    contract = _contract(_frd(tmp_path, [_cell(f) for f in FILES]), config, tmp_path)
    assert contract.feeds[0].key_statement == "LOB, MEMBER_ID"
    assert any(f.startswith("frd_load_type_keys:feeds[0].key_statement — 2 Solution")
               for f in contract.extraction_flags), contract.extraction_flags


def test_differing_key_sets_go_to_each_feed_by_its_file(tmp_path, config):
    cells = [_cell(FILES[0], standard="Incremental:- Upsert using keys LOB, MEMBER_ID"),
             _cell(FILES[1], standard="Incremental:- Upsert using keys LOB, CLAIM_ID")]
    contract = _contract(_frd(tmp_path, cells), config, tmp_path)
    assert contract.feeds[0].key_statement is None
    blocks = contract.structured["feeds[0].key_statement"]
    assert blocks.kind == "per_file_blocks"
    assert [(r.key, r.values["key"]) for r in blocks.rows] == [
        (FILES[0], "LOB, MEMBER_ID"), (FILES[1], "LOB, CLAIM_ID")]
    # the split step gives each derived feed one file; the keys follow the file
    base = contract.feeds[0]
    split = contract.model_copy(update={"feeds": [
        base.model_copy(update={"feed_name": "hedis", "file_name_patterns": [FILES[1]]}),
        base.model_copy(update={"feed_name": "enrollment", "file_name_patterns": [FILES[0]]}),
        base.model_copy(update={"feed_name": "other", "file_name_patterns": []})]})
    resolved, flags = resolve_structured_fields(split, config)
    assert [f.key_statement for f in resolved.feeds] == ["LOB, CLAIM_ID", "LOB, MEMBER_ID",
                                                         None]
    assert any(f.startswith("frd_per_file_blocks:feeds[2].key_statement — no row")
               for f in flags), flags


def _field(name):
    return SimpleNamespace(source_column=name, stage_column=name.upper(),
                           standard_column=name.upper())


def test_a_key_may_name_the_tables_audit_columns():
    table = primary_key.TableKey("t", "stage", [_field("member_id")], True, ("lob", "vendor_name"))
    assert primary_key._match(["LOB", "member_id", "Vendor_Name"], table) == (
        "lob", "MEMBER_ID", "vendor_name")
    # every name must still be a column of the table
    assert primary_key._match(["LOB", "claim_id"], table) == ()
    assert primary_key._match(["LOB"], primary_key.TableKey("t", "stage",
                                                            [_field("member_id")])) == ()
