"""Pre-push scrub gate at home (2026-10-15): every TRACKED file under config/
and docs/acfc/ is scanned with the leak scrubber (scripts/scrub_check.py: its
generic patterns, the harvested raw denylist when inputs/reference_raw/ is
present, and the local term file CODEGEN_SCRUB_DENYLIST names — gitignored).

The known hits are baselined in docs/acfc/LEAK_LEDGER.md as (file, class,
sha256(term)) rows — never the term; the hash is codegen.term_hash.term_sha256
(strip, casefold, NFC). The suite fails only on a hit whose (file, hash) is NOT
in those rows. This test never writes: regenerate the rows deliberately with
``python scripts/scrub_check.py --rebaseline``."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from codegen.term_hash import term_sha256

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scrub_check_gate",
                                              REPO / "scripts" / "scrub_check.py")
scrub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrub)


def _has_git() -> bool:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse"], capture_output=True,
                              check=False).returncode == 0
    except OSError:
        return False


@pytest.mark.skipif(not _has_git(), reason="no git checkout: tracked files unknown")
def test_no_tracked_file_under_config_or_docs_acfc_has_a_new_hit():
    baseline = {(f, digest) for f, _klass, digest in scrub.read_ledger_baseline()}
    assert baseline, "docs/acfc/LEAK_LEDGER.md has no baseline rows (scrub_check --rebaseline)"
    found = scrub.ledger_baseline(scrub.tracked_files(*scrub.LEDGER_ROOTS),
                                  scrub.active_denylist())
    new = sorted((f, klass) for f, klass, digest in found if (f, digest) not in baseline)
    # file + class only: a term never reaches the test output
    assert not new, f"{len(new)} new scrub hit(s) outside the ledger baseline: {new}"


def test_the_ledger_rows_are_hashes_only():
    rows = scrub.read_ledger_baseline()
    assert all(len(d) == 64 and all(c in "0123456789abcdef" for c in d) for _f, _k, d in rows)
    text = scrub.LEDGER.read_text(encoding="utf-8")
    assert text.index("## The harness leak gate") < text.index(scrub.LEDGER_BEGIN)


def test_a_planted_term_is_a_new_hit_and_a_known_one_is_not(tmp_path, monkeypatch):
    planted = tmp_path / "docs" / "acfc" / "note.md"
    planted.parent.mkdir(parents=True)
    planted.write_text("a SYN-Planted-Term here\n", encoding="utf-8")
    deny_file = tmp_path / "terms.txt"
    deny_file.write_text("# local terms\nSYN-Planted-Term\n", encoding="utf-8")
    monkeypatch.setenv(scrub.LOCAL_DENYLIST_ENV, str(deny_file))
    deny = scrub.active_denylist()
    assert deny["SYN-Planted-Term"] == "local_denylist"
    rows = scrub.ledger_baseline([planted], deny, repo=tmp_path)
    assert rows == {("docs/acfc/note.md", "local_denylist", term_sha256("SYN-Planted-Term"))}
    # the same row in a ledger: known; a second file with it: new
    ledger = tmp_path / "LEDGER.md"
    ledger.write_text("# prose\n", encoding="utf-8")
    scrub.write_ledger_baseline(rows, ledger)
    assert scrub.read_ledger_baseline(ledger) == rows
    assert ledger.read_text(encoding="utf-8").startswith("# prose\n")
    other = tmp_path / "config" / "x.yaml"
    other.parent.mkdir()
    other.write_text("k: SYN-Planted-Term\n", encoding="utf-8")
    known = {(f, d) for f, _k, d in scrub.read_ledger_baseline(ledger)}
    found = scrub.ledger_baseline([planted, other], deny, repo=tmp_path)
    assert [f for f, _k, d in found if (f, d) not in known] == ["config/x.yaml"]


def test_rebaseline_rewrites_only_the_marked_block(tmp_path):
    ledger = tmp_path / "LEDGER.md"
    ledger.write_text("# head\n\n" + scrub.LEDGER_BEGIN + "\nold\n" + scrub.LEDGER_END
                      + "\n\n## tail\n", encoding="utf-8")
    scrub.write_ledger_baseline({("a", "k", "0" * 64)}, ledger)
    text = ledger.read_text(encoding="utf-8")
    assert text.startswith("# head\n") and text.endswith("\n## tail\n") and "old" not in text
    assert scrub.read_ledger_baseline(ledger) == {("a", "k", "0" * 64)}


def test_a_named_local_denylist_that_is_missing_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv(scrub.LOCAL_DENYLIST_ENV, str(tmp_path / "absent.txt"))
    with pytest.raises(OSError):
        scrub.active_denylist()
