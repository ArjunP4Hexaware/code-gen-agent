"""A run's error is read from its exit code first; warnings are never the error
(D1 post50: a Pydantic deprecation on stderr was reported as the run's error).

D1 post51 (post52 version note): two tiers. ``first_error_line`` is
coordinates only (what a pushed report carries); ``first_error_line_full`` is
the quoted line (``codegen-outputs/`` inside ACFC only). Exit 0 / 3 (PASS /
NEEDS_ANSWERS) has no error line in either tier."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from codegen.run_errors import (
    MARKER,
    REASONS,
    Coord,
    column_number,
    coordinate_line,
    error_marker,
    first_error_line,
    first_error_line_full,
    is_warning_line,
    located,
    sheet_number,
    without_warnings,
)

SRC = str(Path(__file__).resolve().parents[1] / "src")

_WARNINGS = textwrap.dedent("""
    import warnings
    from pydantic.warnings import PydanticDeprecatedSince20
    warnings.warn(PydanticDeprecatedSince20("class-based `config` is deprecated"))
    warnings.warn("a plain user warning", UserWarning)
    warnings.warn("going away", DeprecationWarning)
""")

# pydantic 2.8.2's protected-namespace warning, as D1 printed it for pair_07
# (a blank line INSIDE the message; the second half was reported as the error)
_PROTECTED = (
    "/x/site-packages/pydantic/_internal/_fields.py:161: UserWarning: Field "
    "\"model_confidence\" has conflict with protected namespace \"model_\".\n"
    "\n"
    "You may be able to resolve this warning by setting "
    "`model_config['protected_namespaces'] = ()`.\n"
    "  warnings.warn(\n")


def _run(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-W", "always", "-c", body], text=True,
                          capture_output=True, check=False, env={"PYTHONPATH": SRC,
                                                                 "SYSTEMROOT": "C:\\Windows"})


# ---- exit code first, per stage ------------------------------------------------

def test_warnings_then_traceback():
    done = _run(_WARNINGS + "raise ValueError('the real failure')\n")
    assert done.returncode == 1
    assert "PydanticDeprecatedSince20" in done.stderr and "UserWarning" in done.stderr
    assert first_error_line_full(done.returncode, done.stderr, done.stdout) == \
        "Traceback (most recent call last):"
    line = first_error_line(done.returncode, done.stderr, done.stdout)
    assert line == f"{'FAIL':<15} codegen \u2014 uncaught exception [ValueError]"
    assert "the real failure" not in line


def test_only_warnings_and_exit_0_is_no_error():
    done = _run(_WARNINGS)
    assert done.returncode == 0 and "Warning" in done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None
    assert first_error_line_full(done.returncode, done.stderr, done.stdout) is None


@pytest.mark.parametrize("code", [0, 3])
def test_pass_and_needs_answers_stages_have_no_error_line(code):
    """D1 post51 pair_07: a NEEDS_ANSWERS stage (exit 3) got a warning as its
    error line. A stage that is PASS or NEEDS_ANSWERS never has one."""
    stderr = _PROTECTED + "ERROR something\nTraceback (most recent call last):\n"
    assert first_error_line(code, stderr, "FAIL x") is None
    assert first_error_line_full(code, stderr, "FAIL x") is None


def test_cli_fail_label_on_stdout_after_warnings():
    stderr = ("/x/site-packages/m.py:12: PydanticDeprecatedSince211: Accessing the "
              "'model_fields' attribute on the instance is deprecated.\n"
              "  return self.model_fields\n"
              "config overlays (in order): a.yaml\n")
    stdout = "codegen 0.5.8 (src)\nFAIL           environment — x\n"
    assert first_error_line_full(1, stderr, stdout) == "FAIL           environment — x"
    # no marker: the coordinates tier says so and quotes nothing
    assert first_error_line(1, stderr, stdout) == \
        f"{'FAIL':<15} codegen \u2014 error (unclassified)"


def test_no_error_opening_line_falls_back_to_the_first_real_line():
    stderr = "/x/m.py:3: UserWarning: hi\n  warnings.warn('hi')\nsomething broke\n"
    assert first_error_line_full(2, stderr) == "something broke"
    assert first_error_line_full(2, "UserWarning: only\n") == ""
    assert "broke" not in first_error_line(2, stderr)


# ---- the whole warning block is one unit ----------------------------------------

def test_the_protected_namespace_block_is_skipped_whole():
    stdout = "NOTE           run.environment — environment: D1\n"
    assert without_warnings(_PROTECTED) == []
    assert first_error_line_full(1, _PROTECTED + "something broke\n", stdout) == \
        "something broke"
    # a block ends early (exclusive) at the next traceback / CLI / log line
    no_source = _PROTECTED.replace("  warnings.warn(\n", "")
    assert without_warnings(no_source + "Traceback (most recent call last):\n") == \
        ["Traceback (most recent call last):"]
    assert without_warnings(no_source + "QUESTION       feeds[0].x — y\n") == \
        ["QUESTION       feeds[0].x — y"]
    assert without_warnings(no_source + "2026-10-15 06:58:41 INFO started\n") == \
        ["2026-10-15 06:58:41 INFO started"]
    assert without_warnings(no_source + "config overlays (in order): a.yaml\n") == \
        ["config overlays (in order): a.yaml"]


def test_warning_line_shapes():
    assert is_warning_line("/a/b.py:9: DeprecationWarning: x")
    assert is_warning_line("C:\\a\\b.py:9: PydanticDeprecatedSince20: x")
    assert is_warning_line("FutureWarning: x")
    assert is_warning_line("  warnings.warn(msg, UserWarning)")
    assert not is_warning_line("Traceback (most recent call last):")
    assert not is_warning_line("ValueError: Warning: nested text")
    assert without_warnings("/a.py:1: UserWarning: w\n  src_line()\nkept\n") == ["kept"]


# ---- coordinates ---------------------------------------------------------------

def test_coord_reads_as_positions_and_holds_no_text():
    assert str(Coord("STTM", sheet=2, row=4, col=7)) == "STTM sheet 2 row 4 col 7"
    assert str(Coord("FRD", table=3, row=2)) == "FRD table 3 row 2"
    assert str(Coord("file", n=1, of=3)) == "file 1 of 3"
    with pytest.raises(ValueError):
        Coord("a sheet name")
    with pytest.raises(ValueError):
        Coord("STTM", row="4")              # type: ignore[arg-type]
    assert column_number("G") == 7 and column_number("AA") == 27 and column_number("x1") is None
    assert sheet_number(["A", "B", "C"], "C") == 3 and sheet_number(["A"], "Z") is None


def test_coord_in_sheet_uses_the_sheet_index():
    from openpyxl import Workbook

    wb = Workbook()
    wb.active.title = "SENTINEL_TERM_A"
    ws = wb.create_sheet("SENTINEL_TERM_B")
    assert str(Coord.in_sheet("STTM", ws, row=4, col="G")) == "STTM sheet 2 row 4 col 7"


def test_the_marker_is_rebuilt_from_vocabulary_only():
    exc = located(ValueError("cell 'SENTINEL_TERM' is bad"), Coord("STTM", sheet=1, row=2),
                  "sttm.value")
    marker = error_marker("extract-sttm", "unclassified", Coord("STTM"), exc=exc,
                          checks=["derivations", "SENTINEL TERM"])
    assert marker.startswith(MARKER) and "SENTINEL" not in marker
    line = first_error_line(1, marker + "\n", "FAIL x — cell 'SENTINEL_TERM'")
    assert line == (f"{'FAIL':<15} extract-sttm \u2014 STTM cell value invalid at STTM sheet 1 "
                    "row 2 (failed checks: derivations) [ValueError]")
    # a hand-made marker with text in its fields: every bad field is dropped
    forged = MARKER + json.dumps({"stage": "SENTINEL_TERM", "reason": "SENTINEL_TERM",
                                  "coord": {"doc": "SENTINEL_TERM"}, "exception": "SENTINEL_TERM",
                                  "checks": "SENTINEL_TERM"})
    assert first_error_line(1, forged) == f"{'FAIL':<15} codegen \u2014 error (unclassified)"
    assert first_error_line(1, MARKER + "{not json SENTINEL_TERM") == \
        f"{'FAIL':<15} codegen \u2014 error (unclassified)"
    # the harness's phrases survive (docs/acfc/HARNESS_EXIT_CODES.md)
    assert "contract not found:" in coordinate_line({"reason": "contract.not_found"})
    assert "under gaps:" in REASONS["answers.missing"]
    assert "no resolved feed matches --feed" in REASONS["feed.no_match"]


def test_every_located_call_in_src_names_a_registered_reason():
    """A located(...) reason literal outside REASONS would silently read
    'unclassified' — the audit's codes are checked here."""
    import re

    src = Path(SRC) / "codegen"
    used = set()
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        used |= set(re.findall(r"located\((?:.|\n)*?,\s*\"([a-z_.]+)\"\)", text))
    assert used, "no located(...) call found"
    assert used <= set(REASONS), sorted(used - set(REASONS))


