"""Shared fixtures: the real config and both resolved contract pairs.

These tests exercise the GENERATOR (no Spark). Generated-code tests live in
``out/<feed>/tests`` and run under the gate.

2026-08-22: the contract/workbook/replay fixtures were removed from the repo
(no client documents, raw or derived, in the repository). Everything that
needs them SKIPS when they are absent instead of failing -- see
``require_fixture_files`` / ``_pair_paths`` below. Restore anonymized fixtures
at the configured paths and the full suite runs again unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codegen.config import load_config
from codegen.resolve.resolver import resolve_pair
from codegen.resolve.resolver import resolve_pair as resolve_contracts

REPO = Path(__file__).resolve().parents[1]

# Importing ui.backend.main (test_demo_ui and friends) runs load_dotenv as an
# import side effect, which can put the OPERATOR'S machine-local env overrides
# (e.g. CODEGEN_NOTIFICATION_EMAILS — a client value) into this process. The
# suite must run against the tracked config's synthetic values only, so the
# override is stripped before every test.
# Databricks runtime markers flip the Layer-2 transport to the Foundation
# Model endpoint (codegen.reasoning.transport); a developer shell that carries
# DATABRICKS_HOST must not change what the suite asserts.
_MACHINE_LOCAL_ENV = ("CODEGEN_NOTIFICATION_EMAILS", "DATABRICKS_HOST", "DATABRICKS_APP_PORT",
                      "DATABRICKS_APP_NAME", "DATABRICKS_RUNTIME_VERSION")


@pytest.fixture(autouse=True, scope="session")
def _strip_machine_local_env():
    # Session-scoped + autouse: runs after collection (when ui.backend.main's
    # import-time load_dotenv may have fired) and before any other session
    # fixture builds a Config.
    for name in _MACHINE_LOCAL_ENV:
        os.environ.pop(name, None)
    yield


# --------------------------------------------------------------------------- #
# Socket guard (M10). The suite is offline BY CONSTRUCTION, not by luck: any
# outbound connection attempt fails the test that made it. This box resolves
# Databricks auth from a CLI profile with no env secret, so an unpinned live
# path (the FMAPI lesson of 2026-08-28; the M10 environment probe) would
# otherwise reach a REAL workspace — and the wrong one. Loopback stays open:
# asyncio's self-pipe on Windows and in-process servers connect to 127.0.0.1.
# --------------------------------------------------------------------------- #

_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost", ""}


class OutboundConnectionAttempted(AssertionError):
    """A test tried to open a non-loopback connection."""


def _is_loopback(address) -> bool:
    if not isinstance(address, tuple) or not address:
        return True  # AF_UNIX path / abstract socket — never leaves the box
    host = address[0]
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    return str(host) in _LOOPBACK_HOSTS or str(host).startswith("127.")


@pytest.fixture(autouse=True, scope="session")
def _no_outbound_sockets():
    import socket

    attempts: list[str] = []
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def guarded_connect(self, address):
        if not _is_loopback(address):
            attempts.append(repr(address))
            raise OutboundConnectionAttempted(
                f"the suite must never open an outbound connection; attempted {address!r}")
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        if not _is_loopback(address):
            attempts.append(repr(address))
            raise OutboundConnectionAttempted(
                f"the suite must never open an outbound connection; attempted {address!r}")
        return real_connect_ex(self, address)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    # The SDK must not find the operator's CLI profiles either: a config file
    # that does not exist resolves no profile, so nothing here can authenticate
    # against a real workspace even if a guard above were bypassed.
    previous_cfg = os.environ.get("DATABRICKS_CONFIG_FILE")
    os.environ["DATABRICKS_CONFIG_FILE"] = str(REPO / "tests" / "_no_such_databrickscfg")
    try:
        yield attempts
    finally:
        socket.socket.connect = real_connect
        socket.socket.connect_ex = real_connect_ex
        if previous_cfg is None:
            os.environ.pop("DATABRICKS_CONFIG_FILE", None)
        else:
            os.environ["DATABRICKS_CONFIG_FILE"] = previous_cfg
    # A guarded attempt swallowed by a broad `except` would otherwise pass.
    assert not attempts, f"outbound connection attempts during the suite: {attempts}"


FIXTURES_REMOVED = (
    "contract/workbook fixtures are not in the repo (removed 2026-08-22 -- no "
    "client documents in the repository); restore anonymized fixtures to run"
)


def require_fixture_files(*paths: Path) -> None:
    """Skip the calling test/fixture unless every path exists."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        pytest.skip(f"{FIXTURES_REMOVED}: missing {', '.join(p.name for p in missing)}")


@pytest.fixture(scope="session")
def config():
    return load_config(REPO / "config" / "config.yaml")


