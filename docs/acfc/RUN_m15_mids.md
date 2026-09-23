# RUN M15 — MIDS STTM on `acfc-local` (0.5.8.post5)

Date: 2026-09-23  
Branch: `acfc-local` at `71ea571` (merged `origin/fix/remove-mock-provider-ui-text` at `16238d0`, M15)  
Deployment: `01f1b7939dc61054a9adad2d5192c466` (SNAPSHOT, SUCCEEDED)  
App: codegen-agent (`https://...azure.databricksapps.com`)  
STTM: the MIDS workbook (T02 / T03)  
Prior selection (from `selection.json`): STTM, FRD, VDD all recorded for the MIDS triple

---

## 1  Timing — NOT captured (auth blocker)

The Genie Code session could not authenticate to the App's OAuth2 SSO
endpoint from serverless compute (tried: bare request → 401, SDK runtime
token → 401, workspace `/apps/` proxy → returns SSO login page HTML).
Wall-clock timing (chooser warm, Generate enable, FRD/VDD chip resolve,
per-step trace) and `/api/demo/status` payloads were not captured
programmatically.

**Operator observation (manual run):**

> "The screen went white and I had to refresh after I put in the STTM.
> After I reloaded, the FRD was auto paired but the VDD was still loading
> to be paired. The blue button was available."

The remainder of this section records the diagnosis of the two bugs
observed.

---

## 2  Bug: White screen after STTM selection

### Symptom

Selecting the MIDS STTM in the chooser caused the entire page to go
white (blank). The operator had to refresh the browser. After reload,
the FRD was already paired but the VDD was still resolving.

### Diagnosis

**No React ErrorBoundary.** The React tree (`App.tsx`) has no
`ErrorBoundary` component; `grep -rn ErrorBoundary ui/frontend/src/`
returns zero hits. Any uncaught render-time exception kills the entire
React component tree and produces a blank white page — the browser shows
no error to the user.

**M15.2 transitional state.** The M15 changes (`49108e6`) split the
selection job into two phases:

1. **Classify** — the STTM is read and the workbook is applied
   (`_finish_job` at `demo.py:976`). The job state becomes `"done"`,
   `_job_done.set()` fires, and `selection_job.pairing_pending` is
   `["frd", "vdd"]`. Generate is enabled.
2. **Pair FRD / Pair VDD** — run sequentially AFTER the job is "done"
   (lines 977–993). `pairing_pending` shrinks as each pair resolves.

The frontend polling loop (`ModesPage.tsx:400–410`) now includes
`pairingPending.size` in its dependency array and fires at 700 ms while
any pair is pending. The `useEffect` at line 411–423 triggers a
workbook + FRD-choices refresh each time `selectionJob` changes (its
render key at line 412–413 includes `pairing_pending.join(",")`).

**The crash vector.** In the M15.2 transitional state, the status
response arrives with the job `"done"`, `pairing_pending: ["frd","vdd"]`,
the previous STTM's automatic pairs dropped (`_drop_auto_pair` at lines
971–972: `frd_auto_paired = None`, `vdd_auto_paired = None`), and the
selection updated. Multiple concurrent state updates from the polling
effect and the job-change effect race; React re-renders with an
intermediate state snapshot. Without an ErrorBoundary, any TypeError in
the render path (a null dereference on a pairing field that is `None` in
the transitional window) produces the white screen.

The `chooseWorkbook` callback (line 426–434) also fires a one-shot
`api.demoStatus().then(setStatus)` immediately after the POST returns
(202), which races with the first polling tick. Two status responses can
merge into one React batch, producing a state combination no single
response would.

### Severity and scope

* Happens on FIRST selection of a cold app (cold index → pairing steps
  take longer → wider transitional window).
* Likely intermittent: the race depends on whether the first status poll
  arrives in the window between `_finish_job` and the first
  `_apply_pair`.
