"""Audit #13 (2026-10-26, post131): the edo_sfmc DDL writes only the COMMENTs a
document states.

The two-file DDL wrote a COMMENT on every column: a column with no description
got its own name title-cased ("LOB" -> 'Lob', "SRC_FILE_NAME" -> 'Src File
Name'), and the text came from ``description`` - which may be an STTM Comments
cell (rule text) - not ``ddl_description``. Both break "a value not transcribed
from an input is a bug". Now: the STTM description (``ddl_description``; audit
columns from their own rows, as acfc_prx), else no COMMENT + one
``ddl_comment_blank`` flag per table - the acfc_prx rule.
"""

from __future__ import annotations

import re

from codegen import cli
from test_m4_acceptance import _scoped


def _render(config, spec, tmp_path):
    gate = cli._generate_feed(spec, _scoped(config, tmp_path), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="edo_sfmc",
                              iig_template="iig_v2")
    framework = tmp_path / "out" / spec.feed_slug / "framework"
    return gate, {p.name: p.read_text(encoding="utf-8")
                  for p in framework.glob("*_table_creation.txt")}


def _comments(text: str) -> dict[str, str]:
    return dict(re.findall(r"^\s+(\w+) \S.*? COMMENT '((?:[^'\\]|\\.)*)'[,)]", text, flags=re.M))


def test_no_comment_is_invented_from_a_column_name(pair4_config, pair4_spec, tmp_path):
    spec = pair4_spec
    gate, files = _render(pair4_config, spec, tmp_path)
    assert files
    stated = {f.stage_column: f.ddl_description for s in spec.segments for f in s.fields}
    stated.update({f.standard_column: f.ddl_description for s in spec.segments
                   for f in s.fields if f.standard_column})
    for a in [*spec.audit_columns, *(a for s in spec.segments for a in (s.audit_columns or []))]:
        stated.setdefault(a.column, a.description)
    for name, text in files.items():
        for column, comment in _comments(text).items():
            assert comment != column.replace("_", " ").title() or stated.get(column), (name, column)
            assert stated.get(column), (name, column, comment)   # every COMMENT is stated
    blank = [c for c, d in stated.items() if not d]
    if blank:
        assert any(f.startswith("ddl_comment_blank:") for f in gate.flags)


def test_a_comments_cell_never_becomes_a_column_comment(pair4_config, pair4_spec, tmp_path):
    rule = "Syn rule text: reject when blank"
    segments = [s.model_copy(update={"fields": [
        f.model_copy(update={"description": rule, "description_from_comments": True})
        if i == 1 else f for i, f in enumerate(s.fields)]}) for s in pair4_spec.segments]
    _gate, files = _render(pair4_config, pair4_spec.model_copy(update={"segments": segments}),
                           tmp_path)
    assert files and not any("Syn rule text" in text for text in files.values())
