"""post74 (D1 post73 pair_06): "STTM audit column invalid (role audit_column;
type timestamp) at STTM sheet 3 row 30". A type keyword with a parenthesised
attribute — timestamp(YYYY-MM-DD HH:MM:SS), decimal(18,2), varchar(50) — is
split into keyword + attribute before the vocabulary check; a format is kept
on the column (``*_format``) and reaches the IIG's date-rule INPUT_PARAM."""

from __future__ import annotations

import pytest

import codegen.extract.audit_types as audit_types
import codegen.extract.type_format as type_format
from codegen.config import load_config
from codegen.contracts.sttm import SttmField
from codegen.emit.context import sql_type
from codegen.extract import extract_contract
from codegen.extract.audit_types import audit_datatype
from codegen.extract.type_format import split_type
from codegen.metadata_template import _date_rule, _type_formats
from post51_pairs import AUDIT
from post73_pairs import FIELDS, FIRST_DATA_ROW, coordinates, frd, mapping_workbook

DATE = "2026-01-01"
STAMP = "timestamp(YYYY-MM-DD HH:MM:SS)"


@pytest.mark.parametrize(("raw", "keyword", "attribute", "kind", "type_text"), [
    (STAMP, "timestamp", "YYYY-MM-DD HH:MM:SS", "format", "timestamp"),
    ("Decimal(18,2)", "Decimal", "18,2", "size", "Decimal(18,2)"),
    ("decimal( 18 , 2 )", "decimal", "18 , 2", "size", "decimal( 18 , 2 )"),
    ("varchar(50)", "varchar", "50", "size", "varchar(50)"),
    ("Date (MM/DD/YYYY)", "Date", "MM/DD/YYYY", "format", "Date"),
    ("String", "String", None, "none", "String"),
    (None, "", None, "none", ""),
])
def test_split_type(raw, keyword, attribute, kind, type_text):
    parts = split_type(raw)
    assert (parts.keyword, parts.attribute, parts.kind, parts.type_text) == (
        keyword, attribute, kind, type_text)
    assert parts.format == (attribute if kind == "format" else None)


def _pair06(tmp_path, **kwargs):
    return mapping_workbook(tmp_path / "p6.xlsx",
                            audit=[AUDIT[0], ("REC_CREATION_TIME", STAMP)], **kwargs)


def test_the_fixture_reproduces_the_d1_line_without_the_split(config, tmp_path, monkeypatch):
    unsplit = type_format.split_type

    def whole(raw):            # the pre-post74 check: the cell as one token
        parts = unsplit(raw)
        return type_format.TypeParts(parts.raw, " ".join(parts.raw.split()), None, "none")

    monkeypatch.setattr(audit_types, "split_type", whole)
    with pytest.raises(Exception) as caught:
        extract_contract(_pair06(tmp_path), frd(tmp_path / "frd.json"), config,
                         generated_date=DATE)
    audit_row = FIRST_DATA_ROW + len(FIELDS) + 1
    assert coordinates(caught.value) == (
        "FAIL            extract-sttm — STTM audit column invalid (role audit_column; type "
        f"timestamp) at STTM sheet 2 row {audit_row} [ExtractionError]")


def test_an_audit_timestamp_with_a_format_extracts(config, tmp_path):
    contract = extract_contract(_pair06(tmp_path), frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    (feed,) = contract.feeds
    audit = {a.column: a for a in feed.audit_columns}
    assert audit["REC_CREATION_TIME"].datatype == "Timestamp"
    assert audit["REC_CREATION_TIME"].datatype_format == "YYYY-MM-DD HH:MM:SS"
    assert audit["SRC_FILE_NAME"].datatype_format is None


def test_the_vocabulary_check_reads_the_keyword_only(config):
    assert audit_datatype("REC_CREATION_TIME", STAMP, config) == "Timestamp"
    assert audit_datatype("LOAD_ID", "decimal(18,2)", config) is None    # still outside


def test_field_types_keep_their_size_and_split_their_format(config, tmp_path):
    workbook = mapping_workbook(tmp_path / "p6.xlsx", {
        2: {"stage_type": STAMP, "standard_type": "timestamp(YYYY-MM-DD)"},
        3: {"stage_type": "Decimal(18,2)", "standard_type": "decimal(18,2)"},
        4: {"stage_type": "varchar(50)"}})
    contract = extract_contract(workbook, frd(tmp_path / "frd.json"), config,
                                generated_date=DATE)
    by_name = {f.source_column: f for f in contract.feeds[0].fields}
    stamp = by_name["Service Date"]
    assert (stamp.stage_datatype, stamp.stage_datatype_format) == ("timestamp",
                                                                    "YYYY-MM-DD HH:MM:SS")
    assert (stamp.standard_datatype, stamp.standard_datatype_format) == ("timestamp",
                                                                          "YYYY-MM-DD")
    billed = by_name["Billed Amount"]
    assert (billed.stage_datatype, billed.stage_datatype_format) == ("Decimal(18,2)", None)
    assert by_name["Paid Amount"].stage_datatype == "varchar(50)"
    # a field with no parenthesised attribute serializes as before (no new keys)
    assert "stage_datatype_format" not in by_name["Claim Number"].model_dump(exclude_defaults=True)


def test_sql_type_maps_the_keyword_of_a_formatted_type():
    assert sql_type(STAMP) == "TIMESTAMP"
    assert sql_type("Date (MM/DD/YYYY)") == "DATE"
    assert sql_type("Decimal(18,2)") == "DECIMAL(18,2)"


def _field(**kwargs) -> SttmField:
    base = dict(source_column="SVC_DT", description=None, sample_value=None,
                source_datatype="string", nullable=True, phi=False, mandatory=False,
                stage_column="SVC_DT", stage_datatype="string", standard_column="SVC_DT",
                standard_datatype="date")
    return SttmField(**{**base, **kwargs})


def test_the_iig_date_rule_takes_the_type_cells_formats():
    tpl = load_config("config/config.yaml").metadata.templates["iig_v2"]
    both = _field(stage_datatype_format="MMDDYYYY", standard_datatype_format="yyyy-MM-dd")
    one = _field(stage_column="PAID_DT", standard_datatype_format="yyyy-MM-dd")
    assert _type_formats(both) == ("MMDDYYYY", "yyyy-MM-dd")
    assert _type_formats(one) is None
    assert _date_rule(tpl, [both, one]) == (["SVC_DT"], ["MMDDYYYY--yyyy-MM-dd"])
    # a Load Rule "Convert X to Y" still wins
    ruled = both.model_copy(update={"value_spec": "Convert yyyyMMdd to yyyy-MM-dd"})
    assert _date_rule(tpl, [ruled]) == (["SVC_DT"], ["yyyyMMdd--yyyy-MM-dd"])
