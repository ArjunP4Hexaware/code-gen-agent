"""post74 (D1 post73 item 5): pair_04 asked ``feeds[0].Delimiter`` while pair_10
asked ``feeds[0].delimiter``. The live layout model claimed the FRD field
under its header label and the claimed path became the question's key. Keys
come from the ROLE name: a claimed path is normalised before it is stored,
and the answers file is read through the same normaliser, so either
spelling answers the question."""

from __future__ import annotations

import pytest
import yaml

from codegen.answer_keys import canonical_key, canonical_keys
from codegen.layout.answers import load_answers
from codegen.layout.frd_profile import FrdLayoutProfile, FrdUnresolved
from codegen.layout.resolve import _merge_frd


@pytest.mark.parametrize(("written", "canonical"), [
    ("feeds[0].Delimiter", "feeds[0].delimiter"),
    ("feeds[0].delimiter", "feeds[0].delimiter"),
    ("feeds[1].File Format", "feeds[1].file_format"),
    ("feeds[0].Stage_Target.Load Strategy", "feeds[0].stage_target.load_strategy"),
    ("feeds[0].columns[2].Target Type", "feeds[0].columns[2].target_type"),
    ("feeds[0].fields[Amount (01)].Width", "feeds[0].fields[Amount (01)].width"),
    ("feeds[0].landing_location#confirming", "feeds[0].landing_location#confirming"),
    ("feeds.feed_1.SRC_ADLS_PATH", "feeds.feed_1.src_adls_path"),
    ("run.environment.Storage_Account", "run.environment.storage_account"),
    ("sheets[2]/band[1]/layer", "sheets[2]/band[1]/layer"),          # not a scoped key
    ("FEED_1_MAPPING/stage/column", "FEED_1_MAPPING/stage/column"),
])
def test_canonical_key(written, canonical):
    assert canonical_key(written) == canonical


def test_the_canonical_spelling_wins_a_duplicate():
    assert canonical_keys({"feeds[0].delimiter": "|", "feeds[0].Delimiter": ","}) == {
        "feeds[0].delimiter": "|"}


def test_the_answers_file_reads_either_spelling(tmp_path):
    path = tmp_path / "answers.yaml"
    path.write_text(yaml.safe_dump({
        "gaps": {"feeds[0].Delimiter": {"value": "|"}},
        "inputs": {"run": {"Storage_Account": {"value": "acct1"}}}}), encoding="utf-8")
    answers = load_answers(path)
    assert answers.gaps == {"feeds[0].delimiter": {"value": "|"}}
    assert answers.inputs == {"run.storage_account": "acct1"}


def test_a_model_claim_under_a_label_lands_on_the_role_path():
    profile = FrdLayoutProfile(fingerprint="f", family="F1", source="synonyms", unresolved=[
        FrdUnresolved(field="feeds[0].delimiter", reason="no label in the document maps")])
    claim = {"table": 1, "row": 3, "col": 0, "value_col": 1, "label": "Delimiter"}
    merged = _merge_frd(profile, {"feeds[0].Delimiter": claim}, "model", 0.9)
    assert set(merged.fields) == {"feeds[0].delimiter"}
    assert merged.field_sources == {"feeds[0].delimiter": "model"}
    assert not merged.unresolved                       # the role's question is answered
