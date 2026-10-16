"""post59: the file-name recognizer breaks a tie, and remembers the BSA's answer.

When two files match a mapping sheet's table equally (the layout split step's
``tie between``), the conventions profile decides before anyone is asked:

1. the source — ``file_tie_source_priority`` (the FRD's landed pattern over an
   STTM FILE_DETAILS label …);
2. the shape — ``file_tie_shape`` (a vendor prefix + an extension).

A tie still standing is the question. The BSA's answer is cached in the STTM
layout profile (``LayoutProfile.file_choices``, sheet -> file), so the next
run of the same workbook takes it without asking. Synthetic names only."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.extract.frd_docx import discover_frd, read_docx, read_frd
from codegen.layout import resolve as layout_resolve
from codegen.layout.profile import LayoutProfile
from codegen.layout.resolve import break_file_tie, split_frd_feeds_by_sttm

REPO = Path(__file__).resolve().parents[1]
PROFILE = load_config(REPO / "config" / "config.yaml").conventions.get("acfc_prx")


def test_the_frd_landed_pattern_wins_over_a_file_details_label():
    tied = ["Acme claims extract", "ACME_CLAIMS_YYYYMMDD.txt"]
    kinds = {"Acme claims extract": {"sttm_file_details"},
             "ACME_CLAIMS_YYYYMMDD.txt": {"frd_pattern"}}
    name, why = break_file_tie(tied, kinds, PROFILE, {"acme"})
    assert name == "ACME_CLAIMS_YYYYMMDD.txt" and why.startswith("source priority: frd_pattern")


def test_the_shape_decides_between_two_labels_of_one_source():
    tied = ["claims extract", "ACME_claims_YYYYMMDD.csv", "claims_YYYYMMDD.csv"]
    kinds = dict.fromkeys(tied, {"sttm_file_details"})
    assert break_file_tie(tied, kinds, PROFILE, {"acme"}) == (
        "ACME_claims_YYYYMMDD.csv", "shape: a vendor prefix + an extension")


@pytest.mark.parametrize("profile_update", [
    {},                                                          # equal on both counts
    {"file_tie_source_priority": [], "file_tie_shape": False},  # switched off
])
def test_a_tie_that_stands_is_asked(profile_update):
    tied = ["ACME_a_YYYYMMDD.csv", "ACME_b_YYYYMMDD.csv"]
    kinds = dict.fromkeys(tied, {"frd_pattern"})
    profile = PROFILE.model_copy(update=profile_update)
    assert break_file_tie(tied, kinds, profile, {"acme"}) is None


def _split_inputs(config, tmp_path):
    from test_frd_multi_object import _multi_object_docx

    path = tmp_path / "frd.docx"
    path.write_bytes(_multi_object_docx("alpha_claims_YYYYMMDD.csv"))
    content = read_docx(path)
    contract = read_frd(content, discover_frd(content, config.extractor.frd), config,
                        document_name="frd.docx", generated_date="2026-01-01")
    files = ["alpha_claims_YYYYMMDD.csv", "vendor_feed_one_YYYYMMDD.csv",
             "vendor_feed_two_YYYYMMDD.csv"]
    lifted = contract.feeds[0].model_copy(update={"file_name_patterns": files[:1]})
    contract = contract.model_copy(update={"feeds": [lifted]})
    facts = {"meta": {}, "files": [(f, f"FILE_DETAILS!B{i}") for i, f in enumerate(files, 2)],
             "sheet_tables": [
                 {"sheet": f"MAPPING-{t.upper()}", "stage_table": t, "standard_table": None,
                  "stage_schema": "stg_syn"}
                 for t in ("alpha_claims", "beta_members", "gamma_scores")]}
    return contract, facts


def test_the_split_breaks_a_tie_by_source(tmp_path, monkeypatch):
    """A sheet whose two best files tie: the FRD's own pattern is taken, a NOTE
    flag says how, no question is asked for it."""
    config = load_config(REPO / "config" / "config.yaml")
    contract, facts = _split_inputs(config, tmp_path)
    real = layout_resolve.best_file_matches

    def tied(sheets, files, **kw):
        picks, ties = real(sheets, files, **kw)
        if "MAPPING-BETA_MEMBERS" in sheets:
            ties["MAPPING-BETA_MEMBERS"] = [("vendor_feed_one_YYYYMMDD.csv", 0.5),
                                            ("alpha_claims_YYYYMMDD.csv", 0.5)]
        return picks, ties

    monkeypatch.setattr(layout_resolve, "best_file_matches", tied)
    _split, flags, questions = split_frd_feeds_by_sttm(contract, facts, {}, config)
    assert "feeds[1].file_name_patterns" not in [q.key for q in questions]
    (flag,) = [f for f in flags if f.startswith("frd_unstated:feeds[1].file_name_patterns")]
    assert "'alpha_claims_YYYYMMDD.csv'" in flag and "broken by source priority" in flag


def test_the_bsa_answer_is_remembered_with_the_layout_profile(tmp_path):
    config = load_config(REPO / "config" / "config.yaml")
    contract, facts = _split_inputs(config, tmp_path)
    _split, _flags, questions = split_frd_feeds_by_sttm(contract, facts, {}, config,
                                                        remember={})
    assert "feeds[1].file_name_patterns" in [q.key for q in questions]
    remember: dict = {}
    gaps = {"feeds[1].file_name_patterns": {"value": "vendor_feed_one_YYYYMMDD.csv",
                                            "source": "FILE_DETAILS!B3"}}
    split_frd_feeds_by_sttm(contract, facts, gaps, config, remember=remember)
    assert remember == {"MAPPING-BETA_MEMBERS": "vendor_feed_one_YYYYMMDD.csv"}
    # the next run: no answers file, the cached choice — no question for that table
    split, flags, questions = split_frd_feeds_by_sttm(contract, facts, {}, config,
                                                      remember=dict(remember))
    assert "feeds[1].file_name_patterns" not in [q.key for q in questions]
    assert split.feeds[1].file_name_patterns == ["vendor_feed_one_YYYYMMDD.csv"]
    assert any("the BSA's earlier answer (cached in the layout profile)" in f for f in flags)


def test_the_cache_rides_the_profile_and_stays_out_of_an_empty_dump():
    fields = {"fingerprint": "f", "sheets": [], "source": "user", "strategy": "content"}
    assert "file_choices" not in LayoutProfile(**fields).model_dump(mode="json")
    cached = LayoutProfile(**fields, file_choices={"S1": "a.csv"})
    assert LayoutProfile.model_validate(cached.model_dump(mode="json")).file_choices == {
        "S1": "a.csv"}
