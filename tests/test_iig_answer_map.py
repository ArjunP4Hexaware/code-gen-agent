"""P3 (post218): the question dialog's "Fills in the IIG" line is MEASURED, not assumed.

``layout.hints.FRD_FIELD_IIG`` says which IIG cells an FRD answer fills. These tests
change each field on the synthetic CV pair (fixtures/contracts/*cv_golden*), run the
real path (resolve_pair -> metadata_sheet_payload, template iig_v2) under the ACFC
overlay - the App's config (load_config always applies it; only this suite skips it) -
and compare: every cell ``iig_uses`` lists must move, and every DIRECT cell that moves
must be listed (generated-text columns - descriptions, names, email text - are
summarised by the ``text`` flag instead). The base config differs (LOB is left blank
by its family convention, the FILE_ADLS sheet gets rows): its LOB case is checked.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.layout.hints import FRD_FIELD_IIG, IIG_TEXT_COLUMNS, NOT_IN_IIG, iig_uses
from codegen.metadata_sheet import metadata_sheet_payload
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]
FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"
TEMPLATE = "iig_v2"

# field -> a different value of the same type (synthetic)
ALT = {
    "source_system": "Other Vendor (OV)",
    "frequency": "Weekly",
    "lobs": ["Medicaid"],
    "domain": "Pharmacy",
    "sub_domain": "Accumulators",
    "stage_target.load_strategy": "Append",
    "standard_target.load_strategy": "Upsert",
    "landing_location": "/mnt/other/landing/path",
}

pytestmark = pytest.mark.skipif(not (FRD.is_file() and STTM.is_file()),
                                reason="the synthetic CV contract pair is not present")


def _set(contract: dict, path: str, value) -> dict:
    contract = copy.deepcopy(contract)
    for feed in contract["feeds"]:
        node = feed
        *parents, leaf = path.split(".")
        for part in parents:
            node = node[part]
        node[leaf] = value
    return contract


def _cells(config, contract: dict, tmp_path: Path, name: str) -> dict:
    frd = tmp_path / f"{name}.json"
    frd.write_text(json.dumps(contract), encoding="utf-8")
    specs = resolve_pair(frd, STTM, config)
    payload = metadata_sheet_payload(config, REPO, specs=specs, frd_path=frd, template=TEMPLATE)
    return {(tab, i, header): json.dumps(value, sort_keys=True, default=str)
            for tab, entry in payload["tabs"].items()
            for i, row in enumerate(entry["rows"])
            for header, value in row["values"].items()}


def _moved(before: dict, after: dict) -> set[tuple[str, str]]:
    return {(tab, header) for tab, _i, header in before.keys() | after.keys()
            if before.get((tab, _i, header)) != after.get((tab, _i, header))}


@pytest.fixture(scope="module")
def config():
    return load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY])


@pytest.fixture(scope="module")
def base_config():
    return load_config(REPO / "config" / "config.yaml")


@pytest.fixture(scope="module")
def reference(config, tmp_path_factory):
    contract = json.loads(FRD.read_text(encoding="utf-8"))
    return contract, _cells(config, contract, tmp_path_factory.mktemp("ref"), "ref")


def test_every_measured_field_has_a_probe_value():
    # a field added to the map without a probe value here would go unchecked
    assert set(FRD_FIELD_IIG) == set(ALT)


@pytest.mark.parametrize("field", sorted(ALT))
def test_the_listed_cells_are_exactly_the_cells_the_answer_moves(field, config, reference,
                                                                 tmp_path):
    contract, before = reference
    after = _cells(config, _set(contract, field, ALT[field]), tmp_path, field)
    moved = _moved(before, after)
    uses = iig_uses(f"feeds[0].{field}", config, TEMPLATE)
    assert uses is not None and uses["note"] is None, field
    listed = {(c["sheet"], c["column"]) for c in uses["cells"]}
    direct = {cell for cell in moved if cell[1] not in IIG_TEXT_COLUMNS}
    assert direct == listed, (f"{field}: not named {direct - listed}; "
                              f"named but not moved {listed - direct}")
    assert uses["text"] == any(cell[1] in IIG_TEXT_COLUMNS for cell in moved), field


def test_a_lob_answer_is_not_claimed_where_the_family_leaves_lob_blank(base_config, tmp_path):
    _name, tpl = base_config.metadata.resolve(TEMPLATE)
    assert tpl.family_conventions.lob == "blank"
    contract = json.loads(FRD.read_text(encoding="utf-8"))
    before = _cells(base_config, contract, tmp_path, "lob_ref")
    after = _cells(base_config, _set(contract, "lobs", ALT["lobs"]), tmp_path, "lob_alt")
    assert not {c for c in _moved(before, after) if c[1] == "LOB"}
    uses = iig_uses("feeds[0].lobs", base_config, TEMPLATE)
    assert uses["cells"] == [] and "left blank" in uses["note"]
    assert uses["note"].startswith("not written")


@pytest.mark.parametrize("patterns", [None, ["extract_YYYY_MM"]],
                         ids=["pattern_with_extension", "pattern_without_extension"])
def test_the_file_format_fills_no_iig_cell(patterns, config, tmp_path):
    contract = json.loads(FRD.read_text(encoding="utf-8"))
    if patterns is not None:
        contract = _set(contract, "file_name_patterns", patterns)
    before = _cells(config, contract, tmp_path, "fmt_ref")
    after = _cells(config, _set(contract, "file_format", "json"), tmp_path, "fmt_alt")
    assert _moved(before, after) == set()
    uses = iig_uses("feeds[0].file_format", config, TEMPLATE)
    assert uses == {"cells": [], "text": False, "note": NOT_IN_IIG["file_format"]}


def test_no_iig_line_where_nothing_was_measured(config):
    for key in ("feeds[0].feed_name", "feeds[0].delimiter", "feeds[0].recycle_rule",
                "feeds[0].stage_target.schema", "feeds[0].archive_retention",
                "project.frequency", "Mapping/stage/field_name"):
        assert iig_uses(key, config, TEMPLATE) is None, key
    # a template the map was not measured on (v1 builds its rows elsewhere), an unknown one
    assert iig_uses("feeds[0].domain", config, "iig_v1") is None
    assert iig_uses("feeds[0].domain", config, "no_such_template") is None


def test_the_app_serves_the_iig_line_on_frd_questions_only(config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import with_iig

    frd_q = {"document": "frd", "key": "feeds[0].frequency", "kind": "role"}
    served = with_iig(frd_q, config, TEMPLATE)
    assert served["iig"] == iig_uses("feeds[0].frequency", config, TEMPLATE)
    assert "iig" not in frd_q                                   # the stored question is untouched
    for q in ({"document": "frd", "key": "feeds[0].feed_name"},   # nothing measured
              {"document": "sttm", "key": "MAP/band[1]/layer"},   # not an FRD field
              {"document": "run", "key": "run.environment.storage_account"}):
        assert "iig" not in with_iig(q, config, TEMPLATE), q["key"]
