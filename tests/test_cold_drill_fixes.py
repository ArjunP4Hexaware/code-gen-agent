"""Chunk B (2026-10-09) — one focused test per generator fix the cold-pair
drill (``tests/test_cold_pairs.py``) found. Inputs are the synthetic cold
pairs (``fixtures/acfc_shapes/cold/``) and the Chunk A band shapes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from acfc_shapes import bands, cold_pairs
from acfc_shapes.common import docx_bytes, table, xlsx_bytes
from codegen import cli
from codegen.extract.frd_docx import (
    FrdDocxError,
    discover_frd,
    extract_frd_contract,
    is_unnamed_feed,
    read_docx,
)
from codegen.extract.generic import (
    GenericExtractionError,
    answers_section,
    parse_audit_answers,
)
from codegen.layout.answers import AnswersFile, apply_answers
from codegen.layout.classify import classify_workbook
from codegen.layout.discover import discover, is_blank_placeholder
from codegen.layout.resolve import LayoutQuestion, resolve_pair
from codegen.resolve.gapfill import TARGET_KEY_RE

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
DATE = "2026-10-09"


def _sttm(pair: str) -> Path:
    return SHAPES / cold_pairs.sttm_path(pair)


def _frd(pair: str) -> Path:
    return SHAPES / cold_pairs.frd_path(pair)


# ----------------------------------------------------------------- FRD reader


def test_f1_section_tables_with_a_reference_column_are_read(config):
    """``Ref | Label | Value`` (``DM | Descriptive Metadata`` over ``DM-1 |
    Name | …``): the title sits after the reference token, every label row
    repeats the token as its prefix - read like the documented F1 table."""
    profile = discover_frd(read_docx(_frd("cold_1")), config.extractor.frd)
    assert profile.family == "F1" and profile.unresolved == []
    assert profile.fields["feeds[0].file_format"].label == "Object/data Format"
    assert profile.fields["feeds[0].stage_target.load_strategy"].label == "Load Strategy STG"
    assert [s.section for s in profile.sections] == ["descriptive", "structural", "technical",
                                                     "data_quality", "vendor"]


def test_an_object_name_that_is_a_file_pattern_names_the_file(config):
    contract, _profile = extract_frd_contract(_frd("cold_1"), config, generated_date=DATE)
    feed = contract.feeds[0]
    assert feed.file_name_patterns == ["CH_CLAIMS_DAILY_YYYYMMDD.psv"]
    assert feed.feed_name == "ch_claims_daily"                 # the section's Name row
    assert any(f.startswith("file_pattern_from_object_name:feeds[0]")
               for f in contract.extraction_flags)


def test_an_f2_requirement_name_is_not_a_feed_name(config):
    """F2: the Name row names the Solution Requirement ("Ingest member
    enrollment file"); the feed stays unnamed for the STTM band to name."""
    contract, _profile = extract_frd_contract(_frd("cold_6"), config, generated_date=DATE)
    assert is_unnamed_feed(contract.feeds[0].feed_name)


def test_a_target_schema_cell_with_trailing_layer_markers_is_read_per_layer(config):
    """cold_3's F1 ``Target Schema`` reads "stg_nb_prov (stage), nb_prov
    (standard)": the marker in parentheses after each value names its layer."""
    contract, _profile = extract_frd_contract(_frd("cold_3"), config, generated_date=DATE)
    feed = contract.feeds[0]
    assert (feed.stage_target.schema_name, feed.standard_target.schema_name) == (
        "stg_nb_prov", "nb_prov")


def test_an_f2_domain_table_is_read(config):
    """F2 states Domain / Sub Domain in a separate 2x2 label | value table
    (docs/acfc/SHAPES_FOR_PORT.md section 4, pair 10)."""
    contract, profile = extract_frd_contract(_frd("cold_2"), config, generated_date=DATE)
    feed = contract.feeds[0]
    assert (feed.domain, feed.sub_domain) == ("Eligibility", "Enrollment Spans")
    assert profile.fields["feeds[0].domain"].label == "Domain"
    assert "feeds[0].domain" not in {u.field for u in profile.unresolved}


def test_a_prose_frd_places_no_field_and_asks_for_every_required_one(config):
    contract, profile = extract_frd_contract(_frd("cold_5"), config, generated_date=DATE)
    assert profile.family == "prose" and profile.fields == {}
    fields = {u.field for u in profile.unresolved}
    assert {"feeds[0].file_format", "feeds[0].lobs",
            "feeds[0].stage_target.load_strategy"} <= fields
    assert len(contract.feeds) == 1
    # Only the FRD readers accept a paragraphs-only document; the strict read
    # (e.g. the App's probe) still refuses it.
    with pytest.raises(FrdDocxError, match="carries no tables"):
        read_docx(_frd("cold_5"))


def test_an_unreadable_frd_is_a_fail_line_not_a_traceback(config, tmp_path, capsys,
                                                         monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    notes = tmp_path / "notes.docx"
    notes.write_bytes(docx_bytes([table([["Term", "Definition"], ["STG", "Stage"]])]))
    capsys.readouterr()
    code = cli.main(["layout", "--workbook", str(_sttm("cold_1")), "--frd", str(notes),
                     "--dry-run", "--no-cache"])
    out = capsys.readouterr().out
    assert code == 1
    assert out.splitlines()[-1].startswith(f"{'FAIL':<15} layout — FRD notes.docx cannot be read")
    assert "Traceback" not in out


# ----------------------------------------------------------------- STTM reader


@pytest.mark.parametrize("value,blank", [(",", False), ("|", False), ("~", False),
                                         ("TBD", True), ("-", True), ("N/A", True),
                                         ("n.a.", True), ("", True), ("Daily", False)])
def test_a_delimiter_character_is_a_value_not_a_placeholder(value, blank, config):
    assert is_blank_placeholder(value, config.extractor.discovery.meta_blank_values) is blank


def test_pass_3_reads_a_sheet_by_its_band_title_row(config):
    """cold_3: no band row names stage AND standard and "Schema | Table |
    Column | Type" forms no label group - each sheet is a candidate mapping
    sheet by its title spans; "Raw Zone" is stage by its stg_ schema values,
    "Curated Zone" (no layer word, no prefix) is the band question."""
    found = discover(_sttm("cold_3"), config.extractor)
    assert [s.name for s in found.profile.mapping_sheets] == ["PROV_DEMOG", "PROV_LOC",
                                                              "PROV_SPEC"]
    sheet = found.profile.sheet("PROV_DEMOG")
    stage = sheet.band("stage")
    assert (stage.col_start, stage.col_end, stage.layer_evidence) == (6, 9, "schema_value")
    assert sheet.band("standard") is None
    open_ = {f"{u.sheet}/{u.layer}/{u.role}" for u in found.profile.unresolved}
    assert "PROV_DEMOG/band[2]/layer" in open_ and "PROV_DEMOG/stage/table" in open_
    verdict = classify_workbook(_sttm("cold_3"), config.extractor)
    assert verdict.kind == "unclassified" and verdict.reason.startswith("confirm:")


def test_pass_3_reads_bands_by_their_shared_qualifier_word(config):
    """cold_6: no title row over the headers - "Landing …" / "Curated …" runs
    are the bands, told apart by their Catalog values (PR_DLK / PR_STD); the
    qualifier names the band, the rest of a header its role."""
    found = discover(_sttm("cold_6"), config.extractor)
    sheet = found.profile.sheet("STTM")
    stage, standard = sheet.band("stage"), sheet.band("standard")
    assert (stage.col_start, stage.col_end, stage.layer_evidence) == (5, 9, "catalog_value")
    assert (standard.col_start, standard.col_end, standard.layer_evidence) == (
        10, 14, "catalog_value")
    assert stage.roles == {"catalog": 5, "schema": 6, "target_type": 9}
    assert sheet.band("rules").col_start == 15 and sheet.band("source").col_end == 4
    # Rules AFTER both bands ("PII | Primary Key | Load Rules") read with the
    # data-rules synonyms: the key reaches TGT_PRIMARY_KEY.
    assert sheet.band("rules").roles == {"pii": 15, "primary_key": 16, "load_rule": 17}
    verdict = classify_workbook(_sttm("cold_6"), config.extractor)
    assert verdict.kind == "unclassified" and verdict.reason.startswith("confirm:")


def test_pass_3_never_runs_when_a_mapping_sheet_exists(config):
    found = discover(SHAPES / "sttm" / "pair_4_family_d.xlsx", config.extractor)
    assert not any("pass 3" in n for n in found.profile.notes)


def test_a_sheet_without_a_stage_band_names_the_band_remedy(config, tmp_path):
    from codegen.extract import ExtractionError, extract_contract

    sttm = tmp_path / "one.xlsx"
    sttm.write_bytes(xlsx_bytes(bands.one_band(title="Standard Layer")))
    frd = tmp_path / "frd.json"
    frd.write_text(json.dumps(bands.frd_contract()), encoding="utf-8")
    with pytest.raises(ExtractionError, match="has no stage band") as exc:
        extract_contract(sttm, frd, config, generated_date=DATE)
    assert f"{bands.SHEET}/band[<n>]/layer" in str(exc.value)


def test_a_role_key_is_answered_under_answers():
    assert answers_section("Sheet A/stage/table") == "answers"
    assert answers_section("Sheet A/band[2]/layer") == "answers"
    assert answers_section("feeds[0].stage_target.schema") == "gaps"
    assert answers_section("feeds[0].audit_columns") == "gaps"
    assert answers_section("feeds[0].fields[a/b].width") == "gaps"


def test_audit_column_answers_parse_and_refuse_an_unknown_type():
    parsed = parse_audit_answers({"feeds[1].audit_columns": {
        "value": "SRC_FILE_NAME:String; LOAD_TS:timestamp\nBATCH_ID:String"}})
    assert parsed == {1: [("SRC_FILE_NAME", "String"), ("LOAD_TS", "Timestamp"),
                          ("BATCH_ID", "String")]}
    with pytest.raises(GenericExtractionError, match="NAME:Type"):
        parse_audit_answers({"feeds[0].audit_columns": {"value": "LOAD_TS:Date"}})


# ----------------------------------------------------------------- layout stage


def test_frd_field_questions_are_answered_under_gaps():
    question = LayoutQuestion(document="frd", sheet=None, layer=None,
                              role="feeds[0].file_format", reason="no label", header=[],
                              candidates=[])
    answers, notes = apply_answers(AnswersFile(gaps={
        "feeds[0].file_format": {"value": "Fixed Width"},
        "feeds[0].stage_target.catalog": {"value": "cat_x"}}), [question], {})
    assert answers["gaps"]["feeds[0].file_format"]["value"] == "Fixed Width"
    assert answers["gaps"]["feeds[0].stage_target.catalog"]["value"] == "cat_x"
    assert notes == []
    assert TARGET_KEY_RE.match("feeds[3].standard_target.catalog")


def _frd_question(key: str) -> LayoutQuestion:
    return LayoutQuestion(document="frd", sheet=None, layer=None, role=key, reason="no label",
                          header=[], candidates=[])


def test_a_feed_name_answer_is_refused_with_a_note_not_counted_as_applied():
    """B2 (Chunk B review): the layout stage applies no gaps: value for the
    feed NAME (the FRD's Name row names a feed, else the STTM stage band -
    the key each sheet pairs by). The answer is kept out of the applied set
    and a note says why, instead of 'applied' and then dropped."""
    answers, notes = apply_answers(AnswersFile(gaps={
        "feeds[0].feed_name": {"value": "some_feed"},
        "feeds[0].lobs": {"value": "ALL"}}),
        [_frd_question("feeds[0].feed_name"), _frd_question("feeds[0].lobs")], {})
    assert set(answers["gaps"]) == {"feeds[0].lobs"}
    assert notes == ["gaps['feeds[0].feed_name'] is not applied - the FRD's Name row names "
                     "the feed, else the layout stage names it after the STTM stage band - the "
                     "key each STTM sheet pairs by; an answer cannot rename a feed"]


def test_note_lines_drop_the_answer_hint_for_a_field_the_contract_carries(
        tmp_path, monkeypatch, capsys):
    """B2: cold_5's prose FRD places no field; after its answers.yaml the
    pair-resolved contract carries LOBs, the stage strategy, frequency and
    domain (answers) and the file format (STTM). Their NOTE lines say so
    instead of asking for an answer under gaps: again; a field still open
    keeps the hint, and a feed_name answer is refused by name."""
    import yaml

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    answers = yaml.safe_load((SHAPES / "cold" / "cold_5" / "answers.yaml").read_text(
        encoding="utf-8"))
    answers["gaps"]["feeds[0].feed_name"] = {"value": "fc_some_other_name"}
    answers_path = tmp_path / "answers.yaml"
    answers_path.write_text(yaml.safe_dump(answers), encoding="utf-8")
    frd_out = tmp_path / "frd.json"
    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(_sttm("cold_5")), "--frd", str(_frd("cold_5")),
                     "--dry-run", "--no-cache", "--answers", str(answers_path),
                     "--frd-contract-out", str(frd_out)]) == 0
    out = capsys.readouterr().out
    notes = {line[cli.ANSWER_LABEL_WIDTH:].split(" — ", 1)[0]: line
             for line in out.splitlines() if line.startswith("NOTE ") and " — " in line}
    hint = "answer the value under gaps:"
    for field in ("lobs", "stage_target.load_strategy", "frequency", "domain"):
        line = notes[f"feeds[0].{field}"]
        assert hint not in line
        assert "the pair-resolved FRD contract carries it, from the answers file" in line
    assert "carries it, from the STTM (" in notes["feeds[0].file_format"]
    assert hint not in notes["feeds[0].feed_name"]
    assert hint in notes["feeds[0].standard_target.load_strategy"]     # still open
    assert "gaps['feeds[0].feed_name'] is not applied" in out
    assert json.loads(frd_out.read_text(encoding="utf-8"))["feeds"][0]["feed_name"] != (
        "fc_some_other_name")


