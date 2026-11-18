"""post200: FRD labels match their synonyms with spaces ignored (``frd_docx.label_key``
through ``LabelTable`` / ``LabelSet``) - "LoadType:" is "Load Type:" without a config
line per spelling (the post195 class, FRD side; post198 did the STTM / VDD headers).
Only label -> synonym lookups use the key; values keep ``normalize_label``. Synthetic
documents only."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.extract.frd_docx import (
    LabelSet,
    LabelTable,
    label_key,
    line_field_labels,
    normalize_label,
)
from test_frd_requirement_blocks_post196 import FILES, _frd, _run

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def test_label_key_drops_spaces_only():
    assert label_key("LoadType:") == label_key("Load Type") == "loadtype"
    assert normalize_label("LoadType:") == "loadtype"     # normalize_label is unchanged
    assert normalize_label("Load  Type :") == "load type"


def test_label_table_exact_first_then_space_free_and_never_a_pick():
    table = LabelTable([("file name", "file"), ("filename", "other"), ("load type", "lt"),
                        ("a b", "x"), ("ab ", "y")])
    assert table.get("file name") == "file"              # exact spelling wins
    assert table.get("filename") == "other"
    assert table.get("loadtype") == "lt" and "loadtype" in table and table["loadtype"] == "lt"
    assert table.get("fi lename") is None                # two keys share "filename"
    assert "zzz" not in table and table.get("zzz", "d") == "d"
    with pytest.raises(KeyError):
        table["zzz"]
    assert sorted(table) == ["a b", "ab ", "file name", "filename", "load type"]


def test_label_set_matches_space_free_and_keeps_it_through_union():
    labels = LabelSet(["Load Type", "File Name"])
    assert "loadtype" in labels and "load type" in labels and "load" not in labels
    assert "filename" in (LabelSet(["Feed Name"]) | labels)


def _cell(file: str) -> str:
    return (f"<{file}> will be received by the vendor team.\nLoadType:\nSTG:-\n"
            "Incremental:- Truncate & load\n\nSTD:-\nIncremental:- Upsert using keys LOB\n")


def test_a_one_word_frd_label_is_read_without_its_own_synonym(tmp_path, config):
    """Failed before post200: "LoadType:" matched no ``load_type_block_labels``
    spelling, so both load strategies stayed open."""
    assert "loadtype" not in {normalize_label(s)
                              for s in config.extractor.frd.load_type_block_labels}
    doc, contract = _run(_frd(tmp_path, [_cell(f) for f in FILES]), config, tmp_path)
    unresolved = {u.field for u in doc.profile.unresolved}
    for layer in ("stage", "standard"):
        assert f"feeds[0].{layer}_target.load_strategy" not in unresolved
    feed = contract.feeds[0]
    assert feed.stage_target.load_strategy and feed.standard_target.load_strategy


def _clashes(tables: dict[str, dict[str, list[str]]]) -> list[tuple]:
    """(table, spelling, key a, key b) wherever two keys' spellings share a space-free
    key (LabelTable then matches neither - a regression, not a pick)."""
    out = []
    for name, table in tables.items():
        owner: dict[str, str] = {}
        for key, spellings in table.items():
            for spelling in spellings:
                if owner.setdefault(label_key(spelling), key) != key:
                    out.append((name, spelling, owner[label_key(spelling)], key))
    return out


def test_no_two_keys_share_a_label_key_in_the_shipped_config(config):
    frd = config.extractor.frd
    tables = {"labels": frd.labels, "fixed_rows": frd.fixed_rows,
              "section_titles": frd.section_titles,
              "target_schema_markers": frd.target_schema_markers,
              "layer_block_labels": frd.layer_block_labels,
              "object_name_labels": frd.object_name_labels,
              "line_field_labels": line_field_labels(frd),
              # _row_label reads labels, then fixed_rows: one key space between them
              "labels+fixed_rows": {**{f"l:{k}": v for k, v in frd.labels.items()},
                                    **{f"f:{k}": v for k, v in frd.fixed_rows.items()}}}
    assert _clashes(tables) == []
