"""P1-2 (red team LM-2, 2026-10-30): a cached layout profile is not a bypass
of the validator.

The fingerprint hashes the header region, not the data: workbook B with A's
headers and text in a column the model claimed as an integer role was served
A's placement as ``source=cache``, unchecked. Now every hit re-validates the
roles the model or a person placed against the CURRENT workbook (header +
plausibility, the checks a fresh claim meets); any rejection makes the entry
stale and the document is re-resolved. The entry keeps each role's real
provenance (never flattened to ``cache``), so a later hit knows what to check,
and ``layout.cache_model_placements: false`` keeps unanswered model placements
out of the cache altogether.
"""

from __future__ import annotations

import json

from codegen.layout.resolve import resolve_frd, resolve_pair, resolve_workbook, vocabulary_hash
from layout_attack import (
    F1_FRD,
    PAIR4_SHEET,
    SOURCE_LEN,
    STAGE_SCHEMA,
    StubProvider,
    pair4_copy,
    place_sttm,
    with_layout,
)

# A: the stage Schema and the source Len headers renamed (the synonyms leave
# the schema open, and the length unplaced); the model places both.
HEADERS = {STAGE_SCHEMA: "Zone", SOURCE_LEN: "Wd"}
PLACED = {"stage": {"schema": STAGE_SCHEMA}, "source": {"length": SOURCE_LEN}}
LENGTH = f"{PAIR4_SHEET}/source/length"
SCHEMA = f"{PAIR4_SHEET}/stage/schema"


def _empty(tmp_path):
    empty = tmp_path / "empty_cache"
    empty.mkdir(exist_ok=True)
    return [empty]


def _a_then_b(tmp_path, config):
    a = pair4_copy(tmp_path / "a.xlsx", headers=HEADERS)
    b = pair4_copy(tmp_path / "b.xlsx", headers=HEADERS,
                   column_values={SOURCE_LEN: "x'); DROP TABLE t; --"})
    runtime = tmp_path / "runtime"
    first, _ = resolve_workbook(a, config, provider=StubProvider(place_sttm(PAIR4_SHEET, PLACED)),
                                cache_dirs=_empty(tmp_path), runtime_cache_dir=runtime)
    return a, b, runtime, first


def test_a_cached_model_placement_is_revalidated_against_the_current_workbook(config, tmp_path):
    a, b, runtime, first = _a_then_b(tmp_path, config)
    assert first.complete and first.profile.role_sources[LENGTH] == "model"
    assert first.fingerprint == resolve_workbook(b, config, cache_dirs=_empty(tmp_path),
                                                 use_cache=False)[0].fingerprint
    served, _ = resolve_workbook(b, config, provider=None, cache_dirs=_empty(tmp_path),
                                 runtime_cache_dir=runtime)
    # B's length column is text: A's integer-role placement is not served for it
    assert not served.cache_hit
    assert "length" not in served.profile.sheet(PAIR4_SHEET).band("source").roles
    (stale,) = [r for r in served.rejections if r.reason.startswith("cached profile:")]
    assert "length" in stale.reason and "DROP" not in stale.reason     # coordinates only
    # A itself is still served from the cache - its own data validates
    again, _ = resolve_workbook(a, config, provider=None, cache_dirs=_empty(tmp_path),
                                runtime_cache_dir=runtime)
    assert again.cache_hit and again.profile.source == "cache"


def test_the_entry_keeps_each_roles_real_provenance_across_hits(config, tmp_path):
    a, _b, runtime, first = _a_then_b(tmp_path, config)
    path = runtime / f"{first.fingerprint}.json"
    stored = json.loads(path.read_text(encoding="utf-8"))["role_sources"]
    assert stored[SCHEMA] == stored[LENGTH] == "model"
    hit, _ = resolve_workbook(a, config, provider=None, cache_dirs=_empty(tmp_path),
                              runtime_cache_dir=runtime,
                              answers={f"{PAIR4_SHEET}/stage/table": 17})
    # a model placement stays "model" through a hit (what the extractor flags);
    # every other role reads "cache" as before, and the resolution knows who placed it
    assert hit.cache_hit and hit.profile.role_sources[LENGTH] == "model"
    assert hit.profile.role_sources[f"{PAIR4_SHEET}/source/field_name"] == "cache"
    assert hit.placed(f"{PAIR4_SHEET}/source/field_name") == "synonyms"
    assert hit.placed(LENGTH) == "model" and hit.placed(f"{PAIR4_SHEET}/stage/table") == "user"
    rewritten = json.loads(path.read_text(encoding="utf-8"))["role_sources"]
    assert "cache" not in rewritten.values()
    assert rewritten[LENGTH] == "model" and rewritten[f"{PAIR4_SHEET}/source/field_name"] == \
        "synonyms"


def test_cache_model_placements_false_keeps_them_out_of_the_cache(config, tmp_path):
    off = with_layout(config, cache_model_placements=False)
    a = pair4_copy(tmp_path / "a.xlsx", headers=HEADERS)
    runtime = tmp_path / "runtime"
    first, _ = resolve_workbook(a, off, provider=StubProvider(place_sttm(PAIR4_SHEET, PLACED)),
                                cache_dirs=_empty(tmp_path), runtime_cache_dir=runtime)
    assert first.complete and not (runtime / f"{first.fingerprint}.json").exists()
    # a person's answer for the role is a confirmation: then it is cached
    answered, _ = resolve_workbook(a, off, provider=None, cache_dirs=_empty(tmp_path),
                                   runtime_cache_dir=runtime,
                                   answers={SCHEMA: STAGE_SCHEMA})
    assert answered.complete and (runtime / f"{answered.fingerprint}.json").exists()


def test_a_cached_frd_model_placement_is_revalidated(config, tmp_path):
    """A runtime FRD entry whose model-placed field no longer reads as its
    label is stale, not served (the cached branch re-runs ``_validate_frd``)."""
    first, _ = resolve_frd(F1_FRD, config, cache_dirs=_empty(tmp_path), use_cache=False)
    entry = first.profile.model_dump(mode="json")
    entry["fields"]["feeds[0].frequency"]["row"] = 9          # a row of another label
    entry["field_sources"]["feeds[0].frequency"] = "model"
    entry["vocabulary"] = vocabulary_hash(config)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / f"{first.fingerprint}.json").write_text(json.dumps(entry), encoding="utf-8")
    served, _ = resolve_frd(F1_FRD, config, cache_dirs=_empty(tmp_path),
                            runtime_cache_dir=runtime)
    assert not served.cache_hit
    assert served.profile.fields["feeds[0].frequency"].row == 7     # the synonyms' row
    assert any(r.reason.startswith("cached profile:") for r in served.rejections)


def test_a_pair_cache_hit_revalidates_its_sttm_placements(config, tmp_path):
    a, b, runtime, _first = _a_then_b(tmp_path, config)
    stub = StubProvider(place_sttm(PAIR4_SHEET, PLACED))
    _pair, = [resolve_pair(a, F1_FRD, config, provider=stub, cache_dirs=_empty(tmp_path),
                          runtime_cache_dir=runtime, use_cache=False,
                          generated_date="2026-01-01")]
    assert list(runtime.glob("pair_*.json"))
    b_pair = resolve_pair(b, F1_FRD, config, provider=None, cache_dirs=_empty(tmp_path),
                          runtime_cache_dir=runtime, generated_date="2026-01-01")
    assert not b_pair.pair_cache_hit and not b_pair.sttm.cache_hit
    assert "length" not in b_pair.sttm.profile.sheet(PAIR4_SHEET).band("source").roles
