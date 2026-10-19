"""post70: the scrub sees a storage account outside its ADLS host.

A v2 notebook carries the account apart from the host (``STORAGE_ACCOUNT =
"<account>"``; ``adls_uri()`` joins them at run time) — inside ACFC that is
correct, the notebook must run. scripts/scrub_check.py treats it as class
``client_storage_account``: every ``storage_account`` of a loaded environment
profile, and a ``storage_account_pattern`` token assigned to STORAGE_ACCOUNT.
SYN-shaped accounts (the suite's own profile) and placeholders are never a hit.
"""

from __future__ import annotations

import importlib.util

import notebook_v2_fixtures as fx
from codegen import cli

spec = importlib.util.spec_from_file_location("scrub_check_accounts",
                                              fx.REPO / "scripts" / "scrub_check.py")
scrub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrub)

ACCOUNT = "plainacct01"          # not SYN-shaped: stands in for a real account


def _profile(folder, account: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "d1.yaml").write_text(f"storage_account: {account}\n", encoding="utf-8")
    return folder


def _notebooks(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_ENVIRONMENTS_DIR", str(_profile(tmp_path / "envs", ACCOUNT)))
    config = fx.acfc_config(tmp_path)
    assert cli._run_pairs([fx.sd_pair()], config, dry_run=True, skip_tests=True,
                          output_mode=["notebook"], only_feed=None,
                          conventions_profile="acfc_prx", iig_template="iig_v2") == cli.EXIT_OK
    books = sorted(p for p in (tmp_path / "out").rglob("notebook/*.ipynb"))
    assert books
    source = books[0].with_suffix(".py").read_text(encoding="utf-8")
    assert f'STORAGE_ACCOUNT = "{ACCOUNT}"' in source          # the split form
    assert ".dfs.core.windows.net" not in source.replace('_ADLS_HOST = "dfs.core.windows.net"', "")
    return books


def test_a_notebook_with_the_split_form_scrubs_as_a_hit(tmp_path, monkeypatch):
    books = _notebooks(tmp_path, monkeypatch)
    for ipynb in books:
        for path in (ipynb, ipynb.with_suffix(".py")):
            classes = {k for _p, k, _c in scrub.scan_paths([path])}
            assert scrub.ACCOUNT_CLASS in classes, path.name
            assert all(t != ACCOUNT for _p, _k, t in scrub.scan_paths([path]))  # never printed
            assert (scrub.ACCOUNT_CLASS, ACCOUNT) in [(k, t) for _p, k, t in
                                                      scrub.scan_hits([path], {})]


def test_the_assignment_alone_is_a_hit_without_the_profile(tmp_path, monkeypatch):
    books = _notebooks(tmp_path, monkeypatch)
    # the profile is gone (another machine, a copied output): the assignment still hits
    monkeypatch.setenv("CODEGEN_ENVIRONMENTS_DIR", str(tmp_path / "empty"))
    assert ACCOUNT not in scrub.environment_accounts()
    assert scrub.ACCOUNT_CLASS in {k for _p, k, _c in scrub.scan_paths(books)}


def test_a_profile_account_anywhere_is_a_hit(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_ENVIRONMENTS_DIR", str(_profile(tmp_path / "envs", ACCOUNT)))
    assert scrub.environment_accounts()[ACCOUNT] == scrub.ACCOUNT_CLASS
    note = tmp_path / "note.md"
    note.write_text(f"landing lives on {ACCOUNT}/mftlanding\n", encoding="utf-8")
    assert [k for _p, k, _t in scrub.scan_hits([note], {})] == [scrub.ACCOUNT_CLASS]
    note.write_text(f"landing lives on x{ACCOUNT}9\n", encoding="utf-8")   # not the token
    assert scrub.scan_hits([note], {}) == []


def test_syn_shaped_accounts_and_placeholders_are_never_hits(tmp_path, monkeypatch):
    patterns = scrub.account_patterns()
    for text in ('STORAGE_ACCOUNT = "synd1teststorage"', 'STORAGE_ACCOUNT = "<<D1:X>>"',
                 'STORAGE_ACCOUNT = ""', 'STORAGE_ACCOUNT = "nodigits"'):
        assert scrub.account_hits(text, {}, patterns) == [], text
    monkeypatch.setenv("CODEGEN_ENVIRONMENTS_DIR", str(_profile(tmp_path / "envs",
                                                                "synd1teststorage")))
    assert scrub.environment_accounts() == {}      # the suite's own profile, the tracked ones
    # the escaped quote of an .ipynb source line
    assert scrub.account_hits('"STORAGE_ACCOUNT = \\"acct12345\\"\\n"', {}, patterns) == [
        (scrub.ACCOUNT_CLASS, "acct12345")]
