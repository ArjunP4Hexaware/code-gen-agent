"""Pairing by NAME: a token key, not a three-token prefix (2026-10-13).

The real Pyx pair below did not auto-pair. The App (``local_frd_candidates``)
and ``codegen pair`` took a .docx for an FRD only when its name STARTED with
"frd" — this one ENDS with it, so it was never a candidate — and the name rule
compared only the first three content tokens, which every file of the vendor's
family shares (a sibling feed made it ambiguous, a different one could have
paired WRONG). Names are now one token key (lowercased, split on whitespace _ -
., role tokens dropped wherever they sit): an exact key pairs; otherwise a
token-set overlap at or above ``inputs.pairing.name_fuzzy_threshold`` pairs
with a NOTE; anything below is a QUESTION, never a silent pair. A pairs
override file wins over every automatic rule.
"""

from __future__ import annotations

import io
import logging
import shutil
import time
from pathlib import Path

import pytest

from codegen.cli import main as cli_main
from codegen.config import load_config
from codegen.demo_sources import (
    auto_pair_frd,
    auto_pair_vdd,
    document_roles,
    pairing_key,
    suggest_pairs,
)
from codegen.pairing import PairOverridesError, load_pair_overrides, pair_by_content
from test_frd_pairing import MIDS_FRD, MIDS_MAP, MIDS_STTM

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
SHAPES = REPO / "fixtures" / "acfc_shapes"

# The real pair (client file names; the space after "Pyx_" is in the original).
PYX_STTM = "STTM_Pyx_Care_Management_Data_MI_DSNP.xlsx"
PYX_FRD = "Pyx_ Care Management Data MI DSNP_FRD.docx"
PYX_VDD = "Pyx_ Care Management Data MI DSNP_VDD.xlsx"
# Another feed of the same vendor: shares the leading token only.
ROSTER_FRD = "Pyx_ Provider Roster_FRD.docx"
# SYNTHETIC sibling feed: one token different from the real pair.
SIBLING_FRD = "Pyx_ Care Management Data ZZ DSNP_FRD.docx"


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG)


def _xlsx(path: Path) -> Path:
    from openpyxl import Workbook

    buf = io.BytesIO()
    Workbook().save(buf)
    path.write_bytes(buf.getvalue())
    return path


def _unreadable(path: Path) -> Path:
    """A document no reader opens: it pairs on its NAME alone."""
    path.write_bytes(b"not a document")
    return path


# -- the key ------------------------------------------------------------------------


def test_the_key_drops_role_tokens_wherever_they_sit():
    key = "pyx care management data mi dsnp"
    assert pairing_key(PYX_STTM) == pairing_key(PYX_FRD) == pairing_key(PYX_VDD) == key
    assert document_roles(PYX_FRD) == {"frd"}           # a suffix, not a prefix
    assert document_roles(PYX_STTM) == {"sttm"}
    assert document_roles(PYX_VDD) == {"vdd"}
    assert document_roles(MIDS_FRD) == {"frd"}
    # A ".contract.json" double extension is not content; an "iig" token is a role.
    assert pairing_key("FRD_demo_cv_golden.contract.json") == "demo cv golden"
    assert pairing_key("demo_cv_golden_IIG.xlsx") == "demo cv golden"
    # Upload prefix / copy suffix stay stripped, as before.
    assert pairing_key(f"1787853350398_STTM_Pyx_Care_Management_Data_MI_DSNP ({2}).xlsx") == key


# -- auto pairing by name -------------------------------------------------------------


def test_the_pyx_frd_pairs_with_its_sttm_by_key():
    assert auto_pair_frd(PYX_STTM, [PYX_FRD]) == (PYX_FRD, "name_key")
    # Other feeds of the same vendor (and the MIDS FRD) do not get in the way.
    assert auto_pair_frd(PYX_STTM, [ROSTER_FRD, SIBLING_FRD, MIDS_FRD, PYX_FRD]) == (
        PYX_FRD, "name_key")
    assert suggest_pairs([PYX_STTM], [ROSTER_FRD, PYX_FRD]) == {PYX_STTM: PYX_FRD}


