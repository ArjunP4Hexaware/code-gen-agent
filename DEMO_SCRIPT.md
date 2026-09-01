# CodeGen Agent — Client Demo Script

## ⚡ 2026-09-01, 3 PM client demo — CAQH: "two documents, one pipeline"

Corrected build (`staging`, 0.3.1): the CAQH pair extracts with **both
layers derived from the documents, every derivation cited**. Run order:

1. **CV golden first (regression proof, ~1 min).** Load the replay set
   (`live_e2e_20260807`, ~1s, zero cost) — 3 feeds PASS_WITH_FLAGS,
   byte-identical artefacts to before the segmented work (snapshot-
   guarded). One line: "everything
   that worked before still works, to the byte."
2. **CAQH as the centerpiece (~4 min) — two documents, one pipeline.**
   Choose the CAQH STTM (+ its companion FRD). Extraction shows BOTH
   layers derived with citations:
   - **4 stage tables** in `pr_dlk.stg_mbr` (HDR 8 / DTL 101 / TRL 6
     columns + DTL_RECYCLE per the FRD's 15-day member-existence DQ) and
     **3 standard tables** in `pr_std.mbr` — "Load Strategy STG: Truncate
     and Load; STD: Append", with the STD schema sourced from the STTM's
     `PR_STD.MBR` target group (cited provenance note; the FRD's Target
     Schema block names stage targets only).
   - STRING-except-audit in both layers — FRD acceptance criterion 3,
     quoted in the provenance notes.
   - Record identification DERIVED from the STTM: the trailer's own
     "Record Type" comment states the `******` marker (quoted verbatim);
     header = first record; detail = the rest.
   The **review tab shows the two real Layer-2 candidates** (LOB_ID →
   'Payer Area'; populate file-name/timestamp/LOB/file-type fields) **+
   one soft CONFIRM item** (positional identification — confirm with the
   source team; its card quotes the exact STTM cell). Open the report:
   Segment-tables table (both layers), Record-identification section with
   evidence quotes, cited provenance notes; then the artefacts: the two
   deployment-team DDL .txt files (4 + 3 tables) and IIG rows for both
   legs (3 ADLS→STG + 3 STG→STD rows, ReferentialCheckRule DQ row vs
   `facets_member`, Weekly/Monday schedule fields).
   The demo line: *two client documents in, one pipeline out — every
   derivation quoting the cell it came from, and the one thing worth a
   human's eyes raised as a cited confirm card.*
3. **MIDS in reserve** — the zero-candidate complete run, if time allows.

**Rehearsed 2026-09-01 (timings):** replay load ~1 s; CAQH live run
(local, FMAPI) **30 s** end-to-end — extract → resolve → 2 live calls →
emit → gate → published; review tab shows 1 CONFIRM + 2 Layer-2, all
pending; past run reloadable instantly as the fallback. App (0.3.1)
smoke-tested: chooser lists the golden + synthetic workbooks, CAQH
Fetched ✓ from the volume with its companion FRD, choosers left at the
clean base state.

**⚠ App venue caution:** Databricks App runs use the **mock provider**
(the app SP lacks the FMAPI grant) — fine for this script. **The 0.3.1
build MUST be redeployed to the App and smoke-tested there before 3 PM —
a stale App build shows the retired assumption/conflict cards.**
Redeploy: sync the staged tree + `databricks apps deploy codegen-agent`
(see §7), then in the App: choose the CAQH STTM and confirm the run
reaches the review cards.

---

# (Previous script — 2026-08-28, 5 PM)

Personal, machine-specific script for today's client demo. Companion to
the committed `docs/DEMO_RUNBOOK.md` (the rehearsed client runbook) —
this version reflects the exact state of **this Mac** after the
2026-08-28 afternoon pass (`staging` @ `d7aa44c`): **Layer 2 now rides
Databricks FMAPI on `claude-opus-5`** (no Anthropic key anywhere in the
flow), the demo UI is **also deployed as a Databricks App**, and the
documents card shows **all six client reference documents**. Suite:
259 passed / 27 skipped, ruff clean.

---

## 0. Current state (already done — nothing to prepare)

- Server **running** at http://localhost:8571 (single-port mode via
  `./run_demo.sh`; FastAPI serves API + built frontend). Blank base
  state: *none chosen*, mode mock, idle. Live is **armed with no API
  key**: `/api/demo/live-available` returns
  `{"available": true, "provider": "databricks_fmapi"}` — Layer 2 goes
  through the workspace serving endpoint `databricks-claude-opus-5`.
  Anthropic is still the sole model **vendor**; Databricks FMAPI is the
  transport, and billing is DBU-metered instead of an Anthropic invoice.