# ---- signature + the import-time filter ------------------------------------------

def test_silence_at_source_stops_the_pydantic_noise():
    done = _run("from codegen.run_errors import silence_pydantic_deprecations\n"
                "silence_pydantic_deprecations()\n" + _WARNINGS)
    assert done.returncode == 0
    assert "Pydantic" not in done.stderr
    assert "UserWarning" in done.stderr          # scoped: other categories still print


def test_cli_entry_installs_the_filter(monkeypatch):
    import warnings

    from pydantic.warnings import PydanticDeprecatedSince20

    from codegen import cli

    monkeypatch.setattr(cli, "_main", lambda argv: 0)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        assert cli.main([]) == 0
        warnings.warn(PydanticDeprecatedSince20("noise"), stacklevel=2)
    assert not [w for w in seen if issubclass(w.category, PydanticDeprecatedSince20)]


def test_importing_codegen_prints_no_warning_at_all():
    """D1 runs pydantic 2.8.2: a ``model_*`` field (protected namespace) or a
    BaseModel-attribute name warns there on import (tests/test_d1_environment
    runs this suite under the D1 pins too)."""
    done = _run("import codegen.config, codegen.cli, codegen.layout.resolve\n")
    assert done.returncode == 0, done.stderr
    assert "Warning" not in done.stderr, done.stderr


def test_the_harness_signature_takes_completed_process_fields_as_they_come():
    import inspect

    for reader in (first_error_line, first_error_line_full):
        assert list(inspect.signature(reader).parameters) == ["returncode", "stderr", "stdout"]
    assert first_error_line_full(1, b"/a.py:1: UserWarning: w\nTraceback (most recent call "
                                 b"last):\n", None) == "Traceback (most recent call last):"
    assert first_error_line(0, None, None) is None
    assert first_error_line_full(returncode=1, stderr=None, stdout="ERROR x") == "ERROR x"
    assert first_error_line(returncode=1, stderr=None, stdout="ERROR x") == \
        f"{'FAIL':<15} codegen \u2014 error (unclassified)"
