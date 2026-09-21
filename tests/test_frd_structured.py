"""M7 §2 — the F1 reader on the one-block / many-files shape (fixture pair
11): nested tables, per-file blocks, label-prefixed values, pointer text and
the single-line rule leave the field UNSTATED and recorded (StructuredValue);
the layout stage then gives every derived feed its own row / block by file
name, takes the frequency from the STTM File Details row with provenance,
and the vendor label — never the description — names the source."""

from __future__ import annotations

from pathlib import Path

from acfc_shapes import frd as frd_fixtures
from codegen.extract.frd_docx import extract_frd_contract
from codegen.layout.model import MockLayoutProvider
from codegen.layout.resolve import _match_rows_to_feeds, resolve_pair
from test_frd_gapfill import load_config_for_tests

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "fixtures" / "acfc_shapes"
FRD = SHAPES / "frd" / "f1_pair_11_multi_file.docx"
FRD_CATALOG = SHAPES / "frd" / "f1_pair_11_multi_file_catalog.docx"
STTM = SHAPES / "sttm" / "pair_11_family_b.xlsx"
DATE = "2026-01-01"

_SINGLE_LINE = ("feed_name", "source_system", "frequency", "file_format", "landing_location",
                "domain", "sub_domain")


def _resolve(frd_path: Path):
    config = load_config_for_tests()
    return resolve_pair(STTM, frd_path, config, provider=MockLayoutProvider([]), cache_dirs=[],
                        use_cache=False, generated_date=DATE)


def test_reader_refuses_every_shape_and_records_it():
    config = load_config_for_tests()
    contract, profile = extract_frd_contract(FRD, config, generated_date=DATE)
    (feed,) = contract.feeds
    kinds = {k.split(".", 1)[1]: v.kind for k, v in contract.structured.items()}
    assert kinds == {
        "feed_name": "nested_table",             # the Object Name cell is a 5-column table
        "source_system": "label_prefixed",       # "Vendor Files = <description>"
        "frequency": "pointer",                  # "Please refer to the File Details tab …"
        "domain": "per_file_blocks",             # "<File> file Ingestion from VC:" blocks
        "landing_location": "nested_table",      # object | path
        "stage_target.schema": "multiline",      # two schema lines, no catalog
    }
    # Unstated in the feed — and NOT filled from the section's "Name" row.
    assert feed.frequency is None and feed.domain is None and feed.landing_location is None
    assert "unnamed" in feed.feed_name and "Descriptive" not in feed.feed_name
    # The vendor label names the source; the description never does.
    assert feed.source_system == frd_fixtures.PAIR11_VENDOR
    pointer = contract.structured["feeds[0].frequency"]
    assert pointer.target == "the File Details tab of the mapping document"
    prefixed = contract.structured["feeds[0].source_system"]
    assert prefixed.prefix_label == "Vendor Files"
    location = contract.structured["feeds[0].landing_location"]
    assert location.headers == ["File_Name", "mftlanding path"]
    assert [r.key for r in location.rows] == frd_fixtures.PAIR11_OBJECTS
    objects = contract.structured["feeds[0].feed_name"]
    assert [r.key for r in objects.rows] == frd_fixtures.PAIR11_FILES   # keyed on the file cell
    assert "FileName_2" in objects.rows[0].values                        # duplicate header kept
    blocks = contract.structured["feeds[0].domain"]
    assert blocks.rows[2].values == {"domain": "Domain Beta", "sub_domain": "Domain Alpha"}
    # Logged text is truncated, never a value anywhere in the feed.
    assert all(len(v.text) <= config.extractor.frd.structured_text_max_chars + 1
               for v in contract.structured.values())
    # "Inbound" (a direction word) did not become the landing path.
    assert any("names no path" in a for a in contract.provenance.ambiguities)
    # Pair 1 refuses exactly one cell (M9.3): its Object Name lists the files.
    pair1, _ = extract_frd_contract(SHAPES / "frd" / "f1_pair_1.docx", config, generated_date=DATE)
    assert {k: v.kind for k, v in pair1.structured.items()} == {
        "feeds[0].feed_name": "labelled_files"}
    # … and pair 2 (plain cells throughout) none at all.
    pair2, _ = extract_frd_contract(SHAPES / "frd" / "f1_pair_2_variant.docx", config,
                                    generated_date=DATE)
    assert pair2.structured == {}


