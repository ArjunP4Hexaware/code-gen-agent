"""FRD contracts from the upstream FRD→STTM agent's Delta table.

The FRD→STTM agent audits every FRD it processes into
``soham_workspace.sttm_agent.frd_contracts`` (doc_id, status, n_feeds,
n_ambiguities, n_strict_failed, contract JSON, audited_at — schema
confirmed live 2026-08-28). That table is CodeGen's ONLY source of real
FRD contracts: there is deliberately no docx→contract extractor here, and
a document with no contract row is a loud "run the FRD→STTM agent first",
never something CodeGen works around.

Reads go through ``codegen.databricks.read_table_rows`` — SELECT-only by
construction, allowlisted via ``databricks.readable_tables``, 60 s cached,
and the first read wakes the serverless warehouse (DBU spend). Selected
contracts are materialized VERBATIM to ``out/_contracts/<stem>.json`` so
the resolver consumes a local file like any other contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract
from codegen.demo_sources import canonical_document_name

FRD_CONTRACTS_TABLE = "soham_workspace.sttm_agent.frd_contracts"


class UpstreamContractError(RuntimeError):
    """A contract row is missing or fails validation — surfaced verbatim."""


def _cfg(config: Config):
    from codegen.databricks import config_for

    # require=(): a table read needs the warehouse + the readable_tables
    # allowlist, never the document volumes (a separate, optional seam).
    return config_for(config.databricks, require=())


def list_contracts(config: Config) -> list[dict]:
    """Light listing: [{doc_id, status, n_feeds, audited_at}] (no payloads)."""
    from codegen.databricks import read_table_rows

    rows = read_table_rows(
        _cfg(config), FRD_CONTRACTS_TABLE,
        columns=["doc_id", "status", "n_feeds", "audited_at"],
    )
    return sorted(rows, key=lambda r: r["doc_id"].lower())


def load_contract(config: Config, doc_id: str) -> tuple[FrdContract, dict]:
    """(validated FrdContract, {doc_id, status, audited_at, payload}).

    Validation errors surface VERBATIM — a drifted upstream contract is a
    conversation with the FRD→STTM side, not something to paper over.
    """
    from codegen.databricks import read_table_rows

    rows = read_table_rows(_cfg(config), FRD_CONTRACTS_TABLE)
    row = next((r for r in rows if r["doc_id"] == doc_id), None)
    if row is None:
        available = ", ".join(sorted(r["doc_id"] for r in rows)) or "<none>"
        raise UpstreamContractError(
            f"no contract for {doc_id!r} in {FRD_CONTRACTS_TABLE} — run the "
            f"FRD→STTM agent for this document first. Available: {available}"
        )
    try:
        contract = FrdContract.model_validate(json.loads(row["contract"]))
    except Exception as exc:  # noqa: BLE001 — verbatim, per instruction
        raise UpstreamContractError(
            f"contract for {doc_id!r} failed validation:\n{exc}"
        ) from exc
    meta = {"doc_id": row["doc_id"], "status": row["status"],
            "audited_at": row["audited_at"], "payload": row["contract"]}
    return contract, meta


def materialize(config: Config, doc_id: str, base_dir: Path) -> tuple[Path, FrdContract, dict]:
    """Write the contract payload verbatim to ``out/_contracts/<stem>.json``
    and return (path, contract, meta). Content-identical writes are skipped."""
    contract, meta = load_contract(config, doc_id)
    stem = canonical_document_name(doc_id).replace(" ", "_")
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in stem)
    target = base_dir / config.output.dir / "_contracts" / f"{safe}.contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = meta["payload"]
    if not (target.is_file() and target.read_text(encoding="utf-8") == payload):
        target.write_text(payload, encoding="utf-8", newline="\n")
    return target, contract, meta
