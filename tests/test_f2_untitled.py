"""D1 post51 pairs 08-10: "FRD ... cannot be read: no metadata section table
(F1) and no Solution Requirement table (F2) found; table titles seen: [...,
'', '', ...]". The F2 requirement tables carried no caption, and the detector
only looked at the caption. F2 is now found by the tables' row-label
fingerprint (SHAPES_FOR_PORT section F2), the caption a second signal, the
signal printed as a NOTE; the error line names the table count and header-row
fingerprints, never a title."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from acfc_shapes.common import docx_bytes, paragraph, table
from codegen.extract.frd_docx import (
    F2_SIGNAL_NOTE,
    FrdUnreadableError,
    extract_frd_contract,
    header_fingerprint,
)
from codegen.run_errors import first_error_line, first_error_line_full
from codegen.term_hash import term_sha256
from post51_pairs import untitled_f2_frd

REPO = Path(__file__).resolve().parents[1]
SENTINEL = "SENTINEL_TERM"
FIELDS = ("feed_name", "source_system", "file_format", "frequency", "lobs", "domain",
          "stage_target", "standard_target", "validation_rules", "recycle_rule")


def _feed(path: Path, config) -> tuple[dict, list[str]]:
    contract, profile = extract_frd_contract(path, config, generated_date="2026-01-01")
    assert profile.family == "F2" and profile.unresolved == []
    (feed,) = contract.feeds
    dumped = feed.model_dump(mode="json")
    return {k: dumped[k] for k in FIELDS}, [n for n in profile.notes
                                           if n.startswith(F2_SIGNAL_NOTE)]


def test_the_captioned_shape_names_both_signals(config, tmp_path):
    _feed_, signals = _feed(untitled_f2_frd(tmp_path / "f2.docx", "row"), config)
    assert signals == [f"{F2_SIGNAL_NOTE} header-row fingerprint (9 labels) + caption "
                       "— table(s) [1, 2, 3, 4, 5, 6, 7, 8]"]


@pytest.mark.parametrize(("caption", "spacer"), [("blank", False), ("none", False),
                                                 ("blank", True), ("none", True)])
def test_untitled_tables_read_as_the_captioned_ones(config, tmp_path, caption, spacer):
    baseline, _ = _feed(untitled_f2_frd(tmp_path / "row.docx", "row"), config)
    feed, signals = _feed(untitled_f2_frd(tmp_path / "f2.docx", caption, spacer), config)
    assert feed == baseline
    assert feed["feed_name"] == "FEED_8" and feed["stage_target"]["load_strategy"]
    assert signals == [f"{F2_SIGNAL_NOTE} header-row fingerprint (9 labels) "
                       "— table(s) [1, 2, 3, 4, 5, 6, 7, 8]"]


def test_the_fingerprint_needs_the_required_labels(config, tmp_path):
    frd = config.extractor.frd.model_copy(update={"solution_requirement_required_labels": [
        "Business Requirement", "Functional Requirement", "Data Steward"]})
    narrowed = config.model_copy(update={"extractor": config.extractor.model_copy(
        update={"frd": frd})})
    with pytest.raises(FrdUnreadableError):
        extract_frd_contract(untitled_f2_frd(tmp_path / "f2.docx"), narrowed)


def _unreadable(path: Path) -> Path:
    path.write_bytes(docx_bytes([
        paragraph("Functional Requirements"),
        table([["Version", "Date", "Author", "Description"], ["1.0", "2026-01-01", "A", "B"]]),
        table([[SENTINEL, ""], ["Name", "x"]]),
        table([["", "", ""], ["Priority", "High", ""]]),
    ]))
    return path


def test_the_cannot_be_read_line_names_count_and_fingerprints_never_titles(tmp_path):
    docx = _unreadable(tmp_path / "frd.docx")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-frd", "--docx", str(docx),
         "--out", str(tmp_path / "frd.json"), "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode == 1
    version = term_sha256("version|date|author|description")[:12]
    prints = [version, term_sha256(f"{SENTINEL.lower()}|")[:12], term_sha256("||")[:12]]
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert line == (f"{'FAIL':<15} extract-frd — FRD in no documented family (F1 / F2) at "
                    f"FRD: 3 tables, header-row fingerprints {' '.join(prints)} "
                    "[FrdUnreadableError]")
    full = first_error_line_full(done.returncode, done.stderr, done.stdout)
    assert f"among 3 table(s); header-row fingerprints: {prints}" in full
    for text in (line, full, done.stdout, done.stderr):
        assert SENTINEL not in text and "Version" not in text


def test_header_fingerprint_is_reproducible_at_home():
    rows = [["Version", "Date", "Author", "Description"], ["1.0", "x", "y", "z"]]
    assert header_fingerprint(rows) == term_sha256("version|date|author|description")[:12]
    assert header_fingerprint([]) == term_sha256("")[:12]


def test_layout_prints_which_signal_found_the_f2_tables(tmp_path):
    docx = untitled_f2_frd(tmp_path / "f2.docx", "blank")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "layout", "--workbook",
         str(REPO / "fixtures" / "acfc_shapes" / "sttm" / "pair_8_family_a.xlsx"),
         "--frd", str(docx), "--provider", "mock", "--no-cache",
         "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert done.returncode in (0, 3), done.stdout + done.stderr
    assert (f"{'NOTE':<15}frd/family — {F2_SIGNAL_NOTE} header-row fingerprint (9 labels) "
            "— table(s) [1, 2, 3, 4, 5, 6, 7, 8] — informational") in done.stdout


def test_requirement_tables_naming_no_section_leave_the_fields_unresolved(config, tmp_path):
    # Pair 10's shape (SHAPES_FOR_PORT section F2): the metadata sits in free
    # text, no row names a section. One feed whose required fields are owed,
    # never a silently empty feed; the Domain table still fills its two.
    from acfc_shapes.frd import _solution_requirement

    parts = [table([["Domain", "Claims"], ["Sub Domain", "Encounters"]])]
    parts += [_solution_requirement(n, f"Req {n}", "Business text", "Load the file.",
                                    "Requirement Details", "Data Source: VENDOR_X", "blank")
              for n in range(1, 5)]
    path = tmp_path / "f2.docx"
    path.write_bytes(docx_bytes(parts))
    contract, profile = extract_frd_contract(path, config, generated_date="2026-01-01")
    assert profile.family == "F2" and profile.sections == []
    assert len(contract.feeds) == 1
    owed = {u.field for u in profile.unresolved}
    assert "feeds[0].feed_name" in owed and "feeds[0].stage_target.tables" in owed
    assert "feeds[0].domain" not in owed
