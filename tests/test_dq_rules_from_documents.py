"""post165 (2026-11-04): a DATA_QUALITY_RULES row exists only when the STTM states it.

A generated IIG's DQ sheet carried NullCheckRule / DeDuplicationRule on every feed and
LRTrimRule on every standard column - the corpus's most frequent classes, written as a
baseline whether or not the documents asked (read as "drawn from the ground-truth IIG").
Now (Soham: the STTM is the ground truth for the primary key):
- NullCheckRule over the STTM's Primary Key / not-null columns; no row when there are none;
- DeDuplicationRule over the STTM's Primary Key columns ONLY (not-null is not unique);
  no row without a key;
- LRTrimRule over the standard columns whose STTM load rule states a trim
  (``dq_trim_rule_regex``); no row otherwise.
Pair 4 (synthetic) under the ACFC overlay's DQ knobs (the ``dq`` fixture).
"""

from __future__ import annotations

from codegen.metadata_template import template_tab_rows
from test_iig_dq_rules import DQ, _v, dq  # noqa: F401  (dq: the shared fixture)


def _classes(rows, name):
    return [r for r in rows if _v(r, "RULE_CLASS") == name]


def _rerun(rows_spec, spec):
    """The DQ rows for ``spec`` with the fixture's config / FRD (rebuilt from the
    fixture's closure through template_tab_rows' own inputs)."""
    import json

    import yaml

    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from codegen.config import load_config
    from codegen.contracts.frd import FrdContract
    from multi_table_golden import PAIR4_OVERLAY
    from test_iig_dq_rules import DQ_KEYS
    from test_iig_v2_derivations import ACFC_OVERLAY, REPO

    acfc = yaml.safe_load(ACFC_OVERLAY.read_text(encoding="utf-8"))
    knobs = {k: v for k, v in acfc["metadata"]["templates"]["iig_v2"].items() if k in DQ_KEYS}
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        overlay = Path(tmp) / "dq.yaml"
        overlay.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": knobs}}}),
                           encoding="utf-8")
        config = load_config(REPO / "config" / "config.yaml", overlays=[PAIR4_OVERLAY, overlay])
    frd = FrdContract.model_validate(json.loads(
        (FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8")))
    tpl = config.metadata.templates["iig_v2"]
    return template_tab_rows(DQ, frd.feeds[0], config, spec, None, tpl)


def _with_fields(spec, change):
    segments = [s.model_copy(update={"fields": [change(f) for f in s.fields]})
                for s in spec.segments]
    return spec.model_copy(update={"segments": segments})


def test_dedup_is_keyed_on_the_sttm_primary_key_only(dq):  # noqa: F811
    rows, spec = dq
    (dedup,) = _classes(rows, "DeDuplicationRule")
    detail = spec.segments[1]
    key = [f.stage_column for f in detail.fields if f.primary_key]
    assert key, "pair 4's detail table states a Primary Key"
    assert _v(dedup, "SOURCE_COLUMN").split(",") == key
    (null,) = _classes(rows, "NullCheckRule")
    assert set(key) <= set(_v(null, "SOURCE_COLUMN").split(","))      # null check keeps both


def test_no_null_check_or_dedup_row_when_the_sttm_states_no_key_or_not_null(dq):  # noqa: F811
    _rows, spec = dq
    bare = _with_fields(spec, lambda f: f.model_copy(update={"primary_key": False,
                                                             "standard_primary_key": None}))
    bare = bare.model_copy(update={"not_null_columns": []})
    rows = _rerun(dq, bare)
    assert not _classes(rows, "NullCheckRule")
    assert not _classes(rows, "DeDuplicationRule")


def test_no_lr_trim_row_unless_a_load_rule_states_a_trim(dq):  # noqa: F811
    rows, spec = dq
    assert not any("trim" in (f.value_spec or "").lower() for s in spec.segments for f in s.fields)
    assert not _classes(rows, "LRTrimRule")
    detail = spec.segments[1]
    target = next(f for f in detail.fields if f.standard_column)
    fields = [f.model_copy(update={"value_spec": "Trim leading and trailing spaces"})
              if f.stage_column == target.stage_column else f for f in detail.fields]
    segments = [*spec.segments[:1], detail.model_copy(update={"fields": fields}),
                *spec.segments[2:]]
    stated = spec.model_copy(update={"segments": segments})
    trims = _classes(_rerun(dq, stated), "LRTrimRule")
    assert len(trims) == 1
    assert _v(trims[0], "SOURCE_COLUMN") == target.standard_column
    assert _v(trims[0], "TARGET_COLUMN") == target.standard_column
