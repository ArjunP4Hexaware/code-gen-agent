"""post174: proposed vocabulary, approved once (docs/PARSER_SELF_EXTENSION.md step 2).

A person answers a question with a value a REFUSED FRD cell already states on a
"<label>: <value>" line -> the run proposes that label for the field. Approved (dev App
only, Soham), it lands in the shared state root's vocabulary/approved.yaml and every
later run - both Apps - reads that label itself. Nothing applies before approval; a
rejected label is never proposed again; a proposal carries no cell value."""

from __future__ import annotations

import pytest

from codegen import vocabulary as voc
from codegen.storage import open_backend

CELL = {"kind": "multiline", "table": 6, "row": 4, "col": 2, "label": "Object/data Format",
        "text": "Kind Of File: .txt\nSeparator: Pipe Delimited"}
FRD = {"structured": {"feeds[0].file_format": CELL}}


def _backend(tmp_path):
    return open_backend(f"local:{(tmp_path / 'state').as_posix()}", base_dir=tmp_path,
                        create_root=True)


def test_an_answer_the_refused_cell_states_proposes_its_label():
    (proposal,) = voc.propose(FRD, {"feeds[0].file_format": {"value": "txt"}}, run="demo_1")
    assert {k: proposal[k] for k in ("field", "label", "run")} == {
        "field": "file_format", "label": "Kind Of File", "run": "demo_1"}
    assert proposal["cell"] == "FRD table 6 row 4 ('Object/data Format')"
    assert ".txt" not in str(proposal) and "Pipe" not in str(proposal)   # no cell value


@pytest.mark.parametrize("gaps", [
    {"feeds[0].file_format": {"value": "csv"}},                 # not what the cell states
    {"feeds[0].file_format": {"value": ""}},                    # no answer
    {"feeds[0].stage_target.tables": {"value": "txt"}},         # not a line field
])
def test_no_proposal_without_a_verbatim_match_on_a_line_field(gaps):
    assert voc.propose(FRD, gaps) == []


def test_a_known_label_proposes_nothing():
    assert voc.propose(FRD, {"feeds[0].file_format": "txt"},
                       known={"file_format": ["Kind of file"]}) == []


def test_a_derived_feed_reads_the_frds_one_cell():
    assert voc.propose(FRD, {"feeds[3].file_format": "txt"})[0]["field"] == "file_format"


def test_record_approve_and_reject(tmp_path):
    backend = _backend(tmp_path)
    proposals = voc.propose(FRD, {"feeds[0].file_format": "txt",
                                  "feeds[0].delimiter": "Pipe Delimited"})
    assert len(voc.record(backend, proposals)) == 2
    assert voc.record(backend, proposals) == []                # pending: not twice
    by_field = {p["field"]: p for p in voc.load(backend)["proposals"]}
    voc.decide(backend, by_field["file_format"]["id"], approve=True)
    voc.decide(backend, by_field["delimiter"]["id"], approve=False)
    state = voc.load(backend)
    assert state["proposals"] == []
    assert state["approved"] == {"file_format": ["Kind Of File"]}
    assert voc.record(backend, proposals) == []                # approved / rejected: never again
    with pytest.raises(KeyError):
        voc.decide(backend, "nope", approve=True)


def test_approved_labels_join_the_reader_on_the_next_config(tmp_path, monkeypatch):
    from pathlib import Path

    from codegen.config import load_config

    state = tmp_path / "state"
    backend = _backend(tmp_path)
    voc.record(backend, voc.propose(FRD, {"feeds[0].file_format": "txt"}))
    voc.decide(backend, voc.load(backend)["proposals"][0]["id"], approve=True)
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(state))
    repo = Path(__file__).resolve().parents[1]
    labels = load_config(repo / "config" / "config.yaml").extractor.frd.cell_line_labels
    assert "Kind Of File" in labels["file_format"]
    assert "File Format" in labels["file_format"]             # appended, never replacing


def test_the_loop_end_to_end_refused_answered_approved_read(tmp_path, monkeypatch):
    """Through the real FRD reader: an unknown line label refuses the cell; the answer
    proves the label; once approved, the next read takes the value from the cell."""
    import json
    from pathlib import Path

    from acfc_shapes import family_e_multi as fm
    from codegen.config import load_config
    from codegen.extract.frd_docx import extract_frd_contract

    repo = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(tmp_path / "state"))
    frd = tmp_path / "FRD.docx"
    frd.write_bytes(fm.build_frd(format_cell="Kind Of File: .txt\nDelimiter: Pipe Delimited"))

    def read():
        config = load_config(repo / "config" / "config.yaml")
        contract, _ = extract_frd_contract(frd, config, generated_date="2026-11-05")
        return config, contract

    config, contract = read()
    assert contract.feeds[0].file_format is None                   # refused: unknown label
    payload = json.loads(contract.model_dump_json(by_alias=True))
    proposals = voc.propose(payload, {"feeds[0].file_format": {"value": "txt"}},
                            known=config.extractor.frd.cell_line_labels)
    assert [p["label"] for p in proposals] == ["Kind Of File"]
    backend = voc.state_backend(config)
    voc.record(backend, proposals)
    assert read()[1].feeds[0].file_format is None                  # proposed is not applied
    voc.decide(backend, proposals[0]["id"], approve=True)
    _config, contract = read()
    assert (contract.feeds[0].file_format, contract.feeds[0].delimiter) == (
        ".txt", "Pipe Delimited")
