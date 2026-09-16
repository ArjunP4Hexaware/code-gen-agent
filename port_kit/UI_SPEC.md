# UI_SPEC — the demo UI of the CodeGen agent, rebuilt as a Databricks App

**Target decision.** The rebuilt UI is a single-page Databricks App written in Streamlit
(fallback: Dash, same screens) — ONE Python source file plus the app configuration file
Databricks Apps requires. The generator built in slices S1–S6 is a plain Python package in the
same workspace folder; the UI loads it in-process. There is no separate API server, no build
step, no JavaScript. Inputs are read from a Unity Catalog Volume folder the app configuration
points at; every output of a run is written to a Volume path the app configuration points at,
and downloads are served from there. Layer 2 runs its deterministic mock provider (SPEC 5.2)
in the demo build; no model endpoint is needed.

This document describes what the user sees and does and what the app must call. It does not
describe the reference implementation's architecture. Where it names a rule, the rule lives in
`SPEC.md` (the generator) and is cited by section number; nothing here redefines generator
behaviour.

Conventions: `<<name>>` is a variable span; verdict names are exactly `PASS`,
`PASS_WITH_FLAGS`, `FAIL`; the "three files" are, per feed, `<<feed_slug>>_stage_table_creation.txt`,
`<<feed_slug>>_standard_table_creation.txt` and `config_rows.xlsx` (SPEC header table).

---

## 1. Purpose and the demo flow

The app lets an engineer turn one approved pair of documents — an FRD contract and an STTM
mapping workbook — into the three deployment artefacts the ingestion framework needs, with a
computed gate verdict beside them. The engineer picks the pair from the input folder (or
uploads it), the app inspects the pair and lists the feeds it contains, and the engineer answers
the load-pattern questions for each feed, leaving any question unanswered on purpose. One click
runs the generator; the stages appear in order as they start. The results screen shows
`PASS` / `PASS_WITH_FLAGS` / `FAIL` per feed, every flag with the text it rests on, a preview of
each of the three files, and a download button per file plus one for everything. Nothing is
invented, nothing is merged: an unanswered question, a rule the compiler could not map and a
framework-assigned identifier all stay visible as flags or blanks, never as guesses.

---

## 2. Screens

The app is one vertical page in four numbered sections, each in its own expander-style panel;
the section for the current state is open, earlier sections stay open but disabled, later ones
are collapsed. A thin caption under the title reads exactly:
`Layer 1 deterministic · Layer 2 mock provider (review-only candidates) · verdict computed in code, never by judgment.`

DEMO screens first (§2.1–§2.4), then the FULL screens as notes in §8.

### 2.1 Screen 1 — Pair selection  [DEMO]