def test_the_pyx_vdd_attaches_to_the_same_pair():
    assert auto_pair_vdd(PYX_STTM, [PYX_STTM, PYX_VDD, "other.xlsx"]) == (PYX_VDD, "name_key")


def test_a_shared_prefix_never_pairs():
    """A different feed of the same vendor shares "pyx" (and a sibling five of
    six tokens): below the threshold, never paired — the old three-token prefix
    would have paired the sibling had it been the only candidate."""
    assert auto_pair_frd(PYX_STTM, [ROSTER_FRD]) is None
    assert auto_pair_frd(PYX_STTM, [SIBLING_FRD]) is None
    assert suggest_pairs([PYX_STTM], [ROSTER_FRD]) == {}
    assert suggest_pairs([PYX_STTM], [SIBLING_FRD]) == {}


def test_the_mids_names_still_pair():
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD], explicit_map=MIDS_MAP) == (MIDS_FRD, "pairing_map")
    # Without the map: the two titles differ in two word endings only — the same
    # words by stem, so the overlap is complete (a NOTE'd fuzzy pair, not a key).
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD]) == (MIDS_FRD, "name_fuzzy")
    assert auto_pair_frd(MIDS_STTM, [PYX_FRD, ROSTER_FRD, MIDS_FRD]) == (MIDS_FRD, "name_fuzzy")
    assert auto_pair_frd(PYX_STTM, [MIDS_FRD, PYX_FRD]) == (PYX_FRD, "name_key")
    # Two near-identical candidates above the threshold: ambiguous, nothing pairs.
    assert auto_pair_frd(MIDS_STTM, [MIDS_FRD, MIDS_FRD + " v2"]) is None


# -- the stem rule: a WHOLE word that prefixes the other, never a shared beginning --------


def test_the_stem_rule_is_a_whole_word_prefix_not_a_common_prefix():
    from codegen.demo_sources import _same_word, name_overlap

    assert _same_word("care", "career") and _same_word("manage", "management")
    assert not _same_word("medicare", "medicaid")          # share "medica" — not a prefix
    assert not _same_word("mi", "mids")                     # short words compare exactly
    # The MIDS STTM retitled for another program: one word differs by its
    # ending only after a common beginning — never a stem match.
    frd = MIDS_FRD + ".docx"
    sttm = MIDS_STTM.replace("Medicare", "Medicaid")
    score, stems = name_overlap(sttm, frd)
    assert score == pytest.approx(4 / 6)                    # medicaid ≠ medicare
    assert auto_pair_frd(sttm, [frd]) is None


def test_care_vs_career_pairs_only_if_everything_else_clears_the_threshold(config):
    """"care" IS a whole-word prefix of "career", so it counts as one word —
    the rest of the name must still carry the overlap. Built at 6/8 = 0.75:
    loosen ``name_fuzzy_threshold`` to 0.75 and this test fails."""
    from codegen.demo_sources import name_overlap

    sttm = "STTM_Pyx_Care_Management_Data_MI_DSNP_Monthly.xlsx"
    frd = "Pyx_ Career Management Data MI DSNP Weekly_FRD.docx"     # SYNTHETIC
    score, stems = name_overlap(sttm, frd)
    assert score == pytest.approx(0.75) and stems == [("care", "career")]
    threshold = config.inputs.pairing.name_fuzzy_threshold
    assert auto_pair_frd(sttm, [frd], threshold=threshold) is None
    assert auto_pair_frd(sttm, [frd], threshold=0.75) == (frd, "name_fuzzy")   # the edge


