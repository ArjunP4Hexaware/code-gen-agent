# UI_SPEC v2 — the CodeGen agent UI, rebuilt in full as a Databricks App

**Status of this document.** v2 replaces v1.1 outright. v1.1 retargeted the UI onto a
single Streamlit file and specified a "DEMO" subset; that instruction is withdrawn. The
rebuild is the FULL user interface of the reference frontend — every route, screen, modal,
panel and control, at the same fidelity. From v1.1 only two things survive because they are
new UI over existing inputs: the load-pattern FAQ screen (now §2.4.2 step 1.5) and the
Volume-folder pair picker (now inside the chooser modal, §2.4.4).

**Sources, in priority order.** (1) The reference UX specification transcribed from the
shipping frontend (version 0.3.5, transcribed 2026-09-11) — this document rebases it. (2) The
shipping frontend and backend source, diffed against that specification on 2026-09-16; no
UI commit landed after the transcription, and every remaining difference is listed in
§0.3 and carried into the screens below. (3) The reference App manifest. (4) v1.1 §2.1 and
§2.2 as noted. (5) `SPEC.md` and `ACCEPTANCE/S1–S6` — the generator the UI calls, cited by
section number; nothing here redefines generator behaviour.

**Companion documents.** `BACKEND_SPEC.md` carries the route table, state model, run
directory layout, stage list and the App configuration in tabular form; `ACCEPTANCE/S7_ui.md`
carries the checks; `DEMO_SCRIPT.md` the click path; `KICKOFF_UI.md` the first message.

## 0. Conventions, tags and the drift list

### 0.1 Conventions

| Convention | Meaning |
|---|---|
| `<<name>>` | a variable span; the surrounding text is literal |
| exact copy | any string in a table cell or in backticks under "Shows", "copy", "title", "hint", "tooltip" is rendered character for character |
| the three files | per feed, `<<feed_slug>>_stage_table_creation.txt`, `<<feed_slug>>_standard_table_creation.txt`, `config_rows.xlsx` (SPEC header table) |
| verdicts | exactly `PASS`, `PASS_WITH_FLAGS`, `FAIL`; the chip label spells the middle one `PASS WITH FLAGS` |
| `<<inputs_volume>>`, `<<outputs_volume>>` | the two Unity Catalog Volume paths the App configuration resolves (§1.1) |
| `<<run_id>>` | `demo_` + local time `YYYYMMDD_HHMMSS` minted when a run starts (BACKEND_SPEC §2) |
| `<<client>>` | the client's short name, read from configuration (`ui.client_short_name`); never a literal in this kit |
| control table | every screen lists its controls as control · type · enabled when · on action · shows |

### 0.2 Tags

Every screen, panel, modal and control carries one tag. **Tags order the build; they never
remove anything.** A LATER item is built after every DEMO-DAY item is green, with the same
fidelity; an item whose data source does not exist yet is built with the empty or hidden
state this document gives it, never dropped.

| Tag | Meaning |
|---|---|
| **DEMO-DAY** | needed to run one FRD + STTM pair end to end through the full UI and hand over the three Option B files with a visible verdict |
| **LATER** | everything else — built after the DEMO-DAY set, unchanged in fidelity |

### 0.3 Drift between the reference UX specification and the shipping source (2026-09-16)

No commit touched the UI after the specification was transcribed (last UI change:
2026-09-04). The differences below are transcription gaps found by reading the source; each
is folded into the sections named.

| # | Where | Reference specification said | Source does | Folded into |
|---|---|---|---|---|
| D1 | replay load route | 404 unknown set | 404 unknown set AND 500 when the pair fails to resolve (message `contract pair failed to resolve: <<message>>`) | §3.5 |
| D2 | past-run load route | `404 / 409 incomplete` | 404 unknown run; **400** `live run '<<name>>' failed before producing results — cannot load` | §3.5 |
| D3 | generate route | 409 only | 409 empty pairs AND 404 `no resolved feed matches '<<slug>>'` when a slug is given that no pair resolves | §3.1 |
| D4 | live-unavailable block | reason always from the backend | when the backend gives no reason the block reads `Live is unavailable: the backend cannot reach a Layer-2 provider` | §2.4.2 |
| D5 | stage list marks | `✓` completed, `⋯` last while running | when the state is `failed` EVERY listed stage shows `✓` (the failure is the red banner above the list; no `✗` mark exists) | §2.4.2 |
| D6 | Overview tab | "four stacked panels" | five panels: Gate checks, Flags (conditional), Source contracts, Target tables, Load semantics | §2.3 |
| D7 | publish panel outside-policy line | amber text | uses a token `--amber` that the stylesheet never defines; the fallback `#b45309` renders | §2.6, §4.1 |
| D8 | copy strings | — | three copy strings carry the client's short name and one carries a client feed acronym and one a real ticket number as literals; this kit replaces them with `<<client>>`, a feed-neutral sentence and `<<ticket>>` (§4.2 lists each) | §2.2, §2.4.2, §2.5, §2.7, §4.2 |
| D9 | documents card footer | — | reads `All four documents are read…` while the configured expected list has six entries; the sentence is kept verbatim (fidelity) and flagged for the client to reword | §2.4.2 |
| D10 | source-files and metadata routes | no codes listed | both answer 404 when the configured demo FRD file is absent; the panels hide on any failure | §3.6 |
| D11 | file route | 400 escape / 404 missing | a binary file (the workbook) under `framework/` is listed in the Generated code tree and the text route fails on it; v2 adds a 400 `not a text file` answer and a download link in the tree | §2.3, §3.1 |
| D12 | run-live route | 400 / 409 | exact 400 strings: `live run requires explicit confirm: true (billed API calls)` and `live run unavailable: <<reason>>` | §3.3 |
| D13 | feeds route when startup failed | — | answers 200 with `failures: [{label: "startup", error: "pipeline unavailable — <<error>>"}]`, `mode: "mock"`, `label: null`; every other route answers 503 `pipeline unavailable — <<error>>` | §3.1 |
| D14 | decisions | "keyed by run" | the file shape is `{version: 2, runs: {<<run_key>>: {<<feed_slug>>: {"<<index>>": {decision, note}}}}}`; a file of another version is discarded as a whole | §3.1, BACKEND_SPEC §2.3 |
| D15 | cost modal | numbers from `status.estimates` | fallbacks `3`, `0.10`, `20` render when the status carries no estimates | §2.4.5 |

---

## 1. Target decision

### 1.1 Backend

One FastAPI process, deployed as a Databricks App, owns the run state and serves the
frontend's static bundle from the same port. Its shape mirrors the reference App manifest:

| Aspect | Decision |
|---|---|
| command | the Python interpreter launched in module mode on the backend package's main module (the same shape as the reference manifest's command); no shell wrapper |
| port | read `DATABRICKS_APP_PORT` at start-up; fall back to `CODEGEN_UI_PORT`, then `8571`; bind all interfaces |
| static files | the built (or plain) frontend directory is mounted at `/` AFTER every `/api` route; unknown non-`/api` paths answer the HTML shell (deep links survive a refresh); the HTML shell is served `no-store`; hashed assets stay cacheable |
| resources declared in the App configuration | (a) the inputs Volume — read; (b) the outputs Volume — read and write; (c) OPTIONAL: a serving endpoint (CAN_QUERY) for live Layer 2; (d) the force-mock switch as an environment value (`CODEGEN_FORCE_MOCK_PROVIDER=1`) |
| Volume access | through the workspace Files API with the App's own identity; the process never assumes a local mount of `/Volumes` and never uses the viewing user's token |
| generator | the S1–S6 package, loaded in-process; every generation runs on the container's local disk under a scratch directory and is copied to the outputs Volume when the feed completes (BACKEND_SPEC §2.4); reads served to the UI come from the Volume copy |
| run state | one loaded run at a time (mode, label, roots, per-feed records) plus a runner (idle / running / done / failed); both in memory, rebuilt from the Volume on request (BACKEND_SPEC §2) |
| progress | a run starts on a background thread; the POST returns at once; the frontend polls the status route every 1 000 ms — nothing streams, nothing holds a request open |

### 1.2 Frontend — two build paths, one specification

Genie Code runs this check first, in the workspace where it builds:

```
node --version
```

| Result | Path | What is built |
|---|---|---|
| a version prints (Node 18 or newer) and `npm --version` prints | **(A) React + Vite + TypeScript** | a single-page application with client-side routing, built to a static bundle (`index.html` + hashed assets) that the backend mounts at `/`; the reference frontend's dependency set (React, a router, a markdown renderer, a syntax highlighter) is allowed |
| the command is not found, prints an error, or `npm` is missing | **(B) no-build static frontend** | plain HTML + CSS + ES modules loaded by the browser as-is; hash routing (`#/`, `#/modes`, `#/demo`, `#/feeds/<<slug>>?tab=`); markdown rendered by a small inline renderer; code shown in monospace without highlighting (highlighting is a visual nicety, not a spec item) |

Both paths satisfy every screen, control, copy string, design value and status rule in Part 2 and
Part 3. This document never contains component code; it describes DOM structure, behaviour,
copy and design values. The route list, the data flow and the `?tab=` parameter are identical on
both paths; on path (B) the route is the URL hash.

### 1.3 Layer 2

Layer 2 defaults to the deterministic mock provider (SPEC 5.2 provider selection): with the
force-mock switch set, or with no serving endpoint declared, every run makes zero model calls
and the UI shows `MOCK — provider locked`. The cost modal and the live path (§2.4.5, §3.3)
are specified in full and become active only when the App declares the serving-endpoint
resource AND the force-mock switch is unset. Nothing else in the UI changes between the two.

---

## Part 1 — UX doctrine (the rules every screen obeys)

These are the things a "guessed" rebuild most often gets wrong. Treat each as a requirement.

1. **Every number and quote on screen is real output of the loaded run.** Nothing is
   hard-coded, nothing is a mock-up. Tiles, cards, rule tables, candidates, previews and
   reports are read from the run the backend currently holds (`/api/feeds`). If there is no
   run, the UI says so (`No feeds generated yet — the backend generates on startup.`) instead
   of rendering placeholders.

2. **The run mode is always visible.** A `MOCK` / `LIVE` / `REPLAY` badge sits in the sidebar
   brand block on every route; LIVE and REPLAY additionally paint a full-width banner at the
   top of the main column with the run label (`<<run_id>>` or the replay-set name). A viewer
   must never wonder whether they are looking at a fresh run, a recorded run, or the
   deterministic mock.

3. **Honesty badges instead of silent stand-ins.** Any value the agent synthesised rather
   than read from a document is badged `SYNTHETIC` with a tooltip naming where the real value
   lives. A synthetic STTM contract carries a `synthetic STTM` tag on the card, the header and
   the contracts panel. Metadata-sheet cells carry exactly one provenance dot each.
   Framework-assigned identifiers stay blank and are listed as such.

4. **Errors are said, never hidden — and the status code says whose problem it is.**
   `503` = not configured or not built → the section is simply absent. `502` = the workspace
   refused → the section renders the message plus a Retry button. `409` = one-at-a-time /
   nothing to generate → shown verbatim in the red error banner. `400` = the caller's request
   is wrong. `404` = no such feed, file or run. The frontend surfaces every backend `detail`
   string verbatim; it never paraphrases a generator message.

5. **Confirm before anything billed, destructive, or outward.** Four modal dialogs exist and
   each must stay: (a) run live (cost shown), (b) replace LIVE/REPLAY results with a mock
   regenerate, (c) reset review decisions, (d) publish to a Unity Catalog volume. A stray
   click can never spend money, overwrite the view the presenter is standing on, wipe
   decisions, or write outside the App's own outputs Volume.

6. **The human decision is the finale, and it does not merge.** Every route ends at the
   Layer-2 review queue. Approve / Reject records a decision only; the status copy says so
   explicitly. Decisions never gate the verdict and never alter generated output.

7. **The agent never invents identifiers.** Framework-assigned IDs render blank and are
   listed under `Framework-assigned IDs left blank: … — the agent never invents them.`

8. **Colour never carries meaning alone.** Verdict chips pair an icon with a text label;
   classification badges pair a dot with a label; status pills carry words. The three status
   colours (good / warning / critical) are reserved for verdicts and check states and are never
   reused as series or badge identity colours.

9. **Choices are explicit; nothing auto-picks.** The generate card opens with `none chosen`
   for the STTM and the run button disabled until the operator picks. A look-alike FRD is
   *suggested* (`looks like a pair — confirm`), never auto-selected. A feed-match failure
   offers a one-click `Choose companion FRD` button; it does not retry on its own. An FAQ
   question left unanswered stays unanswered and is flagged, never defaulted silently.

10. **The UI is a front door, not a second pipeline.** No generation logic lives in the
    frontend. Everything the screens show comes from the in-process S1–S6 package the batch
    entry point also runs; UI runs are always dry-run and skip the generated tests (SPEC 5.4
    flag 9 is therefore always present — `PASS_WITH_FLAGS` is the honest floor).

11. **Nothing on the container is the system of record.** Every run, every FAQ answer, every
    upload and every review decision lives on the outputs Volume; a container restart loses
    only in-memory selections (STTM, FRD, output mode) and the loaded-run pointer.

---

## Part 2 — Screens

### 2.1 Application shell  [DEMO-DAY]

