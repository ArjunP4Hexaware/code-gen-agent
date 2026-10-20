"""post59: PIPELINE_NAME (and the other defaulted inputs) as a three-way choice.

- use_default: the conventions profile's per-flow template, rendered with the
  feed's {domain} {subdomain} {source} {frequency} {layer} {load_mode};
- naming_standard: the BSA's own template, same placeholders (one template for
  the feed renders all four names);
- leave_blank.

Proposed is not applied (Aruna's rule holds for every unattended run). An
unanswered run writes the cells BLANK and records one non-blocking INPUT_NEEDED
line per flow that shows the proposal and its template. A cell is filled only on
an explicit choice: the answers file's ``choice:`` / ``standard:``, or the BSA's
Confirm in the App. A chosen default / standard raises the "taken from other
documents" gate flag (frd_unstated:… source_used:…). CODEGEN_STAGES.json
records source = default | standard | blank (| answer).

A proposal that collides with a PIPELINE_NAME of the loaded goldens / corpus is
never offered. The shipped templates are SYNTHETIC (SYN_PL_…; "no naming
standard loaded — placeholder") and post79 never writes one (no proposal, not
even on use_default); the real ones come from codegen-state/overlays/acfc_prx.yaml,
per flow — these tests lay a fixture template (TEMPLATES, not SYN_) over them.
post79: ``pipeline_name_autoset`` writes the rendered names unasked (a profile
default). Synthetic fixtures only."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codegen import cli, input_choices, run_stages
from codegen.layout.answers import AnswersFileError, load_answers
from test_derivations import FRD, _pair11_specs, _scoped
from test_iig_corpus_cells import NB, OPEN, SCHED, _acfc, _generate
from test_iig_v2_derivations import _rows, _write_overlay

FLOWS = ["grand_master", "master", "file_to_stg", "stg_to_std"]
# the notebook sheet has the two leg rows only; the schedule all four
TAB_FLOWS = {SCHED: FLOWS, NB: FLOWS[2:]}
LAYERS = {"grand_master": "GRANDMASTER", "master": "MASTER", "file_to_stg": "STG",
          "stg_to_std": "STD"}


# post79: a fixture naming convention (not SYN_: a SYN_ placeholder is never written)
TEMPLATES = {
    "grand_master": "PL_{domain}_{subdomain}_{source}_{frequency}_{layer}",
    "master": "PL_{domain}_{subdomain}_{source}_{frequency}_{layer}",
    "file_to_stg": "PL_{domain}_{subdomain}_{source}_{layer}_{load_mode}",
    "stg_to_std": "PL_{domain}_{subdomain}_{source}_{layer}_{load_mode}",
}


def _templates_overlay(tmp_path: Path, *, autoset: bool = False, templates=None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    body = {"conventions": {"profiles": {"acfc_prx": {
        "pipeline_name_templates": dict(templates or TEMPLATES),
        "pipeline_name_autoset": autoset}}}}
    path = tmp_path / "templates_overlay.yaml"
    path.write_text(yaml.safe_dump(body), encoding="utf-8")
    return path


def _pair(tmp_path, *overlays: Path, templates: bool = True):
    first = (_templates_overlay(tmp_path),) if templates else ()
    config = _scoped(_acfc(*first, *overlays), tmp_path)
    contracts = tmp_path / "contracts"
    contracts.mkdir(parents=True)
    specs, _flags = _pair11_specs(FRD, contracts, config)
    return config, specs[0], (contracts / "frd.contract.json", contracts / "sttm.contract.json")


def _answers(tmp_path, text: str) -> Path:
    path = tmp_path / "answers.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _names(tmp_path, spec, tab: str) -> list:
    xlsx = tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"
    return [r["PIPELINE_NAME"][:2] for r in _rows(xlsx, tab)]


def _report(tmp_path, spec) -> str:
    return (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")


def _feed_inputs(tmp_path) -> dict:
    (feed,) = run_stages.read_stage_manifest(tmp_path / "out")["feeds"]
    return feed["inputs"]


def _pipeline_lines(out: str, feed: str) -> list[str]:
    return [ln for ln in out.splitlines()
            if ln.startswith(f"INPUT_NEEDED   feeds.{feed}.pipeline_name.")]


def test_an_unanswered_run_writes_blank_names_and_four_proposals(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path)
    assert _generate(config, pair, only_feed=spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    for tab in (SCHED, NB):
        assert all(value in (None, "") and badge == OPEN for value, badge in
                   _names(tmp_path, spec, tab)), tab
    lines = _pipeline_lines(out, spec.feed_id)
    assert [ln[15:].split(" — ", 1)[0] for ln in lines] == [
        f"feeds.{spec.feed_id}.pipeline_name.{flow}" for flow in FLOWS]
    records = _feed_inputs(tmp_path)
    for flow, line in zip(FLOWS, lines, strict=True):
        record = records[f"pipeline_name.{flow}"]
        assert record["source"] == "blank" and record["chosen"] is False
        assert record["proposed"].startswith("PL_") and LAYERS[flow] in record["proposed"]
        assert record["template"] == TEMPLATES[flow] and "placeholder" not in record
        # the line shows the proposal and its template
        assert f"proposed {record['proposed']!r} (template {record['template']!r})" in line
        assert "not written until chosen" in line
    assert "frd_unstated:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME" not in _report(
        tmp_path, spec)
    manifest = run_stages.read_stage_manifest(tmp_path / "out")
    assert manifest["stages"]["generate"]["status"] == "PASS_WITH_OPEN_INPUTS"
    template = (tmp_path / "out" / "answers_template.yaml").read_text(encoding="utf-8")
    entry = yaml.safe_load(template)["inputs"]["feeds"][spec.feed_id]["pipeline_name.master"]
    assert entry["choice"] == "" and entry["proposed"] == records["pipeline_name.master"][
        "proposed"]                                 # proposed, the choice left empty


def test_use_default_confirmed_writes_the_names_with_the_gate_flag(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path)
    _generate(config, pair, only_feed=spec.feed_id)
    proposed = {flow: _feed_inputs(tmp_path)[f"pipeline_name.{flow}"]["proposed"]
                for flow in FLOWS}
    capsys.readouterr()
    answers = _answers(tmp_path, f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
                                 "      pipeline_name: {choice: use_default}\n")
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    out = capsys.readouterr().out
    for tab in (SCHED, NB):
        assert [v for v, _b in _names(tmp_path, spec, tab)] == [proposed[f]
                                                                for f in TAB_FLOWS[tab]]
    assert _pipeline_lines(out, spec.feed_id) == []
    report = _report(tmp_path, spec)
    for flow in FLOWS:
        assert (f"frd_unstated:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME[{flow}] "
                "source_used:the conventions profile's proposal") in report
        record = _feed_inputs(tmp_path)[f"pipeline_name.{flow}"]
        assert (record["source"], record["chosen"]) == ("default", True)


def test_a_naming_standard_renders_all_four_and_a_flow_may_stay_blank(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path)
    answers = _answers(tmp_path, (
        f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
        "      pipeline_name: {choice: naming_standard, standard: 'acme {source} {layer}'}\n"
        "      pipeline_name.stg_to_std: {choice: leave_blank}\n"))
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    out = capsys.readouterr().out
    xlsx = tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"
    source = str(_rows(xlsx, "ADLS_DELTA_INGESTION_DETAILS")[0]["SOURCE"][0])
    expected = {f: input_choices.render("acme {source} {layer}",
                                        {"source": source, "layer": LAYERS[f]}) for f in FLOWS}
    expected["stg_to_std"] = None                                   # leave_blank
    for tab in (SCHED, NB):
        names = [v or None for v, _b in _names(tmp_path, spec, tab)]
        assert names == [expected[f] for f in TAB_FLOWS[tab]], tab
    assert expected["grand_master"].startswith("ACME_")
    assert expected["grand_master"].endswith("_GRANDMASTER")
    records = _feed_inputs(tmp_path)
    assert [records[f"pipeline_name.{f}"]["source"] for f in FLOWS] == [
        "standard", "standard", "standard", "blank"]
    assert records["pipeline_name.stg_to_std"]["chosen"] is True     # chosen blank: not open
    assert _pipeline_lines(out, spec.feed_id) == []
    report = _report(tmp_path, spec)
    assert "source_used:the BSA's naming standard 'acme {source} {layer}'" in report
    assert "iig_owed_blank:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME[stg_to_std]" in report


def test_a_proposal_that_collides_with_the_corpus_is_never_offered(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path / "probe")
    _generate(config, pair, only_feed=spec.feed_id)
    clash = (run_stages.read_stage_manifest(tmp_path / "probe" / "out")["feeds"][0]["inputs"]
             ["pipeline_name.grand_master"]["proposed"])
    capsys.readouterr()
    names = tmp_path / "goldens" / "names.txt"
    names.parent.mkdir()
    names.write_text(f"SOMETHING_ELSE\n{clash.lower()}\n", encoding="utf-8")   # case-folded
    corpus = names.parent.as_posix()
    overlay = _write_overlay(tmp_path, "conventions:\n  profiles:\n    acfc_prx:\n"
                                       f"      pipeline_name_corpus: ['{corpus}']\n")
    run = tmp_path / "run"
    run.mkdir()
    config, spec, pair = _pair(run, overlay)
    answers = _answers(run, f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
                            "      pipeline_name: {choice: use_default}\n")
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    out = capsys.readouterr().out
    names_written = [v for v, _b in _names(run, spec, SCHED)]
    assert names_written[0] in (None, "") and all(names_written[1:])
    record = _feed_inputs(run)["pipeline_name.grand_master"]
    assert (record["source"], record["chosen"], record["proposed"]) == ("blank", False, "")
    assert "collides with a PIPELINE_NAME" in record["refused"]
    (line,) = _pipeline_lines(out, spec.feed_id)                  # it falls back to asking
    assert ".pipeline_name.grand_master" in line and "no proposal:" in line
    assert clash not in out                                        # the corpus name never printed


def test_application_name_is_proposed_until_chosen(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path)
    _generate(config, pair, only_feed=spec.feed_id)
    xlsx = tmp_path / "out" / spec.feed_slug / "framework" / "config_rows.xlsx"
    assert {r["APPLICATION_NAME"][0] for r in _rows(xlsx, SCHED)} <= {None, ""}
    capsys.readouterr()
    answers = _answers(tmp_path, "inputs:\n  run:\n    application_name: {choice: use_default}\n")
    _generate(config, pair, only_feed=spec.feed_id, answers_path=answers)
    source = str(_rows(xlsx, "ADLS_DELTA_INGESTION_DETAILS")[0]["SOURCE"][0])
    assert {r["APPLICATION_NAME"][0] for r in _rows(xlsx, SCHED)} == {source}
    assert _feed_inputs(tmp_path)["application_name"]["source"] == "default"
    assert "frd_unstated:DATA_FACTORY_PIPELINE_SCHEDULE.APPLICATION_NAME source_used:the " \
           "conventions profile's proposal" in _report(tmp_path, spec)
    assert "INPUT_NEEDED   run.application_name" not in capsys.readouterr().out


def test_the_state_overlay_replaces_a_synthetic_template_per_flow(tmp_path, monkeypatch):
    """The real templates come from codegen-state/overlays/acfc_prx.yaml, one flow
    at a time; the flows it leaves alone keep the SYN_ placeholder."""
    state = tmp_path / "state_overlays"
    state.mkdir()
    (state / "acfc_prx.yaml").write_text(
        "conventions:\n  profiles:\n    acfc_prx:\n      pipeline_name_templates:\n"
        "        file_to_stg: 'ACME_{source}_{layer}_{load_mode}'\n", encoding="utf-8")
    from codegen.config import load_config
    from test_iig_corpus_cells import REPO

    # as a run loads it: acfc_env.yaml selects acfc_prx, which picks acfc_prx.yaml
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_OVERLAYS_DIR", str(state))
    templates = load_config(REPO / "config" / "config.yaml").conventions.get(
        "acfc_prx").pipeline_name_templates
    assert templates["file_to_stg"] == "ACME_{source}_{layer}_{load_mode}"
    assert [input_choices.is_placeholder_template(templates[f]) for f in FLOWS] == [
        True, True, False, True]
    monkeypatch.delenv("CODEGEN_STATE_OVERLAYS_DIR")
    shipped = _acfc().conventions.get("acfc_prx").pipeline_name_templates
    assert all(t.startswith("SYN_PL_") for t in shipped.values())


@pytest.mark.parametrize(("entry", "problem"), [
    ("{choice: use_it}", "choice must be one of use_default, naming_standard, leave_blank"),
    ("{choice: naming_standard, standard: 'X_{vendor}'}", "unknown placeholder(s) ['vendor']"),
])
def test_the_answers_file_refuses_a_bad_choice(tmp_path, entry, problem):
    path = _answers(tmp_path, f"inputs:\n  feeds:\n    f1:\n      pipeline_name: {entry}\n")
    with pytest.raises(AnswersFileError) as raised:
        load_answers(path)
    assert problem in str(raised.value)


def test_a_standard_alone_reads_as_naming_standard(tmp_path):
    path = _answers(tmp_path, "inputs:\n  feeds:\n    f1:\n"
                              "      pipeline_name: {standard: 'X_{layer}'}\n")
    assert load_answers(path).input_choices == {
        "feeds.f1.pipeline_name": input_choices.Choice("naming_standard", "X_{layer}")}


def test_render_makes_a_name():
    tokens = {"domain": "Claims", "subdomain": "", "source": "Vendor & Co.",
              "layer": "STG", "load_mode": "Truncate and Load"}
    assert input_choices.render("PL_{domain}_{subdomain}_{source}_{layer}_{load_mode}",
                                tokens) == "PL_CLAIMS_VENDOR_CO_STG_TRUNCATE_AND_LOAD"
    assert input_choices.render("{source}", tokens, name=False) == "Vendor & Co."


def test_the_app_applies_a_choice_only_after_confirm(tmp_path):
    """The App: the panel's radio rests on use_default, the run before Confirm
    writes nothing; Confirm records the choice (POST /api/demo/input-choices)
    and the next generate applies it — the names, the gate flag."""
    pytest.importorskip("fastapi")
    from types import SimpleNamespace

    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    config, spec, (frd, _sttm) = _pair(tmp_path)
    runner = SimpleNamespace(effective_output_parts=lambda: ["framework"], iig_template="iig_v2",
                             conventions_profile="acfc_prx", input_choices={},
                             status=lambda: {"ok": True})
    items = DemoRunner._owed_inputs(runner, spec, config, frd,
                                    DemoRunner._resolved_inputs(runner, spec, config, frd))
    flow_items = [i for i in items if ".pipeline_name." in i["key"]]
    assert [i["options"] for i in flow_items] == [list(input_choices.CHOICES)] * 4
    assert all(i["proposed"].startswith("PL_") and i["template"].startswith("PL_")
               and not i.get("placeholder") for i in flow_items)
    assert flow_items[0]["tokens"]["layer"] == "GRANDMASTER"     # the live preview's values
    assert input_choices.faq_answers(
        DemoRunner._resolved_inputs(runner, spec, config, frd)) == {}   # nothing confirmed
    with pytest.raises(ValueError, match="choice must be one of"):
        DemoRunner.confirm_input_choices(runner, {"feeds.x.pipeline_name": {"choice": "nope"}})
    DemoRunner.confirm_input_choices(runner, {
        f"feeds.{spec.feed_id}.pipeline_name": {"choice": "use_default"}})
    resolved = DemoRunner._resolved_inputs(runner, spec, config, frd)
    store = GenerationStore(str(Path(__file__).resolve().parents[1] / "config" / "config.yaml"))
    store.config = config
    run = store._generate_feed(spec, dry_run=True, skip_tests=True, out_root=tmp_path / "app",
                               reports_dir=tmp_path / "app_reports", output_mode=["framework"],
                               conventions_profile="acfc_prx", iig_template="iig_v2",
                               faq_answers=input_choices.faq_answers(resolved))
    xlsx = tmp_path / "app" / spec.feed_slug / "framework" / "config_rows.xlsx"
    assert [r["PIPELINE_NAME"][0] for r in _rows(xlsx, SCHED)] == [
        flow_items[i]["proposed"] for i in range(4)]
    assert sum(f.startswith("frd_unstated:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME[")
               for f in run.gate.flags) == 4
    left = DemoRunner._owed_inputs(runner, spec, config, frd, resolved)
    assert not [i for i in left if ".pipeline_name." in i["key"]]   # chosen: no longer open


# ---- post79: autoset from the naming convention; a placeholder is never written --------


def test_a_placeholder_template_is_never_written_not_even_on_use_default(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path, templates=False)          # the shipped SYN_ ones
    answers = _answers(tmp_path, f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
                                 "      pipeline_name: {choice: use_default}\n")
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert all(v in (None, "") for v, _b in _names(tmp_path, spec, SCHED))
    for flow in FLOWS:
        record = _feed_inputs(tmp_path)[f"pipeline_name.{flow}"]
        assert (record["source"], record["proposed"]) == ("blank", "")
        assert input_choices.PLACEHOLDER_LABEL in record["refused"]
    lines = _pipeline_lines(out, spec.feed_id)
    assert len(lines) == 4 and all("no proposal:" in ln for ln in lines)
    assert "SYN_PL_" not in "".join(str(v) for v, _b in _names(tmp_path, spec, SCHED))


def test_autoset_writes_the_convention_unasked_and_one_name_can_be_changed(tmp_path, capsys):
    config, spec, pair = _pair(tmp_path, _templates_overlay(tmp_path / "auto", autoset=True))
    assert _generate(config, pair, only_feed=spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    records = _feed_inputs(tmp_path)
    written = [v for v, _b in _names(tmp_path, spec, SCHED)]
    assert written == [records[f"pipeline_name.{f}"]["proposed"] for f in FLOWS]
    assert all(v.startswith("PL_") for v in written)
    assert all(records[f"pipeline_name.{f}"]["source"] == "profile" for f in FLOWS)
    assert all(records[f"pipeline_name.{f}"]["kind"] == input_choices.PROFILE_DEFAULT
               for f in FLOWS)
    assert _pipeline_lines(out, spec.feed_id) == []                 # nothing asked
    assert "frd_unstated:DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME" not in _report(
        tmp_path, spec)                                             # no gate flag
    # "Change pipeline names": one flow overridden, the others keep the convention
    capsys.readouterr()
    answers = _answers(tmp_path, f"inputs:\n  feeds:\n    {spec.feed_id}:\n"
                                 "      pipeline_name.master: {choice: naming_standard, "
                                 "standard: SYN_CHANGED_MASTER}\n")
    assert _generate(config, pair, only_feed=spec.feed_id, answers_path=answers) == cli.EXIT_OK
    again = [v for v, _b in _names(tmp_path, spec, SCHED)]
    assert again[1] == "SYN_CHANGED_MASTER" and again[0] == written[0] and again[2:] == written[2:]
    assert _feed_inputs(tmp_path)["pipeline_name.master"]["source"] == "standard"


def test_autoset_never_writes_a_placeholder(tmp_path, capsys):
    overlay = tmp_path / "auto_only.yaml"
    overlay.write_text("conventions:\n  profiles:\n    acfc_prx:\n"
                       "      pipeline_name_autoset: true\n", encoding="utf-8")
    config, spec, pair = _pair(tmp_path, overlay, templates=False)
    assert _generate(config, pair, only_feed=spec.feed_id) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert all(v in (None, "") for v, _b in _names(tmp_path, spec, SCHED))
    assert len(_pipeline_lines(out, spec.feed_id)) == 4             # asked instead


def test_the_cell_tokens_a_prod_shaped_template_uses(tmp_path):
    config, spec, _pair_paths = _pair(tmp_path)
    profile = config.conventions.get("acfc_prx")
    tpl = config.metadata.templates["iig_v2"]
    tokens = input_choices.feed_tokens(spec, tpl, None, config)
    for name in ("lob", "object", "object_code", "src_format", "source_code", "schema_domain"):
        assert name in tokens and name in input_choices.PLACEHOLDERS
        assert tokens[name], name                                    # computable on the fixture
    assert tokens["object_code"] == input_choices._words(tokens["object"])[0]
    assert tokens["source_code"] == input_choices._words(tokens["source"])[0]
    name = input_choices.render("PL_MSTR_{source_code}_{schema_domain}_{lob}_{frequency_code}",
                                input_choices.flow_tokens(tokens, spec, profile, "master"))
    assert name.startswith("PL_MSTR_") and "__" not in name and "{" not in name
