// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetHealthLineCache } from "../components/ErrorCard";
import { ModesPage } from "./ModesPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post67: the live-run confirm dialog shows ranges from the App's record of
   the last live runs (status.live_history) — never the old "~3 calls · ≈ $0.10
   · ~20s" constant. Synthetic backend: a fetch stub, a live FMAPI transport,
   an STTM + FRD chosen. */

const HISTORY = {
  profile: "acfc_prx", runs: 6, min_runs: 3, stopped: null,
  wall_seconds: { low: 95, high: 140 }, model_seconds: { low: 41, high: 68 },
  calls: { low: 3, high: 5 }, cost_usd: { low: 0.1, high: 0.15 }, cost_runs: 6,
  cost_basis: "list", price_source: "anthropic list price, 2026-10-06", billed_in_dbus: true,
};
const EMPTY = {
  profile: "acfc_prx", runs: 0, min_runs: 3, stopped: null, wall_seconds: null, model_seconds: null, calls: null,
  cost_usd: null, cost_runs: 0, cost_basis: null, price_source: null, billed_in_dbus: false,
};

let liveHistory: unknown = HISTORY;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

const ROUTES: Record<string, () => Response> = {
  "GET /api/demo/status": () => json(200, {
    state: "idle", stages: [], error: null, last_run_label: null, layout_refresh: false,
    selection: { sttm: "STTM_syn_feed.xlsx", frd: "FRD_syn_feed.docx", vdd: null },
    frd_name: "FRD_syn_feed.docx", output_parts: ["framework"],
    live_history: liveHistory,
  }),
  "GET /api/demo/live-available": () => json(200, {
    available: true, reason: "", transport: {
      kind: "databricks_fmapi", label: "Claude Opus 5.5 (databricks-claude-opus-5-5)",
      endpoint: "databricks-claude-opus-5-5", model: "claude-opus-5-5",
      detected_by: "test stub", runtime: "local", configured: "databricks_fmapi",
      overridden: false } }),
  "GET /api/demo/output-options": () => json(200, ["notebook", "framework"]),
  "GET /api/demo/workbooks": () => json(200, { workbooks: [] }),
  "GET /api/health/facts": () => json(200, { health_line: "version 0.0.0" }),
};

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  resetHealthLineCache();
  liveHistory = HISTORY;
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${String(url).split("?")[0]}`;
    return (ROUTES[key] ?? (() => json(404, { detail: "not found" })))();
  }));
  vi.spyOn(console, "error").mockImplementation(() => {});
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function settle() {
  for (let i = 0; i < 5; i++) await act(async () => { await Promise.resolve(); });
}

async function openConfirm(): Promise<HTMLElement> {
  await act(async () => {
    root.render(<MemoryRouter><ModesPage onFeedsChanged={() => {}} /></MemoryRouter>);
  });
  await settle();
  const generate = [...host.querySelectorAll<HTMLButtonElement>("button")]
    .find((b) => b.textContent?.trim() === "Generate");
  if (!generate) throw new Error(`no Generate button in: ${host.textContent}`);
  expect(generate.disabled).toBe(false);
  await act(async () => { generate.click(); });
  await settle();
  const modal = [...host.querySelectorAll<HTMLElement>(".modal")]
    .find((m) => m.textContent?.includes("Confirm — run live"));
  if (!modal) throw new Error("the confirm dialog did not open");
  return modal;
}

describe("the live-run confirm dialog", () => {
  it("shows the measured ranges, wall-clock first", async () => {
    const modal = await openConfirm();
    const headline = modal.querySelector("[data-testid=live-estimate]")!;
    expect(headline.textContent).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at "
      + "Anthropic list price; Databricks bills in DBUs");
    expect(modal.textContent).toContain("Measured from 6 runs (profile acfc_prx; anthropic list "
      + "price, 2026-10-06).");
    expect(modal.textContent).not.toMatch(/~\s*20s|~3 calls/);
  });

  it("says 'no history yet for completed runs' when none is recorded — no number at all",
     async () => {
    liveHistory = EMPTY;
    const modal = await openConfirm();
    const headline = modal.querySelector("[data-testid=live-estimate]")!;
    expect(headline.textContent).toBe("no history yet for completed runs");
    expect(headline.parentElement!.textContent).not.toContain("$");
    expect(modal.querySelector("[data-testid=live-estimate-stopped]")).toBeNull();
  });

  it("shows the runs that stopped as a second line when there are any", async () => {
    liveHistory = { ...HISTORY, stopped: { runs: 3, wall_seconds: { low: 22, high: 38 } } };
    const modal = await openConfirm();
    expect(modal.querySelector("[data-testid=live-estimate-stopped]")!.textContent)
      .toBe("runs that stopped for answers: typically 20–40 s");
  });

  it("says 'at this workspace's rate' once the workspace's FM API rate priced the runs",
     async () => {
    liveHistory = { ...HISTORY, cost_basis: "workspace", billed_in_dbus: false,
      price_source: "workspace DBU rate, 2026-10-20" };
    const modal = await openConfirm();
    const headline = modal.querySelector("[data-testid=live-estimate]")!;
    expect(headline.textContent).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at this "
      + "workspace's rate");
  });

  it("drops the dollars when no run reported tokens", async () => {
    liveHistory = { ...HISTORY, cost_usd: null, cost_runs: 0, cost_basis: null,
      price_source: null, billed_in_dbus: false };
    const modal = await openConfirm();
    const headline = modal.querySelector("[data-testid=live-estimate]")!;
    expect(headline.textContent).toBe("typically 1½–2½ min · 3–5 calls");
    expect(headline.parentElement!.textContent).not.toContain("$");
  });
});
