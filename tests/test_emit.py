"""Emitter: byte-stable renders and loud template-gap failures."""

from __future__ import annotations

from codegen.emit.context import build_context
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


def test_an_unknown_audit_column_is_a_typed_null_never_a_stop(specs_by_id, config, tmp_path):
    """M11 item 13 (replaces test_unknown_audit_column_is_a_template_gap): an
    audit column no rule populates is written as a typed NULL, flagged by the
    gate (audit_column_unpopulated) — it used to stop the run."""
    spec = specs_by_id["sd_community_risk"]
    context = _context(spec, config)
    context["audit_columns"] = [*context["audit_columns"], ("MYSTERY_COL", "STRING")]
    context["unpopulated_audit"] = [("MYSTERY_COL", "STRING")]
    written = emit_feed(context, tmp_path)
    audit = next(p for p in written if p.name == "audit.py").read_text(encoding="utf-8")
    assert '.withColumn("MYSTERY_COL", F.lit(None).cast("string"))' in audit
    assert "UNPOPULATED" in audit


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


def test_pyconst_is_tojson_for_short_values_and_wraps_long_free_text():
    """Short constants render exactly as before (baseline byte-identical);
    a free-text FRD value that would overflow the emitted ruff line length
    becomes a parenthesized implicit concatenation of the SAME text."""
    import ast
    import json

    from codegen.emit.emitter import _LINE_LENGTH, _py_const

    assert _py_const("sd_community_risk", "FEED_NAME") == 'FEED_NAME = "sd_community_risk"'
    assert _py_const("File Data Ingestion", "FILE_FORMAT") == \
        'FILE_FORMAT = ' + json.dumps("File Data Ingestion")
    long_text = ("Vendor Files = Community Demographic, Community Risk & \n"
                 "Individual Risk Reports and a further trailing clause")
    rendered = _py_const(long_text, "SOURCE_SYSTEM")
    assert rendered.startswith("SOURCE_SYSTEM = (\n    ") and rendered.endswith("\n)")
    assert all(len(line) <= _LINE_LENGTH for line in rendered.splitlines())
    module = ast.parse(rendered)
    assert ast.literal_eval(module.body[0].value) == long_text     # verbatim