def test_a_stem_matched_mids_pair_names_the_words(tmp_path, config, caplog):
    from codegen.demo_sources import name_overlap

    sttm = _unreadable(tmp_path / MIDS_STTM)
    frd = MIDS_FRD + ".docx"
    frds = {frd: _unreadable(tmp_path / frd)}
    stems = name_overlap(sttm.name, frd)[1]
    assert len(stems) == 2 and all(b.startswith(a) or a.startswith(b) for a, b in stems)
    with caplog.at_level(logging.INFO, logger="codegen.pairing"):
        decision = pair_by_content("frd", sttm, frds, config, REPO)
    assert (decision.chosen, decision.rule) == (frd, "name_fuzzy")
    for a, b in stems:                                      # the NOTE names both words
        assert f"{a!r} ~ {b!r}" in decision.reason and f"{a!r} ~ {b!r}" in caplog.text
    assert "NOTE" in caplog.text
    # The config pairing map stays the explicit override and wins when present.
    mapped = pair_by_content("frd", sttm, frds, config, REPO,
                             explicit_map={document_stem_of(sttm.name): document_stem_of(frd)})
    assert mapped.rule == "pairing_map"


def document_stem_of(name: str) -> str:
    from codegen.demo_sources import document_stem

    return document_stem(name)


# -- pair_by_content: names alone (nothing readable) ------------------------------------


def test_names_alone_pair_by_key(tmp_path, config, caplog):
    sttm = _unreadable(tmp_path / PYX_STTM)
    frds = {n: _unreadable(tmp_path / n) for n in (PYX_FRD, ROSTER_FRD, SIBLING_FRD)}
    with caplog.at_level(logging.INFO, logger="codegen.pairing"):
        decision = pair_by_content("frd", sttm, frds, config, REPO)
    assert (decision.chosen, decision.rule) == (PYX_FRD, "name_key"), decision.reason
    assert "paired by key" in caplog.text and PYX_FRD in caplog.text


def test_a_fuzzy_pair_says_which_files_and_why(tmp_path, config, caplog):
    sttm = _unreadable(tmp_path / "STTM_Pyx_Care_Management_Data_MI_DSNP_v2.xlsx")
    frds = {n: _unreadable(tmp_path / n) for n in (PYX_FRD, ROSTER_FRD)}
    with caplog.at_level(logging.INFO, logger="codegen.pairing"):
        decision = pair_by_content("frd", sttm, frds, config, REPO)
    assert (decision.chosen, decision.rule) == (PYX_FRD, "name_fuzzy"), decision.reason
    assert "paired by fuzzy" in decision.reason
    note = next(r.getMessage() for r in caplog.records if "paired by fuzzy" in r.getMessage())
    assert sttm.name in note and PYX_FRD in note and "0.86" in note


def test_below_the_threshold_is_a_question_not_a_pair(tmp_path, config):
    sttm = _unreadable(tmp_path / PYX_STTM)
    frds = {n: _unreadable(tmp_path / n) for n in (SIBLING_FRD, ROSTER_FRD)}
    decision = pair_by_content("frd", sttm, frds, config, REPO)
    assert decision.chosen is None and decision.ambiguous, decision.reason
    question = decision.question()
    assert question["key"] == "pair.frd"
    assert [c["value"] for c in question["candidates"]][0] == SIBLING_FRD   # closest first
    assert "threshold" in decision.reason


# -- the override file -----------------------------------------------------------------


def _overrides(tmp_path: Path, body: str, name: str = "pairing_overrides.yaml") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_an_override_wins_over_every_automatic_rule(tmp_path, config, caplog):
    renamed = "vendor_upload_frd.docx"                # a name no rule would pair
    overrides = load_pair_overrides(_overrides(tmp_path, (
        "pairs:\n"
        f"  - sttm: {PYX_STTM}\n"
        f"    frd: {renamed}\n"
        f"    vdd: \"{PYX_VDD}\"\n")))
    assert overrides.lookup(PYX_STTM, "frd") == renamed
    assert overrides.lookup(PYX_STTM.upper(), "vdd") == PYX_VDD      # canonical names
    assert overrides.lookup(MIDS_STTM, "frd") is None
    sttm = _unreadable(tmp_path / PYX_STTM)
    frds = {n: _unreadable(tmp_path / n) for n in (PYX_FRD, renamed)}
    with caplog.at_level(logging.INFO, logger="codegen.pairing"):
        decision = pair_by_content("frd", sttm, frds, config, REPO, overrides=overrides)
    assert (decision.chosen, decision.rule) == (renamed, "override")
    assert "paired by override" in caplog.text


