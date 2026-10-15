# CHANGELOG — ACFC (`feature/multi-table`)

What each version marker changes for a run inside ACFC. Newest first. Values that
must not enter git (storage account, containers, notebook names, status sets) are
named by field only — see `docs/acfc/OVERLAY_FIELDS.md`.

## 0.5.8.post52 — 2026-10-15 (D1 post51 report: two defects + the pydantic addendum)

1. **Error lines: two tiers, coordinates only in the one a report carries.** The
   post51 report's 4 static-denylist hits were all document text inside
   `first_error_line`. `codegen.run_errors.first_error_line(returncode, stderr,
   stdout)` (same STABLE signature) now returns ONLY fixed vocabulary + integers:
   `FAIL            extract-sttm — STTM audit column invalid at STTM sheet 3 row 4
   col 11 [WorkbookParseError]`. New `first_error_line_full` (same signature) is the
   quoted line, for `codegen-outputs/` inside ACFC only. The CLI pairs every `FAIL`
   line with a `CODEGEN-ERROR {json}` marker on stderr (stage, reason code, `Coord`);
   118 raise sites in the STTM parser, FRD extractor, VDD reader, layout and generator
   attach their position via `run_errors.located(exc, Coord(...), reason)` (message
   text unchanged); an uncaught error gets a marker too. The harness phrases
   `contract not found:`, `no resolved feed matches --feed`, `produced no feeds`,
   `under gaps:` survive in the reason phrases. `scripts/run_round.py` prints the
   coordinates line (the quoted one stays in its work dir); `acfc_run.py` keeps both.
   **Harness side:** keep importing `first_error_line` for the report; write
   `first_error_line_full` only under `codegen-outputs/`.
2. **Emit stages SKIPPED, never PASS, after a failed Generate.** Pairs 03 / 04 / 07
   showed DDL / IIG / DML emit PASS with pair_02's exact unpopulated counts. A generate
   run where anything failed (contract mismatch, template gap, gate verdict FAIL, an
   uncaught error) prints `SKIPPED        <ddl_emit|iig_emit|dml_emit> — upstream
   stage generate failed`, deletes every emit artefact a failed feed wrote or rewrote
   (no partial workbook), keeps the exit code, and writes
   `<output root>/CODEGEN_STAGES.json` (`codegen.run_stages`, STABLE: stage statuses
   + the artefacts this run actually wrote, per feed). **Harness side:** read the
   emit-stage statuses and the workbook to count from `CODEGEN_STAGES.json`
   (`run_stages.read_stage_manifest(out_root)`), never from a glob of the output
   folder — it is shared across pairs, which is how pair_02's workbook was counted
   for pairs 03 / 04 / 07.
3. **The pydantic addendum (pair_07's error line was a warning).**
   a. `layout.model_confidence` is `LayoutConfig.placed_confidence` in Python (YAML key
      kept as alias) with `protected_namespaces=()` on the model; the App's
      `FeedRun.model_usage` (an API key, not renamed) gets `protected_namespaces=()`.
      `tests/test_d1_environment.py` fails on any unprotected `model_*` field at any
      pydantic version.
   b. A Python warning BLOCK is skipped whole: the head line, its continuation (blank
      lines inside the message included — pydantic's own message has one), through the
      indented source line; it ends early at a traceback / error / CLI-label / log line.
   c. Per stage, exit-code first: 0 (PASS) and 3 (NEEDS_ANSWERS) return `None` from
      both tiers — stderr is read only for a FAILed stage.
   The D1 pin set (pydantic 2.8.2, openpyxl 3.1.2, jinja2 3.1.6, pyyaml 6.0.1, ruff
   0.17.0, databricks-sdk 0.30.0) is `constraints/acfc_d1.txt` + §0 of
   `docs/acfc/ENVIRONMENT_ACFC.md`; the suite runs in the dev venv AND `.venv-d1`
   before a push. Under openpyxl 3.1.2 the byte-pinned `.xlsx` fixtures are compared
   cell by cell.

## 0.5.8.post51 — 2026-10-15 (D1 post50 follow-ups)

1. **Run errors: exit code first, warnings never the error** (904178e).
   `codegen.run_errors.first_error_line(returncode, stderr, stdout)` — a STABLE API
   for the harness report writer: exit 0 = no error whatever stderr holds; otherwise
   the first `Traceback` / `FAIL` / `ERROR` / `<Name>Error:` line, Python warning
   lines (and the source line under them) skipped. `scripts/run_round.py` and
   `acfc_run.py` use it. The noise is gone at its source: importing `codegen.config`
   printed two pydantic `UserWarning`s (fields named after BaseModel attributes);
   they are `thresholds` / `db_schema` in Python now, the YAML keys unchanged
   (`extractor.discovery.validate`, `dml.schema`). The CLI also ignores pydantic's
   own deprecation category. **Harness side:** import `first_error_line` instead of
   taking the first stderr line; the leak gate's stderr reading wants the same filter.
2. **Environment profiles D1 / A2 / PR** (a859b6e; QA / PROD renamed A2 / PR).
   Resolution: `--environment-file` > `--environment <name>` (else the default) =
   `codegen-state/environments/<name>.yaml` (outside the tracked tree) laid over the
   overlay block > INPUT_NEEDED. A REQUIRED value (`environment_schema.required`:
   storage account, containers) still unset is `QUESTION run.environment.<key>`,
   **exit 3** (was a non-blocking INPUT_NEEDED). The run banner / report header /
   RUN.md read `environment: D1 (complete, from codegen-state/environments/d1.yaml;
   selected)`. The DQ header / trailer location never formats a placeholder storage
   account. App: each profile's values prefilled and editable, required fields
   marked, "Other…" free text kept. **ACFC side:** put the storage account in
   `codegen-state/environments/d1.yaml` (`config/environments/example.yaml` shows
   the shape) — without it every D1 run now exits 3.
3. **Golden alignment, mechanism only** (5515376). The ACFC-side overlay
   `codegen-state/overlays/<profile>.yaml` (outside the tracked tree) is applied
   right after `acfc_env.yaml`; notebook names / paths / versions, the email status
   default + per-feed status sets, and per-feed SRC_FILE_NAME styles are set there
   (`docs/acfc/OVERLAY_FIELDS.md`; synthetic `config/overlays/example.yaml`). New:
   `notebook_path_prefix` (`/Workspace` in `acfc_env.yaml`), `email_status_default`,
   `feed_overrides.<feed_id>.{email_statuses, src_file_name}`, the `prefix_middle`
   wildcard style. The "dropped" stg_to_std notebook row was `iig_diff` giving both
   notebook rows no flow (the corpus `PROCESS_NAME` shapes matched no rule): two flow
   rules in `tools/iig_keys.yaml`. SRC_COLUMNS left naming and PIPELINE_DESCRIPTION
   row counts are open convention questions (`docs/acfc/OPEN_QUESTIONS.md`), untouched.
4. **Pre-push scrub gate at home** (f6d0412). `tests/test_tracked_scrub.py` scans
   every tracked file under `config/` + `docs/acfc/` and fails only on a (file, hash)
   pair not in the `docs/acfc/LEAK_LEDGER.md` baseline (18 rows = the 68 known hits,
   hashes only; regenerate with `scripts/scrub_check.py --rebaseline`).
   `codegen.term_hash.term_sha256` (strip, casefold, NFC, sha256) is the shared hash.
5. **`tools/hit_lookup.py`** (b95f39c): matches the gate's per-hit JSONL hash
   records against a local, gitignored candidates file — classification at home
   without a term entering git.
