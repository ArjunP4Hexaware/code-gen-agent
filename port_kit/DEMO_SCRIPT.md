# DEMO_SCRIPT — the full-UI click path

**Pair to pick:** `syn_widget_frd` + `syn_widget_sttm.xlsx` (two feeds: one fully answered, one
untouched — the contrast is the story).

**Before the audience arrives:** confirm the App booted (dashboard shows four feeds in `MOCK`);
run the pair once so a finished run sits on the outputs Volume; note its run id. Open the app
URL in a fresh tab.

**1 — Dashboard on boot.** Say: "The App generated every configured pair on start-up. Every
number here is the run's own output — verdicts, rule counts, pending reviews." Point at the
`PASS WITH FLAGS` chips: "flags are the honest state; nothing is hidden."

**2 — Run modes → choose the pair.** Click `Run modes`. Say: "Nothing is preselected; the
engineer chooses." `Choose STTM…`, pick the workbook, pick the FRD under `FRD for this run`,
`Done`. The card now names both files.

**3 — FAQ.** Click `Inspect pair`. The two feeds appear with their stage tables and rule
counts. Open tab `syn_gadget_events`: "Two answers already came from the contract — see the
evidence column. The rest are the engineer's; we leave this feed untouched on purpose."
Switch to `syn_widget_risk`: "This one is fully answered."

**4 — Generate.** Say: "One click. Every stage is named as it starts; Layer 2 is a mock today
— the modal says zero model calls." `Generate from this STTM…`, `Confirm — run live`. Watch
the stage list tick down to `publishing results — 2 feed(s), 0 failure(s)`.

**5 — Progress → results.** `View results →`. The badge reads `LIVE · <<run_id>>`; the banner
carries the label. Say: "The verdict is computed, never judged."

**6 — Feed detail.** Click `syn_gadget_events`. Overview: gate checks, then the flags panel —
"ten flags; six say exactly which question nobody answered; the amber row is the AI candidate
waiting for a human." `Rules` tab: "every rule verbatim, classified deterministically."
`Layer-2 review` tab: the one candidate, its provider, its citation. "Approve records a
decision. It never merges."

**7 — Framework artefacts panel.** Back to `Dashboard`. Point at the blank
framework-assigned IDs: "the agent never invents these."

**8 — Metadata sheet preview.** Scroll down; click through the seven tabs; hover a dot:
"every cell says where its value came from."

**9 — Downloads.** In the framework panel click the three files for `syn_gadget_events`, then
`Download .xlsx` under the preview. "These are the deliverables — byte-stable, on the Volume."

**Fallback 1 — slow or stuck run.** While the stages tick, switch to the pre-run outputs:
open the outputs Volume in the workspace file browser, `runs/<<run id noted above>>/`, and
walk `syn_gadget_events/framework/` and `reports/` there — same three files, same report.

**Fallback 2 — a run fails.** Read the red banner aloud — it names the sheet or the disagreeing
values, nothing is guessed. Then open the pre-run folder's `reports/syn_gadget_events.md`
directly and show its `Flags:` block and verdict line; the story ends the same way.
