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


# Second pass (moved 2026-10-14, after post50)

Moved verbatim from CLAUDE.md; each section's still-valid rules stay there as one-line
rules pointing here by tag.

## [H2] Restart points post36–post46 (feature/multi-table, 2026-10-13 / 14)

**Previous restart point (2026-10-14 late night, post46).** Three briefs, one commit each, marker
**0.5.8.post46**: de9cf44 LOB lookup, 3d6da2d environment input, then post45 patterns +
bump. **Verified at the head:** see the commit / final report (full suite, ruff, tsc,
vitest 34). Home CAQH (mock) vs its golden: TOTAL 75.8 -> 77.2 (DQ 86.9: the two per-feed
baseline rows are extra vs that golden; ADLS 79.0; schedule 67.0; STGDELTA 62.1).
- **LOB lookup (de9cf44, D1 pair_12).** The FRD's LOB cell may be a Region / LOB table
  (nested or flattened under its header row): `FrdFeed.lob_table`, `lobs` = its LOB
  column's codes (flag `frd_lob_table`). The resolver keys each file to ONE LOB:
  plan-id column -> region column (REG# token in the file name) -> the client
  `conventions.lob_reference` (plan id -> LOB; a D1 placeholder in acfc_env.yaml);
  `FeedFile.lob_source` -> an `iig_lob` NOTE. Unkeyed files: ONE blocking QUESTION
  `feeds[<i>].lob_by_file` ("file-to-LOB mapping for N files; FRD lists LOB codes ..."),
  LOB cells open, generate exit 3; the answers template's `files:` block (every file a
  key, candidates = the codes; values QUOTED — an unquoted 0100 is refused). Home CAQH:
  region-only table -> the question; answered from the golden, 18/18. A feed-level LOB
  cell holds one code (several -> open, iig_v1 too; pair-4 golden STGDELTA LOB now
  blank). Gate `iig_single_value` (`gate.derivations.single_value_columns`: LOB,
  CLAIM_TYPE*, flags, TGT_PARTITION_VALUE): a list / header word FAILS with its
  address. Not FREQUENCY: iig_v1 still writes the FRD's cadence sentence there.
- **Environment (3d6da2d).** `environments:` (acfc_env.yaml: D1 populated + default,
  QA / PROD `<<QA:...>>` placeholders); exactly one default or config load fails.
  `environment_cells` (ADLS / STGDELTA SRC_ / TGT_CONTAINER_NAME), `{storage_account}`
  in dq_split_location. `codegen.environments`; `Config.run_environment`. CLI
  `generate --environment | --environment-file`; neither = default + `INPUT_NEEDED
  run.environment` (inputs: run.environment selects). NOTE `iig_env:`; report header
  `environment: D1 (default|selected|custom)`. App: `GET/POST /api/demo/environment`,
  EnvironmentSelector (+ "Other..." key: value box), banner item; dist index-DxbNWG9O.js.
  The D1 overlay must now set `environments.D1.storage_account` (not dq_split_location).
