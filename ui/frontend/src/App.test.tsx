// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post144: the App opens on Generate ("/"), Results is "/results", the old
   Generate address "/modes" still lands on Generate; the header logo shows only
   when the state root carries one (GET /api/branding). Synthetic fetch stub. */

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

let logo: boolean;
let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  logo = false;
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    const path = String(url).split("?")[0];
    if (path === "/api/branding") return json(200, { logo });
    if (path === "/api/feeds") return json(200, { feeds: [], failures: [], mode: "mock",
                                                  label: null, provider: "mock" });
    return json(404, { detail: "not found" });
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

async function open(path: string) {
  await act(async () => {
    root.render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  });
  for (let i = 0; i < 6; i++) await act(async () => { await Promise.resolve(); });
}

const title = () => host.querySelector(".landing-title")?.textContent;

describe("the App's addresses", () => {
  it("opens on Generate", async () => {
    await open("/");
    expect(title()).toBe("Generate a pipeline from your STTM and FRD");
    expect(host.querySelector(".nav-item.active")?.textContent).toContain("Generate a pipeline");
  });

  it("serves Results at /results", async () => {
    await open("/results");
    expect(title()).toBe("Results");
    expect(host.querySelector(".nav-item.active")?.textContent).toContain("Results");
  });

  it("still lands /modes on Generate", async () => {
    await open("/modes");
    expect(title()).toBe("Generate a pipeline from your STTM and FRD");
  });
});

describe("the header logo", () => {
  it("is absent when the state root has none", async () => {
    await open("/");
    expect(host.querySelector(".topbar-logo")).toBeNull();
  });

  it("shows top-left from the state root when there is one", async () => {
    logo = true;
    await open("/");
    const img = host.querySelector<HTMLImageElement>(".topbar-logo img")!;
    expect(img.getAttribute("src")).toBe("/api/branding/logo");
    expect(host.querySelector(".topbar")!.firstElementChild!.classList.contains("topbar-logo")).toBe(true);
  });
});
