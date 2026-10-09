"""Chunk A (2026-10-09) — STTM bands located by their LABEL GROUP, their layer
only from EVIDENCE.

A band is found wherever its label group (Schema / TableName / ColumnName /
DataType, optional Catalog, Mandatory, Primary Key — the ``roles.target``
synonyms) sits in the header row: any order, any offset, any count of bands,
never fixed columns. Its LAYER comes from an answer, the band title row, a
layer word in its own header texts, its Catalog values, its Schema values —
column order is never evidence. A band nothing names, or two bands naming one
layer, is ``UNRESOLVED <sheet>/band[<n>]/layer`` and its feed waits for the
answer (source | stage | standard). A band missing TableName is
``UNRESOLVED <sheet>/<layer>/table`` — never a blank.

Shapes: ``tests/acfc_shapes/bands.py`` (synthetic, built in code) plus the
ACFC family fixtures A–E, whose profiles are pinned elsewhere and must not move.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from acfc_shapes import bands
from acfc_shapes.common import xlsx_bytes
from codegen import cli
from codegen.extract.workbook import WorkbookParseError, parse_workbook
from codegen.layout.classify import classify_workbook
from codegen.layout.discover import discover, label_groups, normalize, text
from codegen.layout.resolve import parse_answers, resolve_workbook
from test_harness_answer_lines import _NEEDED_KEY_RE

REPO = Path(__file__).resolve().parents[1]
STTM = REPO / "fixtures" / "acfc_shapes" / "sttm"
SHEET = bands.SHEET
LOCATION = ("catalog", "schema", "table", "column", "target_type")


def _write(tmp_path: Path, name: str, workbook) -> Path:
    path = tmp_path / f"{name}.xlsx"
    path.write_bytes(xlsx_bytes(workbook))
    return path


def _bands(profile, sheet: str = SHEET) -> dict[str, tuple[int, int, dict, str | None]]:
    sp = profile.sheet(sheet)
    return {b.layer: (b.col_start, b.col_end, dict(b.roles), b.layer_evidence) for b in sp.bands}


def _open(profile) -> list[str]:
    return [f"{u.sheet}/{u.layer}/{u.role}" for u in profile.unresolved]


# ------------------------------------------------- the five ACFC families (A–E)

FAMILY_FIXTURES = sorted(p.name for p in STTM.glob("pair_*_family_*.xlsx"))


@pytest.mark.parametrize("name", FAMILY_FIXTURES)
def test_every_family_target_band_is_its_label_group(name, config):
    """Families A–E: every stage / standard band the pinned profile places
    (three or more location roles) is exactly one label group of its header
    row — the group reading agrees with the band row, so the profile stays
    the one read before (pinned in test_layout_discovery / the repo cache)."""
    found = discover(STTM / name, config.extractor)
    checked = 0
    for sp in found.profile.mapping_sheets:
        ws = found.workbook[sp.name]
        header = list(next(ws.iter_rows(min_row=sp.header_row, max_row=sp.header_row,
                                        values_only=True)))
        groups = label_groups(header, config.extractor.discovery)
        for band in sp.bands:
            located = {r: c for r, c in band.roles.items() if r in LOCATION}
            if band.layer not in ("stage", "standard") or len(located) < 3:
                continue
            matching = [g for g in groups
                        if {r: c for r, c in g.roles.items() if r in LOCATION} == located]
            assert len(matching) == 1, (name, sp.name, band.layer, located,
                                        [g.roles for g in groups])
            checked += 1
        assert all(b.layer_evidence is None for b in sp.bands), "legacy reading kept"
    assert checked >= 1 or name == "pair_7_family_e.xlsx", name


def test_families_cover_a_to_e():
    assert {n.split("_family_")[1][0] for n in FAMILY_FIXTURES} == set("abcde")


# ------------------------------------------------------------------ SD shape


@pytest.mark.parametrize("narrow", [False, True], ids=["aligned_titles", "titles_over_I-J_N-O"])
def test_sd_shape_stage_i_j_standard_n_o_no_catalog(narrow, config, tmp_path):
    """SD-feed shape: stage Schema/TableName at I/J, standard at N/O, no
    Catalog. With the title merges covering only I–J / N–O the titles
    disagree with the header groups: the groups decide the spans, the
    titles the layers."""
    path = _write(tmp_path, "sd", bands.sd_shaped(narrow_titles=narrow))
    profile = discover(path, config.extractor).profile
    got = _bands(profile)
    assert got["stage"][:3] == (9, 12, {"schema": 9, "table": 10, "column": 11, "target_type": 12})
    assert got["standard"][:3] == (14, 17, {"schema": 14, "table": 15, "column": 16,
                                            "target_type": 17})
    assert "catalog" not in got["stage"][2] and "catalog" not in got["standard"][2]
    assert got["source"][2]["field_name"] == 1
    assert profile.unresolved == []
    assert got["stage"][3] == ("title" if narrow else None)


# --------------------------------------------------------- evidence, one band


def test_one_band_titled_reads_stage(config, tmp_path):
    profile = discover(_write(tmp_path, "one", bands.one_band(title="Staging Layer")),
                       config.extractor).profile
    got = _bands(profile)
    assert got["stage"] == (5, 8, {"schema": 5, "table": 6, "column": 7, "target_type": 8},
                            "title")
    assert "standard" not in got and profile.unresolved == []


def test_one_band_without_evidence_is_one_question(config, tmp_path):
    path = _write(tmp_path, "one", bands.one_band())
    profile = discover(path, config.extractor).profile
    assert _open(profile) == [f"{SHEET}/band[1]/layer"]
    reason = profile.unresolved[0].reason
    assert reason.startswith("band[1] (columns E–H): Schema | TableName | ColumnName | DataType")
    assert reason.endswith("; answer under answers: with source | stage | standard")
    for seen in ("no band title over it", "no layer word in its headers", "no Catalog column",
                 "Schema values (column E) carry no layer prefix"):
        assert seen in reason
    assert "stage" not in _bands(profile)
    verdict = classify_workbook(path, config.extractor)
    assert verdict.kind == "unclassified" and verdict.reason.startswith("confirm:")


def test_one_band_with_stg_schema_reads_stage_without_a_question(config, tmp_path):
    path = _write(tmp_path, "one", bands.one_band(schema="stg_nb"))
    profile = discover(path, config.extractor).profile
    assert _bands(profile)["stage"][3] == "schema_value"
    assert profile.unresolved == []
    assert classify_workbook(path, config.extractor).kind == "sttm"


def test_header_words_and_catalog_values_are_evidence(config, tmp_path):
    words = discover(_write(tmp_path, "w", bands.one_band(header_words=True)),
                     config.extractor).profile
    assert _bands(words)["stage"][3] == "header" and words.unresolved == []
    catalogs = discover(_write(tmp_path, "c", bands.catalog_values()), config.extractor).profile
    got = _bands(catalogs)
    assert (got["stage"][0], got["stage"][3]) == (5, "catalog_value")
    assert (got["standard"][0], got["standard"][3]) == (10, "catalog_value")
    assert catalogs.unresolved == []


def test_in_dl_is_not_stage_evidence(config, tmp_path):
    """'… in DL' is OFF as stage evidence (pair 1 writes it in BOTH bands):
    an untitled one-band sheet with "in DL" headers asks."""
    wb = bands.one_band()
    ws = wb[SHEET]
    for col, label in zip(range(5, 9), ["Target Schema Name in DL", "Target Table Name in DL",
                                         "Target_Column_Name_in_DL", "Target Data Type in DL"],
                          strict=True):
        ws.cell(row=1, column=col, value=label)
    profile = discover(_write(tmp_path, "dl", wb), config.extractor).profile
    assert _open(profile) == [f"{SHEET}/band[1]/layer"]


# ------------------------------------------------- look-alikes, conflicts, order


def test_three_lookalike_bands_without_titles_ask_once_per_band(config, tmp_path):
    profile = discover(_write(tmp_path, "three", bands.three_lookalike()), config.extractor).profile
    assert _open(profile) == [f"{SHEET}/band[{n}]/layer" for n in (1, 2, 3)]
    assert profile.sheet(SHEET).bands == []


def test_three_lookalike_bands_with_titles_are_clean(config, tmp_path):
    path = _write(tmp_path, "three", bands.three_lookalike(titles=True))
    profile = discover(path, config.extractor).profile
    got = _bands(profile)
    assert profile.unresolved == []
    assert got["source"][2] == {"source_schema": 1, "source_table": 2, "field_name": 3,
                                "source_type": 4}
    assert (got["stage"][0], got["standard"][0]) == (5, 9)
    assert classify_workbook(path, config.extractor).kind == "sttm"


def test_two_bands_claiming_stage_both_ask(config, tmp_path):
    profile = discover(_write(tmp_path, "two", bands.two_claim_stage()), config.extractor).profile
    assert _open(profile) == [f"{SHEET}/band[1]/layer", f"{SHEET}/band[2]/layer"]
    for item in profile.unresolved:
        assert "band[1] and band[2] each read as stage" in item.reason


def test_any_order_any_offset(config, tmp_path):
    profile = discover(_write(tmp_path, "rev", bands.reversed_offset()), config.extractor).profile
    sp = profile.sheet(SHEET)
    assert (sp.band_row, sp.header_row) == (6, 7)
    got = _bands(profile)
    assert got["source"][:2] == (4, 7)
    assert got["standard"][:2] == (8, 11) and got["stage"][:2] == (12, 15)
    assert profile.unresolved == []


def test_band_missing_tablename_is_unresolved_never_blank(config, tmp_path):
    profile = discover(_write(tmp_path, "mt", bands.missing_table()), config.extractor).profile
    assert _open(profile) == [f"{SHEET}/stage/table"]


def test_mapping_sheet_the_legacy_reader_refuses_is_read_by_content(config, tmp_path):
    path = _write(tmp_path, "map", bands.mapping_prefix_reversed())
    found = discover(path, config.extractor)
    assert found.profile.strategy == "content"
    got = _bands(found.profile, "MAPPING-NB")
    assert (got["standard"][0], got["stage"][0]) == (5, 9)
    # The flat legacy API still answers with the MAPPING- reader's own refusal.
    with pytest.raises(WorkbookParseError, match="out of order"):
        parse_workbook(path, config.extractor)


def test_a_reference_sheet_beside_mapping_sheets_stays_unread(config):
    """Pair 4's ForReference sheet ("STG - Dest 1 | STD - Dest2" over table /
    column / type groups) is NOT a second feed: header-group detection only
    runs when no sheet is found by its band row; the diagnostics name it."""
    found = discover(REPO / "fixtures" / "acfc_shapes" / "pair_4" / "sttm_nb_cob_report.xlsx",
                     config.extractor)
    assert [s.name for s in found.profile.mapping_sheets] == ["NB_COB_REPORT"]
    assert any("'ForReference': a header row carries target-shaped columns" in d
               for d in found.diagnostics)


# ------------------------------------------------------- answers + the cache


ANSWERED = {f"{SHEET}/band[1]/layer": "source", f"{SHEET}/band[2]/layer": "stage",
            f"{SHEET}/band[3]/layer": "standard"}


def test_band_answers_place_the_layers(config, tmp_path):
    path = _write(tmp_path, "three", bands.three_lookalike())
    profile = discover(path, config.extractor,
                       band_layers={k.rsplit("/", 1)[0]: v for k, v in ANSWERED.items()}).profile
    got = _bands(profile)
    assert profile.unresolved == []
    assert {layer: v[3] for layer, v in got.items()} == {"source": "answer", "stage": "answer",
                                                         "standard": "answer"}
    assert got["source"][2]["field_name"] == 3


def test_resolver_applies_band_answers_and_caches_the_answered_profile(config, tmp_path):
    path = _write(tmp_path, "three", bands.three_lookalike())
    runtime = tmp_path / "runtime"
    doc, _ = resolve_workbook(path, config, runtime_cache_dir=runtime, use_cache=True)
    assert [q.key for q in doc.questions] == list(ANSWERED)
    question = doc.questions[0]
    assert question.kind == "role" and [c["value"] for c in question.candidates] == [
        "source", "stage", "standard"]
    doc, _ = resolve_workbook(path, config, runtime_cache_dir=runtime, answers=dict(ANSWERED))
    assert doc.complete and doc.questions == []
    again, _ = resolve_workbook(path, config, runtime_cache_dir=runtime)
    assert again.cache_hit and again.complete


def test_an_answer_survives_validation_under_a_title_row_without_tokens(config, tmp_path):
    """A band answered stage under a title that names no layer keeps its
    roles when the profile is validated (the title row is not its evidence)."""
    path = _write(tmp_path, "landing", bands.one_band(title="Landing Area"))
    doc, _ = resolve_workbook(path, config, runtime_cache_dir=tmp_path / "rt", use_cache=False)
    assert [q.key for q in doc.questions] == [f"{SHEET}/band[1]/layer"]
    doc, _ = resolve_workbook(path, config, runtime_cache_dir=tmp_path / "rt", use_cache=False,
                              answers={f"{SHEET}/band[1]/layer": "stage",
                                       f"{SHEET}/stage/table": 6})
    stage = doc.profile.sheet(SHEET).band("stage")
    assert stage.roles == {"schema": 5, "table": 6, "column": 7, "target_type": 8}
    assert stage.layer_evidence == "answer" and doc.complete


def test_value_evidence_is_rederived_on_every_cache_hit(config, tmp_path):
    """A layer read from Schema VALUES is never trusted from the cache: the
    fingerprint hashes headers, so another workbook with the same headers and
    no stg_ prefix must ask again, not inherit 'stage'."""
    runtime = tmp_path / "runtime"
    stg = _write(tmp_path, "stg", bands.one_band(schema="stg_nb"))
    doc, _ = resolve_workbook(stg, config, runtime_cache_dir=runtime, refresh=True)
    assert doc.complete
    assert doc.profile.sheet(SHEET).band("stage").layer_evidence == "schema_value"
    assert list(runtime.glob("*.json")), "the complete profile is cached"
    plain = _write(tmp_path, "plain", bands.one_band())
    doc, _ = resolve_workbook(plain, config, runtime_cache_dir=runtime)
    assert doc.fingerprint == resolve_workbook(stg, config, use_cache=False)[0].fingerprint
    assert not doc.cache_hit
    assert any("re-derived" in r.reason for r in doc.rejections)
    assert [q.key for q in doc.questions] == [f"{SHEET}/band[1]/layer"]
    hit, _ = resolve_workbook(stg, config, runtime_cache_dir=runtime)
    assert hit.cache_hit and hit.complete     # the stg_ workbook itself still re-derives stage


def test_app_answer_payload_accepts_band_layers_only_as_a_layer():
    parsed = parse_answers({"sttm": {f"{SHEET}/band[2]/layer": "stage"}})
    assert parsed["sttm"] == {f"{SHEET}/band[2]/layer": "stage"}
    with pytest.raises(ValueError, match="source | stage | standard"):
        parse_answers({"sttm": {f"{SHEET}/band[2]/layer": "landing"}})
    with pytest.raises(ValueError):
        parse_answers({"sttm": {f"{SHEET}/band[2]/layer": 7}})


# --------------------------------------------------------------- the CLI


def _keys(out: str, label: str) -> list[str]:
    return [line[cli.ANSWER_LABEL_WIDTH:].split(" — ", 1)[0]
            for line in out.splitlines() if line.startswith(label + " ") and " — " in line]


def _answers_file(tmp_path: Path) -> Path:
    path = tmp_path / "answers.yaml"
    path.write_text(yaml.safe_dump({"answers": [
        {"sheet": SHEET, "layer": f"band[{n}]", "role": "layer", "value": layer}
        for n, layer in ((1, "source"), (2, "stage"), (3, "standard"))]}), encoding="utf-8")
    return path


@pytest.fixture()
def cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_LAYOUT", "1")
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    state, outputs = tmp_path / "state", tmp_path / "outputs"
    state.mkdir()
    outputs.mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{state.as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{outputs.as_posix()}")
    return tmp_path


def test_cli_chain_asks_per_band_then_completes_after_answers(cli_env, capsys):
    tmp_path = cli_env
    workbook = _write(tmp_path, f"STTM_{bands.FEED}", bands.three_lookalike())
    frd = tmp_path / "frd.contract.json"
    # The look-alike sheet's stage band says nb_land (no stg_ prefix - it must ask).
    # The FRD states the catalogs (the suite runs without the ACFC overlay and
    # its default_catalog; a two-part name is never written).
    contract = bands.frd_contract(stage_schema="nb_land")
    contract["feeds"][0]["stage_target"]["catalog"] = "nb_dlk"
    contract["feeds"][0]["standard_target"]["catalog"] = "nb_std"
    frd.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    sttm_out = tmp_path / "sttm.contract.json"
    wanted = list(ANSWERED)

    # layout: one UNRESOLVED line per band, exit 3; the harness records them.
    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(workbook), "--dry-run", "--no-cache",
                     "--require-complete"]) == cli.EXIT_NEEDS_ANSWERS
    out = capsys.readouterr().out
    assert _keys(out, "UNRESOLVED") == wanted
    assert [m.group(1) for ln in out.splitlines() if (m := _NEEDED_KEY_RE.match(ln))] == wanted
    assert "answer under answers: with source | stage | standard" in out

    # extract-sttm without answers: the only sheet is held back, nothing written.
    assert cli.main(["extract-sttm", "--workbook", str(workbook), "--frd-contract", str(frd),
                     "--out", str(sttm_out), "--generated-date", "2026-10-09"]) \
        == cli.EXIT_NEEDS_ANSWERS
    out = capsys.readouterr().out
    assert _keys(out, "UNRESOLVED") == wanted and _keys(out, "QUESTION") == []
    assert "answer under answers: in answers.yaml" in out
    assert not sttm_out.exists()

    # With answers.yaml: layout complete, extract-sttm writes, generate completes.
    answers = _answers_file(tmp_path)
    assert cli.main(["layout", "--workbook", str(workbook), "--dry-run", "--no-cache",
                     "--require-complete", "--answers", str(answers)]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert _keys(out, "UNRESOLVED") == [] and _keys(out, "QUESTION") == []
    assert cli.main(["extract-sttm", "--workbook", str(workbook), "--frd-contract", str(frd),
                     "--out", str(sttm_out), "--generated-date", "2026-10-09",
                     "--answers", str(answers)]) == cli.EXIT_OK
    contract = json.loads(sttm_out.read_text(encoding="utf-8"))
    feed = contract["feeds"][0]
    assert feed["stage"]["table"] == bands.FEED and feed["field_count"] == len(bands.FIELDS)
    assert contract.get("needs_answers", []) == []      # written only when non-empty
    capsys.readouterr()
    code = cli.main(["generate", "--frd-contract", str(frd), "--sttm-contract", str(sttm_out),
                     "--dry-run", "--skip-tests", "--output-mode", "framework",
                     "--profile", "acfc_prx", "--iig-template", "iig_v2"])
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK, out
    assert _keys(out, "UNRESOLVED") == [] and _keys(out, "QUESTION") == []


def test_cli_missing_tablename_prints_the_table_question(cli_env, capsys):
    workbook = _write(cli_env, "STTM_missing_table", bands.missing_table())
    capsys.readouterr()
    assert cli.main(["layout", "--workbook", str(workbook), "--dry-run", "--no-cache",
                     "--require-complete"]) == cli.EXIT_NEEDS_ANSWERS
    assert _keys(capsys.readouterr().out, "UNRESOLVED") == [f"{SHEET}/stage/table"]


def test_unresolved_report_names_the_band_answer_form(config, tmp_path):
    from codegen.layout.answers import unresolved_report

    doc, _ = resolve_workbook(_write(tmp_path, "one", bands.one_band()), config,
                              use_cache=False)
    report = unresolved_report(doc.questions, {"sttm": "one.xlsx"})
    assert f"`{SHEET}/band[1]/layer`" in report
    assert "`value: source | stage | standard`" in report
    # structural labels only: header texts, never a data cell
    assert "nb_member_risk" not in report and "stg_nb" not in report


def test_header_cells_are_structural_only(config, tmp_path):
    """The band question's reason quotes header texts, never a data cell."""
    profile = discover(_write(tmp_path, "two", bands.two_claim_stage()), config.extractor).profile
    for item in profile.unresolved:
        assert "stg_nb" not in item.reason and "nb_member_risk" not in item.reason
    assert normalize("Schema") == "schema" and text(" x ") == "x"
