"""post74 (D1 post73 item 6): pair_11 asked 15 notebook-only keys
(``feeds.feed_<n>.notebook.landing_path / archive_path / reject_path``) while
pair_02 asked none. The cause: the notebook (v2 and v1's feed_spec) takes its
landing / archive / reject paths from the IIG ADLS_DELTA row's SRC_ADLS_PATH /
SRC_ADLS_ARCHVL_PATH / TGT_RJT_ADLS_PATH, and those derive from the FRD's
landing location — pair_02's FRD states it, the Pyx FRD (pair_11) states no
inbound path, so every path cell is open.

Now an open landing is asked ONCE per feed, by the IIG cell's key
``feeds[<i>].src_adls_path`` — the same key for the workbook (INPUT_NEEDED) and
the notebook (blocking on a notebook run) — with the template's landing
convention shown as the agent's proposal, never written unanswered. The
answer fills the workbook's three path cells and the notebook's paths."""

from __future__ import annotations

import json

import yaml
from openpyxl import load_workbook

from codegen import cli, run_stages
from codegen.metadata_template import landing_proposal
from test_iig_corpus_cells import _pair11

ADLS = "ADLS_DELTA_INGESTION_DETAILS"


def _without_landing(pair, index: int = 0):
    frd_path = pair[0]
    data = json.loads(frd_path.read_text(encoding="utf-8"))
    data["feeds"][index]["landing_location"] = None
    data.get("field_provenance", {}).pop(f"feeds[{index}].landing_location", None)
    frd_path.write_text(json.dumps(data), encoding="utf-8")


def _run(config, pair, parts, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True, output_mode=parts,
                          conventions_profile="acfc_prx", iig_template="iig_v2", **kw)


def _adls_paths(out, feed_slug) -> dict:
    (xlsx,) = (out / feed_slug).rglob("*_IIG.xlsx")
    ws = load_workbook(xlsx, read_only=True)[ADLS]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    return {h: rows[1][header.index(h)] for h in
            ("SRC_ADLS_PATH", "SRC_ADLS_ARCHVL_PATH", "TGT_RJT_ADLS_PATH")}


def _lines(out: str, label: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith(label)]


def test_a_framework_run_asks_the_iig_cell_once_with_a_proposal(tmp_path, capsys):
    config, specs, pair = _pair11(tmp_path)
    _without_landing(pair)
    feed = specs[0]
    code = _run(config, pair, ["framework"], only_feed=feed.feed_id)
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK                      # non-blocking on a framework run
    (line,) = [ln for ln in _lines(out, "INPUT_NEEDED") if "src_adls_path" in ln]
    assert line.startswith("INPUT_NEEDED   feeds[0].src_adls_path — no document states the "
                           "inbound path")
    proposal = landing_proposal(config.metadata.templates["iig_v2"], feed)
    assert proposal and f"proposed (agent_proposal, not applied): {proposal!r}" in line
    assert all(v in (None, "") for v in _adls_paths(tmp_path / "out", feed.feed_slug).values())
    assert not [ln for ln in out.splitlines() if ".notebook." in ln.split(" — ")[0]]


def test_a_notebook_run_asks_the_same_key_blocking(tmp_path, capsys):
    config, specs, pair = _pair11(tmp_path)
    _without_landing(pair)
    feed = specs[0]
    code = _run(config, pair, ["notebook", "framework"], only_feed=feed.feed_id)
    out = capsys.readouterr().out
    assert code == cli.EXIT_NEEDS_ANSWERS
    keys = [ln[15:].split(" — ", 1)[0] for ln in _lines(out, "QUESTION")]
    assert keys == ["feeds[0].src_adls_path"]       # one key, never notebook.<path>
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert [q["key"] for q in manifest["questions"] if q["blocking"]] == [
        "feeds[0].src_adls_path"]


def test_the_answer_fills_the_workbook_and_the_notebook(tmp_path, capsys):
    config, specs, pair = _pair11(tmp_path)
    _without_landing(pair)
    feed = specs[0]
    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"inputs": {
        "feeds[0].src_adls_path": {"value": "/inbound/claims/vendor_k/"}}}), encoding="utf-8")
    code = _run(config, pair, ["notebook", "framework"], only_feed=feed.feed_id,
                answers_path=answers)
    out = capsys.readouterr().out
    assert "src_adls_path" not in out.replace("feeds[0].src_adls_path matches", "")
    paths = _adls_paths(tmp_path / "out", feed.feed_slug)
    assert paths["SRC_ADLS_PATH"] == "/inbound/claims/vendor_k/"
    assert paths["SRC_ADLS_ARCHVL_PATH"] == "/inbound/claims/vendor_k/Archive/"
    assert str(paths["TGT_RJT_ADLS_PATH"]).startswith("/claims/vendor_k/Reject/")
    assert code in (cli.EXIT_OK, cli.EXIT_NEEDS_ANSWERS)
    assert not [ln for ln in _lines(out, "QUESTION") if "adls_path" in ln]


def test_no_proposal_from_an_unstated_source(tmp_path):
    config, specs, _pair = _pair11(tmp_path)
    tpl = config.metadata.templates["iig_v2"]
    spec = specs[0].model_copy(update={"source_system": "unstated", "landing_location": None})
    assert landing_proposal(tpl, spec) == ""
