"""codegen CLI — generate Databricks ingestion pipelines from contracts.

Commands:
  generate      one FRD+STTM pair (optionally one feed of it)
  generate-all  every pair listed in config.contracts.pairs
  extract-sttm  extract an STTM mapping contract from a client workbook
                paired with its FRD feed contract (deterministic, no LLM)
  extract-frd   extract an FRD feed contract from a client FRD .docx
                (families F1/F2, deterministic, stdlib docx reading)
  sharepoint-fetch    library -> local input dir (workbooks + contracts)
  sharepoint-publish  one feed's generated artifacts -> library output folder
  databricks-fetch    UC volumes -> local input dir (FRDs + STTM workbooks)
  databricks-publish  one feed's generated artifacts -> UC output volume
                      (human-gated; WRITABLE_PREFIX enforced in code)
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
from codegen.reasoning.engine import RuleCandidate, segmented_review_items
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
    payload = []
    for candidate in candidates:
        entry = candidate.model_dump()
        if entry.get("kind") == "layer2":
            # Default-kind entries serialize exactly as before the segmented
            # dialect landed — flat candidates.json stays byte-identical.
            entry.pop("kind", None)
            entry.pop("detail", None)
            entry.pop("citation", None)
        payload.append(entry)
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return artifact_path


def _generate_feed(
    spec: ResolvedFeedSpec,
    config: Config,
    *,
    dry_run: bool,
    skip_tests: bool,
    output_mode: str | None = None,
    extra_flags: list[str] | None = None,
    conventions_profile: str | None = None,
    iig_template: str | None = None,
    playbook_template: str | None = None,
) -> GateResult:
    out_root = Path(config.output.dir)
    reports_dir = Path(config.output.reports_dir)
    feed_dir = out_root / spec.feed_slug

    outcomes = compile_rules(spec)
    provider = build_provider(config, dry_run)
    candidates = run_reasoning(spec, outcomes, provider)
    # M3: STTM-vs-VDD cross-check — one flag per mismatch citing both cells;
    # a fixed-width FRD with no VDD positions is a failed gate check.
    # M4: resolver provenance flags (facts taken from the STTM because the
    # FRD named none) and the drag-fill detector ride the same list.
    from codegen.gate.derivations import sibling_type_flags
    from codegen.gate.drag_fill import drag_fill_flags
    from codegen.gate.vdd_check import vdd_cross_check

    vdd_flags, vdd_check = vdd_cross_check(spec, config)
    # M7.1: correctness gates are GLOBAL — sibling-type consistency is a flag
    # (never FAIL); the cell / literal / cap checks join the gate after the
    # framework emit for every profile.
    # (de-duplicated: the UI passes the layout stage's flags, and the FRD
    # contract the layout stage wrote carries the same ones — M9.3)
    extra_flags = [*dict.fromkeys([*(extra_flags or []), *spec.provenance_flags]),
                   *drag_fill_flags(spec),
                   *sibling_type_flags(spec, config), *vdd_flags]
    # Segmented-extraction review items (assumption/conflict cards) ride the
    # same review artifact and decision flow as Layer-2 candidates.
    candidates = [*segmented_review_items(spec), *candidates]
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
    rfc_artefacts = None
    if effective_mode in ("framework", "rfc"):
        written, checks, tests_skipped, ddl_sources = _emit_framework_only(
            context, spec, config, feed_dir, skip_tests
        )
        framework_artefacts = _run_emit_framework(
            spec, faq, ddl_sources, config, out_root, outcomes, base_dir=None,
            conventions_profile=conventions_profile, iig_template=iig_template,
        )
        written = [*written, *framework_artefacts.files]
        if effective_mode == "rfc":
            # M5: the RFC deployment package, assembled from the framework
            # artefacts + config/FAQ; its blank-and-flag list joins the gate.
            from codegen.emit.rfc import emit_rfc_package

            rfc_artefacts = emit_rfc_package(
                spec, faq, config, out_root, framework_artefacts,
                flags_so_far=[*extra_flags, *framework_artefacts.flags],
                conventions_profile=conventions_profile, iig_template=iig_template,
                playbook_template=playbook_template, base_dir=None,
            )
            written = [*written, *rfc_artefacts.files]
    else:
        written = emit_feed(context, out_root)
        checks = None  # computed below, exactly as before
        if effective_mode in ("both", "all"):
            ddl_sources = _read_ddl_sources(feed_dir)
            framework_artefacts = _run_emit_framework(
                spec, faq, ddl_sources, config, out_root, outcomes, base_dir=None,
                conventions_profile=conventions_profile, iig_template=iig_template,
            )
            written = [*written, *framework_artefacts.files]
            if effective_mode == "all":
                from codegen.emit.rfc import emit_rfc_package

                rfc_artefacts = emit_rfc_package(
                    spec, faq, config, out_root, framework_artefacts,
                    flags_so_far=[*extra_flags, *framework_artefacts.flags],
                    conventions_profile=conventions_profile, iig_template=iig_template,
                    playbook_template=playbook_template, base_dir=None,
                )
                written = [*written, *rfc_artefacts.files]
    if framework_artefacts is not None:
        extra_flags = [*extra_flags, *framework_artefacts.flags]
    if rfc_artefacts is not None:
        extra_flags = [*extra_flags, *rfc_artefacts.flags]
    _write_candidates_artifact(candidates, feed_dir)

    if checks is None:
        checks = run_preflight(feed_dir, config)
        tests_skipped = skip_tests or not config.gate.run_generated_tests
        if not tests_skipped:
            checks = [*checks, run_generated_tests(feed_dir, config.gate.pytest_tail_lines)]
    if vdd_check is not None:
        checks = [*checks, vdd_check]
    if framework_artefacts is not None:
        checks = [*checks, *framework_artefacts.checks]   # M7.1 derivation gate (global)

    gate = compute_verdict(
        spec.feed_id,
        outcomes,
        candidates,
        checks,
        tests_skipped,
        faq=faq,
        standards=config.engineering_standards,
        extra_flags=extra_flags,
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
            if rfc_artefacts is not None:
                from codegen.emit.rfc import report_section as rfc_report_section

                handle.write(rfc_report_section(rfc_artefacts))
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
                        base_dir, conventions_profile=None, iig_template=None):
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
        conventions_profile=conventions_profile,
        iig_template=iig_template,
    )


def _run_pairs(
    pairs: list[tuple[Path, Path]],
    config: Config,
    *,
    only_feed: str | None,
    dry_run: bool,
    skip_tests: bool,
    output_mode: str | None = None,
    vdd_path: Path | None = None,
    conventions_profile: str | None = None,
    iig_template: str | None = None,
    playbook_template: str | None = None,
) -> int:
    failed = False
    matched_feed = False
    for frd_path, sttm_path in pairs:
        try:
            specs = resolve_pair(frd_path, sttm_path, config, vdd_path=vdd_path)
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
                                      skip_tests=skip_tests, output_mode=output_mode,
                                      conventions_profile=conventions_profile,
                                      iig_template=iig_template,
                                      playbook_template=playbook_template)
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
        layout = None
        if getattr(args, "layout", None):
            from codegen.layout.profile import LayoutProfile

            layout = LayoutProfile.model_validate_json(
                Path(args.layout).read_text(encoding="utf-8"))
        elif getattr(args, "answers", None):
            layout = _layout_from_answers(workbook_path, Path(args.answers), config)
        contract = extract_to_file(
            workbook_path,
            _contract_path(args.frd_contract, config),
            Path(args.out),
            config,
            contract_name=args.contract_name,
            generated_date=args.generated_date,
            layout=layout,
            require_complete=bool(getattr(args, "require_complete", False)),
        )
    except (WorkbookParseError, ExtractionError, FileNotFoundError, ValueError) as exc:
        print(f"{'FAIL':<15} extract-sttm — {exc}")
        return 1
    feeds = ", ".join(f"{f.feed_id} ({f.field_count} fields)" for f in contract.feeds)
    print(f"{'EXTRACTED':<15} {args.out} — {len(contract.feeds)} feed(s): {feeds}")
    return 0


def _outputs_through_storage(config: Config):
    """(config, push). Under the default outputs role (``output.dir`` in the
    checkout) nothing changes. With ``storage.outputs`` /
    ``CODEGEN_STORAGE_OUTPUTS`` set, generation writes into the role's local
    working directory and ``push()`` sends the tree up afterwards (Workspace
    API / Files API — never a /Volumes or /Workspace path)."""
    from codegen.storage import StorageError, open_storage

    outputs = open_storage(config, Path(".")).outputs
    if outputs.is_local and outputs.workdir == Path(".") / config.output.dir:
        return config, lambda: None
    scoped = config.model_copy(update={"output": config.output.model_copy(update={
        "dir": str(outputs.workdir), "reports_dir": str(outputs.workdir / "reports")})})

    def push() -> None:
        try:
            sent = outputs.push_tree("")
        except StorageError as exc:
            print(f"{'WARN':<15} outputs not stored: {exc} — they remain in {outputs.workdir}")
            return
        if sent:
            print(f"{'STORED':<15} {len(sent)} file(s) -> {outputs.uri()}")

    return scoped, push


def _layout_from_answers(workbook: Path, answers_path: Path, config: Config):
    """The workbook's layout profile with the answers file applied — cache and
    synonyms first, then the file's placements (source=user); never a model."""
    from codegen.layout.answers import apply_answers, load_answers
    from codegen.layout.resolve import resolve_workbook
    from codegen.storage import runtime_layout_cache

    runtime_cache, push_cache = runtime_layout_cache(config, Path("."))
    doc, _wb = resolve_workbook(workbook, config, provider=None,
                                runtime_cache_dir=runtime_cache)
    # M9.1: an answer may set any role, open or not — the file is applied even
    # when nothing is open (it then overrides a synonym / cached placement).
    answers, notes = apply_answers(load_answers(answers_path), doc.questions,
                                   {"sttm": workbook.name},
                                   documents={"sttm": (doc.profile, _wb)})
    for note in notes:
        print(f"{'NOTE':<15} {note}")
    if answers["sttm"]:
        doc, _wb = resolve_workbook(workbook, config, provider=None,
                                    runtime_cache_dir=runtime_cache,
                                    answers=answers["sttm"], prior=doc)
        print(f"{'ANSWERS':<15} {len(answers['sttm'])} answer(s) applied from "
              f"{answers_path} (source=user)")
        push_cache()
    for question in doc.questions:
        print(f"{'UNRESOLVED':<15} {question.key} — {question.reason}")
    return doc.profile


