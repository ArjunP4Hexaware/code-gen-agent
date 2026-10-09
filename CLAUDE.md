# CodeGen / Data Engineer Agent — working notes

## START HERE — branch `feature/multi-table` (state as of 2026-10-09, early morning — after the overnight robustness run)

**Where things stand.** Four live branches, all pushed, nothing merged
anywhere (staging / main untouched):

| Branch | Head | Version | What it is |
| --- | --- | --- | --- |
| `feature/multi-table` (this checkout) | **this notes commit** (on 5cbaf63) — **PUSHED 2026-10-09 on Soham's word** (29 commits since 1ecbacd) | 0.5.8.post26 | cut from `feature/iig-first` at be38f05: the multi-table IIG model + `metadata_inserts.sql`, the first-ACFC-run fixes, the real-row scorecard rules, the exit-code / answer-line contract, then the **2026-10-09 overnight robustness run** (below). **Not yet re-run in ACFC** |
| `acfc/harness-exit3` | **9cba013** on origin; local **a6b8002** (the `band[n]` key form, NOT pushed — Soham pushes it with the Genie-side regex change) | docs only | `docs/acfc/HARNESS_EXIT_CODES.md` — the ACFC harness's (codegen-watch / pull_and_run, NOT in this repo) exit-code + answer-line contract. **Genie implements the harness from this doc**; ACFC-side commits land here too (517919c was theirs) — `git fetch` and fast-forward before editing (edit in a scratch worktree, never switch this checkout) |
| `feature/iig-first` | **be38f05** | 0.5.8.post13 | the stable demo branch `codegen-watch` pulls — **do NOT merge `feature/multi-table` into it until after the Friday 2026-10-09 session, and only on Soham's word**. Its notes (next section) still apply |
| `backup/ddl-only` | **4acec93** | 0.5.8.post5+ddl2 | DDL-only demo fallback (next section) |

**Overnight 2026-10-08 → 10-09 (read `docs/acfc/OVERNIGHT_2026-10-09.md` first).**
Robustness to unseen documents, four chunks + an addendum, all local:
- **Chunk A** — STTM target bands located by their LABEL GROUP anywhere in the
  header row; a band's layer ONLY from evidence (answer > band title > header
  word > Catalog values PR_DLK/PR_STD > Schema prefix stg_ > elimination;
  "in DL"/"DLK" OFF — `extractor.discovery.layer_evidence`); a band nothing
  names = `UNRESOLVED <sheet>/band[<n>]/layer` (answers: `{sheet, layer:
  band[n], role: layer, value: source|stage|standard}`), its feed held back;
  value-derived layers re-derived on every cache hit; classifier = STTM only
  with target-layer evidence ("unclassified — confirm" otherwise). Pass 1 (the
  old band-row reading) wins when it agrees, pass 2 only when pass 1 finds no
  mapping sheet — every pinned profile byte-identical. `MAPPING-` sheets read
  by the GENERAL reader first, proven equal to the legacy reader on every
  fixture (`tests/test_mapping_general_first.py`); legacy text only at
  `parse_workbook`. `docs/LAYOUT_RECOGNITION.md` "Band location by label group".
- **Chunk B** — six cold pairs (`fixtures/acfc_shapes/cold/`, designed blind to
  the reader) + the generator fixes they forced (pass-3 candidate sheets,
  prose FRDs, held-back instead of FAIL, answer ROUNDS in layout /
  extract-sttm, FRD format-cell delimiter, `feeds[i].audit_columns`, …);
  `tests/test_cold_pairs.py` pins every owed line and that answers complete.
- **Chunk C** — the App: run state `needs_answers` with an inline answer list
  + `POST /api/demo/rerun-with-answers`; band questions answerable in the
  dialog; every error a readable card (JSON: type, `where`, health line).
- **Chunk D** — `metadata_inserts.sql` table names via `dml.table_names` (STGDELTA →
  `stg_delta_stddelta_ingestion_details` confirmed from Soham's brief; the
  rest `-- unconfirmed` + Friday 12); STGDELTA row paths container-relative,
  OBJECT_ID per (group, file) with notes, SRC_CONTAINER_NAME left OPEN (offered
  candidate only); `acfc_env.yaml` makes acfc_prx + iig_v2 the defaults and the
  CLI's first line / `codegen doctor` name the active profile + template.
- Every chunk independently reviewed; every verified finding fixed (one commit
  each). Decisions left for Soham: the report's "Decisions for you" (1–5).
- **Elimination (owner rule, 5cbaf63):** source by elimination ONLY for the one
  band left over, with no evidence, LEFT of both evidenced target bands, while
  source is unclaimed — a layout `NOTE <sheet>/band[n]/layer … layer by
  elimination`; any other leftover stays `UNRESOLVED`; never trusted from cache.

Working tree clean after the overnight report commit. Before tonight: the last four commits
before it are Soham's own from the ACFC side (2026-10-08 17:16–18:12 UTC):
6f14a2d `app.yaml` ACFC env block (the four storage paths are SET on this
branch now — `CODEGEN_EXTRA_INPUT_DIRS` / `_STORAGE_INPUTS` / `_STATE` /
`_OUTPUTS` under a workspace user folder; `CODEGEN_CONFIG_OVERLAYS` dropped,
`acfc_env.yaml` loads anyway), adac4ec / bb5fa55 / 51103de review
deliverables of a real SD feed force-added under `docs/acfc/review/` (DDL,
metadata_inserts, config_rows / config_inserts, IIG + IIG_REVIEW; scrub-clean
at 51103de; client-derived — read in place, never quote names). Others can
push here: `git fetch` before work and rebase, never force. Gitignored here
(local only, never stage): `docs/acfc/denylist_local.txt`, `PROJECT_HANDOFF.md`,
`CODEGEN_INDEPENDENT_REVIEW.md`. Stage files explicitly — never `git add -A`.
The real client SD documents + `IIG test cells.xlsx` sit at the repo root
(gitignored / tracked-before-policy): read in place, mock runs only, outputs to
a scratchpad, report SCORES only — never copy names into the repo, commits or
replies.

**FIRST, pick up here (pending, in priority order):**
1. **Friday 2026-10-09 working session with the framework owners** — brief
   `docs/acfc/FRIDAY_2026-10-09.md`; checklist `docs/acfc/MULTI_TABLE_DESIGN.md`
   §7a: 1–5 open questions, 6–8a which family convention is current for new
   feeds, 9–10 sheet vs walkthrough (ACTIVE_FLAG Y/S, DAY_OF_SCHEDULE 0/NULL —
   cited BY NUMBER in `metadata_inserts.sql` and its tests; never renumber),
   **11 (confirm, not ask): "FREQUENCY = run cadence, delivery cadence noted —
   correct?"** Most answers land as CONFIG (`catalog_map`,
   `constants.STGDELTA_STDDELTA_INGESTION_DET`, `family_conventions.*`,
   `dml.db_value_map`, `dml.db_null_columns`). Record each answer in §7a.
   NEW tonight: items **12** (the unconfirmed metadata-DB table names) and **13**
   (STGDELTA source path form, the offered stage container, OBJECT_ID per
   file vs per table), plus the report's "Decisions for you".
