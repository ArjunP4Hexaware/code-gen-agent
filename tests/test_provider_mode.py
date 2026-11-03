"""The ONE provider switch (codegen.reasoning.mode, 2026-10-13).

A D1 run answered from the mock ("mock profile not found for fingerprint")
and read like a real run. Now: mock | live is explicit — ``--provider`` >
``CODEGEN_PROVIDER`` > ``reasoning.mode`` > mock — never inferred from an
endpoint or a Databricks login; every mock says ``provider=mock``; live that
cannot run is ONE startup line naming the unset setting; and the suite can
never open a live model connection (the guard is a BaseException).
"""

from __future__ import annotations

import pytest

import codegen.databricks as db
from codegen import cli
from codegen.reasoning.mode import (
    LiveModelBlocked,
    ProviderMode,
    guard_live_call,
    provider_mode,
)


def test_the_suite_blocks_every_live_model_connection(config):
    """conftest sets CODEGEN_BLOCK_LIVE_MODEL: a real serving-endpoint call
    raises before any connection opens."""
    pytest.importorskip("databricks.sdk")
    cfg = db.config_for(config.databricks, require=())
    with pytest.raises(LiveModelBlocked, match="CODEGEN_ALLOW_LIVE_TESTS"):
        db.chat(cfg, [{"role": "user", "content": "x"}], endpoint="any-endpoint")


def test_the_guard_cannot_be_swallowed_by_except_exception():
    def layer2_like_call():
        try:
            guard_live_call("the endpoint", env={"CODEGEN_BLOCK_LIVE_MODEL": "1"})
        except Exception:  # noqa: BLE001 — what Layer 2 does with provider errors
            return "a flagged candidate"
        return "called"

    with pytest.raises(LiveModelBlocked):
        layer2_like_call()


def test_the_anthropic_client_is_blocked_too(config):
    pytest.importorskip("anthropic")
    from codegen.reasoning.providers.anthropic_provider import AnthropicProvider

    with pytest.raises(LiveModelBlocked):
        AnthropicProvider(config)


def test_an_explicit_opt_in_lets_a_live_test_through():
    guard_live_call("x", env={"CODEGEN_BLOCK_LIVE_MODEL": "1",
                              "CODEGEN_ALLOW_LIVE_TESTS": "1"})       # no raise
    guard_live_call("x", env={})                                       # outside the suite


def test_a_stand_in_sdk_opens_no_connection_and_passes():
    import types

    guard_live_call("x", env={"CODEGEN_BLOCK_LIVE_MODEL": "1"},
                    sdk_module=types.ModuleType("anthropic"))           # no raise


@pytest.mark.parametrize("env, expected", [
    ({}, ProviderMode("mock", "default")),
    ({"DATABRICKS_HOST": "https://x", "DATABRICKS_APP_PORT": "1"}, ProviderMode("mock", "default")),
    ({"CODEGEN_PROVIDER": "live"}, ProviderMode("live", "CODEGEN_PROVIDER")),
    ({"CODEGEN_PROVIDER": "MOCK"}, ProviderMode("mock", "CODEGEN_PROVIDER")),
])
def test_resolution_never_infers_live(config, env, expected):
    assert provider_mode(config, env) == expected


def test_config_mode_and_the_flag(config):
    from codegen.reasoning.mode import set_flag

    live_cfg = config.model_copy(update={"reasoning": config.reasoning.model_copy(
        update={"mode": "live"})})
    assert provider_mode(live_cfg, {}).text() == "provider=live (config reasoning.mode)"
    set_flag("mock")
    try:
        assert provider_mode(live_cfg, {"CODEGEN_PROVIDER": "live"}).text() == (
            "provider=mock (--provider)")
    finally:
        set_flag(None)


