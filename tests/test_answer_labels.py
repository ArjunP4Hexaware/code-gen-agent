"""QUESTION / UNRESOLVED are reserved for answers OWED; everything else is NOTE.

A QUESTION or UNRESOLVED line is printed only when the run cannot complete a
feed without an answers.yaml entry — the ACFC harness records every such key
(its ``_NEEDED_KEY_RE`` scans stdout at the end of every pair) and marks the
pair NEEDS_ANSWERS. Informational items use the same padded form with the
label NOTE, which that regex does not match:

* STTM roles — UNRESOLVED only for a REQUIRED role; an optional role the
  layout could not place is a NOTE (it reads as empty, nothing stops);
* VDD roles — NOTE (VDD gaps are gate flags; extract-vdd never exits 3);
* FRD fields — owed only for a field the run cannot proceed without (format,
  stage load strategy, LOBs, file patterns) that the pair-resolved contract
  still lacks; any other unread field, and every field extract-frd reports on
  its own (the STTM / VDD may still supply it), is a NOTE;
* gap questions (choice / layer / text, byte widths) — QUESTION; the VDD
  pairing — NOTE (a run proceeds without a VDD).

The clean-pair test runs the CLI chain on pair 1 (layout, extract-frd,
extract-sttm, generate) and pair 4 (layout, extract-sttm, generate — pair 4's
FRD is a contract JSON, so extract-frd, which reads a .docx, does not apply)
and asserts not one QUESTION / UNRESOLVED line.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli
from codegen.extract import UnresolvedLayoutError, extract_contract
from codegen.layout.discover import discover
from codegen.layout.profile import UnresolvedRole, is_required_role
from test_harness_answer_lines import _NEEDED_KEY_RE

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
DATE = "2026-01-01"


def _owed_lines(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if _NEEDED_KEY_RE.match(ln)]


# ------------------------------------------------------------ the classification


@pytest.mark.parametrize("key,owed", [
    ("MAPPING-X/stage/schema", True),          # required
    ("MAPPING-X/stage/column", True),
    ("MAPPING-X/source/field_name", True),
    ("MAPPING-X/source/pii", False),           # optional
    ("MAPPING-X/rules/primary_key", False),
    ("MAPPING-X/stage/catalog", False),        # the catalog chain ends in a default
    ("MAPPING-X/source/pii|description", False),       # ambiguous between optionals
    ("MAPPING-X/stage/table|transformation", True),    # ambiguous, one required
    ("Sheet A (x)/stage/schema", True),        # a sheet name with spaces
])
def test_sttm_roles(key, owed):
    assert cli._owed_key("sttm", key) is owed


def test_vdd_roles_are_never_owed():
    assert cli._owed_key("vdd", "FEED_1 Fields/fields/length") is False


def _frd_contract(**fields):
    from types import SimpleNamespace

    from codegen.contracts.frd import TargetSpec

    feed = SimpleNamespace(file_format=fields.get("file_format"), lobs=fields.get("lobs", []),
                           file_name_patterns=fields.get("patterns", []),
                           stage_target=TargetSpec(catalog=None, schema=None, tables=[],
                                                   load_strategy=fields.get("strategy")),
                           domain=None)
    return SimpleNamespace(feeds=[feed])


def test_frd_fields_are_owed_only_while_the_contract_lacks_a_required_one():
    empty = _frd_contract()
    filled = _frd_contract(file_format="Delimited", lobs=["ALL"], strategy="Append",
                           patterns=["x_*.csv"])
    for field in ("file_format", "stage_target.load_strategy", "lobs", "file_name_patterns"):
        assert cli._owed_key("frd", f"feeds[0].{field}", "role", empty) is True, field
        assert cli._owed_key("frd", f"feeds[0].{field}", "role", filled) is False, field
    assert cli._owed_key("frd", "feeds[0].domain", "role", empty) is False   # optional
    assert cli._owed_key("frd", "feeds[0].file_format", "role", None) is False  # extract-frd alone


def test_gap_questions_are_owed_except_the_vdd_pairing():
    assert cli._owed_key("frd", "feeds[0].file_format", "choice") is True
    assert cli._owed_key("frd", "feeds[0].load_strategy", "layer") is True
    assert cli._owed_key("sttm", "feeds[0].fields[Amount (01)].width", "text") is True
    assert cli._owed_key("pair", "pair.frd", "choice") is True
    assert cli._owed_key("pair", "pair.vdd", "choice") is False


def test_the_note_label_is_padded_the_same_and_invisible_to_the_harness():
    line = cli.answer_line("NOTE", "MAPPING-X/source/pii", "optional")
    assert line.startswith("NOTE" + " " * 11 + "MAPPING-X/source/pii — ")
    assert _NEEDED_KEY_RE.match(line) is None


def test_require_complete_stops_on_required_roles_only(config, tmp_path):
    from codegen.extract.frd_docx import contract_to_json
    from codegen.layout.resolve import resolve_pair

    sttm = SHAPES / "sttm" / "pair_1_family_a.xlsx"
    pair = resolve_pair(sttm, SHAPES / "frd" / "f1_pair_1.docx", config, provider=None,
                        cache_dirs=[], generated_date=DATE)
    frd = tmp_path / "frd.json"
    frd.write_text(contract_to_json(pair.frd_contract), encoding="utf-8")
    profile = discover(sttm, config.extractor).profile
    sheet = profile.mapping_sheets[0].name
    optional = profile.model_copy(update={"unresolved": [UnresolvedRole(
        sheet=sheet, layer="source", role="pii", reason="no PII header")]})
    assert not is_required_role("source", "pii")
    contract = extract_contract(sttm, frd, config, generated_date=DATE, layout=optional,
                                require_complete=True)
    assert contract.feeds                                   # an optional role never stops it
    required = optional.model_copy(update={"unresolved": [UnresolvedRole(
        sheet=sheet, layer="stage", role="schema", reason="no schema header")]})
    with pytest.raises(UnresolvedLayoutError) as held:
        extract_contract(sttm, frd, config, generated_date=DATE, layout=required,
                         require_complete=True)
    assert [f"{u.layer}/{u.role}" for u in held.value.unresolved] == ["stage/schema"]


def test_extract_frd_reports_unread_fields_as_notes(monkeypatch, tmp_path, capsys):
    from codegen.extract import frd_docx
    from codegen.layout.frd_profile import FrdUnresolved

    real = frd_docx.extract_frd_contract

    def with_an_unread_field(*args, **kwargs):
        contract, profile = real(*args, **kwargs)
        return contract, profile.model_copy(update={"unresolved": [FrdUnresolved(
            field="feeds[0].file_format", reason="no 'Object/data Format' label")]})

    monkeypatch.setattr(frd_docx, "extract_frd_contract", with_an_unread_field)
    capsys.readouterr()
    assert cli.main(["extract-frd", "--docx", str(SHAPES / "frd" / "f1_pair_1.docx"),
                     "--out", str(tmp_path / "frd.json")]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert _owed_lines(out) == []
    assert "NOTE           feeds[0].file_format — no 'Object/data Format' label" in out


# ------------------------------------------------------------ clean pairs


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    (tmp_path / "state").mkdir()
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(REPO)
    return tmp_path


def _run(capsys, argv: list[str]) -> tuple[int, str]:
    capsys.readouterr()
    rc = cli.main(argv)
    return rc, capsys.readouterr().out


GENERATE = ["--output-mode", "framework", "--profile", "acfc_prx", "--iig-template", "iig_v2",
            "--skip-tests", "--dry-run"]


def test_a_clean_pair_1_prints_no_answer_lines(clean_env, monkeypatch, capsys):
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(SHAPES / "pair_1" / "config_overlay.yaml"))
    sttm, docx = SHAPES / "sttm" / "pair_1_family_a.xlsx", SHAPES / "frd" / "f1_pair_1.docx"
    frd, layout, contract = (clean_env / n for n in ("frd.json", "l.json", "sttm.json"))
    outputs = [
        _run(capsys, ["layout", "--workbook", str(sttm), "--frd", str(docx), "--dry-run",
                      "--no-cache", "--profile-out", str(layout), "--frd-contract-out", str(frd),
                      "--require-complete"]),
        _run(capsys, ["extract-frd", "--docx", str(docx), "--out", str(clean_env / "x.json")]),
        _run(capsys, ["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd),
                      "--out", str(contract), "--layout", str(layout),
                      "--generated-date", DATE]),
        _run(capsys, ["generate", "--frd-contract", str(frd), "--sttm-contract", str(contract),
                      *GENERATE]),
    ]
    for rc, out in outputs:
        assert rc == cli.EXIT_OK, out
        assert _owed_lines(out) == [], _owed_lines(out)


def test_a_clean_pair_4_prints_no_answer_lines(clean_env, monkeypatch, capsys):
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(SHAPES / "pair_4" / "config_overlay.yaml"))
    sttm = SHAPES / "pair_4" / "sttm_nb_cob_report.xlsx"
    frd = SHAPES / "pair_4" / "frd_nb_cob_report.contract.json"   # a contract: no extract-frd
    layout, contract = clean_env / "l.json", clean_env / "sttm.json"
    outputs = [
        _run(capsys, ["layout", "--workbook", str(sttm), "--dry-run", "--no-cache",
                      "--profile-out", str(layout), "--require-complete"]),
        _run(capsys, ["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd),
                      "--out", str(contract), "--layout", str(layout),
                      "--generated-date", DATE]),
        _run(capsys, ["generate", "--frd-contract", str(frd), "--sttm-contract", str(contract),
                      *GENERATE]),
    ]
    for rc, out in outputs:
        assert rc == cli.EXIT_OK, out
        assert _owed_lines(out) == [], _owed_lines(out)