```
┌──────────────────┬──────────────────────────────────────────────────────────┐
│ SIDEBAR (dark)   │ MAIN (light, max-width 1240px, padding 28px 36px 64px)   │
│ 264px, sticky,   │                                                          │
│ 100vh, scrolls   │ [error banner — only when the last API call failed]      │
│                  │ [mode banner — only LIVE or REPLAY]                      │
│ CodeGen · Data   │                                                          │
│ Engineer Agent   │ <route content>                                          │
│ Contracts →      │                                                          │
│ Databricks       │                                                          │
│ pipelines        │                                                          │
│ [MODE · label]   │                                                          │
│                  │                                                          │
│ OVERVIEW         │                                                          │
│  Dashboard       │                                                          │
│  Run modes  live·replay                                                     │
│  Demo mode  guided tour                                                     │
│                  │                                                          │
│ FEEDS            │                                                          │
│  syn_widget_risk           ●                                                │
│  syn_gadget_events         ●                                                │
│  …                         ●  (verdict dot, right-aligned)                  │
│                  │                                                          │
│ ─────────────    │                                                          │
│ Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.            │
│ Gate verdict computed in code, never by judgment.                           │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| Brand block | display | always | — | product name `CodeGen · Data Engineer Agent` (15px, weight 650); sub-line `Contracts → Databricks pipelines` (12px muted) | DEMO-DAY |
| Mode badge | pill (10.5px, weight 750, letter-spacing 0.08em) | `/api/feeds` answered | — | the mode upper-cased plus ` · <<label>>` when a label exists (`MOCK`, `LIVE · demo_20260116_143000`, `REPLAY · <<set>>`); `title` = the mode copy (§4.2); colours §4.1 | DEMO-DAY |
| Nav: Overview | section header (11px uppercase letter-spaced muted) + three rows | always | route change | `Dashboard`; `Run modes` with right-aligned 10.5px hint `live · replay`; `Demo mode` with hint `guided tour`; rows 13px, 8px radius, hover 6% white, active 12% white + weight 600 | DEMO-DAY |
| Nav: Feeds | section header + one row per feed | `/api/feeds` answered | route change to `/feeds/<<slug>>` | the slug (ellipsised) and a right-aligned 8px verdict dot (title = verdict label) | DEMO-DAY |
| Footer | display (11.5px muted) | always | — | `Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.` newline `Gate verdict computed in code, never by judgment.` (a rebuild whose Layer 1 uses another template engine substitutes its name in the parenthetical) | DEMO-DAY |
| Error banner | red tint block at the top of MAIN | the feeds fetch failed | — | `Backend error: <<message>>` | DEMO-DAY |
| Mode banner | full-width block (red tint LIVE, blue tint REPLAY) | mode is not mock | — | the mode copy (§4.2) + ` · ` + `<<label>>` in a code span when a label exists | DEMO-DAY |
| Generate-all confirm modal | modal | opened by "Generate all feeds" while the mode is not mock | primary → `POST /api/generate` `{feed_slug: null, dry_run: true, skip_tests: true}` | title `Replace the current LIVE results?` / `Replace the current REPLAY results?`; body `This replaces the current live results (<<label>>) with a fresh **mock** run. You can reload them afterwards from the Run modes page.` (`replayed` instead of `live` for REPLAY; the parenthesised label only when one exists); buttons `Continue — run mock` (primary) / `Cancel` | LATER |

- **Routes:** `/` Dashboard · `/modes` Run modes · `/demo` Demo mode · `/feeds/<<slug>>`
  Feed detail (accepts `?tab=` one of `overview | rules | candidates | notebook | code |
  report`). Path (A): client-side routing with the HTML-shell fallback; path (B): hash routes.
- **Data flow:** the shell owns the feeds response and passes it down; every page that changes
  the loaded run calls the shell's refresh so the sidebar, badge and banner update together.
- **Favicon:** blue rounded square with white `< >` glyphs (inline SVG data URI). Document
  title `CodeGen · Data Engineer Agent`.

### 2.2 Dashboard (`/`) — "Generation gate"  [DEMO-DAY]

```
Generation gate                                   [Reset decisions] [Generate all feeds]
Pipelines generated from approved FRD + STTM contracts. Every rule is compiled
deterministically or routed to a reviewed Layer-2 candidate — nothing lands unreviewed.

[failures banner: "<label> — <error>" per failed pair, red]

┌ FEEDS ─────┐ ┌ PASS ───────────┐ ┌ RULES COMPILED ┐ ┌ PENDING REVIEW ──┐
│ 2          │ │ 0               │ │ 3/6            │ │ 1                │
│ from       │ │ 2 with flags ·  │ │ deterministic  │ │ Layer-2 candidates│
│ configured │ │ 0 failed        │ │ (Layer 1 +     │ │ awaiting an      │
│ contract   │ │                 │ │ orchestration) │ │ engineer         │
│ pairs      │ │                 │ │                │ │                  │
└────────────┘ └─────────────────┘ └────────────────┘ └──────────────────┘

┌ feed card ───────────────────────────────┐ ┌ feed card ─────────────────┐
│ syn_gadget_events        [⚑ PASS WITH FLAGS]                             │
│ SynVendor Analytics | Region 1, Region 2 | PSV                           │
│ ████████▒▒▒▒▒▒░░  (rule strip, one segment per classification)           │
│ ● mappable 2  ● orchestration 1  ● notification 1  ● unmapped → L2 1     │
│ ──────────────────────────────────────────────────────────────────────── │
│ 3/5 rules compiled deterministically           3 files · 1 pending review│
└──────────────────────────────────────────┘ └────────────────────────────┘

┌ Framework artefacts (Option B) ─────────────────────────────── (only if any feed has framework)
┌ Publish to Unity Catalog volume ────────────────────────────── (only if ≥1 feed)
┌ For <<client>>'s framework: metadata sheet preview ─────────── (only if ≥1 feed)
```

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| Page head | `h1` + sub-line | always | — | `Generation gate`; sub-line §4.2 | DEMO-DAY |
| Reset decisions | secondary button | not resetting | opens the reset modal | `Reset decisions`; tooltip `Clear all approve/reject decisions recorded for the currently loaded run` | LATER |
| Reset modal | modal | — | primary → `POST /api/decisions/reset` then refresh feeds | title `Reset review decisions?`; body `Clears every approve/reject recorded for the currently loaded run (<<label>>). Candidates return to **pending engineer approval**. Decisions made under other runs are untouched.` — the parenthesis reads `(mock state)` when no label; buttons `Reset — clean slate` (primary; `Resetting…` while busy) / `Cancel` | LATER |
| Generate all feeds | primary button | not generating | mock mode → `POST /api/generate` `{feed_slug: null, dry_run: true, skip_tests: true}` at once; LIVE/REPLAY → the §2.1 confirm modal first | `Generate all feeds`; spinner + `Generating…` while busy; a 409 shows its detail in the error banner (`config.contracts.pairs is empty — nothing to generate. Restore anonymized contract pairs in config/config.yaml, or load a replay set / past live run instead.`) — expected, not a fault | DEMO-DAY |
| Failures banner | red banner | `failures` non-empty | — | one line per entry: `**<<label>>** — <<error>>` | DEMO-DAY |
| Stat tiles | grid (auto-fit, min 170px, 14px gap) | always | — | see the tile table | DEMO-DAY |
| Feed cards | grid (auto-fill, min 340px); whole card is a link to `/feeds/<<slug>>` | ≥1 feed | navigate | see the card table | DEMO-DAY |
| Empty state | centred muted | no feeds | — | `No feeds generated yet — the backend generates on startup.` | DEMO-DAY |
| Framework artefacts (Option B) panel | panel | ≥1 feed has `framework != null` | download links | see below | DEMO-DAY |
| Publish to Unity Catalog volume | shared component §2.6 | ≥1 feed | — | — | LATER |
| Metadata sheet preview | shared component §2.7, keyed to `<<mode>>-<<label>>` so it refreshes when the loaded run changes | ≥1 feed | — | — | DEMO-DAY |

**Stat tiles:**

| Label | Value | Hint |
|---|---|---|
| Feeds | number of feeds | `from configured contract pairs` |
| Pass | count of `PASS` | `<<n>> with flags · <<m>> failed` |
| Rules compiled | `<<deterministic>>/<<rules>>`, or `—` when there are no rules | `deterministic (Layer 1 + orchestration)` |
| Pending review | sum of `candidates_pending` | `Layer-2 candidates awaiting an engineer` |

`deterministic` = the sum of `mappable` + `orchestration_config` counts across feeds.

**Feed card:**

| Part | Shows |
|---|---|
| top row | slug in mono 14.5px weight 650 + the verdict chip right |
| meta line (12.5px, ink-2) | `<<source_system>> | <<lobLabel>> | <<FORMAT>>` (+ ` · segmented` when segmented) (+ the `synthetic STTM` tag when `sttm_is_synthetic`); `lobLabel` shows the first three LOB codes then ` +N more` (a segmented client feed lists 14 LOB codes — never dump them all on a card) |
| rule strip | an 8px-tall bar; each classification with a non-zero count gets a segment whose flex weight is its count, in the FIXED order `mappable, orchestration_config, notification, out_of_scope, flagged, unmapped`, 2px surface gap between segments, title `<<label>>: <<n>>`; hidden when `rule_total` is 0 |
| counts row | for each non-zero classification, a 7px dot in its identity colour + label + count |
| foot (hairline above, 12px muted, tabular numerals) | left `<<d>>/<<t>> rules compiled deterministically`; right `<<files_written>> files · <<candidates_pending>> pending review` |
| hover | the border lifts and a soft shadow appears |

**Framework artefacts (Option B) panel.** Head `Framework artefacts (Option B)` with hint
`config rows are the approval artefact; DDL + inserts are add-ons to <<client>>'s master
notebook, applied only after approval`. Body, per feed: `<<slug>>` in a code span + hint
`<<tab>> <<n>> · <<tab>> <<n>> …` (one entry per tab of `row_counts`, in workbook order) `·
<<derived>>/<<total>> derived`; a row of secondary buttons, one per file of `framework.files`,
each a download link to `/api/feeds/<<slug>>/download?path=framework/<<name>>`; then the
11px line `Framework-assigned IDs left blank: <<cols joined by ", ">> — the agent never
invents them.` (`none` when the list is empty). With S1–S6 the files are exactly the three
files; the panel renders whatever `framework.files` lists.

### 2.3 Feed detail (`/feeds/<<slug>>`)  [DEMO-DAY, tabs tagged individually]

```
syn_gadget_events  (mono h1)                                          [Regenerate]
[⚑ PASS WITH FLAGS] SynVendor Analytics · Region 1, Region 2 · PSV

Overview | Rules (5) | Layer-2 review (1) | Generated code (3) | Report
─────────────────────────────────────────────────────────────────────────────────
<tab content>
```

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| Head | mono `h1` + sub-line | feed loaded | — | the slug; sub-line: verdict chip · `<<source_system>> · <<lobLabel>> · <<FORMAT>>` (+ ` · segmented (H/D/T)`) · the `synthetic STTM` tag when synthetic | DEMO-DAY |
| Regenerate | primary button | not generating | `POST /api/generate` `{feed_slug: <<slug>>, dry_run: true, skip_tests: true}` → reload the feed → refresh the shell | `Regenerate`; spinner + `Generating…` while busy | LATER |
| Tab strip | underline tabs; active = accent colour + 2px underline; counts in a grey pill | feed loaded | switch tab | `Overview` · `Rules (<<rule_total>>)` · `Layer-2 review (<<candidate_count>>)` · `Notebook` (ONLY when an `.ipynb` is among `written_files`) · `Generated code (<<n>>)` where n excludes the notebook · `Report` | DEMO-DAY |
| Loading | centred muted | feed not yet loaded | — | `Loading…` | DEMO-DAY |
| Error | red banner replacing the page | the feed fetch failed | — | the backend `detail` verbatim (404: `no generated feed named '<<slug>>'`) | DEMO-DAY |

**Overview tab  [DEMO-DAY]** — five stacked panels (D6):

| # | Panel | Hint | Body |
|---|---|---|---|
| 1 | `Gate checks` | `verdict computed in code — never by judgment` | one row per gate check: 8px dot (green PASS / red FAIL), bold name (min-width 130px), details in ink-2. With S1–S6 the names are `ruff`, `debug_patterns`, `secrets`, `test_per_module` (SPEC 5.4), each passed with the details the generator records |
| 2 | `Flags — needs a human` (only when `flags` is non-empty) | `<<n>> open` | a list; each row has an amber dot. A flag containing `pending engineer approval` is the **HITL centrepiece**: the row gets an amber background and a `PENDING ENGINEER APPROVAL` tag (10px, weight 750, warning background) before the text. Flag strings come verbatim from the gate (SPEC 5.3 texts, in SPEC 5.3 order) |
| 3 | `Source contracts` | `provenance embedded in every generated file` | definition list: `FRD` → name in a code span + line `sha256 <<hash>>`; `STTM` → name (+ `synthetic` tag) + sha256 line; `File patterns` → one code span per line; `Delimiter` → the JSON-quoted delimiter (e.g. `"|"`); `Lines of business` → the full list joined by `, `; `Frequency` → only when present |
| 4 | `Target tables` | — | `Stage` (one code span per line); `Standard` (code span, or italic `none — stage-only feed (load AS-IS)`); `Errors`; `Recycle` (code span, or italic `no recycle rule`); `Processed files` |
| 5 | `Load semantics` | — | `Natural key` (code spans); `Not-null columns` (code spans or italic `none`); `PHI columns` (code spans or italic `none declared`; when present add the muted line `masked to last-4 at every log / report / error egress`); `Load window / SLA` (joined with `; `, only when present) |

**Rules tab  [DEMO-DAY]** — one panel titled `Validation rules — verbatim from the FRD`,
hint `classification is deterministic; only *unmapped* rules reach Layer 2`. Table columns:
`#` (muted, tabular), `Classification` (classification badge), `Rule` (rule text, max-width 520px,
wrap anywhere; notes below in 12.5px ink-2), `Generated feature` (code span or `—`),
`Grounding` (mono 12px, wrapped in curly quotes). Horizontal scroll container. Rows come from
`outcomes` in contract order (SPEC 5.1).

**Layer-2 review tab  [DEMO-DAY for display; decisions LATER]** — empty state `No Layer-2
candidates — every rule compiled deterministically for this feed.` Otherwise an intro
paragraph (max-width 760px): `These rules could not be compiled deterministically, so the
reasoning layer proposed candidates into a review artifact (candidates/candidates.json).
Candidates are **never merged automatically** — approval here records the engineering
decision only.` Then one **candidate card** per entry (SPEC 5.2 artifact, CONFIRM items
first):

```
┌──────────────────────────────────────────────────────────────┐
│ Rule: “<rule_text>”                                          │
│ [provider: mock] [✓ grounded | ✗ NOT grounded] [● mappable]   │
│ <rationale, 13px ink-2>                                      │
│ ┌ candidate (python) ─────────────────────────┐              │
│ │ <PySpark sketch>                            │              │
│ └─────────────────────────────────────────────┘              │
│ │ “<citation 1>”   (left-bordered italic quote)              │
│ │ “<citation 2>”                                             │
│ [✓ Approve] [✗ Reject]  Awaiting engineer decision           │
└──────────────────────────────────────────────────────────────┘
```

