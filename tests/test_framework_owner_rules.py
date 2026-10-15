"""The client framework owner's rules (2026-10-14), the ones not pinned elsewhere.

Rule 3 — FILE_ADLS_INGESTION_DETAILS is EMPTY for an MFT-landed feed: the landing
path / container names ``mftlanding`` as a path segment (SD and CAQH both) — the
sheet is written with its headers only, plus an ``iig_file_adls_mft`` NOTE. Any
other feed gets one FILE_ADLS row per ADLS_DELTA_INGESTION_DETAILS row (its file),
the landing container / path copied from that row. iig_diff: for an MFT agent the
golden's ALL_FILES file rows pair with the agent's ADLS_DELTA rows on the file
identity, and FILE_ADLS reports "empty by rule (MFT)", never missing.
"""

from __future__ import annotations

from openpyxl import load_workbook

from test_iig_corpus_cells import _acfc, _notes
from test_iig_v2_derivations import FRD, _rows, _run, _write_overlay

FILE_ADLS, ADLS = "FILE_ADLS_INGESTION_DETAILS", "ADLS_DELTA_INGESTION_DETAILS"


def test_an_mft_landed_feed_writes_file_adls_with_headers_only(tmp_path):
    """The D1 environment lands files in the mftlanding container: MFT."""
    _spec, gate, xlsx = _run(FRD, _acfc(), tmp_path)
    (adls,) = _rows(xlsx, ADLS)
    assert adls["SRC_CONTAINER_NAME"][0] == "mftlanding"
    workbook = load_workbook(xlsx)
    sheet = workbook[FILE_ADLS]
    assert sheet.max_row == 1                                     # the headers, no row
    assert [c.value for c in sheet[1]][:4] == ["GROUP_ID", "OBJECT_ID", "DOMAIN", "SUBDOMAIN"]
    notes = [f for f in _notes(gate) if f.startswith("iig_file_adls_mft:")]
    assert len(notes) == 1 and "lands by MFT (its landing names 'mftlanding')" in notes[0]
    assert "rule 3" in notes[0]


def test_a_non_mft_feed_gets_one_file_adls_row_per_adls_delta_row(tmp_path):
    """The pair_11 FRD's landing itself sits under mftlanding — here the landing
    container is another and the MFT marker list names neither: not MFT."""
    overlay = _write_overlay(tmp_path, "environments:\n  D1:\n    containers:\n"
                                       "      landing: syn-landing-01\n"
                                       "metadata:\n  templates:\n    iig_v2:\n"
                                       "      mft_landing_markers: [syn-mft-only]\n")
    _spec, gate, xlsx = _run(FRD, _acfc(overlay), tmp_path)
    adls_rows, file_rows = _rows(xlsx, ADLS), _rows(xlsx, FILE_ADLS)
    assert len(file_rows) == len(adls_rows) >= 1
    for adls, row in zip(adls_rows, file_rows, strict=True):
        assert row["TGT_CONTAINER_NAME"][0] == adls["SRC_CONTAINER_NAME"][0] == "syn-landing-01"
        assert row["TGT_ADLS_PATH"][0] == adls["SRC_ADLS_PATH"][0]
        assert row["DOMAIN"][0] == adls["DOMAIN"][0]
        assert "the ADLS_DELTA_INGESTION_DETAILS row of" in row["TGT_ADLS_PATH"][2]
        assert row["SOURCE_TYPE"][0] == "File"                    # the template constant
    assert not [f for f in _notes(gate) if f.startswith("iig_file_adls_mft:")]


# -- rule 5: header check -------------------------------------------------------------


def test_the_iig_v2_emitter_writes_the_template_headers_exactly(tmp_path):
    """Every sheet of the IIG workbook (and config_rows.xlsx) carries the
    template's headers — the same names, spelling and order, nothing extra."""
    config = _acfc()
    _spec, _gate, xlsx = _run(FRD, config, tmp_path)
    tpl = config.metadata.templates["iig_v2"]
    (iig,) = [p for p in xlsx.parent.glob("*_IIG.xlsx")]
    for path in (iig, xlsx):
        workbook = load_workbook(path, read_only=True)
        sheets = [s for s in workbook.sheetnames if not s.startswith("_")]
        assert sheets == list(tpl.tabs), path.name
        for sheet in sheets:
            first = next(workbook[sheet].iter_rows(min_row=1, max_row=1, values_only=True))
            assert [h for h in first if h is not None] == list(tpl.tabs[sheet].headers), (
                path.name, sheet)
        workbook.close()


def test_compare_headers_names_spelling_order_missing_and_extra():
    from test_iig_diff_sheet_alias import iig_diff

    expected = ["GROUP_ID", "OBJECT_ID", "DOMAIN", "SUBDOMAIN", "SOURCE"]
    assert iig_diff.compare_headers(expected, list(expected))["ok"]
    r = iig_diff.compare_headers(expected, ["GROUP_ID", "Object_Id", "SUBDOMAIN", "DOMAIN",
                                            "NEW_COL"])
    assert r["spelling"] == [{"expected": "OBJECT_ID", "actual": "Object_Id"}]
    assert r["missing"] == ["SOURCE"] and r["extra"] == ["NEW_COL"]
    assert r["order"] == {"position": 3, "expected": "DOMAIN", "actual": "SUBDOMAIN"}
    assert not r["ok"]


