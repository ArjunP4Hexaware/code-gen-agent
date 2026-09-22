"""Provider labels are derived from what the run did; outputs are exactly two.

Goal A — every user-facing provider label renders from the per-run record
(``codegen.reasoning.usage``): a live-stub run and a mock-locked run each show
the SAME label in the API payload, the generation report and the CLI line; a
layout the synonyms resolve alone says no model call was needed.

Goal B — the output choices are exactly Notebook and Framework artefacts; a
retired value (both / rfc / all) in config or saved state maps to both with a
one-time notice, never an error.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen import cli
from codegen.config import load_config
from codegen.layout.model import MockLayoutProvider, build_layout_provider
from codegen.layout.resolve import resolve_workbook
from codegen.output_modes import OUTPUT_OPTIONS, notices, output_parts
from codegen.reasoning.schema import CandidateResponse
from codegen.reasoning.usage import (
    NO_CALL_NEEDED,
    StageUsage,
    layout_usage,
    model_display_name,
)
from codegen.resolve.resolver import resolve_pair

REPO = Path(__file__).resolve().parents[1]
_FRD = REPO / "fixtures" / "contracts" / "FRD_demo_cv_golden.contract.json"
_STTM = REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_cv_golden.json"
SHAPES_STTM = REPO / "fixtures" / "acfc_shapes" / "sttm"

needs_demo_pair = pytest.mark.skipif(
    not (_FRD.is_file() and _STTM.is_file()),
    reason="demo fixture pair not restored (removed 2026-08-22)",
)

LIVE_LABEL_PREFIX = "Claude Opus 5 (databricks-claude-opus-5) · "
LOCKED_LABEL = "Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)"


class _LiveStub:
    """Stands in for DatabricksFmapiProvider: same name / endpoint / model /
    call counter, no network."""

    name = "databricks_fmapi"
    endpoint = "databricks-claude-opus-5"
    model = "claude-opus-5"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, pack):
        self.calls += 1
        return CandidateResponse(classification="mappable", code_candidate="# stub",
                                 rationale="live stub", citations=[pack.rule_text])


# ------------------------------------------------------------------ the labels


def test_the_three_label_shapes():
    live = StageUsage(stage="layer2", provider="databricks_fmapi",
                      endpoint="databricks-claude-opus-5", model="claude-opus-5",
                      calls=3, requests=3)
    assert live.label == "Claude Opus 5 (databricks-claude-opus-5) · 3 call(s)"
    assert StageUsage(stage="layout", provider="mock", requests=0).label == NO_CALL_NEEDED
    locked = StageUsage(stage="layer2", provider="mock", requests=2,
                        mock_reason="CODEGEN_FORCE_MOCK_PROVIDER")
    assert locked.label == LOCKED_LABEL and locked.forced_mock
    # A mock built outside the builders still says it is a mock.
    assert StageUsage(
        stage="layer2", provider="mock", requests=1).label == "Mock provider (reason: test)"
    assert model_display_name("claude-opus-4-8") == "Claude Opus 4.8"
    assert "mock" not in live.label.lower()


def _config(tmp: Path):
    config = load_config(REPO / "config" / "config.yaml")
    return config.model_copy(update={"output": config.output.model_copy(update={
        "dir": str(tmp / "out"), "reports_dir": str(tmp / "reports")})})


def _feed_with_unmapped_rules(config):
    from codegen.rules.compiler import compile_rules

    for spec in resolve_pair(_FRD, _STTM, config):
        if any(o.classification == "unmapped" for o in compile_rules(spec)):
            return spec
    pytest.skip("no CV feed carries an unmapped rule")


def _api_usage(store, monkeypatch) -> list[dict]:
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ui.backend import main

    monkeypatch.setattr(main, "store", store)
    return TestClient(main.app).get("/api/feeds").json()["model_usage"]


def _run_both_paths(tmp_path, monkeypatch, capsys, provider_factory):
    """One feed through the UI store (-> API + report) and through the CLI
    (-> console + report); returns the labels each surface shows."""
    pytest.importorskip("httpx")
    from ui.backend import service
    from ui.backend.service import GenerationStore

    config = _config(tmp_path)
    spec = _feed_with_unmapped_rules(config)
    if provider_factory is not None:
        monkeypatch.setattr(service, "build_provider", lambda *_a: provider_factory())
        monkeypatch.setattr(cli, "build_provider", lambda *_a: provider_factory())

    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    store.config = config
    run = store._generate_feed(spec, dry_run=False, skip_tests=True,
                               out_root=tmp_path / "ui_out", reports_dir=tmp_path / "ui_reports")
    store.adopt({spec.feed_slug: run}, [], mode="live", label="demo_test",
                out_root=tmp_path / "ui_out", reports_root=tmp_path / "ui_reports")
    (api,) = [u["label"] for u in _api_usage(store, monkeypatch) if u["stage"] == "layer2"]
    ui_report = (tmp_path / "ui_reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")

    capsys.readouterr()
    cli._generate_feed(spec, config, dry_run=False, skip_tests=True)
    console = capsys.readouterr().out
    cli_report = (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")
    return api, ui_report, console, cli_report


@needs_demo_pair
def test_a_live_stub_run_labels_every_surface_live(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CODEGEN_FORCE_MOCK_PROVIDER", raising=False)
    stubs: list[_LiveStub] = []

    def factory():
        stubs.append(_LiveStub())
        return stubs[-1]

    api, ui_report, console, cli_report = _run_both_paths(tmp_path, monkeypatch, capsys, factory)
    calls = stubs[0].calls
    assert calls > 0
    label = f"{LIVE_LABEL_PREFIX}{calls} call(s)"
    assert api == label
    assert f"- Layer 2 (rule reasoning): {label}" in ui_report
    assert f"- Layer 2 (rule reasoning): {label}" in cli_report
    assert f"MODEL USAGE     layer2: {label}" in console
    # No surface calls a live run a mock.
    for text in (api, ui_report.split("## Model usage")[1].split("## Gate")[0]):
        assert "mock" not in text.lower()


@needs_demo_pair
def test_a_locked_run_labels_every_surface_mock_with_the_lock(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    api, ui_report, console, cli_report = _run_both_paths(tmp_path, monkeypatch, capsys, None)
    assert api == LOCKED_LABEL
    assert f"- Layer 2 (rule reasoning): {LOCKED_LABEL}" in ui_report
    assert f"- Layer 2 (rule reasoning): {LOCKED_LABEL}" in cli_report
    assert f"MODEL USAGE     layer2: {LOCKED_LABEL}" in console
    # The pre-run transport label says the same thing (never hidden).
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ui.backend import main
    from ui.backend.service import GenerationStore

    monkeypatch.setattr(main, "store", GenerationStore(str(REPO / "config" / "config.yaml")))
    live = TestClient(main.app).get("/api/demo/live-available").json()
    assert live["transport"]["label"] == LOCKED_LABEL


def test_a_synonyms_only_layout_needs_no_model_call(config, tmp_path):
    provider = build_layout_provider(config, dry_run=True, base_dir=REPO)
    doc, _wb = resolve_workbook(SHAPES_STTM / "pair_2_family_b.xlsx", config, provider=provider,
                                use_cache=False, base_dir=REPO)
    assert not doc.profile.unresolved and provider.requests == []
    assert layout_usage(provider).label == NO_CALL_NEEDED


def test_a_layout_the_mock_answers_says_mock_and_why(config):
    provider = build_layout_provider(config, dry_run=True, base_dir=REPO)
    assert isinstance(provider, MockLayoutProvider)
    resolve_workbook(SHAPES_STTM / "pair_7_family_e.xlsx", config, provider=provider,
                     use_cache=False, base_dir=REPO)
    assert provider.requests, "pair 7 needs the model (tests/acfc_shapes/layout_truth.py)"
    assert layout_usage(provider).label == "Mock provider (reason: dry-run)"


# ------------------------------------------------------------------ the outputs


def test_output_options_endpoint_returns_exactly_notebook_and_framework(monkeypatch):
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ui.backend import main

    reply = TestClient(main.app).get("/api/demo/output-options")
    assert reply.status_code == 200
    assert reply.json() == ["notebook", "framework"] == list(OUTPUT_OPTIONS)


def test_cli_offers_exactly_the_two_outputs(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["generate", "--frd", "x", "--sttm", "y", "--output-mode", "rfc"])
    assert exit_info.value.code == 2                      # argparse: invalid choice
    assert "choose from 'notebook', 'framework'" in capsys.readouterr().err


@pytest.mark.parametrize("retired", ["both", "rfc", "all"])
def test_a_retired_config_value_maps_to_both_outputs_with_one_notice(retired, tmp_path, caplog):
    overlay = tmp_path / "overlay.yaml"
    overlay.write_text(f"output:\n  mode: {retired}\n", encoding="utf-8")
    source = "config output.mode"
    first = load_config(REPO / "config" / "config.yaml", overlays=[overlay])
    second = load_config(REPO / "config" / "config.yaml", overlays=[overlay])
    assert first.output.mode == second.output.mode == ["notebook", "framework"]
    announced = [n for n in notices() if n.startswith(f"{source}: output {retired!r}")]
    assert len(announced) == 1          # once per process, however often it is read


def test_selections_normalize_and_only_a_never_valid_value_raises():
    assert output_parts("notebook") == ["notebook"]
    assert output_parts(["framework", "notebook"]) == ["notebook", "framework"]
    assert output_parts([]) == []
    assert output_parts(["rfc"], source="saved state") == ["notebook", "framework"]
    with pytest.raises(ValueError):
        output_parts("zip")


def test_a_past_run_recorded_as_rfc_replays_as_both_outputs(tmp_path):
    """A run_meta.json from before the change says output_mode 'rfc'."""
    import json

    meta = tmp_path / "run_meta.json"
    meta.write_text(json.dumps({"output_mode": "rfc"}), encoding="utf-8")
    recorded = json.loads(meta.read_text(encoding="utf-8"))["output_mode"]
    assert output_parts(recorded, source="run_meta.json of demo_old") == ["notebook", "framework"]