def test_an_override_naming_a_missing_document_asks(tmp_path, config):
    overrides = load_pair_overrides(_overrides(tmp_path, (
        f'{{"pairs": [{{"sttm": "{PYX_STTM}", "frd": "gone_FRD.docx"}}]}}'), "pairs.json"))
    sttm = _unreadable(tmp_path / PYX_STTM)
    frds = {PYX_FRD: _unreadable(tmp_path / PYX_FRD)}
    decision = pair_by_content("frd", sttm, frds, config, REPO, overrides=overrides)
    assert decision.chosen is None and decision.ambiguous
    assert "gone_FRD.docx" in decision.reason


@pytest.mark.parametrize("body", [
    "pairs:\n  - frd: a_FRD.docx\n",                              # no sttm
    "pairs:\n  - sttm: a.xlsx\n",                                 # nothing paired with it
    "pairs:\n  - sttm: a.xlsx\n    frd: b.docx\n    fdr: c.docx\n",  # unknown key
    "pairs:\n  - {sttm: a.xlsx, frd: b.docx}\n  - {sttm: A.xlsx, frd: c.docx}\n",  # twice
])
def test_a_malformed_override_file_is_loud(tmp_path, body):
    with pytest.raises(PairOverridesError):
        load_pair_overrides(_overrides(tmp_path, body))


# -- codegen pair ------------------------------------------------------------------------


def _pair_folder(tmp_path: Path, *frd_names: str, vdd: bool = True) -> Path:
    folder = tmp_path / "pair"
    folder.mkdir()
    _xlsx(folder / PYX_STTM)
    for name in frd_names:
        _unreadable(folder / name)
    if vdd:
        _xlsx(folder / PYX_VDD)
    return folder


def test_cli_pair_pairs_the_pyx_documents(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = _pair_folder(tmp_path, PYX_FRD, ROSTER_FRD)
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert f"frd {PYX_FRD} — rule name_key" in out, out
    assert f"vdd {PYX_VDD} — rule name_key" in out, out


def test_cli_pair_below_the_threshold_exits_3_with_a_question(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = _pair_folder(tmp_path, SIBLING_FRD, vdd=False)
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM)])
    out = capsys.readouterr().out
    assert code == 3, out
    assert any(line.startswith("QUESTION") and "pair.frd" in line for line in out.splitlines())


def test_cli_pair_reads_the_override_file(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = _pair_folder(tmp_path, PYX_FRD, "vendor_upload_frd.docx", vdd=False)
    # Found next to the STTM without a flag …
    _overrides(folder, f"pairs:\n  - sttm: {PYX_STTM}\n    frd: vendor_upload_frd.docx\n")
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "frd vendor_upload_frd.docx — rule override" in out, out
    # … and named explicitly with --pairs-file (wins over the folder's file).
    explicit = _overrides(tmp_path, f"pairs:\n  - sttm: {PYX_STTM}\n    frd: \"{PYX_FRD}\"\n",
                          "mine.yaml")
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM),
                     "--pairs-file", str(explicit)])
    out = capsys.readouterr().out
    assert code == 0 and f"frd {PYX_FRD} — rule override" in out, out


# -- the App -----------------------------------------------------------------------------


