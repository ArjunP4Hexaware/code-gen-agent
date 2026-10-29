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
    // post143: one row per file, its Download button named for the file
    expect(links.map((a) => a.getAttribute("aria-label"))).toEqual(["Download syn_a.ipynb"]);
    expect(panel.textContent).toContain("syn_a.ipynb");
    expect(links[0].getAttribute("href")).toBe(
      "/api/feeds/syn_a/download?path=notebook%2Fsyn_a.ipynb");
    expect(host.textContent).toContain("Optional: the notebooks, DDL and");
  });

  it("offers every notebook in one zip when there is more than one (post90)", () => {
    const data = { feeds: [feed("syn_a", "notebook/syn_a.ipynb"), feed("syn_b", null),
                           feed("syn_c", "notebook/syn_c.ipynb")],
                   failures: [], mode: "mock", label: null } as never;
    act(() => root.render(
      <MemoryRouter>
        <Dashboard data={data} generating={false} onGenerateAll={() => undefined}
                   onFeedsChanged={() => undefined} />
      </MemoryRouter>));
    const links = [...host.querySelector('[aria-label="notebooks"]')!.querySelectorAll("a")];
    expect(links.map((a) => a.getAttribute("aria-label") ?? a.textContent)).toEqual(
      ["Download syn_a.ipynb", "Download syn_c.ipynb", "Download all (2) .zip"]);
    expect(links[2].getAttribute("href")).toBe("/api/notebooks.zip");
    expect(links[2].hasAttribute("download")).toBe(true);
  });
});

describe("Dashboard framework artefacts (post91)", () => {
  const framed = (slug: string) => ({
    ...feed(slug, null),
    framework: { files: [`${slug}_IIG.xlsx`], groups: {}, row_counts: {}, coverage: {},
                 flagged_blank_columns: ["GROUP_ID"] },
  }) as FeedSummary;
  const render = (data: unknown) => act(() => root.render(
    <MemoryRouter>
      <Dashboard data={data as never} generating={false} onGenerateAll={() => undefined}
                 onFeedsChanged={() => undefined} />
    </MemoryRouter>));

  it("shows the run's one set under '<STTM> DDL and IIG', not a block per feed", () => {
    render({ feeds: [framed("syn_a"), framed("syn_b")], failures: [], mode: "mock",
             label: null, combined: [{ sttm: "STTM_Syn", files: [
               "STTM_Syn_DDL.txt", "STTM_Syn_IIG.xlsx", "STTM_Syn_IIG_REVIEW.xlsx",
               "STTM_Syn_LOG.md"] }] });
    expect(host.textContent).toContain("STTM_Syn DDL and IIG");
    const links = [...host.querySelectorAll('a[href^="/api/combined/"]')];
    expect(links.map((a) => a.getAttribute("aria-label"))).toEqual([
      "Download STTM_Syn_DDL.txt", "Download STTM_Syn_IIG.xlsx",
      "Download STTM_Syn_IIG_REVIEW.xlsx", "Download STTM_Syn_LOG.md"]);
    expect(host.querySelector('a[href^="/api/feeds/syn_a/download"]')).toBeNull();
  });

  it("falls back to one block per feed for a run without a combined set", () => {
    render({ feeds: [framed("syn_a")], failures: [], mode: "mock", label: null });
    expect(host.querySelector('a[href^="/api/feeds/syn_a/download"]')).not.toBeNull();
    expect(host.querySelector('a[href^="/api/combined/"]')).toBeNull();
  });
});

describe("Dashboard sections and the IDs to assign (post101)", () => {
  const framed = (slug: string) => ({
    ...feed(slug, null),
    framework: { files: [`${slug}_IIG.xlsx`], groups: {}, row_counts: {}, coverage: {},
                 flagged_blank_columns: ["GROUP_ID", "PIPELINE_ID", "CREATED_DATE",
                                         "DATABRICKS_CLUSTERID"] },
  }) as FeedSummary;
  const show = (extra: Record<string, unknown>) => act(() => root.render(
    <MemoryRouter>
      <Dashboard data={{ feeds: [framed("syn_a"), framed("syn_b")], failures: [], mode: "mock",
                         label: null, ...extra } as never}
                 generating={false} onGenerateAll={() => undefined}
                 onFeedsChanged={() => undefined} />
    </MemoryRouter>));

  // post143 (the guided look): the counts first, then the files, then the feeds -
  // nothing folded but the team's details
  it("shows the counts, then the files, then the feed cards", () => {
    show({});
    const order = ["run summary", "framework artefacts", "feeds"]
      .map((name) => host.querySelector(`[aria-label="${name}"]`)!);
    expect(order.every(Boolean)).toBe(true);
    for (let i = 1; i < order.length; i++) {
      expect(order[i - 1].compareDocumentPosition(order[i]) & Node.DOCUMENT_POSITION_FOLLOWING)
        .toBeTruthy();
    }
    expect(host.querySelector("details[aria-label]")).toBeNull();
    expect(host.querySelector('[aria-label="feeds"] h2')!.textContent).toContain("Feeds (2)");
    expect(host.querySelector('[aria-label="run summary"]')!.textContent).toContain(
      "passed with flags2");
    expect(host.textContent).toContain("Framework artefacts");
  });

  it("names only the configured IDs some feed leaves blank, with their hints", () => {
    show({ assign_ids: { PIPELINE_ID: "each pipeline row, unique",
                         PARENT_PIPELINE_ID: "its master's PIPELINE_ID",
                         GROUP_ID: "one unique per feed" } });
    const line = host.querySelector('[aria-label="ids to assign"]')!.textContent;
    expect(line).toBe("Assign before loading: PIPELINE_ID (each pipeline row, unique) · "
      + "GROUP_ID (one unique per feed)");
    expect(host.textContent).not.toContain("DATABRICKS_CLUSTERID");
    expect(host.textContent).not.toContain("Framework-assigned IDs left blank");
  });

  it("keeps the full line when no list is configured", () => {
    show({});
    expect(host.textContent).toContain("Framework-assigned IDs left blank");
  });
});

describe("Dashboard with notebooks off in the App (post91)", () => {
  it("shows no Notebooks panel and no notebook wording", () => {
    const data = { feeds: [feed("syn_a", "notebook/syn_a.ipynb"), feed("syn_b", "notebook/syn_b.ipynb")],
                   failures: [], mode: "mock", label: null, app_options: ["framework"] } as never;
    act(() => root.render(
      <MemoryRouter>
        <Dashboard data={data} generating={false} onGenerateAll={() => undefined}
                   onFeedsChanged={() => undefined} />
      </MemoryRouter>));
    expect(host.querySelector('[aria-label="notebooks"]')).toBeNull();
    expect(host.querySelector('a[href="/api/notebooks.zip"]')).toBeNull();
    expect(host.textContent).toContain("Optional: the DDL and IIG are already written");
    expect(host.textContent).not.toContain("the notebooks, DDL");
  });
});
