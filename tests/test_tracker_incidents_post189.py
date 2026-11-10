"""post189: the incident tracker's CodeGen items 4-8 (a staging Accumulators run,
2026-11-10), on SYNTHETIC documents shaped like the real FRD.

5 - the Object Name block lists sample file names per line of business AND one line
    labelled "file pattern": that pattern is THE file (one IIG entry); the sample
    names are expected files. A sample the pattern does not match keeps every name.
6 - the ADLS Location cell is multi-line ("Raw Path:" then the path, then "Daily
    File:" ...): the labelled Raw Path line is the landing, its trailing
    "<File.extn>" segment dropped (no folder).
7 - the folder-path row's "N/A- The file will land in the ADLS path directly" is a
    note, never a path (its '/' is the one in "N/A").
8 - SRC_COMPRESSION follows the FRD's Archive Schedule ("... should be compressed
    and moved to archive" = Y); unstated = the template constant.
4 - every PROCESS_NAME cell is listed with the source its cell records, then how to
    change a name and rerun.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from acfc_shapes import family_e_multi as fm
from codegen import cli
from codegen.config import load_config
from codegen.contracts.frd import FrdContract

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
NOTE = "N/A- The file will land in the ADLS path directly"
RAW = "synacct01/mftlanding/inbound/vendor_e/care_mgmt"
SAMPLES = ["Exchange: 2010001_SYNRX_EXCH_CMACCUM_YYYYMMDD_HHMMSS_.TXT",
           "Medicare: 2010002_SYNRX_MCR_CMACCUM_YYYYMMDD_HHMMSS_.TXT"]
PATTERN_LINE = "File Pattern: *_SYNRX_*_CMACCUM*"


@pytest.fixture
def env(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    return tmp_path


def _frd(env: Path, capsys, **kwargs) -> FrdContract:
    frd, sttm, out = env / "FRD_cm.docx", env / "STTM_cm.xlsx", env / "frd.json"
    frd.write_bytes(fm.build_frd(**kwargs))
    fm.build_sttm().save(sttm)
    capsys.readouterr()
    code = cli.main(["layout", "--workbook", str(sttm), "--frd", str(frd), "--dry-run",
                     "--no-cache", "--frd-contract-out", str(out)])
    printed = capsys.readouterr().out
    assert code == 0, printed
    return FrdContract.model_validate_json(out.read_text(encoding="utf-8"))


def _read(env: Path, **kwargs) -> FrdContract:
    """The FRD read on its own (the extractor - no layout step, no STTM)."""
    from codegen.extract.frd_docx import extract_frd_contract

    path = env / "FRD_cm.docx"
    path.write_bytes(fm.build_frd(**kwargs))
    contract, _ = extract_frd_contract(path, load_config(CONFIG), generated_date="2026-11-10")
    return contract


def _flags(contract: FrdContract, prefix: str) -> list[str]:
    return [f for f in contract.extraction_flags if f.startswith(prefix)]


# 5 ---------------------------------------------------------------------------------
def test_a_stated_file_pattern_is_the_one_file_and_the_samples_are_expected_names(env):
    contract = _read(env, files=[*SAMPLES, PATTERN_LINE])
    assert contract.feeds[0].file_name_patterns == ["*_SYNRX_*_CMACCUM*"]
    (flag,) = _flags(contract, "frd_file_pattern_stated:")
    assert "'File Pattern'" in flag and "2 other file name(s)" in flag


def test_a_sample_the_pattern_does_not_match_keeps_every_name(env):
    other = "Medicaid: 2010003_OTHER_MCD_ACCUM_YYYYMMDD.TXT"
    contract = _read(env, files=[*SAMPLES, other, PATTERN_LINE])
    assert len(contract.feeds[0].file_name_patterns) == 4
    assert _flags(contract, "frd_file_pattern_stated:") == []


# 6 / 7 -----------------------------------------------------------------------------
def test_the_raw_path_line_of_a_multi_line_cell_is_the_landing(env):
    cell = f"Raw Path:\n{RAW}/<File.extn>\nDaily File :\n{RAW}/daily/<File.extn>"
    contract = _read(env, adls_location=cell, inbound_path=NOTE)
    assert contract.feeds[0].landing_location == RAW + "/"
    (line,) = _flags(contract, "frd_landing_from_labelled_line:")
    assert "['Daily File']" in line                 # the other labelled line is named
    assert _flags(contract, "frd_landing_file_segment:")
    assert not any(a.startswith("frd_multiline:feeds[0].landing_location")
                   for a in contract.provenance.ambiguities)


def test_an_na_note_is_never_a_landing(env):
    contract = _read(env, adls_location="", inbound_path=NOTE)
    assert contract.feeds[0].landing_location is None
    assert any("a note that states no path" in str(a)
               for a in contract.provenance.ambiguities)


def test_a_plain_landing_is_unchanged(env):
    contract = _read(env)                     # the builder's default rows
    assert contract.feeds[0].landing_location == fm.LOCATION
    assert _flags(contract, "frd_landing_") == []


# 8 ---------------------------------------------------------------------------------
@pytest.mark.parametrize(("archive", "expected"), [
    ("Once the file is processed it should be compressed and moved to archive.", "Y"),
    ("Files are moved to archive; they are not compressed.", "N"),
    ("Files are kept for 7 years.", None),
    (None, None),
])
def test_src_compression_follows_the_archive_statement(archive, expected):
    from codegen.metadata_template import _stated_compression

    tpl = load_config(CONFIG).metadata.templates["iig_v2"]
    cell = _stated_compression(tpl, SimpleNamespace(archive_retention=archive))
    assert (cell or {}).get("value") == expected
    if expected:
        assert cell["badge_entry"]["badge"] == "from_frd"


def test_the_archive_statement_reaches_the_iig_builder(env, capsys):
    from codegen.metadata_sheet import _feed_from_spec
    from codegen.resolve.resolver import resolve_feeds

    archive = "Once the file is processed it should be compressed and moved to archive."
    contract = _frd(env, capsys, archive=archive)
    assert contract.feeds[0].archive_retention == archive
    sttm_out = env / "sttm.json"
    assert cli.main(["extract-sttm", "--workbook", str(env / "STTM_cm.xlsx"),
                     "--frd-contract", str(env / "frd.json"), "--out", str(sttm_out),
                     "--generated-date", "2026-11-10"]) == 0
    from codegen.contracts.sttm import SttmContract

    sttm = SttmContract.model_validate_json(sttm_out.read_text(encoding="utf-8"))
    specs = resolve_feeds(contract, sttm, load_config(CONFIG), frd_sha256="0" * 64,
                          sttm_sha256="0" * 64)
    assert specs and all(s.archive_retention == archive for s in specs)
    assert _feed_from_spec(specs[0]).archive_retention == archive


# 4 ---------------------------------------------------------------------------------
def test_every_process_name_is_listed_with_its_source_then_how_to_change_it():
    from codegen.emit.framework import _naming_notes
    from codegen.naming_provenance import CHANGE_HINT

    payload = {"tabs": {
        "DATA_FACTORY_PIPELINE": {"rows": [
            {"values": {"PROCESS_NAME": "G1  Raw to stage load"},
             "badges": {"PROCESS_NAME": {"badge": "synthetic", "tooltip": "the corpus pattern"}}},
            {"values": {"PROCESS_NAME": ""}, "badges": {}}]},
        "OTHER": {"rows": [{"values": {"X": "1"}, "badges": {}}]}}}
    notes = _naming_notes(["PIPELINE_NAME [master] = `PL_X`"], payload)
    assert notes == [
        "PIPELINE_NAME [master] = `PL_X`",
        "PROCESS_NAME [DATA_FACTORY_PIPELINE row 1] = `G1  Raw to stage load` — the corpus pattern",
        "PROCESS_NAME [DATA_FACTORY_PIPELINE row 2] is OPEN — no source recorded",
        CHANGE_HINT]
    assert _naming_notes([], {"tabs": {}}) == []
