// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { FeedSummary } from "../api";
import { Dashboard } from "./Dashboard";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post81: the notebook is one click from the results — a "Notebooks" panel with the
   path the run wrote (v2: notebook/<slug>.ipynb), never behind the Layer-2 review. */

const feed = (slug: string, notebook: string | null): FeedSummary => ({
  feed_slug: slug, feed_id: slug, feed_name: slug, source_system: "SYN", lobs: [],
  file_format: "csv", frequency: null, segmented: false, sttm_is_synthetic: true,
  verdict: "PASS_WITH_FLAGS", flags: [], checks: [], rule_counts: {}, rule_total: 0,
  candidate_count: 0, candidates_pending: 0, files_written: 3, notebook, framework: null,
  layer2: { mode: "defer", review_candidates: "pending", rules: 2 },
} as FeedSummary);

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
});

describe("Dashboard notebooks (post81)", () => {
  it("links each written notebook by its own path, beside an optional Layer-2 panel", () => {
    const data = { feeds: [feed("syn_a", "notebook/syn_a.ipynb"), feed("syn_b", null)],
                   failures: [], mode: "mock", label: null } as never;
    act(() => root.render(
      <MemoryRouter>
        <Dashboard data={data} generating={false} onGenerateAll={() => undefined}
                   onFeedsChanged={() => undefined} />
      </MemoryRouter>));
    const panel = host.querySelector('[aria-label="notebooks"]')!;
    const links = [...panel.querySelectorAll("a")];
    expect(links.map((a) => a.textContent)).toEqual(["syn_a.ipynb"]);
    expect(links[0].getAttribute("href")).toBe(
      "/api/feeds/syn_a/download?path=notebook%2Fsyn_a.ipynb");
    expect(host.textContent).toContain("Optional: the notebooks, DDL and");
  });
});
