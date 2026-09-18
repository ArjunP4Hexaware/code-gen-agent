"""Materialize fixtures/layout_profiles/ (M2.5 §5): the correct layout
profile of every M0 STTM and FRD fixture — the repo cache and the mock
provider's answers, keyed by the ``fingerprint`` inside each file — plus
the adversarial mock set under mock/.

    python scripts/build_layout_profiles.py

Curated truth lives in tests/acfc_shapes/layout_truth.py; the suite asserts
the tracked files equal a fresh build.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "src"))

from acfc_shapes.layout_truth import (  # noqa: E402
    ADVERSARIAL,
    CANARY,
    FRD_FIXTURES,
    STTM_CURATED,
    VDD_ADVERSARIAL,
    VDD_CURATED,
)
from codegen.config import load_config  # noqa: E402
from codegen.extract.frd_docx import discover_frd, read_docx  # noqa: E402
from codegen.layout.discover import discover, discover_vdd  # noqa: E402
from codegen.layout.profile import LayoutProfile  # noqa: E402
from codegen.layout.resolve import _merge_columns  # noqa: E402

FIXTURES = REPO / "fixtures" / "acfc_shapes"
OUT = REPO / "fixtures" / "layout_profiles"
MOCK = OUT / "mock"


def _dump(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def sttm_truth(name: str, config) -> LayoutProfile:
    found = discover(FIXTURES / "sttm" / name, config.extractor)
    profile = _merge_columns(found.profile, STTM_CURATED[name], "cache", 1.0)
    profile = profile.model_copy(update={"source": "cache", "notes": [], "role_sources": {}})
    assert not profile.unresolved, (name, [u.role for u in profile.unresolved])
    return profile


def vdd_truth(name: str, config) -> LayoutProfile:
    found = discover_vdd(FIXTURES / "vdd" / name, config.extractor)
    profile = _merge_columns(found.profile, VDD_CURATED[name], "cache", 1.0)
    profile = profile.model_copy(update={"source": "cache", "notes": [], "role_sources": {}})
    assert not profile.unresolved, (name, [u.role for u in profile.unresolved])
    return profile


def vdd_adversarial(base: LayoutProfile, mutation: str) -> dict:
    payload = base.model_dump(mode="json")
    fields = next(s for s in payload["sheets"] if s["kind"] == "vdd_fields")
    band = fields["bands"][0]
    if mutation == "canary":
        payload["notes"] = [CANARY]
        band["roles"][CANARY] = 2
        payload["source"] = "model"
    elif mutation == "free_text":
        band["roles"]["length"] = 11           # the Description column
    return payload


def frd_truth(name: str, config) -> dict:
    profile = discover_frd(read_docx(FIXTURES / "frd" / name), config.extractor.frd)
    assert not profile.unresolved, (name, profile.unresolved)
    return profile.model_copy(update={"source": "cache", "notes": []}).model_dump(mode="json")


def adversarial(base: LayoutProfile, mutation: str) -> dict:
    payload = base.model_dump(mode="json")
    sheet = next(s for s in payload["sheets"] if s["kind"] == "mapping")
    stage = next(b for b in sheet["bands"] if b["layer"] == "stage")
    standard = next(b for b in sheet["bands"] if b["layer"] == "standard")
    source = next(b for b in sheet["bands"] if b["layer"] == "source")
    if mutation == "header_row":
        sheet["header_row"] = sheet["header_row"] + 4        # a data row
        sheet["band_row"] = None
    elif mutation == "swap_spans":
        stage["col_start"], standard["col_start"] = standard["col_start"], stage["col_start"]
        stage["col_end"], standard["col_end"] = standard["col_end"], stage["col_end"]
        stage["label"] = standard["label"] = None
    elif mutation == "data_column":
        stage["roles"]["table"] = 30                          # beyond every header
    elif mutation == "phantom_sheet":
        payload["sheets"].append({**json.loads(json.dumps(sheet)), "name": "PHANTOM_SHEET"})
    elif mutation == "free_text":
        source["roles"]["length"] = 9                         # the Description column
    elif mutation == "canary":
        payload["notes"] = [CANARY]
        stage["roles"][CANARY] = 18
        payload["source"] = "model"
    return payload


def build_all() -> dict[str, str]:
    config = load_config(REPO / "config" / "config.yaml")
    out: dict[str, str] = {}
    truths: dict[str, LayoutProfile] = {}
    for name in STTM_CURATED:
        profile = sttm_truth(name, config)
        truths[name] = profile
        out[f"sttm_{Path(name).stem}.layout.json"] = _dump(profile.model_dump(mode="json"))
    for name in FRD_FIXTURES:
        out[f"frd_{Path(name).stem}.layout.json"] = _dump(frd_truth(name, config))
    pair1 = truths["pair_1_family_a.xlsx"]
    for file_name, spec in ADVERSARIAL.items():
        out[f"mock/{file_name}"] = _dump(adversarial(pair1, spec["mutation"]))
    vdd_truths = {name: vdd_truth(name, config) for name in VDD_CURATED}
    for name, profile in vdd_truths.items():
        out[f"vdd_{Path(name).stem}.layout.json"] = _dump(profile.model_dump(mode="json"))
    for file_name, spec in VDD_ADVERSARIAL.items():
        out[f"mock/{file_name}"] = _dump(
            vdd_adversarial(vdd_truths["pair_1_v1_segments.xlsx"], spec["mutation"]))
    return out


def materialize() -> list[Path]:
    written = []
    for rel, text in build_all().items():
        path = OUT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in materialize():
        print(path.relative_to(REPO).as_posix())
