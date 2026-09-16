# KICKOFF_UI — paste this as the first message for slice S7

You are building the demo UI for the generator you rebuilt in S1–S6. Prerequisite: S1, S2 and
S3 are frozen and pass; touch no file of those slices.

Read, in this order, and nothing else first:

1. `UI_SPEC.md` — all nine sections. Its target decision is fixed: one Streamlit source file
   plus the Databricks Apps configuration file; the generator package loaded in-process;
   inputs from the inputs Volume, every run written to the outputs Volume.
2. `ACCEPTANCE/S7_ui.md` — the fifteen manual checks and their setup.

Build the DEMO scope only (UI_SPEC §2.1–§2.4, §3, §4, §5, §7, §9). Everything in §8 is after
the demo. Where the generator exposes no progress hook, use the fallback §2.3 states; never
modify a frozen slice to add one.

Materialize the synthetic inputs on the inputs Volume as S7 describes, deploy as a Databricks
App with the two Volume resources and the force-mock switch, then run the checks in order.

Stop when S7 checks 1–8 are green and the app URL loads. Report the run id of check 6, any
check that did not hold with the exact on-screen text, and any generator message shown that
UI_SPEC §7 does not list.