def test_the_frd_format_cell_delimiter_disagreeing_with_the_sttm_is_asked(config):
    pair = resolve_pair(_sttm("cold_1"), _frd("cold_1"), config, provider=None,
                        use_cache=False)
    question = next(q for q in pair.questions if q.key == "feeds[0].delimiter")
    assert question.kind == "choice"
    assert [c["value"] for c in question.candidates] == ["|", ","]
    assert pair.frd_contract.feeds[0].delimiter is None


def test_the_frd_format_cell_delimiter_is_taken_when_nothing_disagrees(config):
    pair = resolve_pair(_sttm("cold_3"), _frd("cold_3"), config, provider=None,
                        use_cache=False)
    assert pair.frd_contract.feeds[0].delimiter == ","
    assert any(f.startswith("frd_unstated:feeds[0].delimiter source_used:FRD")
               for f in pair.flags)


def _cli_contracts(pair: str, tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """The pure-CLI path (no layout stage): extract-frd -> extract-sttm with
    the pair's band placements but NOT its gaps: answers."""
    import yaml

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    answers = yaml.safe_load((SHAPES / "cold" / pair / "answers.yaml").read_text(
        encoding="utf-8"))
    answers.pop("gaps", None)
    answers_path = tmp_path / "answers.yaml"
    answers_path.write_text(yaml.safe_dump(answers), encoding="utf-8")
    frd, sttm = tmp_path / "frd.json", tmp_path / "sttm.json"
    assert cli.main(["extract-frd", "--docx", str(_frd(pair)), "--out", str(frd)]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(_sttm(pair)), "--frd-contract", str(frd),
                     "--out", str(sttm), "--generated-date", DATE,
                     "--answers", str(answers_path)]) == 0
    return frd, sttm


