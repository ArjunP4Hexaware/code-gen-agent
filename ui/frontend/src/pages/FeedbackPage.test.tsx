// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { FeedbackItem } from "../api";
import { FeedbackPage, runWhen } from "./FeedbackPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post215: the Feedback page (ported from the STTM agent's App) against a fetch stub -
   the form posts a bug report / suggestion; the list shows your own; an admin gets the
   Mine / Everyone's switch and a status picker. Synthetic users only. */

const item = (over: Partial<FeedbackItem> = {}): FeedbackItem => ({
  sub_id: "fb_20261120_100000_abcdef", created_at: "2026-11-20T10:00:00+00:00",
  user: "alice@example.com", kind: "bug", title: "Blank column", text: "It was blank.",
  run: "demo_20261120_090000", images: [], status: "new",
  status_history: [{ status: "new", by: "alice@example.com", at: "2026-11-20T10:00:00+00:00" }],
  ...over,
});

let host: HTMLDivElement;
let root: Root;
let isAdmin = false;
let items: FeedbackItem[] = [];

function reply(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  isAdmin = false;
  items = [item()];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (url === "/api/feedback/runs") return reply({ runs: ["demo_20261120_090000"] });
    if (url.startsWith("/api/feedback?") || url === "/api/feedback") {
      if (init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        const saved = item({ ...body, sub_id: "fb_20261120_110000_123456" });
        items = [saved, ...items];
        return reply(saved, 201);
      }
      return reply({ user: "alice@example.com", is_admin: isAdmin, all: url.includes("all=true"), items });
    }
    if (url.endsWith("/status")) {
      const { status } = JSON.parse(String(init?.body));
      return reply(item({ status }));
    }
    return reply({ detail: "unexpected" }, 404);
  }));
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.unstubAllGlobals();
});

async function render() {
  await act(async () => root.render(<FeedbackPage />));
  await act(async () => { await Promise.resolve(); });
}

function setValue(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, value: string) {
  const proto = Object.getPrototypeOf(el);
  Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(el, value);
  el.dispatchEvent(new Event(el instanceof HTMLSelectElement ? "change" : "input", { bubbles: true }));
}

describe("Feedback page (post215)", () => {
  it("has one h1 and lists your own feedback with its status", async () => {
    await render();
    expect(host.querySelectorAll("h1")).toHaveLength(1);
    expect(host.textContent).toContain("Blank column");
    expect(host.textContent).toContain("New");
    expect(host.textContent).toContain("Bug report");
    expect(host.textContent).not.toContain("Everyone's");          // not an admin
    expect(host.querySelector(".fb-status-set")).toBeNull();
  });

  it("refuses to send without a title and details, then sends a suggestion", async () => {
    await render();
    const sendButton = [...host.querySelectorAll("button")].find((b) => b.textContent === "Send feedback")!;
    await act(async () => sendButton.click());
    expect(host.textContent).toContain("Add a title and some details first.");
    expect(vi.mocked(fetch).mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);

    const suggestion = [...host.querySelectorAll("button")].find((b) => b.textContent === "Suggestion")!;
    await act(async () => suggestion.click());
    await act(async () => setValue(host.querySelector("input.fb-input")!, "Add a search box"));
    await act(async () => setValue(host.querySelector("textarea")!, "Searching the runs would help."));
    await act(async () => setValue(host.querySelector("select")!, "demo_20261120_090000"));
    await act(async () => sendButton.click());
    await act(async () => { await Promise.resolve(); });
    const post = vi.mocked(fetch).mock.calls.find(([, init]) => init?.method === "POST")!;
    expect(JSON.parse(String(post[1]!.body))).toEqual({
      kind: "suggestion", title: "Add a search box", text: "Searching the runs would help.",
      run: "demo_20261120_090000", images: [],
    });
    expect(host.textContent).toContain("your feedback was sent");
  });

  it("refuses a file that is not an image before sending anything", async () => {
    await render();
    const input = host.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["<svg/>"], "x.svg", { type: "image/svg+xml" });
    Object.defineProperty(input, "files", { value: [file] });
    await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
    expect(host.textContent).toContain("is not a PNG, JPEG, GIF or WebP image.");
    expect(host.querySelectorAll(".fb-thumb")).toHaveLength(0);
  });

  it("gives an admin the Mine / Everyone's switch and a status picker", async () => {
    isAdmin = true;
    await render();
    const everyone = [...host.querySelectorAll("button")].find((b) => b.textContent === "Everyone's")!;
    await act(async () => everyone.click());
    await act(async () => { await Promise.resolve(); });
    expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url) === "/api/feedback?all=true")).toBe(true);
    const picker = host.querySelector(".fb-status-set select") as HTMLSelectElement;
    await act(async () => setValue(picker, "done"));
    await act(async () => { await Promise.resolve(); });
    expect(host.querySelector(".fb-status")!.textContent).toBe("Done");
  });

  it("names a run by its start time, never by its folder name", () => {
    expect(runWhen("demo_20261120_090000")).toMatch(/^Run started /);
    expect(runWhen("demo_20261120_090000")).not.toContain("demo_");
    expect(runWhen("something")).toBe("something");
  });
});