| Part | Shows |
|---|---|
| title | `Rule: “<<rule_text>>”` |
| pills | `provider: <<provider>>`; `✓ grounded` (green) or `✗ NOT grounded` (red); the classification badge of `response.classification` when a response exists |
| rationale | `response.rationale`, 13px ink-2 |
| code box | present when `response.code_candidate` is non-null: a code pane whose path bar reads `candidate` followed by the Python file extension; highlighted on path (A), plain mono on path (B) |
| citations | one left-bordered italic quote per entry of `response.citations`, in curly quotes |
| **provider-failed variant** | when `response` is null the body is a red banner `Provider failed: <<failure_notes joined by "; ">>`; the decision row still renders |
| **CONFIRM variant** (`kind == "confirm"`) | a leading amber pill `CONFIRM — document-derived, cited`; the title is the item text WITHOUT the `Rule:` prefix; the pill reads `source: <<provider>>` instead of `provider:`; `detail` renders as the rationale; `citation` as the single quote block; no grounded pill, no classification badge |
| decision row | `✓ Approve` (green outline; reads `✓ Confirm` on the CONFIRM variant) and `✗ Reject` (red outline); the selected one gets a tinted fill; **clicking the already-selected decision resets to `pending`**; both disable while the request is in flight; `POST /api/feeds/<<slug>>/candidates/<<index>>/decision` |
| status copy (muted 12.5px) | pending → `Awaiting engineer decision` (CONFIRM: `Soft confirmation — the run proceeds; a source-team answer closes it`); decided → `Marked approved — merge into generated code remains a manual (v2) step` / `Marked rejected — …` (CONFIRM: `Marked approved — recorded in the decision store`) |
| after a decision | reload the feed and refresh the shell so the dashboard's pending count moves |

**Notebook tab  [LATER — Option A]** — HIDDEN by default: the tab exists only when an
`.ipynb` is among `written_files`, which S1–S6 never produce. What makes it appear: a run in
output mode `notebook` or `both` on a generator that carries the Option A emitter (SPEC L16 —
shelved). When it appears: panel titled `<<slug>>.ipynb` (code span) with hint `the whole
pipeline as one runnable Databricks notebook — the module files stay canonical`; body = the
notebook view (markdown cells as prose; code cells in a bordered box with a 3px accent left
border). Loads `GET /api/feeds/<<slug>>/file?path=<<slug>>.ipynb`; `Loading notebook…`
while pending; parse failure → `Could not parse the notebook.`

**Generated code tab  [DEMO-DAY]** — two-pane layout (min-height 480px): left a 280px file
tree, right the code pane (max-height 640px, sticky path bar on top). The tree groups files
by directory (header = the directory name upper-cased, or `ROOT`), mono 12.5px buttons,
active = accent tint. On load the first `pipeline/` file (else the first file) opens
automatically. Paths are derived by locating the `/<<slug>>/` segment in each `written_files`
entry. The notebook is excluded. **Default state with S1–S6:** one group `FRAMEWORK` holding
the two `.txt` files and `config_rows.xlsx`; the first `.txt` opens automatically; the
workbook entry renders as a download link (tooltip `binary — download`) instead of opening,
because the text route answers 400 for it (D11). Highlighting on path (A) for `py sql json
toml md` (a `.txt` renders plain); path (B) renders everything plain. What makes the
`PIPELINE` and `DDL` groups appear: an Option A run (as for the Notebook tab).

**Report tab  [DEMO-DAY]** — the markdown report from `GET /api/feeds/<<slug>>/report`
rendered inside `.report-md` (13.5px, max-width 860px, tables bordered, code inline chips).
`Loading report…` while pending. The report is SPEC 5.5 as written; its `Flags:` block and
verdict line are the acceptance-tested part.

### 2.4 Run modes (`/modes`)  [DEMO-DAY, items tagged individually]

The operational heart of the UI. Two cards side by side (single column under 980px). Page
head: `h1` `Run modes`, subtitle `Pick how the results you're about to walk through get
produced. Both modes end on the same dashboard — and the same human review queue.` A red
error banner above the cards shows the last failed action's message.

On mount the page fires, in parallel: replay sets, live availability, run status, input
documents, source files, input requirements, governance checks, past live runs. Everything
is a live read; nothing is cached to disk. A route that answers 503 (not built / not
configured) leaves its section absent (doctrine 4).

#### 2.4.1 Card A — "Replay a recorded run" (badge `REPLAY`)  [LATER]

Hint: `Loads a tracked, real live run instantly — zero API calls, zero cost, no key needed.
The deterministic pipeline re-runs locally; the recorded AI candidates are injected exactly
as the model returned them.`

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| Replay rows | one row per set (hairline between) | sets listed | — | name in mono weight 650; hint `recorded <<date>> · <<n>> feeds · call log` (`recorded <<date>> · ` only when the set name ends in an 8-digit stamp; ` · call log` only when a call log exists) | LATER |
| Load | primary button per row | no load in progress AND no run in progress | `POST /api/replay/load {set}` → refresh feeds → navigate to `/` | `Load`; `Loading…` while busy | LATER |
| States | centred muted | — | — | `Discovering replay sets…` while pending; `No replay sets tracked under fixtures/replay/.` when empty (the rebuild lists `<<inputs_volume>>/replay/`; the copy keeps the reference wording) | LATER |

#### 2.4.2 Card B — "Generate a Pipeline"  [DEMO-DAY]

Head badge: `LIVE` (red) — or `MOCK — provider locked` (grey) when the live-availability
route reports provider `mock (locked)`, which is the rebuild's default (§1.3).

Top to bottom, in this exact order:

**Step 1 — choose an STTM.**  [DEMO-DAY]

Hint paragraph: `**Step 1 — choose an STTM.** The pipeline's input is a client STTM mapping
workbook, picked from the SharePoint document library — the program's system of record.
Choose the workbook this run will consume:` (the reference copy names SharePoint; the
rebuild's picker lists the inputs Volume — keep the sentence, it describes provenance, not
the picker).

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| STTM line | inline text | always | — | `STTM workbook: ` + the name in a code span when `sttm_chosen`, else italic muted `none chosen` | DEMO-DAY |
| Choose STTM… | secondary button | not running | opens the chooser modal (§2.4.4) | `Choose STTM…` | DEMO-DAY |
| Clear | secondary button | not running AND `sttm_chosen` | `DELETE /api/demo/workbook` → refresh status | `Clear`; tooltip `Back to none chosen` when chosen / `Nothing chosen yet` otherwise | DEMO-DAY |
| FRD line | inline text | always | — | `FRD contract: ` + `<<frd_name>>` in a code span (`…` until the status answers) + hint ` (demo golden — default)` when not `frd_chosen` | DEMO-DAY |
| Choose FRD… | secondary button | not running | opens the same chooser modal | `Choose FRD…`; tooltip `Pick the FRD for this run (companion FRDs are suggested for the chosen STTM)` | DEMO-DAY |
| Reset | secondary button | not running AND `frd_chosen` | `DELETE /api/demo/frd` → refresh status | `Reset`; tooltip `Back to the demo golden default` when chosen / `Already on the demo golden default` otherwise | DEMO-DAY |
| Pair warning pill | red pill | `frd_warning` is true | — | `This STTM does not appear to belong to the demo FRD — expect a feed-match failure.`; tooltip `Pick the companion FRD in the STTM chooser` | DEMO-DAY |

`frd_warning` is computed by the backend: an STTM was explicitly chosen, it is not the
configured default workbook, and no FRD was explicitly chosen (§3.3).

**Source files this run will read**  [LATER] — subhead; rendered only when the source-files
route answered with feeds. Hint `From the demo FRD contract <<name>>, read at request time.`
A horizontally scrolling table: `feed` · `landing root` (code span + `SYNTHETIC` pill when
synthesised, tooltip = the landing tooltip, §4.2) · `file patterns` (one code span per line,
or italic `none in FRD`) · `format` (+ ` · <<delimiter>>` hint) · `frequency` (or italic `not
stated in FRD`) · `stage target` (code span or `—`) · `standard target` · `load strategy`
(two lines `<<stage>> (stage)` / `<<standard>> (standard)` + `SYNTHETIC` pill when
synthesised, tooltip = the strategy tooltip). Absent until the display module is built (its
route answers 503 → section absent).

**Convention check — real FRD <<ticket>>**  [LATER] — subhead; only when the reference
FRD document is present in the standards folder. `<<ticket>>` is the trailing number of the
reference FRD's file name (D8). Hint `Read live from <<file>> (Structural Metadata), at
request time — the client's real convention beside the synthesized paths above.` Two-column
table of `ADLS Location`, `Target Schema`, `Load Strategy STG`, `Load Strategy STD`,
`Object / data Format` (rows with no value are omitted), each with a third cell `from
document`. Absent the document, the block is absent.

**In the Databricks workspace**  [LATER] — a collapsed disclosure block styled as a dark
terminal, summary `In the Databricks workspace`. Header note: `LIVE — listed from <<volume>>
at <<time>>` (green) or `SYNTHETIC (live listing unavailable: <<reason>>) — rendered from the
FRD's landing location and file patterns, not a live listing.` (amber; the parenthesis only
when a reason exists). Body: lines; lines starting with `$ ` are commands
(`$ databricks fs ls dbfs:/Volumes/<<catalog>>/<<schema>>/<<volume>>/<<root>>/`), soft-wrapped
with a hanging indent, non-selectable. Rendered inside the source-files section, so absent
with it.

**Metadata sheet preview**  [DEMO-DAY] — the shared component §2.7, refreshed on
`<<state>>-<<last_run_label>>`. In the reference it sits inside the source-files section; in
the rebuild it renders regardless of that section (the preview reads the loaded run, which
exists from boot).

**Step 1.5 — load-pattern FAQ.**  [DEMO-DAY] — new in v2 (from v1.1 §2.2), rendered
between Step 1 and Step 2.

Hint paragraph: `**Step 1.5 — answer the load-pattern FAQ.** Inspect the chosen pair to
list its feeds, then answer the eight load-pattern questions per feed. Answers are written to
<<outputs_volume>>/faq/<<feed_slug>>.faq.yaml and read by the generator (SPEC 1.8).
Unanswered questions are flagged, never guessed.`

```
┌ Step 1.5 — answer the load-pattern FAQ ─────────────────────────────────────────┐
│ [Inspect pair]   Extracted: syn_widget_sttm.contract.json — 2 feed(s)           │
│ feed_id            stage tables                        standard   rules         │
│ syn_widget_risk    stg_syn.syn_widget_risk             syn.…      1             │
│ syn_gadget_events  stg_syn.syn_gadget_events, …_recycle syn.…      5            │
│                                                                                 │
│ [ syn_widget_risk ] [ syn_gadget_events ]                                       │
│ question                value                     source      evidence          │
│ load_mode               [ truncate_and_load    ▾ ] [contract] stage_target.load_│
│   prefilled from the contract — change the value to override it   strategy: "…" │
│ is_master_file          [ (unanswered)         ▾ ] [engineer▾] [____________]   │
│   default: unknown                                                              │
│ … (eight questions, then the two companions)                                    │
│ 2 answered by the contract · 0 answered here · 6 unanswered → 6 flags           │
│                                                            [Save answers]      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|
| Inspect pair | primary button | `sttm_chosen`, not running | `POST /api/demo/inspect` (§3.2) | `Inspect pair`; `Inspecting…` while busy; tooltip `Choose an STTM workbook first` when disabled for that reason | DEMO-DAY |
| Inspection line + table | text + table | inspection succeeded | — | `Extracted: <<contract file>> — <<n>> feed(s)`; one row per feed: `feed_id`, stage tables (qualified, joined by `, `), standard table (qualified, or `none — stage-only`), validation-rule count | DEMO-DAY |
| Inspection failure | red banner under the button | inspect answered 400 | — | the detail verbatim: `extracting workbook — <<message>>` or `resolving contracts — <<message>>` (multi-line messages keep their lines and indentation); below it the fixed sentence for the family (§4.2 error families) | DEMO-DAY |
| Feed tabs | tab strip (sheet-tab style) | inspection succeeded | switch feed | one tab per feed in feed order, label = `feed_slug` | DEMO-DAY |
| load_mode | dropdown: `(unanswered)`, `truncate_and_load`, `append`, `merge_on_keys` | not running | stores the answer in page state | prefilled (SPEC 1.8 row 1) when the FRD stage load strategy maps; caption `prefilled from the contract — change the value to override it` on a prefilled row, `default: unknown` otherwise | DEMO-DAY |
| is_master_file | dropdown: `(unanswered)`, `yes`, `no` | not running | — | caption `default: unknown` | DEMO-DAY |
| dedup_within_file | dropdown: `(unanswered)`, `none`, `row_level`, `by_keys` | not running | — | caption `default: none` | DEMO-DAY |
| existing_record_policy | dropdown: `(unanswered)`, `plain_append`, `skip_if_exists`, `delete_and_insert` | not running | — | caption `default: unknown` | DEMO-DAY |
| load_frequency | dropdown: `(unanswered)`, `daily`, `weekly`, `monthly`, `yearly`, `adhoc` | not running | — | prefilled from the FRD frequency text (SPEC 1.8 row 5) with the whole frequency text as evidence | DEMO-DAY |
| target_tables_exist | dropdown: `(unanswered)`, `yes`, `no` | not running | — | caption `default: yes` | DEMO-DAY |
| reject_threshold | dropdown: `(unanswered)`, `none`, `number…` (a number box appears when chosen) | not running | — | caption `default: none` | DEMO-DAY |
| data_integrity_checks | dropdown: `(unanswered)`, `none`, `not_null_keys`, `custom` | not running | — | caption `default: none` | DEMO-DAY |
| Source (one per row) | dropdown `engineer` (default) / `frd`; read-only `contract` on a prefilled row the engineer has not changed | not running, value set | the `source` written for that answer | choosing `frd` makes the row's evidence box required | DEMO-DAY |
| Evidence (one per row) | text box | not running, value set | stored as `evidence` | empty allowed for `engineer`; a prefilled row shows the prefill's evidence read-only | DEMO-DAY |
| has_header / has_trailer | dropdowns `(unanswered)`, `yes`, `no`, each with its own source and evidence | not running | companions (SPEC 1.8 companions table) | caption `companion — sets HEADER_FLAG` on has_header; header line `Companions (not questions, never flagged):` | DEMO-DAY |
| Summary line | text | always | — | `<<n>> answered by the contract · <<k>> answered here · <<m>> unanswered → <<m>> flags` where m counts the eight questions only | DEMO-DAY |
| Save answers | button | not running, inspection succeeded | `PUT /api/demo/faq/<<feed_slug>>` (§3.2) | `Saved <<feed_slug>>.faq.yaml` or `No answers set — the generator will use defaults and flag every question` | DEMO-DAY |

Writing rules (the generator's contract, SPEC 1.8): a prefilled answer the engineer did not
change is NOT written (the generator re-derives it, so the banner counts it "from contract");
only answers set on this screen are written, each as a mapping with `value`, `source` and,
when given, `evidence`; `yes`, `no` and any number are written quoted so YAML keeps them as
text; when the engineer set nothing for a feed, no file is written for that feed and an
existing file for it is removed (the banner then reads `defaults (no FAQ file)` exactly as in
ACCEPTANCE S1 case 3). `(unanswered)` is never written; it means "absent", and the gate flags
it as `faq_unanswered:<<question>>`. Changing the STTM or the FRD clears the inspection and
the forms (the saved files stay on the Volume until overwritten).

**Step 2 — generate.**  [DEMO-DAY]

Hint: `**Step 2 — generate.** Extract the chosen STTM into a mapping contract → deterministic
generate → live AI reasoning on the unmapped rules → safety gate. Makes billed API calls.`
(kept verbatim; under the mock lock the cost modal states that zero calls are made).

**Output**  [DEMO-DAY; Notebook / Both LATER] — subhead `Output`; three toggle buttons in a
row: `Notebook`, `Framework artefacts`, `Both`; active = accent outline; `POST
/api/demo/output-mode {mode}`. **Default active in the rebuild: `Framework artefacts`**
(configuration `output.mode: framework`). `Notebook` and `Both` render but are DISABLED
(55% opacity) with tooltip `Option A emitter not built in this workspace (SPEC L16)` while
the status reports `output_modes_available: ["framework"]`; they enable the moment the
status lists `notebook`. Hint below: `Framework artefacts = DDL scripts + config rows +
insert statements for the existing ingestion framework — the ~90% case, adding a feed to
what already runs. Notebook = a fresh standalone pipeline — the ~10% case.`

**Input documents**  [DEMO-DAY] — subhead `Input documents`; the documents card, three states
from the input-documents route:

| State | Condition | Shows |
|---|---|---|
| none | expected list empty OR nothing present | amber call-out `**No reference documents found.** The generator's naming, path and structural checks are grounded in the client FRD and architecture decks; none are present in the configured input directories. Runs proceed without them.` + button `Attach…` (opens the documents modal, reference variant) |
| all | no missing entry | green-tinted card titled `Reference documents attached`; one row per expected file with `✓` + the name in a code span; footer hint `Drives the generator's naming, path and structural checks via config.` |
| partial | some missing | amber-tinted card titled `Some reference documents are missing`; `✓` or `☐` per row |