@pytest.fixture
def runner(monkeypatch, tmp_path):
    """Local roles on scratch directories; an extra input root holding the Pyx
    pair (the pair-1 fixture documents under the real file names)."""
    pytest.importorskip("fastapi")
    from ui.backend import stores as ui_stores
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    from codegen.storage import open_storage

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    pairs = tmp_path / "pairs"
    pairs.mkdir()
    shutil.copyfile(SHAPES / "sttm" / "pair_1_family_a.xlsx", pairs / PYX_STTM)
    shutil.copyfile(SHAPES / "frd" / "f1_pair_1.docx", pairs / PYX_FRD)
    for name in ("inputs", "state"):
        (tmp_path / name).mkdir()
    env = {"CODEGEN_STORAGE_INPUTS": f"local:{(tmp_path / 'inputs').as_posix()}",
           "CODEGEN_STORAGE_STATE": f"local:{(tmp_path / 'state').as_posix()}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
           "CODEGEN_EXTRA_INPUT_DIRS": f"local:{pairs.as_posix()}"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env))
    ui_stores.reset_stores()
    runner = DemoRunner(GenerationStore(str(CONFIG)), work=lambda: None)
    yield runner, pairs
    runner._index.wait_idle(30.0)
    ui_stores.reset_stores()


def test_the_app_offers_and_pairs_the_pyx_frd(runner):
    runner, _pairs = runner
    assert PYX_FRD in runner.local_frd_candidates()
    plan = runner._plan_pair("frd", PYX_STTM, time.monotonic() + 60.0)
    assert plan["decision"].chosen == PYX_FRD, plan["outcome"]


def test_the_app_reads_an_override_file_in_the_input_folder(runner):
    runner, pairs = runner
    # Two FRDs with the SAME content: the documents cannot decide; the file does.
    other = "Pyx_ Care Management Data MI DSNP_FRD_old.docx"
    shutil.copyfile(pairs / PYX_FRD, pairs / other)
    _overrides(pairs, f"pairs:\n  - sttm: {PYX_STTM}\n    frd: \"{other}\"\n")
    runner.refresh_inputs()
    plan = runner._plan_pair("frd", PYX_STTM, time.monotonic() + 60.0)
    assert (plan["decision"].chosen, plan["decision"].rule) == (other, "override"), plan["outcome"]
    assert "pairing_overrides.yaml" in plan["decision"].reason


# -- roles: a role token anywhere in the name (2026-10-13, second brief) ---------------
# The App's pairing diagnostic listed only "FRD_…" files as FRD candidates (a
# PREFIX rule), and a validation golden ("…_IIG.xlsx", unclassified by content)
# was attached as the VDD because it was the only workbook left in the folder.

IIG_GOLDEN = "25_Pyx_Health_IIG.xlsx"
STRAY = "notes.xlsx"


def test_roles_come_from_a_token_anywhere():
    from codegen.demo_sources import classify_document_name

    assert classify_document_name(PYX_FRD).role == "frd"
    assert classify_document_name(PYX_STTM).role == "sttm"
    assert classify_document_name(PYX_VDD).role == "vdd"
    assert classify_document_name(IIG_GOLDEN).role == "iig"
    assert classify_document_name(STRAY).role == "unclassified"
    # The existing SD / MIDS, CAQH and CV names classify as before.
    from test_frd_pairing import CAQH_FRD, CAQH_STTM

    for name, role in ((MIDS_STTM, "sttm"), (MIDS_FRD + ".docx", "frd"),
                       (CAQH_STTM, "sttm"), (CAQH_FRD + ".docx", "frd"),
                       ("demo_sttm_cv_golden.xlsx", "sttm"),
                       ("FRD_demo_cv_golden.contract.json", "frd"),
                       ("VDD_demo_cv_golden.xlsx", "vdd")):
        assert classify_document_name(name).role == role, name


def test_two_role_tokens_fall_back_to_the_prefix_with_a_note(caplog):
    from codegen.demo_sources import classify_document_name

    with caplog.at_level(logging.INFO, logger="codegen.pairing"):
        verdict = classify_document_name("STTM_feed_x_FRD_review.xlsx")
    assert verdict.role == "sttm" and "prefix" in verdict.rule
    assert "STTM_feed_x_FRD_review.xlsx" in caplog.text and "NOTE" in caplog.text


