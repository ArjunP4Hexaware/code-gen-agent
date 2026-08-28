# CodeGen Agent — Client Demo Script (2026-08-28, 5 PM)

Personal, machine-specific script for tomorrow's client demo. Companion
to the committed `docs/DEMO_RUNBOOK.md` (the rehearsed client runbook) —
this version reflects the exact state of this machine after the
demo-readiness pass (`staging` @ `4f9b096`, frontend frozen at the
`3cb9468` build): the **three-input model** plus the new demo panels
(documents card, source-files panel with live convention check, synthetic
Databricks shell block), server running, choose-an-STTM gating live,
Anthropic key proven with live runs on 2026-08-27.

---

## 0. Current state (already done — nothing to prepare)

- Server **running** at http://localhost:8571 (single-port mode: FastAPI
  serves API + the frozen `3cb9468` frontend build), started **detached**
  on 2026-08-27 (PID 2968 — survives the Claude Code session ending; do
  NOT rebuild the frontend before the demo). It is in the state a fresh
  walk wants: ***none chosen***, decisions reset, LIVE key armed. Loading
  a past run or replay set is one click if you prefer a populated
  dashboard.
- **New demo panels are live on the Generate card** (Part A,
  demo-readiness): the green **Input documents** card (three client
  reference documents present by name, scanned via
  `CODEGEN_INPUT_DOCS_DIR` in the gitignored `.env`), the **Source files
  this run will read** table (SYNTHETIC badges on stand-in values), the
  **Convention check — real FRD 1005310** block (read live from the docx
  at request time), and the collapsible **In the Databricks workspace**
  shell block. §2 Step 2 walks all of them.
- **Three-input model is live in the output**: every generated module
  carries an `Inputs (three-input model)` banner block, notebooks list
  prerequisite tables instead of executing DDL (`create_tables: false`),
  job names get frequency prefixes, and the gate adds the honesty flags
  (`faq_unanswered:*`, `load_mode_not_enforced`). Feeds show **~9-10
  flags, not 2** — that's the feature, not a regression; §2 Step 5½ is
  the beat that sells it. Suite: 170 passed / 27 skipped, ruff clean;
  generation path byte-identical to the `pre-demo-2026-08-27` tag.
- FAQ answer files exist and are tracked: `fixtures/faq/<slug>.faq.yaml`
  for the 3 CV feeds — only contract-derived prefills filled (load mode +
  frequency, with quoted evidence), everything else honestly `unknown`.
- Anthropic SDK installed (`.[live]` extra), key present and **proven** —
  two successful live runs on 2026-08-27 (`demo_20260827_142427`,
  `demo_20260827_162317`), all stages green, 3 feeds PASS_WITH_FLAGS
  each; both reloadable for free under **Past live runs**. Replay
  contingency (`live_e2e_20260807`) still tracked.
- A full walkthrough recording exists for reference/pre-reads:
  `codegen_demo_walkthrough_2026-08-27.gif` + `.mp4` in Downloads (GIF
  emailed to Arjun 2026-08-27).
- The live card is titled **"Generate a Pipeline"** and reads as two
  steps: **Choose STTM…** (picker) then **Generate from this STTM…**
  (unlocks only after a pick). A **Clear** button beside the chosen name
  returns it to *none chosen* at any time.
- Refresh the browser tab right before presenting so it shows the fresh
  blank state.

## 1. If the server needs a restart

The current server (PID 2968) was started detached via `Start-Process`,
so it is NOT tied to any terminal. If it must be restarted: end the
`python.exe` bound to :8571 (Task Manager, or `Stop-Process -Id 2968`),
then from the repo root (don't use `run_demo.sh` — it hardcodes the
Linux venv path):

```powershell
.venv\Scripts\python.exe -m ui.backend.main
```

Then open http://localhost:8571 and confirm on **Run modes** that the
**Generate a Pipeline** card shows *none chosen* with a working **Choose
STTM…** button — not "no ANTHROPIC_API_KEY". If live shows unavailable,
fix `.env` and restart — never discover this live. A restart always
lands in the blank base state (empty dashboard, no STTM chosen, Generate
disabled) — that's by design, not a fault, and it's your clean starting
point.

