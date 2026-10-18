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

/* post68: the output toggles show the BACKEND's choice — the selection, else
   its per-profile default (acfc_prx -> framework) — and assume nothing before
   the status answers. post69: the badge names the notebook — "notebook: v2
   (acfc_prx)" when the profile's notebook is v2. */

let status: Record<string, unknown> | null = null;

function json(code: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: code, headers: { "content-type": "application/json" },
  });
}

const ROUTES: Record<string, () => Response> = {
  "GET /api/demo/status": () => (status ? json(200, status) : json(503, { detail: "starting" })),
  "GET /api/demo/live-available": () => json(200, { available: false, reason: "test stub" }),
  "GET /api/demo/output-options": () => json(200, ["notebook", "framework"]),
  "GET /api/demo/workbooks": () => json(200, { workbooks: [] }),
  "GET /api/health/facts": () => json(200, { health_line: "version 0.0.0" }),
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

async function render() {
  await act(async () => {
    root.render(<MemoryRouter><ModesPage onFeedsChanged={() => {}} /></MemoryRouter>);
  });
  for (let i = 0; i < 5; i++) await act(async () => { await Promise.resolve(); });
}

function pressed(label: string): boolean | null {
  const button = [...host.querySelectorAll<HTMLButtonElement>("button[aria-pressed]")]
    .find((b) => b.textContent?.trim() === label);
  return button ? button.getAttribute("aria-pressed") === "true" : null;
}

const BASE = {
  state: "idle", stages: [], error: null, last_run_label: null, layout_refresh: false,
  selection: { sttm: null, frd: null, vdd: null },
};

describe("the output toggles follow the backend", () => {
  it("shows the per-profile default the status reports (acfc_prx: framework)", async () => {
    status = { ...BASE, output_parts: ["framework"], conventions_profile: "acfc_prx" };
    await render();
    expect(pressed("Framework artefacts")).toBe(true);
    expect(pressed("Notebook")).toBe(false);
    expect(host.querySelector("[data-testid=output-badge]")!.textContent)
      .toBe("Output: Framework artefacts");
  });

  it("assumes no output before the status answers", async () => {
    status = null;
    await render();
    expect(pressed("Notebook")).not.toBe(true);
    expect(pressed("Framework artefacts")).not.toBe(true);
    expect(host.querySelector("[data-testid=output-badge]")?.textContent ?? "Output: …")
      .toBe("Output: …");
  });

  it("names the v2 notebook on the badge", async () => {
    status = { ...BASE, output_parts: ["notebook"], conventions_profile: "acfc_prx",
               notebook_version: "v2" };
    await render();
    expect(host.querySelector("[data-testid=output-badge]")!.textContent)
      .toBe("Output: Notebook — notebook: v2 (acfc_prx)");
  });

  it("says nothing more for a v1 notebook", async () => {
    status = { ...BASE, output_parts: ["notebook"], conventions_profile: "edo_sfmc",
               notebook_version: "v1" };
    await render();
    expect(host.querySelector("[data-testid=output-badge]")!.textContent)
      .toBe("Output: Notebook");
  });
});