Always followed by the 11px line `All four documents are read and used in the request-time
checks below. None of them alters generated output — the generation path stays
contract-driven, byte-stable.` (D9: kept verbatim; flagged for the client to reword).

**Input requirements check**  [LATER] — subhead; only when the route answers with a check.
Hint `The demo FRD contract, evaluated against the eleven Structural Metadata rows of
<<deck>> — read live from the document at request time. <<f>> filled · <<p>> partial · <<m>>
missing · <<n>> not captured by the contract shape.` Table rows: row name · status pill
(`filled` green / `partial` amber / `missing` red / `not captured` grey) · how-to-fill
guidance (hint text). Then `A missing or not-captured row is flagged, never guessed — the row
names and guidance come from the document itself.` When the document-side check exists, a
second line `The same rows checked against the **real FRD document** (<<docx>>, Structural
Metadata read live): <<f>> filled · <<p>> partial · <<m>> missing.` followed by an inline run
of pills + row names. Absent until built (503 → absent).

**Reference-architecture checks**  [LATER] — subhead; only when checks exist. Hint
`Controls stated by the governance and solution architecture decks, read live from the
documents and evaluated against the loaded run: <<v>> verified · <<a>> need attention · <<p>>
awaiting a run.` Table: status pill (`verified` green / `attention` amber / `awaiting a run`
grey) · control text (title = deck file) · evidence (hint). These flip from `awaiting a run`
after a run completes (the page re-fetches them on `done`). Absent until built.

**Known input gaps**  [DEMO-DAY] — subhead; amber call-out `**Demo FRD, not the real one.** A
production run needs the FRD with the paths to the actual client files — this build carries
an anonymized stand-in. The pipeline runs end-to-end, but the output does not represent an
accurate case.` + button `Provide…` (opens the documents modal, FRD variant).

**Run button / unavailability**  [DEMO-DAY]

| Condition | Shows |
|---|---|
| live-availability answered `available: false` | a muted block `Live is unavailable: <<reason>> (provider: <<p>>)` — the reason is provider-specific from the backend, never hard-coded; when the backend gives none: `Live is unavailable: the backend cannot reach a Layer-2 provider` (D4); the `(provider: …)` hint only when a provider name exists |
| otherwise | primary button `Generate from this STTM…`, disabled until an STTM is chosen (tooltip `Choose an STTM workbook first`) and while running, where it reads `Live run in progress…`; click opens the cost confirmation modal (§2.4.5) |

Under the mock lock `available` is true and provider is `mock (locked)`: the button is live
and the modal says zero calls are made.

**Run progress**  [DEMO-DAY] — shown once `status.state !== "idle"`:

| Part | Shows |
|---|---|
| lead hint | running → `Running — stages appear as they start:`; done → `Last live run completed.`; failed → `Last live run FAILED — nothing was published.` |
| failed banner | red banner with `status.error` verbatim (`<<ExceptionType>>: <<message>>`; multi-line messages keep their lines); when `error_hint` exists, its `message` in a hint line and a secondary button `Choose companion FRD "<<doc id, middle-truncated to 36>>"` which selects that FRD (`POST /api/demo/frd {kind: "upstream", id}`) and reopens the chooser — never an automatic retry |
| stage list | one line per stage in the order the backend appended them: mark `✓` for every entry except the LAST while the state is `running`, which shows `⋯`; when the state is `done` or `failed` every entry shows `✓` (D5 — the failure is the banner above); bold stage name + ` — <<detail>>` in hint colour when a detail exists. Stage names and details are exactly those of BACKEND_SPEC §3: `extracting workbook` → `resolving contracts` → per feed `<<slug>>: compiling rules` → `<<slug>>: Layer-2 reasoning` (suffix ` (live)` when the provider is not mock) → `<<slug>>: emitting code` → `<<slug>>: framework artefacts` (framework/both only) → `<<slug>>: gate` → `publishing results`. The stage list is what the presenter narrates; keep the names |
| polling | after firing, poll `GET /api/demo/status` every 1 000 ms until `done` or `failed`; on either, refresh the past-runs list; on `done` refresh the shell's feeds and re-fetch the governance checks |
| View results → | primary button when `done`: if the status says the loaded run IS this run (`label == last_run_label` and `mode == "live"`) refresh feeds and navigate to `/`; otherwise load it through the past-run loader (`POST /api/demo/load-live-run`), then navigate |

**Past live runs**  [LATER] — subhead `Past live runs`. Hint `Completed live runs stay on disk
— reload one to restore its results (LIVE state, that run's real candidates) without spending
anything. These are this machine's run history, not the tracked replay fixtures.` (in the
rebuild "disk" is the outputs Volume; the copy is kept). Rows: name + `LIVE RUN` badge (+ red
pill `failed — not loadable` when incomplete); hint `<<timestamp>> · <<n>> feeds` or `no
results produced`; primary `Load` (disabled when incomplete, while any load is busy, or while
running; `Loading…` while busy) → `POST /api/demo/load-live-run {run}` → refresh feeds →
navigate to `/`. States `Scanning past runs…` / `No past live runs on this machine yet.`

#### 2.4.3 Modal — documents ("Attach…" / "Provide…")  [DEMO-DAY]

Two variants share one dialog; the scan re-runs on every open (`GET /api/demo/input-documents`).