def test_the_cli_path_fails_when_the_frd_format_cell_and_the_sttm_disagree(config, tmp_path,
                                                                          monkeypatch):
    """B1 (Chunk B review): cold_1's FRD format cell reads "Pipe delimited
    (|) …", its STTM meta row says ','. Without the layout stage the
    contract resolver applies the same rule: a contract mismatch naming both
    cells and the gaps: key - never the STTM ',' filled silently."""
    from codegen.resolve.resolver import ContractMismatchError
    from codegen.resolve.resolver import resolve_pair as resolve_contracts

    frd, sttm = _cli_contracts("cold_1", tmp_path, monkeypatch)
    with pytest.raises(ContractMismatchError) as exc:
        resolve_contracts(frd, sttm, config)
    (error,) = [e for e in exc.value.errors if "delimiter" in e]
    assert "table 2 row 4 ('Object/data Format')" in error and "names '|'" in error
    assert "CH_CLAIMS_DAILY meta row 'delimiter' says ','" in error
    assert "answer feeds[0].delimiter under gaps:" in error


@pytest.mark.parametrize("sttm_value", ["|", "Pipe", None])
def test_the_cli_path_takes_the_frd_format_cell_delimiter_when_nothing_disagrees(
        sttm_value, config, tmp_path, monkeypatch):
    """B1: the STTM agreeing (as a character or a word) or silent - the FRD
    format cell's character is taken, flagged citing the FRD cell."""
    from codegen.resolve.resolver import resolve_pair as resolve_contracts

    frd, sttm = _cli_contracts("cold_1", tmp_path, monkeypatch)
    data = json.loads(sttm.read_text(encoding="utf-8"))
    feed = data["feeds"][0]
    if sttm_value is None:
        feed["meta_rows"].pop("delimiter")
    else:
        feed["meta_rows"]["delimiter"] = sttm_value
    feed["source_file"]["delimiter"] = None if sttm_value is None else "|"
    sttm.write_text(json.dumps(data), encoding="utf-8")
    (spec,) = resolve_contracts(frd, sttm, config)
    assert spec.delimiter == "|"
    assert any(f.startswith("frd_unstated:delimiter source_used:FRD table 2 row 4 "
                            "('Object/data Format'): 'Pipe delimited (|)") and f.endswith(": '|'")
               for f in spec.provenance_flags)
    assert not any("source_used:STTM" in f and f.startswith("frd_unstated:delimiter")
                   for f in spec.provenance_flags)