```
┌─ 1 · Choose the pair ───────────────────────────────────────────────────────────┐
│ Input folder: /Volumes/<<catalog>>/<<schema>>/<<inputs_volume>>/     [Rescan]   │
│                                                                                 │
│ FRD contract           STTM workbook                Standards                   │
│ ┌────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐  │
│ │ (select one)     ▾ │ │ (select one)          ▾ │ │ ☑ Client Data           │  │
│ │  syn_widget_frd    │ │  syn_widget_sttm.xlsx   │ │   Engineering Naming +  │  │
│ │  syn_sensor_frd    │ │  syn_sensor_sttm.xlsx   │ │   Coding Standards      │  │
│ │  syn_segmented_frd │ │  syn_segmented_sttm.xlsx│ │   (preselected, from    │  │
│ └────────────────────┘ └─────────────────────────┘ │   configuration)        │  │
│ [Upload FRD contract…] [Upload STTM workbook…]     │   documents: 2 present  │  │
│  uploads land in <<inputs_volume>>/uploads/         └─────────────────────────┘  │
│                                                                                 │
│ ⚠ These names do not look like a pair — the FRD feeds must name the workbook's  │
│   stage tables (SPEC 1.4). Inspect anyway; a mismatch fails loudly.             │
│                                                                                 │
│                                                        [Inspect pair]           │
│ ┌─ Pair inspection ──────────────────────────────────────────────────────────┐  │
│ │ Extracted: syn_widget_sttm.contract.json — 2 feed(s)                       │  │
│ │ feed_id            stage tables                        standard   rules    │  │
│ │ syn_widget_risk    stg_syn.syn_widget_risk             syn.…      1        │  │
│ │ syn_gadget_events  stg_syn.syn_gadget_events, …_recycle syn.…      5        │  │
│ └────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows |
|---|---|---|---|---|
| Input folder caption | text | always | — | the resolved Volume folder path; a red line `Input folder is not readable: <<message>>` when the listing fails (§7) |
| Rescan | button | not running | re-lists `<<inputs_volume>>/frd/`, `/sttm/`, `/uploads/` | refreshed dropdowns; `No FRD contracts found` / `No STTM workbooks found` when empty |
| FRD contract | dropdown | not running | stores the pick in session state; clears any inspection | names of `*.contract.json` files (and JSON files whose content validates as an FRD contract, SPEC 1.6) sorted by name, plus `(select one)` first; uploads show a `· uploaded` suffix |
| STTM workbook | dropdown | not running | same | names of `*.xlsx` files, Excel lock files (`~$` prefix) skipped |
| Upload FRD contract… | file uploader (accept `.json`, cap 25 MiB) | not running | validates the content as an FRD contract; writes it to `<<inputs_volume>>/uploads/<<name>>` (renamed to end in `.contract.json`); selects it | success line `Uploaded and selected <<name>>`; on failure the red line `not a valid FRD contract: <<first validation line>> — run the FRD→STTM agent to produce one` (§7) |
| Upload STTM workbook… | file uploader (accept `.xlsx`, cap 25 MiB) | not running | writes to `<<inputs_volume>>/uploads/<<name>>`; selects it | same pattern; a non-`.xlsx` file is refused with `an STTM upload must be a .xlsx workbook, got <<name>>` |
| Standards | checked, disabled checkbox + caption | always | — | the configured standards status text (SPEC 0.1 `engineering_standards.status`) and the count of standards documents present in `<<inputs_volume>>/standards/`; when the status starts with `STUB` the caption turns amber and reads `standards are a stub — the run will flag it` |
| Pair warning | amber line | both picked and the FRD file stem and workbook stem share fewer than 3 underscore-separated name parts | — | the text in the wireframe; informational only, nothing auto-corrects |
| Inspect pair | primary button | both picked, not running | calls extract then resolve (§4); on success state → `inputs-ready` | the Pair inspection card; on failure the hard-fail shape of §2.3 with the extract or resolve message, state stays `idle` |
| Pair inspection card | table | after a successful inspection | — | the extracted contract file name, feed count, and one row per resolved feed: `feed_id`, stage tables (qualified), standard table (or `none — stage-only`), validation-rule count |

Rules of this screen: nothing is preselected except the standards; the pick is explicit
(doctrine 9 of the reference UI: "choices are explicit; nothing auto-picks"); the pair warning
is a suggestion, never a block; an FRD is never offered in the STTM dropdown and vice versa
(folders are separate; the uploader validates the kind).

### 2.2 Screen 2 — FAQ (load-pattern questions)  [DEMO]

Rendered once per resolved feed, as one tab per feed in feed order. Every question is a
dropdown whose options are the SPEC 1.8 allowed values plus the literal option
`(unanswered)`; the generator's default value is shown in the caption so the engineer sees
that an unanswered question still has a working default. A prefilled answer (SPEC 1.8
"contract prefill") is preselected and marked `prefilled from the contract` with its evidence.

```
┌─ 2 · Load-pattern FAQ ──────────────────────────────────────────────────────────┐
│ [ syn_widget_risk ] [ syn_gadget_events ]                                       │
│                                                                                 │
│ Answers are written to <<run_dir>>/faq/<<feed_slug>>.faq.yaml and read by the   │
│ generator (SPEC 1.8). Unanswered questions are flagged, never guessed.          │
│                                                                                 │
│ question                value                     source      evidence          │
│ load_mode               [ truncate_and_load    ▾ ] [contract] stage_target.load_│
│   prefilled from the contract — change the value to override it   strategy: "…" │
│ is_master_file          [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: unknown                                                              │
│ dedup_within_file       [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: none                                                                 │
│ existing_record_policy  [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: unknown                                                              │
│ load_frequency          [ monthly              ▾ ] [contract] Monthly Run; file │
│   prefilled from the contract — change the value to override it   received by… │
│ target_tables_exist     [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: yes                                                                  │
│ reject_threshold        [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: none                                                                 │
│ data_integrity_checks   [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: none                                                                 │
│                                                                                 │
│ Companions (not questions, never flagged):                                     │
│ has_header  [ (unanswered) ▾ ] [engineer▾] [______]  has_trailer [ (unanswered) ▾ ] [engineer▾] [______]
│                                                                                 │
│ 2 answered by the contract · 0 answered here · 6 unanswered → 6 flags           │
│                                                            [Save answers]      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows |
|---|---|---|---|---|
| Feed tabs | tabs | `inputs-ready` or later, not running | switch feed | one FAQ form per feed |
| load_mode | dropdown: `(unanswered)`, `truncate_and_load`, `append`, `merge_on_keys` | not running | stores the answer | prefill when the FRD stage load strategy maps (SPEC 1.8 row 1) |
| is_master_file | dropdown: `(unanswered)`, `yes`, `no` | not running | — | caption `default: unknown` |
| dedup_within_file | dropdown: `(unanswered)`, `none`, `row_level`, `by_keys` | not running | — | caption `default: none` |
| existing_record_policy | dropdown: `(unanswered)`, `plain_append`, `skip_if_exists`, `delete_and_insert` | not running | — | caption `default: unknown` |
| load_frequency | dropdown: `(unanswered)`, `daily`, `weekly`, `monthly`, `yearly`, `adhoc` | not running | — | prefill from the FRD frequency text (SPEC 1.8 row 5) with the whole frequency text as evidence |
| target_tables_exist | dropdown: `(unanswered)`, `yes`, `no` | not running | — | caption `default: yes` |
| reject_threshold | dropdown: `(unanswered)`, `none`, `number…` (a number box appears when chosen) | not running | — | caption `default: none` |
| data_integrity_checks | dropdown: `(unanswered)`, `none`, `not_null_keys`, `custom` | not running | — | caption `default: none` |
| Source (one per row) | dropdown: `engineer` (default) / `frd`; read-only `contract` on a prefilled row the engineer has not changed | not running, value set | the `source` written for that answer | choosing `frd` makes the row's evidence box required |
| Evidence (one per row) | text box | not running, value set | stored as `evidence` on that answer | empty allowed for `engineer`; a prefilled row shows the prefill's evidence read-only |
| has_header / has_trailer | dropdowns: `(unanswered)`, `yes`, `no`, each with its own source and evidence | not running | companions (SPEC 1.8 companions table) | caption `companion — sets HEADER_FLAG` on has_header |
| Summary line | text | always | — | `<<n>> answered by the contract · <<k>> answered here · <<m>> unanswered → <<m>> flags` where m counts the eight questions only |
| Save answers | button | not running | writes the FAQ file(s) (§5 rules); state → `inputs-ready` (unchanged) | `Saved <<feed_slug>>.faq.yaml` or `No answers set — the generator will use defaults and flag every question` |

Writing rules (the generator's contract, SPEC 1.8): a prefilled answer the engineer did not
change is NOT written (the generator re-derives it, so the banner counts it "from contract");
only answers set on this screen are written, each as a mapping with `value`, `source` and,
when given, `evidence`; the values `yes`, `no` and any number are written quoted so YAML keeps
them as text; when the engineer set nothing for a feed, no file is written for that feed (the
banner then reads `defaults (no FAQ file)` exactly as in ACCEPTANCE S1 case 3). `(unanswered)`
is never written; it means "absent", and the gate flags it as `faq_unanswered:<<question>>`.

### 2.3 Screen 3 — Run  [DEMO]

```
┌─ 3 · Generate ───────────────────────────────────────────────────────────────────┐
│ Output mode: framework artefacts (the three files per feed). Layer 2: mock      │
│ provider, zero model calls. Tests: skipped (the verdict says so).               │
│ Run id: run_20260116_143000  →  /Volumes/<<catalog>>/<<schema>>/<<outputs_volume>>/runs/run_20260116_143000/
│                                                                                 │
│                                                             [Generate]          │
│                                                                                 │
│ ✓ extracting workbook — syn_widget_sttm.xlsx → STTM mapping contract (FRD: syn_widget_frd)
│ ✓ resolving contracts — syn_widget_frd ⋈ extracted contract                     │
│ ✓ syn_widget_risk: compiling rules                                              │
│ ✓ syn_widget_risk: Layer-2 reasoning                                            │
│ ✓ syn_widget_risk: emitting code                                                │
│ ✓ syn_widget_risk: framework artefacts                                          │
│ ✓ syn_widget_risk: gate                                                         │
│ ⋯ syn_gadget_events: compiling rules                                            │
│                                                                                 │
│ ┌ RUN FAILED — nothing was written for the failed scope ───────────────────┐    │
│ │ resolving contracts — contract mismatch for feed 'syn_gadget_events':    │    │
│ │   - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days   │
│ │ The FRD and the STTM disagree; nothing here is guessed. Fix the document  │    │
│ │ that is wrong and inspect the pair again.                                 │    │
│ └───────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows |
|---|---|---|---|---|
| Run settings caption | text | always | — | the three fixed facts (framework output mode, mock Layer 2, tests skipped) and the run id + output path the run WILL use; the id is minted when Generate is pressed |
| Generate | primary button | `inputs-ready`, not running | mints `<<run_id>>`, copies inputs and FAQ files into the run directory, runs the stages (§4) synchronously, writes outputs to the Volume; state → `running` → `done-pass` / `done-flags` / `failed` | the stage list below, filling in as stages start; the button reads `Generating…` and is disabled while running; every control of screens 1–2 is disabled while running |
| Stage list | status list | `running` or later | — | one line per stage in this exact order and wording: `extracting workbook` → `resolving contracts` → per feed `<<feed_slug>>: compiling rules` → `<<feed_slug>>: Layer-2 reasoning` → `<<feed_slug>>: emitting code` → `<<feed_slug>>: framework artefacts` → `<<feed_slug>>: gate` → `publishing results` (detail `<<n>> feed(s), <<m>> failure(s)`); the mark is `✓` for a finished stage, `⋯` for the one in progress, `✗` for the stage that raised; the detail text after ` — ` is the one shown in the wireframe for the first two stages |
| Hard-fail card | red panel | `failed` | — | title `RUN FAILED — nothing was written for the failed scope`; line 1 = the stage name, ` — `, the generator's message verbatim (multi-line messages keep their lines and indentation); line 2 = one fixed sentence per error family (§7); a `Back to the pair` button that returns to `inputs-ready` without clearing selections |
| Per-feed failure rows | amber lines inside the stage list | a feed raised a template gap while other feeds continued (SPEC 5.4) | — | `✗ <<feed_slug>> — template gap: <<message>>`; the run continues and ends `done-flags` or `done-pass` for the other feeds, with the failed feed listed on the results screen as `FAIL` (§2.4) |

Stage semantics: the first two stages tick when the corresponding generator call returns
(extract, resolve). The per-feed stages tick as the generator reports them when the S1–S6
build exposes a progress hook; when it does not, the UI shows the five per-feed lines at once
with `⋯` on the first, and flips all five to `✓` when the per-feed call returns (see §4, gap
G2). Either way the names and order above are what the presenter narrates.

### 2.4 Screen 4 — Results  [DEMO]

```
┌─ 4 · Results — run_20260116_143000 ─────────────────────────────────────────────┐
│ ┌───────────────────────────────────────────────────────────────────────────┐   │
│ │ ⚑  PASS_WITH_FLAGS   syn_widget_risk — 2 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok
│ └───────────────────────────────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────────────────────────────┐   │
│ │ ⚑  PASS_WITH_FLAGS   syn_gadget_events — 10 flag(s); ruff=ok, …           │   │
│ └───────────────────────────────────────────────────────────────────────────┘   │
│ Run verdict: PASS_WITH_FLAGS (worst of the feeds)      [Download all (zip)]     │
│                                                                                 │
│ [ syn_widget_risk ] [ syn_gadget_events ]                                       │
│                                                                                 │
│ Flags (2) — needs a human                                                       │
│ ┌ name                    │ trigger                      │ cited text ────────┐ │
│ │ load_mode_not_enforced  │ FAQ load_mode is declared    │ declared            │ │
│ │                         │ (answered or prefilled)      │ truncate_and_load;  │ │
│ │                         │                              │ writer MERGE-by-file│ │
│ │ generated tests were    │ tests skipped in this run    │ —                   │ │
│ │ skipped                 │                              │                     │ │
│ └─────────────────────────┴──────────────────────────────┴─────────────────────┘ │
│ Gate checks: ruff ok · debug_patterns ok · secrets ok · test_per_module ok      │
│                                                                                 │
│ ▸ Stage DDL — syn_widget_risk_stage_table_creation.txt        [Download]       │
│   ┌────────────────────────────────────────────────────────────────────────┐    │
│   │ -- FRD contract: syn_widget_frd sha256 3f0a…                           │    │
│   │ -- STTM contract: STTM mapping contract extracted from …               │    │
│   │ CREATE OR REPLACE TABLE stg_syn.syn_widget_risk (                       │    │
│   │   widget_id STRING COMMENT 'Widget identifier',                         │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│ ▸ Standard DDL — syn_widget_risk_standard_table_creation.txt  [Download]       │
│ ▸ IIG config rows — config_rows.xlsx                          [Download]       │
│   [DATA_FACTORY_PIPELINE_SCHEDULE 2] [ADLS_DELTA_INGESTION_DETAILS 1] [STGDELTA_STDDELTA_INGESTION_DET 1]
│   [DATA_QUALITY_RULES 2] [DATABRICKS_NOTEBOOK_DETAILS 1] [EMAIL_TEMPLATE_CONFIG 1] [ALL_FILES_STATIC_INFORMATION 1]
│   ┌ PIPELINE_ID │ PIPELINE_NAME               │ … ┐                              │
│   │             │ WF_DLK_NSP_SYN_WIDGET_RISK… │   │                              │
│   └─────────────┴─────────────────────────────┴───┘                              │
│   Framework-assigned IDs left blank: PIPELINE_ID, PARENT_PIPELINE_ID, … — the    │
│   agent never invents them.                                                     │
│ ▸ Report — report.md                                          [Download]       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows |
|---|---|---|---|---|
| Verdict banners | one coloured banner per feed (§9 colours) | `done-*` | — | icon, verdict, then the S6 console line for the feed verbatim: `<<feed_id>> — <<n>> flag(s); <<check list>>` (SPEC 5.4); a feed that failed with a template gap shows a red `FAIL` banner with `<<feed_id>> — template gap: <<message>>` and no previews |
| Run verdict line | text | `done-*` | — | `Run verdict: <<worst>> (worst of the feeds)` where FAIL > PASS_WITH_FLAGS > PASS |
| Download all (zip) | download button | `done-*` | builds a zip in memory of every file under `<<run_dir>>` (§5) | file name `<<run_id>>.zip` |
| Feed tabs | tabs | `done-*` | switch feed | the per-feed panels below |
| Flags table | table | flags ≥ 1 | — | one row per flag in report order (SPEC 5.3 order) with three columns derived by the table below; heading `Flags (<<n>>) — needs a human`; when there are none: `No flags — every rule compiled deterministically and every question is answered.` |
| Gate checks line | text | always | — | `<<name>> ok` / `<<name>> FAIL` per check, in report order |
| Stage DDL expander | expander, open by default | always | — | the file name, a Download button, and the whole `.txt` in a monospace block (no wrapping, horizontal scroll) |
| Standard DDL expander | expander | always | — | same; for a stage-only feed the file is the six-line banner followed by the single line `-- No standard-layer table for this feed (stage-only load).` (ACCEPTANCE S2 case 3) and the expander caption reads `stage-only feed — no standard tables` |
| IIG expander | expander | always | — | a tab strip in WORKBOOK ORDER (SPEC 4.0: the seven tabs, then `_provenance` and `_inputs` inside a nested `service sheets` expander), each tab label suffixed with its data-row count; the active tab renders as one table with the header row verbatim and one row per data row; empty cells render empty; the line `Framework-assigned IDs left blank: <<always_blank headers>> — the agent never invents them.` under the strip; the Download button gives the workbook bytes as produced |
| Report expander | expander, collapsed | always | — | the report markdown rendered as text, Download button |
| Candidates expander | expander, collapsed | candidates artifact present | — | one card per entry of `candidates.json` (SPEC 5.2): kind (`CONFIRM` or `Layer 2`), rule text, provider, grounded yes/no, rationale or detail, the citation(s) in quotes; read-only, no approve/reject in the demo (§8) |

Flag row derivation (from the flag text alone, plus the candidates artifact for citations;
SPEC 5.3 numbering):

| Flag text starts with | name column | trigger column | cited-text column |
|---|---|---|---|
| `faq_unanswered:` | `faq_unanswered` | `FAQ question <<question>> has no answer` | the question name and its generator default (SPEC 1.8) |
| `load_mode_not_enforced:` | `load_mode_not_enforced` | `FAQ load_mode is declared (answered or prefilled)` | the rest of the flag text after `: ` |
| `standards_stub:` | `standards_stub` | `standards status starts with STUB` | the status text |
| `rule classified ` | `rule classified <<class>>` | `rule text classified <<class>> by the deterministic compiler` | the repr'd rule text and, after ` — `, the note |
| `confirm item pending` | `confirm item pending` | `document-derived CONFIRM item (segmented feed)` | the item text, and under it the `citation` field of the matching candidates entry (kind `confirm`) |
| `Layer-2 provider failed` | `Layer-2 provider failed` | `provider raised; candidate recorded without a response` | the rule text and the failure notes |
| `Layer-2 candidate NOT grounded` | `Layer-2 candidate NOT grounded` | `a citation is not verbatim contract text` | the rule text and the failure notes |
| `Layer-2 candidate pending engineer approval` | `Layer-2 candidate pending` | `grounded candidate awaits an engineer` | the rule text and the `citations` of the matching candidates entry |
| `generated tests were skipped` | `generated tests were skipped` | `tests skipped in this run` | `—` |

Matching a flag to a candidates entry: same `rule_text` (Layer 2) or the item text equal to the
entry's `rule_text` (CONFIRM). When the artifact is absent or no entry matches, the cited-text
column shows the flag's own text and the caption `citation not recorded`.

---

## 3. State machine

| State | Meaning | Screen 1 controls | Screen 2 controls | Generate | Results |
|---|---|---|---|---|---|
| `idle` | app opened; no complete pair, or the last inspection failed | dropdowns, uploads, Rescan, Inspect pair (when both picked) enabled | hidden | disabled | hidden (a previous run's results, if any, are reachable through FULL run history only) |
| `inputs-ready` | inspection succeeded; feeds listed | enabled (any change returns to `idle` and clears the FAQ forms) | enabled; Save answers enabled | enabled | hidden |
| `running` | Generate pressed; stages in progress | all disabled | all disabled | disabled, reads `Generating…` | hidden; stage list visible |
| `done-pass` | every feed `PASS` | enabled | enabled | enabled (a new run id is minted; §5 rerun rule) | shown, green banners |
| `done-flags` | at least one feed `PASS_WITH_FLAGS`, no `FAIL` | enabled | enabled | enabled | shown, amber banners |
| `failed` | the run raised before any feed completed (extract, resolve, or every feed failed), or any feed is `FAIL` (a failed gate check or a template gap) | enabled | enabled | enabled | when at least one feed completed: shown, with red banners for the failed feeds; otherwise hidden, the hard-fail card (§2.3) shown instead |

Transitions:

| From | Event | To |
|---|---|---|
| `idle` | Inspect pair succeeds | `inputs-ready` |
| `idle` | Inspect pair raises | `idle` (hard-fail card shown under screen 1) |
| `inputs-ready` | any selection change on screen 1 | `idle` |
| `inputs-ready` | Save answers | `inputs-ready` |
| `inputs-ready` | Generate | `running` |
| `running` | extract or resolve raises, or no feed completes | `failed` |
| `running` | every feed completes | `done-pass` when all verdicts are `PASS`; `done-flags` when none is `FAIL` and at least one is `PASS_WITH_FLAGS`; `failed` when any is `FAIL` |
| `done-*` / `failed` | Generate | `running` (new run id) |
| `done-*` / `failed` | Back to the pair / selection change | `inputs-ready` / `idle` |
| any | app container restarts | `idle` (selections lost; runs on the Volume survive) |

Session state holds: the two picks, the inspection result (feed list), the FAQ answers per
feed, the current run id, the stage list, and the results index (verdict, flags, file paths
per feed). Nothing else is remembered between reruns of the script.

---

## 4. Contract with the generator

Every call is in-process against the S1–S6 package. Signatures are prose; names are what the
UI expects to exist in some spelling. "Errors surfaced how" names the §7 shape.

| Call | Inputs (type, where from in the UI) | Returns | Errors surfaced how | In S1–S6? |
|---|---|---|---|---|
| extract(workbook_path, frd_path, out_contract_path, generated_date) | the two picked files copied into `<<run_dir>>/inputs/`; out path `<<run_dir>>/inputs/<<workbook stem>>.contract.json`; generated_date = today (ISO date) | the mapping contract file, plus the extract summary `<<n>> feed(s): <<feed_id>> (<<k>> fields), …` (SPEC 5.4) | any parse/pairing error (SPEC 1.1–1.4) → hard-fail card, stage `extracting workbook`, family "workbook" | yes — S1 (readers) |
| resolve(frd_path, contract_path) → feed specs | the FRD file and the extracted contract | a list of feed specs; the UI reads from each: `feed_id`, `feed_slug`, stage tables (qualified), standard table or none, validation-rule count, stage load strategy, frequency text | validation error or contract mismatch (SPEC 1.5–1.7, 5.4) → hard-fail card, stage `resolving contracts`, family "pair" | yes — S1 |
| faq_prefills(feed spec) → the eight answers after contract prefills (SPEC 1.8) with `value`, `source`, `evidence` each, computed as if no FAQ file existed | the feed spec from resolve | the eight answers; the UI preselects those with source `contract` | none expected | yes — S1 (FAQ loader + prefills); the UI calls it with an empty FAQ directory |
| generate_feed(frd_path, contract_path, feed_spec, faq_dir, out_root, output_mode = framework, dry_run = true, skip_tests = true, on_stage optional) | run-directory paths; `faq_dir` = `<<run_dir>>/faq/`; `out_root` = `<<run_dir>>/out/` | the files SPEC defines under `<<out_root>>/<<feed_slug>>/framework/` (the three files), `<<out_root>>/<<feed_slug>>/candidates/candidates.json` when candidates exist (SPEC 5.2), and `<<run_dir>>/reports/<<feed_slug>>.md` (SPEC 5.5); RunResult fields the UI assembles: `verdict` (the `**Verdict: …**` line), `flags[]` (the `- ` bullets of the `Flags:` block, in order), `checks[]` (the `## Gate` table rows → name + pass/FAIL), `output_paths[]`, `candidates[]` (the artifact) | a template gap → per-feed `FAIL` row (SPEC 5.4, "that FEED only"); any other exception → hard-fail card, stage = the feed's current stage, family "generator" | files: yes — S1–S5. **G1:** no structured in-process result object is specified; the UI reads the files. **G2:** no progress hook is specified; §2.3 states the fallback |
| summary_line(feed result) → the S6 console line for one feed | the RunResult | `<<VERDICT padded to 15>> <<feed_id>> — <<n>> flag(s); <<checks>>` | — | yes — S6 (format); the UI may format it itself from RunResult |
| list_folder(volume_path) / read_file / write_file / list_standards | app-side, via the workspace Files API with the app's identity (§6) | names, bytes | listing/write failures → §7 rows 1 and 5 | not a generator call |

Gaps in the first kit exposed by this contract (also in the checkpoint report): G1 and G2
above. Neither blocks S7: the S5 report and the SPEC 5.2 artifact carry every field the results
screen needs, line-exact; the stage list degrades honestly without a hook. A rebuild MAY add a
thin in-process wrapper that returns RunResult and calls `on_stage` — it must not change any
file the S1–S6 acceptance cases pin.

---

## 5. Files and storage

| Item | Location / rule |
|---|---|
| Input folder | `/Volumes/<<catalog>>/<<schema>>/<<inputs_volume>>/` with sub-folders `frd/` (FRD contracts), `sttm/` (workbooks), `standards/` (the two client standards documents and the reference IIG workbook), `uploads/` (from-device uploads, both kinds; the uploader writes here) |
| Configuration | one configuration file next to the source file, holding every SPEC 0.1 knob plus the four UI knobs: inputs Volume path, outputs Volume path, run-id prefix (`run_`), upload cap in MiB (25) |
| Run directory | `/Volumes/<<catalog>>/<<schema>>/<<outputs_volume>>/runs/<<run_id>>/` where `<<run_id>>` = `run_` + local time `YYYYMMDD_HHMMSS` at the moment Generate is pressed |
| Run directory layout | `inputs/` (copies of the FRD, the workbook, the extracted `<<workbook stem>>.contract.json`), `faq/<<feed_slug>>.faq.yaml` (only feeds with answers), `out/<<feed_slug>>/framework/` (the three files), `out/<<feed_slug>>/candidates/candidates.json` (when present), `reports/<<feed_slug>>.md`, `run_meta.json` (frd name, workbook name, output mode, standards status, started/finished timestamps, per-feed verdict) |
| The three files, names | `<<feed_slug>>_stage_table_creation.txt`, `<<feed_slug>>_standard_table_creation.txt`, `config_rows.xlsx` — exactly as the generator writes them; never renamed |
| Where the generator runs | on the app container's local disk under a temporary run folder; on completion the UI copies the whole run folder to the Volume run directory (the Files API has no local mount guarantee); downloads are served by reading the Volume copy back, so what the user downloads is what is on the Volume |
| Rerun | every Generate mints a new `<<run_id>>`; nothing under a previous run id is ever overwritten or deleted; the same pair run twice yields two directories whose three files are byte-identical except the FAQ sha span when answers differ (SPEC 2.2) |
| Download all | `<<run_id>>.zip` built in memory from the Volume run directory, same relative paths |
| Zero retention of client data on the container | the temporary run folder is deleted after the copy; nothing is cached across sessions |

---

## 6. Databricks Apps specifics

The app configuration file (the one Databricks Apps requires next to the source) declares
three things. First, the run command: the Streamlit launcher followed by the single source
file name; the platform injects the port and Streamlit binds to it without any code. Second,
two resources of type Unity Catalog volume, one named for inputs with the "can read"
permission and one named for outputs with the "can read and write" permission; the app
reads their resolved paths from environment values the configuration maps from those
resources (the `valueFrom` mechanism) — never a hard-coded path. Third, the environment
values the generator honours: the force-mock switch set to `1` so Layer 2 never calls a model
in the demo build (SPEC 5.2 provider selection), and the notification list pinned to the
synthetic address from SPEC 0.1 so no client value can leak into an artefact.

The app's service principal must hold read on the inputs Volume and read-and-write on the
outputs Volume; declaring the resources grants those permissions declaratively. No SQL
warehouse, no serving endpoint and no secret are needed for the demo build; a serving-endpoint
resource is only added when live Layer 2 is switched on (§8). All Volume access goes through
the workspace Files API with the app's own identity; the UI never assumes a local mount of
`/Volumes`, and never uses the viewing user's token.

Because the app is one source file with a requirements file listing the generator's few
dependencies (a YAML reader, an Excel writer, a template engine, a data-model library) and the
generator package sits in the same folder, it deploys without a build step: sync the folder,
deploy the app, open the URL. Container restarts wipe local disk and Streamlit session state;
that is why every run lives on the Volume and why the state machine returns to `idle` after a
restart with runs still downloadable through the FULL run-history screen.

Streamlit reruns the whole script on every widget interaction; the run itself executes
synchronously inside the click handler with a status container that appends stage lines as
they start, so no background thread, no polling and no long-held request is involved. Expect
the generator to take seconds per feed; the status container is the progress indicator.

---

## 7. Error and empty states

| Situation | Where | What the user sees (exact) |
|---|---|---|
| Input folder unreadable (permission, wrong path) | screen 1 caption | red line `Input folder is not readable: <<message from the Files API>>` and `Check the inputs Volume resource and the app's read permission.`; dropdowns empty; Inspect disabled |
| No pairs found (folder readable, no files) | screen 1 dropdowns | dropdown shows only `(select one)`; caption `No FRD contracts found in <<inputs_volume>>/frd/` and/or `No STTM workbooks found in <<inputs_volume>>/sttm/`; upload buttons stay enabled; Inspect disabled |
| Upload refused | screen 1 under the uploader | red line with the generator's or the uploader's message: `an STTM upload must be a .xlsx workbook, got <<name>>` / `not a valid FRD contract: <<first line>> — run the FRD→STTM agent to produce one` / `<<name>> exceeds the 25 MiB upload cap` / `<<name>> is empty` |
| Unparseable STTM (dialect not detected, missing band, unknown header, pairing failure) | hard-fail card under screen 1 (Inspect) or screen 3 (Generate) | title `RUN FAILED — nothing was written for the failed scope`; line 1 `extracting workbook — <<message>>` (the SPEC 1.1–1.4 message verbatim, e.g. `<<file>>: no mapping sheets found (prefix 'MAPPING-'); sheets present: [...]`); line 2 `The workbook could not be read as a mapping document; nothing was guessed. Fix the sheet the message names and inspect the pair again.` |
| Pair mismatch (validation error, contract mismatch) | same card | line 1 `resolving contracts — <<message>>` keeping the multi-line disagreement list; line 2 `The FRD and the STTM disagree; nothing here is guessed. Fix the document that is wrong and inspect the pair again.` |
| Generator raised (any other exception during a feed) | same card on screen 3 | line 1 `<<feed_slug>>: <<stage>> — <<exception type>>: <<message>>`; line 2 `The generator stopped; nothing was written for this feed. The run directory keeps what earlier feeds produced.`; the run id and its Volume path are shown so the partial output can be inspected |
| Template gap on one feed | amber row in the stage list + red `FAIL` banner for that feed on screen 4 | `✗ <<feed_slug>> — template gap: <<message>>`; other feeds continue |
| Volume not writable (copy to the run directory fails) | red card on screen 3 after the stages | title `OUTPUT NOT SAVED`; line 1 `writing <<run_dir>> — <<message from the Files API>>`; line 2 `The run completed on the container but could not be written to the outputs Volume. Check the outputs Volume resource and the app's write permission; download nothing until it is saved.`; state `failed`; results hidden |
| No flags on a feed | screen 4 flags panel | `No flags — every rule compiled deterministically and every question is answered.` (unreachable while tests are skipped, SPEC 5.4 — kept for honesty) |
| No candidates artifact | screen 4 candidates expander | `No Layer-2 candidates — every rule compiled deterministically for this feed.` |
| Standards status is a stub | screen 1 standards caption | amber `standards are a stub — the run will flag it` (the gate adds `standards_stub: <<status>>`) |
| Container restarted mid-session | whole page | the page loads in `idle`; a one-line notice `The app restarted; selections were cleared. Completed runs are on the outputs Volume.` |

Every generator message reaches the screen unchanged; the UI never paraphrases an error and
never hides one.

---

## 8. FULL scope — after the demo

| Screen / feature | Note (all "after the demo") |
|---|---|
| Run history | list `<<outputs_volume>>/runs/*` newest first with pair names, verdicts and timestamps from `run_meta.json`; "Open" loads a past run into the results screen read-only; incomplete runs (no `run_meta.json` finished stamp) are listed as `failed — not loadable` |
| Compare two runs | side-by-side of the three files with a line diff, sha spans masked (SPEC 2.2) |
| Batch run | run every pair the configuration lists and show the S6 summary block line-exact, with exit code |
| Layer-2 review queue | approve / reject / confirm per candidate; decisions stored per run id in a JSON file on the outputs Volume; re-click resets to pending; decisions never gate the verdict and never merge; status copy `Marked approved — merge into generated code remains a manual step` |
| Live Layer 2 | provider switch backed by a serving-endpoint resource; a cost confirmation dialog before any billed run (calls · cost · seconds from configuration); the provider name on every candidate card; the mock lock stays the default |
| Option A output (notebook + module tree) and the `.sql` sources, inserts workbook and addition note | output-mode toggle; notebook rendered cell by cell; file tree; shelved with the first kit (SPEC L16) |
| Reference-document checks | the input-requirements rows and the architecture-deck controls evaluated against the run, read live from the standards folder |
| Provenance badges on the IIG preview | one dot per cell with the seven badge labels and tints (SPEC 4.0), coverage line `<<d>> of <<t>> values derived from documents` |
| Publish to a client location | a confirm-gated copy of a run's artefacts to a chosen Volume path outside the app's own outputs Volume, refusing anything outside a configured writable prefix |
| Pairing suggestions from an upstream contracts table | "looks like a pair — confirm" chips, companion FRD fetch, never auto-pick |
| Guided tour | six steps ending on the human decision |
| Session management | per-user selections that survive a rerun of the script, multi-user isolation of run directories by user name |
| Rule table | every validation rule with its classification, generated feature and grounding span |

---

## 9. Visual conventions

| Element | Convention |
|---|---|
| Verdict colours | `PASS` green (a check icon), `PASS_WITH_FLAGS` amber (a flag icon), `FAIL` red (a cross icon); the label text always accompanies the colour; the same three colours are used nowhere else |
| Banners | full-width, the verdict word first in bold upper case, then the S6 console line in monospace |
| Stage list | monospace marks `✓` `⋯` `✗`, bold stage name, ` — detail` in the muted colour |
| DDL previews | monospace, no wrapping, horizontal scroll, the entire file (no truncation), light background, 12–13 px |
| IIG preview | tab order = workbook order: `DATA_FACTORY_PIPELINE_SCHEDULE`, `ADLS_DELTA_INGESTION_DETAILS`, `STGDELTA_STDDELTA_INGESTION_DET`, `DATA_QUALITY_RULES`, `DATABRICKS_NOTEBOOK_DETAILS`, `EMAIL_TEMPLATE_CONFIG`, `ALL_FILES_STATIC_INFORMATION`, then `_provenance`, `_inputs` under `service sheets`; headers verbatim (including `CRETAED_BY`); empty cells empty, never `NULL`; the whole table scrolls horizontally; numeric cells right-aligned |
| Flags table | three columns, monospace for the cited text, amber left border on rows whose name starts with `Layer-2 candidate pending` or `confirm item pending` (the human-in-the-loop rows) |
| Errors | red panel, title in upper case, the verbatim message in monospace, the fixed sentence in normal text |
| Empty states | centred muted sentence, no icon |
| Disabled controls | 55 % opacity with a tooltip naming why (`Choose both files first`, `A run is in progress`) |
| Type | system font 14 px for text; monospace for feed ids, file names, hashes, DDL, flags' cited text |
| Nothing hard-coded on screen | every number, name and quote on the page is read from the run on the Volume or from the configuration; the only fixed strings are the captions and sentences quoted in this document |
