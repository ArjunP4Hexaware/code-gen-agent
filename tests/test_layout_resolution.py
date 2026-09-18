"""M2.5 — layout recognition: cache → synonyms → model → validate → user,
pair-level cross-checks, and the guarantee that no model string reaches an
artefact.

Fixtures: fixtures/layout_profiles/ (the correct profile of every M0
fixture — repo cache and mock answers) and fixtures/layout_profiles/mock/
(adversarial answers). Tests point the cache at an empty directory when the
model path is what they exercise.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from acfc_shapes.layout_truth import ADVERSARIAL, CANARY, STTM_CURATED
from codegen.extract import extract_contract
from codegen.extract.generic import read_workbook
from codegen.layout.model import MockLayoutProvider
from codegen.layout.profile import LayoutProfile
from codegen.layout.resolve import discovery_for, resolve_pair, resolve_workbook
from segmented_fixture import frd_contract_dict

REPO = Path(__file__).resolve().parents[1]
STTM = REPO / "fixtures" / "acfc_shapes" / "sttm"
FRD = REPO / "fixtures" / "acfc_shapes" / "frd"
VDD = REPO / "fixtures" / "acfc_shapes" / "vdd"
PROFILES = REPO / "fixtures" / "layout_profiles"
MOCK = PROFILES / "mock"

FULL_BY_SYNONYMS = ["pair_2_family_b.xlsx", "pair_4_family_d.xlsx", "pair_6_family_d.xlsx",
                    "pair_5_family_e.xlsx", "pair_9_family_e.xlsx"]
NEEDS_MODEL = ["pair_1_family_a.xlsx", "pair_8_family_a.xlsx", "pair_7_family_e.xlsx",
               "pair_10_family_e.xlsx"]


@pytest.fixture()
def mock():
    return MockLayoutProvider([MOCK, PROFILES])


@pytest.fixture()
def no_cache(tmp_path):
    empty = tmp_path / "empty_cache"
    empty.mkdir()
    return [empty]


# ------------------------------------------------- fixtures are what the builder builds


def test_tracked_layout_profiles_equal_a_fresh_build():
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from build_layout_profiles import build_all

    built = build_all()
    for rel, text in built.items():
        path = PROFILES / rel
        assert path.is_file(), rel
        assert path.read_text(encoding="utf-8") == text, f"{rel} drifted"
    from acfc_shapes.layout_truth import VDD_ADVERSARIAL, VDD_CURATED

    assert len(built) == (len(STTM_CURATED) + 3 + len(ADVERSARIAL)
                          + len(VDD_CURATED) + len(VDD_ADVERSARIAL))


# ------------------------------------------------- (a) synonyms alone + cache path


@pytest.mark.parametrize("name", FULL_BY_SYNONYMS)
def test_synonyms_resolve_families_b_d_and_e_without_a_provider_call(name, config, mock,
                                                                    no_cache, tmp_path):
    runtime = tmp_path / "runtime"
    doc, _ = resolve_workbook(STTM / name, config, provider=mock, cache_dirs=no_cache,
                              runtime_cache_dir=runtime)
    assert doc.profile.source == "synonyms" and doc.complete
    assert doc.provider_calls == 0 and mock.requests == []
    assert doc.sources["model"] == 0 and doc.sources["synonyms"] > 0
    # Second run hits the repo cache (the tracked correct profile): zero calls.
    cached, _ = resolve_workbook(STTM / name, config, provider=mock,
                                 cache_dirs=[PROFILES], runtime_cache_dir=runtime)
    assert cached.cache_hit and cached.profile.source == "cache"
    assert cached.provider_calls == 0 and mock.requests == []


# ------------------------------------------------- (b) model path resolves A / C / E


@pytest.mark.parametrize("name", NEEDS_MODEL)
def test_mock_model_resolves_the_remainder_and_extraction_matches_the_truth(
        name, config, mock, no_cache, tmp_path):
    runtime = tmp_path / "runtime"
    doc, workbook = resolve_workbook(STTM / name, config, provider=mock, cache_dirs=no_cache,
                                     runtime_cache_dir=runtime)
    assert doc.provider_calls == 1 and len(mock.requests) == 1
    assert doc.complete, [f"{u.sheet}/{u.layer}/{u.role}" for u in doc.profile.unresolved]
    assert doc.profile.source == "model" and doc.rejections == []
    assert doc.sources["model"] == len(STTM_CURATED[name])
    assert doc.sources["synonyms"] > 0
    # Model-placed roles start at the configured confidence, synonyms at 1.0.
    for key, source in doc.profile.role_sources.items():
        assert doc.profile.confidence[key] == (
            config.layout.model_confidence if source == "model" else 1.0)
    # Reading through the completed profile matches the M1 truth tables:
    # rows per band are non-zero on every mapping sheet (pairs 8 and 10
    # included — the band detection holds once field_name is placed).
    ir = read_workbook(discovery_for(doc.profile, workbook), name, config)
    for sheet in ir.sheets:
        assert sheet.fields, sheet.profile.name
    truth = LayoutProfile.model_validate_json(
        (PROFILES / f"sttm_{Path(name).stem}.layout.json").read_text(encoding="utf-8"))
    for sp in doc.profile.mapping_sheets:
        truth_sheet = truth.sheet(sp.name)
        assert truth_sheet is not None
        assert ({b.layer: b.roles for b in sp.bands}
                == {b.layer: b.roles for b in truth_sheet.bands})
    # Completed → saved to the runtime cache under the fingerprint.
    assert (runtime / f"{doc.fingerprint}.json").is_file()


def test_pairs_8_and_10_rows_per_band_after_resolution(config, mock, no_cache):
    expected = {
        "pair_8_family_a.xlsx": {"FEED_8_LAYOUT": {"Header": 4, "Detail": 8, "Trailer": 3,
                                                   "File Trailer": 2}},
        "pair_10_family_e.xlsx": {"Outbound_REGION_A": {"-": 10}, "Inbound_REGION_A": {"-": 12},
                                  "Inbound_REGION_B_Adult": {"-": 10},
                                  "Inbound_REGION_B_Child": {"-": 10}},
    }
    for name, sheets in expected.items():
        doc, workbook = resolve_workbook(STTM / name, config, provider=mock, cache_dirs=no_cache)
        ir = read_workbook(discovery_for(doc.profile, workbook), name, config)
        assert {s.profile.name: s.rows_per_segment() for s in ir.sheets} == sheets


# ------------------------------------------------- the model never sees a data row


def test_model_request_carries_header_regions_only(config, no_cache, tmp_path):
    source = STTM / "pair_1_family_a.xlsx"
    wb = load_workbook(source)
    canary = "DATA_ROW_CANARY_5c1e"
    wb["FEED_1_MAPPING"].cell(row=20, column=9, value=canary)     # a data row (header is r15)
    wb["FEED_1_MAPPING"].cell(row=41, column=3, value=canary)     # an audit row
    path = tmp_path / "pair_1_canary.xlsx"
    wb.save(path)
    recorder = MockLayoutProvider([MOCK, PROFILES])
    doc, _ = resolve_workbook(path, config, provider=recorder, cache_dirs=no_cache)
    assert doc.provider_calls == 1
    body = json.dumps(recorder.requests[0])
    assert canary not in body
    # …while the header region IS there.
    assert "Target_Column_Name_in_DL" in body and "Field Name" in body
    assert "header_region=1..15" in body


# ------------------------------------------------- (c) adversarial answers are rejected


@pytest.mark.parametrize("file_name", [f for f in ADVERSARIAL if "canary" not in f])
def test_adversarial_mock_profiles_are_rejected_with_the_right_reason(file_name, config,
                                                                      no_cache):
    provider = MockLayoutProvider([MOCK], override=MOCK / file_name)
    doc, _ = resolve_workbook(STTM / "pair_1_family_a.xlsx", config, provider=provider,
                              cache_dirs=no_cache)
    fragment = ADVERSARIAL[file_name]["reason_fragment"]
    assert any(fragment in r.reason for r in doc.rejections), [r.render() for r in doc.rejections]
    # Everything the synonyms placed is intact: the source band still has
    # its eight roles and the rules band its six.
    sheet = doc.profile.sheet("FEED_1_MAPPING")
    assert sheet is not None
    assert len(sheet.band("source").roles) >= 8 and len(sheet.band("rules").roles) == 6
    assert "PHANTOM_SHEET" not in [s.name for s in doc.profile.sheets] or any(
        r.reason == "sheet does not exist in the workbook" for r in doc.rejections)


def test_swapped_spans_and_wrong_header_row_leave_specific_roles_unresolved(config, no_cache):
    provider = MockLayoutProvider([MOCK], override=MOCK / "adversarial_free_text_column.json")
    doc, _ = resolve_workbook(STTM / "pair_1_family_a.xlsx", config, provider=provider,
                              cache_dirs=no_cache)
    # The free-text claim (length → Description) is rejected; the other
    # model claims (stage/standard table, column, type, schema) survive.
    assert any(r.role == "length" for r in doc.rejections)
    stage = doc.profile.sheet("FEED_1_MAPPING").band("stage")
    assert {"table", "column", "target_type", "schema"} <= set(stage.roles)
    assert doc.complete


# ------------------------------------------------- (d) unresolved still extracts, flagged


def test_unresolved_roles_extract_empty_and_flag_the_gate(config, no_cache, tmp_path):
    from codegen.gate.verdict import compute_verdict

    # No provider: pair 7 keeps stage/column + type unresolved under synonyms.
    doc, _ = resolve_workbook(STTM / "pair_7_family_e.xlsx", config, provider=None,
                              cache_dirs=no_cache)
    assert not doc.complete and doc.questions
    question = next(q for q in doc.questions if q.role == "column" and q.layer == "stage")
    assert question.candidates and all("col" in c for c in question.candidates)
    assert any("Field Name" in h for h in question.header)
    # Extraction through the incomplete profile refuses loudly on the
    # required stage roles (a contract cannot carry empty stage columns) …
    frd = tmp_path / "frd.json"
    data = frd_contract_dict()
    data["feeds"][0].update({"feed_name": "FEED_7", "file_name_patterns": ["FEED_7_RX_*.dat"],
                             "stage_target": {"catalog": None, "schema": "stg_rx",
                                              "tables": ["feed_7_rx_claims"],
                                              "load_strategy": "Truncate and Load"},
                             "record_segments": []})
    frd.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(Exception, match="stage band has no values"):
        extract_contract(STTM / "pair_7_family_e.xlsx", frd, config, generated_date="2026-01-01",
                         layout=doc.profile)
    # … while a run still completes: the gate carries the layout flags.
    pair = resolve_pair(STTM / "pair_7_family_e.xlsx", None, config, provider=None,
                        cache_dirs=no_cache)
    assert any(f.startswith("layout_unresolved:sttm MAPPING_FEED_7/stage/column")
               for f in pair.flags)
    gate = compute_verdict("feed_7", [], [], [], True, extra_flags=pair.flags)
    assert gate.verdict == "PASS_WITH_FLAGS"
    assert any("layout_unresolved" in f for f in gate.flags)


# ------------------------------------------------- (e) user answers merge and cache


def test_user_answers_merge_validate_and_cache(config, no_cache, tmp_path):
    runtime = tmp_path / "runtime"
    answers = {"MAPPING_FEED_7/stage/column": 11, "MAPPING_FEED_7/stage/target_type": 12,
               "MAPPING_FEED_7/standard/column": 15}
    doc, _ = resolve_workbook(STTM / "pair_7_family_e.xlsx", config, provider=None,
                              cache_dirs=no_cache, runtime_cache_dir=runtime, answers=answers)
    assert doc.complete and doc.profile.source == "user"
    for key in answers:
        assert doc.profile.role_sources[key] == "user" and doc.profile.confidence[key] == 1.0
    cached_path = runtime / f"{doc.fingerprint}.json"
    assert cached_path.is_file()
    again, _ = resolve_workbook(STTM / "pair_7_family_e.xlsx", config, provider=None,
                                cache_dirs=no_cache, runtime_cache_dir=runtime)
    assert again.cache_hit and again.complete and again.provider_calls == 0
    # A wrong answer (a column another role claims) is refused, not applied.
    bad, _ = resolve_workbook(STTM / "pair_7_family_e.xlsx", config, provider=None,
                              cache_dirs=no_cache, answers={"MAPPING_FEED_7/stage/column": 9})
    assert not bad.complete


# ------------------------------------------------- (f) canary: no model string reaches an artefact


def test_no_model_string_reaches_any_output(config, no_cache, tmp_path):
    provider = MockLayoutProvider([MOCK], override=MOCK / "adversarial_canary.json")
    runtime = tmp_path / "runtime"
    frd = FRD / "f1_pair_1.docx"
    pair = resolve_pair(STTM / "pair_1_family_a.xlsx", frd, config, provider=provider,
                        cache_dirs=no_cache, runtime_cache_dir=runtime, generated_date="2026-01-01")
    assert pair.sttm.complete
    outputs = [json.dumps(pair.report(), ensure_ascii=False),
               pair.sttm.profile.model_dump_json(),
               "\n".join(pair.flags)]
    for path in runtime.glob("*.json"):
        outputs.append(path.read_text(encoding="utf-8"))
    # The contract read through the resolved profile.
    frd_json = tmp_path / "pair1.frd.contract.json"
    from codegen.extract.frd_docx import contract_to_json as frd_to_json

    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    data = json.loads(frd_json.read_text(encoding="utf-8"))
    data["feeds"][0]["file_name_patterns"] = ["I_ACCUM_*_TO_CLIENT_*.csv"]
    data["feeds"][0]["record_segments"] = ["Header", "Detail", "Trailer"]
    frd_json.write_text(json.dumps(data), encoding="utf-8")
    from codegen.extract import contract_to_json

    contract = extract_contract(STTM / "pair_1_family_a.xlsx", frd_json, config,
                                generated_date="2026-01-01", layout=pair.sttm.profile)
    outputs.append(contract_to_json(contract))
    assert contract.feeds[0].field_count == 23
    assert all(f.provenance is not None for f in contract.feeds[0].fields)
    # field_name was synonyms-placed; the model placed the target roles.
    assert {f.provenance.source for f in contract.feeds[0].fields} == {"synonyms"}
    assert pair.sttm.profile.role_sources["FEED_1_MAPPING/stage/table"] == "model"
    for text in outputs:
        assert CANARY not in text


# ------------------------------------------------- (§9) pair-level cross-checks


def test_pair1_cross_checks_agree_and_raise_confidence(config, no_cache, tmp_path):
    pair = resolve_pair(STTM / "pair_1_family_a.xlsx", FRD / "f1_pair_1.docx", config,
                        provider=MockLayoutProvider([MOCK, PROFILES]), cache_dirs=no_cache,
                        vdd_path=VDD / "pair_1_v1_segments.xlsx",
                        runtime_cache_dir=tmp_path / "runtime", generated_date="2026-01-01")
    assert pair.provider_calls == 1      # the STTM only; the FRD resolves by synonyms
    assert pair.frd is not None and pair.frd.complete and pair.frd.provider_calls == 0
    status = {c.name: c.status for c in pair.cross_checks}
    assert status["feed_name"] == "agree"
    assert status["stage_schema"] == "agree" and status["stage_catalog"] == "agree"
    assert status["standard_schema"] == "agree" and status["standard_catalog"] == "agree"
    assert status["file_format"] == "agree" and status["frequency"] == "agree"
    assert status["delimiter"] == "unchecked"           # neither document states one
    assert not [f for f in pair.flags if f.startswith("layout_crosscheck")]
    # The model-placed schema roles gained the agreement bonus.
    profile = pair.sttm.profile
    assert profile.confidence["FEED_1_MAPPING/stage/schema"] == pytest.approx(
        config.layout.model_confidence + config.layout.crosscheck_bonus)
    fmt = next(c for c in pair.cross_checks if c.name == "file_format")
    assert "Object/data Format" in fmt.frd_citation
    assert fmt.sttm_citation.startswith("FEED_1_MAPPING!")
    # Second resolution of the same pair: served from the pair cache, zero calls.
    again = resolve_pair(STTM / "pair_1_family_a.xlsx", FRD / "f1_pair_1.docx", config,
                         provider=MockLayoutProvider([MOCK, PROFILES]), cache_dirs=no_cache,
                         vdd_path=VDD / "pair_1_v1_segments.xlsx",
                         runtime_cache_dir=tmp_path / "runtime", generated_date="2026-01-01")
    assert again.pair_cache_hit and again.provider_calls == 0
    assert again.sttm.profile.source == "cache" and again.frd.profile.source == "cache"
    assert again.vdd is not None and again.vdd.profile.source == "cache"


def test_target_schema_mismatch_is_a_flag_citing_both_and_the_run_completes(config, no_cache,
                                                                              tmp_path):
    data = frd_contract_dict()
    data["feeds"][0].update({
        "feed_name": "FEED_4 remit", "file_name_patterns": ["feed_4_remit_YYYYMMDD.dat"],
        "file_format": "dat", "delimiter": "|", "record_segments": [],
        "stage_target": {"catalog": None, "schema": "stg_other", "tables": ["feed_4_remit"],
                         "load_strategy": "Truncate and Load"},
        "standard_target": {"catalog": None, "schema": "remit", "tables": ["feed_4_remit"],
                            "load_strategy": "Append"},
    })
    frd = tmp_path / "frd.contract.json"
    frd.write_text(json.dumps(data), encoding="utf-8")
    pair = resolve_pair(STTM / "pair_4_family_d.xlsx", frd, config, provider=None,
                        cache_dirs=no_cache)
    flag = next(f for f in pair.flags if f.startswith("layout_crosscheck:stage_schema"))
    assert "contract feeds[0].stage_target.schema" in flag
    assert "STTM!P" in flag                                # the stage schema column, cited
    assert "'stg_other'" in flag and "'stg_remit'" in flag
    assert pair.sttm.complete and pair.provider_calls == 0
    # The run completes: the contract extracts and the gate carries the flag.
    contract = extract_contract(STTM / "pair_4_family_d.xlsx", frd, config,
                                generated_date="2026-01-01", layout=pair.sttm.profile)
    assert contract.feeds[0].field_count == 12
    from codegen.gate.verdict import compute_verdict

    gate = compute_verdict("feed_4_remit", [], [], [], True, extra_flags=pair.flags)
    assert gate.verdict == "PASS_WITH_FLAGS" and flag in gate.flags


def test_frd_adversarial_claim_is_rejected_by_the_document_validator(config, no_cache, tmp_path):
    """An FRD profile claim whose label cell does not read as claimed is
    dropped with its reason (the FRD fixtures resolve by synonyms, so the
    adversarial path is exercised through a doctored cached profile)."""
    from codegen.extract.frd_docx import read_docx
    from codegen.layout.frd_profile import FrdLayoutProfile
    from codegen.layout.resolve import _validate_frd

    truth = FrdLayoutProfile.model_validate_json(
        (PROFILES / "frd_f1_pair_1.layout.json").read_text(encoding="utf-8"))
    wrong = truth.fields["feeds[0].frequency"].model_copy(update={"row": 9})
    doctored = truth.model_copy(update={
        "fields": {**truth.fields, "feeds[0].frequency": wrong},
        "field_sources": {"feeds[0].frequency": "model"}})
    validated, rejections = _validate_frd(doctored, read_docx(FRD / "f1_pair_1.docx"), config,
                                          {"model"})
    assert [r.role for r in rejections] == ["feeds[0].frequency"]
    assert "label cell reads" in rejections[0].reason
    assert "feeds[0].frequency" not in validated.fields
    assert any(u.field == "feeds[0].frequency" for u in validated.unresolved)


def test_cli_layout_command_reports_sources_and_calls(config, tmp_path):
    from codegen.cli import main

    profile_out = tmp_path / "profile.json"
    exit_code = main(["layout", "--config", str(REPO / "config" / "config.yaml"),
                      "--workbook", str(STTM / "pair_4_family_d.xlsx"), "--dry-run",
                      "--no-cache", "--profile-out", str(profile_out), "--require-complete"])
    assert exit_code == 0
    assert LayoutProfile.model_validate_json(profile_out.read_text(encoding="utf-8")).source == \
        "synonyms"
    # Always --dry-run in the suite (never a live call). With the mock's
    # correct answer pair 7 completes; --require-complete then passes.
    exit_code = main(["layout", "--config", str(REPO / "config" / "config.yaml"),
                      "--workbook", str(STTM / "pair_7_family_e.xlsx"), "--dry-run",
                      "--no-cache", "--require-complete"])
    assert exit_code == 0