@pytest.mark.parametrize("text,char", [
    ("Pipe delimited (|) text file, extension .psv", "|"),
    ("CSV, comma delimited, first row is a header", ","),
    ("tab-delimited text", "\t"),
    ("Delimited (|)", "|"),
    ("Fixed width, 120 bytes", None),           # a stray comma is no delimiter
    ("CSV", None),
    ("pipeline delimited", None),               # whole words only
])
def test_a_format_cell_names_a_delimiter_only_in_so_many_words(text, char, config):
    from codegen.resolve.gapfill import delimiter_in_format

    assert delimiter_in_format(text, config.extractor.delimiter_words) == char


def test_lobs_come_from_the_sttm_meta_row_when_the_frd_lists_none(config):
    answers = {"sttm": {"FC_ELIG_LAYOUT/band[1]/layer": "stage",
                        "FC_ELIG_LAYOUT/band[2]/layer": "standard"}}
    pair = resolve_pair(_sttm("cold_2"), _frd("cold_2"), config, provider=None,
                        use_cache=False, answers=answers)
    feed = pair.frd_contract.feeds[0]
    assert feed.lobs == ["MCD", "CHIP"]
    assert feed.stage_target.tables == ["fc_elig_hdr", "fc_elig_dtl", "fc_elig_trl"]
    assert any(f.startswith("frd_unstated:feeds[0].lobs source_used:STTM") for f in pair.flags)