- **The same UI is live as a Databricks App**:
  https://codegen-agent-7405617821962942.2.azure.databricksapps.com
  (app `codegen-agent`, deployed today; health-checked — feeds API and
  live-availability both answer). Its service principal holds CAN_QUERY
  on the Opus 5 endpoint and read grants on the UC volumes + the
  upstream `frd_contracts` table, so the Databricks documents panel in
  the app lists the **real client** STTM/FRD documents. See §7 before
  choosing it as the venue.
- **Documents card is 6/6 green** — all found in `inputs/standards/`:
  the real FRD 1005310 (SFMC Email Campaign Tracking), the two
  architecture decks, the FRD-and-Dictionary input-requirements deck,
  and the **two EDO standards documents** (Naming + Coding). The
  input-requirements deck is the one reference document that is
  *consumed*, not just displayed: its eleven rows evaluate live against
  the demo contract AND the real FRD docx (today: 8 filled / 3 missing
  on the document side).
- **Engineering standards are REAL, not a stub.** The generated banner
  now reads `Engineering standards  EDO Data Engineering Naming +
  Coding Standards (received 2026-08-26)`. The `standards_stub` flag is
  gone; feeds show **seven flags** (six `faq_unanswered:*` +
  `load_mode_not_enforced`) — that's the feature, not a regression.
- **FMAPI live path is proven today**: runs `demo_20260828_141254` and
  `demo_20260828_141345` completed with `provider: databricks_fmapi`,
  grounded candidates, PASS_WITH_FLAGS — both reloadable under **Past
  live runs**. (They ran on earlier endpoint configs; fire one
  rehearsal run before 5 PM to also prove the `claude-opus-5`
  endpoint E2E — see §5.)
- Replay contingency (`live_e2e_20260807`) still tracked and offline.
- The live card is titled **"Generate a Pipeline"**: **Choose STTM…**
  then **Generate from this STTM…** (unlocks only after a pick);
  **Clear** returns to *none chosen*.
- Refresh the browser tab right before presenting.

## 1. If the server needs a restart

From the repo root on this Mac:

```bash
lsof -ti :8571 | xargs kill    # stop whatever holds the port
./run_demo.sh                  # rebuilds frontend if stale, serves :8571
```

Then open http://localhost:8571 and confirm on **Run modes** that the
**Generate a Pipeline** card shows *none chosen* and Live is available.
The live check is config-driven now — if it shows unavailable, the
`databricks:` section or workspace auth broke; run
`databricks current-user me` to check auth. Never discover this live.
A restart always lands in the blank base state — that's by design.

## 2. The demo (~5 minutes)

### Step 1 — Open on the Run modes page

Frame the two cards in one breath:

> "Everything you'll see is real pipeline output — the only choice is
> whether we spend about 10 cents making it fresh right now, or replay a
> recorded run byte-for-byte."

(The ~10¢ now flows through your own Databricks bill — the model runs
on a Claude endpoint *inside the workspace*. That's a talking point,
not a caveat: no data leaves the platform boundary to a third-party
API.)

### Step 2 — Choose the STTM, then fire it live

The card opens at ***none chosen*** and **Generate from this STTM…**
stays disabled until you pick. Click **"Choose STTM…"** →
`demo_sttm_cv_golden.xlsx`:

> "The pipeline's input is a *chosen* STTM — the client's mapping
> workbook. In production the picker is fed from the document library
> and the Unity Catalog volumes — the Databricks panel below lists the
> real client documents already sitting in `sttm_raw`. Today we run the
> anonymized CV golden pair."

(**Do not fire a live run on the MIDS/CAQH client documents** — client
documents need the program's approval process; the CV golden is the
rehearsal pair. Fetching/listing them is fine and worth showing.)

Before firing, walk the card top to bottom:

**The Input documents card** (green, six checked names). Point at the
names — real FRD 1005310, two architecture decks, the
input-requirements deck, the two EDO standards documents:

> "The generator's inputs are *named client documents*, not prompts —
> swap the document, behavior changes. And two of these stopped being
> display-only: the EDO standards now live as data inside the generator
> — you'll see them named in every generated file's banner — and the
> input-requirements deck's eleven rows are evaluated live against both
> the contract and the real FRD document, right here on the card."

**The remaining gap** (one amber call-out): the demo FRD is an
anonymized stand-in. Don't apologize — point at the **Source files this
run will read** panel:

