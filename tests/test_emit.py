"""Emitter: byte-stable renders and loud template-gap failures."""

from __future__ import annotations

import pytest

from codegen.emit.context import TemplateGapError, build_context
from codegen.emit.emitter import emit_feed


def _context(spec, config):
    return build_context(
        spec,
        config,
        allow_duplicate_file_name=True,
        duplicate_rule_text=None,
        notification_rule_texts=[],
    )


def test_render_twice_is_byte_identical(specs_by_id, config, tmp_path):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    context = _context(spec, config)
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = emit_feed(context, first_root)
    second = emit_feed(context, second_root)
    assert [p.relative_to(first_root) for p in first] == [
        p.relative_to(second_root) for p in second
    ]
    for path_a, path_b in zip(first, second, strict=True):
        assert path_a.read_bytes() == path_b.read_bytes(), path_a.name


def test_unknown_audit_column_is_a_template_gap(specs_by_id, config, tmp_path):
    spec = specs_by_id["sd_community_risk"]
    context = _context(spec, config)
    context["audit_columns"] = [*context["audit_columns"], ("MYSTERY_COL", "STRING")]
    with pytest.raises(TemplateGapError, match="MYSTERY_COL"):
        emit_feed(context, tmp_path)


def test_flat_feed_emits_no_segments_module(specs_by_id, config, tmp_path):
    spec = specs_by_id["sd_community_risk"]
    written = emit_feed(_context(spec, config), tmp_path)
    names = {p.name for p in written}
    assert "segments.py" not in names
    assert "recycle.py" not in names  # community feed has no STTM recycle spec


def test_caqh_emits_segments_and_recycle(specs_by_id, config, tmp_path):
    spec = specs_by_id["caqh_tpl_inbound_files"]
    written = emit_feed(_context(spec, config), tmp_path)
    names = {p.name for p in written}
    assert {"segments.py", "recycle.py", "reference.py"} <= names
    assert "test_segments.py" in names and "test_recycle.py" in names
    # Stage-only feed: no standard DDL.
    assert not any(p.name.endswith(".standard.sql") for p in written)