def test_one_frd_feed_naming_two_sheet_tables_becomes_two_feeds(config):
    roles = {f"{sheet}/{layer}/{role}": col
             for sheet in ("MAPPING-RX_CLAIM", "MAPPING-RX_REVERSAL")
             for layer, role, col in (("source", "field_name", 1), ("stage", "table", 9),
                                      ("stage", "column", 10), ("stage", "target_type", 11),
                                      ("standard", "table", 13), ("standard", "column", 14),
                                      ("standard", "target_type", 15))}
    pair = resolve_pair(_sttm("cold_4"), _frd("cold_4"), config, provider=None,
                        use_cache=False, answers={"sttm": roles})
    assert [f.feed_name for f in pair.frd_contract.feeds] == ["ch_rx_claim", "ch_rx_reversal"]
    # The reversal file matches its table by name; the claim file is asked.
    assert pair.frd_contract.feeds[1].file_name_patterns == ["CH_RX_REV_YYYYMMDD.csv"]
    assert [q.key for q in pair.questions] == ["feeds[0].file_name_patterns"]
    # The FRD's compound Frequency ("Claims daily; reversals weekly") is no
    # single value: each feed takes its own File Details row (flagged).
    assert pair.frd_contract.feeds[1].frequency == "Weekly"
    assert any(f.startswith("frd_frequency_per_file:feeds[1].frequency") for f in pair.flags)


