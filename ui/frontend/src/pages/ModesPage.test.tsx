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

/* Every API error shows an error card (Chunk C): the "Re-resolve layout"
   checkbox and the chooser's Retry on an unreadable workbook used to swallow
   theirs (.catch(() => {})). Synthetic backend: a fetch stub answering the
   page's calls; the two actions under test fail. */

const HEALTH = "version 0.0.0 · codegen source: src/codegen/__init__.py · overlays: none · "
  + "startup error: none";

const STATUS = {
  state: "done", stages: [], error: null, last_run_label: null, layout_refresh: false,
  selection: { sttm: null, frd: null, vdd: null }, output_parts: ["framework"],
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

const ROUTES: Record<string, () => Response> = {
  "GET /api/demo/status": () => json(200, STATUS),
  "GET /api/demo/live-available": () => json(200, { available: false, reason: "test stub" }),
  "GET /api/demo/output-options": () => json(200, ["notebook", "framework"]),
  "GET /api/demo/workbooks": () => json(200, { workbooks: [
    { name: "STTM_nb_member_risk.xlsx", source: "local", size: 1024, modified: null,
      kind: "unreadable", kind_reason: "the parser timed out" }] }),
  "GET /api/health/facts": () => json(200, { health_line: HEALTH }),
  "POST /api/demo/layout-refresh": () => json(500, {
    detail: "OSError: the state role refused the write",
    error: { type: "OSError", message: "the state role refused the write",
             where: "ui/backend/demo.py:1 in set_layout_refresh" } }),
  "POST /api/demo/workbook/reclassify": () => json(502, {
    detail: "the workspace refused the read of STTM_nb_member_risk.xlsx" }),
};

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  resetHealthLineCache();
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

async function renderPage() {
  await act(async () => {
    root.render(<MemoryRouter><ModesPage onFeedsChanged={() => {}} /></MemoryRouter>);
  });
  await settle();
}

function button(text: string): HTMLElement {
  const found = [...host.querySelectorAll<HTMLElement>("button, [role=button]")]
    .find((b) => b.textContent?.trim().startsWith(text));
  if (!found) throw new Error(`no button "${text}" in: ${host.textContent}`);
  return found;
}

describe("the Generate page shows every API error", () => {
  it("a failed 'Re-resolve layout' toggle shows the error card", async () => {
    await renderPage();
    expect(host.textContent).not.toContain("The last action failed.");
    const toggle = [...host.querySelectorAll<HTMLInputElement>("input[type=checkbox]")]
      .find((i) => i.parentElement?.textContent?.includes("Re-resolve layout"))!;
    expect(toggle).toBeTruthy();
    await act(async () => { toggle.click(); });
    await settle();
    expect(host.textContent).toContain("The last action failed.");
    expect(host.textContent).toContain("the state role refused the write");
  });

  it("a failed Retry of an unreadable workbook shows the error card inside the chooser",
     async () => {
    await renderPage();
    await act(async () => { button("Choose documents").click(); });
    await settle();
    // The workbook row's Retry chip (not the volumes section's Retry button).
    const chip = [...host.querySelectorAll<HTMLElement>("span[role=button]")]
      .find((b) => b.textContent?.trim() === "Retry")!;
    expect(chip.title).toContain("read it again");
    await act(async () => { chip.click(); });
    await settle();
    expect(vi.mocked(fetch).mock.calls.some(([url, init]) =>
      String(url) === "/api/demo/workbook/reclassify" && init?.method === "POST")).toBe(true);
    // The chooser covers the page: the card is shown in the modal itself.
    const modal = host.querySelector(".modal")!;
    expect(modal.textContent).toContain("The last action failed.");
    expect(modal.textContent).toContain("the workspace refused the read");
  });
});
