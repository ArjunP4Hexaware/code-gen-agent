import { describe, expect, it } from "vitest";
import type { LiveHistory } from "./api";
import { fmtCallsRange, fmtCostRange, fmtDbuRange, fmtDurationRange, liveEstimate, newPairLine } from "./liveEstimate";

function history(over: Partial<LiveHistory> = {}): LiveHistory {
  return {
    profile: "acfc_prx",
    runs: 8,
    min_runs: 3,
    stopped: null,
    wall_seconds: { low: 95, high: 140 },
    model_seconds: { low: 41, high: 68 },
    calls: { low: 3, high: 5 },
    cost_usd: { low: 0.1, high: 0.15 },
    cost_runs: 8,
    cost_basis: "list",
    price_source: "anthropic list price, 2026-10-06",
    billed_in_dbus: true,
    ...over,
  };
}

describe("fmtDurationRange", () => {
  it("rounds minutes outward to halves", () => {
    expect(fmtDurationRange({ low: 95, high: 140 })).toBe("1½–2½ min");
    expect(fmtDurationRange({ low: 90, high: 100 })).toBe("1½–2 min");
    expect(fmtDurationRange({ low: 118, high: 118 })).toBe("about 2 min");
    expect(fmtDurationRange({ low: 120, high: 120 })).toBe("about 2 min");
  });

  it("stays in seconds under 90 s", () => {
    expect(fmtDurationRange({ low: 41, high: 54 })).toBe("40–55 s");
    expect(fmtDurationRange({ low: 2.1, high: 3.4 })).toBe("2–5 s");
    expect(fmtDurationRange({ low: 30, high: 30 })).toBe("about 30 s");
    expect(fmtDurationRange({ low: 41, high: 68 })).toBe("40–70 s");
  });

  it("starts at ½ min when a long span starts under a minute", () => {
    expect(fmtDurationRange({ low: 20, high: 130 })).toBe("½–2½ min");
  });
});

describe("calls and cost", () => {
  it("collapses an equal range", () => {
    expect(fmtCallsRange({ low: 1, high: 1 })).toBe("1 call");
    expect(fmtCallsRange({ low: 4, high: 4 })).toBe("4 calls");
    expect(fmtCallsRange({ low: 3, high: 5 })).toBe("3–5 calls");
    expect(fmtCostRange({ low: 0.1, high: 0.15 })).toBe("≈ $0.10–0.15");
    expect(fmtCostRange({ low: 0.121, high: 0.124 })).toBe("≈ $0.12");
  });
});

