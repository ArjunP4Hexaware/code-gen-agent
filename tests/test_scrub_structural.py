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
                    "/Workspace/Users/syn.user@synthetic.example/app"):
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
