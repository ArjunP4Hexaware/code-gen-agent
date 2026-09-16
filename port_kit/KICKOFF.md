# KICKOFF — paste this as the first message

You are rebuilding a deterministic code generator from a code-free kit in this folder. Start with slice S1 only.

Read, in this order, and nothing else first:

1. `SKILL.md` (the process; one slice per session, passed slices are frozen forever).
2. `ACCEPTANCE/S1.md` (the goal, three cases, exact expected outputs with checksums).
3. `ACCEPTANCE/INPUTS.md` (the synthetic input pairs; rebuild the workbook sheets cell for cell).
4. `SPEC.md` sections 0, 1 and 2 only. Do not read sections 3–6 yet; do not open the client documents yet.

Then: materialize the S1 case inputs, implement the readers and the stage DDL text file per the SPEC, generate case 1, mask the sha256 spans as the pass criterion says, and diff against the expected block. If a line differs, re-read the SPEC rule it names; if the SPEC is ambiguous, amend the SPEC (never the expected output). Every assumption must quote the FRD field or STTM cell it rests on.

Report when S1 case 1 diffs clean.
