"""M8.2: auto-pairing by content. Four pairs share ONE ticket number and
their names say nothing else (the ACFC inventory's situation,
docs/acfc/RETROFIT_LOG.md §7) — the documents' own content pairs them; a tie
becomes a question; a lone weak signal never pairs."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.demo_sources import auto_pair_document
from codegen.pairing import _name_match, pair_by_content

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
TICKET = "9900001"          # synthetic

# (STTM fixture, its FRD fixture) — copied under names that share the ticket
# and deliberately cross the letters so no name rule can pair them.
PAIRS = [("pair_1_family_a.xlsx", "f1_pair_1.docx", "a", "y"),
         ("pair_2_family_b.xlsx", "f1_pair_2_variant.docx", "b", "z"),
         ("pair_8_family_a.xlsx", "f2_pair_8.docx", "c", "w"),
         ("pair_11_family_b.xlsx", "f1_pair_11_multi_file.docx", "d", "x")]


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture
def shared_ticket(tmp_path):
    sttms, frds, truth = {}, {}, {}
    for sttm, frd, s_tag, f_tag in PAIRS:
        s_name, f_name = f"STTM_{TICKET}_{s_tag}.xlsx", f"FRD_{TICKET}_{f_tag}.docx"
        sttms[s_name] = Path(shutil.copy(SHAPES / "sttm" / sttm, tmp_path / s_name))
        frds[f_name] = Path(shutil.copy(SHAPES / "frd" / frd, tmp_path / f_name))
        truth[s_name] = f_name
    return sttms, frds, truth


def test_the_ticket_alone_cannot_pair_them(shared_ticket):
    sttms, frds, _truth = shared_ticket
    assert all(auto_pair_document(name, list(frds)) is None for name in sttms)


def test_four_pairs_sharing_a_ticket_resolve_by_content(shared_ticket, config):
    sttms, frds, truth = shared_ticket
    for name, path in sttms.items():
        decision = pair_by_content("frd", path, frds, config, REPO)
        assert decision.chosen == truth[name], (name, decision.reason, decision.candidates)
        assert decision.rule == "content"
        winner = decision.candidates[0]
        assert {s.name for s in winner.signals} - {"ticket", "name_stem"}, winner
        # every content signal cites where it was read
        assert all("↔" in s.detail for s in winner.signals if s.name != "ticket")


def test_a_tie_is_a_question_not_a_guess(shared_ticket, config, tmp_path):
    """Two variants of the SAME FRD score within the margin: nothing pairs,
    the top candidates come back as a layout-dialog choice question."""
    sttms, frds, _truth = shared_ticket
    variant = f"FRD_{TICKET}_v.docx"
    frds = {**frds, variant: Path(shutil.copy(
        SHAPES / "frd" / "f1_pair_11_multi_file_catalog.docx", tmp_path / variant))}
    decision = pair_by_content("frd", sttms[f"STTM_{TICKET}_d.xlsx"], frds, config, REPO)
    assert decision.chosen is None and decision.ambiguous
    question = decision.question()
    assert question["kind"] == "choice" and question["key"] == "pair.frd"
    offered = [c["value"] for c in question["candidates"]]
    assert offered[:2] == sorted([variant, f"FRD_{TICKET}_x.docx"],
                                 key=lambda n: -next(c.score for c in decision.candidates
                                                     if c.name == n))
    assert len({c["source"] for c in question["candidates"]}) == len(offered)  # radio keys


def test_an_explicit_map_entry_overrides_content(shared_ticket, config):
    sttms, frds, _truth = shared_ticket
    wrong = f"FRD_{TICKET}_w.docx"
    decision = pair_by_content("frd", sttms[f"STTM_{TICKET}_a.xlsx"], frds, config, REPO,
                               explicit_map={f"sttm_{TICKET}_a": f"frd_{TICKET}_w"})
    assert (decision.chosen, decision.rule) == (wrong, "pairing_map")


def test_an_sttm_with_no_frd_in_the_set_pairs_nothing(shared_ticket, config, tmp_path):
    _sttms, frds, _truth = shared_ticket
    orphan = Path(shutil.copy(SHAPES / "sttm" / "pair_3_family_c.xlsx",
                              tmp_path / f"STTM_{TICKET}_e.xlsx"))
    decision = pair_by_content("frd", orphan, frds, config, REPO)
    assert decision.chosen is None
    assert all(c.score < config.inputs.pairing.min_score for c in decision.candidates)


def test_vdd_pairs_by_files_sheet_agreement(config, tmp_path):
    vdds = {f"VDD_{TICKET}_{tag}.xlsx": Path(shutil.copy(SHAPES / "vdd" / src,
                                                        tmp_path / f"VDD_{TICKET}_{tag}.xlsx"))
            for tag, src in (("p", "pair_1_v1_segments.xlsx"), ("q", "pair_2_v2_per_file.xlsx"),
                             ("r", "pair_9_v3_per_table.xlsx"))}
    sttm = Path(shutil.copy(SHAPES / "sttm" / "pair_2_family_b.xlsx",
                            tmp_path / f"STTM_{TICKET}_b.xlsx"))
    decision = pair_by_content("vdd", sttm, vdds, config, REPO)
    assert (decision.chosen, decision.rule) == (f"VDD_{TICKET}_q.xlsx", "content")


def test_names_alone_still_pair_when_no_document_speaks(config, tmp_path):
    """Pre-M8 behaviour kept: unreadable / contentless candidates fall back to
    the name rules (unique shared ticket, else unique stem)."""
    sttm = tmp_path / "STTM_alpha_beta_gamma_7700001.xlsx"
    frd = tmp_path / "FRD_other_words_here_7700001.contract.json"
    other = tmp_path / "FRD_unrelated_thing_else.contract.json"
    for path in (sttm, frd, other):
        path.write_bytes(b"not a document")
    decision = pair_by_content("frd", sttm, {frd.name: frd, other.name: other}, config, REPO)
    assert (decision.chosen, decision.rule) == (frd.name, "ticket")


@pytest.mark.parametrize(("name", "text", "expected"), [
    ("FEED_8", "Feed Type", False),                 # a generic token is not a name
    ("FEED_8", "feed_8_elig_YYYYMMDD.txt", True),
    ("Accumulators", "I_ACCUM_*_TO_CLIENT_*.csv", True),
    ("Member Eligibility", "Eligibility of members", True),
    ("Risk", "Risk", True),
    ("", "anything", False),
])
def test_name_match_is_strict_about_short_tokens(name, text, expected):
    assert _name_match(name, text) is expected


# -- the runner: an undecided pairing is asked in the layout dialog ---------------------

def test_runner_asks_an_undecided_pairing_and_takes_the_answer(shared_ticket, config, tmp_path):
    pytest.importorskip("fastapi")
    import threading
    import time

    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    sttms, frds, _truth = shared_ticket
    variant = f"FRD_{TICKET}_v.docx"
    frds = {**frds, variant: Path(shutil.copy(
        SHAPES / "frd" / "f1_pair_11_multi_file_catalog.docx", tmp_path / variant))}
    runner = DemoRunner(GenerationStore(str(REPO / "config" / "config.yaml")),
                        work=lambda: None)
    runner.pair_decisions["frd"] = pair_by_content(
        "frd", sttms[f"STTM_{TICKET}_d.xlsx"], frds, config, REPO)
    runner.fetch_frd_candidate = lambda name: frds[name]          # the tmp folder is the inbox
    assert set(runner.status()["pair_candidates"]) == {"frd"}

    runner.state = "running"
    worker = threading.Thread(target=runner._ask_pairing, daemon=True)  # noqa: SLF001
    worker.start()
    deadline = time.time() + 5
    while runner.state != "needs_layout" and time.time() < deadline:
        time.sleep(0.01)
    question = runner.status()["layout_questions"][0]
    assert question["key"] == "pair.frd" and question["kind"] == "choice"
    assert {c["value"] for c in question["candidates"]} >= {variant, f"FRD_{TICKET}_x.docx"}

    runner.answer_layout({"gaps": {"pair.frd": {"value": variant, "source": "candidate 1"}}})
    worker.join(timeout=5)
    assert runner.selected_frd == frds[variant] and runner.selected_frd_label == variant
    assert runner.frd_auto_paired is None                          # the person chose