| Variant | Title | Hints | Rows | Empty state | Footer |
|---|---|---|---|---|---|
| reference_documents | `Attach the reference documents` | `Filenames as they appear in the client SharePoint library, matched live against the configured input directories on every open. Drop a file there — or fetch it from the SharePoint library — and it will appear here.` | one per expected name: `✓` or `☐`, the name in a code span, hint `present` / `missing`; then `Display only in this build — wiring these into generation is the next step.` | `No reference documents configured (demo.input_documents in config/config.yaml).` when the expected list is empty | `Close` |
| frd | `Provide the real FRD contract` | `Currently in use: <<stand-in>> — an anonymized demo stand-in without the real file paths.` and `Scanned live from inputs/sharepoint — the landing folder sharepoint-fetch and the SharePoint picker deliver documents to.` (the rebuild scans `<<outputs_volume>>/uploads/` and `<<inputs_volume>>/frd/`; the copy's folder names are replaced by those two paths) | one amber row per match: `<<name>>` (code span) + hint `found — wiring into the generator is pending; runs do not consume it yet.` | `Not present. Fetch the real FRD contract (.contract.json) from the SharePoint library into inputs/sharepoint/ and it will appear here. Until then, runs use the demo stand-in.` (same path substitution) | `Close` |

`Scanning…` while the scan is pending.

#### 2.4.4 Modal — "Choose an STTM workbook" (the chooser, with the Volume-folder pair picker)  [DEMO-DAY]

Opened by both `Choose STTM…` and `Choose FRD…`. On open it re-fetches the workbook list,
the FRD choices and (LATER) the volumes listing. The modal's structure and copy are the
reference's; the two sections that listed the client's raw-document volumes are replaced by
the Volume-folder listing of `<<inputs_volume>>/sttm/` and `<<inputs_volume>>/frd/` — which
in the rebuild IS the local workbook list and the local-contract list, so those two sections
carry it. Sections, top to bottom:

| # | Section | Type | Enabled when | On action | Shows | Tag |
|---|---|---|---|---|---|---|
| 1 | Hint | text | always | — | `Scanned live from the local fixtures directory and the inputs/sharepoint, inputs/databricks and inputs/uploads landing folders — where the SharePoint picker, the volume fetch below and a from-device upload deliver documents.` — in the rebuild the folder names read `<<inputs_volume>>/sttm/`, `<<inputs_volume>>/frd/` and `<<outputs_volume>>/uploads/`; the sentence shape is kept | DEMO-DAY |
| 2 | Upload row | two secondary buttons + note | no upload in flight, not running | hidden file inputs (`accept=".xlsx"` / `.json`); `POST /api/demo/upload` (multipart `kind`, `file`) validates and selects in one motion; then re-fetch workbooks, status and FRD choices | `Upload STTM (.xlsx)…` (tooltip `Upload an STTM workbook (.xlsx) from this device; it is selected for the next run`) and `Upload FRD contract (.json)…` (tooltip `Upload an FRD contract JSON produced by the FRD→STTM agent; a raw .docx has no contract`); label flips to `Uploading…`; 11px note `Uploads land in <<outputs_volume>>/uploads/ on the outputs Volume.` (the reference note names a container folder wiped on restart; the rebuild stores uploads on the Volume, so the parenthesis is dropped) | DEMO-DAY |
| 3 | Workbooks in the inputs Volume | one full-width row-button per workbook | always | `POST /api/demo/workbook {name}` selects and **keeps the modal open** so the FRD section below can be confirmed; then re-fetch status and FRD choices | mono name (middle-truncated to 46 characters so the trailing ticket suffix stays visible; full name in `title`) + right chip `<<source>> · selected` (`<<source>>` = `sttm` for `<<inputs_volume>>/sttm/`, `uploads` for `<<outputs_volume>>/uploads/`; ` · selected` only on the chosen one); Excel lock files (`~$` prefix) are never listed; states `Scanning…` / `No .xlsx workbooks found in the input directories.` | DEMO-DAY |
| 4 | Volumes error call-out | amber call-out | the volumes listing answered 502 | `Retry` re-fetches | `**Databricks volumes unavailable.** <<message>>` + `Retry` button; a 503 hides sections 4–6 entirely (the rebuild's default until the raw-document volumes seam is built) | LATER |
| 5 | STTM workbooks in `<<catalog>>.<<schema>>` | list | the volumes listing answered | `Fetch` → `POST /api/databricks/fetch {volume, name}` (a paired STTM also fetches its companion FRD); a `fetched` row is a button that selects the local copy | hint `STTM workbooks in <<catalog>>.<<schema>> — fetch lands the file in inputs/databricks and it joins the list above:`; per document: name, meta `<<volume>> · <<size>> KB` (+ ` · differs from local copy`, + ` · includes companion FRD — fetched together`); state `fetched` → chip `Fetched ✓`; `fetchable` → button `Fetch`; `differs` → `Re-fetch`; `Fetching…` while busy | LATER |
| 6 | Companion FRDs in the volume (<<n>>) | collapsed disclosure | as 5 | `Fetch FRD` | hint `Fetching an FRD lands it in inputs/databricks for the documents card and contract use — an FRD is never choosable as the STTM.`; rows as 5 with meta ` · companion of an STTM above` when paired | LATER |
| 7 | FRD for this run | hint + rows | FRD choices answered | rows are buttons → `POST /api/demo/frd {kind, id}`; then re-fetch status and FRD choices | hint `**FRD for this run** — currently <<label>> (demo golden — default). Contracts come from the FRD→STTM agent; a document without a contract is not selectable.` (the parenthesis only when not `frd_chosen`); when `upstream_error` exists: 11px `FRD→STTM agent table unavailable: <<reason>>` (the rest still renders — in the rebuild this line reads the LATER reason until the upstream seam is built); then **upstream rows** (buttons): doc id + meta `from FRD→STTM agent · <<status>> · <<n>> feed(s) · audited <<ts>>`; right chip `companion FRD` (green) when explicitly paired, or amber `looks like a pair — confirm` when only heuristically suggested; nothing otherwise [LATER — empty in the rebuild until built]; then **local contract rows** (buttons): name + chip `local contract` — every `*.contract.json` under `<<inputs_volume>>/frd/` and `<<outputs_volume>>/uploads/` [DEMO-DAY]; then **no-contract rows** (NOT buttons): name + meta `no contract — run the FRD→STTM agent for this document first` — every `.docx` under `<<inputs_volume>>/frd/` whose stem has no contract [DEMO-DAY] | DEMO-DAY / LATER as marked |
| 8 | Footer button | button | always | closes | `Done` once an STTM is chosen, `Cancel` before | DEMO-DAY |

**Pair suggestion (from v1.1 §2.1, kept as a chip, never a block):** when both an STTM and
an FRD are explicitly chosen and their file stems share fewer than 3 underscore-separated
name parts, the FRD line in Step 1 shows the amber pill `These names do not look like a pair —
the FRD feeds must name the workbook's stage tables (SPEC 1.4). Inspect anyway; a mismatch
fails loudly.` This is informational; nothing auto-corrects. It joins the reference's
`frd_warning` pill (which covers the not-chosen-FRD case); the two are never shown together.

#### 2.4.5 Modal — cost confirmation  [DEMO-DAY]

Title `Generate a pipeline from this STTM?`. Body, in order:

| Part | Shows |
|---|---|
| input | `Input: <<workbook>>` (code span; `the configured STTM workbook` when the status carries no name) |
| provider sentence | provider `mock (locked)` → `This deployment is **locked to the mock provider** — the run makes **zero model calls** (deterministic mock candidates).`; provider `databricks_fmapi` → `This makes real, billed Claude calls through the Databricks serving endpoint:`; any other → `This makes real, billed Anthropic API calls:`; the two billed variants are followed by `**~<<calls>> calls · ≈ $<<cost, two decimals>> · ~<<seconds>>s**` from `status.estimates` (fallbacks `3`, `0.10`, `20` — D15) |
| isolation | `Output is isolated to its own run directory; the tracked replay fixtures and default output are never touched.` |
| documents note | `frd_chosen` → `Client documents in play: live runs on client STTM/FRD pairs are permitted only per the program's client-document process (<<program approver>>'s email approval). The demo CV golden remains the default rehearsal pair; mock runs need no approval.` (`<<program approver>>` from configuration `ui.client_document_approver`, D8); otherwise `Known input gap applies: a demo FRD without the real file paths — the run is real, the case it represents is not.` |
| buttons | `Confirm — run live` (primary) → `POST /api/demo/run-live {confirm: true}` then start polling; `Cancel` |

A 400 or 409 from the run route lands in the page's red error banner verbatim.

### 2.5 Demo mode (`/demo`) — the six-step guided tour  [LATER]

Centred column (max-width 880px). Head: kicker `GUIDED DEMO` (11px, accent, letter-spaced),
`h1` = current step title, right side `<<k>> / 6` counter + `Exit demo` link-button. A card
(min-height 380px, 14.5px text) holds the step. Footer nav: `← Back` (disabled on step 1),
six dot buttons (active = filled accent; each has the step title as tooltip and aria-label),
`Next →` or on the last step `Finish → dashboard`. **← / → arrow keys move between steps.**
The running example is the first feed with Layer-2 candidates, else the first feed.
`Loading…` until the feeds response exists; `Loading example feed…` inside a step until the
example feed loads.

| # | Title | Content |
|---|---|---|
| 1 | `What this is` | Lead `Approved spec documents go in. A tested Databricks ingestion pipeline — packaged as **one runnable notebook per feed** — comes out.` Four flow boxes with arrows: `Contracts` / `FRD + STTM, machine-readable, fingerprinted` → `Deterministic compiler` / `templates only — no AI in the generated code` → `Safety gate` / `lint, structure and tests decide the verdict` → `Pipeline + notebook` (accented) / `PySpark + Delta, provenance in every file`. Paragraph `The one place AI is used — free-text rules no regex can classify — its output is quarantined into a *review queue* a human must approve. It can never write into the pipeline itself.` Fact box `Right now: **<<n>>** feeds generated, **<<d>>/<<t>>** contract rules compiled deterministically. Everything you'll see next is live output, not a mock-up.` |
| 2 | `Contracts go in` | Lead `Nothing is generated from a conversation or a PDF. The input is a pair of **approved, machine-readable contracts** — and every generated file cites their fingerprints, so you can always prove where code came from.` Line `Running example: <<slug>> (<<source_system>>, segmented H/D/T file).` (the segmented clause only when segmented). KV: `FRD — what the feed is` (name + `sha256 <<hash>>`), `STTM — how columns map` (name + `synthetic stand-in` tag when synthetic + sha256). If synthetic: fact `Honesty on display: the real mapping workbook for this feed hasn't landed yet, so it uses a clearly-labeled synthetic stand-in — and the UI says so everywhere.` (D8: the reference sentence names a client feed; the rebuild's sentence is feed-neutral) |
| 3 | `Layer 1 — deterministic` | Lead `Every validation rule in the contract is classified by a **deterministic compiler** — pattern matching, not AI. Same contracts in, byte-identical code out, every single time.` A row of classification chips (dot + label + ` · <<n>>`) for every entry of `rule_counts`. A quote block for the first `mappable` outcome: `“<<rule_text>>”` then `→ became <<feature>>, grounded on the contract text *“<<grounding>>”*`. Fact `Rules the compiler can't safely map aren't guessed at — they're **flagged for a human** or handed to Layer 2. Next slide.` |
| 4 | `The safety gate` | Lead `Before anything ships, a gate runs lint, security scans, structural checks and the generated test suite. The verdict is **computed in code** — the AI never grades its own homework.` Gate check rows (as §2.3 panel 1); line `Verdict for <<slug>>: <<verdict chip>>`. Fact `**PASS_WITH_FLAGS** is the honest middle state: the code is clean, but something needs a human — an ambiguous contract rule, or an AI candidate awaiting review. All feeds sit here today, and that's correct behavior, not a failure.` |
| 5 | `What comes out` | Lead `The exit isn't a pile of files — each feed ships as **one clean, runnable Databricks notebook**: DDL, every pipeline module, and the job entrypoint, assembled in dependency order with provenance up top. Import it into Databricks and run top to bottom — each cell registers itself as pipeline.<module>, so the code runs unmodified. The module files and their pytest suites still exist underneath; the notebook is assembled from them at generation time, so it can never drift.` A row of buttons `<<slug>>.ipynb` per feed (selected = primary); the example feed is selected automatically. **Default state with S1–S6 (Option A absent):** the notebook box (46vh scroll area) shows the empty state `No notebook for <<slug>> — this run produced framework artefacts only (Option B). The notebook appears when a run uses output mode Notebook or Both.` and the fact line reads `The Option B deliverables for this feed — the two DDL files and the config rows workbook — are on the dashboard's Framework artefacts panel.` with a link to `/`. What makes the notebook appear: an `.ipynb` among the selected feed's `written_files`; then the box loads `GET /api/feeds/<<slug>>/file?path=<<slug>>.ipynb` (`Loading <<slug>>.ipynb…`), renders the notebook view, and the fact reads `This is the artifact an engineer hands to the platform team — also available on the feed's Notebook tab.` (link to `/feeds/<<slug>>?tab=notebook`). A fetch error renders the detail in a red banner |
| 6 | `Layer 2 — the human decision` | Lead `The demo ends where every run ends: with a **human decision**. Free-text rules no pattern could classify went to the AI in a sandbox — its suggestions landed here, in a review queue, **pending engineer approval**. Nothing merges into the pipeline until a person says so.` Two bullets: `Every suggestion must **quote the contract verbatim** — a grounding check rejects anything it can't find in the source text.` and `Approve or reject below — the decision is recorded; merging stays a manual step.` One quote block per candidate: `“<<rule_text>>”`, then classification badge + grounded pill + `provider: <<p>>` pill + rationale (or italic `provider returned no usable response — recorded as a failure, not hidden`), then `✓ Approve` / `✗ Reject` with the §2.3 toggle semantics and status `Pending engineer approval` / `Marked approved` / `Marked rejected`. Empty: fact `This feed had no ambiguous rules — the queue is empty.` Closing fact `<<p>> of <<c>> candidate(s) still pending for <<slug>> — the full queue lives on the Layer-2 review tab` (`candidate` singular when c is 1; link to `/feeds/<<slug>>?tab=candidates`) |

### 2.6 Shared component — "Publish to Unity Catalog volume" panel  [LATER]

Rendered on the Dashboard whenever `GET /api/databricks/publish-target` answers (it always
answers; the panel is hidden only if the call itself fails). Head `Publish to Unity Catalog
volume`, hint `the human gate for Databricks: reviewed artifacts land under
/Volumes/…/<feed>/ — never a side effect of generating`.

| Control | Type | Enabled when | On action | Shows |
|---|---|---|---|---|
| Catalog / Schema / Volume | three text inputs (170px) | always | trimmed on change | pre-filled from the target defaults |
| Feed | select of loaded slugs | always | — | the first slug by default |
| Publish… | primary button | `available` AND all four set | opens the confirm modal | `Publish…`; `Publishing…` while busy |
| status line (exactly one) | text | always | — | unavailable → `Publishing is unavailable here: <<reason>>` (the rebuild's default until built: reason `not built in this workspace — volume publish`); outside policy (`<<catalog>>.<<schema>>.` does not start with `writable_prefix`) → amber (D7: `#b45309`) `<<catalog>>.<<schema>>.<<volume>> is outside the writable policy — the backend only writes under <<prefix>>* and will refuse this target. Publishing never touches client schemas.`; otherwise → `Target: /Volumes/<<c>>/<<s>>/<<v>>/<<feed>>/ · policy: writes only under <<prefix>>*, enforced in code.` |
| result line | text | after success | — | `Published <<n>> artifact(s) to <<volume>> (volume created): <<a>>, <<b>>, <<c>>` (the parenthesis only when created) |
| error | red banner | a publish failed | — | the detail verbatim |
| confirm modal | modal | — | primary → `POST /api/databricks/publish` with `confirm: true` | title `Publish to the workspace?`; body `Writes <<feed>>'s report, notebook and framework artefacts to /Volumes/<<c>>/<<s>>/<<v>>/<<feed>>/ in Unity Catalog. Publishing is the review gate — do this only after looking at the feed's verdict. Files already there are not overwritten.`; buttons `Confirm — publish` (`Publishing…` while busy) / `Cancel` |

### 2.7 Shared component — "For <<client>>'s framework: metadata sheet preview"  [DEMO-DAY]

Subhead `For <<client>>'s framework: metadata sheet preview` (D8); the `layout_note` from the
backend as the hint; a tab strip (one button per sheet tab, label + row count in a hint span,
active = accent outline); a scrolling table of the active tab. **Every cell carries exactly
one provenance dot** (7px rounded square, `title` = badge label + ` — <<tooltip>>` when a
tooltip exists) and a matching background tint:

| Badge | Label | Tint / dot |
|---|---|---|
| from_sttm | `from STTM` | green 8% / green |
| from_sttm_unmapped | `from STTM (unmapped)` | green 14% / green with dark outline |
| from_frd | `from FRD` | blue 8% / accent |
| from_faq | `from FAQ` | violet 10% / `#7a5abe` |
| from_standards | `from standards` | teal 10% / `#14968c` |
| synthetic | `SYNTHETIC` | amber 14% / warning |
| needs_template | `NEEDS CLIENT TEMPLATE` | grey 12% / muted |

On a tab named `columns` a full-width feed-separator row (`<<slug>>` in a code span, bold,
page background) precedes each new feed's rows. Empty tab → the tab's `state` text or `no
rows`. Footer: `**<<d>> of <<t>>** values derived from documents · <<s>> synthesized · <<n>>
await the client template.`, a secondary `Download .xlsx` link (`/api/demo/metadata-sheet.xlsx`),
and the 11px disclaimer `Display only — the reviewed sheet is the approval artifact. On
approval the rows land in the ingestion framework database, and the generated DDL + insert
SQL are add-ons to <<client>>'s master notebook — the client's own notebook, never generated
or edited by the agent. The agent never inserts unapproved rows.`

In the rebuild the tabs are the seven IIG tabs of the loaded run's `config_rows.xlsx`
(SPEC 4.0 order) with each cell's badge read from the workbook's `_provenance` sheet; before
any run completes (boot failed, or no pairs configured) the route answers the configured
layout with empty tabs and `state` = `awaiting a run`.

### 2.8 Shared primitives  [DEMO-DAY]

- **VerdictChip:** pill, 12px weight 650, icon + label. `PASS` = check glyph, green tint;
  `PASS WITH FLAGS` = flag glyph, amber tint; `FAIL` = × glyph, red tint. **VerdictDot:** 8px
  circle in the status colour with the label as `title`.
- **ClassBadge:** outlined pill, 11.5px weight 600, 7px identity dot + label (`mappable`,
  `orchestration`, `notification`, `out of scope`, `flagged`, `unmapped → L2`).
- **StatTile:** surface card; 11.5px uppercase muted label; 26px weight 650 value; 12px hint.
- **Pill:** outlined 11.5px weight 600; variants `grounded` (green), `ungrounded` (red),
  `synthetic` (amber), `req-filled|partial|missing|not_captured`, `gc-verified|attention|pending_run`.
- **Buttons:** 13px weight 550, 8px radius, 7px×14px padding; `.primary` = deep accent fill,
  white text; `.approve` green outline; `.reject` red outline; disabled = 55% opacity with a
  tooltip naming why where this document gives one. Spinner = 13px ring.
- **Panel:** surface, 1px border, 10px radius; head (13px×18px padding, hairline below, `h2`
  14px + right-aligned 12px muted hint); body 16px×18px. Sub-head = uppercase 12px weight 700
  with a hairline above (used inside the generate card).
- **Modal:** fixed overlay `rgba(15,23,32,.45)`; dialog white, 12px radius, 22px×24px
  padding, width `min(460px, 100vw − 32px)`, max-height 80vh with internal scroll;
  `role="dialog" aria-modal`.
- **Tables:** the data table (13px, uppercase 11.5px muted headers, hairline rows) for rules;
  the source-files table (12px, nowrap cells, one prose column at 240–340px) inside a
  horizontally scrolling container.
- **Empty state:** centred muted 13.5px with 48px vertical padding.
- **Error banner:** red 8% tint, red 35% border, critical text, 8px radius.
- **Synthetic tag:** 10.5px uppercase weight 700, burnt-orange text and outline, 4px radius.
- **HITL row:** amber 10% background block; **HITL tag:** 10px weight 750 warning-filled pill.
- **Shell block:** dark sidebar palette, mono, clickable summary.
- **Middle truncation** for file names: keep the last 16 characters (the ticket/copy suffix
  distinguishes files), elide the middle with `…`, full name in `title`.
- **Stage list:** mono marks `✓` / `⋯`, bold stage name, ` — detail` in the muted colour.
- **DDL / text previews:** mono, no wrapping, horizontal scroll, the entire file, 12–13px.

---

## Part 3 — API contract the screens depend on (rewritten for the rebuild)

All routes are same-origin under `/api`. A non-2xx response carries `{detail: string}`;
the client throws an error carrying the HTTP status so callers can distinguish 503
(unconfigured or not built → hide the section) from 502 (refused → show the message + Retry).
`POST` bodies are JSON unless noted. Every `detail` string below is verbatim; `'<<x>>'` means
the value rendered inside single quotes (repr, SPEC 0). Every route table names what the route
reads or writes on the Volume, the generator step it runs (prose) and the SPEC or ACCEPTANCE
section that defines that step. A route tagged LATER with no S1–S6 backing is specified
against the run directory alone; until it is built it answers `503` with detail
`not built in this workspace — <<feature>>` and the UI hides its section (doctrine 4).

Global: when the backend failed to load its configuration at start-up, `/api/feeds` still
answers 200 (D13) and every other route answers `503` `pipeline unavailable — <<error>>`.

Volume layout the routes address (full table in BACKEND_SPEC §2.4):

```
<<inputs_volume>>/frd/          FRD contracts (*.contract.json) and, optionally, .docx without a contract
<<inputs_volume>>/sttm/         STTM workbooks (*.xlsx)
<<inputs_volume>>/standards/    reference documents (names from configuration demo.input_documents.expected)
<<inputs_volume>>/replay/       tracked replay sets                                   [LATER]
<<outputs_volume>>/uploads/     from-device uploads (both kinds)
<<outputs_volume>>/faq/         <<feed_slug>>.faq.yaml — the live answer store
<<outputs_volume>>/state/       decisions.json (v2)
<<outputs_volume>>/runs/mock/   the mock run (label null), rewritten by every mock generate
<<outputs_volume>>/runs/<<run_id>>/   one directory per live run (BACKEND_SPEC §2.4)
```

### 3.1 Run state and generation

| Route | Purpose · reads/writes · generator step · SPEC | Codes and exact details | Tag |
|---|---|---|---|
| `GET /api/feeds` | The loaded run: `{feeds[], failures[], mode, label}` (shapes §3.9). Reads the in-memory run state; nothing on the Volume. No generator step. | 200 always; when start-up failed: `{feeds: [], failures: [{label: "startup", error: "pipeline unavailable — <<error>>"}], mode: "mock", label: null}` (D13) | DEMO-DAY |
| `GET /api/feeds/{slug}` | `FeedDetail` (summary + contracts, tables, semantics, outcomes, candidates with review, written_files). Reads the run state and the decisions file for the current run key. | 404 `no generated feed named '<<slug>>'` | DEMO-DAY |
| `POST /api/generate` `{feed_slug?, dry_run, skip_tests}` | Mock regenerate over the CONFIGURED pairs (`contracts.pairs`; one feed when `feed_slug` is given). The body's `dry_run` is ignored — this route is always mock. Writes `<<outputs_volume>>/runs/mock/` (rewritten). Generator: for each pair, extract the workbook when the pair names an `.xlsx` (SPEC 1.1–1.4, S1) into `runs/mock/extracted/<<stem>>.contract.json`, resolve (1.5–1.7, S1), then per feed compile rules (5.1), Layer 2 with the mock provider (5.2), FAQ + prefills read from `<<outputs_volume>>/faq/` (1.8), the two DDL files (2, 3; S1, S2), the IIG workbook (4; S3, S4, S5), flags + verdict + report (5.3–5.5; S5). A pair that fails to resolve becomes a `failures` entry `{label: "<<frd file>> + <<sttm file>>", error}`; a feed with a template gap becomes `{label: <<feed_id>>, error: "template gap: <<message>>"}` (5.4). Mode → `mock`, label → `null`. Returns the feeds response. | 409 `config.contracts.pairs is empty — nothing to generate. Restore anonymized contract pairs in config/config.yaml, or load a replay set / past live run instead.`; 404 `no resolved feed matches '<<slug>>'` (D3) | DEMO-DAY |
| `GET /api/feeds/{slug}/file?path=` | `{path, content}` — UTF-8 text of one generated file; `path` is relative to the feed's directory under the CURRENT run's root; containment enforced (the resolved target must stay inside the feed directory). Reads the Volume copy. | 404 `no generated feed named '<<slug>>'`; 400 `path escapes feed directory: <<path>>`; 404 `file not found: <<path>>`; 400 `not a text file: <<path>> — use the download route` (D11, new) | DEMO-DAY |
| `GET /api/feeds/{slug}/download?path=` | Binary download with `Content-Disposition: attachment; filename="<<name>>"`; media type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` for `.xlsx`, `text/plain; charset=utf-8` for everything else. Same containment. | 404 / 400 / 404 as above | DEMO-DAY |
| `GET /api/feeds/{slug}/report` | `{markdown}` — `reports/<<slug>>.md` of the current run (SPEC 5.5). | 404 `no report for '<<slug>>'` | DEMO-DAY |
| `POST /api/feeds/{slug}/candidates/{index}/decision` `{decision, note?}` | Records `pending | approved | rejected` for candidate `index` of the feed under the current run key → `{feed_slug, index, review: {decision, note}}`. Writes `<<outputs_volume>>/state/decisions.json` (shape D14). No generator step; the artifact `candidates/candidates.json` (SPEC 5.2) is never modified. | 404 `no generated feed named '<<slug>>'`; 404 `candidate index <<index>> out of range` | LATER |
| `POST /api/decisions/reset` | Clears the CURRENT run key's decisions only → the feeds response. Writes the decisions file. | 200 | LATER |

**Run-key rule:** `run_key` = the loaded label, or `mock` when the label is null; decisions
made under one key never bleed into another.

### 3.2 Pair inspection and the load-pattern FAQ (new in v2)

| Route | Purpose · reads/writes · generator step · SPEC | Codes and exact details | Tag |
|---|---|---|---|
| `POST /api/demo/inspect` (empty body) | Extract + resolve the chosen pair WITHOUT generating: extract the chosen workbook against the chosen (or default) FRD into a scratch contract (SPEC 1.1–1.4; the extract summary `<<n>> feed(s): <<feed_id>> (<<k>> fields), …` of 5.4), resolve (1.5–1.7), then compute the FAQ prefills per feed as if no FAQ file existed (1.8) and merge the answers on file. Returns `InspectResponse` (§3.9). Writes nothing on the Volume (scratch only). | 400 `no STTM workbook chosen — choose one first`; 409 `cannot inspect while a live run is in progress`; 400 `extracting workbook — <<message>>` (the SPEC 1.1–1.4 message verbatim, multi-line kept); 400 `resolving contracts — <<message>>` (the SPEC 1.5–1.7 / 5.4 mismatch text verbatim, one line per disagreement starting with two spaces and `- `) | DEMO-DAY |
| `GET /api/demo/faq/{slug}` | `FaqForm` for one inspected feed: the eight questions and two companions with the current value, source, evidence, the generator default, whether the value is a contract prefill, and the allowed options; plus the counts line. Reads `<<outputs_volume>>/faq/<<slug>>.faq.yaml` when present (SPEC 1.8 loader; an invalid file is reported, never guessed). | 404 `no inspected feed named '<<slug>>' — inspect the pair first`; 400 `FAQ file <<path>> is not a YAML mapping` / the loader's unknown-key message verbatim | DEMO-DAY |
| `PUT /api/demo/faq/{slug}` `{answers: {<<question>>: {value, source, evidence?}}}` | Writes `<<outputs_volume>>/faq/<<slug>>.faq.yaml` per the §2.4.2 writing rules (SPEC 1.8 file shape: `schema_version: 1` then one mapping per answered key; `yes`/`no`/numbers quoted); an EMPTY `answers` map deletes any existing file for the feed. Returns `{saved: bool, file: "<<slug>>.faq.yaml" | null, message}` where message is `Saved <<slug>>.faq.yaml` or `No answers set — the generator will use defaults and flag every question`; the response also carries the refreshed `FaqForm`. | 404 as above; 409 `cannot change inputs while a live run is in progress`; 400 `unknown FAQ key '<<key>>'`; 400 `answer '<<question>>' has no value`; 400 `answer '<<question>>' with source 'frd' needs evidence` | DEMO-DAY |

### 3.3 Live run (the only path that can bill)

| Route | Purpose · reads/writes · generator step · SPEC | Codes and exact details | Tag |
|---|---|---|---|
| `GET /api/demo/live-available` | `{available, provider, reason}` — provider is `mock (locked)` when the force-mock switch is set (then `available: true`, `reason: ""`), else the configured provider name (`databricks_fmapi`, `anthropic`) with `available` false and a remedy in `reason` when it cannot resolve: `Databricks workspace config does not resolve` / `databricks.serving_endpoint is not configured` / `no ANTHROPIC_API_KEY in the backend env`; `provider: null` and reason `backend has no config loaded` when start-up failed. SPEC 5.2 provider selection. | 200 | DEMO-DAY |
| `POST /api/demo/run-live` `{confirm: true}` | Starts the background run on the chosen pair and returns `DemoStatus` at once. Generator, in stage order (BACKEND_SPEC §3): mint `<<run_id>>`; create `<<outputs_volume>>/runs/<<run_id>>/`; copy the FRD in as `frd.contract.json`; write `run_meta.json`; copy `<<outputs_volume>>/faq/<<slug>>.faq.yaml` for the pair's feeds into `faq/`; extract the workbook into `extracted_sttm.contract.json` (SPEC 1.1–1.4); resolve (1.5–1.7); per feed compile rules (5.1) → Layer 2 with the selected provider (5.2; mock under the lock) → the two DDL files + the IIG workbook (2–4) → flags, verdict, report (5.3–5.5); adopt the results as the loaded run (mode `live`, label `<<run_id>>`). One failed feed does not sink the run (5.4 scoping); zero completed feeds fails the run with `RuntimeError: live run produced no feeds — <<slug>>: <<error>>; …` (`no feeds resolved` when none). Under the mock lock the run makes zero model calls and the candidate cards read `provider: mock`. | 400 `live run requires explicit confirm: true (billed API calls)`; 400 `live run unavailable: <<reason>>`; 409 `a live demo run is already in progress` (D12) | DEMO-DAY |
| `GET /api/demo/status` | `DemoStatus` (§3.9): runner `state idle|running|done|failed`, `stages[{stage, detail, at}]`, `error` (`<<ExceptionType>>: <<message>>`), `error_hint`, `last_run_label`; plus the loaded run's `mode`, `label`; `estimates {calls, cost_usd, seconds}` from configuration (`demo.estimated_calls`, `demo.estimated_cost_usd`, `demo.estimated_seconds`); `sttm_workbook` (file name of the effective workbook), `sttm_chosen`, `output_mode` (the override or the configured default), `output_modes_available` (new in v2: `["framework"]` until an Option A emitter exists), `frd_name` (the chosen label or the configured default's file name), `frd_chosen`, `frd_warning`. | 200 | DEMO-DAY |
| `POST /api/demo/output-mode` `{mode | null}` | Sets the override (`notebook | framework | both`; null = the configured default) → `DemoStatus`. In memory only. | 400 `unknown output mode '<<mode>>'`; 409 `cannot change the output mode while a live run is in progress` | DEMO-DAY (`framework`) / LATER (`notebook`, `both`) |

`error_hint` = `{sttm, frd_used, candidate_doc_id, message}` — set only when the extract
failed with a feed-match message (`matches 0 FRD feeds`) AND a companion FRD is known
(explicit pairing map first, then the ≥3-token stem heuristic); `message` reads `This run used
FRD '<<frd_used>>'. A companion FRD '<<candidate>>' is available from the FRD→STTM agent;
choose it in the STTM picker.` In the rebuild the candidate set is the local contract list
(`<<inputs_volume>>/frd/`), so the hint exists DEMO-DAY without the upstream seam.

`frd_warning` = an STTM is explicitly chosen AND its name differs from the configured
default workbook's name AND no FRD is explicitly chosen.

### 3.4 Choosing inputs

| Route | Purpose · reads/writes · generator step · SPEC | Codes and exact details | Tag |
|---|---|---|---|
| `GET /api/demo/workbooks` | `{workbooks: [{name, source, selected}]}` — every `*.xlsx` under `<<inputs_volume>>/sttm/` (source `sttm`) and `<<outputs_volume>>/uploads/` (source `uploads`), sorted by name within each folder, lock files (`~$`) skipped, duplicates by name skipped; `selected` is true ONLY for an explicit pick. No generator step. | 200 | DEMO-DAY |
| `POST /api/demo/workbook` `{name}` | Select by NAME from the scanned folders (never a raw path) → `{workbooks}`. In memory only. | 404 `no STTM workbook named '<<name>>' in <<inputs_volume>>/sttm/ or <<outputs_volume>>/uploads/`; 409 `cannot change the STTM while a live run is in progress` | DEMO-DAY |
| `DELETE /api/demo/workbook` | Back to `none chosen` → `{workbooks}`. | 409 as above | DEMO-DAY |
| `GET /api/demo/frd-choices` | `{sttm, current{label, chosen}, upstream[], upstream_error, local[], no_contract[]}` — `local` = sorted names of `*.contract.json` under `<<inputs_volume>>/frd/` and `<<outputs_volume>>/uploads/`; `no_contract` = `.docx` files under `<<inputs_volume>>/frd/` whose stem has no contract; `upstream` = rows from the FRD→STTM agent's contracts table with `paired` (explicit pairing map) / `suggested` (heuristic) flags. Until the upstream seam is built: `upstream: []`, `upstream_error: "not built in this workspace — upstream contracts table"` (reported inline, never as an error). | 200 | DEMO-DAY (local, no_contract) / LATER (upstream) |
| `POST /api/demo/frd` `{kind: "upstream" \| "local", id}` | `local`: select the named contract from the two folders → `{selected: <<id>>, kind: "local", feeds: null}`. `upstream`: materialise the contract from the upstream table into `<<outputs_volume>>/uploads/` and select it → `{selected, kind: "upstream", audited_at, feeds: [{feed_name, stage, standard}]}`. In memory selection. | 400 `invalid contract name '<<id>>'` (a separator or `..` in the name); 404 `no local contract named '<<id>>'`; 400 `unknown kind '<<kind>>'`; 409 `cannot change the FRD while a live run is in progress`; 502 the upstream transport's message; `upstream` answers 503 `not built in this workspace — upstream contracts table` until built | DEMO-DAY (local) / LATER (upstream) |
| `DELETE /api/demo/frd` | Back to the configured default → `{selected: null}`. | 409 as above | DEMO-DAY |
| `POST /api/demo/upload` multipart `kind=sttm\|frd`, `file` | Stores the file under `<<outputs_volume>>/uploads/` (write-then-rename) and selects it in one motion → 201 `{stored: <<name>>, kind, selected: true}`. An FRD upload must parse as an FRD contract (SPEC 1.6); its name is normalised to end in `.contract.json`. | 409 `cannot change inputs while a live run is in progress`; 400 `invalid file name '<<name>>'` (empty, `~$` prefix or `..`); 413 `'<<name>>' exceeds the 25 MiB upload cap`; 400 `'<<name>>' is empty`; 400 `an STTM upload must be a .xlsx workbook, got '<<name>>'`; 400 `an FRD upload must be a .contract.json produced by the FRD→STTM agent, got '<<name>>'`; 400 `not a valid FRD contract: <<first validation line, at most 200 characters>> — run the FRD→STTM agent to produce one`; 400 `unknown upload kind '<<kind>>'` | DEMO-DAY |

Pairing precedence (backend, for `paired` / `suggested` / `error_hint`): explicit
`demo.pairing_map` (canonical stems) → shared ticket number → the ≥3-token stem heuristic
**as a suggestion only**, never auto-paired.

### 3.5 Replay sets and past runs  [LATER]

| Route | Purpose · reads/writes · generator step · SPEC | Codes and exact details | Tag |
|---|---|---|---|
| `GET /api/replay/sets` | `{sets: [{name, date, feeds[], has_call_log}]}` from `<<inputs_volume>>/replay/<<name>>/` (a set = a directory with ≥1 `<<feed_slug>>/candidates.json`; `date` parsed from a trailing `YYYYMMDD`). | 200 (`[]` when the folder is absent) | LATER |
| `POST /api/replay/load` `{set}` | Re-run the deterministic pipeline on the configured default pair with the recorded candidates injected in place of Layer 2 (SPEC 5.2 artifact shape), writing `<<outputs_volume>>/runs/replay_<<set>>/`; mode → `replay`, label → the set name → the feeds response. Needs a generator entry point that accepts a candidate override — not in S1–S6; until then 503. | 404 `no replay set named '<<set>>' under fixtures/replay/`; 500 `contract pair failed to resolve: <<message>>` (D1) | LATER |
| `GET /api/demo/live-runs` | `{runs: [{name, timestamp, feeds[], complete}]}` — every `demo_*` directory under `<<outputs_volume>>/runs/`, newest first; a feed counts when its directory holds a `framework/` directory, a `ddl/` directory, a `README.md` or `candidates/candidates.json`; `complete` = at least one feed; `timestamp` = `YYYY-MM-DD HH:MM:SS` parsed from the name. Reads the Volume listing only. | 200 | LATER |
| `POST /api/demo/load-live-run` `{run}` | Restore a completed past run as the loaded run (mode `live`, label = the run name) from its OWN directory: its `frd.contract.json`, `extracted_sttm.contract.json`, `run_meta.json` (`output_mode`; inferred from the feed directories for older runs). Against the run directory alone: read each feed's report (verdict, flags, gate table), `candidates/candidates.json`, and `framework/` listing; no generator re-run. | 404 `no past live run named '<<run>>' under runs/`; 400 `live run '<<run>>' failed before producing results — cannot load` (D2); 400 `contract pair failed to resolve: <<message>>` | LATER |

### 3.6 Request-time display and checks (never alter generated output)

| Route | Purpose · reads · SPEC | Codes | Tag |
|---|---|---|---|
| `GET /api/demo/input-documents` | `{documents: [{kind: "reference_documents", expected[], present[{name, path}], missing[]}, {kind: "frd", matches[], stand_in}]}` — a live scan of `<<inputs_volume>>/standards/` against `demo.input_documents.expected` (case-insensitive; a leading numeric upload prefix stripped); `frd.matches` = `*.contract.json` under `<<outputs_volume>>/uploads/`; `stand_in` = the configured default FRD's file name. | 200 | DEMO-DAY |
| `GET /api/demo/source-files` | `{frd_contract, feeds[], shell_listing[], shell_mode live\|synthetic, shell_reason, shell_source, shell_listed_at, convention_check\|null}` rendered from the effective FRD (landing roots from `demo.source_files.landing_root_template`; SPEC 0.1). | 404 when the FRD file is absent (D10); 503 until built | LATER |
| `GET /api/demo/metadata-sheet` / `…/metadata-sheet.xlsx` | `{layout_note, run_label, tabs{<<name>>: {headers, rows[{values, badges, feed_slug}], state}}, coverage}` — the seven IIG tabs of every loaded feed's `config_rows.xlsx` merged in workbook order, badges from each workbook's `_provenance` sheet (SPEC 4.0); `.xlsx` = the same content as one downloadable workbook (`Content-Disposition` attachment, file name `metadata_sheet_<<label or mock>>.xlsx`). Before any run: the configured tab layout with empty rows and `state: "awaiting a run"`. | 404 when the configured default FRD file is absent (D10) | DEMO-DAY |
| `GET /api/demo/input-requirements` | `{check{source, rows[{row, how_to_fill, status, feeds}], summary}, document_check{source, rows, summary}, reason}` — the eleven rows of the input-requirements deck read live. | 503 until built | LATER |
| `GET /api/demo/governance-checks` | `{checks[{control, deck, status, evidence}], summary, absent_decks[]}` — the two architecture decks read live and evaluated against the loaded run. | 503 until built | LATER |

### 3.7 Databricks volumes seam  [LATER]

| Route | Purpose | Codes and exact details |
|---|---|---|
| `GET /api/databricks/documents` | `{catalog, schema, documents{frd[], sttm[]}}`; each `{name, size, volume, state fetchable\|fetched\|differs, local_name?, companion_frd?, paired?}` — the client's raw-document volumes, deduped server-side against the local folders. | 503 unconfigured / not built (hide); 502 the workspace's message (show + Retry) |
| `POST /api/databricks/fetch` `{volume, name}` | Download one document into the local landing folder → `{fetched, dest}`. | 400 `unknown volume '<<volume>>'`; 502 |
| `GET /api/databricks/publish-target` | Always answers `{available, reason, catalog?, schema?, volume?, writable_prefix}`; until built `{available: false, reason: "not built in this workspace — volume publish", writable_prefix: "<<prefix>>"}`. | 200 |
| `POST /api/databricks/publish` `{confirm: true, feed_slug, catalog, schema_name, volume, force?}` | Upload the feed's report + notebook (when one exists) + framework artefacts under `<<volume>>/<<feed>>/` → `{published: true, volume, volume_created, artifacts[{name, path, size_bytes}]}`. | 400 `publishing writes to a Unity Catalog volume and requires an explicit {"confirm": true}`; 503 `pipeline unavailable`; 404 `no generated feed named '<<slug>>'`; 404 `nothing to publish for '<<slug>>' — generate the feed first`; 400 the writable-prefix refusal text; 502 transport |

### 3.8 SharePoint seam  [LATER — backend only; no panel in the reference frontend]

| Route | Purpose | Codes and exact details |
|---|---|---|
| `GET /api/sharepoint/config` | `{configured, site, library, input_folder, output_folder}`; never raises (`configured: false` with nulls when unconfigured). | 200 |
| `GET /api/sharepoint/documents` | `{site, library, folder, documents[{item_id, name, size_bytes, modified, web_url}]}`. | 503 config text / `pipeline unavailable — no generation store bound`; 502 `SharePoint sign-in failed (<<code>>). Check the app registration, its client secret, and admin consent.` (+ ` Graph request-id <<id>>.`); 502 `Could not list '<<library>>' (<<code>>). The app registration may lack read access to this site.` |
| `POST /api/sharepoint/import` `{item_id, name}` | 201 `{path, name, stem, kind workbook\|contract, source: "sharepoint", size_bytes}` — the file lands in the local landing folder and joins the ordinary STTM list. | 400 `document has no filename`; 400 `only ['.json', '.xlsx'] can be consumed — an STTM workbook (.xlsx) or a contract (.json)`; 502 `Could not download '<<name>>' from SharePoint (<<code>>).`; 413 `<<name>> is <<n>> bytes; the cap is 26214400` |
| `POST /api/sharepoint/locate` `{name}` | Exact (case-insensitive, extension optional) match → `{status: "ready", document, already_published[]}`; several partial matches → `{status: "candidates", candidates[]}` for the human to pick; never a best-match auto-pick. | 400 `give the document's name`; 404 `No document named '<<name>>' in <<library>>/<<folder or <root>>> (<<n>> document(s) there).`; 502 `Could not list '<<library>>' (<<code>>).`; 502 `Found '<<name>>', but could not check the output folder (<<code>>).` |
| `GET /api/sharepoint/artifact/{item_id}` | Serve an already-published artifact (must be in the output folder's current listing) as `application/octet-stream`. | 404 `no such artifact in the SharePoint output folder`; 502 `Could not list the output folder (<<code>>).`; 502 `Could not download '<<name>>' (<<code>>).` |
| `POST /api/sharepoint/publish` `{feed_slug, path?, confirm: true}` | Publish ONE feed's report + notebook (or one named file) under qualified names → `{published: true, feed_slug, artifacts[{name, size_bytes, web_url}], target}`. | 400 `publishing writes to the client's SharePoint library and requires an explicit {"confirm": true}`; 404 `no generated feed named '<<slug>>'`; 400 `path escapes the feed directory: <<path>>`; 404 `nothing to publish for '<<slug>>': <<missing names>> — generate the feed first`; 413 or 502 `Could not publish '<<name>>' to SharePoint (<<code>>).` |

A rebuild that adds a SharePoint panel mirrors the chooser exactly (list → fetch to the
landing folder → the file joins the ordinary STTM list); there is deliberately no second
"generate from SharePoint" path.

### 3.9 Type shapes (verbatim — the contract the frontend is built on)

```ts
type Verdict = "PASS" | "PASS_WITH_FLAGS" | "FAIL";
type Classification = "mappable" | "orchestration_config" | "notification"
                    | "out_of_scope" | "flagged" | "unmapped";
type RunMode = "mock" | "live" | "replay";
type OutputMode = "notebook" | "framework" | "both";
type Decision = "pending" | "approved" | "rejected";

interface GateCheck { name: string; passed: boolean; details: string }
interface FeedSummary {
  feed_slug: string; feed_id: string; feed_name: string; source_system: string;
  lobs: string[]; file_format: string; frequency: string | null; segmented: boolean;
  sttm_is_synthetic: boolean; verdict: Verdict; flags: string[]; checks: GateCheck[];
  rule_counts: Partial<Record<Classification, number>>; rule_total: number;
  candidate_count: number; candidates_pending: number; files_written: number;
  framework: { files: string[]; row_counts: Record<string, number>;
               coverage: { derived: number; synthetic: number; needs_template: number; total: number };
               flagged_blank_columns: string[] } | null;
}
interface FeedsResponse { feeds: FeedSummary[]; failures: { label: string; error: string }[];
                          mode: RunMode; label: string | null }
interface RuleOutcome { feed_id: string; rule_text: string; classification: Classification;
                        feature: string | null; grounding: string; notes: string | null }
interface CandidateResponse { classification: "mappable" | "orchestration_config" | "notification" | "out_of_scope";
                              code_candidate: string | null; rationale: string; citations: string[] }
interface Candidate { index: number; feed_id: string; rule_text: string; provider: string;
                      response: CandidateResponse | null; grounded: boolean; failure_notes: string[];
                      review: { decision: Decision; note: string | null };
                      kind?: string; detail?: string | null; citation?: string | null }
interface FeedDetail extends FeedSummary {
  delimiter: string; file_name_patterns: string[]; landing_location: string | null;
  natural_key_columns: string[]; not_null_columns: string[]; phi_columns: string[];
  load_windows_sla: string[];
  contracts: { frd_name: string; frd_sha256: string; sttm_name: string; sttm_sha256: string; sttm_is_synthetic: boolean };
  tables: { stage: string[]; standard: string | null; errors: string; processed_files: string; recycle: string | null };
  outcomes: RuleOutcome[]; candidates: Candidate[]; written_files: string[];
}
```

Verbatim shapes of the other routes (from the reference client):

```ts
interface ReplaySet { name: string; date: string | null; feeds: string[]; has_call_log: boolean }
interface DemoStage { stage: string; detail: string; at: number }
interface DemoStatus {
  state: "idle" | "running" | "done" | "failed"; stages: DemoStage[]; error: string | null;
  last_run_label: string | null; mode: RunMode; label: string | null;
  estimates: { calls: number; cost_usd: number; seconds: number };
  sttm_workbook?: string; sttm_chosen?: boolean; output_mode?: OutputMode;
  frd_name?: string; frd_chosen?: boolean; frd_warning?: boolean;
  error_hint?: { sttm: string; frd_used: string; candidate_doc_id: string; message: string } | null;
}
interface FrdChoice { doc_id: string; status: string; n_feeds: string; audited_at: string; paired: boolean; suggested: boolean }
interface FrdChoicesResponse { sttm: string; current: { label: string; chosen: boolean };
                               upstream: FrdChoice[]; upstream_error: string | null; local: string[]; no_contract: string[] }
interface SttmWorkbook { name: string; source: string; selected: boolean }
interface InputDocumentScan { kind: string; matches?: string[]; stand_in?: string;
                              expected?: string[]; present?: { name: string; path: string }[]; missing?: string[] }
interface SourceFileValue { value: string; synthetic: boolean }
interface SourceFileFeed { feed_name: string; landing_root: SourceFileValue; file_name_patterns: string[];
                           file_format: string | null; delimiter: string | null; frequency: string | null;
                           stage_target: string | null; standard_target: string | null;
                           load_strategy: { stage: string; standard: string; synthetic: boolean } }
interface ConventionCheck { source: string; adls_location?: string; target_schema?: string;
                            load_strategy_stg?: string; load_strategy_std?: string; object_format?: string }
interface SourceFilesResponse { frd_contract: string; feeds: SourceFileFeed[]; shell_listing: string[];
                                shell_mode: "live" | "synthetic"; shell_reason: string | null;
                                shell_source: string | null; shell_listed_at: string | null;
                                convention_check: ConventionCheck | null }
interface DatabricksDocument { name: string; size: number; volume: string; state: "fetchable" | "fetched" | "differs";
                               local_name?: string; companion_frd?: string; paired?: boolean }
interface DatabricksDocumentsResponse { catalog: string; schema: string;
                                        documents: { frd: DatabricksDocument[]; sttm: DatabricksDocument[] } }
interface DatabricksPublishTarget { available: boolean; reason: string; catalog?: string; schema?: string;
                                    volume?: string; writable_prefix: string }
interface DatabricksPublishResult { published: boolean; volume: string; volume_created: boolean;
                                    artifacts: { name: string; path: string; size_bytes: number }[] }
type RequirementStatus = "filled" | "partial" | "missing" | "not_captured";
interface InputRequirementRow { row: string; how_to_fill: string; status: RequirementStatus; feeds: Record<string, RequirementStatus> }
interface InputRequirementsResponse { check: { source: string; rows: InputRequirementRow[]; summary: Record<RequirementStatus, number> } | null;
                                      document_check: { source: string; rows: { row: string; status: RequirementStatus }[]; summary: Record<string, number> } | null;
                                      reason: string | null }
type GovernanceStatus = "verified" | "attention" | "pending_run";
interface GovernanceCheck { control: string; deck: string; status: GovernanceStatus; evidence: string }
interface GovernanceChecksResponse { checks: GovernanceCheck[]; summary: Record<GovernanceStatus, number>; absent_decks: string[] }
type ProvenanceBadge = "from_sttm" | "from_sttm_unmapped" | "from_frd" | "from_faq" | "from_standards" | "synthetic" | "needs_template";
interface MetadataSheetRow { values: Record<string, string | number>; badges: Record<string, { badge: ProvenanceBadge; tooltip?: string }>; feed_slug?: string }
interface MetadataSheetTab { headers: string[]; rows: MetadataSheetRow[]; state?: string }
interface MetadataSheetResponse { layout_note: string; run_label: string | null; tabs: Record<string, MetadataSheetTab>;
                                  coverage: { derived: number; synthetic: number; needs_template: number; total: number } }
interface PastLiveRun { name: string; timestamp: string | null; feeds: string[]; complete: boolean }
interface LiveAvailability { available: boolean; provider: string | null; reason?: string }
```

Additions in v2 (new routes and one new status field; everything above is unchanged):

```ts
interface DemoStatusV2 extends DemoStatus { output_modes_available: OutputMode[] }   // ["framework"] until Option A exists
interface InspectFeed { feed_id: string; feed_slug: string; stage_tables: string[];
                        standard_table: string | null; rule_count: number }
interface InspectResponse { sttm: string; frd: string; contract_file: string;
                            summary: string;                    // "<<n>> feed(s): <<feed_id>> (<<k>> fields), …"
                            feeds: InspectFeed[]; faq: Record<string, FaqForm> }
interface FaqAnswer { name: string; value: string | null; source: "engineer" | "frd" | "contract" | "unknown";
                      evidence: string | null; default: string; prefilled: boolean; options: string[] }
interface FaqForm { feed_slug: string; file_present: boolean; questions: FaqAnswer[];   // the eight, in SPEC 1.8 order
                    companions: FaqAnswer[];                                             // has_header, has_trailer
                    counts: { from_contract: number; answered_here: number; unanswered: number } }
interface FaqSaveResult { saved: boolean; file: string | null; message: string; form: FaqForm }
```

---

## Part 4 — Design values, copy bank, platform notes

The acceptance checklist that closed the reference specification now lives in
`ACCEPTANCE/S7_ui.md` as numbered checks.

### 4.1 Design values (light theme only; the App renders light)

| Token | Value | Use |
|---|---|---|
| `--page` | `#f9f9f7` | body background |
| `--surface` | `#fcfcfb` | cards, panels, buttons |
| `--ink` / `--ink-2` / `--muted` | `#0b0b0b` / `#52514e` / `#898781` | text hierarchy |
| `--hairline` / `--border` | `#e1e0d9` / `rgba(11,11,11,.1)` | dividers / card borders |
| `--accent` / `--accent-deep` | `#2a78d6` / `#1c5cab` | links, active tabs, primary buttons (hover `#174e91`) |
| `--good` / `--good-text` | `#0ca30c` / `#006300` | PASS, verified, grounded |
| `--warning` / `--warning-text` | `#fab219` / `#7a5300` | PASS_WITH_FLAGS, synthetic, attention, HITL |
| `--critical` / `--critical-text` | `#d03b3b` / `#8f2222` | FAIL, ungrounded, errors |
| `--amber` | `#b45309` | the publish panel's outside-policy line (D7: define it; the reference relied on the fallback) |
| `--sidebar-bg` / `--sidebar-ink` / `--sidebar-muted` | `#16181d` / `#e8e8e4` / `#9a9aa2` | sidebar + shell block |
| `--mono` | `ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace` | slugs, paths, code, hashes |
| body font | `system-ui, -apple-system, "Segoe UI", sans-serif` 14px / 1.5 | — |
| `--radius` | 10px | cards, panels |

**Classification identity colours (fixed, never cycled):** mappable `#2a78d6` ·
orchestration_config `#1baf7a` · notification `#4a3aa7` · out_of_scope `#898781` · flagged
`#eb6834` · unmapped `#eda100`.

**Mode badge colours:** mock grey (`rgba(110,122,135,.16)` / `#4a5560`), live red
(`rgba(217,72,63,.14)` / `#a2231b`), replay blue (`rgba(42,120,214,.14)` / accent-deep). Mode
banners use the same hues at 9–10% with a 28–30% border.

**Highlighter token colours (path A only):** comment muted italic; keyword/builtin `#4a3aa7`;
string `#006300`; number/boolean `#1c5cab`; function/class/decorator `#b3400f`;
operator/punctuation ink-2.

### 4.2 Copy bank (exact strings; do not paraphrase)

- Mode copy: `MOCK — deterministic stand-in provider, zero network` · `LIVE — generated now;
  each candidate card names its provider` · `REPLAY — recorded live run`.
- Sidebar footer: `Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.` /
  `Gate verdict computed in code, never by judgment.`
- Dashboard sub-line: `Pipelines generated from approved FRD + STTM contracts. Every rule is
  compiled deterministically or routed to a reviewed Layer-2 candidate — nothing lands
  unreviewed.`
- Gate flags (SPEC 5.3, shown verbatim): `Layer-2 candidate pending engineer approval:
  '<<rule>>'` · `Layer-2 candidate NOT grounded for rule '<<rule>>': <<notes>>` · `Layer-2
  provider failed for rule '<<rule>>': <<notes>>` · `confirm item pending (document-derived,
  cited): <<text>>` · `rule classified <<class>>: '<<rule>>' — <<notes>>` ·
  `faq_unanswered:<<question>>` · `load_mode_not_enforced: declared <<mode>>; generated writer
  uses MERGE-by-file (branching planned v2)` · `standards_stub: <<status>>` · `generated tests
  were skipped — PASS cannot be claimed`.
- Candidate status: `Awaiting engineer decision` · `Marked approved — merge into generated
  code remains a manual (v2) step` · `Soft confirmation — the run proceeds; a source-team
  answer closes it` · `Marked approved — recorded in the decision store`.
- Live unavailable: `Live is unavailable: <<reason>> (provider: <<p>>)`; fallback reason
  `the backend cannot reach a Layer-2 provider`.
- Run states: `Running — stages appear as they start:` · `Last live run completed.` · `Last
  live run FAILED — nothing was published.`
- FAQ step: `Saved <<feed_slug>>.faq.yaml` · `No answers set — the generator will use defaults
  and flag every question` · `<<n>> answered by the contract · <<k>> answered here · <<m>>
  unanswered → <<m>> flags` · `prefilled from the contract — change the value to override it`
  · `default: <<value>>` · `Companions (not questions, never flagged):` · `companion — sets
  HEADER_FLAG`.
- Inspection error families (the fixed second line under a verbatim generator message):
  workbook → `The workbook could not be read as a mapping document; nothing was guessed. Fix
  the sheet the message names and inspect the pair again.`; pair → `The FRD and the STTM
  disagree; nothing here is guessed. Fix the document that is wrong and inspect the pair
  again.`; generator (a run that failed inside a feed) → `The generator stopped; nothing was
  written for this feed. The run directory keeps what earlier feeds produced.`
- Chooser: `no contract — run the FRD→STTM agent for this document first` · `looks like a
  pair — confirm` · `companion FRD` · `includes companion FRD — fetched together` · `differs
  from local copy` · `These names do not look like a pair — the FRD feeds must name the
  workbook's stage tables (SPEC 1.4). Inspect anyway; a mismatch fails loudly.`
- Option A empty states: `No notebook for <<slug>> — this run produced framework artefacts
  only (Option B). The notebook appears when a run uses output mode Notebook or Both.` ·
  tooltip `Option A emitter not built in this workspace (SPEC L16)`.
- Tooltips: landing `The real FRD states this under Structural Metadata → ADLS Location;
  this build carries an anonymized stand-in.`; load strategy `The real FRD states these under
  Structural Metadata → Load Strategy STG / STD; this build carries a config stand-in.`
- Strings this kit parameterises (D8) — each is a literal in the reference source; the
  rebuild reads the value from configuration: `<<client>>` (`ui.client_short_name`) in the
  framework panel hint, the metadata subhead and the metadata disclaimer; `<<program
  approver>>` (`ui.client_document_approver`) in the cost modal; `<<ticket>>` in the
  convention-check subhead (derived from the reference FRD's file name); the tour's step-2
  synthetic fact is feed-neutral.

### 4.3 Databricks App platform notes that shape the UX

- Single process serves API + frontend (the frontend directory mounted at `/` with the
  HTML-shell fallback and `no-store` on the shell). Port = `DATABRICKS_APP_PORT` →
  `CODEGEN_UI_PORT` → 8571; host all interfaces.
- Container restarts wipe only in-memory state: the runner's selections (STTM, FRD, output
  mode → the configured default) and the loaded-run pointer (the App regenerates the mock
  run on boot). Uploads, FAQ answers, decisions and every run survive on the outputs Volume.
  The Past-live-runs hint (`this machine's run history`) is kept verbatim and reads truthfully
  because the outputs Volume is that history.
- Live Layer 2 rides the declared serving-endpoint resource (CAN_QUERY) when the App declares
  one and the force-mock switch is unset. The provider surfaces in every candidate pill and
  the cost modal's wording. `CODEGEN_FORCE_MOCK_PROVIDER=1` (the rebuild's default) locks the
  mock: badge `MOCK — provider locked`, modal `zero model calls`.
- Workspace client construction failures become `502` with the SDK message; the UI shows
  them (never a bare 500, never hidden as "unconfigured").
- A console that reverse-proxies every route above under `/api/codegen/*` surfaces `detail`
  verbatim; changing a response shape or a status code changes the console. Keep the 409 /
  503 / 502 meanings stable.
- Progress is polled (1 s), never streamed, to stay inside the Apps reverse proxy's untested
  long-request surface; the run POST returns immediately.

---

## Appendix A — What exists in the rebuilt workspace

The folder Genie Code builds in holds, before the UI work starts:

| Item | Where | Role |
|---|---|---|
| the S1–S6 package | the workspace folder (frozen slices) | the generator every route calls in-process: readers + resolution + FAQ (S1), the two DDL files (S1, S2), the seven IIG tabs (S3, S4), the workbook + report (S5), the batch summary (S6) |
| one configuration file | next to the package | every SPEC 0.1 knob plus the UI knobs: `contracts.pairs` (the configured pairs), `demo.frd` / `demo.workbook` (the default pair the generate card starts on — the first configured pair), `demo.estimated_*`, `demo.input_documents.expected`, `demo.metadata_sheet` (the seven tabs, headers, `always_blank`), `output.mode: framework`, `ui.client_short_name`, `ui.client_document_approver`, `ui.upload_cap_mib: 25`, `load_pattern_faq.per_feed_dir` = `<<outputs_volume>>/faq/` |
| the inputs Volume | `<<inputs_volume>>/` with `frd/`, `sttm/`, `standards/`, `replay/` | read-only for the App |
| the outputs Volume | `<<outputs_volume>>/` with `uploads/`, `faq/`, `state/`, `runs/` | read-write for the App; created empty; the App creates the sub-folders it needs |
| the reference documents | `<<inputs_volume>>/standards/` | the client naming standards document, the client coding standards document, the input-requirements deck, the two architecture decks, the reference FRD, and the scrubbed reference IIG workbook and DDL goldens — names as listed in `demo.input_documents.expected`; transcribed from the client library, never reproduced in this kit; the documents card counts them, the LATER checks read them |
| the ten real FRD + STTM pairs | `<<inputs_volume>>/frd/<<pair>>.contract.json` + `<<inputs_volume>>/sttm/<<pair>>.xlsx` | listed in `contracts.pairs` (ten entries in the rebuilt workspace; the staging kit's configuration lists the synthetic pairs instead); the pairing is by the configured entry, never by name guessing |
| the synthetic pairs A–E | the same two folders, plus `<<outputs_volume>>/faq/` for the S1 FAQ files | `ACCEPTANCE/INPUTS.md`; S7 runs on these |

**Generate-on-boot.** At start-up the backend runs the equivalent of `POST /api/generate`
over `contracts.pairs`: each pair's workbook is extracted (when the entry names an `.xlsx`),
resolved and generated in framework mode with the mock provider, FAQ answers read from
`<<outputs_volume>>/faq/`, output under `<<outputs_volume>>/runs/mock/`. The dashboard is
therefore populated on first load with every configured pair's feeds and verdicts; a pair
that fails to resolve appears in the failures banner, and a boot with zero pairs leaves the
empty state (`No feeds generated yet — the backend generates on startup.`) plus the 409 text
when someone clicks Generate all. Boot failure never crashes the App: the UI starts empty and
reports through `/api/feeds` (D13).

**What does NOT exist yet and how the UI shows it:** the Option A emitter (Notebook tab
hidden, Generated code shows the framework group, tour step 5 shows its empty state, the
Notebook/Both toggles disabled); the display modules behind source files, input requirements
and governance checks (their sections absent — 503); the volumes and SharePoint seams
(chooser sections 4–6 absent; publish panel shows `Publishing is unavailable here: not built
in this workspace — volume publish`); the replay loader (Card A shows `No replay sets tracked
under fixtures/replay/.` until sets exist AND the loader is built — with sets on the Volume
but no loader, `Load` answers 503 into the red banner); the upstream contracts table (the
chooser's FRD section shows `FRD→STTM agent table unavailable: not built in this workspace —
upstream contracts table` and lists local contracts only).
