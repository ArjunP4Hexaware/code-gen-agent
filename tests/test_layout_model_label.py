"""Audit #6 (2026-10-26, post129): the layout model's spelling never reaches a contract.

The model decides WHERE a field is; code copies what the document says. The
FRD validator compared only the NORMALIZED label, then the reader copied the
model's ``label`` verbatim into the provenance and, under the model's
``labelled_rule`` flag, into the rule text ("FREQUENCY ::: Daily"); a model
``inline_label`` likewise reached the provenance. A validated claim now carries
the document's own spelling, ``labelled_rule`` is derived exactly as the
synonym path derives it, and an ``inline_label`` naming no pair in the cell
is rejected.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.extract.frd_docx import discover_frd, read_docx, read_frd
from codegen.layout import resolve as rs
from codegen.layout.frd_profile import FrdUnresolved

REPO = Path(__file__).resolve().parents[1]
FRD = REPO / "fixtures" / "acfc_shapes" / "frd"


@pytest.fixture(scope="module")
def config():
    os.environ.setdefault("CODEGEN_SKIP_ENV_OVERLAY", "1")
    return load_config(REPO / "config" / "config.yaml")


def _as_model_claim(content, profile, config, target: str, update: dict, extra: dict | None = None):
    """``target`` left to the model (synonyms dropped it), claimed with ``update``
    applied to the synonym source; returns (validated profile, rejections)."""
    source = profile.fields[target]
    fields = {k: v for k, v in profile.fields.items() if k != target}
    left = profile.model_copy(update={
        "fields": fields,
        "unresolved": [*profile.unresolved, FrdUnresolved(field=target, reason="test")]})
    claim = {**source.model_dump(mode="json"), **update}
    claims = {target: claim, **(extra or {})}
    merged = rs._merge_frd(left, claims, "model", 0.8)
    return rs._validate_frd(merged.model_copy(update={"source": "model"}), content, config,
                            {"model"})


def _contract(content, profile, config):
    return read_frd(content, profile, config, document_name="syn.docx",
                    generated_date="1970-01-01")


def test_a_model_label_variant_carries_the_documents_spelling(config):
    content = read_docx(FRD / "f1_pair_1.docx", prose_ok=True)
    profile = discover_frd(content, config.extractor.frd)
    target = "feeds[0].frequency"
    expected = _contract(content, profile, config)
    stated = profile.fields[target].label
    rules = [k for k in profile.fields if "validation_rules" in k]
    claim = {"label": stated.upper() + " ::", "labelled_rule": True}
    # the model also claims the same (non-DQ) cell as a rule, flagged labelled
    extra = {f"feeds[0].validation_rules[{len(rules)}]": {
        **profile.fields[target].model_dump(mode="json"), **claim}}
    validated, rejections = _as_model_claim(content, profile, config, target, claim, extra)
    assert rejections == []
    assert validated.fields[target].label == stated              # the cell's text
    assert validated.fields[target].labelled_rule is False       # derived, not the model's
    contract = _contract(content, validated, config)
    assert contract.field_provenance[target].label == stated
    assert contract.feeds[0].frequency == expected.feeds[0].frequency
    assert not any(r.startswith(stated.upper()) for r in contract.feeds[0].validation_rules)


def test_a_dq_rule_row_stays_labelled_whatever_the_model_says(config):
    content = read_docx(FRD / "f1_pair_1.docx", prose_ok=True)
    profile = discover_frd(content, config.extractor.frd)
    target = next(k for k, v in profile.fields.items() if v.labelled_rule)
    expected = _contract(content, profile, config)
    validated, rejections = _as_model_claim(content, profile, config, target,
                                            {"labelled_rule": False})
    assert rejections == [] and validated.fields[target].labelled_rule is True
    assert (_contract(content, validated, config).feeds[0].validation_rules
            == expected.feeds[0].validation_rules)


def test_a_model_inline_label_variant_carries_the_documents_spelling(config):
    content = read_docx(FRD / "f2_pair_8.docx", prose_ok=True)
    profile = discover_frd(content, config.extractor.frd)
    target = next(k for k, v in profile.fields.items() if v.inline_label)
    stated = profile.fields[target].inline_label
    validated, rejections = _as_model_claim(content, profile, config, target,
                                            {"inline_label": stated.lower() + ":"})
    assert rejections == []
    assert validated.fields[target].inline_label == stated
    assert _contract(content, validated, config).field_provenance[target].inline_label == stated


def test_an_inline_label_the_cell_does_not_carry_is_rejected(config):
    content = read_docx(FRD / "f2_pair_8.docx", prose_ok=True)
    profile = discover_frd(content, config.extractor.frd)
    target = next(k for k, v in profile.fields.items() if v.inline_label)
    validated, rejections = _as_model_claim(content, profile, config, target,
                                            {"inline_label": "Syn Invented Label"})
    assert target not in validated.fields
    assert [r.role for r in rejections] == [target]
    assert "names no 'Label: value' pair" in rejections[0].reason
