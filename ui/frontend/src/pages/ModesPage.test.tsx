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

/* post80: a run that stopped at blocking questions sends the person to them (no
   "View results"), and the layout dialog's Continue works with nothing picked. */
describe("blocking questions and the layout dialog", () => {
  function withStatus(extra: Record<string, unknown>) {
    ROUTES["GET /api/demo/status"] = () => json(200, { ...STATUS, ...extra });
  }
  afterEach(() => { ROUTES["GET /api/demo/status"] = () => json(200, STATUS); });

  it("a run with a blocking question shows the redirect, not View results", async () => {
    withStatus({
      outcome: "NEEDS_ANSWERS",
      inputs_needed: [{ key: "run.environment.storage_account", question: "the account",
                        feed: "", scope: "run", required: true }],
    });
    await renderPage();
    expect(host.textContent).toContain("Complete the blocking questions first.");
    expect(host.textContent).toContain("stopped at blocking questions");
    expect(host.textContent).not.toContain("View results");
    const target = host.querySelector<HTMLElement>("#blocking-questions")!;
    target.scrollIntoView = vi.fn();
    await act(async () => { button("Go to the blocking questions").click(); });
    expect(target.scrollIntoView).toHaveBeenCalled();
  });

  it("a run without one still offers View results", async () => {
    withStatus({ outcome: "PASS_WITH_OPEN_INPUTS", last_run_label: "demo_x" });
    await renderPage();
    expect(host.textContent).toContain("View results");
    expect(host.textContent).not.toContain("Complete the blocking questions first.");
  });

  it("Continue is enabled with nothing picked and proceeds like Proceed with unresolved",
     async () => {
    const sent: unknown[] = [];
    ROUTES["POST /api/demo/layout-answers"] = () => json(200, { ...STATUS, state: "done" });
    withStatus({
      state: "needs_layout",
      layout_questions: [{ document: "sttm", key: "sheets[0]/stage/table", sheet: "sheets[0]",
                           layer: "stage", role: "table", reason: "no header names it",
                           header: ["A", "B"], candidates: [{ col: 1, header: "A" }] }],
    });
    await renderPage();
    const cont = button("Continue") as HTMLButtonElement;
    expect(cont.disabled).toBe(false);
    vi.mocked(fetch).mockImplementation(async (url: RequestInfo | URL, init?: RequestInit) => {
      const key = `${(init?.method ?? "GET").toUpperCase()} ${String(url).split("?")[0]}`;
      if (key === "POST /api/demo/layout-answers") sent.push(JSON.parse(String(init?.body)));
      return (ROUTES[key] ?? (() => json(404, { detail: "not found" })))();
    });
    await act(async () => { cont.click(); });
    await settle();
    expect(sent).toHaveLength(1);
    expect((sent[0] as { proceed: boolean }).proceed).toBe(true);
    delete ROUTES["POST /api/demo/layout-answers"];
  });
});

describe("blocking lines the page lists nowhere else", () => {
  afterEach(() => { ROUTES["GET /api/demo/status"] = () => json(200, STATUS); });

  it("the alert names them, and still offers the jump for the listed ones", async () => {
    ROUTES["GET /api/demo/status"] = () => json(200, {
      ...STATUS, outcome: "NEEDS_ANSWERS",
      blocking: [{ key: "feeds[0].src_adls_path", scope: "feed", feed: "zq_a" },
                 { key: "run.environment.storage_account", scope: "run" }],
      inputs_needed: [{ key: "run.environment.storage_account", question: "the account",
                        feed: "", scope: "run", required: true }],
    });
    await renderPage();
    const note = host.querySelector('[aria-label="blocking not answerable here"]')!;
    expect(note.textContent).toContain("feeds[0].src_adls_path");
    expect(note.textContent).not.toContain("storage_account");
    expect(host.textContent).toContain("Go to the blocking questions");
    expect(host.textContent).not.toContain("View results");
  });
});

describe("the pause before generating (post80)", () => {
  afterEach(() => { ROUTES["GET /api/demo/status"] = () => json(200, STATUS); });

  it("asks the run's blocking questions in the dialog, environment first", async () => {
    ROUTES["GET /api/demo/status"] = () => json(200, {
      ...STATUS, state: "needs_layout", pause_kind: "before_generate",
      layout_questions: [
        { document: "run", key: "run.environment.storage_account", sheet: null, layer: null,
          role: "run.environment.storage_account", kind: "text", reason: "required",
          header: [], candidates: [], title: "storage_account of this run's environment" },
        { document: "frd", key: "feeds[0].src_adls_path", sheet: null, layer: null,
          role: "feeds[0].src_adls_path", kind: "text", reason: "no document states it",
          header: [], candidates: [{ value: "/inbound/syn/", source: "convention" }],
          suggested: 0, title: "the landing (inbound) path of zq_a" },
      ],
    });
    await renderPage();
    expect(host.textContent).toContain("Paused before generating");
    expect(host.textContent).not.toContain("the layout needs a human decision");
    const text = host.textContent ?? "";
    expect(text.indexOf("This run (environment)")).toBeLessThan(text.indexOf("FRD document"));
    expect(host.textContent).not.toContain("Re-resolve layout");
    expect(host.textContent).not.toContain("Ask the model for advice");
    expect((button("Continue") as HTMLButtonElement).disabled).toBe(false);
  });
});
