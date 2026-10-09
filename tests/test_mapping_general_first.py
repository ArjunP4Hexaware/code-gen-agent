"""Chunk A addendum (2026-10-09) — the legacy ``MAPPING-`` reader is not a
separate world.

Order for any workbook with ``MAPPING-`` sheets: the GENERAL reader first
(band row / label groups, layers by evidence, the band question, family B's
own source vocabulary on those sheets); its bands are used. The legacy reader
is the fallback when the general reader finds nothing, and the reference the
general reader is proven equal to: on every ``MAPPING-`` workbook in the
fixture set both readers place the same roles in the same columns, and the
profile ``discover`` returns is the legacy one byte for byte — so every
contract stays byte-identical. The legacy error text survives only at the
pinned flat entry point (``parse_workbook``).

Shapes: ``tests/acfc_shapes/bands.py::sd_mapping`` — the SD shape on a
family-B sheet, and the variants a hand-written sheet produces.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import pytest
import yaml

from acfc_shapes import bands
from acfc_shapes.common import xlsx_bytes
from codegen import cli
from codegen.extract import extract_contract
from codegen.extract.workbook import WorkbookParseError, parse_workbook
from codegen.layout import discover as discovery
from codegen.layout.extent import load_document
from codegen.layout.fingerprint import fingerprint
from test_band_detection import _keys, cli_env  # noqa: F401  (fixture re-export)
from test_extractor import _write_minimal_workbook

REPO = Path(__file__).resolve().parents[1]
SHEET = bands.MAPPING_SHEET
GENERATED = "2026-10-09"


def _write(tmp_path: Path, name: str, workbook) -> Path:
    path = tmp_path / f"{name}.xlsx"
    path.write_bytes(xlsx_bytes(workbook))
    return path


def _mapping_workbooks(tmp_path: Path) -> list[Path]:
    """Every MAPPING- workbook of the fixture set, plus the ones tests build."""
    tracked = [Path(p) for p in sorted(glob.glob(str(REPO / "fixtures" / "**" / "*.xlsx"),
                                                 recursive=True))]
    built = [_write_minimal_workbook(tmp_path / "minimal.xlsx"),
             _write(tmp_path, "sd_mapping", bands.sd_mapping())]
    out = []
    for path in [*tracked, *built]:
        names = load_document(path, 500).sheetnames
        if any(n.startswith("MAPPING-") for n in names):
            out.append(path)
    return out


def test_the_fixture_set_has_mapping_workbooks(tmp_path):
    names = {p.name for p in _mapping_workbooks(tmp_path)}
    assert {"pair_2_family_b.xlsx", "pair_11_family_b.xlsx", "minimal.xlsx",
            "sd_mapping.xlsx"} <= names


def test_general_and_legacy_readers_place_the_same_roles_in_the_same_columns(config, tmp_path):
    """Equivalence, every MAPPING- workbook: no difference in header / band
    rows, source / stage / standard roles, per-row columns, open roles — and
    discover() returns exactly the legacy profile."""
    ex = config.extractor
    for path in _mapping_workbooks(tmp_path):
        wb = load_document(path, ex.used_range_empty_rows)
        names = [n for n in wb.sheetnames if n.startswith(ex.mapping_sheet_prefix)]
        legacy = discovery._mapping_prefix(wb, ex, path.name, fingerprint(wb), [])
        general = discovery._content(wb, ex, path.name, fingerprint(wb), [])
        assert discovery.mapping_differences(legacy, general, names) == [], path.name
        found = discovery.discover(path, ex)
        assert found.profile.model_dump_json() == legacy.model_dump_json(), path.name


# ------------------------------------------------ the shapes of a hand-written sheet


def _contract(path: Path, tmp_path: Path, config, **frd):
    frd_path = tmp_path / "frd.json"
    frd_path.write_text(json.dumps(bands.frd_contract(**frd)), encoding="utf-8")
    return extract_contract(path, frd_path, config, generated_date=GENERATED)


def _fields(contract) -> list[tuple]:
    return [(f.source_column, f.stage_column, f.stage_datatype, f.standard_column,
             f.standard_datatype) for f in contract.feeds[0].fields]


@pytest.mark.parametrize("variant, rows, strategy", [
    ("titles", (2, 1), "mapping_prefix"),
    ("row3", (3, 2), "mapping_prefix"),
    ("unknown", (2, 1), "mapping_prefix"),
    ("unknown_required", (2, 1), "content"),
])
def test_hand_written_mapping_sheets_read_like_the_base(variant, rows, strategy, config,
                                                        tmp_path):
    """Other title wording, titles in row 2 / headers in row 3, one unknown
    header: the legacy reader refuses each; the general reader reads them and
    the contract carries the base sheet's fields. Where the legacy extractor
    still has every column it needs it reads the rows; an unknown header in
    a column it requires hands the sheet to the generic extractor."""
    base = _contract(_write(tmp_path, "base", bands.sd_mapping()), tmp_path, config)
    path = _write(tmp_path, variant, bands.sd_mapping(variant))
    found = discovery.discover(path, config.extractor)
    assert found.refused is not None                     # the legacy reader refused it
    sp = found.profile.sheet(SHEET)
    assert (found.profile.strategy, (sp.header_row, sp.band_row)) == (strategy, rows)
    assert found.profile.unresolved == []
    contract = _contract(path, tmp_path, config)
    assert _fields(contract) == _fields(base)
    assert contract.feeds[0].stage.table == bands.FEED
    if variant == "titles":
        assert {b.layer: b.layer_evidence for b in sp.bands
                if b.layer in ("stage", "standard")} == {"stage": "title", "standard": "title"}


def test_the_flat_entry_point_keeps_the_legacy_error(config, tmp_path):
    path = _write(tmp_path, "titles", bands.sd_mapping("titles"))
    with pytest.raises(WorkbookParseError, match="must carry the"):
        parse_workbook(path, config.extractor)


def test_the_base_sheet_contract_is_the_legacy_contract(config, tmp_path):
    """Contracts stay byte-identical: the general-first read of the base sheet
    produces the legacy reader's contract."""
    from codegen.extract.extractor import contract_to_json

    path = _write(tmp_path, "base", bands.sd_mapping())
    general_first = contract_to_json(_contract(path, tmp_path, config))
    legacy = discovery.discover(path, config.extractor, legacy_mapping=True).profile
    legacy_only = contract_to_json(extract_contract(
        path, tmp_path / "frd.json", config, generated_date=GENERATED, layout=legacy))
    assert general_first == legacy_only


