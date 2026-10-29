// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FeedDetailPage } from "./FeedDetailPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post148: the feed page's Overview in the Results layout - counts first, a
   failed gate check as a red issue card, the passed ones folded, each flag an
   issue card (shown whole), the facts in cards. Synthetic feed. */

const FEED = {
  feed_slug: "syn_feed", feed_id: "syn_feed", feed_name: "syn_feed", source_system: "SYN",
  lobs: ["110"], file_format: "csv", frequency: "Monthly", segmented: false,
  sttm_is_synthetic: true, verdict: "FAIL", rule_counts: {}, rule_total: 3,
  candidate_count: 0, candidates_pending: 0, files_written: 4, notebook: null, framework: null,
  checks: [{ name: "ruff", passed: true, details: "ruff clean" },
           { name: "ddl_parses", passed: false, details: "statement 2 does not parse" }],
  flags: ["frd_unstated:stage_target.catalog source_used:STTM band", "ddl_comment_blank:c — d",
          "candidate #2 pending engineer approval: rule 1"],
  delimiter: "|", file_name_patterns: ["SYN_<LOB>.txt"], landing_location: null,
  contracts: { frd_name: "frd", frd_sha256: "a", sttm_name: "sttm", sttm_sha256: "b",
               sttm_is_synthetic: true },
  tables: { stage: ["d1.stg.a", "d1.stg.b"], standard: "d1.std.a", errors: "e",
            recycle: null, processed_files: "p" },
  natural_key_columns: ["K"], not_null_columns: [], phi_columns: [], load_windows_sla: [],
  outcomes: [], candidates: [], written_files: [],
};

let host: HTMLDivElement;
let root: Root;
beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(FEED), {
    status: 200, headers: { "content-type": "application/json" } })));
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => { act(() => root.unmount()); host.remove(); vi.unstubAllGlobals(); });

async function open() {
  await act(async () => {
    root.render(<MemoryRouter initialEntries={["/feeds/syn_feed"]}><Routes>
      <Route path="/feeds/:slug" element={<FeedDetailPage onFeedsChanged={() => {}} />} />
    </Routes></MemoryRouter>);
  });
  for (let i = 0; i < 6; i++) await act(async () => { await Promise.resolve(); });
}

describe("the feed Overview (post148)", () => {
  it("leads with the counts", async () => {
    await open();
    const tiles = host.querySelector('[aria-label="feed summary"]')!;
    expect(tiles.textContent).toContain("gate checks passed1/2");
    expect(tiles.textContent).toContain("flags to check3");
    expect(tiles.textContent).toContain("target tables3");
    expect(tiles.querySelector(".tile.bad")).not.toBeNull();
  });

  it("shows a failed check as a red issue card and folds the passed ones", async () => {
    await open();
    const card = host.querySelector('[aria-label="gate checks"]')!;
    const bad = card.querySelector(".issue.bad")!;
    expect(bad.textContent).toBe("failedddl_parses — statement 2 does not parse");
    const fold = card.querySelector<HTMLDetailsElement>("details.fold")!;
    expect(fold.open).toBe(false);
    expect(fold.querySelector("summary")!.textContent).toContain("1 passed");
  });

  it("makes each flag an issue card, its text whole", async () => {
    await open();
    const items = [...host.querySelectorAll('[aria-label="flags"] li.issue')];
    expect(items.map((li) => li.textContent)).toContain(
      "frd_unstated:stage_target.catalog source_used:STTM band");
    expect(items).toHaveLength(3);
    const hitl = items.find((li) => li.classList.contains("bad"))!;
    expect(hitl.textContent).toContain("PENDING ENGINEER APPROVAL");
  });
});
