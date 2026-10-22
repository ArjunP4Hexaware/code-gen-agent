"""post91: notebooks off in the App, one config line to turn them back on.

``output.app_options`` (config/config.yaml: [framework]) is what the App offers:
its output options, the parts a run may select, the default its runs use. A
part it does not offer is refused; a saved choice of one is dropped. The CLI
(output.mode / --output-mode) is not affected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codegen.config import load_config

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def runner(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from ui.backend.demo import DemoRunner
    from ui.backend.service import GenerationStore

    monkeypatch.setenv("CODEGEN_FORCE_MOCK_PROVIDER", "1")
    for role in ("state", "outputs"):
        (tmp_path / role).mkdir()
        monkeypatch.setenv(f"CODEGEN_STORAGE_{role.upper()}",
                           f"local:{(tmp_path / role).as_posix()}")
    monkeypatch.chdir(REPO)
    store = GenerationStore(str(REPO / "config" / "config.yaml"))
    return DemoRunner(store, index_warmup=False)


def _offering(runner, parts):
    config = runner._store.config                                 # noqa: SLF001
    runner._store.config = config.model_copy(update={"output": config.output.model_copy(  # noqa: SLF001
        update={"app_options": parts})})


def test_the_shipped_app_offers_framework_only():
    config = load_config(REPO / "config" / "config.yaml")
    assert config.output.app_options == ["framework"]
    assert config.output.mode == ["notebook"]                     # the CLI default unchanged


def test_a_notebook_choice_is_refused(runner):
    with pytest.raises(ValueError, match="not offered in the App"):
        runner.select_output_parts(["notebook", "framework"])
    with pytest.raises(ValueError, match="not offered in the App"):
        runner.select_output_mode("notebook")
    runner.select_output_parts(["framework"])
    assert runner.effective_output_parts() == ["framework"]


def test_a_saved_notebook_choice_is_dropped(runner):
    runner.output_parts = ["notebook", "framework"]               # an older saved state
    assert runner.effective_output_parts() == ["framework"]
    runner.output_parts = ["notebook"]
    assert runner.effective_output_parts() == ["framework"]       # the App's default


def test_listing_notebook_again_turns_it_back_on(runner):
    _offering(runner, ["notebook", "framework"])
    runner.select_output_parts(["notebook", "framework"])
    assert runner.effective_output_parts() == ["notebook", "framework"]


def test_the_shipped_app_hides_the_iig_review_workbook():
    """post98 (Soham): the App does not list the IIG review workbook; adding
    iig_review back to output.app_files shows it again. The model default lists
    every kind, so a config without the line changes nothing."""
    config = load_config(REPO / "config" / "config.yaml")
    assert config.output.app_files == ["ddl", "iig", "addition", "log"]
    assert "iig_review" in type(config.output).model_fields["app_files"].default


def test_the_shipped_app_names_only_the_ids_the_engineer_assigns():
    """post101 (Soham): the panel's blank-IDs line names PIPELINE_ID,
    PARENT_PIPELINE_ID and GROUP_ID only; the default (empty) keeps the full list."""
    config = load_config(REPO / "config" / "config.yaml")
    assert list(config.output.app_assign_ids) == ["PIPELINE_ID", "PARENT_PIPELINE_ID", "GROUP_ID"]
    assert type(config.output).model_fields["app_assign_ids"].default_factory() == {}
