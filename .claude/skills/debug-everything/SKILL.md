---
name: debug-everything
description: Full-repo health sweep for the code-gen-agent repo — run the offline test suite, ruff lint, a dry-run generate-all sanity pass, a whole-tree bug-hunting code review, and a live browser check of the demo UI via Claude-in-Chrome, then report one consolidated verdict. Use when the user says "debug everything", "check everything", "is the repo broken", "full health check", or wants the entire codebase (not a diff) checked end to end. Pass `quick` to skip the code-review and browser steps; `no-browser` to skip just the browser step; an effort level (low/medium/high/max) controls review depth (default high).
---

# debug-everything — full-repo health sweep

Run the five checks below **in order**, keep going after a failure (later
steps still yield signal), and finish with the consolidated report. Steps
1–3 are cheap and deterministic; steps 4 and 5 are the expensive ones and
the only steps arguments can tune. Step 4 runs in the background — start
it, run step 5 while it works, then fold its findings into the report.

**Hard rules for every step:** no external network — localhost traffic
for step 5 is fine, but no credentials, no live Layer-2 runs, nothing
that wakes a Databricks warehouse or calls the Anthropic/Graph APIs. Everything here must work with zero secrets.
Never set `ANTHROPIC_API_KEY`; the mock provider is the point.

Use the repo venv interpreter for every Python command:
`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on POSIX
(fall back to `python` only if no `.venv` exists, and say so in the
report). Run steps 1 and 2 in parallel — they are independent.

## Step 1 — Offline test suite

```
<venv-python> -m pytest -q
```

- Expect passes plus a block of **skips** — fixture-driven tests skip by
  design while `fixtures/` is absent (see CLAUDE.md "Fixtures & data
  rules"), and demo-UI/SharePoint tests skip without the `[ui]` extra.
  Skips with those reasons are healthy, not failures.
- Any **failure or error** is a red result. Capture the failing test ids
  and the first assertion message for the report — don't dump full
  tracebacks into the summary.

## Step 2 — Lint

```
<venv-python> -m ruff check src/ tests/
```

Must be completely clean. Any finding is a red result (this repo's bar is
zero ruff findings, including in generated output).

## Step 3 — Dry-run generation sanity pass

```
<venv-python> -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests
```

- `config.contracts.pairs` has been `[]` since 2026-08-22, and
  `generate-all` **refuses loudly on an empty pair list — that refusal is
  an expected SKIP**, not a failure. Report it as "skipped: no contract
  pairs configured (expected since fixtures removal)".
- If pairs ARE configured (fixtures locally restored), expect every feed
  to end **PASS_WITH_FLAGS**. Report each feed's gate verdict; a FAIL or
  a crash is red. `PASS_WITH_FLAGS` is the healthy outcome, not a warning.
- Never drop `--dry-run` or `--skip-tests` in this skill: dropping them
  needs a JVM and, with a key present, could trigger live Layer-2 calls.

## Step 4 — Whole-tree code review (skip if args contain `quick`)

Invoke the `code-review` skill via the Skill tool with a **path target**
so it reviews the code itself, not a diff:

- args: `<effort> src/` where `<effort>` is the level passed to this
  skill, default `high`.
- Do NOT use `ultra` from here — it is user-triggered and billed; if the
  user wants it, tell them to type `/code-review ultra <base>` themselves.

Carry the review's findings (or "none") into the report.

## Step 5 — Browser check of the demo UI (skip if args contain `quick` or `no-browser`)

Drive the demo UI in a real browser via Claude-in-Chrome while step 4's
review runs in the background. **Mock mode only** — never click anything
on the Live / "Generate a Pipeline" card, never confirm a cost dialog,
never trigger SharePoint publish. Read-only clicking through pages is the
whole job.

1. **Preflight.** `<venv-python> -c "import fastapi, uvicorn"` — if that
   fails, report this step as ⚠️ skipped with remedy
   `pip install -e ".[ui]"` and move on. Also note whether
   `ui/frontend/dist/` exists (single-port mode needs a build).
2. **Launch** (background Bash/PowerShell, `run_in_background`):
   - If `ui/frontend/dist/` exists:
     `<venv-python> -m uvicorn ui.backend.main:app --port 8571` and use
     `http://localhost:8571`.
   - Otherwise dev mode: same uvicorn command with env
     `CODEGEN_UI_DEV=1`, plus `npm run dev` in `ui/frontend/`, and use
     `http://localhost:5173` (run `npm install` first only if
     `node_modules/` is absent).
   - Wait for readiness by polling `GET /api/feeds` (curl/Invoke-WebRequest),
     not by sleeping blind. With `contracts.pairs` empty the app comes up
     with empty state and reports the problem via `/api/feeds` — that is
     the documented behavior (ui/README.md), an expected-skip condition,
     NOT a failure.
3. **Browser session.** Invoke the `claude-in-chrome` skill first, then
   load every MCP tool needed in ONE ToolSearch call: tabs_context_mcp,
   tabs_create_mcp, navigate, computer, read_page,
   read_console_messages, read_network_requests, tabs_close_mcp. Get tab
   context, open a NEW tab on the app URL.
4. **Checks**, on each of: the dashboard `/`, the Run-modes page, and the
   demo tour `/demo`:
   - the page renders real content (not a blank body or an unhandled
     error boundary); with no pairs configured, an explicit empty/error
     state is the *correct* render;
   - `read_console_messages` shows no errors (warnings are reportable
     but not red);
   - `read_network_requests` shows no failed requests — expected
     non-2xx responses (the documented 409s, empty-state payloads, 503
     from an unconfigured SharePoint panel) are healthy; anything else
     4xx/5xx or a hung request is red.
5. **Teardown, always** (also after a mid-step failure): close the tab
   you opened, then stop the background server process(es).
6. Report per-page verdicts plus any console/network findings.

## Final report

End with one consolidated summary the user can read in ten seconds:

1. A short table: step | result (✅ pass / ⚠️ expected-skip / ❌ fail)
   | one-line detail.
2. Then, only for red rows: what failed and the most likely place to
   look, as clickable `file:line` references.
3. One closing line: either "repo is healthy" or the single most
   important thing to fix first.
