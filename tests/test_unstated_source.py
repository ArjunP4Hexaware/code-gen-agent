"""Audit #5 (2026-10-26, post125): an FRD that names no source never puts the
word 'unstated' in an artefact.

The .docx reader stores the placeholder ``unstated`` when no Data Source /
Vendor label is found (``FrdFeed.source_system`` is a required string). It is
a placeholder, never a name: every artefact leaves the source BLANK and
flagged (``iig_blank:`` + the review's "no input states it"), never the word
badged ``from_frd``. Before the fix pair 4 with that FRD wrote ``unstated``
into the IIG SOURCE column, config_rows / config_inserts, metadata_inserts.sql
(``N'unstated'``) and the v2 notebook's title table.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from codegen import cli
from codegen.contracts.frd import UNSTATED_SOURCE, FrdContract, stated_source
from codegen.extract import contract_to_json, extract_contract
from codegen.resolve.resolver import resolve_pair
from test_m4_acceptance import _scoped

# the bare word, not a flag name (frd_unstated:, recycle_unstated, value.unstated)
_BARE = re.compile(r"(?i)(?<![_a-z.])unstated(?![_a-z:])")


def _pair4_unsourced(config, tmp: Path):
    from acfc_shapes import FIXTURE_ROOT, pair4_nb

    frd = json.loads((FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8"))
    frd["feeds"][0]["source_system"] = UNSTATED_SOURCE        # what the .docx reader writes
    frd_path = tmp / "frd.contract.json"
    frd_path.write_text(json.dumps(frd), encoding="utf-8")
    sttm = extract_contract(FIXTURE_ROOT / pair4_nb.STTM_PATH, frd_path, config,
                            generated_date="2026-10-07")
    sttm_path = tmp / "sttm.contract.json"
    sttm_path.write_text(contract_to_json(sttm), encoding="utf-8")
    (spec,) = resolve_pair(frd_path, sttm_path, config)
    return spec, FrdContract.model_validate(frd).feeds[0]


def _text(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix == ".xlsx":
        with zipfile.ZipFile(path) as book:
            data = b"".join(book.read(n) for n in book.namelist())
    return data.decode("utf-8", "replace")


def test_stated_source_reads_the_placeholder_as_none():
    assert stated_source(UNSTATED_SOURCE) is None
    assert stated_source("  Unstated ") is None
    assert stated_source("") is None and stated_source(None) is None
    assert stated_source(" Northwind Benefits ") == "Northwind Benefits"


def test_no_artefact_of_an_unsourced_feed_carries_the_placeholder(pair4_config, tmp_path):
    spec, _feed = _pair4_unsourced(pair4_config, tmp_path)
    for mode in ("framework", "notebook"):
        cli._generate_feed(spec, _scoped(pair4_config, tmp_path / mode), dry_run=True,
                           skip_tests=True, output_mode=mode, conventions_profile="acfc_prx",
                           iig_template="iig_v2")
    hits = sorted({str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")
                   if p.is_file() and not p.name.endswith(".contract.json")
                   and _BARE.search(_text(p))})
    assert hits == []
    # the SOURCE cells are blank AND flagged, routed to the BSA
    report = (tmp_path / "framework" / "reports" / f"{spec.feed_slug}.md").read_text(
        encoding="utf-8")
    assert re.search(r"iig_blank:ADLS_DELTA_INGESTION_DETAILS: [^\n]*\bSOURCE\b", report)


def test_the_iig_v2_source_cell_is_blank_needs_template():
    from codegen.metadata_template import _source_cell, _source_value

    feed = _feed_with(UNSTATED_SOURCE)
    cell = _source_cell(feed)
    assert cell["value"] == "" and cell["badge_entry"]["badge"] == "needs_template"
    assert "states no source" in cell["badge_entry"]["tooltip"]
    assert _source_value(feed) == ""


def test_the_iig_v1_source_cells_are_blank_needs_template():
    from codegen.metadata_sheet import _source_system_cell

    blank = _source_system_cell(_feed_with(UNSTATED_SOURCE))
    assert blank["value"] == "" and blank["badge_entry"]["badge"] == "needs_template"
    named = _source_system_cell(_feed_with("Northwind Benefits"))
    assert named["value"] == "Northwind Benefits"
    assert named["badge_entry"]["badge"] == "from_frd"


def test_a_name_token_never_spells_the_placeholder():
    from codegen.config import EngineeringStandardsConfig
    from codegen.emit.context import _name_components
    from codegen.faq import LoadPatternFaq

    parts = _name_components(EngineeringStandardsConfig(), LoadPatternFaq(), "syn_feed",
                             source=UNSTATED_SOURCE, domain=None, sub_domain=None, lobs=[])
    assert parts["source"] == ""


def _feed_with(source: str):
    from acfc_shapes import FIXTURE_ROOT, pair4_nb

    frd = json.loads((FIXTURE_ROOT / pair4_nb.FRD_PATH).read_text(encoding="utf-8"))
    frd["feeds"][0]["source_system"] = source
    return FrdContract.model_validate(frd).feeds[0]

