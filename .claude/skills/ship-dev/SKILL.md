---
name: ship-dev
description: Push a green, committed version and deploy the dev App codegen-agent, then prove it (health names the version, Playwright smoke). Run when Soham says to push / deploy dev, or after a version's full suites (both venvs) and 12-pair check are green and read.
disable-model-invocation: true
---

# /ship-dev

1. Preconditions - stop and say which is missing:
   - the version is committed; `src/` changes carry a bump (`scripts/bump_version.py`);
   - BOTH full suites ran on this committed tree and you READ the result (green);
   - a change that can move generated output has its 12-pair check read (`/pair-check`).
2. `git fetch` and confirm nothing new arrived on `origin/feature/multi-table` (rebase
   if it did, then re-run the suites), then `git push origin feature/multi-table`.
   Never force-push.
3. `tools/check/ship.sh dev` (it checks the App is idle, deploys with one retry,
   restores the last good commit if the deploy fails, waits for /api/health to name the
   version, runs the smoke test). The OAuth profile must exist (RESTART.md recipe);
   if `ship.sh` says the profile is missing, ask Soham to log in - never route around it.
4. Report in two lines: version + short sha deployed, health / smoke result. A FAILED
   line means stop and ask (the script already restored the last good commit).

The rules behind each step: `docs/PROCEDURES.md` ("Pushing", "Deploying", "The App").
