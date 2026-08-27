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

### After 5 PM demo (needs a frontend rebuild — do not do before)

Replace the shell block's SYNTHETIC header in
`ui/frontend/src/pages/ModesPage.tsx` (the `.shell-note` div) with
exactly:

> SYNTHETIC — no landing volume exists in the Hexaware workspace yet;
> creating one (e.g. `soham_workspace.codegen_agent.mftlanding`) is the
> Databricks seam's first write task. Rendered from the FRD's landing
> location and file patterns, not a live listing.

Then rebuild the frontend and restart the server (both frozen until after
the demo).