* After reload, the `_start_restore` job reads `selection.json` and
  re-pairs — slower for VDD (see bug #2) but the page does not crash
  because the restore job transitions in a single shot.

### Recommended fix (not applied — diagnosis only)

1. **Add an ErrorBoundary** wrapping `<Routes>` in `App.tsx`. A
   render-time exception should show a recoverable "reload" message, not
   a blank page.
2. **Guard the pairing chip rendering** against the transitional null
   window: `status?.frd_auto_paired?.rule` and
   `status?.vdd_auto_paired?.rule` should use optional chaining
   consistently (the existing code at lines 667–673 and 694–700 accesses
   `.rule` without `?.` only after the truthiness check, which is
   technically safe — the issue may be one level deeper in a custom
   component or a stale closure).
3. **Debounce the one-shot status poll** in `chooseWorkbook`: skip the
   immediate `api.demoStatus()` and let the polling loop (already
   running at 700 ms) deliver the next status. This closes the
   two-response race.

---

## 3  Bug: VDD pairing delay

### Symptom

After reload, the FRD chip showed its paired document immediately while
the VDD chip stayed in "Pairing…" for a noticeable duration before
resolving.

### Diagnosis

**Sequential pairing by design.** In `_run_selection` (lines 977–993),
the FRD and VDD are paired in a serial `for kind in ("frd", "vdd")`
loop. The VDD step starts only after the FRD step completes.

**VDD reads workbooks (openpyxl).** FRD pairing scans `.contract.json`
and `.docx` files — small, fast to classify. VDD pairing scans `.xlsx`
workbooks via the child parser process (`ParserProcess` /
`codegen.layout.docworker`). Each unindexed workbook candidate must be:

1. Downloaded from the Workspace API (the `_fetch` call at line 378).
2. Sent to the child process for classification (openpyxl load +
   sheet-level content extraction).
3. Scored by `pair_by_content` against the STTM's pairing facts.

With a **cold index** (after the white-screen reload destroyed the
in-memory index, and the background reader had not yet reached the MIDS
folder), every VDD candidate must be read from scratch. The M15.8
`prioritize` optimization moves the chosen STTM's folder to the front
of the index queue, but the VDD step's own `read_now` calls still pay
the download + parse cost for any candidate not yet indexed.

**After reload specifically:** The `_start_restore` job re-reads
`selection.json`, locates the STTM, then pairs FRD and VDD again.
The FRD resolves quickly because FRD contracts are lightweight
(`.contract.json` or `.docx`). The VDD candidate — a `.xlsx` workbook —
is re-downloaded and re-parsed. The restore job's FRD pairing may also
benefit from the background index having classified FRD candidates
already (the background reader starts at app launch and may have reached
the FRD files before the VDD files in natural folder order).

### Severity

* Observable in every cold-start selection of the MIDS triple.
* The M15.1 optimization (index writes leave the selection path) and
  M15.8 (folder prioritization) reduce the cost, but the sequential
  design means VDD always pays whatever time FRD spent plus its own.
* For a demo, the "Pairing…" chip on VDD is confusing when FRD resolves
  instantly — the operator may think something is wrong.

### Recommended fix (not applied — diagnosis only)

1. **Parallel FRD + VDD pairing.** Run both `_plan_pair` calls in
   parallel threads (they share no mutable state until `_apply_pair`).
   The total pairing time becomes `max(frd, vdd)` instead of
   `frd + vdd`.
2. **Pre-warm the MIDS folder.** On app start, `prioritize` the last
   `selection.json`'s folder so the background reader indexes it first,
   before any user action.

---

## 4  Tokenised client terms

| Token ID | Category            | Appears in                                    |
| -------- | ------------------- | --------------------------------------------- |
| T01      | program_name        | FRD / STTM / VDD file names                  |
| T02      | vendor_product       | FRD / STTM / VDD file names                  |
| T03      | vendor_name         | FRD / STTM / VDD file names                  |
| T04      | feed_table          | STTM mapping sheets, document index           |
| T05      | feed_table          | STTM mapping sheets, document index           |
| T06      | feed_table          | STTM mapping sheets, document index           |
| T07      | schema              | STTM standard layer, document index           |
| T08      | schema              | STTM stage layer, document index              |
| T09      | file_pattern        | FILE_DETAILS sheet, document index            |
| T10      | file_pattern        | FILE_DETAILS sheet, document index            |
| T11      | file_pattern        | FILE_DETAILS sheet, document index            |
| T12      | sheet_name          | STTM workbook mapping sheets                 |
| T13      | sheet_name          | STTM workbook mapping sheets                 |
| T14      | sheet_name          | STTM workbook mapping sheets                 |
| T15      | vdd_sheet           | VDD workbook field sheets                     |
| T16      | vdd_sheet           | VDD workbook field sheets                     |
| T17      | vdd_sheet           | VDD workbook field sheets                     |
| T18      | workspace_user      | deployment, state-role paths                  |
| T19      | lob_domain          | FRD structural metadata                       |

All raw values corresponding to these tokens are in
`HOME/codegen-state/denylist_local.txt` (never committed).

---

## 5  Pairing payloads — NOT captured

The `/api/demo/status` pairing payloads (`pairing.frd` and
`pairing.vdd` with every candidate, score, rule, and chosen document)
could not be captured due to the auth blocker (§1).

From the **document index** (last indexed state), the MIDS triple is:

* **STTM** — classified `sttm` by mapping sheet discovery
  (`MAPPING-` prefix), 3 mapping sheets, tables: T04/T05/T06, schemas:
  T07/T08, file patterns: T09/T10/T11.
* **FRD** — classified `frd`, 1 unnamed feed, file patterns match STTM.
* **VDD** — classified `vdd` by dictionary sheet discovery
  (`FILES` + field sheets T15/T16/T17), 3 tables, file patterns overlap
  STTM.

The prior `selection.json` recorded the MIDS triple successfully (STTM +
FRD + VDD all non-null), confirming the pairing logic resolves when given
enough time.

---

## 6  Cold-start repeat — NOT performed

A second stop/start measurement was not performed due to the auth
blocker.

---

## 7  Commit record

* `acfc-local` merge: `71ea571` (not pushed — local deployment branch)
* This document committed on `acfc-runs` (see below)
