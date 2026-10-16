"""Golden alignment, mechanism only (2026-10-15, D1 post50 item 3).

The client values (notebook names / paths / versions, a feed's email status set
and SRC_FILE_NAME style) live in the ACFC-side overlay
``codegen-state/overlays/<profile>.yaml`` — outside the tracked tree; the repo
tracks the schema, the loader, a SYNTHETIC example (config/overlays/example.yaml)
and docs/acfc/OVERLAY_FIELDS.md. Two mechanism bugs visible without client data:
a notebook path without the /Workspace root (notebook_path_prefix), and the
notebook rows' flow lost in iig_diff (both rows one identity: a single-feed
workbook read as ONE notebook row)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from codegen import cli
from codegen.config import FeedOverrideConfig, MetadataTemplateConfig, load_config, overlay_paths
from codegen.metadata_template import _prefix_middle, email_status_set
from test_iig_corpus_cells import _acfc, _generate, _pair11, _rows
from test_iig_v2_derivations import ACFC_OVERLAY, REPO

EXAMPLE = REPO / "config" / "overlays" / "example.yaml"
FIELDS_DOC = REPO / "docs" / "acfc" / "OVERLAY_FIELDS.md"
NB, EMAIL, ADLS = "DATABRICKS_NOTEBOOK_DETAILS", "EMAIL_TEMPLATE_CONFIG", \
    "ADLS_DELTA_INGESTION_DETAILS"
TOKENS = ["CCYY", "YYYY", "YY", "MM", "DD", "HH", "MI", "SS"]


# ---- the out-of-tree overlay -------------------------------------------------

def test_the_state_overlay_is_applied_right_after_acfc_env(tmp_path, monkeypatch):
    folder = tmp_path / "codegen-state" / "overlays"
    folder.mkdir(parents=True)
    shutil.copy(EXAMPLE, folder / "acfc_prx.yaml")
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_OVERLAYS_DIR", str(folder))
    extra = tmp_path / "extra.yaml"
    extra.write_text("metadata: {templates: {iig_v2: {notebook_path_prefix: /Ws}}}\n",
                     encoding="utf-8")
    paths = overlay_paths(REPO / "config" / "config.yaml", [extra])
    assert [p.name for p in paths] == ["acfc_env.yaml", "acfc_prx.yaml", "extra.yaml"]
    config = load_config(REPO / "config" / "config.yaml", overlays=[extra])
    tpl = config.metadata.templates["iig_v2"]
    assert tpl.email_status_default == ["Success", "Failed"]          # the state overlay
    assert tpl.notebook_path_prefix == "/Ws"                          # a later overlay wins
    values = tpl.corpus_cells[NB]["DATABRICKS_NOTEBOOK_NAME"].values
    assert values["stg_to_std"] == "SYN_StdNotebook_V9"                # merged over the
    assert "fixed_width" in values                                     # tracked table


def test_no_state_folder_no_overlay(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEGEN_SKIP_ENV_OVERLAY", raising=False)
    monkeypatch.setenv("CODEGEN_STATE_OVERLAYS_DIR", str(tmp_path / "absent"))
    assert [p.name for p in overlay_paths(REPO / "config" / "config.yaml")] == [
        "acfc_env.yaml"]


def test_the_tracked_example_is_synthetic_and_loads():
    config = load_config(REPO / "config" / "config.yaml", overlays=[ACFC_OVERLAY, EXAMPLE])
    assert config.metadata.templates["iig_v2"].feed_overrides["syn_feed_beta"].src_file_name \
        == "prefix_middle"
    tpl = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))["metadata"]["templates"]["iig_v2"]
    names = [v for cell in tpl["corpus_cells"][NB].values() for v in cell["values"].values()]
    assert all("SYN_" in v for v in names), names


def test_the_fields_doc_names_every_overlay_field():
    text = FIELDS_DOC.read_text(encoding="utf-8")
    for field in ("notebook_path_prefix", "email_status_default", "prefix_middle",
                  *(f"feed_overrides.<feed_id>.{f}" for f in FeedOverrideConfig.model_fields),
                  "DATABRICKS_NOTEBOOK_NAME.values.<kind>", "codegen-state/overlays/<profile>.yaml",
                  "codegen-state/environments/<name>.yaml"):
        assert field in text, field
    assert "notebook_path_prefix" in MetadataTemplateConfig.model_fields


# ---- SRC_FILE_NAME wildcard styles --------------------------------------------

@pytest.mark.parametrize("pattern, expected", [
    ("YYYYMMDD_SYN_0001_Report_*_P_X.txt", "*SYN_0001_Report*.txt"),
    ("*_SYN_0001_Report_*_P_X.txt", "*SYN_0001_Report*.txt"),
    ("syn_package_YYYY_MM.csv", "*syn_package*.csv"),
    ("syn_package_*_*.csv", "*syn_package*.csv"),
    ("SYN_feed.psv", "*SYN_feed*.psv"),
    ("syn_MI_YYYYMMDD_HHMM", "*syn_MI*"),
])
def test_prefix_middle(pattern, expected):
    assert _prefix_middle(pattern, TOKENS, ["MI", "SS"]) == expected


# ---- a run under the synthetic overlay ----------------------------------------

def _overlay(tmp_path, feed: str, extra: dict | None = None) -> Path:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    tpl = data["metadata"]["templates"]["iig_v2"]
    tpl["feed_overrides"] = {feed: extra} if extra else {}
    path = tmp_path / "syn_overlay.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _run(tmp_path, extra=None):
    from test_iig_corpus_cells import _scoped

    tmp_path.mkdir(parents=True, exist_ok=True)
    _config, specs, pair = _pair11(tmp_path)
    feed = specs[0].feed_id
    config = _scoped(_acfc(_overlay(tmp_path, feed, extra)), tmp_path)
    assert _generate(config, pair, only_feed=feed) == cli.EXIT_OK
    xlsx = tmp_path / "out" / specs[0].feed_slug / "framework" / "config_rows.xlsx"
    return xlsx, specs[0]


def test_the_overlay_drives_the_notebook_rows_and_the_workspace_root(tmp_path):
    xlsx, spec = _run(tmp_path)
    rows = _rows(xlsx, NB)
    assert len(rows) == 2                                   # one per leg, stg_to_std kept
    names = [r["DATABRICKS_NOTEBOOK_NAME"][0] for r in rows]
    assert names[1] == "SYN_StdNotebook_V9"
    assert names[0] in ("SYN_StageNotebook_V9", "SYN_TplStageNotebook_V9")
    paths = [r["DATABRICKS_NOTEBOOK_PATH"][0] for r in rows]
    assert paths[1] == "/Workspace/SYN_folder/SYN_StdNotebook_V9"      # the root prepended
    assert all(p.startswith("/Workspace/") for p in paths)
    report = (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")
    assert ("iig_notebook_path:DATABRICKS_NOTEBOOK_PATH — the workspace root '/Workspace' "
            "(notebook_path_prefix) prepended: '/SYN_folder/SYN_StdNotebook_V9'") in report


def test_the_default_status_set_and_a_feed_override(tmp_path):
    # post61: email_status_default is a PROFILE DEFAULT — the overlay says
    # [Success, Failed] and the run gives no answer: two rows
    xlsx, _spec = _run(tmp_path / "default")
    assert [r["STATUS"][0] for r in _rows(xlsx, EMAIL)] == ["Success", "Failed"]
    xlsx, _spec = _run(tmp_path / "override", {
        "email_statuses": ["FilesNotReceived", "New Files to Process", "Success", "Failed"],
        "src_file_name": "prefix_middle"})
    assert [r["STATUS"][0] for r in _rows(xlsx, EMAIL)] == [
        "FilesNotReceived", "New Files to Process", "Success", "Failed"]
    for row in _rows(xlsx, ADLS):
        value = row["SRC_FILE_NAME"][0]
        assert value.startswith("*") and value.count("*") >= 2, value


def test_a_feed_override_beats_the_run_answer():
    tpl = load_config(REPO / "config" / "config.yaml",
                      overlays=[ACFC_OVERLAY, EXAMPLE]).metadata.templates["iig_v2"]

    class Answer:
        value, source = "Success", "answered"

    class Faq:
        email_statuses = Answer()

    assert email_status_set(tpl, Faq(), "syn_feed_alpha")[0] == [
        "FilesNotReceived", "New Files to Process", "Success", "Failed"]
    assert email_status_set(tpl, Faq(), "syn_other")[0] == ["Success"]
    # post61: unanswered = the profile default set (no NOTE: no gate flag)
    assert email_status_set(tpl, None, "syn_other") == (["Success", "Failed"], "")
    from codegen.faq import FaqAnswer
    from codegen.input_choices import evidence

    class Chosen:
        email_statuses = FaqAnswer(value="Success, Failed", source="engineer",
                                   evidence=evidence("default", "email_status_default"))

    assert email_status_set(tpl, Chosen(), "syn_other")[0] == ["Success", "Failed"]


# ---- iig_diff: the notebook rows keep their flow ------------------------------

def test_the_corpus_process_name_shapes_have_a_flow():
    from test_iig_diff_identity import iig_diff

    keys = iig_diff.load_keys(REPO / "tools" / "iig_keys.yaml", env_local=None)
    canon = {"PROCESS_NAME": "PROCESS_NAME"}
    flows = [iig_diff.row_flow(NB, {"PROCESS_NAME": f"SYN-App  {text}"}, canon, keys)
             for text in ("Raw to stage load", "stage to std load", "Stage to Standard load")]
    assert flows == ["file_to_stg", "stg_to_std", "stg_to_std"]
