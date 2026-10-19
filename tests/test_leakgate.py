"""post75: the leak gate is codegen.leakgate — harvested terms (file names /
stems, sheet names, header cells, column values), the static denylist BY PATH,
the dictionary filter (wordfreq, else the repo tokens), word-boundary /
substring matching, self-match exclusion, hash-only hit records, the lane.
Every term here is synthetic (Zq… / SYN…)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest

from codegen import leakgate
from codegen.term_hash import term_sha256

REPO = Path(__file__).resolve().parents[1]
SHEET = "ZqVendorFeedMap"
HEADER = "ZqSourceFieldTitle"
VALUE = "ZQ_MEMBER_PLANCODE"
STEM = "sttm_ZqClientFeed_v3"


def _pair(tmp_path: Path) -> Path:
    folder = tmp_path / "pairs" / "pair_1"
    folder.mkdir(parents=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append([HEADER, "Target Column", "Description"])
    ws.append(["Stage Column", "Data Type", None])
    ws.append([VALUE, "STRING", "ZqNotHarvestedColC"])       # only columns A / B below row 2
    wb.save(folder / f"{STEM}.xlsx")
    return folder


def _deny(**terms: str) -> leakgate.Denylist:
    return leakgate.Denylist(dict(terms), 0, "test")


# ------------------------------------------------------------------ harvest


def test_harvest_classes(tmp_path: Path) -> None:
    terms = leakgate.harvest([_pair(tmp_path)])
    assert terms[SHEET] == "sheet_name"
    assert terms[HEADER] == "header_cell"
    assert terms[VALUE] == "column_value"
    assert terms[STEM] == "file_stem"
    assert terms[f"{STEM}.xlsx"] == "file_name"
    assert "ZqNotHarvestedColC" not in terms
    assert "Description" not in terms                    # a structural label


def test_the_static_denylist_is_loaded_by_path(tmp_path: Path, monkeypatch) -> None:
    deny = tmp_path / "deny.txt"
    deny.write_text("# a comment\nZqStaticClient\n\nabc\n", encoding="utf-8")
    monkeypatch.setenv(leakgate.STATIC_DENYLIST_ENV, str(deny))
    assert leakgate.load_static_denylist() == {"ZqStaticClient": "local_denylist"}
    monkeypatch.setenv(leakgate.STATIC_DENYLIST_ENV, str(tmp_path / "missing.txt"))
    with pytest.raises(FileNotFoundError):              # a named list must exist
        leakgate.load_static_denylist()


def test_the_static_denylist_defaults_to_the_state_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(leakgate.STATIC_DENYLIST_ENV, raising=False)
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(tmp_path))
    assert leakgate.static_denylist_path() is None
    (tmp_path / "leakgate").mkdir()
    (tmp_path / "leakgate" / "denylist_local.txt").write_text("ZqOnTheVolume\n", encoding="utf-8")
    assert leakgate.load_static_denylist() == {"ZqOnTheVolume": "local_denylist"}


# ------------------------------------------------------------------- filter


def test_the_filter_drops_dictionary_words_short_terms_and_template_names() -> None:
    raw = {"Member Address": "header_cell", "ZqClient": "column_value", "short": "sheet_name",
           "ADLS_DELTA_INGESTION_DETAILS": "sheet_name", "plan": "local_denylist"}
    words = frozenset({"member", "address"})
    kept, dropped = leakgate.filter_terms(raw, words, frozenset({"adls_delta_ingestion_details"}))
    assert kept == {"ZqClient": "column_value", "plan": "local_denylist"}   # static: never
    assert dropped == 3


def test_without_wordfreq_the_dictionary_is_the_repo_tokens(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "wordfreq", None)          # import fails
    words = leakgate.english_words(REPO)
    assert words.source.startswith("repo-tokens") and "harvest" in words.words


def _repo(tmp_path: Path, git: bool) -> Path:
    root = tmp_path / "repo"
    for rel, text in {"src/a.py": "zqsrctoken = 1", "ui/app.ts": "zquitoken",
                      "ui/frontend/dist/bundle.js": "zqdisttoken",
                      "docs/notes.md": "zqdocstoken zqledgeredhash",
                      "docs/acfc/leaky.md": "zqledgeredfile",
                      "fixtures/f.md": "zqfixturetoken"}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    ledger = root / "docs" / "acfc" / "LEAK_LEDGER.md"
    ledger.write_text(f"{leakgate.LEDGER_BEGIN}\n`docs/acfc/leaky.md\tlocal_denylist\t"
                      f"{term_sha256('zqledgeredhash')}\t1`\n{leakgate.LEDGER_END}\n",
                      encoding="utf-8")
    if git:
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return root


@pytest.mark.parametrize("git", [True, False])
def test_the_repo_token_dictionary_scope_and_exclusions(tmp_path: Path, git: bool) -> None:
    words = leakgate.repo_token_dictionary(_repo(tmp_path, git))
    assert {"zqsrctoken", "zquitoken", "zqdocstoken"} <= words.words
    for excluded in ("zqdisttoken", "zqfixturetoken", "zqledgeredfile", "zqledgeredhash"):
        assert excluded not in words.words, excluded
    assert words.source == ("repo-tokens" if git else
                            "repo-tokens (disk walk, .gitignore honoured)")


# --------------------------------------------------------------------- scan


def test_harvested_terms_match_on_word_boundaries_static_as_substrings() -> None:
    deny = _deny(ZqClient="column_value", ZqStatic="local_denylist")
    result = leakgate.scan({"a.md": "XZqClientY and xxZqStaticxx"}, deny)
    assert [h.pattern_class for h in result.hits] == ["local_denylist"]
    result = leakgate.scan({"a.md": "the ZqClient feed"}, deny)
    assert result.real_hits == 1 and not result.clean


def test_a_hit_inside_the_reports_own_labels_is_a_self_match() -> None:
    deny = _deny(**{"Needed answers": "header_cell"})
    result = leakgate.scan({"r.md": "### Needed answers\n- key"}, deny)
    assert result.hits and result.hits[0].self_match and result.clean


def test_hit_records_carry_hashes_and_the_pair_never_the_term(tmp_path: Path) -> None:
    deny = _deny(ZqClientFeed="sheet_name")
    report = {"pairs": [{"pair": "pair_01"}, {"pair": "pair_02", "error": "ZqClientFeed"}]}
    result = leakgate.scan({"run.json": json.dumps(report, indent=2)}, deny)
    (hit,) = result.hits
    assert hit.report_field == "pairs[1]" and hit.term_sha256 == term_sha256("ZqClientFeed")
    leakgate.write_hits(result, tmp_path / "hits.jsonl")
    assert "ZqClientFeed" not in (tmp_path / "hits.jsonl").read_text(encoding="utf-8")
    assert "ZqClientFeed" not in leakgate.redact("see ZqClientFeed", deny)


def test_the_lane() -> None:
    clean = leakgate.scan({"a.md": "nothing"}, _deny(ZqClient="column_value"))
    dirty = leakgate.scan({"a.md": "ZqClient"}, _deny(ZqClient="column_value"))
    assert leakgate.lane(clean) == "approved"
    assert leakgate.lane(clean, scrub_clean=False) == "held"
    assert leakgate.lane(dirty) == "held"


def test_build_denylist_end_to_end(tmp_path: Path) -> None:
    static = tmp_path / "deny.txt"
    static.write_text("ZqStaticOnly\n", encoding="utf-8")
    deny = leakgate.build_denylist([_pair(tmp_path)], static,
                                   dictionary=leakgate.Dictionary(frozenset(), "test"),
                                   vocabulary=frozenset())
    assert {SHEET, HEADER, VALUE, STEM, "ZqStaticOnly"} <= set(deny.terms)
    result = leakgate.scan({"r.md": f"layout of {SHEET}"}, deny)
    assert result.real_hits == 1


# ------------------------------------------------------- the callers use it


def test_scrub_check_runs_the_leak_gate(tmp_path: Path) -> None:
    pairs = _pair(tmp_path).parent
    report = tmp_path / "report"
    report.mkdir()
    (report / "run.md").write_text("all quiet", encoding="utf-8")
    cmd = [sys.executable, str(REPO / "scripts" / "scrub_check.py"), "--leak-gate", str(pairs),
           str(report)]
    done = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert done.returncode == 0 and "leak gate: CLEAN" in done.stdout
    (report / "run.md").write_text(f"see {VALUE}", encoding="utf-8")
    done = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert done.returncode == 1 and "1 real hit(s) {'column_value': 1}" in done.stdout
    assert VALUE not in done.stdout


def test_scrub_check_reads_the_ledger_through_the_gate() -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import scrub_check
    finally:
        sys.path.remove(str(REPO / "scripts"))
    assert scrub_check.read_ledger_baseline() == leakgate.read_ledger()