def test_the_diff_reports_header_issues_first_and_in_the_scrubbed_export(tmp_path, capsys):
    """An agent workbook with a misspelled, a moved and a missing header against
    the template and the golden: a HEADERS section at the top of the console,
    score.json ``headers``, and a ``## Headers`` section first in sheets.md."""
    import json

    from test_iig_diff_sheet_alias import _book, iig_diff

    heads = iig_diff.template_headers()["iig_v2"]
    adls = list(heads[ADLS])
    bad = [("Src_File_Name" if h == "SRC_FILE_NAME" else h) for h in adls if h != "LOB"]
    bad[3], bad[4] = bad[4], bad[3]
    golden = _book(tmp_path / "golden.xlsx", {ADLS: [adls, [1] * len(adls)]})
    sheets = {name: [list(h)] for name, h in heads.items()}
    sheets[ADLS] = [bad, [1] * len(bad)]
    agent = _book(tmp_path / "run" / "f" / "f_IIG.xlsx", sheets)
    (tmp_path / "run" / "CODEGEN_BUILD.json").write_text(json.dumps(
        {"sha": "abc1234", "line": "codegen 0.0.test"}), encoding="utf-8")
    out = tmp_path / "out"
    assert iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out", str(out),
                          "--export-scrubbed", str(tmp_path / "export")]) in (0, 2)
    printed = capsys.readouterr().out
    report = json.loads((out / "score.json").read_text(encoding="utf-8"))["headers"]
    assert report["template"] == "iig_v2"
    for side in ("agent_vs_template", "agent_vs_golden"):
        r = report[side][ADLS]
        assert r["spelling"] == [{"expected": "SRC_FILE_NAME", "actual": "Src_File_Name"}]
        assert r["missing"] == ["LOB"] and r["order"]["position"] == 4
    assert all(r["ok"] for s, r in report["agent_vs_template"].items() if s != ADLS)
    lines = printed.splitlines()
    first = next(i for i, ln in enumerate(lines) if ln.startswith("HEADERS"))
    assert first < next(i for i, ln in enumerate(lines) if ln.startswith(f"{ADLS}:"))
    assert f"  {ADLS} vs template: spelling Src_File_Name (expected SRC_FILE_NAME)" in printed
    text = (tmp_path / "export" / "sheets.md").read_text(encoding="utf-8")
    assert text.index("## Headers") < text.index("| sheet |")
    assert "missing LOB" in text


# -- the email status set: a run-level input, default all four --------------------------


def test_the_email_status_set_defaults_to_all_four_and_an_answer_trims_it(tmp_path):
    """The corpus writes 4 / 2 / 1 statuses per pipeline (293 / 56 / 256): all four by
    default, a run-level INPUT_NEEDED run.email_statuses; an answer trims the rows."""
    from codegen import cli
    from test_derivations import _scoped

    spec, gate, xlsx = _run(FRD, _acfc(), tmp_path / "base")
    rows = _rows(xlsx, "EMAIL_TEMPLATE_CONFIG")
    assert [r["STATUS"][0] for r in rows] == ["FilesNotReceived", "New Files to Process",
                                              "Success", "Failed"]
    note = next(f for f in _notes(gate) if f.startswith("iig_owed_run:EMAIL_TEMPLATE_CONFIG"))
    assert "written with the default 'all four'" in note
    assert "INPUT_NEEDED run.email_statuses" in note
    config = _scoped(_acfc(), tmp_path)
    gate = cli._generate_feed(spec, config, dry_run=True, skip_tests=True,
                              output_mode="framework", conventions_profile="acfc_prx",
                              iig_template="iig_v2",
                              faq_answers={"email_statuses": "success; FAILED"})
    trimmed = tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"
    assert [r["STATUS"][0] for r in _rows(trimmed, "EMAIL_TEMPLATE_CONFIG")] == [
        "Success", "Failed"]
    assert any(f.startswith("iig_email_statuses:EMAIL_TEMPLATE_CONFIG.STATUS — the status "
                            "set answered: Success, Failed") for f in _notes(gate))


def test_the_diff_reports_an_extra_status_row_as_status_not_in_golden(tmp_path):
    """The CAQH golden writes 2 statuses, the agent all four: the two others are
    'status not in golden' — never extra-in-agent, never scored."""
    import json

    from test_iig_diff_sheet_alias import _book, iig_diff

    head = ["TEMPLATE_ID", "TEMPLATE_NAME", "PROCESS_NAME", "STATUS", "SUBJECT"]
    golden = _book(tmp_path / "golden.xlsx", {"EMAIL_TEMPLATE_CONFIG": [
        head, [1, "syn", "syn", "Success", "Load Completed"],
        [2, "syn", "syn", "Failed", "Load Failed"]]})
    agent = _book(tmp_path / "run" / "f" / "f_IIG.xlsx", {"EMAIL_TEMPLATE_CONFIG": [
        head, *[[None, "syn", "syn", s, subject] for s, subject in (
            ("FilesNotReceived", "File Not Received"), ("New Files to Process", "File Received"),
            ("Success", "Load Completed"), ("Failed", "Load Failed"))]]})
    (tmp_path / "run" / "CODEGEN_BUILD.json").write_text(json.dumps(
        {"sha": "abc1234", "line": "codegen 0.0.test"}), encoding="utf-8")
    payload = iig_diff.run_pair(golden, agent, tmp_path / "out", iig_diff.REPO_ROOT / "tools"
                                / "iig_keys.yaml")
    s = payload["sheets"]["EMAIL_TEMPLATE_CONFIG"]
    assert s["rows"]["extra-in-agent"] == 0 and s["counts"]["extra-in-agent"] == 0
    assert s["status_not_in_golden_rows"] == 2 and s["unpaired"]["agent"] == 0
    assert s["counts"]["status-not-in-golden"] > 0 and s["counts"]["mismatch"] == 0
    assert payload["totals"]["status_not_in_golden_rows"] == 2
    assert any("status not in golden: 2" in w for w in payload["warnings"])
