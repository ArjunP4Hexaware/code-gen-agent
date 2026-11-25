"""post222: one data-type rule for the extractor and the DDL.

post213 let a standard type spelled with spaces ("BIG INT", a real STTM's) through the
extractor as a type, but the DDL's own reader (``emit.context.sql_type``) refused it:
the standard column was then written as stated ("BIG INT" - no Databricks type) and
flagged ``standard_type_unmapped``. Now ``sql_type`` reads the spelling and the
extractor asks it, so the two can never disagree."""

import pytest

from codegen.emit.context import TemplateGapError, sql_type
from codegen.extract.generic import _is_data_type

SPELLINGS = ["BIG INT", "Big Int", "small int", "TINY INT", "time stamp", "String",
             "Decimal(12,2)", "decimal (18, 4)", "Derived", "See comments", "date time", ""]


@pytest.mark.parametrize("text", SPELLINGS)
def test_the_extractor_and_the_ddl_agree_on_every_spelling(text):
    try:
        sql_type(text)
        ddl_reads = True
    except (TemplateGapError, ValueError):
        ddl_reads = False
    assert _is_data_type(text) is ddl_reads


@pytest.mark.parametrize(("text", "sql"), [("BIG INT", "BIGINT"), ("Big Int", "BIGINT"),
                                           ("small int", "SMALLINT"),
                                           ("time stamp", "TIMESTAMP")])
def test_a_type_spelled_with_spaces_is_that_type(text, sql):
    assert sql_type(text) == sql


@pytest.mark.parametrize("text", ["Derived", "date time", "double precision"])
def test_a_note_or_an_unknown_type_is_still_refused(text):
    with pytest.raises(TemplateGapError):
        sql_type(text)


def test_the_ddl_writes_the_type_not_the_spelling():
    from types import SimpleNamespace

    from codegen.emit.framework import _standard_from_stage_type

    field = SimpleNamespace(stage_column="COL_X", standard_datatype="BIG INT",
                            provenance=SimpleNamespace(sheet="MAPPING-X", row=9),
                            stage_datatype="String")
    flags: list[str] = []
    assert _standard_from_stage_type(field, "String", flags) == "BIGINT"
    assert not flags
