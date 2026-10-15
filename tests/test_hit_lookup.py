"""tools/hit_lookup.py — the gate's per-hit hash records matched against a local
candidates file (synthetic data only; a term never enters git)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unicodedata
from pathlib import Path

import pytest

from codegen.term_hash import normalize_term, term_sha256

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hit_lookup", REPO / "tools" / "hit_lookup.py")
hit_lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hit_lookup)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_normalization_is_strip_casefold_nfc():
    assert normalize_term("  SYN-Feed-Alpha \n") == "syn-feed-alpha"
    assert normalize_term("STRASSE") == normalize_term("straße")          # casefold, not lower
    decomposed = "cafe" + "́"
    assert normalize_term(decomposed) == unicodedata.normalize("NFC", "café")
    assert term_sha256(" SYN-Vendor ") == _sha("syn-vendor")
    assert len(term_sha256("x")) == 64


def _hits(tmp_path, records) -> Path:
    path = tmp_path / "hits.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def _candidates(tmp_path, lines) -> Path:
    path = tmp_path / "candidates.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


RECORDS = [
    {"output_file": "out/syn_feed/framework/config_rows.xlsx", "pattern_class": "deny_term",
     "term_sha256": _sha("syn-feed-alpha"), "occurrences": 3},
    {"output_file": "reports/syn_feed.md", "pattern_class": "harness_label",
     "term_sha256": _sha("timestamp").upper(), "occurrences": 1},
    {"output_file": "out/syn_feed/ddl/SYN_DDL.txt", "pattern_class": "deny_term",
     "term_sha256": _sha("syn-unknown"), "occurrences": 2},
]


def test_hashes_are_matched_to_candidates(tmp_path, capsys, monkeypatch):
    hits = _hits(tmp_path, RECORDS)
    cands = _candidates(tmp_path, ["# a comment", "", "SYN-Feed-Alpha", "  Timestamp  "])
    monkeypatch.setenv(hit_lookup.CANDIDATES_ENV, str(cands))
    assert hit_lookup.main([str(hits)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "hash: strip, casefold, NFC, sha256 utf-8 hex"
    assert out[1].endswith("->  SYN-Feed-Alpha") and "x3" in out[1]
    assert out[2].endswith("->  Timestamp") and "harness_label" in out[2]   # upper-case hex ok
    assert out[3].endswith("->  (no candidate matched)")
    assert out[4] == ("3 hit record(s), 3 distinct hash(es): 2 record(s) / 2 hash(es) "
                      "matched a candidate, 1 record(s) unmatched")


def test_the_summary_line_carries_no_candidate(tmp_path):
    results = hit_lookup.lookup(hit_lookup.load_hits(_hits(tmp_path, RECORDS)),
                                hit_lookup.load_candidates(_candidates(tmp_path,
                                                                       ["SYN-Feed-Alpha"])))
    assert "syn" not in hit_lookup.summary(results).lower()


def test_json_output_and_the_candidates_flag(tmp_path, capsys):
    hits = _hits(tmp_path, RECORDS[:1])
    cands = _candidates(tmp_path, ["syn-feed-alpha"])
    assert hit_lookup.main([str(hits), "--candidates", str(cands), "--json"]) == 0
    record = json.loads(capsys.readouterr().out.splitlines()[1])
    assert record["candidate"] == "syn-feed-alpha" and record["occurrences"] == 3


@pytest.mark.parametrize("body, message", [
    ("not json\n", "not JSON"),
    ('{"output_file": "a", "pattern_class": "b"}\n', "missing term_sha256, occurrences"),
])
def test_malformed_records_exit_2(tmp_path, capsys, body, message):
    hits = tmp_path / "hits.jsonl"
    hits.write_text(body, encoding="utf-8")
    cands = _candidates(tmp_path, ["x"])
    assert hit_lookup.main([str(hits), "--candidates", str(cands)]) == 2
    assert message in capsys.readouterr().err


def test_no_candidates_file_exits_2(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv(hit_lookup.CANDIDATES_ENV, raising=False)
    assert hit_lookup.main([str(_hits(tmp_path, RECORDS))]) == 2
    assert hit_lookup.CANDIDATES_ENV in capsys.readouterr().err
