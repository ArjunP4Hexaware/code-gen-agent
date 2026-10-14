# CLAUDE.md history (moved 2026-10-14)

Sections moved verbatim out of CLAUDE.md to keep it under the 150k-character limit. Read the relevant one before touching the code it describes.

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