# ------------------------------------------------ the band question on MAPPING- sheets


def test_the_band_question_applies_to_mapping_sheets(cli_env, capsys):  # noqa: F811
    tmp_path = cli_env
    workbook = _write(tmp_path, "STTM_untitled", bands.sd_mapping("untitled"))
    frd = tmp_path / "frd.contract.json"
    contract = bands.frd_contract(stage_schema="nb_land")
    frd.write_text(json.dumps(contract), encoding="utf-8")
    out_path = tmp_path / "sttm.contract.json"
    wanted = [f"{SHEET}/band[1]/layer", f"{SHEET}/band[2]/layer"]

    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(workbook), "--dry-run", "--no-cache",
                     "--require-complete"]) == cli.EXIT_NEEDS_ANSWERS
    assert _keys(capsys.readouterr().out, "UNRESOLVED") == wanted
    assert cli.main(["extract-sttm", "--workbook", str(workbook), "--frd-contract", str(frd),
                     "--out", str(out_path), "--generated-date", GENERATED]) \
        == cli.EXIT_NEEDS_ANSWERS
    out = capsys.readouterr().out
    assert _keys(out, "UNRESOLVED") == wanted and "answer under answers:" in out

    answers = tmp_path / "answers.yaml"
    answers.write_text(yaml.safe_dump({"answers": [
        {"sheet": SHEET, "layer": "band[1]", "role": "layer", "value": "stage"},
        {"sheet": SHEET, "layer": "band[2]", "role": "layer", "value": "standard"}]}),
        encoding="utf-8")
    assert cli.main(["extract-sttm", "--workbook", str(workbook), "--frd-contract", str(frd),
                     "--out", str(out_path), "--generated-date", GENERATED,
                     "--answers", str(answers)]) == cli.EXIT_OK
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["feeds"][0]["stage"]["schema"] == "nb_land"
    assert written["feeds"][0]["field_count"] == len(bands.FIELDS)