def test_cli_pair_never_attaches_an_iig_or_an_unclassified_workbook(tmp_path, capsys,
                                                                     monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = _pair_folder(tmp_path, PYX_FRD, vdd=False)
    _xlsx(folder / IIG_GOLDEN)
    _xlsx(folder / STRAY)
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert f"frd {PYX_FRD} — rule name_key" in out, out
    attached = [line for line in out.splitlines()
                if line.startswith(("PAIRED", "CANDIDATE"))
                and (IIG_GOLDEN in line or STRAY in line)]
    assert not attached, out
    assert any(line.startswith("NONE") and "vdd" in line and "no VDD" in line
               for line in out.splitlines()), out
    # Every file of the folder is listed with its role and the rule behind it.
    roles = [line for line in out.splitlines() if line.startswith("ROLE")]
    assert any(f"{IIG_GOLDEN} — iig:" in line for line in roles), out
    assert any(f"{STRAY} — unclassified:" in line for line in roles), out
    assert any(f"{PYX_FRD} — frd:" in line for line in roles), out


def test_an_override_may_still_attach_a_workbook_without_a_vdd_token(tmp_path, capsys,
                                                                       monkeypatch):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    folder = _pair_folder(tmp_path, PYX_FRD, vdd=False)
    _xlsx(folder / "pyx_dictionary.xlsx")
    _overrides(folder, f"pairs:\n  - sttm: {PYX_STTM}\n    vdd: pyx_dictionary.xlsx\n")
    code = cli_main(["pair", "--config", str(CONFIG), "--sttm", str(folder / PYX_STTM)])
    out = capsys.readouterr().out
    assert code == 0 and "vdd pyx_dictionary.xlsx — rule override" in out, out


@pytest.fixture
def nested_runner(monkeypatch, tmp_path):
    """The App with the Pyx documents in a PAIR FOLDER (…/pyx/), where the
    same-folder rescue applies: the IIG golden and a stray workbook beside
    them, and no dictionary."""
    pytest.importorskip("fastapi")
    from ui.backend import stores as ui_stores
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    from codegen.storage import open_storage

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    pairs = tmp_path / "pairs"
    folder = pairs / "pyx"
    folder.mkdir(parents=True)
    shutil.copyfile(SHAPES / "sttm" / "pair_1_family_a.xlsx", folder / PYX_STTM)
    shutil.copyfile(SHAPES / "frd" / "f1_pair_1.docx", folder / PYX_FRD)
    # Even a workbook that READS as a dictionary is no VDD when it is an IIG.
    shutil.copyfile(SHAPES / "vdd" / "pair_1_v1_segments.xlsx", folder / IIG_GOLDEN)
    _xlsx(folder / STRAY)
    for name in ("inputs", "state"):
        (tmp_path / name).mkdir()
    env = {"CODEGEN_STORAGE_INPUTS": f"local:{(tmp_path / 'inputs').as_posix()}",
           "CODEGEN_STORAGE_STATE": f"local:{(tmp_path / 'state').as_posix()}",
           "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch"),
           "CODEGEN_EXTRA_INPUT_DIRS": f"local:{pairs.as_posix()}"}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env))
    ui_stores.reset_stores()
    runner = DemoRunner(GenerationStore(str(CONFIG)), work=lambda: None)
    yield runner
    runner._index.wait_idle(30.0)
    ui_stores.reset_stores()


def test_the_app_attaches_no_iig_and_lists_every_file_with_its_role(nested_runner):
    runner = nested_runner
    for doc in runner._workbook_catalog().documents((".xlsx",)):
        runner._index.lookup(doc)
    assert runner._index.wait_idle(60)
    plan = runner._plan_pair("vdd", PYX_STTM, time.monotonic() + 60.0)
    outcome = plan["outcome"]
    assert plan["decision"].chosen is None, outcome
    assert "no VDD" in outcome["reason"], outcome
    roles = {entry["name"]: entry for entry in outcome["folder_roles"]}
    assert set(roles) >= {PYX_STTM, PYX_FRD, IIG_GOLDEN, STRAY}, roles
    assert roles[IIG_GOLDEN]["role"] == "iig" and roles[IIG_GOLDEN]["rule"]
    assert roles[STRAY]["role"] == "unclassified"
    assert roles[PYX_FRD]["role"] == "frd"
    frd = runner._plan_pair("frd", PYX_STTM, time.monotonic() + 60.0)
    assert frd["decision"].chosen == PYX_FRD, frd["outcome"]


