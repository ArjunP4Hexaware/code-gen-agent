"""post92 (pair_03): a DECIMAL column the STTM gives no precision.

The type is written exactly as stated (``DECIMAL`` - valid Databricks SQL, read
as DECIMAL(10,0)) instead of crashing the feed with a TemplateGapError; no
precision is derived (a source length is a byte width); each such column gets
one non-blocking ``decimal_no_precision`` flag. Synthetic inputs only.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from codegen.emit.context import TemplateGapError, sql_type
from codegen.gate.decimal_precision import decimal_no_precision_flags


def test_a_bare_decimal_is_written_as_stated():
    assert sql_type("DECIMAL") == "DECIMAL"
    assert sql_type(" decimal ") == "DECIMAL"
    assert sql_type("Decimal(17,2)") == "DECIMAL(17,2)"         # unchanged
    with pytest.raises(TemplateGapError):
        sql_type("DECIMALISH")                                  # still loud on unknowns


def _field(column, stage="STRING", standard="DECIMAL", row=7):
    return SimpleNamespace(stage_column=column, standard_column=column,
                           stage_datatype=stage, standard_datatype=standard,
                           provenance=SimpleNamespace(row=row))


def _spec(fields, standard_table="syn_std"):
    segment = SimpleNamespace(fields=fields, stage_table=SimpleNamespace(table="syn_stg"),
                              standard_table=None)
    return SimpleNamespace(segments=[segment],
                           standard_table=SimpleNamespace(table=standard_table))


def test_each_bare_decimal_column_gets_one_flag():
    flags = decimal_no_precision_flags(_spec([
        _field("AMT_A"), _field("AMT_B", row=8),
        _field("AMT_C", standard="DECIMAL(5,0)"), _field("NAME", standard="STRING")]))
    assert len(flags) == 2
    assert flags[0].startswith("decimal_no_precision:standard — syn_std.AMT_A: ")
    assert "(STTM row 7)" in flags[0] and "DECIMAL(10,0)" in flags[0]
    assert "syn_std.AMT_B" in flags[1]


def test_a_bare_decimal_on_the_stage_layer_is_flagged_too():
    (flag,) = decimal_no_precision_flags(_spec([_field("AMT", stage="decimal",
                                                       standard="DECIMAL(9,2)")]))
    assert flag.startswith("decimal_no_precision:stage — syn_stg.AMT: ")
