"""Audit #10 (2026-10-26, post130): a corpus key is checked against the table's columns.

The corpus (the prod goldens under ``pipeline_name_corpus``, D1 only) is the last
explicit key signal. The FRD and FAQ signals go through ``_match`` - the key only
when EVERY name is one of the table's columns, spelled as the layer names it -
but the corpus row was taken as written: a TGT_PRIMARY_KEY naming no column of
the table became a profile default, written unasked into every key cell, exit 0.
"""

from __future__ import annotations

from codegen import primary_key


def _unkeyed(spec):
    """pair 4 with no STTM Primary Key mark and no FRD key statement: the corpus
    is the only signal left."""
    segments = [s.model_copy(update={"fields": [
        f.model_copy(update={"primary_key": False, "standard_primary_key": None})
        for f in s.fields]}) for s in spec.segments]
    return spec.model_copy(update={"segments": segments, "frd_key_statement": None})


def _offer(spec, stated: str):
    table = primary_key.detail_table(spec, "stage")
    return primary_key.proposal(table, spec, None, {table.table.casefold(): stated}), table


def test_a_corpus_key_naming_no_column_proposes_nothing(pair4_spec):
    offer, _table = _offer(_unkeyed(pair4_spec), "NOT_A_COLUMN_X")
    assert not offer and offer.columns == ()


def test_a_corpus_key_with_one_unknown_name_proposes_nothing(pair4_spec):
    spec = _unkeyed(pair4_spec)
    real = spec.detail_segment.fields[2].stage_column
    offer, _table = _offer(spec, f"{real}, NOT_A_COLUMN_X")
    assert not offer


def test_a_corpus_key_of_real_columns_is_written_as_the_layer_names_them(pair4_spec):
    spec = _unkeyed(pair4_spec)
    field = spec.detail_segment.fields[2]
    offer, table = _offer(spec, field.source_column)          # the source spelling
    assert offer.columns == (field.stage_column,)
    assert offer.kind == "corpus" and table.table in offer.source
