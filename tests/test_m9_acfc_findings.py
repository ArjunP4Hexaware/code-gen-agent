"""M9 — the ACFC findings of 2026-09-21, landed properly.

What went wrong inside ACFC (``docs/acfc/HANDOVER_GENIE.md`` /
``PAIR1_HEADERS.md`` on the ``acfc-hotfix-1`` branch), each pinned here:

* M9.1 resolver — the sheet's "… in DL" headers were outside the synonym
  tables; a model-made profile WITHOUT the schema role was cached, the schema
  was not a required role so nothing asked, the cache could not be bypassed,
  an answer for a role no question listed was refused, and the reasons the
  model answer was rejected were lost.
* M9.2 extractor — schema / table constants, the "Details" banner, the
  "Do Not Map" row; the hotfix's empty-schema tolerance is NOT kept.
* M9.3 contract matcher — normalized table names.

The FRD reader's half of M9.3 is in tests/test_frd_docx.py, the fixture
geometry in tests/test_acfc_shapes_fixtures.py, the acceptance run in
tests/test_m4_acceptance.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import pre_m9_vocabulary
from codegen import cli
from codegen.extract import ExtractionError, extract_contract
from codegen.layout.discover import discover
from codegen.layout.model import MockLayoutProvider
from codegen.layout.profile import REQUIRED_ROLES, LayoutProfile, Role, missing_required_roles
from codegen.layout.resolve import resolve_pair, resolve_workbook, vocabulary_hash
from codegen.resolve.resolver import normalize_table_name

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
PROFILES = REPO / "fixtures" / "layout_profiles"
PAIR_1 = SHAPES / "sttm" / "pair_1_family_a.xlsx"
PAIR_1_FRD = SHAPES / "frd" / "f1_pair_1.docx"
SHEET = "FEED_1_MAPPING"
DATE = "2026-01-01"


@pytest.fixture()
def no_cache(tmp_path):
    empty = tmp_path / "empty_cache"
    empty.mkdir()
    return [empty]


@pytest.fixture()
def mock():
    return MockLayoutProvider([PROFILES / "mock", PROFILES])


# ---------------------------------------------------------------- M9.1 synonyms


def test_schema_is_required_in_both_target_bands_and_catalog_is_not():
    for layer in ("stage", "standard"):
        assert Role.SCHEMA in REQUIRED_ROLES[layer]
        assert Role.CATALOG not in REQUIRED_ROLES[layer]


def test_in_dl_family_and_details_are_synonyms(config):
    target = config.extractor.discovery.roles["target"]
    for role, header in (("schema", "target schema name in dl"),
                         ("table", "target table name in dl"),
                         ("column", "target column name in dl"),
                         ("target_type", "target data type in dl")):
        assert header in target[role], role
    assert "details" in config.extractor.discovery.segment_synonyms["Detail"]


def test_real_shape_fixture_resolves_fully_by_synonyms_with_zero_model_calls(config, mock,
                                                                             no_cache):
    doc, _ = resolve_workbook(PAIR_1, config, provider=mock, cache_dirs=no_cache)
    assert doc.provider_calls == 0 and mock.requests == []
    assert doc.complete and doc.questions == [] and doc.rejections == []
    assert doc.profile.source == "synonyms" and set(doc.sources) >= {"synonyms"}
    assert doc.sources["synonyms"] == sum(doc.sources.values())
    sheet = doc.profile.sheet(SHEET)
    assert (sheet.band_row, sheet.header_row) == (14, 15)
    spans = {b.layer: (b.col_start, b.col_end) for b in sheet.bands}
    assert spans == {"source": (1, 9), "rules": (11, 16), "stage": (18, 23),
                     "standard": (25, 30)}                       # J, Q, X belong to no band
    assert sheet.band("stage").roles == {"workspace": 18, "catalog": 19, "schema": 20,
                                         "table": 21, "column": 22, "target_type": 23}
    assert sheet.band("standard").roles["schema"] == 27            # AA
    assert sheet.band("standard").roles["table"] == 28             # AB
    assert sheet.band("source").roles["source_type"] == 5          # "Format"
    assert missing_required_roles(doc.profile) == []


def test_a_missing_required_role_is_always_a_question(config, no_cache):
    """The pre-M9 tables leave the schema open: it is ASKED (inside ACFC it
    was not a required role, so a profile without it raised no question)."""
    doc, _ = resolve_workbook(PAIR_1, pre_m9_vocabulary.strip(config), provider=None,
                              cache_dirs=no_cache)
    assert sorted(q.key for q in doc.questions) == sorted(pre_m9_vocabulary.PAIR1_OPEN_ROLES)
    schema = next(q for q in doc.questions if q.key == f"{SHEET}/stage/schema")
    assert {"col": 20, "header": "Target Schema Name in DL"} in schema.candidates


# ---------------------------------------------------------------- M9.1 cache


def _stale_profile(config) -> dict:
    """The profile the ACFC cache held: everything placed EXCEPT the schema,
    and no note that it is missing."""
    payload = discover(PAIR_1, config.extractor).profile.model_dump(mode="json")
    for sheet in payload["sheets"]:
        for band in sheet.get("bands", []):
            band["roles"].pop("schema", None)
    payload["unresolved"] = []
    payload["source"] = "model"
    return payload


def test_a_stale_cached_profile_lacking_schema_is_ignored_and_re_resolved(config, mock, tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    stale = _stale_profile(config)
    stale["vocabulary"] = vocabulary_hash(config)          # right key — still not trusted
    (runtime / f"{stale['fingerprint']}.json").write_text(json.dumps(stale), encoding="utf-8")
    doc, _ = resolve_workbook(PAIR_1, config, provider=mock, cache_dirs=[],
                              runtime_cache_dir=runtime)
    assert not doc.cache_hit and doc.profile.source == "synonyms"
    assert doc.complete and doc.provider_calls == 0
    assert doc.profile.sheet(SHEET).band("stage").roles["schema"] == 20
    (rejection,) = doc.rejections
    assert "cached profile lacks required role(s)" in rejection.reason
    assert f"{SHEET}/stage/schema" in rejection.reason
    # The same stale profile in the REPO cache is refused the same way.
    repo = tmp_path / "repo_cache"
    repo.mkdir()
    (repo / "stale.layout.json").write_text(
        json.dumps({k: v for k, v in stale.items() if k != "vocabulary"}), encoding="utf-8")
    again, _ = resolve_workbook(PAIR_1, config, provider=None, cache_dirs=[repo])
    assert not again.cache_hit and again.complete


def test_a_profile_with_a_required_role_missing_is_never_written(config, tmp_path):
    runtime = tmp_path / "runtime"
    pre_m9 = pre_m9_vocabulary.strip(config)
    # Answers place everything except the two schemas: still incomplete.
    answers = {k: c for k, c in {
        f"{SHEET}/stage/table": 21, f"{SHEET}/stage/column": 22,
        f"{SHEET}/stage/target_type": 23, f"{SHEET}/standard/table": 28,
        f"{SHEET}/standard/column": 29, f"{SHEET}/standard/target_type": 30}.items()}
    doc, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                              runtime_cache_dir=runtime, answers=answers)
    assert sorted(q.key for q in doc.questions) == [f"{SHEET}/stage/schema",
                                                    f"{SHEET}/standard/schema"]
    assert not list(runtime.glob("*.json")) if runtime.is_dir() else True
    # With the schemas answered too the profile is complete and IS written.
    answers.update({f"{SHEET}/stage/schema": 20, f"{SHEET}/standard/schema": 27})
    done, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                               runtime_cache_dir=runtime, answers=answers)
    assert done.complete
    written = json.loads((runtime / f"{done.fingerprint}.json").read_text(encoding="utf-8"))
    assert written["vocabulary"] == vocabulary_hash(pre_m9)


def test_cache_key_includes_the_vocabulary(config, tmp_path):
    runtime = tmp_path / "runtime"
    pre_m9 = pre_m9_vocabulary.strip(config)
    assert vocabulary_hash(pre_m9) != vocabulary_hash(config)
    assert vocabulary_hash(config) == vocabulary_hash(config.model_copy())
    answers = {key: col for key, col in zip(
        pre_m9_vocabulary.PAIR1_OPEN_ROLES, (20, 21, 22, 23, 27, 28, 29, 30), strict=True)}
    first, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                                runtime_cache_dir=runtime, answers=answers)
    assert first.complete
    hit, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                              runtime_cache_dir=runtime)
    assert hit.cache_hit and hit.profile.source == "cache"
    # Other tables (here: the shipped ones, with the M9 synonyms) = another
    # key: the entry is not served; the sheet re-resolves.
    other, _ = resolve_workbook(PAIR_1, config, provider=None, cache_dirs=[],
                                runtime_cache_dir=runtime)
    assert not other.cache_hit and other.profile.source == "synonyms"
    # An entry with NO vocabulary key (written before M9) is stale as well.
    path = runtime / f"{first.fingerprint}.json"
    legacy = json.loads(path.read_text(encoding="utf-8"))
    legacy.pop("vocabulary")
    path.write_text(json.dumps(legacy), encoding="utf-8")
    legacy_run, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                                     runtime_cache_dir=runtime)
    assert not legacy_run.cache_hit


def test_refresh_bypasses_and_overwrites_the_runtime_entry(config, mock, tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    # A COMPLETE but wrong entry (stage schema claimed at the catalog column)
    # under the right key: a plain run serves it, a refresh replaces it.
    wrong = discover(PAIR_1, config.extractor).profile.model_dump(mode="json")
    stage = next(b for s in wrong["sheets"] if s["name"] == SHEET for b in s["bands"]
                 if b["layer"] == "stage")
    stage["roles"].pop("catalog")
    stage["roles"]["schema"] = 19
    wrong["vocabulary"] = vocabulary_hash(config)
    path = runtime / f"{wrong['fingerprint']}.json"
    path.write_text(json.dumps(wrong), encoding="utf-8")
    served, _ = resolve_workbook(PAIR_1, config, provider=mock, cache_dirs=[],
                                 runtime_cache_dir=runtime)
    assert served.cache_hit and served.profile.sheet(SHEET).band("stage").roles["schema"] == 19

    fresh, _ = resolve_workbook(PAIR_1, config, provider=mock, cache_dirs=[],
                                runtime_cache_dir=runtime, refresh=True)
    assert not fresh.cache_hit and fresh.profile.sheet(SHEET).band("stage").roles["schema"] == 20
    overwritten = json.loads(path.read_text(encoding="utf-8"))
    assert LayoutProfile.model_validate(
        {k: v for k, v in overwritten.items() if k != "vocabulary"}
    ).sheet(SHEET).band("stage").roles["schema"] == 20
    # A refresh that cannot complete tombstones the entry instead (the storage
    # roles have no delete): the old profile is never served again.
    pre_m9 = pre_m9_vocabulary.strip(config)
    wrong["vocabulary"] = vocabulary_hash(pre_m9)
    path.write_text(json.dumps(wrong), encoding="utf-8")
    open_again, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                                     runtime_cache_dir=runtime, refresh=True)
    assert open_again.questions and json.loads(path.read_text(encoding="utf-8"))["invalidated"]
    after, _ = resolve_workbook(PAIR_1, pre_m9, provider=None, cache_dirs=[],
                                runtime_cache_dir=runtime)
    assert not after.cache_hit and after.questions


def test_rejection_log_is_written_in_full_and_carries_no_model_string(config, tmp_path):
    """The ACFC report line read "10 validation errors for LayoutProfile" and
    the ten reasons were gone. The log keeps every one — type, location,
    message — and never a string the model made up."""
    runtime = tmp_path / "runtime"
    pre_m9 = pre_m9_vocabulary.strip(config)
    invented = "MODEL_INVENTED_KEY_91ac"
    answer = tmp_path / "answer.json"
    # M12: an extra KEY in the answer is dropped (the response schema ignores
    # it, never a rejection), so the invented name rides where it still errs:
    # a role name whose column is not a number.
    answer.write_text(json.dumps({
        "fingerprint": "x", "source": "model", "strategy": "content",
        "sheets": [{"name": SHEET, "kind": "mapping", "header_row": "fifteen",
                    "bands": [{"layer": "stage", "col_start": 0, "col_end": 23,
                               "roles": {"schema": "T", invented: "x"}}]}]}),
        encoding="utf-8")
    provider = MockLayoutProvider([], override=answer)
    doc, _ = resolve_workbook(PAIR_1, pre_m9, provider=provider, cache_dirs=[],
                              runtime_cache_dir=runtime, refresh=True)
    assert doc.provider_calls == 1 and doc.questions
    (line,) = [r.reason for r in doc.rejections]
    assert line.startswith("model response failed schema validation:")
    log = json.loads((runtime / "rejections" / f"{doc.fingerprint}.json").read_text(
        encoding="utf-8"))
    assert log["document"] == "sttm" and log["fingerprint"] == doc.fingerprint
    assert len(log["schema_errors"]) >= 4
    assert {"type", "loc", "msg"} == set(log["schema_errors"][0])
    assert any(e["loc"][-1] == "header_row" for e in log["schema_errors"])
    text = json.dumps(log)
    assert invented not in text and "<key>" in text           # an invented key is masked
    assert "fifteen" not in text                               # no input value is kept
    # The log is not a cache entry.
    assert not [p for p in runtime.glob("*.json")]


def test_cli_layout_refresh_flag(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.chdir(REPO)
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    # --no-cache so the tracked repo profile is not what answers.
    assert cli.main(["layout", "--workbook", str(PAIR_1), "--dry-run", "--refresh",
                     "--require-complete"]) == 0
    out = capsys.readouterr().out
    assert "REFRESH" in out and "source=synonyms" in out and "cache_hit=False" in out
    cached = list((state / "layout_profiles").glob("*.json"))
    assert len(cached) == 1            # a synonyms-only result IS written on a refresh
    assert json.loads(cached[0].read_text(encoding="utf-8"))["vocabulary"]


def test_pair_refresh_overwrites_the_pair_entry(config, mock, tmp_path):
    runtime = tmp_path / "runtime"
    kwargs = dict(provider=mock, cache_dirs=[], runtime_cache_dir=runtime, generated_date=DATE,
                  vdd_path=SHAPES / "vdd" / "pair_1_v1_segments.xlsx")
    first = resolve_pair(PAIR_1, PAIR_1_FRD, config, refresh=True, **kwargs)
    assert first.questions == [] and first.provider_calls == 0
    entry = runtime / f"pair_{first.pair_fingerprint}.json"
    assert json.loads(entry.read_text(encoding="utf-8"))["vocabulary"] == vocabulary_hash(config)
    again = resolve_pair(PAIR_1, PAIR_1_FRD, config, **kwargs)
    assert again.pair_cache_hit
    refreshed = resolve_pair(PAIR_1, PAIR_1_FRD, config, refresh=True, **kwargs)
    assert not refreshed.pair_cache_hit and refreshed.sttm.profile.source == "synonyms"


# ---------------------------------------------------------------- M9.2 extractor


def _frd_json(tmp_path: Path, config, **stage) -> Path:
    """The pair-1 FRD contract as the layout stage leaves it (named after the
    stage band), optionally with its stage target patched."""
    from codegen.extract.frd_docx import contract_to_json

    pair = resolve_pair(PAIR_1, PAIR_1_FRD, config, provider=None, cache_dirs=[],
                        generated_date=DATE)
    data = json.loads(contract_to_json(pair.frd_contract))
    data["feeds"][0]["stage_target"].update(stage)
    path = tmp_path / "frd.contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_real_shape_fixture_extracts_schema_segments_unmapped_flag_and_field_count(config,
                                                                                   tmp_path):
    contract = extract_contract(PAIR_1, _frd_json(tmp_path, config), config,
                                generated_date=DATE)
    (feed,) = contract.feeds
    # Band constants: schema + table repeat on every data row (the alias of
    # the real sheet's stage / standard schema and table).
    assert (feed.stage.schema_name, feed.stage.table) == ("stg_vnd_p_accum", "vnd_p_accum_client")
    assert (feed.standard.schema_name, feed.standard.table) == ("accum", "vnd_p_accum_client")
    assert (feed.stage.catalog, feed.standard.catalog) == ("pr_dlk_vnd_p", "pr_std_vnd_p")
    # Three segments; the labels are the Segment column's, verbatim.
    assert [s for s in dict.fromkeys(f.record_segment for f in feed.fields)] == [
        "Header", "Detail", "Trailer"]
    assert {f.record_segment_label for f in feed.fields} == {"HDDR", "DET", "TRLR"}
    # Field count pinned: 24 source rows, one "Do Not Map" -> 23.
    assert feed.field_count == 23 == len(feed.fields)
    assert not any("Reserved" in f.source_column or f.stage_column == "Do Not Map"
                   for f in feed.fields)
    (flag,) = feed.extraction_flags
    assert flag == ("field_unmapped:Reserved Group (01) — STTM FEED_1_MAPPING!V38 reads "
                    "'Do Not Map'; the field is in neither the stage nor the standard table")
    # Provenance of the band constants: the cell each was read from.
    notes = "\n".join(contract.notes)
    assert "stage table 'vnd_p_accum_client' — FEED_1_MAPPING!U17 (first non-empty cell" in notes
    assert "stage schema 'stg_vnd_p_accum' — FEED_1_MAPPING!T17" in notes
    assert "standard schema 'accum' — FEED_1_MAPPING!AA17" in notes
    assert [a.column for a in feed.audit_columns] == ["SRC_FILE_NAME", "REC_CREATION_TIME",
                                                      "REC_UPDATED_TIME"]
    # The TBD meta values are blanks, never values.
    assert "file_names" not in feed.meta_rows and "frequency" not in feed.meta_rows
    assert feed.meta_rows["file_format"] == ".dat"


def test_banner_rows_and_placeholders_are_logged_not_read_as_fields(config):
    from codegen.extract.generic import read_workbook

    ir = read_workbook(discover(PAIR_1, config.extractor), PAIR_1.name, config)
    (sheet,) = ir.sheets
    banners = [s for s in sheet.skipped if "segment banner" in s]
    assert [b.split("'")[1] for b in banners] == ["Header", "Details", "Trailer"]
    assert not [s for s in sheet.skipped if "no field name" in s]
    placeholders = [d for d in ir.diagnostics if "(a placeholder); read as blank" in d]
    assert len(placeholders) == 3 and all("'TBD'" in d for d in placeholders)


def _without_schema_role(config):
    profile = discover(PAIR_1, config.extractor).profile
    sheets = [s.model_copy(update={"bands": [
        b.model_copy(update={"roles": {r: c for r, c in b.roles.items() if r != "schema"}})
        for b in s.bands]}) for s in profile.sheets]
    return profile.model_copy(update={"sheets": sheets})


def test_missing_schema_is_a_hard_stop_after_the_fallback_chain(config, tmp_path):
    """The hotfix let an EMPTY schema through. It does not: the chain is STTM
    band -> FRD -> conventions.default_schema, each link flagged, then a stop."""
    layout = _without_schema_role(config)
    frd = _frd_json(tmp_path, config)
    with pytest.raises(ExtractionError, match="no source states the stage schema"):
        extract_contract(PAIR_1, frd, config, generated_date=DATE, layout=layout)
    # 2nd link: the FRD states one.
    frd = _frd_json(tmp_path, config, schema="stg_from_frd")
    contract = extract_contract(PAIR_1, frd, config, generated_date=DATE, layout=layout)
    (feed,) = contract.feeds
    assert feed.stage.schema_name == "stg_from_frd"
    flag = next(f for f in feed.extraction_flags if f.startswith("sttm_unstated:stage.schema"))
    assert "source_used:FRD 'Target Catalog and Schema': 'stg_from_frd'" in flag
    assert "stage schema role is not placed" in flag
    # 3rd link: the config default.
    with_default = config.model_copy(update={"conventions": config.conventions.model_copy(
        update={"default_schema": {"stage": "stg_default", "standard": "std_default"}})})
    contract = extract_contract(PAIR_1, _frd_json(tmp_path, config), with_default,
                                generated_date=DATE, layout=layout)
    (feed,) = contract.feeds
    assert (feed.stage.schema_name, feed.standard.schema_name) == ("stg_default", "std_default")
    assert sum("config_default (conventions.default_schema" in f
               for f in feed.extraction_flags) == 2


def test_band_constant_reads_a_merged_anchor_and_keeps_the_dominant_of_many(config, tmp_path):
    """A constant stated ONCE (a merged cell: openpyxl reads the rest as None)
    is the first non-empty cell; a column with one table per segment (pair 8)
    is not a constant and keeps its dominant value."""
    from openpyxl import load_workbook

    wb = load_workbook(PAIR_1)
    ws = wb[SHEET]
    data_rows = [r for r in range(17, 46) if ws.cell(row=r, column=20).value is not None]
    for row in data_rows[1:]:
        ws.cell(row=row, column=20).value = None
        ws.cell(row=row, column=27).value = None
    ws.merge_cells(start_row=data_rows[0], start_column=20, end_row=data_rows[-1], end_column=20)
    path = tmp_path / "pair_1_merged_schema.xlsx"
    wb.save(path)
    contract = extract_contract(path, _frd_json(tmp_path, config), config, generated_date=DATE)
    (feed,) = contract.feeds
    assert (feed.stage.schema_name, feed.standard.schema_name) == ("stg_vnd_p_accum", "accum")
    assert "T17 (first non-empty cell of the stage schema column; 1 row(s) state it)" \
        in "\n".join(contract.notes)


def test_unmapped_markers_are_config(config, tmp_path):
    assert config.extractor.unmapped_markers == ["do not map", "dnm", "not mapped", "n/a", "na",
                                                 "none"]
    no_markers = config.model_copy(update={"extractor": config.extractor.model_copy(
        update={"unmapped_markers": []})})
    # Without the knob the row is what it always was: a loud failure.
    with pytest.raises(ExtractionError, match="has no stage column/data type"):
        extract_contract(PAIR_1, _frd_json(tmp_path, config), no_markers, generated_date=DATE)


# ---------------------------------------------------------------- M9.3 matcher


@pytest.mark.parametrize("written,expected", [
    ("orders", ("orders", False)),
    ("STG.Orders", ("orders", True)),
    ("`cat`.`stg`.`Orders`", ("orders", True)),
    ('"Orders"', ("orders", False)),
    ("[stg].[Orders]", ("orders", True)),
    ("  Orders  ", ("orders", False)),
])
def test_table_names_compare_normalized(written, expected):
    assert normalize_table_name(written) == expected


def test_contract_matcher_reports_which_side_was_qualified(config, tmp_path):
    from codegen.extract import contract_to_json
    from codegen.resolve.resolver import ContractMismatchError
    from codegen.resolve.resolver import resolve_pair as resolve_contracts

    frd = _frd_json(tmp_path, config, tables=["STG_VND_P_ACCUM.`VND_P_Accum_Client`"])
    # The extractor pairs sheet and feed (single sheet, single feed) …
    sttm = tmp_path / "sttm.contract.json"
    sttm.write_text(contract_to_json(extract_contract(PAIR_1, frd, config, generated_date=DATE)),
                    encoding="utf-8")
    # … and the matcher accepts the qualified / quoted / cased spelling, saying so.
    (spec,) = resolve_contracts(frd, sttm, config)
    (flag,) = [f for f in spec.provenance_flags if f.startswith("table_name_normalized")]
    assert "STTM 'vnd_p_accum_client' ↔ FRD 'STG_VND_P_ACCUM.`VND_P_Accum_Client`'" in flag
    assert flag.endswith("FRD schema-qualified")
    # A different table is still a mismatch.
    other = _frd_json(tmp_path, config, tables=["stg.some_other_table"])
    with pytest.raises(ContractMismatchError, match="is not among FRD stage tables"):
        resolve_contracts(other, sttm, config)


# ---------------------------------------------------------------- the notebook's CLI chain


def test_cli_chain_layout_contract_out_then_generate_matches_the_golden(tmp_path, monkeypatch,
                                                                       capsys):
    """The ACFC notebook's path (acfc_run.py): `layout --frd-contract-out` →
    extract-sttm → extract-vdd → `generate --vdd --profile …`. The FRD contract
    is the one the PAIR resolved (the feed named after the stage band), and
    `generate` honours --vdd / --profile / --iig-template / --playbook-template
    (it used to parse and drop them)."""
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(SHAPES / "pair_1" / "config_overlay.yaml"))
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    (tmp_path / "state").mkdir()
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(REPO)
    vdd = SHAPES / "vdd" / "pair_1_v1_segments.xlsx"
    frd, sttm, vdd_json, layout = (tmp_path / n for n in (
        "frd.contract.json", "sttm.contract.json", "vdd.contract.json", "sttm.layout.json"))
    assert cli.main(["layout", "--workbook", str(PAIR_1), "--frd", str(PAIR_1_FRD), "--vdd",
                     str(vdd), "--dry-run", "--no-cache", "--profile-out", str(layout),
                     "--frd-contract-out", str(frd), "--require-complete"]) == 0
    written = json.loads(frd.read_text(encoding="utf-8"))
    assert written["feeds"][0]["feed_name"] == "vnd_p_accum_client"
    assert any(f.startswith("frd_unstated:feeds[0].feed_name source_used:STTM stage band")
               for f in written["extraction_flags"])
    assert cli.main(["extract-sttm", "--workbook", str(PAIR_1), "--frd-contract", str(frd),
                     "--out", str(sttm), "--layout", str(layout),
                     "--generated-date", DATE]) == 0
    assert cli.main(["extract-vdd", "--vdd", str(vdd), "--out", str(vdd_json),
                     "--generated-date", DATE]) == 0
    capsys.readouterr()
    assert cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm),
                     "--vdd", str(vdd_json), "--output-mode", "rfc", "--profile", "acfc_prx",
                     "--iig-template", "iig_v2", "--playbook-template", "main_single",
                     "--skip-tests", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "PASS_WITH_FLAGS vnd_p_accum_client" in out
    assert "vdd_positions=ok" in out and "dml_row_counts=ok" in out      # --vdd / --profile used
    golden = (SHAPES / "pair_1" / "golden" / "ACCUM_DDL.txt").read_bytes()
    feed_dir = tmp_path / "out" / "vnd_p_accum_client"
    assert (feed_dir / "framework" / "ACCUM_DDL.txt").read_bytes() == golden
    (package,) = [p for p in feed_dir.iterdir() if p.name.startswith("RFC")]
    assert (package / "ACCUM_DDL.txt").read_bytes() == golden
