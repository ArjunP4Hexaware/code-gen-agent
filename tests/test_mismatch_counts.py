"""D1 post51 addendum 4: derived values (feed slugs, work-dir paths, contract
keys) are generated, not harvested — the leak gate cannot see them. The
coordinates tier never prints them: a contract mismatch is its COUNTS on the
first line ("contract mismatch, feed 2 of 3: 1 table only in FRD, ..."), a path
is "<workdir>/pair_07/…", a feed is "feed N of M"."""

from __future__ import annotations

import json
from pathlib import Path

from codegen import cli
from codegen.resolve.resolver import ContractMismatchError, mismatch_item
from codegen.run_errors import (
    MARKER,
    Coord,
    error_marker,
    first_error_line,
    first_error_line_full,
    located,
    path_hint,
)
from test_emit_stages_skipped import FEED, contracts  # noqa: F401 — the pair-1 chain

FRD_ONLY = ("SYN_FRD_ONLY_A", "SYN_FRD_ONLY_B")
FAIL = f"{'FAIL':<15}"


def test_a_synthetic_mismatch_is_counts_never_names(contracts, capsys):  # noqa: F811
    frd = Path(contracts[contracts.index("--frd-contract") + 1])
    data = json.loads(frd.read_text(encoding="utf-8"))
    data["feeds"][0]["stage_target"]["tables"] = list(FRD_ONLY)
    frd.write_text(json.dumps(data), encoding="utf-8")
    code = cli.main(contracts)
    captured = capsys.readouterr()
    assert code == 1

    line = first_error_line(code, captured.err, captured.out)
    assert line == (f"{FAIL} generate \u2014 contract mismatch, feed 1 of 1: 2 tables only in "
                    "FRD, 1 table only in STTM [ContractMismatchError]")
    for derived in (*FRD_ONLY, FEED, frd.name, str(frd.parent)):
        assert derived not in line
        assert all(derived not in ln for ln in captured.err.splitlines()
                   if ln.startswith(MARKER))
    # the full tier keeps the names, the summary on its FIRST line too
    full = first_error_line_full(code, captured.err, captured.out)
    assert FEED in full and "(2 tables only in FRD, 1 table only in STTM):" in full


def test_the_summary_reads_as_counts_by_kind():
    """The shape the pairs 03 / 04 report needs, on a synthetic error."""
    errors = [*(mismatch_item("column.frd_only", f"column SYN_C{i} only in FRD")
                for i in range(4)),
              mismatch_item("column.sttm_only", "columns SYN_X, SYN_Y only in STTM",
                            names=["SYN_X", "SYN_Y"]),
              mismatch_item("column.type_conflict", "SYN_Z: FRD Decimal vs STTM String")]
    exc = located(ContractMismatchError("syn_feed_slug", errors), Coord("feed", n=2, of=3),
                  "contract.mismatch")
    assert exc.counts == {"column.frd_only": 4, "column.sttm_only": 2,
                          "column.type_conflict": 1}
    line = first_error_line(1, error_marker("generate", "contract.mismatch",
                                            Coord("pair", n=1, of=1), exc=exc))
    assert line == (f"{FAIL} generate \u2014 contract mismatch, feed 2 of 3: 4 columns only in "
                    "FRD, 2 columns only in STTM, 1 type conflict [ContractMismatchError]")
    assert "SYN" not in line and "syn_feed_slug" not in line
    assert str(exc).splitlines()[0] == ("contract mismatch for feed 'syn_feed_slug' (4 columns "
                                        "only in FRD, 2 columns only in STTM, 1 type conflict):")


def test_one_table_named_by_three_segments_counts_once():
    errors = [mismatch_item("table.sttm_only", f"segment {s} table T", names=["T"])
              for s in ("Header", "Detail", "Trailer")]
    assert ContractMismatchError("f", errors).counts == {"table.sttm_only": 1}


def test_a_missing_contract_names_the_pair_folder_only(tmp_path, capsys):
    work = tmp_path / "codegen-work-SYN123" / "pair_07"
    work.mkdir(parents=True)
    frd = work / "frd.contract.json"
    frd.write_text("{}", encoding="utf-8")
    missing = work / "SYN_DERIVED_SLUG.sttm.contract.json"
    code = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(missing),
                     "--dry-run", "--skip-tests"])
    captured = capsys.readouterr()
    assert code == 1
    line = first_error_line(code, captured.err, captured.out)
    assert line == (f"{FAIL} generate \u2014 contract not found: STTM <workdir>/pair_07/\u2026 "
                    "[FileNotFoundError]")
    assert "SYN" not in line
    assert "SYN_DERIVED_SLUG" in first_error_line_full(code, captured.err, captured.out)


def test_path_hint_keeps_only_a_pair_folder():
    assert path_hint("/tmp/codegen-work-sb65923-5d36896f/pair_07/x.json") == \
        "<workdir>/pair_07/\u2026"
    assert path_hint(r"C:\work\pair_12\sub\SYN_name.json") == "<workdir>/pair_12/\u2026"
    assert path_hint("/tmp/SYN_feed/x.json") == "<workdir>/\u2026"
    assert path_hint("/tmp/pair_SYN/x.json") == "<workdir>/\u2026"
