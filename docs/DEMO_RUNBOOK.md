# CodeGen client demo — runbook

How to run the client-facing demo in `ui/` (Run modes → live pipeline →
HITL review). Companion to `ui/README.md` (setup detail, run modes,
guardrails), `docs/LIVE_RUN_RECORD.md` (where the cost numbers come from),
and `fixtures/replay/live_e2e_20260807/README.md` (the tracked contingency
set). Rehearsed end-to-end in the browser on 2026-08-07.

## 0. Fresh-machine bootstrap (clone → demo-ready)

A bare clone does NOT run the demo: the demo fixtures are deliberately
untracked (CLAUDE.md "Fixtures & data rules") and secrets never ship.
On a new machine, in Git Bash (byte-safe redirection; PowerShell `>`
would corrupt the .xlsx):

```bash
git clone https://github.com/ArjunP4Hexaware/code-gen-agent.git && cd code-gen-agent
python -m venv .venv && .venv/Scripts/pip install -e ".[dev,live,ui]"   # POSIX: .venv/bin/pip

# Restore the ANONYMIZED demo fixtures from history, working-tree-only.
# ONLY these four paths — the MIDS/CAQH client-derived contracts at the
# same commit must NOT be restored. Never `git checkout` (it would stage
# and re-track them); `git show` writes untracked files that .gitignore
# keeps out of commits.
mkdir -p fixtures/contracts fixtures/workbooks
for p in fixtures/contracts/FRD_demo_cv_golden.contract.json \
         fixtures/contracts/sttm_mapping_contracts_cv_golden.json \
         fixtures/workbooks/demo_sttm_cv_golden.xlsx; do
  git show "044752e^:$p" > "$p"
done
git ls-tree -r --name-only "044752e^" -- fixtures/replay/live_e2e_20260807 |
  while read -r p; do mkdir -p "$(dirname "$p")"; git show "044752e^:$p" > "$p"; done

.venv/Scripts/python.exe -m pytest -q      # sanity: the restored fixtures re-enable the full suite
```

What can never come from GitHub — move each by its own channel:

- **`.env`** (`ANTHROPIC_API_KEY=...`) — copy manually / from the key
  vault. Only needed for LIVE runs; Mock and Replay need no key.
- **Client documents** (the MIDS/CAQH docx/xlsx) — fetch from the
  Databricks volumes with `codegen databricks-fetch` (needs a
  `databricks auth login` profile), or the SharePoint picker. Never via
  the repo. The convention-check / source-files panels simply don't
  render without them; the CV-golden demo path doesn't need them.
- **Past live runs** (`out/demo_<ts>/`) — local to the machine that ran
  them. To show a specific recorded live run's "View results" on another
  machine, copy that `out/demo_<ts>/` directory over (each is
  self-contained: own FRD copy + `run_meta.json`). Otherwise use the
  tracked Replay set — that's what it's for.

Node.js must be installed; `./run_demo.sh` (section 1) runs
`npm install`/build for `ui/frontend` on first use.

## 1. Pre-demo checklist

```bash
.venv/bin/pip install -e ".[dev,live,ui]"   # generator + anthropic SDK + fastapi
ls -l .env                                   # ANTHROPIC_API_KEY=..., -rw------- (600)
./run_demo.sh                                # rebuilds frontend if stale; http://localhost:8571
```

Then, in the browser, before the audience arrives:

1. **Run modes page** → the Live card's key-presence state must show the
   run button, not "no ANTHROPIC_API_KEY". If it shows unavailable, fix
   `.env` and restart — do not discover this live.
2. **Verify the contingency first**: load the tracked replay set
   `live_e2e_20260807` (Replay card) and confirm the dashboard renders 3
   CV feeds PASS_WITH_FLAGS. The fallback must be proven before the live
   path is trusted.
3. **Reset decisions** (dashboard button) on whichever run you'll walk, so
   every candidate shows *pending engineer approval* — the HITL finale
   needs a clean slate. Decisions are run-scoped, so reset the run you'll
   actually present.

## 2. Choreography

**Open on the Run modes page** and frame the two cards in one breath:
*"everything you'll see is real pipeline output — the only choice is
whether we spend ~10 cents making it fresh right now, or replay a recorded
run byte-for-byte."* Then fire live:

1. **"Run live…"** → read the confirmation dialog aloud — ~3 billed API
   calls, ≈ $0.10, ~20s: *"the demo tells you what it costs before it
   spends anything."*
