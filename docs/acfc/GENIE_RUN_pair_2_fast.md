# Genie Code — pair_2 (SD) round 4, FAST (D1 Git folder)
In order; stop where told. NEVER modify `src/codegen/**` (extractor, parser, layout).
Max two attempts per step. A second failure of the same step → write round4/NEEDS_HOME.md
(command, exit code, first FAIL/QUESTION line, values redacted), push it per step 6, STOP.

1. **Code.** `git fetch origin` · `git checkout feature/multi-table` · `git pull --ff-only
   origin feature/multi-table`. Record `python -m codegen.cli doctor`'s `build …` line and
   `git rev-parse --short HEAD`. STOP unless the build line names that SHA `(git)`, or (no
   .git) `python scripts/stamp_build.py --which <src tree>` lists it; version >= 0.5.8.post28.
3. **Run the CLI like the harness** on the pair_2 STTM + FRD of the pair folder.
   - `cp codegen-state/answers/pair_2.yaml /tmp/r4/answers.yaml`; fill THAT copy (the
     FILE_DETAILS file feeds 0 and 2 do not take); STOP while it contains `<FILL`.
   - env: `PYTHONUTF8=1 CODEGEN_FORCE_MOCK_LAYOUT=1 CODEGEN_FORCE_MOCK_PROVIDER=1
     CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
     CODEGEN_STORAGE_STATE=local:/tmp/r4/state CODEGEN_STORAGE_OUTPUTS=local:/tmp/r4/out`
   - `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete
     --frd-contract-out /tmp/r4/frd.json --answers /tmp/r4/answers.yaml`
   - `python -m codegen.cli extract-sttm --workbook <STTM> --frd-contract /tmp/r4/frd.json
     --out /tmp/r4/sttm.json --answers /tmp/r4/answers.yaml`
   - `python -m codegen.cli generate --frd-contract /tmp/r4/frd.json --sttm-contract
     /tmp/r4/sttm.json --output-mode framework --profile acfc_prx --iig-template iig_v2
     --skip-tests --dry-run`
   - `find /tmp/r4/out -name '*_IIG.xlsx'` lists 3 and `/tmp/r4/out/CODEGEN_BUILD.json`
     exists, else → NEEDS_HOME.md. RUN.md: each command (`<STTM>` / `<FRD>`, never the real
     file names), exit code, first line. Expected: exits 0 / 0 / 0, 3 × PASS_WITH_FLAGS.
4. **Diff, key-paired.** `python tools/iig_diff.py --golden <the pair_2 golden
   tools/build_goldens.py builds from docs/acfc/iig_goldens*/ for GROUP_IDs 180251–180256,
   rebuilt on this SHA> --agent <the 3 *_IIG.xlsx, not *_REVIEW> --out /tmp/r4/diff`; never
   pass `--pair-mode`. Header must print AGENT BUILD = step 1's SHA + the IGNORED set;
   "unscored" = STOP, report it.
6. **Scrub, commit, push.** Write ONLY RUN.md (steps 1, 3, 4) and score_totals.json
   (score.json `totals` + each sheet's `rows` / `counts` / `score`; no keys, no paths) to
   `codegen-outputs/iig_validation/round4/pair_2/`; never diff.xlsx, score.json,
   routing.csv, a golden, an agent xlsx or the answers file. `python scripts/scrub_check.py
   codegen-outputs/iig_validation/round4` prints `clean`. `git checkout -b
   acfc-iig-validation-r4`, `git add` the two files by name, commit, `git push -u origin
   acfc-iig-validation-r4`.