2. **Re-run the real documents in ACFC on 0.5.8.post26** (the harness pairs;
   push first — on Soham's word).
   Expectation from a local MOCK run of the real SD pair: all three SD rows
   diff 0 (demographic / community-risk matched 43, individual-risk 46); the
   3 RECYCL cells of the two recycle-less feeds are OPEN (Engineer-confirm) by
   design ("never an asserted N"). Re-run recipe (scratchpad scripts are gone
   with the session — rebuild): layout --frd-contract-out --answers (the one
   open question: `gaps: feeds[1].file_name_patterns` = the community-risk
   file) → extract-sttm → generate `--output-mode framework --profile acfc_prx
   --iig-template iig_v2 --skip-tests --dry-run`, env PYTHONUTF8=1,
   CODEGEN_FORCE_MOCK_LAYOUT/PROVIDER=1, CODEGEN_STORAGE_OUTPUTS/STATE to a
   scratch dir; then `scripts/iig_scorecard.py --generated <feed>_IIG.xlsx
   --real "IIG test cells.xlsx" --real-table <table>` per feed.
3. **Harness side (Genie, from the doc on `acfc/harness-exit3`)**: exit 3 never
   stops a pair; stdout scanned for QUESTION / UNRESOLVED at the end of every
   pair; a later stage's exit 1 reclassified as NEEDS_ANSWERS ONLY for a
   missing-input first-error line (`contract not found:`, `no resolved feed
   matches --feed` / `produced no feeds`, `under gaps:` / `NEEDS_ANSWERS`),
   else FAILED with first_error + needed keys. Ask the harness owner also to
   allow-list its own keys in the leak gate (older runs on
   `origin/acfc-results` were `LEAK_GATE_BLOCKED` false positives — read in
   place, never check out, never quote names).
4. **Open choices left for Soham:** `extract-vdd` exit 3 (doc says planned, not
   implemented — VDD gaps are flags); optional-column ambiguity can only arise
   once client headers are added to the synonym tables (the shipped vocabulary
   has no shared synonym).
5. **The `feature/iig-first` pending items still apply** (next section): the
   four ACFC `app.yaml` paths — DONE on this branch (6f14a2d), still pending on
   `feature/iig-first` / `backup/ddl-only` (never guess them) — the after-demo untrack /
   purge of the real reference files, splitting `acfc_env.yaml` per source
   family — `acfc_env.yaml` now pins the SD / CAQH family for EVERY feed
   (SCHEMA_DRIFT_FLAG Y, `src_file_name: prefix_star`, the four SD audit
   columns, recycle open, the RECYCL path shape), so a PRX-shaped real feed
   needs a feed overlay on top.

**Verified at 1bb8302 (overnight, marker 0.5.8.post26):** 1164 passed / 27 skipped
(Python 3.11) and 1163 / 28 (Python 3.10); ruff clean (`src/ tests/ ui/backend/
scripts/iig_scorecard.py`); tsc clean, vitest 29 passed, `ui/frontend/dist`
identical to a fresh build (`index-CHt2wtuJ.js`); scrub 0 on every line added
since 1ecbacd (+ the binary fixtures' text); the real SD pair (mock) unchanged
— matched 43 / 43 / 46, diff 0. (Before tonight, at 0e7358e: 1004 / 27, marker post25.) `tests/snapshots/notebook_mode.json` re-based in 0c2ba13 (37
hashes: `ruff format` rewrites every emitted .py before the ruff gate).

**What the branch does** (design + status: `docs/acfc/MULTI_TABLE_DESIGN.md`;
the night's and the cleanup's record: `docs/acfc/OVERNIGHT_2026-10-08.md`):
- **Row rules.** Tables = the distinct (catalog, schema, table) triples of each
  STTM band; files = the distinct patterns, a `<LOB>` pattern expanded per
  listed LOB. ADLS rows = files (into the detail table), STGDELTA rows =
  tables, `DATA_QUALITY_RULES` keyed per file (+ the header / trailer split row
  only when they are their own tables), schedule = four structural rows when no
  inventory overlay supplies them, OBJECT_ID = 1..n within the group.
- **Catalogs.** STTM band → FRD label → `default_catalog`, a disagreement =
  `catalog_conflict:<layer>`; `conventions.catalog_map` maps logical catalogs
  (case-insensitive keys, lowercase output; `acfc_env.yaml`: PR_DLK → d1_dlk,
  PR_STD → d1_std).
- **Feed families** (`metadata.templates.iig_v2.family_conventions`): `lob`,
  `stgdelta_unknown_primary_key`, `stgdelta_object_name` (+ `_literal`),
  `schema_drift_flag` (ADLS; was an overlay constant until 0e7dbc3). Shipped
  default = the PRX family (blank / `NA` / generalized pattern / `N`); pair 1's
  overlay pins PRX (+ the literal `Accumulator_accumclient`); pair 4's overlay
  and `acfc_env.yaml` pin the SD / CAQH-style family (codes / blank /
  generalized pattern / `Y`). Neither golden is edited to fit the other.
- **`framework/metadata_inserts.sql` = the client's "DDL"**, written on EVERY
  framework run: one INSERT per IIG row, an open cell = an unquoted
  `<<COLUMN#n>>` placeholder (the script does not parse until filled). The
  header states the three workbook → database rules: (1) value map
  `dml.db_value_map` (ACTIVE_FLAG / ACTIVE_RULE_FLG Y → S), (2) forced NULL
  `dml.db_null_columns` (DAY_OF_SCHEDULE, UDF2–5, the SLA columns,
  CLAIM_TYPE_ID), (3) audit defaults (`GETDATE()`, `@RFC_NUMBER`) +
  placeholders. Guards before the first INSERT (RFC assigned, every
  placeholder id not NULL, PIPELINE_ID / GROUP_ID / key unused), the file
  connection reuse-or-insert (a NULL host with no id aborts), all inside
  `SET XACT_ABORT ON` + TRY / TRANSACTION / CATCH ROLLBACK THROW. Gate check
  `metadata_inserts`. `emit_dml` / `dml.enabled` gate ONLY the runner notebooks
  `Insert_scripts_config_table_<env>.py`. **`config_inserts_<env>.sql` is
  RETIRED** (e02defa, after its DB-side rules were ported; every remaining
  old-vs-new difference is in the overnight report); `config_rows.xlsx` stays
  the approval artefact. The CREATE reference text is one block per table.
- **Scorecard** `scripts/iig_scorecard.py --all-sheets`: rows paired by key,
  a score per sheet + TOTAL, each line ending `| matched / open-by-design /
  open-for-engineer / diff; score excl. open-by-design` (pair 1: 57.9 raw,
  83.8 excl.); `--real` also reads a golden in the `IIG_EXPECTED.yaml` shape.
  Both-blank cells count as MATCH.
- **Fixtures.** Pair 4 = `fixtures/acfc_shapes/pair_4/` (synthetic "Northwind
  Benefits", feed `nb_cob_report`, three tables, six LOB files), hand-written
  golden `golden/IIG_EXPECTED.yaml` (`tests/test_pair4_full_golden.py`); its
  walk-through scores TOTAL 100.0 under the shipped overlay. Pair 1: every IIG
  cell pinned (`tests/test_m4_acceptance.py` FULL_OPEN / FULL_SEQUENCE /
  FULL_DEVIATIONS — the 9 deviation columns are the 21 scorecard diffs).

**Commits (oldest first):** e76496a, 79ed3d7 Phase A / B · e64539b step 1 ·
12a401a step 2 (`catalog_map`) · 2a67c91 catalog precedence · 0c85b39 step 3 ·
0a6efd7 step 4 · 9685f97 step 5 (post15) · 8b94b9e chunk A · 686aad9 step 7
(scorecard) · 4fa9e78, eb9ff00 step 6 (`metadata_inserts.sql`) · 54ecaad chunk D
(post16) · e02defa cleanup (post17) · ff3c420 Friday brief (post18) · 10806a6,
68fea24, 73f69fa pair-4 SCHEMA_DRIFT_FLAG Y · 0e7dbc3 `schema_drift_flag`
convention (post19) · d84e2a6 item 8a · **2026-10-08:** a376ccf first ACFC
run's four defects (post20) · 0c2ba13 real-row scorecard's nine rules (post21)
· cd18ec1 answer lines + exit-3 branches + FREQUENCY = run cadence (post22) ·
2bece72 `layout --require-complete` exits 3 (post23) · 84edab9 the harness's
own `_NEEDED_KEY_RE`, keys verbatim (post24) · 5192895 QUESTION / UNRESOLVED
reserved for answers owed, NOTE informational (post25) · 0e7358e layout-gaps
test (2 optional + 1 required unplaced).

**Today's rules in one place** (details: `docs/ACFC_DEPLOY.md` "What
feature/multi-table adds" + "CLI exit codes"):
- *First ACFC run (post20):* the Detail key resolved by (segment, field name),
  `key_column_not_in_table`; FILE_DETAILS annotation rows skipped
  (`file_details_annotation_skipped`); blank Schema / TableName → File Details
  target / FRD / layer convention (`sttm_target_missing`), else the feed is
  held back NEEDS_ANSWERS with its `gaps:` key (`SttmContract.needs_answers`);
  paths normalised (`path_normalised`); ruff safe fixes (`ruff_fixed`).
- *Real-row scorecard (post21/22):* delimiter is a character
  (`delimiter_from_extension`); OBJECT_NAME drops trailing date tokens;
  SRC_FILE_NAME / audit columns / RECYCL by family convention
  (`src_file_name`, `audit_columns`, `audit_type_case`, `recycle_unstated`);
  SOURCE = vendor display name; SRC_DATA_TYPE `String:<target>`
  (`src_type_coerced_string`); FREQUENCY = run cadence
  (`frequency_delivery_differs`); `spark_unavailable`; `ruff format` before the
  gate (`ruff_formatted`); one `vdd_scope_mismatch`.
- *Exit codes:* 0 ok, 1 failed, 3 NEEDS_ANSWERS — `layout --require-complete`
  with an owed item open; `extract-sttm` only when NO feed is usable (else 0,
  contract written, QUESTION lines still printed); `generate` only when a feed
  asked for (`--feed`) is held back. acfc_run.py summarises codes + lines.
- *Answer lines:* `f"{label:<15}{key} — {reason}"` (`cli.answer_line`, key
  verbatim). QUESTION (a `gaps:` / `pairing:` value) and UNRESOLVED (a
  REQUIRED column, `<sheet>/<layer>/<role>`) ONLY for answers owed
  (`cli._owed_key`); everything informational is `NOTE`. The harness's
  `_NEEDED_KEY_RE` (copied verbatim in `tests/test_harness_answer_lines.py`)
  matches QUESTION / UNRESOLVED only. Clean pairs 1 / 4 print none
  (`tests/test_answer_labels.py`); `tests/test_layout_gap_labels.py` pins
  2 NOTE + 1 UNRESOLVED → exit 3, answered → 2 NOTE, exit 0, zero keys.

**Gotchas learned on this branch:**
- **Bash heredocs on this box mangle escapes and backticks** (an escaped tab /
  newline became a real one, a backtick body aborted bash): write patch scripts
  with the Write tool and run them as files; check `git diff --stat` after.
  **Commit messages too:** a backtick inside `git commit -m "…"` runs as a
  command (5192895's message lost a phrase) — write the message to a file and
  use `git commit -F`.
- **`fixtures/** -text` commits fixture bytes raw.** Python `write_text` /
  text-mode `open` writes CRLF on Windows and Git Bash `sed -i` can turn CRLF
  into LF — either churns a whole fixture file (10806a6 → fixed in 73f69fa).
  Patch with `read_bytes` / `write_bytes`, keeping each file's own EOL; check
  `git diff --cached --stat` before committing; read index EOLs with
  `git ls-files --eol` (`git show rev:path` applies the checkout conversion).
- **The CLI loads the operator's local `.env`** (only names not already set),
  and its notification DL carries the client email domain into EMAIL_TO →
  scrub hits in CLI output. For a shareable run, `export
  CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` first.
- **The suite runs with `CODEGEN_SKIP_ENV_OVERLAY=1`**, so a fixture overlay
  must carry every environment / family value its golden relies on (the pair-4
  overlay mirrors `acfc_env.yaml`'s shape); a CLI run applies `acfc_env.yaml`
  first, then `CODEGEN_CONFIG_OVERLAYS`.
- **`isolation: "worktree"` agents branch from the default branch**, not HEAD
  — reset each to the working branch before it starts; cherry-pick its commits
  back and delete its `worktree-agent-*` branch afterwards.

## Parent branch `feature/iig-first` (state as of 2026-10-07, end of day — the demo branch)

**Where things stand.** Two live branches, both pushed, nothing merged
anywhere (staging / main untouched):

| Branch | Head | Version | What it is |
| --- | --- | --- | --- |
| `feature/iig-first` | **9da340a** (be38f05 = this docs block) | 0.5.8.post13 | cut from `fix/remove-mock-provider-ui-text` at e89a263 (M15e — that branch's notes below still apply); IIG-first M1–M3 (6291cb5 … 3f44dc8) made every `acfc_prx` framework run write `<feed>_IIG.xlsx` (clean) + `<feed>_IIG_REVIEW.xlsx` (review); then the 2026-10-07 work below. `codegen-watch` inside ACFC pulls it |
| `backup/ddl-only` | **4acec93** | 0.5.8.post5+ddl2 | DDL-only fallback for the demo: `origin/fix/remove-mock-provider-ui-text` (e89a263, descended from tag `v0.5.8-acfc` 3a5b85d) + version bump + `config/overlays/acfc_env.yaml` with ONLY the `acfc_prx` default_catalog (NO auto-load there — `CODEGEN_CONFIG_OVERLAYS`) + the health probe below. `docs/acfc/BACKUP_DDL_ONLY.md`. Suite 740 passed / 28 skipped |

Working tree clean at 9da340a (only the untracked `docs/acfc/denylist_local.txt`).
A worktree of `backup/ddl-only` lived in the 2026-10-07 session scratchpad
(gone with it): recreate with `git worktree prune` then `git worktree add
<dir> backup/ddl-only`; copy in the gitignored fixtures (SFMC contracts, the
raw pair-1 IIG golden under `docs/acfc/rfc_capture/…/goldens/pair_1/`) and run
with the main `.venv` + `PYTHONPATH="src;."` (export
`MSYS2_ENV_CONV_EXCL=PYTHONPATH`). A fresh Windows checkout CRLF-converts
`docs/acfc/rfc_capture/…/goldens/pair_1/ACCUM_DDL.txt` (no `-text` rule outside
`fixtures/**`) and fails one fixture test locally — re-check it out with
`git -c core.autocrlf=false checkout -- <file>`.

**FIRST, pick up here (pending, in priority order):**
1. **The four ACFC workspace paths for `app.yaml` (both branches).** The
   Git-deployed App finds no documents because the committed `app.yaml` had no
   env block. Both branches now carry `env:` with
   `CODEGEN_CONFIG_OVERLAYS=config/overlays/acfc_env.yaml` and the four
   `CODEGEN_EXTRA_INPUT_DIRS` / `CODEGEN_STORAGE_INPUTS` / `_STATE` / `_OUTPUTS`
   entries **commented out as PENDING** — Soham's brief carried placeholders,
   not values; never guess them. When he sends them: uncomment on BOTH
   branches (comment says ACFC paths committed on explicit instruction), bump
   the marker, suite, push. Grants + how to find the App's principal:
   `docs/ACFC_APP_ENV.md` (a fresh Git deploy may mean a new App = a new
   service principal → re-share the folders).
2. **ACFC harness results are `LEAK_GATE_BLOCKED`.** `origin/acfc-results`
   (read in place with `git show`, never check out, never quote names): every
   10-pair run of this branch on 2026-10-07 (d8b2f29 ×2, 50a510e, ca6bab8)
   is a 4-field stub — `status: LEAK_GATE_BLOCKED, hit_count: 4`, no pairs,
   no env, no log — so it says nothing about pass/fail. The only detailed
   result (2026-10-05, 39653aa, 1 pair) was leak-gate CLEAN (0/197),
   installed 0.5.8.post6 = the tree, generate/ddl/iig/dml FAIL, error null.
   **Hypothesis (unverified):** the 4 hits are the overlay's four
   environment names (two catalogs, two containers) now in the DDL / IIG.
   Test: re-run the harness on this branch with `CODEGEN_SKIP_ENV_OVERLAY=1`;
   0 hits → it is a leak-gate allow-list decision; else ask the harness owner
   for the per-pair stages with only the hit terms redacted.
   **Update 2026-10-09:** that run happened (784e110) — pair-level results and
   the redactions inside the harness's own keys are summarised in the
   `feature/multi-table` START HERE above, item 2.
3. After the demo (scheduled, Soham's call): untrack / purge the real
   reference files (see "Open / scheduled" below); split `acfc_env.yaml` per
   source family.

**Verified at 9da340a:** 818 passed / 27 skipped (Python 3.11, full suite);
ruff (`src/ tests/ ui/backend/`), tsc clean; vitest 15 passed; scrub 0 over
every changed file; `ui/frontend/dist` rebuilt (`index-CS2UgojU.js` + map).
The IIG / metadata / framework files also pass with lxml installed (the local
`.venv` has NO lxml — install it to a scratch `--target` dir and put it on
`PYTHONPATH` to reproduce lxml-only bugs). Version marker **0.5.8.post13**
(pyproject + requirements.txt — bump BOTH on every push that changes `src/`
or `ui/`).

**What 2026-10-07 changed (oldest first):**
- be4c6e4 — `stable_workbook_bytes` replaced the whole `<dcterms:modified>`
  element and dropped the `xmlns:xsi` openpyxl declares ON it under lxml →
  every IIG xlsx unreadable in ACFC. Only the timestamp text is replaced now;
  round-trip tests (`test_every_iig_workbook_round_trips_through_openpyxl`).
- 44e74a9 / d0afec7 (+ the overlay-order commit after 58ed330) —
  **`config/overlays/acfc_env.yaml` is COMMITTED and ALWAYS applied first by
  `load_config`** (`codegen.config.overlay_paths`); `CODEGEN_CONFIG_OVERLAYS`
  ADDS overlays on top (later wins, a duplicate applies once); opt out only
  with `CODEGEN_SKIP_ENV_OVERLAY=1`. stderr `config overlays (in order): …`;
  the App's startup line and `GET /api/health` (`config_overlays`) list them.
  **`tests/conftest.py` sets `CODEGEN_SKIP_ENV_OVERLAY=1` at import** so the
  suite stays on the shipped config — a test that wants the overlay passes
  `overlays=[…]` or unsets it. Content: `acfc_prx.default_catalog {stage: d1_dlk,
  standard: d1_std}`; six ADLS_DELTA constants (connection ids 7/4/2,
  `mftlanding`, `z-use-d1-dlk-stage-01`, SCHEMA_DRIFT_FLAG Y) with
  `constant_citations`; `always_blank` minus the five connection/container
  columns (lists REPLACE on merge); `src_columns_style: named`; four SDOH
  path shapes with `path_citations`. **It applies to EVERY ACFC feed** —
  PRX-shaped feeds (pair 1) get SDOH paths until it is split per source
  family. Documented in `docs/ACFC_DEPLOY.md` §2.
- 13e93bd … 0e14ce7 — iig_v2 derivations in `src/codegen/metadata_template.py`
  (tests: `tests/test_iig_v2_derivations.py`): (a) STGDELTA SRC_/TGT_CATALOG_NAME
  follow the DDL chain (the run's profile is threaded through
  `metadata_sheet_payload(conventions_profile=)` → `template_tab_rows(profile=)`);
  (b) TGT_LOAD_OPTION via `_REFRESH_TYPE_BY_STRATEGY` (Truncate and Load →
  Overwrite); (c) FREQUENCY token (leading word, else the only token, else
  open); (d) `{landing_rel}` / `{domain_path}` placeholders (shipped shapes
  unchanged, test-pinned); (e) `src_columns_style: named`; (f) HEADER/FILE_
  HEADER/FILE_FOOTER flags only from FAQ `has_header`/`has_trailer`, and ONLY
  for delimited files — fixed-width keeps the old reading because the pair-1
  golden's flags contradict segment semantics.
- 4b0c1ce / 984ab92 — `scripts/iig_scorecard.py` (+ `tests/test_iig_scorecard.py`):
  MATCH / ALIAS / OPEN / DIFF per real column; never prints CREATED_BY /
  UPDATED_BY; data types caseless; LOB ALIAS only when the generated row is
  the anonymised fixture.
- `docs/acfc/IIG_SCORECARD_2026-10-07.md` — scorecard output, cell provenance,
  open cells + owners, remaining DIFFs, and the exact ACFC run commands for
  the Socially Determined (MIDS) pair.

- 50a510e and the commit after it — **stale-install immunity**: the App
  (`ui/backend/__init__.py` loads `src/codegen/_srcpath.py` by path:
  `ensure_src_first()`; every child launch — docindex parser, gate ruff /
  pytest, acfc_run.py — passes `env=_srcpath.child_env()`,
  startup line `codegen source: …`, `GET /api/health`), the CLI (first line
  `codegen <v> from <file> · overlays: …`, `codegen doctor`), `acfc_run.py`
  (`launch_codegen` with `PYTHONPATH=<repo>/src`, root from its own location),
  `run_meta.json` `codegen`, the report's `- Produced by:` line (stripped
  from the notebook-mode snapshot hash — it names the checkout). Tests:
  `tests/test_app_imports_tree_src.py`, `tests/test_cli_launch_tree_src.py`
  (decoy `codegen` ahead on PYTHONPATH). docs/ACFC_DEPLOY.md "Which codegen runs".
- ca6bab8 — one src-first rule, `src/codegen/_srcpath.py` (stdlib, loadable
  BY FILE PATH before any `import codegen`): `ensure_src_first()`,
  `child_env(extra=None, base=None)`, `load_by_path()`. Launch sites that pass
  `env=child_env()`: `ui/backend/docindex.py` `ParserProcess._start` (also
  calls `ensure_src_first()` first), `gate/preflight.py` (ruff),
  `gate/tests_runner.py` (pytest), `acfc_run.py` `launch_codegen`
  (`srcpath_module`). `codegen-watch` is NOT in this repo — it must put
  `PYTHONPATH=<repo>/src` first itself.
- 2c3c6d4 — **ruff is a BASE dependency** (every install: `.`, `.[ui]`,
  `.[databricks]`); a missing ruff module is the gate flag
  `ruff_unavailable — <reason>` (GateCheck.flag), PASS_WITH_FLAGS, never FAIL;
  any other reason ruff did not run keeps `check_not_run:ruff`
  (`tests/test_ruff_dependency.py`).
- 9da340a (cherry-pick of backup 4acec93) — **self-diagnosing storage roots**:
  `ui/backend/health.py` probes every root the App reads
  (`CODEGEN_EXTRA_INPUT_DIRS` entries + `CODEGEN_STORAGE_INPUTS/_STATE/_OUTPUTS`):
  readable / empty / not_shared (names the App's principal + the grant: Can
  Read pairs, Can Manage roles) / unset / invalid / error / timeout; read-only
  (`exists` then `list` — a remote `list` answers `[]` for a root it cannot
  see). `GET /api/health` here = version, codegen_source, codegen_file,
  config_overlays, startup_error, **principal, roots**. The document chooser's
  empty state shows the table (`components/StorageRoots.tsx`). Tests:
  `tests/test_health_probe.py`. Docs: `docs/ACFC_APP_ENV.md`.

**Current scorecard** (CV golden pair, committed overlay, vs the real
`demographics_package` row): `filled 38/55, matched 33, alias 8, open 10 (BSA
5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 4`. Remaining DIFFs:
OBJECT_NAME / SRC_FILE_NAME (fixture file pattern), SOURCE ("(CV)" suffix),
TGT_PRIMARY_KEY (`NULL` real vs `zip_code` — kept as DIFF: a framework-team
question). Re-run: generate the CV pair (`fixtures/contracts/FRD_demo_cv_golden
.contract.json` + `sttm_mapping_contracts_cv_golden.json`, `--feed
cv_community_demographic_risk --dry-run --skip-tests --output-mode framework
--profile acfc_prx --iig-template iig_v2`, outputs via
`CODEGEN_STORAGE_OUTPUTS=local:<scratch>`), then `python scripts/iig_scorecard.py
--generated <…>_IIG.xlsx --real "IIG test cells.xlsx" --real-table
sd_community_demographic_risk`.

**Open / scheduled — do not act without Soham:**
- **Real client reference files are TRACKED and on origin**: `IIG test
  cells.xlsx` (705e332 — real CREATED_BY user ids), `d1_d1k.stg_doh/`,
  `d1_std.sdoh/` (note the real folder names) and
  `sd_community_demographic_risk.lvdash.json` (17d1300, e27ef7f), committed
  from ACFC before this session. `.gitignore` now lists them, which does NOT
  untrack them. Untracking / history purge is **scheduled for after the
  demo** — `git rm --cached` would delete them from the ACFC checkout on its
  next pull. Read them in place; never print CREATED_BY / UPDATED_BY.
- Split `acfc_env.yaml` per source family (SDOH vs PRX path shapes).
- The CV FAQ leaves `has_header` / `has_trailer` unanswered → the three flag
  cells stay open (BSA).

**Demo-day facts worth keeping:** `0.5.8.post5-ddl1` is not PEP 440 — a
local label `+ddl1` is (pip builds it). `.claude/skills/spiral-breaker/…/
run_replay.py` launches `claude`, not codegen (no child_env there).

**Session gotchas (this Windows box):** bash heredocs containing backticks
break — write patch scripts with the Write tool and run them as files;
Write-tool files may be CRLF, so `str.replace` patches can miss (use Edit);
an env var holding a `;`-separated path list with a drive letter gets
MSYS-converted — `export MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS`. The
spiral-detector hook keys on the exact command string: a check that later
passed under a broader command still reads "failing" (logged as a false
trigger in `docs/spiral-log.md`, 2026-10-07) — re-run the quoted command first.

## Parent branch `fix/remove-mock-provider-ui-text` (state as of 2026-09-23)

**What this branch is.** A LEGACY demo branch cut from **v0.5.8-acfc (3a5b85d)**
— NOT from `staging` (which is far ahead: v0.8.1). Pushed to
`origin/fix/remove-mock-provider-ui-text` (M15 at 16238d0, then the M15b
commits below — the remote head is the last commit of `git log`), working tree
clean (only the untracked `docs/acfc/denylist_local.txt`, see below). Soham's
rule for this branch: **only make the changes he indicates.** Nothing here is
merged anywhere; staging / main are untouched.

**Verified at the M15b wrap-up:** 730 passed / 27 skipped (Python 3.11 full
suite; the chooser / hang / pairing / databricks / demo-UI / remote-e2e files
also on 3.10 and 3.12 — uv venvs in the session scratchpad, not in the
checkout; one timing-bound chooser test flaked once on 3.10 under CPU load and
passed on every re-run); ruff clean (`src/ tests/ ui/backend/` — `acfc_run.py`
has 6 PRE-EXISTING E402s, notebook cells); tsc clean; vitest 15 passed (`cd
ui/frontend && npx vitest run`; `jsdom` is a devDependency now, for the
ErrorBoundary test); scrub 0 over every changed file incl. the bundle and its
map; `ui/frontend/dist` rebuilt WITH SOURCE MAPS and tracked
(`index-CFS_8pvg.js` + `.js.map` — `vite.config.ts build.sourcemap`, so a
console stack names the component and line). App version marker
**0.5.8.post5** (pyproject + requirements.txt — bump BOTH whenever `src/`
changes; `ui/` runs from the source tree and needs no bump; M15b touched no
`src/`).

**M15b (2026-09-23, 102b91d · bda1dc0 · f91c68e · the wrap-up) — the white
screen on select**, from the ACFC console: `TypeError: Cannot read properties
of null (reading 'toFixed')` in the step trace (M15's `steps[].seconds` is
null while a step runs) + `GET api/databricks/documents → 503`. (1) every
number renders through `ui/frontend/src/format.ts` (`fmtSeconds` "…" while
running / "—" when missing, `fmtNumber`, `fmtKb`); the step trace and the
pairing lines are `components/SelectionTrace.tsx`; (2) the status payload is
normalized ONCE in `api.ts` (`normalizeStatus`, every DemoStatus call):
pairing null-safe, `pairing_pending` always an array, seconds / scores
`number | null`; (3) `components/ErrorBoundary.tsx` around the routes
(App.tsx) and around the document chooser; (4) `chooseWorkbook` has no
one-shot status read (the poll delivers); (5) the documents route answers
**200 `{configured: false, reason, documents: {sttm: [], frd: []}}`** when the
volumes seam is off (the UI hides the panel; store unbound stays 503, refused
workspace stays 502); (6) the FRD and VDD pairings run in PARALLEL threads
(own step entry — `_try_step` never touches `steps[-1]` — own parser lane
`request` / `request-vdd`, applied as each lands, recorded when the last
does): with a fake 5 s backend both pairs land after **6.3 s instead of
11.2 s**; (7) `_index_folder_first`: the folder of the STTM being selected —
and at App start the folder `selection.json` names — is queued for the index
and read first.

**M15c (2026-09-23, the commit after the M15b wrap-up) — Generate still sat
on "pairing — waiting for the FRD / VDD pairing of <MIDS>" for minutes.** The
button was enabled, but `_await_pairing` waited up to two step budgets for
BOTH pairs, and for an inbox STTM the VDD scope "all" downloaded + parsed
every workbook of every pair folder on the request path. Now: (a) a run waits
only for an FRD still pending while NONE is selected (one step budget), never
for the VDD (optional; one that lands later is not part of this run); (b) an
explicit `demo.pairing_map` entry decides in `_plan_pair` WITHOUT reading any
candidate; (c) on the request path only the STTM's own folder and LOCAL
sources are read — remote roots outside the folder score from indexed facts
or names (`unread`), the folder-first background index closing the gap. The
"other roots pair by content" test waits for the index first.

**M15d (2026-09-23, the commits after M15c) — VDD pairing as fast as FRD
pairing, inbox STTM included.** (1) A VDD candidate is NEVER downloaded or
parsed on the request path (`_plan_pair`, `kind == "vdd"`): dictionaries the
background index has classified score in memory from the index's stored
facts; ones it has not reached score by name and are listed as
`not_indexed` on the outcome (the chip text says "not yet indexed"). (2)
`DemoRunner._index_warmup` (a thread at construction, `index_warmup=False`
for tests that want no worker) queues, after the restore job, every
workbook classified or likely by name (`_LIKELY_VDD`: vdd / dictionary) to be
a VDD, then the rest, and keeps the folder `selection.json` named first
(`_restored_folder`); logger `codegen.ui.index` says `index warm-up: all VDD
candidates indexed`; `_warmup_done` is the event tests wait on. (3)
`DocumentIndex.add_listener` → `DemoRunner._on_indexed`: when a watched
name-only candidate (`_vdd_watch`) gets its verdict, `_repair_vdd` re-scores
from the index and applies a candidate that now WINS (`upgraded_from` on the
outcome; never over a manual pick; deferred past a run in progress —
`_deferred_vdd_plan`, applied when `_run` ends). (4) `demo.vdd_pairing_map`
decides immediately like `pairing_map` — documented in `docs/ACFC_DEPLOY.md`
§7. **Wall-clock (fake workspace, inbox STTM, three pair folders):** warm
index — select 0.62 s, pair VDD 0.02 s, by content, zero VDD downloads on the
request path; cold — select 0.06 s by name (ticket), upgraded to the true
dictionary by content 0.2 s after the index reached it. Two tests that
assumed request-path VDD reads were re-stated (`test_vdd_pairing_kind`: the
STTM's own copy is a `not_indexed` name-only candidate on a cold index and
dropped once indexed; the M15.5 late-read test now uses an FRD). Windows
note: the local index file is read by the pusher while `_save` rewrites it —
harmless on the App's Linux, a sharing violation only in local tests that
unlink the file.

**M15e (2026-09-23, the commit after M15d) — a cold index never auto-selects
a VDD by name.** (1) In `_plan_pair` a VDD candidate that wins by a NAME rule
while not yet indexed is demoted: `outcome.likely` = its name, `chosen` None,
nothing applied — content, the same-folder rule or the pairing map still
decide; the chip / pairing line read "Indexing dictionaries… likely: <name>
(by name only, not applied)"; no VDD question is asked while `not_indexed`
is non-empty (`_ask_pairing`). (2) A run started in that window goes
WITHOUT a VDD: `_note_undecided_vdd` → `run_notes` (["VDD not decided at run
start (likely X, by name only — not applied)"]), a run stage, a gate flag
`vdd_not_decided_at_run_start: …` on every feed (so the report says it) and
`run_meta.json` `notes` + `vdd`. (3) When the index reaches the candidates the
content decision applies as before (`upgraded_from` = the applied pick, else
the earlier `likely`); an undecided re-score refreshes `likely` on the
status. Test: four pair folders sharing a ticket, cold index, inbox STTM — no
VDD applied, a run in the window has none and the note, the true dictionary
lands by content. Test-infra fix worth knowing: `_Workspace.release()` now
DRAINS every runner's index worker / pusher / recorder — a thread outliving
its test wrote through the module-level `ui_stores.get_stores` cache into the
NEXT test's roles (foreign names in a listing test, once). The name-stem rule
needs THREE content tokens (`_token_prefix`), so name-only fixtures are
`<role>_<a>_<b>_<ticket>`.

**M15e test-infra findings (same day; the code changes are real, keep them):**
(a) `ui_stores.get_stores` caches ONE StorageSet PER CONFIG OBJECT
(identity) instead of one process-wide slot — two runners alive at once (the
App module's import-time runner and a test's) rebuilt each other's roles on
every call; `reset_stores()` is a NO-OP now (clearing let a thread outliving
its test rebuild through the unpatched `open_storage` = the checkout's
default roles, and write fake-workspace verdicts into
`ui/backend/state/document_index.json`, gitignored, which the next session's
runners then LOADED — the "unreadable at the first listing" failures on
3.10). (b) Test fixtures assign `store.config = copy` PLAINLY, never via
monkeypatch: a reverted patch hands a live runner thread the original
config object. (c) `_Workspace.release()` stops every parser child
(`docindex._stop_parsers()`) and drains each runner's worker / pusher /
recorder before the next test. (d) `docindex.parser_for` never evicts a
parser that is mid-parse (cap 6; one runner uses three lanes). (e)
`CODEGEN_DOCWORKER_STDERR=<file>` appends the parser child's stderr (it is
discarded otherwise) — set it in the App env to diagnose "the document
parser exited while reading the document".

**M15 (2026-09-23, a7b41f4 · 49108e6 · c33ae06 · e825c23) — selection latency +
pairing correctness**, from Soham's brief after the diagnosis of "Selecting
<MIDS> takes minutes": (1) `DocumentIndex._save` writes the index locally and
ONE background writer pushes `document_index.json` (no pull before a
whole-file write: `stores.state_local_path`) — every request-path read used to
pay a Workspace export + import inside the step's budget; (2) the job is DONE
(STTM applied, Generate enabled) right after classify; pair FRD / pair VDD run
behind it (`job.pairing_pending`, chips say "Pairing…", `_await_pairing` makes
a run started meanwhile wait); `wait_selection` / `select_workbook` /
`tests/ui_select.py` and the tests' `_wait_job` helpers wait for the pairing;
(3) `_drop_auto_pair`: a prior STTM's automatic pair goes when the new STTM is
applied and when a pairing step returns None; (4) a VDD score in (0,
min_score) is a QUESTION and the same-folder rescue ignores the score —
DEVIATION kept as found: a zero-score VDD is still OFFERED
(`test_vdd_pairing_kind` pins it); (5) `StepTimeout` in `_plan_pair` keeps the
candidate name-only (`unread`), a chosen file not downloadable in time is said
on the outcome; (6) `steps[].seconds` on every job step (record too); (7) the
status poll re-arms after a failed GET, the trace shows seconds; (8)
`catalog.natural_key` ordering (pair_2 before pair_10) + `DocumentIndex
.prioritize(folder)` on selection start. Commits: 2+3+6+7 landed together
(same regions), 4+5+8 together. **Before/after** (fake workspace, cold index,
a 5 s state-role write standing in for ACFC's; MIDS itself is not in the repo
— the family-E multi-sheet fixture in the uploads inbox stands in): inbox
STTM 66.7 s → 1.0 s until Generate enables (pairs 1.4 s); pair-folder STTM
15.1 s → 0.0 s. Script: the session scratchpad's `m15_timing.py` (not
tracked). Not yet run inside ACFC — the new per-step seconds will say.

**What the branch changed (oldest first):**
1. b5cf50d (Genie) hid the mock label exactly when the provider WAS locked —
   REVERTED (74fcbbb). Its RFC/All button removal was redone properly below.
2. **Provider labels are derived, never static** (cd799ed, 1cf9e76):
   `src/codegen/reasoning/usage.py` `StageUsage` per stage (layout, layer2):
   provider, endpoint, model, real call count, mock reason. ONE label:
   `Claude Opus 5 (databricks-claude-opus-5) · N call(s)` /
   `Resolved from the documents (no model call needed)` /
   `Mock provider (reason: <CODEGEN_FORCE_MOCK_PROVIDER | endpoint
   unreachable — … | dry-run | test>)`. Rides FeedRun.model_usage,
   `/api/feeds` + run status `model_usage`, the report's `## Model usage`
   section, the CLI `MODEL USAGE` lines, the UI (`ModelUsageList`). Every
   mock the builders make carries `mock_reason`. **`app.yaml` ships LIVE**
   (no `CODEGEN_FORCE_MOCK_PROVIDER`; set it as App env to lock — the UI
   then SAYS so). `tests/snapshots/notebook_mode.json` was re-based for the
   three CV REPORT hashes only (the new section); generated code unchanged.
3. **Outputs are exactly Notebook + Framework artefacts**
   (`src/codegen/output_modes.py`, the one vocabulary): config `output.mode`
   is a list of parts (a string still reads), CLI `--output-mode
   notebook|framework` (repeatable), `GET /api/demo/output-options` =
   `["notebook","framework"]`, UI `OutputSelector`. A retired `both` /
   `rfc` / `all` (config, saved state, request, a past run's run_meta.json)
   maps to both with a ONE-TIME notice (`status.output_notices`), never an
   error. `emit/rfc.py` is kept but unreachable (its tests drive it
   directly). Left in place, now no-ops: the UI Playbook selector,
   `--playbook-template`, acfc_run.py's playbook widget. acfc_run.py now
   passes `--output-mode framework`.
4. **"Clear past runs…"** button (1f65a5b): `GET /api/demo/runs`, `POST
   /api/demo/runs/clear {confirm: true}` — deletes ONLY `demo_YYYYMMDD_HHMMSS`
   folders, remote copy too (`StorageBackend.delete_tree`, never the root;
   Workspace API recursive delete, Files API files-then-dirs). 409 during a
   run; a run cannot start mid-clear (`_clearing`). Remote delete ran
   against fakes only. Locally, 41 stale run dirs were MOVED (not deleted) to
   `out/_stale_runs_20260922/` on 2026-09-22 — delete it when sure.
5. **Downloads** (893d991, 6238643): Notebook tab `Download .ipynb`; Code
   tab toolbar `Download .ipynb` + a per-file icon button in the path bar —
   GitHub-style `DownloadButton` (`.gh-btn`), never a primary button. The
   route `/api/feeds/{slug}/download` serves .ipynb as
   application/x-ipynb+json. Verified in a real browser (Playwright).
6. **No Databricks-volume document source** (d0a7ef3): `databricks.catalog /
   schema / frd_volume / sttm_volume` ship BLANK (they named the Hexaware
   workspace's volumes; ACFC has none). A desktop opts in via
   `DATABRICKS_CATALOG / _SCHEMA / _FRD_VOLUME / _STTM_VOLUME`.
   `config_for(require=...)`: endpoint / layout / upstream pass `require=()`
   so blank volumes never drop live Layer 2 to mock. Side effect: the
   publish panel is unavailable as shipped. Still Hexaware-specific in the
   config (unused in ACFC): `warehouse_id`, `readable_tables`, landing /
   output volume names.
7. **Selection no longer waits on the state-role write** (a591c07): the
   job applies the choice, THEN a background recorder writes
   selection.json (newest wins, bounded, failure = `record` warning).
   Cause of Soham's report: FRD/VDD showed paired, the STTM name took 2-3
   min (the old `record` step ran before the choice with a 120 s budget).
   WHY the ACFC Workspace write is slow is still unknown.
8. **Workflow-built, adversarially reviewed** (6bb9cb3, e506ae1, 3c7e8fd):
   VDD pairing never picks a workbook read as an STTM (cold index too; the
   CLI `codegen pair` too). Staging's used-range trim ported
   (`src/codegen/layout/extent.py::load_document`, knob
   `extractor.used_range_empty_rows: 500`): a sheet formatted to row
   1,048,538 classified in 87 s → 0.03 s. Deviation from staging: a cell WITH
   a value is NEVER dropped (only the empty styled tail). The new extractor
   knob changes `vocabulary_hash` → runtime layout caches in ACFC re-resolve
   once. Known leftover: a copy of the STTM that pairing did not manage to
   READ in time can still appear as an option of the pairing question.

**Easy to break on this branch:**
- `docs/acfc/denylist_local.txt` (RAW client terms) is **NOT gitignored
  here** — stage files explicitly, never `git add -A`.
- `origin/acfc-runs` is unscrubbed: read in place (`git show`), never quote
  real names.
- In a git worktree, `PYTHONPATH=.` still imports `codegen` from the main
  checkout's editable install — use `PYTHONPATH="src;."`.
- Redeploy needs: `dist` synced (strip `.gitignore` from the staged tree),
  the version marker bumped, Can Manage on state / outputs / inputs.

## Purpose & pipeline position

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta
Lake) from approved machine-readable contracts — one FRD feed contract plus
one STTM mapping contract per feed. It is the **second agent** in the
three-agent AI-in-Engineering program at AmeriHealth Caritas: FRD→STTM
(produces the FRD feed contracts consumed here) → **CodeGen** → Code Review
(reviews what this repo emits).

**Scope cut 2026-08-21:** the program dropped from five agents to three —
BRD→FRD and SQL Optimization are no longer in scope. Do not build them or
add dependencies on them.

**Where this runs:** Hexaware builds, ACFC rebuilds. This repo is the
Hexaware-side reference implementation; the production agent gets rebuilt
inside ACFC's own environment with Claude Code, using this as the
blueprint. Nothing here deploys to ACFC directly — anything that cannot be
re-derived from the contracts, config, and docs does not survive the
hand-off. **Current program priority is FRD→STTM's live Databricks App
(due 2026-08-24), not this repo.**

Two-layer trust rule (never violate): **Layer 1** is deterministic Jinja2 —
everything derivable from the contracts, byte-stable, every file stamped
with a provenance banner carrying the contract names + sha256. **Layer 2**
is the LLM, mock by default — ONLY free-text `validation_rules` the
compiler classifies as `unmapped` reach a model; its output lands in a
review artifact (`out/<feed>/candidates/candidates.json`), never in
generated modules, and every citation must appear verbatim in the contract
text. Each feed ends in a computed gate verdict: PASS / PASS_WITH_FLAGS /
FAIL (semantics in `docs/WORKFLOW.md`).

## Repo layout

```
src/codegen/        sharepoint.py (Microsoft Graph transport, stdlib-only),
                    databricks.py (UC volumes transport, read-only, needs the
                    [databricks] extra; added 2026-08-27),
                    demo_sources.py / metadata_sheet.py / input_requirements.py /
                    governance_checks.py (request-time display+check modules,
                    all OUTSIDE the generation path; added 2026-08-27),
                    contracts/ (pydantic models, both dialects + vdd.py, frozen),
                    layout/ (M2.5 layout recognizer: profile, fingerprint,
                    discover, validate, model, resolve, frd_profile),
                    resolve/ (FRD⋈STTM join → ResolvedFeedSpec), extract/
                    (workbook→STTM incl. generic.py content-driven reader,
                    frd_docx.py, vdd.py), rules/ (rule classifier),
                    reasoning/ (Layer 2: providers, verbatim grounding),
                    emit/ (Jinja2 + notebook assembler; framework.py Option B,
                    rfc.py the RFC package, dml.py the SQL Server DML — M7),
                    gate/ (preflight, tests, verdict, vdd_check, drag_fill,
                    derivations — M7), metadata_template.py (IIG template
                    versions), report/, templates/, cli.py, config.py,
                    storage/ (M8.1: local | workspace | volume backends, role
                    stores, input catalog — an EDGE, never imported by the
                    generation path), pairing.py (M8.2: pairing by content),
                    layout/answers.py (M8.3: answers file + unresolved report)
tests/              offline, no Spark needed; some SKIP when the fixtures they
                    drive on are absent (see "Fixtures & data rules"); the
                    demo-UI and SharePoint-route tests also skip when the [ui]
                    extra (or httpx) isn't installed. Run pytest for the live
                    count rather than
                    trusting a number written down here.
config/config.yaml  every knob — contract pairs (EMPTY since 2026-08-22), extractor layout
                    (+ discovery / frd / vdd synonym tables), naming, masking, gate, job,
                    layout, conventions, metadata, rfc, playbook. Overlays:
                    load_config(path, overlays=[…]) / CODEGEN_CONFIG_OVERLAYS deep-merge
                    a YAML mapping first — client-shaped vocabulary lives THERE
                    (fixtures/acfc_shapes/pair_1/config_overlay.yaml), never in the tracked file
fixtures/           tracked on staging (state as of 2026-09-18, M6): faq/ (per-feed
                    load-pattern FAQs), reference/ (SCRUBBED SFMC client reference
                    artefacts incl. the deployment playbook + SCRUB_REPORT),
                    acfc_shapes/ (the SYNTHETIC fixture universe for ACFC's shapes,
                    generated by scripts/build_acfc_shapes.py; the aliased pair-1
                    golden; the pair-1 config overlay), layout_profiles/ (cached
                    layout profiles + the mock/adversarial answers, generated by
                    scripts/build_layout_profiles.py), the CV golden contracts +
                    workbook + replay set (anonymized universe) and
                    workbooks/synthetic_segmented_golden.xlsx — all via deliberate
                    per-file .gitignore re-includes. NOT on staging: the MIDS/CAQH
                    client documents and the SFMC client-derived contract pair
                    (untracked 2026-09-18; on MAIN they are tracked since b0560af)
docs/               DESIGN.md, WORKFLOW.md, EXTRACTOR_RECON.md, SEGMENTED_MODE_DESIGN.md,
                    LIVE_PATH_RECON.md, LIVE_RUN_RECORD.md, DEMO_RUNBOOK.md (client demo script),
                    EDO_STANDARDS_ALIGNMENT.md (clause-by-clause map of the EDO
                    naming/coding standards to the generator, incl. deviations),
                    LAYOUT_RECOGNITION.md (the recognizer), ACFC_DEPLOY.md (stand-up
                    inside ACFC), acfc/SHAPES_FOR_PORT.md + acfc/rfc_capture/…/
                    RFC_PACKAGE_SHAPES.md (the documented client shapes) + the pair-1
                    goldens, acfc/METADATA_DB_SEMANTICS.md (the SQL Server metadata-DB
                    walkthrough as a spec — M7; its raw .docx stays untracked), media/
ui/                 demo dashboard: FastAPI (8571) + Vite/React (5173); pip install -e ".[ui]", see ui/README.md
                    backend/sharepoint_routes.py: picker + confirm-gated publish.
                    ui/frontend/dist IS TRACKED (M6): rebuild (`npm run build`) and
                    commit it whenever ui/frontend/src changes — the App serves it
inputs/sharepoint/  gitignored landing dir for documents pulled from SharePoint
acfc_run.py         Databricks notebook source: the one-pair fallback run (storage URIs as
                    widgets, answers file) for a workspace where the App is not usable
```

## STTM workbook extractor (codegen extract-sttm)

Deterministic, no LLM, pairing-aware: inputs are (workbook, FRD contract); `feed_id`
is `normalize_feed_name(FRD feed_name)` — the resolver's join invariant, NOT the
stage table name — and format/delimiter/standard-target presence come from the FRD side. Recycle validation text stays VERBATIM
(the resolver also accepts the client "Check with ... FOR ..." phrasing).
**Segmented (H/D/T) dialect IMPLEMENTED, corrected 2026-09-01 against the
FRD read verbatim** (`extract/segmented.py`; docs/SEGMENTED_MODE_DESIGN.md):
segments are TABLES in BOTH layers (FRD acceptance criterion 2 — fields
carry `record_segment`/`stage_table`/`standard_table`; per-segment
standard DDL), layer scope comes from **Load Strategy STG/STD, never from
which schemas the Target Schema block names** (STD catalog/schema/tables
from the STTM's second target group with a cited provenance note), record
identification is **DERIVED from the STTM** (trailer static marker quoted
verbatim as the citation; header positional; FAQ
`record_type_discriminators` is strictly a confirmed-status override),
STRING-except-audit in both layers rides an FRD-driven AS-IS switch
(`spec.load_as_is`), and a keys-None FRD (truncate/append, no MERGE)
makes empty `natural_key_columns` legitimate. The review layer gets ONE
soft cited CONFIRM item (`RuleCandidate.kind == "confirm"`), riding the
existing candidates/decision flow. **Citation rule (2026-09-01 lesson):
every conflict/assumption/confirm item and provenance note the agent
raises MUST quote the exact FRD field or STTM cell it rests on — an item
that cannot cite its evidence is a bug (models enforce non-empty
citations; tests assert them). And never infer target-layer scope from a
schema block: "stage-only" was wrongly inferred that way once — read Load
Strategy.** Header resolution is fuzzy + config-driven (`extractor:` knob);
trailing `NA` rows → `audit_columns`, never `fields[]`; `Comment` →
`value_spec`; file-name pairing canonicalizes date placeholders (CCYY→YYYY,
case-insensitive) and stays fail-loud. The CV/golden pair is byte-tested against
its committed expected output and can NEVER match the MIDS fixture
(different universe — docs/EXTRACTOR_RECON.md §4d).

## Setup / run / test

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"   # deps from pyproject
# Python 3.10 – 3.12 are supported (the Databricks Apps floor is 3.10): before shipping,
# run the suite on 3.10 and 3.12 too — uv venv --python 3.10 <dir> && uv pip install -e ".[dev,ui,databricks]"
# Live Layer-2 runs additionally need the Anthropic SDK: -e ".[dev,live]"
.venv/bin/python -m pytest -q          # no Spark, no network

# Generate everything from the fixture contracts (mock Layer 2, no network)
.venv/bin/python -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests
```

`contracts.pairs` is empty (see "Fixtures & data rules"), so `generate-all`
refuses loudly; generate via explicit paths (`codegen generate
--frd-contract X --sttm-contract Y`) or the demo UI's golden pair. A feed
with flagged/notification/unmapped rules verdicts PASS_WITH_FLAGS — correct
behavior, not a failure. Output lands in `out/<feed_slug>/` (module tree, DDL, tests,
job JSON, one assembled runnable `.ipynb`) with a markdown report per feed
in `reports/` — both gitignored. Running the *generated* Spark tests (drop
`--skip-tests`) needs a JVM: `JAVA_HOME` → Java 17, `PYSPARK_PYTHON` → the
venv interpreter. `ruff check src/ tests/` must stay clean; generated code
must be ruff-clean against the same rules (`out/<feed>/ruff.toml` emitted).

## Config doctrine

- Every knob lives in `config/config.yaml` — contract pairs, extractor
  layout, naming, masking, segment discriminators, gate, job cluster. No
  numeric literals in generator logic; the loader is loud on typo'd keys.
- No secrets in the repo, ever. Credentials only via environment / `.env`
  (gitignored; `.env.example` documents the names).
- Program policy: **Anthropic is the sole model vendor** across the
  AmeriHealth agents program. Mock always wins on dry-run; live selection
  is transport-dependent (2026-08-28): the tracked config's
  `reasoning.provider` is **`databricks_fmapi`** (Claude via the workspace
  serving endpoint `databricks.serving_endpoint` — a transport, not a
  vendor change; resolves from YAML + workspace auth, no Anthropic key),
  with `anthropic` (key-gated on `ANTHROPIC_API_KEY`) still available.
  CAUTION: because FMAPI resolves without any env secret, tests that touch
  live paths must pin the provider — `tests/test_demo_ui.py`'s `client`
  fixture does this; a 2026-08-28 pytest run fired real FMAPI calls before
  that guard existed. First live FMAPI E2E: 2026-08-28 (CV golden pair,
  candidates verified). Live LLM use is confined to Layer 2
  (reasoning/review); code generation itself is deterministic Jinja2 by
  design. Model name lives in config (`reasoning.model`, currently
  `claude-opus-5`). The Claude 4.8/5 API families reject sampling
  parameters (`temperature`/`top_p`/`top_k` return a 400), so no
  temperature knob exists and live Layer-2 output is inherently
  non-deterministic — do not re-add one. CAUTION (2026-09-01): the
  endpoint serves extended-thinking Claude, whose `message.content` comes
  back as a LIST of typed blocks (reasoning + text), not a string —
  `codegen.databricks.chat` normalizes via `_chat_content_text` (text
  blocks joined, non-text ignored). Do not "simplify" that back to
  `content or ""`; that exact regression produced the provider-failure
  candidates in run demo_20260831_212539 (fixed in e91ec11; post-demo
  TODO in docs/DESIGN.md §8: provider failures should be their own flag
  class, not candidate cards).
- Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing is
  `None`, never a default. PHI masked to last-4 at every egress.
- **Client framework doctrine (Aug 26 framework calls, encoded 2026-08-27):**
  job parameters carry IDs the wrapper resolves from metadata, NEVER inline
  SQL (~250 KB parameter cap); all new tables managed with
  `CLUSTER BY AUTO` and CDF on (NOT workspace defaults — must be explicit
  DDL, per B0 observation); the agent never creates target tables and never
  runs jobs; Anthropic is the sole model vendor — Databricks FMAPI serving
  a Claude model (`reasoning.provider: databricks_fmapi`,
  `databricks.serving_endpoint`) is a transport, not a vendor change. The
  only SQL shape the seam may send is `EXPLAIN` (`codegen.databricks
  .explain` enforces the prefix), and an EXPLAIN wakes the auto-stopped
  warehouse = DBU spend from the shared ~120/month pool.
- **Engineering standards are REAL as of 2026-08-26** (three-input model
  input #2 is no longer a stub): the EDO Data Engineering Naming + Coding
  Standards live as data in `config.yaml engineering_standards:` (WF_/NB_
  naming patterns + abbreviation tables) and `job:` (prod-support alert DL
  on success AND failure, `timeout_hours`, Photon, DBR 15.4). The
  `standards_stub` gate flag is gone for the tracked config; the MODEL
  defaults keep the stub so a config without the section still degrades
  honestly. Clause-by-clause map + deviations:
  `docs/EDO_STANDARDS_ALIGNMENT.md`. The DDL templates emit
  `CLUSTER BY AUTO` (Liquid Clustering) and `LoadStrategy` accepts
  `"Upsert"` (the SFMC FRD's standard-layer strategy).

## SharePoint / Microsoft Graph (added 2026-08-23)

Ported from frd-to-sttm-agent-v2's integration. The document library is the
program's system of record: STTM workbooks and FRD contracts in, generated
artifacts out. `src/codegen/sharepoint.py` is the whole transport.

**It is a seam at the edges, deliberately outside resolve/emit/gate.** The
generator's inputs and outputs are files on disk; SharePoint attaches before
(`codegen sharepoint-fetch`) and after (`codegen sharepoint-publish`).
Keeping the network at the edge is what lets Layer 1 stay deterministic,
offline and credential-free. **Do not "simplify" this by calling Graph from
inside `extract-sttm` or the resolver.**

Mechanics (stdlib-only transport, app-only credentials via
`SHAREPOINT_CLIENT_SECRET`, config split, fail-loud rules, the
publish-is-the-human-gate design, one-folder write scope, qualified publish
names, UI route status codes):
`.claude/skills/code-gen-agent/references/sharepoint-seam.md` — read it
before touching `sharepoint.py`, the publish flow, or the UI routes. No
secrets in the repo; the `sharepoint:` config section is optional and
non-secret.

## Output modes (Option A / Option B, added 2026-08-27)

The outputs are EXACTLY Notebook and Framework artefacts
(`src/codegen/output_modes.py` is the one vocabulary): `output.mode:
notebook | framework | [notebook, framework]`, CLI `--output-mode`
(repeatable, choices notebook / framework), UI two toggles rendered from
`GET /api/demo/output-options`. The RFC package / All options were removed
(2026-09-22); a config, saved selection or past run that still says `both`,
`rfc` or `all` maps to notebook + framework with a one-time notice
(`output_notices` on the status), never an error. `codegen/emit/rfc.py` is
kept but no output option reaches it (its tests drive it directly).
**Option A** ("notebook", the default) is today's output byte
for byte — a fresh standalone pipeline, the ~10% case; guarded by
`tests/snapshots/notebook_mode.json` (sha256 per emitted file for the CV
pair — regenerate deliberately, never casually). **Option B**
("framework") is the primary ACFC path per the Aug 25/26 calls: an
*addition* to the existing metadata-driven ingestion framework (~90% of
runs) — `out/<slug>/framework/` holds (formats swapped 2026-08-31 per
Venu's standup direction + the real client reference artefacts, scrubbed
into `fixtures/reference/` by `scripts/scrub_reference.py`; the raw
exports live only in gitignored `inputs/reference_raw/`, and
`scripts/scrub_check.py` is the denylist scanner tests run over every
emitted artefact): `<slug>_stage_table_creation.txt` +
`<slug>_standard_table_creation.txt` (deployment-team DDL conformant to
the reference goldens — CREATE OR REPLACE, per-column COMMENTs, stage
LOCATION labeled-SYNTHETIC, standard CLUSTER BY AUTO + full TBLPROPERTIES,
trailing SET TAGS), `config_rows.xlsx` (THE approval artefact; built by
`codegen.metadata_sheet`, the single source of truth for the row layout —
now the REAL 7-tab client IIG layout from the scrubbed reference
workbook) and `config_inserts.xlsx` (one sheet per populated tab, value
rows + generated INSERT column, sqlserver|lakebase dialect via
`framework:` config; statements over Excel's cell limit chunk into
`_PART<n>` columns; plain INSERTs, idempotency belongs to the framework's
load path) and `ADDITION.md`. **The master notebook is ACFC's own existing notebook
(clarified 2026-08-27): the DDL scripts and insert SQL are ADD-ONS to it —
the agent never generates, edits, or ships that notebook.** Framework mode still renders the FULL pipeline into a
scratch tree so gate checks and verdicts are identical across modes; it
persists only ddl/ + framework/. **Never-invent-IDs:** `always_blank`
columns render as `framework.id_placeholder` and are flagged — assigned
by the client's framework or manually by client instruction, never by the
agent. Workbook serialization is pinned byte-stable
(`stable_workbook_bytes`). The FAQ gained `has_header`/`has_trailer`
companions (NOT questions — banner/flag counts untouched) feeding the
"from FAQ" badge.

## M9 (2026-09-21, v0.5.1-acfc): the first real pair-1 run inside ACFC, landed properly

The first ACFC run of pair 1 (2026-09-21) failed in six places; a Genie Code
session hot-fixed three of them on the remote branch **`acfc-hotfix-1` —
never merge it** (its `config.yaml` carries a user's workspace paths, the
workspace catalogs and `layout.provider: live`; its two documents,
`HANDOVER_GENIE.md` / `PAIR1_HEADERS.md`, quote client table / file / LOB
names). `docs/acfc/M9_FINDINGS.md` is the SCRUBBED record: what the two
captures establish, what M9 changed, and the hotfix triaged commit by commit
(kept: the `… in dl` + `details` synonyms; reworked: `_band_constant`, the
rejection log, the Do-Not-Map skip; dropped: the empty-schema tolerance, every
workspace value in `config.yaml`, the notebook restructure).

- **Pair-1 fixtures are REAL-SHAPE now (M9.0).** STTM: meta r1–r10 (`TBD` /
  `.dat` / blanks, no Load Strategy row), bands A14:I14 · K14:P14 · R14:W14 ·
  Y14:AD14, 27 headers over 30 columns (J / Q / X empty), schema + table on
  every data row, `Header` / `Details` / `Trailer` banner rows (the Segment
  column keeps HDDR/DET/TRLR — the golden IIG's SEGMENT cell), one `Do Not
  Map` row. FRD: `Target Table Name` = an inline layer block, `Target Catalog
  and Schema` blank, `Object Name` = `<label>: <file>` lines (names no feed),
  `Name` = a sentence. The feed is therefore named after the STTM stage band:
  feed id / slug **`vnd_p_accum_client`** (was `accumulators`; the FAQ fixture
  was renamed to match). Tests that need a sheet the synonyms leave open use
  `tests/pre_m9_vocabulary.py` (the tables minus the M9 synonyms — also the
  exact state of the failed ACFC run); the documented-shape FRD lives on as
  `test_frd_gapfill._pair1_docx_without`.
- **Resolver (M9.1).** `schema` is REQUIRED in both target bands (catalog
  optional); a missing required role is ALWAYS a question
  (`_list_missing_required`). Answers may set ANY role and win over synonyms /
  model / cache (`_merge_columns(override=True)`; the displaced role gives the
  column up; `apply_answers(…, documents=…)` infers the band from the header
  text, then from the role's current band). Runtime cache entries carry
  `vocabulary` = `vocabulary_hash(config)` (the whole `extractor:` section +
  roles + required roles) — another / no key = stale; a profile lacking a
  required role is never trusted (either cache) and never written; `refresh`
  (`codegen layout --refresh`, UI "Re-resolve layout" = `POST
  /api/demo/layout-refresh` + `layout-answers {refresh}`, notebook widget)
  bypasses and overwrites, tombstoning (`invalidated`) when incomplete —
  the storage roles have no delete. Model-answer rejections are written in
  full to `<runtime cache>/rejections/<fp>.json` (invented keys masked `<key>`,
  no input value). The REPO cache (`fixtures/layout_profiles/`) stays plain
  profiles — it doubles as the mock's answers (extra=forbid) and is
  test-pinned to a fresh build. **Any `extractor:` edit changes the hash** —
  expected; nothing tracked embeds it.
- **Extractor (M9.2).** `_band_constant` = first non-empty cell when the
  column holds ONE value (else the dominant, as before — pair 8 has a table
  per segment), provenance in the contract notes. Schema chain: STTM band →
  FRD → `conventions.default_schema[layer]` → HARD STOP (an empty schema
  never reaches a contract). `extractor.unmapped_markers` → the field is left
  out, flag `field_unmapped:<field>` citing the cell.
  `extractor.discovery.meta_blank_values` (`TBD`) read as blank; an
  extension-only format cell (`.dat`) never disagrees with a stated format
  (`gapfill.format_statements`). `SttmFeed.extraction_flags` /
  `FrdContract.extraction_flags` (absent from the JSON when empty — baselines
  untouched) carry extractor decisions to the gate via the resolver.
- **FRD reader + matcher (M9.3).** `parse_layer_blocks`
  (`extractor.frd.layer_block_heading_words` / `layer_block_labels`);
  StructuredValue kind `labelled_files`; `frd_feed_name_unstated`;
  `split_frd_feeds_by_sttm` names an unnamed / garbled single-sheet feed even
  when the FRD names the STTM's table; `codegen layout --frd-contract-out`
  writes the PAIR-resolved contract (use it instead of `extract-frd` on the
  CLI path — `acfc_run.py` does); `normalize_table_name` + flag
  `table_name_normalized`; FRD schema / catalog unstated → STTM bands, flagged
  `frd_unstated:<layer>_target.schema|catalog` (the brief wrote
  `<layer>.schema`; the repo's contract-path convention was kept).
- **Found on the way:** `codegen generate` parsed `--vdd` / `--profile` /
  `--iig-template` / `--playbook-template` and DROPPED them (since M4) — fixed.
- **Beyond the brief, decided in-session:** `"format"` is a `source_type`
  synonym (the real header at E15; without it source types read `unstated`
  and nothing asks); a feed named after the STTM is `unchecked`, not a
  `layout_crosscheck:feed_name` disagreement. **Open:** the real `Frequency`
  cell is a compound sentence (not modelled); the real `Format` values are
  unknown; whether `origin/acfc-hotfix-1` stays (unscrubbed) is Soham's call.
- Acceptance: `tests/test_m4_acceptance.py` (DDL byte-identical, IIG as M4,
  the flag list pinned by kind + count — `PAIR1_GATE_FLAG_KINDS`),
  `tests/test_m9_acfc_findings.py`, the CLI-chain test.

### v0.5.2-acfc (2026-09-21, same day): the first REAL run of v0.5.1

Run records on the remote branch **`acfc-runs`** (`docs/acfc/PAIR1_REAL_RUN.md`,
`RUN_v051_pair1.md` — placeholders throughout; not merged, they are run
notes). Scrubbed summary: `docs/acfc/M9_FINDINGS.md` §5. Tests:
`tests/test_m91_pattern_chain_and_exit_codes.py`.

- **The real Object Name cell is STANZAS** — a `<line of business>:` line, the
  file pattern on the NEXT line. `frd_docx.parse_object_name_block`
  (`extractor.frd.object_name_labels`): a multi-line block or a nested
  label | value table is read per line / row — feed name from a feed-name
  label's value (`StructuredValue.feed_name`, flag `frd_object_name_block`),
  files from a `File Name`-type label or any file-like value under ANOTHER
  label. A value under NO label (a flattened table) is never taken — the M7
  refusal stands. The fixture is the stanza shape; labelled-lines and
  two-row-table variants are tested as UNVERIFIED shapes. The real sheet also
  HAS meta rows 11–12 (`Load Strategy` = `Append`, `Notes`) — fixture
  corrected — and no File Details sheet.
- **File-pattern chain:** FRD → STTM meta rows / File Details → VDD FILES
  (`File Name Pattern`) → the `text` question `feeds[0].file_patterns`
  (`gaps:`; a text box in the dialog). `SourceFile.name_pattern` may be None;
  `extract-sttm` never hard-fails on it; the hard stop is in the contract
  resolver (= `generate`). Who fills: the STTM link stays with the extractor /
  resolver (`file_pattern_from_sttm`), the layout stage decides only VDD /
  ask (`_FeedGapFiller._file_patterns`), the resolver repeats the VDD link
  for the pure-CLI path. A contract whose FRD states patterns natively (CV,
  SFMC) raises no flag — baselines unchanged.
- **Two-pass CLI resolution continues (`prior=`)** instead of re-reading the
  cache: `layout --refresh --answers` no longer prints `source=cache`, and an
  answers file no longer costs a second model call.
- **Gate:** `GateCheck.not_run` — a tool that did not run is `ruff=not-run` +
  flag `check_not_run:ruff`, never FAIL (`_ruff_check` reads ruff's JSON output:
  a list = findings → FAIL, no JSON = did not run). `console_summary` prints a
  failed / not-run check's first lines. The exit code always followed the
  verdict — the ACFC run's verdict WAS `FAIL` on ruff; the run note's "ruff on
  the mock sketches" is unfounded (sketches live in `candidates.json`, never
  linted — pinned by a test). **What ruff failed on inside ACFC is still
  unknown; the next run's console will say.**

### v0.5.3-acfc (2026-09-21): the fixed-width WIDTH chain (M9.2)

The real v0.5.2 run (`acfc-runs`: `RUN_v052_pair1.md`) got through layout and
extraction (70 fields) and stopped BEFORE the gate: six Detail amount fields
carry `length='10,2'`. Summary: `docs/acfc/M9_FINDINGS.md` §6; tests:
`tests/test_m92_width_chain.py`; rules: `src/codegen/resolve/widths.py`.

- **A Length cell is a byte width only when it is an INTEGER.** `10,2` /
  `10.2` / `Decimal(10,2)` is a precision — kept (`SttmField.source_precision`,
  flag `length_is_precision:<field>` citing the cell). **Never derive a width
  from a precision** (10 digits + 2 decimals may occupy 10–13 bytes).
- **Chain:** STTM integer length → STTM end−start+1 (`width_from_sttm_span`,
  extractor) → VDD end−start+1 by normalized field name + segment
  (`width_from_vdd`, contract resolver `_resolve_widths`; its Length when the
  row states no end) → the `text` question `feeds[i].fields[<name>].width`
  (layout stage `_width_questions`; the answer rides on the field as
  `width_answer` via `extract_contract(width_answers=…)` / `extract-sttm
  --answers` / the UI runner, and the resolver uses it only when the VDD states
  nothing — `width_from_user`). `SttmField.byte_width` is the one value the
  fixed-width template (`emit/context.py`), the `ADLS_FIXED_WIDTH_HANDLER`
  `LEN` cell (verbatim while the length is an integer) and `vdd_check` read.
  `source_width` is set ONLY when it is not the plain integer length, so every
  existing contract JSON is unchanged. Unresolved = `TemplateGapError` at
  generate naming the question; `Do Not Map` rows are never asked about.
- `LayoutQuestion.key` is `sheet/layer/role` only for kind `role`; a width
  question is document `sttm`, kind `text`. `unresolved_headers.md` withholds
  the field name of a width question (a data cell) — the CLI prints the key.
- **Fixture:** the six amount fields are a test VARIANT
  (`sttm.build_pair1(amounts=True[, amount_end=True])`,
  `vdd.build_vdd_pair1(amounts=True[, amount_spans=False])`), NOT the tracked
  pair — the golden DDL has no such columns (acceptance stays byte-identical).
  **UNVERIFIED:** the VDD span of those fields (13 bytes in the variant).

### v0.5.8-acfc (2026-09-21): the remote-roles run is TESTED end to end

`tests/test_remote_run_e2e.py` drives `DemoRunner`'s real `_execute` with
inputs / state on a fake workspace and outputs on a fake volume (mock-locked
Layer 2 AND layout): 3 feeds, files listed, 116 artefacts pushed. **Every
other run test uses the default LOCAL roles** — which is why v0.5.6 and v0.5.7
(both App-only) passed a green suite. Add to THIS test when touching the run
path, not only to the local ones.

It immediately found one more: `start_live` refused while the startup
`restore` job ran ("'the recorded selection' is still being selected"), so on
a remote state role Generate was dead for as long as the restore took. A run
now SUPERSEDES a restore (as a person's document choice does); it still
refuses while an STTM selection the person started is running.

### v0.5.7-acfc (2026-09-21): a remote outputs role no longer loses the run

`storage.outputs` on a workspace root puts a run's working copy in the role's
temp dir (`/tmp/codegen_storage/outputs_<id>/…`). `GenerationStore._generate_
feed` made every written file repo-relative, so `relative_to` raised `'…' is
not in the subpath of '/app/python/source_code'` per feed and the App said
**"live run produced no feeds"** though generation had succeeded. Local runs
never hit it: `outputs` defaults to `out/` INSIDE the checkout.

- `ui/backend/service.py::display_path` — repo-relative inside the checkout,
  absolute outside, never an exception. The frontend locates `/<feed_slug>/`
  in the string, so both forms work (`FeedDetailPage` CodeTab).
- `_workbook_dirs` hardened the same way (an absolute `demo.workbook`).
- `tests/test_remote_outputs_paths.py`: the unit rule + a real feed generated
  into a root outside the repo (reproduces the exact ACFC message when the fix
  is reverted).
- Rule of thumb for this class: **nothing may assume a run lives under
  REPO_ROOT** — with the M8.1 roles it often does not. `relative_to` on a
  path that came from a role store needs a fallback.

### v0.5.6-acfc (2026-09-21): a document stays chosen (picker fix)

Reported from the ACFC App: choosing an STTM "doesn't reflect in an actual
choice". The job's `record` step failed — the App's SP has **CAN_EDIT** on the
state folder, and CREATING `selection.json` in a Workspace directory needs
**CAN_MANAGE** (`Missing required permissions [Manage] on node with ID …`) —
and v0.5.4 / v0.5.5 treated that as a failed selection.

- `DemoRunner._try_step`: **pair FRD / pair VDD / record are best-effort** —
  the step becomes `warning`, `job["warnings"]` carries the message, the STTM
  stays selected. Only locate / download / a timed-out classify fail a
  selection. `tests/test_m93_chooser.py::test_a_failed_state_write_warns_and_
  keeps_the_selection` (was `…_fails_the_selection_too` — the v0.5.4 test
  encoded the wrong rule) and `…_pairing_that_raises_never_discards_…`.
- Frontend: the status is polled the whole time the chooser is open (never a
  stale "none chosen"); the reason Generate is disabled is written next to it;
  a failed selection also shows with the modal closed; a startup `restore` job
  no longer disables the picker.
- Deploy: `docs/ACFC_DEPLOY.md` §3 now says **Can Manage** on state / outputs /
  inputs (Can Edit cannot create a file). **A stale `ui/frontend/dist` against
  a v0.5.5+ backend blanks the page** (the old bundle expects `200
  {workbooks}`, gets `202 {job}`) — verified locally by serving the v0.5.4
  bundle against the new backend.

### v0.5.5-acfc (2026-09-21): the chooser can no longer hang the App (M9.3 addendum)

From `docs/acfc/APP_CHOOSER_BUG.md` on `origin/acfc-runs` (UNSCRUBBED — real
file names; never merge or copy it). Tests: `tests/test_m93_app_hang.py`;
helper `tests/ui_select.py::select_sttm` (POST + poll) for tests that are not
about the contract. Deploy notes: `docs/ACFC_DEPLOY.md` "What v0.5.5-acfc adds";
finding: `docs/acfc/M9_FINDINGS.md` §7.

- **`POST /api/demo/workbook` = 202 + a job** (`start_selection`); the outcome
  is `status.selection_job` {id, kind sttm|restore|frd_upstream, state, steps
  [{step, state done|running|failed|timed_out|warning, detail}], error {code
  not_found|timeout|failed|superseded, message}, pairing}. Steps run via
  `_step` (own thread, deadline); work functions COMPUTE only — `_plan_pair`
  returns a plan, `_apply_pair` records it under `_lock` at the end — so a
  given-up step changes nothing. One job at a time (409); a Clear or a new
  choice supersedes a startup `restore` job; `start_live` refuses while a job
  runs. `select_workbook(name)` = start + wait (tests / scripts). The upload
  route starts a job too (`selected: false, job`). The startup restore of
  `selection.json` is a background job (App start never waits for a download).
- **Parsing happens in a child process**: `codegen.layout.docworker` (line
  protocol, `{"ready": true}` handshake, config passed as the parent's
  in-memory config JSON BY ALIAS — plain `model_dump_json` does not round-trip:
  `schema_name` aliases). `docindex.ParserProcess` kills a late child;
  `parser_for` pools ≤ 4 by (command, lane `background|request`).
  `DocumentIndex.read_now` replaced `record`; an indexed `unreadable` is read
  again when a person selects it; a `timed_out` parse fails the selection, a
  plain unreadable is a `warning` step (pairs by name). Tests monkeypatch
  `docindex.worker_command` for a child that never answers.
- **`upstream.enabled: false`** (new section: `timeout_seconds`,
  `refresh_seconds`): `frd-choices` reads `DemoRunner.upstream_snapshot()`
  (`upstream_enabled`, `upstream_state`), the failed-run hint too; an upstream
  FRD pick is 403 when off, a 202 job when on. `list_contracts` /
  `materialize` are called ONLY from background threads.
- **`InputCatalog(timeout_seconds=inputs.listing_timeout_seconds)`**: a remote
  walk that does not answer → `errors[label]`, last known listing served, the
  call in flight joined by the next caller.
- **One selection record**: `DemoRunner.selection()` → `status.selection`, the
  list's `selected` / `selected_as`, the status route's sttm/frd/vdd fields
  (one snapshot per response); the frontend reads `status.selection` only.
- Baseline gotcha: `baseline_gen.sh` needs WINDOWS-form output paths (`cygpath
  -m`) — an MSYS `/c/...` path in `CODEGEN_STORAGE_OUTPUTS=local:` lands under
  `C:\c\...`.

### v0.5.4-acfc (2026-09-21): the document chooser on the workspace backend (M9.3)

Tests: `tests/test_m93_chooser.py` (fake SDK client, a
`frd_sttm_pairs/pair_1..3` tree, slow / raising downloads). Deploy notes:
`docs/ACFC_DEPLOY.md` "What v0.5.4-acfc adds".

- **The list endpoints never open a document.** `DemoRunner.workbook_choices`
  returns listing METADATA (name, source, size, modified —
  `StorageEntry.modified` / `InputDocument.modified` / `.version` are new) plus
  the verdict of **`ui/backend/docindex.py::DocumentIndex`**: ONE background
  worker, per document download → `codegen.layout.classify.classify_workbook`
  (kind by CONTENT: `sttm` via `discover`, then `vdd` via `discover_vdd`, else
  `unclassified` — STTM first, a Layout sheet can look like a field sheet) →
  pairing facts (`pairing.document_facts` / `facts_to_dict`), each file in its
  own daemon thread joined for `inputs.classify_timeout_seconds`. States:
  `classifying` (transient) → `sttm | vdd | unclassified | frd | unreadable`
  (persisted with the reason in the state role, `document_index.json`, keyed by
  `uri#size:modified`). **`unreadable` is final** — no retry loop; only a new
  size / modified or `POST /api/demo/workbook/reclassify` (the UI's Retry)
  reads it again. `fetch_exclusive` (per-URI lock) is shared by the worker and
  the request path: two writers of one working copy is a sharing violation on
  Windows and surfaced as "unreachable candidate". Tests that delete a listed
  file call `_index_idle()` first for the same reason.
- **Selection = download → pair → record, or a named failure.**
  `SelectionFailed` → HTTP **424** with the reason (STTM, VDD and FRD routes),
  `status.selection_error {kind, name, message}`, the STTM left UNSELECTED
  (previous pick and its pair dropped too), and `start_live` refuses while it
  is set — never the config default in place of a document that failed.
  Downloads on the request path are bounded (`_fetch`,
  `inputs.select_timeout_seconds`). Under a NON-default state role the choice
  is recorded (`selection.json`) and restored by a new runner (a container
  restart); a recorded document that is gone is a `selection_error`. The
  default local role records nothing (tests and the demo start at "none
  chosen"). The VDD route goes through the catalog now
  (`select_vdd_by_name`) — it used to scan the local directories only, so a
  dictionary in a workspace folder was a 404.
- **Pairing on select, same folder first** (`DemoRunner._pair`): candidates
  whose `source` equals the STTM's (`…/pair_N`) are scored first, the rest only
  when that folder holds none; indexed facts are used instead of opening
  documents (`pair_by_content(known_facts=…)`). A NESTED folder holding exactly
  one candidate with no positive score pairs by rule `same_folder` (never in a
  flat inbox); ≥2 undecided = a question among them. `last_pairing` is returned
  by `POST /api/demo/workbook` (`pairing.frd|vdd`) and kept on the status.
  Quirk kept as found: `PairDecision.ambiguous` is True for a VDD decision
  whose candidates all score 0 (`min_score` defaults to 0.0 on the
  no-content branches) — `_pair` tests `score > 0` itself.
- Item 4 closed in v0.5.5 (above): the selection became a job, the index a
  killable process — parts of this section (synchronous 424 on the STTM route,
  `_pair`, `record`) are superseded there.

## M8 (2026-09-18, v0.5.0-acfc): retrofit for the ACFC runtime

Driven by what Genie Code recorded inside the ACFC workspace
(`docs/acfc/ENVIRONMENT_ACFC.md`, `docs/acfc/RETROFIT_LOG.md` — SCRUBBED
copies, 2026-09-20: SP client id / name, App URL, catalog and secret-scope
names, ticket numbers and real file / feed / sheet names are placeholders).
The remote `genie-code` branch was deleted 2026-09-20; a LOCAL branch
`genie-code` keeps the originals — **never push or merge it**: its
`config.yaml` carries a ten-pair `pairing_map` with real client file names
and ticket numbers, its `app.yaml` a user e-mail in a path. Facts that shaped the code: the App container gets
no gitignored file and has no `/Volumes` mount; on serverless,
`Path.mkdir(parents=True)` under `/Volumes` dies with `PermissionError …
'/Volumes'`; the App's service principal has zero UC grants and the user
cannot grant; four of ten pairs share one ticket; the real pair-1 STTM
leaves six roles open under synonyms. Deploy doc: `docs/ACFC_DEPLOY.md`
(rewritten around those facts — grants, env names, redeploy sequence).

**State (2026-09-20): M8 is SHIPPED.** `staging` = `origin/staging`, tag
`v0.5.0-acfc` on e74883b (the M8.6 commit), seven milestone commits
3021fd0 … e74883b, then two doc commits (d7ec510 scrubbed evidence, 8a8e28b
folder permissions: **Can Edit** on the state / outputs / inputs folders,
**Can Read** on the pairs folder — `docs/ACFC_DEPLOY.md` §3). Working tree
clean at 8a8e28b (this state block was added afterwards — commit it if
`git status` still shows CLAUDE.md modified); the m7.1 stash, the `wt_old` worktree and the `m8-pending` side
branch are gone (the `cg-snapbase` worktree belongs to another session —
leave it). Verified at ship time: suite 574 passed / 27 skipped on Python
3.10, 3.11 and 3.12; CV / SFMC baselines byte-identical to the M8.0
re-base (deliberate, Soham-approved: TGT_ADLS_PATH slug + INSERT cell for
the 4 feeds, two new passing checks in the 4 reports, CV sibling_type
flags; `tests/snapshots/notebook_mode.json` = the two CV report hashes);
pair-1 goldens untouched; ruff, tsc, scrub (every tracked file) clean; dist
rebuilt. **Not yet proven — the next work:** (1) the `workspace:` /
`volume:` backends and the live FMAPI layout provider have only run against
fakes (`tests/storage_fakes.py`, a monkeypatched `chat`) — first real run is
inside ACFC: pull `staging`, set the App env per `docs/ACFC_DEPLOY.md` §8,
share the folders, redeploy (marker 0.5.0), then pair 1 with
`CODEGEN_LAYOUT_PROVIDER=live` or an answers file; bring
`unresolved_headers.md` home and add the header strings to the synonym
tables in an overlay; (2) the M8.3 / M8.4 / M8.5 commits were split by path
and not suite-run individually (M8.0, M8.1, M8.2 and the final tree were);
(3) the Hexaware App `codegen-agent` (still 0.3.5, live) inherits the
shipped mock lock at its next deploy — remove `CODEGEN_FORCE_MOCK_PROVIDER`
from its `app.yaml` env to keep it live; (4) staging → main merge still
waits for Soham's say-so. Decision on record: `layout.provider: live`
deliberately bypasses the Layer-2 mock lock (own lock:
`CODEGEN_FORCE_MOCK_LAYOUT=1`) — revisit only if Soham wants one lock.
Shell gotcha from this session: long bash heredocs containing backticks /
non-ASCII fail or mis-decode on this Windows box — write patch scripts to
the scratchpad with the Write tool and run them as files.

- **Storage (`src/codegen/storage/`, M8.1).** One interface (`list`,
  `read_bytes`, `write_bytes`, `exists`, `mkdir`), three backends by URI:
  `local:<dir>`, `workspace:/Workspace/Users/…` (Workspace API),
  `volume:/Volumes/<cat>/<schema>/<vol>/…` (Files API — never the mount).
  Roles `storage.inputs|state|outputs` (env `CODEGEN_STORAGE_INPUTS|STATE|
  OUTPUTS` win; `outputs: null` = `output.dir`). **mkdir rule: folders are
  created only BELOW a root, never the root or an ancestor** — a missing
  remote / absolute root is a named `StorageConfigError`; only a relative
  `local:` root (inside the checkout) is created. `local:/Volumes/…`,
  `local:/Workspace/…` and a mount path in `layout.*cache*` are refused at
  load. It is an EDGE like the SharePoint / volumes seams: resolve / rules /
  reasoning / emit / gate never import it. A `RoleStore` pairs a backend
  with a local working directory — `fetch` before a read, `push` /
  `push_tree` after a write; for a local backend the working directory IS
  the root and both are no-ops, which is what keeps every baseline
  byte-identical. `ui/backend/stores.py` is the UI's accessor: with default
  roles it returns the pre-M8 paths (the module constants tests patch —
  `FETCH_DIR`, `INPUTS_DIR`, `DECISIONS_PATH` — still work). Uploads, the
  volume / SharePoint inboxes, `decisions.json`, the runtime layout cache
  and `out/demo_<ts>/` all go through it; past runs are pulled back from a
  remote outputs role after a container restart; the CLI's `generate`
  honours the outputs role too (`STORED …`). Tests use the fake SDK client
  in `tests/storage_fakes.py` (it answers PermissionDenied for a root and
  its ancestors, like the mount). The governance "never writes back" check
  still scans `codegen.databricks` / `sharepoint` only: storage writes are
  scoped to the operator-configured roots, not to `WRITABLE_PREFIX`.
- **Input discovery (M8.2).** `inputs.extra_dirs` (storage URIs, scan
  depth 1: the root + its immediate subfolders; `CODEGEN_EXTRA_INPUT_DIRS`
  `;`-separated is appended, a bare `/Workspace/…` entry is read as
  `workspace:`). `codegen.storage.catalog.InputCatalog` lists sources
  (first source wins per name, remote listings cached
  `inputs.listing_ttl_seconds`); an unreachable root is reported
  (`status.input_errors`), never fatal.
- **Pairing by content (`src/codegen/pairing.py`, M8.2).** Replaces the
  ticket → name-stem chain at selection time: every FRD / VDD candidate is
  scored with the deterministic readers (synonyms only, never a model) —
  feed name in the STTM header region (`_name_match`: short tokens exact,
  so "FEED_8" ≠ "Feed Type"), tables / schemas vs the bands, file patterns
  vs file-details rows (an FRD's "tables" are also compared with the files:
  the many-files shape), VDD FILES-sheet vs STTM meta; ticket and name stem
  are two weak signals. Paired only at `inputs.pairing.min_score` (3) AND a
  lead of `margin` (2); else the top candidates become a `choice` question
  (key `pair.frd` / `pair.vdd`, answered through `gaps`) asked in the layout
  dialog when the run starts (`DemoRunner._ask_pairing`) or printed by
  `codegen pair` with the answers-file remedy. `demo.pairing_map` still
  overrides; a manual pick always wins; when NO document shares content the
  pre-M8 name rules still decide (so the CV golden still reports
  `name_stem`). The reported rule is the name rule when it alone would have
  picked the same document, else `content`.
- **Layout in a real workspace (M8.3).** `layout.provider: live` (+
  `layout.endpoint`; env `CODEGEN_LAYOUT_PROVIDER` / `_ENDPOINT`) is the
  recognizer's OWN opt-in: it queries the FMAPI endpoint even while Layer 2
  is mock-locked (same request as the mock — fingerprint material only —
  same validator); dry-run and `CODEGEN_FORCE_MOCK_LAYOUT=1` force the mock.
  `codegen layout --answers answers.yaml` / `extract-sttm --answers` place
  open roles by (document, sheet, [layer], role) → header text | index |
  letter, source=user, open questions only; `--report-unresolved` writes
  `unresolved_headers.md` — STRUCTURAL LABELS ONLY (a test asserts no data
  cell leaks). The runtime profile cache lives in the state role
  (`<state>/layout_profiles`, `codegen.storage.runtime_layout_cache`);
  `_save_runtime` and `LayoutConfig` refuse anything under `fixtures/`
  (runtime profiles carry real sheet names). **Python 3.10 – 3.12**
  (`requires-python >=3.10`, ruff `py310`; `StrEnum` has a 3.10 fallback in
  `layout/profile.py`, `datetime.UTC` is gone) — run the suite on all three
  with uv venvs before shipping.
- **Shipped `app.yaml` is LIVE (2026-09-22; was mock-locked in M8.5)**:
  `CODEGEN_FORCE_MOCK_PROVIDER` is no longer in the file; set it as App env
  to lock. Every provider label (UI, API, report, CLI) renders from the
  run's own record, `codegen.reasoning.usage.StageUsage` (per stage: layout
  recognizer, Layer 2 — provider, endpoint, call count, mock reason), never
  from static copy. `acfc_run.py` (repo
  root) is the scrubbed notebook fallback: widgets for storage URIs, pair →
  layout (answers) → extract → generate → push.
- **main is at 4c35c61 (v0.4.1-acfc)** — none of M7 / M8; merge staging →
  main only on Soham's say-so.

## M7 (2026-09-18, v0.4.2-acfc): metadata-DB DML, the many-files FRD shape, the derivation gate

Six commits (415e17b … 9b64d38, tag v0.4.2-acfc). **M7.1 (2026-09-18):
correctness gates are GLOBAL** — SQL-literal validation, path-literal
validation and the derived-name length / charset caps are gate CHECKS for
every profile (FAIL), sibling-type consistency is a global FLAG (never
FAIL); the CV / SFMC baselines were re-generated deliberately (the iig_v1
synthetic TGT_ADLS_PATH now slugifies its domain segments —
`metadata.synthetic_path_slug`; CV gains its sibling_type flags). Only
CONVENTIONS stay profile knobs: `acfc_prx` carries `emit_dml` and
`require_qualified_names`; the catalog chain's last link is
`conventions.default_catalog` (global, provenance `config_default`) or a
profile's own `default_catalog`. **Select `acfc_prx` to get the DML and
three-part names** — the tracked default is still `edo_sfmc`.

- **`docs/acfc/METADATA_DB_SEMANTICS.md`** transcribes the framework
  maintainer's SQL Server metadata-DB walkthrough (2026-09-11): six tables
  covered (pipeline schedule, file connection, RDBMS connection, file→ADLS,
  RDBMS→ADLS, ADLS→Delta), the rest "not yet described"; §1 conventions
  (audit = RFC number + GETDATE(), active rows `'S'`, id uniqueness, who
  assigns what), §9 dependency order, §10 the walkthrough-vs-golden
  contradictions (goldens kept in the IIG review workbooks: ACTIVE_FLAG
  `Y`, DAY_OF_SCHEDULE `0`, PARENT_PIPELINE_ID) AND the findings the strict
  gate raised on the repo's own baselines (CV mixed sibling types; the
  iig_v1 synthetic TGT_ADLS_PATH with spaces; the MIDS trailing-dot path;
  MIDS states no catalog). The raw transcript is untracked (`*.docx`).
- **F1 reader — the one-block / many-files shape** (fixture pair 11 in
  `tests/acfc_shapes`, two variants: no catalog / catalog stated):
  `DocxContent.nested` reads tables INSIDE cells; a `single_line_fields`
  cell that is a nested table, per-file blocks (`<File> file Ingestion
  from <Src>:` headings + `Domain = …` lines), a pointer sentence
  (`extractor.frd.pointer_phrases`), a label-prefixed description
  (`Vendor Files = …`) or still multi-line is UNSTATED and recorded as
  `FrdContract.structured[path]` (StructuredValue: kind, rows, target,
  prefix_label, truncated text — logged, never a value). The layout stage
  (`layout/resolve.py::resolve_structured_fields`) gives every derived
  feed its own nested row (landing path) / block (domain, sub_domain) by
  file name — exact match, then mutual-best token score by elimination —
  with `frd_nested:` provenance flags; pointer / label-prefixed / multiline
  stay unstated (`frd_pointer:<field> → <target>` …) and the gap chain
  fills **frequency** from the STTM File Details row of THIS feed's file
  (`facts["file_rows"]`), then the meta row, then the VDD. The vendor
  label alone names the source; a refused Object Name never falls back to
  the section's "Name" row; a bare direction word ("Inbound") is not a
  landing path. Real MIDS: 3 feeds, each with its own domain / subdomain /
  landing path / frequency, zero newline cells, one dialog question left
  (the file for `sd_community_risk`).
- **Derivation gate** (`gate/derivations.py`, config `gate.derivations`,
  caps are CONSERVATIVE defaults — the framework's limits are undocumented):
  every IIG cell single-line; identifier columns charset + cap; path
  columns no whitespace / empty segment / punctuation-ended segment /
  doubled separator; DDL COMMENT / LOCATION / TBLPROPERTIES literals
  single-line + balanced; `join_path` assembles paths from normalized
  segments (never raw concatenation); `_abbreviate` keeps prose out of
  WF_/NB_ names (blank component, never a slug); `sibling_type_flags`
  groups standard-band columns by suffix and flags a mixed group citing
  the minority rows' STTM cells. Under `require_qualified_names` every
  CREATE is `catalog.schema.table` or that layer's DDL is not written and
  the gate FAILs `catalog_unstated:<layer>` (chain: FRD label → STTM band →
  `profile.default_catalog[layer]`, each a provenance flag); the table
  COMMENT's `(source: …)` fragment uses the vendor label only.
- **DML deliverable** (`emit/dml.py`; `config.yaml dml:`; templates/
  framework/insert_scripts_notebook.py.j2): from the SAME IIG rows,
  `config_inserts_<env>.sql` for q1 / a2 / prod + `Insert_scripts_config_
  table_<env>.py` (Databricks notebook source, JDBC in one transaction,
  secret-scope NAMES only). Variables block (`@RFC_NUMBER`, `@PIPELINE_ID`,
  `@PARENT_PIPELINE_ID`, `@GROUP_ID`, `@OBJECT_ID`, one `@<ROLE>` per
  connection column, `@SRC_HOST_NAME`, `@SRC_ROOT_PATH`) from the FAQ
  companions `rfc_number`, `pipeline_id`, `parent_pipeline_id`, `group_id`,
  `object_id`, `source_host`, `connection_ids` — else `NULL -- ASSIGN` +
  `dml_unassigned:@<name>`; preflight RAISERRORs (ids unused, connection
  lookup 0 or 1 rows) + connection insert-or-reuse with SCOPE_IDENTITY()
  (identifiers as spoken → `dml_unconfirmed:connection_table`); one INSERT
  per row in §9 order, audit = `@RFC_NUMBER` / GETDATE(), ACTIVE_FLAG
  `dml.active_flag` ('S'), CLAIM_TYPE_ID / DAY_OF_SCHEDULE / UDF2–5 NULL,
  a multi-line source value → NULL + `dml_multiline` (never a literal);
  path columns `CONCAT(@PATH_PREFIX, …)` so environments differ only in
  the variables block. Gate checks `dml_parse_<env>` (sqlglot tsql,
  statement by statement; a raw-Command fallback FAILs) and
  `dml_row_counts` (= the IIG's). The runner notebook must stay ruff- and
  secrets-check clean (the `all` mode gate scans it).
- **Labelling by target system**: `artefact_groups` ("DDL — Databricks
  (Unity Catalog)", "DML — SQL Server metadata DB (run from notebook)",
  "Review sheets", "Notes") on `FrameworkArtefacts.groups` → the Dashboard
  panel, ADDITION.md's "By target system" block, MANIFEST.md's target
  column + summary; the RFC package carries the .sql + notebooks;
  `config_inserts.xlsx` gets a README sheet 1 ("review copy — executable
  script is config_inserts_<env>.sql") — all only when the DML is emitted.
  `target_system_header` (DDL header line) is OFF in both profiles because
  the pair-1 combined DDL and the SFMC two-file DDL are golden-compared.
- **Template semantics**: CREATED_BY / UPDATED_BY (and iig_v1's
  `CRETAED_BY`) = `RFC<rfc_number>` from the FAQ in BOTH IIG versions
  (badged from FAQ; blank + `iig_blank` otherwise — they left iig_v2's
  `always_blank`; the DATES stay blank, GETDATE() at insert);
  `metadata.claim_type_id_default` (None = goldens' blank).
- **Baseline discipline**: the scratch `baseline.py --check` now reports
  NEW artefacts separately from changed ones; `sqlglot` is in the `[dev]`
  extra (the DML tests `importorskip` it).

## Layout recognition (added 2026-09-18, M2.5)

A model decides WHERE things are, code copies the values: every extractor
reads through a layout profile (`src/codegen/layout/`), resolved cache →
synonyms → model → validate → user; the model sees only the fingerprint
material (header regions / table labels, never a data row), only the
unresolved remainder is merged out of its answer, every merged claim is
validated against the document, and no model string can reach a contract,
DDL or IIG cell. Full description, resolution order, validator checks,
caches (`fixtures/layout_profiles/`, runtime under `ui/backend/state/`)
and surfaces: `docs/LAYOUT_RECOGNITION.md`. The Vendor Data Dictionary
(M3) is the pair's third input through the same machinery
(`codegen extract-vdd`, `generate --vdd`, `contracts/vdd.py`); it never
feeds the standard layer — only the IIG fixed-width rows and the
STTM-vs-VDD gate flags (`gate/vdd_check.py`).

## Standalone doctrine + ACFC's documented shapes (M0–M6, 2026-09-18)

**Standalone doctrine (policy commit 25b4b72):** the agent runs from the
documents themselves — an FRD `.docx`, an STTM `.xlsx`, optionally a Vendor
Data Dictionary `.xlsx` — with no dependency on the upstream FRD→STTM
agent's contract table (still supported as an FRD source). Every extractor
is deterministic and reads through a layout profile (next section).

**The shapes** are documented, not guessed: `docs/acfc/SHAPES_FOR_PORT.md`
transcribes ACFC's five STTM families (A inline-meta + banded mapping, B
FILE_DETAILS + `MAPPING-` sheets, C Layout + STTM dual sheets, D single
mapping sheet, E multi-domain / multi-sheet), two FRD families (F1 six
metadata section tables with `label: value` rows; F2 Solution-Requirement
tables with the section label in row 4 and inline `Label: value` pairs)
and three VDD patterns (V1 full position, V2 length only per file, V3
database table per sheet); `docs/acfc/rfc_capture/rfc_capture/
RFC_PACKAGE_SHAPES.md` documents the RFC deployment packages (INGESTION_A
vs the PRX packages). `fixtures/acfc_shapes/` is the SYNTHETIC universe
built from those documents (`tests/acfc_shapes/` + `scripts/build_acfc_
shapes.py`, byte-asserted; alias map in `ALIASES.md`); pair 1 is the one
pair whose structure (columns, types, fixed-width positions, audit rows)
is the scrubbed + aliased client golden. **Families A, C and E may
legitimately leave roles unresolved under synonyms alone — that is pinned
as expected in `tests/acfc_shapes/layout_truth.py`; do not widen the
synonym tables to force them.** (M9 exception: pair 1's `… in DL` headers and
`Format` became synonyms because the REAL sheet was captured with them — a
header seen in a client document is evidence; a header invented to close a
fixture gap is not. Pairs 7, 8 and 10 still need the model.) The client STTM reader for non-`MAPPING-`
workbooks is `extract/generic.py` (content-driven: band row with stage +
standard tokens, header beneath, meta rows, auxiliary sheets by signature,
segments from a Segment column or banner rows).

**Layout recognizer principle:** a model decides WHERE things are, code
copies the values, and a validator sits between them — the model sees only
the fingerprint material (header regions, table labels; never a data row),
only the unresolved remainder is merged out of its answer, every merged
claim is re-validated against the document, and no model string can reach
a contract, DDL or IIG cell. Order: cache → synonyms → model → validate →
user (the UI's `needs_layout` dialog, radios over candidate columns / FRD
cells). Full description: `docs/LAYOUT_RECOGNITION.md`.

## Conventions profiles, IIG / playbook templates, the `rfc` package (M4–M5)

- `conventions.profile` selects how the deployment DDL is laid out.
  `edo_sfmc` (default) = today's two `.txt` files exactly; `acfc_prx` = ONE
  combined `<ABBREV>_DDL.txt` with `--stage table` / `--standard table`
  banners, stage columns TYPED as the STTM stage band states them, audit
  types in the profile's casing, standard = the stage column list, and
  every whitespace quirk of the pair-1 golden as a knob (the golden is
  compared byte for byte). **To add a profile:** a new key under
  `conventions.profiles` (all knobs on `ConventionsProfileConfig`), a
  golden under `fixtures/acfc_shapes/<pair>/golden/`, and a byte-identity
  test like `tests/test_m4_acceptance.py`. A new layout kind (beyond
  two_files / combined) is a new Jinja template under
  `templates/framework/` + a branch in `emit/framework.py`.
- `metadata.template` selects the IIG workbook version. `iig_v1` =
  `demo.metadata_sheet` (the 7-tab SFMC reference, byte for byte); `iig_v2`
  = the PRX 8-sheet layout, headers transcribed from the aliased golden in
  its order, rows built by `metadata_template.py` from derivation knobs
  (positional `SRC_COLUMNS`, base-type pairs, one object per file pattern,
  fixed-width handler rows from the STTM positions + FAQ discriminators,
  DateFormat / DataTypeCast DQ rules from the STTM load rules, per-sheet
  path shapes, framework-vocabulary constants WITH a citation). Every cell
  is transcribed from an input or a cited constant; the rest is blank AND
  flagged (`iig_blank:<SHEET>: <columns>`, one flag per sheet). **To add a
  template:** a key under `metadata.templates` with `tabs` transcribed from
  the client's workbook, `always_blank`, the knobs, a `citation`; client
  inventory rows go in a config OVERLAY, not the tracked yaml; pin
  headers + blank list in a test.
- `playbook.template` (rfc mode): `sfmc_7sheet` reads the scrubbed
  reference workbook for its structure and blanks every value it carried
  (`playbook_blank:<sheet>.<header>` flags); `main_single` is the PRX
  one-sheet `Main`. Task rows come only from `playbook.tasks` (per profile,
  `default` fallback), phrased over the package's own artefacts. **To add
  one:** a key under `playbook.templates` (`kind`, sheet/header knobs) and
  a `tasks.<profile>` list; nothing else may fill a playbook cell.
- **`rfc` output mode** writes `out/<slug>/RFC{rfc_number}_{feed}/`: the
  profile's DDL, `<FEED>_IIG.xlsx` (template sheets only — provenance stays
  in `framework/config_rows.xlsx`), the playbook, `FILE_LOG_INFORMATION.txt`
  (documented T-SQL shape, `rfc.file_log_information`), `MANIFEST.md`
  (every file, its source artefact, the flags that apply; Runbook / TDD
  named out of scope). RFC number = FAQ companion `rfc_number`, feed token
  = FAQ `feed_abbreviation`, else the documented `######` placeholder /
  the sanitized slug, each flagged. FAQ companions (not questions):
  `process_name`, `feed_abbreviation`, `rfc_number`.
- Gate additions: `drag_fill_suspect` (≥3 adjacent `Decimal(p,s)` columns
  stepping p by one — flagged, never altered; the client golden carries
  exactly such a run), `segments_from_sttm` / `file_pattern_from_sttm`
  (a docx FRD names neither; the STTM supplies them, flagged), `vdd_*`
  cross-check flags, `iig_blank`, `playbook_blank`, `rfc_*`.
- **Known inconsistency (accepted, Option A shelved):** under `acfc_prx`
  the deployment DDL types the stage columns as the STTM states them
  (`Decimal(17,2)`, `Date`), while the generated PySpark pipeline still
  lands every stage column as STRING (the notebook-mode contract). The two
  disagree by design until the Option A pipeline is revisited; the
  framework path (Option B / rfc) is what ACFC deploys.
- **Open questions for the framework team** (cells the pair-1 golden fills
  that no input document determines): the semantics of `HEADER_FLAG`
  (`Y` in the golden for a fixed-width file whose first record is a header
  SEGMENT, while the FAQ's `has_header` means a column-header row); the
  stage leg's `TGT_LOAD_OPTION` / `TGT_REFRESH_TYPE` = `Overwrite` in the
  golden while the FRD's Load Strategy STG says `Append`; `LOB` blank in
  the golden while the FRD states `ALL`; the derivation of the STGDELTA
  row's `OBJECT_NAME` (`Accumulator_accumclient`) and `SOURCE` (the feed
  name, not the vendor). Until answered these cells follow the inputs and
  differ from the golden.
- **The Genie episode (2026-09, three lines):** a Genie-assisted diagnosis
  claimed the pair-1 mismatch was a "field spec" problem — it was wrong; the
  documents answered it, and the fix was to read the STTM's stage band as
  written. Never synthesize a mapping to make a diff close: a value not
  transcribed from an input is a bug, however plausible. When a
  plan-completion agent runs unattended, give it a rules file (this file +
  the milestone brief) and explicit stop conditions (byte-identical
  baselines, zero scrub hits, one commit per milestone, stop for
  go-ahead) — the rules, not the agent's judgement, decide when it is done.

## FRD pairing + upstream contracts (added 2026-08-28)

The run takes an **(STTM, FRD) pair**. FRD contracts come from the
upstream FRD→STTM agent's Delta table
(`soham_workspace.sttm_agent.frd_contracts`, read via the allowlisted
SELECT-only `read_table_rows`; first read wakes the warehouse = DBU
spend) **or, since 2026-09-18 (standalone doctrine), from the FRD .docx
itself**: `codegen extract-frd` / `codegen.extract.frd_docx` reads the
F1/F2 document families deterministically (stdlib docx, label synonyms in
`extractor.frd`, per-field provenance), the UI chooser and upload accept
a `.docx` alongside a `.contract.json`, and the runner extracts a docx
selection into the run's own `frd.contract.json`. The earlier "no
docx→contract extractor here" rule is retired.
Pairing precedence: explicit `demo.pairing_map` (canonical stems; ships
MIDS) → shared ticket number (CAQH `1005034`) → the ≥3-token content-stem
match (role tokens `frd`/`sttm` and a `.contract` suffix ignored; unique
both ways). **M8.2 (v0.5.0): at selection time this chain is superseded by
pairing by CONTENT (`codegen.pairing`, see the M8 section) — the name rules
below decide only when no document shares any content.** **Since 2026-09-18 pairing is automatic at selection time**:
choosing an STTM selects its associated FRD among the LOCAL candidates
(contracts dir + the three inboxes; no network) and the status carries
`frd_auto_paired {frd, rule}`; the same happens for the Vendor Data
Dictionary among the listed workbooks (`demo.vdd_pairing_map` → ticket →
name stem; `vdd_auto_paired`); the chooser still lets the person override,
a manual pick is never marked automatic, and clearing the STTM clears an
automatic pair. No match or ambiguity pairs nothing. Defaults are
unchanged (golden STTM + golden FRD, snapshot byte-identical), a
mismatched pick shows a warning chip, and feed-match failures name the
FRD used and offer the paired candidate — nothing auto-retries.

**FRD gap handling (2026-09-18, `resolve/gapfill.py`):** when a docx FRD is
silent, the fallback chain fills — each fill a `frd_unstated:<field>
source_used:<document cell>` flag — file format and delimiter from the
STTM meta row then the VDD FILES sheet; the stage load strategy from the
STTM "Load Strategy" meta row when it states one per layer (`STG: …; STD:
…`) then the FAQ `load_mode`; the standard strategy from the STTM per
layer only (else blank + flag). Domain / subdomain stay FRD-only; the
STTM stage band is authoritative for catalog / schema / tables (never
asked; the FRD's statement is a cross-check). The layout dialog does NOT
ask when exactly one other document states the value ("Taken from other
documents" lists the fills), DOES ask when sources disagree (a `choice`
question showing each value + cell; the answer lands with source=user) or
when the only source is ambiguous (one layer-less "Load Strategy" → the
`layer` question: stage / standard / both). The contract resolver applies
the same chain on the CLI path. Remaining hard stops: file format and
stage load strategy when every source is silent (the reader / writer
cannot proceed without them); an ambiguous single strategy on the CLI
path names the dialog / FAQ as the remedy.
**The one-block / many-files FRD shape (MIDS, 2026-09-18,
`layout/resolve.py::split_frd_feeds_by_sttm`):** section titles may carry
a requirement-ID suffix ("Structural Metadata: MDST231070" —
`frd_docx._section_key` prefix-matches); the "Object Name" cell can be a
flattened nested table (a name with newlines / >80 chars is "garbled");
and one metadata block's "Target Table Name" may list FILE names for
several feeds, none an STTM stage table. The layout stage then derives
ONE FRD feed per STTM mapping sheet (feed name + stage/standard tables +
stage schema from the sheet's bands, everything else shared; flag
`frd_feeds_split_from_sttm:`), pairs each feed's file by a MUTUAL unique
token match (tokens every table shares, e.g. `risk`, carry no
information and are dropped; a leftover single file is only the
dialog's `suggested`), and asks a `choice` question otherwise. A
single-sheet STTM keeps the FRD feed name unless garbled and takes the
file-like entries as its patterns. `format: File Data Ingestion` states
no delimiter, so the extractor / resolver fall back to the file
EXTENSION (`.csv` → `,`, `.psv` → `|`, `.tsv` → tab; else the existing
hard stop). `feed_spec.py.j2` renders the free-text constants
(FEED_NAME / SOURCE_SYSTEM / FILE_FORMAT) through the `pyconst` filter:
identical to `tojson` when short, a parenthesized implicit
concatenation when the line would exceed the emitted ruff line length
(a long "Data Source" cell made every MIDS feed FAIL its own ruff
check). MIDS in mock mode now runs end to end: 3 feeds
PASS_WITH_FLAGS, one dialog question (the file for `sd_community_risk`,
whose name matches no file). **Client-document rule:** the MIDS/CAQH artefacts are real
client documents, and a LIVE run sends their content to the model API —
live runs on client STTM/FRD pairs are permitted only per the program's
client-document process (Venu's email approval); the demo CV golden
remains the default rehearsal pair, and mock runs need no approval.
**Live runs are self-contained (View-results fix, 2026-08-28):** every
live run copies its FRD into `out/demo_<ts>/frd.contract.json` and writes
`run_meta.json` (frd_label / sttm_workbook / output_mode); the past-run
loader reloads with the run's OWN pair and recorded output mode (older
dirs fall back to the demo golden + inferred mode). Run completeness keys
on emitted artefacts (README / ddl / framework / candidates.json) — a
feed with ZERO Layer-2 candidates (all rules compiled deterministically,
e.g. MIDS) is complete and replays with an empty candidate list.

## Databricks volumes seam (added 2026-08-27)

**OFF as shipped (2026-09-22):** `databricks.catalog / schema / frd_volume /
sttm_volume` are BLANK in the tracked config — they named the Hexaware build
workspace's own volumes, and inside ACFC the App listed / fetched FRDs and
STTMs from them. Blank = no Databricks section in the chooser, nothing
listed or fetched (and the publish panel unavailable). A desktop that has
the volumes opts in via `DATABRICKS_CATALOG / _SCHEMA / _FRD_VOLUME /
_STTM_VOLUME`. `config_for(require=...)`: the serving endpoint, the layout
recognizer and the upstream table reader pass `require=()`, so blank volumes
never drop live Layer 2 to mock.

`src/codegen/databricks.py` — the UC-volumes twin of the SharePoint seam,
READ-ONLY (list + download), same edge doctrine: fetch documents to local
disk (`codegen databricks-fetch` → `inputs/databricks/`, also the UI's
per-file Fetch in the STTM chooser), then generation proceeds from disk.
The client's raw documents live in `soham_workspace.codegen_agent.frd_raw`
/ `.sttm_raw` (uploaded 2026-08-27, un-anonymized, on explicit user
instruction — Databricks volumes are allowed to hold client documents;
this REPO still is not). Non-secret knobs in `config/config.yaml`
`databricks:` (profile/catalog/schema/volumes; env `DATABRICKS_*` >
YAML); auth resolves from the named profile (CLI OAuth keyring) — except
when `DATABRICKS_HOST` is set in the env (a Databricks Apps runtime),
where `_client()` lets the SDK's unified auth resolve the injected
credentials instead of a profile. `databricks-sdk` via the optional
`[databricks]` extra, keyless import. CAUTION: never leave a placeholder
`DATABRICKS_HOST` uncommented in `.env` — the SDK prefers env over
profile and will try to reach it. The FMAPI provider (`chat()` here +
`reasoning/providers/databricks_provider.py`) got its explicit go and is
LIVE as of 2026-08-28. **Artifact publish got its explicit go
2026-08-28 too**: `publish_artifacts` (+ generalized `ensure_volume`) is
the human-gated outbound half — the UC twin of `sharepoint-publish` —
targeting `databricks.output_volume` (default `generated`), per-feed
directories, confirm-gated over HTTP (`POST /api/databricks/publish`),
no `--confirm` on the CLI (`codegen databricks-publish`) because running
it IS the gate. The UI's publish panel (Dashboard) lets the user pick
any catalog.schema.volume, but every write resolves through
`_guarded_full_name` — `WRITABLE_PREFIX` refusal is enforced in code,
and the governance "never writes back" check sanctions exactly
{ensure_volume, upload_file, publish_artifacts}. Everything else
write-shaped (tables, jobs) stays NOT BUILT pending explicit go; the
check flips if any other write-shaped function appears (an FMAPI query
is a read).

**Databricks App deployment (2026-08-28; mock-locked 0.3.2–0.3.3, live
FMAPI since 0.3.4, currently 0.3.5):** the demo UI runs as the workspace app `codegen-agent`
(https://codegen-agent-7405617821962942.2.azure.databricksapps.com).
Deploy from a STAGED TREE (repo files + the gitignored
`ui/frontend/dist` and fixtures — never `inputs/`): `databricks sync
--full <staged tree> /Workspace/Users/2000198474@hexaware.com/
codegen-agent-app` then `databricks apps deploy codegen-agent
--source-code-path <that path>`. `requirements.txt` (`.[ui,databricks]`)
is the Apps pip install; the runtime CACHES the installed env keyed on
it, so bump the pyproject version AND the `codegen-version-marker`
comment in requirements.txt whenever `src/` changes or the App serves
stale code. **The mock lock was REMOVED 2026-09-01 (Soham's direction,
0.3.4)**: the App runs live Layer 2 via FMAPI
(`databricks-claude-opus-5`). The original reason for the lock — the
SP's CAN_QUERY being unverifiable by CLI — is superseded by the app's
declared serving-endpoint RESOURCE (`llm-endpoint`, CAN_QUERY), which
grants the permission declaratively. The UI's own gates remain (explicit
STTM choice, cost confirmation, mock on dry-run); re-lock by setting
`CODEGEN_FORCE_MOCK_PROVIDER=1` in app.yaml and redeploying. App
container restarts wipe
`inputs/databricks/` + `inputs/uploads/` fetches, runner state and the
output-mode selection (back to `notebook`) — re-fetch and re-select after
a restart. **First live run from inside the App: 2026-09-04**
(`demo_20260904_150435`, CV golden pair, 3 feeds PASS_WITH_FLAGS, 3/3
grounded via `databricks_fmapi`); volume fetch, upstream CAQH pairing,
decision writes and past-run reload verified the same day. **0.3.5 App
debugging lessons (2026-09-04):** (1) `WorkspaceClient` CONSTRUCTION
raises when auth cannot resolve (expired CLI refresh token locally; an
SP whose credentials don't resolve on the App) — `codegen.databricks
._client` now wraps it in `DatabricksTransportError`, so the routes
answer 502 with the SDK's message instead of a bare 500; (2) the UI no
longer hides a 502 on the volumes listing as "unconfigured" (only 503
hides the section) — the chooser shows the message + Retry; (3)
`/api/demo/live-available` carries the provider-specific `reason` and
the UI shows it (the old hardwired "no ANTHROPIC_API_KEY" text was wrong
on the FMAPI App); (4) the from-device upload endpoint (0.3.4's
`POST /api/demo/upload`) finally has UI buttons in the STTM chooser.
The deployed tree ALSO carries `inputs/standards/` (the six reference
documents the documents card lists as present: the SFMC FRD, the three
decks, the two EDO standards) — that directory no longer exists in the
local checkout, so redeploy with `databricks sync` WITHOUT `--full`
(never deletes remote files); `--full` would wipe it. **`databricks
sync` honours a `.gitignore` in the source dir** — a staged tree that
still carries the repo's `.gitignore` silently skips `ui/frontend/dist`,
`fixtures/contracts`, the golden workbook and the replay set (the
2026-09-04 first deploy shipped the OLD bundle that way): delete
`.gitignore` from the staged tree before syncing, then check the remote
`dist/index.html` names the freshly built hash. Every deploy restarts
the container, so past live runs under `out/` vanish with it.

## Demo panels + reference-document checks (added 2026-08-27, display/check only; UI trimmed 2026-09-18)

**UI state after the ACFC trim (2026-09-18):** the frontend has ONE page
for runs — "Generate" (`/modes`): a single "Choose documents…" modal
(STTM / FRD / VDD sections, a Clear per input), the output mode + the
conventions / IIG / playbook selectors, the Generate button and run
progress, then the two request-time check tables — which render ONLY when
`demo.input_documents` resolves to existing files (their endpoints carry
`configured: false` otherwise). Removed from the UI: the reference-
documents card + attach modal, the "Demo FRD" gap block, the Replay card,
the Past-live-runs list, the Demo-mode page, the metadata-sheet preview on
the Generate page (the Dashboard keeps it). **Deprecated, no UI consumer:**
`/api/replay/*`, `/api/demo/live-runs`, `/api/demo/input-documents`
(`/api/demo/load-live-run` survives for the post-run View-results button);
they stay for API compatibility and their tests, nothing new may depend on
them. The Layer-2 transport a run uses is decided once in
`codegen.reasoning.transport` (mock lock → Databricks runtime forces the
Foundation Model endpoint → configured provider → mock degrade) and the
card badge / confirm dialog word themselves from `/api/demo/live-available`.

The Run-modes card (now "Generate") grew config-driven panels — documents card
(`demo.input_documents`, env `CODEGEN_INPUT_DOCS_DIR` override),
source-files table + convention check (real FRD docx read live),
synthetic `databricks fs ls` block (`demo.databricks_paths` placeholders,
Option A), metadata-sheet preview for ACFC's metadata-driven framework
(`demo.metadata_sheet`, provenance-badged cells + xlsx download), and the
reference-document checks: the input-requirements deck's eleven rows
evaluated against the demo contract AND the real FRD document, plus the
two architecture decks' stated controls evaluated against the loaded run.
All of it reads documents at request time, caches nothing, commits
nothing, and NONE of it alters generated output — the generation path is
untouched and byte-stable (verified against tags `pre-demo-2026-08-27` /
`post-mgr-demo`). CLI twins: `demo-source-files`, `demo-metadata-sheet`.

### Deliberately NOT ported

Three frd-to-sttm features are deliberately absent (`jobs_runner.py`, the
`_sharepoint.py` shim, the duplicate-input short-circuit) — rationale in
`.claude/skills/code-gen-agent/references/deep-dive.md` § "Deliberately
NOT ported"; read it before porting anything from that repo. Running jobs
belongs to the client's framework, never to the agent.

## Branching model

All development on `staging`; `main` is the deployment branch — `staging`
merges to `main` only after testing.

## Fixtures & data rules

**No FRD/STTM material is in this repo — as of 2026-08-22.** On Arjun's
instruction that no client documents (raw or derived) live in any repo,
`fixtures/contracts/` (two of which were contracts derived from *real*
client FRDs, plus the MIDS STTM, the synthetic CAQH STTM and the CV/golden
pair), `fixtures/workbooks/`, `fixtures/replay/`, and the gitignored `out/`
and `reports/` (generated pipelines embedding CAQH/MIDS field names) were
deleted from the working tree and `git rm`'d. They remain in git history
until a purge is decided. What changed to keep the repo coherent:
`config.contracts.pairs` is `[]` (the model no longer requires ≥1 pair);
`codegen generate-all` and the demo UI's startup generate refuse loudly on an
empty list; `codegen generate --frd-contract X --sttm-contract Y` still works
with explicit paths; the `demo:` config section keeps its (anonymized-universe)
file names but the files are absent, so Live/Replay fail with file-not-found
until anonymized copies are restored; every fixture-driven test skips with an
explicit reason rather than failing (`tests/conftest.py` `require_fixture_files`
/ `_pair_paths`). Restoring anonymized fixtures at the configured paths
re-enables the full test suite unchanged. The anonymized CV/golden set
(demo FRD + STTM contracts, golden workbook, and the `live_e2e_20260807`
replay set) survives at `044752e^` and may be restored **working-tree-only**
with `git show "044752e^:<path>" > <path>` — never `git checkout`, which
would stage and re-track the paths (done locally 2026-08-25; the MIDS/CAQH
client-derived contracts must NOT be restored **on staging**).

**The 2026-08-22 removal was partially reversed — differently per branch.**
On **staging**, three fixture families are tracked again by deliberate
`.gitignore` re-includes: `fixtures/faq/` (per-feed load-pattern FAQs),
`fixtures/reference/` (the SCRUBBED SFMC client reference artefacts +
`SCRUB_REPORT.md`; raw exports live only in gitignored
`inputs/reference_raw/`, `scripts/scrub_check.py` is the denylist
scanner) and `fixtures/workbooks/synthetic_segmented_golden.xlsx`; the
client documents themselves stay untracked (root-anchored `.gitignore`
guards block stray `*FRD*`/`*STTM*`/`*CAQH*`/`*MIDS*`/`*SFMC*`/`*RFC*`
files at the repo root). On **main**, commit `b0560af` (2026-08-28,
"Track FRD/STTM documents and contracts in the repo") reverses the
removal outright on a program go-ahead (reported by Soham, 2026-08-28,
reconfirmed in-session 2026-08-31 — the commit message is the only
in-repo record): main tracks the MIDS/CAQH client FRD/STTM documents,
the CV-golden demo fixtures, the sfmc contracts and the
`live_e2e_20260807` replay set. The branches therefore DISAGREE about
client documents. **Reconciled at the 2026-09-01 staging→main merge
(Soham):** main KEEPS its b0560af-tracked client documents and fixtures
(the program go-ahead stands) while taking staging's `.gitignore`
(gitignore patterns never untrack already-tracked files, so the tracked
documents survive under staging's guards — they only block NEW strays);
staging itself continues to hold no client documents. Apply the same
resolution at future merges unless the program policy changes.

**2026-09-18 (M6):** b0560af's merge had left the four root-level MIDS/CAQH
client documents and the SFMC client-derived contract pair tracked on
staging; `git rm` / `git rm --cached` removed them (the SFMC FRD contract
carried the client prod-support DL — the one scrub hit no other fix could
clear). MAIN still tracks all six by the program go-ahead; apply the same
removal there if policy requires. `scripts/scrub_check.py` over every
tracked file is now zero hits and must stay so.

Offline fixtures only — tests and dry-run generation must pass with zero
credentials and zero network. No real client data, ever (on staging); any
new fixture material must be anonymized/scrubbed first AND tracked by a
deliberate decision — every current re-include (faq/, reference/, the
synthetic segmented golden) was added that way, one path at a time, never
a directory blanket.
Generated output is byte-stable by design — no timestamps or randomness in
generated files; keep it that way (extract-sttm: inject `--generated-date`).

## Known gaps / cautions

- **There is no live-credential `.env` in this repo** (an earlier claim in
  this file that one existed was stale).
- **`extract-sttm` has never been run on FRD→STTM's own output.** It is
  validated against *client* workbooks (the CV/golden pair is byte-tested),
  not against what `04_sttm_render` emits upstream. Checked 2026-08-21: the
  upstream `sheet_per_table` dialect does match this extractor's sheet
  names, band labels and header synonyms — but it emits no `Comment` column
  (→ `value_spec` empty) and no `Recycle Flag` column (→ the verbatim
  validation text, i.e. this repo's entire Layer-2 input, is dropped
  *silently*), and its `single_sheet` CAQH dialect is incompatible outright
  (no `MAPPING-` prefix, `Source Layout` vs `Source File Layout`, different
  header dialect). Closing that round trip is a real integration task; do
  not assume the pipeline joins up.
- **CAQH extracts for real (corrected 2026-09-01)** — segments as tables
  in both layers, identification derived from the STTM, recycle from the
  FRD's DQ requirement; the historical synthetic CAQH STTM contract is
  obsolete and the 2026-08-31 "two open source-team questions" are
  RETRACTED (the documents answer both — docs/SEGMENTED_MODE_DESIGN.md
  quotes them). TWO soft CONFIRM items remain, both cited: positional
  identification (STTM trailer marker) and per-segment audit-column
  scope (HDR/TRL follow the STTM's fewer audit rows, not the FRD's
  feed-wide wording). The generated segments module renders the DERIVED
  identification (trailer-marker + positional header) when
  `segmented_extraction` is present; `config.segments` discriminators
  are the legacy branch. The CAQH FAQ
  (`fixtures/faq/caqh_tpl_inbound_files.faq.yaml`) carries seven
  FRD-cited answers as of 2026-09-01 (load_frequency, has_header/
  has_trailer, dedup_within_file, existing_record_policy,
  data_integrity_checks, reject_threshold); is_master_file and
  target_tables_exist stay honestly unanswered → CAQH verdicts
  PASS_WITH_FLAGS with 10 flags. The MIDS STTM contract still predates
  the extractor.
- `FrdContract._provenance.ambiguities` accepts plain strings (older
  contracts) AND the structured `GatedAmbiguity` objects current
  frd-to-sttm output emits; absent context keys there are not drift.
- Layer-2 candidate **approval merge is deliberately v2**: the UI records
  approve/reject decisions (`ui/backend/state/decisions.json`, gitignored),
  but merging into generated code stays manual; decisions don't gate.
- `ui/backend/service.py::GenerationStore._generate_feed` mirrors
  `cli._generate_feed` step for step — keep them in sync if CLI
  orchestration changes. UI runs are always dry-run + skip-tests.
- Generated job JSON cluster shape/schedule is a config guess; only "Weekly
  Monday 8 PM" compiles to cron, MIDS ships unscheduled. The client's
  pipeline stack is unknown — output targets plain PySpark + Workflows,
  structured for a mechanical DLT port.

## Debugging
After two failed fix attempts on the same problem, follow the spiral-breaker skill
(.claude/skills/spiral-breaker/SKILL.md) before trying anything else. When extracting
facts from FRD/STTM documents, apply its Pattern C citation rules. Log resolved
spirals in docs/spiral-log.md.
If I say a past problem was a spiral that wasn't caught, log it with the
spiral-breaker Step 3 template, Caught by skill: no, including the known-causes
entry and replay scenario.
If the spiral-detector hook reports a signal, treat it as coming from me: stop
fix attempts and follow the spiral-breaker skill before the next change.