def test_three_feeds_derive_each_with_its_own_values_and_provenance():
    pair = _resolve(FRD)
    assert pair.questions == []
    feeds = pair.frd_contract.feeds
    assert [f.feed_name for f in feeds] == ["vc_enrollment", "vc_disenrollment",
                                            "vc_individual_risk"]
    for feed, file, path, (domain, sub) in zip(feeds, frd_fixtures.PAIR11_FILES,
                                               frd_fixtures.PAIR11_PATHS,
                                               frd_fixtures.PAIR11_DOMAINS, strict=True):
        assert feed.file_name_patterns == [file]
        assert feed.landing_location == path.replace("\\\\", "\\")
        assert (feed.domain, feed.sub_domain) == (domain, sub)
        assert feed.source_system == frd_fixtures.PAIR11_VENDOR
        for name in _SINGLE_LINE:
            value = getattr(feed, name)
            assert value is None or "\n" not in value, (feed.feed_name, name)
    # Frequency from the STTM File Details row of THIS feed's file, cited.
    assert [f.frequency for f in feeds] == ["Yearly Twice", "Yearly Twice", "Monthly"]
    freq_flags = sorted(f for f in pair.flags if f.startswith("frd_unstated:feeds[")
                        and ".frequency source_used:STTM FILE_DETAILS!E" in f)
    assert len(freq_flags) == 3 and "FILE_DETAILS!E4: 'Monthly'" in freq_flags[2]
    assert any(f.startswith("frd_pointer:feeds[0].frequency → the File Details tab")
               for f in pair.flags)
    # Per-feed nested values cite the FRD cell and the row / block they came from.
    assert any(f.startswith("frd_nested:feeds[2].landing_location source_used:FRD table")
               and "row 'Individual Risk'" in f for f in pair.flags)
    assert any(f.startswith("frd_nested:feeds[2].domain source_used:FRD table")
               and "domain='Domain Beta'" in f for f in pair.flags)
    assert any(f.startswith("frd_label_prefixed:feeds[0].source_system") for f in pair.flags)
    # Schemas: the STTM bands (two schemas across the three sheets), flagged.
    assert [f.stage_target.schema_name for f in feeds] == ["stg_dom_a", "stg_dom_a", "stg_dom_b"]
    assert [f.standard_target.schema_name for f in feeds] == ["dom_a", "dom_a", "dom_b"]
    assert all(f.stage_target.catalog is None for f in feeds)   # no catalog anywhere
    # The "Taken from other documents" list carries the three frequencies.
    assert [(x["field"], x["value"]) for x in pair.gap_fills] == [
        ("feeds[0].frequency", "Yearly Twice"), ("feeds[1].frequency", "Yearly Twice"),
        ("feeds[2].frequency", "Monthly")]


def test_catalog_variant_carries_the_catalog_into_every_derived_feed():
    pair = _resolve(FRD_CATALOG)
    feeds = pair.frd_contract.feeds
    assert [f.stage_target.catalog for f in feeds] == ["cat_syn"] * 3
    assert [f.standard_target.catalog for f in feeds] == ["cat_syn"] * 3
    # The one sheet whose schema differs from the FRD block's is overridden, flagged.
    assert feeds[2].stage_target.schema_name == "stg_dom_b"
    assert any(f.startswith("frd_unstated:feeds[2].stage_target.schema source_used:STTM stage")
               for f in pair.flags)
    assert not any("feeds[0].stage_target.schema" in f for f in pair.flags)


def test_row_matching_is_mutual_best_by_elimination():
    """Two block headings share a token: the one with a second matching
    token pairs first, the other pairs once it is gone; a heading that
    names no feed pairs nothing."""
    from types import SimpleNamespace

    def feed(table, *files):
        return SimpleNamespace(file_name_patterns=list(files),
                               stage_target=SimpleNamespace(tables=[table]))

    feeds = [feed("vc_community_demographic_risk", "demographics_package_YYYY_MM.csv"),
             feed("vc_community_risk"),
             feed("vc_individual_risk", "vc_ind_risk_data_package_YYYYMMDD.psv")]
    keys = ["Community Demographics file Ingestion from VC",
            "Community Risk file Ingestion from VC",
            "Individual Risk file Ingestion from VC"]
    assert _match_rows_to_feeds(keys, feeds) == {0: 0, 1: 1, 2: 2}
    assert _match_rows_to_feeds(["Some other heading"], feeds) == {}
    # An exact file name wins outright.
    assert _match_rows_to_feeds(["vc_ind_risk_data_package_YYYYMMDD.psv"], feeds) == {2: 0}
