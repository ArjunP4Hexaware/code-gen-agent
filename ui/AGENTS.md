# ui/ — App UI rules

Loaded when working under `ui/`; the repo-wide rules are in the root `AGENTS.md`; the
App's identity, grants, model cost and learned labels are in `docs/PROCEDURES.md` ("The
App", moved there from AGENTS.md on 2026-11-10).

## The App's UI

- The App opens on the guided run page, "Generate a pipeline" (`/`; the old `/modes`
  redirects there; Results is `/results`): a step strip (Choose
  documents → Check the settings → Answer questions → Get the results), a Documents
  card (drop zone + "Choose documents…", STTM / FRD / VDD rows), a Settings card
  (Advanced folded), the run card with the questions asked BEFORE generating, then
  "View results" (Results). The App's API wants an OAuth token, not a PAT.
- Deprecated, no UI consumer (kept for API compatibility; nothing new may depend on
  them): `/api/replay/*`, `/api/demo/live-runs`, `/api/demo/input-documents`.
- **Look:** ACFC's own design tokens (its public style guide: Brand / Text and Accents /
  UI colours, Open Sans bundled via `@fontsource`) in the guided style of the STTM
  agent's App (Soham, 2026-10-29: white header, light sidebar, white ROUNDED cards with
  a soft shadow, plain words, technical detail folded), defined ONCE in
  `ui/frontend/src/styles.css` `:root`. No hard-coded colour anywhere else (tints are
  `color-mix` of a token); status colours are reserved for verdicts / checks; every
  text pair WCAG AA. **Two themes, DARK the default** (post162, Raj via Soham,
  2026-11-02): `:root` = light, `:root[data-theme="dark"]` = dark (ACFC navy surfaces,
  ACFC light-blue accent, ACFC status colours lifted), set before first paint by
  `public/theme-init.js` (a same-origin blocking script - never inline: the CSP), switched
  by the header toggle (`src/theme.ts`, key `codegen.theme.v1`). A new colour token needs
  a value in BOTH blocks; a filled token needs its `--on-*` text token;
  `src/themeContrast.test.ts` checks every pair in both themes. No ACFC logo or name in the repo: the header's top-left logo is
  read at runtime from the state root, `branding/logo.<png|svg|jpg|webp>` (`GET
  /api/branding`, post144); without one the header is the wordmark alone.
  The spec: the UX skill Part 1 "Design pillars" and §4.1. Every page (post157): a
  loading card until its first answer (never "0 chosen" / "No results yet" before the
  App knows), no sideways scroll at 390 px, targets of at least 24 px (WCAG 2.2 2.5.8),
  ONE `h1` (rendered report headings are demoted), the logo is decoration (no tab
  stop). Check with Playwright against a local mock App before claiming a UI fix.
- **What the App says about providers:** the header badge = the provider the NEXT run
  uses (`/api/feeds` `provider`); a banner's LIVE / MOCK RUN word = the provider that
  answered the served run (`run_provider`). The served `mode` drives behaviour only —
  never show it as the provider (it read MOCK after every deploy of a live App).
- Choose documents: a pick applies at once (download, classify, pair); Cancel restores
  the selection the dialog opened on (`/api/demo/choosing*`), Done keeps it.
- **Cancel run is a choice, not a failure** (post164, Soham): `POST /api/demo/cancel`
  stops a run paused on its questions (layout / pairing / before-generate dialog) or drops
  the questions a stopped run left (needs_answers, a done run with blocking lines); the
  page goes back to idle with no error card (`RunCancelled`), nothing recorded, the run's
  folder kept. "Clear past runs" resets the run card in EVERY finished state too.
