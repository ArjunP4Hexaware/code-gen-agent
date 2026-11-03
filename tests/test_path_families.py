"""post86: path families - a source family's path convention beside the
template's own path_patterns (``default``).

The pair_11 prod golden writes one folder per table (``Reject/<table>/``,
``Processed/<table>/``, the stage -> standard archive inside it) where the SD
prod rows and the SFMC reference write ``Reject/<table>_reject`` and
``Processed/``. ``acfc_env.yaml`` ships the second as family ``per_table``;
which feeds use it is the ACFC overlay's ``path_family_by_source`` (client
source names) or ``feed_overrides.<feed>.path_family``.

Pinned on SYNTHETIC inputs only: pair 11 of the fixture universe (vendor
VENDOR_C), mapped to ``per_table`` by a test overlay.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from openpyxl import load_workbook

from acfc_shapes import sttm as sttm_fixtures
from codegen.config import PATH_FAMILY_DEFAULT, load_config
from codegen.metadata_template import path_family, with_path_family
from test_sd_scorecard_rules import RUN_STATEMENT, _generate

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
ACFC_ENV = REPO / "config" / "overlays" / "acfc_env.yaml"
ADLS, STG = "ADLS_DELTA_INGESTION_DETAILS", "STGDELTA_STDDELTA_INGESTION_DET"


def _overlay(tmp: Path, template: dict) -> Path:
    path = tmp / "overlay.yaml"
    path.write_text(yaml.safe_dump({"metadata": {"templates": {"iig_v2": template}}}),
                    encoding="utf-8")
    return path


def _template(tmp: Path, **template):
    return load_config(CONFIG, overlays=[ACFC_ENV, _overlay(tmp, template)]
                       ).metadata.templates["iig_v2"]


def _sheet(book, name: str) -> list[dict]:
    rows = list(book[name].iter_rows(values_only=True))
    return [dict(zip(rows[0], r, strict=True)) for r in rows[1:]]


def _tooltips(book, name: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for tab, _row, header, _badge, tooltip in book["_provenance"].iter_rows(min_row=2,
                                                                          values_only=True):
        if tab == name:
            out.setdefault(header, []).append(tooltip or "")
    return out


# --- resolution -------------------------------------------------------------

def test_the_feed_override_wins_over_the_source_and_the_source_over_the_default(tmp_path):
    tpl = _template(tmp_path, path_family_by_source={"vendor_c": "per_table"},
                    feed_overrides={"feed_b": {"path_family": "default"}})
    assert path_family(tpl, "feed_a", "VENDOR_C – VC 00000")[0] == "per_table"
    assert path_family(tpl, "feed_b", "VENDOR_C – VC 00000") == (
        PATH_FAMILY_DEFAULT, "feed_overrides.feed_b.path_family")
    assert path_family(tpl, "feed_a", "Vendor D")[0] == PATH_FAMILY_DEFAULT


def test_a_source_key_matches_whole_leading_words_only(tmp_path):
    tpl = _template(tmp_path, path_family_by_source={"vendor c": "per_table"})
    assert path_family(tpl, None, "  vendor   C (Supplier ID 1)")[0] == "per_table"
    assert path_family(tpl, None, "Vendor Co")[0] == PATH_FAMILY_DEFAULT       # not a word end
    assert path_family(tpl, None, "The Vendor C")[0] == PATH_FAMILY_DEFAULT    # not leading
    assert path_family(tpl, None, None)[0] == PATH_FAMILY_DEFAULT


def test_the_longest_source_key_wins(tmp_path):
    overlay = {"path_families": {"other": {"citation": "test", "path_patterns": {
        ADLS: {"TGT_RJT_ADLS_PATH": "/x/"}}}},
        "path_family_by_source": {"vendor": "other", "vendor c": "per_table"}}
    tpl = _template(tmp_path, **overlay)
    assert path_family(tpl, None, "Vendor C")[0] == "per_table"
    assert path_family(tpl, None, "Vendor D")[0] == "other"


def test_a_family_replaces_only_the_shapes_it_names(tmp_path):
    tpl = _template(tmp_path, path_family_by_source={"vendor_c": "per_table"})
    applied = with_path_family(tpl, None, "VENDOR_C")
    assert applied.path_patterns[ADLS]["TGT_RJT_ADLS_PATH"] == "/{domain_path}Reject/{stage_table}/"
    assert applied.path_patterns[ADLS]["SRC_ADLS_PATH"] == tpl.path_patterns[ADLS]["SRC_ADLS_PATH"]
    assert "path family per_table" in applied.path_citations[ADLS]["TGT_RJT_ADLS_PATH"]
    # a shape the family does not name keeps the template's citation, labelled
    assert applied.path_citations[ADLS]["SRC_ADLS_PATH"].startswith(
        tpl.path_citations[ADLS]["SRC_ADLS_PATH"] + " — path family per_table")


def test_a_template_without_families_is_unchanged():
    tpl = load_config(CONFIG).metadata.templates["iig_v2"]
    assert not tpl.path_families
    assert with_path_family(tpl, "feed", "VENDOR_C") is tpl


@pytest.mark.parametrize(("template", "message"), [
    ({"path_family_by_source": {"vendor_c": "nope"}}, "path_family_by_source.vendor_c"),
    ({"feed_overrides": {"f": {"path_family": "nope"}}}, "feed_overrides.f.path_family"),
    ({"path_families": {"default": {"citation": "x", "path_patterns": {}}}}, "reserved"),
    ({"path_families": {"x": {"citation": "x", "path_patterns": {"NO_SHEET": {}}}}},
     "not a sheet"),
    ({"path_families": {"x": {"citation": "", "path_patterns": {}}}}, "citation"),
])
def test_a_wrong_family_fails_when_the_config_loads(tmp_path, template, message):
    with pytest.raises(ValueError, match=message):
        _template(tmp_path, **template)


# --- the workbook and the notebook ------------------------------------------

def _run(tmp: Path, template: dict):
    config = load_config(CONFIG, overlays=[ACFC_ENV, _overlay(tmp, template)])
    gates = _generate(config, sttm_fixtures.build_pair11(), tmp, run_statement=RUN_STATEMENT)
    return {slug: load_workbook(tmp / "out" / slug / "framework" / "config_rows.xlsx")
            for slug in gates}


@pytest.fixture(scope="module")
def per_table(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("per_table"),
                {"path_family_by_source": {"vendor_c": "per_table"}})


@pytest.fixture(scope="module")
def default(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("default"), {})


def test_per_table_writes_one_folder_per_table_on_both_sheets(per_table):
    for book in per_table.values():
        for row in _sheet(book, ADLS):
            table = row["TGT_TABLE_NAME"]
            assert row["TGT_ADLS_PATH"].endswith(f"/Processed/{table}/")
            assert row["TGT_RJT_ADLS_PATH"].endswith(f"/Reject/{table}/")
        for row in _sheet(book, STG):
            table = row["TGT_TABLE_NAME"]
            assert row["SRC_ADLS_PATH"].endswith(f"/Processed/{table}/")
            assert row["SRC_ADLS_ARCHVL_PATH"].endswith(f"/Processed/{table}/Archive/")
            assert row["TGT_ADLS_PATH"].endswith(f"/Processed/{table}/")
            assert row["TGT_RJT_ADLS_PATH"].endswith(f"/Reject/{table}/")
        tips = _tooltips(book, ADLS)["TGT_RJT_ADLS_PATH"]
        assert tips and all("path family per_table (path_family_by_source" in t for t in tips)


def test_the_default_keeps_its_shapes_and_says_which_family(default, per_table):
    assert set(default) == set(per_table)
    for book in default.values():
        for row in _sheet(book, ADLS):
            table = row["TGT_TABLE_NAME"]
            assert row["TGT_RJT_ADLS_PATH"].endswith(f"/Reject/{table}_reject")
        for row in _sheet(book, STG):
            assert row["TGT_ADLS_PATH"].endswith("/Processed/")
        tips = _tooltips(book, ADLS)["TGT_RJT_ADLS_PATH"]
        assert tips and all("path family default" in t for t in tips)


def test_the_landing_cells_are_the_same_in_both_families(default, per_table):
    for slug, book in default.items():
        for a, b in zip(_sheet(book, ADLS), _sheet(per_table[slug], ADLS), strict=True):
            assert (a["SRC_ADLS_PATH"], a["SRC_ADLS_ARCHVL_PATH"]) == (
                b["SRC_ADLS_PATH"], b["SRC_ADLS_ARCHVL_PATH"])


def test_the_notebook_reject_path_follows_the_family(tmp_path):
    from codegen.metadata_template import notebook_paths

    config = load_config(CONFIG, overlays=[ACFC_ENV, _overlay(
        tmp_path, {"path_family_by_source": {"vendor_c": "per_table"}})])
    tpl = config.metadata.templates["iig_v2"]
    spec = _spec(tmp_path, config)
    reject, _container = notebook_paths(tpl, spec)["reject_path"]
    assert "/Reject/" in reject and reject.endswith("/") and not reject.endswith("_reject/")


def _spec(tmp: Path, config):
    from acfc_shapes.common import xlsx_bytes
    from codegen.extract import contract_to_json as sttm_to_json
    from codegen.extract import extract_contract
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.layout.model import MockLayoutProvider
    from codegen.layout.resolve import resolve_pair
    from codegen.resolve.resolver import resolve_pair as resolve_contracts
    from test_sd_scorecard_rules import DATE, PAIR_11_FRD

    sttm = tmp / "sttm.xlsx"
    sttm.write_bytes(xlsx_bytes(sttm_fixtures.build_pair11()))
    pair = resolve_pair(sttm, PAIR_11_FRD, config, provider=MockLayoutProvider([]),
                        cache_dirs=[], use_cache=False, generated_date=DATE)
    frd_json = tmp / "frd.contract.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    contract = extract_contract(sttm, frd_json, config, generated_date=DATE,
                                layout=pair.sttm.profile)
    sttm_json = tmp / "sttm.contract.json"
    sttm_json.write_text(sttm_to_json(contract), encoding="utf-8")
    return resolve_contracts(frd_json, sttm_json, config)[0]