> "One gap we're naming ourselves: this FRD is an anonymized stand-in,
> not the real FRD with the paths to the actual client files. Here's
> every column a real FRD would fill — and everything the stand-in
> lacks wears a **SYNTHETIC** badge. The **Convention check** below is
> the proof the shape is right: the real 1005310's ADLS location, read
> live from the document, beside the synthesized template path."

**The Output selector** (Notebook / Framework artefacts / Both — the
beat for Nikshit). Click **Framework artefacts**:

> "Two shapes of deliverable from the same approved STTM. The notebook
> is the ~10% case. Framework artefacts are the ~90% case — DDL scripts
> and insert SQL as **add-ons to your master notebook** — your
> notebook, we never generate or touch it — plus the config rows as the
> approval artefact. Same generation, same gate, same verdict. The ID
> columns are blank because **the agent refuses to guess**."

(Reset to **Notebook** — or leave **Both** — before firing.)

**The shell block** ("In the Databricks workspace", collapsed) and the
**metadata sheet preview** — same beats as rehearsed: the listing is
rendered from the FRD today and says so; the metadata sheet is the
framework-mode output shape, every cell provenance-badged, IDs blank by
design.

Then click **"Generate from this STTM…"**. Read the confirmation dialog
aloud — input workbook, the demo-FRD caveat, then the cost: ~3 model
calls, ≈ $0.10, ~20 seconds:

> "The demo tells you what it costs before it spends anything — and the
> spend lands on the Databricks bill, not a third-party API."

Click **Confirm — run live**.

### Step 3 — Narrate the stage checklist (~20s)

- **extracting workbook** — the STTM Excel becomes a machine-readable
  contract *deterministically*, before any model is involved.
- **resolving contracts** — the FRD ⋈ STTM join.
- Per feed: **compiling rules** → **Layer-2 reasoning (live)** — *the
  only model step, Claude Opus 5 served by the workspace endpoint* —
  → **emitting code** → **gate**.

### Step 4 — Results walk (dashboard)

**View results →**, red **LIVE** banner, three CV feeds, all
**PASS WITH FLAGS**:

> "The honest middle state — the code is clean, but something needs a
> human. That's correct behavior, not a failure."

Metadata sheet preview at the bottom: columns tab now populated from
this run's mapping contract, all badged *from STTM*.

Each feed shows **seven flags** — pre-empt it:

> "Seven flags, and most are questions, not defects: every load-pattern
> question nobody has answered yet is a named flag. The gate refuses to
> let an unanswered question look like a decision."

### Step 5 — One feed's detail

Click any feed card (e.g. `cv_community_risk`). **Overview** tab:

- Gate checks all green — ruff, debug patterns, secrets,
  test-per-module.
