"""codegen CLI — generate Databricks ingestion pipelines from contracts.

Commands:
  generate      one FRD+STTM pair (optionally one feed of it)
  generate-all  every pair listed in config.contracts.pairs
  extract-sttm  extract an STTM mapping contract from a client workbook
                paired with its FRD feed contract (deterministic, no LLM)

Per feed: resolve -> compile rules -> Layer 2 over unmapped rules -> render
templates -> write candidates artifact -> gate -> report. A feed that fails
resolution or rendering is reported FAIL and does not stop other feeds.
Exit code is 0 only when no feed FAILed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codegen.config import Config, load_config, load_dotenv
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.emit.context import TemplateGapError, build_context
from codegen.emit.emitter import emit_feed
from codegen.gate import compute_verdict, run_generated_tests, run_preflight
from codegen.gate.verdict import GateResult
from codegen.reasoning import build_provider, run_reasoning
from codegen.reasoning.engine import RuleCandidate
from codegen.report import console_summary, write_generation_report
from codegen.resolve.resolver import ContractMismatchError, resolve_pair
from codegen.rules.compiler import compile_rules


def _write_candidates_artifact(candidates: list[RuleCandidate], feed_dir: Path) -> Path | None:
    """Layer-2 output goes here — a review artifact, never a generated module."""
    if not candidates:
        return None
    artifact_dir = feed_dir / "candidates"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "candidates.json"
    payload = [candidate.model_dump() for candidate in candidates]
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return artifact_path


def _generate_feed(
    spec: ResolvedFeedSpec,
    config: Config,
    *,
    dry_run: bool,
    skip_tests: bool,
) -> GateResult:
    out_root = Path(config.output.dir)
    reports_dir = Path(config.output.reports_dir)
    feed_dir = out_root / spec.feed_slug

    outcomes = compile_rules(spec)
    provider = build_provider(config, dry_run)
    candidates = run_reasoning(spec, outcomes, provider)

    duplicate_outcome = next(
        (o for o in outcomes if o.feature == "allow_duplicate_file_name"), None
    )
    context = build_context(
        spec,
        config,
        # True both ways today: re-ingest is idempotent (MERGE), and the only
        # known duplicate-file rule turns the check off. The flag exists so a
        # future "check on" rule can flip it.
        allow_duplicate_file_name=True,
        duplicate_rule_text=(
            duplicate_outcome.rule_text if duplicate_outcome is not None else None
        ),
        notification_rule_texts=[
            o.rule_text for o in outcomes if o.classification == "notification"
        ],
    )
    written = emit_feed(context, out_root)
    _write_candidates_artifact(candidates, feed_dir)

    checks = run_preflight(feed_dir, config)
    tests_skipped = skip_tests or not config.gate.run_generated_tests
    if not tests_skipped:
        checks = [*checks, run_generated_tests(feed_dir, config.gate.pytest_tail_lines)]

    gate = compute_verdict(spec.feed_id, outcomes, candidates, checks, tests_skipped)
    write_generation_report(spec, written, outcomes, candidates, gate, reports_dir, out_root)
    print(console_summary(spec, gate))
    return gate


def _run_pairs(
    pairs: list[tuple[Path, Path]],
    config: Config,
    *,
    only_feed: str | None,
    dry_run: bool,
    skip_tests: bool,
) -> int:
    failed = False
    matched_feed = False
    for frd_path, sttm_path in pairs:
        try:
            specs = resolve_pair(frd_path, sttm_path, config)
        except (ContractMismatchError, ValueError) as exc:
            print(f"{'FAIL':<15} {frd_path.name} + {sttm_path.name} — {exc}")
            failed = True
            continue
        for spec in specs:
            if only_feed is not None and spec.feed_id != only_feed:
                continue
            matched_feed = True
            try:
                gate = _generate_feed(spec, config, dry_run=dry_run, skip_tests=skip_tests)
            except TemplateGapError as exc:
                print(f"{'FAIL':<15} {spec.feed_id} — template gap: {exc}")
                failed = True
                continue
            if gate.verdict == "FAIL":
                failed = True
    if only_feed is not None and not matched_feed:
        print(f"{'FAIL':<15} no resolved feed matches --feed {only_feed!r}")
        failed = True
    return 1 if failed else 0


def _extract_sttm(args: argparse.Namespace, config: Config) -> int:
    from codegen.extract import ExtractionError, WorkbookParseError, extract_to_file

    try:
        workbook_path = Path(args.workbook)
        if not workbook_path.is_file():
            raise FileNotFoundError(f"workbook not found: {workbook_path}")
        contract = extract_to_file(
            workbook_path,
            _contract_path(args.frd_contract, config),
            Path(args.out),
            config,
            contract_name=args.contract_name,
            generated_date=args.generated_date,
        )
    except (WorkbookParseError, ExtractionError, FileNotFoundError, ValueError) as exc:
        print(f"{'FAIL':<15} extract-sttm — {exc}")
        return 1
    feeds = ", ".join(f"{f.feed_id} ({f.field_count} fields)" for f in contract.feeds)
    print(f"{'EXTRACTED':<15} {args.out} — {len(contract.feeds)} feed(s): {feeds}")
    return 0


def _contract_path(value: str, config: Config) -> Path:
    path = Path(value)
    if path.is_file():
        return path
    fallback = Path(config.contracts.dir) / value
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"contract not found: {value} (also tried {fallback})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codegen", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="config/config.yaml")
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="force the mock Layer-2 provider (no network)",
    )
    common.add_argument(
        "--skip-tests",
        action="store_true",
        help="skip running the generated pytest suites",
    )

    generate = subparsers.add_parser(
        "generate", parents=[common], help="generate one contract pair"
    )
    generate.add_argument("--feed", help="generate only this feed_id from the pair")
    generate.add_argument("--frd-contract", required=True)
    generate.add_argument("--sttm-contract", required=True)

    subparsers.add_parser("generate-all", parents=[common], help="generate every configured pair")

    extract = subparsers.add_parser(
        "extract-sttm",
        help="extract an STTM mapping contract from a workbook + FRD contract pair",
    )
    extract.add_argument("--config", default="config/config.yaml")
    extract.add_argument("--workbook", required=True, help="client STTM workbook (.xlsx)")
    extract.add_argument("--frd-contract", required=True)
    extract.add_argument("--out", required=True, help="path for the emitted contract JSON")
    extract.add_argument("--contract-name", help="override the derived contract_name")
    extract.add_argument(
        "--generated-date",
        help="YYYY-MM-DD stamped as generated_date; defaults to today "
        "(inject for byte-reproducible output)",
    )

    args = parser.parse_args(argv)
    load_dotenv()
    config = load_config(args.config)

    if args.command == "extract-sttm":
        return _extract_sttm(args, config)

    if args.command == "generate":
        try:
            pairs = [
                (
                    _contract_path(args.frd_contract, config),
                    _contract_path(args.sttm_contract, config),
                )
            ]
        except FileNotFoundError as exc:
            print(f"{'FAIL':<15} {exc}")
            return 1
        only_feed = args.feed
    else:
        contracts_dir = Path(config.contracts.dir)
        pairs = [(contracts_dir / p.frd, contracts_dir / p.sttm) for p in config.contracts.pairs]
        only_feed = None

    return _run_pairs(
        pairs, config, only_feed=only_feed, dry_run=args.dry_run, skip_tests=args.skip_tests
    )


if __name__ == "__main__":
    sys.exit(main())
