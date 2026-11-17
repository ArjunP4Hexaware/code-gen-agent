"""post198: STTM / VDD headers match their role synonyms with spaces ignored
(``layout.discover.header_key``) - "FieldName" is "Field Name" without a config line
per spelling (post195 added "fieldname" by hand; "columnname" / "tablename" are the
same pattern). Only header -> role lookups use the key; values keep ``normalize``."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.layout.discover import discover, header_key, normalize
from test_sttm_fieldname_header import _workbook

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


def _without(config, layer: str, role: str, spelling: str):
    disc = config.extractor.discovery
    roles = {k: dict(v) for k, v in disc.roles.items()}
    roles[layer][role] = [s for s in roles[layer][role] if normalize(s) != spelling]
    return config.extractor.model_copy(update={
        "discovery": disc.model_copy(update={"roles": roles})})


def test_header_key_drops_spaces_only():
    assert header_key("FieldName") == header_key("Field Name") == header_key("field_name")
    assert header_key("Start Position (Fixed Width)") == "startpositionfixedwidth"
    assert normalize("FieldName") == "fieldname"          # normalize itself is unchanged


def test_a_one_word_header_resolves_without_its_own_synonym(config, tmp_path):
    extractor = _without(config, "source", "field_name", "fieldname")
    assert "fieldname" not in {normalize(s) for s in
                               extractor.discovery.roles["source"]["field_name"]}
    profile = discover(_workbook(tmp_path / "s.xlsx", "FieldName"), extractor).profile
    for sheet in ("FEED_A", "FEED_B"):
        assert "source/field_name" not in [f"{u.layer}/{u.role}"
                                           for u in profile.unresolved_for(sheet)]


def test_no_two_roles_share_a_header_key_in_the_shipped_config(config):
    """The guard that makes space-free matching safe: a collision would make a header
    ambiguous between two roles (refused, never picked - but a regression)."""
    disc = config.extractor.discovery
    clashes = []
    for layer, roles in disc.roles.items():
        owner: dict[str, str] = {}
        for role, spellings in roles.items():
            for spelling in spellings:
                key = header_key(spelling)
                if owner.setdefault(key, role) != role:
                    clashes.append((layer, spelling, owner[key], role))
    assert clashes == []