2. Narrate the stage checklist as entries appear (~20s total):
   - **extracting workbook** — call this one out: the client's STTM Excel
     workbook becomes a machine-readable mapping contract,
     deterministically, before any model is involved.
   - **resolving contracts** — FRD ⋈ extracted contract, the join that
     fingerprints everything downstream.
   - per-feed: **compiling rules** (deterministic classifier) → **Layer-2
     reasoning (live)** — the only billed step — → **emitting code** →
     **gate**.
3. **Results walk**, dashboard first: three CV feeds, verdicts
   PASS_WITH_FLAGS. Talking point: *"the honest middle state — code is
   clean, but something needs a human. That's correct behavior, not a
   failure."* The LIVE badge and banner are on screen; point at them.
4. **One feed's detail** (any `cv_*`): gate checks all green (ruff, debug
   patterns, secrets, test-per-module), then the Flags panel — the
   PENDING ENGINEER APPROVAL call-out is the bridge to the finale.
5. **Layer-2 review — the finale.** Open the candidate: the rule quoted
   from the contract, the model's rationale, the grounded citation
   (verbatim contract text — the grounding check rejects anything it can't
   find in the source), and the candidate PySpark sketch. Then **click
   Approve in front of the client**, and read the copy that appears:
   *merge into generated code remains a manual step*. That sentence is the
   product's HITL thesis — the agent proposes, the engineer confirms, and
   even an approval doesn't self-merge.

## 3. Non-determinism framing (grounded in observed runs)

Sampling parameters are rejected by this model family, so live output
varies run to run — the rehearsal's live run produced a candidate sketch
with the same two-line valid/reject filter shape as the tracked replay
set's, with surface differences (line order, quote style). If someone
notices the replay and live variants differ: that is the framing, not a
bug — *"the agent proposes; the engineer confirms. What varies is the
proposal's phrasing, never the contract it must cite or the gate it must
pass."* Every live run to date classified the same rules `mappable`,
grounded every citation, and landed the same verdicts.

## 4. Contingency

No key, API failure, no network → **Replay card → `live_e2e_20260807` →
Load**. Identical walk (dashboard → feed → HITL approve), REPLAY badge
instead of LIVE, zero API calls, works offline on a fresh clone — the set
ships in git. Completed live runs are also reloadable from the Live card's
**Past live runs** list ("this machine's run history") — including the
one you may have just fired — so a mid-demo detour never strands the
results. (A crashed live run surfaces as a failed state with the error;
the single-run guard releases; its directory is labeled failed and won't
load.)

## 5. Safety rails (for the presenter's nerves)

- **Generate all feeds** from LIVE or REPLAY state asks for confirmation
  before replacing the view with a mock run — no stray-click resets.
- **Decisions are run-scoped** — approvals made rehearsing one run never
  appear in another; the Reset decisions button clears only the loaded
  run's slate.
- **Live output is isolated** to `out/demo_<timestamp>/` — it can never
  touch the tracked replay fixtures or the default output tree.
- The only billed path is the confirmed live button; the generate endpoint
  is hardwired to the mock provider.

## 6. Rehearsal record (2026-08-07)

Maiden voyage of the in-UI confirm button: run `demo_20260807_094606` —
all stages green, 3 feeds PASS_WITH_FLAGS, every citation grounded on the
first firing. Three demo-flow findings were identified in the same
rehearsal and fixed the same day (verified in the running app at
`bde2b1e`):

1. **Decision bleed-through** — approvals were keyed by rule alone and
   leaked across runs/modes → run-scoped keying + the Reset button.
2. **Unrecoverable live results** — leaving a live run's view lost it →
   the Past live runs loader.
3. **Unguarded Generate-all** — one click silently replaced the live view
   → the confirmation dialog.

## 7. Known gaps (honest footer)

1. **First live run on an actual Databricks Apps deployment still
   pending.** The UI polls for progress rather than streaming precisely to
   minimize the untested-proxy surface (see `app.yaml`), but nothing has
   been exercised against a real workspace yet.
2. **UC-volume / bundle-job execution is not wired** — the pipeline runs
   in-process on the demo machine; the workspace version would trigger a
   job and read outputs from volumes.
3. **The CAQH segmented (H/D/T) workbook family is out of extractor
   scope** pending the source dictionary and the standard-target decision
   — the CAQH feed in mock state runs on a clearly-labeled synthetic
   contract.