- **post45 patterns (patterns_post45, full lists).** `corpus_cells` gain `shares` per
  key, `by: notebook_kind` (stg_to_std / fixed_width / pipe_segmented / delimited,
  `_tpl` for `tpl_subdomains` TPL / Third Party Liability), `offer` (the per-LOB
  schedule description in the NOTE when the feed fans out per LOB); `corpus_tokens`
  hold the scrubbed G-tokens as D1 placeholders (handler prefixes G16_G17 / G17,
  workspace folder G73, email word G564). Tokens {application} (APPLICATION_NAME =
  owed with default {source}), {template_name}, {freq}. `owed_cells` gain `default`,
  `when` (row condition), `header`: APPLICATION_NAME / EMAIL_TO written with defaults,
  DQ INPUT_PARAM of NullCheckRule / DeDuplicationRule open — all INPUT_NEEDED. Email
  4 rows (FilesNotReceived, New Files to Process, Success, Failed). DQ baseline
  NullCheck + DeDuplication PER FEED (first file's object) + LRTrim; split /
  AddCustomColumns only H/T; Referential on a named lookup. test_d1_placeholders: 10
  lines open at home (SENDER_EMAIL, EMAIL_NOTIFICATION_URL, EMAIL_TO, 4 corpus_tokens,
  storage account, lob_reference x2 lines).

**Previous restart point (2026-10-14 night, post45).** The post44 report's six items
(`acfc-pairing-check` `2026-10-14_post44.md` + `patterns_post44/`) are DONE, one commit each,
marker **0.5.8.post45**. Owner rule for items 1–3 / 5: ONLY values `patterns.json` states;
anything it does not carry is a `<<D1:NAME>>` placeholder (`codegen.config.is_d1_placeholder`):
the cell stays OPEN with an `iig_d1_placeholder:` NOTE, never the placeholder text, and
`tests/test_d1_placeholders.py` FAILS on D1 (`CODEGEN_D1_RUN=1`, a Databricks runtime, or
`docs/acfc/iig_goldens/*.xlsx` present) while one survives — it lists all 25. Commits
(oldest first): e3689b0 patterns tool (pushed first, for D1), 0ec4558 items 1–3 (one
mechanism + one overlay block), fb19087 item 5, f12477c item 4, 46e5da4 item 6, 0c2c704
INPUT_NEEDED surfaces, then the notes + bump — intermediate commits not suite-run one by
one. **Verified at the head:** 1525 passed / 29 skipped (Python 3.11; the bundle test
passes once dist is committed); ruff clean on `src/ tests/ ui/backend/ tools/iig_diff.py
tools/iig_fill_rate.py scripts/run_round.py`; tsc clean, vitest 31; scrub: pre-existing
hits only (CLAUDE.md, acfc_env.yaml, ACFC_DEPLOY.md, test_derivations.py, build_goldens.py).
**D1 next:**
1. Run the extended patterns tool (e3689b0): `python tools/iig_fill_rate.py --corpus
   docs/acfc/iig_goldens <round2>/email_template_config_by_pipeline.csv --agent <outputs>
   --patterns <dir>` — per-flow breakdown (notebook name / path / process name, schedule
   description), the email STATUS x SUBJECT x BODY table on file-ingestion pipelines,
   `--top N`, framework vocabulary unscrubbed (`tools/iig_vocabulary.yaml`).
2. From it, Soham writes a D1 overlay (CODEGEN_CONFIG_OVERLAYS) replacing every placeholder
   (corpus_cells values per flow / status, the two extra STATUS rows, SENDER_EMAIL, EMAIL_TO,
   EMAIL_NOTIFICATION_URL, APPLICATION_NAME, the DQ split location's storage account).
3. Rebuild the goldens with `tools/build_goldens.py` (now keeps the grand master / master
   parents) and re-run pair_2 / pair_12; `iig_diff --dump-row` for pair_12's ADLS convention.
- **post45 mechanics.** `MetadataTemplateConfig.corpus_cells` {tab: {header: {value | by
  flow|status|frequency + values ("*" fallback; no entry = decided blank), share, todo}}} —
  NOTE `iig_corpus:` with the corpus share; never over an input-stated cell (FAQ / FRD / STTM).
  Row keys from `metadata_template._row_context` (flow = the pipeline role as the report
  names it: file_to_stg / stg_to_std / grand_master / master). `owed_cells` (ACTIVE_START_DATE
  -> FAQ companion `active_start_date`) are NON-BLOCKING: `codegen.owed_inputs` — `generate`
  prints `INPUT_NEEDED   feeds[<i>].active_start_date — …` (never QUESTION), exit 0, the
  workbook written with the cell empty, the item under `inputs:` in `answers_template.yaml`
  (output root; header "N open question(s), M input(s) needed"); `generate --answers` reads
  `inputs:` (`AnswersFile.inputs`, `faq.with_faq_answers`) and fills the cell. The feed
  report's header: "**Answers owed** — questions: N, inputs needed: M" (only when either > 0,
  so feeds owing nothing keep their bytes); the App: `status.inputs_needed` ->
  `InputsNeededBanner` (non-blocking, never the Answers-needed pause; dist
  `index-DqG-rduu.js`). NEEDS_ANSWERS = QUESTION / UNRESOLVED lines only (docs/ACFC_DEPLOY.md;
  harness doc on `acfc/harness-exit3` local commit 625617f, NOT pushed — with a6b8002, on
  Soham's word); `run_round.py` records INPUT_NEEDED keys and keeps going.
  ACFC overlay: email 4 rows per feed (Success, Failed + 2 placeholders), + EMAIL_NOTIFICATION_URL
  column; schedule gets the corpus's 28 columns, LAYER_NAME STAGE / STANDARD by flow,
  DAY_OF_SCHEDULE '0' only for Weekly, PROCESS_NAME / SUBPROCESS_NAME / SLA / UDF decided
  blank; `pending_cells` and the home-golden SUBJECT / BODY / notebook names are gone.
- **post45 DQ (item 5).** `dq_rules` kinds add_custom_columns (an audit row's load rule
  "Default to 'X'" — `AuditColumn.value_spec`, carried by `extract/generic.py` and
  `extract/segmented.py`; header / trailer feeds only), null_check (PK + not-null), referential_check
  (the STTM recycle lookup's column), and per STANDARD table lr_trim / std_date_conversion
  (a Date column; INPUT_PARAM open unless the load rule states the formats) /
  std_data_type_cast; `dq_rule_types`, `dq_params` (CAQH + SFMC golden formats),
  `dq_split_style: header_and_trailer` (SOURCE_COLUMN header '|' trailer, TARGET_COLUMN
  catalog,schema,table,location per table). G72 / G73 = NullCheckRule (pair_2 golden) and
  AddCustomColumnsRule (CAQH golden). iig_diff: `object_tables.by_rule_type` resolves a DQ
  row's OBJECT_ID on its leg's sheet (STDDelta -> STGDELTA). Home CAQH (mock, vs the real golden in
  Downloads): DQ 0 -> 54 / 54 paired (90.2), TOTAL 45.9 -> 75.8; the split TARGET_COLUMN stays
  open until the storage account is set.
- **post45 items 4 / 6.** `build_goldens._with_ancestors` keeps every PARENT_PIPELINE_ID
  ancestor of the pair's pipelines; iig_keys flow rules classify masters by description
  substring or name token (PL_GMSTR_ / PL_Gmstr_ / PL_MSTR_) — "group-level rows: N (not
  scored)" stays until the goldens are rebuilt. `iig_diff --dump-row [SHEET[:N] ...]`: one
  paired row's golden / agent / status per column (D1 only, console, withheld columns hidden).
- CLAUDE.md was 158k chars: the M15 / M9 / M8 / M7 history moved verbatim to
  `docs/CLAUDE_HISTORY.md` (pointer section "History moved out").

**Previous restart point (2026-10-14 evening, post44).** cd56673 is pushed; the head is the docs-only notes commit
after it (check `git status -sb` for whether it is pushed), marker **0.5.8.post44**. The post43 report's six
items are DONE (the post44 bullet below). Verified at cd56673: **1509 passed / 27 skipped**
(Python 3.11); ruff clean on `src/ tests/ ui/backend/ tools/iig_diff.py
tools/iig_fill_rate.py` (`tools/build_goldens.py` keeps 8 pre-existing findings); scrub: the
3 pre-existing hits only (CLAUDE.md, acfc_env.yaml, config.yaml — `document_title_phrase`),
none on post44's lines. **Waiting on D1 (nothing to do at home until it lands on
`acfc-pairing-check`):**
1. `python tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens <path>/email_template_config_by_pipeline.csv --agent <run outputs> --patterns <dir>`
   → bring home the scrubbed `patterns.md`. It decides the 3b fills (APPLICATION_NAME,
   notebook PROCESS_NAME, DAY_OF_SCHEDULE — blank + `iig_pending:` NOTE until then), whether
   the emitter keeps writing grand master / master rows (item 5), and the corpus DQ classes.
2. Re-run pair_2 and pair_12 on post44: the `LAYER2 FAILED` / `RAW (D1 only)` lines give
   the still-unknown cause of pair_12's 5/5 Layer-2 failures; ADLS / STGDELTA projected
   ~99 / ~100 on pair_2 (from D1's per-column counts — RECYCL_RETN_DAYS 7 vs 30 is the open
   remainder); the `RULES (D1 only)` block for DQ.
3. Confirm with Soham: the D1 standard container `z-use-d1-dlk-std-01` (assumed by analogy
   with the stage container); RECYCL_RETN_DAYS.
DQ next (only once the corpus classes are in, see `docs/acfc/DQ_DIAGNOSTIC_2026-10-14.md`):
CAQH split rule SOURCE_COLUMN = header + trailer columns and RULE_TYPE Predefined;
AddCustomColumnsRule / ReferentialCheckRule; SD's STDDelta casts / trims.

**Previous restart point (2026-10-13, App demo day).** Working tree clean at 042b9fa, `HEAD:src` tree
`54a50fefb007`, marker 0.5.8.post36. The App on D1 deploys from `feature/multi-table` in the D1
Git folder; `docs/acfc/APP_DEMO_CHECKLIST.md` is the demo script, pinned to that tree and
version >= post36 (step 5: the run header badge must read `Output: Framework artefacts`).
**post35 was never pushed** — D1's annotated-column DDL came from post34 (9fb09c6).
- **post34 (9fb09c6) file_format:** an FRD ingestion-type phrase ("File Data Ingestion",
  `extractor.frd.format_tokens`) is no format — the file pattern's extension decides
  (`resolve/gapfill.py` `is_format_text` / `format_delimiter`; `layout/resolve.py`
  `_FeedGapFiller._file_format`, VDD FILES rows matched per feed by file pattern —
  `_own_vdd_rows`); flag `format_from_extension` printed as a NOTE. SD with the VDD: the only
  QUESTIONs are `feeds[0..2].frequency`; without it, exit 0 with three file_format NOTEs.
  Tests `tests/test_format_from_extension.py`.
- **post36 (042b9fa) — the D1 App failure `TemplateGapError 'LOB(Hardcod to MIDS)'`.** Cause:
  the App ran NOTEBOOK mode (config `output.mode: notebook`, toggles untouched); every scored
  round used `--output-mode framework`, whose render skips that gap check and wrote the
  annotated name into the DDL as a column. Fixes: (1) `src/codegen/extract/audit_names.py`
  (`split_audit_annotation`, `clean_audit_column`) used by all three STTM readers (generic,
  legacy `MAPPING-`, segmented) — the contract carries `LOB`, flag
  `audit_column_annotated:<key> <cell>: … (value 'MIDS')`; the emitter is unchanged.
  (2) `output.profile_mode: {acfc_prx: framework}` + `OutputConfig.default_parts()` — the App
  (`ui/backend/demo.py::effective_output_parts`) defaults to framework for acfc_prx; the CLI
  default stays notebook. `ModesPage.tsx` shows an `Output: …` badge and warns "notebook not
  validated for acfc_prx" (dist `index-BdZrOxwQ.js`). (3) `src/codegen/gate/ddl_names.py` +
  `scripts/run_round.py` stage `## DDL sanity` after the CLI: a column identifier not
  `^[A-Za-z_][A-Za-z0-9_]*$` = exit 1, named. Tests `tests/test_audit_annotation.py`, a DDL-gate
  test in `tests/test_run_round.py`.
- **post38 — the D1 pairing-check report's four fixes** (`origin/acfc-pairing-check`
  `codegen-outputs/pairing_check/2026-10-13_pyx_caqh.md`, read in place):
  (1) **family E, a file per sheet** — `split_frd_feeds_by_sttm` now splits when the sheets
  SHARE the FRD's one table; sheets whose feed names would collide are named per sheet
  (`sheet_feed_label`: own `File Name` row, extension + date tokens dropped, else the sheet
  name; flag `feed_names_per_sheet`), the sheet's own file is its pattern; the generic
  extractor's `_match_feed` tries the sheet's own file row, then a feed named after the sheet,
  and two sheets on one FRD feed are a NAMED error (never pydantic's "duplicate feed_id").
  Unique names stay as they were. Fixture `tests/acfc_shapes/family_e_multi.py`, tests
  `tests/test_multi_sheet_feed_ids.py`. (2) **ONE provider switch** `codegen.reasoning.mode`:
  `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` > mock; never inferred from
  DATABRICKS_HOST / the App markers / an endpoint (`resolve_transport` no longer overrides by
  runtime); live that cannot run = ONE startup line (CLI `FAIL provider —`, App
  `startup_error`); `provider=<mode> (<source>)` on the CLI first line, doctor, /api/health and
  every mock reason. ACFC sets live in `app.yaml` + `acfc_run.py` + `scripts/run_round.py`
  (`--provider`, default live; no `--dry-run`, every `CODEGEN_FORCE_MOCK_*` cleared; RUN.md's
  Build section names it); the recipes `docs/acfc/GENIE_RUN_pair_2*.md` show
  `CODEGEN_PROVIDER=live` without `--dry-run`; the harness jobs (in D1) are Soham's.
  `--dry-run` under live = `WARNING provider=live overridden by --dry-run → mock` as the FIRST
  line of the run AND of the report (+ mock reason, flag `provider_overridden:`). Test guard: conftest sets
  `CODEGEN_BLOCK_LIVE_MODEL`; `guard_live_call` (a BaseException) at every real connection
  unless `CODEGEN_ALLOW_LIVE_TESTS=1`. Serving model **Claude Opus 5.5**
  (`claude-opus-5-5` / `databricks-claude-opus-5-5` — confirm the endpoint exists in D1).
  Tests `tests/test_provider_mode.py`, `tests/test_transport.py` rewritten.
  (3) **iig_diff like with like** — `FeedScope` (`--scope feeds` default): an unpaired golden
  row naming another feed of the group and none of the agent's = `out-of-scope`, not missing;
  a one-sided sheet = `sheet not in <side>`, score None; iig_v1 / iig_v2 detected + a note (post41: inform only);
  overall `score` unchanged in meaning, `comparable_score` over scoped shared-sheet cells;
  duplicate-key warnings name the values. (4) `codegen pair` lists EVERY file (the STTM,
  lock files) and NOTEs `pair.sttm` when a folder holds 2+ STTMs with no override pinning one
  (App: outcome `notes`; `acfc_run.py`: the override pins one, else it stops naming them);
  a `name_fuzzy` NOTE in the content branch carries the stem words.
- **post40 — iig_diff pairs rows by IDENTITY, not by generated names** (`acfc-pairing-check`
  `2026-10-13_pair2_diff.md`: SD pair_2 0.0, zero rows paired — goldens `PL_File_<DOMAIN>_<PKG>_<FLOW>_Incr`,
  agent iig_v1 `WF_DLK_NSP_…` / `NB_…`; ALL_FILES_STATIC_INFORMATION stripped by hand to dodge
  a 600 s timeout). Default `--pair-mode identity`: golden rows get feed + flow from
  `docs/acfc/iig_goldens/01_pair_group_index.csv` (GROUP_ID / PIPELINE_ID → flow_type +
  matched_table, matched to the agent workbook whose name / TGT_TABLE_NAME it is; a feed the
  agent did not write = out of scope); agent rows: workbook = feed, flow from the sheet or
  LAYER_NAME / PIPELINE_DESCRIPTION / PROCESS_NAME (`iig_keys.yaml flow`). Per-sheet `identity`
  in `tools/iig_keys.yaml` (schedule / notebook = feed × flow; ADLS / STGDELTA + TGT_TABLE_NAME;
  DQ = feed × @table × SOURCE_COLUMN × RULE_CLASS; email + STATUS; ALL_FILES = FILE_NAME), values
  normalized (case, separators, a table's schema prefix); a component one side never states is
  dropped + warned; an incomplete identity = unpaired + said. No identity → position only when
  counts are equal, else unpaired + said. `convention_columns` (PIPELINE_NAME, notebook names,
  TEMPLATE_NAME, TGT_RJT_TABLE_NAME) never pair, never score: status `convention`, counted with
  how many differ. Every sheet reports paired by identity / position / unpaired. `--pair-mode
  key` = the old natural-key rule. Speed: diff.xlsx called `ws.max_row` per cell (64 of 72 s at
  3,000 rows) and FeedScope compared every row with every stem (`StemIndex` now) — the
  D1-sized CLI runs in ~8 s. `tools/iig_identity_check.py` (counts only) self-pairs goldens by
  identity — run it over the 199-IIG corpus on D1 (only the SFMC / pair_1 / CAQH goldens are
  at home: every row identified). Note: post38's `WF_` / `NB_` names came from
  `--iig-template iig_v1`, not the live model. Tests `tests/test_iig_diff_identity.py`.
  **post41:** the iig_v1 / iig_v2 `HINT` is now an inform-only `NOTE` (score.json
  `templates.note`) and never recommends a template switch: iig_v1 also changes the naming
  convention (`WF_` / `NB_` vs `PL_File_`). ACFC default stays iig_v2 —
  `docs/acfc/IIG_TEMPLATE_DEFAULT.md`.
  **post42 — cross-template sheet:** `iig_keys.yaml sheet_aliases` (replaces the hard-coded
  round-3 `TEMPLATE_ALIASES`): a v1 golden `ALL_FILES_STATIC_INFORMATION` (one row per FILE)
  vs the v2 agent `FILE_ADLS_INGESTION_DETAILS` (one row per FEED, no file column) is ONE
  sheet `ALL_FILES_STATIC_INFORMATION → FILE_ADLS_INGESTION_DETAILS`; a golden file row pairs
  with the FILE_ADLS row of the agent feed whose ADLS_DELTA `SRC_FILE_NAME` is that file
  (`file_identity` + `file_name_tokens`: case, separators, extension, CCYY_MM = YYYY_MM = `*`;
  many golden files → one feed row), scoped by FeedScope; only the shared headers are compared
  (`columns`: OBJECT_ID, domain, subdomain, CREATED_DATE, UPDATED_DATE — only domain /
  subdomain scored), the rest `not_comparable` per side (score.json + console). Applies only
  when neither side has the other's sheet. Tests `tests/test_iig_diff_sheet_alias.py`.
- **post43 — the identity-diff report's four items** (`acfc-pairing-check`
  `2026-10-13_identity_diff.md`; one commit each + the Opus 5.5 labels):
  (1) **live layout JSON** — `layout/model.py` `parse_json_response` (fences, a preamble,
  the outermost balanced object, never a nested one) + `ask_for_json` (one retry with
  `RETRY_INSTRUCTION` "Respond with JSON only, no fences"); every rejected response logged,
  first 500 chars, D1-only: stderr `RAW (D1 only)` + `<runtime cache>/rejections/<fp>.raw.json`.
  Tests `tests/test_layout_json_response.py`. (2) **Pyx questions** (synthetic
  `family_e_multi.build_sttm_reports` / `build_frd_reports` reproduce D1's 22 → 0):
  a metadata sheet (`extractor.discovery.metadata_sheet_names`, or no role resolving while
  other sheets map) is kind `table_details`, never a feed; FRD "Text files"
  (`extractor.frd.generic_text_formats`) + a csv / psv / tsv / txt extension → the extension,
  `format_from_extension` NOTE; files per sheet: one candidate per FILE (`file_identity`),
  then `best_file_matches` (sheet title + File Name row + label vs the files, Jaccard, words
  shared by all sheets / files dropped) → unique best = NOTE "best name match", a tie =
  QUESTION naming the tied files; `answers_template.yaml` beside `--out` whenever answers
  are owed (layout `--require-complete` starts it, extract-sttm adds; empty entries are
  skipped by `load_answers`). Tests `tests/test_pyx_questions.py`. (3) **iig_diff** —
  scrubbed `sheets.md` (per-sheet table with missing / extra + per-column breakdown,
  template headers verbatim), score.json `column_counts` + `file_samples`, console
  `FILE NAMES (D1 only - unscrubbed)`; pair_12's 0 rows = a CAQH inventory name with a date
  FIRST and a wildcard INSIDE vs the agent's prefix-star SRC_FILE_NAME: `file_identity` now
  drops date / wildcard tokens wherever they sit. (4) **corpus fill rate** —
  `tools/iig_fill_rate.py` (GAP = corpus >= 90 %, agent not; assigned = needs_assignment +
  always_blank); ACFC overlay `derived_cells` (shapes over {source} {layer} {outcome}
  {notebook} {pipeline} {sender}; one `iig_derived` NOTE per column) fills notebook
  PIPELINE_NAME / PROCESS_NAME / NOTEBOOK_PATH, schedule APPLICATION_NAME, email
  TEMPLATE_NAME / PROCESS_NAME / SUBJECT / BODY / SENDER_NAME (dbo) / SENDER_EMAIL
  (`job.notification_sender`, env `CODEGEN_NOTIFICATION_SENDER`). The 199-IIG corpus is
  D1-only: measured over the 3 home goldens (SFMC, pair_1, CAQH) — 11 gaps → 1
  (ACTIVE_START_DATE, a go-live date). `docs/acfc/IIG_FILL_RATE_2026-10-13.md`; tests
  `tests/test_iig_fill_rate.py`. Run the tool on D1 over `docs/acfc/iig_goldens`.
- **post44 — the post43 report's six items** (`acfc-pairing-check`
  `2026-10-14_post43.md`; one commit each): (1) **Layer 2** — both live providers ask
  through `reasoning/providers/ask.py::ask_candidate` (post43 `parse_json_response`, one
  `RETRY_INSTRUCTION` retry, a response that `TRUNCATED` = "ends inside the JSON object"
  retried with `reasoning.truncation_max_tokens` 32000); every failed attempt an
  `AttemptFailure` on `provider.failures`, logged by `reasoning/raw_log.py`
  (`LAYER2 FAILED` reason, `RAW (D1 only)` 500 chars, the max_tokens NOTE;
  `<state>/rejections/layer2_<feed>.raw.json`); `StageUsage.recovered` / `all_failed` -> a
  `> **WARNING**` report header + console line. Tests `tests/test_layer2_failures.py`.
  (2) **iig_diff identity `@file`** (`iig_keys.yaml file_columns`) splits ONLY rows the
  other components leave equal (CAQH: 18 ADLS rows, one table); `file_name_tokens` drops a
  trailing run of 2+ one-character segments (CAQH `_P_I_1_T`) — home CAQH ADLS and
  ALL_FILES -> FILE_ADLS 18 / 18 paired. (3a) `iig_fill_rate.py --patterns DIR`: scrubbed
  `patterns.md` / `.json` (dominant value + slot pattern {table} {schema} {domain} … per
  column, DAY_OF_SCHEDULE per PIPELINE_FREQUENCY, master rows per GROUP_ID, DQ rule
  classes), re-scanned with scrub_check. (3c) sheets match case / separator-blind, a header
  row may sit under a title, `.csv` table exports (suffix allowed); the 199 per-pair
  workbooks carry NO email sheet — build_goldens reads `email_template_config_by_pipeline.csv`.
  (3b) `pending_cells` (blank + `iig_pending:` NOTE, never over an FAQ value): schedule
  APPLICATION_NAME / DAY_OF_SCHEDULE, notebook PROCESS_NAME; ACTIVE_END_DATE
  `9999-12-31 00:00:00` (the corpus's datetime). (4) ACFC overlay: FILE_HEADER_FLAG by
  format (`file_header_flag_by_format`: delimited Y / fixed-width N), ADLS FILE_METADATA
  (the prod 55th column; `deliberate_blanks` -> NULL in the SQL), STGDELTA containers
  stage in / std out (constants, the offer retired), `data_type_style: full`
  (`String:Decimal(10,2)`). Tests `tests/test_iig_cheap_misses.py`. (5) iig_diff status
  `group-level` (`group_level_flows`: grand_master / master agent rows the golden lacks) —
  "group-level rows: N (not scored)". (6) DQ diagnostic only: `component_overlap` per
  identity sheet, `RULES (D1 only)` block / `rule_samples`; `docs/acfc/DQ_DIAGNOSTIC_2026-10-14.md`.
- **post39 — the live D1 check's four fixes** (`origin/acfc-pairing-check`
  `codegen-outputs/pairing_check/2026-10-13_live_three_pairs.md`; one commit each):
  (1) **pair_12 CAQH** — `frd_docx.split_domain_labels`: a cell with a `Domain:` AND a
  `Sub Domain:` label (any case / separator) → DOMAIN + SUBDOMAIN, flag
  `frd_domain_labels_split:`; every IIG payload cell made single-line at the emitter
  boundary (`gate/derivations.normalise_iig_line_breaks`, flag
  `iig_line_break_normalised:<SHEET>!<A1>`); gate check `iig_single_line` over the WRITTEN
  config_rows / `_IIG.xlsx` fails with `<file> <SHEET>!<A1> (<header>)`. Real CAQH (mock):
  22 × Member / Third Party Liability, PASS_WITH_FLAGS. (2) **pair_11 Pyx** — the harness
  handed extract-sttm a ONE-feed FRD contract (extract-frd's); extract-sttm now splits it
  per mapping sheet by the layout rule (`layout/resolve.split_single_frd_feed`,
  `split_frd_feeds_by_sttm(force=True)`; the layout stage forces it too for content
  strategy), records `SttmContract.frd_split` (absent when unused), and generate joins it
  (`resolver.apply_frd_split`); NOTE `frd.split`. Live layout answers are SALVAGED
  (`salvage_layout_answer`): one REJECTED line per schema error, null role = not found,
  valid sheets / bands kept and workbook-validated; `--report-unresolved` lists them. The
  real Pyx shape is still unseen here — the synthetic family-E fixture stands in.
  (3) **iig_diff** — `key_samples` (first 5 golden vs agent keys, console + score.json, D1
  only) and a SEPARATE `positional` score (key-unpaired rows paired by position when the
  counts match, else best cell overlap); key-paired score + scrubbed export unchanged.
  (4) **App deploy** — nothing needs `out/` (`tests/test_deploy_without_out.py`); deploy
  from Git or keep harness outputs under `/tmp` (`docs/acfc/APP_DEPLOY_NO_OUT.md`).
- **post37 — pairing by NAME ROLE + token key (the Pyx pair_11 failure).** The App's
  `local_frd_candidates` and `codegen pair` took a `.docx` as an FRD only when its name
  STARTED with "frd" (`Pyx_ … DSNP_FRD.docx` was never a candidate), the name rule was the
  first three tokens, and the same-folder rescue attached an IIG golden as the VDD. Now:
  `demo_sources.classify_document_name` (a role token ANYWHERE; `iig` always = IIG, never an
  input; two roles → the prefix decides + NOTE), `pairing_key` / `match_by_name` (exact key →
  `name_key`; else a unique whole-word-stem Jaccard ≥ `inputs.pairing.name_fuzzy_threshold`
  0.8 → `name_fuzzy` + NOTE naming the stem-matched words; below → QUESTION, `codegen pair`
  exit 3). A VDD candidate needs a `vdd` token or the index's positive dictionary verdict
  ("VDD by content: <file>" NOTE → outcome `notes`, run flag `pairing_note:`); the same-folder
  rescue applies to a confirmed dictionary only. Pairs override file
  (`pairing_overrides.yaml|yml|json` in an input folder, `--pairs-file`,
  `inputs.pairing.overrides_file` / `CODEGEN_PAIRING_OVERRIDES`) wins over everything
  (`rule: override`); `InputCatalog.every_document` (no name dedupe). The pairing outcome
  carries `folder_roles` (every file of the STTM's folder, role + rule) and `considered`
  (every document of the kind, its name score, why it is not a candidate); dist
  `index-DGsprVYN.js`. Tests `tests/test_pairing_name_key.py` (incl. pair_11 end to end on
  local folders AND the fake workspace backend). Storage path audit: nothing strips / splits /
  quotes a segment; the SDK quotes Files API URLs, the Workspace API takes `path` as a
  parameter (`clean_rel` strips only the ends of the whole rel — not this shape).
- **Verified at 042b9fa:** 1360 passed / 28 skipped; ruff, tsc clean; vitest 29. SD invariant
  (home, mock) 47 / 47 / 45 matched, diff 1 / 1 / 3 — unchanged by post36. App (nothing POSTed
  → framework) vs CLI: `framework/` + `ddl/` byte-identical, mock AND live
  (databricks-claude-opus-5, profile DEFAULT; only `candidates.json` differs live); the IIGs
  equal post33's; 16 DDL files / 1,735 column identifiers / 0 with "(". A double-POST of the
  same workbook answers 200 `joined`.
- **The home SD documents:** the home STTM (60,905 B) has anonymized ColumnName columns; D1's
  (61,141 B) is the reference. The SD VDD is only in the user's Downloads folder; its FILES!C2:C4
  say "Delimited text" (D1's reportedly `csv`). Session scratch scripts (`drive_app.py` App HTTP
  driver, `cli_ref.py`, `sd_run.py`) died with the session — rebuild from the checklist.
- **The round-8 brief (was ON HOLD for the demo):** DONE in post44 — Decimal(10,2) precision,
  the STGDELTA containers (constants stage in / std out, not a QUESTION). Still open: drop Q8;
  RECYCL Q3; ALL_FILES layout; EMAIL_TEMPLATE_CONFIG (the corpus email CSV — D1 item 1 above).
- Commits post30 → post33 (oldest first): a7f98fc `run_round.py` (post31/32), 28d3abb iig_diff
  environment tokens, df0e1a7 STGDELTA paths, b9a10c8 SD-family flags, e90562d `_MI` OBJECT_NAME,
  0891329 EMAIL_TEMPLATE_CONFIG export, fff4f57 post33 + `GENIE_RUN_pair_2_r7.md`, 1cd5574 the
  demo checklist.

- **D1 runs, home reviews.** The prod goldens exist only on D1 (`*.xlsx` + the 860a798 ignore
  lines keep them off origin; unscrubbed prod rows — never force-add them). Genie runs
  `docs/acfc/GENIE_RUN_pair_2_r5.md` in the D1 Git folder and pushes scrubbed evidence to
  `acfc-results` (`codegen-outputs/iig_validation/round<N>/pair_2/`); this checkout reads it
  in place (`git show`), never checks it out.
- **D1's SD STTM is the reference (accepted after round 6):** the home copy differs only in its anonymized stage / standard `ColumnName` columns (compare.txt: J, O / K, P) — column-dependent fixes (SRC_DATA_TYPE precision, DQ column lists) are unit-tested here, verified on D1 only.
- **Build identity (99f262b):** `codegen.build_info.build_identity()` — git → the deploy stamp
  `src/codegen/_build.py` (`scripts/stamp_build.py`, never committed) → `CODEGEN_BUILD_SHA` →
  the src tree id — names commit / branch / commit time on the CLI's first line, `codegen
  doctor`'s `build …` line and `GET /api/health`. `codegen generate` writes
  `<output root>/CODEGEN_BUILD.json`; iig_diff refuses an agent workbook without one within 5
  folders above it (`unscored: agent workbook has no build identity`).
- **Pushing:** once per clone `git config core.hooksPath scripts/git-hooks`. `pre-push`
  refuses a code push to `feature/multi-table` / `feature/iig-first` with an unchanged
  version, a requirements marker ≠ pyproject, a tracked `_build.py`, or `ui/frontend/src`
  changed without `dist` (1f7316f, b06ce1f). Bump: `python scripts/bump_version.py`. Docs-only
  pushes need no bump.
- **409 fix (53468c2):** `POST /api/demo/workbook` for the workbook already being selected =
  200 + that job (`joined: true`); another workbook is still 409; a job older than every step
  budget is replaced; a job always ends.
- **`tools/iig_diff.py` + `tools/iig_keys.yaml`:** rows paired by natural key only (4ba59b9;
  `--pair-mode` still parses — never use it for a score). Cell statuses exact / normalized /
  mismatch / missing-in-agent / extra-in-agent / needs_assignment. The agreed ignore set =
  `needs_assignment` in iig_keys.yaml (INVENTORY / OBJECT / PIPELINE / GROUP_ID, the connection
  ids, the audit stamps; every other `*_ID` IS scored), printed in each report header;
  CREATED_BY / UPDATED_BY values withheld. `--agent` takes every feed's `*_IIG.xlsx` (not
  `*_REVIEW`), scored as their union (5e3df10). `--export-scrubbed DIR` → mismatches.md /
  row_keys.md / SELF_CHECK.md with G<n> / A<n> tokens, a re-scan must find 0;
  `--golden-structure` describes the golden's shape (d8cb519). score.json / diff.xlsx /
  routing.csv carry prod text — never committed.
- **`tools/build_goldens.py` (28fd6d2):** each sheet de-duplicated across the GROUP_ID exports
  on the non-ignored columns; `_source_group_ids` lists the contributing exports (never
  scored, shown in row_keys.md); one `dedup before -> after` line per sheet. Pre-existing,
  not ours: 8 ruff findings + 2 scrub hits (SFMC GROUP_IDs).
- **Blank Schema / TableName in an STTM band (581d235):** the feeds are split on the mapping
  sheets (`layout/resolve.py::_blank_sheet_targets`); the schema comes from the FRD when it
  states one, with a NOTE (`sttm_target_from_frd`), else it is a QUESTION; table names are
  always a QUESTION — never derived. A blank-cell copy of the real SD STTM owes 14 QUESTIONs
  (6 schema, 6 table, 2 file): its FRD's Target Schema is a per-file-group list.
- **Round gate (post30):** `python scripts/doc_fingerprint.py --compare
  docs/acfc/fingerprints/pair_2_sd_home.json <D1 fingerprint>` — exit 1 on a HARD line (sheet
  names, counts, extents, merged ranges, header row + hash, per-column fill, the docx
  `text_hash` + counts) = STOP; WARN (whole-file sha256 / size, document.xml, `body_hash`,
  per-column value hashes) is recorded, the run continues. Value hashes are HMAC under the
  gitignored `codegen-state/fingerprint.key` (post31; same key both sides, else REFUSED).
- **Round 4 (not a clean run):** TOTAL 4.6; ADLS 33.5 / STGDELTA 31.7 with 2 of 3 rows paired.
  The golden was 6× duplicated on the unfiltered pair-wide sheets (now de-duplicated), and the
  run used a hand-split contract and the blank-cell STTM.
- **Round 5 ran on the blank STTM** (Genie chose the input). **Round 6 = `scripts/run_round.py`**
  (post32; `docs/acfc/GENIE_RUN_pair_2_r6.md`): the inputs come from the gitignored
  `codegen-state/round_inputs/pair_2.yaml`, no answers file, gate → CLI → golden → diff → RUN.md
  → scrub (exit 2 gate; 3 layout asks / scrub hit; 1 a stage). Then: only name / description columns differ →
  anonymization; Schema / TableName / file-pattern columns differ → the home SD invariant
  (mock 43 / 43 / 46, diff 0) was measured on another copy. DQ rules: not implemented.

## [H3] START HERE — branch `feature/multi-table` (state as of 2026-10-09, early morning — after the overnight robustness run)


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

## [H4] Parent branch `feature/iig-first` (state as of 2026-10-07, end of day — the demo branch)


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

## [H5] FRD pairing + upstream contracts (added 2026-08-28)


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

## [H6] Databricks volumes seam (added 2026-08-27)


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
--full <staged tree> /Workspace/Users/<deploy-contact>/
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

## [H7] Demo panels + reference-document checks (added 2026-08-27, display/check only; UI trimmed 2026-09-18)


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

## [H8] Fixtures & data rules


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

## §[H9] CLAUDE.md session notes post47–post103 (moved verbatim 2026-10-23)

Everything CLAUDE.md carried above "Purpose & pipeline position" at fa79a28: the
restart notes, the post47–post102 "After postNN (kept for reference)" blocks, the
condensed rules list, the working rules and the 2026-10-14 history index. Current
state now lives in `docs/RESTART.md`; rules still in force are in CLAUDE.md.
Headings inside are demoted one level so they nest under this section.

### NEWEST — IIG validation (state as of 2026-10-22, `feature/multi-table`, post102)

Scoring the agent's IIG workbooks against prod "golden" IIG rows — pair_2 (SD) first, for Venu.
Deliverables: DDL / `metadata_inserts.sql` + the IIG workbook (runbook / playbook out of scope).

**RESTART HERE (2026-10-23, post103; everything pushed, tree clean).**
- **Head:** post103 (`31b46ed`), and the App is deployed at **post103** (`/api/health`;
  redeployed from GitHub 2026-10-23 12:56 UTC).
- **post98–103 verified on the App (2026-10-23)** on the pair_11 live run
  `demo_20261023_132913` (artefacts via `/api/combined/…` + a Playwright pass):
  - the combined set named `Pyx_Care_Management_Data_MI_DSNP_*` (no `STTM_`);
  - OBJECT_ID 1..5 across the run;
  - 12 pipeline rows = 1 grand master + 1 master, both Daily `_DLY`, + 2 × 5 children;
  - the `_LOG.md` merge / kept lists; the short IDs line; IIG_REVIEW hidden;
  - Run summary + Feeds collapsed; View results hides the sidebar for the page only.
  - Noted: that run made NO model call (layout from the documents, `--layer2 defer`,
    35 rules pending review). PARENT_PIPELINE_ID is blank on master + children (IDs are
    the framework's), so the parent links only show in the review copy.
- **After a container reset** (venvs, `/tmp` and the OAuth profile are gone):
  - venvs via uv (pip's isolated pyspark build failed 2026-10-23): `uv venv --python 3.12
    .venv && uv pip install --python .venv/bin/python -e ".[dev,ui,live,databricks]"`;
    `.venv-d1` the same with `-e ".[dev,databricks]" -c constraints/acfc_d1.txt`.
  - OAuth: the login's `localhost:8020` callback listens IN the container. Start
    `BROWSER=echo DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks auth login --host
    <the DEFAULT profile's host, `databricks auth profiles`> --profile codegen-oaut` in the
    background, Soham opens the printed URL and pastes back the `localhost:8020/?code=…`
    URL, `curl` that URL inside the container. A code only works for the login that
    issued it.
- **Deploying the App:** it builds from GitHub, not a staged tree: push, then
  `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks apps deploy codegen-agent -p
  codegen-oaut --json '{"mode":"SNAPSHOT","git_source":{"branch":"feature/multi-table"}}'`
  (prints the resolved commit). Soham also deploys this way himself.
- **Working rule** (memory `test-runs-targeted-then-full-once`):
  - run the affected test files while working;
  - run the full suite in BOTH venvs ONCE, on the locally committed tree;
  - READ the result before `git push`, never chain the push.
  - Full runs: d1 ≈ 9 min, dev ≈ 14.5 min. Run them in parallel with each job doing
    its own `cd`, or one after the other.
- **Driving the deployed App from this container:**
  - Token: `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks auth token -p
    codegen-oaut` gives an OAuth token the App's API accepts (a PAT does not). URL
    `https://codegen-agent-4812116803419068.8.azure.databricksapps.com`.
  - The App runs LIVE (`CODEGEN_PROVIDER=live` in app.yaml): a run sends client documents
    to the model, so ask Soham first. He approved pairs 08 / 10 / 03 / 11 on 2026-10-22.
  - Flow: `POST /api/demo/workbook {name}` (202, poll status `selection_job`) →
    `/api/demo/run-live {confirm: true}` → while paused, `/api/demo/layout-answers
    {answers, proceed | cancel}` or `/api/demo/rerun-with-answers {answers: {gaps},
    confirm: true}`.
  - Only one run at a time: cancel a paused one first.
  - A throwaway client was `/tmp/rjt/app_client.py` (session scratch; rewrite if gone).
- **Live App results (post94–97):**
  - **pair_03:** PASS_WITH_OPEN_INPUTS with NO answers.
  - **pair_11:** PASS_WITH_OPEN_INPUTS (answer the VDD question with "none"); combined set
    of 67 rows, per-table reject paths.
  - **pair_08:** the live layout resolves the STTM; the audit columns are no longer asked;
    7 blank stage types carry a proposal; then FAIL on the multi-table mismatch (the FRD
    names 4 stage tables in one cell).
  - **pair_10:** stops before generating on the delimiter of all 4 feeds and the load
    strategy / LOBs of feeds 1–3 (the BSA answered feed 0 only).
- **Container harness:** pairs in `/Workspace/Users/<me>/frd_sttm_pairs/pair_<n>`; for the
  App's own state copy `environments/`, `overlays/`, `leakgate/` and `answers/pair_<n>` from
  `dbfs:/Volumes/d1_dlk/codegen/state/` into a /tmp state dir (`databricks fs cp -r`), then
  `PYTHONUTF8=1 .venv-d1/bin/python scripts/container_harness.py --pairs-dir <dir>
  --state-dir <dir> --out <dir> --work <dir> --pairs 3,8,9,10 --dry-run --output-mode
  framework`.
  - `--pairs` is comma-separated.
  - It is mock: pairs 08 / 10 stop at the layout step (no cached layout profile; the live
    App resolves it).
  - Never run the CLI from the repo root with outputs in `out/`; use the harness or a
    scratch output dir.
- **Browser checks:** Chromium in `/tmp/pw` + libs unpacked in `/tmp/pwlibs` (`apt-get
  download` + `dpkg -x`, no root), `LD_LIBRARY_PATH=/tmp/pwlibs/usr/lib/x86_64-linux-gnu:
  /tmp/pwlibs/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node <script>`. Stub
  `/api/feeds` or `/api/demo/status` with `page.route`. Session scratch — re-download if
  gone. Rebuild (2026-10-23):
  - `cd ui/frontend && npm ci`, then (no `npx` in the container)
    `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node node_modules/playwright/cli.js install
    chromium-headless-shell`; a script `require`s that `node_modules/playwright` by path.
  - Libs: `apt-get download` + `dpkg -x … /tmp/pwlibs` of libglib2.0-0 libnspr4 libnss3
    libatk1.0-0 libatk-bridge2.0-0 libdbus-1-3 libxcomposite1 libxdamage1 libxfixes3
    libxrandr2 libgbm1 libxkbcommon0 libasound2 libatspi2.0-0 libwayland-server0 libdrm2
    libxi6 libxrender1 libxext6 libx11-6 libxcb1 libxau6 libxdmcp6 libbsd0 libmd0
    libxcb-randr0; `ldd …/chrome-headless-shell | grep "not found"` must print nothing.
  - Against the deployed App: `newContext({extraHTTPHeaders: {Authorization: "Bearer
    <OAuth token>"}})`.

**post98–post102 at a glance** (details: `CHANGELOG_ACFC.md`):
- **post98 — App:** the environment panel is a collapsible (summary line; Storage /
  Catalogs / Framework connection IDs; a layer's `catalog_map` + `default_catalog` with the
  same value shown as ONE row, an edit writes both keys; a plain-English line per row).
  The IIG review workbook is hidden in the App: `output.app_files` (`[ddl, iig, addition,
  log]`; add `iig_review` back to show it — still written, still served by name).
- **post99 — the combined IIG writes the grand master / master once**
  (`combined.dedup_rows`: `PL_GMSTR_` / `PL_MSTR_` rows equal on every column); children
  are never merged; same-name rows that differ are listed in the `_LOG.md`; "row n" parent
  references follow the kept row (`run_artefacts._remap_refs`). App: each environment
  value's provenance (`environments.<name>.provenance` in acfc_env.yaml) under "Where these
  values come from".
- **post100 — the combined set's name drops a leading / trailing `STTM` token**
  (`run_artefacts.sttm_name`: `STTM_Pyx_X` -> `Pyx_X`). **OBJECT_ID numbered 1..n across the
  run** in the combined IIG (`combined.object_ids: run`; every sheet of a feed shifted
  alike, so DQ / STGDELTA rows keep their object; per-feed IIGs keep 1..n). Nikshit's ask.
- **post101 — App:** the artefacts panel says only "Assign before loading: PIPELINE_ID ·
  PARENT_PIPELINE_ID · GROUP_ID" (`output.app_assign_ids`, column -> hint; empty = the old
  long line); the `_LOG.md` keeps the full list (Soham: the log can be verbose, the UI not).
  The Run summary (tiles + Layer-2) and the feed cards are collapsed `<details>`, so the
  Framework artefacts lead. "View results" hides the sidebar (`ModesPage onViewResults`).
- **post102 — one Daily grand master + master per run** (the pair_11 golden):
  `pipeline_roles[].frequency: Daily` on grand_master / master (acfc_env.yaml) sets their
  PIPELINE_FREQUENCY, description and name frequency code (`input_choices.flow_tokens(...,
  tpl)`, `metadata_template.role_frequency`); children keep their feed's. pair_11 mock:
  12 rows = 1 + 1 + 2 × 5 feeds, every child under row 2 (golden: 10 = 4 feeds).
- **Decided by Soham (2026-10-22), not built:** the four Databricks workspace / cluster
  columns of DATABRICKS_NOTEBOOK_DETAILS stay blank and out of the panel (not needed);
  TEMPLATE_ID out of the IDs line.
- **State change (no code):** `environments/d1.yaml` (volume + workspace copy) no longer
  claims to be the suite's synthetic profile; value unchanged; backups
  `d1.yaml.bak_20261022_pre_comment`.
- **Docs:** `docs/acfc/HEDIS_CONSUMPTION_STTM_SHAPE.md` (the 9 HEDIS Stage -> Consumption
  STTMs, structure only, 5 families, feasibility, owner questions §6);
  `docs/acfc/STANDARDS_DEPRECATION_REVIEW.md` (which agent rules came from the deprecated
  ADF coding-standards section; Soham's keep/drop table still blank).
- **Reaching SharePoint:** memory `sharepoint-via-uc-connection` (read_files +
  `d1_dlk_sharepoint` on the Serverless Starter Warehouse). The 9 HEDIS workbooks are in
  `/Volumes/d1_dlk/codegen/state/hedis/stage_to_consumption/`.

**post86–post97 at a glance** (details: `CHANGELOG_ACFC.md`):
- **post86 — path families:** `acfc_env.yaml` `path_families.per_table` (pair_11:
  `Reject/<t>/`, `Processed/<t>/`); feeds pick it via the overlay's `path_family_by_source`
  or `feed_overrides.<feed>.path_family`.
- **post87–89 — App clean-up:**
  - post87: the blank-IDs line once per run;
  - post88: a collapsible sidebar;
  - post89: no per-feed summary line; REVIEW_SUMMARY rows for sheets empty by rule.
- **post90 — the notebooks zip:** `GET /api/notebooks.zip` + "Download all". A wrapper
  notebook was assessed and NOT built.
- **post91 — one set per run and STTM** in `<out>/combined/` (`codegen.run_artefacts`):
  `<STTM>_IIG.xlsx`, `_IIG_REVIEW.xlsx`, `_DDL.txt`, `_LOG.md`.
  - The per-feed files are still written.
  - Rows merge by content ONLY on `combined.dedup_sheets` (EMAIL_TEMPLATE_CONFIG).
  - App: `/api/combined/{name}`.
  - **Notebooks OFF in the App: `output.app_options: [framework]` in config.yaml**
    (`[notebook, framework]` turns them back on). Tests of the App's notebook behaviour
    use the conftest `notebooks_in_app` / `offer_notebooks`.
- **post92 — a bare `DECIMAL`** is written as stated (Databricks DECIMAL(10,0)) + a
  `decimal_no_precision` flag per column (pair_03's crash).
- **post93 — repeated source names** (pair_03: 10 × Qualifier / Type):
  - SRC_COLUMNS positional `col<i>:<stage>`;
  - a headerless file's pipeline uses `col<i>`;
  - a `source_names_repeated` flag;
  - not STAGE:STAGE (rule 4 is still pending).
- **post94 — three extraction gaps:**
  - `extractor.frd.load_strategy_synonyms` ("Truncate & Load (…)");
  - audit rows = no source field name + `extractor.audit_column_names`;
  - a blank stage type's question PROPOSES what the sheet unanimously pairs with that
    standard type (`stage_type_proposal_min_rows: 3`; never written).
- **post95 — the proposal:** case-insensitive spellings; a one-click candidate in the App
  (never pre-selected).
- **post96 — wording:** a question with a suggestion says it comes from the sheet's other
  rows.
- **post97 — the combined DDL by layer:** every stage table, then every standard table
  (as one feed's DDL already orders several tables); within a layer, feed order.
- **c503417 — test-only:** `test_storage_ui`'s runner without the index warm-up (the
  full-run flake was the warm-up racing the test).

**Open — with Soham right now:** he reported the pair_11 combined DDL as "4 stage + 5
standard tables from 3 feeds". The App's pair_11 runs (3 today, all 5 feeds) give 5 + 5,
one pair per feed, with merged = the per-feed files added up. Still to learn: which file
or run he counted (an older pre-post97 download? a comparison with the golden, which has
4 feeds — no Engagement Billing?). Mock runs of pairs 01 / 02 / 04 / 12 are consistent
too. 4 + 5 would be correct only if two feeds share a stage table or a feed has more
standard than stage tables.

**Open — codeable here:**
- **`tools/iig_diff.py` depends on the `--agent` file order** (30.0 sorted vs 30.3
  unsorted; run_round sorts). Sort internally.
- **`test_demo_ui.py::test_choosing_an_sttm_auto_pairs_its_vdd`** fails when a stale
  `ui/backend/state/document_index.json` exists (isolation gap).
- **STGDELTA SRC_ADLS_PATH** uses the standard table's name. Wrong only when stage ≠
  standard names; no such pair found yet, so wait for one.
- **RECYCL_ADLS_PATH on pair_11 (4 cells):** the golden states a recycle no document
  does. Ask where prod got it.

**Open — needs others:**
- **Soham:** the multi-table / contract-mismatch decision (blocks pairs 05 / 06 / 08 / 09,
  and pair_09's per-table load strategies from its STTM Summary sheet).
- **The BSA:**
  - pair_10's delimiters (4 feeds) and feeds 1–3 load strategy / LOBs;
  - pair_08 `columns[87].target_type` is answered INT, probably STRING (INT in standard =
    STRING in stage, 39 of 39). Reported, not changed.
- **Nikshit / Venu:**
  - child pipeline names: Nikshit says follow the EDO Naming Standards, whose child pattern
    `PL_CHLD_<Product>_<Sub-Product>_<Source>_TO_<Target>_<Load Strategy>` has NO feed slot,
    so every feed's children share a name (the `_LOG.md` lists them). The pair_11 golden
    uses an older pattern (`PL_File_PYX_CM_MIDS_<feed>_ADLS_To_Delta_Incr`: no product /
    sub-product codes, `File` not `CHLD`, `ADLS_To_Delta`, `Incr`). Tell Nikshit the
    document cannot give unique child names; do NOT deviate without his word;
  - which path convention is standard.
- **Nikshit (Soham asking 2026-10-22):** re-confirm the D1 `storage_account`
  `z-use-d1-dlk-std-02` (he gave it 2026-10-21; hyphens are invalid in an Azure account
  name and it looks like a container; the earlier value, which has a valid account
  name's shape, is in `d1.yaml.bak_20261021_pre_storage_account`, volume only). If it changes: both state
  copies + the `storage_account` provenance text in acfc_env.yaml.
- **Soham — standards:** the keep/drop decisions in `docs/acfc/STANDARDS_DEPRECATION_
  REVIEW.md` (alerts, timeout, default DQ on upsert, DBR 15.4 + Photon); then rewrite
  `docs/EDO_STANDARDS_ALIGNMENT.md`, `print` -> logging in the v2 notebook templates, the
  `engineering_standards.status` line (byte-pinned outputs: one bump + snapshots).
- **HEDIS owners (via Soham):** what prod deploys for one Stage -> Consumption load + one
  deployed XREF and one claims example (`HEDIS_CONSUMPTION_STTM_SHAPE.md` §6); nothing to
  build before that.
- **EMAIL_TO:** no value anywhere.
- **Raj:** the `USE CATALOG` grant (then app.yaml back to the volume; until then edit
  BOTH state copies: the volume and `/Workspace/Users/<me>/codegen/state/codegen-state`).
- **D1 / Genie:** the golden SRC_COLUMNS cells (rule 4), the PIPELINE_DESCRIPTION dump,
  the workspace-folder token.
- **Aruna:** OPEN_QUESTIONS §4–6.
- **Deferred by Soham:** pair_10's FRD prose values (file format / load strategy / LOBs in
  paragraphs, not in feed order) — a layout-model task.

**After post85 (kept for reference).** post85 (Nikshit:
"go by the document"): PIPELINE_NAME = the EDO Naming Standards' patterns
(`acfc_env.yaml`; master `PL_<GMSTR|MSTR>_{product_code}_{sub_product_code}_{source_std}_
{domain_std}_{subdomain_std}_{lob_std}_{frequency_code}`, child `PL_CHLD_…_RAW_TO_STG_{load_std}`
/ `_STG_TO_STD_`; tokens in `input_choices._standards_tokens`, load codes
`engineering_standards.load_strategy_abbreviations`). The D1 overlay's interim templates
were removed (volume + workspace copy; backup `.bak_20261021_pre_post85`). On pair_11 the
child names are identical across the 5 feeds and the masters are long (no table code for the
source / domain / sub-domain) — for Nikshit / Venu.
The App must be redeployed to get post81–84; none of them is verified on the deployed
App yet (the post84 check was the container harness, below).

What post81–post84 did (details: `CHANGELOG_ACFC.md`):
- **post81: defaults written unasked, one "Change defaults" button.**
  - What is written: the interim `pipeline_name_templates` (shipped in `acfc_env.yaml`),
    APPLICATION_NAME (the feed's SOURCE), ACTIVE_START_DATE (`{run_date}` =
    `CODEGEN_RUN_DATE`, else today; conftest pins `2026-01-02`), and TGT_PRIMARY_KEY
    from an explicit signal (`primary_key_autoset`). No signal on a merge load = the
    blocking QUESTION.
  - App: one "Defaults" line + panel (`InputsNeededBanner` `DefaultsPanel`); pipeline
    names keep their own button.
- **post81: the App reads its state from a workspace folder.** `CODEGEN_STATE_DIR` may
  be a `/Workspace/...` folder (Workspace API copy, `state_mirror`). `app.yaml` points
  it at `/Workspace/Users/<me>/codegen/state/codegen-state`: a copy of the volume's
  `environments/d1.yaml` (storage account) + `overlays/acfc_prx.yaml` (notebook names,
  status sets, per-feed overrides), NOT in git. The overlay does NOT set EMAIL_TO
  (`<<D1:EMAIL.EMAIL_TO>>`): `run.email_to` stays open either way. Until Raj's `USE CATALOG` grant, edit BOTH copies; after it,
  set `CODEGEN_STATE_DIR` back to `/Volumes/d1_dlk/codegen/state`.
- **post82: the notebook download.** The feed summary carries `notebook` (feed-relative;
  v2 = `notebook/<slug>.ipynb`, the old `<slug>.ipynb` lookup missed it). The results
  page has a "Notebooks" panel above the Layer-2 one, which says it is optional. Layer 2
  stays deferred in the App (`reasoning.layer2_app: defer`).
- **post83: View results lag.** Every status-returning POST (`input-choices`,
  `run-live`, `layout-answers`, `layout-refresh`) returns `main.demo_status()`. The bare
  runner status lacked mode / label, so "View results" fell back to `load-live-run` (a
  ≈3 s full re-run). `load-live-run` itself is still a re-run (only for opening old runs).
- **post84: the landing.**
  - From the FRD: each Solution Requirement's "Raw ADLS Location" line
    (`frd_docx.requirement_landings`) becomes per-file blocks, given per derived feed by
    `resolve_structured_fields`. The key is the requirement's Name plus the identifiers
    only it names.
  - Else the convention, written (`metadata.templates.iig_v2.landing_autoset`,
    `metadata_template.with_landing_default`, flag `landing_from_convention:`).
  - A change in the App's "Change defaults" is the next run's gaps answer
    (`DemoRunner._landing_choices`).
  - Tests of the landing QUESTION use the `landing_autoset_off` fixture (conftest).

State of pair_11 (mock container harness, `.venv-d1`, state = environments only, no
overlay / answers — what the App had before post81's workspace copy):
- outcome PASS_WITH_OPEN_INPUTS; 5 notebooks; the only open line is `run.email_to`;
  leak gate CLEAN;
- SRC_ADLS_PATH and SRC_ADLS_ARCHVL_PATH = golden for 5 / 5; pipeline names: 4 of 8
  child names exact (post79).
- Recipe: copy `/tmp/pyx/state/{environments,leakgate}` into a fresh state dir, then
  `PYTHONUTF8=1 .venv-d1/bin/python scripts/container_harness.py --pairs-dir /tmp/pyx/pairs
  --state-dir <dir> --out <dir>/out --work <dir>/work --pairs 11 --dry-run --output-mode
  notebook --output-mode framework` (the /tmp copies are session scratch — re-copy pairs
  from `/Workspace/Users/<me>/frd_sttm_pairs` and state from the volume if they are gone).

Verified at post84: `.venv-d1` full suite 1715 passed / 116 skipped / 0 failed; dev
`.venv` full suite 2006 passed with 1 failure, since fixed (that file re-run green). Ruff
clean, frontend 86 tests, `dist` rebuilt.

**After post81 (kept for reference).** As above. On the post80 App run, the 32 questions
were 20 pipeline names (only the shipped `SYN_` templates), 5 primary keys, 5 start
dates, application_name and email_to.

**After post80 (kept for reference) — the App asks before generating.** post80:
- **The pause before generating:** the App's run asks every blocking question known
  before generating — required environment values (document `run`), unstated values,
  LOB per file, the notebook's landing — ONCE in the run's dialog, then generates once
  (`DemoRunner._before_generate_questions` / `_ask_before_generate`, status
  `pause_kind`).
- **Environment answers** become the picker's `overrides`.
- **"Proceed with unresolved"** leaves them to the post-run list; the landing is
  answerable there too (`GenerateRun.landing_asked`).
- **A blocked run** shows "Complete the blocking questions first", not "View results"
  (status `blocking`).
- **Continue** works with nothing picked.
- **Still post-run:** the merge-load primary-key QUESTION.

**After post79 (kept for reference) — pipeline names autoset.** post79 (Venu):
- **Autoset:** PIPELINE_NAME defaults to the naming convention, written unasked
  (`conventions.profiles.acfc_prx.pipeline_name_autoset: true` in `acfc_env.yaml`;
  `input_choices.resolve_feed` gives the flow items kind `profile_default`;
  `faq_answers` carries them with evidence `choice:profile|…`).
- **Placeholders:** a `SYN_` template is NEVER written, not even on `use_default`.
- **New template tokens:** `{source_code}` `{schema_domain}` `{lob}` `{object}`
  `{object_code}` `{src_format}` `{frequency_code}`, from the IIG's own cells
  (`input_choices.feed_tokens`).
- **App:** pipeline names are one line plus a "Change pipeline names" / "Set pipeline
  names" panel (`InputsNeededBanner.PipelineNames`), never radios per name; `dist`
  rebuilt (npm ci works here).
- **Interim templates:** the prod convention, reconstructed from the Pyx golden IIG
  (`frd_sttm_pairs/pair_11`). They live in the volume overlay
  (`state/overlays/acfc_prx.yaml`; backup `.bak_20261020_pre_post79`). On pair_11 they
  give 4 of 8 child names exact; the masters differ only in the frequency code.
- **Open:**
  - Venu: EDO Naming Standards (`/Workspace/Users/<me>/standards_docs`) vs prod as
    ground truth.
  - The App still can't read the volume (Raj's `USE CATALOG` grant), so it keeps
    asking.
  - `pipeline_name_corpus` refuses a name equal to a prod one.

**After post78 (kept for reference) — gold layer, v2.2.** post78:
- **One feed per target table.** `GoldFeed.manifest_index` / `blocks`; `feeds[<i>]` is
  numbered over the whole manifest, so a `--table` run keeps the same keys.
- **`length` role:** `field_length`, or the `(n)` of a type → proposal.
- **`--questions-xlsx PATH`:** one sheet per feed. It quotes cells, so it is refused
  inside the repo; a `/Volumes/` path always goes through the Files API (the
  `test_storage` mount rule).
- **`--answers FILE`:** an answers.yaml through `layout.answers.load_answers`, or the
  filled workbook. Answered keys are recorded under `GoldFeed.answered` and counted as
  filled.
- **v2.2 run:** 390 rows → 12 feeds; 1,793 / 107 / 210. The workbook (210 rows) is
  `/Volumes/d1_dlk/codegen/state/edh_e2e/questions_run_20261020T180637Z_fa5270e.xlsx`.
- **Profile docs:** `ENVIRONMENT_ACFC.md` §h; `OPEN_QUESTIONS.md` §7.1–7.4 (the client
  questions).
- **`test_m93_chooser`** passes again (`DocumentIndex._bounded` budget fix + the test
  warms the SDK import). It had failed since c0358f6; it is never deselected.

**After post77 (kept for reference) — gold layer.** post77 = the EDH E2E gold-mapping
reader: `codegen read-edh-e2e --input DIR --out FILE [--table N]` (`codegen.layouts.edh_e2e`
-> `codegen.contracts.gold.GoldContract`). Rules: stated = filled, derived = `status:
proposed` + INPUT_NEEDED, unstated / free text = QUESTION `feeds[<i>].<role>` /
`feeds[<i>].columns[<j>].<role>` (i = manifest index), cell quoted. Profile = config
section `edh_e2e:` (target_schema, source_catalog_map, scd2_mode, sk_strategy,
function_map); empty in the tracked config, values go in the ACFC overlay. Docs:
`docs/acfc/EDH_E2E_JSON_SCHEMA.md` (dialect v2.1, grammars), `EDH_E2E_EXTRACTION_DEFECTS.md`
(A extractor / B source document, v2.1 status), `EDH_E2E_READER_RUN.md` (11 real files:
1,470 filled / 98 proposed / 200 QUESTION, no crash), `GOLD_STTM_SHAPE.md` (the Provider
Lakehouse STTM, a different family). Synthetic fixtures `tests/fixtures/edh_gold_synthetic/`
(rebuilt by `scripts/gold/build_edh_synthetic.py`; `scripts/gold/profile_edh.py DIR` =
counts only). The reader and the profiler share their regexes (a test pins it). Open: v2.1
retargeted m10's second block (the workbook names another table) and moved m0's types into
`field_length` — ask the extractor owner; no SQL emit yet (the contract is the input).

**After post76 (kept for reference).** post76 = Layer 2 as its own stage after the
outcome (`codegen.layer2_stage`, `GenerateRun.layer2` after `finish`): ONE request per feed
(`complete_batch` / `providers.ask.ask_batch`), `--layer2 now | defer | skip`
(`reasoning.layer2_cli` now, `reasoning.layer2_app` defer; deferred = `<feed>/candidates/
layer2_pending.json`, asked by `codegen layer2 --output DIR` or `POST /api/demo/layer2`).
Candidates never affect the verdict (`compute_verdict` takes none; Layer 2's findings are
informational flags `unimplemented_rule_has_candidate` / `layer2_*`); notebook v2's review
%md is the TRAILING cell, re-emitted by the stage (`notebook_v2.with_review`); manifest
`layer2` block + feeds[].`review_candidates` (pending | done | skipped | none). Tests that
pass `generate_feed_result` directly get `layer2="now"` (the stage runs inside); the CLI /
App pass `"later"`. Test: `test_layer2_stage.py`. Pre-existing here (also at post75):
`test_m93_chooser.py` 2 failures on this Windows host.

**After post75 (kept for reference).** post75 = the leak gate in the repo:
`codegen.leakgate` (harvest + static denylist BY PATH from `<state root>/leakgate/` on the
volume + the repo-token dictionary fallback + self-match + hash-only records + the
approved / held lane). Callers: `tools/iig_diff.py --export-scrubbed --gate-pairs DIR`,
`scripts/scrub_check.py --leak-gate PAIRS_DIR path ...`, the container runner
`scripts/container_harness.py`. Client terms never in the repo. Test: `test_leakgate.py`.

**State after the post75 12-pair run (2026-10-20, nothing queued, docs-only note).**
- Last run: acfc-results `35b8ef8`, `results/approved/run_20261019T223801Z_6b20a1b/` (gate
  CLEAN, 0 hits). PASS_WITH_OPEN_INPUTS 01 02 04 11 12 (pair_11 notebooks 5/5); NEEDS_ANSWERS
  07 (2 `sheets[i]/standard/column`), 10 (10 keys: delimiter / lobs / load_strategy for
  feeds[1..3] — only feeds[0] was answered); FAIL 05 06 08 09 (contract mismatch); CRASHED 03
  (`STTM data type invalid … [TemplateGapError]` after its load_strategy answer — a bug).
  pair_01 score 28.8; its scrubbed export fails the shared gate on 1 column_value hit
  (SELF_CHECK only pushed). pair_11 time = layer2 35 calls / 528 s (answers don't change it).
- Fix at home (the BSA pass found values the extractor missed): FRD "Truncate & Load"
  (pair_03), audit columns as plain mapping rows (pair_08), stage load strategy in an STTM
  summary sheet (pair_09), empty stage type with the standard type in the same row (08, 10),
  the Pyx FRD's `<landing container>/inbound` root stated in prose (pair_11).
- Landing convention (step 3): corpus coarse shapes top 50.0% / 30.8% — under 60%, the
  overlay's `landing_proposal` left as is (the knob is `landing_proposal`, no
  `paths.landing_template`).
- How runs happen now: the cluster's pip goes through Nexus and BLOCKS `pip install -e <clone>`,
  so the 12-pair run is the CONTAINER runner: clone at the head into `/tmp/cgs/clone`, pairs
  copied from `/Workspace/Users/<me>/frd_sttm_pairs`, state copied from the volume, then
  `python <clone>/scripts/container_harness.py --pairs-dir … --state-dir … --out … --work …`
  with `.venv-d1` (never install anything; it lists missing dists). Push: clone acfc-results,
  copy the run into `results/approved/<run>/`, `scripts/gate_approve.py`, commit as
  codegen-harness, push. `codegen-watch` runs still die at the pip step (it swallows it).
- Volume `d1_dlk.codegen.state`: `environments/d1.yaml`, `overlays/acfc_prx.yaml`,
  `answers/pair_{1,2,3,4,7,8,9,10,11,12}/answers.yaml` (BSA pass: `source:` per answer,
  `assumed: true` where no document states it), `leakgate/denylist_local.txt`.
- Open with others: Raj — `GRANT USE CATALOG ON CATALOG d1_dlk` to the App SP (the App's
  state copy fails PermissionDenied until then; then re-check the picker: storage_account
  from environments/d1.yaml). Raj / Sarath — which cluster or external location reads the
  landing container (the CAQH notebook proof's read fails on D1-FSC-ETL-SC-S-16.4-01: no
  credential; 0 of 16 visible external locations cover the account).
- Auth in the container: the OAuth profile was saved as `codegen-oaut`, but the environment
  rewrites `~/.databrickscfg`; use `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg` (profile
  `codegen-oaut`, auth_type databricks-cli) for `apps logs` / the App URL. The mlflow Stop
  hook was removed from `/app/python/source_code/.claude/settings.json`.

**Before post75 (kept for reference) (2026-10-19, after post74).** post74 = the post73 12-pair report's items
(acfc-results `run_20261019T193332Z_fe61bc4`; `CHANGELOG_ACFC.md` lists all 8), one commit
each; synthetic reproductions in `tests/post73_pairs.py` (Family E with per-cell
overrides):
- extract-sttm (generic): profile `skip_row_markers` + ONE `skipped_rows:feeds[i]` flag
  (replaces a marked row's `field_unmapped`); `extract.type_format.split_type` (format
  split off a type, size kept; `*_datatype_format` contract fields; IIG date rules read
  them); one row's missing type = blocking `QUESTION feeds[i].columns[j].target_type`
  (no stage column = skipped row); `run_errors.CONTRACT_RULES` (question | fail per rule,
  `contracts.validation.classify`; first line `contract validation: <rule> (<n>)`).
- `codegen.answer_keys.canonical_key`: keys are role names; `_merge_frd` and
  `load_answers` go through it.
- Open landing = ONE key per feed, the IIG cell's `feeds[<i>].src_adls_path`
  (`metadata_template.landing_question`; INPUT_NEEDED, blocking on a notebook run);
  template `landing_proposal` shown as agent_proposal (ACFC overlay value is a TODO D1).
- iig_diff export: `repo_token_dictionary` (GATE_SCOPE text files) + harvested gate terms
  (`--gate-terms`) + static denylist; the fixture universe is no longer the keep-set.
  PROVISIONAL best guess (SELF_CHECK header says so) - Soham: don't reproduce the D1 gate
  further.
- `CODEGEN-USAGE` stderr marker beside every MODEL USAGE line; STABLE
  `run_errors.model_usage` / `usage_summary`. Layout = at most 1 request per document;
  Layer 2 scales per feed × unmapped rule (not changed; D1 timing pending).
- Windows: tests/test_state_volume_mirror.py fails here (symlink privilege, WinError
  1314) — pre-existing, logged in docs/spiral-log.md; passes on Linux. Verified before
  the push: dev `.venv` 1937 passed / 28 skipped / 7 failed (those), `.venv-d1` 1652
  passed / 77 skipped / 6 failed (those); ruff src tests clean.
Open for D1: re-export pair_01 with the new vocabulary (+ `--gate-terms`); confirm the
landing proposal against the corpus; pair_11's MODEL USAGE split (layout vs layer2).

**Session end (2026-10-19, home, before post74).** Head `dded7d7` (pushed from ACFC after post73: the
SFMC-shaped notebook / primary-key tests and the acfc_shapes registry test skip through
`conftest.require_fixture_files` when the client fixtures are absent; a clean clone had
dev 1 failure, the timing-dependent m93 chooser test). post70 + post71 were reported to
Soham; nothing is queued at home. Open:
- For Aruna (docs/acfc/OPEN_QUESTIONS.md): §4 PHI masking (no IIG cell), §5 v1 / iig_v1
  use the not-null list as the key, §6 SCHEMA_DRIFT_FLAG. §6 was kept as written by
  request, so its "Now (post70)" bullet still says the overlay writes Y (post71 = N).
- The post50 D1 asks below (SRC_COLUMNS golden cells → rule 4 cherry-pick; the
  PIPELINE_DESCRIPTION dump; the workspace-folder token) are still open.
- Verification is D1 via Genie (MIDS, Pyx, CAQH + one imported notebook); no home live
  SD run.

**After post73 (2026-10-19, kept for reference).** post73 = the refresh error is exception types + error code only (no SDK config dump). post72 = `CODEGEN_STATE_DIR` on the UC
volume `d1_dlk.codegen.state` (`app.yaml`). An App has no `/Volumes` mount:
`codegen.state_mirror` copies it read-only via the Files API at import and before each
generate request (`main._refresh_state`, config reloaded on change);
`config.state_root()` answers the copy; the state line names volume + copy. Volume
holds `environments/d1.yaml` (from the D1 Git folder's codegen-state) and
`overlays/acfc_prx.yaml` (authored from the pair_2 / pair_12 goldens; no
`naming.pipeline_name`: no derivation table). Harness: `codegen-pull-and-run` /
`codegen-watch` take a `state_dir` job parameter (the runner notebook sets
`CODEGEN_STATE_DIR` and clears the per-folder variables). USE CATALOG on `d1_dlk` for
the App SP is Raj's grant. Test: `test_state_volume_mirror.py`.

**After post71 (kept for reference).** post71 = SCHEMA_DRIFT_FLAG default back to
N in acfc_env.yaml (prod rows, SFMC reference, pair-1 golden; the Y was the test-cells
sheet only); `feed_overrides.<feed>.schema_drift_flag` sets a feed Y. Decided: no live
SD run at home — D1 via Genie is the verification.

**After post70 (kept for reference).** post70 = three items:
- `scripts/scrub_check.py` class `client_storage_account`: profile accounts and
  `STORAGE_ACCOUNT = <pattern token>`; SYN-shaped / placeholders exempt.
- TGT_PRIMARY_KEY via `codegen.primary_key` (template knob `primary_key_input`, on in
  acfc_env.yaml):
  - the STTM contract's `load_rules.natural_key` (Primary Key cells) is apart from
    `not_null_columns`; `FrdFeed.key_statement`; `spec.frd_key_statement`;
  - a proposal only from an explicit signal (STTM PK cells, FRD statement, FAQ
    `natural_key_columns`, corpus row), shown on `INPUT_NEEDED
    feeds.<feed>.primary_key` and written only when chosen (`key_from_contract`);
  - a merge with no signal = blocking `QUESTION feeds.<feed>.primary_key` (cli
    `_key_question`), candidates = the not-null columns;
  - v1 / iig_v1 still use the not-null list (OPEN_QUESTIONS §5).
- Notebook v2's IIG-driven cells: drift (`SCHEMA_DRIFT_FLAG`), recycle (`RECYCL_*`), the
  final run-report cell, and an open merge key in `OPEN_CELLS`. SCHEMA_DRIFT_FLAG
  defaulted to Y in post70 (back to N in post71); `feed_overrides.<feed>.schema_drift_flag`
  sets one feed (OPEN_QUESTIONS §6). Parity tool: "IIG-driven"
  vs "only v1". Tests: `test_storage_account_scrub.py`, `test_primary_key_proposal.py`,
  `test_notebook_v2_iig_cells.py`. The SFMC-shaped v2 fixtures pass a typed key
  (`notebook_v2_fixtures.key_answers`).

**After post69 (kept for reference).** post69 = notebook v2 for acfc_prx
(`conventions.profiles.acfc_prx.notebook_version: v2`; every other profile keeps v1).
`codegen.emit.notebook_v2` renders from `FrameworkArtefacts.payload` (the IIG rows; a
notebook-only run emits the framework into a scratch dir and counts its checks /
flags) through `templates/notebook_v2/*.j2`; `codegen.emit.notebook_files` = cells ->
.ipynb + Databricks .py + the checks (nbformat, compile, ruff, scrub). Files
`<feed>/notebook/<slug>.{ipynb,py}`. DQ registry `notebook_v2.RULES`; unknown class =
markdown + `notebook_rule_not_implemented`; open needed IIG cell = `OPEN_CELLS` stop +
`notebook_iig_cell_open`. Writes happen in the run cell after the DQ rules (the
specified cell order 3-6 defines steps; the run cell executes them). `frd_path` /
`sttm_path` now reach `generate_feed_result` (provenance coordinates). Tests:
`test_notebook_v2.py` + fixtures `tests/notebook_v2_fixtures.py` (SD = CV golden, SFMC,
TPL from SFMC renamed, PRX = pair 1). Tool: `tools/notebook_parity.py`. Open: SD parity
shows v1-only PHI masking / schema drift / post-load DQ / run report / recycle, the
file-name pattern style (IIG `prefix_star` vs FRD pattern) and the natural key (v1 FAQ /
contract key vs an empty IIG TGT_PRIMARY_KEY).

**After post68 (kept for reference).** post68 = the notebook path made honest
(cell layout untouched; session B is the layout). One GenerateRun for both outputs: a
blocking line withholds the feed's notebook (`run_stages.remove_notebook`, NOTE
`feeds.<feed>.notebook`; notebook-only = `written: false`); owed inputs / choices /
answers-file environment apply in notebook mode (`owed_inputs._template` ignores the
mode); manifest stage `notebook_emit`; `codegen.emit.notebook_env` puts catalogs,
account, containers and container-relative paths into feed_spec (`adls_uri()` at run
time; a missing value = QUESTION on notebook runs; no environment block = contract
values); `codegen.notification_contacts.redact_contacts` for FRD addresses; nbformat in
dev + d1 constraints, conftest validates every emitted notebook. Tests:
`test_notebook_path_honest.py`, `test_notebook_validation.py`,
`OutputDefault.test.tsx`. Inventory item 14 (stale RFC / contracts.pairs / replay /
SharePoint) left alone by request. Next: Genie runs MIDS, Pyx, CAQH on D1 + imports one
notebook (no home live SD run — D1 via Genie is the verification).

**After post67 (kept for reference).** post67 = the live-run confirm dialog is
measured: tokens per call (`StageUsage.input_tokens / output_tokens / cache_read_tokens`,
FM API `chat(usage=)`), cost = tokens × `reasoning.prices` (`anthropic` list rows +
an EMPTY `databricks_fmapi` set for the workspace's DBU rate; each row has a `source`;
`PriceTableConfig.rate`; the dialog says "at Anthropic list price; Databricks bills in
DBUs" or "at this workspace's rate"), the
App's last 10 live runs per (conventions profile, outcome) (`ui/backend/run_history.py`,
`live_run_history.json` in the state role; wall-clock minus dialog waits; CRASHED / FAIL
not kept), the dialog (`ui/frontend/src/liveEstimate.ts`) ranges over PASS /
PASS_WITH_OPEN_INPUTS runs only ("no history yet for completed runs" under 3), a second
line for NEEDS_ANSWERS / GATE_FAIL runs, no dollars when no tokens; `demo.estimated_*` /
status `estimates` removed. Test: `test_live_run_history.py`. Open for Soham: the
second line says "stopped for answers" for GATE_FAIL runs too (the wording as given).

**After post66 (kept for reference).** post66 = the artefacts panel's per-feed
line is `artefacts.ts reviewSummary` (sheets · rows · open inputs (blocking) · empty by
rule: <label> (<reason>)) from `framework.empty_by_rule` + `framework.open`
(`GenerateRun.review_open`: feed + run-level lines); the derived ratio is the report's
labelled line (`framework.derived_line`). post65 + post66 were reported to Soham
(2026-10-16); nothing is queued. Open after post66 (Soham to decide): run-level open
lines count in every feed's summary; a feed generated outside `DemoRunner` has no
`framework.open`, so its summary omits the open-inputs part; the summary keeps the old
bold styling. post65 = the Dashboard's metadata-sheet
preview and "Publish to Unity Catalog volume" sections are gone with their routes
(`/api/demo/metadata-sheet[.xlsx]`, `/api/databricks/publish[-target]`); the payload
builder and `codegen databricks-publish` stay. post64 = the "Framework artefacts" output
toggle tooltip says "DDL + BSA-annotated IIG for the existing ingestion framework".
post63 = wording only: the metadata-sheet
preview footnote and the report's framework section ("Framework artefacts",
`framework.presented_files`) say what the artefacts panel says (`artefacts.ts`
`APPROVAL_NOTE`): the BSA-annotated IIG is the approval artefact, CI/CD applies the DDL.

**After post62 (kept for reference).** post62 = App-only demo cleanup (one commit
each): no source-files panel / `/api/demo/source-files` route; the artefacts panel shows only
DDL / IIG / IIG_REVIEW / ADDITION.md (`ui/frontend/src/artefacts.ts`; the other files still
written); ADDITION.md = file table + "Review flow" + blank IDs (no inserts / config rows);
FRD picker "none chosen" unless chosen or paired (`DemoRunner.effective_frd` is None for a
chosen STTM without one; status `frd_paired`; `frd_warning` gone; `test_frd_default.py`);
`classify_workbook(..., iig_sheets=, review_sheet=)` → `iig` / `iig_review` (App index only,
`docindex.CLASSIFIER_VERSION` re-reads old "unclassified"), left out of the chooser lists.

**After post61 (kept for reference).** post61 = two kinds of default
(`codegen.input_choices`, `Defaulted.kind` / owed `default_kind`): `profile_default` (email
status set, EMAIL_TO, notebook names `notebook_name.<leg>`, `src_file_name_style`) is WRITTEN
unanswered — source `profile`, no NOTE / gate flag, not open (a NOTE line, `applied:` in the
answers template, `OwedInput.applied` / `is_open` in the App) and changeable via
`naming_standard`; `agent_proposal` (PIPELINE_NAME, APPLICATION_NAME, ACTIVE_START_DATE) stays
proposed-not-applied. Unset `default_kind`: `{token}` default = proposal, literal = profile.
Test: `test_default_kinds.py`.

**After post60 (kept for reference).** post60 = ONE generate entry point:
`cli.generate_feed_result` (the feed pipeline; the App's `GenerationStore._generate_feed`
wraps it — no more mirror) + `codegen.generate_run.GenerateRun` (open lines, choices,
CRASHED / GATE_FAIL quarantine / written, outcome, CODEGEN_STAGES.json), driven by
`cli._run_pairs` and the App's `DemoRunner._generate_specs`. App and CLI manifests are
byte-identical for the same pair (`test_generate_entry_point.py`); the App's state reads
`outcome` / `written` from the manifest (`status.outcome`). Tests that patch the pipeline
patch `codegen.cli` names (`cli.compute_verdict`, `cli.build_provider`, …).

**After post59 (kept for reference).** post59 = PIPELINE_NAME (+ APPLICATION_NAME,
EMAIL_TO, email statuses where a default exists) as a three-way choice (`codegen.input_choices`):
use_default / naming_standard / leave_blank. PROPOSED IS NOT APPLIED — unanswered = blank cell
+ INPUT_NEEDED with the proposal and its template; only an explicit choice (answers file
`choice:` / `standard:`, App Confirm `POST /api/demo/input-choices`) fills a cell, with an
`frd_unstated:` flag; manifest `feeds[].inputs.<key>.source`. Shipped templates are
`SYN_PL_…` placeholders; real ones in `codegen-state/overlays/acfc_prx.yaml`. Collision
check: `pipeline_name_corpus`. File tie-break: `file_tie_source_priority` / `file_tie_shape`,
the BSA's answer cached as `LayoutProfile.file_choices`. Tests: `test_pipeline_name_choice.py`,
`test_file_tie_break.py`.

**After post58 (kept for reference).** post58 = one item: generate outcome
`PASS_WITH_OPEN_INPUTS` (exit 0) = workbook written, every open line non-blocking.
`CODEGEN_STAGES.json` `questions: [{line, key, scope, blocking}]`: QUESTION / UNRESOLVED
are blocking, INPUT_NEEDED is not; feeds carry `written` + `open: {blocking,
non_blocking}`. NEEDS_ANSWERS (exit 3) = ANY blocking line open, workbook written or not
(Soham: an empty storage account is not deployable; the harness must not call it a pass)
— env-required QUESTION (mock and live), `lob_by_file`, and now also an unasked held-back
feed without `--feed`. STABLE `run_stages.pair_outcome(steps, out_root)` = the worst step
(generate's status from the manifest when its `exit` matches); `acfc_run.py` prints it.
Test: `test_open_inputs_outcome.py`. The App path still writes no manifest (open item below).

**After post57 (kept for reference).** post57 = five items from the post55 D1 report
(`CHANGELOG_ACFC.md`), one commit each:
- Printed answer keys say `sheets[<i>]/<layer>/<role>` (0-based workbook position), never a
  sheet name; internal keys (profiles, caches, App) unchanged — translate only at the edge
  (`codegen.layout.sheet_refs`; `PendingAnswer.sheet_index`). Answers files accept either form.
  Test: `test_sheet_ref_keys.py`; cold-pair fixtures pinned in the new form.
- `value.unstated` only = `ContractUnstatedError` (subclass of ContractMismatchError) raised by
  `resolve_feeds` after every feed: CLI prints one `QUESTION feeds[<i>].<field>` each, exit 3,
  generates the rest; `generate --answers` fills it. Conflicts still FAIL. Test:
  `test_unstated_values.py`.
- Stated paths (`codegen.resolve.stated`, first thing in `_resolve_one`): an FRD
  `<Label> : <value>` cell with a label in the profile's `field_label_synonyms` for that
  field -> `<value>` + `label_stripped`; a landing `<account>/<container>/<folder>`
  (`storage_account_pattern`) or abfss URI -> the run environment's account / container,
  folder byte for byte, `environment_mismatch` when the document's differ (never its value).
  Conventions profile `path_whitespace: keep | fail` (default keep): `normalise_path` never
  touches whitespace, ONE `iig_path_whitespace:<SHEET>!<A1> (<COL>)` flag per cell. Tests:
  `test_stated_landing.py`, `test_path_whitespace_kept.py`; `test_gate_fail_breakdown.py`
  runs under `fail`.
- iig_diff: `order` pairing (`name_components`), `template-only` status, date == midnight
  datetime, `segment_codes` (profile) via `segment_columns`. `tools/iig_rescore_export.py`
  re-scores a scrubbed export at home; pair_01 3.2 -> 28.3
  (`docs/acfc/iig_exports/pair_01_post55/RESCORE.md`). NOTE: the suite runs WITHOUT the ACFC
  overlay, so the iig_v2 template in tests lacks the overlay's PROCESS_NAME..UDF5 columns.
- Error lines: `located(..., role=, type_text=)` -> `(role X; type Y)` in the coordinates tier,
  allowlists `run_errors.ROLE_WORDS` / `TYPE_KEYWORDS`. Test: `test_error_roles.py`.
- Open: pair_05 / 06 fixes wait for Genie's answer on the segment vocabulary. RESCORE.md also
  lists what is left (DQ rules pair nothing; agent SRC_ADLS_PATH starts `/Path : `).

**After post56 (kept for reference).** post56 = two items (`CHANGELOG_ACFC.md`):
- Per-feed IIG cell counts in `CODEGEN_STAGES.json` (`feeds[].iig_cells`: per sheet
  `open_for_bsa` / `empty_other` / `template_blanks` + `open_inputs`;
  `run_stages.iig_unpopulated(out_root)` is the harness reader). The old harness metric
  = empty cells of the sheet's used range (reproduced pair_02's numbers on the home SD
  run); the "constant" was one workbook counted for two pairs. One input can open several
  cells, so cells ≠ inputs. Test: `test_iig_cell_counts.py`. openpyxl 3.1.2 keeps a
  `load_workbook(path)` file open, so a workbook read on the generate path must come from
  its bytes, or the quarantine move fails on Windows (`.venv-d1` caught it).
- One environment resolver `codegen.environments.resolve` (CLI + App). Per-field
  `RunEnvironment.sources` are shown in the picker. The `codegen-state` root is the
  `CODEGEN_STATE_DIR` setting (`config.state_root`), and the App logs `state_dirs_line()`
  at startup. The App's 10:07 miss = a staged copy without `codegen-state/`
  (gitignored), so ACFC must copy it into the staged tree and set the variable. Test:
  `test_environment_resolution_parity.py`.
- Harness asks: read per-feed `iig_cells` (never a workbook glob); set `CODEGEN_STATE_DIR`
  on the App.

**After post55 (kept for reference).** post55 = the post51 12-pair report's
extraction failures (acfc-results `run_20261015T074546Z_97fe673`), one commit each,
`CHANGELOG_ACFC.md` has the items. Verified before the push: dev `.venv` 1687 passed / 28
skipped / 1 failed, `.venv-d1` 1399 passed / 68 skipped. The one failure,
`test_demo_ui.py::test_choosing_an_sttm_auto_pairs_its_vdd`, comes from state: a stale
`ui/backend/state/document_index.json` makes it fail at 7620649 too, and it passes at
post55 once that file is removed (test-isolation gap, not fixed). Ruff clean,
scrub_check 68 hits / 18 rows / 13 files (unchanged). Synthetic reproductions live in
`tests/post51_pairs.py` (Family E builder, untitled F2 FRD). The version comes from the
last `CHANGELOG_ACFC.md` entry + 1, never from the prompt. Open after post55:
- **Item 4 (pairs 03 / 04), Soham's call:** keep the contract mismatch a FAIL until the
  D1 rerun under post55 shows their mismatch kinds (the coordinates line now prints the
  counts). The FRD contract has no column list; `column.*` mismatch kinds are labels that
  nothing raises. The set differences are `table.*` / `segment.*`. Candidate rule: a
  table-only difference = exit 3, one QUESTION per table, answer frd|sttm.
- **D1 asks for the post55 run:** pair_01's line now carries flags per type plus the
  derivations findings per rule. Also run `tools/iig_diff.py --golden <PRX golden> --agent
  <pair_01 quarantine>/*_IIG.xlsx --out … --export-scrubbed …` and bring the per-sheet
  cell-diff counts home (`GATE_FAIL.md` names the step). Decide gate vs golden from those.
  pair_03's MODEL USAGE line now shows the live seconds per stage. Pairs 08–10: the
  `NOTE frd/family` line says which F2 signal matched.
- Pair 10's FRD (no section labels in the SR tables) now yields an F2 feed whose
  required fields are unresolved (QUESTIONs / gap chain), not the old "cannot be read".

**post55 rules (2026-10-15).**
- Segment cells in `extractor.discovery.unsegmented_markers` (or blank) = unsegmented;
  they are kept OUT of `segment_synonyms` because those spellings also mark banner rows
  and segment-named sheets. Test: `test_unsegmented_markers.py`.
- Audit datatypes are conventions-profile fields (`audit_datatypes`,
  `audit_flag_datatypes`, `audit_flag_suffixes`; `extract.audit_types`); each listed type
  must be a key of `contracts.sttm.AUDIT_DATATYPE_SPELLING`. Test: `test_audit_flag_types.py`.
- F2 detection = `frd_docx.sr_signal` (row-label fingerprint, caption second); a table
  with the SR labels is never an F1 section table. "Cannot be read" raises
  `FrdUnreadableError` (count + `header_fingerprint`s). Test: `test_f2_untitled.py`.
- The coordinates-tier marker gains `tables` / `flags` / `violations`, vocabulary + ints
  only (`run_errors.error_tables`, `kind_counts`); `GateCheck.violations` counts a failed
  check's findings per rule. Test: `test_gate_fail_breakdown.py`.
- `StageUsage.seconds` (live round-trips via `reasoning.usage.timed`). Test:
  `test_model_seconds.py`.

**After post54 (kept for reference).** Pushed head `7620649` (0.5.8.post54); post52
(`c236840`), post53 (`1e2f813`), post54 (`7620649`) each got their own bump; items in
`CHANGELOG_ACFC.md`. Verified at head: dev `.venv` 1643 passed / 29 skipped, `.venv-d1`
1354 passed / 69 skipped, ruff clean, scrub_check 68 hits / 18 rows / 13 files (unchanged).
The post54 report was given. Nothing queued at home; open items:
- **App path:** done in post60 (the App drives `GenerateRun`: quarantine + manifest).
- **Harness (Genie's side):** read emit-stage statuses, the generate outcome and the
  workbook paths from `CODEGEN_STAGES.json` (`run_stages.read_stage_manifest(out_root)`),
  never a glob of the shared output folder (how pair_02's workbook got counted for
  03 / 04 / 07); show GATE_FAIL as "complete, gate failed, review only"; push
  `first_error_line`, write `first_error_line_full` only under codegen-outputs/.
- Parser / extractor failures of pairs 05 / 06 / 08 / 09 / 10: done in post55.
- The post50 D1 asks (below) are still open.
- Scratch leftovers for Soham to delete by hand (Windows long paths; `rm -rf` is blocked):
  the session scratchpad's `head_wt` folder (already unregistered from git) and `C:/t52a`.

**post52–post54 rules (2026-10-15).** From the post51 12-pair report (acfc-results
`run_20261015T065841Z_97fe673`, read via `git show`):
- Error lines are TWO tiers (`codegen.run_errors`, STABLE): `first_error_line` = coordinates
  only (built from `REASONS` / `STAGES` / ints — what the harness pushes),
  `first_error_line_full` = quoted (codegen-outputs/ only). The CLI prints FAIL lines via
  `cli._fail(stage, text, reason, coord, …)` = the line + a `CODEGEN-ERROR {json}` stderr
  marker; `main` adds an "uncaught" marker before re-raising. A NEW raise that quotes
  document text goes through `run_errors.located(exc, Coord(...), "<REASONS code>")` (a
  test checks every code; `Coord` = a DOCS name + integer axes only). Exit 0 / 3 = no
  error line in either tier; a Python warning block is skipped whole. Tests:
  `test_run_errors.py`, `test_error_coordinates.py` (SENTINEL through the real CLI).
- `generate` outcomes (post54, `codegen.run_stages.OUTCOMES`), exit 1 for all:
  CRASHED (exception mid-write) = the feed's partial emit files deleted, emit stages
  SKIPPED; GATE_FAIL (files complete, gate said no) = files moved byte for byte to
  `<output>/<feed>/quarantine/` + `GATE_FAIL.md` (failed checks + flag counts per
  `flag_type`, never names / values), emit stages PASS, manifest `generate: {status:
  GATE_FAIL, label, quarantine}`, REASONS phrase "gate verdict FAIL (complete, review
  only: quarantined)"; FAIL (nothing written: mismatch, no `--feed` match) = emit
  SKIPPED. A rerun clears the feed's old quarantine; an uncaught crash writes the
  manifest first; `iig_diff.find_build` still finds the quarantined stamp. Tests:
  `test_generate_outcomes.py`, `test_emit_stages_skipped.py`.
- Second test env `.venv-d1` (uv, Python 3.12, `-e ".[dev,databricks]"`, no `ui` extra;
  pins `constraints/acfc_d1.txt` = pydantic 2.8.2 / openpyxl 3.1.2 / ruff 0.17.0 …,
  documented in `docs/acfc/ENVIRONMENT_ACFC.md` §0): run the suite in BOTH venvs before a
  push. `model_*` pydantic fields need `protected_namespaces=()`
  (`tests/test_d1_environment.py`; `LayoutConfig.placed_confidence`, YAML alias
  `model_confidence`). Byte-pinned xlsx fixtures compare cell by cell when openpyxl ≠
  3.1.5; fastapi-only tests `importorskip`.
- post53: a NEW resolver mismatch goes through `resolver.mismatch_item(kind, text,
  names=…)` (kinds = `run_errors.MISMATCH_LABELS`) — the coordinates tier prints its
  COUNT (distinct names per kind), never the names; feed position = `feed N of M` from
  `original_frd_feed`; a path in a marker is `path_hint` (`<workdir>/pair_NN/…`). Test:
  `test_mismatch_counts.py`.

**post51 (2026-10-15; `CHANGELOG_ACFC.md` has the five items).** Head was the
bump commit after b95f39c. Item 0 (the post50 LEAK_GATE_BLOCKED 9 → 3 hits) was closed
"unclassifiable from current reports" (the gate writes 4-field stubs); the gate fix is
Genie's — it should emit per-hit JSONL (`output_file, pattern_class, term_sha256,
occurrences`), classified at home with `tools/hit_lookup.py`.
- `codegen.run_errors.first_error_line` + `codegen.term_hash.term_sha256` are STABLE APIs
  the harness imports. Config fields renamed in Python only: `discovery.thresholds`
  (YAML `validate`), `dml.db_schema` (YAML `schema`).
- Environments are PROFILES (D1 / A2 / PR): `codegen-state/environments/<name>.yaml`
  over the overlay block; a required key (storage account, containers) unset =
  `QUESTION run.environment.<key>`, exit 3. The suite runs on its own synthetic D1
  profile (`tests/environment_profiles/d1.yaml`; fixture `no_environment_profiles`
  opts out). ACFC must place `codegen-state/environments/d1.yaml` or every run exits 3.
- The ACFC-side overlay `codegen-state/overlays/<profile>.yaml` (after acfc_env.yaml)
  holds notebook names / versions, status sets, per-feed SRC_FILE_NAME styles
  (`docs/acfc/OVERLAY_FIELDS.md`); both `codegen-state/` folders are gitignored.
- Pre-push: `tests/test_tracked_scrub.py` vs the hashed rows in `docs/acfc/LEAK_LEDGER.md`
  (68 known hits / 18 rows; `scripts/scrub_check.py --rebaseline`); local terms via
  `CODEGEN_SCRUB_DENYLIST`.
- Home SD scorecard (three SD rows, `IIG test cells.xlsx`): diff 1 / 1 / 3, per-cell
  verdicts identical to c3f2153 (not 0: SCHEMA_DRIFT_FLAG Y vs N is the known round-6
  conflict; individual-risk OBJECT_NAME / SRC_FILE_NAME).

**Waiting on D1 since post50 (2026-10-14, still open) — nothing to code at home for these until Soham brings:**
1. **The D1 golden SRC_COLUMNS cells** (ADLS_DELTA + STGDELTA, pair_2 / pair_12). Home
   comparison (masked, given in the report): SD — current = the strict
   `source_column:target_column` reading (ADLS 86 pairs, STGDELTA 90). CAQH ADLS — current
   `Display:Display` (STTM display names), strict `Display:STAGE_COL`, golden
   `STAGE_COL:STAGE_COL` (neither matches; rule 4's variant matched 18/18). CAQH STGDELTA
   trailer — strict 9 pairs (own STTM audit rows) = golden; current 10 (adds LOB). If the
   cells confirm rule 4: `git cherry-pick 49d3e73 3b0082d` from local `wip/src-columns-rule4`
   (overlay `src_columns_style: source_target` + `audit_columns_from_sttm`), suite, bump.
2. The D1 dump for rule 2's PIPELINE_DESCRIPTION shapes (provisional; per-LOB fan-out cell
   left open by choice) and the D1 workspace-folder token (notebook path, home CAQH 40.0).
Home CAQH (mock, no LOB answers, vs p45 golden): 78.4 (baseline 77.2; 79.1 with rule 4).
Run-level inputs at home: environment, storage_account, application_name, email_to,
email_statuses; per feed 5 (4 pipeline names + active_start_date).

**post50 (2026-10-14) — four follow-ups** (marker **0.5.8.post50**): rule 4 (SRC_COLUMNS)
REVERTED pending the D1 golden cells (0132080; kept on local branch `wip/src-columns-rule4`);
2b01346 the handler two-notebook forms only for EDI 834 feeds (`edi_feed_patterns`: 834 / EDI
tokens in source / file patterns / name; else the single notebook, `_TPL` for TPL; NOTE names
the rule, `_notebook_rule`); 46272ce `gate.derivations.list_columns` (notebook NAME / PATH:
comma list OK when every segment passes); 12605b8 NullCheck / DeDup INPUT_PARAM = the stage
table FQN (`_target_fqn_cell`; owed items + FAQ companions dropped; open + NOTE only when the
catalog is unset — the environment's INPUT_NEEDED asks); bf1b6dc `email_status_input`
(run-level `INPUT_NEEDED run.email_statuses`, default all four; an answer trims the rows) +
iig_diff `status_columns` → `status-not-in-golden`. Home CAQH 78.4 (email 11.5 → 21.4).

**post49 (2026-10-14) — the client framework owner's rules 1–5**, one commit each
(8a2108d, 86bcc16, 8e4c65c, 49d3e73, 7d59a3f), marker **0.5.8.post49**; tests in
`tests/test_framework_owner_rules.py` + the touched files.
1. **PIPELINE_NAME is BSA-assigned.** ACFC `pipeline_roles` carry no name (`name: None`);
   owed cells `per_flow` on schedule + notebook: `INPUT_NEEDED
   feeds.<feed>.pipeline_name.<flow>` (FAQ companions `pipeline_name_<flow>`; answers_for maps
   `.`→`_`). iig_v2 email has no PIPELINE_NAME. iig_diff: `bsa_columns` → status
   `bsa-owned` (never missing / scored; `bsa_cells` cells + golden_filled).
2. **PIPELINE_DESCRIPTION long shapes** (corpus_cells values; short forms in `alternatives` +
   `alternative_shares`, NOTE only; `per_lob` + `per_lob_share`: a LOB-fan-out feed's ONE
   file_to_stg row is left OPEN with each LOB's description in the NOTE). Shapes provisional
   until the D1 dump of pair_2 / pair_12 cells — overlay-editable.
3. **FILE_ADLS empty for MFT** (`file_adls_rows: per_file`, `mft_landing_markers:
   [mftlanding]`; `metadata_template.mft_landing`): headers only + `iig_file_adls_mft` NOTE;
   non-MFT = one row per ADLS_DELTA row. iig_diff `mft:` block: ALL_FILES alias retargeted to
   ADLS_DELTA, FILE_ADLS presence `empty-by-rule`. pair_11's FRD landing is itself under
   mftlanding.
4. **SRC_COLUMNS** `src_columns_style: source_target` (source names when EVERY one is an
   identifier, else the stage columns throughout, verbatim) + `audit_columns_from_sttm` (a
   table's own STTM audit rows, in order). Home CAQH: ADLS SRC_COLUMNS 0 → 18/18, STGDELTA 3/3,
   ADLS TGT_COLUMN_NAMES 18/18; TOTAL 79.1 (no LOB answers). SD unchanged.
   **REVERTED on the branch (Soham: wait for the D1 golden cells)** — kept on the local
   branch `wip/src-columns-rule4` (49d3e73 + 3b0082d); re-apply with `git cherry-pick`
   once the D1 SRC_COLUMNS cells confirm the reading.
5. **Header check** — iig_diff `header_report` / `compare_headers` (score.json `headers`,
   console HEADERS first, `## Headers` first in sheets.md). Home CAQH: 2 golden-side issues
   (notebook DQ_NOTEBOOK_PATH / DELETE order = iig_v1's; email CRETAED_BY / CREATED_AT).
- Spiral: hook (a) on the rule-4 audit test — my oracle guessed the row layout; logged.

**post48 (2026-10-14) — the D1 exemption replaced by the provider.** A NAMED
environment with a key unset (blank / any `<<ENV:...>>`, D1's included) is FATAL
only under provider=live and no `--dry-run` (`environments._complete(live=)`; CLI
`cli._live_run`; App `_execute` checks it before the run folder exists) — the
message names every key, nothing written. Under mock: one `INPUT_NEEDED
run.environment.<key>` each (`unset_items` now covers named environments), cells
empty; a placeholder catalog is left unset (`catalog_unset_reason`,
`default_catalog_unset`), never written. At home every run now lists
`run.environment.storage_account` (D1's placeholder). `tests/test_d1_placeholders.py`
is the live-only check: conftest keeps the operator's `CODEGEN_PROVIDER` as
`CODEGEN_PROVIDER_REQUESTED`; started live it FAILS on any `<<D1:...>>` (10 at home).

**Restart here (2026-10-14, post47).** Three small items, marker **0.5.8.post47**:
- **Catalogs + connection ids per environment.** `EnvironmentConfig` gains
  `catalog_map`, `default_catalog`, `connection_ids` (acfc_env.yaml: D1 real, QA /
  PROD `<<QA:...>>`); `conventions.catalog_map` / the acfc_prx `default_catalog` /
  the ADLS connection-id constants are gone from the overlay. Readers:
  `codegen.environments.catalog_map` / `default_catalog` (resolver `map_catalog`,
  `emit.framework._config_default_catalog`); ADLS connection ids are
  `environment_cells` (`connection_ids.<name>`). Catalog cells get an `iig_env:`
  NOTE (`metadata_template._catalog_env_notes`). A NAMED environment (selected or
  default) with any key unset FAILS naming every key (`_complete`; superseded by
  post48 above: fatal only under provider=live). A CUSTOM one inherits nothing: missing keys stay unset,
  their cells empty (an unset catalog: `catalog_env_unset:<layer>` flag, DDL for
  that layer not written, never FAIL), one `INPUT_NEEDED run.environment.<key>`
  each, header `environment: SANDBOX (custom, N keys unset)`; `inputs.run:
  environment.<key>` fills one on a rerun.
- **INPUT_NEEDED scoping.** `owed_cells.<..>.scope: run` (APPLICATION_NAME,
  EMAIL_TO; NOTE prefix `iig_owed_run:`) + the environment = RUN-level: printed
  once before any feed (`owed_inputs.run_block_lines`), one block at the top of
  each feed report (`run_block`), `inputs.run` in answers_template.yaml. Feed-level
  keys are now `feeds.<feed_id>.<name>` (`inputs.feeds.<feed>`); the flat
  `feeds[<i>].` keys still read (`answers_template.flatten_inputs`). App banner
  groups by `scope`; `DemoRunner._run_level_inputs` (NOT `_run_inputs` — that is
  the documents tuple).
- **LOB question in the App dialog.** `resolver.lob_question_item(spec)` = a
  layout question of kind `files` (the unkeyed files, the FRD codes as
  candidates); the App appends it to the Answers-needed list, passes the gaps
  answers to the contract resolver (`resolve_pair(gaps=)` — it was never passed)
  and writes the applied ones to `<run>/answers.yaml` (`write_applied_answers`,
  every value quoted). Frontend: `LayoutQuestions` kind `files` (a `<select>` per
  file, posted `"<file>=<code>; ..."`), `pickFile`.

**Restart points post36–post46 moved verbatim to `docs/CLAUDE_HISTORY.md` §[H2].** Rules still in force:
- Owner rule (post45): a corpus value fills a cell only when `patterns.json` states it; anything else is a `<<D1:NAME>>` placeholder (`codegen.config.is_d1_placeholder`) — the cell stays OPEN with an `iig_d1_placeholder:` NOTE, never the placeholder text; `tests/test_d1_placeholders.py` is the live-only check (post48 above). → §[H2] post45
- `MetadataTemplateConfig.corpus_cells` (per tab / header; `by:` flow / status / frequency / notebook_kind, `shares`, `offer`, `alternatives`; NOTE `iig_corpus:`) never overwrites an FAQ / FRD / STTM-stated cell; `owed_cells` carry `default`, `when`, `header`, `scope: run`. → §[H2] post45, post46
- INPUT_NEEDED is NON-blocking (`codegen.owed_inputs`): exit 0, the cell written empty, the key under `inputs:` in `answers_template.yaml`, `generate --answers` fills it; NEEDS_ANSWERS = QUESTION / UNRESOLVED lines only; `scripts/run_round.py` records INPUT_NEEDED keys and keeps going. → §[H2] post45
- Environments: `environments:` in `acfc_env.yaml` with exactly one default; CLI `generate --environment NAME | --environment-file PATH`; neither = the default + `INPUT_NEEDED run.environment`; report header `environment: <name> (default|selected|custom)`. → §[H2] post46
- LOB lookup: FRD Region / LOB table → plan-id column → region (REG# token) → `conventions.lob_reference`; files still unkeyed = ONE blocking QUESTION `feeds[<i>].lob_by_file`, answer values QUOTED; gate `iig_single_value` (LOB, CLAIM_TYPE*, flags, TGT_PARTITION_VALUE) fails a list in a single-value cell. → §[H2] post46
- iig_diff (`tools/iig_diff.py` + `tools/iig_keys.yaml`): default `--pair-mode identity` (golden feed × flow from `docs/acfc/iig_goldens/01_pair_group_index.csv`); `--pair-mode key` is the old natural-key rule — never use it for a score. → §[H2] post40
- iig_diff statuses: `convention_columns` (generated names) never pair or score; FeedScope marks other feeds' rows `out-of-scope`; `sheet_aliases` map v1 ALL_FILES ↔ v2 FILE_ADLS; `group-level` agent master rows are not scored. → §[H2] post38, post40, post42, post44
- iig_diff outputs: `--dump-row SHEET[:N]` and the `RAW` / `FILE NAMES` / `RULES (D1 only)` blocks are D1-only console; `--export-scrubbed DIR` must re-scan to 0 hits; score.json / diff.xlsx / routing.csv carry prod text and are never committed; CREATED_BY / UPDATED_BY values are withheld. → §[H2] post43, post45
- Provider: ONE switch, `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` > mock, never inferred from the runtime; `--dry-run` under live prints `WARNING provider=live overridden by --dry-run → mock` first; conftest sets `CODEGEN_BLOCK_LIVE_MODEL` (live tests only with `CODEGEN_ALLOW_LIVE_TESTS=1`). → §[H2] post38
- Model JSON: `layout/model.py::parse_json_response` + one `RETRY_INSTRUCTION` retry for layout and Layer 2 (`reasoning/providers/ask.py::ask_candidate`, truncation retried at `reasoning.truncation_max_tokens`); failures logged `LAYER2 FAILED` / `RAW (D1 only)`. → §[H2] post43, post44
- Build identity: `codegen.build_info.build_identity()` on the CLI's first line, `codegen doctor` and `/api/health`; `generate` writes `CODEGEN_BUILD.json`; iig_diff refuses an agent workbook without one. → §[H2] "Build identity"
- D1 runs, home reviews: the prod goldens (`docs/acfc/iig_goldens/*.xlsx`) exist only on D1 — never force-add; Genie pushes scrubbed evidence to `acfc-results` / `acfc-pairing-check`, read here in place with `git show`, never checked out. → §[H2] "D1 runs, home reviews"
- Pushing: once per clone `git config core.hooksPath scripts/git-hooks`; pre-push refuses a code push with an unchanged version, a requirements marker ≠ pyproject, a tracked `_build.py`, or `ui/frontend/src` changed without `dist`; bump with `python scripts/bump_version.py`; docs-only pushes need no bump. → §[H2] "Pushing"
- Round gate: `python scripts/doc_fingerprint.py --compare docs/acfc/fingerprints/pair_2_sd_home.json <D1 fingerprint>` — a HARD line = STOP, WARN recorded; value hashes HMAC under the gitignored `codegen-state/fingerprint.key`. → §[H2] "Round gate"
- ACFC output is framework mode: `output.profile_mode: {acfc_prx: framework}` makes the App default to framework; a DDL column identifier must match `^[A-Za-z_][A-Za-z0-9_]*$` (`gate/ddl_names.py`). → §[H2] post36
- Document roles by name: `demo_sources.classify_document_name` (a role token anywhere, `iig` is never an input), `pairing_key` / `match_by_name`; a `pairing_overrides.yaml` (or `--pairs-file`) wins over everything. → §[H2] post37
- Blank Schema / TableName in an STTM band: schema from the FRD with a NOTE, else a QUESTION; table names are always a QUESTION, never derived. → §[H2] "Blank Schema / TableName"
- Home run recipe: `codegen layout --frd-contract-out … --answers …` (`--require-complete` exits 3 while an owed item is open; `--report-unresolved` lists them) → `extract-sttm` → `generate --feed <id> --output-mode framework --profile acfc_prx --iig-template iig_v2 --skip-tests --dry-run` with `PYTHONUTF8=1` and outputs in a scratch dir. → §[H3] item 2, §[H2] post43
- `tools/iig_diff.py --golden <xlsx> --agent <every feed's *_IIG.xlsx>` (scored as their union; `--scope feeds` default; `--golden-structure` describes the golden's shape). → §[H2] post38, "iig_diff"
- `tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens <email csv> --agent <outputs> --patterns <dir> [--top N]` (D1 only; the scrubbed `patterns.md` comes home). → §[H2] post44, post45
- `scripts/iig_scorecard.py --generated <feed>_IIG.xlsx --real "IIG test cells.xlsx" --real-table <table> [--all-sheets]` is the older per-row scorecard (pair 1 / SD rows). → §[H3], §[H4]
- Tests by area (all current; the moved text describes each): provider / transport `test_provider_mode.py`, `test_transport.py`, `test_layer2_failures.py`, `test_layout_json_response.py`; iig_diff `test_iig_diff_identity.py`, `test_iig_diff_sheet_alias.py`, `test_iig_fill_rate.py`, `test_iig_scorecard.py`; IIG cells `test_iig_v2_derivations.py`, `test_iig_cheap_misses.py`, `test_derivations.py`, `test_pair4_full_golden.py`; answer lines `test_answer_labels.py`, `test_layout_gap_labels.py`, `test_cold_pairs.py`, `test_pyx_questions.py`, `test_multi_sheet_feed_ids.py`, `test_format_from_extension.py`, `test_audit_annotation.py`, `test_mapping_general_first.py`; pairing `test_pairing_name_key.py`; launch / deploy `test_app_imports_tree_src.py`, `test_cli_launch_tree_src.py`, `test_ruff_dependency.py`, `test_health_probe.py`, `test_deploy_without_out.py`, `test_run_round.py`. → §[H2], §[H3], §[H4]

### Working rules (older branch notes moved to `docs/CLAUDE_HISTORY.md` §[H3] 2026-10-09 / §[H4] 2026-10-07)

- Branches: `feature/multi-table` = this checkout (all current work); `feature/iig-first` = the old demo branch `codegen-watch` pulled (post13) — never merge into it without Soham's word; `backup/ddl-only` = DDL-only fallback; `acfc/harness-exit3` = docs only (`docs/acfc/HARNESS_EXIT_CODES.md`, local a6b8002 NOT pushed — edit in a scratch worktree). → §[H3], §[H4]
- Others push to this branch from ACFC: `git fetch` and rebase before work, never force-push. → §[H3]
- Stage files explicitly, never `git add -A`; gitignored local-only files (never stage): `docs/acfc/denylist_local.txt`, `PROJECT_HANDOFF.md`, `CODEGEN_INDEPENDENT_REVIEW.md`. → §[H3]
- The real client SD documents + `IIG test cells.xlsx` at the repo root: read in place, mock runs only, outputs to a scratchpad, report SCORES only — never copy names into the repo, commits or replies. → §[H3]
- Exit codes 0 ok / 1 failed / 3 NEEDS_ANSWERS; answer lines `f"{label:<15}{key} — {reason}"` (`cli.answer_line`, key verbatim); QUESTION / UNRESOLVED only for answers owed, everything informational is NOTE; the harness regex is copied in `tests/test_harness_answer_lines.py`; details in `docs/ACFC_DEPLOY.md` "CLI exit codes". → §[H3] "Today's rules"
- An STTM band's layer comes only from evidence; source by elimination only for the one leftover band left of both evidenced target bands (owner rule 5cbaf63); anything else stays `UNRESOLVED <sheet>/band[<n>]/layer`. → §[H3] Chunk A
- `framework/metadata_inserts.sql` is the client's "DDL": one INSERT per IIG row, an open cell = unquoted `<<COLUMN#n>>`; rules via `dml.db_value_map` / `dml.db_null_columns`; `config_inserts_<env>.sql` is retired. → §[H3] "What the branch does"
- `config/overlays/acfc_env.yaml` is committed and ALWAYS applied first by `load_config`; `CODEGEN_CONFIG_OVERLAYS` adds on top (later wins); `CODEGEN_SKIP_ENV_OVERLAY=1` opts out and `tests/conftest.py` sets it, so a test that wants the overlay passes `overlays=[…]` and a fixture overlay carries every value its golden needs. → §[H4], §[H3] gotchas
- `acfc_env.yaml` pins the SD / CAQH family for EVERY feed; a PRX-shaped feed needs a feed overlay on top (splitting it per source family is still open). → §[H3] item 5, §[H4]
- Src-first: `src/codegen/_srcpath.py` (`ensure_src_first`, `child_env`) — every child launch passes `env=child_env()`; `codegen-watch` (not in this repo) must put `PYTHONPATH=<repo>/src` first itself. → §[H4] ca6bab8
- ruff is a base dependency; a missing ruff module = flag `ruff_unavailable`, PASS_WITH_FLAGS, never FAIL. → §[H4] 2c3c6d4
- Real reference files are TRACKED on origin (`IIG test cells.xlsx`, `d1_d1k.stg_doh/`, `d1_std.sdoh/`, `sd_community_demographic_risk.lvdash.json`); untrack / purge is Soham's call after the demo — `git rm --cached` would delete them from the ACFC checkout; never print CREATED_BY / UPDATED_BY. → §[H4] "Open / scheduled"
- Storage health: `ui/backend/health.py` probes every root (`GET /api/health`: principal, roots); App env + grants in `docs/ACFC_APP_ENV.md`. → §[H4] 9da340a
- Gotcha: bash heredocs mangle escapes and backticks — write patch scripts with the Write tool and run them as files; write commit messages to a file and `git commit -F`. → §[H3], §[H4]
- Gotcha: `fixtures/** -text` commits raw bytes — patch fixtures with `read_bytes` / `write_bytes`, keep each file's EOL, check `git diff --cached --stat` for whole-file churn. → §[H3]
- Gotcha: the CLI loads the local `.env` (its DL leaks the client domain into EMAIL_TO) — `export CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` before a shareable run. → §[H3]
- Gotcha: `isolation: "worktree"` agents branch from the default branch — reset each to the working branch first, cherry-pick back, delete the `worktree-agent-*` branch. → §[H3]
- Gotcha: `;`-separated path lists get MSYS-converted — `export MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS` (or `PYTHONPATH`); the spiral-detector hook keys on the exact command string, so re-run the quoted command before trusting a "failing" signal. → §[H4] "Session gotchas"
- The local `.venv` has no lxml: install it to a scratch `--target` dir on `PYTHONPATH` to reproduce lxml-only bugs (the 2026-10-07 unreadable-xlsx bug was one). → §[H4] be4c6e4

### History moved out (2026-10-14)

`docs/CLAUDE_HISTORY.md` holds, VERBATIM: (first pass) the legacy demo branch
`fix/remove-mock-provider-ui-text` (M15–M15e), M9 + v0.5.1–v0.5.8-acfc, M8 and M7;
(second pass, tagged) §[H2] restart points post36–post46, §[H3] the 2026-10-09 START HERE,
§[H4] the `feature/iig-first` notes (2026-10-07), §[H5] FRD pairing, §[H6] the Databricks
volumes seam, §[H7] demo panels, §[H8] fixtures & data rules. Each rule still in force has a
one-line copy above or below with its § pointer. From the first pass:
- Nothing may assume a run lives under REPO_ROOT (`relative_to` on a role-store path
  needs a fallback); Can Manage (not Can Edit) on the state / outputs / inputs folders.
- `tests/test_remote_run_e2e.py` is the only run test on remote roles — extend it when
  touching the run path; a pairing / record step is best-effort (never discards a choice).
- A Length cell is a byte width only when it is an INTEGER; never derive a width from a
  precision. An empty schema never reaches a contract (STTM band -> FRD -> default -> stop).
- `ui_stores.get_stores` caches per config object; test fixtures assign `store.config`
  plainly; `_Workspace.release()` drains every runner thread.
- A rebuilt `ui/frontend/dist` must ship with any `ui/frontend/src` change (pre-push).

## §[H10] RESTART.md State blocks, post94–103 (moved verbatim 2026-10-26)

- **post98–103 verified on the App** on the pair_11 live run `demo_20261023_132913`
  (artefacts via `/api/combined/…` + a Playwright pass):
  - the combined set is `Pyx_Care_Management_Data_MI_DSNP_*` (no `STTM_`);
  - OBJECT_ID 1..5 across the run;
  - 12 pipeline rows = 1 grand master + 1 master (both Daily, `_DLY`) + 2 × 5 children;
  - the `_LOG.md` merged / kept lists; the short IDs line; IIG_REVIEW hidden;
  - Run summary + Feeds collapsed; View results hides the sidebar for the page only.
  - That run made NO model call: layout from the documents, `--layer2 defer`, 35 rules
    pending review.
  - PARENT_PIPELINE_ID is blank on the master + children (the framework assigns IDs),
    so the parent links show only in the review copy.
- **Live App results (post94–97):**
  - pair_03: PASS_WITH_OPEN_INPUTS with no answers.
  - pair_11: PASS_WITH_OPEN_INPUTS (answer the VDD question "none"); 67 combined rows,
    per-table reject paths.
  - pair_08: the live layout resolves the STTM; 7 blank stage types carry a proposal; then
    FAIL on the multi-table mismatch (the FRD names 4 stage tables in one cell).
  - pair_10: stops before generating on the delimiter of all 4 feeds and the load
    strategy / LOBs of feeds 1–3 (the BSA answered feed 0 only).


## §[H11] RESTART.md State blocks, post105–107 (moved verbatim 2026-10-27)

### State (2026-10-26, post107 pushed; App still on post105)

- **post106** (PK note joined with " — ", not "; ") and **post107** (notebook v2 never
  `partitionBy` — clustered tables; gate check `ddl_parses`, sqlglot now a base
  dependency; the pair-1 overlay turns that gate off: its golden is unterminated) are
  pushed at `05a9f12`; suites `.venv` 2116 / `.venv-d1` 1809. NOT deployed — waiting on
  Soham's go.
- **DDL review page for Nikshit:** `/tmp/ddl_review/ddl-review.html` (synthetic examples
  only); not published — the Artifact tool needs a claude.ai login (this session runs
  on `ANTHROPIC_AUTH_TOKEN`). Its questions: framework `TGT_PARTITION_COLUMN` handling,
  stage STRING vs typed, the protocol / 13 standard properties, PHI tag key + PK RELY,
  stage written by name or ADLS path.
- **Codeflow audit (2026-10-26, in progress):** Phase-1 tool facts in /tmp/trace (static
  graph, coverage with test contexts: 91 functions never run, 153 CLI-only / 112
  App-only src functions; 62 tests skip, 33+ for fixtures removed 2026-08-22), then an
  adversarially verified multi-agent pass. /tmp is lost on a container reset.

#### Earlier today (post105)

- **Branch** `feature/multi-table`, pushed (`e216588` + this note). The `gh` login has
  the `workflow` scope since 2026-10-26; CI (`.github/workflows/tests.yml`) ran green on
  its first push (pytest full + d1, vitest + tsc, version guard).
- **App** `codegen-agent` deployed 2026-10-26 from `e216588`; `/api/health` reports
  `0.5.8.post105`. Browser smoke (Chromium in /tmp, `/` and `/modes`): no page errors, no
  failed API calls. The sidebar badge reads MOCK while the Dashboard holds no runs (it is
  `/api/feeds` `mode`, the served runs' mode, not the provider) — misleading after
  every deploy; not changed.
- **Suite on the post105 commit `bcb1bd1`:** `.venv` 2106 passed, `.venv-d1` 1799 passed
  (parallel, `-n 4 --dist loadgroup`); ruff clean in both.
- **Current work:** the run-safe DDL is live (post105); waiting on Soham's answers to
  the DDL questions below. Then IIG scoring vs prod goldens
  (pair_2 first, for Venu).
- **Today 2026-10-26:** the session with Rama (child pipelines: parallel vs sequential,
  children per feed) — the child-pipeline item waits for his answers.
- **Decided by Soham (2026-10-22), not built:** the four Databricks workspace / cluster
  columns of DATABRICKS_NOTEBOOK_DETAILS stay blank and out of the panel; TEMPLATE_ID
  out of the IDs line.

