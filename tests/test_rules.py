"""Rule compiler classifications against the verified fixture map."""

from __future__ import annotations

from collections import Counter

from codegen.rules.compiler import compile_rules


def _by_class(spec):
    return Counter(outcome.classification for outcome in compile_rules(spec))


def test_community_feeds_flag_member_id_and_recycle(specs_by_id):
    for feed_id in ("sd_community_demographic_risk", "sd_community_risk"):
        outcomes = compile_rules(specs_by_id[feed_id])
        assert _by_class(specs_by_id[feed_id]) == {"mappable": 1, "flagged": 2}
        flagged = {o.rule_text[:20]: o for o in outcomes if o.classification == "flagged"}
        member_id = next(o for o in outcomes if "MEMBER_ID" in o.rule_text)
        assert member_id.classification == "flagged"
        assert "does not exist" in member_id.notes
        assert flagged  # recycle + member_id


def test_individual_feed_flags_zip_code_only(specs_by_id):
    outcomes = compile_rules(specs_by_id["sd_individual_risk"])
    assert _by_class(specs_by_id["sd_individual_risk"]) == {"mappable": 2, "flagged": 1}
    zip_rule = next(o for o in outcomes if "ZIP_CODE" in o.rule_text)
    assert zip_rule.classification == "flagged"


def test_caqh_classification_map(specs_by_id):
    outcomes = compile_rules(specs_by_id["caqh_tpl_inbound_files"])
    assert _by_class(specs_by_id["caqh_tpl_inbound_files"]) == {
        "mappable": 4,
        "orchestration_config": 2,
        "unmapped": 2,
        "notification": 2,
    }
    unmapped = [o for o in outcomes if o.classification == "unmapped"]
    assert any("Payer Area" in o.rule_text for o in unmapped)
    assert any("File type" in o.rule_text for o in unmapped)
    # The AS-IS rule carries U+2011; the regex must still classify it mappable.
    as_is = next(o for o in outcomes if "AS‑IS" in o.rule_text or "AS-IS" in o.rule_text)
    assert as_is.classification == "mappable"
    assert as_is.feature == "identity_mapping"
