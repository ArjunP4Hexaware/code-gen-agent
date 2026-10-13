# Genie Code — pair_2 (SD) round 7 (D1 Git folder)
Run exactly these steps. No other commands, no edits under `src/`, no answers file, never
choose an input.
1. `git fetch origin` · `git checkout feature/multi-table` · `git pull --ff-only origin feature/multi-table`.
   `python -m codegen.cli doctor` — its `build …` line must name the pulled SHA `(git)` and
   version >= 0.5.8.post33, else STOP.
2. `codegen-state/fingerprint.key` and `codegen-state/round_inputs/pair_2.yaml` must both exist
   (gitignored; Soham places them — never print, copy or commit either), else STOP.
   `codegen-state/env_tokens.yaml` is optional (Soham's; same rule) — never create it.
3. `python scripts/run_round.py --round 7 --inputs codegen-state/round_inputs/pair_2.yaml
   --golden-dir docs/acfc/iig_goldens --out /tmp/r7/push --provider live` — note its exit code.
   (2026-10-13, >= 0.5.8.post38: the provider is ONE explicit switch; run_round.py sets
   `CODEGEN_PROVIDER` from `--provider` for every stage, passes no `--dry-run` and clears every
   `CODEGEN_FORCE_MOCK_*`. RUN.md's Build section must say ``provider=`live` ``, and each stage's
   first line must contain `provider=live (CODEGEN_PROVIDER)`; a `WARNING provider=live
   overridden by --dry-run → mock` or `provider=mock` first line = STOP: the run is not live.)
4. `git checkout -B acfc-results origin/acfc-results`; copy the files of `/tmp/r7/push/` (not
   `/tmp/r7/push.work/`) to `codegen-outputs/iig_validation/round7/pair_2/` — on exit 2 or 3
   `RUN.md` ONLY; `git add` each copied file by name; `git commit -m "round7 pair_2"`;
   `git push origin acfc-results`; `git checkout feature/multi-table`. Exit 2 or 3 → STOP here.