## 2. The demo (~5 minutes)

### Step 1 — Open on the Run modes page

Frame the two cards in one breath:

> "Everything you'll see is real pipeline output — the only choice is
> whether we spend about 10 cents making it fresh right now, or replay a
> recorded run byte-for-byte."

### Step 2 — Choose the STTM, then fire it live

The **Generate a Pipeline** card reads as two explicit steps, and the
choice is *enforced*: the card opens at ***none chosen*** and the
**Generate from this STTM…** button stays disabled until you pick.

For **Step 1 — choose an STTM**, click **"Choose STTM…"**: a picker
opens, scanned live from the fixtures directory and the
`inputs/sharepoint` landing folder. Click `demo_sttm_cv_golden.xlsx` —
the card updates to show your choice, the row gets its *selected* badge,
and the Generate button unlocks:

> "The pipeline's input is a *chosen* STTM — the client's mapping
> workbook. In production the picker is fed from the SharePoint document
> library, the program's system of record: anything `sharepoint-fetch`
> pulls down appears in this list. Today the library holds one anonymized
> CV workbook."

(Optional: show the SharePoint shell blurb in §6 here — how the same
choice looks from the terminal. And if you fumble or want to re-run the
moment, the **Clear** button next to the chosen name puts the card
straight back to *none chosen* — no restart.)

Before firing, walk the card top to bottom — three beats, in the order
they sit on screen:

**The Input documents card** (green, three checked names). Point at the
file names — the real FRD 1005310 and the two architecture decks, found
by name in the configured input directory:

> "The generator's inputs are *named client documents*, not prompts —
> swap the document, behavior changes. The card is live: drop a file in
> the input directory and it goes green; take it away and the gap comes
> back. And it says on its face what's wired today: display only, wiring
> into generation is the next step."

**The remaining gap** (one amber call-out): the demo FRD is an anonymized
stand-in. Don't apologize — point at the **Source files this run will
read** panel directly above it:

> "One gap we're naming ourselves: this FRD is an anonymized stand-in,
> not the real FRD with the paths to the actual client files. Here's
> every column a real FRD would fill — landing root, file patterns,
> format, frequency, targets — and everything the stand-in lacks wears a
> **SYNTHETIC** badge that tells you exactly where in the real FRD the
> value lives. And the **Convention check** block below it is the proof
> the shape is right: the real 1005310's ADLS location, read live from
> the document, sitting beside the synthesized template path — same
> convention, real vs stand-in."

**The Output selector** (Notebook / Framework artefacts / Both — the beat
for Nikshit). Click **Framework artefacts**:

> "Two shapes of deliverable from the same approved STTM. The notebook is
> the ~10% case — a fresh standalone pipeline. Framework artefacts are the
> ~90% case — an *addition* to your existing ingestion framework: DDL
> scripts, config rows, insert statements. Same generation, same gate,
> same verdict — only what lands on disk changes. After a run, open
> `config_rows.xlsx` and `ADDITION.md` from the results page: the config
> rows are the approval artefact, the inserts run only after approval
> through your metadata path, and the ID columns are blank because your
> framework assigns them — **the agent refuses to guess**."

(Reset to **Notebook** — or leave **Both** — before firing, per what you
want the results walk to show.)

**The shell block** ("In the Databricks workspace", collapsed). Expand it
once:

> "This is what `fs ls` shows once the Databricks seam lands — today it's
> rendered from the FRD's landing location and file patterns, and it says
> so in the header. When the seam is live, this becomes a real listing."

**The metadata sheet preview** ("For ACFC's framework", below the shell
block — the beat for Nikshit and Raj). Click through the three tabs, point
at the coverage line:

> "The notebook you'll see generated is what the agent does *today*. For
> your metadata-driven framework, this is the output shape it becomes: a
> reviewable metadata sheet, not code. Every cell is badged with where its
> value came from — the FRD, the STTM, or a stand-in — and the coverage
> line tells you how many values came from your documents. The three ID
> columns, cluster and service principal are blank *by design*: your
> framework assigns those, so **the agent refuses to guess**. And the
> layout itself — tabs, headers — is our stand-in until your metadata
> template arrives; the values carry over. Review the sheet, approve it,
> and insertion goes through your existing metadata path; a workflow then
> wraps your common notebook with the assigned IDs."

