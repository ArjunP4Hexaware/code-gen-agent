"""post56 (D1, 2026-10-15 10:07): the App showed "D1 (1 required missing:
storage_account, from overlay environments.D1; default)" while
codegen-state/environments/d1.yaml existed and the CLI resolved it. The App
already called the CLI's resolver; what differed was the FOLDER — derived from
the code's own location, and the App runs a staged copy (``databricks sync``
honours .gitignore, so codegen-state never reaches it). Now:

- one resolver, ``codegen.environments.resolve`` — explicit file >
  ``<state root>/environments/<name>.yaml`` > the overlay block > unset
  (INPUT_NEEDED / QUESTION), with the source of every field;
- the root is a setting, ``CODEGEN_STATE_DIR`` (logged at App startup).

The same profile set gives the App and the CLI the same environment."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from types import MethodType, SimpleNamespace

import pytest

from codegen.config import load_config, state_overlays_dir, state_root
from codegen.environments import display_path, profiles_dir, resolve, state_dirs_line
from post51_pairs import family_e_frd, family_e_workbook

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "config.yaml"
ACFC_OVERLAY = REPO / "config" / "overlays" / "acfc_env.yaml"
ACCOUNT = "synacct01"


@pytest.fixture
def state(tmp_path, monkeypatch):
    """A codegen-state root named ONLY by CODEGEN_STATE_DIR (the suite's own
    environment-folder variables removed)."""
    root = tmp_path / "state"
    (root / "environments").mkdir(parents=True)
    monkeypatch.delenv("CODEGEN_ENVIRONMENTS_DIR", raising=False)
    monkeypatch.delenv("CODEGEN_STATE_OVERLAYS_DIR", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_DIR", str(root))
    return root


def _app(config):
    pytest.importorskip("fastapi")
    from ui.backend.demo import DemoRunner

    runner = SimpleNamespace(_store=SimpleNamespace(config=config), _lock=threading.Lock(),
                             state="idle", environment_choice=None, iig_template="iig_v2",
                             effective_output_parts=lambda: ["framework"])
    for name in ("run_environment", "select_environment", "environment_options",
                 "_run_level_inputs"):
        setattr(runner, name, MethodType(getattr(DemoRunner, name), runner))
    return runner


def _cli_banner(tmp_path: Path) -> str:
    """The banner a CLI generate prints for the default environment."""
    overlay = tmp_path / "out_overlay.yaml"
    overlay.write_text(f"output:\n  dir: {(tmp_path / 'out').as_posix()}\n"
                       f"  reports_dir: {(tmp_path / 'reports').as_posix()}\n", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1",
           "CODEGEN_CONFIG_OVERLAYS": f"{ACFC_OVERLAY};{overlay}",
           "CODEGEN_NOTIFICATION_EMAILS": "syn.dl.prodsupport@synthetic.example"}
    frd = family_e_frd(tmp_path / "frd.json")
    extracted = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "extract-sttm", "--workbook",
         str(family_e_workbook(tmp_path / "e.xlsx", [None])), "--frd-contract", str(frd),
         "--out", str(tmp_path / "sttm.json"), "--config", str(CONFIG)],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert extracted.returncode == 0, extracted.stdout + extracted.stderr
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "generate", "--config", str(CONFIG),
         "--frd", str(frd), "--sttm", str(tmp_path / "sttm.json"), "--dry-run",
         "--skip-tests", "--output-mode", "framework", "--profile", "acfc_prx",
         "--iig-template", "iig_v2"],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=REPO)
    match = re.search(r"run\.environment — environment: (.+?)$", done.stdout, re.M)
    assert match, done.stdout + done.stderr
    return match.group(1)


def test_the_state_root_is_a_setting(state):
    assert state_root() == state
    assert profiles_dir() == state / "environments"
    assert state_overlays_dir() == state / "overlays"
    line = state_dirs_line()
    assert line.startswith(f"codegen-state root: {display_path(state)} (CODEGEN_STATE_DIR)")
    assert "overlays" in line and "[MISSING]" in line          # no overlays folder here


def test_a_profile_with_the_storage_account_is_complete_in_app_and_cli(state, tmp_path):
    (state / "environments" / "d1.yaml").write_text(f"storage_account: {ACCOUNT}\n",
                                                    encoding="utf-8")
    config = load_config(CONFIG, overlays=[ACFC_OVERLAY])
    options = _app(config).environment_options()
    assert options["missing_required"] == []
    assert options["banner"].startswith("D1 (complete, from ")
    profile = f"profile {display_path(state / 'environments' / 'd1.yaml')}"
    assert options["sources"]["storage_account"] == profile
    assert options["sources"] == resolve(config).sources            # the one resolver
    assert options["profiles_dir"] == display_path(state / "environments")
    assert _cli_banner(tmp_path) == options["banner"]                # the CLI agrees


def test_without_a_profile_app_and_cli_both_ask_for_it(state, tmp_path):
    config = load_config(CONFIG, overlays=[ACFC_OVERLAY])
    options = _app(config).environment_options()
    assert options["missing_required"] == ["storage_account"]
    assert options["sources"]["storage_account"] == \
        "unset — QUESTION run.environment.storage_account"
    assert _cli_banner(tmp_path) == options["banner"]


def test_precedence_file_over_profile_over_overlay(state, tmp_path):
    (state / "environments" / "d1.yaml").write_text(f"storage_account: {ACCOUNT}\n",
                                                    encoding="utf-8")
    config = load_config(CONFIG, overlays=[ACFC_OVERLAY])
    named = resolve(config, live=False)
    overlay_keys = [k for k, v in named.sources.items() if v == "overlay environments.D1"]
    assert named.sources["storage_account"].startswith("profile ")
    assert overlay_keys                       # the overlay block fills what the file leaves
    explicit = tmp_path / "env.yaml"
    explicit.write_text("storage_account: synacct02\ncontainers.stage: syn-stage\n",
                        encoding="utf-8")
    custom = resolve(config, file=explicit, live=False)
    assert custom.sources["storage_account"] == f"--environment-file {display_path(explicit)}"
    assert custom.sources["containers.landing"].startswith("unset — QUESTION")
    edited = resolve(config, overrides={"storage_account": "synacct03"}, live=False)
    assert edited.sources["storage_account"] == "the App form"
    assert edited.sources[overlay_keys[0]] == "overlay environments.D1"
