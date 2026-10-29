"""post146: a feed's own steps carry which feed of how many - what the
Generate page's progress bar splits its generation band by. Other steps keep
their three keys."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from ui.backend.demo import DemoRunner  # noqa: E402


def test_a_feed_step_says_which_feed_of_how_many():
    runner = SimpleNamespace(stages=[])
    DemoRunner._stage(runner, "feed_a: rendering", feed={"n": 1, "of": 2})
    DemoRunner._stage(runner, "storing outputs", "3 file(s)")
    first, second = runner.stages
    assert first["feed"] == {"n": 1, "of": 2}
    assert set(second) == {"stage", "detail", "at"}
