# Genie Code — pair_2 (SD) round 6 (D1 Git folder)
Run exactly these steps. No other commands, no edits under `src/`, no answers file, never
choose an input.
1. `git fetch origin` · `git checkout feature/multi-table` · `git pull --ff-only origin feature/multi-table`.
   `python -m codegen.cli doctor` — its `build …` line must name the pulled SHA `(git)` and
   version >= 0.5.8.post32, else STOP.
2. `codegen-state/fingerprint.key` and `codegen-state/round_inputs/pair_2.yaml` must both exist
   (gitignored; Soham places them — never print, copy or commit either), else STOP.
3. `python scripts/run_round.py --round 6 --inputs codegen-state/round_inputs/pair_2.yaml
   --golden-dir docs/acfc/iig_goldens --out /tmp/r6/push` — note its exit code.
4. `git checkout -B acfc-results origin/acfc-results`; copy the files of `/tmp/r6/push/` (not
   `/tmp/r6/push.work/`) to `codegen-outputs/iig_validation/round6/pair_2/` — on exit 2 or 3
   `RUN.md` ONLY; `git add` each copied file by name; `git commit -m "round6 pair_2"`;
   `git push origin acfc-results`; `git checkout feature/multi-table`. Exit 2 or 3 → STOP here.