Then click **"Generate from this STTM…"**. Read the confirmation dialog
aloud — it names the input workbook, repeats the one remaining caveat
(a demo FRD without the real file paths — the run is real, the case it
represents is not), then the cost: ~3 billed API calls, ≈ $0.10, ~20
seconds:

> "The demo tells you what it costs before it spends anything."

Click **Confirm — run live**.

### Step 3 — Narrate the stage checklist (~20s)

- **extracting workbook** — call this out: the client's STTM Excel
  workbook becomes a machine-readable mapping contract,
  *deterministically*, before any model is involved.
- **resolving contracts** — the FRD ⋈ STTM join that fingerprints
  everything downstream.
- Per feed: **compiling rules** (deterministic classifier) → **Layer-2
  reasoning (live)** — *the only billed step* — → **emitting code** →
  **gate**.

### Step 4 — Results walk (dashboard)

Click **View results →**. Point at the red **LIVE** banner. Three CV
feeds, all **PASS WITH FLAGS**:

> "The honest middle state — the code is clean, but something needs a
> human. That's correct behavior, not a failure."

At the bottom of the dashboard, the **metadata sheet preview** reappears —
and now its `columns` tab is populated from the run's mapping contract
(every mapped column, ordinal preserved, all badged *from STTM*). One
line, pointing at the coverage numbers:

> "Same sheet as before the run — but now the columns tab is filled from
> the mapping contract this run extracted. The download button gives the
> reviewable Excel, provenance sheet included."

Each feed now shows **~10 flags** — pre-empt it before anyone reads it as
trouble:

> "Ten flags, and most of them are questions, not defects: every
> load-pattern question nobody has answered yet is a named flag. The gate
> refuses to let an unanswered question look like a decision."

### Step 5 — One feed's detail

Click any feed card (e.g. `cv_community_risk`). On the **Overview** tab:

- Gate checks all green — ruff, debug patterns, secrets, test-per-module.
- The **Flags** panel — walk it top to bottom: six `faq_unanswered:*`
  (the open load-pattern questions), `load_mode_not_enforced` (declared
  truncate-and-load; the writer still does MERGE-by-file — branching is
  v2), `standards_stub`, and the orange *PENDING ENGINEER APPROVAL*
  call-out — that last one is the bridge to the finale.

### Step 5½ — The three-input model (~60s, the new beat)

Stay on the feed detail and show the three inputs *in the output*:

1. **Generated code tab → `pipeline/writer.py`** — scroll to the top-of-file
   banner and read the `Inputs (three-input model)` block aloud: STTM
   sha256, `Engineering standards  STUB — awaiting client engineering
   standards document`, `Load-pattern FAQ ..... 2 answered (2 from
   contract), 6 unknown`, Collibra dataset IDs *not yet integrated
   (planned)*, then the last two lines — **declared** load mode vs the
   **actual** write behavior:

   > "Every generated file declares its inputs and their honesty level.
   > Three inputs: the approved STTM contract — real; the client's
   > engineering standards — a declared stub until their document lands;
   > and a per-feed load-pattern FAQ — two answers prefilled from the
   > contract with the quoted evidence, six still waiting on an engineer."

2. **Generated code tab → `job/workflow.json`** — the job name:
   `M_ingest_cv_individual_risk` / `Y_ingest_cv_community_risk` — the
   standards input already naming jobs by load frequency (FAQ-sourced).
3. **Notebook tab** — scroll to the *Prerequisite tables* cell near the
   top: under `create_tables: false` (the MVP prerequisite — tables
   already exist at the client) the notebook **lists** the required
   tables instead of creating them; the `ddl/` files are still emitted,
   marked REFERENCE only.
4. (Optional, terminal) `fixtures/faq/cv_individual_risk.faq.yaml` — one
   answered question with `source: contract` and the quoted evidence
   string; everything unanswered simply isn't there.

If asked "so what's real and what's stubbed?" — the one-breath version:

