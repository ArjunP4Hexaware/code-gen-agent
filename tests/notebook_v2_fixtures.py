"""post69: the synthetic pairs the notebook v2 tests run (contracts on disk,
the ACFC overlay on, the suite's synthetic D1 environment profile).

- ``sd_pair``: the CV golden pair — SD-shaped, three delimited feeds.
- ``sfmc_pair``: the SFMC fixture — one delimited feed.
- ``tpl_pair``: a CAQH-shaped single-table TPL feed — pipe-delimited, a header
  and a trailer record (FILE_FOOTER_FLAG Y), built from the SFMC contracts with
  every name replaced (synthetic).
- ``prx_pair``: pair 1 — PRX-shaped fixed width, three segments (HDDR / DET /
  TRLR), confirmed record-type discriminators (its FAQ).
"""

from __future__ import annotations

import json
from pathlib import Path

from codegen.config import load_config

REPO = Path(__file__).resolve().parents[1]
CONTRACTS = REPO / "fixtures" / "contracts"
ACFC_SHAPES = REPO / "fixtures" / "acfc_shapes"
ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"
PAIR1_OVERLAY = ACFC_SHAPES / "pair_1" / "config_overlay.yaml"


def acfc_config(tmp_path: Path, *extra: Path):
    """The shipped config + the ACFC overlay (+ ``extra``), outputs under tmp."""
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, *extra])
    return config.model_copy(update={"output": config.output.model_copy(
        update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})})


def sd_pair() -> tuple[Path, Path]:
    return (CONTRACTS / "FRD_demo_cv_golden.contract.json",
            CONTRACTS / "sttm_mapping_contracts_cv_golden.json")


def sfmc_pair() -> tuple[Path, Path]:
    return (CONTRACTS / "FRD_sfmc_email_campaign.contract.json",
            CONTRACTS / "sttm_mapping_contracts_sfmc.json")


TPL_FEED = "SYN TPL Inbound Files"


def tpl_pair(tmp_path: Path) -> tuple[Path, Path]:
    """A CAQH-shaped single-table TPL feed: the SFMC contracts renamed
    (feed, source, file pattern, tables), pipe-delimited."""
    frd = json.loads((CONTRACTS / "FRD_sfmc_email_campaign.contract.json").read_text(
        encoding="utf-8"))
    sttm = json.loads((CONTRACTS / "sttm_mapping_contracts_sfmc.json").read_text(
        encoding="utf-8"))
    from codegen.resolve.resolver import normalize_feed_name

    old_name = frd["feeds"][0]["feed_name"]
    old_id, new_id = normalize_feed_name(old_name), normalize_feed_name(TPL_FEED)

    def rename(node):
        if isinstance(node, dict):
            return {k: rename(v) for k, v in node.items()}
        if isinstance(node, list):
            return [rename(v) for v in node]
        if isinstance(node, str):
            return (node.replace(old_name, TPL_FEED).replace(old_id, new_id)
                    .replace("sfmc_member_outreach_email_tracking", "syn_tpl_inbound")
                    .replace("Salesforce Marketing Cloud", "SYN_TPL_VENDOR")
                    .replace("SFMC", "SYN_TPL").replace("sfmc", "syn_tpl"))
        return node

    frd, sttm = rename(frd), rename(sttm)
    for feed in frd["feeds"]:
        feed["delimiter"] = "|"
        feed["file_name_patterns"] = ["SYN_TPL_INBOUND_CCYYMMDD.txt"]
        feed["file_format"] = "txt"
    for feed in sttm["feeds"]:
        feed["source_file"].update(delimiter="|", format="txt",
                                   name_pattern="SYN_TPL_INBOUND_CCYYMMDD.txt")
    folder = tmp_path / "tpl_contracts"
    folder.mkdir(parents=True, exist_ok=True)
    paths = (folder / "frd.contract.json", folder / "sttm.contract.json")
    paths[0].write_text(json.dumps(frd, indent=2), encoding="utf-8")
    paths[1].write_text(json.dumps(sttm, indent=2), encoding="utf-8")
    return paths


def prx_pair(tmp_path: Path, config) -> tuple[Path, Path, Path]:
    """Pair 1 end to end (as tests/conftest.py pair1_spec): FRD + STTM + VDD
    contracts written under tmp."""
    from codegen.extract import contract_to_json as sttm_to_json
    from codegen.extract import extract_contract
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.extract.vdd import contract_to_json as vdd_to_json
    from codegen.extract.vdd import extract_vdd_contract
    from codegen.layout.model import MockLayoutProvider
    from codegen.layout.resolve import resolve_pair as resolve_layout_pair

    profiles = REPO / "fixtures" / "layout_profiles"
    folder = tmp_path / "prx_contracts"
    folder.mkdir(parents=True, exist_ok=True)
    provider = MockLayoutProvider([profiles / "mock", profiles])
    pair = resolve_layout_pair(
        ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx", ACFC_SHAPES / "frd" / "f1_pair_1.docx",
        config, provider=provider, cache_dirs=[folder / "cache"], generated_date="2026-01-01",
        vdd_path=ACFC_SHAPES / "vdd" / "pair_1_v1_segments.xlsx")
    frd = folder / "frd.contract.json"
    frd.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    sttm = folder / "sttm.contract.json"
    contract = extract_contract(ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx", frd, config,
                                generated_date="2026-01-01", layout=pair.sttm.profile)
    sttm.write_text(sttm_to_json(contract), encoding="utf-8")
    vdd = folder / "vdd.contract.json"
    vdd_contract, _ = extract_vdd_contract(ACFC_SHAPES / "vdd" / "pair_1_v1_segments.xlsx",
                                           config, generated_date="2026-01-01")
    vdd.write_text(vdd_to_json(vdd_contract), encoding="utf-8")
    return frd, sttm, vdd
