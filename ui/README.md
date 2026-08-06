# Demo UI — React + FastAPI

A thin front door onto the generator: it invokes the same in-process pipeline
the CLI runs (`resolve → compile rules → Layer 2 → render → gate → report`)
and renders its structured artifacts. No generation logic lives in the UI.

## Run (two terminals, from the repo root)

```bash
# 1. Backend — generates all feeds on startup (dry-run, tests skipped)
.venv/bin/pip install -e ".[ui]"          # first time only
.venv/bin/uvicorn ui.backend.main:app --reload --port 8571

# 2. Frontend
cd ui/frontend
npm install                                # first time only
npm run dev                                # http://localhost:5173
```

## What it shows

- **Dashboard** — one card per resolved feed with the three-state gate
  verdict (PASS / PASS WITH FLAGS / FAIL), rule-classification breakdown,
  and pending Layer-2 reviews. "Generate all feeds" re-runs the pipeline.
- **Feed detail**
  - *Overview* — gate checks, open flags, contract provenance (name +
    sha256), target tables, load semantics.
  - *Rules* — every FRD validation rule with its deterministic
    classification and the grounding substring that fired it.
  - *Layer-2 review* — candidates from `out/<feed>/candidates/`, with
    approve / reject. Decisions persist to `ui/backend/state/decisions.json`
    (gitignored) and are a review record only — **merging an approved
    candidate into generated code remains a manual v2 step.**
  - *Notebook* — the assembled `out/<feed>/<feed>.ipynb` rendered
    cell-by-cell (markdown as prose, code highlighted) — the single
    runnable deliverable per feed.

    ![Notebook tab walkthrough](../docs/media/notebook_tab_walkthrough.gif)
  - *Generated code* — file tree + syntax-highlighted viewer over
    `out/<feed>/`.
  - *Report* — the rendered markdown generation report from `reports/`.
- **Demo mode** (`/demo`) — a six-step guided tour for live demos
  (what it is → contracts → Layer 1 → Layer 2 → gate → the notebook
  deliverable). Every number and quote on screen is real output from the
  latest run; navigate with the buttons or ← / → keys. The final step
  renders the generated notebook **inline** — pick any feed's `.ipynb`
  and scroll it without leaving the tour.

  ![Demo mode walkthrough](../docs/media/demo_mode_walkthrough.gif)

## Notes

- The backend always runs the mock Layer-2 provider and skips generated
  tests (`dry_run=True`, `skip_tests=True` in `POST /api/generate`) — the
  full Spark gate stays a CLI concern.
- The Vite dev server proxies `/api` to `localhost:8571`
  (`ui/frontend/vite.config.ts`).
- `playwright` in devDependencies is only used for ad-hoc screenshot
  verification; the app itself doesn't need it.
