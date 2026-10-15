"""A run's error is read from its exit code first; warnings are never the error
(D1 post50: a Pydantic deprecation on stderr was reported as the run's error)."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from codegen.run_errors import first_error_line, is_warning_line, without_warnings

SRC = str(Path(__file__).resolve().parents[1] / "src")

_WARNINGS = textwrap.dedent("""
    import warnings
    from pydantic.warnings import PydanticDeprecatedSince20
    warnings.warn(PydanticDeprecatedSince20("class-based `config` is deprecated"))
    warnings.warn("a plain user warning", UserWarning)
    warnings.warn("going away", DeprecationWarning)
""")


def _run(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-W", "always", "-c", body], text=True,
                          capture_output=True, check=False, env={"PYTHONPATH": SRC,
                                                                 "SYSTEMROOT": "C:\\Windows"})


def test_warnings_then_traceback_reports_the_traceback():
    done = _run(_WARNINGS + "raise ValueError('the real failure')\n")
    assert done.returncode == 1
    assert "PydanticDeprecatedSince20" in done.stderr and "UserWarning" in done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) == \
        "Traceback (most recent call last):"


def test_only_warnings_and_exit_0_is_no_error():
    done = _run(_WARNINGS)
    assert done.returncode == 0 and "Warning" in done.stderr
    assert first_error_line(done.returncode, done.stderr, done.stdout) is None


def test_exit_code_decides_even_with_error_looking_text():
    assert first_error_line(0, "ERROR something\nTraceback (most recent call last):") is None


def test_cli_fail_label_on_stdout_after_warnings():
    stderr = ("/x/site-packages/m.py:12: PydanticDeprecatedSince211: Accessing the "
              "'model_fields' attribute on the instance is deprecated.\n"
              "  return self.model_fields\n"
              "config overlays (in order): a.yaml\n")
    stdout = "codegen 0.5.8 (src)\nFAIL           environment — x\n"
    assert first_error_line(1, stderr, stdout) == "FAIL           environment — x"


def test_no_error_opening_line_falls_back_to_the_first_real_line():
    stderr = "/x/m.py:3: UserWarning: hi\n  warnings.warn('hi')\nsomething broke\n"
    assert first_error_line(2, stderr) == "something broke"
    assert first_error_line(2, "UserWarning: only\n") == ""


def test_warning_line_shapes():
    assert is_warning_line("/a/b.py:9: DeprecationWarning: x")
    assert is_warning_line("C:\\a\\b.py:9: PydanticDeprecatedSince20: x")
    assert is_warning_line("FutureWarning: x")
    assert is_warning_line("  warnings.warn(msg, UserWarning)")
    assert not is_warning_line("Traceback (most recent call last):")
    assert not is_warning_line("ValueError: Warning: nested text")
    assert without_warnings("/a.py:1: UserWarning: w\n  src_line()\nkept\n") == ["kept"]


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


def test_the_harness_signature_takes_completed_process_fields_as_they_come():
    import inspect

    params = list(inspect.signature(first_error_line).parameters)
    assert params == ["returncode", "stderr", "stdout"]
    assert first_error_line(1, b"/a.py:1: UserWarning: w\nTraceback (most recent call last):\n",
                            None) == "Traceback (most recent call last):"
    assert first_error_line(0, None, None) is None
    assert first_error_line(returncode=1, stderr=None, stdout="ERROR x") == "ERROR x"
