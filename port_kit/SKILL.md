---
name: codegen-option-b-port
description: Rebuild the CodeGen agent's Option B outputs (stage and standard deployment DDL text files, the seven-tab IIG config-rows workbook, the flags report and the batch summary) from SPEC.md and the ACCEPTANCE cases, one frozen slice per session, verifying each slice against exact expected outputs.
---

# What this skill is for

You are rebuilding a deterministic generator from a code-free specification. The kit is these
files, all in this folder:

| File | Role |
|---|---|
| `SKILL.md` | this process (no domain rules live here) |
| `KICKOFF.md` | the first message that starts slice S1 |
| `SPEC.md` | every rule, as decision tables and filled examples; the only source of domain truth |
| `ACCEPTANCE/INPUTS.md` | the synthetic input pairs every case uses |
| `ACCEPTANCE/S1.md` … `S6.md` | one slice each: goal, cases, exact expected outputs with checksums |
| `UI_SPEC.md`, `BACKEND_SPEC.md`, `ACCEPTANCE/S7_ui.md`, `DEMO_SCRIPT.md`, `KICKOFF_UI.md` | slice S7: the full UI as a Databricks App — screens, API contract, backend, checks, demo path; `KICKOFF_UI.md` starts it |
| `MANIFEST.md` | file list, line counts, sha256 of the kit |

Real client documents (the ten FRD/STTM pairs, the client DDL goldens, the client IIG
workbook, the naming and coding standards) are reference material you read; never modify them.

# Build order and the frozen-slice rule

Build S1 → S2 → S3 → S4 → S5 → S6, one slice per session. A slice whose cases all pass is
frozen: its files are read-only forever. Later slices add files; they never edit frozen ones.
If a later slice cannot pass without touching a frozen slice, stop and report the conflict;
do not unfreeze on your own.

# The loop for one slice

1. Read the slice file `ACCEPTANCE/S<n>.md` completely.
2. Read ONLY the SPEC sections the slice file names, plus `ACCEPTANCE/INPUTS.md`.
3. Materialize the case inputs exactly as given (cell for cell, whitespace included).
4. Implement the slice.
5. Run every case; diff your output against the expected block using the slice's pass
   criterion (byte-exact after sha masking for `.txt`; cell-exact for tab dumps; line-exact
   for flags and summaries). Verify the block checksum you are diffing against.
6. Iterate until every case is exact. When the SPEC is ambiguous for a differing line, amend
   the SPEC (add the rule or example, citing the case) — never the expected output, never a
   special case for the acceptance inputs.
7. Freeze the slice and write a three-line checkpoint: slice id and pass count; the SPEC
   sections you amended (or "none"); what the next session should start with.

# Assumption and conflict rule

Every assumption, conflict or confirm item you raise must quote the exact FRD field or STTM
cell it rests on. Nothing is invented: framework-assigned identifiers stay blank and flagged,
unknown facts stay blank and flagged, disagreements between the FRD and the STTM stop the pair
with a message naming both values.

# Environment notes

- Outputs are plain files in the workspace: two `.txt` files and one `.xlsx` per feed, one
  report per feed, one summary per batch. Write `.xlsx` with openpyxl; compare cells, not
  bytes.
- No internet. No model calls are needed for any acceptance case (Layer 2 runs its
  deterministic mock; see SPEC 5.2).
- Never modify the client reference files; read them, transcribe from them into your
  configuration where the SPEC says so, and cite them.
- Keep every knob in one configuration file (SPEC 0.1). No numeric or naming literal belongs in
  logic.
