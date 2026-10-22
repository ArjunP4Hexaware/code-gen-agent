"""post93 (pair_03): a source layout that repeats column names (10 x Qualifier,
10 x Type - a repeating group; the stage / standard names are unique).

A repeated name identifies no field: the IIG's SRC_COLUMNS takes the positional
form the rule already had (``col<i>:<stage column>``), a generated pipeline that
reads a file without a header row names its fields by position too, and one
``source_names_repeated`` flag names the repeated columns. A feed whose names are
unique is unchanged. Synthetic inputs only.
"""

from __future__ import annotations

from types import SimpleNamespace

from codegen import cli
from codegen.emit.context import pipeline_source_names
from codegen.gate.source_names import repeated_names, repeated_source_name_flags
from codegen.metadata_template import _named_sources


def _f(source, stage=None):
    return SimpleNamespace(source_column=source, stage_column=stage or source.upper())


def test_a_repeated_name_is_not_a_named_source():
    assert _named_sources([_f("A"), _f("B")])
    assert not _named_sources([_f("A"), _f("Qualifier", "Q1"), _f("Qualifier", "Q2")])


def test_the_pipeline_names_fields_by_position_only_when_headerless_and_repeated():
    fields = [_f("A"), _f("Qualifier", "Q1"), _f("Qualifier", "Q2")]
    assert pipeline_source_names(fields, headerless=True) == ["col1", "col2", "col3"]
    assert pipeline_source_names(fields, headerless=False) == ["A", "Qualifier", "Qualifier"]
    unique = [_f("A"), _f("B")]
    assert pipeline_source_names(unique, headerless=True) == ["A", "B"]


def test_one_flag_per_segment_names_the_repeats():
    fields = [_f("Qualifier", "Q1"), _f("Type", "T1"), _f("Qualifier", "Q2"), _f("Type", "T2")]
    assert repeated_names(fields) == {"Qualifier": 2, "Type": 2}
    spec = SimpleNamespace(segments=[SimpleNamespace(
        segment="Detail", fields=fields, stage_table=SimpleNamespace(table="syn_stg"))])
    (flag,) = repeated_source_name_flags(spec, headerless=True)
    assert flag.startswith("source_names_repeated:Detail — syn_stg: source columns "
                           "Qualifier x2, Type x2;")
    assert "by position too" in flag
    (header_flag,) = repeated_source_name_flags(spec, headerless=False)
    assert "not covered" in header_flag
    unique = SimpleNamespace(segments=[SimpleNamespace(
        segment="Detail", fields=[_f("A")], stage_table=SimpleNamespace(table="t"))])
    assert repeated_source_name_flags(unique, headerless=True) == []


def _with_repeated_sources(spec):
    """Pair 1 (fixed width) with two Detail fields given one source name."""
    segments = []
    for segment in spec.segments:
        fields = list(segment.fields)
        mapped = [i for i, f in enumerate(fields) if f.stage_column and f.standard_column]
        if segment.segment == "Detail" and len(mapped) >= 2:
            for i in mapped[:2]:
                fields[i] = fields[i].model_copy(update={"source_column": "Qualifier"})
        segments.append(segment.model_copy(update={"fields": fields}))
    return spec.model_copy(update={"segments": segments})


def test_a_fixed_width_feed_with_repeated_names_passes_its_gate(pair1_config, pair1_spec,
                                                                tmp_path):
    scoped = pair1_config.model_copy(update={"output": pair1_config.output.model_copy(
        update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})})
    result = cli.generate_feed_result(
        _with_repeated_sources(pair1_spec), scoped, dry_run=True, skip_tests=True,
        output_mode="framework", conventions_profile="acfc_prx", iig_template="iig_v2",
        console=False)
    gate = result.gate
    assert gate.verdict != "FAIL", [c for c in gate.checks if not c.passed]
    assert any(f.startswith("source_names_repeated:Detail") for f in gate.flags)
    # (pair 1's SRC_COLUMNS is positional by its own template; the note is pinned below)


def test_a_positional_src_columns_cell_says_why():
    from codegen.metadata_template import _src_columns_cell

    cell = _src_columns_cell("col1:Q1,col2:Q2", [_f("Qualifier", "Q1"), _f("Qualifier", "Q2")])
    assert cell["value"] == "col1:Q1,col2:Q2"
    assert cell["badge_entry"]["note"].startswith("iig_src_columns_positional: the source "
                                                  "layout repeats Qualifier x2")
    assert "note" not in _src_columns_cell("A:A", [_f("A")])["badge_entry"]