_COLD4_ROLES = {f"{sheet}/{layer}/{role}": col
                for sheet in ("MAPPING-RX_CLAIM", "MAPPING-RX_REVERSAL")
                for layer, role, col in (("source", "field_name", 1), ("stage", "table", 9),
                                         ("stage", "column", 10), ("stage", "target_type", 11),
                                         ("standard", "table", 13), ("standard", "column", 14),
                                         ("standard", "target_type", 15))}


def test_a_compound_frequency_gives_way_to_each_feeds_own_file_details_row(config):
    """B4 (Chunk B review): cold_4's FRD Frequency cell names two cadences
    ("Claims daily; reversals weekly") for the two files of one block. With
    the claim file answered, EACH derived feed takes its own File Details
    row, flagged citing the FRD cell (the block's, for the derived feed too)
    and the row's cell."""
    gaps = {"feeds[0].file_name_patterns": {"value": "CH_RX_CLM_<LOB>_YYYYMMDD.csv",
                                            "source": "user"}}
    pair = resolve_pair(_sttm("cold_4"), _frd("cold_4"), config, provider=None,
                        use_cache=False, answers={"sttm": _COLD4_ROLES, "gaps": gaps})
    assert [f.frequency for f in pair.frd_contract.feeds] == ["Daily", "Weekly"]
    flags = [f for f in pair.flags if f.startswith("frd_frequency_per_file:")]
    assert flags == [
        "frd_frequency_per_file:feeds[0].frequency — the FRD table 0 row 6 ('Frequency') names "
        "several cadences ('Claims daily; reversals weekly'); this feed's File Details row "
        "FILE_DETAILS!E2 states 'Daily': taken",
        "frd_frequency_per_file:feeds[1].frequency — the FRD table 0 row 6 ('Frequency') names "
        "several cadences ('Claims daily; reversals weekly'); this feed's File Details row "
        "FILE_DETAILS!E3 states 'Weekly': taken"]
    fills = {f["field"]: (f["value"], f["source"], f["cell"]) for f in pair.gap_fills}
    assert fills["feeds[0].frequency"] == ("Daily", "STTM", "FILE_DETAILS!E2")
    assert fills["feeds[1].frequency"] == ("Weekly", "STTM", "FILE_DETAILS!E3")


def test_a_compound_frequency_stays_when_the_feeds_rows_state_several(config):
    """B4: before the claim file is answered, feed 0 still lists both files -
    its File Details rows state two cadences, so the FRD text stays (no
    single value to take, nothing flagged for it)."""
    pair = resolve_pair(_sttm("cold_4"), _frd("cold_4"), config, provider=None,
                        use_cache=False, answers={"sttm": _COLD4_ROLES})
    assert pair.frd_contract.feeds[0].frequency == "Claims daily; reversals weekly"
    assert not any(f.startswith("frd_frequency_per_file:feeds[0]") for f in pair.flags)