# -- end to end: the ACFC pair_11 folder, through local folders AND the workspace backend --
# The original symptom: the Pyx FRD never appeared as a candidate at all. The
# folder mirrors pair_11's listing byte for byte; a sibling folder holds three
# copies of the MIDS FRD and another vendor's FRD. If the Pyx FRD is missing
# from ``folder_roles`` the discovery / walk layer is dropping it — a different
# bug from the role rule, and these tests say so.

BFF_FRD = "FRD_BestFootForward.docx"
MIDS_COPIES = (MIDS_FRD + ".docx", MIDS_FRD + " - Copy.docx", MIDS_FRD + "_v2.docx")
SIBLINGS = (*MIDS_COPIES, BFF_FRD)


def _pair11_tree() -> dict[str, bytes]:
    """{folder/name: bytes}: real-shape fixture documents under the real names."""
    sttm = (SHAPES / "sttm" / "pair_1_family_a.xlsx").read_bytes()
    frd = (SHAPES / "frd" / "f1_pair_1.docx").read_bytes()
    golden = (SHAPES / "vdd" / "pair_1_v1_segments.xlsx").read_bytes()  # reads AS a dictionary
    others = [(SHAPES / "frd" / n).read_bytes()
              for n in ("f1_pair_2_variant.docx", "f2_pair_8.docx", "f1_pair_11_multi_file.docx",
                        "f1_pair_11_multi_file_catalog.docx")]
    tree = {f"pair_11/{PYX_FRD}": frd, f"pair_11/{PYX_STTM}": sttm,
            f"pair_11/{IIG_GOLDEN}": golden}
    tree.update({f"pair_mids/{name}": data for name, data in zip(SIBLINGS, others, strict=True)})
    return tree


def _assert_pair11(runner) -> None:
    for doc in runner._workbook_catalog().documents((".xlsx",)):
        runner._index.lookup(doc)
    assert runner._index.wait_idle(60)
    frd = runner._plan_pair("frd", PYX_STTM, time.monotonic() + 60.0)
    outcome = frd["outcome"]
    roles = {entry["name"]: entry for entry in outcome["folder_roles"]}
    # 1. the Pyx FRD is listed — as an FRD (else: the walk drops it; stop there)
    assert PYX_FRD in roles, f"discovery dropped the Pyx FRD: {sorted(roles)}"
    assert roles[PYX_FRD]["role"] == "frd", roles[PYX_FRD]
    # 2. it is the selected FRD, by exact key
    assert (frd["decision"].chosen, frd["decision"].rule) == (PYX_FRD, "name_key"), outcome
    # 3. the IIG is listed as an IIG and no VDD is attached
    assert roles[IIG_GOLDEN]["role"] == "iig", roles[IIG_GOLDEN]
    vdd = runner._plan_pair("vdd", PYX_STTM, time.monotonic() + 60.0)
    assert vdd["decision"].chosen is None, vdd["outcome"]
    assert "no VDD" in vdd["outcome"]["reason"] and IIG_GOLDEN in vdd["outcome"]["reason"]
    assert all(c["name"] != IIG_GOLDEN for c in vdd["outcome"]["candidates"])
    # 4. the sibling folder's FRDs are scored as non-candidates, not dropped
    considered = {entry["name"]: entry for entry in outcome["considered"]}
    for name in SIBLINGS:
        assert name in considered, (name, sorted(considered))
        entry = considered[name]
        assert entry["status"].startswith("not a candidate"), entry
        assert isinstance(entry["name_score"], float) and entry["name_score"] < 0.8, entry


def _runner_with(monkeypatch, tmp_path, env, client=None):
    pytest.importorskip("fastapi")
    from ui.backend import stores as ui_stores
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    from codegen.storage import open_storage

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    env = {**env, "CODEGEN_STORAGE_SCRATCH": str(tmp_path / "scratch")}
    monkeypatch.setattr(ui_stores, "open_storage",
                        lambda config, base: open_storage(config, base, env=env, client=client))
    ui_stores.reset_stores()
    return DemoRunner(GenerationStore(str(CONFIG)), work=lambda: None)


