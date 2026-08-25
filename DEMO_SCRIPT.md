# CodeGen Agent — Manager Demo Script (2026-08-25)

Personal, machine-specific script for today's demo. Companion to the
committed `docs/DEMO_RUNBOOK.md` (the rehearsed client runbook) — this
version reflects the exact state of this machine as of the 2026-08-25
afternoon build: server running, blank base state, choose-an-STTM gating
live, Anthropic key verified working.

---

## 0. Current state (already done — nothing to prepare)

- Server **running** at http://localhost:8571 (single-port mode: FastAPI
  serves API + built frontend), sitting in the **blank base state**: MOCK
  badge, empty dashboard, STTM workbook shows ***none chosen***, and
  **"Generate from this STTM…" is disabled** until a workbook is picked.
- Anthropic SDK installed (`.[live]` extra), key present and **proven** —
  two successful live runs today, all stages green, 3 feeds each.
- The live card is titled **"Generate a Pipeline"** and reads as two
  steps: **Choose STTM…** (picker) then **Generate from this STTM…**
  (unlocks only after a pick). A **Clear** button beside the chosen name
  returns it to *none chosen* at any time.
- Past run `demo_20260825_111028` is reloadable for free under **Past
  live runs**; replay contingency (`live_e2e_20260807`) verified today.
- Refresh the browser tab right before presenting so it shows the fresh
  blank state.

## 1. If the server needs a restart

From the repo root (don't use `run_demo.sh` — it hardcodes the Linux venv
path):

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

Before firing, point at the **Known input gaps** panel — two amber
call-outs on the card, each with its own input slot (**Attach…** /
**Provide…**). Click one live: the dialog does a real scan of
`inputs/sharepoint/` and reports *Not present*, with instructions on
where the document would come from — the slot exists, the document
doesn't. Own them; honesty is the pitch:

> "Two gaps we're naming ourselves. One: the generator wants the client's
> coding standards document for best performance — we don't have it yet,
> so it runs without. Two: this FRD is an anonymized stand-in, not the
> real FRD with the paths to the actual files. So the pipeline you're
> about to watch is real end-to-end, but the *case* it represents is not
> — plug in the real documents and this same run becomes the real thing."

Then click **"Generate from this STTM…"**. Read the confirmation dialog
aloud — it names the input workbook, repeats the input-gaps caveat, then
the cost: ~3 billed API calls, ≈ $0.10, ~20 seconds:

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

### Step 5 — One feed's detail

Click any feed card (e.g. `cv_community_risk`). On the **Overview** tab:

- Gate checks all green — ruff, debug patterns, secrets, test-per-module.
- The **Flags** panel — the orange *PENDING ENGINEER APPROVAL* call-out
  is the bridge to the finale.

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
