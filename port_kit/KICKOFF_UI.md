# KICKOFF_UI — paste this as the first message for slice S7

You are building the full user interface of the generator you rebuilt in S1–S6, as a
Databricks App. S1–S6 are frozen; touch no file of those slices.

Read, in this order, and nothing else first:

1. `UI_SPEC.md` v2 — target decision, doctrine, every screen, the API contract.
2. `BACKEND_SPEC.md` — routes, state model, stages, start-up, App configuration.
3. `ACCEPTANCE/S7_ui.md` — the checks.

Run `node --version` first and take UI_SPEC §1.2's path (A) or (B) accordingly.

Build order:

1. The backend: every route of BACKEND_SPEC §1 against S1–S6, until S7 Block A (the curl
   checks) is green.
2. The frontend shell, the Dashboard, Run modes Card B (Step 1, Step 1.5 FAQ, Step 2, the
   chooser, the cost modal, progress), Feed detail Overview and Rules tabs, the framework
   artefacts panel, the metadata sheet panel.
3. Deploy as a Databricks App: two Volume resources, the force-mock switch, the port from
   the environment. Open the URL.
4. Every remaining screen, tab, modal and route — the LATER items, same fidelity.

Full fidelity. The scope is not reducible: every screen, control and route in UI_SPEC exists.
A screen whose data source does not exist yet is built with its documented empty or hidden
state, never dropped. Every generator message reaches the screen unchanged.

Stop when every DEMO-DAY check in S7 is green and the App URL loads. Report: node
availability and the path taken; each UI_SPEC §0.3 drift item met; any route you could not
back and what it answers instead; any check that did not hold, with the exact on-screen text.
