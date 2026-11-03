"""post74 (D1 post73 item 8): pair_11 took 556 s, and the pushed report had no
MODEL USAGE line to say where.

1. The live layout path asks the model at most ONCE per document — one request
   for the whole STTM workbook (every sheet's header region and every open
   role, whatever the number of sheets / feeds), one for the FRD, one for a
   VDD — never per feed or per open (path) question; an answers pass reuses
   the first pass. Nothing to batch there. (Layer 2 in ``generate`` is the
   stage that scales with feeds: one request per unmapped validation rule per
   feed.)
2. Every MODEL USAGE console line is paired with a ``CODEGEN-USAGE {json}``
   stderr marker — stage, provider word, calls, requests, seconds, failed,
   recovered; numbers and vocabulary only — and the harness reads them with
   ``run_errors.model_usage`` / ``usage_summary`` (STABLE), the repo's own
   runners (scripts/run_round.py, acfc_run.py) carry the summary line."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from codegen.layout.model import MockLayoutProvider
from codegen.layout.resolve import resolve_workbook
from codegen.reasoning.usage import StageUsage
from codegen.run_errors import (
    USAGE_MARKER,
    first_error_line,
    model_usage,
    usage_marker,
    usage_summary,
)

REPO = Path(__file__).resolve().parents[1]
STTM = REPO / "fixtures" / "acfc_shapes" / "sttm"
FRD = REPO / "fixtures" / "acfc_shapes" / "frd"
PROFILES = REPO / "fixtures" / "layout_profiles"


def test_one_request_covers_every_sheet_and_open_role(config, tmp_path):
    # Family E, open roles on 4 mapping sheets (one feed each)
    mock = MockLayoutProvider([PROFILES / "mock", PROFILES])
    empty = tmp_path / "empty"
    empty.mkdir()
    doc, workbook = resolve_workbook(STTM / "pair_10_family_e.xlsx", config, provider=mock,
                                     cache_dirs=[empty], runtime_cache_dir=tmp_path / "rt")
    (request,) = mock.requests
    assert len({u["sheet"] for u in request["unresolved"]}) == 4
    assert len(request["header_regions"]) == len(workbook.sheetnames)
    assert doc.provider_calls == 1 and doc.complete


def test_the_marker_carries_numbers_and_vocabulary_only():
    usage = StageUsage(stage="layer2", provider="databricks_fmapi", model="m", endpoint="e",
                       calls=4, requests=3, seconds=95.04, failed=1, recovered=1)
    line = usage_marker(usage)
    assert line.startswith(USAGE_MARKER)
    assert json.loads(line[len(USAGE_MARKER):]) == {
        "stage": "layer2", "provider": "databricks_fmapi", "calls": 4, "requests": 3,
        "seconds": 95.0, "failed": 1, "recovered": 1}


def test_the_reader_validates_and_the_summary_sums_per_stage():
    stderr = "\n".join([
        usage_marker({"stage": "layout", "provider": "databricks_fmapi", "calls": 2,
                      "requests": 2, "seconds": 41.3}),
        *(usage_marker({"stage": "layer2", "provider": "databricks_fmapi", "calls": 4,
                        "requests": 4, "seconds": 96.0}) for _ in range(5)),
        USAGE_MARKER + '{"stage": "layer2", "provider": "<client text>", "calls": "x"}',
        USAGE_MARKER + '{"stage": "anything"}',
        USAGE_MARKER + "not json"])
    entries = model_usage(stderr, "")
    assert len(entries) == 7
    assert entries[-1] == {"stage": "layer2", "provider": "none", "calls": 0, "requests": 0,
                           "failed": 0, "recovered": 0, "seconds": 0.0}
    assert usage_summary(entries) == (
        "layout: 2 call(s) in 41.3s (databricks_fmapi); "
        "layer2: 20 call(s) in 480.0s (databricks_fmapi, none) over 6 feed(s)")
    assert usage_summary([]) == "no model call"


def test_the_layout_command_prints_the_marker(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1",
           "CODEGEN_SKIP_ENV_OVERLAY": "1", "CODEGEN_PROVIDER": "mock"}
    done = subprocess.run(
        [sys.executable, "-m", "codegen.cli", "layout", "--workbook",
         str(STTM / "pair_1_family_a.xlsx"), "--frd", str(FRD / "f1_pair_1.docx"),
         "--no-cache", "--config", str(REPO / "config" / "config.yaml")],
        capture_output=True, text=True, encoding="utf-8", check=False, env=env, cwd=tmp_path)
    assert any(ln.startswith("MODEL USAGE     layout: ") for ln in done.stdout.splitlines()), \
        done.stdout + done.stderr
    (entry,) = model_usage(done.stderr, done.stdout)
    assert entry["stage"] == "layout" and entry["provider"] == "mock"
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None


def test_a_usage_marker_is_never_the_error_line():
    from codegen.run_errors import first_error_line_full

    marker = usage_marker({"stage": "layer2", "provider": "mock"})
    assert first_error_line_full(1, marker + "\nsomething went wrong", "") == (
        "something went wrong")
