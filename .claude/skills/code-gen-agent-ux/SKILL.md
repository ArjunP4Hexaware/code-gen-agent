---
name: code-gen-agent-ux
description: The complete user-experience specification of the CodeGen / Data Engineer Agent demo UI (FastAPI backend + React frontend, deployed as the Databricks App `codegen-agent`). Read this when rebuilding, porting, or reviewing the agent's UI in the AmeriHealth (ACFC) Databricks environment with Genie Code, or when the console that proxies this backend needs the exact screens, states, copy, colours, status codes and gating rules. Companion to the `code-gen-agent` skill (architecture + pipeline); this file covers only what the human sees and clicks.
---

# CodeGen / Data Engineer Agent — UX specification

> **Import note.** This file is written to be sufficient on its own. Only
> the two SKILL.md files (`code-gen-agent` = architecture, this one = UX)
> are reachable from inside Genie Code in the AmeriHealth workspace; every
> repo path mentioned here is a *provenance pointer* for a human reading the
> Hexaware repo, never a build dependency. Where this file and a Genie
> Code guess disagree, this file wins — it was transcribed from the
> shipping frontend (`ui/frontend/src/**`, version 0.3.5, 2026-09-11) and
> the backend routes it calls (`ui/backend/*.py`).
>
> **Scope.** Part 1 is the UX doctrine (why the UI looks the way it does).
> Part 2 is the screen-by-screen specification. Part 3 is the API contract
> the screens are built on. Part 4 is copy, tokens, and the acceptance
> checklist. Appendix A is the manifest of reference files that must be
> placed in the `code-gen-agent` folder of the AmeriHealth workspace.

---

## Part 1 — UX doctrine (the rules every screen obeys)

These are the things a "guessed" rebuild most often gets wrong. Treat each
as a requirement, not a style preference.

1. **Every number and quote on screen is real output of the loaded run.**
   Nothing is hard-coded, nothing is a mock-up. Tiles, cards, rule tables,
   candidates, notebooks and reports are all read from the run the backend
   currently holds (`/api/feeds`). If there is no run, the UI says so
   ("No feeds generated yet — the backend generates on startup.") instead
   of rendering placeholders.

2. **The run mode is always visible.** A `MOCK` / `LIVE` / `REPLAY` badge
   sits in the sidebar brand block on every route; LIVE and REPLAY
   additionally paint a full-width banner at the top of the main column
   with the run label (`demo_<timestamp>` or the replay-set name). A
   viewer must never wonder whether they are looking at a fresh live run,
   a recorded run, or the deterministic mock.