def test_the_first_line_and_doctor_name_the_provider(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{tmp_path.as_posix()}")
    assert cli.main(["doctor"]) == 0
    assert "provider=mock (default)" in capsys.readouterr().out.splitlines()[0]
    cli.main(["extract-frd", "--docx", str(tmp_path / "missing.docx"),
              "--out", str(tmp_path / "x.json")])
    assert "provider=mock (default)" in capsys.readouterr().out.splitlines()[0]


def test_live_with_the_endpoint_unset_fails_at_startup(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVING_ENDPOINT", "")
    overlay = tmp_path / "no_endpoint.yaml"
    overlay.write_text("databricks:\n  serving_endpoint: ''\n", encoding="utf-8")
    monkeypatch.setenv("CODEGEN_CONFIG_OVERLAYS", str(overlay))
    code = cli.main(["--provider", "live", "extract-frd", "--docx", str(tmp_path / "x.docx"),
                     "--out", str(tmp_path / "x.json")])
    lines = capsys.readouterr().out.splitlines()
    assert code == 1
    assert "provider=live (--provider)" in lines[0]
    fail = [line for line in lines if line.startswith("FAIL")]
    assert fail == [fail[0]] and "databricks.serving_endpoint is unset" in fail[0], lines


def test_the_mock_says_provider_mock_when_it_knows_no_profile(tmp_path):
    from codegen.layout.model import LayoutProviderError, MockLayoutProvider

    mock = MockLayoutProvider([tmp_path], reason="provider=mock (default)")
    with pytest.raises(LayoutProviderError) as excinfo:
        mock.complete_layout({"fingerprint": "abc"})
    message = str(excinfo.value)
    assert message.startswith("provider=mock (default): the mock layout provider has no "
                              "profile for fingerprint abc")
    assert "CODEGEN_PROVIDER=live" in message
    dry = MockLayoutProvider([tmp_path], reason="dry-run")
    with pytest.raises(LayoutProviderError, match=r"^provider=mock \(dry-run\)"):
        dry.complete_layout({"fingerprint": "abc"})


def test_the_serving_model_is_opus_5_5(config):
    """2026-10-13 (Soham): the Foundation Model endpoint serves Claude Opus 5.5."""
    from codegen.reasoning.usage import model_display_name

    assert config.reasoning.model == "claude-opus-5-5"
    assert config.databricks.serving_endpoint == "databricks-claude-opus-5-5"
    assert model_display_name(config.reasoning.model) == "Claude Opus 5.5"


def test_dry_run_under_live_is_a_warning_first_in_the_run_and_the_report(tmp_path, capsys,
                                                                          monkeypatch):
    """--dry-run under provider=live answers from the mock — said as the FIRST
    line of the run and of the report, never a quiet downgrade."""
    from acfc_shapes import family_e_multi as fm
    from codegen.reasoning.mode import DRY_RUN_OVER_LIVE

    monkeypatch.setenv("CODEGEN_NOTIFICATION_EMAILS", "syn.dl@synthetic.example")
    for name in ("state", "out"):
        (tmp_path / name).mkdir()
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{(tmp_path / 'state').as_posix()}")
    monkeypatch.setenv("CODEGEN_STORAGE_OUTPUTS", f"local:{(tmp_path / 'out').as_posix()}")
    sttm, frd = tmp_path / "STTM.xlsx", tmp_path / "FRD.docx"
    fm.build_sttm().save(sttm)
    frd.write_bytes(fm.build_frd())
    frd_out, sttm_out = tmp_path / "frd.json", tmp_path / "sttm.json"
    assert cli.main(["--provider", "live", "layout", "--workbook", str(sttm), "--frd", str(frd),
                     "--dry-run", "--no-cache", "--frd-contract-out", str(frd_out)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("WARNING") and DRY_RUN_OVER_LIVE in lines[0]
    assert DRY_RUN_OVER_LIVE in lines[1]                      # the version line says it too
    assert cli.main(["extract-sttm", "--workbook", str(sttm), "--frd-contract", str(frd_out),
                     "--out", str(sttm_out), "--generated-date", "2026-10-13"]) == 0
    capsys.readouterr()
    assert cli.main(["--provider", "live", "generate", "--frd-contract", str(frd_out),
                     "--sttm-contract", str(sttm_out), "--feed", "nb_cm_north", "--dry-run",
                     "--skip-tests", "--output-mode", "framework"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("WARNING")
    assert f"Mock provider (reason: {DRY_RUN_OVER_LIVE})" in out
    (report,) = (tmp_path / "out").rglob("reports/nb_cm_north.md")
    text = report.read_text(encoding="utf-8")
    assert text.splitlines()[0] == f"> **WARNING** {DRY_RUN_OVER_LIVE}"
    assert f"provider_overridden: {DRY_RUN_OVER_LIVE}" in text


def test_a_plain_dry_run_under_mock_says_nothing_extra(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("CODEGEN_STORAGE_STATE", f"local:{tmp_path.as_posix()}")
    cli.main(["layout", "--workbook", str(tmp_path / "missing.xlsx"), "--dry-run"])
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith("codegen ") and "provider=mock (default)" in first