def test_pair_11_end_to_end_local_folders(monkeypatch, tmp_path):
    from ui.backend import stores as ui_stores

    pairs = tmp_path / "pairs"
    for rel, data in _pair11_tree().items():
        (pairs / rel).parent.mkdir(parents=True, exist_ok=True)
        (pairs / rel).write_bytes(data)
    for name in ("inputs", "state"):
        (tmp_path / name).mkdir()
    runner = _runner_with(monkeypatch, tmp_path, {
        "CODEGEN_STORAGE_INPUTS": f"local:{(tmp_path / 'inputs').as_posix()}",
        "CODEGEN_STORAGE_STATE": f"local:{(tmp_path / 'state').as_posix()}",
        "CODEGEN_EXTRA_INPUT_DIRS": f"local:{pairs.as_posix()}"})
    try:
        _assert_pair11(runner)
    finally:
        runner._index.wait_idle(30.0)
        ui_stores.reset_stores()


def test_pair_11_end_to_end_workspace_backend(monkeypatch, tmp_path):
    """The same four checks with every input on the (fake) Databricks
    workspace — the Workspace API listing / download path the App uses in ACFC."""
    from ui.backend import stores as ui_stores

    from storage_fakes import FakeWorkspaceClient

    shared = "/Users/u/shared"
    fake = FakeWorkspaceClient(workspace_root=shared)
    fake.ws.dirs.update({f"{shared}/inputs", f"{shared}/state", f"{shared}/pairs",
                         f"{shared}/pairs/pair_11", f"{shared}/pairs/pair_mids"})
    for rel, data in _pair11_tree().items():
        fake.ws.files[f"{shared}/pairs/{rel}"] = data
    runner = _runner_with(monkeypatch, tmp_path, {
        "CODEGEN_STORAGE_INPUTS": f"workspace:/Workspace{shared}/inputs",
        "CODEGEN_STORAGE_STATE": f"workspace:/Workspace{shared}/state",
        "CODEGEN_EXTRA_INPUT_DIRS": f"workspace:/Workspace{shared}/pairs"}, client=fake)
    try:
        _assert_pair11(runner)
        # The Pyx FRD was asked of the workspace under its exact name (space kept).
        asked = {path for _call, path in fake.ws.calls}
        assert f"{shared}/pairs/pair_11/{PYX_FRD}" in asked, sorted(asked)
    finally:
        runner._index.wait_idle(30.0)
        ui_stores.reset_stores()


@pytest.mark.parametrize("scheme", ["workspace", "volume"])
def test_a_space_bearing_name_round_trips_through_the_remote_backends(scheme):
    """No backend path builder mangles "Pyx_ Care" (no strip / split / quote on
    a segment; the SDK quotes the Files API URL and the Workspace API takes the
    path as a parameter)."""
    from codegen.storage import open_backend
    from storage_fakes import FakeWorkspaceClient

    fake = FakeWorkspaceClient()
    root = ("/Workspace/Users/u/shared" if scheme == "workspace" else "/Volumes/cat/sch/vol")
    api_root = "/Users/u/shared" if scheme == "workspace" else root
    tree = fake.ws if scheme == "workspace" else fake.vol
    tree.dirs.add(f"{api_root}/pair_11")
    tree.files[f"{api_root}/pair_11/{PYX_FRD}"] = b"frd bytes"
    backend = open_backend(f"{scheme}:{root}", base_dir=REPO, client=fake)
    assert [e.name for e in backend.list("pair_11")] == [PYX_FRD]
    assert backend.read_bytes(f"pair_11/{PYX_FRD}") == b"frd bytes"
    assert backend.exists(f"pair_11/{PYX_FRD}")
    assert backend.uri(f"pair_11/{PYX_FRD}") == f"{scheme}:{root}/pair_11/{PYX_FRD}"
