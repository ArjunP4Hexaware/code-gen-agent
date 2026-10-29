# CHANGELOG — ACFC (`feature/multi-table`)

What each version marker changes for a run inside ACFC. Newest first. Values that
must not enter git (storage account, containers, notebook names, status sets) are
named by field only — see `docs/acfc/OVERLAY_FIELDS.md`.

## 0.5.8.post156 — 2026-10-29 (one STTM sheet, several tables: a feed per table)

Soham (2026-10-29), the pair_09 shape: the FRD's one block names N target tables and the
STTM maps all N on ONE sheet (its stage TableName column, a table per block of rows).
Read as one table, the other N-1 met nothing (ContractMismatchError "N-1 tables only in
FRD"). Now:
- **Layout stage** (`layout.resolve._split_per_table`, tried before the per-sheet split):
  when one non-segmented sheet's tables are EXACTLY the FRD's, each table is its own FRD
  feed, named after its table. Every pairing from the documents, never a guess: the
  standard table = the one its rows name (else none + `table_split_standard_unpaired`);
  the file pattern = the FRD pattern that IS the table / its source table by file
  identity (else none + a flag). The token-overlap pairing of the per-sheet split
  (audit #4) is not used on this path. A segmented sheet (a table per record type) and
  a table set that differs from the FRD's keep the old behaviour.
- **Extraction** (`extract.generic._split_by_table`): such a sheet is read as one sheet
  per table; a row with a blank table cell belongs to the block above, an audit row to
  the block it sits in.
- **Table sources** (with post155): the resolver no longer demands a delimiter
  (`delimiter_not_applicable:table_source`) or a file pattern (the feed's object is the
  STTM's source table, `file_pattern_from_source_table`); the DDL test cases speak of
  loads from the source table and drop the file-only cases (location, delimiter /
  position, column shift, several files).
- Tests: `tests/test_one_sheet_tables_split.py` (the chain on a synthetic pair_09-shaped
  pair + the split's rules), `tests/test_table_source_hold.py` (the wording).
- Deliberately NOT here: extract-sttm splitting an unsplit one-feed contract. Tried: at
  extract time pair_09's contract carries its 36 tables (gap-filled from the STTM), so it
  split there and generate stopped at a TemplateGapError (a value only the answers file
  can supply, contract segment 1 field 1) = CRASHED, worse than the FAIL; reverted.
- **Not yet the real pair_09.** Its FRD states no table, no file pattern and no format: the
  36 tables come from the STTM, the 36 file patterns from the VDD FILES sheet (gap fill
  gives a multi-feed FRD the WHOLE list per feed), the format from the pair's answers. The
  split needs the FRD to name the tables, so pair_09 still stops at "35 tables only in
  FRD" (12-pair check: no pair changed). Finishing it - split when the FRD names no table
  (the STTM band is authoritative), and give each table source its own object, not the
  VDD's whole list - waits for the RDMS sheet (Soham, 2026-10-29, option B).

## 0.5.8.post155 — 2026-10-29 (a table-sourced feed holds its IIG)

Soham (2026-10-29): two client pairs state their source as a database table ("Database
Table"), and the agent only writes FILE-ingestion IIG rows — table ingestion (the RDMS
sheet) is not built. File rows for a table source would be values no document gives.
Such a feed now:
- writes its DDL and DDL test cases (the target tables do not depend on the source) and
  runs their checks;
- writes NO IIG, review copy, config rows or metadata inserts; ADDITION.md says HELD BACK
  and why (the FRD's file format, as stated); flag `iig_held:table_ingestion`;
- asks none of the IIG's inputs (containers, landing, LOB, key) — one NOTE line and one
  non-blocking open item instead, so the run reads PASS_WITH_OPEN_INPUTS (exit 0), never
  a clean PASS; the combined set carries no IIG for it.
- Vocabulary: `framework.table_source_formats: ["database table"]` (cited).
- Tests: `tests/test_table_source_hold.py` (4; fail with only the source reverted).
- Prepares the pair_09 per-table split (next): its 36 tables are database tables.

## 0.5.8.post154 — 2026-10-29 (DDL test cases: the client's pipeline-level cases, and its workbook)

Soham (2026-10-29), from the client's own DDL test workbook (Aruna): its cases test
the whole pipeline (a second file, several files, emails, overwrite vs append), ours
the DDL. Four cases added, every value from the documents, and the cases as a workbook:
- **Load strategy on a second file**, one per table: the FRD's strategy says what a
  second load does (Truncate and Load = only the second file's rows; Append = both
  files'; Upsert = keys updated, never duplicated) — a self-checking COUNT with its own
  `expected_rows_tcNN` parameter. No strategy stated = OPEN + flag; an unknown one = a
  `ddl_tests_load_strategy_unread` flag, no check.
- **A second sample file** and **Several files at once** (written steps; the latter names
  the processed-files table).
- **Email notification**, one per EMAIL_TEMPLATE_CONFIG status THIS run's IIG writes
  (`ddl_test_email_triggers` says what sends each; an IIG without the sheet = no case).
- **`<ABBREV>_DDL_TestCases.xlsx`**: the cases in the client's test-record layout — its
  headers transcribed (`ddl_test_workbook_headers`), then "SQL to run"; the tester fills
  Actual Results / Executed By / Executed Date / Output(Pass/Fail). Byte-stable; the
  combined set gets `<STTM>_DDL_TestCases.xlsx` with one sheet per feed, and the App lists
  it with the other combined files.
- The cases are renumbered (new ones sit after the record counts / before the key case).
- On D1 (synthetic pair 4): 67 cases — 30 PASS, 6 NO DATA, 9 count checks pass with 0
  rows, 0 FAIL, no error.
- Not yet: the audit-log case (needs the Databricks clone's table name of the
  framework's audit DB; it goes in the environment state file, never the repo).
- Tests: `tests/test_ddl_test_cases.py` (7 new; fail with only the source reverted).

## 0.5.8.post153 — 2026-10-29 (DDL test cases: the column check counts as Databricks does)

Found by running the generated DDLs on D1 (Soham, 2026-10-29: test schema
`d1_dlk.soham_test`, scratch copies retargeted; the DDLs created every table and re-ran
cleanly). Every "Columns and types match the DDL" case FAILED: Databricks numbers
`information_schema.columns.ordinal_position` from 0, the expected list counts the DDL's
columns from 1, so each column was off by one though names and types matched.
- The deployed side now reads `ordinal_position + 1` (new knob
  `conventions.profiles.acfc_prx.ddl_test_ordinal_base: 0`, cited; None = read as it is),
  so a FAIL lists positions the way the DDL counts them.
- On D1 (synthetic pair 4, Serverless Starter warehouse): 30 PASS, 6 NO DATA (empty
  tables), 0 FAIL — was 12 FAIL before this fix and the runner's own tag-filter fix.
- Changes only the `_DDL_TestCases.txt` files (12-pair check: see the session log).
- Tests: `tests/test_ddl_test_cases.py::test_the_column_check_counts_columns_as_the_ddl_does`
  (fails with only the generator reverted).

## 0.5.8.post152 — 2026-10-29 (Generate: the run shows up where you pressed Generate)

Soham (2026-10-29): after pressing Generate (at the foot of the page) the progress
bar and the questions appeared at the TOP, out of sight — a run paused for "Continue"
(e.g. to go on without a VDD) looked like a run still working. The run card now sits
directly under the Generate button, and the page brings it into view when the run
starts, pauses for answers or ends (a change of state, never a poll tick; a page
opened on a finished run stays where it is, one opened mid-run scrolls to it).
- Tests: `GuidedGenerate.test.tsx` (the card after the Generate button; scrolled to
  when paused; not when opened on a finished run) — fail with only the page reverted.

## 0.5.8.post151 — 2026-10-29 (the run button reads "Generate Documents" again)

The post143 redesign shortened the run button to "Generate"; it had been renamed to
"Generate Documents" at a stakeholder's request (an action item marked done). The label
is back; nothing else changes. Tests: the confirm-dialog and guided-page tests find the
button by that label.

## 0.5.8.post150 — 2026-10-29 (generated files name no person)

Found while making the App's text client-safe (post149): one config VALUE, the
corpus-share note behind the delimited feeds' notebook name (`acfc_env.yaml`,
`DATABRICKS_NOTEBOOK_NAME` shares), ended "…which version is current: flag for
<person>)". That note is copied into the gate flags and the IIG cell notes, so it
reached every generated set with a non-EDI delimited feed. It now ends "…which
version is current is to be confirmed)"; the values and the choice are unchanged.
- Guard: `tests/test_config_names_no_person.py` — no value in config.yaml or an
  overlay may name a person (who decided stays in YAML comments); fails with only the
  overlay line reverted.
- 12-pair check (mock, framework mode, post149 vs post150): see the session log.

## 0.5.8.post149 — 2026-10-29 (client-facing App text names no person)

Soham (2026-10-29): the App is client-facing. Two texts it shows from config named a
person, and now don't:
- The confirm dialog's new-pair note read "estimated ≈ 6–8 DBU (a conservative
  approximation (<name>, …), above the offline estimate …)". It now reads "estimated
  ≈ 6–8 DBU (rounded up on purpose)". Who decided it, and the offline figure, stay in
  the config comment, which the App never shows.
- The environment's "Where these values come from" note for the storage account no
  longer names who gave the D1 value.
- Tests: `tests/test_new_pair_cost.py` checks that every config text the App shows (the
  DBU sources, the environment provenance) names no person; it fails with only the
  config reverted.

## 0.5.8.post148 — 2026-10-29 (the feed page in the Results layout; the new-pair estimate 6–8 DBU)

Soham (2026-10-29):
- The feed page's Overview takes the Results layout: four count tiles (gate checks
  passed — red when one fails, flags to check, target tables, validation rules); a
  failed gate check is a red issue card, the passed ones fold under "N passed"; each
  flag is an issue card inside its section (orange bar; red with its tag when it waits
  for an engineer), its text still whole; Source contracts / Target tables / Load
  semantics in cards.
- The confirm dialog's new-pair layout estimate is 6–8 DBU (was 1.5–4.5): Venu said to
  approximate, conservatively, so the client is never surprised. The config cites it
  and keeps the offline figure it sits above. A measured first run still replaces it.
- Tests: `FeedOverview.test.tsx`; `tests/test_new_pair_cost.py` pins the shipped 6–8.

## 0.5.8.post147 — 2026-10-29 (Generate: the environment line in Advanced)

Soham (2026-10-29): the environment line (selector, profile path, values) moves from
the Settings card into its folded "Advanced" section. The fold's summary names the
environment in use ("environment D1 · conventions, templates, layout cache"); when a
required environment value is missing the fold starts open and its summary says how
many, so folding never hides a problem.
- Tests: `GuidedGenerate.test.tsx` (inside Advanced and named on its summary; open
  when a required value is missing).

## 0.5.8.post146 — 2026-10-29 (Generate: a progress bar while the run works)

Soham (2026-10-29): a minute of waiting needs feedback. The run card shows a blue bar
that fills, the % beside it, and what the agent is doing under it in plain words
("Reading the STTM workbook", "Writing the DDL and IIG for <feed> (feed 1 of 2)").
- Honest about what the backend reports (`ui/frontend/src/runProgress.ts`): each known
  step sets a floor; a feed's own steps split the generation band by "feed n of N"
  (new: those steps carry `feed: {n, of}`); inside a step the bar creeps toward the next
  floor, paced by how long completed runs took (`live_history.wall_seconds`). It never
  goes backwards, holds at "Waiting for your answers" while paused, and shows 100 %
  only when the run is done.
- Tests: `runProgress.test.ts`, `ProgressBar.test.tsx`, `tests/test_run_progress_stages.py`.

## 0.5.8.post145 — 2026-10-29 (the confirm dialog: a new pair's first-run cost in DBUs)

Soham (2026-10-29): the dialog read "0 calls · ≈ $0.00", because every recorded run
was on a pair whose layout was already mapped. A pair the agent has not seen
before makes the layout calls on its first run, and the dialog now says so, in DBUs.
- The measured headline is labelled "Pairs the agent has mapped before:". A note
  follows: one layout call per document (STTM, FRD, the VDD if chosen) on a new pair's
  first run, the cost in DBUs, and that later runs of that pair make no call.
- The DBUs are MEASURED once a recorded run made layout calls: its `layout` stage's
  tokens x `reasoning.dbu_rates` (new: Claude Opus 5.5 = 57.143 / 285.714 DBU per 1M
  input / output tokens; it reproduces the measured 3.15 DBU of post123's Layer-2 run).
  Until then the dialog states `demo.new_pair_layout_estimate` (new: 1.5–4.5 DBU, the
  2026-10-27 offline estimate from two client pairs' layout requests, output tokens not
  measured) and calls it an estimate. Neither configured = "no DBU figure is configured".
- The run record now keeps each stage's name (older entries have none and never count).
- Tests: `tests/test_new_pair_cost.py`, `liveEstimate.test.ts` (the new-pair line),
  `LiveRunConfirm.test.tsx` (the note in the dialog).

## 0.5.8.post144 — 2026-10-29 (the App opens on Generate; the client's logo top-left)

Soham (2026-10-29), two changes to post143's App:
- The App opens on "Generate a pipeline" (`/`). Results moved to `/results`; the old
  Generate address `/modes` redirects to `/`, so a saved link still works.
- The client's logo sits top-left in the header. It never enters the repo (CLAUDE.md):
  the App reads `<state root>/branding/logo.<png|svg|jpg|webp>` (the state mirror copies
  it with the rest of the state folder), `GET /api/branding` says whether there is one,
  `GET /api/branding/logo` serves it. Without a file the header is the wordmark alone
  and no image request fails.
- Tests: `tests/test_branding_route.py` (none / served with its type / only a file named
  logo), `App.test.tsx` (each address, the logo only when the state root has one).

## 0.5.8.post143 — 2026-10-29 (the App: the guided look of the STTM agent's App)

Soham (2026-10-29): the App rebuilt in the style of the STTM agent's App, every
capability kept. Frontend only; no backend route, generated file or verdict changes.
- The look: a white header with the wordmark (no logo) and the provider badge, a light
  sidebar with icons, white rounded cards with a soft shadow, brand-blue page titles.
  The tokens stay ACFC's and stay in `styles.css` `:root`; corners are rounded now
  (they were square, post135).
- Generate is a guided page: a step strip (Choose documents → Check the settings →
  Answer questions → Get the results), a Documents card with a drop zone (an .xlsx
  uploads as the STTM, a .docx / .json as the FRD, anything else refused before an
  upload), rows for STTM / FRD / VDD, a Settings card with Advanced folded, the run
  card on top once a run exists, one action bar ("Generate"), and the requirement /
  governance checks under "Details for the team". The confirm button says "run live"
  only when a model can be called.
- The Dashboard is "Results": four count tiles, the files as rows with a Download
  button each (named for its file), Notebooks, Layer-2 review, the feeds; rules
  compiled, the doctrine sentence, Reset decisions and Generate all feeds under
  "Details for the team". The feed page gains "← Results".
- Below 760px the sidebar is a drawer over the page, hidden on a first visit.
- Tests: `GuidedGenerate.test.tsx` (step strip, drop-zone routing, the mock wording),
  a narrow-screen sidebar test; Dashboard / confirm tests follow the new layout and
  copy. The UX skill gains Part 1 "Design pillars"; CLAUDE.md's Look rule says rounded.

## 0.5.8.post142 — 2026-10-29 (notebook v2: stage columns land as the STTM types them)

Soham (2026-10-29): stage columns keep the types the STTM states, and the DDL
is the reference. Notebook v2 read the file as strings and wrote the stage
table unchanged, so every stage column landed as STRING. Once the DDL had
created the typed stage table, the notebook's append failed.
- `stage_frame` now casts each column to the ADLS row's TGT_DATA_TYPE, the
  STTM's stage types (the same ones the DDL writes), right before the write.
  The stage DQ rules (e.g. a stated date conversion) still run first.
- A non-blank value the type cannot read would load as NULL. Instead the load
  stops and names each column, its type and the row count. Blank cells (a
  space-padded fixed-width field) are NULL as before. `char` / `varchar(n)`
  cast as string, because the table's own column type holds the length.
- A header / trailer segment that loads into its OWN stage table has no type
  cell in its fixed-width IIG row. It still lands as read (STRING), never with
  a guessed type, and raises `notebook_segment_types_unstated:<table>`.
- Framework mode (what ACFC deploys) is unchanged.
- Tests: `tests/test_notebook_stage_types.py`. On synthetic pair 4, the
  notebook's stage types equal the DDL's, table by table. The guard runs
  against a row-by-row stand-in (no Spark here). Fails with only the fix
  reverted.

## 0.5.8.post141 — 2026-10-28 (Choose documents: a Cancel button)

Aruna (via Soham): the Choose documents dialog closed only with Done, so a
pair picked by mistake could not be backed out of. Picking a document applies
at once (download, classify, pair), so closing the dialog was never an undo.
- When the dialog opens, the backend remembers the selection
  (`POST /api/demo/choosing`).
- **Cancel** restores it exactly (`POST /api/demo/choosing/cancel`): STTM, FRD,
  VDD, the automatic pairing and the selection job. There is no re-download
  and no re-pairing. A pick still downloading is superseded and changes
  nothing.
- **Done** keeps the new selection (`POST /api/demo/choosing/done`). It is
  disabled until an STTM is chosen and while a pick is still selecting.
- Both buttons are pinned to the bottom of the dialog, so they stay in view
  without scrolling.
- The UX skill's chooser spec follows.
- Tests: `tests/test_m93_chooser.py` (cancel after a pick, cancel from "none
  chosen", cancel during a running pick). The first two fail when Cancel only
  closes the dialog. Browser click-through on a local synthetic App (pick +
  Done, pick + Cancel, pick + Done): no console errors.

## 0.5.8.post140 — 2026-10-28 (the DDL table COMMENT: the Table Description + the load strategy)

Soham (2026-10-28), answering the open DDL question 2 from 2026-10-23: the
table COMMENT is "description + load strategy". Until now it was the load
strategy alone. The STTM's Table Description column was recognised by the
layout (`table_description` role) but read by no reader.
- The content-driven reader keeps each target table's Table Description
  (`SttmFeed.table_descriptions`, keyed `<layer>.<table>`). It is usually stated
  once per table. The resolver carries it to the spec.
- The `acfc_prx` table COMMENT opens with it, then the load-strategy text,
  joined by the column separator (" — "). Example: `COMMENT '<description> —
  Load strategy: Append (FRD Load Strategy STG)'`. New knob
  `table_description_comment` (on in config.yaml, off in the pair-1 overlay,
  so that golden stays byte-identical).
- If a table's rows state two different descriptions, none is used (never a
  silent pick) and the `table_description_differs` flag is raised.
- If no description is stated, the COMMENT is the load strategy alone, with one
  `ddl_table_comment_no_description` flag per feed.
- The DDL test cases' comments check follows automatically (it reads the
  COMMENT the DDL writes). The feed page files the new flag under "From the
  documents".
- Contracts with no Table Description are byte-identical (the map is left out
  of the JSON when empty).
- Test: `tests/test_table_comment.py`. All three tests fail with only the fix
  reverted.

## 0.5.8.post139 — 2026-10-28 (a Comments cell repeating the Field Description no longer drops the column COMMENT)

The DDL's column COMMENT is the target band's Field Description (post104). The
content-driven STTM reader (`extract/generic.py`) kept that Field Description
only when it differed from the field's `description`. With no source
Description column, `description` is the source Comments cell, which is rule
text and never a COMMENT. So on a row whose Comments cell repeats the Field
Description word for word, the Field Description was dropped as a "duplicate".
The DDL then wrote no COMMENT at all for a description the STTM states twice.
- On D1 pair_11 that hit 61 of 62 fields: most column lines had no COMMENT, or
  only the primary-key note.
- Now the Field Description is kept unless `description` is that same text
  read from a real description column. Every column whose band states a Field
  Description carries it as a COMMENT on its own line, on both layers.
- The segmented (H/D/T) reader already kept it; only the content-driven reader
  changes. The pair-1 golden is unchanged.
- Test: `tests/test_ddl_comments.py::test_a_comments_cell_repeating_the_field_
  description_keeps_the_column_comment`. It fails with only the fix reverted.

## 0.5.8.post138 — 2026-10-28 (the LOB question is asked once and never blocks)

A feed whose files the FRD's LOB table keys to no single LOB (D1 pair_12) asks
ONE question, `feeds[<i>].lob_by_file`. It was a blocking QUESTION, so in the
App "proceed" without an answer ended the run as NEEDS_ANSWERS. The same
question was listed again as an answer the run still waited for, with no
View results, and the pair never got past it. The CLI exited 3.
- Now it is INPUT_NEEDED: asked once, before generating. Unanswered, those
  files' LOB cells stay open and flagged (`lob_unkeyed`; the IIG note reads
  INPUT_NEEDED). The run generates everything else and ends
  PASS_WITH_OPEN_INPUTS (exit 0). The answers template still lists the files,
  so the LOBs can be given on a later run.
- An answer, when given, keys each file as before.
- Only feeds with unkeyed LOB files change: their outcome, and the IIG note
  word. On the 12 ACFC pairs (mock) that is pair_12.
- Tests: `tests/test_lob_lookup.py`, `test_the_home_caqh_shape_asks_one_
  question_with_18_keys` (CLI) and `test_the_app_asks_the_lob_question_once_
  and_a_skipped_answer_never_blocks` (App). Both fail with only the fix
  reverted.

## 0.5.8.post137 — 2026-10-28 (the feed page's flags, in sections)

The feed page's "Flags — needs a human" panel was one list of every gate flag
(dozens per feed; 1,648 over the 12 ACFC pairs). It is now in collapsible
sections, grouped by each flag's leading code:
- Rules an engineer must decide (open): the unmapped rules (the gate's
  "pending engineer approval" flag, written with Layer 2 on or off) and the
  rules the gate marks for a human (`rule classified …`, `confirm item
  pending …`).
- From the documents (FRD / STTM / VDD) (open).
- IIG workbook cells · DDL and its test cases · Metadata inserts ·
  Environment · Generation and checks.
- Other: any code no rule names. Nothing is ever dropped.
- Then the two housekeeping families the page already folded away
  (`faq_unanswered`, `iig_blank`).
Each section shows its count and a one-line hint. "Expand all" / "Collapse
all" open or close every section. Flag text is shown exactly as before, and
the PENDING ENGINEER APPROVAL tag is kept. Frontend only: no flag, verdict or
API changed. On the 12 pairs (mock, counts only) every flag lands in a named
section. Tests: `ui/frontend/src/flagGroups.test.ts`,
`ui/frontend/src/components/FlagSections.test.tsx`.

## 0.5.8.post136 — 2026-10-28 (the App says which provider a run uses)

Four things the App said that were not true, or not plain, when presented:
- **The sidebar badge** showed the served result set's mode, so after every
  deploy (no run loaded) it read MOCK on an App that runs live. It now shows
  the provider a run started now would use: LIVE or MOCK (`/api/feeds`
  `provider`, from the same resolution the Generate card shows).
- **A run answered by the mock was labelled LIVE RUN** (banner, the
  Generate-all confirmation). The store now records which provider answered
  the served run (`run_provider`). Such a run reads "MOCK RUN — generated now
  with the mock provider; no model was called" (grey banner), and the
  confirmation says "Replace the current MOCK RUN results?". The Generate page's
  "Last live run …" lines read "Last run …".
- **The Generate card** said "Detected by provider=live (CODEGEN_PROVIDER)
  (Databricks App runtime)". It now says, e.g., "A run will use: Claude Opus
  5.5, through Databricks. A model is called only when the documents need it;
  those calls are billed." The detection detail sits one click away under
  "How this was chosen".
- **The Generate-all confirmation** pointed at the "Run modes page"; it is
  the Generate page.

A provider label that cannot resolve gives `provider: null` (the old badge),
never a failed `/api/feeds`.

Unchanged: the served `mode` (mock / live / replay) and everything keyed on it
(the confirmation's trigger, which folders files are read from, View results).
`provider` / `run_provider` are additions to `/api/feeds`; an older frontend
ignores them. Tests: `tests/test_provider_labels.py`,
`tests/test_remote_run_e2e.py` (the held-back run), `ui/frontend/src/runLabels.test.ts`.

## 0.5.8.post135 — 2026-10-28 (the App in ACFC's visual identity)

The App is presented inside ACFC, so it now uses ACFC's own design tokens: the
Brand, Text and Accents, and UI colour sets of the public style guide on ACFC's
web properties. Visual only: no screen, control, route, copy or API changed.
- Colours: primary blue for actions and links, navy headings, a navy sidebar
  with a light-blue bar on the current page, and ACFC's UI colours for the
  gate verdicts (confirmation green, warning yellow, error red). Every text /
  background pair meets WCAG AA (≥ 4.5:1).
- Type: Open Sans (ACFC's secondary typeface), bundled with the App
  (`@fontsource/open-sans` 5.2.7, latin 400 / 600 / 700), so the browser never
  fetches fonts at runtime. ACFC's primary typeface is a licensed web font: it
  is first in the stack and used only when the browser already has it.
- Shape: square corners, as on ACFC's sites. Secondary buttons are blue
  outlines; form fields and plain inline buttons, which had browser defaults
  on the Generate page, now match.
- Every hard-coded colour in the stylesheet is a token now (tints via
  `color-mix`), so a palette change is one block.
- Fixed while restyling: the mode badge is readable on the navy sidebar, and
  a card header wraps on a narrow window instead of running off the edge.
- No logo and no company name: client terms stay out of the repo.
- The UX skill's token tables and component specs follow (Part 4.1, 2.8).

## 0.5.8.post134 — 2026-10-28 (DDL test cases: every SELECT checks itself)

The post128 test-cases file printed the expected result as a comment, and the
engineer compared each query's output with it by eye. Now each SELECT returns one
row: `test_id`, `result`, `found`, `expected`.
- `result` is PASS, FAIL, or NO DATA (the table has no rows yet; load a test file
  first). NO DATA keeps an empty table from passing the required-columns and
  key checks without testing anything.
- Required columns: the number of rows with a required column empty (PASS = 0).
- Record count: the engineer enters the expected count as a parameter, one per
  case (`:expected_rows_tc16`), and the query compares it.
- Primary key: the number of duplicated keys (PASS = 0).
- Table exists, comments, tags: compared with what the DDL writes.
- Columns and types: the DDL's columns, in order, are compared with
  `information_schema.columns`; a FAIL lists every difference. Types are
  compared in the catalog's spelling (INTEGER = int, a bare DECIMAL =
  decimal(10,0)), from two new profile knobs, `ddl_test_type_names` and
  `ddl_test_type_defaults`.
- Schema and table names are compared in lower case, as Unity Catalog stores
  them. Before this, a DDL naming a table in upper case would not have been
  found by the structure queries.
- Unchanged: the load cases with no SQL (file present, location, column
  mapping, column shift, name or position), and the table properties SHOW,
  which is still checked by eye (a query cannot read table properties).
- The file stays read-only (gate `ddl_tests_read_only`). The DDL, the IIG and
  the pair-1 golden are unchanged.
- Test: `tests/test_ddl_test_cases.py` (five new tests).

## 0.5.8.post133 — 2026-10-27 (layout rejections carry coordinates, never model or cell text; audit medium #9)

When the layout validator rejects a claim, the reason goes to the state role's
rejection log (promised to hold no workbook cell and no model string), the run's
`REJECTED` lines, `layout_rejected:` flags, and the `--report-unresolved` file
("structural labels only"). Several reasons quoted text instead:
- a sheet name the model invented (it may echo header text it was shown);
- the label cell and the model's label, for STTM meta rows and FRD fields;
- a data cell's value, when the claimed header row was really a data row;
- the model's FRD section and inline label;
- the input values inside a cached profile's schema error.

Now:
- Each of those reasons gives coordinates and vocabulary only.
- A model FRD claim under a path it was not asked about (an invented key) is
  dropped and counted, never merged. This is the FRD side of the STTM's existing
  `_strip_unknown_roles`.
- Layouts and contracts are unchanged; only the wording of rejection messages
  changes, plus the dropped invented FRD claims.
- Test: `tests/test_rejection_text.py`.

## 0.5.8.post132 — 2026-10-27 (a rerun never leaves a stale combined set; audit #14)

The per-STTM combined set (`<out>/combined/<STTM>_{IIG.xlsx, IIG_REVIEW.xlsx,
DDL.txt, DDL_TestCases.txt, LOG.md}`) was written only for STTMs with a kept feed
and never cleared. A CLI or harness rerun into the same output folder whose feeds
now all failed the gate (or crashed) therefore kept the previous run's
deployable-looking IIG and DDL, while the run itself exited 1.
- A full run now first removes the combined files an earlier run wrote. Only the
  configured name patterns are removed; any other file in the folder is left alone.
- A `--feed` (partial) run still writes no combined set and clears nothing.
- The App was never affected (each App run has its own folder).
- Test: `tests/test_run_artefacts.py::test_a_rerun_that_keeps_no_feed_leaves_no_stale_combined_set`.

## 0.5.8.post131 — 2026-10-27 (edo_sfmc DDL: only the COMMENTs a document states; audit #13)

The two-file `edo_sfmc` DDL wrote a COMMENT on every column. A column with no
description got its own name title-cased (`LOB` → `'Lob'`, `SRC_FILE_NAME` →
`'Src File Name'`), and the text came from the STTM `description`, which may be a
Comments cell (rule text).
- The COMMENT is now the STTM description (`ddl_description`, never a Comments
  cell). Audit columns take theirs from their own STTM rows, as `acfc_prx` does.
- A column no document describes gets no COMMENT, and one `ddl_comment_blank` flag
  per table.
- ACFC runs `acfc_prx`, which already followed this rule, so its output is
  unchanged. Only `edo_sfmc` runs change.
- Test: `tests/test_edo_sfmc_comments.py`.

## 0.5.8.post130 — 2026-10-27 (a corpus primary key is checked against the table's columns; audit #10)

On D1, where the prod IIG goldens are loaded as a corpus, a golden row's
`TGT_PRIMARY_KEY` was the last key signal and was taken exactly as written. A key
naming no column of the table became a profile default, written unasked into
every key cell of the ADLS / STGDELTA rows and `metadata_inserts.sql`, and the run
still exited 0 (probe: `NOT_A_COLUMN_X`).
- The corpus key now gets the same check as the FRD key statement and the FAQ:
  it is used only when **every** name is one of the table's columns, written as
  the layer names it (a source spelling becomes the stage / standard column).
- Otherwise there is no proposal, and the key is asked for as when no signal exists.
- Outside D1 (no corpus) nothing changes.
- Test: `tests/test_primary_key_corpus.py`.

## 0.5.8.post129 — 2026-10-27 (the layout model's spelling never reaches a contract; audit #6)

When the synonyms cannot place an FRD field, the layout model says where it is.
The validator checked only that the model's label matched the cell after
normalizing, then copied the model's spelling into the contract. A claim of
`FREQUENCY ::` for a cell reading `Frequency` put `FREQUENCY ::` into the
provenance, and with the model's `labelled_rule` flag the rule text became
`FREQUENCY ::: Daily`. A model `inline_label` reached the provenance the same way.
- A validated claim now carries the document's own label cell text.
- `labelled_rule` is derived as the synonym path derives it (a Data Quality rule
  row); the model's flag is ignored.
- An `inline_label` naming no `Label: value` pair in the value cell is rejected
  and goes back to the user as unresolved.
- Synonym-resolved layouts are unchanged. Only layouts the model placed (live
  runs, or a cached model layout) can change, and then to the document's wording.
- Test: `tests/test_layout_model_label.py`.

## 0.5.8.post128 — 2026-10-27 (DDL test cases: a separate `<DDL>_TestCases.txt`)

Nikshit's review (2026-10-23) asked for DDL test cases. Venu (2026-10-27) said
they go in a **separate framework file, never inside the DDL**, named like the
DDL with `_TestCases`.
- Per feed (acfc_prx): `<ABBREV>_DDL_TestCases.txt` next to `<ABBREV>_DDL.txt`.
  Per STTM: `combined/<STTM>_DDL_TestCases.txt`, every kept feed's cases in turn.
  The App lists it right after the DDL (`output.app_files: ddl_tests`), and the RFC
  package carries it with the DDL.
- **What it is:** read-only SQL plus `--` comments the engineer runs **after** the
  DDL, in a Databricks SQL editor. The agent writes it and never runs it. Each case
  has an ID (TC01…), what it checks, the negative variant, where its values come
  from, then its SQL and the expected result.
- **The cases, in order** (`conventions.profiles.acfc_prx.ddl_test_cases`):
  - Nikshit's six: file available; file in the right location; column mapping
    (source → stage → standard, per table); required columns populated; column
    shift; columns matched by name or by position (a question for the framework
    owners: Spark applies a schema by position unless the header is validated).
  - Then: record count; primary key unique; and the structure checks (table exists,
    columns and types, comments present, table properties, tags, the DDL is safe to
    re-run).
- Every value comes from the resolved feed or from the DDL the same run wrote. An
  unstated value (e.g. no landing location) is `OPEN` and raises
  `ddl_tests_open:<case>`.
- New gate check `ddl_tests_read_only` (sqlglot): every statement is a SELECT,
  DESCRIBE or SHOW. The DDL checks (`ddl_parses`, `sql_literals`) never read this
  file. The DDL and IIG are unchanged; the pair-1 golden stays byte-identical.
- Found by the 12-pair check before release: an STTM column name with a line break
  inside split a comment line, so the file stopped parsing and the gate failed that
  feed. Every comment line is now one line, whatever the documents contain.
- Test: `tests/test_ddl_test_cases.py`.

## 0.5.8.post127 — 2026-10-27 (segmented recycle window: the config default, never 15; audit #2)

When a segmented (H/D/T) pair's FRD recycle rule stated no day count, the
segmented reader wrote a recycle window of **15 days**, a number no document and
no config states. It went into the IIG's `RECYCL_RETN_DAYS`, and the reader used
its own copies of the match / no-match texts.
- The window now follows the flat and generic readers: a window the FRD states
  wins, otherwise `config.defaults.recycle_window_days` (7). The texts are
  `config.extractor.recycle_on_match` / `recycle_on_no_match`. The provenance
  note says when the window is the config default.
- A pair whose FRD states the window (e.g. "retained for 15 days") is unchanged.
- Test: `tests/test_segmented_extraction.py::test_a_recycle_rule_with_no_day_count_
  takes_the_config_default_not_15`; it fails with only the fix reverted.
- **Not changed, raised with Soham:** in all three readers a defaulted window still
  reaches `RECYCL_RETN_DAYS` with the tooltip "the recycle window the STTM states".

## 0.5.8.post126 — 2026-10-27 (a VDD / STTM delimiter disagreement is a conflict; audit #7)

When the FRD states no delimiter, the resolver fills it from the STTM and the VDD
only when they agree. A disagreement (STTM `|`, VDD FILES `,`) used to fall
through to the STTM's character with no flag and no error.
- It is now a `value.conflict` naming both cells (`the FRD states no delimiter
  and the other documents disagree: STTM … says '|'; VDD FILES row 3 says ','`).
  This matches the existing file-format rule. Documents that agree (`Pipe` = `|`)
  or a single statement still fill, flagged `frd_unstated:delimiter`.
- The answer the error asks for (`feeds[<n>].delimiter` under `gaps:`, or the
  layout dialog) settles it either way. A delimiter the user answered now wins over
  the STTM, flagged `delimiter_answered:<char> — the answer overrides the STTM,
  which states <value>`. Before, siding against the STTM raised "delimiter
  disagrees" again. The existing FRD-format-cell conflict had the same dead end;
  this fixes that too.
- Test: `tests/test_delimiter_vdd_conflict.py`; the conflict and the `,` answer
  fail with only the fix reverted.

## 0.5.8.post125 — 2026-10-27 (an unstated source stays blank, never the word "unstated"; audit #5)

When a .docx FRD has no Data Source / Vendor label, the reader stores the
placeholder `unstated`. That word went into the IIG SOURCE column (every row),
`config_rows.xlsx`, `config_inserts.xlsx`, `metadata_inserts.sql` and the v2
notebook's title table, badged as coming from the FRD. That broke the "never
invent a value" rule.
- The placeholder now has one definition (`codegen.contracts.frd.UNSTATED_SOURCE`)
  and one reader (`stated_source`: blank or the placeholder means None).
- iig_v2 SOURCE, and iig_v1 SOURCE / APPLICATION_NAME / SUPPLIER / vendor_name, are
  BLANK with badge `needs_template`, so the gate lists them under `iig_blank:` and
  the review copy routes them to the BSA as "no input states it". The v2 notebook
  title copies that blank. Naming tokens and the DDL table comment read it as unstated.
- A feed whose STTM or the user's answer supplies the source is unchanged.
- Test: `tests/test_unstated_source.py` (pair 4 with the placeholder, both output
  modes, every artefact searched); it fails with only the fix reverted.

## 0.5.8.post124 — 2026-10-27 (the run button reads "Generate Documents")

Nikshit's review (2026-10-23): the blue button on the Generate page, formerly
"Generate from this STTM…", now reads "Generate Documents". The click opens the
same confirm dialog as before. The App's `dist` is rebuilt, and the port kit, the
demo scripts and the UX skill use the new label. Nothing generated changes (no
`src/` change). The same push carries `tools/iig_diff.py` sorting its `--agent`
files itself, so a score no longer depends on the order the files are named in.

## 0.5.8.post123 — 2026-10-27 (Layer-2 review switched OFF for ACFC)

Soham, 2026-10-27: Layer 2 (the AI suggestions for FRD rules the compiler cannot map:
`candidates.json` and the App's review panel) is not used. It never changed the DDL,
IIG or log, and nothing consumes its suggestions in framework mode.
- `config/overlays/acfc_env.yaml` gains a labelled `reasoning:` block, `layer2_app:
  skip` and `layer2_cli: skip`, so neither the App nor an ACFC CLI / harness run
  prepares or asks Layer 2. The code and config.yaml are unchanged. One App test,
  which builds its config with the ACFC overlay, now pins `layer2_app: defer` itself,
  because it tests the defer path.
- **To turn it back on:** delete that block (config.yaml's defaults return: App `defer`,
  CLI `now`), then bump, push and redeploy.
- Checked offline (pair_11, mock harness): the same outcome as before, with 0
  `candidates.json` and 0 `layer2_pending.json` (4 candidates files before).
- Measured before switching off (pair_11 live, 2026-10-27): 4 calls, 5,757 input +
  9,860 output tokens = 3.15 DBU.

## 0.5.8.post122 — 2026-10-26 (gate check ddl_identifiers: the DDL identifier rule, enforced)

Found by the first live run with the post107 parse gate (pair_11 on the App, post121):
one feed failed `ddl_parses` with "Expecting ) at line 44, col 19". The cause is an STTM
Standard-band column name with a stray space ("Word _Word"), copied as stated, as the
agent copies every name. The DDL had carried that invalid column since the feed was
first generated, including the post105 DDL on the App. CLAUDE.md's rule ("a DDL column
identifier must match `^[A-Za-z_][A-Za-z0-9_]*$`") was never a gate check (codeflow
audit #43): only `scripts/run_round.py` called it. Its text scan also read a spaced
name as its first word and passed it (#44).
- New gate check `ddl_identifiers` (`gate/ddl_names.check_ddl_identifiers`), run on
  the table definitions the DDL is rendered from, stage and standard, audit columns
  included. A FAIL names the layer, the table, the column position and the name as
  stated, and says to correct the STTM's column name. Violations count as
  `ddl_identifier`. The agent never rewrites the name.
- `ddl_parses` still runs; the new check is the one that says what to fix.
- For that pair_11 feed: the run stays GATE_FAIL until the STTM's column name is
  corrected. That's the right outcome, because the DDL would fail when run.

## 0.5.8.post121 — 2026-10-26 (acfc_run.py honours the answers file's pairing:)

Codeflow audit, medium #19, verified by reading. `acfc_run.py` (the one-pair notebook
fallback) calls `codegen pair --answers …`, which applies the answers file's `pairing:`
choice. It then worked out the FRD / VDD pairing a second time from content and a
`pairing_overrides.yaml` only, ignoring that choice, while its own failure message
says "add `pairing:` to the answers file".
- The answers file's `pairing: {<STTM>: {frd, vdd}}` choice for this STTM now wins, as
  in `codegen pair`. A named file missing from the pair folder stops with its name.
  Content pairing is the fallback, as before.
- Not covered by a test: the notebook needs `dbutils` (the repo's CLI suite covers
  `codegen pair`'s handling). The file's 6 pre-existing ruff findings are unchanged.

## 0.5.8.post120 — 2026-10-26 (IIG: the unstated-recycle N is badged a convention)

Codeflow audit #30 (low), verified. Under a family whose convention writes `N` when no
document states a recycle (`family_conventions.recycle_unstated: N`, the pair-1
family), the RECYCL_ENBL_FLG cell was badged `from_frd`, as if the FRD said so. The
review copy, which surfaces non-document cells, therefore never showed it to the BSA.
It is now badged `synthetic` with the convention's citation, as the
`schema_drift_flag` convention already is. The cell value is unchanged.

## 0.5.8.post119 — 2026-10-26 (edo_sfmc: tag values escaped)

Codeflow audit #37 (low), verified. The two-file (`edo_sfmc`) DDL wrote the FRD's Domain
/ Sub-Domain into `ALTER TABLE … SET TAGS (…)` unescaped. A quote in either ("Member's
Care") ended the string literal. Since post107 the `ddl_parses` gate fails such a file
rather than letting it ship; now the values are escaped as every other literal is
(`\'`), as `acfc_prx`'s tags already were.

## 0.5.8.post118 — 2026-10-26 (.docx FRD: Load Strategy STD makes the feed two-layer)

Codeflow audit #1 (medium), verified. CLAUDE.md: "Layer scope comes from Load Strategy,
never from which schemas a Target Schema block names". The `.docx` FRD reader set a
feed's standard tables only when the Target Schema block named a standard schema
(`standard_tables = list(tables) if std_schema or std_catalog else []`). A feed whose
Load Strategy STD states a load, but whose Target Schema names only the stage schema,
was therefore read as stage-only.
- `extract/frd_docx.read_frd`: a stated standard load strategy now also gives the
  standard layer the stage table names (the existing convention of that line), with a
  `frd_standard_from_load_strategy:<feed>` flag citing the Load Strategy STD cell. A
  Target Schema that names a standard schema behaves as before.
- Regression check, all 12 real pairs (mock harness, old vs new code): the same
  outcomes. Three pairs' FRD contracts now carry the standard tables their Load Strategy
  STD implies (0 to 4). Every DDL and IIG file is byte-identical, because the resolver
  already filled those tables from the STTM. Only the contract hash in
  `metadata_inserts.sql`'s comment banner changes. For one more pair the rule fires
  where a later step already set the same table names, which adds a flag only.

## 0.5.8.post117 — 2026-10-26 (the recycle-column question can be answered)

Codeflow audit #3 (medium), verified. When a recycle rule's column is not a source
column of its sheet (the `Y (…)` flag sits on a row the extractor does not keep as a
field), contract validation asks `feeds[i].recycle.applies_to` (`recycle_unknown_column`,
NEEDS_ANSWERS). The answer was dropped twice: `generic.parse_cell_answers` kept only
`file_format` / `source_system` keys, and nothing applied it. The feed could only ask
again, on every rerun.
- `VALUE_KEY_RE` accepts `recycle.applies_to`. `generic._build_feed` uses the answer
  when the rule's column is no source column, with an `answered_value:` flag, as the
  other answered values do.
- Test: the question is asked, the answer is parsed and applied, and the flag is
  written. The old code drops the answer at the parse step.

## 0.5.8.post116 — 2026-10-26 (answers file: a quoted column index is an index)

Codeflow audit #21 (low), verified. The answers template writes `column: ""` with the
comment "header text | 1-based index | letter". An index typed between the quotes
(`column: "3"`) is text, and `layout/answers._column_among` accepted only an integer, a
header or a letter, so it refused the answer as "neither a header …, an index nor a
column letter".
- A digit string is now read as the 1-based index. A header literally named "3" still
  wins (headers are matched first). "0" and "" name no column, as before.

## 0.5.8.post115 — 2026-10-26 (an answered load strategy must name one)

Codeflow audit #17 (medium), verified by a probe. A `gaps:` answer for an unstated stage
load strategy went through `canonical_strategy(answer) or answer`. An answer naming no
strategy ("Bananas") was therefore written into the FRD contract as typed, with a
normal-looking `frd_unstated` fill flag. That is an invalid `LoadStrategy` literal: any
later re-validation crashes with a `ValidationError`, and anything that doesn't
re-validate carries the text into the artefacts.
- `resolve/resolver._answered_unstated` refuses it with an answers-file error
  (`answers.file`, coordinates `answers`) naming the key and listing the strategies
  (`Truncate and Load`, `Append`, `Upsert`). Any spelling `canonical_strategy` knows
  ("append", the aliases) still fills.

## 0.5.8.post114 — 2026-10-26 (pairing: a document name matches on word boundaries)

Codeflow audit #20 (medium), verified. `pairing._name_match` decides whether an FRD feed
name appears in an STTM's text when the agent pairs documents automatically. Its
whole-name branch was a raw substring test on the normalized texts, so "FEED_8" matched
"FEED_80_…" and "CM" matched "PCM_…", even though its docstring promises the opposite.
A false positive pairs the WRONG documents.
- The whole name now has to appear on word boundaries. The token rule (short tokens
  exactly, longer ones by stem) is unchanged.
- Regression check, all 12 real pairs (mock harness, old vs new code): identical pairing
  report and outcomes.

## 0.5.8.post113 — 2026-10-26 (delimiter agreement: compared as characters)

Codeflow audit #8 (high) and the medium #8, one root cause, verified. Agreement
between documents goes through `discover.normalize`, which turns a punctuation-only
value (`|`, `,`) into `''`. As a result:
- `gapfill.same_value('|', '|')` was False. Two documents stating the same delimiter
  "disagreed": the layout dialog asked a blocking choice between `|` and `|`, and the
  CLI resolver filled nothing (no `frd_unstated:delimiter` flag).
- The layout cross-check tested `'' in value`, so ANY two punctuation delimiters
  "agreed". A `,` vs `|` conflict between the FRD and the STTM / VDD went unseen.

The fix:
- `same_value(a, b, words)` / `distinct(statements, words)`: when either side is
  punctuation-only, compare as written, or, with `extractor.delimiter_words`, as the
  delimiter CHARACTER each side states (`|` = `Pipe` = `Pipe delimited (|)`, never `,`).
  Text values compare as before.
- Passed `words` in the resolver's `others_for`, the layout dialog's statement loop,
  and the cross-check, which now uses `same_value` instead of its own copy of the
  comparison.
- Regression check, all 12 real pairs (mock harness, old vs new code): the same outcome
  per pair, identical SRC_FILE_DELIMITER cells in all 12 IIG workbooks, and the same
  flags. None of them hits the bug's shape in mock mode; `tests/test_same_value.py`
  carries it.

## 0.5.8.post112 — 2026-10-26 (edo_sfmc DDL run-safe; the gate fails CREATE OR REPLACE)

Codeflow audit #12 / #15, verified. Only `acfc_prx` had become run-safe (post105).
`edo_sfmc`'s two-file template hardcoded `CREATE OR REPLACE TABLE`, the code default of
`create_statement` was also the destructive form, and no check enforced the rule. The
App offers `edo_sfmc` as a selectable profile. An engineer re-running that profile's
DDL against deployed tables would empty them.
- `templates/framework/table_creation.txt.j2` takes the CREATE wording from the
  profile's `create_statement`, as the combined template does.
- `ConventionsProfileConfig.create_statement` now defaults to `CREATE TABLE IF NOT
  EXISTS`. Only the pair-1 fixture overlay pins `CREATE OR REPLACE TABLE`, for its
  golden. `acfc_prx` output is unchanged.
- Gate `ddl_parses` also FAILs any `CREATE OR REPLACE` statement (sqlglot's `replace`
  flag). The run-safe rule is now enforced, not only documented. The pair-1 overlay
  already runs with that check off.
- `edo_sfmc` output now deviates from its scrubbed SFMC reference files in this one
  clause, deliberately. Those reference files fail the run-safe check (recorded in
  `tests/test_ddl_parse_gate.py`). The current prod D1 set is `IF NOT EXISTS`.

## 0.5.8.post111 — 2026-10-26 (layout model: no cells of a sheet without a header row)

Codeflow audit #9, verified. The layout model is meant to see header regions only,
never a data row. A sheet with no row of 3+ filled cells within its first 25 rows (a
two-column lookup, valid-values or member list) has no header region, so its region is
"capped". The request then carried every non-empty cell of its first 25 rows, which can
be data, for every sheet of the workbook, on any live layout call.
- `layout/fingerprint.model_region`: the region the MODEL sees. A capped sheet sends its
  summary line only (name, size, merged ranges, `(capped, cells withheld)`); a bounded
  sheet is unchanged. `layout/resolve` builds the model request from it.
- The fingerprint, which is the layout-profile cache key, still hashes the full region,
  so no cached profile is invalidated.
- Trade-off: a role on a capped sheet is no longer placed by the model. Synonyms place
  it, or the run asks the user.
- `docs/LAYOUT_RECOGNITION.md` said both "a data row never enters" and "capped at 25
  rows". It now describes the capped case.
- Test: a canary in a lookup sheet's data row leaks to the recorded request on the old
  call path and not on the new one.
- Not changed, noted: `header_bound`'s band rule (a header of at most 5 labels over a
  WIDER next row takes the next row as the header) can still let one data row through,
  when a data row has more cells than its header. That's rare and needs a header-shape
  decision.

## 0.5.8.post110 — 2026-10-26 (generic reader: the recycle rule behind an N cell)

Codeflow audit #1, verified. The generic (content-path) reader built the recycle rule
from the FIRST non-empty Recycle Flag cell alone. An `N` on a row above the
`Y ( <validation> )` row therefore dropped the rule silently: no recycle step, RECYCL_*
cells `N`, no flag. A second flagged row was never read. One real pair has this shape:
462 `N` cells and one `Y (…)` rule (counts only).
- `extract/generic._recycle`: a cell reading an `extractor.discovery.no_values` word
  (N, No, …) is an unflagged row. Every other non-empty cell must be a `Y (…)` flag, as
  the classic reader requires. Several flagged rows with the same rule are one rule (the
  first row's column).
- Now loud instead of silent, as the classic reader already is: flagged rows with
  different rules (`sttm.conflict`), a cell that is neither a no-word nor a flag
  (`sttm.value`), and a flag with no validation text (`sttm.missing`). Each error names
  the sheet and row.
- Regression check on five real pairs (mock, container harness, old code vs new): the
  same outcome per pair and identical RECYCL_* cells in all 9 IIG workbooks. The pair
  with the bug's shape stops at NEEDS_ANSWERS in mock, so the unit tests carry that
  case (`tests/test_generic_recycle.py`: 5 of 6 fail on the old code).

## 0.5.8.post109 — 2026-10-26 (segmented: the File Type delimiter is the stated character)

Codeflow audit #3, verified by a probe. The segmented reader took the delimiter from
the metadata block's File Type as "the first non-space character after `delimited`".
"Pipe delimited (|)" therefore gave `(` and "Comma delimited file" gave `f`. That source
decides whenever the FRD states no delimiter, which is every pair with a `.docx` FRD,
because its reader never states one. The wrong character went to the contract, the
IIG's SRC_FILE_DELIMITER and the notebook's read options.
- `extract/segmented._metadata_delimiter` now reads the File Type text with
  `resolver.delimiter_char`, the reader every other stated delimiter goes through: a
  quoted character, else a delimiter word (`extractor.delimiter_words`). Text that
  doesn't mention a delimiter, or names none, gives None, and the format-implied
  delimiter applies as before.
- No test had run this function: the segmented fixture's FRD states `|` itself. New
  tests blank the FRD delimiter and vary the File Type text. Three of the four phrases
  failed on the old code.

## 0.5.8.post108 — 2026-10-26 (TGT_PRIMARY_KEY: a key only the Standard band marks)

Codeflow audit #11, verified by a probe. The feed's `primary_key` input was built from
the stage detail table's key signal only. If only the STTM's Standard band marked the
key (stage band unkeyed) and the standard leg was an Upsert, the run got no
INPUT_NEEDED line, no QUESTION, no answers-template entry and no manifest record. The
STGDELTA row's `TGT_PRIMARY_KEY` shipped blank with exit 0, and the framework cannot
merge without a key.
- `primary_key.feed_proposal` now falls back to the standard detail table's signal when
  the stage table has none. Under `primary_key_autoset` (on in acfc_env.yaml) the
  standard row is written unasked, with a NOTE. Without autoset the feed gets its
  INPUT_NEEDED line, and `use_default` writes it. Each row still writes its own table's
  key: the ADLS (stage) rows stay blank, because the stage table has no signal.
- Not changed, noted: `question()` asks only when NO merge leg has a signal. A stage key
  with the standard band explicitly `N` on an Upsert standard leg still gets no
  question. That shape is rare: the standard leg inherits the stage cells unless its own
  band says otherwise.

## 0.5.8.post107 — 2026-10-26 (notebook v2: no partitionBy on clustered tables; the DDL parse gate)

From the DDL / Databricks-capabilities review (2026-10-26):
- **notebook v2 never calls `partitionBy`.** The DDL creates every table `CLUSTER BY
  AUTO`, and Delta clustering is not compatible with partitioning, so a per-LOB file's
  `TGT_PARTITION_COLUMN` (LOB) write against a table created from the DDL would fail.
  `TGT_PARTITION_COLUMN` / `_VALUE` now only scope an Overwrite with `replaceWhere`
  (`<col> = '<value>'`, unchanged). An Append, or a value of `NA`, writes plainly. The
  IIG cells are unchanged. Open with Nikshit: what ACFC's own framework notebook does
  with `TGT_PARTITION_COLUMN`.
- **Gate check `ddl_parses`** (`codegen.gate.ddl_parse`, `gate.ddl_parse_dialect:
  databricks`): every emitted DDL file is parsed with sqlglot. A parse error or an
  unrecognised statement FAILs the feed, and the details name the file. sqlglot absent:
  a `sqlglot_unavailable` flag, never a FAIL. sqlglot moved from the `dev` extra to the
  base dependencies (as ruff did), so the App runs the check too. Checked: sqlglot 25 to
  30 all parse the run-safe shape.
- The pair-1 golden FAILS the parse: its two CREATEs carry no `;` and run together as
  one statement, so it is not runnable as a single script. Its fixture overlay sets
  `gate.ddl_parse_dialect: null`.
- Found on the way: 23 of the 25 notebook v2 tests skip in this checkout (the SFMC
  contracts they need were removed 2026-08-22). The new partition test renders from the
  PRX pair, which is present.

## 0.5.8.post106 — 2026-10-26 (DDL: the primary-key note joined with " — ")

Seen on the App's live pair_11 run (post105): the PK note was joined to the column
description with `"; "`, so two COMMENT literals held a `;`, and a deployment script
that splits the DDL on `;` would cut those statements in two. Soham: use `" — "`.
`conventions.profiles.acfc_prx.column_comment_separator` (and the model default) is now
`" — "`. The pair-1 golden is unaffected: its overlay turns the note off. A `;` inside an
STTM description itself is still written as stated.

## 0.5.8.post105 — 2026-10-26 (DDL: run-safe — IF NOT EXISTS, terminators, CLUSTER BY, stage TBLPROPERTIES, tags)

Soham, 2026-10-26: the engineer RUNS the agent's DDL, against tables that may already
be deployed. The `acfc_prx` combined DDL (`<ABBREV>_DDL.txt` and `combined/<STTM>_DDL.txt`)
gains five `conventions.profiles.acfc_prx` knobs, ON in config.yaml, transcribed from
ACFC's production template:
- **`create_statement: CREATE TABLE IF NOT EXISTS`** (was `CREATE OR REPLACE TABLE`:
  re-running that would empty a deployed table) and **`statement_terminator: ";"`**
  after every statement, CREATE and ALTER.
- **`cluster_by`**: `CLUSTER BY AUTO` on both layers, after the table COMMENT (the
  profile writes no LOCATION; prod's stage tables are the same).
- **`stage_tblproperties`**: the stage blocks' 4 properties (autoCompact, optimizeWrite,
  minReaderVersion 1, minWriterVersion 2), prod's order.
- **`domain_tags`**: `ALTER TABLE <table> SET TAGS ('DOMAIN' = …, 'SUBDOMAIN' = …);`
  after each CREATE, from the FRD's Domain / Sub-Domain (quotes `\'`-escaped). Either
  blank: no tag statement + one `ddl_tags_blank:<feed>` flag.
- The pair-1 fixture overlay switches all five off: `ACCUM_DDL.txt` stays the golden
  byte for byte. `edo_sfmc` is unchanged (its SFMC reference goldens are CREATE OR
  REPLACE).
- **Scored vs prod D1** (`tools/ddl_shape.py`, structure only, a scratch copy deleted
  after): pair 11's DDL is stage 11/12, standard 10/11 (post104: 6/12, 6/11). The one
  DIFF on each layer is column-comment coverage (the fixture's audit rows state no
  description). Prod's current set is itself `IF NOT EXISTS` and terminated.
- **`tools/ddl_shape.py`**: a file's leading `<env>_<dlk|stg|std>_` prefix decides
  its layer over layer words in the document title (`…_STTM_STG_STD_…`). Before
  this, 5 of the 6 D1 stage files were scored as standard.
- Still open (asked 2026-10-23): stage column types (all STRING like most prod files,
  or as the STTM states) and the table COMMENT's content; one file per layer vs the
  combined file.

## 0.5.8.post104 — 2026-10-23 (DDL: column COMMENTs, primary-key notes, the load strategy, standard TBLPROPERTIES)

Nikshit's review (2026-10-23), decided with Soham: the `acfc_prx` combined DDL
(`<ABBREV>_DDL.txt` and the run's `combined/<STTM>_DDL.txt`) gains four
`conventions.profiles.acfc_prx` knobs, ON in config.yaml:
- **`column_comments`**: `<col> <type> COMMENT '<text>'` = the STTM's Field Description
  (target band), else its source Description / Column Description / Data Definition.
  Never a Comments cell (rule text). A column with none gets no COMMENT; one
  `ddl_comment_blank:<layer>:<table>` flag per table names the columns, audit columns
  included (the contract keeps no description for audit rows).
- **`primary_key_note`** (`Primary key (STTM Primary Key)`): added to the COMMENT of a
  column the layer's STTM Primary Key cell marks (`primary_key` / `standard_primary_key`).
  A note only, not a constraint.
- **`load_strategy_comment`**: a table COMMENT after `USING delta`, `Load strategy:
  <FRD words> (FRD Load Strategy STG|STD)`, from the same resolved strategy the IIG's
  `TGT_LOAD_OPTION` reads.
- **`standard_tblproperties`**: the standard blocks' TBLPROPERTIES, the 13 properties of
  ACFC's own production SFMC standard DDL (`fixtures/reference/
  SFMC_standard_table_creation.txt`), in its order. Open with Nikshit: ACFC's standard,
  or a `SHOW CREATE TABLE` dump? Stage blocks carry none.
- STTM contract: `SttmField.field_description` and `description_from_comments` (written
  only when they say something, so existing contracts are byte-identical) and the
  `ddl_description` property; generic + segmented extractors fill them. `description`
  itself is unchanged.
- The pair-1 fixture overlay switches all four off: `ACCUM_DDL.txt` is still the golden
  byte for byte. `edo_sfmc` keeps its own COMMENT logic.
- **Checked against ACFC's prod DDLs** (`/Volumes/d1_dlk/stg_ddls/ddls/`, 5 STTMs, structure
  only): every standard file carries exactly these 13 properties, same values and order.
- **Audit columns are commented too** (prod comments them): `AuditColumn.description`,
  read by all three STTM readers (`generic.py`, `segmented.py`, the `MAPPING-` reader
  `workbook.py`) in the same order, never Comments, and never the audit marker (`NA`)
  that makes the row an audit row. Only audit columns still without one are flagged.
- **Quote escaping (both profiles):** a COMMENT's `'` is written `\'` (backslashes
  first), the Databricks SQL escape the prod DDLs use. `''` is no escape there: Databricks
  Runtime 18+ reads `'a''b'` as two chained literals, "ab". The `sql_literals` gate now
  reads backslash escapes and fails a doubled quote by name.

**Tests:** `test_ddl_comments.py` (12 new, incl. pair 1 with the knobs on = the golden
plus the additions only); the block parsers of `test_metadata_inserts.py` and
`test_ddl_standard_types.py` strip COMMENTs / skip the table-level lines;
`test_derivations.py` (the doubled-quote failure).

## 0.5.8.post103 — 2026-10-22 (App: the sidebar's auto-hide on View results is not remembered)

Soham: after post101 the sidebar was hidden even on a fresh visit. post88 remembers the
sidebar's state per browser, and post101's "View results" hide was saved like the
person's own toggle. Now only the sidebar's own button is remembered
(`useSidebarOpen` setter `(open, remember = true)`; App passes `remember = false` for View
results), and the key is `codegen.sidebar.open.v2`, so the "false" post101 saved is ignored.

**Tests:** `CollapsibleSidebar.test.tsx` (2 new).

## 0.5.8.post102 — 2026-10-22 (one Daily grand master + master per run, as the pair_11 golden has it)

Soham, against the pair_11 golden IIG (`DATA_FACTORY_PIPELINE_SCHEDULE`: one
`PL_GMSTR_…_DLY` + one `PL_MSTR_…_DLY`, both DAILY, then a stage and a standard child per
feed, each child on its feed's own schedule and parented to that one master). The agent
gave the masters each feed's frequency, so a run with weekly and monthly feeds had a
master pair per frequency (post99 merged identical copies, leaving one pair per frequency).
- **`pipeline_roles[].frequency`** (acfc_env.yaml: grand_master / master `Daily`): the
  role's `PIPELINE_FREQUENCY` cell (a cited template constant), its description's `{freq}`
  and its name's `{frequency}` / `{frequency_code}` (`input_choices.flow_tokens`, `tpl`
  passed by every caller; `metadata_template.role_frequency`). Children keep the feed's.
- With the masters equal across feeds, `combined.dedup_rows` writes them once and every
  child's "row n" parent reference points at the one master.
- **On pair_11** (mock container harness): 12 rows = 1 grand master + 1 master (Daily) +
  2 children × 5 feeds (Weekly / Monthly), every child parented to row 2 — the golden's
  shape (its 10 rows = 4 feeds). Child names stay the naming document's pattern (Nikshit:
  follow the document), so feeds' children still share a name; the log lists them.

**Tests:** `test_pipeline_name_choice.py::test_the_masters_names_carry_the_run_frequency_
the_children_their_feeds`, `test_iig_corpus_cells.py` (the schedule rows' frequencies).

## 0.5.8.post101 — 2026-10-22 (App: a shorter IDs line; the run summary and feed cards collapsed; the sidebar hides on View results)

Soham: the results page should lead with the Framework artefacts, and say only what the
data engineer acts on.
- **IDs to assign:** `output.app_assign_ids` (config.yaml: PIPELINE_ID, PARENT_PIPELINE_ID,
  GROUP_ID, each with a hint) replaces the panel's long "Framework-assigned IDs left blank:
  …" line with "Assign before loading: …", naming only the configured columns some feed
  leaves blank (`artefacts.idsToAssign`; `/api/feeds` `assign_ids`). Left out of the panel:
  OBJECT_ID (filled since post100), the load timestamps, the Databricks workspace / cluster
  settings, TEMPLATE_ID, and the columns of sheets with no rows. The combined `_LOG.md` and
  the review workbook still list / mark every blank column. An empty `app_assign_ids` brings
  the old line back.
- **Collapsed sections:** the stat tiles + the Layer-2 review panel are a "Run summary"
  `<details>`, the feed cards a "Feeds (n)" one, both closed at first, each summary line
  carrying the counts.
- **Sidebar:** "View results" hides it (`ModesPage` `onViewResults`; the show tab brings it
  back, and the choice is remembered as before).

**Tests:** `Dashboard.test.tsx` (3 new), `ModesPage.test.tsx` (View results hides the
sidebar), `test_app_options.py` (assign ids).

## 0.5.8.post100 — 2026-10-22 (the combined set: no "STTM_" in its name; OBJECT_ID numbered across the run)

- **Name** (Soham: confusing): the combined files and the App's "<name> DDL and IIG"
  heading came from the workbook's stem as is (`STTM_Pyx_…_IIG.xlsx`). `run_artefacts.
  sttm_name` now drops a leading / trailing `STTM` token (`STTM_Pyx_X` -> `Pyx_X`,
  `X - sttm` -> `X`); a name that is only `STTM` keeps it.
- **OBJECT_ID** (Nikshit via Soham): every row read 1 - each feed is its own group with one
  file (the framework's 1..n within the group; the pair_11 golden has 1 everywhere too,
  told apart by GROUP_ID, which the agent leaves blank). `combined.object_ids: run`
  (config.yaml) numbers the objects across the run's feeds in the combined IIG: feed 2's
  objects follow feed 1's, and every sheet of a feed moves alike, so its STGDELTA and DQ
  rows still name their object; the cell note says so. The per-feed IIGs keep 1..n;
  `object_ids: group` turns it off.
- **On pair_11** (mock container harness): `Pyx_Care_Management_Data_MI_DSNP_{DDL.txt,
  IIG.xlsx, IIG_REVIEW.xlsx, LOG.md}`; ADLS_DELTA 1–5, STGDELTA 1–5 (same tables), DQ rows
  their feed's number; gate clean.

**Tests:** `test_run_artefacts.py` (`sttm_name`;
`test_object_ids_are_numbered_across_the_run_and_keep_their_links`).

## 0.5.8.post99 — 2026-10-22 (the combined IIG writes the master pipelines once; where each environment value came from)

**The grand master / master pipeline rows are written once** (Soham, against the pair_11
golden: 1 grand master + 1 master for the run, then a stage and a standard child per feed;
the combined IIG had 4 rows per feed, 20 in all). `combined.dedup_rows`
(`DATA_FACTORY_PIPELINE_SCHEDULE: {column: PIPELINE_NAME, prefixes: [PL_GMSTR_, PL_MSTR_]}`,
the EDO Naming Standards' grand master / master types): a row with one of those prefixes
that equals an earlier feed's row on every column is dropped
(`run_artefacts.merge_payloads`).
- **Children are never merged.** Under the naming document's child pattern (no feed token)
  several feeds' children share a name; Soham: do not deviate from the document. Rows that
  share a PIPELINE_NAME but differ in any cell are kept, and the combined `_LOG.md` names
  them ("Same PIPELINE_NAME, different cells … check before approving").
- **"row n" references follow** (`_remap_refs`): a child whose master was merged away now
  points at the kept master.
- **On pair_11** (mock container harness): 20 rows -> 14 (one grand master + master per
  frequency: weekly and monthly), every child kept, each child's parent its own frequency's
  master. The per-feed IIGs are unchanged.

**Where each environment value came from** (App): `environments.<name>.provenance` (per
field, plain English; D1's in `acfc_env.yaml`, never a value that stays out of git) is
listed under the panel's "Where these values come from"; a value edited in the App says so.
Display only.

**State (no code):** the D1 profile `environments/d1.yaml` (volume + workspace copy) no
longer says "the suite's synthetic D1 profile"; the value is unchanged (backups
`d1.yaml.bak_20261022_pre_comment`).

**Tests:** `test_run_artefacts.py::test_the_masters_are_written_once_and_children_follow_them`,
`test_environments.py` (provenance), `EnvironmentSelector.test.tsx` (2 new).

## 0.5.8.post98 — 2026-10-22 (App: the environment values as a collapsible; the IIG review workbook hidden)

Soham: the environment panel listed 11 technical keys, each with a long "from …" line
(`catalog_map.PR_DLK` next to `default_catalog.stage`, the framework connection ids).
Display only (`ui/frontend/src/components/EnvironmentSelector.tsx`); how a run resolves
its environment, the answer keys and the CLI are unchanged.
- **Collapsible:** the fields sit behind one summary line (storage account · catalogs ·
  required values set / N missing); it opens by itself while a required value is missing.
- **Groups:** Storage (the required keys) · Catalogs · Framework connection IDs (a nested,
  closed section) · Other values.
- **Catalogs:** a layer's `default_catalog` and the `catalog_map` entries with the same
  value show as ONE row ("Stage catalog", "Standard catalog"); an edit writes every merged
  key. Values that differ, or are unset (A2 / PR), stay separate rows.
- **Plain English:** every row carries a one-line explanation (`explainField`).
- **Sources:** shown only where a row's source differs from the one most fields share,
  shortened (`shortSource`), the full text as the tooltip; the shared source and the
  profiles folder moved into a closed "Where these values come from" section.

**The IIG review workbook is hidden in the App** (Soham): `output.app_files` (config.yaml
`[ddl, iig, addition, log]`) is what the artefacts panel and the combined set LIST
(`/api/feeds` `combined` + `app_files`; `artefacts.presentedArtefacts(files, shown)`).
The workbook is still written and `/api/combined/<name>` still serves it by name; the
CLI is not affected. **To show it again:** `app_files: [ddl, iig, iig_review, addition,
log]` (the model default lists every kind).

**Also:** `docs/acfc/STANDARDS_DEPRECATION_REVIEW.md` — which agent rules came from the
deprecated ADF coding-standards section, and the decisions still open.

**Tests:** `EnvironmentSelector.test.tsx` (5 new; the source test updated);
`test_app_options.py`, `test_combined_route.py`, `artefacts.test.ts` (app_files).

## 0.5.8.post97 — 2026-10-22 (the combined DDL: every stage table first, then every standard table)

Soham: the combined `<STTM>_DDL.txt` (post91) placed each feed's stage and standard tables
next to each other (stage A, standard A, stage B, standard B, …).
- **Now by layer** (`run_artefacts.merge_ddl`): every stage table, then every standard
  table — the order one feed's own DDL already uses for several tables
  (`emit.framework._combined_ddl_text`: each layer in turn), and the client reference
  DDL's layout. It also matches the deployment: stage and standard sit in different
  catalogs / schemas, and stage loads first.
- **Order inside a layer:** within a layer the tables keep feed order; a block's layer is
  its banner line.
- **Unchanged:**
  - each block keeps its own banner;
  - an identical block is still written once;
  - a conflict's versions still sit together under the `-- CONFLICT` line;
  - the per-feed DDL files (byte-compared to the golden).

**On pair_11** (mock container harness): stage ×5, then standard ×5; 10 blocks (= the
per-feed total); outcome and gate unchanged.

**Tests:** `test_run_artefacts.py::test_all_stage_tables_come_first_then_all_standard_tables`.

## 0.5.8.post96 — 2026-10-22 (App: the wording of a question that carries a suggestion)

Checked on the redeployed App (post95, pair_08 live): the blank-stage-type questions offer
`STRING` as one unselected click. Their text still said "No document states this value …
the agent never guesses a target" and "No document states it — type it, or leave it
empty", which reads oddly next to a suggestion.
- **Backend:** `ui/backend/demo.pending_question` — with a proposal, the hint reads "This
  row leaves the value blank. The suggestion below comes from the sheet's other rows —
  pick it, or type the value the source team confirms. Nothing is filled in until you
  answer."
- **Frontend:** `LayoutQuestions.whyLine` — with a proposal, "Pick the suggestion below, or
  type your own value, or leave it empty."
- **Unchanged:** questions without a suggestion keep their wording.

**Tests:** `test_post94_extraction.py` (the hint); `LayoutQuestions.test.tsx` (the
unselected radio, the line, the plain case); frontend 97 tests; `dist` rebuilt.

## 0.5.8.post95 — 2026-10-22 (the blank-stage-type proposal: spellings, and one click in the App)

The first live runs on the redeployed App (post94; Soham approved, pairs 08 / 10 / 03 / 11)
showed two gaps in post94's proposal:
1. **Spellings:** pair_10's sheet writes the stage type of its STRING columns `string` ×157,
   `String` ×3, `STRING` ×3; the tally counted them as a disagreement, so no proposal. Stage
   types now group case-insensitively; the sheet's most common spelling is proposed.
2. **One click in the App:** `ui/backend/demo.pending_question` built the question as a
   free-text box only. It now carries the extractor's proposal as a candidate (source
   `proposed`): one click, never pre-selected; typing another value still works.

**The live App runs** (post94 on the App; CODEGEN_PROVIDER=live):
- **pair_03:** PASS_WITH_OPEN_INPUTS with NO answers (post92–94).
- **pair_11:** PASS_WITH_OPEN_INPUTS (no VDD — answered "none"). One combined set, 67 IIG rows,
  per-table reject paths (post86 / post91).
- **pair_08:**
  - the live layout model resolves the STTM;
  - the audit columns are no longer asked (post94 item 2);
  - all 7 blank stage types carry a proposal — column 87 `STRING`, "INT in standard =
    STRING in stage, 39 of 39";
  - the run then FAILs on the known contract mismatch (the FRD names 4 stage tables in one
    cell): the multi-table decision.
- **pair_10:** stops before generating on the delimiter of all 4 feeds and the load
  strategy / LOBs of feeds 1–3 (the BSA answered feed 0 only), as in the post75 report.
- **Redeploy checks:**
  - the storage account is pre-filled with the demo value;
  - framework only (no notebook in the App);
  - the combined set downloads (DDL / IIG / IIG review / LOG).

**Tests:** `test_post94_extraction.py` (mixed spellings; the App candidate).

## 0.5.8.post94 — 2026-10-22 (extraction gaps the BSA pass answered by hand)

The post75 BSA answers record where each value was (`source:`). Three values a document
states that the extractor missed (Soham's choices, one each):

1. **pair_03 — "Truncate & Load (Delete existing records and perform a full data
   reload)"** was left null (only "Truncate and Load" matched).
   - `extractor.frd.load_strategy_synonyms` (`"Truncate & Load": "Truncate and Load"`,
     the EDO Naming Standards' spelling too); values typed to the three strategies.
   - A trailing parenthetical explanation is ignored when matching.
   - pair_03 now completes with NO answers file: PASS_WITH_OPEN_INPUTS (mock container
     harness).
2. **pair_08 — audit rows written as mapping rows.** Rows 444–446 (SRC_FILE_NAME,
   REC_CREATION_TIME, REC_UPDATED_TIME) carry a description in the source band ("Data
   Definition"), so they read as neither audit nor mapping rows; the feed asked for its
   audit columns.
   - A row with NO source field name whose stage column is in the new
     `extractor.audit_column_names` (`[SRC_FILE_NAME, REC_CREATION_TIME,
     REC_UPDATED_TIME]`; LOB left out — often mapped) is an audit row.
   - Both conditions must hold (blank source field alone could be a derived column; a
     name alone could be a real mapped field).
3. **pairs 08 / 10 — a stage type left empty while the row's standard band types it**
   (8 columns). Not copied from the standard band:
   - In pair_08 every standard INT row is STRING in stage (39 of 39), likewise DECIMAL
     13/13 and DOUBLE 3/3; copying would have typed one stage column INT.
   - The blocking question stays and now PROPOSES the stage type the same sheet's other
     rows unanimously pair with that standard type, with the count (`candidates`, the
     reason).
   - The proposal needs at least `extractor.discovery.stage_type_proposal_min_rows` (3)
     agreeing rows; with a split or too few, no proposal. Never written unasked.

**Not done (deferred, Soham's choice):**
- pair_09's per-table load strategies in its STTM Summary sheet. 36 tables, 3
  strategies; the contract holds one per feed and the pair FAILs on "35 tables only in
  FRD" anyway — waits on the multi-table / contract-mismatch decision.
- pair_10's FRD prose values (file format, load strategy, LOBs). The paragraphs are not
  in feed order, so attributing them is a layout-model task, not a reader rule.

**For the BSA (reported, not changed):** the volume's pair_08 answer for
`feeds[0].columns[87].target_type` is `INT`; by the sheet's own convention (INT in
standard = STRING in stage, 39 of 39) it is probably `STRING`.

**Not shown on pairs 08 / 10 here:** in the container's mock run they stop at the layout
step (no cached layout profile; D1 resolves it with the live model). Items 2 and 3 are
pinned on synthetic Family E workbooks.

**Tests:** `test_load_strategy_spelling.py`, `test_post94_extraction.py`.

## 0.5.8.post93 — 2026-10-22 (pair_03: a source layout that repeats column names)

After post92, pair_03 reached its gate and failed `ruff` on the scratch pipeline's test
fixtures. The cause: its source layout repeats column names (10 × Qualifier, 10 × Type, a
repeating group; the stage / standard names are unique). That also left the IIG's
SRC_COLUMNS ambiguous (`Qualifier:Qualifier` ten times), which notebook v2's reader and
the client's framework map by name, and the generated pipeline's `F.col("Qualifier")`
select ambiguous.

Soham's choice (of: pipeline-only suffixes, leave at GATE_FAIL, ask the BSA, the
existing positional fallback): a repeated name identifies no field, so the existing rule
applies.
1. **The IIG:** `metadata_template._named_sources` also requires every source name to
   be unique, so SRC_COLUMNS takes the rule's own positional form `col<i>:<stage column>`.
   The cell carries an `iig_src_columns_positional` NOTE naming the repeats. (Not
   `STAGE:STAGE`: that is the rule-4 reading reverted pending the D1 golden cells.)
2. **The pipeline:** `emit.context.pipeline_source_names` — a file without a header row
   (fixed width, or segmented) whose source names repeat names its fields `col<i>` by
   position, for slicing, positions, the mapping and the test fixtures. A file WITH a
   header row keeps its header's names (not covered; the flag says so). The fixed-width
   test is now one function, `emit.context.is_fixed_width`.
3. **The flag:** `gate.source_names.repeated_source_name_flags` — one non-blocking
   `source_names_repeated:<segment>` flag per segment naming the repeated columns.
4. Feeds with unique source names are unchanged.

**On pair_03** (mock container harness, notebook + framework): GATE_FAIL →
**PASS_WITH_OPEN_INPUTS**.
- SRC_COLUMNS: 331 positional pairs, unique on both sides.
- Notebook v2: valid and compiles.
- Combined set: written.
- Leak gate: CLEAN.
- Flags: 5 `decimal_no_precision`, 1 `source_names_repeated`.

**Tests:** `test_repeated_source_names.py` (including a fixed-width synthetic feed with
two Detail fields renamed alike: its gate passes).

## 0.5.8.post92 — 2026-10-22 (pair_03: a DECIMAL with no precision no longer crashes the feed)

pair_03 CRASHED since post75 with "STTM data type invalid … [TemplateGapError]". The
cause was not its load_strategy answer: five standard-layer columns of its STTM are
typed `DECIMAL` with no precision (stage STRING, source numeric length 5), and
`emit.context.sql_type` knew `DECIMAL(p,s)` and plain types only.

1. **Written as stated** (Soham's choice): a bare `DECIMAL` maps to `DECIMAL` (valid
   Databricks SQL, read as DECIMAL(10,0) — no fractional digits). No precision is derived
   (a source length is a byte width).
2. **Flagged:** `gate.decimal_precision.decimal_no_precision_flags` — one non-blocking
   `decimal_no_precision:<layer> — <table>.<column>` flag per such column (STTM row,
   "confirm the precision with the STTM author"), joined with the drag-fill flags in
   `cli.generate_feed_result`.

**On pair_03** (mock container harness): CRASHED → GATE_FAIL. The gate now reaches its
checks and fails `ruff` on the scratch pipeline's test fixtures. That is the next defect,
not this one: the source repeats column names (10 × Qualifier, 10 × Type; the stage /
standard names are unique), which also makes the IIG's SRC_COLUMNS ambiguous. That is
the next version (the stage names when source names repeat).

**Tests:** `test_decimal_no_precision.py`.

## 0.5.8.post91 — 2026-10-21 (one IIG / DDL / review / log per run; notebooks off in the App)

Soham: one IIG, one DDL, one IIG review per run (overlaps skipped), ADDITION.md merged
as `<STTM>_LOG.md`, one "<STTM> DDL and IIG" heading, and notebook generation out of the
App, easy to turn back on. Plan tested adversarially before building; the main finding
changed the overlap rule (below).

1. **The combined set** (`codegen.run_artefacts`, config `combined:`). Each generate
   run writes `<out>/combined/<STTM>_IIG.xlsx`, `_IIG_REVIEW.xlsx`, `_DDL.txt` and
   `_LOG.md` beside the per-feed files (which the harness, iig_diff and the manifest
   keep reading).
   - **STTM name:** the workbook the extracted contract names (`generated_from_workbook`),
     upload prefix / `(n)` dropped, made file-safe; the same in the CLI and the App, whose
     manifests stay byte-identical.
   - **Overlaps:** rows merge by content ONLY on `combined.dedup_sheets`
     (`[EMAIL_TEMPLATE_CONFIG]`). On pair_11 a merge-any-equal-row rule would have
     dropped 26 of 73 rows (12 / 20 schedule, 8 / 10 notebook, 6 / 10 email), but the prod
     golden keeps every schedule and notebook row distinct per feed (and 5 DQ rows that
     differ only by IDs) while it has 2 email rows for the whole run. Look-alike rows
     elsewhere are kept and counted in the log.
   - **The DDL:** an identical table block is written once; two different blocks for one
     table are both kept under a `-- CONFLICT` line (listed in the log; never chosen).
   - **The review copy:** each feed's first row is commented with its sheet rows; an
     in-feed "PIPELINE_ID of row N" reference is moved to the merged row.
   - **The gate:** the IIG checks (derivations, single-line, single-value) run on the
     combined workbook; a failure is listed in the log and the manifest.
   - **Which feeds:** kept feeds only. GATE_FAIL (quarantined), CRASHED and held-back
     feeds are listed in the log as left out, with the reason. A `--feed` run writes no
     combined set; `combined.enabled: false` turns it off.
   - **The log:** inputs (contract names + sha256), the files, the feeds, sheet rows per
     feed, merged / kept counts, conflicts, the framework-assigned IDs once, the review
     flow once.
   - **The manifest:** `CODEGEN_STAGES.json` gains `combined` (only when written).
   - **Tools:** `scripts/run_round.py` and `tools/iig_fill_rate.py` skip `combined/`.
2. **The App:** GET /api/feeds carries `combined` (from the run's manifest; files that
   exist); GET /api/combined/{name} serves a listed file only. The Framework artefacts
   panel shows one block "<STTM> DDL and IIG" with the four files; a run without a set
   (older runs, startup feeds) keeps the per-feed blocks.
3. **Notebooks off in the App:** `output.app_options` (config.yaml: `[framework]`; to
   show notebooks again: `[notebook, framework]`). The output options, the parts a run
   may select (a hidden one is refused, a stale saved one dropped), the App's default,
   and the startup / Regenerate generations follow it. With one option the Output toggle
   row is hidden; the Notebooks panel, the zip button, the feed page's Notebook tab and
   `.ipynb` download, and the notebook wording in the Layer-2 hint go when notebook is
   not offered. The CLI is not affected.
   - Framework-only App runs ask fewer before-generate questions (a notebook's open
     landing / cells block only notebook runs).

**On pair_11** (mock container harness):
- 4 combined files; 67 rows (73 − 6 email rows merged); schedule 12 and notebook 8
  look-alikes kept; 10 DDL blocks, no conflicts; the combined gate checks pass;
- outcome PASS_WITH_OPEN_INPUTS and gate CLEAN, unchanged; the per-feed IIGs are
  cell-for-cell identical to post90's;
- iig_diff on the per-feed files: 30.0 (unchanged). An unsorted `--agent` list scored
  30.3: iig_diff depends on the file order (pre-existing; run_round sorts).

**Tests:** `test_run_artefacts.py`, `test_combined_route.py`, `test_app_options.py`,
`appOptions.test.ts`, `Dashboard.test.tsx` (combined panel, notebooks off); updated
`test_generate_entry_point.py` (the App passes its contract, as the real caller does),
`test_audit_annotation.py`, `test_model_usage_and_outputs.py`. Frontend 95 tests;
`dist` rebuilt. Screenshots: the combined panel; the Generate page without the Output
row.

## 0.5.8.post90 — 2026-10-21 (App: download every notebook in one zip)

Soham asked for a final notebook wrapping every feed. Assessed first:
- orchestration belongs to the client's master pipelines (`PL_GMSTR` / `PL_MSTR`; "the
  master notebook is ACFC's own");
- the feeds don't share a schedule (pair_11: 3 Weekly, 2 Monthly);
- a failed wrapper re-run would re-load the feeds that had succeeded (append = duplicate
  rows);
- withheld notebooks would go unseen;
- pasting the notebooks together would let one feed's names overwrite another's;
- a wrapper has no contract of its own to put in a provenance banner.

His choice: a zip of the notebooks, which needs none of those decisions.

1. **`GET /api/notebooks.zip`** (`ui/backend/main.py notebooks_zip_bytes`):
   - every written `.ipynb` of the loaded run, at the zip root, byte-identical to the
     generated file, in feed order;
   - plus `README.txt`, listing them and naming each feed that has no notebook
     (framework only, or withheld by a blocking question);
   - fixed entry timestamps (the same run gives the same bytes); 404 when the run wrote
     no notebook.
2. **The Notebooks panel:** a "Download all (<n>) .zip" button before the per-feed
   buttons, when there is more than one notebook.

**Checked:**
- pair_11's 5 real notebooks zipped: each entry is valid nbformat and identical to its
  generated file;
- the panel screenshotted in headless Chromium.

**Tests:** `test_notebooks_zip.py` (4); `Dashboard.test.tsx` (zip button); frontend
91 tests; `dist` rebuilt.

## 0.5.8.post89 — 2026-10-21 (App: no per-feed summary line; empty sheets explained in the review copy)

Soham: the line after each feed name in the Framework artefacts panel ("8 sheets · 15
rows · 2 open inputs (0 blocking) · empty by rule: FILE_ADLS (MFT), FIXED_WIDTH
(delimited)") need not be visible to the client. Assessment:
- the sheet / row counts decide nothing (every iig_v2 feed has 8 sheets);
- the open-input count added the run-level lines to EVERY feed (one `run.email_to`
  counted once per feed: the post66 open item), and the inputs are answered in the
  inputs panel and listed in the review copy anyway;
- only "empty by rule" helps, and the review copy the BSA approves did not carry it (its
  summary lists open cells; an empty sheet has none).

1. **The App:** the line is gone (`artefacts.ts reviewSummary` and its tests removed); a
   feed shows its name and its downloads. The API fields (`framework.open`,
   `framework.empty_by_rule`) are unchanged.
2. **The review copy:** `REVIEW_SUMMARY` gets one row per sheet left empty by rule:
   - the columns: sheet, `empty by rule (no rows expected)`, owner `no action`, 0 cells,
     and the reason in plain words;
   - the wording: config `iig_review.empty_by_rule_label` / `empty_by_rule_owner` /
     `empty_by_rule_reasons`;
   - the reasons: MFT landing → FILE_ADLS; delimited file → the fixed-width handler.
   ADDITION.md's description of the review copy says so. The clean IIG is unchanged.

**On pair_11** (mock harness): both rows are written for every feed; outcome, open lines
and leak gate unchanged.

**Tests:** `test_review_summary.py::test_the_review_copy_says_why_a_sheet_is_empty`;
`test_iig_review.py`'s open-cell inventory skips the new rows; frontend 90 tests;
`dist` rebuilt.

## 0.5.8.post88 — 2026-10-21 (App: the sidebar can be hidden and shown again)

Soham: a button to collapse the dark sidebar and another to bring it back
(`components/CollapsibleSidebar.tsx`, used by `App.tsx`).
- **Hide:** an icon button in the sidebar's top-right corner. The sidebar is then not
  displayed but stays in the DOM.
- **Show:** a small dark tab fixed at the top-left. The main area gets a wider left
  gutter while it shows, so the tab never covers content; modals (z-index 50) sit above
  it.
- **Accessibility:** real `<button>`s with `aria-label`, `aria-controls` (the sidebar's
  id) and `aria-expanded`, and a visible focus ring. After each toggle, focus moves to
  the button that undoes it; nothing moves focus on page load.
- **Remembered per browser:** `localStorage` key `codegen.sidebar.open`. Blocked or empty
  storage = shown, and the toggle still works for the page.

**Tests:** `CollapsibleSidebar.test.tsx` (4); frontend 94 tests; `dist` rebuilt. Not
checked in a real browser here (no browser binary in the container).

## 0.5.8.post87 — 2026-10-21 (App: the framework-assigned IDs said once)

Soham: the Dashboard's Framework artefacts panel repeated "Framework-assigned IDs left
blank: … — the agent never invents them." under every feed.
- **Said once:** the line now sits at the top of the panel and lists the columns every
  feed leaves blank (`artefacts.ts blankIdColumns`).
- **Per feed:** a feed shows "Also left blank for this feed: …" only when it leaves
  blank a column the others don't (usually never); no column a feed lists is dropped.
- **Unchanged:** the backend field (`framework.flagged_blank_columns`) and each feed's
  ADDITION.md, which still lists its own IDs (every download stands alone).

**Tests:** `artefacts.test.ts` `blankIdColumns` (frontend 90 tests); `dist` rebuilt.

## 0.5.8.post86 — 2026-10-21 (path families: a source's own path convention)

The pair_11 TGT_RJT_ADLS_PATH gap (open since post84) was a convention, not a bug:
- **pair_11's prod golden** writes one folder per table, on 4 of 4 rows:
  - `Processed/<table>/` and `Reject/<table>/`;
  - the stage → standard leg's archive at `Processed/<table>/Archive/`.
- **The SD prod rows and the SFMC reference IIG** write `Reject/<table>_reject`, and
  `Processed/` + `Archive/` on the stage → standard leg (round 6).
- **The pair-1 PRX golden** has a third shape again (`Processed/<table>_reject`).

Changing the shipped shapes would have broken SD to fix pair_11.

1. **`path_families`** (`metadata.templates.<t>.path_families.<name>`: `path_patterns`
   + a required `citation`):
   - the shapes a family writes differently; every other cell keeps the template's
     `path_patterns` (family `default`, reserved);
   - `acfc_env.yaml` ships `per_table`, from the pair_11 golden.
2. **Which feeds use one:**
   - `path_family_by_source.<words>`: the FRD source begins with those words
     (case-insensitive, whole words; the longest key wins);
   - `feed_overrides.<feed>.path_family` wins over it;
   - source names are client terms, so they go in the ACFC overlay only.
   - An unknown family, a reserved name, a sheet the template lacks, or an empty
     citation fails when the config loads.
3. **Applied once per feed** (`metadata_template.with_path_family`), in
   `template_tab_rows` (every IIG sheet) and `notebook_paths` (the notebook's reject
   path follows). When a template has families, every path cell's tooltip names the
   family and why, `default` included.
4. **The D1 overlay** (volume + the App's workspace copy) maps pair_11's source to
   `per_table`.

**On pair_11** (mock container harness, state = environments + the post86 overlay
line only):
- **The fixed cells:** ADLS TGT_ADLS_PATH / TGT_RJT_ADLS_PATH and STGDELTA SRC_ADLS_PATH
  / SRC_ADLS_ARCHVL_PATH / TGT_ADLS_PATH / TGT_RJT_ADLS_PATH are 4 / 4 exact (were 16
  mismatched + 8 normalized).
- **Score and outcome:** TOTAL 28.5 → 29.7; outcome and open lines unchanged
  (`run.email_to` only); leak gate clean.
- **Without the overlay line** the feeds get `default`, the shapes as before.

**Still open:**
- RECYCL_ADLS_PATH (4 rows): the golden states a recycle that no document we read
  does, so the cell is NA (recycle detection, not a shape).
- A new feed of a source the overlay does not map gets `default`; its tooltip says so.
- Which convention is the standard (or whether it varies by source) is for
  Venu / Nikshit; the corpus's shares (D1 `patterns.json`) would answer it too.

**Tests:** `test_path_families.py`.

## 0.5.8.post85 — 2026-10-21 (pipeline names: the EDO Naming Standards document)

Nikshit (2026-10-21), on the Naming Standards vs the prod IIG: "yes it would [be]
layer rather than table names. go by the document for now.. we would see how it comes
out."

1. **The document's patterns, shipped in `acfc_env.yaml`**
   (`conventions.profiles.acfc_prx.pipeline_name_templates`):
   - master: `PL_<GMSTR|MSTR>_<Product>_<Sub-Product>_<Sources>_<Domain>_<Subdomain>_<Region/LOB>_<Frequency>`;
   - child: `PL_CHLD_<Product>_<Sub-Product>_<Source>_TO_<Target>_<Load Strategy>`, with
     Source / Target = the DATA LAYERS: `RAW_TO_STG` (file → stage) and `STG_TO_STD`.

   They replace post81's interim prod-reconstructed convention.
2. **New tokens** (`input_choices`), read through the document's abbreviation tables the
   way the WF job name already reads them (`emit.context._abbreviate`):
   - `{product_code}` `{sub_product_code}` (DLK / NSP) `{source_std}` `{domain_std}`
     `{subdomain_std}` `{lob_std}`;
   - per child flow, `{load_std}`: the document's Load Strategy table, new
     `engineering_standards.load_strategy_abbreviations` (TRUNC / INSRT / UPSRT / EXTR);
   - the App's preview tokens now carry the config too.
3. **The D1 overlay no longer overrides them.** The post79 interim templates were removed
   from the volume's `overlays/acfc_prx.yaml` and from the App's workspace copy (backup
   `acfc_prx.yaml.bak_20261021_pre_post85` on the volume).

**How it comes out on pair_11** (mock harness, full state):
- 30 of 30 names written; outcome PASS_WITH_OPEN_INPUTS; leak gate clean.
- **The child names are the same for all 5 feeds**, one for RAW_TO_STG and one for
  STG_TO_STD: the document's child pattern has no feed component.
- **The master names are long:** the document's tables have no code for this source,
  domain or sub-domain, so each is spelled out:
  - the source is the FRD's SOURCE text, a parenthetical included;
  - the domain is two words;
  - the sub-domain is the FRD's two sub-domains joined.
- Both are for Nikshit / Venu.

**Correction to post81:** the overlay does NOT set EMAIL_TO (its default is the
`<<D1:EMAIL.EMAIL_TO>>` placeholder), so `run.email_to` stays open with or without the
grant. post81 item 6 said otherwise.

**Tests:** `test_pipeline_name_choice.py::test_the_shipped_names_follow_the_naming_standards_document`.

## 0.5.8.post84 — 2026-10-21 (the landing: read from the FRD's requirements, else written from the convention)

Soham: the landing (inbound) paths were still asked, one per feed, instead of being
written by default with a button to change them.

1. **The Pyx FRD states every feed's landing; the reader missed it.** Its metadata
   "ADLS Location" cell lists two paths on two lines, so the reader refused it as
   multiline, and every feed's landing came out unstated. Each Solution Requirement
   states its own file's landing ("Raw ADLS Location : <path>", on the same line or the
   next). `frd_docx.requirement_landings` reads them (labels:
   `extractor.frd.requirement_landing_labels`, as the client FRD writes them).
   - **Per-feed matching:** they become per-file blocks for the unstated landing, and
     `layout.resolve.resolve_structured_fields` gives each derived feed its own.
   - **The key:** each block is keyed by the requirement's Name plus the `word_word`
     identifiers only that requirement names. A descriptive Name still reaches its feed
     through the file it names; anything unmatched stays unstated.
   - **On pair_11** (mock harness, no overlay, no answers): 5 of 5 feeds get their stated
     landing, and SRC_ADLS_PATH and SRC_ADLS_ARCHVL_PATH equal the prod golden's for all
     5. TGT_RJT_ADLS_PATH differs from the golden for all 5; that is the existing reject
     derivation, not touched here (open).
   - **The run:** the outcome is PASS_WITH_OPEN_INPUTS (was NEEDS_ANSWERS); 5 notebooks
     written; the only open line is `run.email_to`.
2. **Else, the convention is written** (`metadata.templates.<t>.landing_autoset`, `true`
   in `acfc_env.yaml`). When no document states a landing and `landing_proposal` renders:
   - **Written unasked:** the IIG's path cells and the notebook's paths
     (`metadata_template.with_landing_default`, applied in `cli.generate_feed_result` and
     `notebook_env`);
   - **Flagged:** one flag `landing_from_convention:`;
   - **One NOTE line:** "profile default applied", with no question;
   - **The App:** a profile-default item in the "Change defaults" panel.

   A change there is the next run's `gaps:` answer (`DemoRunner._landing_choices`), and
   the CLI's `inputs: feeds[<i>].src_adls_path` still sets it. A stated landing always
   wins. No rendered proposal (an unstated domain / source) = the question, as before.
   CAUTION: the corpus's top landing shape is only ~50% of rows.

**Tests:** `test_requirement_landing.py` (the reader, synthetic); `test_landing_question.py`
(autoset writes the convention, the notebook is not withheld, a stated landing wins, the
App's item and its change); the question-path tests run under the new
`landing_autoset_off` fixture (conftest).

## 0.5.8.post83 — 2026-10-21 (View results no longer re-runs the run after a Confirm)

Soham: "View results" lagged several seconds. The App logs showed it calling
`POST /api/demo/load-live-run` (≈3 s: the run rebuilt from disk, every feed regenerated)
instead of showing the run already in memory.

- "View results" takes the fast path only when the page's status says `mode: live` and
  `label == last_run_label`. `POST /api/demo/input-choices` (the Confirm of "Change
  defaults" / "Change pipeline names") returned the runner's bare status, without
  `mode` / `label` (only `GET /api/demo/status` added them). Polling has stopped once the
  run is done, so the page kept that status and the next click fell back to
  `load-live-run`. It showed up now because post79 / post81 put those Confirm buttons on
  the finished-run screen.
- Fix: `input-choices`, `run-live`, `layout-answers` and `layout-refresh` all return the
  same full status as `GET /api/demo/status` (`ui/backend/main.demo_status`).

**Tests:** `test_demo_ui.py` (every status-returning POST has the GET's shape, mode /
label included), `ModesPage.test.tsx` (View results on the adopted run never calls
`load-live-run`).

## 0.5.8.post82 — 2026-10-21 (the notebook one click from the results, never behind Layer 2)

Soham: the App's notebook could be reached only through the feed page, beside the
"Layer-2 review" tab and under an "Ask the model (5 request(s))" panel — so deferring
Layer 2 looked like deferring the notebooks too.

1. **The notebook tab looked in the wrong place.** Notebook v2 (acfc_prx) writes
   `<feed>/notebook/<slug>.ipynb`; the feed page's Notebook tab and both "Download
   .ipynb" buttons asked for `<slug>.ipynb` at the feed root (v1's place), so they
   could not find it. The App's feed summary now carries `notebook` (the path the run
   wrote, relative to the feed dir; `ui/backend/main._notebook_path`), and the page
   uses it.
2. **A "Notebooks" panel on the results page**: one download per written notebook,
   above the Layer-2 panel ("ready to download — the Layer-2 review is optional").
3. **The Layer-2 panel says it is optional**: the notebooks, DDL and IIG are already
   written; asking adds the review candidates and the notebook's trailing review cell
   (nothing else in the notebook changes — `notebook_v2.with_review`).

**Tests:** `Dashboard.test.tsx` (the panel and its path), `test_generate_entry_point.py`
(`_notebook_path` for v1 / v2 / none).

## 0.5.8.post81 — 2026-10-21 (defaults written unasked; one "Change defaults" button)

Soham, after the deployed post80 App run of the Pyx pair asked 32 questions: those should
run as defaults unless the button is pressed; ACTIVE_START_DATE defaults to the run date.
The 32 were 20 pipeline names (the App cannot read the state volume's overlay until the
`USE CATALOG` grant, so it had only the `SYN_` placeholders), 5 primary keys, 5 active
start dates, application_name and email_to.

1. **The interim pipeline-name convention ships in `config/overlays/acfc_env.yaml`**
   (`conventions.profiles.acfc_prx.pipeline_name_templates`, the four flows — tokens and
   format / layer words only; scrub + leak gate clean). The state overlay still overrides
   a flow. It stays the interim convention until Venu says which is ground truth (EDO
   Naming Standards vs the prod IIG).
2. **APPLICATION_NAME is a profile default** (`default_kind: profile_default`, the feed's
   SOURCE), written unasked. A run-level default with a per-feed token is no longer asked
   once for the run (`metadata_template.owed_questions`): each feed writes its own value.
3. **ACTIVE_START_DATE = the run date** (`default: "{run_date} 00:00:00"`, profile
   default). `{run_date}` = `CODEGEN_RUN_DATE`, else today (`metadata_template.run_date`);
   the suite pins `CODEGEN_RUN_DATE` (conftest) so workbooks stay byte-stable.
4. **TGT_PRIMARY_KEY autoset** (`conventions.profiles.<p>.primary_key_autoset`, `true`
   in `acfc_env.yaml`): a key an explicit signal states (STTM Primary Key cells, the FRD
   key statement, FAQ `natural_key_columns`, corpus row) is written as a profile default.
   No signal on a merge load is still the blocking `QUESTION feeds.<feed>.primary_key`.
5. **App: one "Defaults" line + a "Change defaults" button.** Every applied profile
   default other than the pipeline names (application name, active start date, primary
   key, email statuses, notebook names, SRC_FILE_NAME style) is no longer a radio list:
   "Defaults: N set by default (…)", and the button opens every value pre-filled; Confirm
   sends only the changed ones (`naming_standard` + the value; a cleared value is
   `leave_blank` only where the item offers it). Pipeline names keep their own line and
   button (post79). `ui/frontend/dist` is rebuilt.
6. **The storage account in the App, without the volume grant.** The App's picker
   showed `storage_account` blank: the account is in the volume's
   `environments/d1.yaml`, and the App cannot read the volume until the `USE CATALOG`
   grant (the picker's own override is in memory, lost on a redeploy).
   `CODEGEN_STATE_DIR` may now name a WORKSPACE folder (`/Workspace/...`), copied
   read-only through the Workspace API like the volume (`codegen.state_mirror`; the
   state line says "workspace folder"). The volume's `environments/d1.yaml` and
   `overlays/acfc_prx.yaml` were copied into the App's workspace state folder
   (`<App state folder>/codegen-state/`, not git), and `app.yaml` points
   `CODEGEN_STATE_DIR` there until the grant lands; then it goes back to the volume.
   This also gives the App the overlay's EMAIL_TO, so `run.email_to` is no longer open.

Pair_11 mock harness (`.venv-d1`), state = the environments only (no overlay, no answers
— what the App sees today): 6 open lines (post80 App run: 32) — the 5 landing paths
(blocking, notebook run; asked in the pre-generate pause with the proposal pre-filled) and
`run.email_to` (non-blocking; the overlay's value once the grant lands). Every pipeline
name, application name, active start date and primary key is written (source `profile`);
leak gate clean.

**Tests:** `test_pipeline_name_choice.py` (placeholder tests pass `SYN_` templates
explicitly; the shipped convention; application_name written and cleared),
`test_default_kinds.py` (the run date), `test_primary_key_proposal.py` (autoset writes the
signal's key; without it, proposed as before), `test_open_inputs_outcome.py`,
`InputsNeededBanner.test.tsx` (the Defaults line and panel).

## 0.5.8.post80 — 2026-10-21 (App: blocking questions asked before generating, once)

Soham, on the Pyx runs:
- "View results" was offered on a run that had stopped at blocking questions;
- "Continue" could not be clicked with nothing picked;
- the questions came after the run, followed by a rerun — why not ask them from the start?

1. **The pause before generating.** Every BLOCKING question the App can know before
   anything is written is asked ONCE, in the run's dialog, after the contracts resolve
   and before any feed is generated:
   - a required environment value (a "This run (environment)" group);
   - a value no document states;
   - the LOB per file;
   - on a notebook run, the landing path no document states, with the convention's
     proposal pre-filled.

   The run re-resolves with the answers and generates once. An environment answer
   becomes the environment picker's override, so it is kept for the next runs.
   "Proceed with unresolved" generates without the answers; they are then listed after
   the run, as before. The status carries `pause_kind: "layout" | "before_generate"`, and
   the dialog says "Paused before generating — …". Re-resolve layout and the model's
   advice are hidden during this pause. The code is `DemoRunner._before_generate_questions`
   / `_ask_before_generate` / `_resolve_specs`.
2. **No "View results" on a blocked run.** A finished run whose outcome is
   `NEEDS_ANSWERS`, or with a blocking line open, shows "Complete the blocking
   questions first" and a "Go to the blocking questions" button instead.
3. **The status names every blocking line** (`blocking: [{key, scope, feed}]`, from the
   run's open items). The page lists the ones no panel shows.
4. **The landing question is answerable after the run too.** When "Proceed with
   unresolved" left it open, it is a typed `gaps:` answer in "Answers needed"; the
   re-run's resolver sets the landing from it. Before, the App listed it nowhere and
   applied no answer: it ran generate with `inputs={}`. `GenerateRun.landing_asked`
   records what was asked.
5. **Continue works with nothing picked.** In the dialog, Continue with no pick does
   what "Proceed with unresolved" does.

Not moved into the pause: the merge-load primary-key QUESTION (`feeds.<feed>.primary_key`)
is still asked after the run.

**Tests:**
- `tests/test_app_needs_answers.py`: the pause on a full App run; Proceed lists the
  questions afterwards; an environment answer becomes the picker's override.
- `tests/test_generate_entry_point.py`: the status's blocking list; the landing answered
  in the App writes the notebook.
- `ModesPage.test.tsx`: the redirect; Continue with nothing picked; the pause's dialog.

## 0.5.8.post79 — 2026-10-20 (pipeline names: autoset from the naming convention, one "Change pipeline names" button)

Venu: use the naming standards for the defaults, and do not ask about the pipeline names
during the run; listing every name with its own choice is ugly. The EDO Naming Standards
and the Pyx prod IIG disagree on the convention, and Venu has been asked which is ground
truth. Until he answers, the interim default is the prod convention.

1. **Autoset** (`conventions.profiles.<p>.pipeline_name_autoset`, `true` in
   `acfc_env.yaml`). The rendered PIPELINE_NAME of every flow is written UNASKED, as a
   profile default:
   - source `profile` in `CODEGEN_STAGES.json`;
   - no INPUT_NEEDED line and no `frd_unstated` gate flag;
   - listed as changeable.

   An answers-file `choice: naming_standard` + `standard: <name>` overrides one flow, and
   `leave_blank` clears one.
2. **A `SYN_` placeholder template is never written**, not even on `use_default`. The
   Pyx App runs had written all 30 PIPELINE_NAME cells as `SYN_PL_…` that way. With no
   real template the name stays open: "no proposal: no naming standard loaded —
   placeholder".
3. **New name tokens**, taken from the IIG's own cells:
   - `{source_code}`: SOURCE's first word;
   - `{schema_domain}`: the word the stage and standard schema names share;
   - `{lob}`: the ADLS LOB cell;
   - `{object}` / `{object_code}`: OBJECT_NAME / its first word;
   - `{src_format}`: the file extension;
   - `{frequency_code}`: `engineering_standards.frequency_abbreviations`.

   See `codegen.input_choices.feed_tokens` and `docs/acfc/OVERLAY_FIELDS.md`.
4. **App.** Pipeline names are no longer a radio list per name. Each run shows ONE
   line: "Pipeline names: N set from the naming convention" (or "N of M open — no
   naming convention loaded"). A **Change pipeline names** / **Set pipeline names**
   button opens every name, pre-filled, in one panel, with an optional "fill all from
   one template" box. Confirm sends only the changed names: `naming_standard` + the name,
   or `leave_blank` for a cleared one. `ui/frontend/dist` is rebuilt.
5. **Interim templates in the ACFC overlay** (on the state volume, not git):
   - reconstructed from the Pyx golden IIG by aligning its names with the run's own
     IIG cells;
   - the previous overlay is kept as `acfc_prx.yaml.bak_20261020_pre_post79`.

   Mock harness run of pair_11 (`.venv-d1`):
   - 30 of 30 cells filled; 20 of 20 pipeline inputs from the convention; 0 pipeline
     INPUT_NEEDED lines; leak gate clean; 5 notebooks;
   - against the golden: **4 of 8 child names exact**. Both master names match except the
     frequency code: the FRD's frequency maps to a different code than prod uses. The 4
     other child names differ only in the object token.
6. **Caveats:**
   - The App cannot read the state volume until the `USE CATALOG` grant on `d1_dlk`
     lands. Until then the App sees only the shipped `SYN_` templates, so it asks, and
     writes nothing.
   - `pipeline_name_corpus` (the goldens folder) still refuses a name that collides with
     a prod one. Re-running an existing prod feed with its goldens loaded asks again
     instead of reusing its prod names.

**Tests:**
- `tests/test_pipeline_name_choice.py` now runs on a non-`SYN_` fixture template. New:
  a placeholder is never written; autoset writes unasked and one name can be changed;
  autoset never writes a placeholder; the cell tokens.
- `InputsNeededBanner.test.tsx`: the one line and the panel.

## 0.5.8.post78 — 2026-10-20 (EDH E2E v2.2: one feed per target; questions workbook; m93 chooser)

1. **One feed per target table.** v2.2 has a file whose blocks load two tables (m10, the
   `mixed_target` note). `read_dir` now emits one `GoldFeed` per target. Each feed carries
   its `manifest_index` and `blocks`, and the feeds are numbered over the whole manifest,
   so a `--table <i>` run keeps the same `feeds[<i>]` keys. A note goes to the feed of the
   lowest block it names, and rules go to the file's first feed: both are asked once.
2. **Lengths.** A new `length` role:
   - `field_length` holding a length → filled;
   - a type written in `field_length` or `target_format` → its `(n)` is proposed;
   - DATE → no length;
   - other text → QUESTION.

   m0's 9 lengths are proposals from `target_format`.
3. **`--questions-xlsx PATH`.** One sheet per feed (`feed_<i>`), columns `question_key,
   role, block_index, source_row, cell_text, question, answer`. The workbook quotes cells:
   - a path inside the repository is refused (exit 1);
   - a `/Volumes/...` path goes through the Files API when there is no mount;
   - the run prints `questions workbook: <path> (<n> rows)`.
4. **`--answers FILE`.** Either an answers.yaml read by the ingestion loader
   (`codegen.layout.answers.load_answers`, `gaps:` / `inputs:`) or the filled workbook.
   An answered key is not asked again; it is recorded under `GoldFeed.answered`, counted as
   filled, and applied where it sets a value (schema, load mode, SCD2 / SK, source
   catalog.schema, type, expression, key, length).
5. **Schema v2.2:** `extractor_version` 2.x, and the optional note `blocks:
   [{block_index, target_table}]`. On v2.2: the manifest and 11 of 11 files are valid.
6. **D1 run on the 11 real v2.2 files** (`docs/acfc/EDH_E2E_READER_RUN.md`):
   - 390 rows → 12 feeds; no crash;
   - 1,793 filled / 107 proposed / 210 QUESTION;
   - the questions workbook has 210 rows, in the state volume
     (`.../state/edh_e2e/questions_<run>.xlsx`).
7. **Profile docs.** `docs/acfc/ENVIRONMENT_ACFC.md` §h documents the `edh_e2e` keys and
   the QUESTION keys each closes. `docs/acfc/OPEN_QUESTIONS.md` §7 adds the four client
   questions: target schema; Facets database → UC; SCD2 / SK; the two functions.
8. **`test_m93_chooser` re-included and passing** (48 of 48). It had failed since c0358f6
   (2026-09-21) for two reasons:
   - `DocumentIndex._bounded` charged a parser restart to the file's budget (a product
     bug, fixed: the parse budget is the timeout minus the download time);
   - the first workspace download's cold SDK import (1.1 s) landed inside the test's
     1.0 s listing budget (the test now warms it).

   `main` has neither the test nor the code.

**Tests:** `tests/test_edh_e2e_reader.py`:
- per-target feeds, the stable numbering and the lengths;
- the workbook, the YAML / xlsx answers and the CLI's repo refusal.

Fixture (e) `syn_split_a_dim.json` is the clean two-target file. The profiler's mixed-target
defect is now "more than one target in one block".

## 0.5.8.post77 — 2026-10-20 (the EDH E2E gold-mapping reader)

The next phase is the gold layer: CodeGen generates the load SQL from extracted EDH E2E
mappings (Facets → Enterprise Data Hub; extractor dialect v2.1,
`docs/acfc/EDH_E2E_JSON_SCHEMA.md`). Nothing in the ingestion path changes.

1. **`codegen read-edh-e2e --input DIR --out FILE [--table N]`** reads `_manifest.json` +
   the table files into a new gold contract (`codegen.contracts.gold.GoldContract`; the
   STTM contract has no place for joins, filters, expressions or regions). The rule is
   the ingestion layouts' one:
   - **stated → filled**;
   - **derived → `status: proposed`**, plus an `INPUT_NEEDED` line;
   - **unstated or free text → `QUESTION feeds[<i>].<role>` /
     `feeds[<i>].columns[<j>].<role>`**, quoting the cell, exit 3.

   `<i>` is the manifest index. Every translated expression opens with
   `/* <file> block_index=<b> source_row=<r> */`.
2. **What it reads** (`codegen.layouts.edh_e2e`):
   - **Target:** catalog + table.
   - **Sources:** per block (`source_sets[]`).
   - **Column types:** from the regional structures (comma stripped, whitespace collapsed,
     `NOT NULL` → nullability; a sentinel → QUESTION; regions that disagree → proposal).
   - **Expressions:** Direct, `set NULL`, `current timestamp`, `CAST`, `[a,b]` →
     `substr(x, a, b-a+1)`, ISNULL / empty-string → `coalesce` / `nullif`,
     `if/THEN/ELSE` → `CASE`, `:` → `concat`.
   - **Joins:** J1 / J2 are proposed (same-name column); J3 gives explicit pairs, with
     `*=` read as LEFT; a second joined table becomes a second join.
   - **Filters:** F1–F5 become predicates (F4's slash notation is a proposal).
   - **Keys:** PK spellings → `primary_key`.
   - **Load:** "full … load" → `load_mode: full`.
   - **Regions:** keyed on their label; per-region drift is a proposal.
   - **Notes and rules:** `document_notes` and `rules` → one QUESTION each.
   - **Flags:** drag-fill and non-identifier region columns.
3. **Profile `edh_e2e:`** (config section; empty in the tracked config): `target_schema`,
   `source_catalog_map` (source database → UC `catalog.schema`), `scd2_mode`,
   `sk_strategy` and `function_map` (the documents' zero-argument functions → Spark SQL).
   Unset = a QUESTION per table, never a guess. The documents state no SCD2 / SK.
4. **D1 run on the 11 real v2.1 files** (`docs/acfc/EDH_E2E_READER_RUN.md`, counts only):
   - no crash; 11 of 11 exit 3;
   - 1,470 filled, 98 proposed, 200 QUESTION;
   - 102 of the 200 close with the profile, and 17 more with `function_map`.
5. **Dialect v2.1 docs + fixtures** (38f0959): the schema validates 11 of 11 real v2.1
   files. Fixtures are regenerated (fixture (a) has two blocks). The profiler checks
   `(block_index, target_attribute)`.

**Inside ACFC:** set the `edh_e2e` values in the ACFC overlay
(`codegen-state/overlays/<profile>.yaml`), never in the tracked config.

**Tests:**
- `tests/test_edh_e2e_reader.py`: every grammar class is filled or asked; the two-block
  fixture yields two source sets; the translator's classes; the CLI's answer lines; the
  reader and the profiler share their regular expressions.
- `tests/test_gold_profiler.py` (updated).

## 0.5.8.post76 — 2026-10-19 (Layer 2: one request per feed, its own stage after emit)

D1 post73 pair_11 (556 s over five feeds): Layer 2 asked one request per unmapped rule
per feed, inside each feed's generate, before the feed's files were written.

1. **One request per feed.** `reasoning.engine.reason_over_packs` hands a provider with
   `complete_batch` every unmapped rule of the feed in ONE request (`schema.BatchPack`:
   the rules numbered, the shared contract excerpts / columns once). The response is
   `{"candidates": [{rule, classification, code_candidate, rationale, citations}]}`
   (`providers.ask.ask_batch`, the same tolerant parser and retry loop). A response that
   leaves rules out is retried naming them; on the last attempt the answered rules are
   kept and the rest are recorded as failed. Grounding stays per rule, against that
   rule's own pack. Both live providers (anthropic, databricks_fmapi) and the mock
   implement it; a provider without it is still asked rule by rule.
2. **Layer 2 is its own stage, after emit** (`codegen.layer2_stage`). `generate` writes
   every feed's files, its gate verdict, its report and `CODEGEN_STAGES.json` (the
   outcome) with no model call. Only then does the stage run (`GenerateRun.layer2`,
   after `finish`). Its results never change the outcome or the exit code.
   `--layer2 now | defer | skip` on `generate` / `generate-all` (default
   `reasoning.layer2_cli: now`); the App's default is `reasoning.layer2_app: defer`.
   - `now`: one request per feed with rules. The candidates go into `candidates.json`,
     the report's candidates section, its Model usage line, and the notebook's trailing
     review cell.
   - `defer`: nothing is asked. `<feed>/candidates/layer2_pending.json` keeps the feed's
     rule packs (contract text only). The report and the App say "review candidates:
     pending". `codegen layer2 --output DIR [--feed ID] [--reports DIR]`, or the App's
     "Ask the model" button (`POST /api/demo/layer2`, confirm-gated), asks later with
     the same one request per feed.
   - `skip`: nothing is asked and nothing is kept; the rules stay unmapped for review.
   - `MODEL USAGE layer2:` and the `CODEGEN-USAGE` marker are printed once per feed, by
     the stage. Their providers now include `deferred` and `skipped` (0 calls).
   - Only a written feed is asked: a GATE_FAIL or CRASHED feed's Layer 2 is not. Generate
     clears a feed's previous `candidates.json` and `layer2_pending.json` first, so a
     rerun never shows the last run's candidates.
3. **Candidates never affect the verdict.** `compute_verdict` no longer takes
   candidates. An unmapped rule is the gate flag "Layer-2 candidate pending engineer
   approval" in every mode, read from the rule outcomes. The deterministic CONFIRM items
   (segmented extraction) reach the gate as flags (`verdict.review_item_flags`). What
   Layer 2 used to add to the gate ("provider failed", "NOT grounded", "pending
   approval" per candidate) is now an INFORMATIONAL flag of the Layer-2 stage, never
   pass/fail: `unimplemented_rule_has_candidate`, `layer2_candidate_not_grounded`,
   `layer2_provider_failed`. These appear in the report's candidates section and as
   counts per kind in the manifest's `layer2` rows. A feed's GateResult is
   byte-identical under `now`, `defer` and `skip`.
4. **Notebook (v2).** The executable cells are identical in all three modes; only the
   trailing `%md` review cell differs. That cell is now the last cell (it used to sit
   before the run report). Generate writes the notebook without it, and the Layer-2
   stage re-emits the notebook with it (`notebook_v2.with_review`: the other cells are
   unchanged byte for byte).
   - Under `now` this happens before the command returns, so the finished notebook
     carries the review cell as before.
   - Under `defer` it happens when `codegen layer2` or the App's button completes.
   - Under `skip` the notebook has no review cell.
   - A notebook a blocking line withheld, or a GATE_FAIL moved, is not touched.
5. **Manifest.** `CODEGEN_STAGES.json` gains `layer2: {mode, review_candidates, feeds:
   [{n, of, review_candidates, rules, calls, failed, seconds, flags}]}`, and each feed
   entry gains `review_candidates`. The values are `pending | done | skipped`, and `none`
   when the feed has no unmapped rule. The App and the CLI write byte-identical manifests
   under the same mode.
6. Tests: `tests/test_layer2_stage.py` (5 feeds × 7 rules → 5 calls, and the outcome
   and every IIG written before the first call; the verdict is byte-identical across
   modes; defer, then `codegen layer2`; skip; the batch retry; the App defers, then its
   button asks; the notebook's executable cells are identical across modes).

## 0.5.8.post75 — 2026-10-19 (the leak gate in the repo: codegen.leakgate)

1. **`src/codegen/leakgate.py`** — the one leak gate, ported from the D1 harness's
   pull_and_run report cell: harvested terms (file names / stems, sheet names, the
   header cells of rows 1–2, the column-A/B values below), the static denylist loaded
   BY PATH (`CODEGEN_LEAKGATE_DENYLIST`, else `<state root>/leakgate/denylist_local.txt`
   — the volume; never in the repo), the filter (> 5 characters, not an English word,
   not an IIG template sheet / column, not harness vocabulary; static terms never
   dropped), word-boundary matching for harvested terms and substring for static ones,
   self-match exclusion (a hit wholly inside the report's own label phrases), per-hit
   records (file, class, sha256, occurrences, pair index — never the term), `redact`,
   and the lane (`approved` only with zero real hits AND a clean scrub check, else
   `held`). The English-word list is wordfreq when installed, else the **repo-token
   dictionary**: the tracked text files of `src/` (templates included), `ui/` (the
   built `dist/` excluded) and `docs/`, never `fixtures/`, every file the LEAK_LEDGER
   baseline lists left out whole and any token whose hash is a ledger hash dropped; no
   git (D1's workspace) = the same scope walked on disk, `.gitignore` honoured.
2. **Callers.** `tools/iig_diff.py --export-scrubbed` builds the gate's denylist
   (`--gate-pairs DIR`, `--gate-denylist FILE`), masks every gate term and passes only
   when `leakgate.scan` of the written files finds no real hit (else the evidence files
   are deleted, `rescan` = `gate_<class>` counts); its dictionary is the gate's
   (`GATE_SCOPE` = src ui docs; post74's fixtures-inclusive guess and the PROVISIONAL
   header are gone; the `.gitignore` helpers moved into leakgate).
   `scripts/scrub_check.py`: the gate's static list joins the local term file, the
   ledger is read by `leakgate.read_ledger`, and `--leak-gate PAIRS_DIR path ...` runs
   the whole gate (counts only, exit 1 on a real hit). The container runner
   (`scripts/container_harness.py`, next commit) calls it; its private gate script is
   deleted. The cluster's pull_and_run notebook still has its own copy.
3. Tests: `tests/test_leakgate.py` (synthetic), `tests/test_iig_diff_export.py` (+2;
   three post74 assertions moved to the post75 scope).

## 0.5.8.post74 — 2026-10-19 (D1 post73 12-pair report: extractor fixes, landing key, export vocabulary, model usage)

From acfc-results `run_20261019T193332Z_fe61bc4` (timestamp 181043Z). Each item has a
synthetic fixture reproducing the coordinate-only line (`tests/post73_pairs.py`).

1. pair_05 (`required element missing (role column) … col 15`): conventions profile
   `skip_row_markers` (default "do not map", "not mapped", "n/a"; read with
   `extractor.unmapped_markers`). A row whose stage column reads one — or is blank while
   another target column / data type cell reads one — is out before the required-element
   checks; ONE `skipped_rows:feeds[i]` flag per feed with the count and the cells (it
   replaces the per-row `field_unmapped` flag of a marked row).
2. pair_06 (`audit column invalid (… type timestamp)`): `codegen.extract.type_format`
   splits `timestamp(YYYY-MM-DD HH:MM:SS)` into keyword + format before the vocabulary
   check; a size (`decimal(18,2)`, `varchar(50)`) stays in the type. Contract:
   `AuditColumn.datatype_format`, `SttmField.stage_datatype_format` /
   `standard_datatype_format` (left out of the JSON when empty). IIG: the DateFormatRule /
   DateConversionRule INPUT_PARAM takes `<stage format>--<standard format>` from the type
   cells when no "Convert X to Y" rule states them; one format alone = open cell + NOTE.
3. pair_08 (`required element missing (role target_type) … col 17`): one row never fails
   the feed. No stage column = not a mapping row (counted in `skipped_rows`); a stage
   column without a data type = blocking `QUESTION feeds[i].columns[j].target_type`
   (j = the row among the sheet's field rows), cited by coordinates; the feed extracts
   without that column; `gaps:` answer fills it (`answered_cell` flag).
4. pair_10 (`Contract fails validation at STTM sheet 2`): `run_errors.CONTRACT_RULES` names
   every STTM contract rule with a disposition. QUESTION: value_unstated,
   value_outside_vocabulary, value_out_of_range, feed_without_audit_columns,
   recycle_unknown_column, segment_missing_on_fields, segment_without_table (the feed held
   back, one key each, e.g. `feeds[0].file_format`). FAIL: feed_without_fields,
   field_count_mismatch, load_rule_unknown_column, phi_mismatch, duplicate_feed_id,
   invalid_value — first line `contract validation: <rule> (<n>) at STTM sheet 2`,
   details in the full tier only. pair_10's shape (no file format anywhere) is now
   `QUESTION feeds[0].file_format`, exit 3.
5. Answer keys: `codegen.answer_keys.canonical_key` — a key's path is the role name
   (lowercase, `_`), never a header label. The layout stage normalises every path a model
   claims (pair_04's `feeds[0].Delimiter` came from a live claim under the label); the
   answers file is read through it, so both spellings answer.
6. Notebook paths: an open landing is asked ONCE per feed by the IIG cell's key
   `feeds[<i>].src_adls_path` (INPUT_NEEDED for the workbook; the same line blocking on a
   notebook run) — never `feeds.<feed>.notebook.<path>`. pair_11 vs pair_02: the paths
   derive from the FRD's landing location; pair_02's FRD states it, an FRD without an
   inbound path (Pyx, to confirm on D1) leaves all three open. The template's
   `landing_proposal` (ACFC overlay: `/inbound/{domain}/{sub_domain}/{source}/`, TODO D1:
   confirm against the corpus) is shown as an agent_proposal, never written. The answer
   (gaps: or inputs:) sets the landing; archive / reject follow.
7. `tools/iig_diff.py --export-scrubbed` keeps a token only when it is in the gate's
   repo-token dictionary (tracked text files of src fixtures config tools scripts + root
   files; no workbook cell text) — not the fixture-token universe. Harvested gate terms
   (the workbooks' sheet / file names + `--gate-terms FILE`) minus dictionary words /
   template names are masked and re-scanned (class `harvested_term`); static denylist =
   the local file + `CODEGEN_SCRUB_DENYLIST`. PROVISIONAL: a best guess at the gate's
   vocabulary from its reports (not its code), said in the SELF_CHECK header; the D1 gate
   is not reproduced further. The pair_01 re-export needs the prod golden: run it on D1.
8. pair_11 556 s: live layout asks at most one request per document (all STTM sheets /
   roles in one; one for the FRD), never per feed or per path question — nothing to
   batch. Layer 2 (generate) is the per-feed one: one request per unmapped rule per feed.
   No before/after claimed. Every MODEL USAGE line now has a `CODEGEN-USAGE {json}`
   stderr marker (stage, provider, calls, requests, seconds, failed, recovered); STABLE
   readers `run_errors.model_usage(stderr, stdout)` / `usage_summary(entries)` for the
   harness report; run_round.py / acfc_run.py print it per stage.

Harness asks: stop a pair at an extract-sttm exit 3 (pairs 07 / 09); put
`usage_summary(model_usage(stderr, stdout))` on every stage's report line; pass the
harvested term list to `--gate-terms` for the scrubbed export.

## 0.5.8.post73 — 2026-10-19 (state refresh error without the SDK config dump)

1. `state_mirror.error_text`: a failed volume refresh is reported as the exception
   types + the error code only (`StorageError <- PermissionDenied, error code
   PERMISSION_DENIED`); the SDK message (its config dump: host, client id, auth type)
   reached the App log and the state line on the first post72 deploy. A missing volume
   folder is `StateDirNotFound` (`STATE_DIR_NOT_FOUND`).

## 0.5.8.post72 — 2026-10-19 (CODEGEN_STATE_DIR on a UC volume)

1. **`codegen.state_mirror`.** A Databricks App has no `/Volumes` mount, so a
   `CODEGEN_STATE_DIR=/Volumes/<catalog>/<schema>/<volume>[/…]` that is not a local
   folder is copied read-only through the Files API (`VolumeBackend` list + download,
   never a write) into `<tmp>/codegen-state-volume/current` (`CODEGEN_STATE_MIRROR_DIR`
   moves it); `config.state_root()` answers the copy for that value
   (`register_state_mirror`). Each copy is its own `gen-<sha>` folder swapped in by one
   atomic symlink rename. The App copies at import (before the config loads, so the
   volume's `overlays/<profile>.yaml` applies) and again before `POST /api/generate` /
   `POST /api/demo/run-live` (`main._refresh_state`; a changed copy reloads the
   config). A failed refresh keeps the previous copy; with none the root stays the
   volume path (`[MISSING]`). Job compute that mounts `/Volumes` reads the folder as is.
2. **State line + picker.** `state_dirs_line()` reads `codegen-state root: /Volumes/…
   (CODEGEN_STATE_DIR; volume) -> local copy … (N files, copied …)`; `display_path`
   shows a file in the copy as its volume path (picker source `profile
   /Volumes/…/environments/d1.yaml`).
3. **`app.yaml`** sets `CODEGEN_STATE_DIR=/Volumes/d1_dlk/codegen/state`; the grants
   are in `docs/ACFC_APP_ENV.md` §1. Test: `test_state_volume_mirror.py` (the fake
   Files API in `tests/storage_fakes.py`).

## 0.5.8.post71 — 2026-10-18 (SCHEMA_DRIFT_FLAG default back to N)

1. The ACFC overlay's SCHEMA_DRIFT_FLAG default is N again. The SD PROD rows, the
   SFMC reference IIG and the pair-1 golden all say N; the Y came from the SD
   test-cells sheet only. `feed_overrides.<feed_id>.schema_drift_flag` stays, to set
   Y on a feed whose golden says Y. docs/acfc/OPEN_QUESTIONS.md §6 is unchanged (its
   "Now" bullet describes post70). Decided: no live SD run at home; D1 via Genie is
   the verification.

## 0.5.8.post70 — 2026-10-18 (scrub: split storage account; TGT_PRIMARY_KEY from a key signal only; v2's IIG-driven cells)

1. **Scrub (`scripts/scrub_check.py`):** a storage account written apart from its host
   (a notebook's `STORAGE_ACCOUNT = "<account>"`; `adls_uri()` joins them at run time)
   is now a hit, class `client_storage_account`. Two sources: every `storage_account`
   of a loaded environment profile (the config's `environments:` blocks, the profiles
   directory, the tracked examples), and any `storage_account_pattern` token assigned
   to `STORAGE_ACCOUNT`. SYN-shaped accounts (`syn…`) and `<<…>>` placeholders never
   hit, so the tracked tree stays at 68 hits / 18 rows. A notebook generated inside
   ACFC still carries the real account (it must, to run); the harness's scrub now
   catches it before anything leaves.
2. **TGT_PRIMARY_KEY (iig_v2, `primary_key_input: true` in acfc_env.yaml;
   `codegen.primary_key`):**
   - **The contract now has two lists.** `load_rules.not_null_columns` is the
     required columns; `load_rules.natural_key` comes only from Primary Key / Key
     cells. They used to be one list. The FRD's Primary Key / Natural Key /
     Business Key row is read as `FrdFeed.key_statement`.
   - **Where a proposal can come from.** Only an explicit signal: the STTM's
     Primary Key cells, the FRD's key statement, the FAQ's `natural_key_columns`,
     or a corpus row for the same target table. The not-null list never proposes
     a key.
   - **A proposal is shown, not applied.** It appears on `INPUT_NEEDED
     feeds.<feed>.primary_key` and in the cell's NOTE. It is written only on an
     explicit choice (`choice: use_default`, a typed column list, or Confirm in
     the App), and then flagged `key_from_contract`.
   - **No signal on a merge load (Upsert / Merge):** ONE blocking `QUESTION
     feeds.<feed>.primary_key`, exit 3, with the not-null columns listed as
     candidates, none selected. Without a merge, the cell stays blank.
   - **SFMC shape** (standard Upsert, no key cell) now asks this question.
   - **Unchanged:** the v1 notebook and iig_v1 keep their not-null-list keys, now
     named as such in the code (docs/acfc/OPEN_QUESTIONS.md §5).
3. **Notebook v2: the cells v1 had, only where an IIG cell states them.**
   - `SCHEMA_DRIFT_FLAG = Y`: a drift cell before the stage. A missing column stops
     the run before any write; extra columns are counted.
   - `RECYCL_ENBL_FLG = Y`: a recycle cell. Rejects are kept in RECYCL_TBL_NM at
     RECYCL_ADLS_PATH and retried with the next run's records until
     RECYCL_RETN_DAYS days have passed. An open cell, or a retention that is not a
     whole number of days, stops the run at the config cell.
   - Always, a final run-report cell: row counts per step and the DQ rule counts,
     appended to `<stage catalog>.<TGT_DATABASE_NAME>.<feed>_run_report`
     (`_dryrun` under dry_run).
   - A merge row whose TGT_PRIMARY_KEY is open or NA stops the run at the config
     cell (`notebook_iig_cell_open`); nothing is appended silently.
   - PHI masking has no IIG cell, so v2 has none (OPEN_QUESTIONS.md §4, for Aruna).
   - `tools/notebook_parity.py` reports these stages as "IIG-driven" (the cell,
     its value, whether v2 has the cell) and keeps "only v1" for stages no IIG cell
     states. A differing file-name pattern is reported as expected (v2 writes the
     IIG's SRC_FILE_NAME).
4. **SCHEMA_DRIFT_FLAG defaults to Y** in the ACFC overlay (`family_conventions`),
   to match the SD golden. It was N from round 6. A feed whose golden says N sets
   the new `feed_overrides.<feed_id>.schema_drift_flag: N` (docs/acfc/OVERLAY_FIELDS.md).
   The sources disagree; the question for Aruna is docs/acfc/OPEN_QUESTIONS.md §6.
   The SD parity run now generates the drift cell on all three feeds.

## 0.5.8.post69 — 2026-10-18 (notebook v2 for acfc_prx; v1 unchanged elsewhere)

1. **Selection:** `conventions.profiles.<p>.notebook_version` — `v1` (the default,
   unchanged) | `v2`; acfc_prx = v2. The App's badge reads "Output: Notebook —
   notebook: v2 (acfc_prx)".
2. **Source of truth = the IIG rows** the workbook emitter produced (the same feed
   contract, environment profile, overlay and answers). On a notebook-only run the
   framework emit runs into a scratch folder: nothing of it is persisted, but its
   gate checks and flags count for the notebook (a derivation-gate FAIL quarantines
   the notebook). The notebook states no value the IIG does not; the storage
   account is the one value from the environment profile. Jinja only, no model call.
3. **Files:** `<feed>/notebook/<slug>.ipynb` (nbformat 4.5) and `<slug>.py` (a
   Databricks notebook source: `# Databricks notebook source`, `# COMMAND ----------`,
   `# MAGIC %md`) — the manifest's `notebook_emit` stage. **Harness:** the paths
   moved from `<feed>/<slug>.ipynb` + `pipeline/` to `<feed>/notebook/` for acfc_prx.
4. **Cells:** title · config (widgets `run_date` and `dry_run` only; `adls_uri()`) ·
   read (delimited from the ADLS_DELTA row, or fixed width from
   ADLS_FIXED_WIDTH_HANDLER; MANDATORY_FIELD_LIST rejects) · stage · standard · DQ
   (one call per DATA_QUALITY_RULES row through a registry: DateFormat, DataTypeCast,
   LRTrim, DateConversion, NullCheck, DeDuplication, AddCustomColumns,
   LoadHeaderAndTrailerToSeparateTables; any other RULE_CLASS — e.g. the Custom
   ReferentialCheckRule — is a markdown "rule not implemented" cell and a
   `notebook_rule_not_implemented` flag) · a provenance cell per stage (IIG sheet /
   row; STTM `sheets[i]` rows, FRD `tables[t]` row / col — coordinates only) · run ·
   review-only Layer-2 candidates (markdown; omitted when empty). The writes happen
   in the run cell, after the DQ rules (the rules must run before the data lands).
   `dry_run` (default true) reads 100 rows and writes `*_dryrun`; nothing archived.
5. **A cell the notebook needs and the IIG leaves open** stops the run at the config
   cell (`OPEN_CELLS`) and is a `notebook_iig_cell_open` flag (e.g. SEGMENT_FILTER on
   a multi-segment fixed-width feed without confirmed record-type discriminators).
6. **Checks at generate time:** nbformat validate (flagged not-run where nbformat is
   absent — a dev dependency), every code cell compiles, ruff on the .py, the scrub
   (no ADLS host literal, no address other than the configured notification list).
   App and CLI write byte-identical notebooks.
7. **`tools/notebook_parity.py`** reports v1 vs v2 on a pair (cell counts, stages,
   constants that differ; values only with `--show-values`).

## 0.5.8.post68 — 2026-10-18 (the notebook path made honest; cell layout unchanged)

One commit per item, mock only, synthetic fixtures. The notebook's cells are
laid out as before (session B changes them).

1. **A blocking line withholds the notebook.** A feed with a blocking line open
   (its own, or a run-level one such as a required environment value) writes no
   `.ipynb`, `pipeline/*.py` or `job/*`: one `NOTE feeds.<feed>.notebook — not
   written — …` line names the keys. On a notebook-only run its emit artefacts go
   too and the manifest entry says `written: false` (`notebook_withheld: n`);
   next to Framework the workbook is still written for review (post58). CLI and
   App ask the required environment values whatever the output mode.
2. **One input set.** The owed inputs, the input choices and the answers file's
   `run.environment` (+ `environment.<key>`) apply on a notebook run exactly as on
   a framework run: the same open lines and counts.
3. **Manifest:** `CODEGEN_STAGES.json` has a `notebook_emit` stage (`.ipynb`,
   `pipeline/*.py`, `job/*`; PASS / SKIPPED like the others); a crash mid-feed
   removes those files too. **Harness:** read the notebook paths from
   `feeds[].artefacts.notebook_emit`, never a glob.
4. **The environment profile reaches the notebook** (`codegen.emit.notebook_env`):
   `feed_spec` states the stage / standard catalogs, the storage account, and the
   landing / archive / reject containers + container-relative paths (the IIG
   ADLS_DELTA row's own cells); `adls_uri()` builds the abfss:// address at run
   time. No `None` default, no account in a widget. A value the profile leaves
   unset (a catalog, the account, a container) or an unstated landing is a
   QUESTION on a notebook run (an INPUT_NEEDED for the same key turns blocking),
   so the notebook is withheld. A config with no environment block keeps the
   contract's values. The create_tables=false prerequisites list every standard
   table.
5. **Scrub:** an address an FRD notification requirement quotes (and its domain)
   becomes the configured `job.notification_emails` (`CODEGEN_NOTIFICATION_EMAILS`)
   before it reaches `job/workflow.json`; the notebook text spells no ADLS host.
6. **nbformat** is in the dev extra and `constraints/acfc_d1.txt` (5.11.1 — D1 to
   confirm); the suite validates every notebook it emits. **ACFC side:** reinstall
   `.venv-d1` with the constraints. The App's output toggles show the backend's
   per-profile default only (no Notebook fallback); the "notebook not validated for
   acfc_prx" badge stays.

SD mock run, same contracts + answers, notebook vs framework (home D1 profile, its
storage account a placeholder): both NEEDS_ANSWERS, run-level 1 blocking + 3
non-blocking, each feed 0 blocking / 5 non-blocking; the notebook path writes no
notebook (`written: false`). With a complete synthetic D1 profile: both
PASS_WITH_OPEN_INPUTS with the same counts, 3 notebooks written.

## 0.5.8.post67 — 2026-10-18 (live-run confirm dialog: measured, not a constant; generated files unchanged)

1. **Tokens are measured per call.** The FM API transport (`codegen.databricks.chat`,
   `usage=`) reads `prompt_tokens` / `completion_tokens` (cached prompt tokens from
   `prompt_tokens_details` count as cache reads); the Anthropic providers read
   `input_tokens` / `output_tokens` / `cache_read_input_tokens`. `StageUsage` carries
   `input_tokens`, `output_tokens`, `cache_read_tokens` next to `seconds` (the label,
   the report and the MODEL USAGE line are unchanged).
2. **Price table** `reasoning.prices`, model id -> $/MTok input, output, cache read, each
   row with its `source`: `anthropic` = `claude-opus-5-5` 4.00 / 20.00 / 0.20 ("anthropic
   list price, 2026-10-06"); `databricks_fmapi` = EMPTY, for this workspace's per-token DBU
   rate (shape in `config/config.yaml`). An FM API call is priced at the workspace's row
   when its model has one, else at the list price; a model with no row = no dollars.
   **ACFC side (optional):** fill `reasoning.prices.databricks_fmapi.claude-opus-5-5` in
   the overlay with the workspace's rate and a `source`; the record is re-priced at once.
3. **The App keeps the last `demo.run_history_size` (10) live runs per (conventions
   profile, generate outcome)** in the state role (`live_run_history.json`,
   `ui/backend/run_history.py`): calls, live-call seconds, wall-clock, tokens, cost.
   Wall-clock = run start to end minus the time spent waiting on a pairing / layout
   dialog. Kept outcomes: PASS, PASS_WITH_OPEN_INPUTS (completed) and NEEDS_ANSWERS,
   GATE_FAIL (stopped); CRASHED, FAIL, a run that ended with no outcome, and mock runs
   are not recorded.
4. **The confirm dialog shows ranges from the COMPLETED runs**, wall-clock first: "typically
   1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at Anthropic list price; Databricks bills in
   DBUs" ("at this workspace's rate" once that row exists) + "Measured from N runs
   (profile P; <the price row's source>)". From five runs on, the fastest and slowest are
   left out of each range. Under 3 completed runs: "no history yet for completed runs".
   Stopped runs, when any exist, are a second line: "runs that stopped for answers:
   typically 20–40 s". The record keeps each run's per-stage provider / model / tokens,
   so the dialog prices it at the CURRENT table.
   No token counts = calls + wall-clock only, no dollars. `demo.estimated_calls / estimated_cost_usd / estimated_seconds` and the status
   `estimates` are gone (status `live_history`).

## 0.5.8.post66 — 2026-10-16 (artefacts panel review summary; generated files unchanged except the report's wording)

1. **Artefacts panel, per feed:** the bold sheet-count line is one review summary,
   e.g. "8 sheets · 17 rows · 9 open inputs (1 blocking) · empty by rule:
   FILE_ADLS (MFT), FIXED_WIDTH (delimited)". The derived ratio left the panel.
   - "empty by rule" lists only empty sheets, each with its reason:
     `FrameworkArtefacts.empty_by_rule` (FILE_ADLS = MFT from the rule-3 note; the
     fixed-width handler = delimited for a delimited file); short names in
     `metadata_template.EMPTY_BY_RULE_LABELS`.
   - Open inputs = the feed's open lines + the run-level ones
     (`GenerateRun.review_open`), attached by the App after the run. At home the
     one blocking line is `run.environment.storage_account` (D1's placeholder).
2. **Generation report:** the "badge coverage" row became the labelled line
   "cells derived from documents: <d> of <t>; the rest are profile defaults,
   framework-assigned blanks, or open inputs", under the per-sheet "IIG rows".

## 0.5.8.post65 — 2026-10-16 (Dashboard: two deprecated sections removed; App only)

One commit per item. Nothing else on the Dashboard moved; generated files are unchanged.

1. **Metadata-sheet preview removed** (tabs, table, coverage line, Download .xlsx,
   footnote): `MetadataSheetPanel`, its types / CSS, and the routes
   `GET /api/demo/metadata-sheet` and `/api/demo/metadata-sheet.xlsx`.
   `codegen.metadata_sheet` stays (the generator and `codegen demo-metadata-sheet`
   use it).
2. **"Publish to Unity Catalog volume" removed** (controls and the volume /
   credentials text): `DatabricksPublishPanel`, its types, and the routes
   `GET /api/databricks/publish-target` and `POST /api/databricks/publish`.
   Publishing stays on the CLI (`codegen databricks-publish`); the documents /
   fetch routes are unchanged.

## 0.5.8.post64 — 2026-10-16 (App wording; text only)

1. **Output toggle tooltip (App).** "Framework artefacts" now reads "DDL +
   BSA-annotated IIG for the existing ingestion framework" (was "DDL scripts +
   config rows + inserts …").

## 0.5.8.post63 — 2026-10-16 (approval wording; text only, the same files are written)

One commit per item.

1. **Metadata-sheet preview footnote (App).** It no longer describes the config
   rows and the insert SQL as the approval path. It now says the BSA-annotated
   IIG is the approval artefact and the CI/CD pipeline applies the DDL after
   approval: the artefacts panel's sentence (one constant, `artefacts.ts`
   `APPROVAL_NOTE`).
2. **Generation report.** "Framework output (Option B)" is now "Framework
   artefacts", with the same sentence. Its file table lists the files the App
   presents (`framework.presented_files`: the DDL, the IIG, its review copy,
   ADDITION.md); the DML / `metadata_inserts.sql` line is gone. Row counts read
   "IIG rows: <sheet>".

## 0.5.8.post62 — 2026-10-16 (App cleanup for the demo; no generator behaviour change)

One commit per item.

1. **Generate panel.** The "Source files this run will read" section was removed,
   along with its convention-check table (fed by the same request), the
   "In the Databricks workspace" disclosure, their state, the `api.sourceFiles()`
   request and the `GET /api/demo/source-files` route. Nothing else on the panel
   moved. The payload builder `codegen.demo_sources.source_files_payload` (used by
   `codegen demo-source-files`) is kept.
2. **Framework artefacts panel.** Each feed now shows exactly four files:
   `<FEED>_DDL.txt`, `<feed>_IIG.xlsx`, `<feed>_IIG_REVIEW.xlsx` and
   `ADDITION.md` (`ui/frontend/src/artefacts.ts`). `metadata_inserts.sql`,
   `config_rows.xlsx` and `config_inserts.xlsx` are still generated; the App no
   longer lists them.
   - Heading: "Framework artefacts".
   - Subtitle: the BSA-annotated IIG is the approval artefact; the CI/CD
     pipeline applies the DDL after approval.
3. **ADDITION.md** (template text only; the same files are written). It now has
   three sections:
   - the file table: the DDL, the IIG, the IIG review copy and ADDITION.md itself;
   - "Review flow": IIG → BSA review → the CI/CD pipeline applies the DDL;
   - "Framework-assigned IDs left blank", one per line.

   Nothing mentions inserts or config rows any more: the "By target system" and
   "Switches" blocks are gone.
4. **FRD picker default: none chosen.**
   - The demo contract is never preselected.
   - If the STTM has a match in the pair index, that FRD is preselected and
     labelled "paired" (status `frd_paired`, frd-choices `current.paired`).
   - A chosen STTM with no chosen or paired FRD disables Generate, with the reason
     shown. The run refuses with "no FRD chosen for <STTM>", unless the FRD
     pairing is still landing or will be asked.
   - Only when no STTM is chosen does a run fall back to the configured demo
     pair.
   - The `frd_warning` flag is gone.
   - Test: `test_frd_default.py`.
5. **The STTM picker lists only STTMs.** The existing content classifier
   (`classify_workbook`) gains the kinds `iig` and `iig_review`. A workbook with
   at least two IIG template sheets is an IIG; with the `REVIEW_SUMMARY` sheet as
   well, it is the review copy.
   - Only the App's document worker passes the template sheet names; the CLI's
     pair folders classify as before.
   - The chooser leaves both kinds out of the STTM and VDD lists, as well as any
     workbook with an `iig` token in its name (the existing name rule).
   - Index verdicts are stamped `classifier: 2`. An older verdict of
     "unclassified" is read again once, so IIGs cached before this change also
     drop out.
   - Test: a folder with 2 STTMs and 2 IIGs lists 2 (`test_m93_chooser.py`).

## 0.5.8.post61 — 2026-10-16 (two kinds of default: profile_default / agent_proposal)

- **profile_default** — the value comes from the conventions profile or the ACFC
  overlay. It is written when the run gives no answer: source `profile` in
  `CODEGEN_STAGES.json`, no gate flag and no open INPUT_NEEDED line (so it does
  not count toward PASS_WITH_OPEN_INPUTS). It is still listed as changeable: a
  `NOTE` line on the console, an `applied:` entry in `answers_template.yaml`
  (`choice: naming_standard` + `standard:` changes it) and the App's panel.
  - The email status set: back to the overlay's `email_status_default` (else every
    template row) when unanswered. With the overlay saying [Success, Failed] and
    no answer, the workbook gets two rows.
  - EMAIL_TO: the overlay's literal default (open while it is a `<<D1:…>>`
    placeholder, as before).
  - The notebook NAME per leg (`notebook_name.file_to_stg` / `.stg_to_std`, the
    `corpus_cells` value for the feed's notebook kind) and the ADLS SRC_FILE_NAME
    style (`src_file_name_style`: pattern | prefix_star | prefix_middle). These
    were already applied from the profile; they are now also listed and
    changeable. A changed notebook name leaves DATABRICKS_NOTEBOOK_PATH as the
    profile's (said in the cell's tooltip).
- **agent_proposal** — the value is rendered or derived by the agent: the
  PIPELINE_NAME template, APPLICATION_NAME from SOURCE, ACTIVE_START_DATE (no
  default). Unchanged from post59: shown, never written until chosen.
- An owed cell's kind is its new `default_kind`; unset, a default with a `{token}` is
  an agent proposal, a literal one a profile default. The committed overlay sets
  EMAIL_TO `profile_default`, APPLICATION_NAME `agent_proposal`; the email status
  rule is `profile_default`.
- Manifest: `feeds[].inputs.<key>.kind`. The App's `inputs_needed` items carry
  `kind` / `applied`; the panel counts only open inputs and lists applied
  profile defaults as "profile default applied … — changeable". The console's
  `ANSWERS FILE` line and the template header no longer count them (nor the
  shared pipeline_name entry) as needed.
- Tests: `tests/test_default_kinds.py` (the two-row status set, the agent
  proposals in the same run, EMAIL_TO, notebook names / style, changing each,
  the kind rule) and an `InputsNeededBanner.test.tsx` case. Updated:
  `test_overlay_fields.py`, `test_framework_owner_rules.py`,
  `test_iig_corpus_cells.py`, `test_environments.py`,
  `test_open_inputs_outcome.py` (the run-level open inputs are now 3, not 4).

## 0.5.8.post60 — 2026-10-16 (the App writes CODEGEN_STAGES.json; one generate entry point)

- **One feed pipeline.** `codegen.cli.generate_feed_result` is the feed
  pipeline of both the CLI and the App. `ui.backend.service.GenerationStore.
  _generate_feed` wraps it in a FeedRun instead of mirroring the CLI step by
  step. The App now gets the CLI's `iig_cells` and check order.
- **One run bookkeeper.** `codegen.generate_run.GenerateRun` is driven by both
  `codegen generate` (`cli._run_pairs`) and the App's live run
  (`DemoRunner._generate_specs`). It records:
  - the run-level lines (`run_level_lines`), held-back feeds and values no
    document states;
  - the BSA's choices and each feed's owed inputs / LOB question;
  - CRASHED (partial files removed) / GATE_FAIL (files quarantined +
    GATE_FAIL.md) / written;
  - the outcome and `<out root>/CODEGEN_STAGES.json`.

  The manifest (questions with `blocking`, `written`, `open`, `inputs`,
  `iig_cells`, the outcome) is identical from both.
- **App run states read the manifest.** The run's `outcome` (also on
  `GET /api/demo/status`) and each feed's `written` decide the state; nothing
  is inferred from which feeds returned. A run with no written feed is
  needs_answers when the outcome is NEEDS_ANSWERS, else failed. A GATE_FAIL
  feed is now quarantined in the App too, and its listed files point under
  `quarantine/`.
- Test: `tests/test_generate_entry_point.py`. It runs the App and the CLI on
  the same synthetic pair and checks the manifests are byte-identical (the
  manifest carries no timestamp), unanswered and with a confirmed choice, plus
  a GATE_FAIL quarantined by the App.

## 0.5.8.post59 — 2026-10-16 (PIPELINE_NAME three-way choice; file-name tie-break)

- **A defaulted input is a three-way choice** (`codegen.input_choices`): every
  `pipeline_name.<flow>` (grand_master / master / file_to_stg / stg_to_std, per
  feed) and APPLICATION_NAME, EMAIL_TO and the email status set where a default
  exists (ACTIVE_START_DATE has none).
  - `use_default`: the proposal. For PIPELINE_NAME this is the conventions
    profile's per-flow `pipeline_name_templates` over {domain} {subdomain}
    {source} {frequency} {layer} {load_mode}, shown with its template.
  - `naming_standard`: the BSA's template in the same syntax. One template for
    the feed renders all four names.
  - `leave_blank`.
- **Proposed is not applied** (Aruna's rule holds for every unattended run:
  CLI, harness, an App run with no confirmation).
  - An unanswered run writes the cell BLANK. Its non-blocking INPUT_NEEDED line
    shows the proposal and its template.
  - A cell is filled only on an explicit choice: the answers file's `choice:` /
    `standard:`, or Confirm in the App. A chosen default / standard raises the
    "taken from other documents" flag (`frd_unstated:<TAB>.<HEADER>[<flow>]
    source_used:…`).
  - Behaviour change: an unanswered APPLICATION_NAME is now blank (it was
    written with the feed's SOURCE), and an unanswered email status set writes
    every template row (`email_status_default` is a proposal).
  - `CODEGEN_STAGES.json` records each input's `source` per feed entry
    (`inputs`): default | standard | blank | answer, with `chosen`, `proposed`
    and `template`.
- **Templates.** The repo ships SYNTHETIC placeholders (`SYN_PL_…`, labelled
  "no naming standard loaded — placeholder" in the CLI line and the App). The
  real templates come from `codegen-state/overlays/acfc_prx.yaml`, overriding
  per flow (`docs/acfc/OVERLAY_FIELDS.md`).
- **Collisions.** A proposal that collides with a PIPELINE_NAME of the loaded
  goldens / corpus (`pipeline_name_corpus`; the committed overlay lists
  `docs/acfc/iig_goldens`) is never offered — the line asks instead, without
  printing the colliding name.
- **App.** The inputs panel shows radios (resting on use_default), the
  proposal beside its template, one naming-standard box per feed with a live
  preview of all four names, and Confirm (`POST /api/demo/input-choices`). Only
  confirmed choices reach the next Generate.
- **File-name recognizer.** A tie between files is broken by source priority
  (`file_tie_source_priority`: the FRD's landed pattern over an STTM
  FILE_DETAILS label …), then by shape (`file_tie_shape`: a vendor prefix + an
  extension). The BSA's answer is cached in the STTM layout profile
  (`file_choices`), so the next run of the same workbook takes it.
- `docs/acfc/OPEN_QUESTIONS.md` §3: Aruna's "blank" vs Venu's "default +
  standard", resolved as BSA-chooses-with-default-shown. Attach-a-document
  path deferred.
- Tests: `test_pipeline_name_choice.py`, `test_file_tie_break.py`,
  `InputsNeededBanner.test.tsx`.

## 0.5.8.post58 — 2026-10-15 (outcome PASS_WITH_OPEN_INPUTS; blocking per question)

- **New generate outcome `PASS_WITH_OPEN_INPUTS`** (exit 0): the workbook was
  written and every open line is non-blocking (`INPUT_NEEDED` only). The console
  prints an `OUTCOME` line with the counts (for NEEDS_ANSWERS too).
  `run_stages.OUTCOMES`, most severe first: CRASHED, FAIL, GATE_FAIL,
  NEEDS_ANSWERS, PASS_WITH_OPEN_INPUTS, PASS.
- **`CODEGEN_STAGES.json` lists every open line.** `questions: [{line, key,
  scope, blocking}]`:
  - `QUESTION` / `UNRESOLVED` are `blocking: true`. In the App these are
    "Answers needed" and the "required (blocking)" environment values.
  - `INPUT_NEEDED` is `blocking: false` (the App's "not blocking").

  Each generated feed's entry gains `written: true|false` and `open: {blocking,
  non_blocking}`.
- **NEEDS_ANSWERS (exit 3) = at least one blocking line open, whether or not a
  workbook was written.** A workbook with an empty storage account is not
  deployable, so the harness number never calls it a pass. Exit 3 as before for
  the unset required environment value (mock and live) and pair_12's
  `lob_by_file`; their workbooks are marked `written: true` so the App can still
  show them. One change: without `--feed`, a held-back feed's QUESTION used to
  leave the run at exit 0 (printed for information); it is now exit 3 too, with
  the ready feeds' workbooks written.
- **`run_stages.pair_outcome(steps, out_root)`** (STABLE; the post56 report
  noted it was missing). It returns a pair's outcome as the worst of its steps'
  exit codes. Generate's status comes from the manifest when the manifest's
  `exit` matches that step. `acfc_run.py`'s summary prints it as `outcome`.
  Test: `tests/test_open_inputs_outcome.py`.

## 0.5.8.post57 — 2026-10-15 (D1 post55 report: leak keys, unstated values, path whitespace, scorer)

From acfc-results `run_20261015T172048Z_3e09149` and the pair_01 scrubbed diff
(`run_20261015T193331Z_3e09149`). One commit each, synthetic fixtures only.

- **Answer keys name sheets by position.** All 10 post55 leak hits were sheet
  names inside `needed_answer_keys`. Every key on stdout is now
  `sheets[<i>]/<layer>/<role>` (0-based workbook position, like `feeds[<i>]`;
  the coordinates tier's `STTM sheet <i+1>`), band keys too:
  `sheets[<i>]/band[<n>]/layer`. The name stays ACFC-side: the answers
  template's `sheet_name:` reading aid and `unresolved_headers.md`. An answers
  file may give `sheet: "sheets[2]"` or the name; an unknown position is a NOTE,
  never applied elsewhere (`codegen.layout.sheet_refs`).
- **A value no document states is NEEDS_ANSWERS, not a FAIL** (pairs 03 / 04).
  A feed whose every mismatch is `value.unstated` exits 3 with one
  `QUESTION feeds[<i>].<field>` per value, citing the contract field and the
  places searched (vocabulary only); the other feeds of the pair still
  generate. `generate --answers` (gaps:) fills the value
  (`frd_unstated:<field> source_used:user`). Two documents stating different
  values stay a FAIL.
- **Stated paths** (pair_01's `derivations [path_whitespace 19]` all came from ONE
  FRD landing cell copied with its label, `Path : <account>/<container>/<folder>`):
  - *Label stripping.* An FRD cell `<Label> : <value>` whose label is a synonym of
    the field being read (conventions profile `field_label_synonyms`: landing
    path / folder / location, file name, frequency, delimiter) is read as
    `<value>`, flag `label_stripped` with the FRD table / row. A label that is
    not a synonym of that field is never stripped.
  - *The environment's address.* A landing that starts `<account>/<container>/`
    (the account matching the profile's `storage_account_pattern`) or an abfss
    URI takes account and container from the run's environment profile; the
    folder under the container stays the document's, byte for byte. A different
    document account / container raises `environment_mismatch` naming the field
    and "document states another environment" — never the document's value.
  - *Whitespace* (switch `path_whitespace: keep | fail`, default `keep`): a
    stated path keeps its whitespace byte for byte, and each path cell gets ONE
    flag `iig_path_whitespace:<SHEET>!<A1> (<COLUMN>) — double space | leading |
    trailing | tab` for the BSA to confirm; `fail` = the old check. On the
    pair_01 shape: the D1 address, one `label_stripped`, one
    `environment_mismatch`, zero whitespace flags.
- **iig_diff, four rules** (re-scored: pair_01 export 3.2 → 28.3, see
  `docs/acfc/iig_exports/pair_01_post55/RESCORE.md`):
  (a) an identity carrying a NAME (TGT_TABLE_NAME / TGT_TABLE / @file) that
  differs, both sides one feed and one flow: leftover rows pair by feed + flow +
  row order — the name is one mismatch cell; (b) agent-template columns the
  golden lacks are `template-only` (not scored, listed once under HEADERS);
  (c) `9999-12-31` == `9999-12-31 00:00:00`; (d) segment codes through the
  profile's new `segment_codes` (hddr / det / trlr == header / details /
  trailer). `tools/iig_rescore_export.py` re-scores a scrubbed export at home
  (the post56 scorer reproduces the export's 3.2 exactly on the rebuilt pair).
- **Extraction error lines say what kind of thing.** "STTM required element
  missing" / "STTM audit column invalid" now carry `(role <role>; type
  <keyword>)` — the header role in the template vocabulary and the type keyword
  in the framework type vocabulary, both allowlisted (`run_errors.ROLE_WORDS`,
  `TYPE_KEYWORDS`; anything else is dropped or `other`).
- **Not in this release:** pair_05 / pair_06's own fixes wait for Genie's answer
  on the segment-code vocabulary (rule (d) above).

## 0.5.8.post56 — 2026-10-15 (IIG cell counts per feed; one environment resolver)

- **IIG cell counts.** pair_11 (4 feeds) and pair_12 (1 feed) printed the same
  nine "unpopulated" numbers because the harness counted one workbook for both.
  Its metric (empty cells of each sheet's used range) matches the generator's
  own SD workbook exactly, so the counter was right but the file was wrong.
  Each feed now writes its own counts to `CODEGEN_STAGES.json`
  (`feeds[].iig_cells`; read them with `codegen.run_stages.iig_unpopulated(out_root)`),
  per sheet over the rows the generator wrote:
  - `open_for_bsa`: empty cells that the inputs panel asks about (an owed-cell
    or environment NOTE);
  - `empty_other`: every other empty cell;
  - `template_blanks`: the old number, kept for this release only.
  
  `open_inputs` lists the input keys behind the `open_for_bsa` cells. One
  input can leave several cells open (`run.email_to` on each status row), so
  cells ≠ inputs. The harness should read these per feed instead of scanning a
  workbook.
- **Environment resolution.** The App and the CLI share one resolver,
  `codegen.environments.resolve`. Precedence: explicit file >
  `<state root>/environments/<name>.yaml` > the overlay block > unset
  (INPUT_NEEDED, or a QUESTION for a required key). Every field records its
  source, and the picker shows it.
  
  The 10:07 mismatch came from where `codegen-state/` was looked up: next to
  the code. The App runs a staged copy with no `codegen-state/` (gitignored, so
  `databricks sync` skips it). New App setting **`CODEGEN_STATE_DIR`**: copy
  `codegen-state/` into the staged tree and point the variable at it
  (`docs/ACFC_APP_ENV.md`). The App logs `codegen-state root: …` at startup,
  with `[MISSING]` after any folder it cannot see.

## 0.5.8.post55 — 2026-10-15 (D1 post51 12-pair report: the extraction failures)

From acfc-results `run_20261015T074546Z_97fe673`. Each fix has a synthetic
reproduction of the pair's exact error line (`tests/post51_pairs.py`).
- **pair_05**: a Segment column of `NA` / `-` / blank no longer FAILs "outside
  the Header/Detail/Trailer vocabulary". New `extractor.discovery.
  unsegmented_markers` (`na`, `n/a`, `-`, `none`, `null`): a sheet whose Segment
  cells are only these (or blank) is unsegmented, with a contract note. The
  segmented path needs one real segment word, and a marker beside one still
  FAILs at its coordinates.
- **pair_06**: a flag / indicator audit column (`*_FLAG`, `*_IND`) may be
  `tinyint` / `int` / `smallint` / `boolean`; every other audit column stays
  `string` / `timestamp`. The sets are conventions-profile fields
  (`audit_datatypes`, `audit_flag_datatypes`, `audit_flag_suffixes`;
  `docs/acfc/OVERLAY_FIELDS.md`), so an overlay widens them. Framework DDL
  renders `DELETE_FLAG TINYINT`.
- **pairs 08–10**: F2 FRDs whose Solution Requirement tables carry no caption
  are now read. A table counts as one by its row labels (`extractor.frd.
  solution_requirement_labels` / `_required_labels` / `_min_labels`), with the
  caption as a second signal. `codegen layout` prints `NOTE frd/family — F2
  signal: <header-row fingerprint | caption> — table(s) [...]`. The section row
  is found when the caption row is missing, and labels may sit after a blank
  first column. An F2 feed whose tables name no section lists its required
  fields as unresolved, never an empty feed. "Cannot be read" now names the
  table COUNT and each table's header-row fingerprint (12 hex of `term_sha256`
  over row 0), never a title: `… at FRD: 12 tables, header-row fingerprints …`.
- **pairs 03 / 04**: the count-only mismatch summary (post52 / post53) is
  confirmed end to end: `contract mismatch, feed 1 of 1: 2 tables only in FRD`.
  It stays FAIL for now. The FRD carries no column list, so the set differences
  are tables / segments, and which kinds become NEEDS_ANSWERS waits for these
  two pairs' counts under post55.
- **pair_01**: the gate is unchanged. On a FAIL, the full report (ACFC-side)
  lists the flags grouped by type, and stdout prints `GATE_FLAGS <type> — n`.
  The pushed line carries counts only: `… (failed checks: derivations
  [path_whitespace 9]; flags by type: path_normalised 9, …)`. `GATE_FAIL.md`
  gains the findings-by-rule table and the D1 step to score the quarantined
  workbook (`tools/iig_diff.py … --export-scrubbed`).
- **pair_03 at 109 s**: no stage scales with the column count (a 330-column
  synthetic pair takes about 5 s under mock), and no model call runs per column.
  The MODEL USAGE line now carries the live calls' seconds (`· 2 call(s) in
  97.3s`), so the next D1 run shows which stage spent them.

## 0.5.8.post54 — 2026-10-15 (generate: CRASHED vs GATE_FAIL)

Two failure outcomes of the generate stage, exit code 1 for both
(`codegen.run_stages.OUTCOMES`; CODEGEN_STAGES.json `stages.generate.status`):
- **CRASHED** (an exception mid-write: a template gap, an uncaught error): the
  feed's partial emit files are deleted and the emit stages SKIPPED, as post52.
  An uncaught crash now writes the manifest before the error propagates.
- **GATE_FAIL** (files complete, the correctness gate said no): every file the
  feed wrote is KEPT, moved byte for byte to `<output>/<feed>/quarantine/` (same
  relative paths) beside a `GATE_FAIL.md`. That file lists the failed checks and
  the flag counts per type, with no names or values (those stay in the run's full
  report, ACFC-side). The emit stages report PASS, and the manifest says
  `generate: {status: GATE_FAIL, label: "complete, gate failed, review only",
  quarantine: [...]}`, with each feed's artefact paths under `quarantine/`.
  `tools/iig_diff.py` still scores the quarantined workbook: its build stamp is
  3 folders up, within the 5 it searches. Generating the feed again clears its
  old quarantine. Console: `GATE_FAIL      <feed> — complete, gate failed,
  review only: N file(s) moved to …`.
- **FAIL** (nothing written: a contract mismatch, no feed matching `--feed`):
  emit stages SKIPPED.
- The App's own generate path (`ui/backend/service.py`) does not quarantine yet;
  it can read the same outcome from `CODEGEN_STAGES.json` for CLI runs.

## 0.5.8.post53 — 2026-10-15 (addendum 4: derived values never reach the error line)

Feed slugs, work-dir paths and contract keys are generated, not harvested, so the
leak gate cannot see them. The coordinates tier (`first_error_line`) already
printed none (it is built from vocabulary + integers); post53 makes what it prints
for them useful:
- **Contract mismatch = counts on the first line**, e.g. `contract mismatch,
  feed 1 of 1: 2 tables only in FRD, 1 table only in STTM`. Every resolver
  mismatch item is tagged by kind (`resolver.mismatch_item`; labels in
  `run_errors.MISMATCH_LABELS`). Names count once, so three segments naming one
  table are 1 table. `ContractMismatchError.counts` rides the marker.
  The full message's first line carries the same summary.
- **A feed is `feed N of M`**: the mismatch coordinate now uses the original
  FRD feed object (the gap chain had replaced it, so it read `pair 1 of 1`).
- **A path is `<workdir>/pair_07/…`** (`run_errors.path_hint`: only a harness
  `pair_NN` folder survives), e.g. `contract not found: STTM <workdir>/pair_07/…`.
- Column names were already coordinates (the post52 raise-site audit).

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
