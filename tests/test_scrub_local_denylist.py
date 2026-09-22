"""The scrub check's third layer: a LOCAL, gitignored raw-term denylist
(``docs/acfc/denylist_local.txt``). Synthetic terms only — the real file is
never read here (``local=`` / ``path=`` point at a temp file)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import scrub_check  # noqa: E402


def test_the_local_file_parses_pipes_comments_and_blank_lines(tmp_path):
    deny = tmp_path / "denylist_local.txt"
    deny.write_text("Alpha Vendor | ZX | beta_sheet_7\n# a comment | NotATerm\n\nZX | gamma\n",
                    encoding="utf-8")
    assert scrub_check.load_local_denylist(deny) == ["Alpha Vendor", "ZX", "beta_sheet_7",
                                                     "gamma"]
    assert scrub_check.load_local_denylist(tmp_path / "absent.txt") == []


def test_terms_match_as_whole_terms_of_any_length_and_never_echo_the_term(tmp_path):
    doc = tmp_path / "run.md"
    doc.write_text("sheet Inbound_ZX_OH/source: ok\nthe alpha vendor files\nZXY is fine\n",
                   encoding="utf-8")
    hits = scrub_check.scan_paths([doc], deny={}, local=["ZX", "Alpha Vendor", "absent"])
    classes = {h[1] for h in hits}
    assert classes == {"local_denylist"}
    contexts = [h[2] for h in hits]
    # ZX inside an underscore-joined name (line 1), the vendor case-insensitively
    # (line 2); "ZXY" is another word and does not match.
    assert contexts == ["term #1 of denylist_local.txt at line 1",
                        "term #2 of denylist_local.txt at line 2"]
    assert not any("ZX" in c or "Alpha" in c for c in contexts)


def test_the_denylist_file_itself_is_never_a_hit():
    assert scrub_check.LOCAL_DENYLIST.name == "denylist_local.txt"
    ignored = subprocess.run(["git", "check-ignore", "-q",
                              str(scrub_check.LOCAL_DENYLIST.relative_to(REPO))],
                             cwd=REPO, check=False)
    assert ignored.returncode == 0, "docs/acfc/denylist_local.txt must stay gitignored"
