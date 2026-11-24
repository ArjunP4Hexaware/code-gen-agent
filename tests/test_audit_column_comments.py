"""post220: the standard COMMENT of an audit column no STTM row describes.

A staging data engineer's request (2026-11-24): LOB, SRC_FILE_NAME,
REC_CREATION_TIME and REC_UPDATED_TIME carried no COMMENT (no STTM row describes
them) and were named in ddl_comment_blank. acfc_prx's
``audit_column_comments`` (config) now supplies the text; an STTM description
still wins; the texts are config, so a rewording is a config line.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.emit.framework import _combined_ddl_text
from test_derivations import FRD_CATALOG, REPO, _pair11_specs


@pytest.fixture(scope="module")
def shipped():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture(scope="module")
def spec(shipped):
    specs, _ = _pair11_specs(FRD_CATALOG, Path(tempfile.mkdtemp()), shipped)
    (one,) = [s for s in specs if s.feed_slug == "vc_disenrollment"]
    return one


def _ddl(spec, profile, config):
    flags: list[str] = []
    return _combined_ddl_text(spec, profile, flags, config), flags


def test_the_shipped_texts(shipped):
    texts = shipped.conventions.get("acfc_prx").audit_column_comments
    assert texts == {"LOB": "Line of Business", "SRC_FILE_NAME": "Source File Name",
                     "REC_CREATION_TIME": "Record Created Date",
                     "REC_UPDATED_TIME": "Record Updated Date"}
    assert shipped.conventions.get("edo_sfmc").audit_column_comments == {}


def test_each_undescribed_audit_column_gets_its_text_in_both_layers(spec, shipped):
    ddl, flags = _ddl(spec, shipped.conventions.get("acfc_prx"), shipped)
    for line in ("SRC_FILE_NAME STRING COMMENT 'Source File Name'",
                 "REC_CREATION_TIME TIMESTAMP COMMENT 'Record Created Date'",
                 "REC_UPDATED_TIME TIMESTAMP COMMENT 'Record Updated Date'"):
        assert ddl.count(f"\n{line}") == 2, line
    assert not [f for f in flags if f.startswith("ddl_comment_blank:")]


def test_a_reworded_text_is_written_as_configured_and_escaped(spec, shipped):
    base = shipped.conventions.get("acfc_prx")
    profile = base.model_copy(update={"audit_column_comments": {
        **base.audit_column_comments, "REC_UPDATED_TIME": "Record's last update time"}})
    ddl, _ = _ddl(spec, profile, shipped)
    assert ddl.count("\nREC_UPDATED_TIME TIMESTAMP COMMENT 'Record\\'s last update time'") == 2


def test_a_removed_key_leaves_that_column_blank_and_flagged(spec, shipped):
    base = shipped.conventions.get("acfc_prx")
    texts = {k: v for k, v in base.audit_column_comments.items() if k != "SRC_FILE_NAME"}
    ddl, flags = _ddl(spec, base.model_copy(update={"audit_column_comments": texts}), shipped)
    assert ddl.count("\nSRC_FILE_NAME STRING,\n") == 2
    blank = [f for f in flags if f.startswith("ddl_comment_blank:")]
    assert len(blank) == 2 and all("for SRC_FILE_NAME (" in f for f in blank)


def test_no_text_without_column_comments(spec, shipped):
    # the pair-1 golden's shape (column_comments off) stays bare
    profile = shipped.conventions.get("acfc_prx").model_copy(update={"column_comments": False})
    ddl, _ = _ddl(spec, profile, shipped)
    assert "Source File Name" not in ddl and "Record Created Date" not in ddl
