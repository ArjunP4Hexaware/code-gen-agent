"""post150: config VALUES reach client-facing text - flags, the IIG's cell notes,
the LOG, the App's dialogs - so none may name a person. Who decided something
lives in a YAML comment, never in a value."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PEOPLE = re.compile(r"\b(Venu|Aruna|Soham|Jinesh|Suganya|Rama|Nikshit|Arjun|Saswata)\b")


def _strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def test_no_config_value_names_a_person():
    overlays = sorted((REPO / "config" / "overlays").glob("*.yaml"))
    files = [REPO / "config" / "config.yaml", *overlays]
    named = [f"{f.name}{path}" for f in files
             for path, text in _strings(yaml.safe_load(f.read_text(encoding="utf-8")))
             if PEOPLE.search(text)]
    assert named == []
