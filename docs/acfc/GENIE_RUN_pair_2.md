# Genie Code — pair_2 (SD) validation run, round 4 (D1 Git folder)

Do these in order. Stop where told. NEVER modify extractor, parser or layout code
(`src/codegen/**`): if the run needs a code change, write the symptom (command,
exit code, first FAIL / QUESTION line, values redacted) to
`codegen-outputs/iig_validation/round4/NEEDS_HOME.md`, commit + push it (step 6), STOP.

1. **Code.** `git config core.hooksPath scripts/git-hooks` · `git fetch origin` ·
   `git checkout feature/multi-table` · `git pull --ff-only origin feature/multi-table`.
   Run `python -m codegen.cli doctor`; record its `build …` line and
   `git rev-parse --short HEAD`. STOP unless the build line names that SHA `(git)`,
   or (no .git) `python scripts/stamp_build.py --which <src tree>` lists it. The
   version must be 0.5.8.post28 or later.
2. **App** (only if `POST /api/demo/workbook` still answers 409): `DELETE /api/demo/workbook`
   (the chooser's Clear), choose again. Redeployed, `GET /api/health/facts` shows step 1's build.
3. **Run the CLI like the harness**, on the pair_2 STTM + FRD of the pair folder.
   - Fill `codegen-state/answers/pair_2.yaml` (the FILE_DETAILS file feeds 0 and 2 do not
     take); refuse to continue while it contains `<FILL`; never commit it filled.
   - env: `PYTHONUTF8=1 CODEGEN_FORCE_MOCK_LAYOUT=1 CODEGEN_FORCE_MOCK_PROVIDER=1
     CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
     CODEGEN_STORAGE_STATE=local:/tmp/r4/state CODEGEN_STORAGE_OUTPUTS=local:/tmp/r4/out`
   - `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete
     --frd-contract-out /tmp/r4/frd.json --answers codegen-state/answers/pair_2.yaml`
   - `python -m codegen.cli extract-sttm --workbook <STTM> --frd-contract /tmp/r4/frd.json
     --out /tmp/r4/sttm.json --answers codegen-state/answers/pair_2.yaml`
   - `python -m codegen.cli generate --frd-contract /tmp/r4/frd.json --sttm-contract
     /tmp/r4/sttm.json --output-mode framework --profile acfc_prx --iig-template iig_v2
     --skip-tests --dry-run`
   Record each command, exit code and first line (it names profile + IIG template). Home's
   mock run: exits 0 / 0 / 0, 3 feeds PASS_WITH_FLAGS; anything else → NEEDS_HOME.md.
4. **Diff, key-paired.** Use the pair_2 golden that `tools/build_goldens.py` builds from
   `docs/acfc/iig_goldens*/` for GROUP_IDs 180251–180256 (rebuild it on this SHA).
   `python tools/iig_diff.py --golden <pair_2 golden> --agent <the 3 */*_IIG.xlsx under
   /tmp/r4/out, not *_REVIEW> --out /tmp/r4/diff`. The default key mode is the
   validation score; never pass `--pair-mode`. The header must print AGENT BUILD =
   step 1's SHA and the IGNORED set. "unscored" = STOP and report it.
5. **Explain every cell.**
   - `MISMATCHES.md`: one row per mismatch / missing / extra cell in score.json:
     `sheet | column | golden [scrubbed] | agent | class | evidence`. Classes: A = no
     FRD/STTM states it (the engineer's tacit knowledge) · B = stated but the parser
     missed it (cite the cell) · C = conventions profile key wrong or missing (cite the
     key) · D = template / overlay constant (cite it) · E = the golden itself looks
     odd: flag it, don't chase it.
   - `WALKTHROUGH_pair_2.md`: every populated column of the agent IIG → its source
     (FRD section/field · STTM sheet+cell · profile key · template constant ·
     "blank by design: engineer-assigned ID"). Read each feed's `*_IIG_REVIEW.xlsx`
     (cell provenance). Order: ADLS_DELTA_INGESTION_DETAILS, ALL_FILES_STATIC_INFORMATION
     / FILE_ADLS_INGESTION_DETAILS, then the rest. End with "Known gaps" (A + E items)
     and one question per gap.
6. **Scrub, commit, push.** Write to `codegen-outputs/iig_validation/round4/pair_2/`:
   RUN.md (steps 1, 3 and 4 as recorded), MISMATCHES.md, WALKTHROUGH_pair_2.md,
   score_totals.json (score.json's `totals`, plus each sheet's `rows` / `counts` /
   `score`; no keys, no paths) and SELF_CHECK.md (COUNTS only, never a term). Golden
   values: real IDs → `SYN-*`; no vendor, table or file names beyond those already in
   the repo. Never commit diff.xlsx, score.json, routing.csv, a golden, an agent xlsx
   or the filled answers file. `python scripts/scrub_check.py
   codegen-outputs/iig_validation/round4` must print `clean`. Then `git checkout -b
   acfc-iig-validation-r4`, `git add` the files by name, commit, and `git push -u
   origin acfc-iig-validation-r4`.
