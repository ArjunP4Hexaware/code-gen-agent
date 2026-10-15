"""The ACFC D1 pin set (docs/acfc/ENVIRONMENT_ACFC.md, constraints/acfc_d1.txt)
and the import-time warnings only those pins show (D1 post51: pydantic 2.8.2
warned on a ``model_*`` field — pair_07's reported error — which pydantic
>= 2.10 never does, so home never saw it)."""

from __future__ import annotations

import importlib
import pkgutil
import re
from pathlib import Path

from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "acfc" / "ENVIRONMENT_ACFC.md"
PINS = REPO / "constraints" / "acfc_d1.txt"


def _pins() -> dict[str, str]:
    out = {}
    for line in PINS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            name, version = line.split("==")
            out[name.strip().lower()] = version.strip()
    return out


def test_the_doc_table_and_the_constraints_file_agree():
    table = dict(re.findall(r"^\| ([a-z][\w-]*) \| (\d[\w.]*) \|$",
                            DOC.read_text(encoding="utf-8").replace("\r\n", "\n"), re.M))
    assert table == _pins()
    assert {"pydantic", "openpyxl", "jinja2", "pyyaml", "databricks-sdk"} <= set(table)
    assert table["pydantic"] == "2.8.2"


def _models():
    seen = set()
    for package in ("codegen", "ui.backend"):
        try:
            root = importlib.import_module(package)
        except ImportError:          # ui extra absent (the D1 venv): codegen only
            continue
        for info in pkgutil.walk_packages(root.__path__, package + "."):
            try:
                module = importlib.import_module(info.name)
            except Exception:        # noqa: BLE001 — optional extras (databricks, ui)
                continue
            for obj in vars(module).values():
                if (isinstance(obj, type) and issubclass(obj, BaseModel)
                        and obj.__module__ == module.__name__ and obj not in seen):
                    seen.add(obj)
                    yield obj


def test_no_model_field_sits_in_pydantics_protected_namespace():
    """At ANY pydantic version: a field named ``model_*`` needs
    ``protected_namespaces=()`` on its model (pydantic < 2.10 warns otherwise)."""
    offenders = [f"{m.__module__}.{m.__name__}.{name}" for m in _models()
                 for name in m.model_fields
                 if name.startswith("model_") and m.model_config.get("protected_namespaces") != ()]
    assert not offenders, offenders


def test_the_layout_confidence_keeps_its_yaml_key():
    from codegen.config import LayoutConfig

    assert LayoutConfig.model_validate({"model_confidence": 0.6}).placed_confidence == 0.6
    assert LayoutConfig(placed_confidence=0.7).placed_confidence == 0.7
    assert LayoutConfig.model_config.get("protected_namespaces") == ()
