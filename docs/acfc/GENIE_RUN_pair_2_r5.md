# Genie Code — pair_2 (SD) round 5 (D1 Git folder)
In order; stop where told. NEVER modify `src/codegen/**`, never hand-edit or split a contract,
never add an answer beyond step 3's one. Results go to `/tmp/r5/push/` (RUN.md is one of them).
1. **Code.** `git fetch origin` · `git checkout feature/multi-table` · `git pull --ff-only origin
   feature/multi-table`. Record `python -m codegen.cli doctor`'s `build …` line and `git rev-parse
   --short HEAD`; STOP unless the build line names that SHA `(git)`; version >= 0.5.8.post29.
2. **Fingerprint + content gate** (hashes + counts only). `<STTM>` = the FILLED workbook, never
   `*_blank_version*`. `python scripts/doc_fingerprint.py <STTM> <FRD> --json >
   /tmp/r5/push/fingerprint_d1.json`; its text form (no `--json`) into RUN.md. Gate on CONTENT,
   never whole-file sha256 (a re-save or re-zip changes the bytes, not the content):
   `body_hash` of sheet `name#01292dd6fa7b` starts `f5648cd5d589e163`, `name#ef35f6a78545`
   `0bb226b3c86fbf04`, `name#a60e2e099a94` `706a9af9a734deca`; the docx `text_hash` starts
   `311c437cd18ebdd0`. Any differs → RUN.md names which, STOP. Whole-file sha256 + size of both
   go in RUN.md as a record only (they differed in the first r5 attempt; never a stop).
   Finding to record, do not investigate: `*_blank_version*` has other mapping-sheet names, a
   uniform 18-column header and no merged ranges; all five of its sheet-name hashes equal the
   repo's synthetic `fixtures/acfc_shapes/sttm/pair_2_family_b.xlsx` → pipeline-generated (the
   STTM agent or a normalisation export), not BSA-authored.
3. **Run the CLI clean.** `/tmp/r5/answers.yaml` = ONE entry, `gaps:` →
   `"feeds[1].file_name_patterns": {value: <the FILE_DETAILS file feeds 0 and 2 do not take>}`.
   env: `PYTHONUTF8=1 CODEGEN_FORCE_MOCK_LAYOUT=1 CODEGEN_FORCE_MOCK_PROVIDER=1
   CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
   CODEGEN_STORAGE_STATE=local:/tmp/r5/state CODEGEN_STORAGE_OUTPUTS=local:/tmp/r5/out`
   - `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete
     --frd-contract-out /tmp/r5/frd.json --answers /tmp/r5/answers.yaml` — exit 3 → record
     every QUESTION / UNRESOLVED key (text up to ` — `) in RUN.md, go to step 4, skip step 5.
   - `python -m codegen.cli extract-sttm --workbook <STTM> --frd-contract /tmp/r5/frd.json
     --out /tmp/r5/sttm.json --answers /tmp/r5/answers.yaml`
   - `python -m codegen.cli generate --frd-contract /tmp/r5/frd.json --sttm-contract
     /tmp/r5/sttm.json --output-mode framework --profile acfc_prx --iig-template iig_v2
     --skip-tests --dry-run` — RUN.md: each command (`<STTM>` / `<FRD>`), exit, first line, verdicts.
4. **Golden, rebuilt on this SHA.** `python tools/build_goldens.py --out /tmp/r5/goldens`; `<G>` =
   `/tmp/r5/goldens/pair_2_iig_golden.xlsx`. Its pair_2 `dedup … -> …` lines into RUN.md (GROUP_IDs
   180251–180256 may stay); `python tools/iig_diff.py --golden <G> --golden-structure --out /tmp/r5/push`.
5. **Diff + scrubbed evidence.** `python tools/iig_diff.py --golden <G> --agent <the 3 *_IIG.xlsx,
   not *_REVIEW> --out /tmp/r5/diff --export-scrubbed /tmp/r5/push`; never `--pair-mode`.
   score.json's `totals` + per-sheet `rows` / `counts` / `score` → `/tmp/r5/push/score_totals.json`.
   In RUN.md, right under the dedup lines, one line per sheet from score.json `rows`:
   `<sheet>: agent <agent> rows · golden <golden> rows (deduped) · paired <paired>` — a row-count gap.
6. **Scrub, commit, push.** `python scripts/scrub_check.py /tmp/r5/push` must print `clean` (else
   STOP; report class counts only). `git checkout -B acfc-results origin/acfc-results`; copy
   `/tmp/r5/push/*` to `codegen-outputs/iig_validation/round5/pair_2/`; `git add` those files by
   name; `git commit -m "round5 pair_2"`; `git push origin acfc-results`; `git checkout
   feature/multi-table`. Never commit diff.xlsx, score.json, routing.csv, a golden, an xlsx,
   the answers file or anything under /tmp/r5/out.
