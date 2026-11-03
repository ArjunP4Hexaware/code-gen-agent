// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NotebookView } from "../components/NotebookView";
import { FeedDetailPage } from "./FeedDetailPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* P0-4: the report and notebook markdown carries document text (an FRD
   validation rule, an STTM cell, flag text), so markup in it must never run.
   Rendered through the real Report tab and NotebookView. Synthetic feed. */

const PAYLOAD_LIST = [
  "Rule: <img src=x onerror=alert(1)>",
  "<script>alert(2)</script>",
  "[x](javascript:alert(3))",
  '<a href="JaVaScRiPt:alert(4)">y</a>',
  '<svg onload="alert(5)"><circle r="1"/></svg>',
  '<a href=" &#14;javascript:alert(6)">z</a>',
  '<iframe src="https://example.invalid"></iframe><form action="/x"><input></form>',
];
let PAYLOADS = PAYLOAD_LIST.join("\n\n");

const NORMAL = [
  "# Report title",
  "## Gate checks",
  "| check | result |",
  "| --- | --- |",
  "| ruff | passed |",
  "",
  "```sql",
  "SELECT 1",
  "```",
  "",
  "See [the docs](https://example.invalid/docs), [a file](reports/syn_feed.md),",
  "[a section](#gate-checks) and [the root](/results).",
].join("\n");

const FEED = {
  feed_slug: "syn_feed", feed_id: "syn_feed", feed_name: "syn_feed", source_system: "SYN",
  lobs: ["110"], file_format: "csv", frequency: "Monthly", segmented: false,
  sttm_is_synthetic: true, verdict: "PASS", rule_counts: {}, rule_total: 0,
  candidate_count: 0, candidates_pending: 0, files_written: 0, notebook: null, framework: null,
  checks: [], flags: [], delimiter: "|", file_name_patterns: [], landing_location: null,
  contracts: { frd_name: "frd", frd_sha256: "a", sttm_name: "sttm", sttm_sha256: "b",
               sttm_is_synthetic: true },
  tables: { stage: [], standard: null, errors: null, recycle: null, processed_files: null },
  natural_key_columns: [], not_null_columns: [], phi_columns: [], load_windows_sla: [],
  outcomes: [], candidates: [], written_files: [],
};

let host: HTMLDivElement;
let root: Root;
beforeEach(() => {
  PAYLOADS = PAYLOAD_LIST.join("\n\n");
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    const body = String(url).endsWith("/report")
      ? { markdown: `${NORMAL}\n\n${PAYLOADS}` } : FEED;
    return new Response(JSON.stringify(body), {
      status: 200, headers: { "content-type": "application/json" } });
  }));
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => { act(() => root.unmount()); host.remove(); vi.unstubAllGlobals(); });

async function openReport(): Promise<Element> {
  await act(async () => {
    root.render(<MemoryRouter initialEntries={["/feeds/syn_feed?tab=report"]}><Routes>
      <Route path="/feeds/:slug" element={<FeedDetailPage onFeedsChanged={() => {}} />} />
    </Routes></MemoryRouter>);
  });
  for (let i = 0; i < 8; i++) await act(async () => { await Promise.resolve(); });
  const md = host.querySelector(".report-md");
  expect(md).not.toBeNull();
  return md!;
}

async function openNotebook(): Promise<Element> {
  const nb = { cells: [{ cell_type: "markdown", id: "m", source: [NORMAL, "\n\n", PAYLOADS] },
                       { cell_type: "code", id: "c", source: "x = '<img src=x onerror=alert(7)>'" }] };
  await act(async () => { root.render(<NotebookView content={JSON.stringify(nb)} />); });
  return host.querySelector(".notebook")!;
}

function expectInert(el: Element) {
  const all = Array.from(el.querySelectorAll("*"));
  const handlers = all.flatMap((n) => Array.from(n.attributes)
    .filter((a) => a.name.toLowerCase().startsWith("on")).map((a) => `${n.tagName}@${a.name}`));
  expect(handlers).toEqual([]);
  expect(el.querySelectorAll("script, iframe, form, style")).toHaveLength(0);
  const badHref = Array.from(el.querySelectorAll("[href], [src], [action]")).filter((n) =>
    ["href", "src", "action"].some((a) =>
      /^\W*(javascript|data|vbscript):/i.test((n.getAttribute(a) ?? "").replace(/\s/g, ""))));
  expect(badHref.map((n) => n.outerHTML)).toEqual([]);
}

function hrefs(el: Element): string[] {
  return Array.from(el.querySelectorAll("a[href]")).map((a) => a.getAttribute("href")!);
}

describe("the Report tab renders document text inert (P0-4)", () => {
  it.each(PAYLOAD_LIST)("%s", async (payload) => {
    PAYLOADS = payload;
    expectInert(await openReport());
  });

  it("keeps normal markdown, headings demoted one level", async () => {
    const md = await openReport();
    expect(md.querySelector("h1")).toBeNull();
    expect(md.querySelector("h2")?.textContent).toBe("Report title");
    expect(md.querySelector("h3")?.textContent).toBe("Gate checks");
    expect(md.querySelector("table td")?.textContent).toBe("ruff");
    expect(md.querySelector("pre code")?.textContent).toContain("SELECT 1");
    expect(hrefs(md)).toEqual(expect.arrayContaining(
      ["https://example.invalid/docs", "reports/syn_feed.md", "#gate-checks", "/results"]));
    expect(md.textContent).toContain("Rule:");
  });
});

describe("NotebookView renders markdown cells inert (P0-4)", () => {
  it.each(PAYLOAD_LIST)("%s", async (payload) => {
    PAYLOADS = payload;
    expectInert(await openNotebook());
  });

  it("keeps normal markdown and escapes code cells", async () => {
    const nb = await openNotebook();
    expect(nb.querySelector(".nb-md h1")?.textContent).toBe("Report title");
    expect(nb.querySelector(".nb-md table td")?.textContent).toBe("ruff");
    expect(hrefs(nb)).toEqual(expect.arrayContaining(
      ["https://example.invalid/docs", "reports/syn_feed.md", "#gate-checks", "/results"]));
    expect(nb.querySelector(".nb-code pre")?.textContent).toContain("<img src=x onerror=alert(7)>");
  });
});
