// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StepStrip } from "../components/StepStrip";
import { ModesPage } from "./ModesPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post143, the guided Generate page: the step strip says where the person is,
   and the drop zone sends an .xlsx up as the STTM and a .docx / .json as the FRD
   (the chooser's own uploads), STTM first; anything else is refused before any
   upload. Synthetic backend: a fetch stub that records the uploads. */

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

let status: Record<string, unknown>;
let uploads: string[];
let environment: Record<string, unknown> | null;

const routes = (): Record<string, (init?: RequestInit) => Response> => ({
  "GET /api/demo/status": () => json(200, status),
  "GET /api/demo/live-available": () => json(200, { available: true, transport: {
    kind: "mock", label: "mock provider", detected_by: "test stub", runtime: null } }),
  "GET /api/demo/output-options": () => json(200, ["framework"]),
  "GET /api/demo/workbooks": () => json(200, { workbooks: [] }),
  "GET /api/demo/environment": () =>
    environment ? json(200, environment) : json(404, { detail: "not found" }),
  "POST /api/demo/upload": (init) => {
    const form = init?.body as FormData;
    uploads.push(`${form.get("kind")}:${(form.get("file") as File).name}`);
    return json(200, { stored: "x", kind: String(form.get("kind")), selected: true });
  },
});

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  uploads = [];
  environment = null;
  status = { state: "idle", stages: [], error: null, last_run_label: null,
             layout_refresh: false, selection: { sttm: null, frd: null, vdd: null },
             output_parts: ["framework"] };
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${String(url).split("?")[0]}`;
    const route = routes()[key];
    return route ? route(init) : json(404, { detail: "not found" });
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
  for (let i = 0; i < 6; i++) await act(async () => { await Promise.resolve(); });
}

async function renderPage() {
  await act(async () => {
    root.render(<MemoryRouter><ModesPage onFeedsChanged={() => {}} /></MemoryRouter>);
  });
  await settle();
}

const current = () => host.querySelector('.steps [aria-current="step"]')?.textContent;

async function drop(files: File[]) {
  const input = host.querySelector<HTMLInputElement>('.dropzone input[type="file"]')!;
  Object.defineProperty(input, "files", { value: files, configurable: true });
  await act(async () => { input.dispatchEvent(new Event("change", { bubbles: true })); });
  await settle();
}

describe("the step strip", () => {
  it("ticks the steps before the current one and marks the current one", () => {
    act(() => root.render(<StepStrip steps={["A", "B", "C"]} active={1} />));
    const items = [...host.querySelectorAll("li")];
    expect(items.map((li) => li.className)).toEqual(["done", "on", ""]);
    expect(items[0].textContent).toBe("✓A");
    expect(items[1].getAttribute("aria-current")).toBe("step");
  });

  it("starts on Choose documents while no STTM is chosen", async () => {
    await renderPage();
    expect(current()).toContain("Choose documents");
    expect(host.textContent).toContain("Choose the STTM workbook first.");
  });

  it("moves to the settings once the STTM and its FRD are chosen", async () => {
    status = { ...status, selection: { sttm: "STTM_syn.xlsx", frd: "FRD_syn.docx", vdd: null },
               frd_name: "FRD_syn.docx", frd_chosen: true };
    await renderPage();
    expect(current()).toContain("Check the settings");
    expect(host.textContent).toContain("2 of 2 required chosen");
    // the drop zone is for what is still missing
    expect(host.querySelector(".dropzone")).toBeNull();
  });

  it("ends on Get the results after a run that completed", async () => {
    status = { ...status, state: "done", outcome: "PASS",
               selection: { sttm: "STTM_syn.xlsx", frd: "FRD_syn.docx", vdd: null },
               frd_name: "FRD_syn.docx", frd_chosen: true };
    await renderPage();
    expect(current()).toContain("Get the results");
    expect(host.textContent).toContain("Your results are ready");
    expect(host.textContent).toContain("View results");
  });
});

describe("the drop zone", () => {
  it("uploads an .xlsx as the STTM and a .docx as the FRD, the STTM first", async () => {
    await renderPage();
    await drop([new File(["d"], "FRD_syn.docx"), new File(["s"], "STTM_syn.xlsx")]);
    expect(uploads).toEqual(["sttm:STTM_syn.xlsx", "frd:FRD_syn.docx"]);
  });

  it("refuses a file that is neither, before uploading anything", async () => {
    await renderPage();
    await drop([new File(["s"], "STTM_syn.xlsx"), new File(["n"], "notes.txt")]);
    expect(uploads).toEqual([]);
    expect(host.textContent).toContain("notes.txt: not an STTM (.xlsx) or an FRD (.docx / .json).");
  });
});

describe("the confirm dialog under the mock", () => {
  it("says the run uses the mock, never 'run live'", async () => {
    status = { ...status, selection: { sttm: "STTM_syn.xlsx", frd: "FRD_syn.docx", vdd: null },
               frd_name: "FRD_syn.docx", frd_chosen: true };
    await renderPage();
    const generate = [...host.querySelectorAll<HTMLButtonElement>(".action-bar button")]
      .find((b) => b.textContent?.trim() === "Generate Documents")!;
    await act(async () => { generate.click(); });
    await settle();
    const modal = host.querySelector(".modal")!;
    expect(modal.textContent).toContain("Confirm — generate with the mock");
    expect(modal.textContent).not.toContain("run live");
  });
});

// post147: the environment line sits in Advanced, named on its summary; a
// required value missing opens the fold and says so
describe("the environment in Advanced", () => {
  const env = (missing: string[]) => ({
    options: [{ name: "D1", default: true, description: "synthetic", values: {} }],
    default: "D1", selected: null, source: "default", custom: null, fields: ["storage_account"],
    required: ["storage_account"], missing_required: missing, origin: null,
  });
  const advanced = () => [...host.querySelectorAll<HTMLDetailsElement>("details.fold")]
    .find((d) => d.querySelector("summary")?.textContent?.startsWith("Advanced"))!;

  it("is inside the folded Advanced section, named on its summary", async () => {
    environment = env([]);
    await renderPage();
    const fold = advanced();
    expect(fold.open).toBe(false);
    expect(fold.querySelector("summary")!.textContent).toContain("environment D1");
    expect(fold.querySelector(".fold-body")!.textContent).toContain("Environment");
    // and nowhere outside it
    const settings = host.querySelector('[aria-label="settings"]')!;
    const outside = [...settings.children].filter((c) => c !== fold).map((c) => c.textContent).join("");
    expect(outside).not.toContain("Environment");
  });

  it("opens and says so when a required value is missing", async () => {
    environment = env(["storage_account"]);
    await renderPage();
    const fold = advanced();
    expect(fold.open).toBe(true);
    expect(fold.querySelector("summary")!.textContent).toContain("1 required value missing");
  });
});

// post152: the run card sits under the Generate button, not at the top of the
// page, and comes into view when a run is live or paused for answers
describe("where the run shows up", () => {
  const chosen = { selection: { sttm: "STTM_syn.xlsx", frd: "FRD_syn.docx", vdd: null },
                   frd_name: "FRD_syn.docx", frd_chosen: true };

  it("puts the run card after the Generate button", async () => {
    status = { ...status, ...chosen, state: "done", outcome: "PASS" };
    await renderPage();
    const bar = host.querySelector(".action-bar")!;
    const card = host.querySelector('[aria-label="this run"]')!;
    expect(bar.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(host.querySelector('[aria-label="documents"]')!
      .compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("scrolls to a run paused for answers", async () => {
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    status = { ...status, ...chosen, state: "needs_layout", pause_kind: "before_generate",
               layout_questions: [] };
    await renderPage();
    expect(scroll).toHaveBeenCalled();
    expect(scroll.mock.contexts.some((el) => (el as Element).getAttribute("aria-label") === "this run"))
      .toBe(true);
  });

  it("leaves a page opened on a finished run where it is", async () => {
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    status = { ...status, ...chosen, state: "done", outcome: "PASS" };
    await renderPage();
    expect(scroll).not.toHaveBeenCalled();
  });
});