PAIR1_OVERLAY = REPO / "fixtures" / "acfc_shapes" / "pair_1" / "config_overlay.yaml"


@pytest.fixture(scope="session")
def pair1_config():
    """The shipped config + the pair-1 fixture overlay (M5): the client-shaped
    IIG template rows live in fixtures/, never in config/config.yaml."""
    return load_config(REPO / "config" / "config.yaml", overlays=[PAIR1_OVERLAY])


def _pair_paths(config, index: int) -> tuple[Path, Path]:
    if len(config.contracts.pairs) <= index:
        pytest.skip(f"{FIXTURES_REMOVED}: config.contracts.pairs[{index}] not configured")
    pair = config.contracts.pairs[index]
    contracts_dir = REPO / config.contracts.dir
    frd, sttm = contracts_dir / pair.frd, contracts_dir / pair.sttm
    require_fixture_files(frd, sttm)
    return frd, sttm


@pytest.fixture(scope="session")
def mids_specs(config):
    frd, sttm = _pair_paths(config, 0)
    return resolve_pair(frd, sttm, config)


@pytest.fixture(scope="session")
def caqh_spec(config):
    frd, sttm = _pair_paths(config, 1)
    specs = resolve_pair(frd, sttm, config)
    assert len(specs) == 1
    return specs[0]


@pytest.fixture(scope="session")
def specs_by_id(mids_specs, caqh_spec):
    return {spec.feed_id: spec for spec in [*mids_specs, caqh_spec]}


ACFC_SHAPES = REPO / "fixtures" / "acfc_shapes"
LAYOUT_PROFILES = REPO / "fixtures" / "layout_profiles"


@pytest.fixture(scope="session")
def pair1_contracts(pair1_config, tmp_path_factory) -> dict:
    """Pair 1 end to end (M9.4): the real-shape fixtures resolve by synonyms
    alone — the mock provider is offered and must never be called, no answers
    file — then STTM + FRD(docx) + VDD contracts. The FRD's Object Name cell
    lists the files (the patterns); the STTM supplies segments, schema and
    catalog; the layout stage names the feed after the stage band."""
    config = pair1_config
    tmp = tmp_path_factory.mktemp("pair1_contracts")
    import json

    from codegen.extract import contract_to_json as sttm_to_json
    from codegen.extract import extract_contract
    from codegen.extract.frd_docx import contract_to_json as frd_to_json
    from codegen.extract.vdd import contract_to_json as vdd_to_json
    from codegen.extract.vdd import extract_vdd_contract
    from codegen.layout.model import MockLayoutProvider
    from codegen.layout.resolve import resolve_pair as resolve_layout_pair

    provider = MockLayoutProvider([LAYOUT_PROFILES / "mock", LAYOUT_PROFILES])
    pair = resolve_layout_pair(
        ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx",
        ACFC_SHAPES / "frd" / "f1_pair_1.docx", config, provider=provider,
        cache_dirs=[tmp / "cache"], generated_date="2026-01-01",
        vdd_path=ACFC_SHAPES / "vdd" / "pair_1_v1_segments.xlsx")
    assert pair.provider_calls == 0 and provider.requests == [] and pair.questions == []
    frd_json = tmp / "frd.contract.json"
    frd_json.write_text(frd_to_json(pair.frd_contract), encoding="utf-8")
    frd_feed = json.loads(frd_json.read_text(encoding="utf-8"))["feeds"][0]
    assert frd_feed["feed_name"] == "vnd_p_accum_client"       # named after the stage band
    assert len(frd_feed["file_name_patterns"]) == 4            # the Object Name cell's lines
    sttm_json = tmp / "sttm.contract.json"
    contract = extract_contract(ACFC_SHAPES / "sttm" / "pair_1_family_a.xlsx", frd_json, config,
                                generated_date="2026-01-01", layout=pair.sttm.profile)
    sttm_json.write_text(sttm_to_json(contract), encoding="utf-8")
    vdd_json = tmp / "vdd.contract.json"
    vdd_contract, _ = extract_vdd_contract(ACFC_SHAPES / "vdd" / "pair_1_v1_segments.xlsx", config,
                                           generated_date="2026-01-01")
    vdd_json.write_text(vdd_to_json(vdd_contract), encoding="utf-8")
    return {"frd": frd_json, "sttm": sttm_json, "vdd": vdd_json}


@pytest.fixture(scope="session")
def pair1_spec(pair1_config, pair1_contracts):
    """The pair-1 contracts (``pair1_contracts``) resolved: one feed."""
    (spec,) = resolve_contracts(pair1_contracts["frd"], pair1_contracts["sttm"], pair1_config,
                                vdd_path=pair1_contracts["vdd"])
    return spec