@pytest.mark.parametrize("frequency,patterns,rows,taken", [
    # two cadences, this feed's own row states one: taken
    ("Claims daily; reversals weekly", ["CLM_YYYYMMDD.csv"],
     [("CLM_YYYYMMDD.csv", "Daily"), ("REV_YYYYMMDD.csv", "Weekly")], ("Daily", "E2")),
    # the date placeholder is canonicalised (CCYY = YYYY)
    ("Claims daily; reversals weekly", ["REV_CCYYMMDD.csv"],
     [("CLM_YYYYMMDD.csv", "Daily"), ("REV_YYYYMMDD.csv", "Weekly")], ("Weekly", "E3")),
    # ONE cadence is a single value: the FRD text stays
    ("Daily by 6 AM", ["CLM_YYYYMMDD.csv"], [("CLM_YYYYMMDD.csv", "Weekly")], None),
    # the feed's own rows disagree: the FRD text stays
    ("Daily or weekly", ["CLM_YYYYMMDD.csv"],
     [("CLM_YYYYMMDD.csv", "Daily"), ("CLM_YYYYMMDD.csv", "Weekly")], None),
    # no File Details row names this feed's file: the FRD text stays
    ("Claims daily; reversals weekly", ["OTHER_YYYYMMDD.csv"],
     [("CLM_YYYYMMDD.csv", "Daily")], None),
])
def test_the_compound_frequency_rule(frequency, patterns, rows, taken, config):
    from codegen.contracts.frd import FrdContract
    from codegen.layout.resolve import GapFillResult, _FeedGapFiller

    data = bands.frd_contract()
    data["feeds"][0].update({"frequency": frequency, "file_name_patterns": patterns})
    contract = FrdContract.model_validate(data)
    facts = {"meta": {}, "file_rows": [
        {"name": name, "cell": f"FILE_DETAILS!A{row}", "frequency": cadence,
         "frequency_cell": f"FILE_DETAILS!E{row}"}
        for row, (name, cadence) in enumerate(rows, start=2)]}
    result = GapFillResult(contract=contract)
    filler = _FeedGapFiller(contract, 0, facts, {}, {}, config, REPO, result)
    filler._compound_frequency()
    if taken is None:
        assert filler.patched.frequency == frequency
        assert result.flags == [] and "feeds[0].frequency" not in result.handled
        return
    value, cell = taken
    assert filler.patched.frequency == value
    assert result.flags == [
        f"frd_frequency_per_file:feeds[0].frequency — the FRD contract field "
        f"feeds[0].frequency names several cadences ({frequency!r}); this feed's File Details "
        f"row FILE_DETAILS!{cell} states {value!r}: taken"]
    assert "feeds[0].frequency" in result.handled


def test_a_stated_catalog_answer_reaches_the_frd_contract(config, tmp_path):
    sttm = tmp_path / "one.xlsx"
    sttm.write_bytes(xlsx_bytes(bands.one_band(title="Staging Layer", schema="stg_nb")))
    frd = tmp_path / "frd.json"
    frd.write_text(json.dumps(bands.frd_contract()), encoding="utf-8")
    gaps = {"feeds[0].stage_target.catalog": {"value": "cat_x", "source": "user"}}
    pair = resolve_pair(sttm, frd, config, provider=None, use_cache=False,
                        answers={"gaps": gaps})
    assert pair.frd_contract.feeds[0].stage_target.catalog == "cat_x"


# ----------------------------------------------------------------- resolve / emit


def test_an_unknown_audit_column_stops_notebook_mode_only():
    from codegen.emit.context import TemplateGapError
    from codegen.emit.emitter import _check_gaps

    context = {"audit_columns": [("SRC_FILE_NAME", "STRING"), ("LOAD_TS", "TIMESTAMP")]}
    _check_gaps(context, framework_only=True)                 # carried, flagged by the caller
    with pytest.raises(TemplateGapError, match="output-mode framework"):
        _check_gaps(context)


def test_the_sttm_stage_schema_wins_over_a_disagreeing_frd(config, tmp_path, monkeypatch,
                                                            capsys):
    """CLAUDE.md doctrine: the STTM stage band is authoritative for the
    schema; an FRD stating another is a flagged cross-check, never a
    contract mismatch (Chunk A finding iv)."""
    from codegen.resolve.resolver import resolve_pair as resolve_contracts

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    answers = SHAPES / "cold" / "cold_1" / "answers.yaml"
    frd, sttm = tmp_path / "frd.json", tmp_path / "sttm.json"
    assert cli.main(["layout", "--workbook", str(_sttm("cold_1")), "--frd", str(_frd("cold_1")),
                     "--dry-run", "--no-cache", "--answers", str(answers),
                     "--frd-contract-out", str(frd)]) == 0
    assert cli.main(["extract-sttm", "--workbook", str(_sttm("cold_1")), "--frd-contract",
                     str(frd), "--out", str(sttm), "--generated-date", DATE,
                     "--answers", str(answers)]) == 0
    data = json.loads(frd.read_text(encoding="utf-8"))
    data["feeds"][0]["stage_target"]["schema"] = "stg_other"
    frd.write_text(json.dumps(data), encoding="utf-8")
    (spec,) = resolve_contracts(frd, sttm, config)
    assert spec.segments[0].stage_table.schema_name == "stg_ch_claims"
    assert any(f.startswith("frd_crosscheck:stage_target.schema") and "'stg_other'" in f
               for f in spec.provenance_flags)
