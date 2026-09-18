# Standup notes

## 2026-08-27 — demo-readiness freeze (client demo tomorrow 5 PM)

- Baseline tag: **`pre-demo-2026-08-27`** (= `003c0fe`, EDO standards
  adoption). Rollback point for everything below.
- Part A commits: **`889c008`** on `demo-readiness` (documents card,
  source-files panel + live FRD convention check, synthetic Databricks
  shell block; display-only, config-driven, no new runtime deps), merged
  to `staging` as **`3cb9468`** (no-ff). Not pushed.
- Rehearsal (all passed, verified in Chrome against the rebuilt
  single-port server):
  1. Blank base state — none chosen, Generate disabled, LIVE badge with
     key present.
  2. Documents card green with all three reference documents present by
     name (scanned via `CODEGEN_INPUT_DOCS_DIR` from the gitignored
     `.env`).
  3. Source-files table renders for the CV golden FRD with SYNTHETIC
     badges; Convention check block shows the real FRD 1005310 values
     read live from the docx.
  4. Shell block renders; collapse/expand works.
  5. Choose STTM → confirmed live run (`demo_20260827_142427`, ~$0.10) →
     three CV feeds PASS_WITH_FLAGS. Mock reports and `out/` trees
     byte-identical between the tag and HEAD; live artifacts identical to
     the 2026-08-26 live run modulo contract-sha/date stamps and Layer-2
     candidate wording (inherently non-deterministic).
  6. Clear → back to none chosen.
- Tests 153→169 passed (27 skipped unchanged), ruff clean.
- Server running from staging @3cb9468; no frontend rebuild before the
  5 PM demo.
  - **Correction (state of this machine):** the rehearsal server was
    stopped during Part A cleanup, before the freeze was declared. It is
    being started by hand (detached from the Claude Code session, so it
    survives the session ending) — the built frontend at
    `ui/frontend/dist` is the frozen 3cb9468 build; no rebuild needed
    or wanted.
- B0 Databricks discovery done (read-only, `--profile DEFAULT`) and
  committed as `docs/DATABRICKS_DISCOVERY.md` (`docs: Databricks
  workspace discovery (B0, read-only)`), hostname/principal redacted.
- **Option A chosen** for `demo.databricks_paths`: keep
  `hexaware_demo/landing/mft` placeholders; do not point at `frd_raw`.
- **B1 pending explicit go** after the 5 PM demo — nothing beyond B0 in
  this session.

- **Freeze amendment (2026-08-27, on explicit instruction):** one frontend
  change was made and rebuilt before the demo — the documents card's
  green-state note now reads "Drives the generator's naming, path and
  structural checks via config" (the old "Read by …" wording overstated
  runtime behavior; the standards enter via reviewed config transcription,
  not document parsing). The running server picked up the new bundle
  (`index-BQUJNkmp.js`) without a restart. `dist/` is now the staging
  HEAD build, no longer the literal 3cb9468 bundle; everything else,
  including the shell-header text below, remains deferred.

## 2026-08-28 (early) — seam's first write task DONE

- `soham_workspace.codegen_agent.mftlanding` created and seeded with 4
  SYNTHETIC files (~27 KB, from the resolved demo spec; manifest in
  `out/_seed_manifest.json`) by `codegen databricks-seed-landing --apply`
  (typed confirm given). The shell block is **LIVE** (green header, real
  names/sizes/timestamps) with the synthetic renderer as the honest
  fallback (`demo.shell_listing: auto`; creds-pulled rehearsal showed
  SYNTHETIC + one-line reason). Write surface is exactly
  {ensure_volume, upload_file}, prefix-guarded to
  soham_workspace.codegen_agent.* — no deletes exist. This ticks the
  Option A header's "seam's first write task".
- **Push rule re-armed (Soham)**: no `git push` without a typed go in the
  same session. (One prior push — main, after "merge to main" — was on
  inferred rather than literal instruction; disclosed.)

## 2026-08-27 (late evening) — go B1 + Option B framework output

- **B1 merged** (`fc62008`): warehouse/serving/catalog surface on the
  Databricks seam (EXPLAIN-only, no execute/create_job/run_now — suite-
  enforced), `databricks_fmapi` Layer-2 provider (transport only; Anthropic
  stays default), Option A shell-header applied and serving. Live smoke
  (describe_table + one ≤50-token chat) **pending explicit cost
  confirmation** — nothing billed yet; the warehouse stayed asleep.
- **Option B merged**: `output.mode notebook|framework|both` — framework =
  DDL workbook + config rows (approval artefact, from the metadata-sheet
  layout) + dialected inserts + ADDITION.md under `out/<slug>/framework/`;
  verdicts identical across modes; Option A guarded byte-for-byte by
  `tests/snapshots/notebook_mode.json`; UI Output selector + results
  downloads. **Master-notebook question RESOLVED (Soham, 2026-08-27): the
  master notebook is ACFC's own existing notebook — the generated DDL +
  insert SQL are add-ons to it; the agent never produces or edits the
  notebook itself.** Artefact/UI/talk-track copy updated to say so.

## 2026-08-27 (evening) — post-freeze additions, all merged to staging

On explicit instruction, the freeze was superseded by further feature
work; the server was rebuilt/restarted several times and now runs staging
HEAD (blank base state). Landed, in order: metadata-sheet preview
(`202ac06`), documents card note fix (`bb81d41`), Databricks volumes seam
+ input-requirements check (`be96156` — client FRDs/STTMs uploaded
un-anonymized to `soham_workspace.codegen_agent.{frd_raw,sttm_raw}` on
explicit instruction, fetchable via `codegen databricks-fetch` and the
STTM chooser), and all four reference documents consumed in request-time
checks (`8a0daf4`). Suite 170 → 207 passed / 27 skipped; generation
byte-identical throughout (tags `pre-demo-2026-08-27`, `post-mgr-demo`).
B1 (warehouse/EXPLAIN/FMAPI/UC-grounding) remains gated on explicit go.

### ~~After 5 PM demo~~ — DONE 2026-08-27 evening (go B1 §0): the Option A
### shell-header text below is applied, rebuilt and serving.

Replace the shell block's SYNTHETIC header in
`ui/frontend/src/pages/ModesPage.tsx` (the `.shell-note` div) with
exactly:

> SYNTHETIC — no landing volume exists in the Hexaware workspace yet;
> creating one (e.g. `soham_workspace.codegen_agent.mftlanding`) is the
> Databricks seam's first write task. Rendered from the FRD's landing
> location and file patterns, not a live listing.

Then rebuild the frontend and restart the server (both frozen until after
the demo).

2026-09-16: gate.ruff runs `python -m ruff` at runtime but ruff is declared only in [dev]; a plain .[ui] install produces FAIL verdicts on every feed. Shipped zip patches pyproject [ui]; fix in source next.
