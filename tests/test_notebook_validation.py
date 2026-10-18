"""post68: every emitted notebook is nbformat-valid.

``tests/conftest.py`` wraps the two notebook writers (``build_notebook`` and
``resync_notebook``) for EVERY test, so each notebook any test emits is
checked with ``nbformat.validate`` as it is written. This file proves the
check is on and bites: nbformat is installed (the dev extra; pinned in
constraints/acfc_d1.txt), the SFMC fixture and synthetic pair 11 notebooks go
through it, and an invalid notebook is refused.
"""

from __future__ import annotations

import json

import pytest

import conftest
from codegen import cli
from codegen.config import load_config
from conftest import REPO
from test_iig_corpus_cells import _pair11


def test_nbformat_is_installed():
    import nbformat

    assert nbformat.__version__.split(".")[0] == "5"


def test_the_sfmc_fixture_notebook_is_validated(tmp_path):
    before = conftest.NOTEBOOKS_VALIDATED["count"]
    config = load_config(REPO / "config" / "config.yaml")
    config = config.model_copy(update={"output": config.output.model_copy(
        update={"dir": str(tmp_path / "out"), "reports_dir": str(tmp_path / "reports")})})
    pair = (REPO / "fixtures" / "contracts" / "FRD_sfmc_email_campaign.contract.json",
            REPO / "fixtures" / "contracts" / "sttm_mapping_contracts_sfmc.json")
    cli._run_pairs([pair], config, dry_run=True, skip_tests=True, output_mode=["notebook"],
                   only_feed=None)
    assert list((tmp_path / "out").rglob("*.ipynb"))
    assert conftest.NOTEBOOKS_VALIDATED["count"] > before


def test_the_synthetic_acfc_pair_notebook_is_validated(tmp_path):
    before = conftest.NOTEBOOKS_VALIDATED["count"]
    config, specs, pair = _pair11(tmp_path)
    cli._run_pairs([pair], config, dry_run=True, skip_tests=True, output_mode=["notebook"],
                   conventions_profile="acfc_prx", iig_template="iig_v2",
                   only_feed=specs[0].feed_id)
    assert list((tmp_path / "out").rglob("*.ipynb"))
    assert conftest.NOTEBOOKS_VALIDATED["count"] > before


def test_an_invalid_notebook_is_refused():
    from nbformat import ValidationError

    broken = {"nbformat": 4, "nbformat_minor": 5, "metadata": {},
              "cells": [{"cell_type": "code", "source": "x = 1"}]}   # no outputs / metadata
    with pytest.raises(ValidationError):
        conftest._validate_notebook_text(json.dumps(broken))
