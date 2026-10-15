# CHANGELOG — ACFC (`feature/multi-table`)

What each version marker changes for a run inside ACFC. Newest first. Values that
must not enter git (storage account, containers, notebook names, status sets) are
named by field only — see `docs/acfc/OVERLAY_FIELDS.md`.

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