> "Everything structural still compiles deterministically from the
> approved contracts, byte-stable — that path is unchanged. What's new is
> that the generator reads three inputs and every file says which were
> real for that run. The standards input is an honest stub that already
> drives job naming and the prerequisite-tables behavior. The FAQ
> captures the load-pattern questions with a source on every answer, and
> unanswered ones become gate flags, never silent defaults. And a
> declared load mode doesn't change the write path yet — the writer says
> so itself; that's the v2 work."

### Step 6 — The finale: Layer-2 review tab

Open the candidate and walk its parts:

1. The rule quoted from the contract.
2. The model's rationale.
3. The **grounded citation** — verbatim contract text; the grounding
   check rejects anything it can't find in the source.
4. The candidate PySpark sketch.

Then **click Approve in front of the audience** and read the copy that
appears — *merge into generated code remains a manual step*:

> "The agent proposes, the engineer confirms — and even an approval
> doesn't self-merge. That's the human-in-the-loop thesis."

Optional closers: the **Notebook** tab (the single runnable `.ipynb`
deliverable per feed), or **Demo mode** in the sidebar — the six-step
guided tour (← / → keys) ending on the same human-review step.

## 3. If asked: "why does live output differ from the recorded run?"

That's the framing, not a bug. This model family rejects sampling
parameters, so the proposal's *phrasing* varies run to run — but every
live run to date classified the same rules, grounded every citation, and
landed the same verdicts:

> "What varies is the proposal's wording — never the contract it must
> cite or the gate it must pass."

## 4. Contingency (no network / API failure mid-demo)

**Run modes → Replay card → `live_e2e_20260807` → Load.** Identical walk
(dashboard → feed detail → approve), REPLAY badge instead of LIVE, zero
API calls, works fully offline.

Any live run you fire during the demo writes `out/demo_<timestamp>/` and
reappears under **Past live runs** — a mid-demo detour never strands the
results. (A crashed run shows as failed with its error; the single-run
guard releases; the failed directory won't load.)

## 5. Safety rails

- **Don't click "Generate all feeds"** — contract pairs are empty, so it
  refuses loudly. Stay on the live/replay path.
- **Decisions are run-scoped.** If you rehearse the Approve click before
  the demo, hit **Reset decisions** (dashboard) afterwards so the finale
  starts at *pending engineer approval*.
- **Live output is isolated** to `out/demo_<timestamp>/` — it can never
  touch the tracked replay fixtures or the default output tree.
- **The only billed path is the confirmed live button.** Everything else
  is mock or replay.
- **The STTM can't change mid-run.** Choose, Clear, and the picker all
  refuse (409) while a live run is in flight.

### Reset toolkit (presenter's sanity)

| Want to undo… | Use |
| --- | --- |
| The STTM choice (back to *none chosen*) | **Clear** button on the card |
| Approve/reject clicks from rehearsal | **Reset decisions** (dashboard) |
| Everything — full blank base state | Restart the backend (§1) + refresh the tab |

## 6. SharePoint integration — shell blurb

The document library is the program's system of record: STTM workbooks
and FRD contracts **in**, generated artifacts **out**. The network stays
at the edges — fetch before, publish after — so generation itself remains
deterministic, offline, and credential-free. Show (or run, if the
`SHAREPOINT_TENANT_ID` / `SHAREPOINT_CLIENT_ID` /
`SHAREPOINT_CLIENT_SECRET` env vars are set) this:

```powershell
# IN — choose your STTM: pull the mapping workbooks + FRD contracts
# from the SharePoint library into the local input directory
.venv\Scripts\python.exe -m codegen.cli sharepoint-fetch --dest inputs\sharepoint

# ... generate (the UI button, or codegen generate) ...

# OUT — after the human gate: publish one feed's report + assembled
# notebook back to the library's output folder. Running this command IS
# the approval gate — generation never auto-publishes.
.venv\Scripts\python.exe -m codegen.cli sharepoint-publish --feed cv_community_risk
```

Talking points: app-only Graph auth scoped to `Sites.Selected` on one
site; write scope limited to a single output folder; publish is a
deliberate, separate act — a re-generate is never a re-publish. The UI's
SharePoint panel drives the same path: a picked document lands in
`inputs/sharepoint/` and goes through the ordinary generate flow, and the
HTTP publish endpoint additionally requires `{"confirm": true}`.
