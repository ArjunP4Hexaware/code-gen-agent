"""post158 (pentest CS-1): a DataType cell cannot add SQL to the framework DDL.

Under ``typed_stage`` the DDL writes each data type as the STTM states it. A
stated type that is no plain type spelling (``gate.ddl_type_pattern``) is never
written - the column gets ``TYPE_NOT_WRITTEN`` - and the ``ddl_types`` check
FAILs, so the feed is quarantined. Pair 4 (synthetic). A standard / audit type
with no SQL mapping already stops the run loudly (``sql_type``, the notebook
pipeline every framework run also renders) before any DDL is written.
"""

from __future__ import annotations

import pytest

from codegen import cli
from codegen.emit.context import TemplateGapError
from codegen.gate.ddl_names import TYPE_NOT_WRITTEN
from test_m4_acceptance import _scoped

PAYLOAD = ("String COMMENT 'x'); DROP TABLE PWN_DTYPE; "
           "CREATE TABLE IF NOT EXISTS pwn.pwn_t (a INT")
MARKER = "PWN_DTYPE"


def _with_types(spec, *, stage=None, standard=None, audit=None):
    """``spec`` with the stage / standard type of the first business field that
    has a Standard column, and the type of every audit column, replaced."""
    update = {}
    if stage is not None:
        update["stage_datatype"] = stage
    if standard is not None:
        update["standard_datatype"] = standard
    done = False
    segments = []
    for segment in spec.segments:
        fields = []
        for f in segment.fields:
            if not done and update and f.standard_column is not None:
                f, done = f.model_copy(update=update), True
            fields.append(f)
        audits = segment.audit_columns
        if audit is not None and audits:
            audits = [a.model_copy(update={"datatype": audit}) for a in audits]
        segments.append(segment.model_copy(update={"fields": fields, "audit_columns": audits}))
    changes = {"segments": segments}
    if audit is not None:
        changes["audit_columns"] = [a.model_copy(update={"datatype": audit})
                                    for a in spec.audit_columns]
    return spec.model_copy(update=changes)


def _run(spec, config, tmp):
    gate = cli._generate_feed(spec, _scoped(config, tmp), dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2")
    return gate, _ddl_texts(tmp)


def _ddl_texts(tmp):
    """Every DDL text the run wrote (quarantine included): the SQL the engineer runs."""
    return [p.read_text(encoding="utf-8", errors="replace")
            for p in (tmp / "out").rglob("*_DDL*.txt") if p.is_file()]


def _check(gate, name):
    (check,) = [c for c in gate.checks if c.name == name]
    return check


def test_a_payload_stage_type_never_reaches_the_ddl_and_fails_the_gate(
        pair4_config, pair4_spec, tmp_path):
    spec = _with_types(pair4_spec, stage=PAYLOAD)
    gate, texts = _run(spec, pair4_config, tmp_path)
    assert gate.verdict == "FAIL"
    check = _check(gate, "ddl_types")
    assert not check.passed and MARKER not in check.details
    assert texts, "the feed wrote no DDL text"
    assert not any(MARKER in t for t in texts)
    assert any(TYPE_NOT_WRITTEN in t for t in texts)


@pytest.mark.parametrize("where", ["standard", "audit"])
def test_a_payload_standard_or_audit_type_stops_the_run_before_any_ddl(
        where, pair4_config, pair4_spec, tmp_path):
    spec = _with_types(pair4_spec, **{where: PAYLOAD})
    with pytest.raises(TemplateGapError):
        _run(spec, pair4_config, tmp_path)
    assert not any(MARKER in t for t in _ddl_texts(tmp_path))


def test_plain_type_spellings_are_written_as_stated(pair4_config, pair4_spec, tmp_path):
    spec = _with_types(pair4_spec, stage="varchar(50)", standard="Decimal(10, 2)")
    gate, texts = _run(spec, pair4_config, tmp_path)
    assert _check(gate, "ddl_types").passed
    ddl = "\n".join(t for t in texts)
    assert "varchar(50)" in ddl
    assert TYPE_NOT_WRITTEN not in ddl


def test_the_unchanged_pair_passes_the_type_check(pair4_config, pair4_spec, tmp_path):
    gate, _texts = _run(pair4_spec, pair4_config, tmp_path)
    assert _check(gate, "ddl_types").passed
    assert gate.verdict != "FAIL"