3. **Honesty badges instead of silent stand-ins.** Any value the agent
   synthesised rather than read from a document is badged `SYNTHETIC`
   with a tooltip naming where the real value lives (e.g. "The real FRD
   states this under Structural Metadata → ADLS Location; this build
   carries an anonymized stand-in."). A synthetic STTM contract carries a
   `synthetic STTM` tag on the card, the header and the contracts panel.
   Metadata-sheet cells carry exactly one provenance dot each.

4. **Errors are said, never hidden — and the status code says whose
   problem it is.** `503` = not configured → the section is simply
   absent. `502` = the workspace/Graph refused → the section renders the
   message plus a Retry button. `409` = one-at-a-time / nothing to
   generate → shown verbatim in the red error banner. `400` = the
   caller's request is wrong (e.g. a target outside the writable prefix).
   The frontend surfaces every backend `detail` string verbatim.

5. **Confirm before anything billed, destructive, or outward.** Four
   modal dialogs exist and each must stay: (a) run live (cost shown),
   (b) replace LIVE/REPLAY results with a mock regenerate, (c) reset
   review decisions, (d) publish to a Unity Catalog volume. A stray click
   can never spend money, overwrite the view the presenter is standing
   on, wipe decisions, or write to the workspace.

6. **The human decision is the finale, and it does not merge.** Every
   route ends at the Layer-2 review queue. Approve/Reject records a
   decision only; the status copy says so explicitly ("merge into
   generated code remains a manual (v2) step"). Decisions never gate the
   verdict and never alter generated code.

7. **The agent never invents identifiers.** Framework-assigned IDs render
   blank (or as the configured placeholder in inserts) and are listed
   under "Framework-assigned IDs left blank … the agent never invents
   them."

8. **Colour never carries meaning alone.** Verdict chips pair an icon
   with a text label; classification badges pair a dot with a label;
   status pills carry words. Status colours (good / warning / critical)
   are reserved for verdicts and check states and are never reused as
   series or badge identity colours.

9. **Choices are explicit; nothing auto-picks.** The live card opens with
   "none chosen" for the STTM and the run button disabled until the
   operator picks. A look-alike FRD is *suggested* ("looks like a pair —
   confirm"), never auto-selected. A feed-match failure offers a one-click
   "Choose companion FRD" button; it does not retry on its own.

10. **The UI is a front door, not a second pipeline.** No generation logic
    lives in the frontend. Everything the screens show comes from the
    in-process pipeline the CLI also runs, and UI runs are always
    `dry_run=True, skip_tests=True` (the only billed path is the confirmed
    live endpoint).

---

## Part 2 — Screens

### 2.1 Application shell

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
│  cv_individual_risk        ●                                                │
│  cv_community_risk         ●                                                │
│  …                         ●  (verdict dot, right-aligned)                  │
│                  │                                                          │
│ ─────────────    │                                                          │
│ Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.            │
│ Gate verdict computed in code, never by judgment.                           │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

- **Brand block:** product name "CodeGen · Data Engineer Agent" (15px,
  weight 650), sub-line "Contracts → Databricks pipelines" (12px muted),
  then the **mode badge** (pill, 10.5px, weight 750, letter-spacing
  0.08em): text is the mode upper-cased plus ` · <label>` when a label
  exists. Title attribute carries the mode copy (see Part 4).
- **Nav:** section headers are 11px uppercase letter-spaced muted text
  ("Overview", "Feeds"). Nav items are 13px rows with 8px radius, hover
  = 6% white, active = 12% white + weight 600. "Run modes" and "Demo
  mode" carry a right-aligned 10.5px hint ("live · replay", "guided
  tour"). Feed items show the slug (ellipsised) and a right-aligned
  8px verdict dot.
- **Footer:** the two-line doctrine sentence above, 11.5px muted.
- **Main column behaviours:**
  - `error-banner` (red tint) reads "Backend error: <message>" when the
    feeds fetch failed.
  - `mode-banner` for LIVE (red tint) or REPLAY (blue tint): the mode
    copy plus ` · <code>label</code>`.
  - **Generate-all confirm modal** (opened only when the current mode is
    not mock): title "Replace the current LIVE|REPLAY results?", body
    "This replaces the current live|replayed results (<label>) with a
    fresh **mock** run. You can reload them afterwards from the Run modes
    page.", buttons "Continue — run mock" (primary) / "Cancel".
- **Routes:** `/` Dashboard · `/modes` Run modes · `/demo` Demo mode ·
  `/feeds/:slug` Feed detail (accepts `?tab=` one of `overview | rules |
  candidates | notebook | code | report`). Client-side routing with an
  `index.html` fallback so deep links survive a refresh on the App.
- **Data flow:** the shell owns `FeedsResponse` (`/api/feeds`) and passes
  it down; every page that changes the loaded run calls
  `onFeedsChanged()` so the sidebar, badge and banner update together.
- **Favicon:** blue rounded square with white `< >` glyphs (inline SVG
  data URI). Document title "CodeGen · Data Engineer Agent".

### 2.2 Dashboard (`/`) — "Generation gate"

```
Generation gate                                   [Reset decisions] [Generate all feeds]
Pipelines generated from approved FRD + STTM contracts. Every rule is compiled
deterministically or routed to a reviewed Layer-2 candidate — nothing lands unreviewed.

[failures banner: "<label> — <error>" per failed pair, red]

┌ FEEDS ─────┐ ┌ PASS ───────────┐ ┌ RULES COMPILED ┐ ┌ PENDING REVIEW ──┐
│ 3          │ │ 0               │ │ 11/14          │ │ 3                │
│ from       │ │ 3 with flags ·  │ │ deterministic  │ │ Layer-2 candidates│
│ configured │ │ 0 failed        │ │ (Layer 1 +     │ │ awaiting an      │
│ contract   │ │                 │ │ orchestration) │ │ engineer         │
│ pairs      │ │                 │ │                │ │                  │
└────────────┘ └─────────────────┘ └────────────────┘ └──────────────────┘

┌ feed card ───────────────────────────────┐ ┌ feed card ─────────────────┐
│ cv_individual_risk       [⚑ PASS WITH FLAGS]                             │
│ Community Vitality | REG_1, REG_2 +3 more | CSV · segmented [SYNTHETIC STTM]
│ ████████▒▒▒▒▒▒░░  (rule strip, one segment per classification)           │
│ ● mappable 4  ● orchestration 1  ● flagged 1  ● unmapped → L2 1          │
│ ──────────────────────────────────────────────────────────────────────── │
│ 5/7 rules compiled deterministically          31 files · 1 pending review│
└──────────────────────────────────────────┘ └────────────────────────────┘

┌ Framework artefacts (Option B) ─────────────────────────────── (only if any feed has framework)
┌ Publish to Unity Catalog volume ────────────────────────────── (only if ≥1 feed)
┌ For ACFC's framework: metadata sheet preview ───────────────── (only if ≥1 feed)
```

**Header row.** `h1` "Generation gate" + the two-sentence sub-line.
Buttons right-aligned: "Reset decisions" (secondary, tooltip "Clear all
approve/reject decisions recorded for the currently loaded run") and
"Generate all feeds" (primary; shows a spinner + "Generating…" while
busy). Generate-all calls `POST /api/generate` with `{feed_slug: null,
dry_run: true, skip_tests: true}`; from LIVE/REPLAY it first opens the
confirm modal from §2.1. With `contracts.pairs` empty the backend answers
`409 "config.contracts.pairs is empty — nothing to generate"` and the
banner shows it — expected, not a fault.

**Reset decisions modal.** Title "Reset review decisions?"; body "Clears
every approve/reject recorded for the currently loaded run (<label> |
(mock state)). Candidates return to **pending engineer approval**.
Decisions made under other runs are untouched."; buttons "Reset — clean
slate" (primary, "Resetting…" while busy) / "Cancel". Calls
`POST /api/decisions/reset` then refreshes feeds.

**Failures banner.** When `FeedsResponse.failures` is non-empty, one red
banner listing `<strong>label</strong> — error` per entry.

**Stat tiles** (grid, auto-fit minmax 170px, 14px gap):

| Label | Value | Hint |
|---|---|---|
| Feeds | `feeds.length` | "from configured contract pairs" |
| Pass | count of `PASS` | "`n` with flags · `m` failed" |
| Rules compiled | `deterministic/rules` or "—" when no rules | "deterministic (Layer 1 + orchestration)" |
| Pending review | Σ `candidates_pending` | "Layer-2 candidates awaiting an engineer" |

`deterministic` = Σ(`mappable` + `orchestration_config`) counts.

**Feed card** (grid auto-fill minmax 340px; whole card is a link to
`/feeds/<slug>`; hover lifts the border and adds a soft shadow):

- Top row: slug in mono 14.5px weight 650 + `VerdictChip` right.
- Meta line (12.5px, ink-2): `source_system | <lobLabel> | FORMAT`
  (+ " · segmented" when segmented) (+ `synthetic STTM` tag when
  `sttm_is_synthetic`). `lobLabel` shows the first three LOB codes then
  "+N more" (CAQH lists 14 REG codes — never dump them all on a card).
- **Rule strip:** an 8px-tall bar; each classification with a non-zero
  count gets a segment whose flex weight is its count, in the FIXED
  order `mappable, orchestration_config, notification, out_of_scope,
  flagged, unmapped`, 2px surface gap between segments, title
  "<label>: <n>". Hidden when `rule_total` is 0.
- Counts row: for each non-zero class, a 7px dot in its identity colour +
  label + count.
- Foot (hairline above, 12px muted, tabular numerals): left
  "`d`/`t` rules compiled deterministically", right "`files_written`
  files · `candidates_pending` pending review".

**Empty state:** "No feeds generated yet — the backend generates on
startup."

**Framework artefacts (Option B) panel** — rendered only when at least
one feed has `framework != null`. Head: "Framework artefacts (Option B)"
with hint "config rows are the approval artefact; DDL + inserts are
add-ons to ACFC's master notebook, applied only after approval". Body,
per feed: `<code>slug</code>` + hint "`tab n · tab n …` · `derived/total`
derived"; a row of secondary buttons, one per file (each an `<a download>`
to `/api/feeds/<slug>/download?path=framework/<name>`); then the 11px
line "Framework-assigned IDs left blank: `<cols>` | none — the agent
never invents them."

**Publish to Unity Catalog volume panel** — see §2.6 (shared component).

**Metadata sheet preview panel** — see §2.7 (shared component), keyed to
`mode-label` so it refreshes when the loaded run changes.

### 2.3 Feed detail (`/feeds/:slug`)

```
cv_individual_risk  (mono h1)                                        [Regenerate]
[⚑ PASS WITH FLAGS] Community Vitality · REG_1, REG_2 +3 more · CSV · segmented (H/D/T) [SYNTHETIC STTM]

Overview | Rules (7) | Layer-2 review (1) | Notebook | Generated code (30) | Report
─────────────────────────────────────────────────────────────────────────────────
<tab content>
```

- **Regenerate** = `POST /api/generate` with this slug (mock, dry-run).
- **Tabs:** underline style, active = accent colour + 2px underline;
  counts in a grey pill. The **Notebook tab is hidden when no `.ipynb`
  is among `written_files`** (framework-only output) rather than 404ing.
  "Generated code" count excludes the notebook.
- Loading states: "Loading…" centred muted; an error replaces the page
  with the red banner.

**Overview tab** — four stacked panels:

1. *Gate checks* (hint "verdict computed in code — never by judgment"):
   one row per `GateCheck` — 8px dot (green PASS / red FAIL), bold name
   (min-width 130px), details in ink-2. Check names today: `ruff`,
   `debug_patterns`, `secrets`, `test_per_module` (+ `generated_tests`
   when run).
2. *Flags — needs a human* (only when `flags` non-empty; hint "`n`
   open"): a list; each row has an amber dot. A flag containing
   "pending engineer approval" is the **HITL centrepiece**: the row gets
   an amber background and a `PENDING ENGINEER APPROVAL` tag (10px,
   weight 750, warning background) before the text. Flag strings come
   verbatim from the gate (see Part 4 copy bank).
3. *Source contracts* (hint "provenance embedded in every generated
   file"): definition list — FRD name + `sha256 <hash>` line; STTM name
   (+ `synthetic` tag) + sha256; File patterns (one `<code>` per line);
   Delimiter (JSON-quoted, e.g. `"|"`); Lines of business (full list);
   Frequency (only when present).
4. *Target tables:* Stage (one per line), Standard (or *"none —
   stage-only feed (load AS-IS)"*), Errors, Recycle (or *"no recycle
   rule"*), Processed files.
5. *Load semantics:* Natural key (codes), Not-null columns (or *none*),
   PHI columns (or *none declared*; when present add the muted line
   "masked to last-4 at every log / report / error egress"), Load window
   / SLA (joined with "; ", only when present).

**Rules tab** — one panel titled "Validation rules — verbatim from the
FRD", hint "classification is deterministic; only *unmapped* rules reach
Layer 2". Table columns: `#` (muted, tabular), `Classification`
(`ClassBadge`), `Rule` (rule text, max-width 520px, wrap anywhere; notes
below in 12.5px ink-2), `Generated feature` (`<code>` or "—"),
`Grounding` (mono 12px, wrapped in curly quotes). Horizontal scroll
container.

**Layer-2 review tab** — empty state "No Layer-2 candidates — every rule
compiled deterministically for this feed." Otherwise an intro paragraph
(max-width 760px): "These rules could not be compiled deterministically,
so the reasoning layer proposed candidates into a review artifact
(`candidates/candidates.json`). Candidates are **never merged
automatically** — approval here records the engineering decision only."
Then one **candidate card** per entry:

```
┌──────────────────────────────────────────────────────────────┐
│ Rule: “<rule_text>”                                          │
│ [provider: databricks_fmapi] [✓ grounded | ✗ NOT grounded] [● mappable]
│ <rationale, 13px ink-2>                                      │
│ ┌ candidate.py ──────────────────────────────┐               │
│ │ <PySpark sketch, Prism-highlighted>        │               │
│ └────────────────────────────────────────────┘               │
│ │ “<citation 1>”   (left-bordered italic quote)              │
│ │ “<citation 2>”                                             │
│ [✓ Approve] [✗ Reject]  Awaiting engineer decision           │
└──────────────────────────────────────────────────────────────┘
```

- **Provider failed variant:** when `response` is null the body is a red
  banner "Provider failed: <failure_notes joined by ; >". Still gets the
  decision row.
- **CONFIRM variant** (`kind == "confirm"`, from segmented extraction):
  a leading amber pill "CONFIRM — document-derived, cited"; the title is
  the item text without the "Rule:" prefix; the pill reads
  "source: <provider>" instead of "provider:"; `detail` renders as the
  rationale; `citation` as the single quote block; the approve button
  reads "✓ Confirm"; pending status copy "Soft confirmation — the run
  proceeds; a source-team answer closes it"; decided copy "Marked
  approved|rejected — recorded in the decision store".
- **Decision buttons:** Approve is green-outlined, Reject red-outlined;
  the selected one gets a tinted fill. **Clicking the already-selected
  decision resets to `pending`.** Both disable while the request is in
  flight. Status copy (muted, 12.5px): pending → "Awaiting engineer
  decision"; decided → "Marked approved|rejected — merge into generated
  code remains a manual (v2) step". After a decision the page reloads
  the feed and calls `onFeedsChanged()` so the dashboard's pending count
  moves.

**Notebook tab** — panel titled `<code><slug>.ipynb</code>` with hint
"the whole pipeline as one runnable Databricks notebook — the module
files stay canonical". Body: `NotebookView` — markdown cells rendered as
prose (`marked`), code cells in a bordered box with a 3px accent left
border and Python highlighting. Loads `GET /api/feeds/<slug>/file?path=<slug>.ipynb`;
"Loading notebook…" while pending; parse failure → "Could not parse the
notebook."

**Generated code tab** — two-pane layout (min-height 480px): left a
280px file tree, right the code pane (max-height 640px, sticky path bar
on top). The tree groups files by directory (header = uppercase
directory name or "ROOT"), mono 12.5px buttons, active = accent tint.
On load the first `pipeline/` file (else the first file) opens
automatically. Paths are derived by locating the `/<slug>/` segment in
each `written_files` entry (mock runs write `out/<slug>/…`, live/replay
write `out/demo_<ts>/<slug>/…`). Notebook excluded. Highlighting via
Prism for `py sql json toml md`; anything else renders plain.

**Report tab** — the markdown report from `GET /api/feeds/<slug>/report`
rendered with `marked` inside `.report-md` (13.5px, max-width 860px,
tables bordered, code inline chips). "Loading report…" while pending.

### 2.4 Run modes (`/modes`)

The operational heart of the UI. Two cards side by side (single column
under 980px). Page head: `h1` "Run modes", subtitle "Pick how the
results you're about to walk through get produced. Both modes end on the
same dashboard — and the same human review queue." A red error banner
above the cards shows the last failed action's message.

On mount the page fires, in parallel: `replaySets`, `liveAvailable`,
`demoStatus`, `inputDocuments`, `sourceFiles`, `inputRequirements`,
`governanceChecks`, `liveRuns`. Everything is a live read; nothing is
cached to disk.

#### 2.4.1 Card A — "Replay a recorded run" (badge `REPLAY`)

Hint: "Loads a tracked, real live run instantly — zero API calls, zero
cost, no key needed. The deterministic pipeline re-runs locally; the
recorded AI candidates are injected exactly as the model returned them."
Rows (`replay-row`, hairline between): name in mono weight 650; hint
"recorded <date> · <n> feeds · call log" (date from the trailing 8-digit
stamp of the set name); a primary "Load" button ("Loading…" while busy;
disabled while any load or a live run is in progress). Load →
`POST /api/replay/load {set}` → refresh feeds → navigate to `/`. States:
"Discovering replay sets…" / "No replay sets tracked under
fixtures/replay/."

#### 2.4.2 Card B — "Generate a Pipeline" (badge `LIVE`, or `MOCK — provider locked` when the backend reports provider `mock (locked)`)

Top to bottom, in this exact order:

**Step 1 — choose an STTM.** Hint paragraph: "**Step 1 — choose an
STTM.** The pipeline's input is a client STTM mapping workbook, picked
from the SharePoint document library — the program's system of record.
Choose the workbook this run will consume:". Then two inline rows:

- `STTM workbook: <code>name</code>` or *none chosen* · buttons
  "Choose STTM…" (opens the chooser modal) and "Clear" (disabled until
  chosen; tooltip "Back to none chosen" / "Nothing chosen yet"; `DELETE
  /api/demo/workbook`).
- `FRD contract: <code>name</code>` + "(demo golden — default)" hint when
  not explicitly chosen · buttons "Choose FRD…" (same chooser modal,
  tooltip "Pick the FRD for this run (companion FRDs are suggested for
  the chosen STTM)") and "Reset" (disabled unless chosen; tooltip "Back
  to the demo golden default" / "Already on the demo golden default";
  `DELETE /api/demo/frd`). When `frd_warning` is true a red pill reads
  "This STTM does not appear to belong to the demo FRD — expect a
  feed-match failure." (tooltip "Pick the companion FRD in the STTM
  chooser").

All of these disable while a run is in progress.

**Source files this run will read** (subhead; only when the source-files
call returned feeds). Hint "From the demo FRD contract `<name>`, read at
request time." A horizontally scrolling table with columns: feed ·
landing root (+ `SYNTHETIC` pill when synthesised, tooltip = landing
tooltip) · file patterns (one per line, or *none in FRD*) · format
(+ " · <delimiter>") · frequency (or *not stated in FRD*) · stage
target · standard target · load strategy (two lines "X (stage)" / "Y
(standard)" + `SYNTHETIC` pill when synthesised).

**Convention check — real FRD 1005310** (only when the real SFMC FRD
docx is present in an input dir). Hint "Read live from `<file>`
(Structural Metadata), at request time — the client's real convention
beside the synthesized paths above." Two-column table of ADLS Location,
Target Schema, Load Strategy STG, Load Strategy STD, Object / data
Format, each with a third cell "from document". Absent the document the
block is absent.

**In the Databricks workspace** — a collapsed `<details>` block styled
as a dark terminal. Header note: `LIVE — listed from <volume> at <time>`
(green) or `SYNTHETIC (live listing unavailable: <reason>) — rendered
from the FRD's landing location and file patterns, not a live listing.`
(amber). Body: lines; lines starting with `$ ` are commands
(`$ databricks fs ls dbfs:/Volumes/<catalog>/<schema>/<volume>/<root>/`),
soft-wrapped with a hanging indent, non-selectable.

**Metadata sheet preview** (shared component §2.7), refreshed on
`state-last_run_label`.

**Step 2 — generate.** Hint: "**Step 2 — generate.** Extract the chosen
STTM into a mapping contract → deterministic generate → live AI reasoning
on the unmapped rules → safety gate. Makes billed API calls."

**Output** (subhead) — three toggle buttons in a row: "Notebook",
"Framework artefacts", "Both"; active = accent outline; `POST
/api/demo/output-mode {mode}`; default `notebook`. Hint below:
"Framework artefacts = DDL scripts + config rows + insert statements for
the existing ingestion framework — the ~90% case, adding a feed to what
already runs. Notebook = a fresh standalone pipeline — the ~10% case."

**Input documents** (subhead) — the documents card, three states:

- *none present*: an amber call-out "**No reference documents found.**
  The generator's naming, path and structural checks are grounded in the
  client FRD and architecture decks; none are present in the configured
  input directories. Runs proceed without them." + "Attach…" button.
- *all present*: green-tinted card titled "Reference documents attached",
  one row per expected file with ✓ + `<code>name</code>`, footer hint
  "Drives the generator's naming, path and structural checks via config."
- *partial*: amber-tinted card titled "Some reference documents are
  missing", ✓ or ☐ per row.

Always followed by the 11px line "All four documents are read and used
in the request-time checks below. None of them alters generated output —
the generation path stays contract-driven, byte-stable."

**Input requirements check** (subhead; only when the check exists). Hint
"The demo FRD contract, evaluated against the eleven Structural Metadata
rows of `<deck>` — read live from the document at request time. `f`
filled · `p` partial · `m` missing · `n` not captured by the contract
shape." Table rows: row name · status pill (`filled` green / `partial`
amber / `missing` red / `not captured` grey) · how-to-fill guidance. Then
"A missing or not-captured row is flagged, never guessed — the row names
and guidance come from the document itself." When the real FRD document
check exists, a second line "The same rows checked against the **real FRD
document** (`<docx>`, Structural Metadata read live): …" followed by an
inline run of pills + row names.

**Reference-architecture checks** (subhead; only when checks exist).
Hint "Controls stated by the governance and solution architecture decks,
read live from the documents and evaluated against the loaded run: `v`
verified · `a` need attention · `p` awaiting a run." Table: status pill
(`verified` green / `attention` amber / `awaiting a run` grey) · control
text (title = deck file) · evidence. These flip from "awaiting a run" to
verified/attention after a live run completes (the page re-fetches them
on `done`).

**Known input gaps** (subhead) — amber call-out "**Demo FRD, not the real
one.** A production run needs the FRD with the paths to the actual client
files — this build carries an anonymized stand-in. The pipeline runs
end-to-end, but the output does not represent an accurate case." +
"Provide…" button (opens the FRD documents modal).

**Run button / unavailability.** If `liveAvailable === false`: a muted
block "Live is unavailable: <reason from the backend> (provider: <p>)".
The reason is provider-specific ("Databricks workspace config does not
resolve", "databricks.serving_endpoint is not configured", "no
ANTHROPIC_API_KEY in the backend env") — never hard-code one. Otherwise a
primary button "Generate from this STTM…" (disabled until an STTM is
chosen — tooltip "Choose an STTM workbook first" — and while running,
where it reads "Live run in progress…"). Click opens the **cost
confirmation modal** (§2.4.5).

**Run progress** (shown once `status.state !== "idle"`):

- Lead hint: running → "Running — stages appear as they start:"; done →
  "Last live run completed."; failed → "Last live run FAILED — nothing
  was published."
- Failed: red banner with `status.error`; when `error_hint` exists, add
  its message and a secondary button `Choose companion FRD "<doc id,
  middle-truncated to 36>"` which selects that upstream FRD and reopens
  the chooser — never an automatic retry.
- **Stage list:** one line per stage, `✓` for completed, `⋯` for the
  last entry while running; bold stage name + " — detail". Stage names,
  in order: `extracting workbook` (detail = workbook name) → `resolving
  contracts` (detail "<frd> ⋈ extracted contract") → per feed
  `<slug>: compiling rules` → `<slug>: Layer-2 reasoning (live)` →
  `<slug>: emitting code` → (`<slug>: framework artefacts` in
  framework/both) → `<slug>: gate` → `publishing results` (detail "<n>
  feed(s), <m> failure(s)"). The stage list is what the presenter
  narrates; keep the names.
- Polling: after firing, poll `GET /api/demo/status` every 1000 ms until
  `done` or `failed`; on `done` refresh feeds, refresh past runs and
  re-fetch governance checks.
- On done: primary "View results →". If the store already holds this
  run (label matches `last_run_label` and mode is live) just navigate to
  `/`; otherwise load it through the past-run loader.

**Past live runs** (subhead). Hint "Completed live runs stay on disk —
reload one to restore its results (LIVE state, that run's real
candidates) without spending anything. These are this machine's run
history, not the tracked replay fixtures." Rows: name + `LIVE RUN` badge
(+ red pill "failed — not loadable" when incomplete); hint "<timestamp>
· <n> feeds" or "no results produced"; primary "Load" (disabled when
incomplete or busy). States "Scanning past runs…" / "No past live runs on
this machine yet."

#### 2.4.3 Modal — documents ("Attach…" / "Provide…")

Two variants share one dialog:

- **reference_documents:** title "Attach the reference documents"; hint
  "Filenames as they appear in the client SharePoint library, matched
  live against the configured input directories on every open. Drop a
  file there — or fetch it from the SharePoint library — and it will
  appear here."; then one row per expected name with ✓/☐ and
  "present"/"missing"; footer "Display only in this build — wiring these
  into generation is the next step." Empty config → "No reference
  documents configured (demo.input_documents in config/config.yaml)."
- **frd:** title "Provide the real FRD contract"; hints "Currently in
  use: `<stand-in>` — an anonymized demo stand-in without the real file
  paths." and "Scanned live from `inputs/sharepoint` — the landing folder
  `sharepoint-fetch` and the SharePoint picker deliver documents to.";
  matches render as amber rows "`<name>` found — wiring into the
  generator is pending; runs do not consume it yet."; none → "Not
  present. Fetch the real FRD contract (.contract.json) from the
  SharePoint library into inputs/sharepoint/ and it will appear here.
  Until then, runs use the demo stand-in."
- Single "Close" button. The scan re-runs on every open.

#### 2.4.4 Modal — "Choose an STTM workbook" (the chooser)

Opened by both "Choose STTM…" and "Choose FRD…". On open it re-fetches
`demoWorkbooks`, `databricksDocuments` and `frdChoices`. Sections, top to
bottom:

1. Hint: "Scanned live from the local fixtures directory and the
   `inputs/sharepoint`, `inputs/databricks` and `inputs/uploads` landing
   folders — where the SharePoint picker, the volume fetch below and a
   from-device upload deliver documents."
2. **Upload row:** two secondary buttons "Upload STTM (.xlsx)…" and
   "Upload FRD (.json / .docx)…" (each backed by a hidden `<input
   type=file>` with `accept=".xlsx"` / `.json,.docx`; label flips to
   "Uploading…"), plus the 11px note "Uploads land in `inputs/uploads` on
   the server (wiped on an App restart)." Tooltips: "Upload an STTM
   workbook (.xlsx) from this device; it is selected for the next run" /
   "Upload an FRD: a contract JSON produced by the FRD→STTM agent, or the
   FRD .docx itself (extracted when the run starts)". `POST
   /api/demo/upload` (multipart `kind`, `file`), which validates (JSON
   must parse as an FRD contract; .docx must be an F1/F2 FRD the
   extractor recognises) and selects in one motion. Standalone doctrine
   (2026-09-18): a .docx FRD is a first-class input.
3. **Local workbooks:** one full-width row-button per workbook: mono
   name (middle-truncated to 46 chars so the trailing ticket suffix stays
   visible; full name in title) + right chip "<source> · selected".
   Clicking selects (`POST /api/demo/workbook`) and **keeps the modal
   open** so the FRD section below can be confirmed. States "Scanning…" /
   "No .xlsx workbooks found in the input directories."
4. **Databricks volumes error** (only on 502): amber call-out
   "**Databricks volumes unavailable.** <message>" + "Retry". A 503 hides
   the whole volumes section instead.
5. **STTM workbooks in `<catalog>.<schema>`** — hint "— fetch lands the
   file in `inputs/databricks` and it joins the list above:". Per
   document: name, meta "<volume> · <size> KB" (+ " · differs from local
   copy", + " · includes companion FRD — fetched together"). State
   `fetched` → the row is a button with chip "Fetched ✓" that selects the
   local copy; `fetchable` → "Fetch" button; `differs` → "Re-fetch". A
   fetch of a paired STTM also fetches its companion FRD.
6. **Companion FRDs in the volume (n)** — a collapsed `<details>`; hint
   "Fetching an FRD lands it in `inputs/databricks` for the documents
   card and contract use — an FRD is never choosable as the STTM." Rows
   as above with "Fetch FRD" / "Fetched ✓" and the meta " · companion of
   an STTM above".
7. **FRD for this run** — hint "**FRD for this run** — currently
   `<label>` (demo golden — default). Contracts come from the FRD→STTM
   agent; a document without a contract is not selectable." If the
   upstream table is unreachable: "FRD→STTM agent table unavailable:
   <reason>" (the rest still renders). Then:
   - upstream rows (buttons): doc id + meta "from FRD→STTM agent ·
     <status> · <n> feed(s) · audited <ts>"; right chip "companion FRD"
     (green) when explicitly paired, or amber "looks like a pair —
     confirm" when only heuristically suggested; nothing otherwise.
   - local FRD rows (buttons): name + chip "local contract" for a
     `.contract.json`, or "FRD document — extracted at run start" for an
     FRD `.docx` (standalone doctrine, 2026-09-18).
   - no-contract rows: retired — `no_contract[]` is always empty now that
     a .docx is selectable; the frontend block remains for API compatibility.
8. Footer button reads **"Done"** once an STTM is chosen, **"Cancel"**
   before.

#### 2.4.5 Modal — cost confirmation

Title "Generate a pipeline from this STTM?". Body: "Input:
`<workbook>`"; then either "This deployment is **locked to the mock
provider** — the run makes **zero model calls** (deterministic mock
candidates)." or "This makes real, billed Claude calls through the
Databricks serving endpoint:" (FMAPI) / "This makes real, billed
Anthropic API calls:" (Anthropic) followed by "**~3 calls · ≈ $0.10 ·
~20s**" (numbers from `status.estimates`). Then "Output is isolated to
its own run directory; the tracked replay fixtures and default output
are never touched." and, depending on `frd_chosen`: "Client documents in
play: live runs on client STTM/FRD pairs are permitted only per the
program's client-document process (Venu's email approval). The demo CV
golden remains the default rehearsal pair; mock runs need no approval."
or "Known input gap applies: a demo FRD without the real file paths —
the run is real, the case it represents is not." Buttons "Confirm — run
live" (primary) / "Cancel". Confirm → `POST /api/demo/run-live
{confirm: true}` then start polling.

### 2.5 Demo mode (`/demo`) — the six-step guided tour

Centred column (max-width 880px). Head: kicker "GUIDED DEMO" (11px,
accent, letter-spaced), `h1` = current step title, right side "`k` / 6"
counter + "Exit demo" link-button. A card (min-height 380px, 14.5px
text) holds the step. Footer nav: "← Back" (disabled on step 1), six
dot buttons (active = filled accent; each has the step title as
tooltip/aria-label), "Next →" or on the last step "Finish → dashboard".
**← / → arrow keys move between steps.** The running example is the
first feed with Layer-2 candidates, else the first feed.

| # | Title | Content |
|---|---|---|
| 1 | What this is | Lead "Approved spec documents go in. A tested Databricks ingestion pipeline — packaged as **one runnable notebook per feed** — comes out." Four flow boxes: Contracts → Deterministic compiler → Safety gate → Pipeline + notebook (accented). Paragraph on the AI sandbox. Fact box "Right now: `n` feeds generated, `d/t` contract rules compiled deterministically. Everything you'll see next is live output, not a mock-up." |
| 2 | Contracts go in | Lead on approved machine-readable contracts + fingerprints. "Running example: `<slug>` (<source>, segmented H/D/T file)". KV: FRD — what the feed is (name + sha), STTM — how columns map (name + synthetic tag + sha). If synthetic: fact "Honesty on display: the real CAQH mapping workbook hasn't landed yet, so this feed uses a clearly-labeled synthetic stand-in — and the UI says so everywhere." |
| 3 | Layer 1 — deterministic | Lead on pattern matching, byte-identical output. Row of class chips (dot + label + count). A quote block: the first `mappable` rule → "became `<feature>`, grounded on the contract text *“<grounding>”*". Fact "Rules the compiler can't safely map aren't guessed at — they're **flagged for a human** or handed to Layer 2. Next slide." |
| 4 | The safety gate | Lead "Before anything ships, a gate runs lint, security scans, structural checks and the generated test suite. The verdict is **computed in code** — the AI never grades its own homework." Gate check rows; "Verdict for `<slug>`: <chip>". Fact explaining PASS_WITH_FLAGS as the honest middle state. |
| 5 | What comes out | Lead on the single runnable notebook (cells self-register as `pipeline.<module>`). A row of buttons `<slug>.ipynb` per feed (selected = primary); the example feed's notebook opens automatically in a 46vh scroll box. Fact linking to the feed's Notebook tab. |
| 6 | Layer 2 — the human decision | Lead "The demo ends where every run ends: with a **human decision**…". Two bullets (verbatim quoting; approve/reject records only). One quote block per candidate with class badge, grounded pill, provider pill, rationale, and Approve/Reject buttons (same toggle semantics as §2.3; status "Pending engineer approval" / "Marked approved"). Empty: "This feed had no ambiguous rules — the queue is empty." Fact "`p` of `c` candidate(s) still pending for `<slug>` — the full queue lives on the Layer-2 review tab" (link with `?tab=candidates`). |

### 2.6 Shared component — "Publish to Unity Catalog volume" panel

Rendered on the Dashboard whenever `GET /api/databricks/publish-target`
answers (it always answers; the panel is hidden only if the call itself
fails). Head hint: "the human gate for Databricks: reviewed artifacts
land under `/Volumes/…/<feed>/` — never a side effect of generating".
Body: three text inputs Catalog / Schema / Volume (170px, pre-filled from
the target defaults, trimmed on change), a Feed `<select>` of loaded
slugs, and a primary "Publish…" button (enabled only when available and
all four are set; "Publishing…" while busy). Under it exactly one line:

- unavailable → "Publishing is unavailable here: <reason>"
- outside policy (`<catalog>.<schema>.` does not start with
  `writable_prefix`) → amber: "`<full name>` is outside the writable
  policy — the backend only writes under `<prefix>*` and will refuse this
  target. Publishing never touches client schemas."
- otherwise → "Target: `/Volumes/<c>/<s>/<v>/<feed>/` · policy: writes
  only under `<prefix>*`, enforced in code."

Result line after success: "Published `n` artifact(s) to `<volume>`
(volume created): a, b, c". Errors in a red banner. **Confirm modal:**
"Publish to the workspace?" — "Writes `<feed>`'s report, notebook and
framework artefacts to `/Volumes/<c>/<s>/<v>/<feed>/` in Unity Catalog.
Publishing is the review gate — do this only after looking at the feed's
verdict. Files already there are not overwritten." Buttons "Confirm —
publish" / "Cancel". Calls `POST /api/databricks/publish` with
`confirm: true`.

### 2.7 Shared component — "For ACFC's framework: metadata sheet preview"

Subhead "For ACFC's framework: metadata sheet preview"; `layout_note`
from the backend as the hint; a tab strip (one button per sheet tab,
label + row count, active = accent outline); a scrolling table of the
active tab. **Every cell carries exactly one provenance dot** (7px
rounded square, title = badge label + optional tooltip) and a matching
background tint:

| Badge | Label | Tint / dot |
|---|---|---|
| from_sttm | from STTM | green 8% / green |
| from_sttm_unmapped | from STTM (unmapped) | green 14% / green with dark outline |
| from_frd | from FRD | blue 8% / accent |
| from_faq | from FAQ | violet 10% / #7a5abe |
| from_standards | from standards | teal 10% / #14968c |
| synthetic | SYNTHETIC | amber 14% / warning |
| needs_template | NEEDS CLIENT TEMPLATE | grey 12% / muted |

On the `columns` tab a full-width feed-separator row (`<code>slug</code>`,
bold, page background) precedes each new feed's rows. Empty tab → the
tab's `state` text or "no rows". Footer: "**`d` of `t`** values derived
from documents · `s` synthesized · `n` await the client template.", a
secondary "Download .xlsx" link (`/api/demo/metadata-sheet.xlsx`), and
the 11px disclaimer "Display only — the reviewed sheet is the approval
artifact. On approval the rows land in the ingestion framework database,
and the generated DDL + insert SQL are add-ons to ACFC's master notebook
— the client's own notebook, never generated or edited by the agent. The
agent never inserts unapproved rows."

### 2.8 Shared primitives

- **VerdictChip:** pill, 12px weight 650, icon + label. PASS = check
  glyph, green tint; PASS WITH FLAGS = flag glyph, amber tint; FAIL = ×
  glyph, red tint. **VerdictDot:** 8px circle in the status colour with
  the label as title.
- **ClassBadge:** outlined pill, 11.5px weight 600, 7px identity dot +
  label (`mappable`, `orchestration`, `notification`, `out of scope`,
  `flagged`, `unmapped → L2`).
- **StatTile:** surface card; 11.5px uppercase muted label; 26px weight
  650 value; 12px hint.
- **Pill:** outlined 11.5px weight 600; variants `grounded` (green),
  `ungrounded` (red), `synthetic` (amber), `req-*`, `gc-*`.
- **Buttons:** 13px weight 550, 8px radius, 7px×14px padding; `.primary`
  = deep accent fill, white text; `.approve` green outline; `.reject`
  red outline; disabled = 55% opacity. Spinner = 13px ring.
- **Panel:** surface, 1px border, 10px radius; `.panel-head` (13px×18px
  padding, hairline below, `h2` 14px + right-aligned 12px muted hint);
  `.panel-body` 16px×18px. `.panel-subhead` = uppercase 12px weight 700
  with a hairline above (used inside the live card).
- **Modal:** fixed overlay `rgba(15,23,32,.45)`; dialog white, 12px
  radius, 22px×24px padding, width `min(460px, 100vw − 32px)`,
  max-height 80vh with internal scroll; `role="dialog" aria-modal`.
- **Tables:** `table.data` (13px, uppercase 11.5px muted headers,
  hairline rows) for rules; `.source-files-table` (12px, nowrap cells,
  `.sf-wrap` for the one prose column at 240–340px) inside a
  horizontally scrolling `.source-files-scroll`.
- **Empty state:** centred muted 13.5px with 48px vertical padding.
- **Error banner:** red 8% tint, red 35% border, critical text, 8px
  radius.
- **`tag-synthetic`:** 10.5px uppercase weight 700, burnt-orange text and
  outline, 4px radius.
- **`flag-hitl`:** amber 10% background block; **`hitl-tag`:** 10px
  weight 750 warning-filled pill.
- **Shell block:** dark sidebar palette, mono, `summary` clickable.
- **Middle truncation** for file names: keep the last 16 characters (the
  ticket/copy suffix distinguishes files), elide the middle with `…`,
  full name in `title`.

---

## Part 3 — API contract the screens depend on

All routes are same-origin under `/api`. A non-2xx response carries
`{detail: string}`; the client throws an `ApiError` with the HTTP status
so callers can distinguish 503 (unconfigured → hide) from 502 (refused →
show + Retry). `POST` bodies are JSON unless noted.

### 3.1 Run state and generation

| Route | Purpose | Notable codes |
|---|---|---|
| `GET /api/feeds` | The loaded run: `{feeds[], failures[], mode, label}` | — |
| `GET /api/feeds/{slug}` | `FeedDetail` (summary + contracts, tables, semantics, outcomes, candidates, written_files) | 404 unknown slug |
| `POST /api/generate` `{feed_slug?, dry_run, skip_tests}` | Mock regenerate (one feed or all). UI always sends `dry_run: true, skip_tests: true` | 409 `config.contracts.pairs is empty — nothing to generate` |
| `GET /api/feeds/{slug}/file?path=` | Text of a generated file (path relative to the feed dir; containment enforced) | 400 escape, 404 missing |
| `GET /api/feeds/{slug}/download?path=` | Binary download (framework `.xlsx`/`.txt`) with `Content-Disposition` | 400/404 |
| `GET /api/feeds/{slug}/report` | `{markdown}` | 404 |
| `POST /api/feeds/{slug}/candidates/{index}/decision` `{decision, note?}` | Record `pending|approved|rejected` → `{review}` | 404 |
| `POST /api/decisions/reset` | Clear the CURRENT run's decisions only → `FeedsResponse` | — |

**Store semantics the UI relies on:** the backend holds one loaded run at
a time with `mode ∈ {mock, live, replay}`, a `label` (`null` for mock,
`demo_<YYYYMMDD_HHMMSS>` for live, the set name for replay) and the
run's own `out_root` / `reports_root`. Decisions persist in
`ui/backend/state/decisions.json` (version 2) keyed by `run_key = label
or "mock"` → feed slug → candidate index, so approvals rehearsed on one
run never bleed into another. Startup generation runs mock dry-run; if
it fails the app still starts with empty state and reports through
`/api/feeds`.

### 3.2 Replay and past runs

| Route | Purpose | Codes |
|---|---|---|
| `GET /api/replay/sets` | `{sets: [{name, date, feeds[], has_call_log}]}` from `fixtures/replay/` | — |
| `POST /api/replay/load` `{set}` | Re-run the deterministic pipeline with the recorded candidates injected; mode → replay | 404 unknown set |
| `GET /api/demo/live-runs` | `{runs: [{name, timestamp, feeds[], complete}]}` from `out/demo_*` | — |
| `POST /api/demo/load-live-run` `{run}` | Reload a complete past live run with its OWN FRD copy and recorded output mode; mode → live | 404 / 409 incomplete |

### 3.3 Live run (the only billed path)

| Route | Purpose | Codes |
|---|---|---|
| `GET /api/demo/live-available` | `{available, provider, reason}` — provider is `databricks_fmapi`, `anthropic`, `mock (locked)` or null; `reason` is the remedy | — |
| `POST /api/demo/run-live` `{confirm: true}` | Start the background live run; returns `DemoStatus` | 400 no confirm / unavailable; 409 already running |
| `GET /api/demo/status` | `DemoStatus`: `state idle|running|done|failed`, `stages[{stage, detail, at}]`, `error`, `error_hint`, `last_run_label`, `mode`, `label`, `estimates{calls,cost_usd,seconds}`, `sttm_workbook`, `sttm_chosen`, `output_mode`, `frd_name`, `frd_chosen`, `frd_warning` | — |
| `POST /api/demo/output-mode` `{mode|null}` | `notebook|framework|both`; null = config default → `DemoStatus` | 400 bad value; 409 running |

`error_hint` = `{sttm, frd_used, candidate_doc_id, message}` when a
feed-match failure has a known companion FRD.

### 3.4 Choosing inputs

| Route | Purpose | Codes |
|---|---|---|
| `GET /api/demo/workbooks` | `{workbooks: [{name, source, selected}]}` — fixtures dir + `inputs/sharepoint` + `inputs/databricks` + `inputs/uploads` | — |
| `POST /api/demo/workbook` `{name}` / `DELETE` | Select / clear the STTM | 404 unknown; 409 running |
| `GET /api/demo/frd-choices` | `{sttm, current{label,chosen}, upstream[{doc_id,status,n_feeds,audited_at,paired,suggested}], upstream_error, local[] (contract JSONs AND FRD .docx), no_contract[] (always empty since 2026-09-18)}` | — (upstream failure is reported inline, not as an error) |
| `POST /api/demo/frd` `{kind: upstream|local, id}` / `DELETE` | Select (materialising an upstream contract) / reset to the demo golden | 400 bad kind/name; 404 no local; 409 running; 502 upstream refused |
| `POST /api/demo/upload` multipart `kind=sttm|frd`, `file` | Store in `inputs/uploads/` and select. FRD: a JSON must parse as an FRD contract (name normalised to `.contract.json`) or a `.docx` must be an F1/F2 FRD the extractor recognises | 201 ok; 400 wrong type / invalid contract / unrecognised docx / empty; 409 running; 413 over 25 MiB |

Pairing precedence (backend): explicit `demo.pairing_map` → shared
ticket number → ≥3-token stem heuristic **as a suggestion only**.

### 3.5 Request-time display and checks (never alter generated output)

| Route | Feeds |
|---|---|
| `GET /api/demo/input-documents` | `{documents: [{kind: "reference_documents", expected[], present[{name,path}], missing[]}, {kind: "frd", matches[], stand_in}]}` → documents card + both document modals |
| `GET /api/demo/source-files` | `{frd_contract, feeds[], shell_listing[], shell_mode live|synthetic, shell_reason, shell_source, shell_listed_at, convention_check|null}` |
| `GET /api/demo/metadata-sheet` / `…/metadata-sheet.xlsx` | `{layout_note, run_label, tabs{name: {headers, rows[{values, badges, feed_slug}], state}}, coverage}` / the byte-stable workbook |
| `GET /api/demo/input-requirements` | `{check{source, rows[{row, how_to_fill, status, feeds}], summary}, document_check{source, rows, summary}, reason}` |
| `GET /api/demo/governance-checks` | `{checks[{control, deck, status, evidence}], summary, absent_decks[]}` |

### 3.6 Databricks volumes seam

| Route | Purpose | Codes |
|---|---|---|
| `GET /api/databricks/documents` | `{catalog, schema, documents{frd[], sttm[]}}`; each `{name, size, volume, state fetchable|fetched|differs, local_name?, companion_frd?, paired?}` | 503 unconfigured (hide); 502 refused (show + Retry) |
| `POST /api/databricks/fetch` `{volume, name}` | Download one document to `inputs/databricks/` → `{fetched, dest}` | 502 |
| `GET /api/databricks/publish-target` | Always answers `{available, reason, catalog?, schema?, volume?, writable_prefix}` | — |
| `POST /api/databricks/publish` `{confirm: true, feed_slug, catalog, schema_name, volume, force?}` | Upload report + notebook + framework artefacts under `<volume>/<feed>/` | 400 no confirm / outside `WRITABLE_PREFIX`; 404 no feed / nothing to publish; 502 transport; 503 unconfigured |

### 3.7 SharePoint seam (backend only — no panel in the current frontend)

`GET /api/sharepoint/config` · `GET /api/sharepoint/documents` ·
`POST /api/sharepoint/import` (201) · `POST /api/sharepoint/locate` ·
`GET /api/sharepoint/artifact/{item_id}` · `POST /api/sharepoint/publish`
(`{confirm: true}` required). Same code discipline: 503 unconfigured,
502 Graph refused, 400, 404, 413. A rebuild that adds a SharePoint panel
must mirror the volumes chooser exactly (list → fetch to
`inputs/sharepoint/` → the file joins the ordinary STTM list); there is
deliberately no second "generate from SharePoint" path.

### 3.8 Type shapes (verbatim from the client)

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

---

## Part 4 — Tokens, copy bank, platform notes, acceptance

### 4.1 Design tokens (light theme only; the App renders light)

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
| `--sidebar-bg` / `--sidebar-ink` / `--sidebar-muted` | `#16181d` / `#e8e8e4` / `#9a9aa2` | sidebar + shell block |
| `--mono` | `ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace` | slugs, paths, code, hashes |
| body font | `system-ui, -apple-system, "Segoe UI", sans-serif` 14px / 1.5 | — |
| `--radius` | 10px | cards, panels |

**Classification identity colours (fixed, never cycled):** mappable
`#2a78d6` · orchestration_config `#1baf7a` · notification `#4a3aa7` ·
out_of_scope `#898781` · flagged `#eb6834` · unmapped `#eda100`.

**Mode badge colours:** mock grey (`rgba(110,122,135,.16)` / `#4a5560`),
live red (`rgba(217,72,63,.14)` / `#a2231b`), replay blue
(`rgba(42,120,214,.14)` / accent-deep). Mode banners use the same hues
at 9–10% with a 28–30% border.

**Prism token colours:** comment muted italic; keyword/builtin `#4a3aa7`;
string `#006300`; number/boolean `#1c5cab`; function/class/decorator
`#b3400f`; operator/punctuation ink-2.

### 4.2 Copy bank (exact strings; do not paraphrase)

- Mode copy: `MOCK — deterministic stand-in provider, zero network` ·
  `LIVE — generated now; each candidate card names its provider` ·
  `REPLAY — recorded live run`.
- Sidebar footer: `Layer 1 deterministic (Jinja2) · Layer 2 review-only
  candidates.` / `Gate verdict computed in code, never by judgment.`
- Dashboard sub-line: `Pipelines generated from approved FRD + STTM
  contracts. Every rule is compiled deterministically or routed to a
  reviewed Layer-2 candidate — nothing lands unreviewed.`
- Gate flags (from the verdict computation, shown verbatim):
  `Layer-2 candidate pending engineer approval: '<rule>'` ·
  `Layer-2 candidate NOT grounded for rule '<rule>': <notes>` ·
  `Layer-2 provider failed for rule '<rule>': <notes>` ·
  `confirm item pending (document-derived, cited): <text>` ·
  `rule classified <class>: '<rule>' — <notes>` ·
  `faq_unanswered:<question>` ·
  `load_mode_not_enforced: declared <mode>; generated writer uses <behaviour> (branching planned v2)` ·
  `standards_stub: <status>` ·
  `generated tests were skipped — PASS cannot be claimed`.
- Candidate status: `Awaiting engineer decision` · `Marked approved —
  merge into generated code remains a manual (v2) step` · `Soft
  confirmation — the run proceeds; a source-team answer closes it`.
- Live unavailable: `Live is unavailable: <reason> (provider: <p>)`.
- Run states: `Running — stages appear as they start:` · `Last live run
  completed.` · `Last live run FAILED — nothing was published.`
- Chooser: `FRD document — extracted at run start` · `looks like a
  pair — confirm` · `companion FRD` ·
  `includes companion FRD — fetched together` · `differs from local copy`.
- Tooltips: landing `The real FRD states this under Structural Metadata →
  ADLS Location; this build carries an anonymized stand-in.`; load
  strategy `The real FRD states these under Structural Metadata → Load
  Strategy STG / STD; this build carries a config stand-in.`

### 4.3 Databricks App platform notes that shape the UX

- Single process serves API + built frontend (`ui/frontend/dist`
  mounted at `/` with an `index.html` fallback and `no-store` on the HTML
  shell). Port = `DATABRICKS_APP_PORT` → `CODEGEN_UI_PORT` → 8571; host
  `0.0.0.0`.
- Container restarts wipe `inputs/databricks/`, `inputs/uploads/`, the
  runner's selections (STTM, FRD, output mode → `notebook`) and past live
  runs under `out/`. The chooser's "wiped on an App restart" note and the
  Past-live-runs "this machine's run history" hint exist because of this.
- Live Layer 2 rides `reasoning.provider: databricks_fmapi` against the
  declared serving-endpoint resource (`llm-endpoint`, CAN_QUERY). The
  provider surfaces in every candidate pill and the cost modal's wording.
  `CODEGEN_FORCE_MOCK_PROVIDER=1` re-locks: badge "MOCK — provider
  locked", modal "zero model calls".
- `WorkspaceClient` construction failures become `502` with the SDK
  message; the UI shows them (never a bare 500, never hidden as
  "unconfigured").
- The unified agent console reverse-proxies every route above under
  `/api/codegen/*` and surfaces `detail` verbatim; changing a response
  shape or a status code changes the console. Keep 409 / 503 / 502
  meanings stable.
- Progress is polled (1 s), never streamed, to stay inside the Apps
  reverse-proxy's untested long-request surface.

### 4.4 Acceptance checklist (a rebuild is not done until every line holds)

1. Sidebar mode badge on every route; LIVE/REPLAY banner with label.
2. Dashboard tiles, cards, rule strip order and foot line match §2.2;
   empty state and 409 banner behave as specified.
3. Generate-all from LIVE/REPLAY prompts; from mock it runs directly.
4. Reset decisions clears only the loaded run; other runs keep theirs.
5. Feed detail tabs with counts; Notebook tab hidden for framework-only
   output; Generated code opens the first `pipeline/` file.
6. Candidate cards: provider pill, grounded pill, class badge, rationale,
   code sketch, citations; provider-failed and CONFIRM variants; toggle
   semantics (re-click → pending); status copy verbatim.
7. Run modes: STTM must be chosen before the run button enables; Clear /
   Reset behave; `frd_warning` chip; output-mode toggle persists until
   restart; documents card three states; requirements and governance
   tables with the four/three status pills.
8. Chooser: uploads, local list keeps modal open after pick, volumes
   section hidden on 503 and shown with Retry on 502, fetch/re-fetch/
   fetched states, companion FRDs collapsed, FRD section with paired /
   suggested / local / no-contract rows, Done vs Cancel.
9. Cost modal shows estimates from the backend and the FMAPI wording;
   confirm → run → 1 s polling → stage checklist → View results.
10. Failed run shows the error and, when hinted, the one-click companion
    FRD button; no auto-retry.
11. Past live runs list, incomplete runs marked not loadable.
12. Demo mode: six steps, arrow keys, dots, inline notebook, ends on the
    approve/reject queue.
13. Publish panel: defaults, policy line, confirm modal, result line,
    400 on outside-prefix targets.
14. Metadata sheet: tab strip, one provenance dot per cell, coverage
    line, xlsx download, disclaimer.
15. Every backend `detail` string reaches the screen unchanged.

---

## Appendix A — Reference files to place in the `code-gen-agent` folder (AmeriHealth workspace)

Legend: **Channel** = how the file travels. `bundle` = part of the synced
source tree (`databricks sync` from a staged tree with the repo's
`.gitignore` REMOVED, never `--full`); `email` = attached to the
hand-off email; `volume` = uploaded to the UC document volumes, never
committed; `build` = produced locally before syncing. **Need** = `must`
(the App or a test breaks without it) / `demo` (needed for the CV-golden
demo path) / `ref` (human reference, not consumed at runtime).

### A.1 Skills (the only files Genie Code can read)

| Path | Purpose | Need | Channel |
|---|---|---|---|
| `.claude/skills/code-gen-agent/SKILL.md` | Architecture + pipeline + Genie Code rebuild spec (Part A §1–§8) | must | email + bundle |
| `.claude/skills/code-gen-agent-ux/SKILL.md` | **This file** — the UX specification | must | email + bundle |
| `.claude/skills/code-gen-agent/references/deep-dive.md` | File-level tour of `src/codegen/` | ref | bundle |
| `.claude/skills/code-gen-agent/references/reusable-checklist.md` | Part B build checklist | ref | bundle |
| `.claude/skills/code-gen-agent/references/sharepoint-seam.md` | Graph transport doctrine + route status codes | ref | bundle |
| `.claude/skills/debug-everything/SKILL.md` | Repo health-sweep procedure | ref | bundle |

### A.2 Configuration, manifests, entry points

| Path | Purpose | Need | Channel |
|---|---|---|---|
| `config/config.yaml` | Every knob: contracts, extractor, naming, masking, segments, reasoning (`databricks_fmapi`, `claude-opus-5`), demo (input documents, pairing map, metadata sheet 7-tab IIG layout), engineering standards, job, gate, sharepoint, databricks | must | bundle |
| `app.yaml` | Databricks Apps manifest (`python -m ui.backend.main`, `llm-endpoint` resource) | must | bundle |
| `requirements.txt` | Apps pip install `.[ui,databricks]` + `codegen-version-marker` (bump on every `src/` change) | must | bundle |
| `pyproject.toml` | Package + extras (`dev`, `live`, `ui`, `databricks`), ruff rules, version 0.3.5 | must | bundle |
| `.env.example` | Names of every env secret/override (no values) | ref | bundle |
| `run_demo.sh` | Single-port local launcher | ref | bundle |
| `README.md`, `CLAUDE.md`, `ui/README.md` | Quick start, working conventions, UI run modes | ref | bundle |

### A.3 Source (the whole package — listed by directory)

| Path | Purpose | Need | Channel |
|---|---|---|---|
| `src/codegen/**` | Generator: contracts, resolve, extract (flat + segmented), rules, reasoning (mock / anthropic / databricks_fmapi providers), emit + templates, gate, report, cli, config, sharepoint, databricks, demo_sources, metadata_sheet, input_requirements, governance_checks, upstream_contracts | must | bundle |
| `ui/backend/*.py` | FastAPI app: main, service, demo (runner), replay, databricks_routes, sharepoint_routes | must | bundle |
| `ui/frontend/{index.html,package.json,package-lock.json,tsconfig.json,vite.config.ts,src/**}` | React source (App, api, lobs, pages ×4, components ×7, styles.css) | must | bundle |
| `ui/frontend/dist/**` | **Built bundle** (`npm install && npm run build`); gitignored, so it must be built and staged before sync; verify the remote `dist/index.html` names the fresh hash | must | build → bundle |
| `tests/**` | Offline suite (fixture-driven tests skip when fixtures absent) | must | bundle |
| `scripts/scrub_reference.py`, `scripts/scrub_check.py`, `scripts/build_acfc_deck.py` | Reference scrubber + denylist scanner (tests run it over every emitted artefact) + deck builder | must (scrub_check) / ref | bundle |

### A.4 Demo fixtures (anonymized CV-golden universe; needed for Replay, Live default pair, and the full test suite)

| Path | Purpose | Need | Channel |
|---|---|---|---|
| `fixtures/contracts/FRD_demo_cv_golden.contract.json` | Demo FRD contract (`demo.frd`) | demo | bundle |
| `fixtures/contracts/sttm_mapping_contracts_cv_golden.json` | Demo STTM contract (`demo.sttm`), byte-tested extractor golden | demo | bundle |
| `fixtures/workbooks/demo_sttm_cv_golden.xlsx` | Demo STTM workbook (`demo.workbook`) — the Live default | demo | bundle |
| `fixtures/workbooks/synthetic_segmented_golden.xlsx` | Synthetic H/D/T workbook for the segmented dialect tests | must | bundle |
| `fixtures/contracts/FRD_sfmc_email_campaign.contract.json`, `fixtures/contracts/sttm_mapping_contracts_sfmc.json` | SFMC pair (Option B / standards-alignment tests) | must | bundle |
| `fixtures/replay/live_e2e_20260807/README.md`, `call_log.json` | Tracked replay set metadata | demo | bundle |
| `fixtures/replay/live_e2e_20260807/{cv_individual_risk,cv_community_risk,cv_community_demographic_risk}/{candidates.json,report.md}` | Recorded Layer-2 candidates + reports (3 feeds, all PASS_WITH_FLAGS) | demo | bundle |
| `fixtures/faq/cv_individual_risk.faq.yaml`, `cv_community_risk.faq.yaml`, `cv_community_demographic_risk.faq.yaml`, `caqh_tpl_inbound_files.faq.yaml` | Per-feed load-pattern FAQs (`has_header`/`has_trailer`, discriminator overrides, FRD-cited answers) | must | bundle |
| `fixtures/reference/SFMC_IIG.xlsx` | SCRUBBED client IIG workbook — source of the 7-tab metadata layout | must | bundle |
| `fixtures/reference/SFMC_Deployment_Playbook.xlsx` | SCRUBBED deployment playbook | must | bundle |
| `fixtures/reference/SFMC_stage_table_creation.txt`, `SFMC_standard_table_creation.txt` | SCRUBBED DDL goldens the Option B `.txt` output conforms to | must | bundle |
| `fixtures/reference/SCRUB_REPORT.md` | What was scrubbed and how | ref | bundle |
| `tests/snapshots/notebook_mode.json` | sha256 per emitted file for the CV pair (Option A byte-stability guard) | must | bundle |

### A.5 Reference documents the documents card expects (`demo.input_documents.expected`)

These are **client documents**. They never enter a git repo; on the App
they live in `inputs/standards/` (remote-only — that is why sync must
never use `--full`) or arrive via the UC volumes / SharePoint fetch.
Place them per the program's client-document process.

| File name (matched case-insensitively, upload prefix stripped) | Role | Where it lands |
|---|---|---|
| `FRD_STG_STD_SFMC_Email_Campaign_Tracking_Details_Ingestion_1005310.docx` | Real SFMC FRD — drives the Convention check panel and the document-side input-requirements check | `inputs/standards/` (volume) |
| `FRD-to-STTM-Agent-Data-Governance-Architecture.pptx` | Governance deck — reference-architecture checks | `inputs/standards/` |
| `FRD-to-STTM-Agent-Solution-Architecture.pptx` | Solution-architecture deck — reference-architecture checks | `inputs/standards/` |
| `FRD-and-Dictionary-Input-Requirements.pptx` | Input-requirements deck — the eleven Structural Metadata rows (the one deck consumed in processing) | `inputs/standards/` |
| `EDO Data Engineering Naming Standards.docx` | Source of `engineering_standards:` (WF_/NB_ patterns, abbreviation tables) | `inputs/standards/` |
| `EDO Data Engineering Coding Standards.docx` | Source of `job:` conventions (alert DL, timeout, Photon, DBR 15.4) | `inputs/standards/` |
| `SFMC_IIG.xlsx`, `SFMC_Deployment_Playbook.xlsx`, `SFMC_stage_table_creation.txt`, `SFMC_standard_table_creation.txt` | The four scrubbed SFMC artefacts (already in `fixtures/reference/`, see A.4) | bundle |

### A.6 Client STTM/FRD documents for live runs (volumes only)

Uploaded to the document volumes (`<catalog>.<schema>.frd_raw` /
`.sttm_raw`) and fetched into `inputs/databricks/` through the chooser.
FRD contracts come from the upstream FRD→STTM agent's Delta table
(`<catalog>.sttm_agent.frd_contracts`) or from the FRD .docx itself
(standalone doctrine, 2026-09-18: selectable, extracted at run start). Live runs on these pairs need the program's
client-document approval (Venu's email).

| Document | Pairing |
|---|---|
| `FRD_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Ingestion_1005034.docx` + `…1005034.contract.json` | CAQH — paired by shared ticket `1005034` |
| `STTM_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Mapping_Document_1005034.xlsx` | CAQH STTM (segmented H/D/T) |
| `FRD_Medicare Expansion-MIDS - Socially Determined.docx` | MIDS — paired by `demo.pairing_map` |
| `STTM-Medicare Expansion-MIDS-Social Determine.xlsx` | MIDS STTM |

### A.7 Docs worth carrying for the humans (not runtime)

`docs/DESIGN.md`, `docs/WORKFLOW.md` (verdict semantics),
`docs/DEMO_RUNBOOK.md` (demo choreography, contingency, safety rails),
`docs/EDO_STANDARDS_ALIGNMENT.md`, `docs/SEGMENTED_MODE_DESIGN.md`,
`docs/EXTRACTOR_RECON.md`, `docs/LIVE_RUN_RECORD.md`,
`docs/LIVE_PATH_RECON.md`, `docs/NATIVE_REBUILD_SPEC.md`,
`docs/DATABRICKS_DISCOVERY.md`, `docs/media/demo_mode_walkthrough.gif`,
`docs/media/notebook_tab_walkthrough.gif` (the two GIFs are the closest
thing to screenshots of the intended UX — include them in the hand-off).

### A.8 What must NOT travel

- Any `.env` or credential (there is none in the repo; the App uses the
  platform-injected identity and the declared serving-endpoint resource).
- `inputs/reference_raw/` (raw client exports incl. the real RFC number),
  `inputs/client_docs/`, `inputs/databricks/`, `inputs/uploads/`,
  `inputs/sharepoint/` — client documents go by volume/SharePoint only.
- `out/`, `reports/`, `ui/backend/state/decisions.json` — run output and
  local review state.
- The repo's `.gitignore` inside the staged sync tree (it silently drops
  `dist/`, the contracts, the golden workbook and the replay set).
