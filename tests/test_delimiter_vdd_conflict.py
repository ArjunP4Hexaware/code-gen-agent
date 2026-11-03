"""Audit #7 (2026-10-26, post126): a VDD that disagrees with the STTM on the
delimiter is a conflict, never the STTM value taken silently.

When the FRD states no delimiter, the resolver's gap chain fills it from the
other documents only when they agree — the same rule as the file format,
which already raised ``value.conflict`` on a disagreement. The delimiter
branch had no case for two distinct statements, so the STTM's character won
with no flag and no error (STTM '|' + VDD ',' -> '|').
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen.contracts.vdd import VddContract, VddFile
from codegen.extract import contract_to_json, extract_contract
from codegen.resolve.resolver import ContractMismatchError, resolve_pair


def _pair4(config, tmp: Path, *, sttm: str | None, vdd: str | None):
    """Pair 4 with the FRD's delimiter removed, the STTM meta row and the VDD
    FILES row stating ``sttm`` / ``vdd`` (None = the document is silent)."""
    from acfc_shapes import FIXTURE_ROOT, pair4_nb

    frd = json.loads((FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8"))
    frd["feeds"][0]["delimiter"] = None
    frd_path = tmp / "frd.contract.json"
    frd_path.write_text(json.dumps(frd), encoding="utf-8")
    contract = json.loads(contract_to_json(extract_contract(
        FIXTURE_ROOT / pair4_nb.STTM_PATH, frd_path, config, generated_date="2026-10-07")))
    for feed in contract["feeds"]:
        feed["meta_rows"].pop("delimiter", None)
        feed["source_file"]["delimiter"] = None
        if sttm is not None:
            # what extract/generic.py does: source_file.delimiter = the meta row
            feed["meta_rows"]["delimiter"] = sttm
            feed["source_file"]["delimiter"] = sttm
    sttm_path = tmp / "sttm.contract.json"
    sttm_path.write_text(json.dumps(contract), encoding="utf-8")
    vdd_contract = VddContract(
        contract_name="syn_vdd", generated_from_vdd="syn_vdd.xlsx", generated_date="2026-10-07",
        notes=[], field_sheets=[], fields=[], position_rows=[],
        files=[VddFile(pattern=None, title=None, format=None, delimiter=vdd, cadence=None,
                       description=None, field_sheet=None, multi_record=None,
                       record_type_field=None, header_row=None, row=3)])
    vdd_path = tmp / "vdd.contract.json"
    vdd_path.write_text(vdd_contract.model_dump_json(), encoding="utf-8")
    return frd_path, sttm_path, vdd_path


def test_an_sttm_and_a_vdd_that_disagree_stop_the_resolver_naming_both(pair4_config,
                                                                          tmp_path):
    frd, sttm, vdd = _pair4(pair4_config, tmp_path, sttm="|", vdd=",")
    with pytest.raises(ContractMismatchError) as exc:
        resolve_pair(frd, sttm, pair4_config, vdd_path=vdd)
    (error,) = [e for e in exc.value.errors if "delimiter" in e]
    assert "the FRD states no delimiter and the other documents disagree" in error
    assert "STTM" in error and "meta row 'delimiter' says '|'" in error
    assert "VDD FILES row 3 says ','" in error


@pytest.mark.parametrize("sttm,vdd", [("|", "|"), ("Pipe", "|"), ("|", None), (None, "|")])
def test_agreeing_or_single_statements_still_fill_the_delimiter(pair4_config, tmp_path,
                                                                 sttm, vdd):
    """The documents agreeing (as a character or a word) or only one stating
    it: filled, flagged frd_unstated:delimiter citing the cell used."""
    frd, sttm_path, vdd_path = _pair4(pair4_config, tmp_path, sttm=sttm, vdd=vdd)
    (spec,) = resolve_pair(frd, sttm_path, pair4_config, vdd_path=vdd_path)
    assert spec.delimiter == "|"
    assert any(f.startswith("frd_unstated:delimiter source_used:") for f in spec.provenance_flags)


@pytest.mark.parametrize("answer", ["|", ","])
def test_the_gaps_answer_the_error_names_settles_the_conflict(pair4_config, tmp_path, answer):
    """The conflict names ``feeds[0].delimiter`` under gaps:; either choice
    resolves, flagged as the user's answer."""
    frd, sttm, vdd = _pair4(pair4_config, tmp_path, sttm="|", vdd=",")
    (spec,) = resolve_pair(frd, sttm, pair4_config, vdd_path=vdd,
                           gaps={"feeds[0].delimiter": answer})
    assert spec.delimiter == answer
    assert any(f.startswith("frd_unstated:delimiter source_used:user")
               for f in spec.provenance_flags)
    overrides = [f for f in spec.provenance_flags if f.startswith("delimiter_answered:")]
    # siding with the VDD overrides the STTM's '|' - said, citing what it overrode
    assert overrides == ([] if answer == "|" else
                         ["delimiter_answered:',' — the answer overrides the STTM, which "
                          "states '|'"])
