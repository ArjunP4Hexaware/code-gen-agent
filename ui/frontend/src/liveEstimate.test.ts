import { describe, expect, it } from "vitest";
import type { LiveHistory } from "./api";
import { fmtCallsRange, fmtCostRange, fmtDurationRange, liveEstimate } from "./liveEstimate";

function history(over: Partial<LiveHistory> = {}): LiveHistory {
  return {
    profile: "acfc_prx",
    runs: 8,
    wall_seconds: { low: 95, high: 140 },
    model_seconds: { low: 41, high: 68 },
    calls: { low: 3, high: 5 },
    cost_usd: { low: 0.1, high: 0.15 },
    cost_runs: 8,
    prices_as_of: "2026-10-06",
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
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15");
    expect(estimate.detail).toContain("Measured from 8 runs");
    expect(estimate.detail).toContain("prices as of 2026-10-06");
    expect(estimate.detail).toContain("Model calls took 40–70 s of that.");
  });

  it("says 'no history yet' — never a made-up number — when nothing is recorded", () => {
    for (const empty of [undefined, null, history({ runs: 0, wall_seconds: null, calls: null,
      model_seconds: null, cost_usd: null, cost_runs: 0, prices_as_of: null })]) {
      const estimate = liveEstimate(empty);
      expect(estimate.headline).toBe("no history yet");
      // no figure of any kind: no dollar sign, no digit
      expect(estimate.headline + estimate.detail).not.toMatch(/\$|\d/);
    }
  });

  it("shows calls and wall-clock only, no dollars, when no run reported tokens", () => {
    const estimate = liveEstimate(history({ cost_usd: null, cost_runs: 0, prices_as_of: null }));
    expect(estimate.headline).toBe("typically 1½–2½ min · 3–5 calls");
    expect(estimate.headline + estimate.detail).not.toContain("$");
    expect(estimate.detail).not.toContain("Measured from");
    expect(estimate.detail).toContain("no token counts recorded");
  });

  it("names how many runs the cost was measured from", () => {
    const estimate = liveEstimate(history({ cost_runs: 3 }));
    expect(estimate.detail).toContain("Measured from 3 of 8 runs");
  });

  it("calls one run the last run, not typical", () => {
    const estimate = liveEstimate(history({ runs: 1, cost_runs: 1,
      wall_seconds: { low: 118, high: 118 }, calls: { low: 4, high: 4 },
      cost_usd: { low: 0.13, high: 0.13 } }));
    expect(estimate.headline).toBe("last run about 2 min · 4 calls · ≈ $0.13");
    expect(estimate.detail).toContain("Measured from 1 run ");
  });
});