def _pair(args: argparse.Namespace, config: Config) -> int:
    """Pair an STTM with its FRD / VDD among a folder's documents BY CONTENT
    (codegen.pairing). An undecided pairing prints its candidates; settle it
    with `pairing:` in the answers file."""
    from codegen.demo_sources import canonical_document_name
    from codegen.layout.answers import AnswersFileError, load_answers
    from codegen.pairing import pair_by_content

    sttm = Path(args.sttm)
    if not sttm.is_file():
        print(f"{'FAIL':<15} pair — workbook not found: {sttm}")
        return 1
    folders = [Path(d) for d in (args.candidates or [str(sttm.parent)])]
    files = [p for d in folders if d.is_dir() for p in sorted(d.iterdir())
             if p.is_file() and not p.name.startswith("~$") and p != sttm]
    frds = {p.name: p for p in files
            if p.name.lower().endswith((".docx", ".contract.json"))
            and (p.suffix.lower() != ".docx" or canonical_document_name(p.name).startswith("frd"))}
    vdds = {p.name: p for p in files if p.suffix.lower() == ".xlsx"
            and not canonical_document_name(p.name).startswith("sttm")}
    try:
        chosen = (load_answers(Path(args.answers)).pairing.get(sttm.name, {})
                  if args.answers else {})
    except (AnswersFileError, OSError) as exc:
        print(f"{'FAIL':<15} pair — answers file: {exc}")
        return 1
    undecided = False
    for kind, candidates, explicit in (("frd", frds, config.demo.pairing_map),
                                       ("vdd", vdds, config.demo.vdd_pairing_map)):
        if chosen.get(kind):
            known = chosen[kind] in candidates
            print(f"{'PAIRED' if known else 'FAIL':<15} {kind} {chosen[kind]} — answers file"
                  + ("" if known else " names a document that is not among the candidates"))
            undecided = undecided or not known
            continue
        decision = pair_by_content(kind, sttm, candidates, config, Path("."),
                                   explicit_map=explicit)
        if decision.chosen:
            print(f"{'PAIRED':<15} {kind} {decision.chosen} — rule {decision.rule}: "
                  f"{decision.reason}")
        elif decision.ambiguous:
            undecided = True
            print(f"{'QUESTION':<15} {kind} — {decision.reason}")
            for candidate in decision.candidates:
                print(f"{'CANDIDATE':<15} {candidate.name} score {candidate.score:g} — "
                      f"{candidate.summary()}")
            print(f"{'REMEDY':<15} answers file: pairing: {{\"{sttm.name}\": "
                  f"{{{kind}: <candidate>}}}}")
        else:
            print(f"{'NONE':<15} {kind} — {decision.reason}")
    return 1 if undecided else 0


