"""scripts/scrub_check.py structural patterns (2026-10-12): an e-mail address and a
``/Workspace/Users/<user>`` path are leaks wherever they appear (the round3
pair_2 score.json put both on origin) — except the synthetic / placeholder
forms the repo writes on purpose. All addresses below are synthetic."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scrub_check  # noqa: E402

# Assembled at run time, so a scan of THIS file finds no address or user path
# (a repo-wide scrub stays clean); the names and domains below are made up.
AT = "@"
JDOE = "jdoe" + AT + "corp-mail.net"
USERS = "/Workspace/" + "Users/"


def _classes(text: str) -> list[str]:
    return [klass for klass, _match in scrub_check.structural_hits(text)]


def test_an_email_address_is_a_hit_unless_synthetic():
    assert _classes("owner: jane.doe" + AT + "corp-mail.net") == ["email_address"]
    two = "alerts to ops" + AT + "client.co.uk and dl" + AT + "other.org"
    assert _classes(two) == ["email_address"] * 2
    for allowed in ("syn.dl.prodsupport@synthetic.example", "a@b.example.com",
                    "x@acct.example.invalid", "noreply@anthropic.com", "t@synthetic.example"):
        assert _classes(allowed) == [], allowed


def test_a_workspace_user_path_is_a_hit_unless_a_placeholder():
    assert _classes(f'"golden": "{USERS}someone.real/proj/g.xlsx"') == ["workspace_user_path"]
    leak = f"{USERS}{JDOE}/code-gen-agent/x.xlsx"
    assert sorted(_classes(leak)) == ["email_address", "workspace_user_path"]
    for allowed in ("<WORKSPACE_PATH>/goldens/g.xlsx", "/Workspace/Users/<user>/app",
                    "workspace:/Workspace/Users/u/shared/frd_sttm_pairs",
                    "/Workspace/Users/syn.user@synthetic.example/app",
                    "`workspace:/Workspace/Users/…` (Workspace API)",
                    "/Workspace/Users/<deploy-contact>/codegen-agent-app"):
        assert _classes(allowed) == [], allowed


def test_scan_paths_reports_both_classes(tmp_path):
    (tmp_path / "score.json").write_text(
        '{"golden": "' + USERS + JDOE + '/p/g.xlsx"}', encoding="utf-8")
    (tmp_path / "notes.md").write_text(f"ask {JDOE}", encoding="utf-8")
    (tmp_path / "clean.md").write_text("see <WORKSPACE_PATH>/p", encoding="utf-8")
    hits = {(path.name, klass)
            for path, klass, _ctx in scrub_check.scan_paths([tmp_path], deny={})}
    assert ("notes.md", "email_address") in hits
    assert {name for name, _klass in hits} == {"score.json", "notes.md"}


def test_the_scrubbed_round3_score_json_is_clean():
    path = ROOT / "codegen-outputs" / "iig_validation" / "round3" / "pair_2" / "score.json"
    assert scrub_check.structural_hits(path.read_text(encoding="utf-8")) == []


def test_claude_md_carries_no_address_or_user_path():
    # 2026-10-13: the deploy notes carried a user id in a workspace path (d7aa44c);
    # scrubbed to <deploy-contact>, the history purge is in docs/acfc/LEAK_LEDGER.md.
    assert scrub_check.structural_hits((ROOT / "CLAUDE.md").read_text(encoding="utf-8")) == []


# 2026-10-13: the document-title phrases (held as hashes) and downloaded-copy names.
# The words are assembled here so this file never holds a title phrase whole.
_MEDI, _EXP = "Medi" + "care", "Expan" + "sion"
_SOC, _DET = "Social" + "ly", "Deter" + "mined"


def test_a_document_title_phrase_is_a_hit_in_any_spelling(tmp_path):
    assert scrub_check.title_hits(f"STTM {_MEDI} {_EXP}_MIDS_{_SOC[:-2]} {_DET}.xlsx") == 2
    assert scrub_check.title_hits(f"FRD_{_MEDI.upper()}-{_EXP.lower()} - {_SOC} {_DET}") == 2
    assert scrub_check.title_hits(f"{_MEDI} coverage was {_DET.lower()} by policy") == 0
    (tmp_path / "RUN.md").write_text(f"read {_MEDI}  {_EXP}", encoding="utf-8")
    hits = scrub_check.scan_paths([tmp_path], deny={})
    assert [(k, ctx) for _p, k, ctx in hits] == [
        ("document_title_phrase", "<a deny-listed title phrase>")]


def test_a_copy_suffixed_document_name_is_a_hit(tmp_path):
    (tmp_path / "a.md").write_text("input: STTM x (" + "1).xlsx and FRD y (" + "12).DOCX",
                                   encoding="utf-8")
    (tmp_path / "b.md").write_text("see step (" + "1). xlsx files only; out_IIG.xlsx",
                                   encoding="utf-8")
    hits = {(p.name, k) for p, k, _ctx in scrub_check.scan_paths([tmp_path], deny={})}
    assert hits == {("a.md", "copy_suffixed_document_name")}
