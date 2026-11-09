"""post186 (Soham, 2026-11-09): the Naming Standards' Product (3.2) / Sub-Product (3.3)
codes are READ from the FRD through the tables, never the DLK / NSP constants.

Product = the 3.2 entry the FRD ingests INTO; a consumer mention is not it. Sub-product
= a 3.3 entry the FRD names; none = the table's "No Sub-Product" code WITH a flag.
None / several = open: the names that carry the code are not written (asked).
Synthetic text only."""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.emit.context import resolve_job_name
from codegen.naming_codes import find_naming, resolve_codes, spec_codes

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def standards():
    return load_config(REPO / "config" / "config.yaml").engineering_standards


def _codes(standards, *texts):
    lines = [(f"paragraph {i}", t) for i, t in enumerate(texts, 1)]
    return resolve_codes(find_naming(lines, standards), standards)


def test_the_tables_are_transcribed_and_no_constant_is_left(standards):
    assert standards.product_code == "" and standards.sub_product_code == ""
    assert {e.code for e in standards.product_codes} >= {"DLK", "HDS", "EDH", "MDM"}
    assert [e.code for e in standards.sub_product_codes] == [
        "BCL", "LTL", "HVR", "FHR", "BDS", "FCT"]
    assert standards.no_sub_product_code == "NSP"


def test_the_product_is_what_the_frd_ingests_into(standards):
    product, _sub, flags = _codes(standards, "Scope", "Vendor files ingested into Lakehouse.")
    assert product == "DLK"
    flag = next(f for f in flags if f.startswith("naming_product:"))
    assert "paragraph 2" in flag and "ingested into Lakehouse" in flag      # cited
    assert _codes(standards, "Claims Ingestion to DL 2.0")[0] == "DLK"


def test_a_consumer_mention_is_not_the_product(standards):
    product, _sub, flags = _codes(standards, "Claims for HEDIS Consumption",
                                  "Quality checks (only for BSL and EDH)")
    assert product is None
    assert any(f.startswith("naming_product_unstated:") for f in flags)


def test_two_ingestion_targets_pick_none(standards):
    product, _sub, flags = _codes(standards, "Loaded into Lakehouse", "then into EDH")
    assert product is None
    assert any(f.startswith("naming_product_ambiguous:") for f in flags)


def test_a_named_sub_product_is_its_code_with_the_line(standards):
    _p, sub, flags = _codes(standards, "Data ingested into Lakehouse",
                            "Enable change data capture via HVR tool")
    assert sub == "HVR"
    flag = next(f for f in flags if f.startswith("naming_sub_product:"))
    assert "paragraph 2" in flag and "HVR tool" in flag


def test_no_sub_product_named_is_nsp_with_a_flag(standards):
    _p, sub, flags = _codes(standards, "Data ingested into Lakehouse",
                            "Volumes are forecast to grow")       # an ordinary word
    assert sub == "NSP"
    assert any(f.startswith("naming_sub_product_unstated:NSP") for f in flags)


def test_two_sub_products_pick_none(standards):
    _p, sub, flags = _codes(standards, "via HVR tool", "exposed as FHIR resources")
    assert sub is None
    assert any(f.startswith("naming_sub_product_ambiguous:") for f in flags)


def test_a_word_inside_another_is_no_match(standards):
    assert _codes(standards, "ingested into DLX staging")[0] is None     # not "DL"
    assert _codes(standards, "the HVRX tool")[1] == "NSP"


def test_names_use_the_feeds_codes_and_stay_open_without_them(standards):
    from codegen.faq import FaqAnswer, LoadPatternFaq

    class Spec:
        product_code, sub_product_code = "DLK", "HVR"

    class Open:
        product_code = sub_product_code = None

    assert spec_codes(Spec, standards) == ("DLK", "HVR")
    assert spec_codes(Open, standards) == ("", "")
    faq = LoadPatternFaq(load_frequency=FaqAnswer(value="daily", source="contract"))
    name = resolve_job_name(standards, faq, "feed_x", source="FACETS",
                            codes=spec_codes(Spec, standards))
    assert name.startswith("WF_DLK_HVR_")
    assert resolve_job_name(standards, faq, "feed_x", source="FACETS",
                            codes=spec_codes(Open, standards)).startswith("WF_FEED_X")