def load_workbook_for_answers(path: Path):
    from openpyxl import load_workbook

    return load_workbook(path, data_only=True)


def _layout(args: argparse.Namespace, config: Config) -> int:
    """Resolve and print the layout of a workbook (and optionally its FRD
    document): source per role, confidences, unresolved roles, the
    provider call count and — for a pair — the cross-document checks."""
    from codegen.layout.model import build_layout_provider
    from codegen.layout.resolve import resolve_pair

    workbook = Path(args.workbook)
    if not workbook.is_file():
        print(f"{'FAIL':<15} layout — workbook not found: {workbook}")
        return 1
    from codegen.layout.answers import (
        AnswersFileError,
        apply_answers,
        load_answers,
        unresolved_report,
    )
    from codegen.storage import StorageError, runtime_layout_cache

    frd = Path(args.frd) if args.frd else None
    vdd = Path(args.vdd) if args.vdd else None
    provider = build_layout_provider(config, dry_run=args.dry_run)
    try:
        # M8.3: the runtime profile cache lives in the state role
        # (storage.state) — the checkout by default, a workspace folder / a
        # volume when configured; never under fixtures/.
        runtime_cache, push_cache = runtime_layout_cache(config, Path("."))
    except StorageError as exc:
        print(f"{'FAIL':<15} layout — state storage: {exc}")
        return 1

    def resolve(answers: dict | None, refresh: bool = False, prior=None):
        return resolve_pair(workbook, frd, config, vdd_path=vdd, provider=provider,
                            runtime_cache_dir=runtime_cache, use_cache=not args.no_cache,
                            answers=answers, refresh=refresh, prior=prior)

    result = resolve(None, refresh=args.refresh)
    names = {"sttm": workbook.name, "frd": frd.name if frd else "", "vdd": vdd.name if vdd else ""}
    if args.refresh:
        print(f"{'REFRESH':<15} caches bypassed; runtime entries overwritten "
              f"({result.provider_calls} provider call(s))")
    if args.answers:
        # M9.1: applied even when nothing is open — an answer may override a
        # synonym / model / cached placement.
        try:
            documents = {"sttm": (result.sttm.profile, load_workbook_for_answers(workbook))}
            if vdd is not None and result.vdd is not None:
                documents["vdd"] = (result.vdd.profile, load_workbook_for_answers(vdd))
            answers, notes = apply_answers(load_answers(Path(args.answers)), result.questions,
                                           names, documents=documents)
        except (AnswersFileError, OSError) as exc:
            print(f"{'FAIL':<15} layout — answers file: {exc}")
            return 1
        for note in notes:
            print(f"{'NOTE':<15} {note}")
        placed = sum(len(answers[k]) for k in ("sttm", "vdd", "gaps"))
        if placed:
            # The second pass CONTINUES from the first (M9.1b): no cache read —
            # after --refresh the first pass has just written the entry, and
            # re-reading it reported source=cache — and no second model call.
            result = resolve(answers, refresh=args.refresh, prior=result)
            print(f"{'ANSWERS':<15} {placed} answer(s) applied from {args.answers} (source=user)")
    try:
        push_cache()
    except StorageError as exc:
        print(f"{'WARN':<15} layout — profile cache not stored: {exc}")
    if args.report_unresolved:
        target = Path(args.report_unresolved)
        target.write_text(unresolved_report(result.questions, names), encoding="utf-8",
                          newline="\n")
        print(f"{'REPORT':<15} {target} — {len(result.questions)} unresolved item(s), "
              "structural labels only")
    report = result.report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for document in ("sttm", "frd"):
            doc = report[document]
            if doc is None:
                continue
            print(f"{document.upper():<15} source={doc['source']} cache_hit={doc['cache_hit']} "
                  f"provider_calls={doc['provider_calls']} roles_by_source="
                  f"{doc['roles_by_source']}")
            for item in doc["rejections"]:
                print(f"{'REJECTED':<15} {item}")
            for item in doc["unresolved"]:
                print(f"{'UNRESOLVED':<15} {item}")
        profile = result.sttm.profile
        for key in sorted(profile.confidence):
            print(f"{'ROLE':<15} {key} conf={profile.confidence[key]:.2f} "
                  f"source={profile.role_sources.get(key, profile.source)}")
        for check in report["cross_checks"]:
            print(f"{'CROSSCHECK':<15} {check}")
        print(f"{'PROVIDER':<15} {provider.name}, {report['provider_calls']} call(s)")
    if args.profile_out:
        Path(args.profile_out).write_text(
            result.sttm.profile.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.frd_contract_out:
        if result.frd_contract is None:
            print(f"{'FAIL':<15} layout — --frd-contract-out needs --frd")
            return 1
        from codegen.extract.frd_docx import contract_to_json as frd_contract_to_json

        target = Path(args.frd_contract_out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(frd_contract_to_json(result.frd_contract), encoding="utf-8",
                          newline="\n")
        print(f"{'FRD CONTRACT':<15} {target} — feeds "
              f"{[f.feed_name for f in result.frd_contract.feeds]} "
              f"({len(result.gap_fills)} value(s) taken from the other documents)")
    if args.require_complete and result.questions:
        for question in result.questions:
            print(f"{'QUESTION':<15} {question.document} {question.key} — {question.reason}; "
                  f"candidates {question.candidates}")
        return 1
    return 0


def _extract_vdd(args: argparse.Namespace, config: Config) -> int:
    from codegen.extract.vdd import VddExtractionError, contract_to_json, extract_vdd_contract
    from codegen.layout.discover import NoLayoutError

    try:
        vdd_path = Path(args.vdd)
        if not vdd_path.is_file():
            raise FileNotFoundError(f"VDD workbook not found: {vdd_path}")
        tables: list[str] | None = None
        if args.sttm_contract:
            from codegen.contracts.sttm import SttmContract

            sttm = SttmContract.model_validate_json(
                Path(args.sttm_contract).read_text(encoding="utf-8"))
            tables = sorted({t for f in sttm.feeds
                             for t in (f.stage.table, f.source_table, f.feed_id) if t})
        layout = None
        if args.layout:
            from codegen.layout.profile import LayoutProfile

            layout = LayoutProfile.model_validate_json(
                Path(args.layout).read_text(encoding="utf-8"))
        contract, profile = extract_vdd_contract(
            vdd_path, config, sttm_tables=tables, layout=layout,
            generated_date=args.generated_date, contract_name=args.contract_name)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(contract_to_json(contract), encoding="utf-8", newline="\n")
        if args.profile:
            Path(args.profile).write_text(profile.model_dump_json(indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
    except (VddExtractionError, NoLayoutError, FileNotFoundError, ValueError) as exc:
        print(f"{'FAIL':<15} extract-vdd — {exc}")
        return 1
    print(f"{'EXTRACTED':<15} {args.out} — {len(contract.files)} file row(s), "
          f"{len(contract.fields)} field(s) on {contract.field_sheets}, "
          f"{len(contract.position_rows)} position row(s); layout source {profile.source}, "
          f"{len(profile.unresolved)} unresolved role(s)")
    return 0


def _extract_frd(args: argparse.Namespace, config: Config) -> int:
    from codegen.extract.frd_docx import FrdDocxError, contract_to_json, extract_frd_contract

    try:
        docx_path = Path(args.docx)
        if not docx_path.is_file():
            raise FileNotFoundError(f"FRD document not found: {docx_path}")
        contract, profile = extract_frd_contract(
            docx_path, config, contract_name=args.contract_name,
            generated_date=args.generated_date,
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(contract_to_json(contract), encoding="utf-8", newline="\n")
        if args.profile:
            profile_path = Path(args.profile)
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(profile.model_dump_json(indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    except (FrdDocxError, FileNotFoundError, ValueError) as exc:
        print(f"{'FAIL':<15} extract-frd — {exc}")
        return 1
    feeds = ", ".join(f.feed_name for f in contract.feeds)
    print(f"{'EXTRACTED':<15} {args.out} — family {profile.family}, layout source "
          f"{profile.source}, {len(contract.feeds)} feed(s): {feeds}; "
          f"{len(profile.unresolved)} unresolved field(s); status {contract.status}")
    for item in profile.unresolved:
        print(f"{'UNRESOLVED':<15} {item.field} — {item.reason}")
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


def _databricks_publish(args: argparse.Namespace, config: Config) -> int:
    """Publish one feed's generated artifacts to a Unity Catalog volume.

    The UC twin of `sharepoint-publish` — same doctrine: running this command
    IS the human gate (no `--confirm`; the UI endpoint requires one), and
    publishing nothing is an error, never a silent no-op. The target may be
    overridden per call, but `codegen.databricks` refuses anything outside
    WRITABLE_PREFIX in code.
    """
    from codegen.databricks import (
        DatabricksConfigError,
        DatabricksTransportError,
        config_for,
        ensure_volume,
        publish_artifacts,
    )

    try:
        artifacts = _publishable(args, config)
    except ValueError as exc:
        print(f"{'FAIL':<15} databricks-publish — {exc}")
        return 1
    missing = [p for p in artifacts if not p.is_file()]
    if missing:
        print(
            f"{'FAIL':<15} databricks-publish — nothing to publish for {args.feed!r}: "
            + ", ".join(str(p) for p in missing)
            + ". Run `codegen generate` (or generate-all) first."
        )
        return 1

    try:
        cfg = config_for(config.databricks)
        target = ensure_volume(cfg, volume=args.volume or cfg.output_volume,
                               knob="output_volume", catalog=args.catalog,
                               schema=args.schema)
        print(f"volume:    {target['full_name']}"
              + ("  (created)" if target["created"] else ""))
        published = publish_artifacts(
            cfg, args.feed, artifacts, catalog=args.catalog,
            schema=args.schema, volume=args.volume, force=args.force,
        )
        for item in published:
            print(f"{'PUBLISHED':<15} {item['name']} — "
                  f"{item['size_bytes']:,} bytes -> {item['path']}")
    except (DatabricksConfigError, DatabricksTransportError) as exc:
        print(f"{'FAIL':<15} databricks-publish — {exc}")
        return 1

    print(f"\n{len(artifacts)} artifact(s) published to /Volumes/"
          f"{target['full_name'].replace('.', '/')}/{args.feed}/.")
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
        choices=["notebook", "framework", "both", "rfc", "all"],
        default=None,
        help="override output.mode: notebook (Option A, default), framework "
        "(Option B: DDL scripts + config rows + inserts for the existing "
        "ingestion framework), both (notebook + framework), rfc (framework "
        "artefacts + the assembled RFC<number>_<Feed>/ deployment package), "
        "or all (notebook + framework + rfc)",
    )

    generate = subparsers.add_parser(
        "generate", parents=[common], help="generate one contract pair"
    )
    generate.add_argument("--feed", help="generate only this feed_id from the pair")
    generate.add_argument("--frd-contract", "--frd", dest="frd_contract", required=True,
                          help="FRD contract JSON (the pair's FRD side)")
    generate.add_argument("--sttm-contract", "--sttm", dest="sttm_contract", required=True,
                          help="STTM mapping contract JSON (the pair's STTM side)")
    generate.add_argument("--vdd-contract", "--vdd", dest="vdd_contract",
                          help="VDD contract JSON (codegen extract-vdd) — the pair's third input")
    generate.add_argument("--profile", dest="conventions_profile", default=None,
                          help="conventions profile (config conventions.profiles; default "
                               "conventions.profile — edo_sfmc = today's output)")
    generate.add_argument("--iig-template", dest="iig_template", default=None,
                          help="IIG workbook template version (iig_v1 = demo.metadata_sheet, "
                               "or a key of config metadata.templates)")
    generate.add_argument("--playbook-template", dest="playbook_template", default=None,
                          help="rfc mode: deployment playbook template (a key of config "
                               "playbook.templates; default playbook.template)")

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
    extract.add_argument("--layout", help="read through this resolved LayoutProfile JSON "
                                          "instead of discovering the layout")
    extract.add_argument("--answers", help="answers.yaml placing unresolved roles by hand "
                                           "(see `codegen layout --answers`); no model is "
                                           "called")
    extract.add_argument("--require-complete", action="store_true",
                         help="refuse when the layout has unresolved roles")

    layout = subparsers.add_parser(
        "layout",
        help="resolve a workbook's (and optionally its FRD's) layout: cache -> synonyms "
             "-> model -> validate -> user",
    )
    layout.add_argument("--config", default="config/config.yaml")
    layout.add_argument("--workbook", required=True, help="STTM workbook (.xlsx)")
    layout.add_argument("--frd", help="FRD document (.docx) or contract JSON of the pair")
    layout.add_argument("--vdd", help="vendor data dictionary (.xlsx) for the cross-checks")
    layout.add_argument("--dry-run", action="store_true",
                        help="mock provider (answers from fixtures/layout_profiles)")
    layout.add_argument("--no-cache", action="store_true", help="ignore cached profiles")
    layout.add_argument("--frd-contract-out",
                        help="write the FRD contract AS THE PAIR RESOLVED IT (a feed the FRD "
                             "leaves unnamed is named after the STTM stage band, gaps filled "
                             "from the STTM / VDD, each flagged) — use it for extract-sttm / "
                             "generate instead of a separate extract-frd")
    layout.add_argument("--refresh", action="store_true",
                        help="re-resolve past every cache AND overwrite the runtime cache "
                             "entries (a result with open questions tombstones them); the "
                             "reasons a model answer was rejected are written to "
                             "<runtime cache>/rejections/<fingerprint>.json")
    layout.add_argument("--json", action="store_true", help="print the report as JSON")
    layout.add_argument("--profile-out", help="write the resolved STTM profile JSON here")
    layout.add_argument("--answers", help="answers.yaml placing unresolved roles by hand: "
                                          "(document, sheet, role) -> column header text or "
                                          "index; applied with source=user")
    layout.add_argument("--report-unresolved", nargs="?", const="unresolved_headers.md",
                        help="write unresolved_headers.md (or the given path): per unresolved "
                             "role the sheet name, the header row texts and the candidate "
                             "columns — structural labels only, no data rows")
    layout.add_argument("--require-complete", action="store_true",
                        help="print the open questions and exit non-zero when roles remain")

    pair = subparsers.add_parser(
        "pair",
        help="pair an STTM with its FRD / VDD among a folder's documents by CONTENT (feed "
             "name, target tables, file patterns; the ticket number is one weak signal)",
    )
    pair.add_argument("--config", default="config/config.yaml")
    pair.add_argument("--sttm", required=True, help="STTM workbook (.xlsx)")
    pair.add_argument("--candidates", action="append",
                      help="folder of candidate documents (repeatable; default: the STTM's)")
    pair.add_argument("--answers", help="answers.yaml whose `pairing:` settles an undecided pair")

    extract_vdd = subparsers.add_parser(
        "extract-vdd",
        help="extract a Vendor Data Dictionary contract from a VDD workbook (patterns V1/V2/V3)",
    )
    extract_vdd.add_argument("--config", default="config/config.yaml")
    extract_vdd.add_argument("--vdd", required=True, help="vendor data dictionary (.xlsx)")
    extract_vdd.add_argument("--out", required=True, help="path for the emitted contract JSON")
    extract_vdd.add_argument("--sttm-contract", help="STTM contract JSON whose table names "
                                                     "select the field sheets of a "
                                                     "one-sheet-per-table dictionary")
    extract_vdd.add_argument("--layout", help="read through this resolved LayoutProfile JSON")
    extract_vdd.add_argument("--profile", help="also write the resolved layout profile JSON here")
    extract_vdd.add_argument("--contract-name", help="override the derived contract_name")
    extract_vdd.add_argument("--generated-date", help="YYYY-MM-DD stamped as generated_date")

    extract_frd = subparsers.add_parser(
        "extract-frd",
        help="extract an FRD feed contract from a client FRD .docx (families F1/F2)",
    )
    extract_frd.add_argument("--config", default="config/config.yaml")
    extract_frd.add_argument("--docx", required=True, help="client FRD document (.docx)")
    extract_frd.add_argument("--out", required=True, help="path for the emitted contract JSON")
    extract_frd.add_argument("--profile", help="also write the resolved FRD layout profile "
                                               "JSON to this path")
    extract_frd.add_argument("--contract-name", help="override the derived contract_name")
    extract_frd.add_argument(
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

    db_publish = subparsers.add_parser(
        "databricks-publish",
        help="publish one feed's generated artifacts to a Unity Catalog "
        "volume (human-gated write; targets outside WRITABLE_PREFIX refused)",
    )
    db_publish.add_argument("--config", default="config/config.yaml")
    db_publish.add_argument("--feed", required=True, help="feed_slug to publish")
    db_publish.add_argument(
        "--path",
        help="one file relative to out/<feed_slug>/ (default: the feed's "
        "report + assembled notebook)",
    )
    db_publish.add_argument("--catalog", default="",
                            help="override databricks.catalog for the target")
    db_publish.add_argument("--schema", default="",
                            help="override databricks.schema for the target")
    db_publish.add_argument("--volume", default="",
                            help="override databricks.output_volume")
    db_publish.add_argument("--force", action="store_true",
                            help="overwrite files already in the volume")

    args = parser.parse_args(argv)
    load_dotenv()
    config = load_config(args.config)

    if args.command == "extract-sttm":
        return _extract_sttm(args, config)
    if args.command == "extract-frd":
        return _extract_frd(args, config)
    if args.command == "extract-vdd":
        return _extract_vdd(args, config)
    if args.command == "layout":
        return _layout(args, config)
    if args.command == "pair":
        return _pair(args, config)

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

    if args.command == "databricks-publish":
        return _databricks_publish(args, config)

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

    try:
        config, push_outputs = _outputs_through_storage(config)
    except Exception as exc:  # noqa: BLE001 — a storage URI / auth problem, named
        print(f"{'FAIL':<15} outputs storage — {exc}")
        return 1
    # M9: `generate` parsed --vdd / --profile / --iig-template /
    # --playbook-template and then dropped them (the notebook run inside ACFC
    # had to edit config.yaml to select acfc_prx, and its VDD never reached
    # the gate). generate-all has none of these flags: getattr -> None.
    vdd_contract = getattr(args, "vdd_contract", None)
    try:
        vdd_path = _contract_path(vdd_contract, config) if vdd_contract else None
    except FileNotFoundError as exc:
        print(f"{'FAIL':<15} {exc}")
        return 1
    code = _run_pairs(
        pairs, config, only_feed=only_feed, dry_run=args.dry_run,
        skip_tests=args.skip_tests, output_mode=args.output_mode, vdd_path=vdd_path,
        conventions_profile=getattr(args, "conventions_profile", None),
        iig_template=getattr(args, "iig_template", None),
        playbook_template=getattr(args, "playbook_template", None),
    )
    push_outputs()
    return code


if __name__ == "__main__":
    sys.exit(main())