describe("liveEstimate", () => {
  it("leads with wall-clock, then calls and the measured cost", () => {
    const estimate = liveEstimate(history());
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at "
      + "Anthropic list price; Databricks bills in DBUs");
    expect(estimate.detail).toContain("Measured from 8 runs");
    expect(estimate.detail).toContain("(profile acfc_prx; anthropic list price, 2026-10-06)");
    expect(estimate.detail).toContain("Model calls took 40–70 s of that.");
  });

  it("says 'no history yet for completed runs' — never a made-up number — when none is "
     + "recorded", () => {
    for (const empty of [undefined, null, history({ runs: 0, wall_seconds: null, calls: null,
      model_seconds: null, cost_usd: null, cost_runs: 0, cost_basis: null, price_source: null,
      billed_in_dbus: false })]) {
      const estimate = liveEstimate(empty);
      expect(estimate.headline).toBe("no history yet for completed runs");
      // no figure of any kind: no dollar sign, no digit
      expect(estimate.headline + estimate.detail).not.toMatch(/\$|\d/);
      expect(estimate.stopped).toBeNull();
    }
  });

  it("needs three completed runs before it shows a range", () => {
    const estimate = liveEstimate(history({ runs: 2, wall_seconds: null, calls: null,
      model_seconds: null, cost_usd: null, cost_runs: 0, cost_basis: null }));
    expect(estimate.headline).toBe("no history yet for completed runs");
    expect(estimate.detail).toBe("2 completed live runs recorded for profile acfc_prx; a range "
      + "is shown from 3.");
    expect(estimate.headline + estimate.detail).not.toContain("$");
  });

  it("adds the runs that stopped as a second line, only when there are any", () => {
    expect(liveEstimate(history()).stopped).toBeNull();
    const two = liveEstimate(history({ stopped: { runs: 4, wall_seconds: { low: 22, high: 38 } } }));
    expect(two.stopped).toBe("runs that stopped for answers: typically 20–40 s");
    expect(two.headline).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at "
      + "Anthropic list price; Databricks bills in DBUs");
    const one = liveEstimate(history({ stopped: { runs: 1, wall_seconds: { low: 31, high: 31 } } }));
    expect(one.stopped).toBe("runs that stopped for answers: about 30 s (1 run)");
    // shown even before three completed runs exist
    const early = liveEstimate(history({ runs: 0, wall_seconds: null, calls: null,
      stopped: { runs: 2, wall_seconds: { low: 22, high: 38 } } }));
    expect(early.headline).toBe("no history yet for completed runs");
    expect(early.stopped).toBe("runs that stopped for answers: typically 20–40 s");
  });

  it("shows calls and wall-clock only, no dollars, when no run reported tokens", () => {
    const estimate = liveEstimate(history({ cost_usd: null, cost_runs: 0, cost_basis: null,
      price_source: null, billed_in_dbus: false }));
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls");
    expect(estimate.headline + estimate.detail).not.toContain("$");
    expect(estimate.detail).not.toContain("Measured from");
    expect(estimate.detail).toContain("no token counts recorded");
  });

  it("says 'at this workspace's rate' when the workspace's FM API rate priced the runs", () => {
    const estimate = liveEstimate(history({ cost_basis: "workspace", billed_in_dbus: false,
      price_source: "workspace DBU rate, 2026-10-20" }));
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at this "
      + "workspace's rate");
    expect(estimate.headline).not.toContain("list price");
    expect(estimate.detail).toContain("workspace DBU rate, 2026-10-20");
  });

  it("drops the DBU note for list-priced runs through the Anthropic API", () => {
    const estimate = liveEstimate(history({ billed_in_dbus: false }));
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15 at "
      + "Anthropic list price");
  });

  it("names how many runs the cost was measured from", () => {
    const estimate = liveEstimate(history({ cost_runs: 3 }));
    expect(estimate.detail).toContain("Measured from 3 of 8 runs");
  });

  it("collapses equal ranges", () => {
    const estimate = liveEstimate(history({ runs: 3, cost_runs: 3,
      wall_seconds: { low: 118, high: 118 }, calls: { low: 4, high: 4 },
      cost_usd: { low: 0.13, high: 0.13 } }));
    expect(estimate.headline).toBe("typically about 2 min · 4 calls · ≈ $0.13 at Anthropic list "
      + "price; Databricks bills in DBUs");
    expect(estimate.detail).toContain("Measured from 3 runs ");
  });
});

// post145: the ranges come from pairs already mapped; a new pair's first run pays
// its layout calls, said in DBUs - measured when a run recorded it, else the estimate
describe("the new-pair line", () => {
  it("says the configured estimate as an estimate, with its source, in DBUs", () => {
    const line = newPairLine(history({ calls: { low: 0, high: 0 }, new_pair: {
      measured_runs: 0, calls: null, dbu: { low: 1.5, high: 4.5 }, source: "offline estimate" } }));
    expect(line).toContain("A pair the agent has not seen before costs more on its first run");
    expect(line).toContain("one call per document — STTM, FRD, and the VDD if chosen");
    expect(line).toContain("estimated ≈ 1.5–4.5 DBU (offline estimate)");
    expect(line).toContain("Later runs of that pair reuse the mapping and make no call.");
  });

  it("prefers the measurement once runs recorded it", () => {
    const line = newPairLine(history({ new_pair: {
      measured_runs: 2, calls: { low: 2, high: 3 }, dbu: { low: 3.15, high: 6.29 },
      source: "FM API rate" } }));
    expect(line).toContain("typically 2–3 calls, ≈ 3.1–6.3 DBU (measured from 2 runs; FM API rate)");
    expect(line).not.toContain("estimated");
  });

  it("says when no figure is configured, never a made-up one", () => {
    expect(newPairLine(history({ new_pair: null }))).toContain("no DBU figure is configured");
  });

  it("travels with the estimate, history or not", () => {
    expect(liveEstimate(null).newPair).toContain("no DBU figure is configured");
    expect(liveEstimate(history()).newPair).toContain("A pair the agent has not seen before");
  });

  it("formats DBUs", () => {
    expect(fmtDbuRange({ low: 1.5, high: 4.5 })).toBe("≈ 1.5–4.5 DBU");
    expect(fmtDbuRange({ low: 12.4, high: 12.4 })).toBe("≈ 12 DBU");
  });
});
