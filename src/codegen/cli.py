"""codegen CLI — generate Databricks ingestion pipelines from contracts.

Commands:
  generate      one FRD+STTM pair (optionally one feed of it)
  generate-all  every pair listed in config.contracts.pairs
  extract-sttm  extract an STTM mapping contract from a client workbook
                paired with its FRD feed contract (deterministic, no LLM)
  sharepoint-fetch    library -> local input dir (workbooks + contracts)
  sharepoint-publish  one feed's generated artifacts -> library output folder
  databricks-fetch    UC volumes -> local input dir (FRDs + STTM workbooks)
  demo-source-files   the demo UI's source-files display JSON (pure read)

The two sharepoint-* commands are the transport seam at the edges; the
generation path between them never opens a socket (codegen/sharepoint.py).

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
from codegen.faq import faq_for_spec
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
    output_mode: str | None = None,
) -> GateResult:
    out_root = Path(config.output.dir)
    reports_dir = Path(config.output.reports_dir)
    feed_dir = out_root / spec.feed_slug

    outcomes = compile_rules(spec)
    provider = build_provider(config, dry_run)
    candidates = run_reasoning(spec, outcomes, provider)
    # Three-input model: file answers (fixtures/faq/<slug>.faq.yaml) plus
    # contract prefills; missing file => all defaults, flagged by the gate.
    faq = faq_for_spec(spec, config)

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
        faq=faq,
    )
    # Option A ("notebook") is today's path, byte for byte. Option B
    # ("framework") renders the SAME pipeline into a scratch tree so the
    # gate checks stay identical, but persists only ddl/ + framework/;
    # "both" persists everything. MIRRORED in service._generate_feed.
    effective_mode = output_mode or config.output.mode
    framework_artefacts = None
    if effective_mode == "framework":
        written, checks, tests_skipped, ddl_sources = _emit_framework_only(
            context, spec, config, feed_dir, skip_tests
        )
        framework_artefacts = _run_emit_framework(
            spec, faq, ddl_sources, config, out_root, outcomes, base_dir=None
        )
        written = [*written, *framework_artefacts.files]
    else:
        written = emit_feed(context, out_root)
        checks = None  # computed below, exactly as before
        if effective_mode == "both":
            ddl_sources = _read_ddl_sources(feed_dir)
            framework_artefacts = _run_emit_framework(
                spec, faq, ddl_sources, config, out_root, outcomes, base_dir=None
            )
            written = [*written, *framework_artefacts.files]
    _write_candidates_artifact(candidates, feed_dir)

    if checks is None:
        checks = run_preflight(feed_dir, config)
        tests_skipped = skip_tests or not config.gate.run_generated_tests
        if not tests_skipped:
            checks = [*checks, run_generated_tests(feed_dir, config.gate.pytest_tail_lines)]

    gate = compute_verdict(
        spec.feed_id,
        outcomes,
        candidates,
        checks,
        tests_skipped,
        faq=faq,
        standards=config.engineering_standards,
    )
    write_generation_report(
        spec,
        written,
        outcomes,
        candidates,
        gate,
        reports_dir,
        out_root,
        inputs_summary=context["provenance"]["inputs"],
    )
    if framework_artefacts is not None:
        # Appended AFTER the standard report so report/ stays untouched and
        # notebook-mode reports remain byte-identical.
        from codegen.emit.framework import report_section

        with open(reports_dir / f"{spec.feed_slug}.md", "a",
                  encoding="utf-8", newline="\n") as handle:
            handle.write(report_section(framework_artefacts))
    print(console_summary(spec, gate))
    return gate


def _read_ddl_sources(feed_dir: Path) -> list[tuple[str, str]]:
    return sorted(
        (p.name, p.read_text(encoding="utf-8"))
        for p in (feed_dir / "ddl").glob("*.sql")
    )


def _emit_framework_only(context, spec, config, feed_dir, skip_tests):
    """Framework mode: full render + gate checks in a scratch tree (so the
    verdict is IDENTICAL to notebook mode), persisting only ddl/."""
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        emit_feed(context, tmp_root)
        tmp_feed_dir = tmp_root / spec.feed_slug
        checks = run_preflight(tmp_feed_dir, config)
        tests_skipped = skip_tests or not config.gate.run_generated_tests
        if not tests_skipped:
            checks = [*checks,
                      run_generated_tests(tmp_feed_dir, config.gate.pytest_tail_lines)]
        ddl_sources = _read_ddl_sources(tmp_feed_dir)
        feed_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp_feed_dir / "ddl", feed_dir / "ddl", dirs_exist_ok=True)
    written = [feed_dir / "ddl" / name for name, _ in ddl_sources]
    return written, checks, tests_skipped, ddl_sources


def _run_emit_framework(spec, faq, ddl_sources, config, out_root, outcomes,
                        base_dir):
    from codegen.emit.framework import emit_framework

    contracts_dir = Path(config.contracts.dir)
    if base_dir is not None:
        contracts_dir = base_dir / contracts_dir
    frd_path = contracts_dir / spec.frd_contract_name
    return emit_framework(
        spec, faq, ddl_sources, config, out_root,
        base_dir=base_dir,
        frd_path=frd_path if frd_path.is_file() else None,
        unmapped_rule_texts={
            o.rule_text for o in outcomes if o.classification == "unmapped"
        },
    )


def _run_pairs(
    pairs: list[tuple[Path, Path]],
    config: Config,
    *,
    only_feed: str | None,
    dry_run: bool,
    skip_tests: bool,
    output_mode: str | None = None,
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
                gate = _generate_feed(spec, config, dry_run=dry_run,
                                      skip_tests=skip_tests, output_mode=output_mode)
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


def _sharepoint_fetch(args: argparse.Namespace, config: Config) -> int:
    """Pull the library's workbooks/contracts into a local input directory.

    The read-side edge of the transport seam (codegen.sharepoint's module
    docstring has the full rationale). Deliberately a separate command rather
    than a flag on `extract-sttm`: keeping the network at the edge is what
    lets the generator stay offline and credential-free, and it means a
    re-run after a parse fix does not re-download anything.

    Fetching nothing is an error, not a no-op — an empty library folder and a
    successful fetch must not look the same to whatever runs next.
    """
    from codegen.sharepoint import (
        SUPPORTED_SUFFIXES,
        GraphError,
        SharePointConfigError,
        build_client,
        config_for,
    )

    try:
        cfg = config_for(config.sharepoint)
        client = build_client(cfg)
        print(f"site:    {cfg.host}{cfg.site_path}")
        print(f"library: {cfg.library}  folder: {cfg.input_folder or '<root>'}")
        print(f"dest:    {args.dest}")
        fetched = client.fetch_to_dir(args.dest, suffixes=SUPPORTED_SUFFIXES)
    except (SharePointConfigError, GraphError) as exc:
        print(f"{'FAIL':<15} sharepoint-fetch — {exc}")
        return 1

    for item in fetched:
        print(f"{'FETCHED':<15} {item.name} — {item.size:,} bytes, modified {item.modified}")
    if not fetched:
        print(
            f"{'FAIL':<15} sharepoint-fetch — no supported documents in "
            f"{cfg.library}/{cfg.input_folder or '<root>'} "
            f"(supported: {sorted(SUPPORTED_SUFFIXES)}). Upload an STTM workbook or an "
            f"FRD contract, or check sharepoint.input_folder in config/config.yaml."
        )
        return 1
    print(f"\n{len(fetched)} file(s) -> {args.dest}")
    return 0


def _publishable(args: argparse.Namespace, config: Config) -> list[Path]:
    """The artifact list for one publish call, with containment enforced.

    `--path` addresses one file relative to the feed's output directory and
    is resolved-and-checked the same way the UI's file reader does: a library
    write must never be steerable outside `out/<feed_slug>/` by a `..`.
    With no `--path`, the deliverables are the feed's generation report and
    its assembled notebook — the two artifacts a reviewer hands over.
    """
    feed_dir = (Path(config.output.dir) / args.feed).resolve()
    if args.path:
        target = (feed_dir / args.path).resolve()
        if not target.is_relative_to(feed_dir):
            raise ValueError(f"path escapes the feed directory: {args.path}")
        return [target]
    return [
        Path(config.output.reports_dir).resolve() / f"{args.feed}.md",
        feed_dir / f"{args.feed}.ipynb",
    ]


def _sharepoint_publish(args: argparse.Namespace, config: Config) -> int:
    """Publish one feed's generated artifacts to the library output folder.

    The write-side edge. Publishing is deliberately NOT folded into
    `generate`: generation re-runs every time a rule or a contract changes,
    and a re-generate is not automatically a re-publish — the human gate sits
    between them. Running this command IS that gate, which is why it takes no
    `--confirm` flag; the UI endpoint, which a stray POST could reach, does
    require one.

    Publishing nothing is an error for the same reason a silent no-op is
    wrong upstream: downstream it is indistinguishable from success.
    """
    from codegen.sharepoint import (
        GraphError,
        SharePointConfigError,
        build_client,
        config_for,
        published_name,
    )

    try:
        artifacts = _publishable(args, config)
    except ValueError as exc:
        print(f"{'FAIL':<15} sharepoint-publish — {exc}")
        return 1

    missing = [p for p in artifacts if not p.is_file()]
    if missing:
        print(
            f"{'FAIL':<15} sharepoint-publish — nothing to publish for {args.feed!r}: "
            + ", ".join(str(p) for p in missing)
            + ". Run `codegen generate` (or generate-all) first."
        )
        return 1

    try:
        cfg = config_for(config.sharepoint)
        client = build_client(cfg)
        print(f"site:      {cfg.host}{cfg.site_path}")
        print(f"library:   {cfg.library}  folder: {cfg.output_folder or '<root>'}")
        for path in artifacts:
            name = published_name(args.feed, path.name)
            result = client.upload_file(path, name=name)
            print(f"{'PUBLISHED':<15} {name} — {path.stat().st_size:,} bytes "
                  f"-> {result.get('webUrl', '<no url>')}")
    except (SharePointConfigError, GraphError) as exc:
        print(f"{'FAIL':<15} sharepoint-publish — {exc}")
        return 1

    print(f"\n{len(artifacts)} artifact(s) published to "
          f"{cfg.library}/{cfg.output_folder or '<root>'}.")
    return 0


# Filename date-token table for the landing seeder. Tokens resolve only at
# word boundaries (so OH / MIDS stay literal); HHMM/HH use a fixed synthetic
# delivery time of 06:00. Anything date-ish left after resolution is flagged
# and kept literal — the seeder never guesses.
_SEED_TOKEN_TABLE: tuple[tuple[str, str], ...] = (
    ("CCYYMMDD", "%Y%m%d"),
    ("YYYYMMDD", "%Y%m%d"),
    ("CCYY", "%Y"),
    ("YYYY", "%Y"),
    ("MM", "%m"),
    ("DD", "%d"),
    ("HHMM", "0600"),
    ("HH", "06"),
)
_SEED_LEFTOVER_RE = None  # compiled lazily in _resolve_pattern_tokens


def _resolve_pattern_tokens(pattern: str, date) -> tuple[str, list[str]]:
    """(resolved filename, flagged leftover tokens)."""
    import re as re_module

    global _SEED_LEFTOVER_RE  # noqa: PLW0603 — lazy compile, module cache
    if _SEED_LEFTOVER_RE is None:
        _SEED_LEFTOVER_RE = re_module.compile(
            r"(?<![A-Za-z])(?:CC|YY|MM|DD|HH|SS)[A-Z]*(?![a-z])"
        )
    resolved = pattern
    for token, replacement in _SEED_TOKEN_TABLE:
        value = date.strftime(replacement) if "%" in replacement else replacement
        resolved = re_module.sub(
            rf"(?<![A-Za-z]){token}(?![A-Za-z])", value, resolved
        )
    flagged = _SEED_LEFTOVER_RE.findall(resolved)
    return resolved, flagged


def _synthetic_file_bytes(spec, filename: str) -> bytes:
    """Deterministic synthetic content: header row from the spec's source
    columns + 3 obviously-fake rows (seeded RNG keyed by filename; values
    like MBR000001 — never real-looking PII, never client data)."""
    import random

    columns = [f.source_column for seg in spec.segments for f in seg.fields]
    delimiter = spec.delimiter or ","
    rng = random.Random(f"{spec.feed_slug}/{filename}")
    rows = [delimiter.join(columns)]
    for _ in range(3):
        rows.append(delimiter.join(
            f"{column[:3].upper()}{rng.randint(0, 999999):06d}"
            for column in columns
        ))
    return ("\n".join(rows) + "\n").encode("utf-8")


def _databricks_seed_landing(args: argparse.Namespace, config: Config) -> int:
    """Seed the landing volume with synthetic files (the seam's first write).

    Dry-run by default; --apply creates the volume, uploads, lists back and
    verifies. The target is read from config ONLY and guarded by
    codegen.databricks.WRITABLE_PREFIX — there is no target argument.
    """
    import hashlib
    from datetime import datetime

    from codegen.databricks import (
        DatabricksConfigError,
        DatabricksTransportError,
        config_for,
        ensure_volume,
        list_landing,
        upload_file,
    )
    from codegen.resolve.resolver import resolve_pair

    date = datetime.strptime(args.date, "%Y%m%d") if args.date else datetime.now()

    contracts_dir = Path(config.contracts.dir)
    frd_path = contracts_dir / config.demo.frd
    sttm_path = contracts_dir / config.demo.sttm
    if not (frd_path.is_file() and sttm_path.is_file()):
        print(f"{'FAIL':<15} databricks-seed-landing — demo contract pair not found "
              f"({frd_path.name}, {sttm_path.name}); synthetic content comes from "
              "the resolved demo spec only.")
        return 1
    specs = resolve_pair(frd_path, sttm_path, config)

    files: list[tuple[str, bytes]] = []
    flagged_tokens: list[str] = []
    seen: set[str] = set()
    for spec in specs:
        root = (spec.landing_location or "").replace("\\", "/").strip("/")
        if not root:
            print(f"{'SKIP':<15} {spec.feed_slug} — no landing_location in the FRD")
            continue
        for pattern in spec.file_name_patterns:
            name, flagged = _resolve_pattern_tokens(pattern, date)
            flagged_tokens += [f"{spec.feed_slug}/{pattern}: {t}" for t in flagged]
            relative = f"{root}/{name}"
            if relative in seen:  # CCYY and YYYY variants resolve identically
                continue
            seen.add(relative)
            files.append((relative, _synthetic_file_bytes(spec, name)))

    try:
        cfg = config_for(config.databricks)
        target = f"{cfg.catalog}.{cfg.schema}.{cfg.landing_volume}"
    except DatabricksConfigError as exc:
        print(f"{'FAIL':<15} databricks-seed-landing — {exc}")
        return 1

    print(f"target volume: {target}  (the ONLY writable location)")
    for relative, data in files:
        print(f"{'WOULD UPLOAD' if not args.apply else 'QUEUED':<15} "
              f"{relative} — {len(data):,} bytes")
    for note in flagged_tokens:
        print(f"{'FLAGGED':<15} unresolved token left literal: {note}")
    if not args.apply:
        print(f"\nDRY RUN — {len(files)} file(s), nothing written. "
              "Re-run with --apply to create the volume and upload.")
        return 0

    answer = input(
        f"\nType 'yes' to create/seed {target} with {len(files)} synthetic "
        "file(s): "
    )
    if answer.strip() != "yes":
        print(f"{'ABORTED':<15} confirmation not given — nothing written.")
        return 1

    try:
        state = ensure_volume(cfg)
        print(f"{'CREATED' if state['created'] else 'EXISTED':<15} {state['full_name']}")
        for relative, data in files:
            path = upload_file(cfg, relative, data, force=args.force)
            print(f"{'UPLOADED':<15} {path} — {len(data):,} bytes")
        listed = list_landing(cfg)
    except (DatabricksConfigError, DatabricksTransportError) as exc:
        print(f"{'FAIL':<15} databricks-seed-landing — {exc}")
        return 1

    # Verify: everything sent must list back with the size we sent.
    listed_sizes = {entry["path"]: entry["size"] for entry in listed}
    mismatches = [
        f"{relative}: sent {len(data):,} B, listed "
        f"{listed_sizes.get(relative, 'MISSING')}"
        for relative, data in files
        if listed_sizes.get(relative) != len(data)
    ]
    if mismatches:
        print(f"{'FAIL':<15} verification mismatch:\n  - " + "\n  - ".join(mismatches))
        return 1

    manifest = {
        "volume": target,
        "seeded_at": datetime.now().isoformat(timespec="seconds"),
        "date_token": date.strftime("%Y%m%d"),
        "files": [
            {"path": relative, "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest()}
            for relative, data in files
        ],
    }
    manifest_path = Path(config.output.dir) / "_seed_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
    print(f"\n{'VERIFIED':<15} {len(files)} file(s) listed back with matching sizes")
    for entry in listed:
        print(f"  {entry['path']}  {entry['size']:,} B  {entry['modified']}")
    print(f"manifest -> {manifest_path}")
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
    common.add_argument(
        "--output-mode",
        choices=["notebook", "framework", "both"],
        default=None,
        help="override output.mode: notebook (Option A, default), framework "
        "(Option B: DDL scripts + config rows + inserts for the existing "
        "ingestion framework), or both",
    )

    generate = subparsers.add_parser(
        "generate", parents=[common], help="generate one contract pair"
    )
    generate.add_argument("--feed", help="generate only this feed_id from the pair")
    generate.add_argument("--frd-contract", "--frd", dest="frd_contract", required=True,
                          help="FRD contract JSON (the pair's FRD side)")
    generate.add_argument("--sttm-contract", "--sttm", dest="sttm_contract", required=True,
                          help="STTM mapping contract JSON (the pair's STTM side)")

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

    fetch = subparsers.add_parser(
        "sharepoint-fetch",
        help="download STTM workbooks / FRD contracts from the SharePoint library",
    )
    fetch.add_argument("--config", default="config/config.yaml")
    fetch.add_argument(
        "--dest", required=True, help="local directory the documents land in"
    )

    demo_sources = subparsers.add_parser(
        "demo-source-files",
        help="print the demo UI's source-files JSON (pure read, no network)",
    )
    demo_sources.add_argument("--config", default="config/config.yaml")

    seed = subparsers.add_parser(
        "databricks-seed-landing",
        help="seed the landing volume with SYNTHETIC files from the demo spec "
        "(dry-run by default; the ONLY writable location is guarded in code)",
    )
    seed.add_argument("--config", default="config/config.yaml")
    seed.add_argument("--apply", action="store_true",
                      help="actually create the volume and upload (typed 'yes' "
                      "confirmation required); default is a dry-run print")
    seed.add_argument("--force", action="store_true",
                      help="allow overwriting files that already exist in the volume")
    seed.add_argument("--date", help="YYYYMMDD resolved into filename date tokens "
                      "(CCYY/YYYY/MM/DD; HHMM fixed at 0600); default today")

    demo_metadata = subparsers.add_parser(
        "demo-metadata-sheet",
        help="print the metadata-sheet preview JSON, or write it as .xlsx "
        "(display only; pure read, no network)",
    )
    demo_metadata.add_argument("--config", default="config/config.yaml")
    demo_metadata.add_argument("--xlsx", help="write the workbook here instead of printing JSON")

    db_fetch = subparsers.add_parser(
        "databricks-fetch",
        help="download raw FRD/STTM documents from the Unity Catalog volumes "
        "(read-only; requires the [databricks] extra)",
    )
    db_fetch.add_argument("--config", default="config/config.yaml")
    db_fetch.add_argument(
        "--dest", default="inputs/databricks",
        help="local directory the documents land in (default: inputs/databricks)",
    )

    publish = subparsers.add_parser(
        "sharepoint-publish",
        help="publish one feed's generated artifacts to the SharePoint library",
    )
    publish.add_argument("--config", default="config/config.yaml")
    publish.add_argument("--feed", required=True, help="feed_slug to publish")
    publish.add_argument(
        "--path",
        help="one file relative to out/<feed_slug>/ (default: the feed's "
        "report + assembled notebook)",
    )

    args = parser.parse_args(argv)
    load_dotenv()
    config = load_config(args.config)

    if args.command == "extract-sttm":
        return _extract_sttm(args, config)

    if args.command == "demo-source-files":
        # Same JSON as GET /api/demo/source-files — display data only.
        from codegen.demo_sources import source_files_payload

        try:
            # shell_mode pinned synthetic: this command stays offline.
            payload = source_files_payload(config, Path.cwd(), shell_mode="synthetic")
        except FileNotFoundError as exc:
            print(f"{'FAIL':<15} demo-source-files — {exc}")
            return 1
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "demo-metadata-sheet":
        # Same payload as GET /api/demo/metadata-sheet — display data only.
        # The STTM-derived cells resolve from the demo contract pair when its
        # fixture files exist; otherwise the columns tab is empty, honestly.
        from codegen.metadata_sheet import build_workbook, metadata_sheet_payload

        contracts_dir = Path(config.contracts.dir)
        frd_path = contracts_dir / config.demo.frd
        sttm_path = contracts_dir / config.demo.sttm
        specs = unmapped = None
        if frd_path.is_file() and sttm_path.is_file():
            specs = resolve_pair(frd_path, sttm_path, config)
            unmapped = {
                spec.feed_slug: {
                    o.rule_text
                    for o in compile_rules(spec)
                    if o.classification == "unmapped"
                }
                for spec in specs
            }
        try:
            payload = metadata_sheet_payload(
                config, Path.cwd(), specs=specs, unmapped_by_slug=unmapped
            )
        except FileNotFoundError as exc:
            print(f"{'FAIL':<15} demo-metadata-sheet — {exc}")
            return 1
        if args.xlsx:
            build_workbook(payload).save(args.xlsx)
            coverage = payload["coverage"]
            print(f"{'WRITTEN':<15} {args.xlsx} — {coverage['derived']}/{coverage['total']} "
                  "cells derived from documents")
        else:
            print(json.dumps(payload, indent=2))
        return 0

    if args.command == "sharepoint-fetch":
        return _sharepoint_fetch(args, config)

    if args.command == "databricks-seed-landing":
        return _databricks_seed_landing(args, config)

    if args.command == "databricks-fetch":
        # Read-side edge of the Databricks volumes seam — same posture as
        # sharepoint-fetch: fetch to local disk, then generate from disk.
        from codegen.databricks import (
            DatabricksConfigError,
            DatabricksTransportError,
            config_for,
            fetch_document,
            list_documents,
        )

        try:
            cfg = config_for(config.databricks)
            listing = list_documents(cfg)
            print(f"volumes: {cfg.catalog}.{cfg.schema}.{cfg.frd_volume} + "
                  f".{cfg.sttm_volume}  (profile {cfg.profile})")
            fetched = 0
            for kind, files in listing.items():
                volume = cfg.frd_volume if kind == "frd" else cfg.sttm_volume
                for item in files:
                    local = fetch_document(cfg, volume, item["name"], args.dest)
                    print(f"{'FETCHED':<15} {local.name} — {item['size']:,} bytes")
                    fetched += 1
        except (DatabricksConfigError, DatabricksTransportError) as exc:
            print(f"{'FAIL':<15} databricks-fetch — {exc}")
            return 1
        if not fetched:
            print(f"{'FAIL':<15} databricks-fetch — no supported documents in "
                  "either volume. Upload an STTM workbook or an FRD document, or "
                  "check the `databricks:` section of config/config.yaml.")
            return 1
        print(f"\n{fetched} file(s) -> {args.dest}")
        return 0

    if args.command == "sharepoint-publish":
        return _sharepoint_publish(args, config)

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
        if not config.contracts.pairs:
            # Empty since 2026-08-22 (contract fixtures removed from the repo).
            # Refuse loudly rather than report a silent zero-feed success.
            print(
                f"{'FAIL':<15} config.contracts.pairs is empty -- nothing to generate. "
                "Restore anonymized contract pairs in config/config.yaml or run "
                "`codegen generate --frd-contract X --sttm-contract Y`."
            )
            return 1
        contracts_dir = Path(config.contracts.dir)
        pairs = [(contracts_dir / p.frd, contracts_dir / p.sttm) for p in config.contracts.pairs]
        only_feed = None

    return _run_pairs(
        pairs, config, only_feed=only_feed, dry_run=args.dry_run,
        skip_tests=args.skip_tests, output_mode=args.output_mode
    )


if __name__ == "__main__":
    sys.exit(main())