- The **Flags** panel: six `faq_unanswered:*` (open load-pattern
  questions), `load_mode_not_enforced` (declared truncate-and-load; the
  writer still does MERGE-by-file — branching is v2), and the orange
  *PENDING ENGINEER APPROVAL* call-out — the bridge to the finale.
  (No `standards_stub` any more — if anyone remembers it from a
  pre-read, that's the standards input graduating from stub to real.)

### Step 5½ — The three-input model (~60s)

Stay on the feed detail and show the three inputs *in the output*:

1. **Generated code tab → `pipeline/writer.py`** — the top-of-file
   `Inputs (three-input model)` block: STTM sha256, `Engineering
   standards  EDO Data Engineering Naming + Coding Standards (received
   2026-08-26)`, `Load-pattern FAQ ..... 2 answered (2 from contract),
   6 unknown`, Collibra *not yet integrated (planned)*, then declared
   load mode vs actual write behavior:

   > "Every generated file declares its inputs and their honesty level.
   > The standards input is now the real EDO document — it drives job
   > naming, DDL shape, and the job alert/timeout settings. The FAQ has
   > two answers prefilled from the contract with quoted evidence, six
   > still waiting on an engineer."

2. **`job/workflow.json`** — frequency-prefixed job names
   (`M_ingest_…` / `Y_ingest_…`), prod-support alert DL on success and
   failure, Photon, DBR 15.4 — the standards document, visible in
   config.
3. **Notebook tab** — *Prerequisite tables* cell: under
   `create_tables: false` the notebook **lists** required tables; the
   `ddl/` files are emitted REFERENCE-only, `CLUSTER BY AUTO` + CDF per
   the Aug 26 framework calls.
4. (Optional, terminal) `fixtures/faq/cv_individual_risk.faq.yaml` —
   one answered question with `source: contract` and quoted evidence.

### Step 6 — The finale: Layer-2 review tab

Open the candidate and walk its parts: the rule quoted from the
contract → the model's rationale → the **grounded citation** (verbatim
contract text; the grounding check rejects anything it can't find) →
the candidate PySpark sketch. Then **click Approve in front of the
audience** — *merge into generated code remains a manual step*:

> "The agent proposes, the engineer confirms — and even an approval
> doesn't self-merge. That's the human-in-the-loop thesis."

Optional closers: the **Notebook** tab, or **Demo mode** in the sidebar
(six-step guided tour, ← / → keys).

## 3. If asked: "why does live output differ from the recorded run?"

That's the framing, not a bug. This model family rejects sampling
parameters, so the proposal's *phrasing* varies run to run — but every
live run to date classified the same rules, grounded every citation,
and landed the same verdicts:

> "What varies is the proposal's wording — never the contract it must
> cite or the gate it must pass."

**If asked "is this still Anthropic?"** — yes: Anthropic is the sole
model vendor across the program; Databricks FMAPI serves the same
Claude model inside the workspace. Transport changed, vendor didn't.

## 4. Contingency (no network / API failure mid-demo)

**Run modes → Replay card → `live_e2e_20260807` → Load.** Identical
walk, REPLAY badge instead of LIVE, zero model calls, fully offline.

Any live run writes `out/demo_<timestamp>/` and reappears under **Past
live runs** — today's two FMAPI runs are already there, so a mid-demo
detour never strands the results. Past runs are self-contained (own FRD
copy + `run_meta.json`) and a zero-candidate feed replays correctly
with an empty candidate list.

## 5. Pre-demo checklist (do these once, before 5 PM)

1. Fire **one rehearsal live run** on the CV golden pair to prove the
   `claude-opus-5` endpoint end-to-end (today's proven runs used the
   earlier endpoint configs). Then **Reset decisions** so the finale
   starts at *pending engineer approval*.
2. Note the first Layer-2 call (and any EXPLAIN / table read) wakes the
   auto-stopped warehouse/endpoint — DBU spend from the shared
   ~120/month pool; the rehearsal run doubles as the warm-up.
3. Refresh the tab → confirm blank state + Live available.

## 6. Safety rails

- **Don't click "Generate all feeds"** — contract pairs are empty, so
  it refuses loudly. Stay on the live/replay path.
- **No live runs on MIDS/CAQH client documents** without the program's
  client-document approval (Venu's email). CV golden only.
- **Decisions are run-scoped.** Rehearsed an Approve? **Reset
  decisions** on the dashboard.
- **Live output is isolated** to `out/demo_<timestamp>/`.
- **The only billed path is the confirmed live button.** Everything
  else is mock or replay.
- **The STTM can't change mid-run** (409 while a run is in flight).

### Reset toolkit

| Want to undo… | Use |
| --- | --- |
| The STTM choice | **Clear** button on the card |
| Approve/reject clicks | **Reset decisions** (dashboard) |
| Everything — blank base state | Restart the backend (§1) + refresh |

## 7. Venue choice: localhost vs the Databricks App

Default to **localhost:8571** — it's the rehearsed venue. The App URL
(https://codegen-agent-7405617821962942.2.azure.databricksapps.com) is
a strong closer instead: "and this exact UI is already running *as a
Databricks App* in the workspace" — open it, show the same Run-modes
page and the documents panel listing the real client documents from the
volumes. Caveats before promoting it to the main venue: no live run has
been fired from inside the App yet, viewers need workspace SSO, and the
App's snapshot is from the 15:00 redeploy (it has all six reference
documents; anything changed locally after that isn't in it — redeploy =
`databricks sync` + `databricks apps deploy`, see CLAUDE.md).

## 8. SharePoint / Databricks seams — shell blurb

The document library and the UC volumes are the program's system of
record: documents **in**, generated artifacts **out**. The network
stays at the edges — fetch before, publish after — so generation stays
deterministic, offline, credential-free:

```bash
# IN — from SharePoint (needs SHAREPOINT_* env) …
.venv/bin/python -m codegen.cli sharepoint-fetch --dest inputs/sharepoint
# … or from the UC volumes (works now, read-only, CLI OAuth):
.venv/bin/python -m codegen.cli databricks-fetch

# ... generate (the UI button, or codegen generate) ...

# OUT — after the human gate. Running this IS the approval gate —
# generation never auto-publishes.
.venv/bin/python -m codegen.cli sharepoint-publish --feed cv_community_risk
```

Talking points: app-only Graph auth scoped to `Sites.Selected`; write
scope one output folder; publish is a deliberate separate act; the
Databricks seam is read-only by design and a governance check would
flip if a write-shaped function ever appeared.