def test_a_config_without_the_tables_keeps_its_constants(standards):
    legacy = standards.model_copy(update={"product_codes": [], "sub_product_codes": [],
                                          "product_code": "AAA", "sub_product_code": "BBB"})
    assert resolve_codes({}, legacy) == ("AAA", "BBB", [])

    class Spec:
        product_code = sub_product_code = None

    assert spec_codes(Spec, legacy) == ("AAA", "BBB")


# ---- the names' provenance in the feed report and the run's LOG.md (post186) ------


def _framework_run(tmp_path, naming=None, extra=None):
    import json

    import test_sttm_authoritative_tables as T

    frd, sttm = T._family_e(tmp_path, lambda old: old)
    if naming is not None:
        data = json.loads(frd.read_text(encoding="utf-8"))
        data["naming"] = naming
        frd.write_text(json.dumps(data), encoding="utf-8")
    env = T._env(tmp_path)
    env.pop("CODEGEN_SKIP_ENV_OVERLAY", None)        # the ACFC pipeline-name rules
    done = T._run(["generate", "--config", str(T.CONFIG), "--frd", str(frd), "--sttm",
                   str(sttm), "--dry-run", "--skip-tests", "--output-mode", "framework",
                   "--profile", "acfc_prx", "--iig-template", "iig_v2", *(extra or [])],
                  env, REPO)
    report = "".join(p.read_text("utf-8") for p in (tmp_path / "reports").rglob("*.md"))
    log = "".join(p.read_text("utf-8") for p in (tmp_path / "out").rglob("*_LOG.md"))
    return done, report, log


def _section(text: str) -> str:
    start = text.index("## How the names were built")
    end = text.find("\n## ", start + 3)
    return text[start:end if end > 0 else None]


def test_an_open_pipeline_name_is_sourced_part_by_part(tmp_path):
    done, report, log = _framework_run(tmp_path)
    assert done.returncode in (0, 3), done.stdout + done.stderr
    for text in (report, log):
        section = _section(text)
        for flow in ("grand_master", "master", "file_to_stg", "stg_to_std"):
            assert f"PIPELINE_NAME [{flow}] is OPEN" in section
        assert "pipeline_name_templates.file_to_stg" in section          # the config key
        assert "{product_code} = `` ← OPEN" in section                   # why it is open
        assert "{sub_product_code} = `NSP` ← " in section
        assert "'No Sub-Product' code" in section
        assert "{source_std} = " in section and "FRD source system" in section
        assert "{load_std} = " in section and "FRD Load Strategy (STG)" in section


def test_a_written_pipeline_name_cites_the_frd_line_of_each_code(tmp_path):
    naming = {"product": {"codes": ["DLK"], "entries": ["Data Lake"],
                          "quotes": ["paragraph 4: 'Synthetic files ingested into Lakehouse'"]},
              "sub_product": {"codes": ["HVR"], "entries": ["HVR"],
                              "quotes": ["paragraph 9: 'CDC via HVR tool'"]}}
    done, report, log = _framework_run(tmp_path, naming)
    assert done.returncode in (0, 3), done.stdout + done.stderr
    for text in (report, log):
        section = _section(text)
        line = next(x for x in section.splitlines() if "PIPELINE_NAME [file_to_stg]" in x)
        assert "= `PL_CHLD_DLK_HVR_RAW_TO_STG_" in line
        assert "written unasked (pipeline_name_autoset)" in line
        assert ("{product_code} = `DLK` ← Naming Standards 3.2 'Data Lake', from the FRD: "
                "paragraph 4: 'Synthetic files ingested into Lakehouse'") in section
        assert ("{sub_product_code} = `HVR` ← Naming Standards 3.3 'HVR', from the FRD: "
                "paragraph 9: 'CDC via HVR tool'") in section
